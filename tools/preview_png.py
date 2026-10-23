"""Renderiza os SVGs gerados num PNG de conferência (fundo escuro e claro)."""
import io
import sys
from pathlib import Path

import resvg_py
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "assets"
out = Path(sys.argv[1])
W = 1200
rows = [["banner.svg"], ["divider.svg"], ["utility-belt.svg"], ["mission-srec.svg", "mission-ludens.svg"],
        ["footer.svg"]]


def render(name, width):
    png = resvg_py.svg_to_bytes(svg_path=str(ROOT / name), width=width)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def sheet(bg):
    imgs = []
    for row in rows:
        w = W if len(row) == 1 else (W - 20) // 2
        imgs.append([render(n, w) for n in row])
    h = sum(max(i.height for i in r) + 24 for r in imgs) + 24
    canvas = Image.new("RGBA", (W + 48, h), bg)
    y = 24
    for r in imgs:
        x = 24
        for im in r:
            canvas.alpha_composite(im, (x, y))
            x += im.width + 20
        y += max(i.height for i in r) + 24
    return canvas


dark, light = sheet("#0d1117"), sheet("#ffffff")
final = Image.new("RGBA", (dark.width, dark.height + light.height))
final.paste(dark, (0, 0))
final.paste(light, (0, dark.height))
final.convert("RGB").save(out)
print(out)
