"""Place the censored ('--', 1 to 15 patients) cells from the exact center totals.

Table 4 gives every center's total number of patients. Minus the visible row totals, that is the exact sum of the center's
hidden cells (each between 1 and 15). Given a fitted expectation for each cell, the exact conditional distribution of the
cells given that sum is sampled with a backward convolution (no approximation beyond the Poisson prior on each cell).
Payer cells that are hidden are filled in expectation from the row total, which is a different exact constraint.
"""
import numpy as np
import pandas as pd
from scipy.special import logsumexp
from scipy.optimize import minimize_scalar
from scipy.stats import nbinom, poisson

DRAWS = 200
PAYERS = ["uninsured", "medicaid", "medicare", "private"]


def _log_trunc_pmf(lam, cap=15, prior="poisson"):
    """log P(Y=v | 1 <= Y <= cap) for v = 1..cap, one row per lambda. prior: "poisson", "flat" (every value equally likely, the
    expectation is ignored), or a number r for a negative binomial with variance lam + lam^2 / r."""
    v = np.arange(1, cap + 1)[None, :]
    lam = np.maximum(np.asarray(lam, float), 1e-9)[:, None]
    if isinstance(prior, str) and prior == "flat":
        lp = np.zeros((len(lam), cap))
    elif isinstance(prior, str):
        lp = poisson.logpmf(v, lam)
    else:
        lp = nbinom.logpmf(v, prior, prior / (prior + lam))
    return lp - logsumexp(lp, axis=1, keepdims=True)


def fit_dispersion(lam, y, cap):
    """Size r of the negative binomial that fits counts y in 1..cap best given their expectations lam (zero-truncated, capped)."""
    lam, y = np.asarray(lam, float), np.asarray(y, int)
    ok = (y >= 1) & (y <= cap)
    lam, y = np.maximum(lam[ok], 1e-9), y[ok]
    grid = np.arange(1, cap + 1)[None, :]

    def nll(lr):
        r = np.exp(lr)
        all_lp = nbinom.logpmf(grid, r, r / (r + lam[:, None]))
        return -(nbinom.logpmf(y, r, r / (r + lam)) - logsumexp(all_lp, axis=1)).sum()

    return float(np.exp(minimize_scalar(nll, bounds=(np.log(1e-3), np.log(1e4)), method="bounded").x))


def sample_center(lams, total, n, rng, cap=15, prior="poisson"):
    """n integer vectors in [1,cap]^m summing to total, with the exact conditional law under independent truncated Poissons.
    Works in logs: a center with dozens of cells can have a total near the end of the range, where plain probabilities underflow."""
    m = len(lams)
    lp = _log_trunc_pmf(lams, cap, prior)
    tail = [None] * (m + 1)  # tail[i][s] = log P(cells i..m-1 sum to s)
    tail[m] = np.array([0.0])
    for i in range(m - 1, -1, -1):
        L = len(tail[i + 1])
        st = np.full((cap, L + cap), -np.inf)
        for v in range(1, cap + 1):
            st[v - 1, v:v + L] = lp[i, v - 1] + tail[i + 1]
        tail[i] = logsumexp(st, axis=0)
    out = np.zeros((m, n), dtype=np.int16)
    rem = np.full(n, int(total))
    v = np.arange(1, cap + 1)
    for i in range(m):
        nxt = tail[i + 1]
        idx = rem[:, None] - v[None, :]
        ok = (idx >= 0) & (idx < len(nxt))
        lw = lp[i][None, :] + np.where(ok, nxt[np.clip(idx, 0, len(nxt) - 1)], -np.inf)
        w = np.exp(lw - lw.max(axis=1, keepdims=True))
        w /= w.sum(axis=1, keepdims=True)
        u = rng.random(n)[:, None]
        pick = (np.cumsum(w, axis=1) < u).sum(axis=1).clip(0, cap - 1)
        out[i] = pick + 1
        rem = rem - (pick + 1)
    return out


def sample_all(rows, lam_row, centers, draws=DRAWS, seed=1, prior="poisson"):
    """rows: DataFrame of hidden-total rows with grant; lam_row: prior expectation per row. Returns (rows, y[n_rows, draws])."""
    rng = np.random.default_rng(seed)
    y = np.zeros((len(rows), draws), dtype=np.int16)
    bad = []
    for grant, idx in rows.groupby("grant").indices.items():
        total = centers.hidden_patients[grant]
        m = len(idx)
        if total < m or total > 15 * m:
            bad.append(grant)
            y[idx] = np.clip(np.round(total / m), 1, 15)
            continue
        y[idx] = sample_center(lam_row[idx], total, draws, rng, prior=prior)
    return y, bad


def fill_payers(z, total_row, pattern):
    """Expected payer counts for every row. z has columns uninsured..private (NaN where hidden) and hid_<payer> flags.
    total_row: row totals (the visible total, or the mean of the hidden draws). pattern: per-row payer shares (n, 4) used to
    split what the visible payer cells leave over, with every hidden cell kept inside 1 to 15. Returns an (n, 4) array."""
    vals = np.stack([np.nan_to_num(z[p].to_numpy(float), nan=0.0) for p in PAYERS], axis=1)
    hid = np.stack([z["hid_" + p].to_numpy(bool) for p in PAYERS], axis=1)
    left = np.maximum(total_row - vals.sum(axis=1), 0.0)
    out, free = vals.copy(), hid.copy()
    for _ in range(5):
        ww = np.where(free, pattern + 1e-9, 0.0)
        s = ww.sum(axis=1, keepdims=True)
        est = left[:, None] * ww / np.where(s > 0, s, 1.0)
        clipped = free & ((est > 15) | (est < 1))
        if not clipped.any():
            break
        pin = np.clip(est, 1, 15)
        out = np.where(clipped, pin, out)
        left = np.maximum(left - (pin * clipped).sum(axis=1), 0.0)
        free = free & ~clipped
    return np.where(free, est, out)
