import { FilesetResolver, HandLandmarker } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/+esm";

const WASM_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task";
const HOLD_FRAMES = 10;   // detections in a row before a sign counts

const CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4], [0, 5], [5, 6], [6, 7], [7, 8], [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16], [13, 17], [17, 18], [18, 19], [19, 20], [0, 17],
];

const $ = (id) => document.getElementById(id);
const video = $("video"), canvas = $("overlay"), ctx = canvas.getContext("2d");

const store = {
  get(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode */ } },
};

const slugOf = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

let SIGNS = [];
const state = {
  mode: "learn", current: 0, revealed: false, hold: 0,
  done: new Set(), outline: store.get("outline", true),
  landmarker: null, lastTime: -1, bannerTimer: 0,
};

// ---------- recognition (same rules as src/signs.py) ----------
const dist = (a, b, A) => Math.hypot((a.x - b.x) * A, a.y - b.y, (a.z - b.z) * A);

function curl(lm, f, A) {
  const mcp = 5 + 4 * f, pip = 6 + 4 * f, dip = 7 + 4 * f, tip = 8 + 4 * f;
  const length = dist(lm[0], lm[mcp], A) + dist(lm[mcp], lm[pip], A) + dist(lm[pip], lm[dip], A) + dist(lm[dip], lm[tip], A);
  const ratio = dist(lm[0], lm[tip], A) / length;
  return Math.min(1, Math.max(0, (0.95 - ratio) / 0.6));
}

function features(lm, A) {
  const scale = dist(lm[0], lm[9], A);
  const curls = [0, 1, 2, 3].map((f) => curl(lm, f, A));
  const tags = new Set();
  if (dist(lm[4], lm[5], A) / scale > 0.75) {
    tags.add("out");
    if (lm[4].y < lm[0].y - 0.3 * scale) tags.add("up");
    else if (lm[4].y > lm[0].y + 0.3 * scale) tags.add("down");
  } else {
    tags.add("in");
  }
  for (let k = 0; k < 4; k++) if (dist(lm[4], lm[8 + 4 * k], A) / scale < 0.35) tags.add(`touch:${k}`);
  const spread = dist(lm[8], lm[12], A) / scale > 0.3 ? "apart" : "together";
  return { curls, tags, spread };
}

function detect(lm, A = 4 / 3, threshold = 1.0) {
  const { curls, tags, spread } = features(lm, A);
  let best = null, bestScore = threshold;
  SIGNS.forEach((s, i) => {
    if (!tags.has(s.thumb)) return;
    if (s.spread && s.spread !== spread) return;
    const score = curls.reduce((sum, c, k) => sum + Math.abs(c - s.curl[k]), 0);
    if (score < bestScore) { best = i; bestScore = score; }
  });
  return best;
}
window.__detect = detect;   // handy for testing in the console

// ---------- UI ----------
function render() {
  document.querySelectorAll(".mode").forEach((b) => b.classList.toggle("active", b.dataset.mode === state.mode));
  $("outlineBtn").textContent = `Outline: ${state.outline ? "on" : "off"}`;
  $("outlineBtn").setAttribute("aria-pressed", state.outline);

  const total = SIGNS.length, n = state.done.size;
  $("barFill").style.width = `${(100 * n) / total}%`;
  $("hintBtn").hidden = true;

  if (n === total) {
    $("counter").textContent = "All done!";
    $("pic").hidden = true;
    $("placeholder").hidden = false;
    $("placeholder").textContent = "✓";
    $("name").textContent = "You know them all";
    $("how").textContent = "Reset your progress to practise again.";
    $("skipBtn").disabled = true;
    return;
  }

  $("skipBtn").disabled = false;
  $("counter").textContent = `${n} of ${total} learned`;
  const sign = SIGNS[state.current];
  $("name").textContent = sign.name;
  if (state.mode === "learn" || state.revealed) {
    $("pic").hidden = false;
    $("pic").src = `../images/${sign.slug}.png`;
    $("pic").alt = sign.name;
    $("placeholder").hidden = true;
    $("how").textContent = sign.how;
  } else {
    $("pic").hidden = true;
    $("placeholder").hidden = false;
    $("placeholder").textContent = "?";
    $("how").textContent = "Make this sign in front of the camera.";
    $("hintBtn").hidden = false;
  }
}

function advance(after) {
  for (let step = 1; step <= SIGNS.length; step++) {
    const next = (after + step) % SIGNS.length;
    if (!state.done.has(SIGNS[next].name)) { state.current = next; break; }
  }
  state.revealed = false;
  state.hold = 0;
  render();
}

