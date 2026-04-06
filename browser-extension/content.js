const API_URL = "http://localhost:8000/predict";
const currentURL = window.location.href;

// Skip internal browser pages
if (!currentURL.startsWith("chrome://") && 
    !currentURL.startsWith("chrome-extension://") &&
    !currentURL.startsWith("about:")) {

  fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: currentURL, model: "stack" })
  })
  .then(res => res.json())
  .then(data => {
    if (data.is_phishing && Number(data.confidence) >= 90) {
      showWarningOverlay(currentURL, data.confidence);
    } else if (data.is_phishing) {
      showSoftWarningBanner(currentURL, data.confidence);
    }
  })
  .catch(() => {
    // Silently fail if API is not running
  });
}

function showSoftWarningBanner(url, confidence) {
  if (document.getElementById("phishvision-soft-warning")) {
    return;
  }

  const banner = document.createElement("div");
  banner.id = "phishvision-soft-warning";
  banner.innerHTML = `
    <div style="
      position: fixed;
      top: 12px;
      right: 12px;
      max-width: 420px;
      background: #1a1a2e;
      border: 1px solid #dc3545;
      border-left: 4px solid #dc3545;
      border-radius: 10px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      z-index: 999999;
      color: #fff;
      font-family: Segoe UI, sans-serif;
      padding: 12px 14px;
    ">
      <div style="font-weight: 700; font-size: 13px; color: #ff6b6b; margin-bottom: 4px;">
        PhishVision Warning
      </div>
      <div style="font-size: 12px; color: #ddd; line-height: 1.4;">
        Suspicious URL indicators detected (${confidence}% confidence). Proceed with caution.
      </div>
      <div style="
        margin-top: 8px;
        font-size: 11px;
        color: #aaa;
        word-break: break-all;
      ">${url}</div>
      <button id="phishvision-soft-close" style="
        margin-top: 10px;
        background: transparent;
        border: 1px solid #ff6b6b;
        color: #ff6b6b;
        border-radius: 6px;
        font-size: 11px;
        padding: 5px 10px;
        cursor: pointer;
      ">Dismiss</button>
    </div>
  `;

  document.documentElement.appendChild(banner);
  const closeBtn = document.getElementById("phishvision-soft-close");
  if (closeBtn) {
    closeBtn.addEventListener("click", () => banner.remove());
  }
}

function showWarningOverlay(url, confidence) {
  // Block the page
  document.body.style.display = "none";

  const overlay = document.createElement("div");
  overlay.id = "phishvision-overlay";
  overlay.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0;
      width: 100vw; height: 100vh;
      background: #0f0f1a;
      display: flex; align-items: center;
      justify-content: center;
      z-index: 999999;
      font-family: Segoe UI, sans-serif;
    ">
      <div style="
        background: #1a1a2e;
        border: 2px solid #dc3545;
        border-radius: 16px;
        padding: 40px;
        max-width: 520px;
        text-align: center;
        box-shadow: 0 0 60px rgba(220,53,69,0.3);
      ">
        <div style="font-size: 64px; margin-bottom: 16px;">🚨</div>

        <h1 style="color: #dc3545; font-size: 26px; margin-bottom: 10px;">
          PHISHING WEBSITE DETECTED
        </h1>

        <p style="color: #aaa; font-size: 14px; margin-bottom: 20px; line-height: 1.6;">
          PhishVision AI has blocked this page with
          <strong style="color:#fff">${confidence}% confidence</strong>.
          This site may be attempting to steal your credentials or personal data.
        </p>

        <div style="
          background: #0f0f1a;
          border-radius: 8px;
          padding: 10px 14px;
          margin-bottom: 24px;
          word-break: break-all;
          font-size: 11px;
          color: #dc3545;
          border: 1px solid #2a2a4a;
        ">${url}</div>

        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
          <button onclick="window.history.back()" style="
            padding: 12px 28px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
          ">← Go Back (Safe)</button>

          <button onclick="
            document.getElementById('phishvision-overlay').remove();
            document.body.style.display='';
          " style="
            padding: 12px 28px;
            background: transparent;
            color: #dc3545;
            border: 2px solid #dc3545;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
          ">Proceed Anyway (Risk)</button>
        </div>

        <p style="color: #444; font-size: 11px; margin-top: 20px;">
          PhishVision AI v1.0 — Powered by Machine Learning
        </p>
      </div>
    </div>
  `;

  document.documentElement.appendChild(overlay);
}