"""Render story HTML files to 1080x1920 PNGs.

Usage: python3 render.py page.html [page2.html ...] [--guides]
--guides overlays Instagram safe zones and a sample question-sticker box (preview only).
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

GUIDES = """
<div style="position:absolute;inset:0;pointer-events:none;z-index:999">
  <div style="position:absolute;left:0;right:0;top:0;height:250px;background:rgba(0,120,255,.18);border-bottom:2px dashed #08f"></div>
  <div style="position:absolute;left:0;right:0;bottom:0;height:260px;background:rgba(0,120,255,.18);border-top:2px dashed #08f"></div>
  <div style="position:absolute;left:190px;width:700px;top:%dpx;height:250px;border-radius:34px;background:rgba(255,255,255,.92);box-shadow:0 10px 30px rgba(0,0,0,.25);font:600 34px Inter;color:#222;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px">
    <div>What should we bring up?</div>
    <div style="width:600px;height:64px;border-radius:16px;background:#eee;color:#999;font:500 28px Inter;display:flex;align-items:center;justify-content:center">Type something...</div>
  </div>
</div>
"""

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    guides = "--guides" in sys.argv or "--sticker" in sys.argv
    zones = "--guides" in sys.argv
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        for a in args:
            src = Path(a).resolve()
            page.goto(src.as_uri())
            page.wait_for_timeout(300)
            if guides:
                top = page.evaluate("() => +(document.body.dataset.sticker || 1340)")
                html = GUIDES % top
                if not zones:
                    html = "\n".join(l for l in html.splitlines() if "dashed #08f" not in l)
                page.evaluate("(h) => document.body.insertAdjacentHTML('beforeend', h)", html)
            suffix = "-guides" if zones else ("-with-sticker" if guides else "")
            out = src.with_name(src.stem + suffix + ".png")
            page.screenshot(path=str(out), full_page=False)
            print("wrote", out)
        browser.close()

if __name__ == "__main__":
    main()
