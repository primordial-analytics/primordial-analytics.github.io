"""Download the raw public files into data/raw/ and record where and when."""
import datetime
import hashlib
import io
import zipfile
from pathlib import Path

import requests

RAW = Path(__file__).parent / "data" / "raw"
ACS = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData"

# name -> (url, is_zip). Zips are unpacked into data/raw/<name>/.
SOURCES = {
    "H80-2025.xlsx": ("https://data.hrsa.gov/DataDownload/StaticDocuments/H80-2025.xlsx", False),
    "H80-2024.xlsx": ("https://data.hrsa.gov/DataDownload/StaticDocuments/H80-2024.xlsx", False),
    "sites.csv": ("https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv", False),
    "acs_c17002.dat": (f"{ACS}/acsdt5y2024-c17002.dat", False),
    "acs_c27016.dat": (f"{ACS}/acsdt5y2024-c27016.dat", False),
    "acs_b14001.dat": (f"{ACS}/acsdt5y2024-b14001.dat", False),
    "gazetteer": ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip", True),
    "zcta_county.txt": ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt", False),
    "nap_bulletin.html": ("https://content.govdelivery.com/accounts/USHHSHRSA/bulletins/426df8a", False),
    "fr_2026-11094.txt": ("https://www.federalregister.gov/documents/full_text/text/2026/06/03/2026-11094.txt", False),
    "uns.xlsx": ("https://data.hrsa.gov/Content/Documents/topics/Full_Unmet_Need_Score_File.xlsx", False),
}


def digest(target):
    """sha256 (first 12 hex) of a file, or of a folder's files in sorted order, and the byte count."""
    files = [target] if target.is_file() else sorted(f for f in target.rglob("*") if f.is_file())
    h = hashlib.sha256()
    for f in files:
        h.update(f.read_bytes())
    return h.hexdigest()[:12], sum(f.stat().st_size for f in files)


def fetch_all(raw=RAW):
    """Download what is missing. SOURCES.txt keeps the original download date and lists url, bytes and sha256."""
    raw.mkdir(parents=True, exist_ok=True)
    log_file = raw / "SOURCES.txt"
    first = log_file.read_text().splitlines()[0] if log_file.exists() else f"Downloaded {datetime.date.today().isoformat()}"
    log = [first]
    for name, (url, is_zip) in SOURCES.items():
        target = raw / name
        if not target.exists():
            with requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=600, stream=True) as r:
                r.raise_for_status()
                body = b"".join(r.iter_content(1 << 20))
            if is_zip:
                zipfile.ZipFile(io.BytesIO(body)).extractall(target)
            else:
                target.write_bytes(body)
        sha, size = digest(target)
        log.append(f"{name}\t{url}\tbytes={size}\tsha256={sha}")
    log_file.write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    fetch_all()
