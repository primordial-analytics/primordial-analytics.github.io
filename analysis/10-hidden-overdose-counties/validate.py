"""Validation that can actually be run.

No published cell is 1 to 9, so the suppressed counts cannot be masked and scored. Instead:

1. Pseudo-suppression. Hide every count from 1 to T-1 (T = 20, 30), refit, and score the predictive
   distribution for the counties whose true count (10 to T-1) is known. Only 10 to T-1 can be scored,
   so this tests the upper part of the hidden range, not the whole of it.
2. Temporal. Fit the window ending March 2025 and predict the counties that were published for March 2026.
3. Aggregate. Compare the modelled total of suppressed deaths in each state with the state residual,
   from a model that never saw the residual.
"""
import numpy as np
from scipy.stats import nbinom, poisson, spearmanr

import baselines
import data
import model

LEVELS = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
SEED = 20261022   # each check seeds its own generator, so a cached or partial run reproduces a full one


def thin(eta, n=2000):
    return eta[np.linspace(0, len(eta) - 1, n).astype(int)]


def trunc_pmf_from_draws(eta, offset, hi, chunk=100):
    """Posterior-predictive pmf over k = 1..max(hi) for cells known to lie in 1..hi."""
    kmax = int(hi.max())
    ks = np.arange(1, kmax + 1)
    lg = np.array([np.sum(np.log(np.arange(1, k + 1))) for k in ks])
    out = np.empty((len(hi), kmax))
    for a in range(0, len(hi), chunk):
        mu = np.exp(eta[:, a:a + chunk] + offset[a:a + chunk])            # draws x chunk
        lp = ks[None, None, :] * np.log(mu)[:, :, None] - mu[:, :, None] - lg[None, None, :]
        lp = np.where(ks[None, None, :] <= hi[a:a + chunk][None, :, None], lp, -np.inf)
        lp -= lp.max(2, keepdims=True)
        p = np.exp(lp)
        p /= p.sum(2, keepdims=True)
        out[a:a + chunk] = p.mean(0)
    return out


def score_pmf(pmf, y, rng):
    """pmf over k = 1..K (rows sum to 1); y true counts (1..K). Returns rps, log score, randomized PIT."""
    cdf = np.cumsum(pmf, 1)
    ks = np.arange(1, pmf.shape[1] + 1)[None, :]
    rps = ((cdf - (y[:, None] <= ks)) ** 2).sum(1)
    idx = (y - 1).astype(int)
    py = pmf[np.arange(len(y)), idx]
    logs = np.log(np.maximum(py, 1e-300))
    lower = cdf[np.arange(len(y)), idx] - py
    pit = lower + rng.uniform(size=len(y)) * py
    return rps, logs, pit


def coverage(pit):
    return np.array([(np.abs(pit - 0.5) <= a / 2).mean() for a in LEVELS])


