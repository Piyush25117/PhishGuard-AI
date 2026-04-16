/**
 * PhishGuard AI — Frontend Application Logic
 * ─────────────────────────────────────────────
 * Handles:
 *   • URL scanning (POST /api/predict)
 *   • History display & clearing (GET/DELETE /api/history)
 *   • Analytics dashboard (GET /api/analytics)
 *   • Animated particles background
 *   • Tab navigation
 *   • Error handling & loading states
 */

"use strict";

/* ══════════════════════════════════════════════════════════
   CONFIG
   ══════════════════════════════════════════════════════════ */

const API_BASE = "http://localhost:5000/api";

/* ══════════════════════════════════════════════════════════
   PARTICLES BACKGROUND
   ══════════════════════════════════════════════════════════ */

(function spawnParticles() {
  const container = document.getElementById("particles");
  const COLORS = [
    "hsla(258,76%,67%,.6)",
    "hsla(190,80%,60%,.5)",
    "hsla(142,70%,45%,.4)",
    "hsla(220,80%,60%,.4)",
  ];
  const COUNT = 28;

  for (let i = 0; i < COUNT; i++) {
    const el = document.createElement("div");
    el.className = "particle";
    const size = Math.random() * 4 + 2;        // 2–6 px
    const x    = Math.random() * 100;          // % horizontal
    const dur  = Math.random() * 15 + 10;      // 10–25 s
    const del  = Math.random() * 15;           // 0–15 s delay
    el.style.cssText = `
      width:${size}px; height:${size}px;
      left:${x}%;
      background:${COLORS[Math.floor(Math.random() * COLORS.length)]};
      animation-duration:${dur}s;
      animation-delay:${del}s;
      filter:blur(1px);
    `;
    container.appendChild(el);
  }
})();

/* ══════════════════════════════════════════════════════════
   TAB NAVIGATION
   ══════════════════════════════════════════════════════════ */

const tabs = ["scanner", "history", "analytics"];

function switchTab(tabId) {
  tabs.forEach((t) => {
    document.getElementById(`tab-${t}`).classList.remove("active");
    document.getElementById(`panel-${t}`).classList.remove("active");
  });
  document.getElementById(`tab-${tabId}`).classList.add("active");

  const panel = document.getElementById(`panel-${tabId}`);
  panel.classList.add("active");

  // Auto-load data when switching to those tabs
  if (tabId === "history")   loadHistory();
  if (tabId === "analytics") loadAnalytics();
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

/* ══════════════════════════════════════════════════════════
   UTILITY HELPERS
   ══════════════════════════════════════════════════════════ */

function $(id) { return document.getElementById(id); }

function showEl(id)  { $(id).classList.remove("hidden"); }
function hideEl(id)  { $(id).classList.add("hidden"); }

function setError(msg) {
  $("error-text").textContent = msg;
  showEl("error-banner");
  $("input-group").classList.add("error");
}

function clearError() {
  hideEl("error-banner");
  $("input-group").classList.remove("error");
}

/** Normalise a URL: prepend https:// if no scheme is present. */
function normaliseURL(raw) {
  raw = raw.trim();
  if (raw && !/^https?:\/\//i.test(raw)) return "https://" + raw;
  return raw;
}

/** Format ISO timestamp to a human-readable local string. */
function fmtDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

/** Truncate a URL for display. */
function truncURL(url, max = 50) {
  return url.length > max ? url.slice(0, max) + "…" : url;
}

/* ══════════════════════════════════════════════════════════
   SCANNER — POST /api/predict
   ══════════════════════════════════════════════════════════ */

const scanBtn   = $("scan-btn");
const urlInput  = $("url-input");

/** Validate the URL client-side before sending to the API. */
function clientValidate(url) {
  if (!url) return "Please enter a URL.";
  if (url.length > 2048) return "URL is too long (max 2048 characters).";
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol))
      return "Only HTTP and HTTPS URLs are supported.";
  } catch {
    return "Invalid URL format. Make sure to include https:// or http://";
  }
  return null; // valid
}

