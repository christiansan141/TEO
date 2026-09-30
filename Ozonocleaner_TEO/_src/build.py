#!/usr/bin/env python3
"""Genera Ozonocleaner_TEO: propuestas HTML, logos, paleta y bocetos.
Uso:  python3 _src/build.py      (desde la carpeta Ozonocleaner_TEO)"""
import os, re, urllib.parse, math
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
def rd(p): return open(os.path.join(HERE, p), encoding="utf-8").read()
def wr(p, s):
    full = os.path.join(ROOT, p); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- tokens
STATIC = {"r": "20px", "row": "40px",
  "sans": '"Segoe UI Variable Display","Segoe UI",system-ui,-apple-system,"Helvetica Neue",sans-serif',
  "mono": '"Cascadia Mono",ui-monospace,"SF Mono",Consolas,monospace'}
LIGHT = {
 "ground":"#E9EDF6","surface":"#FFFFFF","surface-2":"#F2F5FC","line":"#DBE2F0","line-soft":"#EAEEF7",
 "ink":"#231F20","ink-2":"#565B6C","muted":"#8A91A6","chip":"#EDF1FA",
 "azul":"#1D71B8","indigo":"#2E2A5C","indigo-fill":"#2E2A5C",
 "o3":"#08807D","o3-deep":"#05595C","o3-glow":"#12A099","o3-bg":"rgba(8,128,125,.13)","on-o3":"#FFFFFF",
 "aviso":"#B96A12","aviso-bg":"rgba(232,149,44,.16)","ok":"#1B8F62","ok-bg":"rgba(27,143,98,.12)",
 "stop":"#B23A2B","stop-bg":"rgba(178,58,43,.09)",
 "lg-blue":"#3466AE","lg-k1":"#29265B","lg-k2":"#2E2B7A","lg-arc":"#313132",
 "shadow":"0 22px 50px -30px rgba(46,42,92,.55), 0 1px 2px rgba(46,42,92,.05)"}
DARK = {
 "ground":"#0E0E22","surface":"#191934","surface-2":"#212143","line":"#2D2D55","line-soft":"#242449",
 "ink":"#EDEFF8","ink-2":"#AEB4CB","muted":"#7B8299","chip":"#242449",
 "azul":"#57A3E4","indigo":"#9A92F0","indigo-fill":"#2E2A5C",
 "o3":"#4FD8CC","o3-deep":"#16716F","o3-glow":"#2FB5AC","o3-bg":"rgba(79,216,204,.15)","on-o3":"#062B2A",
 "aviso":"#F2A83F","aviso-bg":"rgba(242,168,63,.16)","ok":"#3EC38C","ok-bg":"rgba(62,195,140,.14)",
 "stop":"#E0705F","stop-bg":"rgba(224,112,95,.12)",
 "lg-blue":"#7FAEE8","lg-k1":"#8F8AE6","lg-k2":"#A9A2F5","lg-arc":"#8A90A6",
 "shadow":"0 24px 60px -34px rgba(0,0,0,.85), 0 1px 2px rgba(0,0,0,.4)"}
def block(d, ind="  "): return "\n".join(f"{ind}--{k}:{v};" for k, v in d.items())
TOKENS = (":root{\n" + block(STATIC) + "\n" + block(LIGHT) + "\n}\n"
  "@media (prefers-color-scheme: dark){\n  :root:not([data-theme=\"light\"]){\n" + block(DARK, "    ") + "\n  }\n}\n"
  ":root[data-theme=\"dark\"]{\n" + block(DARK) + "\n}")

