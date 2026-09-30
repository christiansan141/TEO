/* ============ Ozonocleaner · TEO — núcleo común ============
   Mismo protocolo y misma tarjeta que Teo: un relé que enciende el generador,
   un ESP32-C3 que cuenta el tiempo y una OLED con sensores táctiles.
   La app solo elige el área, calcula el tiempo y envía órdenes. */
const $ = (id) => document.getElementById(id);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const pad2 = (n) => String(n).padStart(2, "0");
const mmss = (sec) => { const v = Math.max(0, Math.ceil(sec)); return pad2(Math.floor(v / 60)) + ":" + pad2(v % 60); };
const store = {
  get(k){ try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v){ try { localStorage.setItem(k, v); } catch {} }
};
const jget = (k, d) => { try { const v = JSON.parse(store.get(k)); return v == null ? d : v; } catch { return d; } };
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));

/* ---- Protocolo (heredado de Teo; UUID y códigos por confirmar con el firmware) ---- */
const SERVICE_UUID = "2bef07a5-297a-4071-8eaa-1b5ad35bd18e";
const STATE_UUID   = "f7ed213f-fcfc-418a-92d1-9b4d1ec14197";
const CMD_UUID     = "92483b33-6ebf-4a0f-beb3-8ab946488f9c";
const OP = { RELAY: 0x01, SETPOINT: 0x02, TIMER: 0x03, STOP: 0x04 };
function decodeState(dv){
  if (dv.byteLength < 10) return null;               // una lectura corta no se interpreta
  const tm = dv.getUint16(7, true), mask = dv.getUint8(4);
  return {
    relay: !!(mask & 1),
    timerSec: tm === 0xFFFF ? null : tm,
    errors: dv.getUint8(9),
    owner: dv.byteLength > 10 ? dv.getUint8(10) : 2   // 0 sin elegir · 1 equipo · 2 app
  };
}
const cmdStop  = () => Uint8Array.of(OP.STOP);
const cmdTimer = (sec) => { const b = new DataView(new ArrayBuffer(3)); b.setUint8(0, OP.TIMER); b.setUint16(1, sec, true); return new Uint8Array(b.buffer); };

/* ---- Área → tiempo (FÓRMULA PROVISIONAL, editable en Ajustes) ----
   volumen = área × altura;  minutos = volumen × factor (min/m³), con tope. */
const AREA_MIN = 4, AREA_MAX = 120;
const PRESETS = [
  { n: "Baño", a: 6 }, { n: "Habitación", a: 14 }, { n: "Consultorio", a: 20 },
  { n: "Sala", a: 30 }, { n: "Local", a: 60 }
];
const CFG = Object.assign({ h: 2.5, k: 0.6, max: 120 }, jget("oz.cfg", {}));
function saveCfg(){ store.set("oz.cfg", JSON.stringify(CFG)); emit(); }
function calc(area){
  const vol = area * CFG.h, raw = vol * CFG.k, min = clamp(Math.ceil(raw), 1, CFG.max);
  return { vol, min, sec: min * 60, capped: raw > CFG.max };
}
const fmtMin = (m) => m < 60 ? m + " min" : Math.floor(m / 60) + " h" + (m % 60 ? " " + pad2(m % 60) + " min" : "");
const fmtDim = (a) => { const s = Math.sqrt(a); return "≈ " + s.toFixed(1) + " × " + s.toFixed(1) + " m"; };

/* ---- Estado ---- */
const S = { connected: false, owner: 0, relay: false, timerSec: null, total: 0, errors: 0,
            area: clamp(+store.get("oz.area") || 18, AREA_MIN, AREA_MAX) };
let huboHardware = false;
const subs = [];
const onChange = (fn) => subs.push(fn);
function emit(){ subs.forEach(f => f()); paintLock(); paintAlert(); }
const running = () => S.timerSec !== null;
function setArea(v){
  S.area = clamp(Math.round(v * 10) / 10, AREA_MIN, AREA_MAX);
  store.set("oz.area", S.area);
  emit();
}

