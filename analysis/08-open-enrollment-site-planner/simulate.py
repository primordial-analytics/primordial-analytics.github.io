"""Parametric simulation (validation D) and the plan-regret check (validation E1).

Truth is drawn from the fitted model (covariate mean + county effect + tract effect, scaled by the model's calibration),
as true counts per tract and target. The survey is then simulated: a reported count is W x Poisson(true / W), W the
survey's per-unit weight from the fitted weight function, so small cells often read zero. Reported margins follow
sqrt(W x count), and a zero count gets the survey-wide constant margin of the real tables. The whole pipeline is rerun
on the simulated tables (new GVF, new fits, calibration, tiers) and compared with the truth.
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import estimate
import plans
import sae
import sites
import tiers
from common import DEFAULT_TIERS, TARGETS, TIERS

ZERO_SE = 14.0 / 1.645  # the margin of error the real tables report on a zero count is about 14 people


def draw_truth(model, t, rng):
    """True counts per target (n x 1 arrays keyed by target) from the model-world."""
    truth = {}
    for tg in TARGETS:
        th = np.zeros(len(t))
        for r, f in model.fits[tg].items():
            groups, gi = np.unique(f.inv, return_inverse=True)
            u = rng.standard_normal(len(groups))[gi] * np.sqrt(f.su2)
            v = rng.standard_normal(len(f.rows)) * np.sqrt(f.sv2)
            th[f.rows] = np.clip(model.region_f[tg][r] * (f.xb + u + v), 0, 100)
        truth[tg] = th / 100 * model.n[tg]
    return truth


def observe_table(model, truth, rng):
    """Reported counts and standard errors for every target."""
    obs, se = {}, {}
    for tg in TARGETS:
        n = model.n[tg]
        W = model.gvf[tg](n, truth[tg] / np.maximum(n, 1))[1]
        u = W * rng.poisson(truth[tg] / W)
        obs[tg] = u
        se[tg] = np.where(u > 0, np.sqrt(W * u), ZERO_SE)
    return obs, se


def sim_table(t, obs, se):
    ts = t.copy()
    for tg in TARGETS:
        ts[f"{tg}_u"], ts[f"{tg}_se"] = obs[tg], se[tg]
    ts["low_u"], ts["low_se"] = ts.L_u, ts.L_se
    return ts


def truth_tiers(t, truth, frac_A, shares, kid_hi):
    """Truth for every tier and the default eligible count, per tract."""
    out = {nm: np.zeros(len(t)) for nm in TIERS + ["elig"]}
    sl = estimate.county_slices(t)
    for c, rows in sl.items():
        state = t.state.to_numpy()[rows[0]]
        exp = bool(t.expansion.to_numpy()[rows[0]])
        cnt = {tg: truth[tg][rows][:, None] for tg in TARGETS}
        td = tiers.make_tiers(cnt, frac_A[rows], {b: shares[b][rows] for b in shares}, exp, state, kid_hi[rows])
        td["elig"] = sum(td[x] for x in DEFAULT_TIERS)
        for nm in out:
            out[nm][rows] = td[nm][:, 0]
    return out


def tier_coverage(tr, truth_t):
    """Coverage of each tier's tract 90% range in the simulation, and the factor on its half-width that would give 90%."""
    out = {}
    for nm, tru in truth_t.items():
        est, lo, hi = (tr[f"{nm}_{s}"].to_numpy(float) for s in ("mean", "q05", "q95"))
        half = (hi - lo) / 2
        z = np.abs(tru - est)[half > 0] / half[half > 0]
        out[nm] = {"coverage90": float(((tru >= lo) & (tru <= hi))[half > 0].mean()), "scale_to_90": float(np.quantile(z, 0.9)), "_z": z}
    return out


def rankable(lo, hi, mid, county, ok):
    med = pd.Series(np.where(ok, mid, np.nan)).groupby(county).transform("median").to_numpy()
    return ((lo > med) | (hi < med)) & ok