function complete(i) {
  state.done.add(SIGNS[i].name);
  store.set("done", [...state.done]);
  const banner = $("banner");
  banner.textContent = `${SIGNS[i].name}  ✓`;
  banner.hidden = false;
  clearTimeout(state.bannerTimer);
  state.bannerTimer = setTimeout(() => (banner.hidden = true), 1500);
  advance(i);
}

document.querySelectorAll(".mode").forEach((b) => b.addEventListener("click", () => {
  state.mode = b.dataset.mode; state.revealed = false; render();
}));
$("hintBtn").addEventListener("click", () => { state.revealed = true; render(); });
$("skipBtn").addEventListener("click", () => advance(state.current));
$("resetBtn").addEventListener("click", () => {
  state.done.clear(); store.set("done", []); state.current = 0; state.revealed = false; state.hold = 0; render();
});
$("outlineBtn").addEventListener("click", () => {
  state.outline = !state.outline; store.set("outline", state.outline); render();
  if (!state.outline) ctx.clearRect(0, 0, canvas.width, canvas.height);
});

// ---------- camera + tracking ----------
function drawHand(lm) {
  const cw = canvas.clientWidth, ch = canvas.clientHeight, vw = video.videoWidth, vh = video.videoHeight;
  if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }
  ctx.clearRect(0, 0, cw, ch);
  if (!lm || !state.outline) return;
  // the video is shown with object-fit: cover, so map landmarks the same way
  const s = Math.max(cw / vw, ch / vh);
  const ox = (cw - vw * s) / 2, oy = (ch - vh * s) / 2;
  const pt = (p) => [ox + p.x * vw * s, oy + p.y * vh * s];
  ctx.lineCap = "round";
  ctx.strokeStyle = "#f0ede5"; ctx.lineWidth = 3;
  ctx.beginPath();
  for (const [a, b] of CONNECTIONS) { ctx.moveTo(...pt(lm[a])); ctx.lineTo(...pt(lm[b])); }
  ctx.stroke();
  ctx.fillStyle = "#f0ede5"; ctx.strokeStyle = "#004643"; ctx.lineWidth = 1.5;
  for (const p of lm) { const [x, y] = pt(p); ctx.beginPath(); ctx.arc(x, y, 5, 0, 7); ctx.fill(); ctx.stroke(); }
}

function loop() {
  requestAnimationFrame(loop);
  if (!state.landmarker || video.readyState < 2 || video.currentTime === state.lastTime) return;
  state.lastTime = video.currentTime;

  const result = state.landmarker.detectForVideo(video, performance.now());
  const lm = result.landmarks && result.landmarks[0];
  drawHand(lm);

  if (!lm) { $("status").textContent = "Show your hand"; state.hold = 0; return; }
  const seen = detect(lm, video.videoWidth / video.videoHeight);
  $("status").textContent = seen === null ? "Hand detected" : SIGNS[seen].name;
  if (seen !== null && seen === state.current && state.done.size < SIGNS.length) {
    if (++state.hold >= HOLD_FRAMES) { state.hold = 0; complete(seen); }
  } else {
    state.hold = 0;
  }
}

async function createLandmarker() {
  const files = await FilesetResolver.forVisionTasks(WASM_URL);
  const options = (delegate) => ({
    baseOptions: { modelAssetPath: MODEL_URL, delegate },
    runningMode: "VIDEO", numHands: 1,
    minHandDetectionConfidence: 0.6, minTrackingConfidence: 0.6,
  });
  try { return await HandLandmarker.createFromOptions(files, options("GPU")); }
  catch { return await HandLandmarker.createFromOptions(files, options("CPU")); }
}

async function start() {
  const note = $("startNote"), btn = $("startBtn");
  btn.disabled = true;
  note.textContent = "Asking for the camera...";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: false,
    });
    video.srcObject = stream;
    await video.play();
  } catch (e) {
    note.textContent = "Camera blocked. Allow camera access for this site in Settings, then try again.";
    btn.disabled = false;
    return;
  }

  $("start").hidden = true;
  $("app").hidden = false;
  render();
  $("status").textContent = "Loading hand model...";
  try { await navigator.wakeLock?.request("screen"); } catch { /* not supported */ }

  try {
    state.landmarker = await createLandmarker();
    $("status").textContent = "Show your hand";
    loop();
  } catch (e) {
    $("status").textContent = "Could not load the hand model. Check your connection.";
    console.error(e);
  }
}

async function init() {
  SIGNS = (await (await fetch("../signs.json")).json()).map((s) => ({ ...s, slug: slugOf(s.name) }));
  const saved = new Set(store.get("done", []));
  state.done = new Set(SIGNS.filter((s) => saved.has(s.name)).map((s) => s.name));
  const first = SIGNS.findIndex((s) => !state.done.has(s.name));
  state.current = first === -1 ? 0 : first;
  $("startBtn").addEventListener("click", start);
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
}

init();
