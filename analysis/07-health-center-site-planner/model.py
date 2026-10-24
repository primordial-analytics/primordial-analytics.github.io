"""Competitive gravity model of where health center patients live, fit by maximum likelihood in JAX.

Expected patients from ZCTA z to center c:  lam_cz = L_z * theta_c * f_k(d_cz) / (1 + S_z),  S_z = sum_c' theta_c' f_k(d_c'z).
d is straight-line miles from the ZCTA centroid to the center's nearest permanent site, f_k(d) = exp(-(d/rho_k)^gamma_k) with
one (rho, gamma) per density class k of the ZCTA, and log theta_c = mu_type + beta log(sites_c) + sigma_type * eps_c.
The '1' in the denominator is the outside option: people who use no health center.
"""
import os

os.environ.setdefault("XLA_FLAGS", "--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=1")

import jax
import jax.numpy as jnp
import numpy as np
import pandas as pd
from jax.scipy.special import gammaincc
from scipy.optimize import minimize
from scipy.spatial import cKDTree

jax.config.update("jax_enable_x64", True)

MILES = 3958.8
RADIUS = 60.0  # miles: pairs farther than this are dropped
D_FLOOR = 0.1
BIG_CELL = 30  # visible patients above which a partly hidden merged cell is treated as exact
TYPES = ["chc", "special"]
SEED = 20261023


def xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]


def miles_between(lat1, lon1, lat2, lon2):
    a, b = xyz(lat1, lon1), xyz(lat2, lon2)
    return 2 * MILES * np.arcsin(np.clip(np.linalg.norm(a - b, axis=-1) / 2, 0, 1))


# ------------------------------------------------------------------ data assembly
class Data:
    """Entities (centers with at least one usable site), pairs within RADIUS and the cells observed on them."""

    def __init__(self, zcta, centers, lookalikes, sites, cells, radius=RADIUS):
        self.zcta = zcta
        self.zidx = pd.Series(np.arange(len(zcta)), index=zcta.index)
        ent = pd.concat([centers[centers.n_sites.notna()].assign(lookalike=False),
                         lookalikes[["name", "state", "type", "n_sites", "lookalike"]]])
        ent = ent[ent.index.isin(sites.grant)]
        self.ent = ent
        self.eidx = pd.Series(np.arange(len(ent)), index=ent.index)
        self.n_sites = ent.n_sites.to_numpy(float)
        self.lnn_ref = np.log(self.n_sites[~ent.lookalike.to_numpy().astype(bool)]).mean()
        self.lnn = np.log(self.n_sites) - self.lnn_ref
        self.type = (ent.type != "chc").to_numpy(int)
        self.free = (~ent.lookalike).to_numpy(float)
        self.dclass = zcta.dclass.to_numpy(int)
        self.L = zcta.low.to_numpy(float)
        self.sites = sites[sites.grant.isin(ent.index)].reset_index(drop=True)
        pairs = self._pairs(radius)
        self.c, self.z, self.d = (pairs[k].to_numpy() for k in ("c", "z", "d"))
        self.k = self.dclass[self.z]
        self._cells(cells)

    def _pairs(self, radius):
        tz = cKDTree(xyz(self.zcta.lat.to_numpy(), self.zcta.lon.to_numpy()))
        ts = cKDTree(xyz(self.sites.lat.to_numpy(), self.sites.lon.to_numpy()))
        m = ts.sparse_distance_matrix(tz, 2 * np.sin(radius / MILES / 2), output_type="ndarray")
        df = pd.DataFrame({"c": self.eidx.reindex(self.sites.grant).to_numpy()[m["i"]], "z": m["j"],
                           "d": 2 * MILES * np.arcsin(np.clip(m["v"] / 2, 0, 1))})
        return df.groupby(["c", "z"], as_index=False).d.min().sort_values(["c", "z"]).reset_index(drop=True)

    def _cells(self, cells):
        """Merge HRSA ZIP rows that share a ZCTA; lo and hi bound each pair's patient count (censored cells are 1 to 15)."""
        g = cells[cells.grant.isin(self.eidx.index)].groupby(["grant", "zcta"]).agg(
            V=("total", lambda s: s.fillna(0).sum()), nh=("hid_total", "sum")).reset_index()
        g["c"] = self.eidx.reindex(g.grant).to_numpy()
        g["z"] = self.zidx.reindex(g.zcta).to_numpy()
        key = pd.Series(np.arange(len(self.c)), index=pd.MultiIndex.from_arrays([self.c, self.z]))
        pos = key.reindex(pd.MultiIndex.from_arrays([g.c, g.z])).to_numpy()
        self.cells_total = g
        self.cells_outside = g[np.isnan(pos)]
        g, pos = g[~np.isnan(pos)], pos[~np.isnan(pos)].astype(int)
        self.lo = np.zeros(len(self.c))
        self.hi = np.zeros(len(self.c))
        self.lo[pos] = g.V.to_numpy() + g.nh.to_numpy()
        self.hi[pos] = g.V.to_numpy() + 15 * g.nh.to_numpy()
        # A merged cell with a large visible part is treated as exact at the midpoint: the hidden part cannot matter there.
        big = np.zeros(len(self.c), bool)
        big[pos] = g.V.to_numpy() >= BIG_CELL
        self.lo[big] = self.hi[big] = (self.lo[big] + self.hi[big]) / 2
        self.cell_pos = pos
        self.cell_row = g.index.to_numpy()
        self.censored = np.flatnonzero(self.hi > self.lo)
        self.exact = np.flatnonzero(self.hi == self.lo)
        self.grantee = self.free[self.c] > 0


