"""Clean the raw files into one table of census tracts and one table of candidate venues.

Conventions
- Tracts are 2020-vintage 11-digit GEOIDs. Puerto Rico (state 72) is dropped: it has no premium tax credits or
  Medicaid expansion in the sense used here. The 50 states and DC remain.
- ACS margins of error are 90%; standard error = MOE / 1.645. When estimates are added, squared standard errors are
  added, except that of the zero estimates only the largest standard error is counted once (Census guidance).
- Cell populations are insured plus uninsured, so they are the denominators of the uninsured rates.
- C27016 cell order (checked against the table shells): for income band k = 0..4 (under 1.00, 1.00-1.37, 1.38-1.99,
  2.00-3.99, 4.00+) the block starts at E(2+10k); under 19 insured / uninsured are +2 / +3; 19 to 64 insured / uninsured
  are +5 / +6.
"""
import glob
import re

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import sources
from common import DIVISION, RAW, REGION, STATE_FIPS, STATE_NAMES

CACHE = RAW / "_cache"
CACHE.mkdir(exist_ok=True)
Z90 = 1.645
EXPANSION_STATES = {s for s in STATE_NAMES} - set(sources.NON_EXPANSION)
MIN_HOURS = 20  # a health center site must be open at least this many hours a week to count as a venue
DENSITY_CUTS = (500, 3500)  # people per land square mile: rural below, urban at or above the second


def _read_acs(name, prefix):
    d = pd.read_csv(RAW / name, sep="|", dtype={"GEO_ID": str})
    d = d[d.GEO_ID.str.startswith("1400000US")].copy()
    d["geoid"] = d.GEO_ID.str[9:]
    return d.drop(columns="GEO_ID").set_index("geoid")


def _agg(est_cells, moe_cells):
    """Sum of estimates and its standard error under the Census rule for zero estimates."""
    est = sum(est_cells)
    var = 0.0
    zero_max = np.zeros(len(est))
    for e, m in zip(est_cells, moe_cells):
        se2 = (m / Z90) ** 2
        var = var + np.where(e > 0, se2, 0.0)
        zero_max = np.maximum(zero_max, np.where(e > 0, 0.0, se2))
    return est, np.sqrt(var + zero_max)


def load_acs():
    c = _read_acs("c27016.dat", "C27016")
    if (c.filter(like="_E") < 0).any().any():
        raise ValueError("negative ACS estimates (sentinel codes) in C27016")
    e = lambda n: c[f"C27016_E{n:03d}"].to_numpy(float)
    m = lambda n: c[f"C27016_M{n:03d}"].to_numpy(float)
    t = pd.DataFrame(index=c.index)
    t["pop_all"] = e(1)
    bands = {k: 2 + 10 * k for k in range(5)}
    # Targets: children; adults at or below 138% (L = bands 0 and 1); adults 138-399% (C); adults 400%+ (D). A and B (under
    # 100%, 100-137%) are kept as direct cells for the split of L at 100% of poverty.
    uninsured_cells = {"kids": [bands[k] + 3 for k in range(5)], "L": [bands[0] + 6, bands[1] + 6], "C": [bands[2] + 6, bands[3] + 6],
                       "D": [bands[4] + 6], "A": [bands[0] + 6], "B": [bands[1] + 6]}
    pop_cells = {"kids": [i for k in range(5) for i in (bands[k] + 2, bands[k] + 3)],
                 "L": [i for k in (0, 1) for i in (bands[k] + 5, bands[k] + 6)], "C": [i for k in (2, 3) for i in (bands[k] + 5, bands[k] + 6)],
                 "D": [bands[4] + 5, bands[4] + 6], "A": [bands[0] + 5, bands[0] + 6], "B": [bands[1] + 5, bands[1] + 6]}
    for tg in ("kids", "L", "C", "D", "A", "B"):
        t[f"{tg}_u"], t[f"{tg}_se"] = _agg([e(i) for i in uninsured_cells[tg]], [m(i) for i in uninsured_cells[tg]])
        t[f"{tg}_n"] = sum(e(i) for i in pop_cells[tg])
    # uninsured children at 400% of poverty and over (cell E045): they are not in the Medicaid/CHIP range and get no premium credit
    t["kids_hi_u"] = e(bands[4] + 3)
    # poverty share of everyone in the tract
    t["pov138_share"] = (e(bands[0]) + e(bands[1])) / np.maximum(e(1), 1)  # share of all ages under 138% (header cells of the first two bands)
    # uninsured adults, all four target cells together (for the 'one tract's own count' figures)
    t["low_u"], t["low_se"], t["low_n"] = t.L_u, t.L_se, t.L_n          # adults at or below 138%
    t["low_zero_cells"] = (e(8) == 0).astype(int) + (e(18) == 0).astype(int)
    t["adult_u"], t["adult_se"] = _agg([e(8), e(18), e(28), e(38), e(48)], [m(8), m(18), m(28), m(38), m(48)])
    t["adult_n"] = t.L_n + t.C_n + t.D_n

    b = _read_acs("b27020.dat", "B27020")
    nat, nat_cit, non = b.B27020_E006.to_numpy(float), b.B27020_E012.to_numpy(float), b.B27020_E017.to_numpy(float)
    t["unins_all_ages"] = (nat + nat_cit + non)
    t["noncit_unins_all_ages"] = non
    t["state_fips"] = t.index.str[:2]
    t["county"] = t.index.str[:5]
    t = t[t.state_fips.isin(STATE_FIPS)].copy()  # drops Puerto Rico
    t["state"] = t.state_fips.map(STATE_FIPS)
    t["division"] = t.state.map(DIVISION)
    t["region"] = t.division.map(REGION)
    t["expansion"] = t.state.isin(EXPANSION_STATES).astype(int)
    return t


