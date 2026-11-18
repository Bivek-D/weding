// Offline three.js renders of the invitation's objects (cover, stage, section textures).
// Each job builds a small scene in CSS-pixel units, lights it like the rest of the card (soft studio light,
// key from the top left) and returns a transparent PNG at 2x. Run by render.mjs in headless Chromium.
import * as THREE from "./three.module.min.js";

const S = 2; // output scale
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.setPixelRatio(1);
document.body.appendChild(renderer.domElement);

const PAL = {
  yellow: "#F2C318", scarlet: "#D7332B", scarletD: "#A8221D", emerald: "#0F7A4A", gold: "#D9A84A",
  ivory: "#FBF6EC", bamboo: "#C9A063", brass: "#B98A3A", navy: "#1E2457", magenta: "#B0287A",
};

// ---------------------------------------------------------------- environment: a warm studio
function studioEnv() {
  const env = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.BoxGeometry(40, 30, 40), new THREE.MeshBasicMaterial({ color: 0x3a342c, side: THREE.BackSide }));
  env.add(room);
  const panel = (w, h, color, k, pos, look) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), side: THREE.DoubleSide }));
    m.position.set(...pos);
    m.lookAt(...look);
    env.add(m);
  };
  panel(14, 10, 0xfff1dc, 6, [-12, 12, 12], [0, 0, 0]);   // key softbox, top left front
  panel(10, 8, 0xe8f0ff, 1.6, [14, 4, 8], [0, 0, 0]);     // cool fill, right
  panel(30, 30, 0xffe6c0, 0.9, [0, -14, 0], [0, 0, 0]);   // warm floor bounce
  panel(20, 6, 0xffffff, 2.2, [0, 14, -6], [0, 0, 0]);    // top strip for sheen
  const pm = new THREE.PMREMGenerator(renderer);
  return pm.fromScene(env, 0.02).texture;
}
const ENV = studioEnv();

// ---------------------------------------------------------------- helpers
const loader = new THREE.TextureLoader();
const tex = (url, srgb = false) => new Promise((ok, err) => loader.load(url, (t) => {
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  t.anisotropy = 8;
  ok(t);
}, undefined, err));

/** Roughness/metalness map from a thread mask: zari thread is shiny metal, the cotton ground is matt. */
async function ormFromMask(url, { threadRough = 0.32, groundRough = 0.82, threadMetal = 0.85 } = {}) {
  const img = await new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = url; });
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  const x = c.getContext("2d");
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height);
  for (let i = 0; i < d.data.length; i += 4) {
    const m = d.data[i] / 255;
    d.data[i] = 255;
    d.data[i + 1] = 255 * (groundRough + (threadRough - groundRough) * m);
    d.data[i + 2] = 255 * threadMetal * m;
  }
  x.putImageData(d, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.NoColorSpace;
  return t;
}

async function wovenMaterial(name, { sheen = "#ffffff", bump = 2.2, threadMetal = 0.85, repeat = [1, 1], wrap = false } = {}) {
  const [map, height, orm] = await Promise.all([
    tex(`tex/${name}-albedo.png`, true), tex(`tex/${name}-height.png`), ormFromMask(`tex/${name}-mask.png`, { threadMetal }),
  ]);
  for (const t of [map, height, orm]) {
    if (wrap) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  }
  return new THREE.MeshPhysicalMaterial({
    map, bumpMap: height, bumpScale: bump, roughnessMap: orm, metalnessMap: orm, roughness: 1, metalness: 1,
    sheen: 0.6, sheenRoughness: 0.5, sheenColor: new THREE.Color(sheen), envMap: ENV, envMapIntensity: 0.9,
    side: THREE.DoubleSide,
  });
}

/** A plane in CSS px, finely subdivided and gently rippled like hanging cloth (amp px, waves across x). */
function clothPlane(w, h, { amp = 1.5, waves = 3, edgeRound = 0 } = {}) {
  const g = new THREE.PlaneGeometry(w, h, Math.ceil(w / 3), Math.ceil(h / 3));
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i);
    let z = amp * (Math.sin((x / w) * Math.PI * waves + y * 0.004) * 0.7 + Math.sin(y * 0.021 + x * 0.013) * 0.3);
    if (edgeRound) {
      const ex = 1 - Math.min(1, (w / 2 - Math.abs(x)) / edgeRound);
      const ey = 1 - Math.min(1, (h / 2 - Math.abs(y)) / edgeRound);
      z -= edgeRound * 0.6 * (ex * ex + ey * ey);   // edges roll down, the strip reads as having thickness
    }
    p.setZ(i, z);
  }
  g.computeVertexNormals();
  return g;
}

function lights(scene, { w, h, shadow = true, key = 2.6 } = {}) {
  scene.environment = ENV;
  const amb = new THREE.HemisphereLight(0xfff6e6, 0x403020, 0.35);
  scene.add(amb);
  const sun = new THREE.DirectionalLight(0xfff1dc, key);
  sun.position.set(-0.8 * w, 1.0 * h, 1.2 * Math.max(w, h));
  sun.castShadow = shadow;
  const r = Math.max(w, h);
  Object.assign(sun.shadow.camera, { left: -r, right: r, top: r, bottom: -r, near: 1, far: 6 * r });
  sun.shadow.mapSize.set(4096, 4096);
  sun.shadow.radius = 11;
  sun.shadow.bias = -0.0004;
  scene.add(sun);
  return sun;
}

function shoot(scene, w, h, { persp = null, ss = 2 } = {}) {
  renderer.setSize(Math.round(w * S * ss), Math.round(h * S * ss), false);
  let cam;
  if (persp) {
    cam = new THREE.PerspectiveCamera(persp.fov, w / h, 1, 10000);
    cam.position.set(...persp.pos);
    cam.lookAt(...persp.look);
  } else {
    cam = new THREE.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 1, 4000);
    cam.position.set(0, 0, 1000);
  }
  renderer.setClearColor(0x000000, 0);
  renderer.render(scene, cam);
  if (ss === 1) return renderer.domElement.toDataURL("image/png");
  // downsample for clean, anti-aliased edges
  const out = document.createElement("canvas");
  out.width = Math.round(w * S); out.height = Math.round(h * S);
  const x = out.getContext("2d");
  x.imageSmoothingEnabled = true; x.imageSmoothingQuality = "high";
  x.drawImage(renderer.domElement, 0, 0, out.width, out.height);
  return out.toDataURL("image/png");
}

const castAll = (o) => o.traverse((m) => { if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } });

// ---------------------------------------------------------------- cover jobs
const JOBS = {};

