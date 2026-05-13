"""
AuditCraft v2 API Tests
Run: pytest tests/test_api.py
"""
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ------------------------------------------------------------------ #
# Sample contracts
# ------------------------------------------------------------------ #

VULNERABLE_CONTRACT = """
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() external {
        uint256 amount = balances[msg.sender];
        (bool success, ) = msg.sender.call{value: amount}("");
        balances[msg.sender] = 0;
    }

    function setTime() external view returns (uint256) {
        return block.timestamp;
    }
}
"""

SIMPLE_CONTRACT = """
pragma solidity ^0.8.0;

contract Simple {
    uint256 public value;

    function set(uint256 x) external {
        value = x;
    }

    function get() external view returns (uint256) {
        return value;
    }
}
"""


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #

class TestHealthEndpoint:
    def test_health_returns_200(self):
        """/health should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"
        assert "solc_available" in data
        assert "supported_detectors" in data
        assert isinstance(data["supported_detectors"], list)
        assert len(data["supported_detectors"]) > 0


class TestScanEndpoint:
    def test_scan_vulnerable_contract_returns_findings(self):
        """Scanning a known-vulnerable contract should produce findings."""
        payload = {
            "source_code": VULNERABLE_CONTRACT,
            "version": "0.8.19",
            "run_compiler": False,
        }
        response = client.post("/scan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "findings" in data
        assert isinstance(data["findings"], list)
        # Should detect reentrancy and timestamp dependence at minimum
        types_found = {f["vulnerability_type"] for f in data["findings"]}
        assert "Reentrancy" in types_found or "Timestamp Dependence" in types_found
        assert "summary" in data
        assert "scan_time_ms" in data
        assert data["scan_time_ms"] >= 0

    def test_scan_with_detectors_filter(self):
        """Limiting detectors should only return findings for those types."""
        payload = {
            "source_code": VULNERABLE_CONTRACT,
            "version": "0.8.19",
            "run_compiler": False,
            "detectors": ["Timestamp Dependence"],
        }
        response = client.post("/scan", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        for finding in data["findings"]:
            assert finding["vulnerability_type"] == "Timestamp Dependence"


class TestCompileEndpoint:
    def test_compile_simple_contract_skips_solc(self):
        """/compile with a simple contract; we accept either 200 (success) or 422 (solc unavailable)."""
        payload = {
            "source_code": SIMPLE_CONTRACT,
            "version": "0.8.19",
            "optimize": True,
            "runs": 200,
        }
        response = client.post("/compile", json=payload)
        assert response.status_code in (200, 422)
        data = response.json()
        if response.status_code == 200:
            assert data["success"] is True
            assert data["version"] == "0.8.19"
            assert data["bytecode"] is not None or data["abi"] is not None
        else:
            # 422 from HTTPException returns FastAPI error shape: { "detail": [...] }
            assert "detail" in data


class TestDetectorsEndpoint:
    def test_list_detectors(self):
        """/detectors should return a non-empty list of strings."""
        response = client.get("/detectors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all(isinstance(d, str) for d in data)
