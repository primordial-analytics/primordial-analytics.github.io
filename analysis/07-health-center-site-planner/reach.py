"""Reach accounting: patients per ZIP (with the censored cells placed), low-income residents who are not patients, payer mix.

Everything here is observed counts plus two sources of uncertainty that are sampled, not assumed away:
the censored HRSA cells (hidden.py, exact center sums) and the ACS margins of error (Monte Carlo, below).
"""
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

import hidden
import model

MC_DRAWS = 2000
ACS_STATE_CORR = 0.25  # assumed correlation of ACS errors between ZCTAs of one state (the Census approximation uses 0)
DEFAULT_CELL_LAMBDA = 4.0
SMALL_LOW_INCOME = 1000
CAMPUS_COLLEGE_PCT = 20  # ZCTAs where college students are this share of residents or more: about the top 2.5%


def place_hidden(d, data, x, prior="poisson"):
    """Sample the censored cells with the fitted expectation as the prior. Returns (hidden rows, draws y, centers with bad sums)."""
    rows = d["rows"]
    hid = rows[rows.hid_total]
    lam, _ = model.expected(x, model.arrays(data))
    pair = pd.Series(lam, index=pd.MultiIndex.from_arrays([data.ent.index[data.c], data.zcta.index[data.z]]))
    key = pd.MultiIndex.from_arrays([hid.grant, hid.zcta])
    lam_row = pair.reindex(key).to_numpy()
    lam_row = np.where(np.isnan(lam_row), DEFAULT_CELL_LAMBDA, lam_row)
    y, bad = hidden.sample_all(hid.reset_index(drop=True), lam_row, d["centers"], draws=hidden.DRAWS, prior=prior)
    return hid, y, bad


def patients_by_zcta(d, hid, y, national_low_share):
    """Visible plus placed patients per ZCTA, as draws. Returns dict of arrays aligned to d['zcta'].index."""
    rows, cen, zcta = d["rows"], d["centers"], d["zcta"]
    zi = pd.Series(np.arange(len(zcta)), index=zcta.index)
    share = rows.grant.map(cen.low_share).fillna(national_low_share).to_numpy()
    mapped = rows.zcta.notna().to_numpy()
    zrow = zi.reindex(rows.zcta).to_numpy()
    vis = rows.total.fillna(0).to_numpy()
    n = len(zcta)
    vis_tot = np.bincount(zrow[mapped].astype(int), vis[mapped], minlength=n)
    vis_low = np.bincount(zrow[mapped].astype(int), (vis * share)[mapped], minlength=n)
    hz = zi.reindex(hid.zcta).to_numpy()
    sel = ~np.isnan(hz)
    hs = share_for(hid, cen, national_low_share)
    M = sp.csr_matrix((np.ones(sel.sum()), (hz[sel].astype(int), np.flatnonzero(sel))), shape=(n, len(hid)))
    Ml = sp.csr_matrix((hs[sel], (hz[sel].astype(int), np.flatnonzero(sel))), shape=(n, len(hid)))
    return {"total": vis_tot[:, None] + M @ y, "low": vis_low[:, None] + Ml @ y, "hidden_mean": np.asarray(M @ y.mean(axis=1)).ravel()}


def share_for(hid, cen, national):
    return hid.grant.map(cen.low_share).fillna(national).to_numpy()


def payer_counts(d, hid, y):
    """Expected patients by payer per ZCTA (n x 4), hidden payer cells filled from row totals, in expectation."""
    rows, cen, zcta = d["rows"], d["centers"], d["zcta"]
    zi = pd.Series(np.arange(len(zcta)), index=zcta.index)
    r = rows[rows.zcta.notna()].copy()
    tot = r.total.to_numpy(float).copy()
    hm = pd.Series(y.mean(axis=1), index=hid.index)
    hidden_tot = r.hid_total.to_numpy()
    tot[hidden_tot] = hm.reindex(r.index[hidden_tot]).to_numpy()
    pat = cen[["pay_uninsured", "pay_medicaid", "pay_medicare", "pay_private"]]
    pat = (pat.div(pat.sum(axis=1).replace(0, np.nan), axis=0)).fillna(0.25)
    pattern = pat.reindex(r.grant).to_numpy()
    est = hidden.fill_payers(r, np.nan_to_num(tot), pattern)
    z = zi.reindex(r.zcta).to_numpy().astype(int)
    out = np.zeros((len(zcta), 4))
    for j in range(4):
        out[:, j] = np.bincount(z, est[:, j], minlength=len(zcta))
    return out


