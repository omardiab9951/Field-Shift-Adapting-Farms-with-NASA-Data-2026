
(() => {
"use strict";
const D = window.FS_DATA;
const API = window.FS_API;
const RM = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const WHAT = ["Winter crop is growing","Winter crop is growing","Winter crop at its greenest","Winter crop ripens","Harvest. Fields lie open","Summer crop is planted","Summer crop is growing","Summer crop is growing","Summer harvest begins","Fields open again","Winter crop is planted","Winter crop comes up"];
const OPTS = D.options;
const C = D.cells.map(a => ({id:a[0],row:a[1],col:a[2],farm:a[5],isFarm:!!a[6],wN:a[7],ndvi:a[13],conf:a[18],warn:a[19],altSave:a[21],wrob:a[16],srob:a[17]}));
const S = D.scores, N = C.length;
const GRID = {}; C.forEach((c,i) => GRID[c.row + "_" + c.col] = i);

// ---------- icons: one hand-drawn set, 24px grid ----------
const leafPair = y => `<path d="M12 ${y}c-2.300-.2-3.700-1.600-3.900-3.900 2.300.2 3.700 1.600 3.900 3.900zM12 ${y}c2.300-.2 3.700-1.600 3.900-3.900-2.300.2-3.700 1.600-3.900 3.900z"/>`;
const ICON = {
  wheat:`<path d="M12 22V6.500"/><path d="M12 6.500c-1.300-1.300-1.300-3 0-4.500 1.300 1.500 1.300 3.200 0 4.500z"/>${leafPair(11)}${leafPair(15.5)}${leafPair(20)}`,
  rice:`<path d="M7.500 19c.4-7 3-11.600 9-14"/><path d="M7.500 19c-.2-3.500-.9-6-2.500-8"/><ellipse cx="17.200" cy="6.800" rx="1" ry="1.900" transform="rotate(38 17.200 6.800)"/><ellipse cx="13.400" cy="6.300" rx="1" ry="1.900" transform="rotate(-24 13.400 6.300)"/><ellipse cx="17.600" cy="10.600" rx="1" ry="1.900" transform="rotate(14 17.600 10.600)"/><ellipse cx="13.600" cy="10.300" rx="1" ry="1.900" transform="rotate(-8 13.600 10.300)"/><path d="M3 21.500c1.500-1 3-1 4.500 0s3 1 4.500 0 3-1 4.500 0 3 1 4.500 0"/>`,
  maize:`<ellipse cx="12" cy="9.500" rx="3.400" ry="7"/><path d="M9.300 6.500h5.400M8.700 9.500h6.600M9.300 12.500h5.400"/><path d="M12 22c-4.500-1.500-6.500-5-6-9.500 2.800 1.500 5 4.500 6 9.500zM12 22c4.500-1.500 6.500-5 6-9.500-2.800 1.500-5 4.500-6 9.500z"/>`,
  cotton:`<circle cx="9" cy="10" r="3.300"/><circle cx="15" cy="10" r="3.300"/><circle cx="12" cy="6.300" r="3.300"/><path d="M12 13.300V22M12 17.500l-3.500 2.500M12 17.500l3.500 2.500"/>`,
  soybean:`<path d="M4.500 17.500c-.5-7 5-13 15-13 .5 7-5 13-15 13z"/><circle cx="9" cy="14.200" r="1.700"/><circle cx="12.300" cy="11" r="1.700"/><circle cx="15.600" cy="7.900" r="1.600"/>`,
  sugarbeet:`<path d="M12 22c-3.800-2.800-6-5.800-6-8.700a6 6 0 0 1 12 0c0 2.900-2.200 5.900-6 8.700z"/><path d="M12 7.300V2.500M12 7.300C10 6.500 8.300 4.800 8 2.800M12 7.300c2-.8 3.700-2.500 4-4.500"/>`,
  potato:`<path d="M4.500 13.500C4.200 9.500 7.200 6 12 6c4.500 0 7.500 2.500 7.500 6 0 3.800-3.200 7-8 7-4 0-6.800-2-7-5.500z"/><path d="M9 11.500h.01M14.500 10h.01M13 15h.01" stroke-width="2.400"/>`,
  alfalfa:`<path d="M12 22v-9"/><path d="M12 13c-2-2.300-2-5.700 0-8.500 2 2.800 2 6.200 0 8.500z"/><path d="M12 13c-3 .3-5.700-1.300-7-4.400 3.200-.8 5.800.9 7 4.400zM12 13c3 .3 5.700-1.300 7-4.400-3.200-.8-5.800.9-7 4.400z"/>`,
  drop:`<path d="M12 3c3.800 4.600 6 7.800 6 11a6 6 0 0 1-12 0c0-3.200 2.200-6.400 6-11z"/><path d="M9.500 14.500a2.600 2.600 0 0 0 2.200 2.500"/>`,
  cloud:`<path d="M7.500 16a4 4 0 0 1 .3-8 5.500 5.500 0 0 1 10.500 1.600 3.300 3.300 0 0 1-.6 6.400z"/><path d="M9 19v2.500M12.500 19v2.500M16 19v2.500"/>`,
  satellite:`<rect x="9" y="9" width="6" height="6" rx="1"/><rect x="1.500" y="9.500" width="5.500" height="5" rx=".6"/><rect x="17" y="9.500" width="5.500" height="5" rx=".6"/><path d="M7 12h2M15 12h2M4.250 9.500v5M19.750 9.500v5M12 15v2.500M9.500 20a2.500 2.500 0 0 1 5 0"/>`,
  scales:`<path d="M12 4v16M7 20h10M5 8h14M5 8l-2.500 6a2.500 2.500 0 0 0 5 0zM19 8l-2.500 6a2.500 2.500 0 0 0 5 0z"/>`,
  sprout:`<path d="M12 22v-9M12 13c0-4-3-6.500-7.500-6.500C4.500 10.500 7.500 13 12 13zM12 11c0-3.200 2.500-5.500 6.500-5.500 0 3.500-2.500 5.500-6.500 5.500z"/>`,
  person:`<circle cx="12" cy="8" r="3.400"/><path d="M5 21c0-4 3-7 7-7s7 3 7 7"/>`,
  check:`<path d="M5 12.500l4.500 4.500L19 7.500" stroke-width="2.200"/>`,
  trend:`<path d="M3 17l5.500-5.500 4 3L20 7M15 7h5v5"/>`
};
const icon = (n, s = 24) => `<svg class="ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[n]}</svg>`;
document.querySelectorAll("[data-icon]").forEach(e => e.insertAdjacentHTML("afterbegin", icon(e.dataset.icon, +e.dataset.size || 24)));
document.querySelectorAll("[data-icon-g]").forEach(e => e.innerHTML = ICON[e.dataset.iconG]);

// ---------- helpers ----------
const OPT_COLOR = {
  "wheat -> rice":"#35A05A","wheat -> maize":"#9FCF4A","wheat -> cotton":"#8E9BA6","wheat -> soybean":"#E8A33D",
  "sugarbeet -> rice":"#E58BA6","sugarbeet -> maize":"#D46E90","sugarbeet -> cotton":"#F2B3C6","sugarbeet -> soybean":"#B9577A",
  "potato -> rice":"#D9925A","potato -> maize":"#C07A45","potato -> cotton":"#EDB98A","potato -> soybean":"#9C6238",
  "alfalfa (all year)":"#8F7FE0"};
const cap = s => s[0].toUpperCase() + s.slice(1);
const pretty = c => c === "sugarbeet" ? "sugar beet" : c;
const optLabel = o => { const m = OPTS[o]; return m.summer ? `${cap(pretty(m.winter))}, then ${pretty(m.summer)}` : "Alfalfa, all year"; };
const hex = h => [parseInt(h.slice(1,3),16)/255, parseInt(h.slice(3,5),16)/255, parseInt(h.slice(5,7),16)/255];
const mixc = (a,b,t) => [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t];
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
function ramp(stops, t){ t = clamp(t); const n = stops.length-1, i = Math.min(n-1, Math.floor(t*n)); return mixc(hex(stops[i]), hex(stops[i+1]), t*n - i); }
const RAMP_ROW = ["#8A6A45","#D2B35E","#A9D163","#63BD55"];     // bare soil, straw, young crop, dense crop
const RAMP_SOIL = ["#5A4330","#6E5A36","#4F6A38","#3B7238"];
const RAMP_WATER = ["#1F4F5A","#2F8E9C","#4CC3D0","#C4F1F4"];
const SOIL = hex("#4A3829"), VILLAGE = hex("#56605C");
const fmt = (v, d=0) => v.toLocaleString("en-US", {minimumFractionDigits:d, maximumFractionDigits:d});
const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs = {}, parent){ const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }

// ---------- scoring: the same scores and formula as notebook 11 ----------
let W = [1/3,1/3,1/3];
const EQ = [1/3,1/3,1/3], WATERW = [.5,.5,0];
const scoreOf = (i, o, w = W) => { const q = S[i][o]; return w[0]*q[2] + w[1]*q[3] + w[2]*q[4]; };
const ranked = (i, w = W) => OPTS.map((_,o) => [o, scoreOf(i,o,w)]).sort((a,b) => b[1]-a[1] || a[0]-b[0]);
let top = new Array(N);
const recompute = () => { for (let i=0;i<N;i++) top[i] = ranked(i)[0][0]; };
recompute();
(() => { let tot = 0; for (let i=0;i<N;i++){ const a = ranked(i,EQ)[0][0], b = ranked(i,WATERW)[0][0]; tot += (S[i][a][1]-S[i][b][1]) * 10 * C[i].farm * 100; } document.getElementById("totSave").textContent = Math.round(tot/1e6); })();

// ---------- the 3D land: field squares with crop rows ----------
class Land {
  constructor(cv, o){
    this.cv = cv; this.o = o;
    try { this.r = new THREE.WebGLRenderer({canvas:cv, antialias:true, alpha:true, powerPreference:"high-performance"}); }
    catch(e){ this.failed = true; const d = document.createElement("div"); d.className = "nogl"; d.textContent = "This 3D view needs WebGL, which is off in this browser. The rest of the page still works."; cv.parentNode.appendChild(d); return; }
    const r = this.r; r.setPixelRatio(Math.min(window.devicePixelRatio, 2)); r.outputEncoding = THREE.sRGBEncoding;
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
    const sc = this.scene = new THREE.Scene();
    this.cam = new THREE.PerspectiveCamera(o.fov || 32, 1, .1, 500);
    this.theta = o.theta; this.phi = o.phi; this.rad = o.rad; this.home = {theta:o.theta, phi:o.phi, rad:o.rad};
    this.target = new THREE.Vector3(o.tx || 0, o.ty || 0, o.tz || 0);

    sc.add(new THREE.HemisphereLight(0xffffff, 0x7a6a52, .86));
    const sun = new THREE.DirectionalLight(0xfff0cf, 1.0); sun.position.set(20, 17, 9); sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048); const s = sun.shadow.camera; s.left = -22; s.right = 22; s.top = 22; s.bottom = -22; s.near = 1; s.far = 80; sun.shadow.bias = -.0006; sun.shadow.normalBias = .02;
    sc.add(sun);
    const fill = new THREE.DirectionalLight(0x4cc3d0, .28); fill.position.set(-14, 6, -10); sc.add(fill);

    // a slice of Delta soil the fields sit on
    const lin = c => new THREE.Color(c).convertSRGBToLinear();
    const std = (c, extra = {}) => new THREE.MeshStandardMaterial({color:lin(c), roughness:.9, metalness:0, ...extra});
    const topSoil = new THREE.Mesh(new THREE.BoxGeometry(21, .7, 29), std(0x3E2F23)); topSoil.position.y = -.35; topSoil.receiveShadow = true; sc.add(topSoil);
    const sub = new THREE.Mesh(new THREE.BoxGeometry(21, 1.1, 29), std(0x261D17)); sub.position.y = -1.25; sc.add(sub);
    const water = new THREE.Mesh(new THREE.BoxGeometry(21, .28, 29), new THREE.MeshStandardMaterial({color:lin(0x2F8E9C), roughness:.3, metalness:.2, emissive:lin(0x0e3c44)})); water.position.y = -1.94; sc.add(water);
    // soft glow under the slice
    const g = document.createElement("canvas"); g.width = g.height = 256; const gx = g.getContext("2d"); const gr = gx.createRadialGradient(128,128,10,128,128,128);
    gr.addColorStop(0, "rgba(16,62,76,.42)"); gr.addColorStop(.45, "rgba(16,62,76,.16)"); gr.addColorStop(1, "rgba(16,62,76,0)"); gx.fillStyle = gr; gx.fillRect(0,0,256,256);
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(58, 58), new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(g), transparent:true, depthWrite:false}));
    glow.rotation.x = -Math.PI/2; glow.position.y = -2.3; sc.add(glow);

    if (o.stars){
      const sg = new THREE.BufferGeometry(), n = 700, p = new Float32Array(n*3);
      for (let i=0;i<n;i++){ const R = 120 + Math.random()*80, a = Math.random()*Math.PI*2, b = Math.random()*Math.PI*.42 + .12; p[i*3] = R*Math.cos(a)*Math.cos(b); p[i*3+1] = R*Math.sin(b); p[i*3+2] = R*Math.sin(a)*Math.cos(b); }
      sg.setAttribute("position", new THREE.BufferAttribute(p, 3));
      this.stars = new THREE.Points(sg, new THREE.PointsMaterial({color:0xece6d6, size:.55, transparent:true, opacity:.5})); sc.add(this.stars);
    }

    // field squares
    const tg = new THREE.BoxGeometry(.93, 1, .93); tg.translate(0, .5, 0);
    this.tiles = new THREE.InstancedMesh(tg, std(0xffffff), N); this.tiles.castShadow = true; this.tiles.receiveShadow = true; sc.add(this.tiles);
    // crop rows: three rounded ridges per square
    const rg = new THREE.CylinderGeometry(1, 1, .8, 12, 1); rg.rotateZ(Math.PI/2);
    this.rows = new THREE.InstancedMesh(rg, std(0xffffff, {roughness:.7}), N*3); this.rows.castShadow = true; this.rows.receiveShadow = true; sc.add(this.rows);
    // a few houses on squares that are mostly village
    const vill = C.map((c,i) => c.isFarm ? -1 : i).filter(i => i >= 0);
    this.houses = new THREE.InstancedMesh(new THREE.BoxGeometry(.24, .26, .24), std(0xece6d6, {roughness:.6}), vill.length*4); this.houses.castShadow = true;
    const d0 = new THREE.Object3D();
    vill.forEach((i,k) => [[-.22,-.2],[.2,-.24],[-.18,.22],[.24,.18]].forEach(([dx,dz],j) => { d0.position.set(C[i].col-10.5+dx, .31, C[i].row-14.5+dz); d0.scale.set(1, .8 + ((i*7+j*3)%5)/8, 1); d0.rotation.y = (i+j)*.4; d0.updateMatrix(); this.houses.setMatrixAt(k*4+j, d0.matrix); }));
    sc.add(this.houses);

    this.tH = new Float32Array(N).fill(.16); this.tHT = new Float32Array(N).fill(.16);
    this.rH = new Float32Array(N); this.rHT = new Float32Array(N);
    this.tC = new Float32Array(N*3); this.tCT = new Float32Array(N*3); this.rC = new Float32Array(N*3); this.rCT = new Float32Array(N*3);
    this.delay = new Float32Array(N); this.orient = new Uint8Array(N); this.jit = new Float32Array(N*3);
    for (let i=0;i<N;i++){ const c = C[i], x = c.col-10.5, z = c.row-14.5; this.delay[i] = Math.hypot(x, z)*.05; this.orient[i] = (c.id*2654435761 >>> 7) & 1; for (let k=0;k<3;k++) this.jit[i*3+k] = .82 + ((c.id*(k+3)*40503) % 97)/97*.36; }
    this.dummy = new THREE.Object3D(); this.col = new THREE.Color();

    // selection pin and hover frame
    const gold = new THREE.MeshStandardMaterial({color:0xf0c56a, emissive:0xf0c56a, emissiveIntensity:.55, roughness:.4});
    this.pin = new THREE.Group(); const cone = new THREE.Mesh(new THREE.ConeGeometry(.3, .62, 20), gold); cone.rotation.x = Math.PI; cone.position.y = .31;
    const ball = new THREE.Mesh(new THREE.SphereGeometry(.34, 24, 16), gold); ball.position.y = .82; this.pin.add(cone, ball); this.pin.visible = false; sc.add(this.pin);
    const frame = v => { const pts = [[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]].map(([a,b]) => new THREE.Vector3(a, 0, b)); return new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({color:v})); };
    this.selFrame = frame(0xf0c56a); this.hovFrame = frame(0xece6d6); this.selFrame.visible = this.hovFrame.visible = false; sc.add(this.selFrame, this.hovFrame);
    this.sel = -1; this.hov = -1;

    if (o.satellite) this.buildSatellite();

    this.t0 = performance.now(); this.intro = !RM;
    this.bind(); this.resize(); new ResizeObserver(() => this.resize()).observe(cv);
    this.visible = true; new IntersectionObserver(es => { this.visible = es[0].isIntersecting; }).observe(cv);
    this.loop = this.loop.bind(this); requestAnimationFrame(this.loop);
  }
  buildSatellite(){
    const sat = this.sat = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(.7, .7, 1.1), new THREE.MeshStandardMaterial({color:new THREE.Color(0xe2c98a).convertSRGBToLinear(), metalness:.5, roughness:.35}));
    const pm = new THREE.MeshStandardMaterial({color:new THREE.Color(0x2a6f9c).convertSRGBToLinear(), metalness:.4, roughness:.35, emissive:new THREE.Color(0x0a2233).convertSRGBToLinear()});
    const p1 = new THREE.Mesh(new THREE.BoxGeometry(1.9, .05, .85), pm), p2 = p1.clone(); p1.position.x = -1.4; p2.position.x = 1.4;
    const dish = new THREE.Mesh(new THREE.CylinderGeometry(.3, .08, .22, 20), new THREE.MeshStandardMaterial({color:0xece6d6, metalness:.3, roughness:.4})); dish.position.y = -.46;
    sat.add(body, p1, p2, dish); sat.scale.setScalar(1.25); this.scene.add(sat);
    this.beam = new THREE.Mesh(new THREE.ConeGeometry(2.6, 1, 40, 1, true), new THREE.MeshBasicMaterial({color:0x1fa3b8, transparent:true, opacity:.2, side:THREE.DoubleSide, depthWrite:false}));
    this.scene.add(this.beam);
    this.foot = new THREE.Mesh(new THREE.RingGeometry(2.45, 2.6, 64), new THREE.MeshBasicMaterial({color:0x1487a0, transparent:true, opacity:.9, side:THREE.DoubleSide, depthWrite:false}));
    this.foot.rotation.x = -Math.PI/2; this.scene.add(this.foot);
  }
  resize(){ const w = this.cv.clientWidth, h = this.cv.clientHeight; if (!w || !h) return; this.r.setSize(w, h, false); this.cam.aspect = w/h; this.cam.updateProjectionMatrix(); this.target.x = this.cam.aspect < 1.2 ? 0 : (this.o.tx || 0); this.rad = this.home.rad = Math.max(this.o.rad, (this.o.fitK || 60)/this.cam.aspect); }
  set(v){ for (let i=0;i<N;i++){ this.tHT[i] = v.tH[i]; this.rHT[i] = v.rH[i]; for (let j=0;j<3;j++){ this.tCT[i*3+j] = v.tC[i][j]; this.rCT[i*3+j] = v.rC[i][j]; } }
    if (!this.started){ this.tC.set(this.tCT); this.rC.set(this.rCT); this.tH.set(this.tHT); this.rH.set(this.rHT); this.started = true; } }
  bind(){
    const cv = this.cv; let drag = null, moved = 0;
    cv.addEventListener("pointerdown", e => { drag = {x:e.clientX, y:e.clientY, th:this.theta, ph:this.phi}; moved = 0; this.userMoved = true; });
    window.addEventListener("pointermove", e => {
      if (drag){ const dx = e.clientX-drag.x, dy = e.clientY-drag.y; moved = Math.max(moved, Math.abs(dx)+Math.abs(dy)); this.theta = drag.th - dx*.006; if (this.o.interactive) this.phi = clamp(drag.ph - dy*.005, .3, 1.35); }
      else if (this.o.interactive && e.target === cv){ const i = this.pick(e); this.hov = i; const r = cv.getBoundingClientRect(); this.o.onHover && this.o.onHover(i, e.clientX-r.left, e.clientY-r.top); }
    });
    window.addEventListener("pointerup", e => { if (drag && moved < 6 && this.o.interactive && e.target === cv){ const i = this.pick(e); if (i >= 0) this.select(i); } drag = null; });
    cv.addEventListener("pointerleave", () => { this.hov = -1; this.o.onHover && this.o.onHover(-1); });
  }
  pick(e){
    const r = this.cv.getBoundingClientRect(), m = new THREE.Vector2(((e.clientX-r.left)/r.width)*2-1, -((e.clientY-r.top)/r.height)*2+1);
    const ray = new THREE.Raycaster(); ray.setFromCamera(m, this.cam);
    const hit = ray.intersectObjects([this.tiles, this.rows])[0]; if (!hit) return -1;
    return hit.object === this.tiles ? hit.instanceId : Math.floor(hit.instanceId/3);
  }
  select(i){ this.sel = i; this.o.onSelect && this.o.onSelect(i); }
  zoom(f){ this.rad = clamp(this.rad*f, 18, 110); }
  reset(){ Object.assign(this, this.home); }
  loop(now){
    requestAnimationFrame(this.loop);
    if (!this.visible || this.failed) return;
    const t = (now - this.t0)/1000, dt = Math.min(.1, (now - (this.last || now))/1000), k = RM ? 1 : 1 - Math.exp(-dt*5), d = this.dummy; this.last = now;
    if (this.o.autoRotate && !RM && !this.userMoved) this.theta = this.home.theta + Math.sin(t*.07)*.3;
    for (let i=0;i<N;i++){
      this.tH[i] += (this.tHT[i]-this.tH[i])*k; this.rH[i] += (this.rHT[i]-this.rH[i])*k;
      for (let j=0;j<3;j++){ this.tC[i*3+j] += (this.tCT[i*3+j]-this.tC[i*3+j])*k; this.rC[i*3+j] += (this.rCT[i*3+j]-this.rC[i*3+j])*k; }
      let g = 1; if (this.intro){ const p = clamp((t - .25 - this.delay[i])/.8); g = 1 - Math.pow(1-p, 3); }
      const c = C[i], x = c.col-10.5, z = c.row-14.5, th = Math.max(.02, this.tH[i]*g), lift = i === this.hov ? 1.22 : 1;
      d.position.set(x, 0, z); d.rotation.set(0, 0, 0); d.scale.set(g || .001, th, g || .001); d.updateMatrix(); this.tiles.setMatrixAt(i, d.matrix);
      this.col.setRGB(Math.min(1, this.tC[i*3]*lift), Math.min(1, this.tC[i*3+1]*lift), Math.min(1, this.tC[i*3+2]*lift)).convertSRGBToLinear(); this.tiles.setColorAt(i, this.col);
      const o = this.orient[i], rh = this.rH[i]*g;
      this.col.setRGB(Math.min(1, this.rC[i*3]*lift), Math.min(1, this.rC[i*3+1]*lift), Math.min(1, this.rC[i*3+2]*lift)).convertSRGBToLinear();
      for (let q=0;q<3;q++){
        const off = (q-1)*.3, h = rh*this.jit[i*3+q];
        d.position.set(o ? x+off : x, th, o ? z : z+off); d.rotation.set(0, o ? Math.PI/2 : 0, 0);
        if (h < .02) d.scale.set(.001, .001, .001); else d.scale.set(g, h, .13);
        d.updateMatrix(); this.rows.setMatrixAt(i*3+q, d.matrix); this.rows.setColorAt(i*3+q, this.col);
      }
    }
    if (this.intro && t > 2.6) this.intro = false;
    this.tiles.instanceMatrix.needsUpdate = this.rows.instanceMatrix.needsUpdate = true; this.tiles.instanceColor.needsUpdate = this.rows.instanceColor.needsUpdate = true;
    const place = (f, i) => { const c = C[i]; f.position.set(c.col-10.5, this.tH[i] + .03, c.row-14.5); f.visible = true; };
    if (this.sel >= 0){ place(this.selFrame, this.sel); const c = C[this.sel]; this.pin.position.set(c.col-10.5, this.tH[this.sel] + this.rH[this.sel] + .35 + (RM ? 0 : Math.sin(t*2.2)*.09), c.row-14.5); this.pin.visible = true; } else { this.selFrame.visible = this.pin.visible = false; }
    if (this.hov >= 0 && this.hov !== this.sel) place(this.hovFrame, this.hov); else this.hovFrame.visible = false;
    if (this.sat){
      const a = RM ? .9 : t*.22, x = 6.5*Math.cos(a), z = 9.5*Math.sin(a), y = 10.5 + Math.sin(a*2)*.35, base = 1.25;
      this.sat.position.set(x, y, z); this.sat.rotation.set(Math.sin(a)*.12, -a, 0);
      this.beam.position.set(x, base + (y-base-.6)/2, z); this.beam.scale.set(1, y-base-.6, 1); this.foot.position.set(x, base, z);
      if (this.stars) this.stars.rotation.y = t*.003;
    }
    const p = this.phi, th = this.theta;
    this.cam.position.set(this.target.x + this.rad*Math.sin(p)*Math.sin(th), this.rad*Math.cos(p), this.target.z + this.rad*Math.sin(p)*Math.cos(th));
    this.cam.lookAt(this.target); this.r.render(this.scene, this.cam);
  }
}
const greenView = v => { const t = v == null ? 0 : clamp((v-.3)/.58); return {tH:.16, rH:.03 + t*.46, tC:ramp(RAMP_SOIL, t), rC:ramp(RAMP_ROW, t)}; };
const villageView = {tH:.18, rH:0, tC:VILLAGE, rC:VILLAGE};
const pack = fn => { const v = {tH:[], rH:[], tC:[], rC:[]}; for (let i=0;i<N;i++){ const q = C[i].isFarm ? fn(i) : villageView; v.tH.push(q.tH); v.rH.push(q.rH); v.tC.push(q.tC); v.rC.push(q.rC); } return v; };