/** Kick off a scan for the value in the input box. */
async function runScan() {
  clearError();
  hideEl("result-card");

  const raw = normaliseURL(urlInput.value);
  const err = clientValidate(raw);
  if (err) return setError(err);

  // Show loading state
  scanBtn.classList.add("loading");
  scanBtn.disabled = true;
  showEl("skeleton-card");

  try {
    const res  = await fetch(`${API_BASE}/predict`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ url: raw }),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `Server error ${res.status}`);

    renderResult(data);

  } catch (exc) {
    // API unreachable — show fallback demo result so UI still looks good
    if (exc instanceof TypeError && exc.message.includes("fetch")) {
      setError("Cannot reach the backend server. Start Flask: python backend/app.py");
    } else {
      setError(exc.message || "Unexpected error. Please try again.");
    }
  } finally {
    hideEl("skeleton-card");
    scanBtn.classList.remove("loading");
    scanBtn.disabled = false;
  }
}

/** Render the prediction result card. */
function renderResult({ url, prediction, confidence, features }) {
  const isPhishing = prediction === "Phishing";
  const cls        = isPhishing ? "phishing" : "safe";
  const icon       = isPhishing ? "🎣" : "🛡️";
  const pct        = Math.round(confidence * 100);

  const card = $("result-card");
  card.className = `card result-card ${cls}`;

  // Icon
  const iconWrap = $("result-icon-wrap");
  iconWrap.className = `result-icon-wrap ${cls}`;
  iconWrap.textContent = icon;

  // Label & URL
  const labelEl = $("result-label");
  labelEl.className = `result-label ${cls}`;
  labelEl.textContent = prediction;
  $("result-url").textContent = truncURL(url, 65);

  // Confidence bar
  const confVal = $("conf-value");
  confVal.className = `conf-value ${cls}`;
  confVal.textContent = `${pct}%`;

  const bar = $("conf-bar");
  bar.className = `confidence-bar-fill ${cls}`;
  // Defer so CSS transition fires
  requestAnimationFrame(() => {
    bar.style.width = `${pct}%`;
  });

  // Feature chips
  if (features && typeof features === "object") {
    renderFeatureChips(features);
  }

  showEl("result-card");
  card.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/** Pretty-print name. */
function prettify(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

/** Render extracted feature chips inside the details element. */
function renderFeatureChips(features) {
  const grid = $("feature-grid");
  grid.innerHTML = "";

  // Features where value=1 means suspicious
  const phishingFlags = new Set([
    "has_ip_address", "has_at_symbol", "has_double_slash_redirect",
    "has_hyphen_in_domain", "has_suspicious_tld", "has_port_in_url",
  ]);
  // Features where value=1 means safe
  const safeFlags = new Set(["uses_https", "ssl_valid", "page_rank_mock"]);

  Object.entries(features).forEach(([key, val]) => {
    const chip = document.createElement("div");
    chip.className = "feature-chip";

    let valClass = "";
    const numVal = Number(val);
    if (phishingFlags.has(key)) {
      valClass = numVal === 1 ? "flag" : "ok";
    } else if (safeFlags.has(key)) {
      valClass = numVal === 1 ? "ok" : "flag";
    }

    const displayVal =
      typeof val === "number" && !Number.isInteger(val)
        ? val.toFixed(4)
        : String(val);

    chip.innerHTML = `
      <span class="feature-chip-name">${prettify(key)}</span>
      <span class="feature-chip-val ${valClass}">${displayVal}</span>
    `;
    grid.appendChild(chip);
  });
}

/* Scan button click */
scanBtn.addEventListener("click", runScan);

/* Allow Enter key to trigger scan */
urlInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runScan();
});

/* Clear error when user starts typing again */
urlInput.addEventListener("input", clearError);

/* ══════════════════════════════════════════════════════════
   HISTORY — GET/DELETE /api/history
   ══════════════════════════════════════════════════════════ */

