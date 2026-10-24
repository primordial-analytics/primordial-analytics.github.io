"""The two downloadable tables and their codebook."""
import numpy as np
import pandas as pd

import sources
from common import SITE, SLUG, STATE_NAMES, TIERS

DOWNLOADS = SITE / "downloads"
TIER_COL = {"kids": "children", "medicaid": "medicaid_range", "subsidy": "subsidy_range", "gap": "coverage_gap", "d400": "over_400pct",
            "noncit": "noncitizen_adults", "elig": "eligible_default"}
TIER_TEXT = {
    "kids": "uninsured children under 19 and under 400% of poverty",
    "medicaid": "uninsured citizen adults 19-64 in the Medicaid range (at or below 138% of poverty in expansion states; under 100% in Wisconsin)",
    "subsidy": "uninsured citizen adults 19-64 in the subsidy range (138-399% of poverty in expansion states; 100-399% elsewhere)",
    "gap": "uninsured citizen adults 19-64 in the coverage gap (under 100% of poverty in non-expansion states, except Wisconsin; Georgia included)",
    "d400": "uninsured citizen adults 19-64 and uninsured children at 400% of poverty and over (full price for adults)",
    "noncit": "uninsured noncitizen adults 19-64 at any income (eligibility varies)",
    "elig": "default eligible: children under 400% + Medicaid range + subsidy range (income only: work rules, employer offers and immigration status are not tested)",
}


def tract_table(t, tr):
    d = pd.DataFrame({"geoid": t.index, "state": t.state.to_numpy(), "county_fips": t.county.to_numpy(),
                      "nearest_zcta": t.zcta.fillna("").to_numpy(), "population": t.pop_all.astype(int).to_numpy()})
    for nm in TIER_COL:
        d[f"{TIER_COL[nm]}_est"] = np.rint(tr[f"{nm}_mean"]).astype(int).to_numpy()
        d[f"{TIER_COL[nm]}_lo90"] = np.rint(tr[f"{nm}_q05"].clip(lower=0)).astype(int).to_numpy()  # widening around the mean can pass below 0
        d[f"{TIER_COL[nm]}_hi90"] = np.rint(tr[f"{nm}_q95"]).astype(int).to_numpy()
    d["direct_eligible"] = np.rint(tr.elig_direct).astype(int).to_numpy()
    d["can_be_ranked"] = tr.can_rank.astype(int).to_numpy()
    d["places_missing"] = t.places_missing.astype(int).to_numpy()
    return d


def county_table(t, co, sahie, oep, rel):
    names = sahie.county_name.str.strip()
    d = pd.DataFrame(index=co.index)
    d["county_fips"] = co.index
    d["state"] = co.state
    d["county_name"] = names.reindex(co.index).to_numpy()
    d["tracts"] = t.groupby("county").size().reindex(co.index).to_numpy()
    d["population"] = t.groupby("county").pop_all.sum().reindex(co.index).astype(int).to_numpy()
    for nm in TIER_COL:
        d[f"{TIER_COL[nm]}_est"] = np.rint(co[f"{nm}_mean"]).astype(int)
        d[f"{TIER_COL[nm]}_lo90"] = np.rint(co[f"{nm}_q05"]).astype(int)
        d[f"{TIER_COL[nm]}_hi90"] = np.rint(co[f"{nm}_q95"]).astype(int)
    d["direct_eligible"] = np.rint(co.elig_direct).astype(int)
    for tg, key, label in (("L", "le138", "adults_le138"), ("C", "b138_400", "adults_138_399"), ("kids", "kids", "children")):
        d[f"model_{label}_est"] = np.rint(co[f"band_{tg}_mean"]).astype(int)
        d[f"model_{label}_lo90"] = np.rint(co[f"band_{tg}_q05"]).astype(int)
        d[f"model_{label}_hi90"] = np.rint(co[f"band_{tg}_q95"]).astype(int)
        s = sahie.reindex(co.index)
        d[f"sahie_{label}_est"] = np.rint(s[f"sahie_{key}_u"]).astype("Int64")
        d[f"sahie_{label}_moe90"] = np.rint(s[f"sahie_{key}_moe"]).astype("Int64")
    d["plan_selections_2026"] = oep.plan_selections_2026.reindex(co.index).astype("Int64")
    d["subsidy_per_plan_selection"] = (co.subsidy_mean / oep.plan_selections_2026.reindex(co.index)).round(2)
    d["subsidy_per_plan_selection_vs_state"] = rel.reindex(co.index).round(2)
    d["default_travel_miles"] = co.radius_miles
    d["venues_libraries_and_health_centers"] = co.venues
    d["plan_interval_inflation"] = co.plan_inflation.round(2)
    d["medicaid_expansion_state"] = (~co.state.isin(sources.NON_EXPANSION)).astype(int)
    return d.reset_index(drop=True)


