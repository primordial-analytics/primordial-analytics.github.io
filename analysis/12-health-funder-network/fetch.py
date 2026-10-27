"""Download the raw public files into data/raw/ and record where and when. Files are streamed to disk.

The IRS 990 e-file XML comes as zip batches per processing year; the batches are read in place (unpacked they would be
tens of gigabytes). The list of batches is read from the IRS download page, so a new batch is picked up on the next run.
"""
import datetime
import hashlib
import re
from pathlib import Path

import requests

RAW = Path(__file__).parent / "data" / "raw"
XML = "https://apps.irs.gov/pub/epostcard/990/xml"
PAGE = "https://www.irs.gov/charities-non-profits/form-990-series-downloads"
YEARS = range(2021, 2027)  # processing years; they hold tax years 2020 to 2025
UA = {"User-Agent": "Mozilla/5.0"}

FILES = {f"index_{y}.csv": f"{XML}/{y}/index_{y}.csv" for y in YEARS}
FILES |= {f"eo{i}.csv": f"https://www.irs.gov/pub/irs-soi/eo{i}.csv" for i in range(1, 5)}  # Business Master File
FILES["hrsa_sites.csv"] = "https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv"
# on the server but not linked from the download page (October 2026); without it tax year 2021 is a third short
FILES["2022_TEOS_XML_02A.zip"] = f"{XML}/2022/2022_TEOS_XML_02A.zip"


def batches():
    html = requests.get(PAGE, headers=UA, timeout=60).text
    urls = sorted(set(re.findall(rf"{re.escape(XML)}/(\d{{4}})/([\w.-]+\.zip)", html)))
    return {name: f"{XML}/{y}/{name}" for y, name in urls if int(y) in YEARS}


def download(url, dest):
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers=UA, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.rename(dest)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def fetch_all(raw=RAW):
    """Download what is missing. SOURCES.txt keeps the original download date and lists url, bytes and sha256 of each download."""
    raw.mkdir(parents=True, exist_ok=True)
    log_file = raw / "SOURCES.txt"
    first = log_file.read_text().splitlines()[0] if log_file.exists() else f"Downloaded {datetime.date.today().isoformat()}"
    log = [first]
    for name, url in (FILES | batches()).items():
        target = raw / name
        if not target.exists():
            print(f"  downloading {name}", flush=True)
            download(url, target)
        log.append(f"{name}\t{url}\tbytes={target.stat().st_size}\tsha256={digest(target)}")
    log_file.write_text("\n".join(log) + "\n")


def main():
    fetch_all()


if __name__ == "__main__":
    main()
