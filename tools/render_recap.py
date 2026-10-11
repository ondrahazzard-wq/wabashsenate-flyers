"""Render the Senate meeting recap carousel.

Usage: python3 render_recap.py recap.json out_dir
recap.json = {
  "date": "Monday, Oct 12",
  "subtitle": "Key takeaways from this week's Student Senate meeting",
  "takeaways": [{"label": "Funding", "title": "...", "body": "..."}],   # 3-6 items
  "closing": {"headline": "Your voice,\nyour Senate.", "body": "..."}   # optional
}
Writes slide-01.png ... and prints the paths. Exits non-zero if any slide's text overflows.
"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = pathlib.Path(__file__).parent
TEMPLATE = (HERE / "recap_template.html").resolve().as_uri()
SAFE_BOTTOM = 1350 - 120

DEFAULT_CLOSING = {
    "headline": "Your voice,\nyour Senate.",
    "body": "Have a question or an idea? Reach out to your class representatives or send us a DM.",
}


def main(src, out):
    r = json.loads(pathlib.Path(src).read_text())
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    pts = r["takeaways"]
    total = len(pts) + 2
    slides = [dict(kind="cover", date=r["date"], subtitle=r.get("subtitle", "Key takeaways from this week's Student Senate meeting"))]
    for i, p in enumerate(pts, 1):
        slides.append(dict(kind="point", num=f"{i:02d}", label=p["label"], title=p["title"], body=p["body"], date=r["date"]))
    slides.append(dict(kind="close", date=r["date"], **(r.get("closing") or DEFAULT_CLOSING)))

    files, problems = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for n, s in enumerate(slides, 1):
            s["page"] = f"{n}/{total}"
            ctx = browser.new_context(viewport={"width": 1080, "height": 1350})
            pg = ctx.new_page()
            pg.add_init_script(f"window.__SLIDE__ = {json.dumps(s)};")
            pg.goto(TEMPLATE)
            bottom = pg.evaluate("""() => { const el = document.querySelector('.content, .big, .msg');
                                     return el ? el.getBoundingClientRect().bottom : 0; }""")
            if bottom > SAFE_BOTTOM:
                problems.append(f"slide {n} overflows by {int(bottom - SAFE_BOTTOM)}px — shorten its text")
            f = out / f"slide-{n:02d}.png"
            pg.screenshot(path=str(f))
            Image.open(f).convert("RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT,
                                                  dither=Image.Dither.NONE).save(f, optimize=True)
            files.append(str(f)); ctx.close()
        browser.close()
    print("\n".join(files))
    if problems:
        print("\n".join(problems), file=sys.stderr); sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
