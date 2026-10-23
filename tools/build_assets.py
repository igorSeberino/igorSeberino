"""Gera os SVGs fixos do README de perfil (tema Robin / Teen Titans) em assets/.

Todo texto vira <path> (fontes Bangers + Barlow Condensed, OFL), então o
resultado não depende de fonte instalada nem de serviço externo. As peças
genéricas vêm do svgkit (skill readme-design); a identidade fica em robin.py.

    pip install -r tools/requirements.txt
    python tools/build_assets.py
"""
from __future__ import annotations

import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from robin import (BANGERS, BARLOW, BARLOW_B, BARLOW_SB, BLACK, GREEN, GREY, INK, LINE,  # noqa: E402
                   MUTED, RED, RED_DARK, ROOT, THEME, TRIO, WHITE, YELLOW, YELLOW_DARK, emblem, frame, tab)
from svgkit import (balloon, chip, data_uri, halftone, heading, line_width, num, rich_lines,  # noqa: E402
                    rich_paths, svg, warning_icon)

OUT = ROOT / "assets"
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


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
    label = "CONSULTOR DE IMPLANTAÇÃO @ TOTVS SC"
    cw = BANGERS.width(label, 30, 1) + 44
    d += [
        f'<path d="M{tx + 10},204 h{num(cw)} l-10,46 h-{num(cw)} z" fill="{YELLOW}" stroke="{BLACK}" stroke-width="4"/>',
        f'<path d="{BANGERS.path(label, 30, tx + 27, 238, tracking=1)}" fill="{BLACK}"/>',
        f'<path d="{BARLOW_SB.path("Customizações Protheus em AdvPL & TLPP", 28, tx, 296)}" fill="{GREY}"/>',
        f'<path d="{BARLOW.path("Joinville · Santa Catarina · Brasil", 22, tx, 330, tracking=.6)}" fill="{MUTED}"/>',
    ]

    # faixa tricolor no rodapé
    d += [
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
        + REDUCED
    )
    return svg(W, H, "Igor Seberino — Consultor de Implantação na TOTVS SC, dev AdvPL e TLPP",
               "".join(d), style)


# --------------------------------------------------------------------------- crachás (abaixo do banner)
def chip_shadowed(x: float, y: float, text: str, font, size: float, fill: str, ink: str = BLACK) -> list[str]:
    shape, label = chip(x, y, text, font, size, fill, ink)
    shadow = chip(x, y, text, font, size, BLACK, BLACK)[0]
    return [f'<g transform="translate(5,6)" opacity=".45">{shadow}</g>', shape, label]


def chip_width(text: str, font, size: float) -> float:
    return font.width(text, size, 1) + 44 + 10  # pad * 2 + inclinação


def badges() -> str:
    """Três crachás: equipe, especialidade, base. 780 x 64 para casar com badge_mail (400 x 64)."""
    W, H, size, gap = 780, 64, 25, 16
    items = [("TOTVS SC · CONSULTOR DE IMPLANTAÇÃO", RED), ("ADVPL · TLPP", YELLOW), ("JOINVILLE · SC", GREEN)]
    total = sum(chip_width(t, BANGERS, size) for t, _ in items) + gap * (len(items) - 1)
    x = (W - total) / 2
    d = []
    for text, color in items:
        d += chip_shadowed(x, 6, text, BANGERS, size, color)
        x += chip_width(text, BANGERS, size) + gap
    return svg(W, H, "TOTVS SC, Consultor de Implantação · AdvPL e TLPP · Joinville, SC", "".join(d))