def add_noncitizen_share(t, k=10.0):
    """Noncitizen share of a tract's uninsured, shrunk toward its county's share (k = pseudo-count of uninsured people)."""
    cs = t.groupby("county")[["noncit_unins_all_ages", "unins_all_ages"]].transform("sum")
    sc = cs.noncit_unins_all_ages / cs.unins_all_ages.clip(lower=1)
    t["noncit_share_raw"] = t.noncit_unins_all_ages / t.unins_all_ages.where(t.unins_all_ages > 0)
    t["noncit_share"] = (t.noncit_unins_all_ages + k * sc) / (t.unins_all_ages + k)
    return t


def add_places(t):
    p = pd.read_csv(RAW / "places.csv", dtype={"locationid": str, "countyfips": str})
    p = p.set_index("locationid").data_value
    t["places"] = p.reindex(t.index)
    t["places_missing"] = t.places.isna().astype(int)
    t["places"] = t.places / 100.0
    fill = (t.groupby("state").places.transform("mean")).fillna(t.places.mean())
    t["places"] = t.places.fillna(fill)
    return t


def load_sahie():
    """County SAHIE 2024: adults 18-64 (agecat 1) at or below 138% (iprcat 3), 138-400% (5) and all incomes (0);
    children under 19 (agecat 4), all incomes. Returns one row per county FIPS."""
    s = pd.read_csv(RAW / "sahie" / "sahie_2024.csv", skiprows=85, dtype=str, skipinitialspace=True)
    s.columns = [c.strip() for c in s.columns]
    for c in s.columns:
        s[c] = s[c].str.strip()
    s = s[(s.geocat == "50") & (s.racecat == "0") & (s.sexcat == "0")].copy()
    s["county"] = s.statefips + s.countyfips
    for c in ("NIPR", "NUI", "nui_moe"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    out = pd.DataFrame(index=sorted(s.county.unique()))
    for name, agecat, ipr in (("le138", "1", "3"), ("b138_400", "1", "5"), ("all", "1", "0"), ("kids", "4", "0")):
        x = s[(s.agecat == agecat) & (s.iprcat == ipr)].set_index("county")
        out[f"sahie_{name}_pop"] = x.NIPR
        out[f"sahie_{name}_u"] = x.NUI
        out[f"sahie_{name}_moe"] = x.nui_moe
        out[f"sahie_{name}_rate"] = x.NUI / x.NIPR
    out["county_name"] = s.drop_duplicates("county").set_index("county").county_name
    return out


def add_sahie(t, sahie):
    rate_col = {"kids": "kids", "L": "le138", "C": "b138_400", "D": "all"}
    for tg, col in rate_col.items():
        t[f"sahie_{tg}"] = t.county.map(sahie[f"sahie_{col}_rate"])
    return t


def add_geography(t):
    g = pd.read_csv(next(glob.iglob(str(RAW / "gaz_tracts" / "*.txt"))), sep="\t", dtype={"GEOID": str})
    g.columns = [c.strip() for c in g.columns]
    g = g.set_index("GEOID")
    t["lat"] = g.INTPTLAT.reindex(t.index)
    t["lon"] = g.INTPTLONG.reindex(t.index)
    t["land_sqmi"] = g.ALAND_SQMI.reindex(t.index)
    if t.lat.isna().any():
        raise ValueError(f"{t.lat.isna().sum()} tracts without a Gazetteer point")
    dens = t.pop_all / t.land_sqmi.clip(lower=0.01)
    t["density"] = dens
    t["density_class"] = np.where(dens < DENSITY_CUTS[0], 0, np.where(dens < DENSITY_CUTS[1], 1, 2))  # 0 rural, 1 suburban, 2 urban
    return t


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]) * 3958.8  # miles