JOBS["door-base"] = async () => {
  const w = 196.5, h = 852, s = new THREE.Scene();
  const mesh = new THREE.Mesh(clothPlane(w, h, { amp: 1.6, waves: 2.5 }), await wovenMaterial("door", { sheen: "#9fe0b8" }));
  s.add(mesh); castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

JOBS["door-column"] = async () => {
  const w = 61, h = 852, s = new THREE.Scene();
  s.add(new THREE.Mesh(clothPlane(w, h, { amp: 0.6, waves: 1, edgeRound: 3 }), await wovenMaterial("column", { sheen: "#ffb090" })));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

JOBS["door-hem"] = async () => {
  const w = 196.5, h = 61, s = new THREE.Scene();
  s.add(new THREE.Mesh(clothPlane(w, h, { amp: 0.6, waves: 2, edgeRound: 3 }), await wovenMaterial("hem", { sheen: "#ffb090" })));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

// ---- bow: ribbon swept along curves (units: CSS px; same shapes as the 2D art so the CSS layout holds)
async function ribbonMat() {
  return wovenMaterial("ribbon", { sheen: "#fff0a0", bump: 1.6, wrap: true, threadMetal: 0.3 });
}

/** Ribbon strip along f(t) -> [x, y, z], width w; UV runs along the length (texture length texL px). */
function ribbonGeo(f, n, w, texL = 600, cut = null) {
  const pos = [], uv = [], idx = [];
  let L = 0, prev = null;
  const ns = 9;
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1);
    const c = new THREE.Vector3(...f(t));
    const c2 = new THREE.Vector3(...f(Math.min(1, t + 1e-3))).sub(new THREE.Vector3(...f(Math.max(0, t - 1e-3)))).normalize();
    const nrm = new THREE.Vector3(-c2.y, c2.x, 0).normalize();
    if (prev) L += c.distanceTo(prev);
    prev = c;
    for (let j = 0; j < ns; j++) {
      const s = j / (ns - 1) * 2 - 1;
      let off = s;
      if (cut) off = cut(t, s);
      const bow = (1 - s * s) * 1.6;          // the ribbon is slightly domed across its width
      pos.push(c.x + nrm.x * off * w / 2, c.y + nrm.y * off * w / 2, c.z + bow);
      uv.push(L / texL, (s + 1) / 2);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let j = 0; j < ns - 1; j++) {
    const a = i * ns + j, b = a + ns;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

JOBS["bow-loop"] = async () => {
  // canvas 150x115, knot at (143, 59) from the top left; loop goes out to the left and back
  const w = 150, h = 115, s = new THREE.Scene(), mat = await ribbonMat();
  const kx = 143 - w / 2, ky = h / 2 - 59, A = 125, B = 41;
  const loop = (th) => {
    const x = kx - A * (1 - Math.cos(th)) / 2;
    const y = ky + B * Math.sin(th) * (0.55 + 0.45 * (1 - Math.cos(th)) / 2) + 13 * (1 - Math.cos(th)) / 2;
    const z = 9 * Math.sin(th);                                  // the upper half rides over the lower
    return [x, y, z];
  };
  s.add(new THREE.Mesh(ribbonGeo((t) => loop(t * Math.PI * 2), 260, 28, 600), mat));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

JOBS["bow-tail"] = async () => {
  const w = 100, h = 165, s = new THREE.Scene(), mat = await ribbonMat();
  const P = [[93, 6], [75, 70], [35, 150]].map(([x, y]) => [x - w / 2, h / 2 - y]);
  const bez = (t) => [0, 1].map((k) => (1 - t) ** 2 * P[0][k] + 2 * (1 - t) * t * P[1][k] + t * t * P[2][k]);
  const f = (t) => { const [x, y] = bez(t); return [x, y, 4 * Math.sin(t * Math.PI * 1.5)]; };
  // V-cut end: the middle of the ribbon stops short
  const cut = (t, s) => s;
  const geo = ribbonGeo(f, 160, 28, 600, cut);
  // trim the V by pulling the last rows' centre back along the ribbon
  const p = geo.attributes.position, ns = 9, n = 160;
  for (let j = 0; j < ns; j++) {
    const sv = j / (ns - 1) * 2 - 1, back = (1 - Math.abs(sv)) * 9;
    const i = (n - 1) * ns + j, iPrev = (n - 2) * ns + j;
    const dx = p.getX(iPrev) - p.getX(i), dy = p.getY(iPrev) - p.getY(i), dl = Math.hypot(dx, dy) || 1;
    p.setXY(i, p.getX(i) + dx / dl * back, p.getY(i) + dy / dl * back);
  }
  geo.computeVertexNormals();
  s.add(new THREE.Mesh(geo, mat));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

JOBS["bow-knot"] = async () => {
  // a short length of ribbon wrapped over the centre of the bow, bulging toward us
  const w = 45, h = 55, s = new THREE.Scene(), mat = await ribbonMat();
  const f = (t) => [Math.sin(t * Math.PI) * 1.5, 24 - 48 * t, 10 * Math.sin(t * Math.PI)];
  s.add(new THREE.Mesh(ribbonGeo(f, 80, 34, 600), mat));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

JOBS["ribbon"] = async () => {
  const w = 450, h = 28, s = new THREE.Scene(), mat = await ribbonMat();
  mat.map.repeat.set(450 / 600, 1); mat.bumpMap.repeat.set(450 / 600, 1); mat.roughnessMap.repeat.set(450 / 600, 1);
  s.add(new THREE.Mesh(clothPlane(w, h, { amp: 0.4, waves: 4, edgeRound: 2.5 }), mat));
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

// ---- badge: bamboo tube frame, recessed ivory face, gold inlay, scarlet lacquer diamonds
function badgeOutline(a, b, n = 400) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const th = (i / n) * Math.PI * 2;
    const c = Math.cos(th), s = Math.sin(th);
    let x = a * Math.sign(c) * Math.abs(c) ** 0.5, y = b * Math.sign(s) * Math.abs(s) ** 0.5;
    // notched corners: points inside the notch circle are pushed onto it
    const nx = Math.abs(x) / a, ny = Math.abs(y) / b, cx = 1, cy = 1, r = 0.3;
    const d = Math.hypot(nx - cx, ny - cy);
    if (d < r) {
      const k = r / (d || 1e-6);
      x = Math.sign(x) * (cx + (nx - cx) * k) * a;
      y = Math.sign(y) * (cy + (ny - cy) * k) * b;
    }
    pts.push(new THREE.Vector2(x, y));
  }
  return pts;
}

function bambooTexture() {
  const c = document.createElement("canvas");
  c.width = 2048; c.height = 64;
  const x = c.getContext("2d");
  const g = x.createLinearGradient(0, 0, 0, 64);
  g.addColorStop(0, "#9c7440"); g.addColorStop(0.35, "#d9b276"); g.addColorStop(0.6, "#c9a063"); g.addColorStop(1, "#8e6a36");
  x.fillStyle = g; x.fillRect(0, 0, 2048, 64);
  for (let i = 0; i < 900; i++) {          // fibres along the culm
    x.strokeStyle = `rgba(${Math.random() < .5 ? "90,60,25" : "240,215,170"},${0.08 + Math.random() * 0.12})`;
    const y = Math.random() * 64, l = 40 + Math.random() * 160, x0 = Math.random() * 2048;
    x.beginPath(); x.moveTo(x0, y); x.lineTo(x0 + l, y + (Math.random() - .5) * 1.5); x.stroke();
  }
  for (let k = 0; k < 22; k++) {           // node rings
    const nx = (k + 0.5) * 2048 / 22;
    x.fillStyle = "rgba(110,75,35,.85)"; x.fillRect(nx - 3, 0, 6, 64);
    x.fillStyle = "rgba(245,225,185,.6)"; x.fillRect(nx + 3, 0, 2, 64);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.RepeatWrapping;
  return t;
}

function paperTexture(size = 512) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const x = c.getContext("2d");
  x.fillStyle = "#808080"; x.fillRect(0, 0, size, size);
  for (let i = 0; i < 5000; i++) {
    x.fillStyle = `rgba(${Math.random() < .5 ? 0 : 255},${Math.random() < .5 ? 0 : 255},${Math.random() < .5 ? 0 : 255},.05)`;
    const r = Math.random() * 2.2;
    x.fillRect(Math.random() * size, Math.random() * size, r * 3, r);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

JOBS["plaque"] = async () => {
  const w = 200, h = 230, s = new THREE.Scene();
  const a = w / 2 - 2, b = h / 2 - 2, R = 11;
  const outer = badgeOutline(a, b);
  const scaleIn = (pts, d) => pts.map((p) => new THREE.Vector2(p.x * (a - d) / a, p.y * (b - d) / b));
  // bamboo frame: a tube following the outline, R in from the edge
  const path = new THREE.CatmullRomCurve3(scaleIn(outer, R).map((p) => new THREE.Vector3(p.x, p.y, 0)), true, "centripetal");
  const bt = bambooTexture();
  const bamboo = new THREE.MeshPhysicalMaterial({ map: bt, bumpMap: bt, bumpScale: 1.2, roughness: 0.5, clearcoat: 0.35, clearcoatRoughness: 0.4, envMap: ENV });
  s.add(new THREE.Mesh(new THREE.TubeGeometry(path, 600, R, 24, true), bamboo));
  // cane lashings at the four notched corners
  const cane = new THREE.MeshStandardMaterial({ color: 0x6e4a20, roughness: 0.7, envMap: ENV });
  for (const [sx, sy] of [[1, 1], [-1, 1], [1, -1], [-1, -1]]) {
    const p = scaleIn(outer, R).reduce((best, q) => (Math.abs(q.x * sx - (a - 30)) + Math.abs(q.y * sy - (b - 30)) < Math.abs(best.x * sx - (a - 30)) + Math.abs(best.y * sy - (b - 30)) ? q : best));
    for (let k = -2; k <= 2; k++) {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(R + 0.8, 1.1, 8, 32), cane);
      ring.position.set(p.x + sx * k * 2.6, p.y - sy * k * 2.6, 0);
      ring.rotation.set(Math.PI / 2, 0, Math.atan2(sy, sx) + Math.PI / 4);
      s.add(ring);
    }
  }
  // recessed ivory face
  const faceShape = new THREE.Shape(scaleIn(outer, R + 4));
  const pt = paperTexture();
  pt.repeat.set(0.01, 0.01);
  const face = new THREE.Mesh(new THREE.ShapeGeometry(faceShape, 64),
    new THREE.MeshPhysicalMaterial({ color: 0xfbf4e6, roughness: 0.9, bumpMap: pt, bumpScale: 0.6, sheen: 0.3, sheenColor: new THREE.Color(0xffffff), envMap: ENV }));
  face.position.z = -R * 0.5;
  s.add(face);
  // gold inlay: double rule and diamonds stepping round the face
  const gold = new THREE.MeshPhysicalMaterial({ color: PAL.gold, metalness: 1, roughness: 0.28, envMap: ENV, envMapIntensity: 1.3 });
  for (const [d, r] of [[R + 13, 0.9], [R + 19, 0.7]]) {
    const c = new THREE.CatmullRomCurve3(scaleIn(outer, d).map((p) => new THREE.Vector3(p.x, p.y, -R * 0.5 + 0.4)), true);
    s.add(new THREE.Mesh(new THREE.TubeGeometry(c, 500, r, 8, true), gold));
  }
  const ring16 = scaleIn(outer, R + 16);
  for (let i = 0; i < 64; i++) {
    const p = ring16[Math.floor((i / 64) * ring16.length)];
    const d = new THREE.Mesh(new THREE.OctahedronGeometry(1.8), gold);
    d.position.set(p.x, p.y, -R * 0.5 + 0.6);
    d.scale.set(1, 1, 0.5);
    s.add(d);
  }
  // scarlet lacquer diamonds down the centre (the badge parts here)
  const lacquer = new THREE.MeshPhysicalMaterial({ color: PAL.scarlet, roughness: 0.35, clearcoat: 0.8, clearcoatRoughness: 0.2, envMap: ENV });
  for (let y = -b + R + 38; y < b - R - 46; y += 6.5) {
    const d = new THREE.Mesh(new THREE.OctahedronGeometry(2.4), lacquer);
    d.position.set(0, y, -R * 0.5 + 0.8);
    d.scale.set(0.9, 1.1, 0.45);
    s.add(d);
  }
  // gold peacock-eye medallion at the top
  const mc = new THREE.Vector3(0, b - R - 28, -R * 0.5 + 0.6);
  for (const [r, tube] of [[11, 0.9], [7, 0.7]]) {
    const t = new THREE.Mesh(new THREE.TorusGeometry(r, tube, 8, 48), gold);
    t.position.copy(mc); s.add(t);
  }
  for (let i = 0; i < 12; i++) {
    const bead = new THREE.Mesh(new THREE.SphereGeometry(1.1, 10, 8), gold);
    bead.position.set(mc.x + Math.cos(i / 12 * Math.PI * 2) * 14.5, mc.y + Math.sin(i / 12 * Math.PI * 2) * 14.5, mc.z);
    s.add(bead);
  }
  const center = new THREE.Mesh(new THREE.OctahedronGeometry(3.2), lacquer);
  center.position.copy(mc); center.scale.set(1, 1, 0.5); s.add(center);
  // Hajw teeth along the foot
  for (let i = -5; i <= 5; i++) {
    const tri = new THREE.Shape([new THREE.Vector2(-3.6, 0), new THREE.Vector2(3.6, 0), new THREE.Vector2(0, 6)]);
    const m = new THREE.Mesh(new THREE.ExtrudeGeometry(tri, { depth: 0.8, bevelEnabled: true, bevelSize: 0.3, bevelThickness: 0.3, bevelSegments: 2 }), lacquer);
    m.position.set(i * 7.4, -b + R + 26, -R * 0.5);
    s.add(m);
  }
  castAll(s); lights(s, { w, h });
  return shoot(s, w, h);
};

// butterfly wing (right side): scarlet velvet with a gold zari edge and small gold diamonds
JOBS["wing"] = async () => {
  const w = 65, h = 75, s = new THREE.Scene();
  const c = document.createElement("canvas");
  c.width = 260; c.height = 300;
  const x = c.getContext("2d");
  const lobe = (cx, cy, rx, ry, rot) => { x.beginPath(); x.ellipse(cx, cy, rx, ry, rot, 0, Math.PI * 2); };
  x.fillStyle = PAL.scarlet;
  lobe(130, 100, 125, 74, -0.55); x.fill();
  lobe(92, 215, 78, 60, 0.5); x.fill();
  x.strokeStyle = PAL.gold; x.lineWidth = 12; x.setLineDash([10, 6]);
  lobe(130, 100, 116, 66, -0.55); x.stroke();
  lobe(92, 215, 70, 52, 0.5); x.stroke();
  x.setLineDash([]);
  x.fillStyle = PAL.gold;
  for (const [dx, dy, r] of [[150, 92, 16], [95, 215, 12]]) {
    x.save(); x.translate(dx, dy); x.rotate(Math.PI / 4); x.fillRect(-r / 2, -r / 2, r, r); x.restore();
  }
  x.fillStyle = "#3a2618"; x.fillRect(0, 30, 10, 240);
  const map = new THREE.CanvasTexture(c);
  map.colorSpace = THREE.SRGBColorSpace;
  const g = new THREE.PlaneGeometry(w, h, 40, 40);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) p.setZ(i, -(((p.getX(i) + w / 2) / w) ** 2) * 6);   // wing curls back a little
  g.computeVertexNormals();
  const mat = new THREE.MeshPhysicalMaterial({ map, transparent: true, alphaTest: 0.5, roughness: 0.75, sheen: 1, sheenRoughness: 0.4, sheenColor: new THREE.Color(0xff9a80), envMap: ENV, side: THREE.DoubleSide });
  s.add(new THREE.Mesh(g, mat));
  castAll(s); lights(s, { w, h, shadow: false });
  return shoot(s, w, h);
};


// ---------------------------------------------------------------- stage: the Bathou and its garden
const rnd = (() => { let x = 12345; return () => ((x = (x * 16807) % 2147483647) / 2147483647); })();

function canvasTex(w, h, draw, srgb = true, repeat = null) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  draw(c.getContext("2d"), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  t.anisotropy = 8;
  return t;
}

function bambooPole(h, r) {
  const map = canvasTex(64, 512, (x, w, hh) => {
    const g = x.createLinearGradient(0, 0, w, 0);
    g.addColorStop(0, "#a07a43"); g.addColorStop(.4, "#d8b377"); g.addColorStop(1, "#9c7440");
    x.fillStyle = g; x.fillRect(0, 0, w, hh);
    for (let i = 0; i < 160; i++) { x.fillStyle = `rgba(90,60,25,${.05 + rnd() * .1})`; x.fillRect(rnd() * w, rnd() * hh, 1, 20 + rnd() * 80); }
    for (let k = 1; k < 4; k++) { const y = k * hh / 4; x.fillStyle = "rgba(105,72,32,.9)"; x.fillRect(0, y - 4, w, 7); x.fillStyle = "rgba(240,215,170,.5)"; x.fillRect(0, y + 3, w, 2); }
  });
  map.wrapT = THREE.RepeatWrapping; map.repeat.set(1, h / 30);
  return new THREE.Mesh(new THREE.CylinderGeometry(r * 0.92, r, h, 28), new THREE.MeshPhysicalMaterial({ map, bumpMap: map, bumpScale: 0.6, roughness: 0.55, clearcoat: 0.25, envMap: ENV }));
}

const brassMat = () => new THREE.MeshPhysicalMaterial({ color: 0xc08a3e, metalness: 1, roughness: 0.3, envMap: ENV, envMapIntensity: 1.4 });

/** Marigolds: each flower is a dome of ruffled petals (instanced), orange to yellow. */
function marigolds(list) {
  const petal = new THREE.PlaneGeometry(1, 0.62, 2, 1);
  const pp = petal.attributes.position;
  for (let i = 0; i < pp.count; i++) pp.setZ(i, -Math.abs(pp.getX(i)) * 0.25);
  petal.computeVertexNormals();
  const per = 220;
  const mat = new THREE.MeshPhysicalMaterial({ roughness: 0.6, sheen: 0.8, sheenColor: new THREE.Color(0xffd27a), side: THREE.DoubleSide, envMap: ENV });
  const inst = new THREE.InstancedMesh(petal, mat, list.length * per);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), v = new THREE.Vector3(), sc = new THREE.Vector3(), col = new THREE.Color();
  let k = 0;
  for (const { pos, r, hue = rnd() } of list) {
    const base = new THREE.Color().setHSL(0.05 + hue * 0.045, 0.97, 0.47);
    for (let i = 0; i < per; i++) {
      const phi = Math.acos(1 - (i / per) * 1.35), th = i * 2.399;
      const dir = new THREE.Vector3(Math.sin(phi) * Math.cos(th), Math.cos(phi), Math.sin(phi) * Math.sin(th));
      v.copy(dir).multiplyScalar(r * (0.75 + 0.2 * rnd())).add(pos);
      q.setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);
      q.multiply(new THREE.Quaternion().setFromEuler(e.set((rnd() - .5) * .9, (rnd() - .5) * .9, rnd() * 6.28)));
      const s = r * (0.42 + 0.18 * rnd());
      m.compose(v, q, sc.set(s, s, s));
      inst.setMatrixAt(k, m);
      inst.setColorAt(k, col.copy(base).offsetHSL((rnd() - .5) * .02, 0, (rnd() - .5) * .12 - (1 - Math.cos(phi)) * .12));
      k++;
    }
  }
  inst.castShadow = inst.receiveShadow = true;
  return inst;
}

function leafTexture({ tears = 0, light = "#7dbb44", dark = "#2f6b24" } = {}) {
  return canvasTex(512, 128, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, dark); g.addColorStop(.48, light); g.addColorStop(.52, light); g.addColorStop(1, dark);
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.strokeStyle = "rgba(230,245,190,.55)"; x.lineWidth = 3; x.beginPath(); x.moveTo(0, h / 2); x.lineTo(w, h / 2); x.stroke();
    x.strokeStyle = "rgba(20,50,10,.25)"; x.lineWidth = 1;
    for (let i = 0; i < w; i += 5) { x.beginPath(); x.moveTo(i, h / 2); x.lineTo(i + 18, 0); x.moveTo(i, h / 2); x.lineTo(i + 18, h); x.stroke(); }
    x.globalCompositeOperation = "destination-out";
    for (let k = 0; k < tears; k++) {           // banana leaves tear along their veins
      const t0 = 60 + rnd() * (w - 120), side = rnd() < .5;
      x.lineWidth = 5; x.beginPath();
      x.moveTo(t0, side ? 0 : h); x.lineTo(t0 - 26, side ? h * .38 : h * .62); x.stroke();
    }
  });
}

/** A leaf along a quadratic curve in 3D, width profile w(t), cupped across, UV u along / v across. */
function leafGeo(p0, p1, p2, width, n = 60, cup = 0.25) {
  const pos = [], uv = [], idx = [], ns = 9;
  const P = [p0, p1, p2].map((p) => new THREE.Vector3(...p));
  const at = (t) => P[0].clone().multiplyScalar((1 - t) ** 2).add(P[1].clone().multiplyScalar(2 * (1 - t) * t)).add(P[2].clone().multiplyScalar(t * t));
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1), c = at(t);
    const tan = at(Math.min(1, t + .01)).sub(at(Math.max(0, t - .01))).normalize();
    const side = new THREE.Vector3().crossVectors(tan, new THREE.Vector3(0, 0, 1)).normalize();
    if (side.lengthSq() < .1) side.set(1, 0, 0);
    const up = new THREE.Vector3().crossVectors(side, tan).normalize();
    const wd = width * Math.sin(Math.PI * Math.min(1, t * 1.05)) ** 0.5 * (1 - .2 * t);
    for (let j = 0; j < ns; j++) {
      const sv = j / (ns - 1) * 2 - 1;
      const p = c.clone().add(side.clone().multiplyScalar(sv * wd / 2)).add(up.clone().multiplyScalar(-cup * wd * sv * sv));
      pos.push(p.x, p.y, p.z); uv.push(t, (sv + 1) / 2);
    }
  }
  for (let i = 0; i < n - 1; i++) for (let j = 0; j < ns - 1; j++) { const a = i * ns + j, b = a + ns; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

function shadowCatcher(size = 600, opacity = 0.22) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.ShadowMaterial({ opacity }));
  m.rotation.x = -Math.PI / 2; m.receiveShadow = true;
  return m;
}

