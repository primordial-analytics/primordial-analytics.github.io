"""What a new site would draw: the projection from the competitive gravity model (method step 5 and 6).

For a candidate at x with capacity K and a typical theta, with w_z = theta * f(d_xz) and S_z the competition already in ZCTA z:
  draw from z      = L_z w_z / (1 + S_z + w_z)
  newly reached    = L_z w_z / ((1 + S_z)(1 + S_z + w_z))            taken from the outside option (people with no center)
  from neighbours  = L_z w_z S_z / ((1 + S_z)(1 + S_z + w_z))
  neighbour c loses  lam_cz w_z / (1 + S_z + w_z)   where lam_cz is c's expected patients from z today
If the draw D is more than K every flow is scaled by K / D. Payer mix: neighbours' patients keep the source ZIP's observed mix;
newly reached patients are uninsured at the ACS low-income uninsured share of the ZIP (all ages), and the insured remainder follows the ZIP's
observed Medicaid / Medicare / private pattern.
"""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

import model

PAYERS = ["uninsured", "medicaid", "medicare", "private"]
D_FLOOR = model.D_FLOOR


class Sets:
    """B parameter sets with their own competition S_z and low-income draws L_z, as arrays."""

    def __init__(self, data, X, L_draws):
        a = model.arrays(data)
        self.B = len(X)
        self.rho = np.zeros((self.B, 3))
        self.gamma = np.zeros((self.B, 3))
        self.theta = np.zeros((self.B, 2))
        self.S = np.zeros((self.B, len(data.L)), dtype=np.float32)
        self.L = np.asarray(L_draws[:, :self.B].T, dtype=np.float32)
        lnn_new = -data.lnn_ref  # a single new site: log(1) minus the reference
        single = (data.n_sites == 1) & (data.free > 0)
        for b, x in enumerate(X):
            p = model.unpack(x)
            self.rho[b] = np.exp(p["log_rho"])
            self.gamma[b] = np.exp(p["log_gamma"])
            # A new site is a single site: it gets the typical effect of the fitted single-site centers of its type, not eps = 0. Single-site
            # centers sit below the average center effect at their size (the size term does not fully capture it), so eps = 0 would overstate them.
            eps = np.array([np.median(p["eps"][single & (data.type == t)]) for t in (0, 1)])
            self.theta[b] = np.exp(np.asarray(p["mu"]) + float(p["beta"]) * lnn_new + np.exp(p["log_sigma"]) * eps)
            _, S = model.expected(x, a)
            self.S[b] = S

    def subset(self, n):
        s = object.__new__(Sets)
        s.B, s.rho, s.gamma, s.theta, s.S, s.L = n, self.rho[:n], self.gamma[:n], self.theta[:n], self.S[:n], self.L[:n]
        return s


class ZData:
    """Per-ZCTA inputs of the projection."""

    def __init__(self, zcta, new_payer, obs_mix):
        self.lat = zcta.lat.to_numpy()
        self.lon = zcta.lon.to_numpy()
        self.k = zcta.dclass.to_numpy(int)
        self.new_payer = new_payer  # (n, 4): payer vector of a newly reached patient
        self.obs_mix = obs_mix  # (n, 4): observed payer mix of patients already served


def new_patient_payer(zcta, obs_mix, gmix_unins):
    """Uninsured share from ACS C27016 (all ages below 200%), insured remainder in the ZIP's observed pattern."""
    unins, ins = zcta.unins_all_low.to_numpy(), zcta.ins_all_low.to_numpy()
    tot = unins + ins
    u = np.where(tot >= 20, unins / np.maximum(tot, 1), gmix_unins)
    pattern = obs_mix[:, 1:] / obs_mix[:, 1:].sum(axis=1, keepdims=True)
    return np.c_[u, (1 - u)[:, None] * pattern]


def zpairs(zcta, radius=model.RADIUS):
    """All ordered ZCTA pairs within radius miles (candidate x, source z, miles), as compact arrays."""
    t = cKDTree(model.xyz(zcta.lat.to_numpy(), zcta.lon.to_numpy()))
    m = t.sparse_distance_matrix(t, 2 * np.sin(radius / model.MILES / 2), output_type="ndarray")
    return m["i"].astype(np.int32), m["j"].astype(np.int32), (2 * model.MILES * np.arcsin(np.clip(m["v"] / 2, 0, 1))).astype(np.float32)


