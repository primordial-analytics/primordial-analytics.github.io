"""Download the raw data and record where it came from."""
import hashlib, json, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import requests

from common import EXPANSION, OUT, RAW

BASE = "https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year"
FILES = {
    "fr_2026-11094.txt": "https://www.federalregister.gov/documents/full_text/text/2026/06/03/2026-11094.txt",
    "H80-2025.xlsx": "https://data.hrsa.gov/DataDownload/StaticDocuments/H80-2025.xlsx",
    "hrsa_national_table9d_2025.html": "https://data.hrsa.gov/topics/healthcenters/uds/overview/national/table?tableName=9D&year=2025",
    "renewals.csv": "https://download.medicaid.gov/data/updated-renewal-outcomes-october-2024-releasefinal.csv",
}
for st in EXPANSION:
    FILES[f"pums/csv_p{st.lower()}.zip"] = f"{BASE}/csv_p{st.lower()}.zip"


def get(item):
    name, url = item
    path = RAW / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        r = requests.get(url, timeout=600, headers={"User-Agent": "Mozilla/5.0 (primordial-analytics-analysis)"})
        r.raise_for_status()
        path.write_bytes(r.content)
    if name.startswith("pums/"):
        out = RAW / "pums" / name.split("/")[1][4:-4]
        if not out.exists():
            with zipfile.ZipFile(path) as z:
                z.extractall(out)
    return name, url, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main():
    prior = {}
    if (OUT / "sources.json").exists():
        prior = {r["file"]: r for r in json.load(open(OUT / "sources.json"))["files"]}
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(get, FILES.items()))
    today = date.today().isoformat()
    files = [{"file": n, "url": u, "bytes": b, "sha256_16": h,
              "downloaded": prior.get(n, {}).get("downloaded", today)} for n, u, b, h in rows]
    json.dump({"files": files}, open(OUT / "sources.json", "w"), indent=1)
    print(f"{len(files)} files in data/raw")


if __name__ == "__main__":
    main()