/* ---- Quién manda ----
   Con el mando en el equipo (sensores táctiles) o sin enlace, la app solo mira:
   dejar botones que no hacen nada es peor que apagarlos, y simular es mentir. */
function lockReason(){
  if (!S.connected) return huboHardware ? "perdida" : null;
  if (S.owner === 1) return "local";
  if (S.owner !== 2) return "sin-mando";
  return null;
}
const appSinMando = () => lockReason() !== null;
const LOCK_TXT = {
  local: "<b>El equipo tiene el control.</b> Desde aquí solo se mira. Para mandar desde el móvil, elige <b>BLUETOOTH</b> en la pantalla del equipo.",
  "sin-mando": "<b>Falta elegir quién manda.</b> En la pantalla del equipo, elige <b>BLUETOOTH</b> para poder controlarlo desde aquí.",
  perdida: "<b>Sin enlace con el equipo.</b> Se muestra el último dato recibido y no se envían órdenes. Pulsa <b>Conectar</b>."
};
function paintLock(){
  const r = lockReason();
  document.body.classList.toggle("solo-mirar", !!r);
  document.querySelectorAll("[data-cmd]").forEach(e => { e.disabled = !!r; });
  const box = $("local"); if (!box) return;
  box.classList.toggle("show", !!r);
  if (r) $("localTxt").innerHTML = LOCK_TXT[r];
}
function paintAlert(){
  const box = $("alert"); if (!box) return;
  box.textContent = S.errors ? "Aviso del equipo · código " + S.errors : "";
  box.classList.toggle("show", !!S.errors);
}

let toastTimer;
function toast(msg){
  const t = $("toast"); if (!t) return;
  t.textContent = msg; t.classList.toggle("arriba", !!document.querySelector(".sheet")); t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 2400);
}

/* ---- Sesión ---- */
function send(bytes){
  if (appSinMando()) return;
  if (S.connected && cmdChar) cmdChar.writeValue(bytes).catch(() => toast("No se pudo enviar"));
}
function startSession(sec){
  if (appSinMando()){ toast(lockReason() === "perdida" ? "Sin enlace con el equipo" : "El mando lo tiene el equipo"); return false; }
  if (running()){ toast("Ya hay una sesión en marcha"); return false; }
  sec = Math.round(sec);
  if (!(sec > 0)){ toast("Elige un área mayor que cero"); return false; }
  S.total = sec; S.timerSec = sec; S.relay = true;
  send(cmdTimer(sec)); emit(); toast("Sesión iniciada");
  return true;
}
function stopSession(){
  if (appSinMando()){ toast("El mando lo tiene el equipo"); return; }
  S.timerSec = null; S.relay = false;
  send(cmdTimer(0)); emit(); toast("Sesión detenida");
}
function paroTotal(){
  if (appSinMando()){ toast("El mando lo tiene el equipo"); return; }
  S.timerSec = null; S.relay = false;
  send(cmdStop()); emit(); toast("Todo apagado");
}
function frac(){ return running() && S.total > 0 ? clamp(1 - S.timerSec / S.total, 0, 1) : 0; }

/* ---- Programación ----
   Aquí solo se guarda y se muestra. El disparo real con la app cerrada necesita
   reloj en la tarjeta (RTC/NTP) y una orden nueva en el protocolo: en esta
   maqueta el disparo funciona únicamente con la página abierta. */