# ---------------------------------------------------------------- logo TK (mismos trazos que Teo)
T_POLY = "246.71 639.26 246.71 143.38 50.36 143.38 50.36 0 622.95 0 622.95 143.38 427.52 143.38 427.52 639.26 246.71 639.26"
K_POLY = "908.96 695.6 634.65 339.57 894.35 56.34 696.18 56.34 421.3 351.31 421.3 564.81 515.83 463.52 698.92 695.6 908.96 695.6"
ARC = "M463.23,765.85c-215.43,0-390.07-106.11-390.07-237,0-73.42,55-139,141.21-182.5-97.1,43.11-160.19,112.8-160.19,191.46,0,130.89,174.65,237,390.08,237,94.6,0,181.33-20.46,248.86-54.5-64.47,28.63-143.92,45.54-229.89,45.54"
def mark_inner(blue, k1, k2, arc, gid):
    return (f'<defs><linearGradient id="{gid}" x1="421.29" y1="375.97" x2="908.96" y2="375.97" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="{k1}"/><stop offset=".64" stop-color="{k2}"/></linearGradient></defs>'
            f'<polygon fill="{blue}" points="{T_POLY}"/><g transform="translate(-17.54 -56.34)">'
            f'<polygon fill="url(#{gid})" points="{K_POLY}"/><path fill="{arc}" d="{ARC}"/></g>')
def mark_css(gid):   # para el HTML: usa variables del tema
    return ('<svg class="mark" viewBox="36.64 0 854.78 718.47" aria-label="TK">' +
            mark_inner("var(--lg-blue)", "var(--lg-k1)", "var(--lg-k2)", "var(--lg-arc)", gid).replace('stop-color="var(--lg-k1)"', 'style="stop-color:var(--lg-k1)"').replace('stop-color="var(--lg-k2)"', 'style="stop-color:var(--lg-k2)"') + '</svg>')
def o3_molecule(cx, cy, s, col, fill_op=1):
    """Molécula de ozono (O3): tres esferas en ángulo. s = escala."""
    a, b, c = (cx, cy - 0.62*s), (cx - 0.95*s, cy + 0.55*s), (cx + 0.95*s, cy + 0.55*s)
    r = 0.42*s
    return (f'<g stroke="{col}" stroke-width="{0.16*s:.1f}" stroke-linecap="round" fill="none">'
            f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/><line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{c[0]:.1f}" y2="{c[1]:.1f}"/></g>' +
            "".join(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r:.1f}" fill="{col}" fill-opacity="{fill_op}"/>' for p in (a, b, c)))

PWR = '<svg class="pb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9"/><path d="M6.6 6.6a8 8 0 1 0 10.8 0"/></svg>'
PWR_SM = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 3v9"/><path d="M6.6 6.6a8 8 0 1 0 10.8 0"/></svg>'
CHROME = f'''<header class="topbar">{mark_css("mk")}
    <div class="titles"><h1>Ozono<b>cleaner</b> TEO</h1><span class="brandline">TK &mdash; Ingenier&iacute;a para la est&eacute;tica</span></div>
    <button class="icon-btn theme-btn" id="themeBtn" data-icon="moon" aria-label="Cambiar a tema oscuro">
      <svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
      <svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.1"/><path d="M12 2.7v2M12 19.3v2M4.4 4.4l1.4 1.4M18.2 18.2l1.4 1.4M2.7 12h2M19.3 12h2M4.4 19.6l1.4-1.4M18.2 5.8l1.4-1.4"/></svg>
    </button>
  </header>
  <div class="connbar"><span class="pill" id="pill" data-state="demo"><i class="dot"></i><span id="pillText">Modo demostraci&oacute;n</span></span><button class="btn btn-primary" id="connectBtn">Conectar</button></div>
  <div class="alert" id="alert"></div>
  <div class="local" id="local"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg><span id="localTxt"></span></div>'''
SPLASH = ('<div id="splash" aria-hidden="true"><div class="in"><div class="halo"></div>'
  '<svg class="mark" viewBox="36.64 0 854.78 718.47" aria-label="TK">' + mark_inner("#FFFFFF", "#6E9FDD", "#9AC0F2", "#8F93A3", "mks") + '</svg>'
  '<div class="wm">Ozono<b>cleaner</b></div><div class="wm-sub">TK &middot; Ingenier&iacute;a para la est&eacute;tica</div></div></div>')
def favicon():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="114" fill="#2E2A5C"/>' + icon_body() + '</svg>')
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="/:=' ")
def icon_body():
    s = .32; tx = 256 - s*464.03; ty = 190 - s*359.2
    return (f'<g transform="translate({tx:.2f} {ty:.2f}) scale({s})">' + mark_inner("#FFFFFF", "#6E9FDD", "#9AC0F2", "#8F93A3", "ik") + '</g>' +
            o3_molecule(256, 386, 52, "#4FD8CC"))

