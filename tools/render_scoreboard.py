"""Render the Monday scoreboard post.

Usage: python3 render_scoreboard.py score.json out_dir

score.json = {
  "range": "October 5 – 11, 2026",
  "results": [
    {"sport": "Soccer", "date": "Sat, Oct 10", "prefix": "vs.", "opponent": "No. 25 Kenyon",
     "site": "Home" | "Away" | "Neutral", "outcome": "W" | "L" | "T", "score": "0–3"},
    {"sport": "Golf", "date": "Oct 5–6", "opponent": "Wabash College Invitational",
     "site": "Away", "place": "12th", "of": "of 16 teams"}          # meets: use place/of instead of outcome/score
  ],
  "records": [{"sport": "Football", "record": "4–1", "detail": "3–1 NCAC · bye week"}],
  "note": optional footnote line
}

Tries the normal layout, then a compact one, then splits results across
several 1080x1350 pages (season records go on the last page). Prints the PNG paths.
"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = pathlib.Path(__file__).parent
TEMPLATE = (HERE / "scoreboard_template.html").resolve().as_uri()
LIMIT = 1350 - 120  # keep clear of the footer row


def bottom(page, payload):
    page.add_init_script(f"window.__SCORE__ = {json.dumps(payload)};")
    page.goto(TEMPLATE)
    return page.evaluate("""() => Math.max(...['rows','recordsWrap','note']
        .map(id => document.getElementById(id))
        .filter(e => e && e.offsetParent !== null)
        .map(e => e.getBoundingClientRect().bottom))""")


def fits(browser, payload):
    ctx = browser.new_context(viewport={"width": 1080, "height": 1350})
    b = bottom(ctx.new_page(), payload)
    ctx.close()
    return b <= LIMIT


def plan(browser, data):
    for compact in (False, True):
        p = dict(data, compact=compact)
        if fits(browser, p):
            return [p]
    # split results across pages, compact layout, records only on the last page
    pages, cur = [], []
    for r in data["results"]:
        trial = dict(data, compact=True, results=cur + [r], records=[], note=None)
        if cur and not fits(browser, trial):
            pages.append(cur); cur = [r]
        else:
            cur = cur + [r]
    last = dict(data, compact=True, results=cur)
    if cur and not fits(browser, last):
        pages.append(cur); cur = []
    out = [dict(data, compact=True, results=p, records=[], note=None) for p in pages]
    out.append(dict(data, compact=True, results=cur))
    n = len(out)
    for i, p in enumerate(out, 1):
        p["pageLabel"] = f"{i}/{n}"
        if i > 1:
            p["title"] = "The Scoreboard\n(cont.)"
        if not p["results"]:
            p["resultsLabel"] = ""
    return out


def main(src, out):
    data = json.loads(pathlib.Path(src).read_text())
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        files = []
        for i, payload in enumerate(plan(browser, data), 1):
            ctx = browser.new_context(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            pg = ctx.new_page()
            pg.add_init_script(f"window.__SCORE__ = {json.dumps(payload)};")
            pg.goto(TEMPLATE)
            f = out / f"scoreboard-{i}.png"
            pg.screenshot(path=str(f), full_page=False)
            # dark board has gradients and glow, so keep full colour (no palette quantize)
            Image.open(f).convert("RGB").save(f, optimize=True)
            files.append(str(f)); ctx.close()
        browser.close()
    print("\n".join(files))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