def add_neighbors(t, k=6):
    """Indices (positions in t) of the six nearest tracts by internal point, excluding the tract itself."""
    tree = cKDTree(xyz(t.lat.to_numpy(), t.lon.to_numpy()))
    _, idx = tree.query(xyz(t.lat.to_numpy(), t.lon.to_numpy()), k=k + 1)
    return t, idx[:, 1:]


def add_zip(t):
    """Nearest ZCTA (largest land overlap) and the share of the tract's land in it."""
    z = pd.read_csv(RAW / "zcta_tract.txt", sep="|", dtype=str, usecols=["GEOID_ZCTA5_20", "GEOID_TRACT_20", "AREALAND_TRACT_20", "AREALAND_PART"], encoding="utf-8-sig")
    z = z.dropna(subset=["GEOID_ZCTA5_20", "GEOID_TRACT_20"])
    z["part"] = pd.to_numeric(z.AREALAND_PART)
    z["tract_land"] = pd.to_numeric(z.AREALAND_TRACT_20)
    z = z.sort_values("part", ascending=False).drop_duplicates("GEOID_TRACT_20").set_index("GEOID_TRACT_20")
    t["zcta"] = z.GEOID_ZCTA5_20.reindex(t.index)
    return t


def zcta_weights():
    """Tract-to-ZCTA land-area shares, for rolling tract estimates up to ZCTAs (ZCTAs are not ZIP codes)."""
    z = pd.read_csv(RAW / "zcta_tract.txt", sep="|", dtype=str, usecols=["GEOID_ZCTA5_20", "GEOID_TRACT_20", "AREALAND_TRACT_20", "AREALAND_PART"], encoding="utf-8-sig")
    z = z.dropna(subset=["GEOID_ZCTA5_20", "GEOID_TRACT_20"])
    z["w"] = pd.to_numeric(z.AREALAND_PART) / pd.to_numeric(z.AREALAND_TRACT_20).clip(lower=1)
    return z.rename(columns={"GEOID_ZCTA5_20": "zcta", "GEOID_TRACT_20": "geoid"})[["zcta", "geoid", "w"]]


def load_venues(t):
    """Libraries (IMLS FY2023 outlets, no bookmobiles) and HRSA health center sites that are permanent, deliver services and are
    open 20 or more hours a week (no administrative-only offices; no hospital, school, nursing home, shelter or correctional
    settings). A venue belongs to the county its own file gives (IMLS tract code, HRSA county code). Where that code is not a
    county in the tract table (Connecticut's old counties, Alaska boroughs that were split) it takes the county of the nearest
    tract internal point. The venue's tract is the nearest tract inside its county."""
    lib = pd.read_csv(RAW / "imls" / "CSV" / "pls_fy23_outlet_pud23i.csv", dtype=str, encoding="latin1")
    lib = lib[~lib.C_OUT_TY.isin(["BS", "BM"])]
    lib = pd.DataFrame({
        "kind": "library", "name": lib.LIBNAME.fillna("Library").str.title(), "address": lib.ADDRESS.str.title(), "city": lib.CITY.str.title(),
        "file_county": lib.CENTRACT.str[:5], "zip": lib.ZIP.str[:5], "lat": pd.to_numeric(lib.LATITUDE), "lon": pd.to_numeric(lib.LONGITUD)})
    h = pd.read_csv(RAW / "hrsa.csv", dtype=str)
    hours = pd.to_numeric(h["Operating Hours per Week"], errors="coerce")
    h = h[(h["Health Center Location Type Description"] == "Permanent")
          & h["Health Center Type Description"].isin(["Service Delivery Site", "Administrative/Service Delivery Site"])
          & h["Health Center Service Delivery Site Location Setting Description"].isin(["All Other Clinic Types", "Unknown"])
          & (hours.reindex(h.index) >= MIN_HOURS)]
    hc = pd.DataFrame({
        "kind": "health_center", "name": h["Site Name"].fillna("Health center").str.title(), "address": h["Site Address"].str.title(), "city": h["Site City"].str.title(),
        "file_county": h["State and County Federal Information Processing Standard Code"].str.zfill(5), "zip": h["Site Postal Code"].str[:5],
        "lat": pd.to_numeric(h["Geocoding Artifact Address Primary Y Coordinate"]), "lon": pd.to_numeric(h["Geocoding Artifact Address Primary X Coordinate"])})
    v = pd.concat([lib, hc], ignore_index=True)
    v = v[v.lat.between(17, 72) & v.lon.between(-180, -60)].dropna(subset=["lat", "lon"]).copy()
    v = v[~((v.lat == 0) | (v.lon == 0))]
    tree = cKDTree(xyz(t.lat.to_numpy(), t.lon.to_numpy()))
    dist, j = tree.query(xyz(v.lat.to_numpy(), v.lon.to_numpy()))
    near_county = t.county.to_numpy()[j]
    v["county"] = np.where(v.file_county.isin(set(t.county)), v.file_county, near_county)
    v["file_county_unmatched"] = ~v.file_county.isin(set(t.county))
    v["dist_to_tract_mi"] = dist
    v = v[v.dist_to_tract_mi <= 25].drop(columns=["dist_to_tract_mi", "file_county"])  # a venue far from any tract point is a geocoding error
    v["state"] = v.county.str[:2].map(STATE_FIPS)
    v = v.drop_duplicates(["kind", "name", "address", "city"]).reset_index(drop=True)
    v["venue_id"] = np.arange(len(v))
    pos = pd.Series(np.arange(len(t)), index=t.index)
    tract = np.empty(len(v), dtype=object)
    for c, idx in v.groupby("county").indices.items():
        rows = np.flatnonzero(t.county.to_numpy() == c)
        _, k = cKDTree(xyz(t.lat.to_numpy()[rows], t.lon.to_numpy()[rows])).query(xyz(v.lat.to_numpy()[idx], v.lon.to_numpy()[idx]))
        tract[idx] = t.index.to_numpy()[rows[k]]
    v["tract"] = tract
    return v


