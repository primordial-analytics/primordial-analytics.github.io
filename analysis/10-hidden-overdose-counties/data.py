"""Download the public inputs and build the county analysis table for one 12-month window."""
import calendar
import json
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import shapely

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"

SOURCES = {
    "county_od.csv": "https://data.cdc.gov/api/views/gb4e-yj24/rows.csv?accessType=DOWNLOAD",
    "state_od.json": ("https://data.cdc.gov/resource/xkb8-kh2a.json?$where="
                      "indicator='Number of Drug Overdose Deaths' AND year>='2024'&$limit=50000"),
    "co-est2024-alldata.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/counties/totals/co-est2024-alldata.csv",
    # NCHS still uses the 8 old Connecticut counties; the 2024 Census file uses 9 planning regions.
    "co-est2020-alldata.csv": "https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/counties/totals/co-est2020-alldata.csv",
    "sahie-2024-csv.zip": "https://www2.census.gov/programs-surveys/sahie/datasets/time-series/estimates-acs/sahie-2024-csv.zip",
    "cb_2020_us_county_500k.zip": "https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_county_500k.zip",
}


def download(force=()):
    """Fetch every raw file once; record the URL, date and size in data/raw/SOURCES.json."""
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "SOURCES.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, url in SOURCES.items():
        path = RAW / name
        if path.exists() and name in manifest and name not in force:
            continue
        print("downloading", name)
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        path.write_bytes(r.content)
        manifest[name] = {"url": url, "downloaded": date.today().isoformat(), "bytes": len(r.content)}
    manifest_path.write_text(json.dumps(manifest, indent=1))
    return manifest