async function loadHistory() {
  showEl("history-loading");
  hideEl("history-empty");
  hideEl("history-table-wrap");

  try {
    const res  = await fetch(`${API_BASE}/history?limit=100`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load history");

    renderHistory(data.records || []);
  } catch (exc) {
    hideEl("history-loading");
    showEl("history-empty");
    $("history-empty").querySelector("h3").textContent = "Failed to load history";
    $("history-empty").querySelector("p").textContent  = exc.message;
  }
}

function renderHistory(records) {
  hideEl("history-loading");

  if (!records.length) {
    showEl("history-empty");
    return;
  }

  const tbody = $("history-tbody");
  tbody.innerHTML = "";

  records.forEach((rec, idx) => {
    const isPhishing = rec.prediction === "Phishing";
    const pct        = Math.round((rec.confidence || 0) * 100);
    const cls        = isPhishing ? "phishing" : "safe";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="color:var(--text-muted);font-size:.8rem">${idx + 1}</td>
      <td>
        <div class="history-url" title="${rec.url}">${rec.url}</div>
      </td>
      <td>
        <span class="badge badge-${cls}">
          ${isPhishing ? "🎣" : "🛡️"} ${rec.prediction}
        </span>
      </td>
      <td>
        <div class="mini-bar-wrap">
          <div class="mini-bar">
            <div class="mini-fill mini-fill-${cls}" style="width:${pct}%"></div>
          </div>
          <span class="mini-pct">${pct}%</span>
        </div>
      </td>
      <td style="color:var(--text-muted);font-size:.8rem;white-space:nowrap">
        ${fmtDate(rec.timestamp)}
      </td>
    `;
    tbody.appendChild(tr);
  });

  showEl("history-table-wrap");
}

$("refresh-history-btn").addEventListener("click", loadHistory);

$("clear-history-btn").addEventListener("click", async () => {
  if (!confirm("Delete all scan history? This cannot be undone.")) return;

  try {
    const res  = await fetch(`${API_BASE}/history`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to clear history");
    loadHistory();
  } catch (exc) {
    alert("Error clearing history: " + exc.message);
  }
});

/* ══════════════════════════════════════════════════════════
   ANALYTICS — GET /api/analytics
   ══════════════════════════════════════════════════════════ */

async function loadAnalytics() {
  try {
    const res  = await fetch(`${API_BASE}/analytics`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Failed to load analytics");

    renderAnalytics(data);
  } catch (exc) {
    console.warn("Analytics load failed:", exc.message);
  }
}

function renderAnalytics(data) {
  const total         = data.total || 0;
  const byLabel       = data.by_label || {};
  const safeData      = byLabel["Safe"]     || { count: 0, avg_confidence: 0 };
  const phishingData  = byLabel["Phishing"] || { count: 0, avg_confidence: 0 };
  const phishingRate  = data.phishing_rate  || 0;

  // Stat cards
  $("stat-total-val").textContent    = total;
  $("stat-safe-val").textContent     = safeData.count;
  $("stat-phishing-val").textContent = phishingData.count;
  $("stat-rate-val").textContent     = `${Math.round(phishingRate * 100)}%`;

  // Donut chart (circumference of r=70 ≈ 439.82)
  const C            = 2 * Math.PI * 70;   // ≈ 439.82
  const safeArc      = total ? (safeData.count    / total) * C : 0;
  const phishingArc  = total ? (phishingData.count / total) * C : 0;

  const safeEl = $("donut-safe-arc");
  const phEl   = $("donut-phishing-arc");

  safeEl.setAttribute("stroke-dasharray",     `0 ${C}`);
  phEl.setAttribute("stroke-dasharray",       `0 ${C}`);
  safeEl.setAttribute("stroke-dashoffset",   0);
  phEl.setAttribute("stroke-dashoffset",     0);

  // Offset phishing arc so it starts after the safe arc
  const safeOffset = -safeArc;

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      safeEl.setAttribute("stroke-dasharray", `${safeArc} ${C - safeArc}`);
      phEl.setAttribute("stroke-dasharray",   `${phishingArc} ${C - phishingArc}`);
      phEl.style.strokeDashoffset = safeOffset;
    });
  });

  $("donut-pct").textContent    = total ? `${Math.round(phishingRate * 100)}%` : "0%";
  $("legend-safe-n").textContent    = safeData.count;
  $("legend-phishing-n").textContent = phishingData.count;

  // Confidence bars
  const safeConf    = Math.round((safeData.avg_confidence    || 0) * 100);
  const phishConf   = Math.round((phishingData.avg_confidence || 0) * 100);

  $("bar-safe").style.width     = `${safeConf}%`;
  $("bar-phishing").style.width = `${phishConf}%`;
  $("bar-safe-pct").textContent     = `${safeConf}%`;
  $("bar-phishing-pct").textContent = `${phishConf}%`;
}

$("refresh-analytics-btn").addEventListener("click", loadAnalytics);

/* ══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
   ══════════════════════════════════════════════════════════ */

document.addEventListener("keydown", (e) => {
  // Ctrl/Cmd + K → focus URL input & switch to scanner
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    switchTab("scanner");
    urlInput.focus();
  }
});

/* ══════════════════════════════════════════════════════════
   INIT
   ══════════════════════════════════════════════════════════ */

// Pre-focus the input on load
urlInput.focus();

console.log(
  "%c🛡️ PhishGuard AI",
  "color:#a78bfa;font-size:20px;font-weight:800;",
  "\nBackend API:", API_BASE,
  "\nPress Ctrl+K to quick-search a URL"
);
