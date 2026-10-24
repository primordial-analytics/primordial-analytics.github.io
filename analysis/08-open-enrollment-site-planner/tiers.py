"""From model draws to tiers: calibration, the SAHIE soft benchmark, the split at 100% of poverty, the noncitizen carve-out.

For each county the model gives K posterior draws of the uninsured count in four targets (children, adults at or below
138%, adults 138-399%, adults 400%+). Then, in order:

1. Calibration. The model's county total falls below the sum of the tracts' own survey counts (shrinkage in a model fit
   on rates; the shortfall is reported). Each county and target is scaled by f = (U + a) / (M + a / f_region), U the direct
   total, M the model total, a = CALIB_PRIOR people, f_region the region's own ratio. A county with few uninsured people
   borrows its region's ratio.
2. SAHIE soft benchmark. If the county mean for a SAHIE-comparable group is outside SAHIE's 90% interval, that group is
   scaled to the nearest edge of the interval. Groups: adults at or below 138%, adults 138-399%, children; then adults
   at 400%+ so the all-income adult total falls inside SAHIE's interval.
3. Adults at or below 138% are split at 100% of poverty: the tract's own two bands (shrunk to a prior from the state's
   ratio of the two bands' uninsured rates).
4. Tiers. Expansion states: Medicaid range = adults at or below 138%; subsidy range = 138-399%. Other states: coverage gap
   = under 100% (Wisconsin only: placed in the Medicaid range and flagged); subsidy range = 100-399%. Children under 400% of
   poverty in one tier; the share of a tract's uninsured children at 400% and over (the tract's own cell, shrunk to its
   county) goes to the 400% tier with the adults. Noncitizen adults are removed from every adult tier into their own tier.
"""
import numpy as np
import pandas as pd

import sources
from common import DEFAULT_TIERS, K, TIERS

CALIB_PRIOR = 100.0
KIDS_HI_PRIOR = 10.0  # children: pseudo-count for shrinking a tract's share of uninsured children at 400%+ to its county's
SPLIT_PRIOR = 30.0    # adults: pseudo-count (people) for shrinking a tract's under-100% share to the state-ratio prior
QS = (0.05, 0.5, 0.95)
BANDS = ("A", "B", "C", "D")


def kids_hi_share(t):
    """Share of a tract's uninsured children who are at 400% of poverty or over: the tract's own cell shrunk to its county."""
    cs = t.groupby("county")[["kids_hi_u", "kids_u"]].transform("sum")
    sc = cs.kids_hi_u / cs.kids_u.clip(lower=1)
    return ((t.kids_hi_u + KIDS_HI_PRIOR * sc) / (t.kids_u + KIDS_HI_PRIOR)).clip(0, 1).to_numpy()


def split_fraction(t):
    """Share of a tract's adult at-or-below-138% uninsured who are under 100% of poverty (band A): the tract's own two bands
    shrunk (SPLIT_PRIOR people) to a prior built from its population shares and the state's ratio of the bands' rates."""
    st = t.state.to_numpy()
    g = t.groupby("state")
    rA = g.A_u.sum() / g.A_n.sum().clip(lower=1)
    rB = g.B_u.sum() / g.B_n.sum().clip(lower=1)
    rho = (rA / rB.where(rB > 0)).clip(0.5, 2.0).fillna(1.0)
    p = np.where(t.L_n > 0, t.A_n / np.maximum(t.L_n, 1), 0.5)
    r = rho.reindex(st).to_numpy()
    prior = r * p / (r * p + (1 - p))
    return (t.A_u.to_numpy() + SPLIT_PRIOR * prior) / (t.L_u.to_numpy() + SPLIT_PRIOR)


def noncitizen_shares(t, orr, odds_scale=1.0):
    """Noncitizen share of the uninsured in each adult band: the tract's share (all ages, shrunk to its county) moved by the
    state-and-band odds ratio from the 1-year person file."""
    out = {}
    base = t.noncit_share.clip(1e-4, 1 - 1e-4).to_numpy()
    odds = base / (1 - base)
    key = orr.set_index(["state", "band"]).odds_ratio
    for b in BANDS:
        r = key.xs(b, level="band").reindex(t.state.to_numpy()).to_numpy() * odds_scale
        o = odds * r
        out[b] = o / (1 + o)
    return out


def region_factors(model, t):
    """Region-level ratio of direct total to model total, per target."""
    out = {}
    for tg, mean in model.means.items():
        n = model.n[tg]
        u = t[f"{tg}_u"].to_numpy()
        ok = (n > 0) & ~model.hold
        out[tg] = {r: u[ok & (model.region == r)].sum() / max((mean[ok & (model.region == r)] / 100 * n[ok & (model.region == r)]).sum(), 1.0)
                   for r in model.regions}
    return out


