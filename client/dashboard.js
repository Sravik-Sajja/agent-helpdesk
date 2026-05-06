const API = "http://localhost:8000";
const STATUSES = ["pending", "in_progress", "resolved", "escalated"];

// ── Clock ───────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById("nav-time");
  if (!el) return;
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };
  tick();
  setInterval(tick, 10000);
}

// ── Status update ───────────────────────────────────────────────
async function updateStatus(id, status) {
  try {
    await fetch(`${API}/tasks/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
  } catch (err) {
    console.error("Status update failed:", err);
  }
}

// ── Render helpers ──────────────────────────────────────────────
function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderCard(task, idx) {
  const urgency  = task.entities?.urgency || "low";
  const route    = task.route || "";
  const conf     = Math.round((task.confidence || 0) * 100);
  const intent   = (task.intent || "").replace(/_/g, " ");
  const routeLbl = route.replace(/_/g, " ");
  const time     = new Date(task.created_at + "Z").toLocaleString([], {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit"
  });

  const message = task.title;

  const opts = STATUSES.map(s =>
    `<option value="${s}" ${s === task.status ? "selected" : ""}>${s.replace("_", " ")}</option>`
  ).join("");

  return `
    <div class="task-card" style="animation-delay:${idx * 40}ms">
      <div class="task-urgency-bar ${urgency}"></div>
      <div class="task-message">${esc(message)}</div>
      <div class="task-badges">
        <span class="badge route-${route}">${esc(routeLbl)}</span>
        <span class="badge">${esc(intent)}</span>
      </div>
      <div class="conf-row">
        <div class="conf-track"><div class="conf-fill" style="width:${conf}%"></div></div>
        <span class="conf-label">${conf}%</span>
      </div>
      <div class="task-footer">
        <span class="task-time">${esc(time)}</span>
        <select class="status-select" onchange="updateStatus(${task.id}, this.value)">${opts}</select>
      </div>
    </div>`;
}

function renderColumn(containerId, tasks) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = tasks.length
    ? tasks.map((t, i) => renderCard(t, i)).join("")
    : `<div class="col-empty">no tasks</div>`;
}

// ── Load ────────────────────────────────────────────────────────
async function load() {
  const btn = document.getElementById("btn-refresh");
  const err = document.getElementById("error-banner");

  btn.classList.add("spinning");
  btn.textContent = "Loading…";
  err.classList.remove("visible");

  try {
    const res   = await fetch(`${API}/dashboard`);
    const data  = await res.json();
    const tasks = data.tasks || [];

    const high = tasks.filter(t => t.entities?.urgency === "high");
    const med  = tasks.filter(t => t.entities?.urgency === "medium");
    const low  = tasks.filter(t => t.entities?.urgency === "low");

    // Stats
    document.getElementById("stat-total").textContent = tasks.length;
    document.getElementById("stat-high").textContent  = high.length;
    document.getElementById("stat-med").textContent   = med.length;
    document.getElementById("stat-low").textContent   = low.length;

    // Column counts
    document.getElementById("count-high").textContent = high.length;
    document.getElementById("count-med").textContent  = med.length;
    document.getElementById("count-low").textContent  = low.length;

    renderColumn("col-high", high);
    renderColumn("col-med",  med);
    renderColumn("col-low",  low);

  } catch (err2) {
    err.textContent = "⚠ Could not reach server — is the API running on port 8000?";
    err.classList.add("visible");
    ["col-high", "col-med", "col-low"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.innerHTML = `<div class="col-empty">—</div>`;
    });
  }

  btn.classList.remove("spinning");
  btn.textContent = "Refresh";
}

// ── Init ────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  startClock();
  load();
});