const DIAS = ["D", "L", "M", "X", "J", "V", "S"];          // índice = Date.getDay()
const ORDEN = [1, 2, 3, 4, 5, 6, 0];                        // semana empezando en lunes
const DIAS_LARGO = ["domingo","lunes","martes","miércoles","jueves","viernes","sábado"];
const ymd = (d) => d.getFullYear() + "-" + pad2(d.getMonth() + 1) + "-" + pad2(d.getDate());
const addDays = (d, n) => { const x = new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); return x; };
const uid = () => Math.random().toString(36).slice(2, 9);
function seedSched(){
  const t = new Date(), sab = addDays(t, (6 - t.getDay() + 7) % 7 || 7);
  return [
    { id: uid(), label: "Consultorio", time: "20:30", days: [1,2,3,4,5], date: null, area: 20, on: true, last: null },
    { id: uid(), label: "Sala de espera", time: "09:00", days: null, date: ymd(sab), area: 30, on: true, last: null }
  ];
}
let sched = jget("oz.sched", null) || seedSched();
const saveSched = () => { store.set("oz.sched", JSON.stringify(sched)); emit(); };
const occursOn = (s, d) => s.days ? s.days.includes(d.getDay()) : s.date === ymd(d);
const byTime = (a, b) => a.time.localeCompare(b.time);
const atOf = (s, d) => { const [h, m] = s.time.split(":").map(Number); return new Date(d.getFullYear(), d.getMonth(), d.getDate(), h, m); };
function schedOn(d){ return sched.filter(s => occursOn(s, d)).sort(byTime); }
function upcoming(n = 5, from = new Date()){
  const out = [];
  for (let i = 0; i < 62 && out.length < n; i++){
    const d = addDays(from, i);
    for (const s of schedOn(d)) if (s.on){ const at = atOf(s, d); if (at > from) out.push({ s, at }); }
  }
  return out.slice(0, n);
}
const HORA = (d) => pad2(d.getHours()) + ":" + pad2(d.getMinutes());
function whenTxt(at){
  const hoy = new Date(), dif = Math.round((new Date(at.getFullYear(), at.getMonth(), at.getDate()) - new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())) / 864e5);
  if (dif === 0) return "Hoy " + HORA(at);
  if (dif === 1) return "Mañana " + HORA(at);
  return DIAS_LARGO[at.getDay()].slice(0, 3) + " " + at.getDate() + "/" + pad2(at.getMonth() + 1) + " " + HORA(at);
}
function relTxt(at){
  const min = Math.max(0, Math.round((at - new Date()) / 6e4));
  if (min < 1) return "ahora"; if (min < 60) return "en " + min + " min";
  const h = Math.floor(min / 60); if (h < 24) return "en " + h + " h " + pad2(min % 60) + " min";
  return "en " + Math.floor(h / 24) + " d";
}
const diasTxt = (s) => s.days
  ? (s.days.length === 7 ? "Todos los días" : ORDEN.filter(d => s.days.includes(d)).map(d => DIAS[d]).join(" · "))
  : (() => { const [y, m, d] = s.date.split("-").map(Number); const x = new Date(y, m - 1, d); return DIAS_LARGO[x.getDay()] + " " + d + "/" + pad2(m); })();
function tickSched(){
  const now = new Date(), key = ymd(now) + " " + HORA(now);
  let cambio = false;
  sched.forEach(s => {
    if (!s.on || s.time !== HORA(now) || s.last === key || !occursOn(s, now)) return;
    s.last = key; cambio = true;
    if (running()){ toast("Programación omitida: hay una sesión en marcha"); return; }
    if (startSession(calc(s.area).sec)) toast("Programado: " + (s.label || "Sesión") + " · " + fmtMin(calc(s.area).min));
  });
  if (cambio) saveSched();
}

/* ---- Burbujas ---- */
function bubbles(el, n = 14, h = 120){
  el.classList.add("bub");
  let html = "";
  for (let i = 0; i < n; i++){
    const s = 5 + Math.random() * 11;
    html += `<i style="--s:${s.toFixed(1)}px;--x:${(Math.random() * 94).toFixed(1)}%;--d:${(4 + Math.random() * 4).toFixed(1)}s;--dl:${(-Math.random() * 6).toFixed(1)}s;--h:${h}px;--dx:${(Math.random() * 18 - 9).toFixed(1)}px"></i>`;
  }
  el.innerHTML = html;
}
function ring(circle, f){ circle.style.opacity = f > 0 ? 1 : 0; circle.style.strokeDashoffset = (100 * (1 - clamp(f, 0, 1))).toFixed(2); }

