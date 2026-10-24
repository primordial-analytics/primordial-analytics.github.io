"""Write the page data for the example: assets/examples/08/data.json and one state-<FIPS>.json per state.

data.json holds every number on the page (numbers.json and facts.json verbatim), the state list, the default county and the
tables behind the sites figure. A state file holds that state's tracts, counties and venues as parallel arrays, loaded when a
state is chosen. Nothing is typed by hand: all values come from the pipeline's tables. run.py calls build() at the end;
`python web_data.py` rebuilds from the tables run.py --cache keeps in data/raw/_cache/page_args.pkl.
"""
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # python -I ignores PYTHONDONTWRITEBYTECODE; keep __pycache__ out of the repo
sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works under python -I

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sources  # noqa: E402
from common import OUT, RAW, SITE, STATE_FIPS, STATE_NAMES, TIERS  # noqa: E402

DEST = SITE / "assets" / "examples" / "08"
PAGE = SITE / "_casestudies" / "08-open-enrollment-site-planner.md"
STATE_FIPS_BY_ABBR = {v: k for k, v in STATE_FIPS.items()}


def arr(series, nd=None):
    out = []
    for v in series:
        if pd.isna(v):
            out.append(None)
        elif nd is None:
            out.append(int(round(float(v))))
        else:
            out.append(round(float(v), nd))
    return out


def zip_cities(sub, venues):
    """ZIP area -> the city most venues with that ZIP give, for the ZIP areas of this state's tracts. Not every ZIP area has a venue."""
    v = venues[venues.zip.isin(set(sub.zcta.dropna()))]
    top = v.groupby("zip").city.agg(lambda c: c.value_counts().index[0])
    return {z: c for z, c in top.items() if isinstance(c, str) and c}


def state_file(st, t, tr, co, sahie, oep, venues, rel):
    rows = np.flatnonzero(t.state.to_numpy() == st)
    sub, ctr = t.iloc[rows], tr.iloc[rows]
    counties = list(dict.fromkeys(sub.county))
    cidx = {c: i for i, c in enumerate(counties)}
    names = sahie.county_name.str.strip()
    tr_out = {
        "g": [g[5:] for g in sub.index], "c": [cidx[c] for c in sub.county],
        "lon": arr(sub.lon, 4), "lat": arr(sub.lat, 4), "pop": arr(sub.pop_all),
        "zip": [z if isinstance(z, str) else "" for z in sub.zcta], "dens": arr(sub.density_class),
        "rk": arr(ctr.can_rank), "pm": arr(sub.places_missing),
        "direct": arr(ctr.elig_direct, 1), "esd": arr(ctr.elig_sd, 1), "den": arr(sub.kids_n + sub.L_n + sub.C_n),
        # adults at or below 138% of poverty: the survey's own count and standard error, and the model's, for the tracts figure
        "Lu": arr(sub.L_u), "Lse": arr(sub.L_se, 1), "L": arr(ctr.bandL_mean, 1), "L_lo": arr(ctr.bandL_q05), "L_hi": arr(ctr.bandL_q95),
    }
    for nm in list(TIERS) + ["elig"]:
        tr_out[f"{nm}"] = arr(ctr[f"{nm}_mean"], 1)
        tr_out[f"{nm}_lo"] = arr(ctr[f"{nm}_q05"])
        tr_out[f"{nm}_hi"] = arr(ctr[f"{nm}_q95"])
    county_out = []
    for c in counties:
        r = co.loc[c]
        county_out.append({"f": c, "n": names.get(c, c), "r": float(r.radius_miles), "infl": round(float(r.plan_inflation), 3),
                           "sel": (None if pd.isna(oep.plan_selections_2026.get(c, np.nan)) else int(oep.plan_selections_2026[c])),
                           "elig": int(round(r.elig_mean)), "sub": int(round(r.subsidy_mean)), "elig_lo": int(round(r.elig_q05)), "elig_hi": int(round(r.elig_q95)),
                           "sub_vs_state": (None if pd.isna(rel.get(c, np.nan)) else round(float(rel[c]), 2))})
    v = venues[venues.county.isin(cidx)]  # a venue belongs to the county its own file gives, whatever the nearest tract is
    ven_out = {"n": v["name"].tolist(), "k": (v.kind == "library").astype(int).tolist(), "a": v.address.fillna("").tolist(), "city": v.city.fillna("").tolist(),
               "zip": v.zip.fillna("").tolist(), "lat": arr(v.lat, 4), "lon": arr(v.lon, 4), "c": [cidx[c] for c in v.county]}
    return {"state": st, "fips": STATE_FIPS_BY_ABBR[st], "name": STATE_NAMES[st], "expansion": int(st not in sources.NON_EXPANSION),
            "waiver": sources.STATE_NOTES.get(st, ""), "own_marketplace": int(st in sources.STATE_MARKETPLACES), "zip_city": zip_cities(sub, venues), "counties": county_out, "tracts": tr_out, "venues": ven_out}


def stat_tiles(n):
    """The three tiles on the page, from numbers.json. The page's front matter holds the same text for readers without scripts;
    build() fails if it differs, so no tile can drift from the numbers."""
    env = n["national"]["scenarios"]["envelope"]["elig"]
    base = next(g for g in n["national"]["scenarios"]["grid"] if g["sahie_benchmark"] and g["noncitizen_odds"] == "odds_base")
    v, lead = n["sites"]["venues"], n["sites"]["lead"]
    return [(f"{base['elig'] / 1e6:.1f} million", f"Modeled. Range {env['min'] / 1e6:.1f} to {env['max'] / 1e6:.1f} million"),
            (f"{v['share_of_county_eligible_reached_by_greedy_median_pct']:.0f}%",
             f"Modeled, distance-weighted. Middle half {v['share_of_county_eligible_reached_by_greedy_q25_pct']:.0f}% to {v['share_of_county_eligible_reached_by_greedy_q75_pct']:.0f}%"),
            (f"{lead['median_gain_pct']:.0f}%", f"Modeled, planner's own rule. Middle half {lead['q25_pct']:.0f}% to {lead['q75_pct']:.0f}%")]


