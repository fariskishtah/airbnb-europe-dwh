#!/usr/bin/env python
"""Real-browser verification of the running Streamlit dashboard (Playwright/Chromium). Saves genuine screenshots."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8599"
OUT = ROOT / "artifacts" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)
PAGES = [("Executive Overview", "01_executive_overview"), ("City Intelligence", "02_city_intelligence"),
         ("Pricing Analytics", "03_pricing_analytics"), ("Property & Room Insights", "04_property_room"),
         ("Ratings & Location", "05_ratings_location"), ("Geospatial View", "06_geospatial"),
         ("Data Quality & Pipeline", "07_data_quality_pipeline"), ("SQL Analytics Explorer", "08_sql_explorer")]
report = {"url": URL, "pages": [], "console_errors": []}


def settle(page, extra=2500):
    page.wait_for_selector('[data-testid="stApp"]', timeout=30000)
    page.wait_for_timeout(extra)
    try:
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=30000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(1500)


with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for label, ctx_args in [("desktop", dict(viewport={"width": 1440, "height": 900})),
                            ("mobile", dict(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2))]:
        ctx = browser.new_context(accept_downloads=True, **ctx_args)
        page = ctx.new_page()
        page.on("console", lambda m, l=label: report["console_errors"].append(f"[{l}] {m.text[:200]}") if m.type == "error" else None)
        page.goto(URL)
        settle(page, 4000)
        for title, slug in PAGES:
            if label == "mobile":
                if title != "Executive Overview" and title != "Data Quality & Pipeline":
                    continue
                page.get_by_test_id("stExpandSidebarButton").click() if page.get_by_test_id("stExpandSidebarButton").count() else None
            link = page.get_by_role("link", name=title)
            if link.count() == 0:
                page.get_by_text(title, exact=True).first.click()
            else:
                link.first.click()
            if label == "mobile":
                page.mouse.click(380, 400)
            settle(page, 5000 if "Geospatial" in title else 2500)
            exc = page.locator('[data-testid="stException"]').count()
            h1 = page.locator("h1").first.inner_text() if page.locator("h1").count() else ""
            charts = page.locator(".js-plotly-plot").count()
            tables = page.locator('[data-testid="stDataFrame"]').count()
            name = f"{slug}.png" if label == "desktop" else f"mobile_{slug}.png"
            page.screenshot(path=str(OUT / name), full_page=False)
            if label == "desktop":
                page.screenshot(path=str(OUT / f"full_{slug}.png"), full_page=True)
            report["pages"].append({"viewport": label, "page": title, "heading": h1, "exceptions": exc, "plotly_charts": charts, "dataframes": tables, "screenshot": name})
            print(label, title, "| exceptions:", exc, "| charts:", charts, "| tables:", tables, "| h1:", h1)
        ctx.close()
    browser.close()
(ROOT / "artifacts/reports/browser_verification.json").write_text(json.dumps(report, indent=2))
print("console errors:", len(report["console_errors"]))
for e in report["console_errors"][:10]:
    print("  ", e)
