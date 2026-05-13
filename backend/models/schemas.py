"""
AuditCraft v2 - Pydantic Schemas
Defines request/response models for the audit API.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Vulnerability severity levels aligned with industry standards."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class VulnerabilityType(str, Enum):
    """Supported vulnerability categories."""
    REENTRANCY = "Reentrancy"
    OVERFLOW = "Integer Overflow/Underflow"
    ACCESS_CONTROL = "Access Control"
    UNCHECKED_SEND = "Unchecked External Call"
    TIMESTAMP_DEPENDENCE = "Timestamp Dependence"
    TX_ORIGIN = "tx.origin Authentication"
    UNUSED_VARIABLES = "Unused Variables"
    COMPILER_WARNINGS = "Compiler Warnings"


class CompileRequest(BaseModel):
    """Request body for Solidity compilation."""
    source_code: str = Field(
        ...,
        min_length=10,
        description="Solidity source code to compile",
        examples=["pragma solidity ^0.8.0; contract A {}"]
    )
    version: str = Field(
        default="0.8.19",
        pattern=r"^0\.8\.\d+$",
        description="Target solc version (0.8.x only)"
    )
    optimize: bool = Field(default=True, description="Enable optimizer")
    runs: int = Field(default=200, ge=0, le=10000, description="Optimizer runs")


class CompileResult(BaseModel):
    """Result of a compilation attempt."""
    success: bool
    version: str
    bytecode: Optional[str] = None
    abi: Optional[list] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Finding(BaseModel):
    """A single vulnerability finding."""
    id: str = Field(..., description="Unique finding ID")
    title: str
    vulnerability_type: VulnerabilityType
    severity: Severity
    line: int = Field(..., ge=1, description="Line number in source")
    column: int = Field(default=0, ge=0)
    contract: Optional[str] = None
    function: Optional[str] = None
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    confidence: str = Field(default="Medium", pattern=r"^(High|Medium|Low)$")


class ScanRequest(BaseModel):
    """Request body for security scan."""
    source_code: str = Field(..., min_length=10)
    version: Optional[str] = Field(default="0.8.19", pattern=r"^0\.8\.\d+$")
    run_compiler: bool = Field(default=True, description="Compile before scanning")
    detectors: Optional[List[VulnerabilityType]] = Field(
        default=None,
        description="Limit to specific detectors; None = run all"
    )


class ScanResult(BaseModel):
    """Aggregated scan output."""
    success: bool
    findings: List[Finding] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    compiler_output: Optional[CompileResult] = None
    scan_time_ms: int
    detectors_run: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """/health endpoint response."""
    status: str
    version: str = "2.0.0"
    solc_available: bool
    solc_version: Optional[str] = None
    supported_detectors: List[str]
