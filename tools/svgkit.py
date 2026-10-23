"""svgkit: peças para gerar cards SVG de README com texto convertido em <path>.

O GitHub exibe SVG via <img> em sandbox: fonte web e imagem externa não carregam.
Por isso todo texto vira contorno (HarfBuzz + fontTools) e imagens entram em base64.

Uso mínimo:
    from svgkit import Font, Theme, svg, card_frame, heading
    display = Font("fonts/Bangers-Regular.ttf")
    body = Font("fonts/BarlowCondensed-SemiBold.ttf")
    open("h.svg", "w", encoding="utf-8").write(heading("MISSÕES", display, Theme()))

Dependências: fonttools, uharfbuzz.
"""
from __future__ import annotations

import base64
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def num(v: float) -> str:
    """Uma casa decimal: corta ~40% do tamanho do path sem diferença visível."""
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


@dataclass
class Theme:
    card: str = "#121218"      # fundo dos cards (legível nos temas claro e escuro do GitHub)
    line: str = "#2A2A35"      # borda dos cards
    ink: str = "#0B0B0F"       # contorno / texto sobre cor clara
    text: str = "#F5F5F0"      # texto principal
    soft: str = "#C9CBD3"      # texto secundário
    muted: str = "#8B8E99"     # apoio, rótulos discretos
    accent: str = "#FFC93C"    # destaque (caixa de título)
    stripes: list[str] = field(default_factory=lambda: ["#E0262B", "#FFC93C", "#2E9D4A"])


class MissingGlyph(ValueError):
    pass


class Font:
    def __init__(self, path: str | Path):
        path = Path(path)
        self.name = path.stem
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
        """Contorno do texto com a linha de base em y. anchor: start | middle | end."""
        w = self.width(text, size, tracking)
        x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
        s = size / self.upem
        pen = SVGPathPen(self.gs, ntos=num)
        infos, pos = self._shape(text)
        cx = 0.0
        for info, p in zip(infos, pos):
            if info.codepoint == 0:
                raise MissingGlyph(f"{self.name} não tem glifo para algum caractere de {text!r}")
            tp = TransformPen(pen, (s, 0, 0, -s, x + cx + p.x_offset * s, y - p.y_offset * s))
            self.gs[self.order[info.codepoint]].draw(tp)
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

    def fit(self, text: str, size: float, max_w: float, tracking: float = 0, floor: float = 12) -> float:
        """Maior tamanho <= size em que o texto cabe em max_w."""
        while size > floor and self.width(text, size, tracking) > max_w:
            size -= 0.5
        return size


# --------------------------------------------------------------------------- texto rico
Segment = tuple  # (texto, Font, tamanho, cor)


def rich_lines(segs: list[Segment], max_w: float):
    """Quebra trechos com estilos diferentes só nos espaços ("**Igor**." fica junto)."""
    words, cur = [], []
    for text, font, size, color in segs:
        for tok in re.findall(r"\S+|\s+", text):
            if tok.isspace():
                if cur:
                    words.append(cur)
                    cur = []
            else:
                cur.append((tok, font, size, color))
    if cur:
        words.append(cur)

    lines, line, lw = [], [], 0.0
    for w in words:
        space = w[0][1].width(" ", w[0][2]) if line else 0.0
        ww = sum(f.width(t, s) for t, f, s, _ in w)
        if line and lw + space + ww > max_w:
            lines.append(line)
            line, lw, space = [], 0.0, 0.0
        line.append((space, w))
        lw += space + ww
    if line:
        lines.append(line)
    return lines


def line_width(line) -> float:
    return sum(sp + sum(f.width(t, s) for t, f, s, _ in w) for sp, w in line)


def rich_paths(lines, x: float, y: float, line_h: float, align: str = "start", box_w: float = 0) -> list[str]:
    out = []
    for i, line in enumerate(lines):
        cx = x + {"start": 0, "middle": (box_w - line_width(line)) / 2}[align]
        for space, w in line:
            cx += space
            for t, f, s, c in w:
                out.append(f'<path d="{f.path(t, s, cx, y + i * line_h)}" fill="{c}"/>')
                cx += f.width(t, s)
    return out


# --------------------------------------------------------------------------- peças
def svg(w: int, h: int, title: str, body: str, style: str = "") -> str:
    """title vira <title> (leitor de tela); repita o texto completo no alt do <img>."""
    css = f"<style>{style}</style>" if style else ""
    title = title.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-labelledby="t"><title id="t">{title}</title>{css}{body}</svg>\n')