function sijou() {
  const g = new THREE.Group();
  const ribs = canvasTex(64, 256, (x, w, h) => {
    x.fillStyle = "#4f8f2c"; x.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 16) { x.fillStyle = "rgba(25,60,15,.55)"; x.fillRect(0, y, w, 4); x.fillStyle = "rgba(170,220,110,.4)"; x.fillRect(0, y + 6, w, 3); }
  });
  ribs.wrapS = ribs.wrapT = THREE.RepeatWrapping; ribs.repeat.set(8, 1);
  const mat = new THREE.MeshPhysicalMaterial({ map: ribs, bumpMap: ribs, bumpScale: 1.2, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.5, envMap: ENV });
  const stem = (pts, r0, r1) => {
    const curve = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)));
    const geo = new THREE.TubeGeometry(curve, 80, 1, 16, false);
    const p = geo.attributes.position, n = geo.attributes.normal;
    for (let i = 0; i < p.count; i++) {                   // taper along the stem
      const t = Math.floor(i / 17) / 80, r = r0 + (r1 - r0) * t - 1;
      p.setXYZ(i, p.getX(i) + n.getX(i) * r, p.getY(i) + n.getY(i) * r, p.getZ(i) + n.getZ(i) * r);
    }
    geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, mat));
    const tip = pts[pts.length - 1];
    const cap = new THREE.Mesh(new THREE.SphereGeometry(r1, 20, 14), mat); cap.position.set(...tip); g.add(cap);
    const leaf = new THREE.MeshStandardMaterial({ color: 0x5c9c34, roughness: .5, side: THREE.DoubleSide, envMap: ENV });
    for (let k = 0; k < 6; k++) {                       // small leaves crowning each tip
      const L = new THREE.Mesh(new THREE.CircleGeometry(1, 12), leaf);
      L.scale.set(1.3, 3.2, 1);
      L.position.set(tip[0], tip[1] + 1.5, tip[2]);
      L.rotation.set(-0.5 - rnd() * .4, k / 6 * Math.PI * 2, 0, "YXZ");
      L.translateY(2.6);
      g.add(L);
    }
  };
  stem([[0, 0, 0], [0.5, 25, 0], [0, 50, 0], [0.4, 68, 0]], 3.2, 1.6);
  const branches = [[-1, 18, -.6], [1, 20, .4], [-.8, 27, .8], [.9, 29, -.7], [-.5, 35, .3], [.6, 37, .5], [-1.1, 23, .2], [1.1, 25, -.2]];
  for (const [dx, y0, dz] of branches) {
    const out = 7 + rnd() * 6, top = 50 + rnd() * 14 - (y0 > 30 ? 4 : 0);
    stem([[0, y0, 0], [dx * out * .6, y0 + 4, dz * out * .6], [dx * out, y0 + 12, dz * out], [dx * out * 1.05, top, dz * out * 1.05]], 2.0, 1.15);
  }
  return g;
}

