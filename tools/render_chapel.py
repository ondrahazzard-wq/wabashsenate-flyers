"""Render a Chapel Talk Instagram story (1080x1920 PNG).

Usage: python3 render_chapel.py chapel.json editorial|bigtime out.png

chapel.json fields (empty/missing optional fields are hidden):
  title      (required) talk title, e.g. "The BE's"
  subtitle   (optional) subtitle of the talk
  speaker    (required) e.g. "Emilio Robles '94"
  role       (optional) one line about the speaker, e.g. "Professor of Music"
  insight    (optional) 1-2 sentences on what the talk is about, from the email only
  date       (required) short, e.g. "Thu Oct 22"         (Editorial)
  day_long   (required) e.g. "Thursday, Oct 22"          (Big Time)
  time       (required) e.g. "11:15 AM"
  place      (optional) defaults to "Pioneer Chapel · All are welcome"
Exits with code 2 if the text could not be made to fit.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

DESIGNS = {"editorial": "chapel_editorial.html", "bigtime": "chapel_bigtime.html"}


def main():
    data_path, design, out = sys.argv[1], sys.argv[2], sys.argv[3]
    data = json.loads(Path(data_path).read_text())
    tpl = Path(__file__).resolve().with_name(DESIGNS[design])
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto(tpl.as_uri())
        page.evaluate("() => document.fonts.ready")
        fits = page.evaluate("(d) => window.fill(d)", data)
        page.wait_for_timeout(200)
        page.screenshot(path=out, full_page=False)
        browser.close()
    print("wrote", out)
    if not fits:
        print("WARNING: text overflows; shorten the insight/subtitle and re-render", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
