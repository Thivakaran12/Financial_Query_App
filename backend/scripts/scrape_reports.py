#!/usr/bin/env python3
"""
Scrape the CSE website for interim PDF links and download the last N years
of quarterly reports for each symbol into data/raw/<company-slug>/.
"""
import logging
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ─── Configuration ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR      = PROJECT_ROOT / "data" / "raw"
LOG_DIR      = PROJECT_ROOT / "logs"

YEARS_BACK = 3
BASE_URL   = "https://www.cse.lk/pages/company-profile/company-profile.component.html"
SYMBOLS    = {
    "DIPD.N0000": "dipped-products",
    "REXP.N0000": "richard-pieris",
}

# ─── Logging Setup ────────────────────────────────────────────────────────────
def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "scrape_reports.log", encoding="utf-8"),
    ]
    logging.basicConfig(
        level    = logging.INFO,
        format   = "%(asctime)s %(levelname)-8s %(message)s",
        handlers = handlers,
    )

logger = logging.getLogger(__name__)

# ─── Helpers ─────────────────────────────────────────────────────────────────
def ensure_dirs() -> None:
    for slug in SYMBOLS.values():
        (RAW_DIR / slug).mkdir(parents=True, exist_ok=True)

def fetch_pdf_links(symbol: str) -> List[str]:
    """
    Use Selenium to render the page, capture its HTML, then
    parse with BeautifulSoup to avoid stale-element errors.
    """
    options = Options()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    try:
        driver.get(f"{BASE_URL}?symbol={symbol}")
        # wait until at least one PDF link appears in the DOM
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href$='.pdf']"))
        )
        html = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.lower().endswith(".pdf"):
            continue
        text = (a.get_text() or "").lower()
        if "interim" in text or "quarter" in text:
            url = href if href.startswith("http") else f"https://www.cse.lk{href}"
            links.append(url)
    return sorted(set(links))

def parse_date_from_url(url: str) -> Optional[datetime]:
    """
    Extract a date from the PDF filename (either dd-mm-yyyy or yyyy-mm-dd).
    """
    m = re.search(r"(\d{1,2})[^\d](\d{1,2})[^\d](\d{4})", url)
    if m:
        d, mth, y = m.groups()
        try:
            return datetime(int(y), int(mth), int(d))
        except ValueError:
            pass
    m = re.search(r"(\d{4})[^\d](\d{1,2})[^\d](\d{1,2})", url)
    if m:
        y, mth, d = m.groups()
        try:
            return datetime(int(y), int(mth), int(d))
        except ValueError:
            pass
    return None

def download_pdf(url: str, dest: Path) -> None:
    logger.info("Downloading %s → %s", url, dest.name)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)

# ─── Main Orchestration ───────────────────────────────────────────────────────
def main() -> None:
    setup_logging()
    load_dotenv()
    logger.info("Starting CSE interim PDF scraper")

    ensure_dirs()
    cutoff = datetime.today() - timedelta(days=365 * YEARS_BACK)

    for symbol, slug in SYMBOLS.items():
        logger.info("Processing %s → %s", symbol, slug)
        try:
            links = fetch_pdf_links(symbol)
        except Exception as e:
            logger.error("Failed to fetch links for %s: %s", symbol, e)
            continue

        if not links:
            logger.info("Found 0 candidate PDFs for %s", symbol)

        for url in links:
            dt = parse_date_from_url(url)
            if not dt or dt < cutoff:
                logger.debug("Skipping %s (date %s)", url, dt)
                continue

            fname = Path(url).name
            dest  = RAW_DIR / slug / fname
            if dest.exists():
                logger.debug("Already have %s, skipping", fname)
                continue

            try:
                download_pdf(url, dest)
            except Exception as e:
                logger.warning("Error downloading %s: %s", url, e)

    logger.info("Scraping complete")

if __name__ == "__main__":
    main()