def load_oep():
    f = next(glob.iglob(str(RAW / "oep2026" / "**" / "*.csv"), recursive=True))
    o = pd.read_csv(f, dtype=str)
    total = o[o.State_Abrvtn == "Total"]
    o = o[o.State_Abrvtn != "Total"]
    sel = pd.to_numeric(o.Cnsmr.str.replace(",", "").where(o.Cnsmr.str.strip() != "*"), errors="coerce")
    out = pd.DataFrame({"county": o.County_FIPS_Cd.str.zfill(5), "state": o.State_Abrvtn, "plan_selections_2026": sel.to_numpy()}).set_index("county")
    return out, int(pd.to_numeric(total.Cnsmr.str.replace(",", "")).iloc[0])


def build():
    """Tract table, neighbour indices, SAHIE counties, venues, plan selections, with the counts used by numbers.json."""
    t = load_acs()
    t = add_noncitizen_share(t)
    t = add_places(t)
    sahie = load_sahie()
    t = add_sahie(t, sahie)
    t = add_geography(t)
    t, nbr = add_neighbors(t)
    t = add_zip(t)
    venues = load_venues(t)
    oep, oep_total = load_oep()
    checks = {
        "tracts": int(len(t)), "states": int(t.state.nunique()), "counties": int(t.county.nunique()),
        "population_total": int(t.pop_all.sum()),
        "sahie_county_rows": int(len(sahie)), "tract_counties_missing_in_sahie": int((~t.county.drop_duplicates().isin(sahie.index)).sum()),
        "places_tracts_present": int((1 - t.places_missing).sum()), "places_tracts_missing": int(t.places_missing.sum()),
        "places_missing_states": sorted(t[t.places_missing == 1].groupby("state").size().loc[lambda s: s > 0.5 * t.groupby("state").size().reindex(s.index)].index.tolist()),
        "venues_libraries": int((venues.kind == "library").sum()), "venues_health_centers": int((venues.kind == "health_center").sum()),
        "venues_county_taken_from_nearest_tract": int(venues.file_county_unmatched.sum()),
        "venue_vintage": {"libraries": "IMLS Public Libraries Survey FY2023; some have closed", "health_centers": "HRSA site file, " + (RAW / "SOURCES.txt").read_text().splitlines()[0].lower(),
                          "health_center_rule": f"permanent, service delivery (not administrative-only), open {MIN_HOURS}+ hours a week, not a hospital, school, nursing home, shelter or correctional setting"},
        "oep_county_rows": int(len(oep)), "oep_total_row": oep_total, "oep_county_sum": int(oep.plan_selections_2026.sum()),
        "tracts_without_zcta": int(t.zcta.isna().sum()),
    }
    return t, nbr, sahie, venues, oep, checks