def check_stat_tiles(n):
    text = PAGE.read_text().split("---", 2)[1]
    got = list(zip(re.findall(r"^  - value: (.+)$", text, flags=re.M), [x.strip('"') for x in re.findall(r"^    note: (.+)$", text, flags=re.M)]))
    if got != stat_tiles(n):
        raise ValueError(f"the stats in {PAGE.name} differ from numbers.json:\n{got}\n{stat_tiles(n)}")


def build(t, tr, co, sahie, oep, venues, cmp_df, example_info, rel):
    DEST.mkdir(parents=True, exist_ok=True)
    for old in DEST.glob("state-*.json"):
        old.unlink()
    sizes = {}
    states = []
    n_venues = 0
    for st in sorted(t.state.unique(), key=lambda s: STATE_NAMES[s]):
        d = state_file(st, t, tr, co, sahie, oep, venues, rel)
        n_venues += len(d["venues"]["n"])
        for c_i, c in enumerate(d["counties"]):  # the candidate set the browser gets for a county is the one the analysis used
            mine = venues[venues.county == c["f"]]
            got = sorted(zip(*(np.array(d["venues"][k], dtype=object)[np.array(d["venues"]["c"]) == c_i] for k in ("lat", "lon", "n"))))
            want = sorted(zip(arr(mine.lat, 4), arr(mine.lon, 4), mine["name"].tolist()))
            if got != want:
                raise ValueError(f"venue set differs for county {c['f']}")
        f = DEST / f"state-{d['fips']}.json"
        f.write_text(json.dumps(d, separators=(",", ":")))
        states.append({"abbr": st, "fips": d["fips"], "name": STATE_NAMES[st], "file": f"state-{d['fips']}.json", "tracts": len(d["tracts"]["g"]), "bytes": f.stat().st_size,
                       "counties": [[c["f"], c["n"]] for c in d["counties"]]})
    numbers = json.loads((OUT / "numbers.json").read_text())
    check_stat_tiles(numbers)
    facts = json.loads((OUT / "facts.json").read_text())
    # figure: interval width (percentage points of the cell population) by cell size, whole country
    ok = t.L_n.to_numpy() > 0
    ln = t.L_n.to_numpy(float)[ok]
    bins = pd.qcut(ln, 5, duplicates="drop")
    dwid = (2 * 1.645 * t.L_se.to_numpy(float)[ok]) / ln * 100
    mwid = (tr.bandL_q95.to_numpy(float)[ok] - tr.bandL_q05.to_numpy(float)[ok]) / ln * 100
    g = pd.DataFrame({"b": bins, "d": dwid, "m": mwid, "n": ln}).groupby("b", observed=True)
    fig_width = {"cell_size_lo": arr(g.n.min()), "cell_size_hi": arr(g.n.max()), "direct_width_pp": arr(g.d.median(), 1), "model_width_pp": arr(g.m.median(), 1)}
    names = sahie.county_name.str.strip()
    fig_sites = {"county": cmp_df.index.tolist(), "name": [names.get(c, c) for c in cmp_df.index], "state": [co.state[c] for c in cmp_df.index],
                 "tracts": cmp_df.tracts.astype(int).tolist(), "eligible": arr(cmp_df.eligible_total)}
    for k in ("rate", "direct", "model", "greedy"):
        fig_sites[f"venue_{k}"] = arr(cmp_df[f"venue_{k}"])
        fig_sites[f"popup_{k}"] = arr(cmp_df[f"popup_{k}"])
    # the county the tool opens on: the median-population county among the compared counties in states that expanded Medicaid
    exp = cmp_df[(cmp_df.expansion == 1)].sort_values("population")
    default = exp.index[len(exp) // 2]
    share = lambda pre, k: (cmp_df[f"{pre}{k}"] / cmp_df.eligible_total)
    summary = {pre.rstrip("_"): {k: {"median": round(float(share(pre, k).median()), 4), "q25": round(float(share(pre, k).quantile(.25)), 4), "q75": round(float(share(pre, k).quantile(.75)), 4)}
                                 for k in ("rate", "direct", "model", "greedy")} for pre in ("venue_", "popup_")}
    summary["top_rate_tract_not_in_top3_by_count_pct"] = round(100 * float(1 - cmp_df.venue_top3_has_top_rate.mean()), 0)
    data = {"numbers": numbers, "facts": facts, "states": states, "example": example_info, "default_county": default, "fig_width": fig_width, "fig_sites": fig_sites, "sites_summary": summary}
    (DEST / "data.json").write_text(json.dumps(data, separators=(",", ":"), default=float))
    if n_venues != len(venues):
        raise ValueError(f"{len(venues) - n_venues} venues are in no state file")
    return {"default_county": default, "venues_in_state_files": n_venues, "state_files": len(states), "largest_state_bytes": max(s["bytes"] for s in states), "data_json_bytes": (DEST / "data.json").stat().st_size}


if __name__ == "__main__":
    import pickle

    print(build(*pickle.loads((RAW / "_cache" / "page_args.pkl").read_bytes())))
