"""Scenario model for 2027 additional low-income uninsured adults, plus the stability-adjusted ranking, a
backtest of county change, and the session calculation. Everything uncertain is an explicit prior."""
import numpy as np
import pandas as pd
from scipy import stats

SEED = 20261022
K = 10_000                      # Monte Carlo draws
QS = [0.10, 0.50, 0.80, 0.90, 0.95]
Z90 = 1.645                      # SAHIE margins of error are 90%

# Location of each uncertain quantity in the three scenarios (Beta means) and how tightly each is pinned down.
#   u  share of people who lose paid marketplace coverage and end up uninsured (not Medicaid, employer or never real)
#   d  further loss of paid marketplace coverage after February 2026, as a share of February 2026 paid enrollment
#   w  share of Medicaid expansion adults who eventually lose coverage under work requirements and six-month renewals
#   z  share of those who lose Medicaid who end up uninsured
#   r  share of that eventual loss in place on average during 2027 (a phase-in)
SCENARIOS = {
    "lower":   dict(u=0.30, d=0.04, w=0.135, z=0.70, r=0.35),
    "central": dict(u=0.50, d=0.09, w=0.280, z=0.85, r=0.50),
    "higher":  dict(u=0.70, d=0.16, w=0.500, z=0.95, r=0.65),
}
KAPPA = dict(u=10, d=20, w=12, z=15, e=60, r=12)   # Beta concentration: larger is tighter
E_MEAN = 0.30                                # expansion adults as a share of Medicaid/CHIP enrollment in expansion states (KFF)
PHI = 0.80                                   # share of the 2026 marketplace loss already in a clinic's trailing-year visits (clinic step only)


def beta_from_u(u, mean, kappa):
    return stats.beta.ppf(u, mean * kappa, (1 - mean) * kappa)


def draw_uniforms(n_counties, k=K, seed=SEED):
    rng = np.random.default_rng(seed)
    return {
        "params": rng.random((k, 6)),                              # u, d, w, z, e, r
        "base": rng.standard_normal((k, n_counties), dtype=np.float32),
        "supp": rng.integers(1, 11, size=(k, n_counties, 4), dtype=np.int8),
    }


def county_arrays(c):
    """Observed pieces per county as arrays. Suppressed band cells are redrawn as 1-10 people in each draw."""
    def band(y):
        parts = [(c[f"{b}_{y}"].fillna(0).to_numpy(), c[f"{b}_supp_{y}"].to_numpy()) for b in ("FPL_100_150", "FPL_150_200")]
        return parts
    return {
        "b25": band(2025), "b26": band(2026),
        "ad25": c.adult_share_2025.to_numpy(), "ad26": c.adult_share_2026.to_numpy(),
        "r25": c.rate_2025.to_numpy(), "r26": c.rate_2026.to_numpy(),
        "nui": c.uninsured_le200.to_numpy(), "moe": c.uninsured_moe90.to_numpy(),
        "mcd": (c.expansion.astype(float) * c.medicaid_chip * c.pop138_share).to_numpy(),
    }


def subset(a, U, j):
    """The same arrays and random draws, restricted to county j."""
    aj = {k: (v[j:j + 1] if isinstance(v, np.ndarray) else [(x[j:j + 1], y[j:j + 1]) for x, y in v]) for k, v in a.items()}
    Uj = {"params": U["params"], "base": U["base"][:, j:j + 1], "supp": U["supp"][:, j:j + 1, :]}
    return aj, Uj


def simulate(a, U, scenario, overrides=None, phi=PHI, baseline="draw"):
    """Return per-draw arrays (K x n): the marketplace part of additional uninsured adults, the same part net of the
    share (phi) of the 2026 loss already in a clinic's trailing-year visits, the Medicaid part, the baseline pool, and
    the net paid-coverage loss. The county pool uses the first; the clinic step uses the second.

    overrides replaces entries of the scenario's means (for the tornado). Common random numbers are used across scenarios.
    """
    m = {**SCENARIOS[scenario], "e": E_MEAN, **(overrides or {})}
    p = U["params"]
    u, d, w, z, e, r = (beta_from_u(p[:, j], m[n], KAPPA[n]) for j, n in enumerate("udwzer"))
    supp = U["supp"]
    def bands(parts, off):
        return sum(v + s * supp[:, :, off + j] for j, (v, s) in enumerate(parts))
    s25 = bands(a["b25"], 0) * a["ad25"]
    s26 = bands(a["b26"], 2) * a["ad26"]
    paid25, paid26 = a["r25"] * s25, a["r26"] * s26
    lost = paid25 - paid26                                       # net loss of paid marketplace coverage by February 2026
    mkt = u[:, None] * (lost + d[:, None] * paid26)
    mkt_new = u[:, None] * ((1 - phi) * lost + d[:, None] * paid26)
    mcd = (e * w * r * z)[:, None] * a["mcd"]
    sd = a["moe"] / Z90
    if baseline == "draw":
        pool = np.maximum(a["nui"] + sd * U["base"], np.maximum(0.3 * a["nui"], 10))
    else:                                                        # "lo" / "hi": SAHIE 90% interval ends
        pool = np.maximum(a["nui"] + (-1 if baseline == "lo" else 1) * a["moe"], 10) * np.ones_like(mkt)
    return mkt.astype(np.float32), mkt_new.astype(np.float32), mcd.astype(np.float32), pool.astype(np.float32), lost.astype(np.float32)


