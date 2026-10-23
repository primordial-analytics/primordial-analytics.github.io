"""Download the raw public files into data/raw/ and record where and when."""
import datetime
import hashlib
import io
import zipfile
from pathlib import Path

import requests

RAW = Path(__file__).parent / "data" / "raw"

# name -> (url, is_zip). Zips are unpacked into data/raw/<name>/.
SOURCES = {
    "oep2026": ("https://www.cms.gov/files/zip/2026-oep-county-level-public-use-file.zip", True),
    "oep2025": ("https://www.cms.gov/files/zip/2025-oep-county-level-public-use-file.zip", True),
    "sahie": ("https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-2024-csv.zip", True),
    "effectuated.csv": (
        "https://data.cms.gov/sites/default/files/2026-06/f4dc299e-e04d-49af-8224-35b47f309735/"
        "Health%20Insurance%20Exchanges%20Monthly%20Effectuated%20Enrollment%20Data_asof_20260505.csv",
        False,
    ),
    "medicaid_pi.csv": ("https://download.medicaid.gov/data/pi-dataset-september-2026-release.csv", False),
}


def digest(target):
    """sha256 of a file, or of a folder's files in sorted order (zips are unpacked, so their own hash is not kept)."""
    files = [target] if target.is_file() else sorted(f for f in target.rglob("*") if f.is_file())
    h = hashlib.sha256()
    for f in files:
        h.update(f.read_bytes())
    return h.hexdigest()[:12], sum(f.stat().st_size for f in files)


def fetch_all(raw=RAW):
    """Download what is missing. SOURCES.txt keeps the original download date and always lists url, bytes and sha256."""
    raw.mkdir(parents=True, exist_ok=True)
    log_file = raw / "SOURCES.txt"
    first = log_file.read_text().splitlines()[0] if log_file.exists() else f"Downloaded {datetime.date.today().isoformat()}"
    log = [first]
    for name, (url, is_zip) in SOURCES.items():
        target = raw / name
        if not target.exists():
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=300)
            r.raise_for_status()
            if is_zip:
                zipfile.ZipFile(io.BytesIO(r.content)).extractall(target)
            else:
                target.write_bytes(r.content)
        sha, size = digest(target)
        log.append(f"{name}\t{url}\tbytes={size}\tsha256={sha}")
    log_file.write_text("\n".join(log) + "\n")


if __name__ == "__main__":
    fetch_all()
