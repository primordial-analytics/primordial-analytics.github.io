"""Every number quoted on the case-study page, computed from the outputs, written to output/numbers.json."""
import json
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd


URBAN_RURAL = {1: "Large central metro", 2: "Large fringe metro", 3: "Medium metro", 4: "Small metro",
               5: "Micropolitan", 6: "Noncore"}


def r1(x):
    """Round half up to one decimal (Python's round() and float noise turn 22.95 into 22.9)."""
    return float(Decimal(repr(round(float(x), 6))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def build(cs, res, manifest, state_total_sum):
    """cs: full county table (one row per county); res: model_results dict."""
    n = {}
    sup = cs[cs.count_status == "suppressed_1_to_9"]
    pub = cs[cs.count_status.isin(["published", "published_zero"])]
    pos = cs[cs.count_status == "published"]
    zero = cs[cs.count_status == "published_zero"]
    dq = cs[cs.count_status == "suppressed_data_quality"]
    n["counties"] = len(cs)
    n["published"] = len(pub)
    n["published_zero"] = len(zero)
    n["published_10_plus"] = len(pos)
    n["suppressed_1_to_9"] = len(sup)
    n["suppressed_data_quality"] = len(dq)
    n["suppressed_share_pct"] = round(100 * len(sup) / len(cs), 1)
    n["published_deaths_total"] = int(pub.published_deaths.sum())
    n["state_totals_sum"] = int(state_total_sum)
    n["population_total"] = int(cs.population.sum())
    n["suppressed_population"] = int(sup.population.sum())
    n["suppressed_population_share_pct"] = round(100 * sup.population.sum() / cs.population.sum(), 1)
    n["suppressed_median_population"] = int(sup.population.median())
    n["published_median_population"] = int(pub.population.median())

    # What the model says about the hidden counties
    n["hidden_total_deaths_median"] = int(res["hidden_total"][0])
    n["hidden_total_deaths_lo90"] = int(res["hidden_total"][1])
    n["hidden_total_deaths_hi90"] = int(res["hidden_total"][2])
    n["hidden_deaths_per_county"] = round(res["hidden_total"][0] / len(sup), 1)
    n["rate_median_hidden_counties"] = round(float(sup.rate_median_per_100k.median()), 1)
    pub_rate = cs.published_deaths / cs.population * 1e5          # unrounded, so ties round the same way everywhere
    n["rate_median_published_10_plus"] = r1(pub_rate[pos.index].median())
    n["rate_median_published_incl_zeros"] = r1(pub_rate[pub.index].median())
    n["rate_median_published_zero_modelled"] = round(float(zero.rate_median_per_100k.median()), 1)
    w_model = (sup.rate_hi90_per_100k - sup.rate_lo90_per_100k)
    w_hard = (sup.hard_hi_per_100k - sup.hard_lo_per_100k)
    n["width_ratio_median_pct"] = round(float((w_model / w_hard).median() * 100))
    n["width_ratio_share_narrower_pct"] = round(float((w_model < w_hard).mean() * 100))
    n["model_width_median"] = round(float(w_model.median()), 1)
    n["hard_width_median"] = round(float(w_hard.median()), 1)
    n["hidden_median_outside_hard_bounds"] = int(((sup.rate_median_per_100k < sup.hard_lo_per_100k) | (sup.rate_median_per_100k > sup.hard_hi_per_100k)).sum())
    n["hidden_interval_below_hard_lo"] = int((sup.rate_hi90_per_100k < sup.hard_lo_per_100k).sum())
    n["hidden_interval_above_hard_hi"] = int((sup.rate_lo90_per_100k > sup.hard_hi_per_100k).sum())
    n["hidden_p_above_state_gt_80"] = int((sup.p_rate_above_state > 0.8).sum())
    n["hidden_p_above_state_gt_50"] = int((sup.p_rate_above_state > 0.5).sum())
    n["hidden_p_above_state_lt_20"] = int((sup.p_rate_above_state < 0.2).sum())
    n["hidden_p_top_decile_gt_50"] = int((sup.p_top_decile > 0.5).sum())
    n["hidden_p_top_decile_gt_20"] = int((sup.p_top_decile > 0.2).sum())
    n["all_p_top_decile_gt_50"] = int((cs.p_top_decile > 0.5).sum())
    n["top_decile_cut_per_100k"] = round(float(cs.rate_median_per_100k.quantile(0.9)), 1)
    n["hidden_rank_interval_median_span"] = int((sup.rank_hi90 - sup.rank_lo90).median())
    n["published_rank_interval_median_span"] = int((pos.rank_hi90 - pos.rank_lo90).median())
    n["zero_counties_p_above_state_gt_20"] = int((zero.p_rate_above_state > 0.2).sum())
    n["zero_counties_hi90_median"] = round(float(zero.rate_hi90_per_100k.median()), 1)
    n["zero_median_population"] = int(zero.population.median())

    # Map and table facts
    top = cs[cs.rate_median_per_100k >= 45]
    n["map_counties_45_plus"] = len(top)
    n["map_45_plus_by_state"] = top.state.value_counts().to_dict()
    n["map_hatched_counties"] = len(sup) + len(dq)
    ur = []
    for code, label in URBAN_RURAL.items():
        g = cs[cs.nchs_urban_rural_2013 == code]
        gs, gp, g10 = g[g.count_status == "suppressed_1_to_9"], g[g.count_status.isin(["published", "published_zero"])], g[g.count_status == "published"]
        ur.append(dict(label=label, counties=len(g), suppressed=len(gs), share_suppressed_pct=round(100 * len(gs) / len(g)),
                       median_model_rate_suppressed=r1(gs.rate_median_per_100k.median()) if len(gs) else None,
                       median_published_incl_zeros=r1(pub_rate[gp.index].median()),
                       median_published_10_plus=r1(pub_rate[g10.index].median()), published_zero=int((gp.published_deaths == 0).sum()),
                       published=len(gp)))
    n["urban_rural_table"] = ur

    # Aggregate check: unconstrained model vs state residual
    ag = pd.DataFrame(res["aggregate"])
    ok = ag[ag.within_bounds & ~ag.has_dq]
    inside = (ok.residual >= ok.model_lo90) & (ok.residual <= ok.model_hi90)
    n["agg_states_with_suppressed"] = len(ag)
    n["agg_states_plausible"] = len(ok)
    n["agg_states_excluded"] = len(ag) - len(ok)
    n["agg_residual_sum_plausible"] = int(ok.residual.sum())
    n["agg_model_sum_plausible"] = int(ok.model_median.sum())
    n["agg_sum_diff_pct"] = round(100 * (ok.model_median.sum() / ok.residual.sum() - 1), 1)
    n["agg_inside_90"] = int(inside.sum())
    n["agg_within_20pct"] = int((np.abs(ok.model_median / ok.residual - 1) <= 0.2).sum())
    n["agg_corr_log"] = round(float(np.corrcoef(np.log(ok.model_median), np.log(ok.residual))[0, 1]), 3)
    bad = ag[~(ag.within_bounds & ~ag.has_dq)]
    n["agg_excluded_out_of_bounds"] = int((~ag.within_bounds).sum())
    n["agg_excluded_data_quality_only"] = int((ag.within_bounds & ag.has_dq).sum())
    n["agg_excluded_data_quality_states"] = ag[ag.within_bounds & ag.has_dq].state.tolist()
    n["agg_excluded_negative_residual"] = int((ag.residual < 0).sum())
    n["agg_plotted_excluded"] = int(((~ag.within_bounds | ag.has_dq) & (ag.residual > 0)).sum())
    # naive benchmark: hidden-county count times the average residual per hidden county, and log(count) vs residual
    per_county = ok.residual.sum() / ok.n_suppressed.sum()
    naive = per_county * ok.n_suppressed
    n["agg_naive_within_20pct"] = int((np.abs(naive / ok.residual - 1) <= 0.2).sum())
    n["agg_naive_corr_log"] = round(float(np.corrcoef(np.log(ok.n_suppressed), np.log(ok.residual))[0, 1]), 3)
    # the model interval is too narrow against these states, so widen it until 90% of them are inside
    lo_d, hi_d = ok.model_median - ok.model_lo90, ok.model_hi90 - ok.model_median
    need = np.abs(ok.residual - ok.model_median) / np.where(ok.residual > ok.model_median, hi_d, lo_d)
    k = float(np.sort(need.values)[int(np.ceil(0.9 * len(ok))) - 1])
    n["agg_coverage_scale"] = round(k, 2)
    ht = res["hidden_total"]
    n["hidden_total_widened_lo90"] = int(round(ht[0] - k * (ht[0] - ht[1]), -2))
    n["hidden_total_widened_hi90"] = int(round(ht[0] + k * (ht[2] - ht[0]), -2))
    variants = [res["sensitivity"][v]["hidden_total_median"] for v in ("main", "no_constraint", "no_covariates", "no_spatial", "pending_adjusted")]
    n["hidden_total_variant_min"], n["hidden_total_variant_max"] = int(min(variants)), int(max(variants))
    n["agg_excluded_residual_sum"] = int(bad.residual.sum())
    n["agg_excluded_model_sum"] = int(bad.model_median.sum())
    n["residual_ca"] = int(ag.set_index("state").residual["CA"])
    n["bound_hi_ca"] = int(9 * ag.set_index("state").n_suppressed["CA"])
    n["constrained_states"] = res["fit"]["n_constrained_states"]
    n["constraint_sd_pct_of_state_total"] = 5
    n["mcmc_chains"], n["mcmc_warmup"], n["mcmc_draws"] = 4, 1000, 1000

    # Fit diagnostics
    for k in ("divergences", "hyper_rhat_max", "hyper_ess_min", "eta_rhat_max", "eta_ess_min", "mean_steps"):
        n["fit_" + k] = round(res["fit"][k], 3) if isinstance(res["fit"][k], float) else res["fit"][k]
    sm = res["sensitivity"]
    n["rho_median"] = round(sm["main"]["rho_median"], 2)
    n["sigma_median"] = round(sm["main"]["sigma_median"], 2)
    for name in ("no_constraint", "no_covariates", "no_spatial", "pending_adjusted"):
        n[f"sens_{name}_median_abs_pct_change"] = round(sm[name]["median_abs_pct_change"], 1)
        n[f"sens_{name}_spearman"] = round(sm[name]["spearman_vs_main"], 3)
        n[f"sens_{name}_hidden_total"] = int(sm[name]["hidden_total_median"])
        n[f"sens_{name}_width_ratio"] = round(sm[name]["median_width_ratio"], 2)
    for k, v in res["coefficients"].items():
        n[f"coef_{k}_exp_median"] = round(float(np.exp(v[0])), 2)

    # Validation
    for T in (20, 30):
        v = res["validation"][f"pseudo_{T}"]
        n[f"pseudo{T}_n_scored"] = v["n_scored"]
        n[f"pseudo{T}_n_hidden"] = v["n_hidden"]
        for m, key in (("spatial", "spatial"), ("covariates_only", "cov"), ("poisson_gamma", "gamma")):
            r = v["models"][m]
            n[f"pseudo{T}_{key}_rps"] = round(r["rps"], 2)
            n[f"pseudo{T}_{key}_mae"] = round(r["mae"], 2)
            n[f"pseudo{T}_{key}_spearman"] = round(r["spearman"], 2)
            n[f"pseudo{T}_{key}_cov90"] = round(100 * r["coverage"][4])
            n[f"pseudo{T}_{key}_cov50"] = round(100 * r["coverage"][0])
        n[f"pseudo{T}_split_mae"] = round(v["models"]["residual_split"]["mae"], 2)
        n[f"pseudo{T}_split_spearman"] = round(v["models"]["residual_split"]["spearman"], 2)
        n[f"pseudo{T}_mid_mae"] = round(v["models"]["midpoint"]["mae"], 2)
        n[f"pseudo{T}_rps_gain_vs_gamma_pct"] = round(100 * (1 - v["models"]["spatial"]["rps"] / v["models"]["poisson_gamma"]["rps"]), 1)
        n[f"pseudo{T}_rps_gain_vs_cov_pct"] = round(100 * (1 - v["models"]["spatial"]["rps"] / v["models"]["covariates_only"]["rps"]), 1)
        n[f"pseudo{T}_mae_gain_vs_mid_pct"] = round(100 * (1 - v["models"]["spatial"]["mae"] / v["models"]["midpoint"]["mae"]), 1)
        n[f"pseudo{T}_mae_gain_vs_split_pct"] = round(100 * (1 - v["models"]["spatial"]["mae"] / v["models"]["residual_split"]["mae"]), 1)
    t = res["validation"]["temporal"]
    n["temporal_n_scored"] = t["n_scored"]
    for k, key in (("spatial_no_trend", "notrend"), ("spatial_state_trend", "trend"), ("poisson_gamma_state_trend", "gamma")):
        n[f"temporal_{key}_crps"] = round(t[k]["crps"], 2)
        n[f"temporal_{key}_mae"] = round(t[k]["mae"], 2)
        n[f"temporal_{key}_cov90"] = round(100 * t[k]["cov90_interval"])
    n["temporal_last_year_mae"] = round(t["last_year_state_trend"]["mae"], 2)
    n["temporal_last_year_n"] = t["last_year_state_trend"]["n"]
    n["temporal_gamma_mae_same_counties"] = round(t["poisson_gamma_state_trend"]["mae_same_counties"], 2)
    n["temporal_spatial_mae_same_counties"] = round(t["last_year_state_trend"]["spatial_mae_same_counties"], 2)
    n["sources"] = {k: dict(url=v["url"], downloaded=v["downloaded"]) for k, v in manifest.items()}
    return n