def flows(d, k_z, rho, gamma, theta, S_z, L_z):
    """The three flows per (candidate, source ZIP) pair for one parameter set."""
    f = np.exp(-np.power(np.maximum(d, D_FLOOR) / rho[k_z], gamma[k_z]))
    w = theta * f
    den = 1.0 + S_z + w
    draw = L_z * w / den
    new = draw / (1.0 + S_z)
    return draw, new, w, den


def screen(zp, zd, sets, theta_type, K, payer_sets=None):
    """Draw table: for every candidate ZCTA centroid and parameter set, patients (capped at K), newly reached, from neighbours,
    and the payer counts. Returns dict of arrays of shape (B, n)."""
    xi, zi, d = zp
    n = len(zd.lat)
    B = sets.B
    out = {k: np.zeros((B, n), dtype=np.float32) for k in ("draw", "new", "nb")}
    kz = zd.k[zi]
    pay = np.zeros((min(B, payer_sets or B), n, 4), dtype=np.float32)
    for b in range(B):
        draw, new, w, den = flows(d, kz, sets.rho[b], sets.gamma[b], sets.theta[b, theta_type], sets.S[b][zi], sets.L[b][zi])
        D = np.bincount(xi, draw, minlength=n)
        N = np.bincount(xi, new, minlength=n)
        scale = np.where(D > K, K / np.maximum(D, 1e-9), 1.0)
        out["draw"][b], out["new"][b], out["nb"][b] = D * scale, N * scale, (D - N) * scale
        if b < pay.shape[0]:
            nb_f = draw - new
            for j in range(4):
                pay[b, :, j] = np.bincount(xi, new * zd.new_payer[zi, j] + nb_f * zd.obs_mix[zi, j], minlength=n) * scale
    out["pay"] = pay
    return out


def payer_shares(pay):
    tot = pay.sum(axis=2, keepdims=True)
    return np.where(tot > 0, pay / np.maximum(tot, 1e-9), np.nan)


def candidate(lat, lon, zd, sets, theta_type, K, nbr, centers_names, radius=model.RADIUS, b_idx=None):
    """Full detail for one candidate point: used for the fixtures and by the browser check.
    nbr: dict with 'c' (n_z x m ints, -1 for none) and 'lam' (n_z x m) top neighbours per ZIP at today's fit."""
    dist = model.miles_between(lat, lon, zd.lat, zd.lon)
    z = np.flatnonzero(dist <= radius)
    d = dist[z].astype(np.float32)
    bs = range(sets.B) if b_idx is None else b_idx
    res = []
    for b in bs:
        draw, new, w, den = flows(d, zd.k[z], sets.rho[b], sets.gamma[b], sets.theta[b, theta_type], sets.S[b][z], sets.L[b][z])
        D = draw.sum()
        scale = min(1.0, K / D) if D > 0 else 1.0
        res.append({"D": D * scale, "new": new.sum() * scale, "draw_z": draw * scale, "new_z": new * scale, "w": w, "den": den, "scale": scale})
    return z, d, res


def neighbour_loss(z, res, nbr):
    """Expected patients lost by each named neighbour, one value per parameter set, from today's fitted flows."""
    cs, lams = nbr["c"][z], nbr["lam"][z]
    frac = np.stack([r["w"] / r["den"] * r["scale"] for r in res])
    return {int(c): frac @ np.where(cs == c, lams, 0.0).sum(axis=1) for c in np.unique(cs[cs >= 0])}


def top_neighbours(lam, data, m=6):
    """For each ZCTA, the m centers with the most expected patients there today (from the fit)."""
    n = len(data.L)
    order = np.lexsort((-lam, data.z))
    zs, cs, ls = data.z[order], data.c[order], lam[order]
    first = np.searchsorted(zs, np.arange(n))
    c = -np.ones((n, m), dtype=np.int32)
    v = np.zeros((n, m), dtype=np.float32)
    cnt = np.bincount(zs, minlength=n)
    for j in range(m):
        has = cnt > j
        idx = first[has] + j
        c[has, j] = cs[idx]
        v[has, j] = ls[idx]
    return {"c": c, "lam": v}
