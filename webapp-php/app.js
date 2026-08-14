/*
 * Logika bersama semua halaman:
 * - proteksi login sederhana (sessionStorage)
 * - memuat data dari api.php
 * - komponen chart SVG tanpa library eksternal
 */

const COLORS = {
  pos: "#059669",
  neg: "#dc2626",
  neu: "#64748b",
  nb: "#2563eb",
  svm: "#ea580c",
  bar: "#2563eb",
  ink2: "#475569",
  muted: "#94a3b8",
  grid: "#e2e8f0",
};

/* ---------- Auth sederhana (untuk demonstrasi) ---------- */
function requireLogin() {
  if (sessionStorage.getItem("loggedIn") !== "true") {
    window.location.href = "index.html";
  }
}

function logout() {
  sessionStorage.removeItem("loggedIn");
  window.location.href = "index.html";
}

/* ---------- Data ---------- */
async function loadData() {
  const res = await fetch("api.php?action=data");
  if (!res.ok) {
    let msg = "Gagal memuat data dari api.php.";
    try { msg = (await res.json()).message || msg; } catch (e) { /* bukan JSON */ }
    throw new Error(msg);
  }
  return res.json();
}

function showLoadError(err) {
  const el = document.createElement("div");
  el.className = "panel";
  el.style.borderLeft = "4px solid " + COLORS.neg;
  el.innerHTML = "<h2>Gagal Memuat Data</h2><p>" + err.message + "</p>";
  document.querySelector(".container").prepend(el);
}

/* ---------- Menjalankan fase pipeline lewat api.php ---------- */
async function runPhase(phase, params, btn, logEl) {
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Memproses Pipeline...";
  if (logEl) { logEl.textContent = "Menjalankan fase " + phase + ", mohon tunggu..."; }
  try {
    const res = await fetch("api.php?action=run&phase=" + encodeURIComponent(phase), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params || {}),
    });
    const out = await res.json();
    if (logEl) logEl.textContent = out.log || out.message || "(tidak ada output)";
    return out.ok;
  } catch (e) {
    if (logEl) logEl.textContent = "Gagal terhubung ke server: " + e.message +
      "\nPastikan aplikasi dijalankan lewat server PHP (php -S localhost:8000 -t webapp-php).";
    return false;
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

/* ---------- Format ---------- */
const fmtPct = (v) => (v * 100).toFixed(2) + "%";

function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/* ---------- Donut chart (distribusi sentimen) ---------- */
function donutChart(el, items) {
  const total = items.reduce((s, d) => s + d.value, 0);
  if (!total) { el.textContent = "Belum ada data."; return; }

  const size = 240, cx = size / 2, cy = size / 2, r = 88, inner = 54;
  let angle = -Math.PI / 2;
  let paths = "";
  let labels = "";

  items.forEach((d) => {
    if (!d.value) return;
    const frac = d.value / total;
    const a0 = angle, a1 = angle + frac * 2 * Math.PI;
    angle = a1;
    const large = frac > 0.5 ? 1 : 0;
    const p0 = [cx + r * Math.cos(a0), cy + r * Math.sin(a0)];
    const p1 = [cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
    const q1 = [cx + inner * Math.cos(a1), cy + inner * Math.sin(a1)];
    const q0 = [cx + inner * Math.cos(a0), cy + inner * Math.sin(a0)];
    paths += `<path d="M${p0} A${r} ${r} 0 ${large} 1 ${p1} L${q1} A${inner} ${inner} 0 ${large} 0 ${q0} Z"
      fill="${d.color}" stroke="#ffffff" stroke-width="2.5">
      <title>${esc(d.label)}: ${d.value} tweet (${(frac * 100).toFixed(1)}%)</title></path>`;
    const mid = (a0 + a1) / 2, lr = (r + inner) / 2;
    if (frac > 0.06) {
      labels += `<text x="${cx + lr * Math.cos(mid)}" y="${cy + lr * Math.sin(mid)}"
        text-anchor="middle" dominant-baseline="middle" fill="#ffffff"
        font-size="12" font-weight="800">${(frac * 100).toFixed(0)}%</text>`;
    }
  });

  el.innerHTML = `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" role="img"
    aria-label="Distribusi sentimen">${paths}${labels}
    <text x="${cx}" y="${cy - 4}" text-anchor="middle" font-size="22" font-weight="800" fill="#0f172a">${total}</text>
    <text x="${cx}" y="${cy + 16}" text-anchor="middle" font-size="11" font-weight="600" fill="${COLORS.muted}">tweet</text></svg>`;
}

function renderLegend(el, items) {
  el.innerHTML = items.map((d) =>
    `<div class="item"><span class="swatch" style="background:${d.color}"></span>
     ${esc(d.label)}: <strong style="color:var(--ink)">&nbsp;${d.value}</strong>&nbsp;(${d.pct}%)</div>`).join("");
}

/* ---------- Grouped bar (perbandingan metrik NB vs SVM) ---------- */
function groupedBarChart(el, metricNames, series) {
  const W = 640, H = 300, padL = 48, padB = 40, padT = 20, padR = 12;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const groups = metricNames.length;
  const groupW = plotW / groups;
  const barW = Math.min(34, groupW / (series.length + 1));

  let bars = "", gl = "", xLabels = "";
  for (let i = 0; i <= 4; i++) {
    const v = i / 4, y = padT + plotH * (1 - v);
    gl += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="${COLORS.grid}" stroke-width="1"/>
      <text x="${padL - 8}" y="${y + 4}" text-anchor="end" font-size="11" fill="${COLORS.muted}">${(v * 100).toFixed(0)}%</text>`;
  }

  metricNames.forEach((m, gi) => {
    const gx = padL + gi * groupW + groupW / 2;
    series.forEach((s, si) => {
      const v = s.values[gi];
      const h = Math.max(plotH * v, v > 0 ? 2 : 0);
      const x = gx - (series.length * barW + (series.length - 1) * 3) / 2 + si * (barW + 3);
      const y = padT + plotH - h;
      bars += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" fill="${s.color}" rx="6"
        ><title>${esc(s.name)} — ${esc(m)}: ${fmtPct(v)}</title></rect>
        <text x="${x + barW / 2}" y="${y - 6}" text-anchor="middle" font-size="11" font-weight="700"
          fill="${COLORS.ink2}">${(v * 100).toFixed(1)}</text>`;
    });
    xLabels += `<text x="${gx}" y="${H - padB + 20}" text-anchor="middle" font-size="12" font-weight="600"
      fill="${COLORS.ink2}">${esc(m)}</text>`;
  });

  el.innerHTML = `<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Perbandingan metrik">
    ${gl}${bars}${xLabels}
    <line x1="${padL}" y1="${padT + plotH}" x2="${W - padR}" y2="${padT + plotH}" stroke="#cbd5e1" stroke-width="1"/>
  </svg>`;
}

