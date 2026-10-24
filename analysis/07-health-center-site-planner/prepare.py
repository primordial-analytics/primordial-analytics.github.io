"""Clean the raw files into ZCTA, center, site and center-by-ZCTA cell tables.

Conventions
- ZIP codes are read as text. HRSA ZIPs are mapped to ZCTAs with HRSA's own crosswalk (the UNS file); 'Other ZIP Codes'
  and 'Unknown Residence' rows stay in center totals but out of every ZIP-level table.
- '--' in the HRSA ZIP file is a censored cell: 1 to 15 patients. '-' is a blank. Zeros are real zeros.
- Low-income means under 200% of the federal poverty level (ACS C17002 estimates 002 to 007).
- ACS margins of error are 90%: standard error = margin / 1.645. Sums add squared margins (Census approximation).
"""
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw"
CACHE = RAW / "cache"
Z90 = 1.645
PAYERS = ["uninsured", "medicaid", "medicare", "private"]
ZIP_PAYER_COLS = ["None_UninsuredPatients", "Medicaid_CHIP_OtherPublicPatients", "MedicarePatients", "PrivatePatients"]
SITE_CUTOFF = {2025: "2025-12-31", 2024: "2024-12-31"}
STATE_FIPS = dict(zip(
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56 60 66 69 72 78".split(),
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY AS GU MP PR VI".split()))
# Fixed density cuts (people per square mile of land), applied to ZCTAs.
DENSITY_CUTS = (200.0, 2000.0)
CLASSES = ["rural", "suburban", "urban"]


def _cached(name, build):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    obj = build()
    path.write_bytes(pickle.dumps(obj))
    return obj


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def density_class(density):
    return np.where(density < DENSITY_CUTS[0], 0, np.where(density < DENSITY_CUTS[1], 1, 2))


# ------------------------------------------------------------------ census side
def _acs(path, prefix, est_idx):
    est = [f"{prefix}_E{i:03d}" for i in est_idx]
    moe = [f"{prefix}_M{i:03d}" for i in est_idx]
    d = pd.read_csv(path, sep="|", usecols=["GEO_ID", *est, *moe], dtype={"GEO_ID": str})
    d = d[d.GEO_ID.str.startswith("860Z200US")].copy()
    d.index = d.GEO_ID.str[-5:]
    return d.drop(columns="GEO_ID").astype(float)


def load_zcta():
    """One row per ZCTA with an ACS row and a centroid."""
    inc = _acs(RAW / "acs_c17002.dat", "C17002", range(1, 8))
    # Three income bands below 200% start at rows 2, 12, 22; in each, rows +2/+3 are under 19 (insured/uninsured), +5/+6 are 19 to 64, +8/+9 are 65 and over.
    ins = _acs(RAW / "acs_c27016.dat", "C27016", [h + k for h in (2, 12, 22) for k in (2, 3, 5, 6, 8, 9)])
    out = pd.DataFrame(index=inc.index)
    low = [f"C17002_E{i:03d}" for i in range(2, 8)]
    low_m = [f"C17002_M{i:03d}" for i in range(2, 8)]
    out["pop"] = inc.C17002_E001
    out["low"] = inc[low].sum(axis=1)
    out["low_se"] = np.sqrt((inc[low_m] ** 2).sum(axis=1)) / Z90
    un, un_m = ["C27016_E008", "C27016_E018", "C27016_E028"], ["C27016_M008", "C27016_M018", "C27016_M028"]
    out["unins_adult_low"] = ins[un].sum(axis=1).reindex(out.index)
    out["unins_se"] = (np.sqrt((ins[un_m] ** 2).sum(axis=1)) / Z90).reindex(out.index)
    ok = ["C27016_E007", "C27016_E017", "C27016_E027"]
    out["ins_adult_low"] = ins[ok].sum(axis=1).reindex(out.index)
    # all ages: the uninsured share a newly reached patient is given (children are far less often uninsured than adults)
    no_ins = [f"C27016_E{h + k:03d}" for h in (2, 12, 22) for k in (3, 6, 9)]
    with_ins = [f"C27016_E{h + k:03d}" for h in (2, 12, 22) for k in (2, 5, 8)]
    out["unins_all_low"] = ins[no_ins].sum(axis=1).reindex(out.index)
    out["ins_all_low"] = ins[with_ins].sum(axis=1).reindex(out.index)
    # college and graduate students (B14001 008 + 009) per resident aged 3+: the poverty count includes off-campus students
    sch = _acs(RAW / "acs_b14001.dat", "B14001", [1, 8, 9])
    out["college_pct"] = (100 * (sch.B14001_E008 + sch.B14001_E009) / sch.B14001_E001.where(sch.B14001_E001 > 0)).reindex(out.index).fillna(0)
    g = pd.read_csv(next((RAW / "gazetteer").glob("*.txt")), sep="\t", dtype={"GEOID": str})
    g.columns = g.columns.str.strip()
    g = g.set_index("GEOID")
    out = out.join(g[["ALAND_SQMI", "INTPTLAT", "INTPTLONG"]].rename(columns={"ALAND_SQMI": "land_sqmi", "INTPTLAT": "lat", "INTPTLONG": "lon"}), how="inner")
    out["density"] = out["pop"] / out.land_sqmi.clip(lower=0.01)
    out["dclass"] = density_class(out.density)

    rel = pd.read_csv(RAW / "zcta_county.txt", sep="|", dtype=str, encoding="utf-8-sig")
    rel = rel.dropna(subset=["GEOID_ZCTA5_20"]).assign(part=lambda d: _num(d.AREALAND_PART))
    top = rel.sort_values("part", ascending=False).drop_duplicates("GEOID_ZCTA5_20").set_index("GEOID_ZCTA5_20")
    out["county_fips"] = top.GEOID_COUNTY_20.reindex(out.index)
    out["county"] = top.NAMELSAD_COUNTY_20.reindex(out.index)
    out["state"] = out.county_fips.str[:2].map(STATE_FIPS)
    return out


def load_uns():
    """HRSA's own ZIP table: the ZIP-to-ZCTA crosswalk and its published penetration (a comparator only)."""
    u = pd.read_excel(RAW / "uns.xlsx", dtype=str)
    u = u.rename(columns={"Zip Code": "zip", "ZIP Code Tabulation Area (ZCTA) Map": "zcta", "Health Center Penetration": "pen_low",
                          "Health Center Penetration Total Population": "pen_total", "ZCTA UNS": "uns", "Population Size": "hrsa_pop"})
    for c in ["pen_low", "pen_total", "uns", "hrsa_pop"]:
        u[c] = _num(u[c])
    return u[["zip", "zcta", "pen_low", "pen_total", "uns", "hrsa_pop"]]


# ------------------------------------------------------------------ HRSA side
def load_uds(year):
    """Return (zip_rows, centers) for a UDS year. Table 4 supplies each center's totals."""
    path = RAW / f"H80-{year}.xlsx"
    sheets = pd.read_excel(path, sheet_name=["HealthCenterZipCodes", "Table4", "HealthCenterInfo"], dtype=str)
    z = sheets["HealthCenterZipCodes"].rename(columns={"GrantNumber": "grant", "ZipCode": "zip", "ZipCodeType": "kind"})
    t4 = sheets["Table4"].dropna(subset=["GrantNumber"]).set_index("GrantNumber")
    info = sheets["HealthCenterInfo"].set_index("GrantNumber")
    n = lambda c: _num(t4[c]).fillna(0)
    c = pd.DataFrame(index=t4.index)
    c["name"] = info.HealthCenterName.reindex(c.index)
    c["state"] = info.HealthCenterState.reindex(c.index)
    c["urban_flag"] = info.UrbanRuralFlag.reindex(c.index)
    chc = info.FundingCHC.reindex(c.index) == "TRUE"
    c["type"] = np.where(chc, "chc", "special")
    c["patients"] = _num(t4.T4_L6_Ca)
    c["inc_le100"], c["inc_101_150"], c["inc_151_200"], c["inc_gt200"] = (n(f"T4_L{i}_Ca") for i in (1, 2, 3, 4))
    known = c.inc_le100 + c.inc_101_150 + c.inc_151_200 + c.inc_gt200
    c["low_share"] = ((c.inc_le100 + c.inc_101_150 + c.inc_151_200) / known.where(known > 0)).astype(float)
    c["pay_uninsured"] = n("T4_L7_Ca") + n("T4_L7_Cb")
    c["pay_medicaid"] = n("T4_L8_Ca") + n("T4_L8_Cb") + n("T4_L10_Ca") + n("T4_L10_Cb")
    c["pay_medicare"] = n("T4_L9_Ca") + n("T4_L9_Cb")
    c["pay_private"] = n("T4_L11_Ca") + n("T4_L11_Cb")
    return z, c


def load_sites(year=2025):
    """Permanent, non-school service delivery sites with coordinates, added to scope on or before the UDS year end."""
    s = pd.read_csv(RAW / "sites.csv", dtype=str)
    out = pd.DataFrame({
        "grant": s["Health Center Number"], "site": s["Site Name"], "state": s["Site State Abbreviation"],
        "lat": _num(s["Geocoding Artifact Address Primary Y Coordinate"]), "lon": _num(s["Geocoding Artifact Address Primary X Coordinate"]),
        "added": pd.to_datetime(s["Site Added to Scope this Date"], errors="coerce"),
        "permanent": s["Health Center Location Type Description"] == "Permanent",
        "school": s["Health Center Service Delivery Site Location Setting Description"] == "School",
        "delivers": s["Health Center Type Description"].isin(["Service Delivery Site", "Administrative/Service Delivery Site"]),
        "lookalike": s["Health Center Number"].str.startswith("LAL"),
    })
    geo = out.lat.notna() & out.lon.notna()
    keep = out.permanent & ~out.school & out.delivers & geo
    loc = s["Health Center Location Type Description"]
    stats = {"rows": len(out), "geocoded": int(geo.sum()), "rows_seasonal": int((loc == "Seasonal").sum()), "rows_mobile_van": int((loc == "Mobile Van").sum()),
             "rows_school_setting": int(out.school.sum()), "permanent_nonschool_delivery": int(keep.sum()),
             "added_after_cutoff": int((keep & (out.added > SITE_CUTOFF[year])).sum()), "lookalike_sites": int((keep & out.lookalike).sum())}
    return out[keep & (out.added <= SITE_CUTOFF[year])].reset_index(drop=True), out[keep & (out.added > SITE_CUTOFF[year])].reset_index(drop=True), stats


def build_cells(z, centers, zcta, uns):
    """Parse every HRSA row. Rows of kind ZipCode that map to a ZCTA with ACS data get a zcta; the rest keep zcta NaN but stay
    in the table because their censored cells belong to the center's hidden sum. Returns (rows, summary)."""
    zi = z.copy()
    zi["hid_total"] = zi.TotalNumberofPatients == "--"
    zi["total"] = _num(zi.TotalNumberofPatients)
    for p, col in zip(PAYERS, ZIP_PAYER_COLS):
        zi["hid_" + p] = zi[col] == "--"
        zi[p] = _num(zi[col])
    xw = uns.drop_duplicates("zip").set_index("zip").zcta
    is_zip = zi.kind == "ZipCode"
    mapped = np.where(zi.zip.isin(zcta.index), zi.zip, zi.zip.map(xw))
    zi["zcta_any"] = np.where(is_zip, mapped, None)
    zi["via_crosswalk"] = is_zip & ~zi.zip.isin(zcta.index) & zi.zcta_any.notna()
    zi["zcta"] = zi.zcta_any.where(zi.zcta_any.isin(zcta.index))
    vis = zi.total.fillna(0)
    zr = zi[is_zip]
    summary = {
        "uds_rows": len(zi), "zip_rows": len(zr), "other_zip_rows": int((zi.kind == "Other ZIP Codes").sum()), "unknown_rows": int((zi.kind == "Unknown Residence").sum()),
        "zip_rows_hidden_total": int(zr.hid_total.sum()),
        "distinct_zips": int(zr.zip.nunique()), "zips_not_zcta_mapped_by_crosswalk": int(zi[zi.via_crosswalk].zip.nunique()),
        "zip_rows_unmapped": int(zr.zcta_any.isna().sum()), "visible_patients_unmapped": int(vis[is_zip & zi.zcta_any.isna()].sum()),
        "zip_rows_mapped_without_acs": int((zr.zcta_any.notna() & zr.zcta.isna()).sum()),
        "visible_patients_mapped_without_acs": int(vis[is_zip & zi.zcta_any.notna() & zi.zcta.isna()].sum()),
        "visible_patients_via_crosswalk": int(vis[zi.via_crosswalk & zi.zcta.notna()].sum()),
        "visible_patients_other_zip": int(vis[zi.kind == "Other ZIP Codes"].sum()),
        "visible_patients_unknown": int(vis[zi.kind == "Unknown Residence"].sum()),
        "visible_patients_zip_rows": int(vis[is_zip].sum()), "visible_patients_in_model_zctas": int(vis[zi.zcta.notna()].sum()),
    }
    return zi, summary


def center_sites(centers, sites):
    """Per center: permanent site count and centroid. Look-alike centers (no UDS patient data) are added as competitors."""
    g = sites.groupby("grant")
    n = g.size().rename("n_sites")
    cen = centers.join(n)
    # the UDS file cuts long names at 33 characters ("MONONGAHELA VALLEY ASSOCIATION OF"); the site list has the full name
    full = pd.read_csv(RAW / "sites.csv", dtype=str, usecols=["Health Center Number", "Health Center Name"]).dropna().drop_duplicates("Health Center Number").set_index("Health Center Number")["Health Center Name"]
    cen["name"] = [full[g] if g in full.index and isinstance(nm, str) and full[g].upper().startswith(nm.upper()) else nm for g, nm in zip(cen.index, cen.name)]
    lal = sites[sites.lookalike].groupby("grant").agg(n_sites=("site", "size"), state=("state", "first"))
    lal["name"] = lal.index
    lal["type"] = "chc"
    return cen, lal.assign(lookalike=True)


def build(year=2025):
    zcta = _cached("zcta", load_zcta)
    uns = _cached("uns", load_uns)
    z, centers = _cached(f"uds{year}", lambda: load_uds(year))
    sites, late_sites, site_stats = load_sites(year)
    rows, summary = build_cells(z, centers, zcta, uns)
    centers, lal = center_sites(centers, sites)
    # Table 4 total minus every visible row total (ZIP, Other and Unknown rows) is the exact sum of the center's hidden cells.
    centers["hidden_patients"] = (centers.patients - rows.groupby("grant").total.sum()).reindex(centers.index).fillna(0)
    centers["hidden_cells"] = rows.groupby("grant").hid_total.sum().reindex(centers.index).fillna(0).astype(int)
    summary["centers"] = len(centers)
    summary["centers_without_usable_site"] = int(centers.n_sites.isna().sum())
    summary["centers_without_usable_site_patients"] = int(centers[centers.n_sites.isna()].patients.sum())
    summary["hidden_patients_total"] = int(centers.hidden_patients.sum())
    summary["hidden_cells_total"] = int(centers.hidden_cells.sum())
    summary["hidden_patients_pct_of_total"] = round(100 * centers.hidden_patients.sum() / centers.patients.sum(), 2)
    summary["national_patients_table4"] = int(centers.patients.sum())
    summary["zctas_with_acs"] = len(zcta)
    return {"zcta": zcta, "uns": uns, "centers": centers, "lookalikes": lal, "sites": sites, "late_sites": late_sites,
            "rows": rows, "cells": rows[rows.zcta.notna()], "summary": summary, "site_stats": site_stats}


if __name__ == "__main__":
    d = build()
    print(d["summary"], d["site_stats"], sep="\n")