def halftone(pid: str, step: int, r: float, color: str, opacity: float) -> str:
    return (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{step / 2}" cy="{step / 2}" r="{r}" fill="{color}" fill-opacity="{opacity}"/></pattern>')


def data_uri(path: str | Path) -> str:
    """Imagem embutida (avatar, folha de ícones). Não acompanha mudanças no original."""
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def card_frame(w: int, h: int, theme: Theme, rx: int = 18) -> list[str]:
    """Fundo de card: borda, retícula num canto e a faixa de cores do tema à esquerda."""
    box = f'x="2" y="2" width="{w - 4}" height="{h - 4}" rx="{rx}"'
    out = [
        "<defs>" + halftone("htc", 9, 1.6, "#FFFFFF", 0.06) + f'<clipPath id="cf"><rect {box}/></clipPath></defs>',
        f'<rect {box} fill="{theme.card}"/>',
        '<g clip-path="url(#cf)">',
        f'<rect x="{w - 280}" y="2" width="278" height="{min(190, h - 40)}" fill="url(#htc)"/>',
    ]
    x, widths = 2, [10, 5, 5]
    for color, sw in zip(theme.stripes, widths):
        out.append(f'<rect x="{x}" y="2" width="{sw}" height="{h - 4}" fill="{color}"/>')
        x += sw
    out += ["</g>", f'<rect {box} fill="none" stroke="{theme.line}" stroke-width="3"/>']
    return out


def heading(text: str, display: Font, theme: Theme, w: int = 1200, size: float = 40) -> str:
    """Título de seção: caixa inclinada no acento, sombra sólida e régua fina até a borda."""
    h, bx, by, bh, tr = 72, 40, 12, 48, 1.5
    bw = display.width(text, size, tr) + 56
    k = 0.2126  # tan(12°): compensa o skewX nas coordenadas x
    end = bx + bw + 24
    out = ['<g transform="skewX(-12)">',
           f'<rect x="{num(bx + 6 + by * k)}" y="{by + 6}" width="{num(bw)}" height="{bh}" fill="{theme.ink}" opacity=".55"/>',
           f'<rect x="{num(6 + by * k)}" y="{by}" width="22" height="{bh}" fill="{theme.stripes[0]}" '
           f'stroke="{theme.ink}" stroke-width="3"/>',
           f'<rect x="{num(bx + by * k)}" y="{by}" width="{num(bw)}" height="{bh}" fill="{theme.accent}" '
           f'stroke="{theme.ink}" stroke-width="4"/>']
    dx = end
    for color, sw in zip(theme.stripes, (34, 12, 34)):
        out.append(f'<rect x="{num(dx + by * k)}" y="31" width="{sw}" height="10" fill="{color}"/>')
        dx += sw + 8
    out.append("</g>")
    out.append(f'<line x1="{num(dx + 10)}" y1="36" x2="{w - 6}" y2="36" stroke="{theme.muted}" '
               f'stroke-opacity=".45" stroke-width="2"/>')
    base = by + bh / 2 + display.cap_height(size) / 2
    out.append(f'<path d="{display.path(text, size, bx + 26, base, tracking=tr)}" fill="{theme.ink}"/>')
    return svg(w, h, text, "".join(out))


def chip(x: float, y: float, text: str, font: Font, size: float, fill: str, ink: str,
         pad: float = 22, h: float = 46) -> list[str]:
    """Etiqueta inclinada com sombra sólida (estilo legenda de HQ)."""
    w = font.width(text, size, 1) + pad * 2
    return [f'<path d="M{num(x + 10)},{num(y)} h{num(w)} l-10,{num(h)} h-{num(w)} z" fill="{fill}" '
            f'stroke="{ink}" stroke-width="4"/>',
            f'<path d="{font.path(text, size, x + pad + 5, y + h / 2 + font.cap_height(size) / 2, tracking=1)}" '
            f'fill="{ink}"/>']


def balloon(x1: float, y1: float, x2: float, y2: float, r: float, tail_y: float, tail_dx: float = 44) -> str:
    """Balão de fala num único path (o rabicho faz parte do contorno, sem emenda no stroke)."""
    return (f"M{x1 + r},{y1} H{x2 - r} A{r},{r} 0 0 1 {x2},{y1 + r} V{y2 - r} A{r},{r} 0 0 1 {x2 - r},{y2} "
            f"H{x1 + r} A{r},{r} 0 0 1 {x1},{y2 - r} V{num(tail_y + 18)} L{num(x1 - tail_dx)},{num(tail_y + 4)} "
            f"L{x1},{num(tail_y - 16)} V{y1 + r} A{r},{r} 0 0 1 {x1 + r},{y1} Z")


def warning_icon(x: float, y: float, fill: str, ink: str) -> str:
    """Desenhado à mão: fontes de texto raramente têm ⚠."""
    return (f'<g transform="translate({num(x)},{num(y)})"><path d="M0,-15 L16,13 L-16,13 Z" fill="{fill}" '
            f'stroke="{ink}" stroke-width="2.5" stroke-linejoin="round"/>'
            f'<rect x="-1.6" y="-6" width="3.2" height="10" rx="1.4" fill="{ink}"/>'
            f'<circle cy="8" r="1.9" fill="{ink}"/></g>')