# ---------------------------------------------------------------- propuestas
CSS = rd("base.css").replace("/*@TOKENS@*/", TOKENS); JS = rd("core.js")
def page(name):
    h = rd(name)
    h = (h.replace("/*@BASE_CSS@*/", CSS).replace("/*@CORE_JS@*/", JS)
          .replace("{{CHROME}}", CHROME).replace("{{SPLASH}}", SPLASH).replace("{{PWR}}", PWR)
          .replace("{{STOPICON}}", PWR_SM.replace("<svg ", '<svg width="17" height="17" ')).replace("{{FAVICON}}", favicon()))
    return h
for i, slug in ((1, "panel"), (2, "habitacion"), (3, "agenda")):
    wr(f"propuesta-{i}-{slug}.html", page(f"p{i}.tpl.html"))

h = rd("index.tpl.html")
h = (h.replace("/*@BASE_CSS@*/", CSS).replace("{{SPLASH}}", SPLASH).replace("{{MARK}}", mark_css("mk")).replace("{{FAVICON}}", favicon()))
wr("index.html", h)

# ---------------------------------------------------------------- logos
FONT = 'font-family="Segoe UI Variable Display, Segoe UI, system-ui, Helvetica, Arial, sans-serif"'
def logo_h(d, bg, wm_o, wm_c, sub, name):
    mk = mark_inner(d["lg-blue"], d["lg-k1"], d["lg-k2"], d["lg-arc"], "g" + name)
    bgrect = f'<rect width="760" height="220" rx="28" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 220" role="img" aria-label="Ozonocleaner TEO">'
      f'<title>Ozonocleaner TEO</title>{bgrect}'
      f'<g transform="translate(46 34) scale(.2)"><g transform="translate(-36.64 0)">{mk}</g></g>'
      f'<text x="236" y="118" {FONT} font-size="52" font-weight="300" fill="{wm_o}" letter-spacing="-1">Ozono<tspan font-weight="700" fill="{wm_c}">cleaner</tspan></text>'
      f'<text x="238" y="152" {FONT} font-size="17" letter-spacing="3.6" fill="{sub}">TK · INGENIERÍA PARA LA ESTÉTICA</text>'
      f'{o3_molecule(700, 98, 24, wm_c)}</svg>')
wr("logos/ozonocleaner-logo-claro.svg", logo_h(LIGHT, "#FFFFFF", "#231F20", LIGHT["o3"], "#8A91A6", "c"))
wr("logos/ozonocleaner-logo-oscuro.svg", logo_h(DARK, "#0E0E22", "#EDEFF8", DARK["o3"], "#7B8299", "d"))
wr("logos/ozonocleaner-logo-transparente-claro.svg", logo_h(LIGHT, None, "#231F20", LIGHT["o3"], "#8A91A6", "e"))
def app_icon(rx):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-label="Ozonocleaner TEO"><title>Ozonocleaner TEO</title>'
      '<defs><linearGradient id="tile" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#2E2A5C"/><stop offset="100%" stop-color="#1B1840"/></linearGradient></defs>'
      f'<rect width="512" height="512" rx="{rx}" ry="{rx}" fill="url(#tile)"/>' + icon_body() + '</svg>')
