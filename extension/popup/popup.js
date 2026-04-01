const API_BASE = "http://localhost:8000";
const FREE_DAILY_LIMIT = 3;
const STRIPE_CHECKOUT_URL = "";

let currentMode = "post";
let usageToday = 0;
let isPro = false;
let lastRequest = null;

document.addEventListener("DOMContentLoaded", async () => {
  setupTabs();
  setupButtons();
  await loadUserState();
  updateUI();
});

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      currentMode = tab.dataset.mode;
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll(".mode-panel").forEach((p) => p.classList.remove("active"));
      document.getElementById(`${currentMode}-mode`).classList.add("active");
      hideOutput();
      hideError();
    });
  });
}

function setupButtons() {
  document.getElementById("generate-post-btn").addEventListener("click", generatePost);
  document.getElementById("generate-reply-btn").addEventListener("click", generateReply);
  document.getElementById("copy-btn").addEventListener("click", copyToClipboard);
  document.getElementById("regen-btn").addEventListener("click", regenerate);
  document.getElementById("upgrade-btn")?.addEventListener("click", openUpgrade);
}

async function generatePost() {
  const topic = document.getElementById("topic").value.trim();
  if (!topic) {
    showError("Enter a topic first.");
    return;
  }
  if (!canGenerate()) {
    showUpgradePrompt();
    return;
  }
  lastRequest = {
    type: "post",
    topic,
    tone: document.getElementById("tone").value,
    length: document.getElementById("length").value,
  };
  await callAPI(lastRequest);
}

async function generateReply() {
  const originalPost = document.getElementById("original-post").value.trim();
  if (!originalPost) {
    showError("Paste the post you're replying to.");
    return;
  }
  if (!canGenerate()) {
    showUpgradePrompt();
    return;
  }
  lastRequest = {
    type: "reply",
    original_post: originalPost,
    angle: document.getElementById("reply-angle").value.trim(),
    tone: document.getElementById("reply-tone").value,
  };
  await callAPI(lastRequest);
}

async function regenerate() {
  if (lastRequest) {
    await callAPI(lastRequest);
  }
}

async function callAPI(request) {
  showLoading();
  hideOutput();
  hideError();
  hideUpgradePrompt();
  setButtonsDisabled(true);
  try {
    const response = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Something went wrong.");
    }
    const data = await response.json();
    showOutput(data.text);
    incrementUsage();
    updateUI();
  } catch (err) {
    showError(err.message || "Failed to connect to server. Is the backend running?");
  } finally {
    hideLoading();
    setButtonsDisabled(false);
  }
}

async function loadUserState() {
  const stored = await chrome.storage.local.get(["usageToday", "usageDate", "isPro"]);
  const today = new Date().toDateString();
  if (stored.usageDate === today) {
    usageToday = stored.usageToday || 0;
  } else {
    usageToday = 0;
    await chrome.storage.local.set({ usageToday: 0, usageDate: today });
  }
  isPro = stored.isPro || false;
}

function canGenerate() {
  return isPro || usageToday < FREE_DAILY_LIMIT;
}

async function incrementUsage() {
  if (!isPro) {
    usageToday++;
    await chrome.storage.local.set({
      usageToday,
      usageDate: new Date().toDateString(),
    });
  }
}

function updateUI() {
  const badge = document.getElementById("usage-badge");
  const planLabel = document.getElementById("plan-label");
  if (isPro) {
    badge.textContent = "Pro";
    badge.className = "usage-badge";
    planLabel.textContent = "Pro plan";
    planLabel.className = "plan-label pro";
  } else {
    const remaining = FREE_DAILY_LIMIT - usageToday;
    badge.textContent = `${remaining}/${FREE_DAILY_LIMIT} left`;
    if (remaining <= 0) {
      badge.className = "usage-badge out";
    } else if (remaining === 1) {
      badge.className = "usage-badge warning";
    } else {
      badge.className = "usage-badge";
    }
    planLabel.textContent = "Free plan";
    planLabel.className = "plan-label";
  }
}

function showOutput(text) {
  document.getElementById("output-text").textContent = text;
  document.getElementById("output-area").classList.remove("hidden");
}

function hideOutput() {
  document.getElementById("output-area").classList.add("hidden");
}

function showLoading() {
  document.getElementById("loading").classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loading").classList.add("hidden");
}

function showError(msg) {
  const el = document.getElementById("error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function hideError() {
  document.getElementById("error").classList.add("hidden");
}

function showUpgradePrompt() {
  document.getElementById("upgrade-prompt").classList.remove("hidden");
}

function hideUpgradePrompt() {
  document.getElementById("upgrade-prompt").classList.add("hidden");
}

function setButtonsDisabled(disabled) {
  document.getElementById("generate-post-btn").disabled = disabled;
  document.getElementById("generate-reply-btn").disabled = disabled;
}

async function copyToClipboard() {
  const text = document.getElementById("output-text").textContent;
  await navigator.clipboard.writeText(text);
  showToast("Copied!");
}

function openUpgrade() {
  if (STRIPE_CHECKOUT_URL) {
    chrome.tabs.create({ url: STRIPE_CHECKOUT_URL });
  } else {
    showError("Stripe checkout not configured yet.");
  }
}

function showToast(msg) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 1500);
}