/** A cloth swag between two points, sagging, with the woven mat pattern, width w. */
function swagMesh(a, b, sag, w, mat) {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b);
  const f = (t) => { const p = A.clone().lerp(B, t); p.y -= sag * Math.sin(Math.PI * t); p.z += 2 * Math.sin(Math.PI * t); return [p.x, p.y, p.z]; };
  return new THREE.Mesh(ribbonGeo(f, 160, w, 120), mat);
}

/** Dokhona drape: smooth marigold cloth, a crisp green woven border on both edges, small butis. */
function drapeMaterial() {
  const map = canvasTex(1024, 256, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, "#e8781a"); g.addColorStop(.5, "#f08a22"); g.addColorStop(1, "#e8781a");
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    for (const y0 of [10, h - 46]) {
      x.fillStyle = "#1d6b3a"; x.fillRect(0, y0, w, 36);
      x.fillStyle = "#f2c318"; x.fillRect(0, y0 + 4, w, 2); x.fillRect(0, y0 + 30, w, 2);
      for (let xx = 10; xx < w; xx += 22) {                 // a row of small gold diamonds in the border
        x.save(); x.translate(xx, y0 + 18); x.rotate(Math.PI / 4); x.fillRect(-4, -4, 8, 8); x.restore();
      }
    }
    x.fillStyle = "#1d6b3a";
    for (let yy = 78; yy < h - 70; yy += 34) for (let xx = (yy / 34 % 2) * 26 + 14; xx < w; xx += 52) {
      x.save(); x.translate(xx, yy); x.rotate(Math.PI / 4); x.fillRect(-3, -3, 6, 6); x.restore();
    }
  }, true, [1, 1]);
  map.wrapS = THREE.RepeatWrapping;
  return new THREE.MeshPhysicalMaterial({ map, bumpMap: weaveBump(), bumpScale: .35, roughness: .7, sheen: .9, sheenRoughness: .4, sheenColor: new THREE.Color(0xffd9a0), envMap: ENV, side: THREE.DoubleSide });
}