wr("logos/icono-app-oscuro.svg", app_icon(0)); wr("logos/icono-app-redondeado.svg", app_icon(114))
wr("logos/ozono-molecula.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 100" role="img" aria-label="O3">' + o3_molecule(60, 46, 34, LIGHT["o3"]) + '</svg>')

# ---------------------------------------------------------------- colores
NOMBRES = [("Fondo", "ground"), ("Tarjeta", "surface"), ("Tarjeta 2", "surface-2"), ("Línea", "line"), ("Texto", "ink"), ("Texto 2", "ink-2"),
  ("Azul TK", "azul"), ("Índigo TK", "indigo"), ("Ozono", "o3"), ("Ozono profundo", "o3-deep"), ("Ozono brillo", "o3-glow"), ("Aviso", "aviso"),
  ("OK", "ok"), ("Paro", "stop")]
def swatches(d, x0, y0, title, bg, fg):
    o = f'<rect x="{x0}" y="{y0}" width="560" height="{110 + 84*4}" rx="22" fill="{bg}"/><text x="{x0+26}" y="{y0+42}" {FONT} font-size="20" font-weight="700" fill="{fg}">{title}</text>'
    for i, (n, k) in enumerate(NOMBRES):
        r, c = divmod(i, 4); x = x0 + 26 + c*134; y = y0 + 70 + r*84
        v = d[k]
        o += (f'<rect x="{x}" y="{y}" width="120" height="44" rx="12" fill="{v}" stroke="{d["line"]}"/>'
              f'<text x="{x}" y="{y+62}" {FONT} font-size="12" font-weight="650" fill="{fg}">{n}</text>'
              f'<text x="{x}" y="{y+77}" font-family="Consolas, monospace" font-size="11" fill="{d["muted"]}">{v.upper() if v.startswith("#") else v}</text>')
    return o
H = 110 + 84*4 + 90
wr("colores/paleta.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 {H}"><rect width="1180" height="{H}" fill="#F7F8FC"/>'
   f'<text x="30" y="52" {FONT} font-size="26" font-weight="300" fill="#231F20">Paleta <tspan font-weight="700" fill="{LIGHT["o3"]}">Ozonocleaner</tspan> TEO</text>'
   f'<text x="30" y="76" {FONT} font-size="13" fill="#565B6C">Índigo y azul de TK/Teo + un acento nuevo, el verde-agua del ozono, que reemplaza al ámbar del calor.</text>'
   + swatches(LIGHT, 30, 100, "Modo claro", "#E9EDF6", "#231F20") + swatches(DARK, 590, 100, "Modo nocturno", "#0E0E22", "#EDEFF8") + '</svg>')
wr("colores/tokens.css", "/* Variables de color de Ozonocleaner TEO (las mismas que usan las tres propuestas).\n   Los nombres de Teo se conservan; se agregan --o3, --o3-deep, --o3-glow, --o3-bg y --on-o3. */\n" + TOKENS + "\n")

# ---------------------------------------------------------------- bocetos (wireframes)
INK, SOFT, LN, ACC = "#2E2A5C", "#EDF0F8", "#C9D0E4", "#08807D"
class W:
    def __init__(s, w, h, title, note): s.o = []; s.w, s.h = w, h; s.title, s.sub = title, note
    def r(s, x, y, w, h, rx=10, f="#fff", st=LN, sw=1.2, dash=False):
        s.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{f}" stroke="{st}" stroke-width="{sw}"' + (' stroke-dasharray="5 4"' if dash else "") + "/>")
    def t(s, x, y, txt, sz=12, w=400, c=INK, a="start", mono=False):
        fam = 'font-family="Consolas, monospace"' if mono else FONT
        s.o.append(f'<text x="{x}" y="{y}" {fam} font-size="{sz}" font-weight="{w}" fill="{c}" text-anchor="{a}">{txt}</text>')
    def c(s, x, y, r, f="none", st=LN, sw=1.4): s.o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{f}" stroke="{st}" stroke-width="{sw}"/>')
    def ln(s, x1, y1, x2, y2, st=LN, sw=1.2): s.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{st}" stroke-width="{sw}" stroke-linecap="round"/>')
    def note(s, x, y, txt): s.t(x, y, txt, 10.5, 500, "#8A6D1A"); 
    def out(s):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h}"><rect width="{s.w}" height="{s.h}" fill="#F7F8FC"/>'
          f'<text x="24" y="34" {FONT} font-size="18" font-weight="700" fill="{INK}">{s.title}</text><text x="24" y="54" {FONT} font-size="12" fill="#565B6C">{s.sub}</text>' + "".join(s.o) + "</svg>")
