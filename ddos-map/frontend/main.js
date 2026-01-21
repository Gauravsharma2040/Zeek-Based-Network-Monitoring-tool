import "./style.css";

window.addEventListener("DOMContentLoaded", () => {
  const map = L.map("map").setView([20, 0], 2);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const ws = new WebSocket("ws://127.0.0.1:8000/ws/events");

  ws.onopen = () => {
    console.log("Connected to backend");
  };

  const markers = [];
  let totalEvents = 0;

  function addMarker(marker) {
    markers.push(marker);
    if (markers.length > 1000) {
      map.removeLayer(markers.shift());
    }
  }

  ws.onmessage = (msg) => {
    const e = JSON.parse(msg.data);
    if (e.lat == null || e.lon == null) return;

    totalEvents++;
    document.getElementById("total").textContent = totalEvents;

    const color = e.proto === 6 ? "green" : "orange";

    const marker = L.circleMarker([e.lat, e.lon], {
      radius: 5,
      color,
      fillOpacity: 0.7,
    }).addTo(map);

    addMarker(marker);
  };

  ws.onerror = (err) => {
    console.error("WebSocket error", err);
  };
});
