/**
 * AuditCraft v2 — Frontend Controller
 * Vanilla JS. Calls http://localhost:8000/scan
 */

const API_BASE = "";

// DOM refs
const els = {
  editor: document.getElementById("source-code"),
  btnAnalyze: document.getElementById("btn-analyze"),
  btnClear: document.getElementById("btn-clear"),
  btnLoadSample: document.getElementById("btn-load-sample"),
  versionSelect: document.getElementById("solc-version"),
  findingsContainer: document.getElementById("findings-container"),
  summaryChips: document.getElementById("summary-chips"),
  statusBadge: document.getElementById("status-badge"),
  alertBox: document.getElementById("alert-box"),
  spinner: document.getElementById("spinner"),
};

// Sample vulnerable contract for quick testing
const SAMPLE_CONTRACT = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // Reentrancy vulnerability
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "No balance");
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] = 0; // state update after external call
    }

    // tx.origin auth
    function transferOwner(address newOwner) external {
        require(tx.origin == address(0x123), "Not owner");
        // owner = newOwner;
    }

    receive() external payable {
        deposit();
    }
}`;

// Severity order for sorting (highest first)
const SEVERITY_RANK = {
  Critical: 5,
  High: 4,
  Medium: 3,
  Low: 2,
  Info: 1,
};

/* ---------- Init ---------- */
function init() {
  els.btnAnalyze.addEventListener("click", onAnalyze);
  els.btnClear.addEventListener("click", onClear);
  els.btnLoadSample.addEventListener("click", () => {
    els.editor.value = SAMPLE_CONTRACT;
    hideAlert();
  });

  // Check backend health on load
  checkHealth();
  // Periodically recheck (every 15s)
  setInterval(checkHealth, 15000);
}

/* ---------- Health Check ---------- */
async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    if (res.ok) {
      const data = await res.json();
      setStatus(true, data.solc_version ? `Online — solc ${data.solc_version}` : "Online");
    } else {
      setStatus(false, "Offline");
    }
  } catch {
    setStatus(false, "Offline");
  }
}

function setStatus(online, text) {
  els.statusBadge.className = "status-badge " + (online ? "online" : "offline");
  els.statusBadge.textContent = text;
}

/* ---------- Analyze ---------- */
async function onAnalyze() {
  const source = els.editor.value.trim();
  if (source.length < 10) {
    showAlert("Please paste at least a few lines of Solidity code.", "warning");
    return;
  }

  setLoading(true);
  hideAlert();
  clearResults();

  const payload = {
    source_code: source,
    version: els.versionSelect.value,
    run_compiler: true,
  };

  try {
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const err = await res.json();
        detail = err.detail || JSON.stringify(err);
      } catch {
        detail = await res.text();
      }
      if (res.status === 422) {
        showAlert(`Compilation failed:\n${detail}`, "error");
      } else if (res.status >= 500) {
        showAlert(`Server error (${res.status}):\n${detail}`, "error");
      } else {
        showAlert(`Request failed (${res.status}):\n${detail}`, "error");
      }
      return;
    }

    const data = await res.json();
    if (!data.success) {
      showAlert("Scan reported failure. Check console for details.", "warning");
      console.warn("ScanResult.success=false", data);
    }

    renderResults(data);
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      showAlert("Cannot reach backend.\nMake sure the server is running on localhost:8000", "error");
    } else {
      showAlert(`Unexpected error: ${err.message}`, "error");
    }
    console.error(err);
  } finally {
    setLoading(false);
  }
}

function setLoading(loading) {
  els.btnAnalyze.disabled = loading;
  els.spinner.classList.toggle("show", loading);
}

/* ---------- Render Results ---------- */
function clearResults() {
  els.findingsContainer.innerHTML = "";
  els.summaryChips.innerHTML = "";
}

function renderResults(data) {
  const findings = data.findings || [];

  // Summary chips
  const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Info: 0 };
  findings.forEach((f) => {
    if (counts[f.severity] !== undefined) counts[f.severity]++;
  });

  const total = findings.length;
  let chipsHtml = `<span class="chip">Total<span class="count">${total}</span></span>`;
  for (const [sev, n] of Object.entries(counts)) {
    if (n > 0) {
      chipsHtml += `<span class="chip" style="color:var(--sev-${sev.toLowerCase()})">${sev}<span class="count">${n}</span></span>`;
    }
  }
  if (total === 0) {
    chipsHtml += `<span class="chip" style="color:var(--success)">Clean ✓</span>`;
  }
  els.summaryChips.innerHTML = chipsHtml;

  // Empty state
  if (findings.length === 0) {
    els.findingsContainer.innerHTML = `
      <div class="empty-state">
        <div class="icon">🛡️</div>
        <p>No vulnerabilities detected.</p>
        <p style="font-size:12px">Paste a different contract and run Analyze again.</p>
      </div>`;
    return;
  }

  // Sort by severity desc, then line number asc
  findings.sort((a, b) => {
    const diff = (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0);
    if (diff !== 0) return diff;
    return (a.line || 0) - (b.line || 0);
  });

  // Render cards
  const frag = document.createDocumentFragment();
  findings.forEach((f) => {
    frag.appendChild(buildFindingCard(f));
  });
  els.findingsContainer.appendChild(frag);
}

function buildFindingCard(f) {
  const sevClass = (f.severity || "info").toLowerCase();
  const card = document.createElement("div");
  card.className = `finding-card ${sevClass}`;

  const id = f.id || Math.random().toString(36).slice(2, 8);
  const lineInfo = f.line ? `L${f.line}${f.column ? ":" + f.column : ""}` : "";
  const contractInfo = f.contract ? `<span>${f.contract}</span>` : "";
  const funcInfo = f.function ? `<span>${f.function}()</span>` : "";
  const metaParts = [contractInfo, funcInfo, lineInfo ? `<span class="loc">${lineInfo}</span>` : ""]
    .filter(Boolean)
    .join("<span style='opacity:0.4'>|</span>");

  const snippetHtml = f.code_snippet
    ? `<div class="code-snippet">${escapeHtml(f.code_snippet)}</div>`
    : "";

  const recHtml = f.recommendation
    ? `<div class="recommendation"><strong>💡 Recommendation:</strong> ${escapeHtml(f.recommendation)}</div>`
    : "";

  card.innerHTML = `
    <div class="finding-header" onclick="toggleFinding('${id}')">
      <div class="finding-title-wrap">
        <span class="severity-badge ${sevClass}">${f.severity}</span>
        <span class="finding-title">${escapeHtml(f.title || f.vulnerability_type)}</span>
      </div>
      <div class="finding-meta">
        ${metaParts}
        <span class="chevron">▼</span>
      </div>
    </div>
    <div class="finding-body" id="body-${id}">
      <p><strong>Type:</strong> ${f.vulnerability_type || "—"}</p>
      <p><strong>Confidence:</strong> ${f.confidence || "Medium"}</p>
      <p>${escapeHtml(f.description || "No description provided.")}</p>
      ${snippetHtml}
      ${recHtml}
    </div>
  `;
  return card;
}

// Global helper for inline onclick handlers
window.toggleFinding = function (id) {
  const card = document.querySelector(`#body-${id}`).closest(".finding-card");
  card.classList.toggle("expanded");
};

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ---------- Utilities ---------- */
function onClear() {
  els.editor.value = "";
  clearResults();
  hideAlert();
}

function showAlert(message, type = "info") {
  els.alertBox.className = `alert alert-${type} show`;
  // Preserve newlines
  els.alertBox.innerHTML = `<span>${message.replace(/\n/g, "<br>")}</span>`;
}

function hideAlert() {
  els.alertBox.className = "alert";
  els.alertBox.innerHTML = "";
}

/* ---------- Boot ---------- */
document.addEventListener("DOMContentLoaded", init);