def header(w, x=24, y=76, wd=312):
    w.r(x, y, 34, 30, 6, INK, INK); w.t(x+42, y+13, "Ozonocleaner TEO", 13, 700); w.t(x+42, y+27, "TK — Ingeniería para la estética", 9, 400, "#8A91A6")
    w.c(x+wd-16, y+15, 15); w.t(x+wd-16, y+19, "☾", 13, 400, INK, "middle")
    w.r(x, y+42, 120, 24, 12, SOFT); w.t(x+14, y+58, "● Modo demostración", 10); w.r(x+wd-86, y+38, 86, 30, 9, ACC, ACC); w.t(x+wd-43, y+57, "Conectar", 11, 700, "#fff", "middle")
    return y + 84
def stopbtn(w, y): w.r(24, y, 312, 38, 12, "#FBEDEA", "#D9A69E"); w.t(180, y+24, "⏻  Paro total", 13, 700, "#B23A2B", "middle")

def b1():
    w = W(360, 1010, "Propuesta 1 · Panel", "Una pantalla, en la línea de Teo: plano del área, salida central con anillo y programación al pie.")
    y = header(w)
    w.r(24, y, 312, 300, 18); w.t(40, y+24, "ÁREA A OZONIZAR", 9.5, 700, "#8A91A6"); w.r(252, y+11, 70, 22, 11, "#DDF1EF", "#DDF1EF"); w.t(287, y+26, "En reposo", 10, 700, ACC, "middle")
    w.r(40, y+40, 280, 118, 14, SOFT); w.r(120, y+58, 120, 82, 8, "#DDF1EF", ACC, 2); w.t(180, y+104, "18 m²", 18, 300, INK, "middle"); w.t(180, y+52, "4.9 m", 9, 400, "#8A91A6", "middle"); w.t(252, y+100, "3.7 m", 9, 400, "#8A91A6")
    for i, n in enumerate(["Baño", "Habit.", "Consul.", "Sala"]): w.r(40+i*70, y+170, 62, 24, 12, "#fff" if i != 2 else "#DDF1EF", LN if i != 2 else ACC); w.t(71+i*70, y+186, n, 10, 600, INK, "middle")
    w.r(40, y+206, 34, 34, 10, SOFT); w.t(57, y+229, "−", 18, 300, INK, "middle"); w.t(180, y+232, "18 m²", 20, 300, INK, "middle"); w.r(286, y+206, 34, 34, 10, SOFT); w.t(303, y+229, "+", 18, 300, INK, "middle")
    w.ln(56, y+256, 304, y+256, ACC, 4); w.c(160, y+256, 8, "#fff", ACC, 3)
    for i, (a, b) in enumerate([("VOLUMEN", "45 m³"), ("FACTOR", "0.60"), ("TIEMPO", "27 min")]): w.r(40+i*94, y+270, 88, 20, 8, SOFT, SOFT); w.t(84+i*94, y+284, f"{a} {b}", 8.5, 600, ACC if i == 2 else INK, "middle")
    y += 314
    w.r(24, y, 312, 250, 18); w.t(40, y+24, "SALIDA", 9.5, 700, "#8A91A6"); w.c(180, y+112, 74, "none", LN, 6); w.c(180, y+112, 74, "none", ACC, 6); w.c(180, y+112, 52, SOFT, LN); w.t(180, y+120, "⏻", 34, 300, "#8A91A6", "middle")
    w.t(180, y+212, "APAGADO", 15, 700, "#8A91A6", "middle"); w.t(180, y+238, "27:00 · duración según el área", 11, 400, "#8A91A6", "middle")
    w.note(190, y+30, "anillo = progreso de la sesión")
    y += 262
    w.r(24, y, 312, 250, 18); w.t(40, y+24, "PROGRAMACIÓN", 9.5, 700, "#8A91A6"); w.r(236, y+8, 88, 24, 12, ACC, ACC); w.t(280, y+24, "+ Programar", 10.5, 700, "#fff", "middle")
    for i in range(7): w.r(38+i*42, y+44, 38, 46, 10, "#DDF1EF" if i == 2 else SOFT, "#DDF1EF" if i == 2 else SOFT); w.t(57+i*42, y+62, "LMXJVSD"[i], 9, 700, "#8A91A6", "middle"); w.t(57+i*42, y+80, str(29+i), 12, 500, INK, "middle")
    w.t(40, y+112, "Próxima: Hoy 20:30 · Consultorio · 30 min", 11, 500, "#565B6C")
    for i, (h, n, d) in enumerate([("20:30", "Consultorio", "L·M·X·J·V · 20 m² · 30 min"), ("09:00", "Sala de espera", "sábado · 30 m² · 45 min")]):
        w.ln(40, y+128+i*54, 320, y+128+i*54, "#EAEEF7"); w.t(40, y+160+i*54, h, 18, 500, INK, mono=True); w.t(104, y+150+i*54, n, 12.5, 700); w.t(104, y+167+i*54, d, 10.5, 400, "#8A91A6")
        w.r(276, y+143+i*54, 42, 24, 12, "#DDF1EF", ACC); w.c(305, y+155+i*54, 8, ACC, ACC)
    y += 262; stopbtn(w, y); w.h = y + 60
    return w.out().replace(f'viewBox="0 0 360 1010"', f'viewBox="0 0 360 {w.h}"')
