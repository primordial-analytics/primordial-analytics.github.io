"""Entry point: python run.py [--cache]

Downloads the public files, fits the tract model, builds the tables and plan comparisons, runs the validation, and writes
output/numbers.json (every number on the case-study page), output/facts.json, the downloads in downloads/ and the page data
in assets/examples/08/. About 2 to 5 minutes once the files are downloaded (the first run also downloads about 900 MB); --cache keeps the slow intermediate results in data/raw/_cache
for quick reruns while editing (it is for development only: delete the folder to recompute).
"""
import json
import pickle
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True  # python -I ignores PYTHONDONTWRITEBYTECODE; keep __pycache__ out of the repo
sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works under python -I

import estimate  # noqa: E402
import fetch  # noqa: E402
import pums  # noqa: E402
import plans  # noqa: E402
import prepare  # noqa: E402
import results  # noqa: E402
import sae  # noqa: E402
import simulate  # noqa: E402
import sites  # noqa: E402
import sources  # noqa: E402
import tiers  # noqa: E402
import tables  # noqa: E402
import validate  # noqa: E402
import workbook  # noqa: E402
import web_data  # noqa: E402
from common import K, OUT, RAW, SEED, SLUG  # noqa: E402

USE_CACHE = "--cache" in sys.argv
CACHE = RAW / "_cache"
T0 = time.time()