/* ---- Hoja inferior ---- */
function openSheet(title, build){
  const back = document.createElement("div"); back.className = "sheet-back";
  const sh = document.createElement("div"); sh.className = "sheet";
  sh.setAttribute("role", "dialog"); sh.setAttribute("aria-modal", "true"); sh.setAttribute("aria-label", title);
  sh.innerHTML = '<div class="sheet-grip"></div><div class="sheet-head"><b>' + esc(title) + '</b><button class="icon-btn" aria-label="Cerrar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div><div class="sheet-body"></div>';
  document.body.append(back, sh);
  let cerrada = false;
  const close = () => {
    if (cerrada) return; cerrada = true;
    document.removeEventListener("keydown", onKey);
    back.classList.remove("show"); sh.classList.remove("show");
    setTimeout(() => { back.remove(); sh.remove(); }, 300);
  };
  const onKey = (e) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  back.onclick = close; sh.querySelector(".icon-btn").onclick = close;
  build(sh.querySelector(".sheet-body"), close);
  requestAnimationFrame(() => { back.classList.add("show"); sh.classList.add("show"); });
  return close;
}

/* ---- Selector de área (chips + paso + deslizador) ---- */
function areaPicker(el, { get, set, dim = true }){
  el.classList.add("ap");
  el.innerHTML =
    '<div class="chips">' + PRESETS.map(p => `<button class="qc" data-a="${p.a}">${p.n}<small>${p.a} m²</small></button>`).join("") + '</div>' +
    '<div class="ap-row"><button class="step" data-d="-1" aria-label="Menos área">&minus;</button>' +
    '<div class="ap-val"><span></span><small>m²</small></div><button class="step" data-d="1" aria-label="Más área">+</button></div>' +
    '<input class="ap-range" type="range" min="' + AREA_MIN + '" max="' + AREA_MAX + '" step="1" aria-label="Área a ozonizar en metros cuadrados">' +
    (dim ? '<div class="ap-sub"></div>' : "");
  const rng = el.querySelector("input"), val = el.querySelector(".ap-val span"), sub = el.querySelector(".ap-sub");
  const paint = () => {
    const a = get(); val.textContent = Number.isInteger(a) ? a : a.toFixed(1); rng.value = a;
    rng.style.setProperty("--p", ((a - AREA_MIN) / (AREA_MAX - AREA_MIN) * 100).toFixed(1) + "%");
    el.querySelectorAll(".qc").forEach(c => c.setAttribute("aria-pressed", (+c.dataset.a === a) + ""));
    if (sub) sub.textContent = fmtDim(a) + " · " + (a * CFG.h).toFixed(0) + " m³";
  };
  el.querySelectorAll(".qc").forEach(c => c.onclick = () => { set(+c.dataset.a); paint(); });
  el.querySelectorAll(".step").forEach(b => b.onclick = () => { set(clamp(Math.round(get()) + +b.dataset.d, AREA_MIN, AREA_MAX)); paint(); });
  rng.oninput = () => { set(+rng.value); paint(); };
  paint();
  return { paint };
}

/* ---- Rueda (heredada de Teo) ---- */
const ROW = () => parseInt(css("--row"), 10) || 40;
function wheel(el, max, init, onMove){
  el.innerHTML = '<div class="pad"></div>' + Array.from({ length: max + 1 }, (_, i) => `<b>${pad2(i)}</b>`).join("") + '<div class="pad"></div>';
  const val = () => clamp(Math.round(el.scrollTop / ROW()), 0, max);
  const mark = () => { const v = val(); el.querySelectorAll("b").forEach((b, i) => b.toggleAttribute("data-sel", i === v)); el.setAttribute("aria-valuenow", v); return v; };
  el.setAttribute("role", "slider"); el.tabIndex = 0; el.setAttribute("aria-valuemin", 0); el.setAttribute("aria-valuemax", max);
  let raf = 0;
  el.addEventListener("scroll", () => { if (raf) return; raf = requestAnimationFrame(() => { raf = 0; mark(); onMove && onMove(); }); }, { passive: true });
  el.addEventListener("keydown", e => {
    if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
    e.preventDefault(); el.scrollTo({ top: clamp(val() + (e.key === "ArrowUp" ? -1 : 1), 0, max) * ROW(), behavior: "smooth" });
  });
  const set = (v) => { el.scrollTo({ top: v * ROW(), behavior: "auto" }); mark(); };
  set(init);
  return { val, set };
}

