"""Gera o contador "Visitas na Torre" no visual do perfil (roda no GitHub Actions).

O README tem um pixel do komarev.com que conta cada visualização do perfil.
Aqui lemos esse total, descontamos as leituras feitas pelo próprio workflow
(cada leitura também conta +1) e desenhamos o SVG com as fontes do repo.

    python tools/visits.py dist            # usa o komarev e o estado da branch output
    python tools/visits.py dist --count 42 # teste local, sem rede
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import visits  # noqa: E402

URL = "https://komarev.com/ghpvc/?username=igorSeberino&style=flat"


def previous_state() -> dict:
    try:
        subprocess.run(["git", "fetch", "--depth=1", "origin", "output"], check=True, capture_output=True)
        raw = subprocess.run(["git", "show", "FETCH_HEAD:visits.json"], check=True, capture_output=True).stdout
        return json.loads(raw)
    except Exception:
        return {"bot_hits": 0}


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    if "--count" in sys.argv:
        shown = int(sys.argv[sys.argv.index("--count") + 1])
        state = {"raw": shown, "bot_hits": 0, "shown": shown}
    else:
        state = previous_state()
        req = urllib.request.Request(URL, headers={"User-Agent": "igorSeberino-profile"})
        body = urllib.request.urlopen(req, timeout=30).read().decode()
        texts = re.findall(r"<text[^>]*>([^<]*)</text>", body)
        raw = int(re.sub(r"\D", "", texts[-1]))
        bot = int(state.get("bot_hits", 0)) + 1
        state = {"raw": raw, "bot_hits": bot, "shown": max(raw - bot, 0)}
    (out / "visits.svg").write_text(visits(state["shown"]), encoding="utf-8")
    (out / "visits.json").write_text(json.dumps(state), encoding="utf-8")
    print(state)


if __name__ == "__main__":
    main()