def quantiles(x, qs=QS):
    return np.quantile(x, qs, axis=0)


# ---------- stability-adjusted ranking (empirical Bayes on the log change in low-income selections)

def low_band(c, y):
    return c[f"FPL_100_150_{y}"].fillna(5.5) + c[f"FPL_150_200_{y}"].fillna(5.5)


def eb_ranking(c):
    """Shrink each county's log change toward its state's mean. Noise variance is 1/n25 + 1/n26 (Poisson analogue
    for churn); tau^2 is the between-county variance within states, by the DerSimonian-Laird moment estimator."""
    b25, b26 = low_band(c, 2025), low_band(c, 2026)
    y = np.log(b26 / b25)
    v = 1 / b25 + 1 / b26
    st = c.state.to_numpy()
    w0 = 1 / v
    ybar = pd.Series(y * w0).groupby(st).transform("sum") / pd.Series(w0).groupby(st).transform("sum")
    q = float((w0 * (y - ybar) ** 2).sum())
    n_states = len(set(st))
    sw = pd.Series(w0).groupby(st).sum()
    sw2 = pd.Series(w0 ** 2).groupby(st).sum()
    tau2 = max(0.0, (q - (len(y) - n_states)) / (w0.sum() - (sw2 / sw).sum()))
    wi = 1 / (v + tau2)
    mu = pd.Series(y * wi).groupby(st).transform("sum") / pd.Series(wi).groupby(st).transform("sum")
    shrink = tau2 / (tau2 + v)
    theta = mu + shrink * (y - mu)
    out = pd.DataFrame({"fips": c.fips, "log_change_raw": y, "log_change_adj": theta, "shrink_weight": shrink,
                        "state_mean": mu, "b25": b25, "b26": b26})
    return out, {"tau": float(np.sqrt(tau2)), "raw_sd_within_state": float(np.sqrt(np.average((y - ybar) ** 2, weights=w0))),
                 "median_shrink_weight": float(np.median(shrink)), "n": int(len(y))}


def backtest(c, min_n=100, folds=10, seed=SEED):
    """Can a county's change in one income band predict its change in the other, beyond the state average?
    Ten-fold: a county's own 150-200% change is never used to predict it, but the state mean comes from the other
    counties in the state. Only counties with at least min_n selections in all four band-year cells are used."""
    a25, a26 = c.FPL_100_150_2025, c.FPL_100_150_2026
    b25, b26 = c.FPL_150_200_2025, c.FPL_150_200_2026
    ok = (np.minimum.reduce([a25, a26, b25, b26]) >= min_n)
    d = pd.DataFrame({"state": c.state, "ya": np.log(a26 / a25), "yb": np.log(b26 / b25)})[ok].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    fold = rng.integers(0, folds, len(d))
    pred = {k: np.zeros(len(d)) for k in ("zero", "national", "state", "state_plus_band")}
    for f in range(folds):
        tr, te = d[fold != f], d[fold == f]
        sm_b = tr.groupby("state").yb.mean()
        sm_a = tr.groupby("state").ya.mean()
        g_b = tr.yb.mean()
        dev_a = tr.ya - tr.state.map(sm_a)
        dev_b = tr.yb - tr.state.map(sm_b)
        beta = float((dev_a * dev_b).sum() / (dev_a ** 2).sum())
        sb = te.state.map(sm_b).fillna(g_b)
        sa = te.state.map(sm_a).fillna(tr.ya.mean())
        idx = te.index
        pred["zero"][idx] = 0
        pred["national"][idx] = g_b
        pred["state"][idx] = sb
        pred["state_plus_band"][idx] = sb + beta * (te.ya - sa)
    rmse = {k: float(np.sqrt(np.mean((d.yb - v) ** 2))) for k, v in pred.items()}
    se_s, se_b = (d.yb - pred["state"]).to_numpy() ** 2, (d.yb - pred["state_plus_band"]).to_numpy() ** 2
    boot = rng.integers(0, len(d), (2000, len(d)))
    gain = 100 * (1 - np.sqrt(se_b[boot].mean(1) / se_s[boot].mean(1)))
    within = d.ya - d.groupby("state").ya.transform("mean"), d.yb - d.groupby("state").yb.transform("mean")
    return {"n": int(len(d)), "rmse": rmse, "gain_ci95": [float(x) for x in np.quantile(gain, [0.025, 0.975])], "within_state_corr": float(np.corrcoef(*within)[0, 1]),
            "state_share_of_variance_a": float(1 - ((d.ya - d.groupby("state").ya.transform("mean")) ** 2).sum() / ((d.ya - d.ya.mean()) ** 2).sum())}


# ---------- decision layer

def sessions_needed(patients, visits_per_patient, patients_per_session):
    return np.ceil(patients * visits_per_patient / patients_per_session)