def b2():
    w = W(360, 1010, "Propuesta 2 · Habitación", "Se dibuja el área arrastrando la esquina; el dial marca el tiempo. Tres pestañas.")
    y = header(w)
    w.r(24, y, 312, 300, 18); w.t(40, y+24, "DIBUJA EL ÁREA", 9.5, 700, "#8A91A6")
    w.r(38, y+38, 284, 170, 14, SOFT)
    for i in range(1, 14): w.ln(38+i*20, y+38, 38+i*20, y+208, "#E1E6F2", .8)
    for i in range(1, 9): w.ln(38, y+38+i*20, 322, y+38+i*20, "#E1E6F2", .8)
    w.r(52, y+52, 120, 90, 6, "#DDF1EF", ACC, 2); w.t(112, y+102, "18 m²", 20, 300, INK, "middle"); w.c(172, y+142, 13, "#fff", ACC, 3); w.note(190, y+150, "← arrastrar esquina")
    w.r(38, y+220, 138, 40, 13, SOFT); w.t(107, y+244, "−  Ancho 4.0 m  +", 11, 600, INK, "middle"); w.r(184, y+220, 138, 40, 13, SOFT); w.t(253, y+244, "−  Largo 4.5 m  +", 11, 600, INK, "middle")
    for i, n in enumerate(["Baño", "Habit.", "Consul.", "Sala"]): w.r(38+i*70, y+268, 62, 22, 11, "#fff", LN); w.t(69+i*70, y+283, n, 9.5, 600, INK, "middle")
    y += 314
    w.r(24, y, 312, 300, 18); w.t(40, y+24, "TIEMPO DE OZONIZACIÓN", 9.5, 700, "#8A91A6"); w.c(180, y+128, 84, "none", LN, 5); w.c(180, y+128, 84, "none", ACC, 5)
    w.t(180, y+108, "LISTO", 10, 700, ACC, "middle"); w.t(180, y+142, "27:00", 40, 220, INK, "middle"); w.t(180, y+164, "calculado con el área", 10.5, 400, "#8A91A6", "middle")
    w.r(40, y+232, 280, 46, 15, ACC, ACC); w.t(180, y+260, "⏻  Iniciar · 27 min", 14, 700, "#fff", "middle")
    y += 314
    w.r(24, y, 312, 40, 14); w.t(40, y+25, "▦  Próxima: Hoy 20:30 · Consultorio · en 2 h", 11, 500, "#565B6C")
    y += 52; stopbtn(w, y); y += 56
    w.r(0, y, 360, 56, 0, "#fff", LN); 
    for i, n in enumerate(["Ozonizar", "Agenda", "Ajustes"]): w.r(20+i*112, y+8, 104, 40, 12, "#DDF1EF" if i == 0 else "#fff", "#DDF1EF" if i == 0 else "#fff"); w.t(72+i*112, y+33, n, 11, 700, ACC if i == 0 else "#8A91A6", "middle")
    w.h = y + 70
    return w.out().replace(f'viewBox="0 0 360 1010"', f'viewBox="0 0 360 {w.h}"')
