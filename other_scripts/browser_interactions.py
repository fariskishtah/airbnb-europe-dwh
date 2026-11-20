#!/usr/bin/env python
"""Browser test: global filter changes KPIs; SQL explorer CSV download works."""
import json, re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8599"
res = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(); ctx = b.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True); p = ctx.new_page()
    p.goto(URL); p.wait_for_selector('[data-testid="stApp"]'); p.wait_for_timeout(5000)
    kpi = lambda: p.locator(".kpi .v").first.inner_text()
    res["observations_all"] = kpi()
    # restrict the city filter to Paris: clear all, then pick Paris
    p.get_by_role("combobox").first.click()           # city multiselect
    p.keyboard.press("Escape")
    p.mouse.click(224, 546)                            # "clear all" icon of the city multiselect
    p.wait_for_timeout(1500)
    p.get_by_role("combobox").first.click(); p.keyboard.type("Paris"); p.keyboard.press("Enter"); p.keyboard.press("Escape")
    p.wait_for_timeout(4000)
    res["observations_paris"] = kpi()
    p.screenshot(path=str(ROOT / "artifacts/screenshots/09_filtered_paris.png"))
    p.get_by_role("link", name="SQL Analytics Explorer").click(); p.wait_for_timeout(4000)
    with p.expect_download() as d:
        p.get_by_role("button", name=re.compile("Download aggregated")).click()
    path = ROOT / "artifacts/reports/browser_download_test.csv"; d.value.save_as(str(path))
    res["download_file"] = d.value.suggested_filename; res["download_lines"] = len(path.read_text().splitlines())
    p.screenshot(path=str(ROOT / "artifacts/screenshots/10_sql_explorer_download.png"))
    b.close()
res["filter_changed_kpi"] = res["observations_all"] != res["observations_paris"]
(ROOT / "artifacts/reports/browser_interactions.json").write_text(json.dumps(res, indent=2)); print(res)
