"""
AuditCraft v2 - Solidity Compiler Service
Handles solc installation, compilation, and ABI/bytecode extraction.
Uses py-solc-x for cross-platform solc management.
"""
import json
import tempfile
import os
from typing import Optional
from solcx import install_solc, get_installed_solc_versions, compile_source
from solcx.exceptions import SolcNotInstalled, SolcError

from models.schemas import CompileRequest, CompileResult


class SolidityCompiler:
    """Service wrapper around py-solc-x."""

    # Whitelist of supported versions for security/stability
    SUPPORTED_VERSIONS = {f"0.8.{p}" for p in range(0, 30)}

    def __init__(self):
        self._cached_version: Optional[str] = None

    def ensure_version(self, version: str) -> bool:
        """
        Install solc version if missing.
        Returns True if available, False on failure.
        """
        if version not in self.SUPPORTED_VERSIONS:
            return False
        try:
            installed = {str(v) for v in get_installed_solc_versions()}
            if version not in installed:
                install_solc(version)
            self._cached_version = version
            return True
        except Exception as exc:
            # Log but don't leak internals to caller
            print(f"[Compiler] Failed to install solc {version}: {exc}")
            return False

    def compile(self, request: CompileRequest) -> CompileResult:
        """
        Compile Solidity source code.
        Returns CompileResult with bytecode, ABI, errors, and warnings.
        """
        # Validate version
        if request.version not in self.SUPPORTED_VERSIONS:
            return CompileResult(
                success=False,
                version=request.version,
                errors=[f"Version {request.version} not in supported set."]
            )

        if not self.ensure_version(request.version):
            return CompileResult(
                success=False,
                version=request.version,
                errors=[f"Unable to install or locate solc {request.version}."]
            )

        # Write source to temp file (solcx requires a file path)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".sol", delete=False
            ) as tmp:
                tmp.write(request.source_code)
                tmp_path = tmp.name

            compiler_input = {
                "language": "Solidity",
                "sources": {
                    os.path.basename(tmp_path): {
                        "urls": [tmp_path]
                    }
                },
                "settings": {
                    "optimizer": {
                        "enabled": request.optimize,
                        "runs": request.runs
                    },
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "evm.bytecode.object"]
                        }
                    }
                }
            }

            compiled = compile_source(
                request.source_code,
                solc_version=request.version,
                optimize=request.optimize,
                optimize_runs=request.runs,
                output_values=["abi", "bin"]
            )

            # Extract first contract found
            first_key = next(iter(compiled))
            contract_data = compiled[first_key]
            abi = contract_data.get("abi", [])
            bytecode = contract_data.get("bin", "") or contract_data.get("bytecode", "")

            return CompileResult(
                success=True,
                version=request.version,
                bytecode=bytecode or None,
                abi=abi if abi else None,
                errors=[],
                warnings=[]
            )

        except SolcError as exc:
            # Structured error from solc
            return CompileResult(
                success=False,
                version=request.version,
                errors=self._extract_errors(exc)
            )
        except Exception as exc:
            return CompileResult(
                success=False,
                version=request.version,
                errors=[f"Unexpected compilation error: {exc}"]
            )
        finally:
            # Cleanup temp file
            try:
                if "tmp_path" in locals():
                    os.unlink(tmp_path)
            except OSError:
                pass

    @staticmethod
    def _extract_errors(exc: SolcError) -> list:
        """Parse SolcError into a list of human-readable strings."""
        # py-solc-x wraps stderr; attempt to split by line
        raw = str(exc)
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        return lines if lines else [raw]


# Singleton instance for import convenience
compiler_service = SolidityCompiler()
