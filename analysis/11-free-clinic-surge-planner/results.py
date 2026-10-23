"""Turn the model into the county table, scenario totals, an example clinic, a tornado and the numbers for the page."""
import numpy as np
import pandas as pd

import model

SCEN = list(model.SCENARIOS)
VARIANTS = {"all": True, "mkt": False}          # with / without the Medicaid work-requirement layer
QCOLS = {0.10: "p10", 0.50: "p50", 0.80: "p80", 0.90: "p90", 0.95: "p95"}

SMALL_POOL = 500                                 # counties with fewer uninsured low-income adults get a "small pool" flag

# A hypothetical clinic. Every value is an input a real clinic replaces with its own.
EXAMPLE = dict(fips="37097", patients=480, visits_per_patient=3.0, patients_per_session=12,
               volunteers_per_session=6, hours_per_shift=3, shifts_per_volunteer=12, medication_per_visit=20.0, rho=1.0)


def scenario_quantiles(c, a, U):
    """Per-county quantiles of additional uninsured adults, of growth in the pool (g_) and of the growth a clinic has not
    yet seen in its trailing-year visits (cg_), plus national totals."""
    cols, totals = {}, {}
    for sc in SCEN:
        mkt, mkt_new, mcd, pool, _ = model.simulate(a, U, sc)
        for var, with_mcd in VARIANTS.items():
            inc = mkt + mcd if with_mcd else mkt
            qa = model.quantiles(inc)
            qg = model.quantiles(inc / pool)
            qc = model.quantiles((mkt_new + mcd if with_mcd else mkt_new) / pool)
            for i, q in enumerate(model.QS):
                if q in (0.10, 0.50, 0.90):
                    cols[f"add_{sc}_{var}_{QCOLS[q]}"] = qa[i]
                if q in (0.50, 0.80, 0.95):
                    cols[f"g_{sc}_{var}_{QCOLS[q]}"] = qg[i]
                    cols[f"cg_{sc}_{var}_{QCOLS[q]}"] = qc[i]
            totals[(sc, var)] = inc.sum(1)
        totals[(sc, "mcd_part")] = mcd.sum(1)
        totals[(sc, "mkt_part")] = mkt.sum(1)
        totals[(sc, "pool")] = pool.sum(1)
    return pd.DataFrame(cols, index=c.index), totals


def observed_columns(c, rank, tot_lost):
    o = pd.DataFrame({"fips": c.fips, "state": c.state, "county": c.county_name, "state_name": c.state_name,
                      "medicaid_expansion_state": np.where(c.expansion, "Y", "N")})
    b25, b26 = rank.b25.to_numpy(), rank.b26.to_numpy()
    o["low_income_selections_2025"] = b25.round(0)
    o["low_income_selections_2026"] = b26.round(0)
    o["low_income_change"] = (b26 - b25).round(0)
    o["low_income_pct_change"] = (100 * (b26 / b25 - 1)).round(1)
    o["low_income_suppressed_cell"] = (c[["FPL_100_150_supp_2025", "FPL_150_200_supp_2025", "FPL_100_150_supp_2026", "FPL_150_200_supp_2026"]].any(axis=1)).map({True: "Y", False: "N"})
    o["low_income_small_count"] = np.where(np.minimum(b25, b26) < 100, "Y", "N")
    o["stability_adjusted_pct_change"] = (100 * (np.exp(rank.log_change_adj) - 1)).round(1)
    o["premium_after_credits_2025"] = c.Avg_Prm_Aftr_APTC_2025
    o["premium_after_credits_2026"] = c.Avg_Prm_Aftr_APTC_2026
    o["auto_reenrolled_share_2025_pct"] = (100 * c.Auto_Renrl_2025 / c.Cnsmr_2025).round(1)
    o["auto_reenrolled_share_2026_pct"] = (100 * c.Auto_Renrl_2026 / c.Cnsmr_2026).round(1)
    o["auto_reenrolled_count_pct_change"] = (100 * (c.Auto_Renrl_2026 / c.Auto_Renrl_2025 - 1)).round(1)
    o["state_paid_share_feb2025_pct"] = (100 * c.rate_2025).round(1)
    o["state_paid_share_feb2026_pct"] = (100 * c.rate_2026).round(1)
    o["est_paid_adult_coverage_lost_by_feb2026"] = tot_lost.round(0)
    o["uninsured_adults_le200_2024"] = c.uninsured_le200
    o["uninsured_moe90"] = c.uninsured_moe90
    wide = c.uninsured_moe90 / c.uninsured_le200.clip(lower=1) > 0.2
    small = c.uninsured_le200 < SMALL_POOL
    o["uninsured_estimate_flag"] = np.where(small & wide, "small pool; wide margin", np.where(small, "small pool", np.where(wide, "wide margin", "")))
    return o


def clinic_sessions(growth, ex=EXAMPLE, rho=None):
    r = ex["rho"] if rho is None else rho
    patients = ex["patients"] * (1 + r * growth)
    return model.sessions_needed(patients, ex["visits_per_patient"], ex["patients_per_session"])


