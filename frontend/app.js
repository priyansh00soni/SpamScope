// some ready-made emails so user can test quickly without typing
const SAMPLES = [
  {
    label: "Spam — prize scam",
    subject: "YOU WON $1,000,000!!!",
    body: "Congratulations!! You have been SELECTED as our LUCKY winner! Click here NOW to claim your prize: http://bit.ly/win-prize. Act immediately! This offer expires TODAY!!! Don't miss out on your FREE cash reward!!!"
  },
  {
    label: "Ham — work email",
    subject: "Team standup tomorrow at 2pm",
    body: "Hi everyone, just a reminder about our weekly standup tomorrow at 2pm in Conference Room B. Please bring your status updates. Thanks, Sarah"
  },
  {
    label: "Spam — phishing",
    subject: "URGENT: Your account has been suspended",
    body: "Dear Customer, your bank account has been locked due to unusual activity. Please verify your login details immediately at http://secure-update.xyz to avoid permanent suspension."
  },
  {
    label: "Ham — colleague",
    subject: "Re: Project proposal feedback",
    body: "Hi John, I reviewed your proposal. The timeline looks fine but let's discuss budget. Can we set up a call this week? Best, Alex"
  }
];

// words that are commonly seen in spam emails
// this is our "cheap brain" for detecting spam
const SPAM_WORDS = [
  "free", "win", "winner", "urgent", "cash", "prize", "click here",
  "act now", "limited", "guarantee", "congratulations", "selected",
  "claim", "verify", "suspended", "million", "earn", "loan",
  "discount", "dear customer", "dear user", "dear member", "password"
];

// grabbing all required elements from HTML once (so we don’t repeat later)
const subjectEl     = document.getElementById("subject");
const bodyEl        = document.getElementById("body");
const btnCheck      = document.getElementById("btn-check");
const btnClear      = document.getElementById("btn-clear");
const resultEl      = document.getElementById("result");
const signalsEl     = document.getElementById("signals");
const signalsListEl = document.getElementById("signals-list");
const sampleBtns    = document.getElementById("sample-btns");
const historyEl     = document.getElementById("history");
const historyBody   = document.getElementById("history-body");
const apiNotice     = document.getElementById("api-notice");

// stores last few checks (for history table)
let checks = [];

// create buttons for sample emails dynamically
// so we don’t hardcode buttons in HTML
SAMPLES.forEach(s => {
  const btn = document.createElement("button");
  btn.textContent = s.label;

  // when clicked → fill subject & body automatically
  btn.addEventListener("click", () => {
    subjectEl.value = s.subject;
    bodyEl.value    = s.body;
    clearResult(); // reset old result
  });

  sampleBtns.appendChild(btn);
});


// ---------------- CORE LOGIC ----------------
// this is fallback when backend is not working
// basically a "rule-based spam detector"
function clientPredict(subject, body) {

  // combine subject + body for easier processing
  const text  = (subject + " " + body).toLowerCase();

  // check how many spam words are present
  const hits  = SPAM_WORDS.filter(w => text.includes(w));

  // remove non-letters → helps calculate uppercase ratio
  const alpha = (subject + body).replace(/[^a-zA-Z]/g, "");

  // percentage of uppercase letters (spam mails shout a lot 😄)
  const caps  = alpha.length
    ? alpha.split("").filter(c => c === c.toUpperCase()).length / alpha.length
    : 0;

  // count "!" → too many = suspicious
  const excl  = (subject + body).split("!").length - 1;

  // count links → spam usually has links
  const urls  = (body.match(/https?:\/\/\S+|www\.\S+/g) || []).length;

  // simple scoring system (not ML, just logic)
  const score = hits.length * 0.15 + caps * 0.4 + excl * 0.05 + urls * 0.1;

  // threshold → above this = spam
  const isSpam = score > 0.35;

  // confidence is just adjusted based on score
  const conf  = Math.min(0.99, Math.max(0.52,
    isSpam ? 0.55 + score * 0.3 : 0.85 - score * 0.5
  ));

  // reasons to show user "why it's spam"
  const flags = [];

  if (caps > 0.35)
    flags.push(`${Math.round(caps * 100)}% of letters are uppercase`);

  if (excl >= 3)
    flags.push(`${excl} exclamation marks`);

  if (urls >= 2)
    flags.push(`${urls} URLs in the body`);

  if (hits.length >= 2)
    flags.push(`contains words like: ${hits.slice(0, 4).join(", ")}`);

  if (/dear (customer|user|member)/i.test(text))
    flags.push("generic greeting (Dear Customer / User)");

  return {
    verdict: isSpam ? "spam" : "ham",
    confidence: parseFloat(conf.toFixed(2)),
    triggered_features: flags
  };
}


// shows result on UI
function showResult(data) {
  const isSpam = data.verdict === "spam";

  // update result box styling
  resultEl.className = "result " + data.verdict;

  // show result text
  resultEl.innerHTML = `
    <div class="label">Result</div>
    <div class="verdict">${isSpam ? "Looks like spam" : "Looks legitimate"}</div>
    <div class="conf">${Math.round(data.confidence * 100)}% confidence</div>
  `;

  resultEl.classList.remove("hidden");

  // show reasons (signals)
  signalsListEl.innerHTML = "";

  if (data.triggered_features && data.triggered_features.length > 0) {
    data.triggered_features.forEach(f => {
      const li = document.createElement("li");
      li.textContent = f;
      signalsListEl.appendChild(li);
    });
    signalsEl.classList.remove("hidden");
  } else {
    signalsEl.classList.add("hidden");
  }
}


// keeps last few checks in a table
function addToHistory(subject, data) {

  // add new entry at top
  checks.unshift({ subject: subject || "(no subject)", data });

  // keep only last 8 entries
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

  historyEl.classList.remove("hidden");
}


// clears UI when new input is given
function clearResult() {
  resultEl.className = "result hidden";
  resultEl.innerHTML = "";
  signalsEl.classList.add("hidden");
  apiNotice.classList.add("hidden");
}


// main function when user clicks "Check email"
async function runCheck() {

  const subject = subjectEl.value.trim();
  const body    = bodyEl.value.trim();

  // don’t run if both empty
  if (!subject && !body) return;

  btnCheck.textContent = "Checking...";
  btnCheck.disabled    = true;

  clearResult();

  let data;

  try {
    // try calling backend API
    const res = await fetch("http://127.0.0.1:5000/api/detect", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ subject, body })
    });

    if (!res.ok) throw new Error();

    data = await res.json();

  } catch {
    // if backend fails → fallback to client model
    apiNotice.classList.remove("hidden");
    data = clientPredict(subject, body);
  }

  showResult(data);
  addToHistory(subject, data);

  btnCheck.textContent = "Check email";
  btnCheck.disabled    = false;
}


// prevent HTML injection (basic safety)
function escHtml(str) {
  return str.replace(/&/g,"&amp;")
            .replace(/</g,"&lt;")
            .replace(/>/g,"&gt;");
}


// ---------------- EVENTS ----------------

// button click
btnCheck.addEventListener("click", runCheck);

// clear button
btnClear.addEventListener("click", () => {
  subjectEl.value = "";
  bodyEl.value    = "";
  clearResult();
});

// press Enter in subject → run check
subjectEl.addEventListener("keydown", e => {
  if (e.key === "Enter") runCheck();
});