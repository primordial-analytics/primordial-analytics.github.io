"""Assemble numbers.json and the downloadable tables from the pipeline's outputs. Nothing on the page is typed by hand."""
import json
from datetime import date

import numpy as np
import pandas as pd

import sources
import sites
import tiers
from common import DEFAULT_TIERS, K, OUT, SEED, STATE_NAMES, TIER_LABEL, TIERS
from plans import K_SITES

def pct(x, nd=1):
    return round(100 * float(x), nd)


def q(x, nd=0):
    a = np.asarray(x, float)
    return {"mean": round(float(a.mean()), nd) if nd else int(round(a.mean())),
            "lo90": round(float(np.quantile(a, 0.05)), nd) if nd else int(round(np.quantile(a, 0.05))),
            "hi90": round(float(np.quantile(a, 0.95)), nd) if nd else int(round(np.quantile(a, 0.95)))}


def observed_numbers(t):
    """What the survey's own tract counts say, before any modelling (adults 19-64 at or below 138% of poverty). A tract with no
    adults in the band is counted apart from a tract that has adults and reports none."""
    L_u, L_se, L_n = t.L_u.to_numpy(float), t.L_se.to_numpy(float), t.L_n.to_numpy(float)
    big = L_u >= 50
    moe_pct = 100 * 1.645 * L_se[big] / L_u[big]
    cv = np.where(L_u > 0, L_se / np.maximum(L_u, 1e-9), np.inf)
    out = {
        "tracts": int(len(t)),
        "adults_le138_uninsured_direct_total": int(L_u.sum()),
        "tracts_with_no_adults_in_band": int((L_n == 0).sum()),
        "tracts_with_no_adults_in_band_pct": pct((L_n == 0).mean()),
        "tracts_with_50_or_more": int(big.sum()),
        "median_moe_pct_of_estimate_50_plus": round(float(np.median(moe_pct)), 0),
        "median_moe_label": "90% margin of error as a share of the estimate, tracts reporting 50 or more",
        "adults_in_tracts_with_cv_over_30_pct": pct(L_u[cv > 0.30].sum() / L_u.sum(), 0),
        "median_cv_pct_50_plus": round(float(np.median(100 * L_se[big] / L_u[big])), 0),
        "median_cv_label": "standard error as a share of the estimate (the margin of error is 1.645 times this), tracts reporting 50 or more",
        "tracts_zero_cell_in_either_band_pct": pct((t.low_zero_cells.to_numpy() > 0).mean()),
    }
    for m in (100, 300):
        ok = L_n >= m
        out[f"tracts_with_{m}_or_more_adults_in_band"] = int(ok.sum())
        out[f"tracts_reporting_zero_among_{m}_or_more_pct"] = pct((L_u[ok] == 0).mean())
    return out


def tier_totals(t, tr, frac_A, kid_hi, orr, odds_scale=1.0, benchmark=True):
    """National tier totals from the tract band means (the tiers are linear in the band counts, so this equals the mean of the
    draws), with the noncitizen odds moved by odds_scale and the SAHIE benchmark on or off."""
    exp = t.expansion.to_numpy() == 1
    wi = (t.state == "WI").to_numpy()
    gap_state = ~exp & ~wi
    sh = tiers.noncitizen_shares(t, orr, odds_scale)
    if benchmark:
        L, C, D, kids = (tr[c].to_numpy(float) for c in ("bandL_mean", "bandC_mean", "bandD_mean", "bandKids_mean"))
    else:
        L, C, D, kids = (tr[c].to_numpy(float) for c in ("nb_L", "nb_C", "nb_D", "nb_kids"))
    band = {"A": L * frac_A, "B": L * (1 - frac_A), "C": C, "D": D}
    cit = {b: band[b] * (1 - sh[b]) for b in band}
    out = {"kids": (kids * (1 - kid_hi)).sum(), "medicaid": (cit["A"] * (exp | wi) + cit["B"] * exp).sum(),
           "subsidy": (cit["B"] * ~exp + cit["C"]).sum(), "gap": (cit["A"] * gap_state).sum(),
           "d400": (cit["D"] + kids * kid_hi).sum(), "noncit": sum(band[b] * sh[b] for b in band).sum()}
    out["elig"] = out["kids"] + out["medicaid"] + out["subsidy"]
    return {k: int(round(float(v))) for k, v in out.items()}


