"""Download the raw public files into data/raw/ and record where and when. Files are streamed to disk."""
import datetime
import hashlib
import zipfile
from pathlib import Path

import requests

RAW = Path(__file__).parent / "data" / "raw"
SF = "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF"

# name -> (url, is_zip). Zips are unpacked into data/raw/<name>/.
SOURCES = {
    "c27016.dat": (f"{SF}/data/5YRData/acsdt5y2024-c27016.dat", False),
    "b27020.dat": (f"{SF}/data/5YRData/acsdt5y2024-b27020.dat", False),
    "table_shells.txt": (f"{SF}/documentation/ACS20245YR_Table_Shells.txt", False),
    "pums": ("https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year/csv_pus.zip", True),
    "sahie": ("https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-2024-csv.zip", True),
    "places.csv": ("https://data.cdc.gov/resource/cwsq-ngmh.csv?$limit=200000&$where=measureid='ACCESS2' AND datavaluetypeid='CrdPrv'", False),
    "oep2026": ("https://www.cms.gov/files/zip/2026-oep-county-level-public-use-file.zip", True),
    "hrsa.csv": ("https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv", False),
    "imls": ("https://www.imls.gov/sites/default/files/2025-08/pls_fy2023_csv.zip", True),
    "gaz_tracts": ("https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_tracts_national.zip", True),
    "zcta_tract.txt": ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_tract20_natl.txt", False),
}


def download(url, dest):
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=600) as r:
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
    for name, (url, is_zip) in SOURCES.items():
        target = raw / name
        archive = raw / f"{name}.zip" if is_zip else target
        if not target.exists():
            print(f"  downloading {name}", flush=True)
            download(url, archive)
            if is_zip:
                with zipfile.ZipFile(archive) as z:
                    for member in z.namelist():  # untrusted archive: refuse paths that leave the folder
                        if Path(member).is_absolute() or ".." in Path(member).parts:
                            raise ValueError(f"unsafe path in {archive}: {member}")
                    z.extractall(target)
        log.append(f"{name}\t{url}\tbytes={archive.stat().st_size}\tsha256={digest(archive)}")
    log_file.write_text("\n".join(log) + "\n")


def main():
    fetch_all()


if __name__ == "__main__":
    main()
