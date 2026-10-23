"""Build assets/examples/10/data.json for the example page from output/*.

Reads only files in output/: county_rates.csv, model_results.json and numbers.json. Nothing is typed
by hand. County fields are stored as parallel arrays (one array per field, same row order) because that
gzips to well under 100 KB for 3,142 counties. Rates are per 100,000 people per year, rounded as in the
CSV; probabilities are stored as integers per 1,000.

Run on its own (`python web_data.py`) or at the end of run.py.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
DEST = HERE.parent.parent / "assets" / "examples" / "10" / "data.json"

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
STATUS = {"published": 0, "published_zero": 1, "suppressed_1_to_9": 2, "suppressed_data_quality": 3}

# numbers.json keys the page reads (prose, stat tiles, charts)
NUMBER_KEYS = [
    "counties", "published", "published_zero", "published_10_plus", "suppressed_1_to_9",
    "suppressed_data_quality", "suppressed_share_pct", "suppressed_population",
    "suppressed_population_share_pct", "hidden_total_deaths_median", "hidden_total_deaths_lo90",
    "hidden_total_deaths_hi90", "hidden_total_widened_lo90", "hidden_total_widened_hi90",
    "hidden_total_variant_min", "hidden_total_variant_max", "rate_median_hidden_counties",
    "rate_median_published_10_plus", "hidden_p_above_state_gt_80", "hidden_p_above_state_gt_50",
    "hidden_p_top_decile_gt_50", "top_decile_cut_per_100k", "hidden_rank_interval_median_span",
    "published_rank_interval_median_span", "zero_counties_p_above_state_gt_20",
    "zero_median_population", "agg_states_plausible", "agg_inside_90", "agg_within_20pct",
    "agg_corr_log", "agg_naive_within_20pct", "agg_naive_corr_log", "agg_residual_sum_plausible",
    "agg_model_sum_plausible", "pseudo20_n_scored", "pseudo30_n_scored", "rate_median_published_incl_zeros",
    "agg_coverage_scale", "model_width_median", "hard_width_median", "hidden_median_outside_hard_bounds",
    "hidden_interval_below_hard_lo", "rate_median_published_zero_modelled", "agg_excluded_residual_sum",
    "agg_excluded_model_sum",
]


def main():
    c = pd.read_csv(OUT / "county_rates.csv", dtype={"fips": str})
    res = json.loads((OUT / "model_results.json").read_text())
    nums = json.loads((OUT / "numbers.json").read_text())

    states = sorted(c.state.unique())
    sidx = {s: i for i, s in enumerate(states)}
    c = c.sort_values("fips").reset_index(drop=True)

    def col(series, nd=None, scale=None):
        out = []
        for v in series:
            if pd.isna(v):
                out.append(None)
            elif scale:
                out.append(int(round(v * scale)))
            elif nd == 0:
                out.append(int(v))
            else:
                out.append(round(float(v), nd))
        return out

    counties = {
        "f": c.fips.tolist(),
        "n": c.county.tolist(),
        "s": [sidx[s] for s in c.state],
        "p": c.population.astype(int).tolist(),
        "u": c.nchs_urban_rural_2013.astype(int).tolist(),
        "t": [STATUS[s] for s in c.count_status],  # 0 published 10+, 1 published zero, 2 hidden 1 to 9, 3 hidden for data quality
        "d": col(c.published_deaths, 0),
        "r": col(c.published_rate_per_100k, 1),
        "m": col(c.rate_median_per_100k, 1),
        "l": col(c.rate_lo90_per_100k, 1),
        "h": col(c.rate_hi90_per_100k, 1),
        "a": col(c.p_rate_above_state, scale=1000),
        "q": col(c.p_top_decile, scale=1000),
        "kl": c.rank_lo90.astype(int).tolist(),
        "kh": c.rank_hi90.astype(int).tolist(),
        "bl": col(c.hard_lo_per_100k, 1),
        "bh": col(c.hard_hi_per_100k, 1),
    }

    # NCHS state total = published county counts + the state difference stored in model_results.json
    # (only states that have hidden counties have a difference).
    resid = {a["state"]: a["residual"] for a in res["aggregate"]}
    srows = []
    for s in states:
        d = c[c.state == s]
        pop = int(d.population.sum())
        row = {
            "a": s, "n": STATE_NAMES[s], "f": d.fips.iloc[0][:2], "p": pop, "nc": len(d),
            "nh": int((d.count_status.str.startswith("suppressed")).sum()),
            # the model's state rate: population-weighted county medians (the reference used for p_rate_above_state)
            "r": round(float((d.rate_median_per_100k * d.population).sum() / pop), 1),
        }
        if s in resid:
            row["sr"] = round((float(d.published_deaths.sum()) + resid[s]) / pop * 1e5, 1)  # rate from the NCHS state total
        srows.append(row)

    def model_block(v):
        keep = {}
        for k, m in v["models"].items():
            keep[k] = {kk: (round(vv, 3) if isinstance(vv, float) else [round(x, 3) for x in vv])
                       for kk, vv in m.items() if kk in ("rps", "mae", "coverage")}
        return {"T": v["T"], "n_scored": v["n_scored"], "n_hidden": v["n_hidden"], "models": keep}

    t = res["validation"]["temporal"]
    data = {
        "_source": "analysis/10-hidden-overdose-counties/web_data.py from output/county_rates.csv, "
                   "model_results.json and numbers.json",
        "run_date": nums["run_date"], "window_ending": nums["window_ending"], "nchs_data_as_of": nums["nchs_data_as_of"],
        "counties": counties,
        "states": srows,
        "numbers": {k: nums[k] for k in NUMBER_KEYS},
        "urban_rural": nums["urban_rural_table"],
        "aggregate": res["aggregate"],
        "levels": [0.5, 0.6, 0.7, 0.8, 0.9, 0.95],
        "hide_and_score": {"20": model_block(res["validation"]["pseudo_20"]), "30": model_block(res["validation"]["pseudo_30"])},
        "forecast": {
            "n_scored": t["n_scored"],
            "spatial_crps": round(t["spatial_state_trend"]["crps"], 2), "gamma_crps": round(t["poisson_gamma_state_trend"]["crps"], 2),
            "same_n": t["last_year_state_trend"]["n"], "spatial_mae": round(t["last_year_state_trend"]["spatial_mae_same_counties"], 2),
            "gamma_mae": round(t["poisson_gamma_state_trend"]["mae_same_counties"], 2),
            "last_year_mae": round(t["last_year_state_trend"]["mae"], 2),
        },
        "hidden_total": [round(x) for x in res["hidden_total"]],
        "sensitivity": {k: {"abs_pct": round(v["median_abs_pct_change"], 1), "total": round(v["hidden_total_median"])}
                        for k, v in res["sensitivity"].items()},
    }
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(data, separators=(",", ":")))
    print(f"wrote {DEST} ({DEST.stat().st_size / 1024:.0f} KB, {len(c)} counties)")


if __name__ == "__main__":
    main()