def b3():
    w = W(360, 1010, "Propuesta 3 · Agenda", "El calendario manda: próxima sesión arriba, mes en el centro y botón flotante para ozonizar ahora.")
    y = header(w)
    w.r(24, y, 312, 172, 20, INK, INK); w.t(44, y+28, "PRÓXIMA SESIÓN", 9.5, 700, "#9DA3C8"); w.t(44, y+66, "Hoy 20:30", 32, 250, "#fff"); w.t(44, y+90, "Consultorio · 20 m² · 30 min", 12, 400, "#C4C9E6")
    w.r(44, y+100, 66, 22, 11, "#22405C", "#22405C"); w.t(77, y+115, "en 2 h 14 min", 9.5, 700, "#7FEDE1", "middle")
    w.r(44, y+130, 140, 30, 10, "#4FD8CC", "#4FD8CC"); w.t(114, y+150, "Ozonizar ahora", 11.5, 700, "#06302F", "middle"); w.r(194, y+130, 118, 30, 10, "none", "#5A5F8C"); w.t(253, y+150, "+ Programar", 11.5, 600, "#fff", "middle")
    y += 184
    w.r(24, y, 312, 268, 18); w.t(180, y+30, "octubre 2026", 14, 700, INK, "middle"); w.t(52, y+31, "‹", 20, 400, INK, "middle"); w.t(308, y+31, "›", 20, 400, INK, "middle")
    for i in range(7): w.t(50+i*43.5, y+56, "LMXJVSD"[i], 9, 700, "#8A91A6", "middle")
    for r in range(5):
        for c in range(7):
            n = r*7+c-2; x = 50+c*43.5; yy = y+84+r*38
            if 1 <= n <= 31:
                if n == 2: w.r(x-17, yy-17, 34, 34, 11, ACC, ACC)
                if n == 1: w.r(x-17, yy-17, 34, 34, 11, "none", ACC, 1.5)
                w.t(x, yy+2, str(n), 12, 500, "#fff" if n == 2 else INK, "middle")
                if n in (1, 2, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 19, 20, 21, 22, 23): w.c(x, yy+12, 2.4, "#fff" if n == 2 else ACC, "none")
    y += 280
    w.r(24, y, 312, 150, 18); w.t(40, y+28, "Hoy · 1 de octubre", 13.5, 700); w.r(236, y+12, 88, 24, 12, ACC, ACC); w.t(280, y+28, "+ Programar", 10.5, 700, "#fff", "middle")
    w.ln(40, y+48, 320, y+48, "#EAEEF7"); w.t(40, y+84, "20:30", 18, 500, INK, mono=True); w.t(104, y+74, "Consultorio", 12.5, 700); w.t(104, y+91, "L·M·X·J·V · 20 m² · 30 min", 10.5, 400, "#8A91A6")
    w.r(276, y+66, 42, 24, 12, "#DDF1EF", ACC); w.c(305, y+78, 8, ACC, ACC)
    y += 164; stopbtn(w, y)
    w.r(196, y+58, 140, 46, 23, ACC, ACC); w.t(266, y+86, "⏻ Ozonizar ahora", 12, 700, "#fff", "middle"); w.note(24, y+80, "botón flotante (siempre visible)")
    w.h = y + 120
    return w.out().replace(f'viewBox="0 0 360 1010"', f'viewBox="0 0 360 {w.h}"')