/* ---- Editor de programación (hoja) ---- */
function openEditor(item, prefill = {}){
  const nuevo = !item;
  const manana = ymd(addDays(new Date(), 1));
  const d = nuevo
    ? Object.assign({ id: uid(), label: "", time: "20:00", days: null, date: manana, area: S.area, on: true, last: null }, prefill)
    : JSON.parse(JSON.stringify(item));
  openSheet(nuevo ? "Nueva programación" : "Editar programación", (body, close) => {
    body.innerHTML =
      '<div class="field"><span class="eyebrow">Nombre</span><input class="txt" id="edName" maxlength="28" placeholder="Ej. Consultorio" autocomplete="off"></div>' +
      '<div class="field"><span class="eyebrow">Cuándo</span><div class="seg" id="edKind"><button data-k="once">Una vez</button><button data-k="week">Cada semana</button></div>' +
      '<input class="txt" id="edDate" type="date"><div class="days" id="edDays"></div></div>' +
      '<div class="field"><span class="eyebrow">Hora de encendido</span><div class="tpick"><div class="tband"></div><div class="tcol" id="edH" aria-label="Hora"></div><div class="tsep">:</div><div class="tcol" id="edM" aria-label="Minutos"></div></div></div>' +
      '<div class="field"><span class="eyebrow">Área a ozonizar</span><div id="edArea"></div></div>' +
      '<div class="resumen" id="edSum"></div>' +
      '<div class="sheet-actions">' + (nuevo ? "" : '<button class="btn btn-danger" id="edDel">Eliminar</button>') + '<button class="btn btn-primary" id="edOk">Guardar</button></div>';
    const q = (id) => body.querySelector("#" + id);
    q("edName").value = d.label; q("edDate").value = d.date || manana;
    q("edDays").innerHTML = ORDEN.map(n => `<button data-d="${n}" aria-pressed="${!!(d.days && d.days.includes(n))}" aria-label="${DIAS_LARGO[n]}">${DIAS[n]}</button>`).join("");
    let kind = d.days ? "week" : "once";
    const [hh, mm] = d.time.split(":").map(Number);
    const wH = wheel(q("edH"), 23, hh, sum), wM = wheel(q("edM"), 59, mm, sum);
    const ap = areaPicker(q("edArea"), { get: () => d.area, set: (v) => { d.area = v; sum(); } });
    function paintKind(){
      q("edKind").querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", (b.dataset.k === kind) + ""));
      q("edDate").hidden = kind !== "once"; q("edDays").hidden = kind !== "week";
    }
    function sum(){
      const c = calc(d.area), ini = wH.val() * 60 + wM.val(), fin = (ini + c.min) % 1440;
      q("edSum").innerHTML = "Dura <b>" + fmtMin(c.min) + "</b> · de " + pad2(Math.floor(ini / 60)) + ":" + pad2(ini % 60) + " a " + pad2(Math.floor(fin / 60)) + ":" + pad2(fin % 60);
    }
    q("edKind").onclick = (e) => { const b = e.target.closest("button"); if (b){ kind = b.dataset.k; paintKind(); } };
    q("edDays").onclick = (e) => { const b = e.target.closest("button"); if (b) b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") !== "true"); };
    paintKind(); sum();
    q("edOk").onclick = () => {
      d.label = q("edName").value.trim();
      d.time = pad2(wH.val()) + ":" + pad2(wM.val());
      if (kind === "week"){
        d.days = ORDEN.filter(n => q("edDays").querySelector(`[data-d="${n}"]`).getAttribute("aria-pressed") === "true"); d.date = null;
        if (!d.days.length){ toast("Elige al menos un día"); return; }
      } else {
        d.date = q("edDate").value; d.days = null;
        if (!d.date){ toast("Elige una fecha"); return; }
        const [y, m, dd] = d.date.split("-").map(Number);
        if (atOf(d, new Date(y, m - 1, dd)) <= new Date()){ toast("Esa fecha y hora ya pasaron"); return; }
      }
      d.last = null;
      const i = sched.findIndex(s => s.id === d.id);
      if (i >= 0) sched[i] = d; else sched.push(d);
      saveSched(); close(); toast(nuevo ? "Programación guardada" : "Cambios guardados");
    };
    if (!nuevo) q("edDel").onclick = () => { sched = sched.filter(s => s.id !== d.id); saveSched(); close(); toast("Programación eliminada"); };
  });
}
function toggleSched(id){ const s = sched.find(x => x.id === id); if (s){ s.on = !s.on; saveSched(); } }

/* ---- Tema (igual que Teo) ---- */
const themeBtn = $("themeBtn");
const prefiereOscuro = matchMedia("(prefers-color-scheme: dark)");
const temaOscuro = () => { const t = document.documentElement.getAttribute("data-theme"); return t ? t === "dark" : prefiereOscuro.matches; };
function paintThemeBtn(){
  if (!themeBtn) return;
  const o = temaOscuro();
  themeBtn.dataset.icon = o ? "sun" : "moon";
  themeBtn.setAttribute("aria-label", o ? "Cambiar a tema claro" : "Cambiar a tema oscuro");
  const mt = document.querySelector('meta[name="theme-color"]'); if (mt) mt.content = o ? "#0E0E22" : "#2E2A5C";
}
if (themeBtn) themeBtn.onclick = () => {
  const next = temaOscuro() ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next); store.set("tk.theme", next); paintThemeBtn(); emit();
};
const paramTema = new URLSearchParams(location.search).get("tema");
const savedTheme = (paramTema === "light" || paramTema === "dark") ? paramTema : store.get("tk.theme");
if (savedTheme) document.documentElement.setAttribute("data-theme", savedTheme);
prefiereOscuro.addEventListener("change", () => { if (!store.get("tk.theme")) paintThemeBtn(); });
paintThemeBtn();

