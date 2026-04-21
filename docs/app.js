const SAMPLES = [
  {
    label: "Spam: prize scam",
    subject: "YOU WON ₹1,000,000!!!",
    body: "Congratulations!! You have been SELECTED as our LUCKY winner! Click here NOW to claim your prize: http://bit.ly/win-prize. Act immediately! This offer expires TODAY!!! Don't miss out on your FREE cash reward!!!"
  },
  {
    label: "Ham: work email",
    subject: "Team standup tomorrow at 2pm",
    body: "Hi everyone, just a reminder about our weekly standup tomorrow at 2pm in Conference Room B. Please bring your status updates. Thanks, Sarah"
  },
  {
    label: "Spam: phishing",
    subject: "URGENT: Your account has been suspended",
    body: "Dear Customer, your bank account has been locked due to unusual activity. Please verify your login details immediately at http://secure-update.xyz to avoid permanent suspension."
  },
  {
    label: "Ham: colleague",
    subject: "Re: Project proposal feedback",
    body: "Hi Ramesh, I reviewed your proposal. The timeline looks fine but let's discuss budget. Can we set up a call this week? Best, Alex"
  }
];

const SPAM_WORDS = [
  "free", "win", "winner", "urgent", "cash", "prize", "click here",
  "act now", "limited", "guarantee", "congratulations", "selected",
  "claim", "verify", "suspended", "million", "earn", "loan",
  "discount", "dear customer", "dear user", "dear member", "password"
];

// dom refs
const subjectEl    = document.getElementById("subject");
const bodyEl       = document.getElementById("body");
const btnCheck     = document.getElementById("btn-check");
const btnLabel     = document.getElementById("btn-label");
const btnClear     = document.getElementById("btn-clear");
const idleState    = document.getElementById("idle-state");
const resultState  = document.getElementById("result-state");
const verdictCard  = document.getElementById("verdict-card");
const verdictEye   = document.getElementById("verdict-eyebrow");
const verdictHead  = document.getElementById("verdict-headline");
const verdictDesc  = document.getElementById("verdict-desc");
const confPct      = document.getElementById("conf-pct");
const confBar      = document.getElementById("conf-bar");
const signalsCard  = document.getElementById("signals-card");
const signalsList  = document.getElementById("signals-list");
const sampleBtns   = document.getElementById("sample-btns");
const historyCard  = document.getElementById("history-card");
const historyBody  = document.getElementById("history-body");
const apiNotice    = document.getElementById("api-notice");

let checks = [];

// build sample buttons
SAMPLES.forEach(s => {
  const btn = document.createElement("button");
  btn.textContent = s.label;
  btn.addEventListener("click", () => {
    subjectEl.value = s.subject;
    bodyEl.value    = s.body;
    clearResult();
  });
  sampleBtns.appendChild(btn);
});

// fallback client-side model (used when backend is offline)
function clientPredict(subject, body) {
  const text   = (subject + " " + body).toLowerCase();
  const hits   = SPAM_WORDS.filter(w => text.includes(w));
  const alpha  = (subject + body).replace(/[^a-zA-Z]/g, "");
  const caps   = alpha.length
    ? alpha.split("").filter(c => c === c.toUpperCase()).length / alpha.length
    : 0;
  const excl   = (subject + body).split("!").length - 1;
  const urls   = (body.match(/https?:\/\/\S+|www\.\S+/g) || []).length;
  const score  = hits.length * 0.15 + caps * 0.4 + excl * 0.05 + urls * 0.1;
  const isSpam = score > 0.35;
  const conf   = Math.min(0.99, Math.max(0.52,
    isSpam ? 0.55 + score * 0.3 : 0.85 - score * 0.5
  ));

  const flags = [];
  if (caps > 0.35)      flags.push(`${Math.round(caps * 100)}% of letters are uppercase`);
  if (excl >= 3)        flags.push(`${excl} exclamation marks detected`);
  if (urls >= 2)        flags.push(`${urls} URLs found in body`);
  if (hits.length >= 2) flags.push(`Spam keywords found: ${hits.slice(0, 4).join(", ")}`);
  if (/dear (customer|user|member)/i.test(text)) flags.push("Generic greeting — Dear Customer / User");

  return {
    verdict: isSpam ? "spam" : "ham",
    confidence: parseFloat(conf.toFixed(2)),
    triggered_features: flags
  };
}

// render classification result
function showResult(data) {
  const isSpam = data.verdict === "spam";
  const pct    = Math.round(data.confidence * 100);

  // switch idle → result
  idleState.classList.add("hidden");
  resultState.classList.remove("hidden");

  // verdict card
  verdictCard.className = "panel verdict-card " + (isSpam ? "is-spam" : "is-ham");
  verdictEye.textContent  = isSpam ? "⚠  Spam detected" : "✓  Looks legitimate";
  verdictHead.textContent = isSpam ? "This is spam." : "Not spam.";
  verdictDesc.textContent = isSpam
    ? "This email contains suspicious patterns consistent with spam."
    : "This email appears to be a legitimate message.";

  // confidence bar, reset then animate
  confPct.textContent  = pct + "%";
  confBar.style.width  = "0%";
  requestAnimationFrame(() => requestAnimationFrame(() => {
    confBar.style.width = pct + "%";
  }));

  // signals
  signalsList.innerHTML = "";
  if (data.triggered_features && data.triggered_features.length > 0) {
    data.triggered_features.forEach(f => {
      const li = document.createElement("li");
      li.textContent = f;
      signalsList.appendChild(li);
    });
    signalsCard.classList.remove("hidden");
  } else {
    signalsCard.classList.add("hidden");
  }
}

// add row to history
function addToHistory(subject, data) {
  checks.unshift({ subject: subject || "(no subject)", data });
  if (checks.length > 8) checks.pop();

  historyBody.innerHTML = "";
  checks.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td title="${escHtml(c.subject)}">${escHtml(c.subject)}</td>
      <td><span class="tag ${c.data.verdict}">${c.data.verdict}</span></td>
      <td>${Math.round(c.data.confidence * 100)}%</td>
    `;
    historyBody.appendChild(tr);
  });
  historyCard.classList.remove("hidden");
}

function clearResult() {
  idleState.classList.remove("hidden");
  resultState.classList.add("hidden");
  signalsCard.classList.add("hidden");
  apiNotice.classList.add("hidden");
  confBar.style.width = "0%";
}

async function runCheck() {
  const subject = subjectEl.value.trim();
  const body    = bodyEl.value.trim();
  if (!subject && !body) return;

  btnLabel.textContent = "Analyzing...";
  btnCheck.disabled    = true;
  clearResult();

  let data;
  try {
    const res = await fetch("http://127.0.0.1:5000/api/detect", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ subject, body })
    });
    if (!res.ok) throw new Error();
    data = await res.json();
  } catch {
    apiNotice.classList.remove("hidden");
    data = clientPredict(subject, body);
  }

  showResult(data);
  addToHistory(subject, data);

  btnLabel.textContent = "Analyze email";
  btnCheck.disabled    = false;
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// events
btnCheck.addEventListener("click", runCheck);
btnClear.addEventListener("click", () => {
  subjectEl.value = "";
  bodyEl.value    = "";
  clearResult();
});
subjectEl.addEventListener("keydown", e => {
  if (e.key === "Enter") runCheck();
});