def stage(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def cached(name, fn):
    f = CACHE / f"{name}.pkl"
    if USE_CACHE and f.exists():
        return pickle.loads(f.read_bytes())
    out = fn()
    if USE_CACHE:
        CACHE.mkdir(exist_ok=True)
        f.write_bytes(pickle.dumps(out))
    return out


def main():
    stage("fetch")
    fetch.main()
    sources.main()
    stage("prepare")
    t, nbr, sahie, venues, oep, checks = prepare.build()
    tab = pums.tabulate()
    orr = pums.ratios(tab)
    orr.to_csv(OUT / "pums_noncitizen_ratios.csv", index=False, float_format="%.5g")
    frac_A, kid_hi = tiers.split_fraction(t), tiers.kids_hi_share(t)

    stage("fit production model")
    model = tiers.prepare_model(sae.Model(t, nbr).fit(verbose=True), t)
    counties_cmp = plans.pick_counties(t, venues, 300)
    check_counties = counties_cmp[::15][:20]  # 20 counties spread across the size ranking
    example = workbook.pick_example(t, venues)

    stage("validation D and E1: simulation inside the model")
    def run_d():
        rng = np.random.default_rng(SEED + 3)
        truth = simulate.draw_truth(model, t, rng)
        obs, se = simulate.observe_table(model, truth, rng)
        ts = simulate.sim_table(t, obs, se)
        te = simulate.truth_tiers(t, truth, frac_A, tiers.noncitizen_shares(t, orr), kid_hi)
        trs, cos, _, _, _ = estimate.run(ts, nbr, sahie, venues, orr, K_=300, seed=SEED + 4, benchmark=False, split=(frac_A, kid_hi), verbose=False)
        ev = simulate.evaluate(t, trs, ts, te["elig"], truth["L"])
        ev["tiers"] = simulate.tier_coverage(trs, te)
        reg = simulate.regret(t, trs, te["elig"], venues, check_counties)
        return ev, trs, ts, reg
    val_d, trs, ts, regret_df = cached("val_d", run_d)
    # A tract range that covers less than 88% of the true values in the simulation is widened by the factor that gives 90%.
    needs = lambda v: max(1.0, round(v["scale_to_90"], 2)) if v["coverage90"] < 0.88 else 1.0
    scale = {nm: needs(v) for nm, v in val_d["tiers"].items()}
    scale["L"] = needs(val_d["L"])
    for v, f in [(v, scale[nm]) for nm, v in val_d["tiers"].items()] + [(val_d["L"], scale["L"]), (val_d["elig"], scale["elig"])]:
        v["coverage90_published"] = float((v.pop("_z") <= f).mean())
        v["tract_interval_scale"] = f
    val_d["tract_interval_scale"] = scale

    stage("estimate every county")
    tr, co, kept, model, dsum = cached("production", lambda: estimate.run(t, nbr, sahie, venues, orr, model=model, seed=SEED, keep=set(check_counties), keep_tiers=example, tract_scale=scale))
    county_ids = list(co.index)

    stage("plan strategies in 300 counties")
    exact_set = set(counties_cmp[::6])
    cmp_df = cached("plans", lambda: plans.compare(t, tr, venues, counties_cmp, exact_counties=exact_set))
    cmp_df.to_csv(OUT / "plan_strategies.csv", float_format="%.4g")

    stage("validation A: masked-tract holdouts")
    def run_a(min_pop, seed):
        res, mask = validate.holdout(t, nbr, seed=seed, min_pop=min_pop)
        validate.baselines(res, t, mask)
        return validate.summarize_holdout(res, t), int(mask.sum())
    val_a, n_masked = cached("val_a", lambda: run_a(3000, SEED + 1))
    val_a_all, n_masked_all = cached("val_a_all", lambda: run_a(1, SEED + 6))

    stage("validation B: refit without SAHIE, compare with SAHIE")
    def run_b():
        trb, cob, _, _, _ = estimate.run(t, nbr, sahie, venues, orr, K_=300, seed=SEED + 2, use_sahie=False, benchmark=False, verbose=False)
        return validate.sahie_agreement(cob, sahie)
    val_b_indep = cached("val_b", run_b)
    val_b_prod = validate.sahie_agreement(co, sahie)

    stage("validation E2: browser interval versus Monte Carlo")
    val_e2 = plan_interval_check(t, tr, co, kept, venues, check_counties)

    stage("numbers")
    f_d, f_L = val_d["L"]["direct_scale_to_90"], val_d["L"]["scale_to_90"]
    f_applied = scale.get("L", 1.0)
    rank_published = simulate.rankable_share(t, tr, t)
    rank_equal = simulate.rankable_share(t, tr, t, f_direct=f_d, f_model=f_L / f_applied)
    rank_sim = simulate.rankable_share(t, trs, ts, f_model=f_applied)
    rank_sim_equal = simulate.rankable_share(t, trs, ts, f_direct=f_d, f_model=f_L)
    rank = {"published_intervals": rank_published, "equal_90pct_simulated_coverage": rank_equal,
            "direct_coverage90_simulated": val_d["L"]["direct_coverage90"], "model_coverage90_simulated": val_d["L"]["coverage90_published"],
            "interval_scale_to_90_direct": f_d, "interval_scale_to_90_model": f_L,
            "note": "the model ranks fewer tracts on purpose: it will not rank noise"}
    nat = results.national_numbers(t, tr, co, dsum, county_ids, sahie, orr, frac_A, kid_hi)
    pools, rel = results.county_pool_numbers(co, oep)
    n = {
        "run": {"date": date.today().isoformat(), "seed": SEED, "draws": K, "python_note": "run with python -I", "elapsed_seconds": None},
        "data_checks": {**checks, "pums_state_band_ratios": int(len(orr)), "pums_ratios_pooled_by_division": int(orr.pooled_by_division.sum())},
        "observed": results.observed_numbers(t),
        "national": nat,
        "tracts": results.tract_numbers(t, tr, co, rank, {"direct_published": rank_sim["direct"], "model_published": rank_sim["model"],
                                                           "direct_equal_coverage": rank_sim_equal["direct"], "model_equal_coverage": rank_sim_equal["model"]}),
        "county_pools": pools,
        "sites": results.plan_comparison_numbers(cmp_df),
        "calibration": calibration_numbers(co, model, t),
        "model_fit": model_fit_numbers(model),
        "validation": {
            "A_holdout": {"masked_tracts": n_masked, "rule": "20% of tracts with 3,000+ people withheld at random and refit",
                          "what_it_tests": "the prediction against the survey's own count, which is noisy; the noise is simulated from the model's own weight function", **val_a},
            "A_holdout_all_sizes": {"masked_tracts": n_masked_all, "rule": "20% of tracts of any size withheld at random and refit",
                                    "what_it_tests": "the same, including the small tracts that the 3,000+ rule leaves out", **val_a_all},
            "B_sahie_independent_refit": {"what_it_tests": "a refit without SAHIE, summed to counties. It is calibrated to ACS county totals, so it mostly tests the ACS against SAHIE (administrative records). The log-count correlation is driven by county size; the rate gap is the useful number.", **val_b_indep},
            "B_sahie_production_not_independent": val_b_prod,
            "D_simulation": {"what_it_tests": "a simulation inside the model: truth is drawn from the fitted model, so these are results for a world the model describes, not for the real one. The split at 100% of poverty and the share of children at 400% and over are held fixed in it.",
                             **val_d, "rankable_adults_le138": rank},
            "E1_regret": {"counties": int(len(regret_df)), "median_regret_model_pct": results.pct(regret_df.regret_model.median()),
                          "median_regret_direct_pct": results.pct(regret_df.regret_direct.median()),
                          "share_counties_model_better_pct": results.pct((regret_df.regret_model < regret_df.regret_direct).mean(), 0),
                          "table": [{"county": c, "state": co.state[c], "name": sahie.county_name.str.strip().get(c, c), "regret_model_pct": results.pct(r.regret_model),
                                     "regret_direct_pct": results.pct(r.regret_direct)} for c, r in regret_df.iterrows()]},
            "E2_browser_interval": val_e2,
            "E3_greedy_vs_exact": n_greedy(cmp_df),
            "F_noncitizen_consistency_check": pums_check(tab, nat),
            "F_scenarios": {"noncitizen_share_able_to_get_help": "scenario control, default 0, range 0 to 70%", "plan_selection_slider": "0 to +30% on the eligible pool; a scenario, not a forecast",
                            "circuity_factor": sites.CIRCUITY, "travel_defaults_miles": sites.R_DEFAULT, "travel_max_miles": sites.R_MAX},
            "not_run": "validation C (replication on the 2015-2019 survey) and a binomial-logit interval-width check",
        },
        "methods": {"targets": 4, "regions": 4, "calibration_prior_people": 100, "sahie_benchmark": "scale to the nearest edge of SAHIE's 90% interval when the county mean is outside it"},
    }
    stage("downloads")
    cov = {nm: v["coverage90_published"] for nm, v in val_d["tiers"].items()}
    cov["elig"], cov["L"] = val_d["elig"]["coverage90_published"], val_d["L"]["coverage90_published"]
    tract_csv, county_csv = tables.write(t, tr, co, sahie, oep, rel, cov)
    n["downloads"] = {"tract_table_rows": int(len(tract_csv)), "county_table_rows": int(len(county_csv)),
                      "tract_table_mb": round((tables.DOWNLOADS / f"{SLUG}-tract-table.csv").stat().st_size / 1e6, 2),
                      "county_table_mb": round((tables.DOWNLOADS / f"{SLUG}-county-table.csv").stat().st_size / 1e6, 2)}
    stage("example workbook")
    facts = json.loads((OUT / "facts.json").read_text())
    info = workbook.make(t, tr, co, venues, sahie, example, facts, prepare.zcta_weights(), kept[example]["tiers"])
    info["rule"] = workbook.EXAMPLE_RULE_TEXT
    info["workbook_mb"] = round((tables.DOWNLOADS / f"{SLUG}-example-plan.xlsx").stat().st_size / 1e6, 2)
    n["example_county"] = info
    n["run"]["elapsed_seconds"] = int(time.time() - T0)
    (OUT / "numbers.json").write_text(json.dumps(n, indent=1, default=float))
    stage("page data")
    page_args = (t, tr, co, sahie, oep, venues, cmp_df, info, rel)
    if USE_CACHE:
        (CACHE / "page_args.pkl").write_bytes(pickle.dumps(page_args))
    print(web_data.build(*page_args))
    stage("done")


def pums_check(tab, nat):
    """The modelled national noncitizen share of uninsured adults against the person file's own, an outside check on the carve-out."""
    adults = tab[tab.index.get_level_values("group").isin(["A", "B", "C", "D"])]
    share = float(adults.w_nc.sum() / adults.w.sum())
    return {"person_file_noncitizen_share_of_uninsured_adults_pct": results.pct(share), "modelled_pct": nat["noncitizen_share_of_uninsured_adults_pct"],
            "difference_points": round(results.pct(share) - nat["noncitizen_share_of_uninsured_adults_pct"], 1)}


def model_fit_numbers(model):
    """Fitted variance components (percent squared) and the weight function, per target and region."""
    out = {}
    for tg in model.fits:
        g = model.gvf[tg]
        out[tg] = {"weight_function_log_coefficients": {"const": round(float(g.coef[0]), 3), "log_n": round(float(g.coef[1]), 3), "log_one_minus_rate": round(float(g.coef[2]), 3)},
                   "weight_function_cells": g.n_fit,
                   "share_of_cells_without_usable_se_pct": results.pct(model.zero_flag[tg].mean()),
                   "regions": {r: {"county_variance": round(float(f.su2), 3), "tract_variance_used": round(float(f.sv2), 3), "tract_variance_reml": round(float(f.reml_sv2), 4)}
                               for r, f in model.fits[tg].items()}}
    return out


def calibration_numbers(co, model, t):
    """How far the raw model total fell short of the survey's own county totals, how often the SAHIE benchmark moved a county,
    and why: the survey's rates in the cells it measures worst are much higher than in the cells it measures best, and a
    precision-weighted fit follows the well-measured cells. Rates are in percent, by quintile of the cells' sampling variance."""
    out = {}
    for tg in ("kids", "L", "C", "D"):
        n = model.n[tg]
        ok = n > 0
        direct = 100 * t[f"{tg}_u"].to_numpy(float)[ok] / n[ok]
        mod = model.means[tg][ok]
        qn = pd.qcut(model.d[tg][ok], 5, labels=False, duplicates="drop")
        out[tg] = {"mean_scale_factor": round(float(co[f"calib_{tg}"].mean()), 3), "median_scale_factor": round(float(co[f"calib_{tg}"].median()), 3),
                   "sahie_benchmark_moved_counties_pct": results.pct((co[f"sahie_factor_{tg}"] != 1.0).mean()),
                   "mean_direct_rate_pct_by_sampling_variance_quintile": [round(float(direct[qn == q].mean()), 2) for q in range(5)],
                   "mean_model_rate_pct_by_sampling_variance_quintile": [round(float(mod[qn == q].mean()), 2) for q in range(5)]}
    return out


def n_greedy(df):
    ex = df.dropna(subset=["venue_exact"])
    gap = 1 - ex.venue_greedy / ex.venue_exact
    return {"counties": int(len(ex)), "median_gap_pct": results.pct(gap.median(), 2), "max_gap_pct": results.pct(gap.max(), 2),
            "optimal_solutions": int(ex.venue_exact_optimal.astype(bool).sum())}


def plan_interval_check(t, tr, co, kept, venues, counties, n_random=6):
    """The planner's interval (independence times the county factor) against a Monte Carlo interval from the county's draws, for
    the plans a user is shown (greedy, 5 and 8 sites, at the default distance and at the largest) and for random 5-site plans.
    The factor was fit at the default distance on greedy plans of 3, 5 and 8 sites, so the largest distance is a stress test."""
    rng = np.random.default_rng(SEED + 5)
    kinds = ("greedy_5", "greedy_8", "greedy_5_largest_radius", "random_5")
    inside, ratio = {k: [] for k in kinds}, {k: [] for k in kinds}
    for c in counties:
        rows, vg, R, lat, lon = plans.context(t, tr, venues, c)
        a = sites.reach_matrix(lat, lon, vg.lat.to_numpy(), vg.lon.to_numpy(), R)
        a_max = sites.reach_matrix(lat, lon, vg.lat.to_numpy(), vg.lon.to_numpy(), sites.R_MAX)
        draws = kept[c]["elig"].astype(float)
        mean = tr.elig_mean.to_numpy(float)[rows]
        sd = draws.std(1)  # unscaled: this tests the independence-times-factor rule, not the tract widening
        infl = co.plan_inflation[c]
        trials = [("greedy_5", a, sites.greedy(a, mean, 5)), ("greedy_8", a, sites.greedy(a, mean, 8)), ("greedy_5_largest_radius", a_max, sites.greedy(a_max, mean, 5))]
        trials += [("random_5", a, rng.choice(a.shape[1], size=min(5, a.shape[1]), replace=False)) for _ in range(n_random)]
        for kind, am, sel in trials:
            cov = sites.plan_coverage(am, sel)
            if cov.sum() == 0:
                continue
            mc = cov @ draws
            mid, half = cov @ mean, 1.645 * infl * np.sqrt((cov ** 2 * sd ** 2).sum())
            inside[kind].append(float(((mc >= mid - half) & (mc <= mid + half)).mean()))
            ratio[kind].append(float(2 * half / max(np.quantile(mc, .95) - np.quantile(mc, .05), 1e-9)))
    out = {"counties": len(counties), "note": "the factor is for the default settings; other settings are approximate"}
    for k in kinds:
        i, q = np.array(inside[k]), np.array(ratio[k])
        out[k] = {"plans": int(len(i)), "mean_share_of_draws_inside_interval_pct": results.pct(i.mean()),
                  "plans_with_85_to_95_inside_pct": results.pct(((i >= .85) & (i <= .95)).mean(), 0),
                  "median_width_ratio_planner_to_monte_carlo": round(float(np.median(q)), 2)}
    return out


if __name__ == "__main__":
    main()