JOBS["altar"] = async () => {
  const w = 300, h = 430, s = new THREE.Scene();
  const matCloth = drapeMaterial();
  // woven mat on the floor
  const matTex = drapeMaterial();
  matTex.map.repeat.set(1.6, 1);
  const mat = new THREE.Mesh(clothPlane(110, 62, { amp: .3, waves: 2 }), matTex);
  mat.rotation.x = -Math.PI / 2; mat.position.set(0, 0.2, 14); s.add(mat);
  s.add(shadowCatcher());
  // soil disc and the bamboo fence: 18 pairs of poles, five bands (birth, pain, death, marriage, peace)
  const soil = new THREE.Mesh(new THREE.CylinderGeometry(23, 23.5, 3, 40), new THREE.MeshStandardMaterial({ color: 0x4a3322, roughness: 1 }));
  soil.position.y = 1.5; s.add(soil);
  const R = 24;
  for (let i = 0; i < 18; i++) for (const off of [-0.055, 0.055]) {
    const a = (i / 18) * Math.PI * 2 + off;
    const pole = bambooPole(34, 0.85);
    pole.position.set(R * Math.sin(a), 17, R * Math.cos(a)); s.add(pole);
  }
  const bandMat = new THREE.MeshPhysicalMaterial({ color: 0xc9a063, roughness: 0.55, clearcoat: .2, envMap: ENV });
  for (let k = 0; k < 5; k++) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(R + 0.4, 0.75, 14, 160), bandMat);
    ring.rotation.x = Math.PI / 2; ring.position.y = 5 + k * 6.3; s.add(ring);
  }
  // the sijou rises from the fence
  const plant = sijou(); plant.position.y = 2; s.add(plant);
  // a dokhona cloth knotted round the front of the fence
  const front = [];
  for (let i = 0; i <= 20; i++) { const a = -1.15 + 2.3 * i / 20; front.push([R * 1.04 * Math.sin(a), 27 - 6 * Math.sin(Math.PI * i / 20), R * 1.04 * Math.cos(a)]); }
  const fc = new THREE.CatmullRomCurve3(front.map((p) => new THREE.Vector3(...p)));
  s.add(new THREE.Mesh(ribbonGeo((t) => fc.getPoint(t).toArray(), 240, 9, 120), matCloth));
  // the bamboo frame behind, with swags of dokhona cloth and a marigold garland
  for (const x of [-44, 44]) { const post = bambooPole(96, 1.3); post.position.set(x, 48, -14); s.add(post); }
  const bar = bambooPole(98, 1.2); bar.rotation.z = Math.PI / 2; bar.position.set(0, 94, -14); s.add(bar);
  s.add(swagMesh([-44, 93, -12], [0, 93, -12], 13, 12, matCloth));
  s.add(swagMesh([0, 93, -12], [44, 93, -12], 13, 12, matCloth));
  for (const x of [-44, 44]) {
    s.add(new THREE.Mesh(ribbonGeo((t) => [x + Math.sign(x) * 1.5, 93 - 34 * t, -11 + Math.sin(t * 3) * 1.2], 120, 11, 120), matCloth));
  }
  const gar = [];
  for (let i = 0; i <= 22; i++) { const t = i / 22; gar.push({ pos: new THREE.Vector3(-42 + 84 * t, 90 - 9 * Math.sin(Math.PI * t), -9), r: 2.3 }); }
  for (let i = 0; i < 9; i++) gar.push({ pos: new THREE.Vector3((rnd() - .5) * 30, 31 + rnd() * 2, R * Math.cos((rnd() - .5) * 1.6)), r: 2.4 });
  // brass bowls of offerings at the sides of the mat
  for (const x of [-34, 34]) {
    const bowl = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [5, 0.2], [8.5, 2], [9.5, 4.5], [9.8, 5]].map(([a, b]) => new THREE.Vector2(a, b)), 40), brassMat());
    bowl.position.set(x, 0.3, 26); s.add(bowl);
    for (let k = 0; k < 5; k++) gar.push({ pos: new THREE.Vector3(x + (rnd() - .5) * 9, 6 + rnd() * 2, 26 + (rnd() - .5) * 8), r: 2.6 });
  }
  s.add(marigolds(gar));
  castAll(s);
  const sun = lights(s, { w: 340, h: 340, key: 2.4 });
  sun.position.set(-90, 160, 140);
  return shoot(s, w, h, { persp: { fov: 30, pos: [0, 92, 296], look: [0, 42, 0] } });
};

