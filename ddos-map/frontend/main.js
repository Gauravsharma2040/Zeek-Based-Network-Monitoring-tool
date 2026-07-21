import "./style.css";
import { initChart } from "./src/analytics.js";

const backend = import.meta.env.VITE_API_URL || `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:8000`;
const apiToken = import.meta.env.VITE_API_TOKEN || "";
const authQuery = apiToken ? `?token=${encodeURIComponent(apiToken)}` : "";
const ids = { total_events: "total", ddos_events: "ddos", normal_events: "normal", anomaly_events: "anomaly", ml_anomaly_events: "ml-anomaly", events_per_second: "eps" };
let latestEvent = null;

function setStatus(text, state) { const status = document.querySelector("#status"); status.textContent = text; status.dataset.state = state; }
async function refreshMetrics() {
  try {
    const response = await fetch(`${backend.replace(/^ws/, "http")}/metrics${authQuery}`);
    const data = await response.json();
    Object.entries(ids).forEach(([key, id]) => { document.getElementById(id).textContent = data[key] ?? 0; });
    // Update analytics chart with events per second
    if (typeof initChart === "function") {
      // Ensure chart is initialized once
      if (!window.__analyticsChart) {
        window.__analyticsChart = initChart();
      }
      window.__analyticsChart.updateChart(data.events_per_second ?? 0);
    }
    document.getElementById("protocols").textContent = Object.entries(data.protocols || {}).map(([name, count]) => `${name.toUpperCase()}: ${count}`).join("  ·  ") || "No traffic yet";
    const model = await (await fetch(`${backend.replace(/^ws/, "http")}/model${authQuery}`)).json();
    document.getElementById("model-status").textContent = model.ready ? `Behavior baseline active (${model.samples} samples)` : `Baseline learning: ${model.samples}/${model.min_samples} samples`;
  } catch { /* Connection status is handled by the socket. */ }
}
function showEvent(event) {
  latestEvent = event;
  const severity = event.label === "ddos" ? "Possible DDoS rate burst" : event.ml_anomaly ? "Behavioral baseline anomaly" : event.anomaly ? "Usage anomaly" : "Normal network activity";
  document.getElementById("incident-title").textContent = severity;
  document.getElementById("incident-summary").textContent = `${event.src} -> ${event.dst} on ${event.proto.toUpperCase()}/${event.port}${event.reason ? ` (${event.reason})` : ""}.`;
  document.getElementById("explain-button").disabled = !event.anomaly;
  document.getElementById("ai-explanation").textContent = "";
}
async function startDemo() {
  const button = document.getElementById("demo-button");
  button.disabled = true;
  try {
    const response = await fetch(`${backend.replace(/^ws/, "http")}/demo/start${authQuery}`, { method: "POST" });
    const data = await response.json();
    button.textContent = data.started ? "Demo running..." : data.message;
  } catch { button.textContent = "Demo unavailable"; }
  setTimeout(() => { button.disabled = false; button.textContent = "Run showcase demo"; }, 6000);
}
async function explainLatest() {
  if (!latestEvent) return;
  const output = document.getElementById("ai-explanation");
  output.textContent = "Generating investigation summary...";
  try {
    const response = await fetch(`${backend.replace(/^ws/, "http")}/explain${authQuery}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(latestEvent) });
    const data = await response.json();
    output.textContent = response.ok ? data.explanation : (data.detail || "Explanation unavailable.");
  } catch { output.textContent = "Explanation unavailable. Check the receiver connection."; }
}
document.getElementById("demo-button").addEventListener("click", startDemo);
document.getElementById("explain-button").addEventListener("click", explainLatest);
let reconnectDelay = 1000;
function connect() {
  const ws = new WebSocket(`${backend}/ws/events${authQuery}`);
  ws.onopen = () => { reconnectDelay = 1000; setStatus("Live", "live"); refreshMetrics(); };
  ws.onmessage = (message) => { showEvent(JSON.parse(message.data)); refreshMetrics(); };
  ws.onclose = () => { setStatus("Reconnecting...", "offline"); setTimeout(connect, reconnectDelay); reconnectDelay = Math.min(reconnectDelay * 2, 10000); };
  ws.onerror = () => ws.close();
}
connect();
refreshMetrics();
setInterval(refreshMetrics, 5000);