// ---------- hero: one farming year, seen from orbit ----------
const hero = new Land(document.getElementById("heroCanvas"), {stars:false, satellite:true, autoRotate:true, theta:-.52, phi:1.0, rad:64, fitK:92, tx:-9.5, tz:-1, fov:32});
const dots = document.getElementById("dots"); for (let k=0;k<12;k++) dots.appendChild(document.createElement("i"));
let month = 0, playing = !RM, timer = null;
function showMonth(k){
  month = k;
  if (!hero.failed) hero.set(pack(i => greenView(C[i].ndvi[k])));
  document.getElementById("monthName").textContent = MONTHS[k];
  document.getElementById("monthWhat").textContent = WHAT[k];
  [...dots.children].forEach((d,j) => d.classList.toggle("on", j <= k));
}
const playBtn = document.getElementById("playBtn");
function setPlay(on){ playing = on; playBtn.textContent = on ? "Pause" : "Play"; clearInterval(timer); if (on) timer = setInterval(() => showMonth((month+1) % 12), 1700); }
playBtn.onclick = () => setPlay(!playing);
showMonth(RM ? 2 : 0); setPlay(false); if (!RM) setTimeout(() => setPlay(true), 2800);

// ---------- 1: water tubes ----------
(() => {
  const med = o => { const v = C.map((c,i) => c.isFarm ? S[i][o][1] : null).filter(v => v != null).sort((a,b)=>a-b); return v[Math.floor(v.length/2)]; };
  const rain = D.month.rain_mm.reduce((a,b)=>a+b, 0), rice = med(OPTS.findIndex(o => o.name === "wheat -> rice")), soy = med(OPTS.findIndex(o => o.name === "wheat -> soybean")), max = rice*1.12;
  [["Rain", rain], ["Rice", rice], ["Soy", soy]].forEach(([id, v]) => { document.getElementById("t"+id).style.setProperty("--h", (v/max*100) + "%"); document.getElementById("v"+id).textContent = fmt(v) + " mm"; });
})();
const seen = new IntersectionObserver((es, ob) => es.forEach(e => { if (e.isIntersecting){ e.target.classList.add("seen"); ob.unobserve(e.target); } }), {threshold:.35});
["tubes","howGrid"].forEach(id => { const e = document.getElementById(id); if (RM) e.classList.add("seen"); else seen.observe(e); });

