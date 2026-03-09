"""
data_collection/pdf_downloader.py
Download EV manuals and technical documents from the web.
"""
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ── Free EV manual sources ────────────────────────────────────────────────────
FREE_EV_MANUALS: Dict[str, dict] = {
    "nrel_ev_battery_health": {
        "url":  "https://www.nrel.gov/docs/fy19osti/73714.pdf",
        "dest": "research",
        "brand": "nrel",
        "desc": "NREL EV Battery Health Study 2019",
    },
    "doe_ev_battery_basics": {
        "url":  "https://afdc.energy.gov/files/u/publication/ev_batteries.pdf",
        "dest": "research",
        "brand": "doe",
        "desc": "US DOE — Electric Vehicle Battery Basics",
    },
    "iea_global_ev_outlook_2023": {
        "url":  ("https://iea.blob.core.windows.net/assets/"
                 "dacf14d2-eabc-498a-8263-9f97fd5dc327/GlobalEVOutlook2023.pdf"),
        "dest": "research",
        "brand": "iea",
        "desc": "IEA Global EV Outlook 2023",
    },
}


class PDFDownloader:
    """Download PDFs from URLs into the knowledge base folder."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; EV-AI-Research-Bot/1.0)",
        "Accept":     "application/pdf,*/*",
    }

    def __init__(self, base_path: str, delay: float = 1.5):
        self.base   = Path(base_path)
        self.delay  = delay
        self.log: List[dict] = []

    def download(
        self,
        url: str,
        dest_dir: str,
        filename: Optional[str] = None,
        skip_existing: bool = True,
    ) -> Optional[str]:
        dest_path = self.base / dest_dir
        dest_path.mkdir(parents=True, exist_ok=True)

        if not filename:
            filename = urlparse(url).path.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        out_file = dest_path / filename
        if skip_existing and out_file.exists():
            logger.info(f"Skipped (exists): {filename}")
            return str(out_file)

        try:
            resp = requests.get(url, headers=self.HEADERS,
                                timeout=60, stream=True)
            resp.raise_for_status()

            if "pdf" not in resp.headers.get("Content-Type", ""):
                logger.warning(f"URL may not be a PDF: {url}")

            total = 0
            with open(out_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total += len(chunk)

            size_kb = total // 1024
            logger.info(f"Downloaded: {filename} ({size_kb} KB)")
            self.log.append({"file": str(out_file), "url": url,
                             "size_kb": size_kb, "status": "ok"})
            time.sleep(self.delay)
            return str(out_file)

        except Exception as e:
            logger.error(f"Failed {url}: {e}")
            self.log.append({"url": url, "error": str(e), "status": "failed"})
            return None

    def download_free_manuals(self, manuals: dict = None) -> List[str]:
        """Download all free EV manuals defined in FREE_EV_MANUALS."""
        targets   = manuals or FREE_EV_MANUALS
        downloaded = []
        for key, info in targets.items():
            fname  = f"{key}.pdf"
            result = self.download(info["url"], f"ev_knowledge_base/{info['dest']}", fname)
            if result:
                downloaded.append(result)
        return downloaded

    def find_pdf_links(self, page_url: str) -> List[dict]:
        """Scrape a web page and return all PDF links found."""
        from urllib.parse import urljoin
        try:
            resp = requests.get(page_url, headers=self.HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if ".pdf" in href.lower():
                    links.append({
                        "url":  urljoin(page_url, href),
                        "text": text,
                    })
            return links
        except Exception as e:
            logger.error(f"Scrape failed {page_url}: {e}")
            return []

    def save_log(self, path: str):
        with open(path, "w") as f:
            json.dump(self.log, f, indent=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s — %(message)s")
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ev_kb"
    dl   = PDFDownloader(base)
    files = dl.download_free_manuals()
    print(f"\nDownloaded {len(files)} files:")
    for f in files:
        print(f"  {f}")