JOBS["lamp"] = async () => {
  // a brass saki lamp: footed bowl with a wick flame
  const w = 44, h = 60, s = new THREE.Scene();
  const prof = [[0, 0], [7, 0], [7.5, .8], [3, 2], [2.2, 6], [3, 9], [9, 11.5], [10.5, 14], [10.3, 14.6], [8.5, 12.8], [0, 12.5]];
  const lamp = new THREE.Mesh(new THREE.LatheGeometry(prof.map(([a, b]) => new THREE.Vector2(a, b)), 48), brassMat());
  s.add(lamp);
  const oil = new THREE.Mesh(new THREE.CircleGeometry(8.6, 32), new THREE.MeshPhysicalMaterial({ color: 0x8a5a10, roughness: .1, clearcoat: 1 }));
  oil.rotation.x = -Math.PI / 2; oil.position.y = 13.4; s.add(oil);
  const flame = new THREE.Mesh(new THREE.SphereGeometry(2.4, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffc04a }));
  flame.scale.set(1, 2.6, 1); flame.position.set(5, 19.5, 0); s.add(flame);
  const core = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 10), new THREE.MeshBasicMaterial({ color: 0xfff4d0 }));
  core.scale.set(1, 2.2, 1); core.position.set(5, 18.4, 1.2); s.add(core);
  const glow = new THREE.PointLight(0xffb040, 900, 60, 2); glow.position.set(5, 21, 2); s.add(glow);
  castAll(s); flame.castShadow = core.castShadow = false;
  lights(s, { w: 40, h: 40, shadow: false, key: 2 });
  return shoot(s, w, h, { persp: { fov: 30, pos: [0, 30, 80], look: [0, 12, 0] } });
};

JOBS["banana-l"] = async () => {
  const w = 250, h = 330, s = new THREE.Scene();
  const trunkTex = canvasTex(128, 512, (x, ww, hh) => {
    x.fillStyle = "#6f9e3a"; x.fillRect(0, 0, ww, hh);
    for (let i = 0; i < 40; i++) { x.fillStyle = `rgba(${rnd() < .5 ? "110,80,40" : "60,90,30"},.5)`; x.fillRect(rnd() * ww, 0, 2 + rnd() * 6, hh); }
  });
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(7, 11, 150, 20), new THREE.MeshPhysicalMaterial({ map: trunkTex, roughness: .5, clearcoat: .2, envMap: ENV }));
  trunk.position.y = 75; s.add(trunk);
  const specs = [[-1, .15, 30], [1, .1, 32], [-.6, .75, 26], [.65, .7, 26], [-1, -.35, 30], [1, -.4, 30], [.05, 1, 8]];
  for (const [dx, up, wd] of specs) {
    const L = wd < 10 ? 70 : 125;
    const p0 = [0, 150, 0], p1 = [dx * L * .45, 150 + L * (.5 + up * .45), (rnd() - .5) * 30], p2 = [dx * L * .95, 150 + L * up * .7 - 10, (rnd() - .5) * 40];
    const leafMat = new THREE.MeshPhysicalMaterial({ map: leafTexture({ tears: wd < 10 ? 0 : 8 }), alphaTest: 0.5, transparent: false, roughness: .55, sheen: .4, sheenColor: new THREE.Color(0xd8ffb0), side: THREE.DoubleSide, envMap: ENV });
    s.add(new THREE.Mesh(leafGeo(p0, p1, p2, wd, 70, .18), leafMat));
  }
  castAll(s); s.add(shadowCatcher(800, .25));
  const sun = lights(s, { w: 250, h: 250, key: 2.4 }); sun.position.set(-180, 300, 260);
  return shoot(s, w, h, { persp: { fov: 34, pos: [0, 165, 520], look: [0, 158, 0] } });
};

JOBS["bush-l"] = async () => {
  const w = 170, h = 130, s = new THREE.Scene();
  const leafMat = new THREE.MeshPhysicalMaterial({ map: leafTexture({ light: "#5f9e3a", dark: "#24521c" }), roughness: .55, side: THREE.DoubleSide, envMap: ENV });
  for (let i = 0; i < 70; i++) {
    const x = (rnd() - .5) * 150, z = (rnd() - .5) * 40, a = rnd() * 6.28, L = 18 + rnd() * 14;
    const p0 = [x, 2, z], p2 = [x + Math.cos(a) * L, 10 + rnd() * 30, z + Math.sin(a) * L * .5];
    s.add(new THREE.Mesh(leafGeo(p0, [(p0[0] + p2[0]) / 2, p2[1] + 6, (p0[2] + p2[2]) / 2], p2, 7 + rnd() * 4, 30, .3), leafMat));
  }
  const fl = [];
  for (let i = 0; i < 14; i++) fl.push({ pos: new THREE.Vector3((rnd() - .5) * 140, 22 + rnd() * 30, (rnd() - .5) * 30 + 10), r: 9 + rnd() * 5 });
  s.add(marigolds(fl));
  castAll(s); s.add(shadowCatcher(600, .3));
  lights(s, { w: 200, h: 200, key: 2.4 });
  return shoot(s, w, h, { persp: { fov: 34, pos: [0, 52, 175], look: [0, 26, 0] } });
};

JOBS["strand"] = async () => {
  const w = 20, h = 150, s = new THREE.Scene(), fl = [];
  for (let y = 70; y > -64; y -= 7.2) fl.push({ pos: new THREE.Vector3(Math.sin(y) * .6, y, 0), r: 4.4 });
  s.add(marigolds(fl));
  const threadMat = new THREE.MeshStandardMaterial({ color: PAL.scarlet, roughness: .6 });
  for (let k = -3; k <= 3; k++) {
    const t = new THREE.Mesh(new THREE.CylinderGeometry(.25, .25, 12, 5), k % 2 ? threadMat : brassMat());
    t.position.set(k * .7, -70, 0); s.add(t);
  }
  castAll(s); lights(s, { w: 60, h: 160, shadow: false, key: 2.4 });
  return shoot(s, w, h);
};

// ---------------------------------------------------------------- section pages: real fabric strips
for (const tone of ["scarlet", "emerald", "navy", "yellow", "magenta"]) {
  JOBS[`band-${tone}`] = async () => {
    const w = 600, h = 41, s = new THREE.Scene();
    const m = await wovenMaterial(`band-${tone}`, { sheen: "#ffffff", bump: 1.8, threadMetal: tone === "emerald" || tone === "magenta" ? 0.15 : 0.85 });
    s.add(new THREE.Mesh(clothPlane(w, h, { amp: 0.5, waves: 7, edgeRound: 2.5 }), m));
    castAll(s); lights(s, { w, h });
    return shoot(s, w, h);
  };
}
for (const tone of ["emerald", "scarlet"]) {
  JOBS[`edge-${tone}`] = async () => {
    const w = 19, h = 600, s = new THREE.Scene();
    const m = await wovenMaterial(`edge-${tone}`, { sheen: "#ffffff", bump: 1.6, threadMetal: tone === "scarlet" ? 0.85 : 0.15 });
    s.add(new THREE.Mesh(clothPlane(w, h, { amp: 0.3, waves: 1, edgeRound: 1.5 }), m));
    castAll(s); lights(s, { w, h });
    return shoot(s, w, h);
  };
}

// ---------------------------------------------------------------- cultural objects for the section pages
function weaveBump() {
  return canvasTex(256, 256, (x, w, h) => {
    x.fillStyle = "#808080"; x.fillRect(0, 0, w, h);
    for (let y = 0; y < h; y += 2) { x.fillStyle = y % 4 ? "rgba(255,255,255,.18)" : "rgba(0,0,0,.18)"; x.fillRect(0, y, w, 1); }
    for (let i = 0; i < w; i += 3) { x.fillStyle = "rgba(0,0,0,.08)"; x.fillRect(i, 0, 1, h); }
  }, false, [6, 6]);
}

/** Plain cloth with a woven border band along one edge (canvas texture), e.g. a gamsa or a dokhona body. */
function clothTex({ ground, stripes = [], buti = null, w = 512, h = 512 }) {
  return canvasTex(w, h, (x) => {
    x.fillStyle = ground; x.fillRect(0, 0, w, h);
    for (const [y0, hh, col] of stripes) { x.fillStyle = col; x.fillRect(0, y0 * h, w, hh * h); }
    if (buti) {
      x.fillStyle = buti;
      for (let yy = 30; yy < h * .7; yy += 46) for (let xx = (yy / 46 % 2) * 23 + 10; xx < w; xx += 46) {
        x.save(); x.translate(xx, yy); x.rotate(Math.PI / 4); x.fillRect(-4, -4, 8, 8); x.restore();
      }
    }
  });
}