def prepare_model(model, t):
    model.means = {tg: model.mean_rate(tg) for tg in model.fits}
    model.region_f = region_factors(model, t)
    return model


def calibration_factors(model, t, rows, tg):
    """Scale for one county and target, from the unmasked tracts: f = (U + a) / (M + a / f_region)."""
    n = model.n[tg][rows]
    ok = (n > 0) & ~model.hold[rows]
    U = t[f"{tg}_u"].to_numpy()[rows][ok].sum()
    M = (model.means[tg][rows] / 100 * n)[ok].sum()
    return (U + CALIB_PRIOR) / (M + CALIB_PRIOR / model.region_f[tg][model.region[rows[0]]])


def county_counts(model, t, rows, rng, K=K, calibrate=True, draw_rows=None):
    """Calibrated draws of counts (len(draw_rows) x K) for every target, and the calibration factors. rows are all the
    tracts of a county (the calibration uses all of them); draw_rows (default: rows) are the tracts drawn."""
    draw_rows = rows if draw_rows is None else draw_rows
    out, fac = {}, {}
    zu = rng.standard_normal((1, K))  # the county effect is shared by the targets
    for tg in model.fits:
        theta = model.draw(tg, draw_rows, rng, K, zu)  # percent
        f = calibration_factors(model, t, rows, tg) if calibrate else 1.0
        out[tg] = np.minimum(theta * f, 100.0) / 100 * model.n[tg][draw_rows][:, None]
        fac[tg] = f
    return out, fac


def sahie_adjust(cnt, sah, n_rows):
    """Scale groups to the nearest edge of SAHIE's 90% interval when their mean is outside it. Returns the factors."""
    def clamp(total, key):
        pt, moe = sah.get(f"sahie_{key}_u", np.nan), sah.get(f"sahie_{key}_moe", np.nan)
        if not np.isfinite(pt) or not np.isfinite(moe) or total <= 0:
            return 1.0
        lo, hi = max(pt - moe, 0.0), pt + moe
        return 1.0 if lo <= total <= hi else (lo if total < lo else hi) / total
    fac = {}
    mL = cnt["L"].mean(1).sum()
    fac["L"] = clamp(mL, "le138")
    fac["C"] = clamp(cnt["C"].mean(1).sum(), "b138_400")
    fac["kids"] = clamp(cnt["kids"].mean(1).sum(), "kids")
    for tg in ("L", "C", "kids"):
        if fac[tg] != 1.0:
            cnt[tg] = cnt[tg] * fac[tg]
    adults = cnt["L"].mean(1).sum() + cnt["C"].mean(1).sum() + cnt["D"].mean(1).sum()
    pt, moe = sah.get("sahie_all_u", np.nan), sah.get("sahie_all_moe", np.nan)
    fac["D"] = 1.0
    if np.isfinite(pt) and np.isfinite(moe) and adults > 0:
        lo, hi = max(pt - moe, 0.0), pt + moe
        if not lo <= adults <= hi:
            target = lo if adults < lo else hi
            dm = cnt["D"].mean(1).sum()
            if dm > 0:
                fac["D"] = max((target - (adults - dm)) / dm, 0.0)
                cnt["D"] = cnt["D"] * fac["D"]
    return fac


def make_tiers(cnt, frac_A, shares, expansion, state, kid_hi):
    """Tier draws (len(rows) x K) from calibrated band draws. kid_hi: share of each tract's uninsured children at 400%+."""
    cA, cB = cnt["L"] * frac_A[:, None], cnt["L"] * (1 - frac_A)[:, None]
    bands = {"A": cA, "B": cB, "C": cnt["C"], "D": cnt["D"]}
    cit = {b: bands[b] * (1 - shares[b])[:, None] for b in BANDS}
    non = sum(bands[b] * shares[b][:, None] for b in BANDS)
    z = np.zeros_like(cA)
    if expansion:
        medicaid, gap, subsidy = cit["A"] + cit["B"], z, cit["C"]
    elif state in sources.WAIVER_STATES:  # Wisconsin
        medicaid, gap, subsidy = cit["A"], z, cit["B"] + cit["C"]
    else:
        medicaid, gap, subsidy = z, cit["A"], cit["B"] + cit["C"]
    kh = np.asarray(kid_hi)[:, None]
    return {"kids": cnt["kids"] * (1 - kh), "medicaid": medicaid, "subsidy": subsidy, "gap": gap, "d400": cit["D"] + cnt["kids"] * kh, "noncit": non}


def summarize(draws):
    """mean, q05, q50, q95 along axis 1."""
    q = np.quantile(draws, QS, axis=1)
    return draws.mean(1), q[0], q[1], q[2]