/* ---- Conexión BLE (mismo flujo que Teo) ---- */
let device = null, cmdChar = null, connecting = false;
function setPill(state, text){ $("pill").dataset.state = state; $("pillText").textContent = text; }
function applyState(st){
  if (!st) return;
  const was = running();
  Object.assign(S, st);
  if (S.timerSec !== null && (!was || S.timerSec > S.total)) S.total = S.timerSec;
  emit();
}
function onDisconnect(){
  S.connected = false; cmdChar = null;
  $("connectBtn").textContent = "Conectar";
  if (huboHardware){ setPill("perdida", "Sin conexión · último dato"); toast("Se perdió la conexión — el equipo sigue solo"); }
  else { setPill("demo", "Modo demostración"); toast("Equipo desconectado"); }
  emit();
}
$("connectBtn").onclick = async () => {
  if (connecting) return;
  if (S.connected){ device.gatt.disconnect(); return; }
  if (!navigator.bluetooth){ toast("Usa Chrome, Edge o Bluefy en iPhone"); return; }
  connecting = true; $("connectBtn").disabled = true;
  setPill("wait", "Buscando equipo…");
  try {
    device = await navigator.bluetooth.requestDevice({ filters: [{ services: [SERVICE_UUID] }] });
    device.addEventListener("gattserverdisconnected", onDisconnect);
    const svc = await (await device.gatt.connect()).getPrimaryService(SERVICE_UUID);
    cmdChar = await svc.getCharacteristic(CMD_UUID);
    const stateChar = await svc.getCharacteristic(STATE_UUID);
    await stateChar.startNotifications();
    stateChar.addEventListener("characteristicvaluechanged", e => applyState(decodeState(e.target.value)));
    S.connected = true; huboHardware = true;
    $("connectBtn").textContent = "Desconectar";
    setPill("on", device.name || "Ozonocleaner TEO");
    try { applyState(decodeState(await stateChar.readValue())); } catch (e) {}
    toast("Conectado"); emit();
  } catch (err) {
    try { if (device && device.gatt.connected) device.gatt.disconnect(); } catch {}
    setPill(huboHardware ? "perdida" : "demo", huboHardware ? "Sin conexión · último dato" : "Modo demostración");
    if (err.name !== "NotFoundError") toast("No se pudo conectar");
  } finally { connecting = false; $("connectBtn").disabled = false; }
};