def shrunk_payer_mix(zcta, counts):
    """Dirichlet-multinomial shrinkage toward the state-by-density-class mix. kappa (prior patients) is fit by maximum likelihood."""
    grp = zcta.state.fillna("NA") + "_" + zcta.dclass.astype(str)
    gsum = pd.DataFrame(counts).groupby(grp.to_numpy()).transform("sum").to_numpy()
    nat_class = pd.DataFrame(counts).groupby(zcta.dclass.to_numpy()).transform("sum").to_numpy()
    gtot = gsum.sum(axis=1, keepdims=True)
    gmix = np.where(gtot >= 500, gsum / np.maximum(gtot, 1), nat_class / nat_class.sum(axis=1, keepdims=True))
    n = counts.sum(axis=1)
    use = n >= 1

    def nll(lk):
        k = np.exp(lk)
        a = k * gmix[use]
        c = counts[use]
        ll = gammaln(k) - gammaln(n[use] + k) + (gammaln(c + a) - gammaln(a)).sum(axis=1)
        return -ll.sum()

    res = minimize_scalar(nll, bounds=(np.log(0.5), np.log(5000)), method="bounded")
    kappa = float(np.exp(res.x))
    mix = (counts + kappa * gmix) / (n[:, None] + kappa)
    return mix, kappa, gmix


def acs_draws(zcta, n=MC_DRAWS, rho=ACS_STATE_CORR, seed=7):
    """Draws of low-income residents (n_zcta x n, float32) and of uninsured adults below 200%.
    One state-level normal factor per draw is shared by that state's ZCTAs (weight rho), the rest is independent."""
    rng = np.random.default_rng(seed)
    states = zcta.state.fillna("NA")
    codes, uniq = pd.factorize(states)
    g = rng.standard_normal((len(uniq), n)).astype(np.float32)
    out = []
    for col, se in (("low", "low_se"), ("unins_adult_low", "unins_se")):
        e = rng.standard_normal((len(zcta), n)).astype(np.float32)
        xi = np.sqrt(rho) * g[codes] + np.sqrt(1 - rho) * e
        out.append(np.clip(zcta[col].to_numpy(np.float32)[:, None] + zcta[se].to_numpy(np.float32)[:, None] * xi, 0, None))
    return out


def quantiles(a, qs=(0.1, 0.5, 0.9)):
    return np.quantile(a, qs, axis=1)


def reach_tables(d, patients, L_draws, U_draws):
    """The ZIP-level reach table and the national aggregates with 80% intervals."""
    zcta = d["zcta"]
    low = patients["low"].astype(np.float32)
    k = low.shape[1]
    idx = np.arange(L_draws.shape[1]) % k
    lowd = low[:, idx]
    pen = lowd / np.maximum(L_draws, 1)
    notp = np.clip(L_draws - lowd, 0, None)
    out = pd.DataFrame(index=zcta.index)
    q = quantiles(pen)
    out["pen_p10"], out["pen_p50"], out["pen_p90"] = q
    q = quantiles(notp)
    out["notpat_p10"], out["notpat_p50"], out["notpat_p90"] = q
    out["patients_total"] = patients["total"].mean(axis=1)
    out["patients_low"] = low.mean(axis=1)
    small = (zcta.low < SMALL_LOW_INCOME).to_numpy()
    out["small"] = small
    out["campus"] = (zcta.college_pct >= CAMPUS_COLLEGE_PCT).to_numpy()
    return out, pen, notp, lowd
