"""Cards vivos do perfil: visitas, estatísticas e sequência de contribuições.

Roda no GitHub Actions (workflow torre.yml) e grava em dist/, que vai para a
branch output. Substitui github-readme-stats e streak-stats: mesmos números,
mas no visual do perfil e sem depender de serviço gratuito de terceiros.

    python tools/widgets.py dist                      # komarev + API do GitHub (GH_TOKEN)
    python tools/widgets.py dist --visits 42          # não lê o komarev (não infla o contador)
    python tools/widgets.py dist --visits 42 --sample # sem rede nenhuma, dados de exemplo
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from robin import (BANGERS, BARLOW, BARLOW_B, BLACK, GREEN, GREY, LINE, MUTED, RED,  # noqa: E402
                   TRIO, WHITE, YELLOW, emblem, frame, tab)
from svgkit import num, svg  # noqa: E402

USER = "igorSeberino"
KOMAREV = f"https://komarev.com/ghpvc/?username={USER}&style=flat"
UA = {"User-Agent": f"{USER}-profile"}


# --------------------------------------------------------------------------- dados
def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("defina GH_TOKEN (no Actions: github.token)")
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={**UA, "Authorization": f"bearer {token}"})
    body = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if body.get("errors"):
        raise SystemExit(f"GraphQL: {body['errors']}")
    return body["data"]


PROFILE_Q = """query($login:String!){user(login:$login){
  createdAt
  repositories(ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false, first:100){totalCount nodes{stargazerCount}}
  pullRequests{totalCount}
  issues{totalCount}
  repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]){totalCount}
}}"""

YEAR_Q = ("y{y}: contributionsCollection(from:\"{f}\", to:\"{t}\"){{totalCommitContributions "
          "contributionCalendar{{totalContributions weeks{{contributionDays{{date contributionCount}}}}}}}}")


def fetch_stats(login: str) -> dict:
    u = graphql(PROFILE_Q, {"login": login})["user"]
    created = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    parts = []
    for y in range(created.year, now.year + 1):
        f = max(created, datetime(y, 1, 1, tzinfo=timezone.utc))
        t = min(now, datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        parts.append(YEAR_Q.format(y=y, f=f.isoformat(), t=t.isoformat()))
    years = graphql("query($login:String!){user(login:$login){" + " ".join(parts) + "}}",
                    {"login": login})["user"]
    days = {}
    for col in years.values():
        for w in col["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return {
        "since": created.date().isoformat(),
        "commits": sum(c["totalCommitContributions"] for c in years.values()),
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
        "repos": u["repositories"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        **streaks(days),
    }


def streaks(days: dict[str, int]) -> dict:
    """Sequência atual (hoje sem contribuição ainda não quebra) e a maior, com datas."""
    ordered = sorted(days)
    best, best_range, run, start = 0, (None, None), 0, None
    for d in ordered:
        if days[d] > 0:
            run, start = run + 1, start if run else d
            if run > best:
                best, best_range = run, (start, d)
        else:
            run = 0
    cur, end = 0, None
    tail = ordered[::-1]
    if tail and days[tail[0]] == 0:
        tail = tail[1:]
    for d in tail:
        if days[d] == 0:
            break
        cur, end = cur + 1, end or d
    cur_start = (date.fromisoformat(end) - timedelta(days=cur - 1)).isoformat() if cur else None
    return {"total": sum(days.values()), "current": cur, "current_range": (cur_start, end),
            "longest": best, "longest_range": best_range, "today": ordered[-1] if ordered else None}


SAMPLE = {"since": "2023-03-01", "commits": 412, "prs": 37, "issues": 12, "stars": 9, "repos": 11,
          "contributed": 6, "total": 731, "current": 4, "current_range": ("2026-10-20", "2026-10-23"),
          "longest": 21, "longest_range": ("2026-05-02", "2026-05-22"), "today": "2026-10-23"}


def br(iso: str | None, year: bool = True) -> str:
    if not iso:
        return "—"
    d = date.fromisoformat(iso)
    return d.strftime("%d/%m/%Y" if year else "%d/%m")


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


# --------------------------------------------------------------------------- cards
W, H = 600, 280


def stats_card(s: dict) -> str:
    d = frame(W, H, rx=16, ht_w=180, ht_h=120)
    d += tab(44, 22, "ESTATÍSTICAS")
    d.append(f'<path d="{BARLOW.path(f"na ativa desde {s["since"][:4]}", 18, W - 30, 46, "end")}" fill="{MUTED}"/>')
    cells = [("COMMITS", s["commits"]), ("PULL REQUESTS", s["prs"]), ("ISSUES", s["issues"]),
             ("ESTRELAS", s["stars"]), ("REPOSITÓRIOS", s["repos"]), ("REPOS DE TERCEIROS", s["contributed"])]
    colw = (W - 44 - 30) / 3
    for i, (label, value) in enumerate(cells):
        x = 44 + (i % 3) * colw
        y = 102 + (i // 3) * 96
        color = TRIO[i % 3]
        d += [f'<rect x="{num(x)}" y="{y - 15}" width="4" height="74" rx="2" fill="{color}"/>',
              f'<path d="{BARLOW_B.path(label, 15, x + 16, y, tracking=2)}" fill="{color}"/>',
              f'<path d="{BANGERS.path(fmt(value), 46, x + 16, y + 50, tracking=1)}" fill="{WHITE}"/>']
    title = (f"Estatísticas: {s['commits']} commits, {s['prs']} pull requests, {s['issues']} issues, "
             f"{s['stars']} estrelas, {s['repos']} repositórios, contribuiu em {s['contributed']} repositórios de terceiros")
    return svg(W, H, title, "".join(d))


def streak_card(s: dict) -> str:
    d = frame(W, H, rx=16, ht_w=180, ht_h=120)
    d += tab(44, 22, "SEQUÊNCIA")
    d.append(f'<path d="{BARLOW.path(f"atualizado em {br(s["today"], False)}", 18, W - 30, 46, "end")}" '
             f'fill="{MUTED}"/>')
    # mostrador da sequência atual (mesmo desenho do comunicador)
    cx, cy = 148, 158
    n = str(s["current"])
    size = BANGERS.fit(n, 62, 84)
    d += [
        f'<circle cx="{cx + 5}" cy="{cy + 7}" r="80" fill="{BLACK}" opacity=".5"/>',
        f'<circle cx="{cx}" cy="{cy}" r="80" fill="{YELLOW}" stroke="{BLACK}" stroke-width="6"/>',
        f'<circle cx="{cx}" cy="{cy}" r="64" fill="{BLACK}" stroke="{LINE}" stroke-width="3"/>',
        f'<path d="{BANGERS.path(n, size, cx, cy + 14, "middle", 1)}" fill="{YELLOW}"/>',
        f'<path d="{BARLOW_B.path("DIAS", 15, cx, cy + 40, "middle", 2.4)}" fill="{GREY}"/>',
        f'<path d="{BARLOW_B.path("SEQUÊNCIA ATUAL", 15, cx, 266, "middle", 2)}" fill="{YELLOW}"/>',
    ]
    if s["current"] == 0:
        d.append(emblem(cx + 58, cy - 58, 16, 3))
    x0 = 290
    blocks = [("MAIOR SEQUÊNCIA", RED, f'{s["longest"]} {"DIA" if s["longest"] == 1 else "DIAS"}',
               f'{br(s["longest_range"][0])} – {br(s["longest_range"][1])}'),
              ("CONTRIBUIÇÕES", GREEN, fmt(s["total"]), f'desde {br(s["since"])}')]
    for i, (label, color, value, sub) in enumerate(blocks):
        y = 92 + i * 100
        d += [f'<rect x="{x0}" y="{y - 15}" width="4" height="82" rx="2" fill="{color}"/>',
              f'<path d="{BARLOW_B.path(label, 15, x0 + 16, y, tracking=2)}" fill="{color}"/>',
              f'<path d="{BANGERS.path(value, 44, x0 + 16, y + 46, tracking=1)}" fill="{WHITE}"/>',
              f'<path d="{BARLOW.path(sub, 18, x0 + 16, y + 69)}" fill="{MUTED}"/>']
    title = (f"Sequência atual: {s['current']} dias. Maior sequência: {s['longest']} dias "
             f"({br(s['longest_range'][0])} a {br(s['longest_range'][1])}). {s['total']} contribuições")
    return svg(W, H, title, "".join(d))


def visits_card(n: int) -> str:
    w, h = 600, 150
    d = frame(w, h)
    d.append(f'<path d="{BARLOW_B.path("VISITAS NA TORRE", 18, 46, 46, tracking=2.6)}" fill="{YELLOW}"/>')
    digits = str(max(n, 0)).rjust(6, "0")
    lead = len(digits) - len(str(max(n, 0)))
    bw, gap, x = 54, 8, 46
    for i, ch in enumerate(digits):
        color = MUTED if i < lead else YELLOW
        d += [
            f'<rect x="{x}" y="64" width="{bw}" height="66" rx="8" fill="{BLACK}" stroke="{LINE}" stroke-width="2"/>',
            f'<line x1="{x + 3}" y1="97" x2="{x + bw - 3}" y2="97" stroke="#121218" stroke-width="2"/>',
            f'<path d="{BANGERS.path(ch, 48, x + bw / 2, 97 + BANGERS.cap_height(48) / 2, "middle")}" fill="{color}"/>',
        ]
        x += bw + gap
    d.append(f'<rect x="46" y="134" width="{x - gap - 46}" height="4" fill="{RED}"/>')
    d.append(emblem(w - 82, 88, 40, 6))
    return svg(w, h, f"Visitas na Torre: {n}", "".join(d))


# --------------------------------------------------------------------------- visitas
def previous_visits() -> dict:
    try:
        subprocess.run(["git", "fetch", "--depth=1", "origin", "output"], check=True, capture_output=True)
        out = subprocess.run(["git", "show", "FETCH_HEAD:visits.json"], check=True, capture_output=True).stdout
        return json.loads(out)
    except Exception:
        return {"bot_hits": 0}


def read_visits() -> dict:
    """Total do komarev menos as leituras do próprio workflow (cada uma soma +1)."""
    state = previous_visits()
    body = urllib.request.urlopen(urllib.request.Request(KOMAREV, headers=UA), timeout=30).read().decode()
    raw = int(re.sub(r"\D", "", re.findall(r"<text[^>]*>([^<]*)</text>", body)[-1]))
    bot = int(state.get("bot_hits", 0)) + 1
    return {"raw": raw, "bot_hits": bot, "shown": max(raw - bot, 0)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--visits", type=int, help="usa este número em vez de ler o komarev")
    ap.add_argument("--sample", action="store_true", help="dados de exemplo, sem chamar a API")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    v = {"raw": a.visits, "bot_hits": 0, "shown": a.visits} if a.visits is not None else read_visits()
    s = SAMPLE if a.sample else fetch_stats(USER)
    files = {"visits.svg": visits_card(v["shown"]), "stats.svg": stats_card(s), "streak.svg": streak_card(s),
             "visits.json": json.dumps(v), "stats.json": json.dumps(s)}
    for name, content in files.items():
        (a.out / name).write_text(content, encoding="utf-8")
    print(json.dumps({"visits": v, "stats": {k: s[k] for k in ("commits", "prs", "issues", "stars", "repos",
                                                               "contributed", "total", "current", "longest")}}))


if __name__ == "__main__":
    main()