# ------------------------------------------------------------------ the model
def n_params(data):
    return 11 + len(data.n_sites)


def unpack(x):
    return dict(mu=x[0:2], log_sigma=x[2:4], beta=x[4], log_rho=x[5:8], log_gamma=x[8:11], eps=x[11:])


def pack(mu, log_sigma, beta, log_rho, log_gamma, eps):
    return np.concatenate([mu, log_sigma, [beta], log_rho, log_gamma, eps])


def log_theta(p, lnn, typ, free):
    """lnn is log(sites) minus its mean over centers, so that mu is the level at an average center and beta is separate from it."""
    return p["mu"][typ] + p["beta"] * lnn + jnp.exp(p["log_sigma"])[typ] * p["eps"] * free



def decay(p, d, k):
    return jnp.exp(-jnp.power(jnp.maximum(d, D_FLOOR) / jnp.exp(p["log_rho"])[k], jnp.exp(p["log_gamma"])[k]))


def lam_pairs(p, a):
    """Expected patients on every pair. a is a dict of jnp arrays (see arrays())."""
    th = jnp.exp(log_theta(p, a["lnn"], a["type"], a["free"] * a["fm"]))
    w = th[a["c"]] * decay(p, a["d"], a["k"])
    S = jax.ops.segment_sum(w, a["z"], num_segments=a["L"].shape[0])
    return a["L"][a["z"]] * w / (1.0 + S[a["z"]]), S


def arrays(data):
    return dict(c=jnp.asarray(data.c), z=jnp.asarray(data.z), d=jnp.asarray(data.d), k=jnp.asarray(data.k),
                n_sites=jnp.asarray(data.n_sites), lnn=jnp.asarray(data.lnn), type=jnp.asarray(data.type), free=jnp.asarray(data.free),
                fm=jnp.ones(len(data.n_sites)),
                L=jnp.asarray(np.maximum(data.L, 10.0)),
                lo=jnp.asarray(data.lo), hi=jnp.asarray(data.hi),
                exact=jnp.asarray(data.exact), censored=jnp.asarray(data.censored), pm=jnp.ones(len(data.c)))


def neg_log_post(x, a, wc):
    """wc: data weight of each center (bootstrap multiplicity; 0 holds a center out of the likelihood)."""
    p = unpack(x)
    lam, _ = lam_pairs(p, a)
    w = wc[a["c"]] * a["pm"]
    ex, ce = a["exact"], a["censored"]
    ll = jnp.sum(w[ex] * (a["lo"][ex] * jnp.log(lam[ex]) - lam[ex]))
    lc = lam[ce]
    pr = gammaincc(a["hi"][ce] + 1.0, lc) - gammaincc(a["lo"][ce], lc)
    ll += jnp.sum(w[ce] * jnp.log(jnp.maximum(pr, 1e-300)))
    # Normal(eps) prior plus the log-sigma term of the centered form; without it sigma grows without bound as eps shrinks.
    prior = 0.5 * jnp.sum(p["eps"] ** 2 * a["free"]) + jnp.sum(a["free"] * p["log_sigma"][a["type"]])
    prior += 0.5 * jnp.sum(((p["log_rho"] - jnp.log(5.0)) / 2.0) ** 2) + 0.5 * jnp.sum((p["log_gamma"] / 1.0) ** 2) + 0.5 * (p["beta"] / 2.0) ** 2
    prior += 0.5 * jnp.sum((p["log_sigma"] / 3.0) ** 2) + 0.5 * jnp.sum((p["mu"] / 20.0) ** 2)
    return (-ll + prior) / SCALE


