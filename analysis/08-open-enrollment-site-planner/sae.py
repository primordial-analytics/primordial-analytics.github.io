"""Small-area model for tract counts of uninsured people: an area-level Fay-Herriot model on the rate scale.

For each target (children; adults under 100%, 100-137%, 138-399%, 400% and over) and each Census region:

    direct rate y_i = theta_i + e_i,   e_i ~ N(0, d_i)          (the survey's sampling error)
    theta_i = x_i b + u_county(i) + v_i,  u ~ N(0, su2),  v ~ N(0, sv2)

The rate is in percent. d_i comes from a generalized variance function (GVF): the survey's weight per unit W in
var(count) = W x count, fit on log W against log cell size and log(1 - rate); a cell with a usable published standard
error keeps its own W between the function's 25th percentile and three times its mean. Cells that report zero, or a zero
standard error, take the GVF value (a published margin on a zero count is the same survey-wide constant, not information
about the tract). Variance parameters are fit by REML with the county effect handled through Sherman-Morrison, so a fit is
a two-parameter search. The tract variance is weakly identified, so the model uses the upper end of its one-sided 95%
profile-likelihood interval (found by root finding). Posterior draws of theta come from the conditional normal of v given
u, with u drawn from its conditional normal and b from its estimated sampling distribution, and are clipped to [0, 100]
percent, then multiplied by the cell population. The coefficient draws and the county effect are shared across targets so
that the sum of children, adults at or below 138% and adults 138-399% has the spread of a sum of related things.

Everything here works on arrays so it can be re-used by the validation: the holdout (rows with no data), the
parametric simulation (replacement y and standard errors) and the refit without SAHIE.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from common import TARGETS

COV_BASE = ["places", "places_missing", "sahie", "noncit_share", "pov138_share", "expansion", "dens1", "dens2", "logn", "logn2", "sharen", "spatial"]


class Fit:
    """One fitted model: target x region."""
    pass


class WeightFactor:
    """The survey's 'weight per unit' W in var(count) = W x count (a scaled Poisson, with a binomial correction), as a function
    of cell size n and rate p: log W = a + b log n + c log(1 - p), fit on the cells with a usable published SE (a positive
    count and SE) from W = SE^2 / count. Unlike SE^2 / (n p (1 - p)), this does not divide by the cell's own rate, so
    choosing cells with a positive count does not tilt it. Called with (n, p) it returns (floor, expected): the 25th
    percentile and the mean of the fitted lognormal."""

    def __init__(self, u, se, n):
        ok = (u > 0) & (se > 0) & (n > 0) & (u < n)
        W = se[ok] ** 2 / u[ok]
        F = np.column_stack([np.ones(ok.sum()), np.log(n[ok]), np.log1p(-np.clip(u[ok] / n[ok], 0, 0.99))])
        z = np.log(W)
        self.coef, *_ = np.linalg.lstsq(F, z, rcond=None)
        self.resid_var = float((z - F @ self.coef).var())
        self.n_fit = int(ok.sum())

    def __call__(self, n, p):
        base = self.coef[0] + self.coef[1] * np.log(np.maximum(n, 1)) + self.coef[2] * np.log1p(-np.clip(p, 0, 0.99))
        return np.exp(base - 0.674 * np.sqrt(self.resid_var)), np.exp(base + self.resid_var / 2)


def sampling_variance(u, se, n, county=None, gvf=None, valid=None):
    """Variance d_i (percent squared) of each cell's rate, and the flag for cells with no usable published SE.

    var(count) = W x count, so var(rate) = W p / n with p the cell's true rate. The cell's own rate is not used (a published
    SE moves with it, and weighting by it shrinks high-rate tracts too hard); p is the county's pooled rate. W comes from the
    cells that have a usable published SE (a function of cell size and rate, a generalized variance function) and is used for
    every cell: a zero count or a zero SE gets the same W as any cell of its size, because the published margin on a zero is a
    survey-wide constant. A cell with a usable SE keeps its own W if it lies between the function's 25th percentile and three
    times its mean. `valid` marks the cells whose data may be used (the holdout withholds the others from the function and from
    the county's pooled rate)."""
    n = np.asarray(n, float)
    u, se = np.asarray(u, float), np.asarray(se, float)
    valid = np.ones(len(u), bool) if valid is None else valid
    if gvf is None:
        gvf = WeightFactor(u[valid], se[valid], n[valid])
    cu = pd.Series(np.where(valid, u, 0.0)).groupby(county).transform("sum").to_numpy()
    cn = pd.Series(np.where(valid, n, 0.0)).groupby(county).transform("sum").to_numpy()
    ps = np.clip(np.where(cn > 0, cu / np.maximum(cn, 1), 0.05), 0.002, 0.95)
    floor, expected = gvf(n, ps)
    usable = (u > 0) & (se > 0) & (n > 0)
    W = np.where(usable, np.clip(se ** 2 / np.maximum(u, 1e-9), floor, 3 * expected), expected)
    return 1e4 * W * ps / np.maximum(n, 1), ~usable, gvf


def spatial_term(u, n, nbr, valid):
    """Pooled direct rate (percent) of the six nearest tracts that have data; falls back to the tract's county rate."""
    uu = np.where(valid, u, 0.0)
    nn = np.where(valid, n, 0.0)
    num, den = uu[nbr].sum(1), nn[nbr].sum(1)
    return 100 * np.where(den > 0, num / np.maximum(den, 1), np.nan)


def design(t, tg, spatial, use_sahie=True):
    n = t[f"{tg}_n"].to_numpy(float)
    sah = t[f"sahie_{tg}"].copy()
    sah = sah.fillna(sah.groupby(t.state).transform("mean")).fillna(sah.mean())
    cols = {"places": 100 * t.places.to_numpy(), "places_missing": t.places_missing.to_numpy(float),
            "sahie": 100 * sah.to_numpy(), "noncit_share": 100 * t.noncit_share.to_numpy(), "pov138_share": 100 * t.pov138_share.to_numpy(),
            "expansion": t.expansion.to_numpy(float), "dens1": (t.density_class.to_numpy() == 1).astype(float),
            "dens2": (t.density_class.to_numpy() == 2).astype(float), "spatial": spatial,
            "logn": np.log1p(n), "logn2": np.log1p(n) ** 2, "sharen": 100 * n / np.maximum(t.pop_all.to_numpy(float), 1)}
    names = [c for c in COV_BASE if use_sahie or c != "sahie"]
    X = np.column_stack([np.ones(len(t))] + [cols[c] for c in names])
    return X, ["const"] + names


def _county_sums(x, starts):
    return np.add.reduceat(x, starts, axis=0)


def _reml_terms(params, y, d, X, XX, starts):
    sv2, su2, phi = np.exp(params)
    d = phi * d
    w = 1.0 / (sv2 + d)
    s = _county_sums(w, starts)
    sx = _county_sums(w[:, None] * X, starts)
    sy = _county_sums(w * y, starts)
    gam = su2 / (1 + su2 * s)
    p = X.shape[1]
    xtvx = _county_sums(w[:, None] * XX, starts).sum(0).reshape(p, p) - (gam[:, None, None] * sx[:, :, None] * sx[:, None, :]).sum(0)
    xtvy = _county_sums(w[:, None] * X * y[:, None], starts).sum(0) - (gam[:, None] * sx * sy[:, None]).sum(0)
    ytvy = (w * y * y).sum() - (gam * sy * sy).sum()
    xtvx = xtvx + 1e-8 * np.eye(p)  # a covariate that is constant inside a region (e.g. expansion) has a zero column
    beta = np.linalg.solve(xtvx, xtvy)
    quad = ytvy - beta @ xtvy
    logdet = np.log(sv2 + d).sum() + np.log1p(su2 * s).sum()
    return beta, xtvx, quad, logdet


def _neg_reml(params, y, d, X, XX, starts):
    if np.any(np.abs(params) > 30) or abs(params[2]) > 2.5:
        return 1e18
    beta, xtvx, quad, logdet = _reml_terms(params, y, d, X, XX, starts)
    sign, ld = np.linalg.slogdet(xtvx)
    return 0.5 * (logdet + ld + quad)


def upper_sv2(best, ys, ds, Zs, ZZ, starts, drop=1.353):
    """Tract-level variance is weakly identified: sampling noise is ten times larger. Return the log of the largest value
    whose profile REML (county variance re-optimised) is within `drop` of the best (the one-sided 95% likelihood-ratio
    bound), by root finding between the REML value and the total variance of the rates."""
    from scipy.optimize import brentq, minimize_scalar
    nll0 = best.fun
    lo = best.x[0]
    top = np.log(max(np.var(ys), 1e-6))  # no more than the total variance of the rates

    def excess(v):
        res = minimize_scalar(lambda ls: _neg_reml(np.array([v, ls, 0.0]), ys, ds, Zs, ZZ, starts), bounds=(best.x[1] - 4, best.x[1] + 4), method="bounded",
                              options={"xatol": 0.05})
        return res.fun - nll0 - drop

    if top <= lo:
        return lo
    if excess(top) <= 0:
        return top
    return brentq(excess, lo, top, xtol=0.02)


def fit_region(y, d, X, county, hold, max_rows=9000, seed=0):
    """REML fit on rows that are not held out. The two variance parameters are searched on a random subset of whole
    counties (about max_rows tracts), then the coefficients are re-estimated by GLS on every kept row. Returns a Fit with
    the posterior ingredients for ALL rows."""
    keep = ~hold
    yk, dk, Xk, ck = y[keep], d[keep], X[keep], county[keep]
    starts = np.flatnonzero(np.r_[True, ck[1:] != ck[:-1]])
    mu, sd = Xk[:, 1:].mean(0), Xk[:, 1:].std(0) + 1e-9
    Z = np.column_stack([np.ones(len(X)), (X[:, 1:] - mu) / sd])
    Zk = Z[keep]
    sizes = np.diff(np.r_[starts, len(ck)])
    gid = np.repeat(np.arange(len(starts)), sizes)
    if len(ck) > max_rows:
        rng = np.random.default_rng(seed)
        pick = rng.random(len(starts)) < max_rows / len(ck)
        sub = pick[gid]
    else:
        sub = np.ones(len(ck), bool)
    ys, ds, Zs, cs = yk[sub], dk[sub], Zk[sub], ck[sub]
    starts_s = np.flatnonzero(np.r_[True, cs[1:] != cs[:-1]])
    ZZ = (Zs[:, :, None] * Zs[:, None, :]).reshape(len(Zs), -1)
    v0 = max(np.var(ys) * 0.3, 0.05)
    # The scale on the sampling variances is fixed at 1: the GVF is fit on tens of thousands of cells, and a free scale trades
    # off against the tract-level variance (the two cannot be told apart when sampling noise dominates).
    r = minimize(lambda p2: _neg_reml(np.r_[p2, 0.0], ys, ds, Zs, ZZ, starts_s), [np.log(v0), np.log(v0 * 0.3)], method="Nelder-Mead",
                 options={"xatol": 1e-3, "fatol": 1e-3, "maxiter": 200})
    best = r
    best.x = np.r_[r.x, 0.0]
    reml_sv2 = float(np.exp(best.x[0]))  # the REML point estimate, before it is replaced by the upper bound
    best.x[0] = max(upper_sv2(best, ys, ds, Zs, ZZ, starts_s), best.x[0])
    ZZk = (Zk[:, :, None] * Zk[:, None, :]).reshape(len(Zk), -1)
    params = best.x.copy()

    def moments(params):
        sv2, su2, phi = np.exp(params)
        beta, xtvx, quad, logdet = _reml_terms(params, yk, dk, Zk, ZZk, starts)
        dd = phi * dk
        w = 1.0 / (sv2 + dd)
        r = yk - Zk @ beta
        inv_k = np.repeat(np.arange(len(starts)), sizes)
        u_k = (np.bincount(inv_k, weights=w * r) / (1.0 / su2 + np.bincount(inv_k, weights=w)))[inv_k]
        return beta, xtvx, (r - u_k), dd

    # The best-measured quarter of tracts shows variation beyond sampling error, so the variance is floored at that moment estimate.
    beta, xtvx, res, dd = moments(params)
    best_q = dd <= np.quantile(dd, 0.25)
    mom = float(np.mean(res[best_q] ** 2 - dd[best_q]))
    if mom > np.exp(params[0]):
        params[0] = np.log(mom)
        beta, xtvx, res, dd = moments(params)
    sv2, su2, phi = np.exp(params)
    d = phi * d  # the fitted scale on the sampling variances is carried into everything below
    f = Fit()
    f.sv2, f.su2, f.phi, f.beta, f.cov_beta = sv2, su2, phi, beta, np.linalg.inv(xtvx)
    f.Z, f.mu, f.sd = Z, mu, sd
    # posterior ingredients for every row (held-out rows carry no data: weight 0)
    w = np.where(hold, 0.0, 1.0 / (sv2 + d))
    f.w = w
    f.xb = Z @ beta
    r = y - f.xb
    uc, inv = np.unique(county, return_inverse=True)
    f.inv = inv
    sw = np.bincount(inv, weights=w)
    swr = np.bincount(inv, weights=w * np.where(hold, 0.0, r))
    prec = 1.0 / su2 + sw
    f.u_mean, f.u_sd = (swr / prec)[inv], np.sqrt(1.0 / prec)[inv]
    pv = 1.0 / (1.0 / sv2 + np.where(hold, 0.0, 1.0 / d))
    f.v_var = pv
    f.v_gain = np.where(hold, 0.0, pv / d)  # v | y, u has mean gain * (r - u)
    f.r = np.where(hold, 0.0, r)
    f.y, f.d, f.hold = y, d, hold
    f.reml, f.reml_sv2 = float(best.fun), reml_sv2
    return f


def draw_theta(f, rows, B, rng, K, zu=None):
    """Posterior draws (len(rows) x K) of the true rate in percent, clipped to [0, 100]. rows are positions inside the
    region fit; tracts of the same county share one draw of the county effect (zu: its standard-normal draws, 1 x K, when the
    caller shares them across targets). B is K x p draws of the coefficients."""
    xb = f.Z[rows] @ B.T
    groups, gi = np.unique(f.inv[rows], return_inverse=True)
    Zu = rng.standard_normal((len(groups), K)) if zu is None else zu
    assert len(groups) == Zu.shape[0]
    U = f.u_mean[rows][:, None] + f.u_sd[rows][:, None] * Zu[gi]
    mean_v = f.v_gain[rows, None] * (f.r[rows, None] - U)
    V = mean_v + np.sqrt(f.v_var[rows])[:, None] * rng.standard_normal((len(rows), K))
    th = xb + U + V
    return np.clip(th, 0.0, 100.0)


def beta_draws(f, E):
    """Coefficient draws from standard normals E (K x p); the same E is used for every target of a region."""
    L = np.linalg.cholesky(f.cov_beta + 1e-12 * np.eye(len(f.beta)))
    return f.beta[None, :] + E @ L.T


class Model:
    """The target models over four regions for one tract table."""

    def __init__(self, t, nbr):
        self.t, self.nbr = t, nbr
        self.county = t.county.to_numpy()
        self.region = t.region.to_numpy()
        self.regions = sorted(set(self.region))
        self.n = {tg: t[f"{tg}_n"].to_numpy(float) for tg in TARGETS}

    def fit(self, hold=None, u=None, se=None, use_sahie=True, gvf=None, verbose=False):
        """hold: bool array of tracts whose data are withheld. u, se: replacement direct counts and standard errors per target."""
        t = self.t
        hold = np.zeros(len(t), bool) if hold is None else hold
        self.fits, self.gvf, self.y, self.d, self.zero_flag, self.use_sahie, self.hold = {}, {}, {}, {}, {}, use_sahie, hold
        for tg in TARGETS:
            n = self.n[tg]
            ut = t[f"{tg}_u"].to_numpy(float) if u is None else u[tg]
            st = t[f"{tg}_se"].to_numpy(float) if se is None else se[tg]
            h = hold | (n <= 0)
            d, zflag, g = sampling_variance(ut, st, n, self.county, None if gvf is None else gvf[tg], valid=~h)
            rate = np.where(n > 0, ut / np.maximum(n, 1), 0.0)
            y = 100 * rate
            sp = spatial_term(ut, n, self.nbr, ~h)
            cr = pd.Series(np.where(h, np.nan, rate * n)).groupby(self.county).transform("sum") / pd.Series(np.where(h, np.nan, n)).groupby(self.county).transform("sum")
            sp = np.where(np.isnan(sp), 100 * cr.fillna(rate[~h].mean()), sp)
            X, self.names = design(t, tg, sp, use_sahie)
            self.gvf[tg], self.y[tg], self.d[tg], self.zero_flag[tg] = g, y, d, zflag
            self.fits[tg] = {}
            for r in self.regions:
                rows = np.flatnonzero(self.region == r)
                f = fit_region(y[rows], d[rows], X[rows], self.county[rows], h[rows])
                f.rows = rows
                self.fits[tg][r] = f
            if verbose:
                print(f"  fit {tg}: " + " ".join(f"{r}: sv2={self.fits[tg][r].sv2:.3g} su2={self.fits[tg][r].su2:.3g} phi={self.fits[tg][r].phi:.2f}" for r in self.regions), flush=True)
        return self

    def start_draws(self, rng, K):
        E = {r: rng.standard_normal((K, len(self.names))) for r in self.regions}
        self.B = {tg: {r: beta_draws(self.fits[tg][r], E[r]) for r in self.regions} for tg in TARGETS}

    def draw(self, tg, rows, rng, K, zu=None):
        """Draw rate (percent) for global tract positions rows, all in one county. Returns len(rows) x K."""
        r = self.region[rows[0]]
        f = self.fits[tg][r]
        local = np.searchsorted(f.rows, rows)
        return draw_theta(f, local, self.B[tg][r], rng, K, zu)

    def mean_rate(self, tg):
        """Posterior mean rate in percent (clipping at 0 and 100 ignored beyond the clip of the mean)."""
        out = np.zeros(len(self.t))
        for r, f in self.fits[tg].items():
            out[f.rows] = np.clip(f.xb + f.u_mean + f.v_gain * (f.r - f.u_mean), 0, 100)
        return out
