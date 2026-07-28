const API = ""; // same origin
const POLL_MS = 6000;

const map = L.map("map", { zoomControl: true, attributionControl: false })
  .setView([12.9716, 77.5946], 11.3);

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
  maxZoom: 19,
}).addTo(map);

const areaMarkers = {};       // name -> L.marker
const hotspotMarkers = {};    // name -> L.marker
const corridorLines = {};     // "origin|dest" -> { r1: polyline, r2: polyline }

function bandDivIcon(className, band) {
  return L.divIcon({
    className: "",
    html: `<div class="${className} ${band || ""}"></div>`,
    iconSize: [14, 14],
  });
}

async function fetchJSON(url) {
  const res = await fetch(API + url);
  if (!res.ok) throw new Error(`${url} -> ${res.status}`);
  return res.json();
}

function setLive(ok) {
  const pill = document.getElementById("live-pill");
  const label = document.getElementById("live-label");
  if (ok) {
    pill.classList.remove("stale");
    label.textContent = "LIVE";
  } else {
    pill.classList.add("stale");
    label.textContent = "OFFLINE";
  }
}

function tickClock() {
  const now = new Date();
  document.getElementById("clock").textContent = now.toLocaleTimeString("en-GB");
}
setInterval(tickClock, 1000);
tickClock();

// ---------------- Static markers (areas + hotspots) ----------------

async function initAreas() {
  const data = await fetchJSON("/api/areas");

  data.areas.forEach((a) => {
    const m = L.marker([a.lat, a.lng], { icon: bandDivIcon("area-marker") })
      .addTo(map)
      .bindPopup(`<strong>${a.name}</strong><br/>Origin/destination area`);
    areaMarkers[a.name] = m;
  });

  data.hotspots.forEach((h) => {
    const m = L.marker([h.lat, h.lng], { icon: bandDivIcon("hotspot-marker", "green") })
      .addTo(map)
      .bindPopup(`<strong>${h.name}</strong><br/>Congestion hotspot`);
    hotspotMarkers[h.name] = m;
  });
}

// ---------------- OD dropdowns ----------------

async function initPairs() {
  const pairs = await fetchJSON("/api/pairs");
  const originSel = document.getElementById("origin-select");
  const destSel = document.getElementById("destination-select");

  const origins = [...new Set(pairs.map((p) => p.origin_area))].sort();
  origins.forEach((o) => {
    const opt = document.createElement("option");
    opt.value = o;
    opt.textContent = o;
    originSel.appendChild(opt);
  });

  function refreshDestinations() {
    destSel.innerHTML = "";
    const dests = pairs
      .filter((p) => p.origin_area === originSel.value)
      .map((p) => p.destination_area)
      .sort();
    dests.forEach((d) => {
      const opt = document.createElement("option");
      opt.value = d;
      opt.textContent = d;
      destSel.appendChild(opt);
    });
  }

  originSel.addEventListener("change", refreshDestinations);
  refreshDestinations();
}

// ---------------- Prediction ----------------

function renderPrediction(result) {
  document.getElementById("result-block").hidden = false;

  document.getElementById("rec-banner").innerHTML =
    `<strong>${result.recommended_route}</strong> saves ~${result.time_saved_min} min ` +
    `vs. the alternate route right now.`;

  const compare = document.getElementById("route-compare");
  compare.innerHTML = "";
  [result.route_1, result.route_2].forEach((r) => {
    const picked = r.name === result.recommended_route;
    const div = document.createElement("div");
    div.className = `route-card ${r.band.code} ${picked ? "picked" : ""}`;
    div.innerHTML = `
      <div class="r-name"><span>${r.band.emoji} ${r.name}</span>
        <span class="r-time">${r.predicted_time_min} min</span></div>
      <div class="r-meta">${r.dist_km} km · base ${r.base_time_min} min · bottleneck: ${r.hotspot}</div>
    `;
    compare.appendChild(div);
  });

  document.getElementById("alert-text").textContent = result.alert;

  // Fly to and draw the corridor
  if (result.origin_coords && result.destination_coords) {
    const bounds = L.latLngBounds([result.origin_coords, result.destination_coords]);
    map.fitBounds(bounds.pad(0.35));
  }
}