def tornado(c, a, U, j, ex=EXAMPLE, p=0.80):
    """One-at-a-time swings of each assumption, from its lower to its higher value, for the example county.
    Returns the sessions needed at probability p in the central scenario, with that one input moved. A larger pool or a
    larger share already in your visits gives fewer sessions, so "low" is not always the smaller number."""
    sub, Uj = model.subset(a, U, j)

    def sess(overrides=None, phi=model.PHI, baseline="draw", rho=ex["rho"]):
        _, mkt, mcd, pool, _ = model.simulate(sub, Uj, "central", overrides, phi, baseline)
        g = np.quantile((mkt + mcd)[:, 0] / pool[:, 0], p)
        return float(clinic_sessions(g, ex, rho))

    base = sess()
    labels = {
        "u": "Lost marketplace coverage that ends uninsured (30-70%)",
        "d": "Marketplace attrition after Feb 2026 (4-16%)",
        "w": "Expansion adults losing Medicaid (13.5-50%)",
        "r": "Share of that loss in place in 2027 (35-65%)",
        "z": "Medicaid losers left uninsured (70-95%)",
    }
    rows = []
    for k, lab in labels.items():
        lo = sess({k: model.SCENARIOS["lower"][k]})
        hi = sess({k: model.SCENARIOS["higher"][k]})
        rows.append((lab, lo, hi))
    rows.append(("Expansion adults' share of enrollment (27-33%)", sess({"e": 0.27}), sess({"e": 0.33})))
    rows.append(("2026 loss already in your visits (60-100%)", sess(phi=0.6), sess(phi=1.0)))
    rows.append(("Uninsured pool, SAHIE 90% interval", sess(baseline="lo"), sess(baseline="hi")))
    rows.append(("Your new-patient rate vs today (0.5x-1.5x)", sess(rho=0.5), sess(rho=1.5)))
    all_low = sess({k: model.SCENARIOS["lower"][k] for k in "udwzr"})
    all_high = sess({k: model.SCENARIOS["higher"][k] for k in "udwzr"})
    t = pd.DataFrame(rows, columns=["assumption", "sessions_low", "sessions_high"])
    t["swing"] = (t.sessions_high - t.sessions_low).abs()
    return t.sort_values("swing", ascending=False).reset_index(drop=True), base, (all_low, all_high)


FIXED_COLUMNS = {
    "fips": "5-digit county FIPS code",
    "state": "State abbreviation",
    "county": "County name",
    "state_name": "State name",
    "medicaid_expansion_state": "Y if the state expanded Medicaid (Medicaid.gov, June 2026)",
    "low_income_selections_2025": "Plan selections by people at 100-200% of poverty, 2025 open enrollment (CMS; suppressed cells of 1-10 counted as 5.5)",
    "low_income_selections_2026": "The same, 2026 open enrollment",
    "low_income_change": "2026 minus 2025 selections at 100-200% of poverty",
    "low_income_pct_change": "Percent change in those selections",
    "low_income_suppressed_cell": "Y if CMS suppressed a small cell (1-10 people) in this county's income bands",
    "low_income_small_count": "Y if either year has fewer than 100 selections, so the percent change is noisy",
    "stability_adjusted_pct_change": "Percent change shrunk toward the state mean in proportion to its noise (empirical Bayes). A ranking aid, not an estimate of the true change",
    "premium_after_credits_2025": "Average monthly premium after tax credits, 2025 (CMS)",
    "premium_after_credits_2026": "The same, 2026",
    "auto_reenrolled_share_2025_pct": "Share of selections that were automatic re-enrollments, 2025",
    "auto_reenrolled_share_2026_pct": "The same, 2026",
    "auto_reenrolled_count_pct_change": "Percent change in the number of automatic re-enrollees",
    "state_paid_share_feb2025_pct": "Share of selections paid up by February 2025, for the whole state (CMS effectuated enrollment), not the county",
    "state_paid_share_feb2026_pct": "The same, February 2026",
    "est_paid_adult_coverage_lost_by_feb2026": "Estimated net loss of paid marketplace coverage among adults at 100-200% of poverty, February 2025 to 2026 (county selections times state paid share). Negative where paid coverage rose",
    "uninsured_adults_le200_2024": "Uninsured adults 18-64 at or below 200% of poverty, 2024 (Census SAHIE)",
    "uninsured_moe90": "90% margin of error on that estimate, plus or minus",
    "rank_largest_loss": "Rank by raw loss in selections at 100-200% of poverty (1 = largest loss)",
    "rank_stability_adjusted_decline": "Rank by stability-adjusted percent change (1 = steepest decline)",
    "uninsured_estimate_flag": f"'small pool' if the 2024 estimate is under {SMALL_POOL}; 'wide margin' if the margin is over 20% of the estimate. Growth rates in small pools are unstable",
}
SCEN_TEXT = {"lower": "lower-demand", "central": "central", "higher": "higher-demand"}
VAR_TEXT = {"all": "with the Medicaid work-requirement layer", "mkt": "marketplace losses only"}
Q_TEXT = {"p10": "10th percentile", "p50": "median", "p80": "80th percentile", "p90": "90th percentile", "p95": "95th percentile"}


def codebook(columns):
    """One row per column of the county table. Every column must be described, so a new column fails loudly."""
    rows = []
    for col in columns:
        if col in FIXED_COLUMNS:
            rows.append((col, FIXED_COLUMNS[col]))
            continue
        kind, sc, var, q = col.split("_")
        what = {"add": "Additional uninsured adults at or below 200% of poverty in 2027 relative to 2024 (can be negative where paid marketplace coverage rose)",
                "g": "Additional uninsured adults as a share of the 2024 pool",
                "cg": "Growth a clinic has not yet seen in its last 12 months of visits: as g, but with 80% of the 2026 marketplace loss removed"}[kind]
        rows.append((col, f"{what}; {SCEN_TEXT[sc]} scenario, {VAR_TEXT[var]}, {Q_TEXT[q]} of 10,000 draws"))
    return pd.DataFrame(rows, columns=["column", "description"])