wr("bocetos/boceto-1-panel.svg", b1()); wr("bocetos/boceto-2-habitacion.svg", b2()); wr("bocetos/boceto-3-agenda.svg", b3())

# ---- Pantallas de la OLED (128×64, monocroma) — borrador
def oled():
    S, PX = 3, 6
    scr = [
      ("1 · Reposo", [("OZONOCLEANER", 4, 12, 9), ("BT", 108, 12, 9), ("AREA 18m2", 4, 30, 11), ("TIEMPO 27:00", 4, 46, 11), ("<  >     OK", 4, 61, 8)]),
      ("2 · Elegir área", [("AREA", 4, 12, 9), ("18 m2", 34, 38, 22), ("45m3  27min", 4, 60, 9)]),
      ("3 · Ozonizando", [("OZONIZANDO", 4, 12, 9), ("26:41", 20, 40, 26), ("18m2   RELE ON", 4, 60, 9)]),
      ("4 · Sesión lista", [("SESION LISTA", 4, 16, 11), ("VENTILE ANTES", 4, 38, 11), ("DE ENTRAR", 4, 52, 11)]),
      ("5 · Quién manda", [("MANDO", 4, 12, 9), ("> BLUETOOTH", 4, 34, 11), ("  LOCAL", 4, 50, 11)]),
      ("6 · Programado*", [("PROXIMA 20:30", 4, 14, 11), ("CONSULTORIO", 4, 32, 9), ("27 MIN  20 m2", 4, 48, 9), ("BT", 108, 12, 9)]),
    ]
    W_, H_ = 128*S, 64*S; gx, gy = 40, 120
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {gx*3 + W_*2 + 40} {gy + 3*(H_+70) + 60}"><rect width="100%" height="100%" fill="#F7F8FC"/>',
         f'<text x="{gx}" y="40" {FONT} font-size="20" font-weight="700" fill="{INK}">Pantalla OLED 128×64 · borrador</text>',
         f'<text x="{gx}" y="62" {FONT} font-size="12" fill="#565B6C">Mismos sensores táctiles y misma tarjeta que Teo. Textos y teclas por confirmar con el firmware.</text>',
         f'<text x="{gx}" y="80" {FONT} font-size="11" fill="#8A6D1A">* La pantalla «Programado» solo es posible si la tarjeta tiene reloj propio (RTC o NTP).</text>']
    for i, (tit, lines) in enumerate(scr):
        c, r = i % 2, i // 2; x = gx + c*(W_+gx); y = gy + r*(H_+70)
        o.append(f'<text x="{x}" y="{y-10}" {FONT} font-size="12" font-weight="700" fill="{INK}">{tit}</text>')
        o.append(f'<rect x="{x-10}" y="{y}" width="{W_+20}" height="{H_+20}" rx="10" fill="#1A1A1F"/><rect x="{x}" y="{y+10}" width="{W_}" height="{H_}" fill="#07090C"/>')
        for (txt, lx, ly, sz) in lines:
            o.append(f'<text x="{x+lx*S}" y="{y+10+ly*S}" font-family="Consolas, monospace" font-size="{sz*S*.95:.0f}" fill="#6FE7DC" font-weight="700">{txt.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</text>')
        if i == 2: o.append(f'<rect x="{x+4*S}" y="{y+10+52*S}" width="{110*S}" height="{3*S}" fill="none" stroke="#6FE7DC"/><rect x="{x+4*S}" y="{y+10+52*S}" width="{44*S}" height="{3*S}" fill="#6FE7DC"/>')
    o.append("</svg>"); return "".join(o)
wr("bocetos/boceto-oled-pantallas.svg", oled())
print("ok")