def evaluate(t, tr, ts, truth_e, truth_L, county_e=None):
    """Compare simulated-data estimates with truth for the eligible count and for adults at or below 138%."""
    res = {}
    n_tr = len(t)
    size = pd.qcut(t.pop_all, 3, labels=["small", "medium", "large"], duplicates="drop").to_numpy()
    county = t.county.to_numpy()
    for name, est, lo, hi, direct, truth, direct_lo, direct_hi in (
            ("elig", tr.elig_mean.to_numpy(float), tr.elig_q05.to_numpy(float), tr.elig_q95.to_numpy(float), tr.elig_direct.to_numpy(float), truth_e, None, None),
            ("L", tr.bandL_mean.to_numpy(float), tr.bandL_q05.to_numpy(float), tr.bandL_q95.to_numpy(float), ts.L_u.to_numpy(float), truth_L,
             np.maximum(ts.L_u - 1.645 * ts.L_se, 0).to_numpy(float), (ts.L_u + 1.645 * ts.L_se).to_numpy(float))):
        r = {"bias_pct": 100 * (est.sum() / truth.sum() - 1), "direct_bias_pct": 100 * (direct.sum() / truth.sum() - 1)}
        cov = (truth >= lo) & (truth <= hi)
        r["coverage90"] = float(cov.mean())
        half = (hi - lo) / 2
        z = np.abs(truth - est)[half > 0] / half[half > 0]
        r["_z"] = z  # private: run.py reads the coverage at any scale, then drops it
        r["scale_to_90"] = float(np.quantile(z, 0.9))  # factor on the interval's half-width that would give 90% coverage
        r["coverage90_by_size"] = {s: float(cov[size == s].mean()) for s in ("small", "medium", "large")}
        r["median_interval_width"] = float(np.median(hi - lo))
        if direct_lo is not None:
            dcov = (truth >= direct_lo) & (truth <= direct_hi)
            r["direct_coverage90"] = float(dcov.mean())
            dh = (direct_hi - direct_lo) / 2
            r["direct_scale_to_90"] = float(np.quantile((np.abs(truth - direct)[dh > 0] / dh[dh > 0]), 0.9))
            r["direct_median_interval_width"] = float(np.median(direct_hi - direct_lo))
            r["width_ratio_model_to_direct"] = r["median_interval_width"] / r["direct_median_interval_width"]
        r["rmse_model"] = float(np.sqrt(np.mean((est - truth) ** 2)))
        r["rmse_direct"] = float(np.sqrt(np.mean((direct - truth) ** 2)))
        # rank agreement inside counties with 20+ tracts
        cs = pd.DataFrame({"c": county, "e": est, "d": direct, "t": truth})
        rho_m, rho_d = [], []
        for c, g in cs.groupby("c"):
            if len(g) >= 20 and g.t.nunique() > 1:
                rho_m.append(spearmanr(g.e, g.t)[0])
                rho_d.append(spearmanr(g.d, g.t)[0])
        r["spearman_model_median"], r["spearman_direct_median"] = float(np.nanmedian(rho_m)), float(np.nanmedian(rho_d))
        res[name] = r
    return res


def rankable_share(t, tr, ts_or_t, f_direct=1.0, f_model=1.0):
    """Share of tracts whose own 90% interval excludes the county median rate of adults at or below 138%: the survey's
    intervals and the model's. The factors f widen each interval around its middle (1 = as published); validation D finds
    the factor that gives each one 90% coverage, so the two can be compared at equal coverage."""
    n = ts_or_t.L_n.to_numpy(float)
    ok = n > 0
    county = t.county.to_numpy()
    d_mid = ts_or_t.L_u.to_numpy(float) / np.maximum(n, 1)
    d_half = f_direct * 1.645 * ts_or_t.L_se.to_numpy(float) / np.maximum(n, 1)
    m_mid, m_lo, m_hi = (tr[f"bandL_{s}"].to_numpy(float) / np.maximum(n, 1) for s in ("mean", "q05", "q95"))
    return {"direct": float(rankable(d_mid - d_half, d_mid + d_half, d_mid, county, ok)[ok].mean()),
            "model": float(rankable(m_mid - f_model * (m_mid - m_lo), m_mid + f_model * (m_hi - m_mid), m_mid, county, ok)[ok].mean())}


def regret(t, tr_sim, truth_e, venues, counties, k=5):
    """Plans from the model's estimates, from the survey's own counts, and with the truth, all scored on the truth."""
    out = []
    for c in counties:
        rows, vg, R, lat, lon = plans.context(t, tr_sim, venues, c)
        a = sites.reach_matrix(lat, lon, vg.lat.to_numpy(), vg.lon.to_numpy(), R)
        w_true = truth_e[rows]
        best = sites.reach(a, w_true, sites.greedy(a, w_true, k))
        m = sites.reach(a, w_true, sites.greedy(a, tr_sim.elig_mean.to_numpy(float)[rows], k))
        d = sites.reach(a, w_true, sites.greedy(a, tr_sim.elig_direct.to_numpy(float)[rows], k))
        out.append({"county": c, "oracle": best, "model": m, "direct": d, "regret_model": 1 - m / best, "regret_direct": 1 - d / best})
    return pd.DataFrame(out).set_index("county")
