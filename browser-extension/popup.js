const API_URL = "http://localhost:8000/predict";

// Get current tab URL and display it
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const url = tabs[0].url;
  document.getElementById("currentUrl").textContent = url;
  document.getElementById("scanBtn").dataset.url = url;
});

// Scan button click
document.getElementById("scanBtn").addEventListener("click", async () => {
  const url = document.getElementById("scanBtn").dataset.url;
  const model = document.getElementById("modelSelect").value;

  if (!url) return;

  // Show loading
  document.getElementById("loading").style.display = "block";
  document.getElementById("resultBox").style.display = "none";
  document.getElementById("scanBtn").disabled = true;

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url, model: model })
    });

    const data = await response.json();

    // Hide loading
    document.getElementById("loading").style.display = "none";
    document.getElementById("scanBtn").disabled = false;

    const resultBox = document.getElementById("resultBox");
    const resultTitle = document.getElementById("resultTitle");
    const resultMsg = document.getElementById("resultMsg");
    const confBar = document.getElementById("confBar");
    const confLabel = document.getElementById("confLabel");

    resultBox.style.display = "block";

    if (data.is_phishing) {
      resultBox.className = "result-box result-phishing";
      resultTitle.className = "result-title phishing-text";
      resultTitle.textContent = "⚠️ PHISHING DETECTED";
      resultMsg.textContent = "This URL matches known malicious patterns. Do not enter any credentials.";
      confBar.style.background = "#dc3545";
    } else {
      resultBox.className = "result-box result-safe";
      resultTitle.className = "result-title safe-text";
      resultTitle.textContent = "✅ SAFE — LEGITIMATE";
      resultMsg.textContent = "This URL appears to be safe based on ML analysis.";
      confBar.style.background = "#28a745";
    }

    confBar.style.width = data.confidence + "%";
    confLabel.textContent = `Confidence: ${data.confidence}%  |  Model: ${data.model_used.toUpperCase()}`;

  } catch (err) {
    document.getElementById("loading").style.display = "none";
    document.getElementById("scanBtn").disabled = false;
    const resultBox = document.getElementById("resultBox");
    resultBox.style.display = "block";
    resultBox.className = "result-box result-phishing";
    document.getElementById("resultTitle").textContent = "❌ API Connection Error";
    document.getElementById("resultMsg").textContent = "Make sure FastAPI server is running on port 8000.";
  }
});