"""Render the weekly Student Senate flyer.

Usage: python3 render.py week.json out_dir
week.json = {"dates": "...", "notice": optional, "days": [{"day","date","events":[{"time","title","where","tag"}]}]}
Days are packed onto as few 1080x1350 pages as fit; a page never overflows the footer.
"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
TEMPLATE = (HERE / "template.html").resolve().as_uri()
FOOTER_TOP = 1350 - 110  # keep content clear of the footer row


def fits(page, payload):
    page.add_init_script(f"window.__FLYER__ = {json.dumps(payload)};")
    page.goto(TEMPLATE)
    bottom = page.evaluate("document.getElementById('days').getBoundingClientRect().bottom")
    return bottom <= FOOTER_TOP


def main(src, out):
    week = json.loads(pathlib.Path(src).read_text())
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    base = {k: v for k, v in week.items() if k != "days"}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pages, current = [], []
        for day in week["days"]:
            trial = current + [day]
            ctx = browser.new_context(viewport={"width": 1080, "height": 1350})
            pg = ctx.new_page()
            payload = dict(base, days=trial, notice=base.get("notice") if not pages else None)
            if current and not fits(pg, payload):
                pages.append(current); current = [day]
            else:
                current = trial
            ctx.close()
        if current: pages.append(current)

        files = []
        for i, days in enumerate(pages, 1):
            payload = dict(base, days=days,
                           notice=base.get("notice") if i == 1 else None,
                           pageLabel=f"{i}/{len(pages)}" if len(pages) > 1 else "")
            if i > 1:
                payload["title"] = "This Week\n(cont.)"
            ctx = browser.new_context(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            pg = ctx.new_page()
            pg.add_init_script(f"window.__FLYER__ = {json.dumps(payload)};")
            pg.goto(TEMPLATE)
            f = out / f"flyer-{i}.png"
            pg.screenshot(path=str(f), full_page=False)
            files.append(str(f)); ctx.close()
        browser.close()
    print("\n".join(files))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