def badge_mail() -> str:
    W, H, size = 400, 64, 25
    email = "igor.seberino@totvs.com.br"
    w = chip_width(email, BARLOW_B, size)
    return svg(W, H, f"E-mail: {email}", "".join(chip_shadowed((W - w) / 2, 6, email, BARLOW_B, size, WHITE)))


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
    for x, w, c in [(-110, 60, RED), (-42, 14, YELLOW), (36, 14, YELLOW), (58, 60, GREEN)]:
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
        '<line x1="24" y1="101" x2="1176" y2="101" stroke="#8A5E00" stroke-width="2" stroke-dasharray="9 7"/>',
        '<line x1="24" y1="131" x2="1176" y2="131" stroke="#8A5E00" stroke-width="2" stroke-dasharray="9 7"/>',
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
    d = frame(W, H, rx=16, ht_w=180, ht_h=120)
    d += tab(44, 22, num_label)
    d += [
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
    for i, text in enumerate(chips):
        cw = BARLOW_SB.width(text, 17, .5) + 26
        color = TRIO[i % 3]
        d += [
            f'<rect x="{num(cx)}" y="{cy}" width="{num(cw)}" height="30" rx="15" fill="{color}" fill-opacity=".12" '
            f'stroke="{color}" stroke-width="2"/>',
            f'<path d="{BARLOW_SB.path(text, 17, cx + cw / 2, cy + 21, "middle", .5)}" fill="{WHITE}"/>',
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
        + REDUCED
    )
    return svg(W, H, "Titans, GO! — valeu pela visita", "".join(d), style)


# --------------------------------------------------------------------------- ficha
def titan_file() -> str:
    W, H = 1200, 440
    d = frame(W, H)
    d[0] = ('<defs>' + halftone("htc", 9, 1.6, "#FFFFFF", 0.06) + halftone("htr", 8, 1.6, RED, 0.25)
            + '<clipPath id="ph"><rect x="-120" y="-120" width="240" height="240" rx="10"/></clipPath></defs>')

    # foto estilo polaroid presa na ficha
    px, py = 200, 205
    d += [
        f'<g transform="translate({px},{py}) rotate(-4)">',
        f'<rect x="-136" y="-136" width="272" height="318" rx="10" fill="{BLACK}" opacity=".45" transform="translate(7,9)"/>',
        f'<rect x="-136" y="-136" width="272" height="318" rx="10" fill="{YELLOW}" stroke="{BLACK}" stroke-width="5"/>',
        f'<rect x="-121" y="-121" width="242" height="242" rx="10" fill="{BLACK}"/>',
        f'<image href="{data_uri(ROOT / "tools" / "avatar.jpg")}" x="-120" y="-120" width="240" height="240" '
        'clip-path="url(#ph)" preserveAspectRatio="xMidYMid slice"/>',
        f'<path d="{BANGERS.path("ID CONFIRMADA", 30, 0, 160, "middle", 1.5)}" fill="{BLACK}"/>',
        '</g>',
        # fita adesiva
        f'<rect x="150" y="52" width="104" height="30" fill="{WHITE}" opacity=".55" transform="rotate(-9 202 67)"/>',
        # emblema no canto da foto
        f'<g transform="translate(318,96)">{emblem(0, 0, 30, 5)}</g>',
    ]

    # cabeçalho
    x0 = 400
    d += [
        f'<path d="{BARLOW_B.path("IDENTIDADE", 17, x0, 62, tracking=2.4)}" fill="{YELLOW}"/>',
        f'<path d="{BANGERS.path("IGOR THIAGO SEBERINO", 58, x0 + 4, 120 + 4, tracking=1.5)}" fill="{RED_DARK}"/>',
        f'<path d="{BANGERS.path("IGOR THIAGO SEBERINO", 58, x0, 120, tracking=1.5)}" fill="{WHITE}" '
        f'stroke="{BLACK}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"/>',
        f'<path d="{BARLOW_SB.path("ARQUIVO T-01 · TORRE TITÃ", 17, W - 40, 62, "end", 1.6)}" fill="{MUTED}"/>',
    ]
    # carimbo
    stamp = "CONFIDENCIAL"
    sw = BANGERS.width(stamp, 34, 3) + 36
    d += [
        '<g transform="translate(1040,118) rotate(-10)" opacity=".85">',
        f'<rect x="{num(-sw / 2)}" y="-27" width="{num(sw)}" height="54" rx="6" fill="none" stroke="{RED}" stroke-width="4"/>',
        f'<rect x="{num(-sw / 2 + 6)}" y="-21" width="{num(sw - 12)}" height="42" rx="3" fill="url(#htr)" stroke="{RED}" stroke-width="1.5"/>',
        f'<path d="{BANGERS.path(stamp, 34, 0, 13, "middle", 3)}" fill="{RED}"/>',
        '</g>',
        f'<line x1="{x0}" y1="146" x2="{W - 40}" y2="146" stroke="{LINE}" stroke-width="2"/>',
    ]

    # campos 3 x 2
    fields = [
        ("BASE", "Joinville · SC", "Brasil"),
        ("EQUIPE", "TOTVS SC", "em serviço"),
        ("FUNÇÃO", "Consultor de Implantação", "TOTVS Protheus"),
        ("ESPECIALIDADE", "AdvPL · TLPP", "desenvolvimento"),
        ("TREINAMENTO", "Engenharia de Software", "Católica SC · até 2027"),
        ("IDIOMAS", "Português · Inglês", "nativo · intermediário"),
    ]
    colw = (W - 40 - x0) / 3
    for i, (label, value, sub) in enumerate(fields):
        cx = x0 + (i % 3) * colw
        cy = 186 + (i // 3) * 92
        color = TRIO[i % 3]
        size = BARLOW_SB.fit(value, 27, colw - 34)
        d += [
            f'<rect x="{num(cx)}" y="{cy - 16}" width="4" height="70" rx="2" fill="{color}"/>',
            f'<path d="{BARLOW_B.path(label, 15, cx + 16, cy, tracking=2)}" fill="{color}"/>',
            f'<path d="{BARLOW_SB.path(value, size, cx + 16, cy + 31)}" fill="{WHITE}"/>',
            f'<path d="{BARLOW.path(sub, 18, cx + 16, cy + 54)}" fill="{MUTED}"/>',
        ]

    # antecedentes
    by = 362
    d += [
        f'<rect x="{x0}" y="{by}" width="{W - 40 - x0}" height="50" rx="10" fill="{RED}" fill-opacity=".12" '
        f'stroke="{RED}" stroke-width="2"/>',
        warning_icon(x0 + 30, by + 25, YELLOW, BLACK),
        f'<path d="{BARLOW_B.path("ANTECEDENTES", 15, x0 + 60, by + 31, tracking=2)}" fill="{RED}"/>',
    ]
    lw = BARLOW_B.width("ANTECEDENTES", 15, 2)
    txt = "Ex-jogador de LoL. Está em recuperação e prefere não falar sobre isso."
    size = BARLOW_SB.fit(txt, 22, W - 40 - x0 - lw - 100)
    d.append(f'<path d="{BARLOW_SB.path(txt, size, x0 + 80 + lw, by + 32)}" fill="{WHITE}"/>')
    return svg(W, H, "Ficha do Titã: Igor Thiago Seberino, Joinville - SC, TOTVS SC, Consultor de Implantação, "
                     "AdvPL e TLPP, Engenharia de Software na Católica SC, ex-jogador de LoL", "".join(d))


# --------------------------------------------------------------------------- quem é esse aí
def about() -> str:
    W = 1200
    R, B = BARLOW_SB, BARLOW_B
    sz = 27
    segs = [
        ("E aí! Sou o ", R, sz, INK), ("Igor", B, sz, INK), (". No crachá, ", R, sz, INK),
        ("Consultor de Implantação na TOTVS SC", B, sz, INK), ("; no dia a dia, quem escreve as ", R, sz, INK),
        ("customizações do Protheus", B, sz, RED_DARK), (" em ", R, sz, INK), ("AdvPL", B, sz, RED_DARK),
        (" e ", R, sz, INK), ("TLPP", B, sz, RED_DARK),
        (": aquela regra de negócio que o padrão não cobre e o cliente precisa pra ontem.", R, sz, INK),
    ]
    x1, x2, y1 = 196, 1192, 10
    lines = rich_lines(segs, x2 - x1 - 84)
    lh = 37
    first = y1 + 56
    y2 = first + (len(lines) - 1) * lh + 34
    r = 34
    ty = (y1 + y2) / 2
    shape = balloon(x1, y1, x2, y2, r, ty)
    d = [
        '<defs>' + halftone("htb", 8, 1.5, "#000000", 0.07) + '</defs>',
        f'<path d="{shape}" fill="{BLACK}" opacity=".5" transform="translate(6,7)"/>',
        f'<path d="{shape}" fill="{WHITE}" stroke="{BLACK}" stroke-width="5" stroke-linejoin="round"/>',
        f'<path d="M{x2 - 260},{y1 + 3} H{x2 - r} A{r},{r} 0 0 1 {x2 - 3},{y1 + r} V{y1 + 90} Z" fill="url(#htb)"/>',
        emblem(92, ty, 62, 8),
    ]
    d += rich_paths(lines, x1 + 42, first, lh)

    cols = [
        ("NO TRAMPO", RED, "Customizo o TOTVS Protheus: de ponto de entrada a rotina nova."),
        ("NA FACULDADE", YELLOW, "Engenharia de Software na Católica SC, com formatura prevista para 2027."),
        ("FORA DO ERP", GREEN, "Faço web com Python, JavaScript e C# nos projetos da faculdade."),
    ]
    cy = y2 + 30
    gap = 22
    cw = (W - 8 - gap * 2) / 3
    ch = 138
    for i, (title, color, txt) in enumerate(cols):
        cx = 4 + i * (cw + gap)
        d += [
            f'<rect x="{num(cx)}" y="{num(cy)}" width="{num(cw)}" height="{ch}" rx="16" fill="{INK}" stroke="{LINE}" stroke-width="3"/>',
            f'<path d="M{num(cx)},{num(cy + 16)} a16,16 0 0 1 16,-16 h{num(cw - 32)} a16,16 0 0 1 16,16 v-8 h-{num(cw)} z" fill="{color}"/>',
            f'<rect x="{num(cx)}" y="{num(cy + 8)}" width="{num(cw)}" height="8" fill="{color}"/>',
            f'<path d="{BANGERS.path(title, 32, cx + 26, cy + 58, tracking=1.5)}" fill="{color}"/>',
        ]
        for j, line in enumerate(BARLOW.wrap(txt, 22, cw - 52)[:3]):
            d.append(f'<path d="{BARLOW.path(line, 22, cx + 26, cy + 92 + j * 27)}" fill="{GREY}"/>')
    H = int(cy + ch + 4)
    return svg(W, H, "Quem é esse aí? E aí! Sou o Igor, Consultor de Implantação na TOTVS SC, que escreve as "
                     "customizações do Protheus em AdvPL e TLPP.", "".join(d))


# --------------------------------------------------------------------------- também no cinto
def gear() -> str:
    W = 1200
    icons_path = ROOT / "tools" / "skillicons.svg"
    m = re.search(rb'viewBox="0 0 ([\d.]+) ([\d.]+)"', icons_path.read_bytes())
    iw = 820
    ih = iw * float(m.group(2)) / float(m.group(1))
    iy = 92
    H = int(iy + ih + 76)
    d = frame(W, H)
    d += [
        f'<path d="{BANGERS.path("TAMBÉM NO CINTO", 40, 50, 64, tracking=1.5)}" fill="{WHITE}"/>',
        f'<path d="{BARLOW_SB.path("EQUIPAMENTO SECUNDÁRIO", 17, W - 40, 60, "end", 2)}" fill="{MUTED}"/>',
        f'<image href="{data_uri(icons_path)}" x="{num((W - iw) / 2)}" y="{iy}" width="{iw}" height="{num(ih)}"/>',
    ]
    segs = [("…e um pé no ", BARLOW, 23, GREY), ("Progress / OpenEdge ABL", BARLOW_B, 23, YELLOW),
            (", do curso extracurricular da TOTVS.", BARLOW, 23, GREY)]
    lines = rich_lines(segs, W - 100)
    d += rich_paths(lines, (W - line_width(lines[0])) / 2, iy + ih + 46, 28)
    return svg(W, H, "Também no cinto: Python, C#, JavaScript, React, Node.js, Express, Django, FastAPI, .NET, "
                     "Tailwind, PostgreSQL, MySQL, Flutter, Godot, Git, GitHub e um pé no Progress / OpenEdge ABL",
               "".join(d))


# --------------------------------------------------------------------------- comunicador
def communicator() -> str:
    W, H = 1200, 250
    d = frame(W, H)
    cx, cy = 168, 125
    d += [
        f'<circle cx="{cx + 5}" cy="{cy + 7}" r="88" fill="{BLACK}" opacity=".5"/>',
        f'<circle cx="{cx}" cy="{cy}" r="88" fill="{YELLOW}" stroke="{BLACK}" stroke-width="6"/>',
        f'<circle cx="{cx}" cy="{cy}" r="71" fill="#E8B020" stroke="{BLACK}" stroke-width="3"/>',
        f'<circle cx="{cx}" cy="{cy}" r="56" fill="{BLACK}" stroke="{LINE}" stroke-width="3"/>',
        f'<path d="{BANGERS.path("T", 74, cx, cy + BANGERS.cap_height(74) / 2, "middle")}" fill="{YELLOW}"/>',
        f'<circle class="led" cx="{cx + 62}" cy="{cy - 62}" r="10" fill="{RED}" stroke="{BLACK}" stroke-width="3"/>',
    ]
    for i, rr in enumerate((26, 44, 62)):
        d.append(f'<path class="wave w{i}" d="M{cx + 104},{cy - rr} a{rr},{rr} 0 0 1 0,{rr * 2}" fill="none" '
                 f'stroke="{GREEN}" stroke-width="5" stroke-linecap="round"/>')
    x0 = 360
    email = "igor.seberino@totvs.com.br"
    ew = BARLOW_B.width(email, 52)
    d += [
        f'<circle class="led" cx="{x0 + 6}" cy="56" r="6" fill="{GREEN}"/>',
        f'<path d="{BARLOW_B.path("CANAL ABERTO", 17, x0 + 22, 62, tracking=2.4)}" fill="{GREEN}"/>',
        f'<path d="{BARLOW_SB.path("Bug no ponto de entrada, dúvida de AdvPL/TLPP ou só pra trocar ideia:", 27, x0, 108)}" fill="{GREY}"/>',
        f'<path d="{BARLOW_B.path(email, 52, x0, 172)}" fill="{WHITE}"/>',
        f'<rect x="{x0}" y="184" width="{num(ew)}" height="6" fill="{YELLOW}"/>',
    ]
    label = "CHAMAR"
    lw = BANGERS.width(label, 28, 1.5)
    bx = x0 + ew + 40
    bw = lw + 70
    d += [
        f'<g transform="translate({num(bx)},0) skewX(-12)">',
        f'<rect x="{30 + 6}" y="{132 + 6}" width="{num(bw)}" height="50" fill="{BLACK}" opacity=".55"/>',
        f'<rect x="30" y="132" width="{num(bw)}" height="50" fill="{RED}" stroke="{BLACK}" stroke-width="4"/>',
        '</g>',
        f'<path d="{BANGERS.path(label, 28, bx + 22, 168, tracking=1.5)}" fill="{WHITE}"/>',
        f'<path d="M{num(bx + 34 + lw)},148 l14,9 l-14,9 z" fill="{YELLOW}" stroke="{BLACK}" stroke-width="2" stroke-linejoin="round"/>',
    ]
    style = (
        ".led{animation:blink 1.6s steps(1) infinite}@keyframes blink{50%{opacity:.25}}"
        ".wave{opacity:0;animation:wave 2.4s ease-out infinite}.w1{animation-delay:.3s}.w2{animation-delay:.6s}"
        "@keyframes wave{0%{opacity:0}30%{opacity:1}100%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){*{animation:none!important}.wave{opacity:1}}"
    )
    return svg(W, H, f"Comunicador: {email}", "".join(d), style)


HEADINGS = {
    "h-quem.svg": "QUEM É ESSE AÍ?",
    "h-ficha.svg": "FICHA DO TITÃ",
    "h-cinto.svg": "CINTO DE UTILIDADES",
    "h-missoes.svg": "MISSÕES",
    "h-relatorio.svg": "RELATÓRIO DA TORRE",
    "h-patrulha.svg": "PATRULHA NOTURNA",
    "h-comunicador.svg": "COMUNICADOR",
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    files = {
        "banner.svg": banner(),
        "badges.svg": badges(),
        "badge-mail.svg": badge_mail(),
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
        "titan-file.svg": titan_file(),
        "about.svg": about(),
        "gear.svg": gear(),
        "communicator.svg": communicator(),
        **{name: heading(text, BANGERS, THEME) for name, text in HEADINGS.items()},
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name}: {len(content) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