// ---------- 3: try it ----------
let layer = "best";
const tip = document.getElementById("tip");
const ex = new Land(document.getElementById("exCanvas"), {interactive:true, theta:-.4, phi:.84, rad:54, fitK:67, ty:-1.2, fov:32,
  onHover:(i, x, y) => { if (i < 0){ tip.style.opacity = 0; return; } tip.innerHTML = `<b>Field ${C[i].id}</b>&nbsp; ${hoverText(i)}`; tip.style.left = x+"px"; tip.style.top = y+"px"; tip.style.opacity = 1; },
  onSelect:i => selectCell(i)});
const saveOf = i => { const a = ranked(i, EQ)[0][0], b = ranked(i, WATERW)[0][0]; return (S[i][a][1] - S[i][b][1]) * 10; };   // m3 per hectare a year
function hoverText(i){
  const c = C[i]; if (!c.isFarm) return "mostly village";
  if (layer === "best") return optLabel(top[i]);
  if (layer === "water") return `modeled candidate difference ${fmt(saveOf(i))} m³ per hectare a year`;
  return `winter greenness ${c.wN.toFixed(2)}`;
}
function paint(){
  if (ex.failed) return;
  ex.set(pack(i => {
    if (layer === "best"){ const s = scoreOf(i, top[i]), col = hex(OPT_COLOR[OPTS[top[i]].name]); return {tH:.16, rH:.14 + clamp((s-.45)/.45)*.42, tC:mixc(SOIL, col, .6), rC:col}; }
    if (layer === "water"){ const v = saveOf(i), t = clamp((v-700)/1600), col = ramp(RAMP_WATER, t); return {tH:.2 + t*1.9, rH:0, tC:col, rC:col}; }
    return greenView(C[i].wN);
  }));
  note();
}
function note(){
  const n = document.getElementById("mapnote");
  if (layer === "best"){
    const seenO = [...new Set(C.map((c,i) => c.isFarm ? top[i] : null).filter(v => v != null))];
    n.innerHTML = seenO.map(o => `<span><i style="background:${OPT_COLOR[OPTS[o].name]}"></i>${optLabel(o)}</span>`).join("") + `<span>Taller rows mean a stronger score</span>`;
  } else if (layer === "water") n.innerHTML = `Modeled difference between candidate rotations <span class="ramp" style="background:linear-gradient(90deg,${RAMP_WATER.join(",")})"></span> embedded data; not measured farmer savings`;
  else n.innerHTML = `Winter greenness, Sentinel-2 <span class="ramp" style="background:linear-gradient(90deg,${RAMP_ROW.join(",")})"></span> bare soil to dense crop`;
}
document.querySelectorAll(".seg button").forEach(b => b.onclick = () => { layer = b.dataset.l; document.querySelectorAll(".seg button").forEach(x => { x.classList.toggle("on", x === b); x.setAttribute("aria-checked", x === b); }); paint(); });

