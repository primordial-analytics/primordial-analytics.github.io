"""Entry point: python run.py

Downloads the public files, builds the county table and scenarios, writes output/ (including numbers.json with every
number quoted on the case-study page), the figures in img/case_studies/ and the downloads in downloads/.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))  # also works under python -I

import fetch  # noqa: E402
import figures  # noqa: E402
import model  # noqa: E402
import prepare  # noqa: E402
import results  # noqa: E402
import workbook  # noqa: E402

HERE = Path(__file__).parent
OUT = HERE / "output"
SITE = HERE.parent.parent
SLUG = "11-free-clinic-surge-planner"


# Figures quoted from other people's work, not computed here. Read from the pages linked below on 2026-10-22.
EXTERNAL = {
    "kff_2026-07-28_feb_effectuation_rate_national_pct": {"2025": 90, "2026": 83, "mississippi_2026": 61, "url": "https://www.kff.org/affordable-care-act/how-has-aca-marketplace-enrollment-changed-across-states-in-2026/"},
    "kff_2026-05-19_projected_2026_average_effectuated_millions": {"central": 17.5, "low": 16.5, "wakely_decline_range_pct": [17, 26],
                                                                  "url": "https://www.kff.org/affordable-care-act/what-we-know-so-far-about-2026-aca-marketplace-enrollment-premiums-and-deductibles/"},
    "kff_expansion_adults_share_of_expansion_state_medicaid_enrollment_pct": {"value": 31, "period": "June 2024", "denominator": "Medicaid enrollment (the model applies it to Medicaid plus CHIP)", "model_value": 30, "url": "https://www.kff.org/medicaid/5-key-facts-about-medicaid-expansion/"},
    "aspe_2026-06-26_improper_enrollment_millions": {"remaining": 2.6, "removed_or_blocked": 2.9,
                                                      "url": "https://www.aspe.hhs.gov/sites/default/files/documents/f5f29954221d5b5713070ac2541fda8e/aca-enrollment-report-2026-final-version.pdf"},
    "site_medicaid_what_if_post_loss_shares_pct": {"low": 13.5, "mid": 28, "high": 50, "url": "/blog/medicaid-what-if-template/"},
}


def r(x, nd=0):
    return round(float(x), nd) if nd else int(round(float(x)))


def build_numbers(c, st, checks, rank, eb, bt, qdf, totals, tor, ex_sessions, extras):
    exp = c.expansion
    n = {}
    st_ok = st.dropna(subset=["rate_2026"])
    low25, low26 = prepare_low(c, 2025), prepare_low(c, 2026)
    n["data_checks"] = {
        "oep2026_counties": checks["oep2026_counties"], "oep2025_counties": checks["oep2025_counties"],
        "matched_counties": checks["matched_counties"],
        "oep2026_selections_total_row": checks["oep2026_total_row"], "oep2026_selections_county_sum": r(checks["oep2026_county_sum"]),
        "oep2025_selections_total_row": checks["oep2025_total_row"],
        "sahie_uninsured_le200_national_county_sum": r(checks["county_rows_uninsured_le200"]),
        "sahie_uninsured_le200_national_state_sum": r(checks["state_rows_uninsured_le200"]),
        "medicaid_pi_period": checks["pi_period"], "cms_all_platform_feb2025": checks["cms_all_platform_feb2025"],
        "cms_all_platform_feb2026": checks["cms_all_platform_feb2026"],
        "cms_all_platform_pct_change": r(100 * (checks["cms_all_platform_feb2026"] / checks["cms_all_platform_feb2025"] - 1), 1), "states_with_2026_data": int(len(st_ok)),
    }
    n["observed"] = {
        "selections_2025_matched": r(c.Cnsmr_2025.sum()), "selections_2026_matched": r(c.Cnsmr_2026.sum()),
        "selections_pct_change": r(100 * (c.Cnsmr_2026.sum() / c.Cnsmr_2025.sum() - 1), 1),
        "low_income_selections_2025": r(low25.sum()), "low_income_selections_2026": r(low26.sum()),
        "low_income_pct_change": r(100 * (low26.sum() / low25.sum() - 1), 1),
        "median_county_premium_after_credits_2025": r(c.Avg_Prm_Aftr_APTC_2025.median()),
        "median_county_premium_after_credits_2026": r(c.Avg_Prm_Aftr_APTC_2026.median()),
        "auto_reenrollees_2025": r(c.Auto_Renrl_2025.sum()), "auto_reenrollees_2026": r(c.Auto_Renrl_2026.sum()),
        "auto_reenrollees_pct_change": r(100 * (c.Auto_Renrl_2026.sum() / c.Auto_Renrl_2025.sum() - 1), 1),
        "paid_share_feb2025_pct": r(100 * st_ok.eff_2025.sum() / st_ok.sel_2025.sum(), 1),
        "paid_share_feb2026_pct": r(100 * st_ok.eff_2026.sum() / st_ok.sel_2026.sum(), 1),
        "paid_feb2025": r(st_ok.eff_2025.sum()), "paid_feb2026": r(st_ok.eff_2026.sum()),
        "paid_lost_feb2026_vs_feb2025": r(st_ok.eff_2025.sum() - st_ok.eff_2026.sum()),
        "paid_pct_change": r(100 * (st_ok.eff_2026.sum() / st_ok.eff_2025.sum() - 1), 1),
        "states_paid_share_below_70_pct": sorted(st_ok.index[st_ok.rate_2026 < 0.70].tolist()),
        "lowest_paid_share_state": st_ok.rate_2026.idxmin(), "lowest_paid_share_pct": r(100 * st_ok.rate_2026.min(), 1),
        "corr_state_paid_share_vs_auto_share": r(np.corrcoef(st_ok.rate_2026, st_ok.auto_share_2026)[0, 1], 2),
        "corr_state_paid_share_vs_le10_share": r(np.corrcoef(st_ok.rate_2026, st_ok.le10_share_2026)[0, 1], 2),
        "est_paid_adult_coverage_lost_by_feb2026": extras["lost_total"],
        "uninsured_le200_baseline": r(c.uninsured_le200.sum()),
        "uninsured_le200_baseline_expansion_states": r(c.uninsured_le200[exp].sum()),
        "counties_expansion_states": int(exp.sum()), "counties_other_states": int((~exp).sum()),
        "counties_small_count_flag": int((np.minimum(rank.b25, rank.b26) < 100).sum()),
        "counties_suppressed_cell": int(c[["FPL_100_150_supp_2025", "FPL_150_200_supp_2025", "FPL_100_150_supp_2026", "FPL_150_200_supp_2026"]].any(axis=1).sum()),
        "counties_wide_uninsured_margin": int((c.uninsured_moe90 / c.uninsured_le200.clip(lower=1) > 0.2).sum()),
        "counties_small_pool_under_500": int((c.uninsured_le200 < results.SMALL_POOL).sum()),
        "counties_negative_marketplace_addition_central": int((qdf["add_central_mkt_p50"] < 0).sum()),
        "counties_with_pool_over_5000": int((c.uninsured_le200 >= 5000).sum()),
    }
    n["ranking"] = {**{k: (r(v, 3) if isinstance(v, float) else v) for k, v in eb.items()},
                    "top25_overlap_raw_vs_adjusted": extras["top25_overlap"],
                    "top25_overlap_raw_vs_adjusted_min500": extras["top25_overlap_500"]}
    n["backtest"] = {"counties_used": bt["n"], "rmse_zero_change": r(bt["rmse"]["zero"], 3), "rmse_national_mean": r(bt["rmse"]["national"], 3),
                     "rmse_state_mean": r(bt["rmse"]["state"], 3), "rmse_state_plus_other_band": r(bt["rmse"]["state_plus_band"], 3),
                     "within_state_corr_between_bands": r(bt["within_state_corr"], 2),
                     "state_share_of_variance_pct_100_150_band": r(100 * bt["state_share_of_variance_a"], 0),
                     "rmse_gain_other_band_over_state_pct": r(100 * (1 - bt["rmse"]["state_plus_band"] / bt["rmse"]["state"]), 1),
                     "rmse_gain_ci95_pct": [r(x, 1) for x in bt["gain_ci95"]], "min_selections_per_band_year": 100}
    sc = {}
    for s in results.SCEN:
        t_all, t_mkt, t_mcd, pool = totals[(s, "all")], totals[(s, "mkt")], totals[(s, "mcd_part")], totals[(s, "pool")]
        sc[s] = {
            "total_p10": r(np.quantile(t_all, .1), 0), "total_p50": r(np.quantile(t_all, .5)), "total_p90": r(np.quantile(t_all, .9)),
            "marketplace_p10": r(np.quantile(t_mkt, .1)), "marketplace_p50": r(np.quantile(t_mkt, .5)), "marketplace_p90": r(np.quantile(t_mkt, .9)),
            "medicaid_p10": r(np.quantile(t_mcd, .1)), "medicaid_p50": r(np.quantile(t_mcd, .5)), "medicaid_p90": r(np.quantile(t_mcd, .9)),
            "growth_total_p50_pct": r(100 * np.quantile(t_all / pool, .5), 1),
            "growth_marketplace_p50_pct": r(100 * np.quantile(t_mkt / pool, .5), 1),
            "median_county_growth_p50_expansion_pct": r(100 * qdf.loc[exp, f"g_{s}_all_p50"].median(), 1),
            "median_county_growth_p50_other_pct": r(100 * qdf.loc[~exp, f"g_{s}_all_p50"].median(), 1),
            "median_county_growth_p50_marketplace_only_pct": r(100 * qdf[f"g_{s}_mkt_p50"].median(), 1),
        }
    n["scenarios_2054_counties"] = sc
    n["tornado_example_county"] = {"base_sessions_p80": tor[1], "rows": tor[0].round(0).to_dict("records")}
    n["example_clinic"] = ex_sessions
    n["assumptions"] = {"scenario_means": model.SCENARIOS, "beta_concentration": model.KAPPA, "expansion_share_of_medicaid_chip": model.E_MEAN,
                        "phi_share_of_2026_loss_in_trailing_year": model.PHI, "draws": model.K, "seed": model.SEED}
    return n


def prepare_low(c, y):
    return c[f"FPL_100_150_{y}"].fillna(0) + c[f"FPL_150_200_{y}"].fillna(0)


def example_block(c, a, U):
    ex = results.EXAMPLE
    j = int(np.where(c.fips == ex["fips"])[0][0])
    out = {"county": f"{c.county_name.iloc[j]}, {c.state.iloc[j]}", "fips": ex["fips"], "uninsured_le200": r(c.uninsured_le200.iloc[j]),
           "moe90": r(c.uninsured_moe90.iloc[j]), "inputs": ex}
    today_visits = ex["patients"] * ex["visits_per_patient"]
    out["capture_pct"] = r(100 * ex["patients"] / c.uninsured_le200.iloc[j], 1)
    out["today_visits"] = r(today_visits)
    out["today_sessions"] = r(today_visits / ex["patients_per_session"], 1)
    out["today_volunteers"] = r(np.ceil(out["today_sessions"] * ex["volunteers_per_session"] / ex["shifts_per_volunteer"]))
    rows = []
    aj, Uj = model.subset(a, U, j)
    for s in results.SCEN:
        _, mkt, mcd, pool, _ = model.simulate(aj, Uj, s)
        for var, inc in (("all", mkt + mcd), ("mkt", mkt)):
            g = inc[:, 0] / pool[:, 0]
            for p in (0.5, 0.8, 0.95):
                gq = float(np.quantile(g, p))
                sess = float(results.clinic_sessions(gq))
                visits = ex["patients"] * (1 + ex["rho"] * gq) * ex["visits_per_patient"]
                rows.append({"scenario": s, "layers": var, "probability": p, "growth_pct": r(100 * gq, 1), "sessions": r(sess),
                             "extra_sessions": r(sess - out["today_sessions"]),
                             "volunteers": r(np.ceil(sess * ex["volunteers_per_session"] / ex["shifts_per_volunteer"])),
                             "volunteer_hours": r(sess * ex["volunteers_per_session"] * ex["hours_per_shift"]),
                             "medication_dollars": r(visits * ex["medication_per_visit"])})
    out["rows"] = rows
    out["newsvendor_ratio_80"] = 4
    out["newsvendor_ratio_95"] = 19
    return out, j


def _table(caption, head, rows, first_is_row_header=True):
    num = ' class="text-end"'
    th = "".join(f'<th scope="col"{"" if i == 0 else num}>{h}</th>' for i, h in enumerate(head))
    body = []
    for row in rows:
        cells = "".join((f'<th scope="row">{v}</th>' if i == 0 else f'<td class="text-end">{v}</td>') for i, v in enumerate(row))
        body.append(f"<tr>{cells}</tr>")
    return (f'<div class="table-responsive">\n<table class="table table-sm">\n<caption>{caption}</caption>\n<thead><tr>{th}</tr></thead>\n<tbody>\n'
            + "\n".join(body) + "\n</tbody>\n</table>\n</div>")


def write_tables(c, st, table, numbers, path):
    """HTML data tables for the page, generated from the same numbers as the figures."""
    names = c.drop_duplicates("state").set_index("state").state_name
    s = st.dropna(subset=["rate_2026"]).sort_values("rate_2026", ascending=False)
    t1 = _table("Low-income plan selections and share paid up, by state, 2025 and 2026, highest 2026 paid share first",
                ["State", "Selections 2025", "Selections 2026", "Change", "Paid share Feb 2025", "Paid share Feb 2026"],
                [(names[i], f"{x.low_sel_2025:,.0f}", f"{x.low_sel_2026:,.0f}", f"{100 * (x.low_sel_2026 / x.low_sel_2025 - 1):+.1f}%",
                  f"{100 * x.rate_2025:.1f}%", f"{100 * x.rate_2026:.1f}%") for i, x in s.iterrows()])
    t1b = _table("Ten counties with the largest stability-adjusted decline in low-income selections (at least 500 in 2025)",
                 ["County", "Selections 2025", "Selections 2026", "Raw change", "Stability-adjusted change"],
                 [(f"{x['county']}, {x['state']}", f"{x['low_income_selections_2025']:,.0f}", f"{x['low_income_selections_2026']:,.0f}",
                   f"{x['low_income_pct_change']:+.1f}%", f"{x['stability_adjusted_pct_change']:+.1f}%") for x in numbers["ranking_top10_min500"]])
    sc = numbers["scenarios_2054_counties"]
    t2 = _table("Additional uninsured adults at or below 200% of poverty in 2027 relative to 2024, 2,054 counties (10th, 50th and 90th percentiles)",
                ["Scenario", "Marketplace only", "Medicaid layer only", "Both layers", "Both layers, % of 2024 pool (median)", "Median county, expansion states", "Median county, other states"],
                [(k.capitalize(), f"{v['marketplace_p10']:,} / {v['marketplace_p50']:,} / {v['marketplace_p90']:,}",
                  f"{v['medicaid_p10']:,} / {v['medicaid_p50']:,} / {v['medicaid_p90']:,}",
                  f"{v['total_p10']:,} / {v['total_p50']:,} / {v['total_p90']:,}", f"{v['growth_total_p50_pct']:.1f}%",
                  f"{v['median_county_growth_p50_expansion_pct']:.1f}%", f"{v['median_county_growth_p50_other_pct']:.1f}%") for k, v in sc.items()])
    ex = numbers["example_clinic"]
    t3 = _table(f"Hypothetical clinic: sessions, volunteers and medication for 2027 (today: {ex['today_sessions']:.0f} sessions, {ex['today_volunteers']} volunteers)",
                ["Scenario and layers", "Probability", "Growth in visits", "Sessions a year", "Extra sessions", "Volunteers", "Volunteer hours", "Medication dollars"],
                [(f"{x['scenario'].capitalize()}, {'with Medicaid layer' if x['layers'] == 'all' else 'marketplace only'}", f"{int(100 * x['probability'])}%",
                  f"{x['growth_pct']:.1f}%", x["sessions"], x["extra_sessions"], x["volunteers"], f"{x['volunteer_hours']:,}", f"${x['medication_dollars']:,}")
                 for x in ex["rows"]])
    t3b = _table(f"Sessions a year at 80% probability when one assumption moves from its low to its high end (central case: {numbers['tornado_example_county']['base_sessions_p80']:.0f}). A larger pool, or more of the 2026 loss already in your visits, means fewer sessions",
                 ["Assumption (low to high)", "Sessions at the low end", "Sessions at the high end"],
                 [(x["assumption"], f"{x['sessions_low']:.0f}", f"{x['sessions_high']:.0f}") for x in numbers["tornado_example_county"]["rows"]])
    path.write_text("\n\n".join([t1, t1b, t2, t3, t3b]) + "\n")


def main():
    fetch.fetch_all()
    c, st, checks = prepare.build()
    a = model.county_arrays(c)
    U = model.draw_uniforms(len(c))
    rank, eb = model.eb_ranking(c)
    bt = model.backtest(c)
    qdf, totals = results.scenario_quantiles(c, a, U)
    lost = model.simulate(a, U, "central")[-1]
    lost_point = np.median(lost, axis=0)
    ex_block, j = example_block(c, a, U)
    t, base, bounds = results.tornado(c, a, U, j)

    obs = results.observed_columns(c, rank, lost_point)
    obs["rank_largest_loss"] = (rank.b25 - rank.b26).rank(ascending=False, method="min").astype(int)
    obs["rank_stability_adjusted_decline"] = rank.log_change_adj.rank(method="min").astype(int)
    table = pd.concat([obs, qdf.round(4)], axis=1)
    top_raw = set(rank.fips[rank.log_change_raw.rank(method="first") <= 25])
    top_adj = set(rank.fips[rank.log_change_adj.rank(method="first") <= 25])
    big = rank.b25 >= 500
    top_raw5 = set(rank.fips[big][rank.log_change_raw[big].rank(method="first") <= 25])
    top_adj5 = set(rank.fips[big][rank.log_change_adj[big].rank(method="first") <= 25])
    extras = {"lost_total": r(lost_point.sum()), "top25_overlap": len(top_raw & top_adj), "top25_overlap_500": len(top_raw5 & top_adj5)}
    ex_block["tornado_base_sessions_p80"] = base
    aj, Uj = model.subset(a, U, j)
    _, mkt_j, mcd_j, pool_j, _ = model.simulate(aj, Uj, "central")
    gj = ((mkt_j + mcd_j) / pool_j)[:, 0]
    _, m0, d0, p0, _ = model.simulate(aj, Uj, "central", phi=0.0)
    ex_block["p80_sessions_phi0"] = r(results.clinic_sessions(float(np.quantile(((m0 + d0) / p0)[:, 0], 0.8))))
    pat = np.random.default_rng(1).poisson(results.EXAMPLE["patients"] * (1 + gj))
    ex_block["poisson_check_p80_sessions"] = r(np.quantile(model.sessions_needed(pat, results.EXAMPLE["visits_per_patient"], results.EXAMPLE["patients_per_session"]), 0.8))
    ex_block["poisson_check_p95_sessions"] = r(np.quantile(model.sessions_needed(pat, results.EXAMPLE["visits_per_patient"], results.EXAMPLE["patients_per_session"]), 0.95))
    top10 = table[table.low_income_selections_2025 >= 500].nsmallest(10, "stability_adjusted_pct_change")

    numbers = build_numbers(c, st, checks, rank, eb, bt, qdf, totals, (t, base, bounds), ex_block, extras)
    rows = {(x["scenario"], x["layers"], x["probability"]): x for x in ex_block["rows"]}
    cen, mk = rows[("central", "all", 0.8)], rows[("central", "mkt", 0.8)]
    c95 = rows[("central", "all", 0.95)]
    numbers["derived_example"] = {
        "central_sessions_p50": rows[("central", "all", 0.5)]["sessions"], "central_sessions_p80": cen["sessions"], "central_sessions_p95": c95["sessions"],
        "central_p80_extra_sessions": cen["extra_sessions"], "central_p95_extra_sessions": c95["extra_sessions"],
        "p80_to_p95_added_sessions": c95["sessions"] - cen["sessions"], "p80_to_p95_added_volunteer_hours": c95["volunteer_hours"] - cen["volunteer_hours"],
        "p80_to_p95_added_volunteers": c95["volunteers"] - cen["volunteers"],
        "central_p80_volunteers": cen["volunteers"], "central_p95_volunteers": c95["volunteers"],
        "marketplace_only_central_sessions_p80": mk["sessions"],
        "lower_sessions_p80": rows[("lower", "all", 0.8)]["sessions"], "higher_sessions_p80": rows[("higher", "all", 0.8)]["sessions"],
        "central_growth_pct_p50": rows[("central", "all", 0.5)]["growth_pct"], "central_growth_pct_p80": cen["growth_pct"], "central_growth_pct_p95": c95["growth_pct"],
        "median_sahie_moe_pct_of_estimate": r(100 * (c.uninsured_moe90 / c.uninsured_le200.clip(lower=1)).median(), 0),
        "top10_north_carolina_count": int((top10.state == "NC").sum()),
        "hi_median_county_growth_central_pct": r(100 * qdf.loc[c.state == "HI", "g_central_all_p50"].median(), 0),
        "top10_raw_change_min_pct": float(top10.low_income_pct_change.min()), "top10_raw_change_max_pct": float(top10.low_income_pct_change.max()),
        "top10_adjusted_change_min_pct": float(top10.stability_adjusted_pct_change.min()), "top10_adjusted_change_max_pct": float(top10.stability_adjusted_pct_change.max()),
        "p80_sessions_if_none_of_2026_loss_in_visits": ex_block["p80_sessions_phi0"],
        "median_county_growth_all_central_pct": r(100 * qdf["g_central_all_p50"].median(), 1),
        "oep2026_county_sum_short_of_total_row": checks["oep2026_total_row"] - r(checks["oep2026_county_sum"]),
        "kff_may_projected_2026_average_vs_cms_feb2026_pct": r(100 * (1 - 17.5e6 / checks["cms_all_platform_feb2026"]), 1),
    }
    numbers["ranking_top10_min500"] = top10[["county", "state", "low_income_selections_2025", "low_income_selections_2026", "low_income_pct_change", "stability_adjusted_pct_change"]].to_dict("records")
    numbers["external_figures_quoted"] = EXTERNAL
    numbers["sources"] = [line.split("\t") for line in (HERE / "data" / "raw" / "SOURCES.txt").read_text().splitlines()]

    OUT.mkdir(exist_ok=True)
    table.to_csv(OUT / "county_table.csv", index=False)
    results.codebook(table.columns).to_csv(OUT / "county_table_codebook.csv", index=False)
    st.drop(index=[i for i in st.index if np.isnan(st.loc[i, "rate_2026"])]).round(4).to_csv(OUT / "state_table.csv")
    t.round(1).to_csv(OUT / "tornado.csv", index=False)
    pd.DataFrame(ex_block["rows"]).to_csv(OUT / "example_clinic.csv", index=False)
    (OUT / "numbers.json").write_text(json.dumps(numbers, indent=1, default=str))

    write_tables(c, st, table, numbers, OUT / "page_tables.html")
    print("figure sizes (px):", figures.make_all(c, st, rank, qdf, totals, t, ex_block, numbers, SITE / "img" / "case_studies"))
    workbook.make(table, ex_block, SITE / "downloads")
    shutil.copy(OUT / "county_table.csv", SITE / "downloads" / f"{SLUG}-county-table.csv")
    shutil.copy(OUT / "county_table_codebook.csv", SITE / "downloads" / f"{SLUG}-county-table-codebook.csv")


if __name__ == "__main__":
    main()
