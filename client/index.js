const API = "http://localhost:8000";
let storedContext = null;

const chatEl  = document.getElementById("chat");
const msgEl   = document.getElementById("msg");
const sendBtn = document.getElementById("send");
const emptyEl = document.getElementById("empty");

// Auto-grow textarea
msgEl.addEventListener("input", () => {
  msgEl.style.height = "44px";
  msgEl.style.height = Math.min(msgEl.scrollHeight, 120) + "px";
});
msgEl.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});

function removeEmpty() {
  if (emptyEl) emptyEl.remove();
}

function appendUserBubble(text) {
  removeEmpty();
  const row = document.createElement("div");
  row.className = "message-row user";
  row.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  chatEl.appendChild(row);
  scrollBot();
}

function appendTyping() {
  const row = document.createElement("div");
  row.className = "typing-row";
  row.id = "typing";
  row.innerHTML = `<div class="typing-bubble"><span></span><span></span><span></span></div>`;
  chatEl.appendChild(row);
  scrollBot();
  return row;
}

function appendBotBubble(data) {
  document.getElementById("typing")?.remove();
  const row = document.createElement("div");
  row.className = "message-row bot";

  const action    = data.action || "—";
  const entities  = data._parsed?.entities || {};
  const urgency   = entities.urgency || "low";
  const questions = data.follow_up_questions || [];

  let bodyHtml = "";
  if (action === "follow_up_questions" && questions.length) {
    bodyHtml = `<ul class="follow-up-list">${questions.map(q => `<li>${escHtml(q)}</li>`).join("")}</ul>`;
  } else {
    const msgs = {
      human_handoff:       "Your request has been flagged for a staff member who will follow up shortly.",
      self_schedule:       "You're all set — your scheduling request has been made.",
      auto_response:       "We found information that may help. Would pull from a FAQ database here",
      follow_up_questions: "We need a bit more information to help you.",
      clarify:             "What can I help you with?",
    };
    bodyHtml = `<div class="bubble-body">${msgs[action] || "Request received."}</div>`;
  }

  row.innerHTML = `
    <div class="bubble" onclick='openPanel(${escAttr(JSON.stringify(data))})'>
      <div class="bubble-action">
        <div class="urgency-dot ${urgency}"></div>
        <span class="route-badge ${action}">${action.replace(/_/g, " ")}</span>
      </div>
      ${bodyHtml}
      <div class="bubble-hint">click for details</div>
    </div>`;
  chatEl.appendChild(row);
  scrollBot();
}

async function send() {
  const text = msgEl.value.trim();
  if (!text) return;
  msgEl.value = "";
  msgEl.style.height = "44px";
  sendBtn.disabled = true;

  appendUserBubble(text);
  appendTyping();

  try {
    const body = {
      message: text,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    };
    if (storedContext) body.previous_context = storedContext;

    const res  = await fetch(`${API}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();

    data._parsed = data.context?.previous_json || {};

    if (data.action === "follow_up_questions") {
      storedContext = data.context;
    } else {
      storedContext = null;
    }

    appendBotBubble(data);
  } catch (err) {
    document.getElementById("typing")?.remove();
    const row = document.createElement("div");
    row.className = "message-row bot";
    row.innerHTML = `<div class="bubble" style="color:#dc2626;font-size:13px;">⚠ Could not connect to server.</div>`;
    chatEl.appendChild(row);
    scrollBot();
  }

  sendBtn.disabled = false;
  msgEl.focus();
}

function scrollBot() {
  chatEl.scrollTop = chatEl.scrollHeight;
}

// ── DETAIL PANEL ──────────────────────────────────────────────
function openPanel(data) {
  const parsed   = data._parsed || {};
  const entities = parsed.entities || {};
  const body     = document.getElementById("panel-body");
  const conf     = Math.round((parsed.confidence || 0) * 100);

  const entityRows = Object.entries(entities).map(([k, v]) => {
    let display;
    if (v === null || v === undefined || v === "") {
      display = `<span class="kv-val null">null</span>`;
    } else if (Array.isArray(v)) {
      display = `<span class="kv-val">${v.join(", ") || "—"}</span>`;
    } else {
      display = `<span class="kv-val">${escHtml(String(v))}</span>`;
    }
    return `<span class="kv-key">${escHtml(k)}</span>${display}`;
  }).join("");

  body.innerHTML = `
    <div class="detail-section">
      <h3>Routing</h3>
      <div class="kv-grid">
        <span class="kv-key">action</span>
        <span class="kv-val"><span class="route-badge ${data.action}">${(data.action || "").replace(/_/g, " ")}</span></span>
        <span class="kv-key">reason</span>
        <span class="kv-val">${escHtml(data.reason || "—")}</span>
      </div>
    </div>

    <div class="detail-section">
      <h3>Intent</h3>
      <div class="kv-grid">
        <span class="kv-key">intent</span>
        <span class="kv-val">${escHtml((parsed.intent || "—").replace(/_/g, " "))}</span>
        <span class="kv-key">reasoning</span>
        <span class="kv-val">${escHtml(parsed.reasoning || "—")}</span>
      </div>
    </div>

    <div class="detail-section">
      <h3>Confidence</h3>
      <div class="confidence-bar-wrap">
        <div class="confidence-bar">
          <div class="confidence-fill" style="width:${conf}%"></div>
        </div>
        <span class="confidence-label">${conf}%</span>
      </div>
    </div>

    <div class="detail-section">
      <h3>Entities</h3>
      <div class="kv-grid">${entityRows || '<span class="kv-val null" style="grid-column:span 2">none extracted</span>'}</div>
    </div>

    ${data.follow_up_questions?.length ? `
    <div class="detail-section">
      <h3>Follow-up Questions</h3>
      <ul class="follow-up-list">
        ${data.follow_up_questions.map(q => `<li>${escHtml(q)}</li>`).join("")}
      </ul>
    </div>` : ""}
  `;

  document.getElementById("panel-overlay").classList.add("open");
}

function closePanel(e) {
  if (e && e.target !== document.getElementById("panel-overlay")) return;
  document.getElementById("panel-overlay").classList.remove("open");
}

// ── UTILS ──────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
function escAttr(str) {
  return str.replace(/'/g, "&apos;");
}