const sl = ["wLand","wWater","wPrac"].map(id => document.getElementById(id));
const outs = ["oLand","oWater","oPrac"].map(id => document.getElementById(id));
function readW(){
  const v = sl.map(s => +s.value), sum = v.reduce((a,b)=>a+b, 0);
  const notice = document.getElementById("weightNotice");
  if (!sum){
    sl.forEach(s => s.value = "5");
    W = [1/3,1/3,1/3];
    notice.textContent = "All priorities were zero, so priorities were reset to balanced.";
  } else {
    W = v.map(x => x/sum);
    notice.textContent = "";
  }
  sl.forEach(s => s.style.setProperty("--p", (s.value*10) + "%"));
  outs.forEach((o,k) => o.textContent = Math.round(W[k]*100) + "%");
  document.querySelectorAll(".choice").forEach(c => { const w = c.dataset.w.split(",").map(Number), s2 = w.reduce((a,b)=>a+b,0); c.classList.toggle("on", w.every((x,k) => Math.abs(x/s2 - W[k]) < 1e-9)); });
  recompute(); paint(); summary();
  if (selectedIndex >= 0) scheduleEvaluation();
}
sl.forEach(s => s.addEventListener("input", readW));
document.querySelectorAll(".choice").forEach(c => c.onclick = () => { c.dataset.w.split(",").forEach((x,k) => sl[k].value = x); readW(); });
function summary(){
  const cnt = {};
  for (let i=0;i<N;i++){ if (C[i].isFarm) cnt[top[i]] = (cnt[top[i]]||0) + 1; }
  const order = Object.keys(cnt).sort((a,b) => cnt[b]-cnt[a]);
  document.getElementById("summary").textContent = `Across the map: ${order.slice(0,2).map(o => `${optLabel(+o)} in ${cnt[o]} fields`).join(", and ")}${order.length > 2 ? `, and ${order.length-2} other pairs in the rest` : ""}.`;
}
const card = document.getElementById("card");
const recommendationCache = new Map();
let selectedIndex = -1, selectionRequest = 0, debounceTimer = null;
let recommendationsController = null, evaluationController = null;
let selectedRecommendations = null, selectedRecommendationsPromise = null;
card.addEventListener("click", event => {
  if (event.target.closest("[data-retry]") && selectedIndex >= 0) selectCell(selectedIndex);
});
function addText(parent, tag, text, className){
  const child = document.createElement(tag);
  if (className) child.className = className;
  child.textContent = text == null ? "" : String(text);
  parent.appendChild(child);
  return child;
}
function cardHeader(cell){
  const head = addText(card, "div", "", "reco-header");
  addText(head, "b", `Cell ${cell.id}`);
  addText(head, "span", `${Math.round(cell.farm*100)}% farmland`);
}
function renderState(cell, message, isError = false, retry = false){
  card.replaceChildren();
  cardHeader(cell);
  const state = addText(card, "div", message, `card-state${isError ? " error" : ""}`);
  state.setAttribute("role", isError ? "alert" : "status");
  if (retry){
    const button = addText(state, "button", "Retry");
    button.type = "button";
    button.dataset.retry = "true";
  }
}
function selectCell(i){
  selectedIndex = i;
  const cell = C[i], requestId = ++selectionRequest;
  clearTimeout(debounceTimer);
  if (recommendationsController) recommendationsController.abort();
  if (evaluationController) evaluationController.abort();
  selectedRecommendations = recommendationCache.get(cell.id) || null;
  recommendationsController = null;
  selectedRecommendationsPromise = selectedRecommendations
    ? Promise.resolve(selectedRecommendations)
    : null;
  renderState(cell, "Loading results from the Field Shift backend…");
  if (!selectedRecommendationsPromise){
    recommendationsController = new AbortController();
    selectedRecommendationsPromise = API.getRecommendations(cell.id, recommendationsController.signal)
      .then(data => {
        recommendationCache.set(cell.id, data);
        return data;
      });
  }
  requestEvaluation(requestId, cell, selectedRecommendationsPromise);
}
function scheduleEvaluation(){
  const cell = C[selectedIndex], requestId = ++selectionRequest;
  if (evaluationController) evaluationController.abort();
  renderState(cell, "Updating results for these priorities…");
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    requestEvaluation(requestId, cell, selectedRecommendationsPromise);
  }, 250);
}
async function requestEvaluation(requestId, cell, recommendationPromise){
  if (requestId !== selectionRequest) return;
  evaluationController = new AbortController();
  try{
    const weights = {land:+sl[0].value, water:+sl[1].value, practice:+sl[2].value};
    const [published, evaluation] = await Promise.all([
      recommendationPromise,
      API.evaluateWeights(cell.id, weights, evaluationController.signal)
    ]);
    if (requestId !== selectionRequest || C[selectedIndex].id !== cell.id) return;
    selectedRecommendations = published;
    renderResults(cell, published, evaluation);
  }catch(error){
    if (error.name === "AbortError" || requestId !== selectionRequest) return;
    const message = error.status === 503
      ? "The backend is running, but its data is not ready. Check the backend health and dataset files."
      : error.message || "Could not load results from the backend.";
    renderState(cell, message, true, true);
  }
}
const cropIcon = {wheat:"wheat", rice:"rice", maize:"maize", cotton:"cotton", soybean:"soybean", sugarbeet:"sugarbeet", potato:"potato", alfalfa:"alfalfa"};
function optionInfo(option){
  const index = OPTS.findIndex(item => item.name === option);
  return index < 0 ? null : OPTS[index];
}
function renderCropChip(parent, crop, season){
  const chip = addText(parent, "div", "", "crop-step");
  if (cropIcon[crop]) chip.insertAdjacentHTML("afterbegin", icon(cropIcon[crop], 34));
  const name = addText(chip, "div", "", "crop-name");
  addText(name, "b", cap(pretty(crop)));
  addText(name, "small", season);
}
function formatOption(option){
  const info = optionInfo(option);
  if (!info) return option || "Rotation unavailable";
  const winter = cap(pretty(info.winter || "alfalfa"));
  return info.summer
    ? `${winter} → ${cap(pretty(info.summer))}`
    : `${winter} (all year)`;
}
function renderPair(parent, option){
  const info = optionInfo(option);
  if (!info){ addText(parent, "p", option || "Rotation unavailable"); return; }
  const pair = addText(parent, "div", "", info.summer ? "crop-sequence" : "crop-sequence solo");
  renderCropChip(pair, info.winter || "alfalfa", info.summer ? "Winter" : "All year");
  if (info.summer){
    addText(pair, "span", "→", "sequence-arrow");
    renderCropChip(pair, info.summer, "Summer");
  }
}
function renderMeter(parent, label, value, color){
  const row = addText(parent, "div", "", "criterion");
  addText(row, "span", label);
  const track = addText(row, "span", "", "b");
  const fill = document.createElement("span");
  const safeValue = Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;
  fill.style.width = `${Math.round(safeValue*100)}%`;
  fill.style.background = color;
  track.appendChild(fill);
  addText(row, "span", Number.isFinite(value) ? value.toFixed(2) : "—", "v");
}
function irrigationComparison(evaluation, alternative, topOption){
  const difference = evaluation.modeled_irrigation_difference;
  if (
    !difference ||
    difference.reference !== "land-water alternative minus custom top option" ||
    !Number.isFinite(difference.m3_ha_year)
  ){
    return "Modeled difference vs. the recommended rotation is unavailable.";
  }
  const amount = fmt(Math.abs(difference.m3_ha_year));
  const baseline = formatOption(topOption);
  if (difference.m3_ha_year < 0){
    return `About ${amount} m³/ha/year less modeled irrigation than ${baseline}.`;
  }
  if (difference.m3_ha_year > 0){
    return `About ${amount} m³/ha/year more modeled irrigation than ${baseline}.`;
  }
  return `No modeled irrigation difference from ${baseline}.`;
}
function addOptionCautions(parent, option){
  if (option && option.includes("rice")){
    addText(parent, "p", "Rice estimates exclude additional seepage losses.", "reco-caution");
  }
  if (option && option.includes("sugarbeet")){
    addText(parent, "p", "Sugarbeet land suitability uses the notebook's special winter-crop treatment.", "reco-caution");
  }
}
function addImputationNotice(parent, record){
  const flags = [];
  if (record && record.suit_filled) flags.push("Suitability uses a median-filled source value.");
  if (record && record.water_filled) flags.push("Irrigation uses a median-filled source value.");
  if (flags.length) addText(parent, "p", flags.join(" "), "reco-caution");
}
function addImputationSummary(parent, record){
  if (record && (record.suit_filled || record.water_filled)){
    addText(parent, "p", "This rotation includes median-filled source data.", "reco-caution");
  }
}
function renderResults(cell, published, evaluation){
  card.replaceChildren();
  cardHeader(cell);
  if (!published.farm_eligible || !evaluation.farm_eligible || evaluation.result === "not_eligible"){
    addText(card, "p", "This cell is not eligible for crop recommendations. No rotations are recommended.", "reco-nonfarm");
    renderWarnings(published.warnings);
    return;
  }
  const topThree = evaluation.top_three || [];
  const best = topThree[0];
  if (!best){
    renderState(cell, "The backend returned no ranked options.", true, true);
    return;
  }
  const recommendation = addText(card, "section", "", "recommendation");
  addText(recommendation, "div", "Recommended under your priorities", "reco-eyebrow");
  const hero = addText(recommendation, "div", "", "reco-hero");
  renderPair(hero, best.option);
  const score = addText(hero, "div", "", "score-badge");
  addText(score, "b", `${Math.round(best.score*100)} / 100`);
  addText(score, "span", "Comparative score");
  const metric = addText(recommendation, "div", "", "primary-metric");
  addText(metric, "span", "Modeled irrigation");
  addText(metric, "b", Number.isFinite(best.irrig_mm_year) ? `${fmt(best.irrig_mm_year)} mm/year` : "Not available");
  addOptionCautions(recommendation, best.option);
  addImputationSummary(recommendation, best);

  const why = document.createElement("details");
  why.className = "reco-details why-recommendation";
  addText(why, "summary", "Why this recommendation?");
  addText(why, "p", best.reason || "");
  const criteria = addText(why, "div", "", "crit");
  renderMeter(criteria, "Good land", best.components && best.components.s_land, "#8FD46B");
  renderMeter(criteria, "Less water", best.components && best.components.s_water, "#4CC3D0");
  renderMeter(criteria, "Local practice", best.components && best.components.s_practice, "#F0C56A");
  const contributions = best.weighted_contributions || {};
  addText(
    why,
    "p",
    `Weighted contributions: land ${fmt(contributions.land || 0, 3)}, water ${fmt(contributions.water || 0, 3)}, local practice ${fmt(contributions.practice || 0, 3)}.`,
    "reco-supporting"
  );
  addImputationNotice(why, best);
  card.appendChild(why);

  const others = addText(card, "section", "", "other-options");
  addText(others, "h4", "Other options");
  topThree.slice(1).forEach(item => {
    const row = addText(others, "details", "", "other-option");
    const summary = addText(row, "summary", "", "other-option-row");
    addText(summary, "span", formatOption(item.option));
    addText(summary, "b", `${Math.round(item.score*100)} / 100`);
    addText(row, "p", item.reason || "");
  });

  const alternative = evaluation.land_water_alternative;
  if (alternative){
    const section = addText(card, "section", "", "water-alternative");
    const title = addText(section, "div", "", "alternative-heading");
    title.insertAdjacentHTML("afterbegin", icon("drop", 22));
    addText(title, "h4", "Land + water alternative");
    addText(section, "div", formatOption(alternative.option), "alternative-option");
    addText(section, "p", Number.isFinite(alternative.irrig_mm_year) ? `Modeled irrigation: ${fmt(alternative.irrig_mm_year)} mm/year.` : "Modeled irrigation is not available.", "alternative-metric");
    addText(section, "p", irrigationComparison(evaluation, alternative, best.option), "alternative-difference");
    addOptionCautions(section, alternative.option);
    addImputationSummary(section, alternative);
    const alternativeWhy = addText(section, "details", "", "alternative-why");
    addText(alternativeWhy, "summary", "Why this alternative?");
    addText(alternativeWhy, "p", alternative.reason || "");
  }

  const confidence = addText(card, "details", "", "reco-details confidence-method");
  addText(confidence, "summary", "Confidence & method");
  const defaults = published.published_default_analysis || {};
  const level = String(defaults.label || "not available");
  addText(confidence, "p", `Published default confidence: ${level}.`);
  const robustness = [];
  if (Number.isFinite(defaults.robustness)) robustness.push(`whole rotation ${Math.round(defaults.robustness*100)}%`);
  if (Number.isFinite(defaults.winter_robustness)) robustness.push(`winter ${Math.round(defaults.winter_robustness*100)}%`);
  if (Number.isFinite(defaults.summer_robustness)) robustness.push(`summer ${Math.round(defaults.summer_robustness*100)}%`);
  if (robustness.length) addText(confidence, "p", `Published robustness: ${robustness.join("; ")}.`);
  addText(confidence, "p", "These figures describe the default notebook analysis and are not recalculated for custom priorities. Scores are comparative, not probabilities of success.");
  renderWarnings(published.warnings);

  const localOption = OPTS[top[selectedIndex]] && OPTS[top[selectedIndex]].name;
  if (localOption !== best.option) addText(card, "p", "Map preview differs from this result.", "map-mismatch");
}
function renderWarnings(warnings){
  if (!Array.isArray(warnings) || !warnings.length) return;
  const list = addText(card, "ul", "", "card-warnings");
  warnings.forEach(warning => addText(list, "li", warning));
}
document.getElementById("zIn").onclick = () => ex.zoom(1/1.18);
document.getElementById("zOut").onclick = () => ex.zoom(1.18);
document.getElementById("zReset").onclick = () => ex.reset();
document.getElementById("exCanvas").addEventListener("keydown", e => {
  const mv = {ArrowUp:[-1,0], ArrowDown:[1,0], ArrowLeft:[0,-1], ArrowRight:[0,1]}[e.key]; if (!mv) return; e.preventDefault();
  const cur = ex.sel >= 0 ? C[ex.sel] : C[GRID["14_10"]];
  const nx = GRID[clamp(cur.row + mv[0], 1, 28) + "_" + clamp(cur.col + mv[1], 1, 20)];
  if (nx != null) ex.select(nx);
});
{ const start = GRID["14_10"]; readW(); if (!ex.failed) ex.sel = start; selectCell(start); }