def codebook(tract, county, cov):
    """One row per column of each table. cov: simulated coverage of the tract 90% ranges (validation D)."""
    acs = "ACS 2020-2024 5-year tables C27016 and B27020 (Census); model in analysis README"
    pct = lambda x: f"{100 * x:.0f}%"
    tier_cov = {TIER_COL[nm]: v for nm, v in cov.items() if nm in TIER_COL}
    est_word = {"est": "expected", "lo90": "5th percentile of", "hi90": "95th percentile of"}
    meaning = {
        "geoid": ("11-digit 2020 census tract code", "Census", ""), "state": ("state or DC postal code", "Census", ""),
        "county_fips": ("5-digit county code (Connecticut: planning region)", "Census", ""),
        "nearest_zcta": ("ZIP code tabulation area with the largest land overlap (not always the mailing ZIP; blank for water-only tracts)", "Census 2020 ZCTA-tract relationship file", ""),
        "population": ("civilian noninstitutionalized population with poverty status determined, all ages (a little below the resident population)", acs, "people"),
        "direct_eligible": ("default eligible count built from the survey's own tract counts with no model (the same tier rules and noncitizen shares)", acs, "people"),
        "can_be_ranked": ("1 if the 90% interval of eligible people per resident is wholly above or wholly below the county's median tract", "model", "0/1"),
        "places_missing": ("1 if CDC PLACES has no value for the tract (all of Kentucky and Pennsylvania in the 2025 release)", "CDC PLACES 2025", "0/1"),
        "tracts": ("census tracts in the county", "Census", "count"), "county_name": ("county name from SAHIE", "Census SAHIE 2024", ""),
        "plan_selections_2026": ("2026 open enrollment plan selections (HealthCare.gov states only; not effectuated enrollment; blank where the file has none)", "CMS 2026 OEP county file", "people"),
        "subsidy_per_plan_selection": ("subsidy_range_est divided by plan_selections_2026; children and Medicaid-range adults never appear in plan selections, so only the subsidy range is compared", "model; CMS", "ratio"),
        "subsidy_per_plan_selection_vs_state": ("subsidy_per_plan_selection divided by the same ratio for all the state's counties in the file", "model; CMS", "ratio"),
        "default_travel_miles": ("default travel distance for the planner: 3 urban, 5 suburban, 15 rural, from where the county's people live", "Census Gazetteer; this analysis", "miles"),
        "venues_libraries_and_health_centers": ("candidate venues in the county: public library outlets (IMLS FY2023) and permanent health center service sites open 20+ hours a week (HRSA)", "IMLS; HRSA", "count"),
        "plan_interval_inflation": ("ratio of the true spread of the reach of the greedy 3-, 5- and 8-site plans to the spread obtained by treating tracts as independent", "model draws", "ratio"),
        "medicaid_expansion_state": ("1 if the state has adopted the Medicaid expansion", "KFF, checked " + sources.CHECKED, "0/1"),
    }
    for nm, c in TIER_COL.items():
        for suffix in ("est", "lo90", "hi90"):
            what = f"{est_word[suffix]} {TIER_TEXT[nm]}"
            meaning[f"{c}_{suffix}"] = (what + ("" if suffix == "est" else ". {COV}"), acs + "; PLACES, SAHIE, PUMS", "people")
    groups = {"adults_le138": "adults 19-64 at or below 138% of poverty (all citizenship)", "adults_138_399": "adults 19-64 at 138-399% of poverty (all citizenship)",
              "children": "children under 19 at any income (all citizenship)"}
    for label, what in groups.items():
        for suffix in ("est", "lo90", "hi90"):
            meaning[f"model_{label}_{suffix}"] = (f"{est_word[suffix]} uninsured {what}, comparable with SAHIE", "model", "people")
        meaning[f"sahie_{label}_est"] = (f"SAHIE 2024 estimate of uninsured {what} (SAHIE adults are 18-64; income bands 138% and 138-400%)", "Census SAHIE 2024", "people")
        meaning[f"sahie_{label}_moe90"] = (f"SAHIE 90% margin of error for sahie_{label}_est", "Census SAHIE 2024", "people")
    rows = []
    for name, df in (("tract", tract), ("county", county)):
        for col in df.columns:
            if col not in meaning:
                raise KeyError(f"no codebook entry for {name}.{col}")
            m, src, unit = meaning[col]
            if "{COV}" in m:
                c = col.rsplit("_", 1)[0]
                m = m.replace("{COV}", f"In a simulation this 90% range, after widening, covered {pct(tier_cov[c])} of true tract values" if name == "tract"
                              else "County ranges come from the model draws and were not widened or checked in the simulation")
            rows.append({"table": name, "column": col, "meaning": m, "source": src, "unit": unit})
    return pd.DataFrame(rows)


def write(t, tr, co, sahie, oep, rel, cov):
    DOWNLOADS.mkdir(exist_ok=True)
    tract = tract_table(t, tr)
    county = county_table(t, co, sahie, oep, rel)
    tract.to_csv(DOWNLOADS / f"{SLUG}-tract-table.csv", index=False)
    county.to_csv(DOWNLOADS / f"{SLUG}-county-table.csv", index=False)
    codebook(tract, county, cov).to_csv(DOWNLOADS / f"{SLUG}-tables-codebook.csv", index=False)
    return tract, county