def scenarios(t, tr, orr, frac_A, kid_hi):
    """The headline range: the SAHIE benchmark on or off, times the noncitizen odds at 1/1.3, 1 and 1.3. The central case is
    benchmark on, odds as estimated."""
    grid = []
    for bench in (True, False):
        for label, scale in (("odds_low", 1 / 1.3), ("odds_base", 1.0), ("odds_high", 1.3)):
            grid.append({"sahie_benchmark": bench, "noncitizen_odds": label, "odds_scale": round(scale, 3),
                         **tier_totals(t, tr, frac_A, kid_hi, orr, scale, bench)})
    envelope = {k: {"min": min(g[k] for g in grid), "max": max(g[k] for g in grid)} for k in TIERS + ["elig"]}
    central = next(g for g in grid if g["sahie_benchmark"] and g["noncitizen_odds"] == "odds_base")
    return {"grid": grid, "envelope": envelope, "central": central}


def acs_vs_sahie(co, sahie):
    """Total uninsured in each comparable group: the survey's own tract counts against SAHIE, over the counties in both. SAHIE
    adults are 18 to 64, the survey's 19 to 64."""
    out = {}
    for tg, key in (("L", "le138"), ("C", "b138_400"), ("kids", "kids")):
        s = sahie[f"sahie_{key}_u"].reindex(co.index)
        ok = s.notna()
        a, b = float(co[f"band_{tg}_direct"][ok].sum()), float(s[ok].sum())
        out[tg] = {"survey_tract_sum": int(round(a)), "sahie": int(round(b)), "survey_over_sahie_pct": round(100 * (a / b - 1), 1)}
    return out


def national_numbers(t, tr, co, dsum, sl_counties, sahie, orr, frac_A, kid_hi):
    """Central values with the scenario range (the headline), and the draw-based 90% interval (sampling and model noise given the
    choices, from the joint county draws)."""
    out = {}
    exp_idx = np.array([bool(t.expansion.to_numpy()[np.flatnonzero(t.county.to_numpy() == c)[0]]) for c in sl_counties])
    tot = {nm: dsum[nm].astype(float).sum(0) for nm in dsum}
    out["tiers"] = {nm: q(tot[nm]) for nm in tot}
    out["tiers_label"] = "mean and 5th-95th percentile of the draws: sampling and model noise given the model choices, not the range of the claim"
    out["tiers_expansion_states"] = {nm: q(dsum[nm][exp_idx].astype(float).sum(0)) for nm in dsum}
    out["tiers_other_states"] = {nm: q(dsum[nm][~exp_idx].astype(float).sum(0)) for nm in dsum}
    all_adults = tot["medicaid"] + tot["subsidy"] + tot["gap"] + tot["d400"] + tot["noncit"]
    out["scenarios"] = scn = scenarios(t, tr, orr, frac_A, kid_hi)
    out["scenario_check_central_vs_draws_pct"] = round(100 * (scn["central"]["elig"] / tot["elig"].mean() - 1), 3)
    out["acs_vs_sahie"] = acs_vs_sahie(co, sahie)
    out["noncitizen_share_of_uninsured_adults_pct"] = round(float(np.mean(100 * tot["noncit"] / all_adults)), 1)
    out["noncitizen_slider_max_share"] = 0.7
    out["noncitizen_slider_adds_up_to"] = int(round(0.7 * tot["noncit"].mean()))
    out["children_at_400_plus"] = {"uninsured_children_total": int(t.kids_u.sum()), "at_400_plus": int(t.kids_hi_u.sum()),
                                   "share_pct": pct(t.kids_hi_u.sum() / t.kids_u.sum())}
    out["not_modelled"] = sources.FACTS["not_modelled"]
    out["states"] = int(t.state.nunique())
    out["counties"] = int(len(co))
    out["tracts"] = int(len(t))
    return out