// ---------- 4: results ----------
(() => {
  const med = a => { const v = a.filter(x => x != null).sort((p,q)=>p-q); return v[Math.floor(v.length/2)]; };
  const f = C.filter(c => c.isFarm);
  document.getElementById("duo").innerHTML = [["Winter crop", med(f.map(c => c.wrob)), "#F0C56A"], ["Summer crop", med(f.map(c => c.srob)), "#8FD46B"]]
    .map(([l,v,col]) => `<div class="r"><span>${l}</span><span class="t"><span style="width:${v*100}%;background:${col}"></span></span><b>${Math.round(v*100)}%</b></div>`).join("");
  const svg = document.getElementById("chLandsat"), W0 = 420, H0 = 150, L = 6, R = 6, T = 26, B = 22, w = W0-L-R, h = H0-T-B;
  const Y = D.landsat.years, V = D.landsat.ndvi, lo = .44, hi = .84;
  const x = yr => L + (yr-Y[0])/(Y[Y.length-1]-Y[0])*w, y = v => T + h - (v-lo)/(hi-lo)*h;
  el("path", {d:"M" + Y.map((yr,k) => `${x(yr)} ${y(V[k])}`).join(" L"), fill:"none", stroke:"rgba(62,155,63,.5)", "stroke-width":1.5, "stroke-linejoin":"round"}, svg);
  const f2 = yr => D.landsat.intercept + D.landsat.slope*yr;
  el("line", {x1:x(Y[0]), y1:y(f2(Y[0])), x2:x(Y[Y.length-1]), y2:y(f2(Y[Y.length-1])), stroke:"#3E9B3F", "stroke-width":3, "stroke-linecap":"round"}, svg);
  [[1985,"start"],[2024,"end"]].forEach(([yr,a]) => { const t = el("text", {x:x(yr), y:H0-4, "text-anchor":a}, svg); t.textContent = yr; });
  const t = el("text", {x:x(Y[0]), y:14, "text-anchor":"start"}, svg); t.textContent = "Winter greenness, with the long-term trend";
})();

// ---------- stepper ----------
const ids = ["problem","how","try","results","trust"], links = [...document.querySelectorAll(".bar ol a")];
const io = new IntersectionObserver(es => es.forEach(e => { if (!e.isIntersecting) return; const k = ids.indexOf(e.target.id); links.forEach((a,j) => { a.classList.toggle("on", j === k); a.classList.toggle("done", j < k); }); }), {rootMargin:"-45% 0px -50% 0px"});
ids.forEach(id => io.observe(document.getElementById(id)));
})();