def pseudo_suppression(t, edges, state_totals, T, fit_kw):
    """Hide counts 1..T-1, refit, score the counties whose true count is 10..T-1."""
    rng = np.random.default_rng(SEED + T)
    status = t.status.values.copy()
    pseudo = (status == "exact") & (t.y.values >= 1) & (t.y.values < T)
    status[pseudo] = "censored"
    hi = np.full(len(t), T - 1)
    d = model.prepare(t, edges, status, hi, state_totals, constrain=True)
    fit = model.fit(d, **fit_kw)
    eta = thin(fit["eta"])
    sel = np.where(pseudo)[0]
    offset = d["offset"][sel]
    y = t.y.values[sel].astype(int)
    h = hi[sel]
    pmf_m = trunc_pmf_from_draws(eta[:, sel], offset, h)
    fit_ns = model.fit(d, use_spatial=False, **fit_kw)   # same covariates and state effect, no spatial term
    pmf_n = trunc_pmf_from_draws(thin(fit_ns["eta"])[:, sel], offset, h)
    # Baseline b: non-spatial Poisson-gamma
    mean, alpha = baselines.nb_fit(t["pop"].values, d["sidx"], len(d["states"]), d["exact"],
                                   d["y_exact"], d["cens"], d["hi_cens"])
    pmf_b = baselines.nb_trunc_pmf(mean[sel], alpha, h)
    est_a = baselines.residual_split(t, status, hi, state_totals)[sel]
    ks = np.arange(1, pmf_m.shape[1] + 1)[None, :]
    rows, pits = {}, {}
    rate = y / t["pop"].values[sel] * 1e5
    for name, pmf in (("spatial", pmf_m), ("covariates_only", pmf_n), ("poisson_gamma", pmf_b)):
        rps, logs, pit = score_pmf(pmf, y, rng)
        e = (pmf * ks).sum(1)
        rows[name] = dict(rps=float(rps.mean()), log_score=float(logs.mean()),
                          mae=float(np.abs(e - y).mean()),
                          spearman=float(spearmanr(e / t["pop"].values[sel], rate).statistic),
                          coverage=coverage(pit).tolist())
        pits[name] = pit
    ok = ~np.isnan(est_a)
    rows["residual_split"] = dict(mae=float(np.abs(est_a[ok] - y[ok]).mean()),
                                  spearman=float(spearmanr(est_a[ok] / t["pop"].values[sel][ok], rate[ok]).statistic))
    mid = (1 + h) / 2
    rows["midpoint"] = dict(mae=float(np.abs(mid - y).mean()))
    return dict(T=T, n_scored=int(len(sel)), n_hidden=int((status == "censored").sum()), models=rows,
                constrained_states=int(len(d["con_state"])), fit={k: v for k, v in fit.items()
                                                                 if k not in ("eta", "params", "names")})


def _trunc_poisson_draws(mu, u):
    """Inverse-cdf draws of Poisson(mu) conditioned on the set {0} U {10, 11, ...} (what NCHS publishes)."""
    f0 = np.exp(-mu)
    f9 = poisson.cdf(9, mu)
    mass = f0 + (1 - f9)
    v = u * mass
    low = v < f0
    out = np.where(low, 0, poisson.ppf(np.clip(f9 + (v - f0), 0, 1 - 1e-12), mu))
    return out


def crps_samples(x, y):
    """Sample CRPS for each column of x (draws x counties) against y."""
    n = x.shape[0]
    xs = np.sort(x, axis=0)
    term1 = np.abs(xs - y[None, :]).mean(0)
    w = (2 * np.arange(1, n + 1) - n - 1)[:, None]
    term2 = (w * xs).sum(0) / n ** 2
    return term1 - term2


