"""Gera os SVGs do README de perfil (tema Robin / Teen Titans).

Todo texto vira <path> (fontes Bangers + Barlow Condensed, OFL), então o
resultado não depende de fonte instalada nem de serviço externo.

    pip install -r tools/requirements.txt
    python tools/build_assets.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"
OUT = ROOT / "assets"

# Paleta do Robin (Teen Titans, 2003)
RED = "#E0262B"
RED_DARK = "#9E1B1F"
GREEN = "#2E9D4A"
GREEN_DARK = "#1E6B33"
YELLOW = "#FFC93C"
YELLOW_DARK = "#D99A00"
BLACK = "#0B0B0F"
INK = "#121218"
LINE = "#2A2A35"
WHITE = "#F5F5F0"
GREY = "#C9CBD3"
MUTED = "#8B8E99"


def num(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


class Font:
    def __init__(self, filename: str):
        path = FONTS / filename
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(hb.Blob.from_file_path(str(path))))

    def _shape(self, text: str):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        infos, pos = self._shape(text)
        return sum(p.x_advance for p in pos) * size / self.upem + tracking * max(len(infos) - 1, 0)

    def cap_height(self, size: float) -> float:
        bp = BoundsPen(self.gs)
        self.gs["H"].draw(bp)
        return bp.bounds[3] * size / self.upem

    def path(self, text: str, size: float, x: float, y: float, anchor: str = "start",
             tracking: float = 0) -> str:
        w = self.width(text, size, tracking)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        s = size / self.upem
        pen = SVGPathPen(self.gs, ntos=num)
        infos, pos = self._shape(text)
        cx = 0.0
        for info, p in zip(infos, pos):
            if info.codepoint == 0:
                raise ValueError(f"glifo ausente em {self.tt['name'].getDebugName(4)}: {text!r}")
            glyph = self.gs[self.order[info.codepoint]]
            tp = TransformPen(pen, (s, 0, 0, -s, x + cx + p.x_offset * s, y - p.y_offset * s))
            glyph.draw(tp)
            cx += p.x_advance * s + tracking
        return pen.getCommands()

    def wrap(self, text: str, size: float, max_w: float) -> list[str]:
        lines, cur = [], ""
        for word in text.split():
            trial = f"{cur} {word}".strip()
            if cur and self.width(trial, size) > max_w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines


BANGERS = Font("Bangers-Regular.ttf")
BARLOW = Font("BarlowCondensed-Medium.ttf")
BARLOW_SB = Font("BarlowCondensed-SemiBold.ttf")
BARLOW_B = Font("BarlowCondensed-Bold.ttf")


def svg(w: int, h: int, title: str, body: str, style: str = "") -> str:
    css = f"<style>{style}</style>" if style else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="t"><title id="t">{title}</title>{css}{body}</svg>\n'
    )


def emblem(cx: float, cy: float, r: float, stroke: float) -> str:
    """Círculo amarelo com o 'R' — desenhado aqui, não é arte oficial."""
    size = r * 1.55
    baseline = cy + BANGERS.cap_height(size) / 2
    return (
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="{YELLOW}" stroke="{BLACK}" '
        f'stroke-width="{num(stroke)}"/>'
        f'<path d="{BANGERS.path("R", size, cx + r * 0.03, baseline, "middle")}" fill="{BLACK}"/>'
    )


def birdarang() -> str:
    return (
        '<path d="M0,-4 L18,-16 L13,-3 L30,0 L13,3 L18,16 L0,4 L-18,16 L-13,3 L-30,0 '
        f'L-13,-3 L-18,-16 Z" fill="#DADCE3" stroke="{RED}" stroke-width="2.5" '
        'stroke-linejoin="round"/>'
        f'<circle r="4" fill="{RED}"/>'
    )


def halftone(pid: str, step: int, r: float, color: str, opacity: float) -> str:
    return (
        f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
        f'<circle cx="{step / 2}" cy="{step / 2}" r="{r}" fill="{color}" fill-opacity="{opacity}"/>'
        "</pattern>"
    )


# --------------------------------------------------------------------------- banner
def banner() -> str:
    W, H = 1200, 400
    rnd = random.Random(7)
    d = [
        '<defs>',
        '<clipPath id="clip"><rect width="1200" height="400" rx="20"/></clipPath>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BLACK}"/><stop offset=".65" stop-color="#160A0E"/>'
        '<stop offset="1" stop-color="#2A0B10"/></linearGradient>',
        '<radialGradient id="moon"><stop offset="0" stop-color="#FFF4CC"/>'
        f'<stop offset=".55" stop-color="{YELLOW}"/><stop offset="1" stop-color="{YELLOW}" stop-opacity="0"/>'
        '</radialGradient>',
        '<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>',
        '<mask id="fadeMask"><rect width="1200" height="400" fill="url(#fade)"/></mask>',
        halftone("dots", 12, 1.8, "#FFFFFF", 0.07),
        halftone("dotsRed", 10, 2.2, "#000000", 0.18),
        '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="14"/></filter>',
        '</defs>',
        '<g clip-path="url(#clip)">',
        '<rect width="1200" height="400" fill="url(#bg)"/>',
        '<rect width="1200" height="400" fill="url(#dots)" mask="url(#fadeMask)"/>',
        # lua + estrelas
        '<circle cx="1120" cy="78" r="96" fill="url(#moon)" opacity=".35"/>',
        f'<circle cx="1120" cy="78" r="48" fill="{YELLOW}" opacity=".92"/>',
        '<circle cx="1106" cy="66" r="8" fill="#E8B020" opacity=".6"/>'
        '<circle cx="1137" cy="90" r="5" fill="#E8B020" opacity=".55"/>',
    ]
    for _ in range(26):
        x, y, r = rnd.uniform(640, 1190), rnd.uniform(15, 200), rnd.uniform(0.8, 1.9)
        d.append(f'<circle class="star" cx="{num(x)}" cy="{num(y)}" r="{num(r)}" fill="#fff" '
                 f'opacity="{num(rnd.uniform(.3, .8))}" style="animation-delay:{num(rnd.uniform(0, 4))}s"/>')

    # skyline da cidade
    x = 640.0
    sky, windows = [], []
    while x < 1200:
        w = rnd.uniform(26, 58)
        h = rnd.uniform(50, 150)
        if 1000 < x < 1200:
            h = rnd.uniform(30, 60)  # abre espaço para a torre
        top = 360 - h
        sky.append(f'<rect x="{num(x)}" y="{num(top)}" width="{num(w)}" height="{num(h)}"/>')
        for wy in range(int(top) + 10, 350, 14):
            for wx in range(int(x) + 6, int(x + w) - 6, 11):
                if rnd.random() < 0.18:
                    windows.append(f'<rect x="{wx}" y="{wy}" width="4" height="6"/>')
        x += w + rnd.uniform(2, 8)
    d.append(f'<g fill="#1B1B24">{"".join(sky)}</g>')
    d.append(f'<g fill="{YELLOW}" opacity=".55">{"".join(windows)}</g>')

    # torre em T (silhueta própria) + ilha + água
    d += [
        '<path d="M1030,362 Q1100,334 1170,362 Z" fill="#0E0E14"/>',
        f'<rect x="1076" y="200" width="48" height="160" fill="#101018" stroke="{LINE}" stroke-width="2"/>',
        f'<rect x="1022" y="150" width="156" height="58" rx="4" fill="#101018" stroke="{LINE}" stroke-width="2"/>',
        f'<rect class="lit" x="1030" y="164" width="140" height="9" fill="{YELLOW}"/>',
        f'<rect x="1030" y="183" width="140" height="5" fill="{YELLOW}" opacity=".45"/>',
        f'<g fill="{YELLOW}" opacity=".7"><rect x="1088" y="222" width="24" height="4"/>'
        '<rect x="1088" y="247" width="24" height="4"/><rect x="1088" y="272" width="24" height="4"/>'
        '<rect x="1088" y="297" width="24" height="4"/><rect x="1088" y="322" width="24" height="4"/></g>',
        '<rect y="360" width="1200" height="40" fill="#0A0C12"/>',
        f'<g stroke="{YELLOW}" stroke-width="2" opacity=".35" stroke-linecap="round">'
        '<line x1="1068" y1="372" x2="1132" y2="372"/><line x1="1078" y1="381" x2="1122" y2="381"/>'
        '<line x1="1090" y1="389" x2="1110" y2="389"/></g>',
    ]

    # faixas do uniforme: vermelho / amarelo / verde
    d += [
        '<g transform="skewX(-12)">',
        f'<rect x="-60" y="0" width="390" height="400" fill="{RED}"/>',
        '<rect x="-60" y="0" width="390" height="400" fill="url(#dotsRed)"/>',
        f'<rect x="342" y="0" width="14" height="400" fill="{YELLOW}"/>',
        f'<rect x="368" y="0" width="24" height="400" fill="{GREEN}"/>',
        '</g>',
    ]

    # emblema
    d += [
        f'<circle class="pulse" cx="170" cy="200" r="96" fill="{YELLOW}" filter="url(#glow)"/>',
        emblem(170, 200, 84, 10),
    ]

    # textos
    tx = 430
    title = "IGOR SEBERINO"
    d += [
        f'<path d="{BANGERS.path(title, 96, tx + 6, 176 + 6, tracking=2)}" fill="{RED_DARK}"/>',
        f'<path d="{BANGERS.path(title, 96, tx, 176, tracking=2)}" fill="{WHITE}" stroke="{BLACK}" '
        'stroke-width="6" stroke-linejoin="round" paint-order="stroke"/>',
    ]
    chip = "CONSULTOR DE IMPLANTAÇÃO @ TOTVS SC"
    cw = BANGERS.width(chip, 30, 1) + 44
    d += [
        f'<path d="M{tx + 10},204 h{num(cw)} l-10,46 h-{num(cw)} z" fill="{YELLOW}" stroke="{BLACK}" stroke-width="4"/>',
        f'<path d="{BANGERS.path(chip, 30, tx + 27, 238, tracking=1)}" fill="{BLACK}"/>',
        f'<path d="{BARLOW_SB.path("Customizações Protheus em AdvPL & TLPP", 28, tx, 296)}" fill="{GREY}"/>',
        f'<path d="{BARLOW.path("Joinville · Santa Catarina · Brasil", 22, tx, 330, tracking=.6)}" fill="{MUTED}"/>',
    ]

    # birdarang cruzando o céu
    d += [
        '<g opacity=".95"><g>',
        birdarang(),
        '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur=".55s" '
        'repeatCount="indefinite"/></g>',
        '<animateMotion path="M-60,95 C320,20 760,150 1270,48" dur="11s" begin="1.2s" '
        'repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;.32;1" calcMode="linear"/></g>',
        # faixa tricolor no rodapé
        f'<rect y="392" width="400" height="8" fill="{RED}"/>'
        f'<rect x="400" y="392" width="400" height="8" fill="{YELLOW}"/>'
        f'<rect x="800" y="392" width="400" height="8" fill="{GREEN}"/>',
        '</g>',
    ]
    style = (
        ".pulse{opacity:.22;animation:pulse 3.2s ease-in-out infinite}"
        "@keyframes pulse{50%{opacity:.5}}"
        ".star{animation:tw 4s ease-in-out infinite}@keyframes tw{50%{opacity:.15}}"
        ".lit{animation:lit 5s steps(1) infinite}@keyframes lit{92%{opacity:.35}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return svg(W, H, "Igor Seberino — Consultor de Implantação na TOTVS SC, dev AdvPL e TLPP",
               "".join(d), style)


# --------------------------------------------------------------------------- divisor
def divider() -> str:
    W, H = 1200, 34
    cx = W / 2
    d = [
        f'<line x1="20" y1="17" x2="{cx - 120}" y2="17" stroke="{MUTED}" stroke-opacity=".45" stroke-width="2"/>',
        f'<line x1="{cx + 120}" y1="17" x2="1180" y2="17" stroke="{MUTED}" stroke-opacity=".45" stroke-width="2"/>',
        '<g transform="skewX(-20)">',
    ]
    off = 17 * math.tan(math.radians(20))  # compensa o skew no centro
    for i, (x, w, c) in enumerate([(-110, 60, RED), (-42, 14, YELLOW), (-20, 0, None),
                                   (36, 14, YELLOW), (58, 60, GREEN)]):
        if c:
            d.append(f'<rect x="{num(cx + x + off)}" y="9" width="{w}" height="16" fill="{c}"/>')
    d.append('</g>')
    d.append(emblem(cx, 17, 15, 3))
    return svg(W, H, "divisor", "".join(d))


# --------------------------------------------------------------------------- cinto
def utility_belt() -> str:
    W, H = 1200, 220
    d = [
        '<defs><linearGradient id="strap" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFD45A"/><stop offset=".5" stop-color="#E8B020"/>'
        f'<stop offset="1" stop-color="{YELLOW_DARK}"/></linearGradient></defs>',
        f'<rect x="10" y="92" width="1180" height="48" rx="10" fill="url(#strap)" stroke="{BLACK}" stroke-width="4"/>',
        f'<line x1="24" y1="101" x2="1176" y2="101" stroke="#8A5E00" stroke-width="2" stroke-dasharray="9 7"/>',
        f'<line x1="24" y1="131" x2="1176" y2="131" stroke="#8A5E00" stroke-width="2" stroke-dasharray="9 7"/>',
    ]
    pouches = [(165, "AdvPL", "LINGUAGEM RAIZ"), (385, "TLPP", "LINGUAGEM MODERNA"),
               (815, "PROTHEUS", "ERP TOTVS"), (1035, "SQL SERVER", "BANCO")]
    for cx, label, sub in pouches:
        x, y, w, h = cx - 98, 46, 196, 150
        d += [
            f'<rect x="{x + 5}" y="{y + 7}" width="{w}" height="{h}" rx="16" fill="{BLACK}" opacity=".35"/>',
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="#F4B91C" stroke="{BLACK}" stroke-width="4"/>',
            f'<path d="M{x},{y + 16} a16,16 0 0 1 16,-16 h{w - 32} a16,16 0 0 1 16,16 v34 '
            f'q-{w / 2},26 -{w},0 z" fill="{YELLOW_DARK}" stroke="{BLACK}" stroke-width="4" stroke-linejoin="round"/>',
            f'<circle cx="{cx}" cy="{y + 56}" r="7" fill="{RED}" stroke="{BLACK}" stroke-width="3"/>',
            f'<path d="{BANGERS.path(label, 36, cx, y + 116, "middle", 1)}" fill="{BLACK}"/>',
            f'<path d="{BARLOW_B.path(sub, 15, cx, y + 138, "middle", 1.2)}" fill="#5A3B00"/>',
        ]
    d += [
        f'<rect x="530" y="66" width="140" height="100" rx="18" fill="#F4B91C" stroke="{BLACK}" stroke-width="5"/>',
        emblem(600, 116, 38, 5),
    ]
    return svg(W, H, "Cinto de utilidades: AdvPL, TLPP, Protheus e SQL Server", "".join(d))


# --------------------------------------------------------------------------- missões
def mission(num_label: str, repo: str, title: str, desc: str, role: str, chips: list[str]) -> str:
    W, H = 600, 280
    d = [
        '<defs>' + halftone("ht", 9, 1.6, "#FFFFFF", 0.06) + '</defs>',
        f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="16" fill="{INK}" stroke="{LINE}" stroke-width="3"/>',
        f'<path d="M420,2 h162 a16,16 0 0 1 16,16 v120 z" fill="url(#ht)"/>',
        f'<rect x="2" y="2" width="10" height="{H - 4}" rx="5" fill="{RED}"/>',
        f'<rect x="12" y="2" width="5" height="{H - 4}" fill="{YELLOW}"/>',
        f'<rect x="17" y="2" width="5" height="{H - 4}" fill="{GREEN}"/>',
    ]
    tw = BANGERS.width(num_label, 24, 1) + 32
    d += [
        f'<path d="M44,22 h{num(tw)} l-8,36 h-{num(tw)} z" fill="{YELLOW}" stroke="{BLACK}" stroke-width="3"/>',
        f'<path d="{BANGERS.path(num_label, 24, 56, 49, tracking=1)}" fill="{BLACK}"/>',
        f'<path d="{BARLOW.path(repo, 18, W - 30, 46, "end")}" fill="{MUTED}"/>',
        f'<path d="{BANGERS.path(title, 46, 44, 112, tracking=1.5)}" fill="{WHITE}"/>',
    ]
    y = 146
    for line in BARLOW.wrap(desc, 20, W - 80)[:2]:
        d.append(f'<path d="{BARLOW.path(line, 20, 44, y)}" fill="{GREY}"/>')
        y += 24
    y += 6
    label = "MINHA PARTE:  "
    lw = BARLOW_B.width(label, 18, .8)
    d.append(f'<path d="{BARLOW_B.path(label, 18, 44, y, tracking=.8)}" fill="{GREEN}"/>')
    first, *rest = BARLOW.wrap(role, 19, W - 80 - lw)
    d.append(f'<path d="{BARLOW.path(first, 19, 44 + lw, y)}" fill="{WHITE}"/>')
    rest_lines = BARLOW.wrap(" ".join(rest), 19, W - 80) if rest else []
    for line in rest_lines[:1]:
        y += 23
        d.append(f'<path d="{BARLOW.path(line, 19, 44, y)}" fill="{WHITE}"/>')
    cx, cy = 44, y + 22
    for i, chip in enumerate(chips):
        cw = BARLOW_SB.width(chip, 17, .5) + 26
        color = (RED, YELLOW, GREEN)[i % 3]
        d += [
            f'<rect x="{num(cx)}" y="{cy}" width="{num(cw)}" height="30" rx="15" fill="{color}" fill-opacity=".12" '
            f'stroke="{color}" stroke-width="2"/>',
            f'<path d="{BARLOW_SB.path(chip, 17, cx + cw / 2, cy + 21, "middle", .5)}" fill="{WHITE}"/>',
        ]
        cx += cw + 10
    return svg(W, H, f"{num_label}: {title} — {desc}", "".join(d))


# --------------------------------------------------------------------------- rodapé
def footer() -> str:
    W, H = 1200, 200
    cx, cy = 600, 92
    pts = []
    n = 22
    for i in range(n * 2):
        a = math.pi * i / n
        k = 1.0 if i % 2 == 0 else 0.74
        pts.append(f"{num(cx + math.cos(a) * 250 * k)},{num(cy + math.sin(a) * 78 * k)}")
    lines = []
    rnd = random.Random(3)
    for side in (-1, 1):
        for i in range(7):
            y = 40 + i * 17 + rnd.uniform(-4, 4)
            x1 = cx + side * rnd.uniform(270, 300)
            x2 = x1 + side * rnd.uniform(90, 220)
            lines.append(f'<line x1="{num(x1)}" y1="{num(y)}" x2="{num(x2)}" y2="{num(y)}"/>')
    text = "TITANS, GO!"
    d = [
        f'<g stroke="{MUTED}" stroke-opacity=".55" stroke-width="3" stroke-linecap="round">{"".join(lines)}</g>',
        f'<g class="burst"><polygon points="{" ".join(pts)}" fill="{YELLOW}" stroke="{BLACK}" '
        'stroke-width="6" stroke-linejoin="round"/>',
        f'<path d="{BANGERS.path(text, 76, cx + 5, cy + 30, "middle", 2)}" fill="{BLACK}"/>',
        f'<path d="{BANGERS.path(text, 76, cx, cy + 25, "middle", 2)}" fill="{RED}" stroke="{BLACK}" '
        'stroke-width="5" stroke-linejoin="round" paint-order="stroke"/></g>',
        f'<path d="{BARLOW_SB.path("valeu pela visita — a Torre fica sempre de portas abertas", 21, cx, 192, "middle", .4)}" '
        f'fill="{MUTED}"/>',
    ]
    style = (
        ".burst{transform-origin:600px 92px;animation:pop 2.8s ease-in-out infinite}"
        "@keyframes pop{0%,100%{transform:scale(1)}50%{transform:scale(1.04) rotate(-1deg)}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return svg(W, H, "Titans, GO! — valeu pela visita", "".join(d), style)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    files = {
        "banner.svg": banner(),
        "divider.svg": divider(),
        "utility-belt.svg": utility_belt(),
        "mission-srec.svg": mission(
            "MISSÃO #01", "igorSeberino/srec", "SREC",
            "Reservas de estações de trabalho e salas de reunião para coworking: "
            "disponibilidade, agendamento e gestão do espaço.",
            "auditoria do código herdado, backlog da manutenção e plano de testes e regressão (QA).",
            ["React", "Node.js", "PostgreSQL", "QA"],
        ),
        "mission-ludens.svg": mission(
            "MISSÃO #02", "gcarvalhow/api.ludens", "LUDENS · API",
            "Backend da Ludens, venda de ingressos de um teatro comunitário: "
            "espetáculos, assentos, Pix e ingresso na mão.",
            "cadastro e autenticação do comprador e os endpoints de catálogo (espetáculos, sessões e busca).",
            ["Python", "FastAPI", "PostgreSQL", "DDD", "Docker"],
        ),
        "footer.svg": footer(),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name}: {len(content) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