/* ---------- Horizontal bar (top kata TF-IDF) ---------- */
function hBarChart(el, items) {
  const W = 640, rowH = 32, padL = 130, padR = 60, padT = 10;
  const H = padT + items.length * rowH + 10;
  const maxV = Math.max(...items.map((d) => d.weight));
  const plotW = W - padL - padR;

  let rows = "";
  items.forEach((d, i) => {
    const y = padT + i * rowH;
    const w = Math.max((d.weight / maxV) * plotW, 2);
    rows += `<text x="${padL - 10}" y="${y + rowH / 2 + 4}" text-anchor="end" font-size="12" font-weight="600"
        fill="${COLORS.ink2}">${esc(d.term)}</text>
      <rect x="${padL}" y="${y + 6}" width="${w}" height="${rowH - 12}" fill="${COLORS.bar}" rx="6">
        <title>${esc(d.term)}: ${d.weight}</title></rect>
      <text x="${padL + w + 8}" y="${y + rowH / 2 + 4}" font-size="11" font-weight="700"
        fill="${COLORS.muted}">${d.weight}</text>`;
  });

  el.innerHTML = `<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Kata paling berpengaruh">${rows}</svg>`;
}

/* ---------- Word cloud ---------- */
function wordCloud(el, items, color) {
  if (!items || !items.length) {
    el.innerHTML = '<p style="color:var(--ink-muted);font-size:0.85rem;text-align:center;padding:12px">Belum ada data untuk kategori ini.</p>';
    return;
  }
  const max = items[0].count;
  const min = items[items.length - 1].count;
  const range = Math.max(1, max - min);
  const scale = (c) => 13 + ((c - min) / range) * 26;

  const src = [...items], arranged = [];
  while (src.length) {
    arranged.push(src.shift());
    if (src.length) arranged.push(src.pop());
  }

  el.innerHTML =
    '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:6px 14px;padding:14px 8px">' +
    arranged.map((d) => {
      const t = (d.count - min) / range;
      return `<span style="font-size:${scale(d.count).toFixed(0)}px;line-height:1.25;color:${color};
        font-weight:${t > 0.5 ? 800 : 600};opacity:${(0.6 + 0.4 * t).toFixed(2)}"
        title="${esc(d.term)}: ${d.count} kali">${esc(d.term)}</span>`;
    }).join("") + "</div>";
}

/* ---------- Narasi otomatis ---------- */
function narration(text) {
  return `<p style="font-size:0.88rem;color:var(--ink-secondary);line-height:1.75;margin-top:16px;
    padding-top:14px;border-top:1px solid var(--border);text-align:justify">${text}</p>`;
}

/* ---------- Tabel confusion matrix ---------- */
function confusionTable(el, cm) {
  el.innerHTML = `
    <table class="cm-table">
      <tr><th></th><th>Prediksi Positif</th><th>Prediksi Negatif</th></tr>
      <tr><th>Aktual Positif</th>
        <td class="count diag">${cm.tp}</td><td class="count">${cm.fn}</td></tr>
      <tr><th>Aktual Negatif</th>
        <td class="count">${cm.fp}</td><td class="count diag">${cm.tn}</td></tr>
    </table>`;
}