SCALE = 1e6  # keeps the objective near 1 so L-BFGS tolerances mean the same thing for every fit
_vg = jax.jit(jax.value_and_grad(neg_log_post))


def scales(x0, a, wc, data):
    """Diagonal preconditioner: the step that moves each parameter by one unit of curvature. Without it L-BFGS crawls along the
    ridge between the center effects and the type levels."""
    x0 = jnp.asarray(x0)
    hg = np.zeros(11)  # second derivative by central differences of the gradient
    for i in range(11):
        h = 1e-3
        e = jnp.zeros_like(x0).at[i].set(h)
        hg[i] = (float(_vg(x0 + e, a, wc)[1][i]) - float(_vg(x0 - e, a, wc)[1][i])) / (2 * h) * SCALE
    lam, _ = lam_pairs(unpack(x0), a)
    per_center = np.bincount(np.asarray(a["c"]), np.asarray(lam * wc[a["c"]] * a["pm"]), minlength=len(data.n_sites))
    sig = np.exp(np.asarray(x0[2:4]))[data.type]
    h = np.r_[np.maximum(hg, 1.0), sig ** 2 * per_center + 1.0]
    return np.sqrt(SCALE / h)


def init_x(data, rho=(5.0, 1.7, 0.5), gamma=(0.93, 0.70, 0.54), rounds=8):
    """Starting values: with the decay fixed, solve each center's theta so its expected patients match its observed patients."""
    f = np.exp(-(np.maximum(data.d, D_FLOOR) / np.array(rho)[data.k]) ** np.array(gamma)[data.k])
    n = len(data.n_sites)
    obs = np.bincount(data.c, data.lo, minlength=n)
    theta = np.ones(n)
    for _ in range(rounds):
        w = theta[data.c] * f
        S = np.bincount(data.z, w, minlength=len(data.L))
        pred = np.bincount(data.c, np.maximum(data.L, 10.0)[data.z] * f / (1 + S[data.z]), minlength=n)
        theta = np.where(data.free > 0, np.clip(obs / np.maximum(pred, 1e-9), 1e-6, 1e6), np.exp(np.log(np.median(theta[data.free > 0])) + 0.0))
    u = np.log(theta)
    mu, sig = np.zeros(2), np.ones(2)
    for t in (0, 1):
        m = (data.free > 0) & (data.type == t)
        mu[t], sig[t] = u[m].mean(), max(u[m].std(), 0.3)
    eps = np.where(data.free > 0, (u - mu[data.type]) / sig[data.type], 0.0)
    return pack(mu, np.log(sig), 0.0, np.log(rho), np.log(gamma), eps)


def fit(data, a, wc, x0=None, maxiter=600, fixed=None):
    """Maximum a posteriori fit. fixed: centers held at their type's typical theta (eps = 0) instead of being estimated."""
    wc = jnp.asarray(wc, dtype=float)
    a = dict(a)
    if fixed is not None:
        a["fm"] = jnp.asarray(1.0 - np.asarray(fixed, float))
    n = len(data.n_sites)
    if x0 is None:
        x0 = init_x(data)
    sc = scales(x0, a, wc, data)
    lo = np.r_[[-15, -15], [-3, -3], -1.0, [-3] * 3, [-1.5] * 3, [-8] * n]
    hi = np.r_[[15, 15], [2.0, 2.0], 2.0, [5] * 3, [1.5] * 3, [8] * n]

    def f(y):
        v, g = _vg(jnp.asarray(y * sc), a, wc)
        return float(v), np.asarray(g) * sc

    r = minimize(f, np.asarray(x0) / sc, jac=True, method="L-BFGS-B", bounds=list(zip(lo / sc, hi / sc)),
                 options={"maxiter": maxiter, "maxcor": 20, "ftol": 1e-14, "gtol": 1e-6, "maxls": 30})
    r.x = r.x * sc
    return r.x, r


def params_table(x):
    p = unpack(x)
    return {"mu": [float(v) for v in p["mu"]], "sigma": [float(np.exp(v)) for v in p["log_sigma"]], "beta": float(p["beta"]),
            "rho": [float(np.exp(v)) for v in p["log_rho"]], "gamma": [float(np.exp(v)) for v in p["log_gamma"]]}


def expected(x, a):
    """Return (lam per pair, S per ZCTA) as numpy."""
    lam, S = lam_pairs(unpack(jnp.asarray(x)), a)
    return np.asarray(lam), np.asarray(S)


def expected_typical(x, a, fixed):
    """Like expected(), but the centers in `fixed` get their type's typical theta (eps = 0)."""
    a = dict(a)
    a["fm"] = jnp.asarray(1.0 - np.asarray(fixed, float))
    return expected(x, a)