/* ---- Reloj de la maqueta: cuenta atrás y programación (solo sin hardware) ---- */
setInterval(() => {
  if (!S.connected && !huboHardware && running()){
    S.timerSec = Math.max(0, S.timerSec - 1);
    if (S.timerSec === 0){ S.timerSec = null; S.relay = false; toast("Sesión terminada · ventile el ambiente antes de entrar"); }
    emit();
  } else if (running()) emit();
  tickSched();
}, 1000);

/* ---- Entrada por secciones ---- */
function revealAll(sel){
  if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const io = new IntersectionObserver((items) => items.forEach(it => {
    if (!it.isIntersecting) return; it.target.classList.add("seen"); io.unobserve(it.target);
  }), { threshold: .12, rootMargin: "0px 0px -6% 0px" });
  document.querySelectorAll(sel).forEach(el => {
    if (el.getBoundingClientRect().top < innerHeight * 0.92){ el.classList.add("reveal", "seen"); return; }
    el.classList.add("reveal"); io.observe(el);
  });
}

/* ---- Filas de programación y panel de cálculo (comunes) ---- */
function schedRowHTML(s){
  const c = calc(s.area);
  return `<div class="srow${s.on ? "" : " off"}" data-id="${s.id}" tabindex="0" role="button" aria-label="Editar ${esc(s.label || "programación")}">` +
    `<div class="t">${s.time}</div><div class="m"><b>${esc(s.label || "Sin nombre")}</b><span>${diasTxt(s)} · ${s.area} m² · ${fmtMin(c.min)}</span></div>` +
    `<button class="switch" role="switch" aria-checked="${s.on}" aria-label="Activar o pausar"></button></div>`;
}
function bindRows(root){
  const abrir = (e) => {
    const row = e.target.closest(".srow"); if (!row) return;
    if (e.target.closest(".switch")){ toggleSched(row.dataset.id); return; }
    openEditor(sched.find(s => s.id === row.dataset.id));
  };
  root.addEventListener("click", abrir);
  root.addEventListener("keydown", e => { if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("srow")){ e.preventDefault(); abrir(e); } });
}
function cfgPanel(el){
  const F = [
    { k: "h",   t: "Altura del techo", min: 2, max: 5, step: .1, u: " m",      f: v => v.toFixed(1) },
    { k: "k",   t: "Factor de ozonización", min: .2, max: 2, step: .05, u: " min/m³", f: v => v.toFixed(2) },
    { k: "max", t: "Tope de sesión", min: 30, max: 240, step: 10, u: " min",  f: v => v.toFixed(0) }
  ];
  el.innerHTML = F.map(f => `<div class="cfg"><div class="cfg-h"><span>${f.t}</span><b class="mono" data-v="${f.k}"></b></div>` +
    `<input class="ap-range" type="range" data-k="${f.k}" min="${f.min}" max="${f.max}" step="${f.step}"></div>`).join("") +
    '<p class="cfg-nota">Valores provisionales: se ajustan con mediciones reales del generador.</p>';
  const paint = () => F.forEach(f => {
    const r = el.querySelector(`[data-k="${f.k}"]`); r.value = CFG[f.k];
    r.style.setProperty("--p", ((CFG[f.k] - f.min) / (f.max - f.min) * 100).toFixed(1) + "%");
    el.querySelector(`[data-v="${f.k}"]`).textContent = f.f(CFG[f.k]) + f.u;
  });
  el.querySelectorAll("input").forEach(r => r.oninput = () => { CFG[r.dataset.k] = +r.value; saveCfg(); paint(); });
  paint();
}
