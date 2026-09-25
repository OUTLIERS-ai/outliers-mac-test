"""Photograph 1 panel of a running Jeeves: open the page, click the named tab, save the panel. Headless.

    python ws04e_shot.py <url> <tab text> <out.png>
"""
import sys
from playwright.sync_api import sync_playwright

url, tab, out = sys.argv[1], sys.argv[2], sys.argv[3]
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    try:
        page = b.new_page(viewport={"width": 1400, "height": 860}, device_scale_factor=2)
        page.goto(url, wait_until="load")
        page.wait_for_timeout(3000)
        page.get_by_text(tab, exact=True).first.click()
        page.wait_for_timeout(2500)
        page.screenshot(path=out)
        print("saved", out)
    finally:
        b.close()