/** Folded cloth seen from the front: stacked layers, each with a flat top and a rounded front fold.
 *  topMat shows the face of the cloth, edgeMat the folds; fringe adds threads hanging from the top fold. */
function foldedStack({ w = 120, d = 70, t = 7, layers = 3, topMat, edgeMat, fringe = null }) {
  const g = new THREE.Group();
  for (let k = 0; k < layers; k++) {
    const y = k * t + (k ? 0.4 : 0), inset = (layers - 1 - k) * 1.5;
    const top = new THREE.Mesh(clothPlane(w - inset, d, { amp: 0.25, waves: 2 }), k === layers - 1 ? topMat : edgeMat);
    top.rotation.x = -Math.PI / 2; top.position.set(0, y + t, 0); g.add(top);
    const arc = (tt) => { const a = Math.PI / 2 - tt * Math.PI; return [0, y + t / 2 + Math.sin(a) * t / 2, d / 2 + Math.cos(a) * t / 2]; };
    g.add(new THREE.Mesh(ribbonGeo(arc, 24, w - inset, 300), edgeMat));
  }
  if (fringe) {
    const yTop = (layers - 1) * t + 0.4;
    const fm = new THREE.MeshStandardMaterial({ color: fringe, roughness: .7 });
    for (let x = -w / 2 + 2; x < w / 2; x += 2.2) {
      const L = 9 + Math.random() * 3;
      const th = new THREE.Mesh(new THREE.CylinderGeometry(.35, .3, L, 4), fm);
      th.position.set(x, yTop - L / 2 + t / 2, d / 2 + t / 2 + .5);
      th.rotation.z = (Math.random() - .5) * .15;
      g.add(th);
    }
  }
  return g;
}

const productShot = (s, w, h, look = [0, 8, 0], pos = [0, 95, 190]) => {
  castAll(s); s.add(shadowCatcher(800, .3));
  const sun = lights(s, { w: 260, h: 260, key: 2.5 }); sun.position.set(-160, 260, 220);
  return shoot(s, w, h, { persp: { fov: 30, pos, look } });
};

JOBS["fold-aronai"] = async () => {
  const s = new THREE.Scene();
  const top = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.6, wrap: true, repeat: [0.35, 1] });
  const edge = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.2, wrap: true, repeat: [0.35, .3] });
  s.add(foldedStack({ w: 130, d: 42, t: 6, layers: 4, topMat: top, edgeMat: edge, fringe: 0xd9a84a }));
  return productShot(s, 220, 120, [0, 10, 6], [0, 85, 175]);
};

JOBS["fold-dokhona"] = async () => {
  const s = new THREE.Scene(), bump = weaveBump();
  const body = new THREE.MeshPhysicalMaterial({ map: clothTex({ ground: PAL.yellow, stripes: [[.78, .16, PAL.scarlet], [.8, .02, PAL.gold], [.92, .02, PAL.gold]], buti: PAL.scarlet }), bumpMap: bump, bumpScale: .5, roughness: .7, sheen: .8, sheenColor: new THREE.Color(0xfff2b0), envMap: ENV, side: THREE.DoubleSide });
  const edge = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.2, wrap: true, repeat: [0.3, .4] });
  s.add(foldedStack({ w: 120, d: 70, t: 7, layers: 3, topMat: body, edgeMat: edge }));
  return productShot(s, 160, 120);
};

JOBS["fold-gamsa"] = async () => {
  const s = new THREE.Scene(), bump = weaveBump();
  const stripes = [[.74, .025, "#f4f1e8"], [.79, .05, "#f4f1e8"], [.87, .025, "#f4f1e8"]];
  const t = clothTex({ ground: PAL.emerald, stripes });
  const top = new THREE.MeshPhysicalMaterial({ map: t, bumpMap: bump, bumpScale: .5, roughness: .8, sheen: .6, sheenColor: new THREE.Color(0xb8f0d0), envMap: ENV, side: THREE.DoubleSide });
  const et = clothTex({ ground: PAL.emerald, stripes: [[0, .2, "#f4f1e8"], [.5, .12, "#f4f1e8"]] });
  et.wrapS = et.wrapT = THREE.RepeatWrapping; et.repeat.set(1, 1);
  const edge = new THREE.MeshPhysicalMaterial({ map: et, bumpMap: bump, bumpScale: .5, roughness: .8, sheen: .6, envMap: ENV, side: THREE.DoubleSide });
  s.add(foldedStack({ w: 120, d: 70, t: 7, layers: 3, topMat: top, edgeMat: edge }));
  return productShot(s, 160, 120);
};

function woodTex(base = "#7a4a22") {
  return canvasTex(512, 128, (x, w, h) => {
    x.fillStyle = base; x.fillRect(0, 0, w, h);
    for (let i = 0; i < 60; i++) {
      x.strokeStyle = `rgba(${rnd() < .5 ? "40,20,5" : "200,140,80"},${.1 + rnd() * .15})`; x.lineWidth = 1 + rnd() * 2;
      x.beginPath(); const y = rnd() * h; x.moveTo(0, y);
      for (let xx = 0; xx <= w; xx += 32) x.lineTo(xx, y + Math.sin(xx * .02 + i) * 4);
      x.stroke();
    }
  });
}

function kham() {
  const g = new THREE.Group();
  const prof = [];
  for (let i = 0; i <= 20; i++) { const t = i / 20; prof.push(new THREE.Vector2(10.5 + 2.6 * Math.sin(Math.PI * t), -26 + 52 * t)); }
  const body = new THREE.Mesh(new THREE.LatheGeometry(prof, 48), new THREE.MeshPhysicalMaterial({ map: woodTex(), roughness: .45, clearcoat: .5, clearcoatRoughness: .3, envMap: ENV }));
  g.add(body);
  const skin = new THREE.MeshPhysicalMaterial({ color: 0xe8d6b0, roughness: .8, sheen: .3, envMap: ENV });
  const hoop = new THREE.MeshStandardMaterial({ color: 0x3a2412, roughness: .6 });
  for (const y of [-26.5, 26.5]) {
    const head = new THREE.Mesh(new THREE.CircleGeometry(11, 40), skin);
    head.rotation.x = y > 0 ? -Math.PI / 2 : Math.PI / 2; head.position.y = y; g.add(head);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(11.3, 1.1, 10, 48), hoop);
    ring.rotation.x = Math.PI / 2; ring.position.y = y; g.add(ring);
  }
  // leather lacing in a zigzag from hoop to hoop
  const pts = [];
  for (let i = 0; i <= 24; i++) {
    const a = (i / 24) * Math.PI * 2, top = i % 2 === 0, y = top ? 25.5 : -25.5;
    const r = 11.3 + (Math.abs(y) < 20 ? 2.4 : 0.6);
    pts.push(new THREE.Vector3(Math.cos(a) * r, y, Math.sin(a) * r));
  }
  const path = new THREE.CurvePath();
  for (let i = 0; i < pts.length - 1; i++) {
    const m = pts[i].clone().lerp(pts[i + 1], .5); m.setLength(Math.hypot(m.x, m.z) ? 13.4 : 0); m.y = (pts[i].y + pts[i + 1].y) / 2;
    const mid = new THREE.Vector3(m.x, m.y, m.z);
    path.add(new THREE.QuadraticBezierCurve3(pts[i], mid, pts[i + 1]));
  }
  g.add(new THREE.Mesh(new THREE.TubeGeometry(path, 400, .55, 6, false), new THREE.MeshStandardMaterial({ color: 0xc8a878, roughness: .7 })));
  return g;
}