async function runPrediction() {
  const origin = document.getElementById("origin-select").value;
  const destination = document.getElementById("destination-select").value;
  if (!origin || !destination) return;

  const btn = document.getElementById("predict-btn");
  btn.disabled = true;
  btn.textContent = "Predicting…";
  try {
    const result = await fetchJSON(
      `/api/predict?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`
    );
    renderPrediction(result);
    await refreshActivity();
  } catch (e) {
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.textContent = "Predict Clearance";
  }
}

document.getElementById("predict-btn").addEventListener("click", runPrediction);

// ---------------- Live dashboard snapshot ----------------

async function refreshLiveSnapshot() {
  try {
    const data = await fetchJSON("/api/dashboard/live");
    setLive(true);

    document.getElementById("corridor-count").textContent =
      `${data.count} corridors tracked`;
    document.getElementById("last-updated").textContent =
      `updated ${new Date().toLocaleTimeString("en-GB")}`;

    data.corridors.forEach((c) => {
      // worst band between the two routes drives the hotspot marker color
      const worseBand = rankBand(c.route_1.band.code) >= rankBand(c.route_2.band.code)
        ? c.route_1.band.code
        : c.route_2.band.code;

      if (hotspotMarkers[c.bottleneck]) {
        hotspotMarkers[c.bottleneck].setIcon(bandDivIcon("hotspot-marker", worseBand));
        hotspotMarkers[c.bottleneck].setPopupContent(
          `<strong>${c.bottleneck}</strong><br/>Bottleneck on ${c.origin} → ${c.destination}`
        );
      }

      drawCorridor(c);
    });
  } catch (e) {
    console.error(e);
    setLive(false);
  }
}

function rankBand(code) {
  return { blue: 0, green: 1, yellow: 2, red: 3 }[code] ?? 1;
}

function bandColor(code) {
  return { blue: "#3B82F6", green: "#22C55E", yellow: "#EAB308", red: "#EF4444" }[code] || "#8B98AC";
}

function drawCorridor(c) {
  const key = `${c.origin}|${c.destination}`;
  if (!c.origin_coords || !c.destination_coords) return;

  const existing = corridorLines[key];
  const color = bandColor(
    rankBand(c.route_1.band.code) >= rankBand(c.route_2.band.code)
      ? c.route_1.band.code
      : c.route_2.band.code
  );

  if (existing) {
    existing.setStyle({ color });
  } else {
    const line = L.polyline([c.origin_coords, c.destination_coords], {
      color,
      weight: 2,
      opacity: 0.55,
      dashArray: "4 5",
    }).addTo(map);
    corridorLines[key] = line;
  }
}

// ---------------- Recent activity feed ----------------

async function refreshActivity() {
  try {
    const rows = await fetchJSON("/api/predictions/recent?limit=15");
    const body = document.getElementById("activity-body");
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="4" class="empty-row">No predictions yet</td></tr>`;
      return;
    }
    body.innerHTML = rows
      .map((r) => {
        const band = rankBand(r.route_1_band) >= rankBand(r.route_2_band) ? r.route_1_band : r.route_2_band;
        const t = new Date(r.created_at).toLocaleTimeString("en-GB");
        return `<tr>
          <td><span class="band-chip ${band}"></span>${r.origin_area} → ${r.destination_area}</td>
          <td>${r.recommended_route}</td>
          <td>${r.time_saved_min} min</td>
          <td>${t}</td>
        </tr>`;
      })
      .join("");
  } catch (e) {
    console.error(e);
  }
}

// ---------------- Boot ----------------

(async function init() {
  await initAreas();
  await initPairs();
  await refreshLiveSnapshot();
  await refreshActivity();

  setInterval(refreshLiveSnapshot, POLL_MS);
  setInterval(refreshActivity, POLL_MS);
})();
