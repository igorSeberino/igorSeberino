"""Identidade visual do perfil (Robin / Teen Titans): paleta, fontes e emblema.

Compartilhado por build_assets.py (cards fixos em assets/) e widgets.py
(cards vivos que o workflow publica na branch output).
"""
from __future__ import annotations

from pathlib import Path

from svgkit import Font, Theme, halftone, num

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts"

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
TRIO = (RED, YELLOW, GREEN)

THEME = Theme(card=INK, line=LINE, ink=BLACK, text=WHITE, soft=GREY, muted=MUTED,
              accent=YELLOW, stripes=list(TRIO))

BANGERS = Font(FONTS / "Bangers-Regular.ttf")
BARLOW = Font(FONTS / "BarlowCondensed-Medium.ttf")
BARLOW_SB = Font(FONTS / "BarlowCondensed-SemiBold.ttf")
BARLOW_B = Font(FONTS / "BarlowCondensed-Bold.ttf")


def emblem(cx: float, cy: float, r: float, stroke: float) -> str:
    """Círculo amarelo com o 'R', desenhado aqui (não é arte oficial)."""
    size = r * 1.55
    baseline = cy + BANGERS.cap_height(size) / 2
    return (f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="{YELLOW}" stroke="{BLACK}" '
            f'stroke-width="{num(stroke)}"/>'
            f'<path d="{BANGERS.path("R", size, cx + r * 0.03, baseline, "middle")}" fill="{BLACK}"/>')


def frame(w: int, h: int, rx: int = 18, ht_w: int = 280, ht_h: int = 190) -> list[str]:
    """Fundo dos cards: borda, retícula em triângulo no canto e faixa tricolor à esquerda."""
    return [
        "<defs>" + halftone("htc", 9, 1.6, "#FFFFFF", 0.06) + "</defs>",
        f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" rx="{rx}" fill="{INK}" stroke="{LINE}" stroke-width="3"/>',
        f'<path d="M{w - ht_w},2 h{ht_w - 18} a16,16 0 0 1 16,16 v{min(ht_h, h - 40)} z" fill="url(#htc)"/>',
        f'<rect x="2" y="2" width="10" height="{h - 4}" rx="5" fill="{RED}"/>',
        f'<rect x="12" y="2" width="5" height="{h - 4}" fill="{YELLOW}"/>',
        f'<rect x="17" y="2" width="5" height="{h - 4}" fill="{GREEN}"/>',
    ]


def tab(x: float, y: float, text: str, size: float = 24) -> list[str]:
    """Etiqueta amarela inclinada do canto dos cards ("MISSÃO #01")."""
    tw = BANGERS.width(text, size, 1) + 32
    return [f'<path d="M{num(x)},{num(y)} h{num(tw)} l-8,36 h-{num(tw)} z" fill="{YELLOW}" '
            f'stroke="{BLACK}" stroke-width="3"/>',
            f'<path d="{BANGERS.path(text, size, x + 12, y + 27, tracking=1)}" fill="{BLACK}"/>']