def _census_pop(year):
    """County population for July 1 `year` (2022-2024); old Connecticut counties scaled to the state's growth."""
    p = pd.read_csv(RAW / "co-est2024-alldata.csv", encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
    p["fips"] = p.STATE + p.COUNTY
    col = f"POPESTIMATE{year}"
    pop = p[(p.COUNTY != "000") & (p.STATE != "09")].set_index("fips")[col]
    ct = pd.read_csv(RAW / "co-est2020-alldata.csv", encoding="latin-1", dtype={"STATE": str, "COUNTY": str})
    ct = ct[(ct.STATE == "09") & (ct.COUNTY != "000")]
    state_ct = p[(p.STATE == "09") & (p.COUNTY == "000")].iloc[0]
    scale = state_ct[col] / state_ct["POPESTIMATE2020"]
    ct_pop = pd.Series((ct.POPESTIMATE2020 * scale).round().values, index=ct.STATE + ct.COUNTY)
    pop = pd.concat([pop, ct_pop])
    pop["02261"] = pop["02063"] + pop["02066"]  # NCHS still has Valdez-Cordova, split in 2019
    return pop


def covariates():
    """County covariates that exist for nearly every county: land area (for density) and SAHIE measures."""
    z = zipfile.ZipFile(RAW / "sahie-2024-csv.zip")
    s = pd.read_csv(z.open("sahie_2024.csv"), skiprows=85, skipinitialspace=True, dtype=str)
    s.columns = [c.strip() for c in s.columns]
    s = s.drop(columns=[c for c in s.columns if c.startswith("Unnamed")])
    for c in s.columns:
        s[c] = s[c].str.strip()
    s = s[(s.geocat == "50") & (s.agecat == "0") & (s.racecat == "0") & (s.sexcat == "0")].copy()
    s["fips"] = s.statefips.str.zfill(2) + s.countyfips.str.zfill(3)
    s["NIPR"] = pd.to_numeric(s.NIPR, errors="coerce")
    s["PCTUI"] = pd.to_numeric(s.PCTUI, errors="coerce")
    allp = s[s.iprcat == "0"].set_index("fips")
    low = s[s.iprcat == "3"].set_index("fips")  # at or below 138% of the poverty line
    out = pd.DataFrame({"pct_uninsured": allp.PCTUI, "pct_low_income": 100 * low.NIPR / allp.NIPR})
    land = _boundaries().set_index("GEOID").ALAND / 2.59e6
    out = out.reindex(out.index.union(land.index))
    out["land_sqmi"] = land
    out.loc["02261"] = [out.loc[["02063", "02066"], c].mean() if c != "land_sqmi"
                        else out.loc[["02063", "02066"], c].sum() for c in out.columns]
    return out


def _boundaries():
    """2020 cartographic county boundaries (still has the old Connecticut counties), Valdez-Cordova merged."""
    import geopandas as gpd
    g = gpd.read_file(f"zip://{RAW / 'cb_2020_us_county_500k.zip'}")[["GEOID", "ALAND", "geometry"]]
    g = g.to_crs(5070)
    vc = g[g.GEOID.isin(["02063", "02066"])]
    merged = gpd.GeoDataFrame({"GEOID": ["02261"], "ALAND": [vc.ALAND.sum()],
                               "geometry": [vc.geometry.union_all()]}, crs=g.crs)
    return pd.concat([g[~g.GEOID.isin(["02063", "02066"])], merged], ignore_index=True)


def graph(fips):
    """Queen-contiguity edges (i < j) between the counties in `fips`, plus centroid x, y in km."""
    g = _boundaries().set_index("GEOID").loc[list(fips)]
    geom = g.geometry.buffer(200)  # 200 m: closes slivers between simplified polygons
    tree = shapely.STRtree(geom.values)
    left, right = tree.query(geom.values, predicate="intersects")
    keep = left < right
    edges = np.column_stack([left[keep], right[keep]])
    c = g.geometry.centroid
    return edges, np.column_stack([c.x, c.y]) / 1000


def data_as_of():
    """The 'Data as of' date NCHS stamps on the county file."""
    return pd.read_csv(RAW / "county_od.csv", usecols=["Data as of"], nrows=1).iloc[0, 0]


def county_table(end="2026-03", pop_year=2024):
    """One row per NCHS county for the 12-month window ending `end` (a 'YYYY-MM' string).

    status: 'exact' (published count, including zeros), 'censored' (suppressed, 1 to 9 deaths),
    'missing' (suppressed for data quality: no information about the count).
    """
    y, m = map(int, end.split("-"))
    d = pd.read_csv(RAW / "county_od.csv", dtype={"FIPS": str})
    w = d[d.MonthEndingDate == f"{m:02d}/{calendar.monthrange(y, m)[1]}/{y}"].copy()
    w["fips"] = w.FIPS.str.zfill(5)
    # NCHS lists two Virginia pairs (Alleghany/Clifton Forge, Bedford/Bedford city) under one FIPS each.
    # The rows repeat the same merged county, so keep the county row and drop the old city row.
    w = w[~(w.fips.duplicated(keep=False) & w.COUNTYNAME.str.endswith("(city)"))]
    assert w.fips.is_unique
    foot = w.Footnote.fillna("")
    w["status"] = np.where(foot.str.contains("1-9"), "censored",
                           np.where(foot.str.contains("data quality"), "missing", "exact"))
    t = w.rename(columns={"ST_ABBREV": "state", "STATE_NAME": "state_name", "COUNTYNAME": "county",
                          "CODE2013": "urban_rural", "Provisional Drug Overdose Deaths": "y",
                          "Percentage Of Records Pending Investigation": "pct_pending"})
    t = t[["fips", "state", "state_name", "county", "urban_rural", "y", "status", "pct_pending"]].set_index("fips")
    t["pop"] = _census_pop(pop_year).reindex(t.index)
    t = t.join(covariates())
    assert t["pop"].notna().all(), t[t["pop"].isna()]
    return t


def state_totals(end="2026-03"):
    """Unsuppressed state totals for the 12 months ending `end`; New York = state + New York City."""
    s = pd.DataFrame(json.loads((RAW / "state_od.json").read_text()))
    s = s[(s.year == end[:4]) & (s.month == calendar.month_name[int(end[5:])]) & (s.period == "12 month-ending")]
    tot = s.set_index("state").data_value.astype(float)
    tot["NY"] = tot["NY"] + tot["YC"]
    return tot.drop(["YC", "US", "PR"], errors="ignore")
