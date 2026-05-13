"""
AuditCraft v2 - Static Analyzer Service
Lightweight AST-like analysis for common vulnerabilities.
Uses regex + structural heuristics (no heavy Slither dependency required).
Designed to be upgraded to Slither when available.
"""
import re
import uuid
import time
from typing import List, Optional
from dataclasses import dataclass

from models.schemas import (
    Finding, ScanRequest, ScanResult, CompileResult,
    VulnerabilityType, Severity
)
from services.compiler import compiler_service


@dataclass
class _RawMatch:
    line: int
    column: int
    text: str
    contract: Optional[str] = None
    function: Optional[str] = None


class SolidityAnalyzer:
    """
    Multi-pass analyzer:
      1. Normalize source into lines
      2. Build coarse contract/function map
      3. Run detector passes
      4. Deduplicate overlapping findings
    """

    def __init__(self):
        self.detectors = {
            VulnerabilityType.REENTRANCY: self._detect_reentrancy,
            VulnerabilityType.OVERFLOW: self._detect_overflow,
            VulnerabilityType.ACCESS_CONTROL: self._detect_access_control,
            VulnerabilityType.UNCHECKED_SEND: self._detect_unchecked_external,
            VulnerabilityType.TIMESTAMP_DEPENDENCE: self._detect_timestamp,
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def scan(self, request: ScanRequest) -> ScanResult:
        t0 = time.time()
        findings: List[Finding] = []
        compiler_out: Optional[CompileResult] = None

        # Optional compilation step
        if request.run_compiler:
            from models.schemas import CompileRequest
            comp = compiler_service.compile(
                CompileRequest(
                    source_code=request.source_code,
                    version=request.version or "0.8.19"
                )
            )
            compiler_out = comp
            if not comp.success:
                # Still run regex-based scan even if compilation fails
                pass

        lines = request.source_code.splitlines()
        ctx = _Context(lines)

        active_detectors = request.detectors or list(self.detectors.keys())
        for det_type in active_detectors:
            if det_type in self.detectors:
                raw_matches = self.detectors[det_type](ctx)
                for m in raw_matches:
                    findings.append(self._to_finding(m, det_type))

        # Deduplicate by (line, type)
        deduped = {}
        for f in findings:
            key = (f.line, f.vulnerability_type)
            if key not in deduped:
                deduped[key] = f
            elif f.severity.value > deduped[key].severity.value:
                deduped[key] = f

        findings = list(deduped.values())
        elapsed_ms = int((time.time() - t0) * 1000)

        summary = {
            "total_findings": len(findings),
            "by_severity": {},
            "by_type": {},
        }
        for f in findings:
            summary["by_severity"][f.severity] = summary["by_severity"].get(f.severity, 0) + 1
            summary["by_type"][f.vulnerability_type] = summary["by_type"].get(f.vulnerability_type, 0) + 1

        return ScanResult(
            success=True,
            findings=findings,
            summary=summary,
            compiler_output=compiler_out,
            scan_time_ms=elapsed_ms,
            detectors_run=[d.value for d in active_detectors]
        )

    # ------------------------------------------------------------------ #
    # Detectors
    # ------------------------------------------------------------------ #

    def _detect_reentrancy(self, ctx: "_Context") -> List[_RawMatch]:
        """
        Heuristic: external call (call/value/send) before a state change.
        This is the classic cross-function reentrancy signal.
        """
        matches: List[_RawMatch] = []
        ext_call_pattern = re.compile(
            r"(\.call\{?|\.value\s*\(|\.transfer\s*\(|\.send\s*\()",
            re.IGNORECASE
        )
        state_change_pattern = re.compile(
            r"\b(mapping|balances|storage)\b.*=|\b\w+\s*=\s*\w+\s*[\-+]?",
            re.IGNORECASE
        )

        for i, line in enumerate(ctx.lines, start=1):
            if ext_call_pattern.search(line):
                # Look ahead for state change in the next 5 lines
                for j in range(i, min(i + 5, len(ctx.lines) + 1)):
                    if state_change_pattern.search(ctx.lines[j - 1]):
                        matches.append(_RawMatch(
                            line=i,
                            column=line.index(".") if "." in line else 0,
                            text=line.strip(),
                            contract=ctx.contract_at(i),
                            function=ctx.function_at(i)
                        ))
                        break  # one finding per external call
        return matches

    def _detect_overflow(self, ctx: "_Context") -> List[_RawMatch]:
        """
        Detect arithmetic without SafeMath or unchecked blocks.
        In 0.8.x overflow reverts by default, but unchecked{} disables it.
        Flag: arithmetic ops inside unchecked{}, or raw ops on user input.
        """
        matches: List[_RawMatch] = []
        # Match + - * / on variables (not literals) outside obvious SafeMath usage
        op_pattern = re.compile(r"\b\w+\s*([\-+*/])\s*\b\w+")

        in_unchecked = False
        unchecked_depth = 0

        for i, line in enumerate(ctx.lines, start=1):
            stripped = line.strip()
            if "unchecked" in stripped and "{" in stripped:
                in_unchecked = True
                unchecked_depth = stripped.count("{")
            elif in_unchecked:
                # Track braces to exit unchecked block
                unchecked_depth += stripped.count("{") - stripped.count("}")
                if unchecked_depth <= 0:
                    in_unchecked = False
                    unchecked_depth = 0

            if op_pattern.search(line):
                # In 0.8.x, raw ops are safe unless unchecked{} is used
                # We flag unchecked blocks and also raw ops on balance/amount fields
                if in_unchecked or any(k in line.lower() for k in ("amount", "balance", "value", "supply")):
                    matches.append(_RawMatch(
                        line=i,
                        column=0,
                        text=line.strip(),
                        contract=ctx.contract_at(i),
                        function=ctx.function_at(i)
                    ))
        return matches

    def _detect_access_control(self, ctx: "_Context") -> List[_RawMatch]:
        """
        Flag functions that modify state but lack onlyOwner / require(msg.sender).
        Only checks external/public functions.
        """
        matches: List[_RawMatch] = []
        func_pattern = re.compile(
            r"\b(function)\s+(\w+)\s*\([^)]*\)\s*(external|public)"
        )
        modifier_pattern = re.compile(r"\b(onlyOwner|onlyAdmin|auth|authorized)\b")
        guard_pattern = re.compile(r"require\s*\(\s*msg\.sender")

        for i, line in enumerate(ctx.lines, start=1):
            m = func_pattern.search(line)
            if not m:
                continue
            func_name = m.group(2)
            # Scan next 8 lines for access control
            has_guard = False
            for j in range(i, min(i + 8, len(ctx.lines) + 1)):
                scan = ctx.lines[j - 1]
                if modifier_pattern.search(scan) or guard_pattern.search(scan):
                    has_guard = True
                    break
            if not has_guard:
                # Verify it does something stateful (contains = or mapping update)
                for j in range(i, min(i + 10, len(ctx.lines) + 1)):
                    if re.search(r"\b\w+\s*=\s*", ctx.lines[j - 1]):
                        matches.append(_RawMatch(
                            line=i,
                            column=m.start(),
                            text=line.strip(),
                            contract=ctx.contract_at(i),
                            function=func_name
                        ))
                        break
        return matches

    def _detect_unchecked_external(self, ctx: "_Context") -> List[_RawMatch]:
        """
        Flag .transfer/.send/.call where return value is not checked.
        """
        matches: List[_RawMatch] = []
        call_pattern = re.compile(
            r"(\.(call|send|transfer)\s*\([^)]*\))",
            re.IGNORECASE
        )
        checked_pattern = re.compile(r"require\s*\(|if\s*\(|\w+\s*=\s*.*\.(call|send)")

        for i, line in enumerate(ctx.lines, start=1):
            m = call_pattern.search(line)
            if not m:
                continue
            # Check same line or previous 2 lines for handling
            checked = False
            for j in range(max(1, i - 2), i + 1):
                if checked_pattern.search(ctx.lines[j - 1]):
                    checked = True
                    break
            if not checked:
                matches.append(_RawMatch(
                    line=i,
                    column=m.start(),
                    text=line.strip(),
                    contract=ctx.contract_at(i),
                    function=ctx.function_at(i)
                ))
        return matches

    def _detect_timestamp(self, ctx: "_Context") -> List[_RawMatch]:
        """
        Flag use of block.timestamp for time-sensitive logic.
        """
        matches: List[_RawMatch] = []
        ts_pattern = re.compile(r"\b(block\.timestamp|now)\b")
        for i, line in enumerate(ctx.lines, start=1):
            if ts_pattern.search(line):
                matches.append(_RawMatch(
                    line=i,
                    column=0,
                    text=line.strip(),
                    contract=ctx.contract_at(i),
                    function=ctx.function_at(i)
                ))
        return matches

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _to_finding(self, raw: _RawMatch, vtype: VulnerabilityType) -> Finding:
        mapping = {
            VulnerabilityType.REENTRANCY: (
                Severity.HIGH,
                "External call precedes state change. Reentrancy risk.",
                "Follow Checks-Effects-Interactions pattern. Use ReentrancyGuard."
            ),
            VulnerabilityType.OVERFLOW: (
                Severity.MEDIUM,
                "Arithmetic operation may overflow/underflow.",
                "Use OpenZeppelin SafeMath (pre-0.8) or avoid unchecked blocks."
            ),
            VulnerabilityType.ACCESS_CONTROL: (
                Severity.HIGH,
                "State-modifying function lacks access control.",
                "Add onlyOwner modifier or require(msg.sender == owner)."
            ),
            VulnerabilityType.UNCHECKED_SEND: (
                Severity.MEDIUM,
                "Return value of external call is not checked.",
                "Wrap call in require() or check bool return value."
            ),
            VulnerabilityType.TIMESTAMP_DEPENDENCE: (
                Severity.LOW,
                "Contract relies on block.timestamp.",
                "Avoid strict equality on timestamps; use block.number for finer granularity."
            ),
        }
        sev, desc, rec = mapping.get(vtype, (Severity.INFO, "Unknown.", "Review manually."))
        return Finding(
            id=str(uuid.uuid4())[:8],
            title=vtype.value,
            vulnerability_type=vtype,
            severity=sev,
            line=raw.line,
            column=raw.column,
            contract=raw.contract,
            function=raw.function,
            description=desc,
            recommendation=rec,
            code_snippet=raw.text[:120],
            confidence="Medium"
        )


# ---------------------------------------------------------------------- #
# Internal context builder
# ---------------------------------------------------------------------- #

class _Context:
    """Lightweight source-code navigator."""

    def __init__(self, lines: List[str]):
        self.lines = lines
        self._contract_map: dict = {}
        self._function_map: dict = {}
        self._build_maps()

    def _build_maps(self):
        current_contract: Optional[str] = None
        current_function: Optional[str] = None
        contract_pattern = re.compile(r"\bcontract\s+(\w+)")
        func_pattern = re.compile(r"\bfunction\s+(\w+)")

        for i, line in enumerate(self.lines, start=1):
            cm = contract_pattern.search(line)
            if cm:
                current_contract = cm.group(1)
            fm = func_pattern.search(line)
            if fm:
                current_function = fm.group(1)
            self._contract_map[i] = current_contract
            self._function_map[i] = current_function

    def contract_at(self, line: int) -> Optional[str]:
        return self._contract_map.get(line)

    def function_at(self, line: int) -> Optional[str]:
        return self._function_map.get(line)


# Singleton
analyzer_service = SolidityAnalyzer()