def tract_numbers(t, tr, co, rank_share, sim):
    """Findings for the 'Tracts' section."""
    n = tr.elig_mean.to_numpy(float)
    order = np.sort(n)[::-1]
    top10 = order[: len(order) // 10].sum() / order.sum()
    L_n, L_u = t.L_n.to_numpy(float), t.L_u.to_numpy(float)
    z100 = (L_n >= 100) & (L_u == 0)
    out = {
        "can_be_ranked_eligible_per_resident_pct": pct(tr.can_rank.mean()),
        "can_be_ranked_label": "eligible people per resident, a different quantity from the adults-at-or-below-138% shares below",
        "share_of_eligible_in_top_10pct_of_tracts_pct": pct(top10, 0),
        "rankable_adults_le138": rank_share,
        "rankable_adults_le138_simulated_model": sim,
        "zero_tracts_100_plus_adults": int(z100.sum()),
        "zero_tracts_100_plus_adults_model_median_hi90": int(np.median(tr.bandL_q95.to_numpy(float)[z100])) if z100.any() else None,
    }
    m_w = (tr.bandL_q95 - tr.bandL_q05).to_numpy(float)
    d_w = 2 * 1.645 * t.L_se.to_numpy(float)
    ok = L_n > 0
    out["median_interval_width_adults_le138_model"] = int(np.median(m_w[ok]))
    out["median_interval_width_adults_le138_direct"] = int(np.median(d_w[ok]))
    out["interval_width_reduction_pct"] = pct(1 - np.median(m_w[ok]) / np.median(d_w[ok]), 0)
    return out


def county_pool_numbers(co, oep):
    """People in the subsidy range per 2026 plan selection, against the county's state. The file covers the HealthCare.gov states
    only; children and Medicaid-range adults never appear in plan selections, so only the subsidy range is compared."""
    sel = oep.plan_selections_2026.reindex(co.index)
    ok = sel.notna() & (sel > 0)
    ratio = (co.subsidy_mean[ok] / sel[ok])
    st = co.state[ok]
    state_avg = co.subsidy_mean[ok].groupby(st).sum() / sel[ok].groupby(st).sum()
    rel = ratio / st.map(state_avg)
    return {"counties_with_plan_selection_data": int(ok.sum()), "states_in_file": int(st.nunique()),
            "subsidy_per_plan_selection_overall": round(float(co.subsidy_mean[ok].sum() / sel[ok].sum()), 2),
            "counties_over_2x_state_average": int((rel > 2).sum()), "median_county_vs_state_average": round(float(rel.median()), 2),
            "scope": "HealthCare.gov states only; state-run exchanges, Connecticut included, are not in the file"}, rel


def plan_comparison_numbers(df):
    """Medians across the compared counties. Every strategy is scored with the optimiser's own reach rule on the model's
    expected eligible people, so the optimiser wins by construction; validation E1 is the independent check. The lead is the
    gain over the five highest direct counts (the baseline a person would use), the highest-rate baseline is secondary."""
    def gain(a, b, col_prefix):
        return (df[f"{col_prefix}{a}"] / df[f"{col_prefix}{b}"] - 1)
    out = {"counties": int(len(df)), "min_tracts": int(df.tracts.min()), "k_sites": K_SITES,
           "covers": {"states": int(df.state.nunique()), "expansion_state_counties": int(df.expansion.sum()),
                      "median_tracts": int(df.tracts.median()), "median_venues": int(df.venues.median()), "median_population": int(df.population.median()),
                      "by_travel_distance": {f"{r:g}_miles": int((df.radius == r).sum()) for r in sorted(df.radius.unique())},
                      "rule": "the 300 counties with the most tracts among those with 8 or more candidate venues"}}
    for pre, label in (("venue_", "venues"), ("popup_", "popup")):
        g = {"greedy_over_direct": gain("greedy", "direct", pre), "greedy_over_rate": gain("greedy", "rate", pre), "greedy_over_model": gain("greedy", "model", pre),
             "model_over_direct": gain("model", "direct", pre), "greedy_over_greedy_direct": gain("greedy", "greedy_direct", pre)}
        if pre == "venue_":
            g["greedy_over_direct_spaced"] = gain("greedy", "direct_sep", pre)
            g["greedy_over_direct_no_overlap_discount"] = df.venue_nocap_greedy / df.venue_nocap_direct - 1
        out[label] = {k: {"median_pct": pct(v.median(), 0), "q25_pct": pct(v.quantile(.25), 0), "q75_pct": pct(v.quantile(.75), 0)} for k, v in g.items()}
        out[label]["share_of_county_eligible_reached_by_greedy_median_pct"] = pct((df[f"{pre}greedy"] / df.eligible_total).median(), 0)
        share = df[f"{pre}greedy"] / df.eligible_total
        out[label]["share_of_county_eligible_reached_by_greedy_q25_pct"], out[label]["share_of_county_eligible_reached_by_greedy_q75_pct"] = pct(share.quantile(.25), 0), pct(share.quantile(.75), 0)
        out[label]["share_of_county_eligible_reached_by_rate_median_pct"] = pct((df[f"{pre}rate"] / df.eligible_total).median(), 0)
    out["lead"] = {"text": "expected reach of the optimiser's five sites against the five highest direct counts, same reach rule",
                   "median_gain_pct": out["venues"]["greedy_over_direct"]["median_pct"], "q25_pct": out["venues"]["greedy_over_direct"]["q25_pct"],
                   "q75_pct": out["venues"]["greedy_over_direct"]["q75_pct"],
                   "gain_over_count_plan_with_sites_one_travel_distance_apart_median_pct": out["venues"]["greedy_over_direct_spaced"]["median_pct"]}
    ex = df.dropna(subset=["venue_exact"])
    out["greedy_vs_exact"] = {"counties": int(len(ex)), "median_gap_pct": pct((1 - ex.venue_greedy / ex.venue_exact).median(), 2),
                              "max_gap_pct": pct((1 - ex.venue_greedy / ex.venue_exact).max(), 1),
                              "share_solved_to_optimality_pct": pct(ex.venue_exact_optimal.astype(float).mean(), 0)}
    return out