def temporal(t26, t25, edges, st25, st26, fit_kw):
    """Fit March 2025; predict the counties published for March 2026."""
    rng = np.random.default_rng(SEED + 1)
    d = model.prepare(t25, edges, t25.status.values, np.full(len(t25), 9), st25, constrain=True)
    fit = model.fit(d, **fit_kw)
    eta = thin(fit["eta"])
    pub = (t26.status.values == "exact") & (t26.index.isin(t25.index))
    sel = np.where(pub)[0]
    y = t26.y.values[sel]
    trend = (st26 / st25).reindex(t26.state.iloc[sel]).values
    popratio = t26["pop"].values[sel] / t25["pop"].reindex(t26.index[sel]).values
    base = np.exp(eta[:, sel] + d["offset"][sel]) * popratio
    u = rng.uniform(size=base.shape)
    res = {}
    for name, factor in (("spatial_no_trend", 1.0), ("spatial_state_trend", trend)):
        mu = base * factor
        x = _trunc_poisson_draws(mu, u)
        pit = (x < y).mean(0) + rng.uniform(size=len(y)) * (x == y).mean(0)
        res[name] = dict(crps=float(crps_samples(x, y.astype(float)).mean()),
                         mae=float(np.abs(np.median(x, 0) - y).mean()),
                         coverage=coverage(pit).tolist(),
                         cov90_interval=float(((np.quantile(x, 0.05, 0) <= y) & (y <= np.quantile(x, 0.95, 0))).mean()))
    # Non-spatial Poisson-gamma: each county's 2025 rate is its state-level gamma prior updated by its own 2025 count.
    mean, alpha = baselines.nb_fit(t25["pop"].values, d["sidx"], len(d["states"]), d["exact"],
                                   d["y_exact"], d["cens"], d["hi_cens"])
    k25 = t25.index.get_indexer(t26.index[sel])
    n_draw = base.shape[0]
    mu25 = np.empty(base.shape)
    for col, k in enumerate(k25):
        m, st, y25 = mean[k], t25.status.values[k], t25.y.values[k]
        if st == "exact":
            mu25[:, col] = rng.gamma(alpha + y25, 1 / (alpha / m + 1), size=n_draw)
        else:
            prior = rng.gamma(alpha, m / alpha, size=4000)
            w = poisson.cdf(9, prior) - np.exp(-prior) if st == "censored" else np.ones(4000)
            mu25[:, col] = rng.choice(prior, size=n_draw, p=w / w.sum())
    x = _trunc_poisson_draws(mu25 * popratio * trend, rng.uniform(size=base.shape))
    ok = t25.status.values[k25] == "exact"
    pit = (x < y).mean(0) + rng.uniform(size=len(y)) * (x == y).mean(0)
    res["poisson_gamma_state_trend"] = dict(crps=float(crps_samples(x, y.astype(float)).mean()),
                                            mae=float(np.abs(np.median(x, 0) - y).mean()),
                                            mae_same_counties=float(np.abs(np.median(x, 0)[ok] - y[ok]).mean()),
                                            coverage=coverage(pit).tolist(),
                                            cov90_interval=float(((np.quantile(x, 0.05, 0) <= y) & (y <= np.quantile(x, 0.95, 0))).mean()))
    # naive: last year's published count carried forward with the state trend, on counties published both years
    naive = t25.y.values[k25] * popratio * trend
    xt = _trunc_poisson_draws(base * trend, rng.uniform(size=base.shape))
    res["last_year_state_trend"] = dict(mae=float(np.abs(naive[ok] - y[ok]).mean()), n=int(ok.sum()),
                                        spatial_mae_same_counties=float(np.abs(np.median(xt, 0)[ok] - y[ok]).mean()))
    res["n_scored"] = int(len(sel))
    res["fit"] = {k: v for k, v in fit.items() if k not in ("eta", "params", "names")}
    return res


def aggregate(t, fit_eta, d, state_totals, hi_cap=9):
    """Modelled total of suppressed deaths per state against the state residual (model did not use it)."""
    rng = np.random.default_rng(SEED + 2)
    eta = thin(fit_eta, 1000)
    ce = d["cens"]
    mu = np.exp(eta[:, ce] + d["offset"][ce])
    f0 = np.exp(-mu)
    f9 = poisson.cdf(hi_cap, mu)
    u = rng.uniform(size=mu.shape)
    ydraw = poisson.ppf(np.clip(f0 + u * (f9 - f0), 0, 1 - 1e-12), mu)
    ydraw = np.maximum(ydraw, 1)
    states = t.state.values[ce]
    pub = t[t.status == "exact"].groupby("state").y.sum()
    rows = []
    for s in sorted(set(states)):
        m = states == s
        tot = ydraw[:, m].sum(1)
        resid = state_totals[s] - pub.get(s, 0.0)
        n = int(m.sum())
        rows.append(dict(state=s, n_suppressed=n, residual=float(resid), model_median=float(np.median(tot)),
                         model_lo90=float(np.quantile(tot, 0.05)), model_hi90=float(np.quantile(tot, 0.95)),
                         within_bounds=bool(n <= resid <= 9 * n),
                         has_dq=bool(((t.state == s) & (t.status == "missing")).any())))
    return rows