JOBS["instruments"] = async () => {
  const s = new THREE.Scene();
  const k = kham(); k.rotation.z = Math.PI / 2; k.rotation.y = -0.35; k.position.set(-6, 13.5, 0); s.add(k);
  // siphung: a long bamboo flute resting across the drum, with a scarlet tassel
  const flute = bambooPole(110, 1.9); flute.rotation.z = Math.PI / 2 - .22; flute.rotation.y = .5; flute.position.set(14, 30, 14); s.add(flute);
  // jotha: a pair of brass cymbals tied with a red cord
  for (const [x, z, rot] of [[44, 26, .2], [56, 18, -.4]]) {
    const cym = new THREE.Mesh(new THREE.LatheGeometry([[0, 2.4], [2.5, 2.2], [3.2, 1], [9, .4], [9.4, 0]].map(([a, b]) => new THREE.Vector2(a, b)), 40), brassMat());
    cym.position.set(x, .2, z); cym.rotation.set(rot * .2, rot, 0); s.add(cym);
  }
  return productShot(s, 260, 140, [12, 16, 8], [0, 72, 158]);
};

JOBS["meal"] = async () => {
  const s = new THREE.Scene();
  // banana leaf laid flat, a mound of rice, ondlakhari in a small leaf cup, and the wooden hatha bowl
  const leafMat = new THREE.MeshPhysicalMaterial({ map: leafTexture({ light: "#6fb03a", dark: "#2f6b24" }), roughness: .35, clearcoat: .4, side: THREE.DoubleSide, envMap: ENV });
  s.add(new THREE.Mesh(leafGeo([-70, .5, 4], [0, 3, -4], [72, .8, 2], 60, 60, -.05), leafMat));
  const grain = canvasTex(256, 256, (x, w, h) => { x.fillStyle = "#f6f2e6"; x.fillRect(0, 0, w, h); for (let i = 0; i < 2500; i++) { x.fillStyle = rnd() < .5 ? "rgba(255,255,255,.9)" : "rgba(200,190,170,.5)"; x.save(); x.translate(rnd() * w, rnd() * h); x.rotate(rnd() * 6.3); x.fillRect(-3, -1, 6, 2); x.restore(); } }, true, [3, 3]);
  const rice = new THREE.Mesh(new THREE.SphereGeometry(20, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshPhysicalMaterial({ color: 0xf3ecd8, map: grain, bumpMap: grain, bumpScale: 4, roughness: .8, sheen: .4, envMap: ENV }));
  rice.scale.set(1.15, .42, 1); rice.position.set(-8, 1.5, 2); s.add(rice);
  const curry = new THREE.Mesh(new THREE.SphereGeometry(9, 30, 16, 0, Math.PI * 2, 0, Math.PI / 2), new THREE.MeshPhysicalMaterial({ color: 0xc98a3c, roughness: .35, clearcoat: .8, envMap: ENV }));
  curry.scale.set(1, .35, 1); curry.position.set(26, 2.6, 6); s.add(curry);
  const cup = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [8, .2], [11, 3], [11.5, 3.5]].map(([a, b]) => new THREE.Vector2(a, b)), 32), leafMat);
  cup.position.set(26, .6, 6); s.add(cup);
  const bowl = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [9, 0], [13, 4], [15.5, 9], [16, 10], [15, 10], [12.5, 5], [0, 4]].map(([a, b]) => new THREE.Vector2(a, b)), 48),
    new THREE.MeshPhysicalMaterial({ map: woodTex("#6a3e1c"), roughness: .5, clearcoat: .3, envMap: ENV }));
  bowl.position.set(-52, 0, -22); s.add(bowl);
  return productShot(s, 260, 130, [-6, 4, 0], [0, 110, 175]);
};

JOBS["lamps3"] = async () => {
  const s = new THREE.Scene();
  const prof = [[0, 0], [7, 0], [7.5, .8], [3, 2], [2.2, 6], [3, 9], [9, 11.5], [10.5, 14], [10.3, 14.6], [8.5, 12.8], [0, 12.5]];
  for (const [x, z, sc] of [[-30, 4, .9], [0, -6, 1.1], [30, 4, .9]]) {
    const g = new THREE.Group();
    g.add(new THREE.Mesh(new THREE.LatheGeometry(prof.map(([a, b]) => new THREE.Vector2(a, b)), 48), brassMat()));
    const flame = new THREE.Mesh(new THREE.SphereGeometry(2.4, 16, 12), new THREE.MeshBasicMaterial({ color: 0xffc04a }));
    flame.scale.set(1, 2.6, 1); flame.position.set(5, 19.5, 0); g.add(flame);
    const core = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 10), new THREE.MeshBasicMaterial({ color: 0xfff4d0 }));
    core.scale.set(1, 2.2, 1); core.position.set(5, 18.4, 1.2); g.add(core);
    const pl = new THREE.PointLight(0xffb040, 700, 60, 2); pl.position.set(5, 21, 2); g.add(pl);
    g.position.set(x, 0, z); g.scale.setScalar(sc); s.add(g);
  }
  const fl = [];
  for (let i = 0; i < 6; i++) fl.push({ pos: new THREE.Vector3(-50 + i * 20 + (rnd() - .5) * 6, 3, 22 + (rnd() - .5) * 6), r: 4 });
  s.add(marigolds(fl));
  return productShot(s, 200, 110, [0, 10, 2], [0, 60, 150]);
};

JOBS["knot"] = async () => {
  // two aronai, emerald and scarlet, tied together: two families, one knot
  const s = new THREE.Scene();
  const em = await wovenMaterial("band-emerald", { sheen: "#c0ffe0", bump: 1.4, wrap: true, threadMetal: .15 });
  const sc = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.4, wrap: true });
  // two interlocked loops: emerald passes in front at the top crossing and behind at the bottom one
  const loop = (cx, sign, phase) => (t) => {
    const a = t * Math.PI * 2 + phase;
    return [cx + Math.cos(a) * 30, Math.sin(a) * 20, sign * 10 * Math.sin(a)];
  };
  s.add(new THREE.Mesh(ribbonGeo(loop(-17, 1, 0), 220, 15, 600), em));
  s.add(new THREE.Mesh(ribbonGeo(loop(17, -1, Math.PI), 220, 15, 600), sc));
  s.add(new THREE.Mesh(ribbonGeo((t) => [-47 - t * 26, -4 - t * 34, 2], 60, 15, 600), em));
  s.add(new THREE.Mesh(ribbonGeo((t) => [47 + t * 26, -4 - t * 34, 2], 60, 15, 600), sc));
  castAll(s); lights(s, { w: 200, h: 200 });
  return shoot(s, 180, 100);
};

JOBS["plate"] = async () => {
  const s = new THREE.Scene();
  const tray = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [30, 0], [36, 1.5], [44, 3.2], [45, 4.2], [43.5, 4.2], [35, 2.6], [0, 2]].map(([a, b]) => new THREE.Vector2(a, b)), 64),
    new THREE.MeshPhysicalMaterial({ color: 0xd9a24a, metalness: .8, roughness: .38, envMap: ENV, envMapIntensity: 1.6 }));
  s.add(tray);
  const top = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.6, wrap: true, repeat: [0.3, 1] });
  const edge = await wovenMaterial("band-scarlet", { sheen: "#ffc0a0", bump: 1.2, wrap: true, repeat: [0.3, .3] });
  const fold = foldedStack({ w: 56, d: 30, t: 4.5, layers: 3, topMat: top, edgeMat: edge, fringe: 0xd9a84a });
  fold.position.set(-4, 2.2, -4); fold.rotation.y = .25; s.add(fold);
  const fl = [];
  for (let i = 0; i < 9; i++) { const a = -.6 + i * .32; fl.push({ pos: new THREE.Vector3(Math.cos(a) * 34, 6, Math.sin(a) * 34 * .55 + 8), r: 5 }); }
  s.add(marigolds(fl));
  return productShot(s, 220, 120, [0, 6, 4], [0, 95, 150]);
};

window.JOBS = Object.keys(JOBS);
window.renderJob = async (name) => JOBS[name]();
window.ready = true;
