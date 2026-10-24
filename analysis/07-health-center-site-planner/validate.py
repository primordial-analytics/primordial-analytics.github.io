"""Checks A to F of the method: what the model gets right on data it has not seen, and what it does not.

A  hidden-cell reconstruction      B  random cell holdout        C  leave-one-center-out (a new site in miniature)
D  out-of-time on 2025 openings    E  agreement with HRSA's published penetration       F  sensitivity of the top-50 lists
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.spatial import cKDTree
from scipy.special import gammaln
from scipy.stats import nbinom, spearmanr

import fits
import hidden
import model

SEED = 11


# ------------------------------------------------------------------ A: hidden-cell reconstruction
def visible_cell_expectations(d, data, x):
    """Visible ZIP rows of the HRSA file with the fitted expectation for their center and ZCTA."""
    rows = d["rows"]
    lam, _ = model.expected(x, model.arrays(data))
    pair = pd.Series(lam, index=pd.MultiIndex.from_arrays([data.ent.index[data.c], data.zcta.index[data.z]]))
    vis = rows[(rows.kind == "ZipCode") & rows.total.notna() & (rows.total >= 1) & rows.zcta.notna()].copy()
    vis["lam"] = pair.reindex(pd.MultiIndex.from_arrays([vis.grant, vis.zcta])).to_numpy()
    return vis[vis.lam.notna()]


def check_hidden_reconstruction(d, data, x, n_centers=250, seed=SEED):
    """Hide visible cells below a cap at random centers, give the sampler only their exact sum, and score it against the truth.
    Three ways to place them: independent Poisson cells at the fitted expectation, a flat prior (every value equally likely, expectation ignored) and the plain equal split.
    A negative binomial fitted to these cells goes to its lower size bound (as flat as the family allows), so it is recorded but not scored. The expectations come from the main fit, which saw these cells: a leak of one cell in dozens
    through the center's scale. Which of Poisson and flat does better at 24 is recorded in placement_used."""
    rng = np.random.default_rng(seed)
    vis = visible_cell_expectations(d, data, x)
    out = {}
    for cap in (39, 24):
        r_nb = hidden.fit_dispersion(vis.lam, vis.total, cap)
        centers = rng.choice(vis.grant.unique(), n_centers, replace=False)
        recs = []
        for g in centers:
            r = vis[(vis.grant == g) & (vis.total <= cap)]
            if len(r) < 2:
                continue
            truth = r.total.to_numpy().astype(int)
            rec = {"truth": truth, "equal": truth.sum() / len(truth)}
            for name, prior in (("poisson", "poisson"), ("flat", "flat")):
                draws = hidden.sample_center(r.lam.to_numpy(), truth.sum(), 200, rng, cap=cap, prior=prior)
                q = np.quantile(draws, [0.1, 0.5, 0.9], axis=1)
                rec.update({f"{name}_p10": q[0], f"{name}_p50": q[1], f"{name}_p90": q[2]})
            recs.append(pd.DataFrame(rec))
        e = pd.concat(recs)
        e["bin"] = pd.cut(e.truth, [0, 5, 15, 24, 39], labels=["1-5", "6-15", "16-24", "25-39"])
        by = {}
        for label, g in [("all", e)] + [(str(k), v) for k, v in e.groupby("bin", observed=True)]:
            row = {"cells": int(len(g)), "mae_equal_split": float((g.equal - g.truth).abs().mean())}
            for name in ("poisson", "flat"):
                row[f"mae_{name}"] = float((g[f"{name}_p50"] - g.truth).abs().mean())
                row[f"coverage_80_{name}"] = float(((g.truth >= g[f"{name}_p10"]) & (g.truth <= g[f"{name}_p90"])).mean())
                row[f"mean_width_{name}"] = float((g[f"{name}_p90"] - g[f"{name}_p10"]).mean())
            by[label] = row
        out[f"cells_up_to_{cap}"] = {"centers": int(len(recs)), "negative_binomial_size": r_nb, "negative_binomial_size_at_search_bound": bool(r_nb < 1.01e-3), "by_size": by}
    a24 = out["cells_up_to_24"]["by_size"]["all"]
    out["placement_used"] = "flat" if a24["mae_flat"] <= a24["mae_poisson"] else "poisson"
    return out


# ------------------------------------------------------------------ baselines
def nb_dispersion(lam, y):
    """Negative binomial size r (variance = lam + lam^2 / r) by maximum likelihood on pairs with data."""
    def nll(lr):
        r = np.exp(lr)
        return -(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + lam)) + y * np.log(lam / (r + lam))).sum()
    return float(np.exp(minimize_scalar(nll, bounds=(np.log(0.05), np.log(1e4)), method="bounded").x))


def site_pairs(data, radius):
    """(site index, zcta index, miles) for sites of modeled centers within radius."""
    from scipy.spatial import cKDTree as KD
    tz = KD(model.xyz(data.zcta.lat.to_numpy(), data.zcta.lon.to_numpy()))
    ts = KD(model.xyz(data.sites.lat.to_numpy(), data.sites.lon.to_numpy()))
    m = ts.sparse_distance_matrix(tz, 2 * np.sin(radius / model.MILES / 2), output_type="ndarray")
    return m["i"], m["j"], 2 * model.MILES * np.arcsin(np.clip(m["v"] / 2, 0, 1))


def sfca_pairs(data, sp, train_patients, r):
    """Two-step floating catchment predictions for every (center, ZCTA) pair of `data`.
    Step 1: each site's supply (its center's training patients split over its sites) over the low-income residents within r miles.
    Step 2: a ZCTA's expected patients at a site = its residents times that site's ratio. Also returns the access score per ZCTA."""
    si, zj, dm = sp
    keep = dm <= r
    si, zj = si[keep], zj[keep]
    ent_of_site = data.eidx.reindex(data.sites.grant).to_numpy()
    supply = (train_patients / data.n_sites)[ent_of_site]
    pop_in = np.bincount(si, data.L[zj], minlength=len(data.sites))
    ratio = np.where(pop_in > 0, supply / np.maximum(pop_in, 1), 0.0)
    access = np.bincount(zj, ratio[si], minlength=len(data.L))
    cell = pd.DataFrame({"c": ent_of_site[si], "z": zj, "v": ratio[si] * data.L[zj]}).groupby(["c", "z"]).v.sum()
    key = pd.MultiIndex.from_arrays([data.c, data.z])
    return cell.reindex(key).fillna(0.0).to_numpy(), access


def pop_only(data, train_patients, train_mask):
    """Population-only baseline: a center's training patients spread over its pairs in proportion to low-income residents."""
    L = data.L[data.z]
    tot = np.bincount(data.c, L * train_mask, minlength=len(data.n_sites))
    return train_patients[data.c] * L / np.maximum(tot[data.c], 1)


# ------------------------------------------------------------------ B: random cell holdout
def holdout_jobs(data, x, frac=0.1, seed=SEED):
    rng = np.random.default_rng(seed)
    pm = np.ones(len(data.c))
    test = (data.free[data.c] > 0) & (data.hi == data.lo) & (rng.random(len(data.c)) < frac)
    pm[test] = 0.0
    return [{"variant": "main", "tag": "holdout", "pm": pm, "x0": x}], test


def check_holdout(d, data, a, x_hold, test):
    lam, _ = model.expected(x_hold, a)
    y = data.lo
    train = (data.free[data.c] > 0) & ~test
    train_patients = np.bincount(data.c, y * train, minlength=len(data.n_sites))
    tr_ex = train & (y > 0)
    r_nb = nb_dispersion(lam[train & (lam >= 1)], y[train & (lam >= 1)])
    sp = site_pairs(data, 30.0)
    best = None
    for r in (5, 10, 15, 20, 30):
        pred, _ = sfca_pairs(data, sp, train_patients, r)
        rho = spearmanr(pred[tr_ex], y[tr_ex])[0]
        if best is None or rho > best[0]:
            best = (rho, r, pred)
    pred_sfca = best[2]
    pred_pop = pop_only(data, train_patients, train)
    t = test & (y >= 0)
    nz = t & (y > 0)

    def score(name, p):
        return {"spearman_cells_with_patients": float(spearmanr(p[nz], y[nz])[0]), "mae_all_held_out": float(np.abs(p[t] - y[t]).mean()),
                "mae_cells_with_patients": float(np.abs(p[nz] - y[nz]).mean()), "total_ratio": float(p[t].sum() / y[t].sum())}

    q10, q90 = nbinom.ppf(0.1, r_nb, r_nb / (r_nb + lam[t])), nbinom.ppf(0.9, r_nb, r_nb / (r_nb + lam[t]))
    cov = (y[t] >= q10) & (y[t] <= q90)
    bins = pd.cut(lam[t], [0, 0.5, 5, 50, np.inf], labels=["<0.5", "0.5-5", "5-50", ">50"], include_lowest=True)
    pq10, pq90 = nbinom.ppf(0.1, 1e6, 1e6 / (1e6 + lam[t])), nbinom.ppf(0.9, 1e6, 1e6 / (1e6 + lam[t]))
    return {
        "held_out_pairs": int(t.sum()), "held_out_pairs_with_patients": int(nz.sum()), "share_of_pairs": float(test.sum() / (data.free[data.c] > 0).sum()),
        "gravity": score("gravity", lam), "two_step_floating_catchment": {**score("sfca", pred_sfca), "best_radius_miles": best[1]},
        "population_only": score("pop", pred_pop), "negative_binomial_size": r_nb,
        "interval_80_coverage": float(cov.mean()), "interval_80_coverage_by_expected_size": {str(k): float(cov[bins == k].mean()) for k in bins.categories},
        "interval_80_coverage_poisson_only": float(((y[t] >= pq10) & (y[t] <= pq90)).mean()),
    }, best[1]


# ------------------------------------------------------------------ C: leave one center out
SITE_BINS = ["1", "2-3", "4-10", ">10"]


def sites_bin(n):
    return pd.cut(pd.Series(np.asarray(n, float)), [0, 1, 3, 10, np.inf], labels=SITE_BINS).astype(str).to_numpy()


def loco_plan(data, d, n_per_stratum=25, n_single=40, seed=SEED, min_gap_miles=100.0):
    """Grantees stratified by urban/rural and number of sites (1, 2-3, 4-10, over 10), split into folds whose centers are far apart.
    Single-site centers are what the tool projects, so up to 40 of them per urban/rural stratum are held out (all, where fewer exist)."""
    rng = np.random.default_rng(seed)
    cen = d["centers"]
    ent = data.ent[data.free > 0]
    info = cen.loc[ent.index, ["urban_flag", "patients"]].copy()
    info["sites"] = data.n_sites[data.free > 0]
    info["sites_bin"] = sites_bin(info.sites)
    chosen = []
    for (u, s), g in info.groupby(["urban_flag", "sites_bin"], observed=True):
        chosen += list(rng.choice(g.index, min(n_single if s == "1" else n_per_stratum, len(g)), replace=False))
    chosen = list(rng.permutation(chosen))
    trees = {g: cKDTree(model.xyz(*data.sites[data.sites.grant == g][["lat", "lon"]].to_numpy().T)) for g in chosen}
    gap = 2 * np.sin(min_gap_miles / model.MILES / 2)
    folds = []
    for g in chosen:
        sites_g = data.sites[data.sites.grant == g][["lat", "lon"]].to_numpy()
        for f in folds:
            if len(f) < 15 and all(trees[o].query(model.xyz(sites_g[:, 0], sites_g[:, 1]))[0].min() > gap for o in f):
                f.append(g)
                break
        else:
            folds.append([g])
    return folds, info


def loco_jobs(data, folds, x):
    jobs = []
    for i, f in enumerate(folds):
        idx = data.eidx[f].to_numpy()
        w = np.where(data.free > 0, 1.0, 0.0)
        w[idx] = 0.0
        fixed = np.zeros(len(data.n_sites))
        fixed[idx] = 1.0
        jobs.append({"variant": "main", "tag": f"loco{i}", "w": w, "fixed": fixed, "x0": x, "maxiter": fits.MAXITER})
    return jobs


def check_loco(d, data, a, folds, results, info, sfca_radius):
    """Each held-out center is predicted with its own rows out of the likelihood. Its attractiveness is the one the tool would give a site of
    its size: the median center effect of the fitted centers of the same type and site-count bin ("tool rule"). Predicted total patients is also
    reported with the plain type level (eps = 0)."""
    y = (data.lo + data.hi) / 2
    rows = []
    L = data.L
    bins = sites_bin(data.n_sites)
    free = data.free > 0
    for i, f in enumerate(folds):
        x = results[f"loco{i}"][0]
        held = data.eidx[f].to_numpy()
        fixed = np.zeros(len(data.n_sites))
        fixed[held] = 1.0
        lam0, _ = model.expected_typical(x, a, fixed)
        eps = x[11:]
        x_rule = x.copy()
        train = free & (fixed == 0)
        for c in held:
            m = train & (data.type == data.type[c]) & (bins == bins[c])
            x_rule[11 + c] = np.median(eps[m]) if m.any() else 0.0
        lam, _ = model.expected(x_rule, a)
        for g in f:
            c = data.eidx[g]
            m = data.c == c
            yy, ll, z, dd = y[m], lam[m], data.z[m], data.d[m]
            if yy.sum() <= 0:
                continue
            top = lambda score: float(yy[np.argsort(-score)[:20]].sum() / yy.sum())
            near = dd <= sfca_radius
            sf_score = np.where(near, L[z], -1.0)
            rho = spearmanr(ll, yy)[0] if np.ptp(yy) > 0 else np.nan
            cors = np.corrcoef(np.log1p(ll), np.log1p(yy))[0, 1] if np.ptp(yy) > 0 else np.nan
            rows.append({"grant": g, "urban": info.urban_flag[g], "sites": int(info.sites[g]), "sites_bin": info.sites_bin[g], "patients": float(yy.sum()),
                         "pred_total_tool_rule": float(ll.sum()), "pred_total_typical": float(lam0[m].sum()),
                         "top20_model": top(ll), "top20_population": top(L[z]), "top20_nearest": top(-dd), "top20_population_within_radius": top(sf_score),
                         "spearman": rho, "log_pearson": cors})
    e = pd.DataFrame(rows)
    w = lambda col, g=e: float((g[col] * g.patients).sum() / g.patients.sum())
    ratio = e.pred_total_tool_rule / e.patients
    ratio0 = e.pred_total_typical / e.patients
    rstat = lambda r: {"total_ratio_median": float(r.median()), "total_ratio_p10": float(r.quantile(0.1)), "total_ratio_p90": float(r.quantile(0.9)),
                       "total_ratio_within_factor_2": float(((r > 0.5) & (r < 2)).mean())}
    cols = lambda g: {"centers": int(len(g)), "patients_median": float(g.patients.median()), "top20_model_mean": float(g.top20_model.mean()), "top20_model_patient_weighted": w("top20_model", g),
                      "top20_nearest_mean": float(g.top20_nearest.mean()), "top20_population_mean": float(g.top20_population.mean()),
                      "share_centers_model_beats_nearest": float((g.top20_model > g.top20_nearest).mean())}
    by_bin = {s: {**cols(g), **rstat(g.pred_total_tool_rule / g.patients), "total_ratio_median_eps0": float((g.pred_total_typical / g.patients).median())}
              for s, g in e.groupby("sites_bin") if len(g)}
    by_bin = {s: by_bin[s] for s in SITE_BINS if s in by_bin}
    by_u = {u: {**cols(g)} for u, g in e.groupby("urban")}
    by = {f"{u}_{s}": {**cols(g)} for (u, s), g in e.groupby(["urban", "sites_bin"])}
    gap = (e.top20_model - e.top20_nearest) * 100
    return {
        "centers": int(len(e)), "folds": len(folds), "single_site_centers_held_out": int((e.sites == 1).sum()),
        "top20_model_mean": float(e.top20_model.mean()), "top20_model_patient_weighted": w("top20_model"),
        "top20_population_only_mean": float(e.top20_population.mean()), "top20_population_only_patient_weighted": w("top20_population"),
        "top20_nearest_zips_mean": float(e.top20_nearest.mean()), "top20_nearest_zips_patient_weighted": w("top20_nearest"),
        "top20_population_within_radius_mean": float(e.top20_population_within_radius.mean()), "sfca_radius_miles": sfca_radius,
        "median_spearman_cell_counts": float(e.spearman.median()), "median_log_pearson_cell_counts": float(e.log_pearson.median()),
        "share_centers_model_beats_population_only": float((e.top20_model > e.top20_population).mean()),
        "share_centers_model_beats_nearest": float((e.top20_model > e.top20_nearest).mean()), "model_minus_nearest_points_median": float(gap.median()),
        **rstat(ratio), "total_ratio_median_eps0": float(ratio0.median()), "total_ratio_within_factor_2_eps0": float(((ratio0 > 0.5) & (ratio0 < 2)).mean()),
        "by_sites_bin": by_bin, "by_urban_rural": by_u, "by_stratum": by,
    }, e


# ------------------------------------------------------------------ D: openings
def opening_window(d24, start="2025-01-01", end="2025-06-30"):
    s = d24["late_sites"]
    return s[(s.added >= start) & (s.added <= end)].reset_index(drop=True)


YEAR_END = pd.Timestamp("2025-12-31")


def zcta_patients(rows):
    """Patients per ZCTA from the visible cells plus 8 (the middle of 1 to 15) per censored cell."""
    r = rows[rows.zcta.notna()]
    return (r.total.fillna(0) + 8 * r.hid_total).groupby(r.zcta).sum()


def check_openings(d24, d25, x24, boots24, data24, a24, new_sites):
    """Predict the change in patients within 5 miles of sites added to scope in the first half of 2025, from the 2024 fit."""
    zcta = d24["zcta"]
    grantee = new_sites[new_sites.grant.isin(data24.ent.index[data24.free > 0])]
    cen24 = d24["centers"].copy()
    add = grantee.groupby("grant").size()
    cen24.loc[add.index, "n_sites"] = cen24.loc[add.index, "n_sites"] + add
    lal24 = d24["lookalikes"].copy()
    lal_new = new_sites[new_sites.lookalike & new_sites.grant.isin(lal24.index)]
    lal24.loc[lal_new.grant.unique(), "n_sites"] = lal24.loc[lal_new.grant.unique(), "n_sites"] + lal_new.groupby("grant").size()
    sites_aug = pd.concat([d24["sites"], grantee, lal_new], ignore_index=True)
    data_b = model.Data(zcta, cen24, lal24, sites_aug, d24["cells"])
    data_b.lnn_ref = data24.lnn_ref  # the reference is part of the fitted model, not of the new site list
    data_b.lnn = np.log(data_b.n_sites) - data24.lnn_ref
    a_b = model.arrays(data_b)
    n = len(zcta)

    def zsum(x, dat, a):
        lam, _ = model.expected(x, a)
        return np.bincount(dat.z, lam, minlength=n)

    before = np.stack([zsum(x, data24, a24) for x in boots24])
    after = np.stack([zsum(x, data_b, a_b) for x in boots24])
    delta = after - before  # (B, n)
    p24, p25 = zcta_patients(d24["rows"]), zcta_patients(d25["rows"])
    p24 = p24.reindex(zcta.index).fillna(0).to_numpy()
    p25 = p25.reindex(zcta.index).fillna(0).to_numpy()
    xyz = model.xyz(zcta.lat.to_numpy(), zcta.lon.to_numpy())
    tz = cKDTree(xyz)
    r5 = 2 * np.sin(5.0 / model.MILES / 2)
    all_new = d24["late_sites"]
    near_any = np.zeros(n, bool)
    for la, lo in all_new[["lat", "lon"]].to_numpy():
        near_any[tz.query_ball_point(model.xyz(np.array([la]), np.array([lo]))[0], r5)] = True
    rows = []
    for _, s in grantee.iterrows():
        z = np.array(tz.query_ball_point(model.xyz(np.array([s.lat]), np.array([s.lon]))[0], r5))
        if len(z) == 0 or p24[z].sum() < 200:
            continue
        st, dc = zcta.state.iloc[z[0]], np.bincount(zcta.dclass.to_numpy()[z]).argmax()
        ctrl = (zcta.state.to_numpy() == st) & (zcta.dclass.to_numpy() == dc) & ~near_any & (p24 > 0)
        g = p25[ctrl].sum() / p24[ctrl].sum() - 1 if ctrl.sum() >= 5 else np.nan
        obs = p25[z].sum() - p24[z].sum()
        excess = obs - g * p24[z].sum()
        pred = delta[:, z].sum(axis=1)
        sd = np.sqrt(p24[z].sum() + p25[z].sum())
        rows.append({"grant": s.grant, "state": st, "added": s.added, "exposure": (YEAR_END - s.added).days / 365.0, "zctas": len(z), "patients_2024": p24[z].sum(), "observed_change": obs, "control_growth": g, "observed_excess": excess,
                     "pred_p10": np.quantile(pred, 0.1), "pred_p50": np.median(pred), "pred_p90": np.quantile(pred, 0.9),
                     "wide_p10": np.quantile(pred + np.random.default_rng(1).normal(0, sd, len(pred)), 0.1),
                     "wide_p90": np.quantile(pred + np.random.default_rng(1).normal(0, sd, len(pred)), 0.9), "noise_sd": sd})
    e = pd.DataFrame(rows).dropna(subset=["control_growth"])

    def score(g, scale):
        """Predictions are for a full year of operation; scale = the share of the 2025 reporting year the site was in scope (1 = unscaled)."""
        lo, mid, hi = g.pred_p10 * scale, g.pred_p50 * scale, g.pred_p90 * scale
        wlo, whi = g.wide_p10 * scale, g.wide_p90 * scale
        both = (g.observed_excess > 0) & (mid > 0)
        return {
            "sites": int(len(g)), "median_predicted_change": float(mid.median()), "median_observed_excess": float(g.observed_excess.median()),
            "spearman_predicted_vs_observed": float(spearmanr(mid, g.observed_excess)[0]),
            "spearman_per_baseline_patient": float(spearmanr(mid / g.patients_2024, g.observed_excess / g.patients_2024)[0]),
            "share_observed_excess_positive": float((g.observed_excess > 0).mean()), "share_predicted_positive": float((mid > 0).mean()),
            "observed_inside_80_interval_params_only": float(((g.observed_excess >= lo) & (g.observed_excess <= hi)).mean()),
            "observed_inside_80_interval_with_count_noise": float(((g.observed_excess >= wlo) & (g.observed_excess <= whi)).mean()),
            "median_ratio_observed_to_predicted_where_both_positive": float((g.observed_excess / mid)[both].median()),
            "predicted_over_observed_median": float(mid.median() / g.observed_excess.median()),
        }

    full = score(e, 1.0)
    out = {
        "new_sites_in_window": int(len(new_sites)), "new_sites_of_2024_grantees": int(len(grantee)), "sites_evaluated": int(len(e)),
        "median_observed_raw_change": float(e.observed_change.median()), **full,
        "exposure_median": float(e.exposure.median()), "exposure_min": float(e.exposure.min()), "exposure_max": float(e.exposure.max()),
        "exposure_scaled": score(e, e.exposure), "added_by_march_31": score(e[e.added <= "2025-03-31"], 1.0),
        "added_by_march_31_exposure_scaled": score(e[e.added <= "2025-03-31"], e.exposure[e.added <= "2025-03-31"]),
        "bootstrap_sets_2024": int(len(boots24)),
        "note": "Sites added in the first half of 2025 serve part of the 2025 reporting year only; the exposure-scaled rows multiply each prediction by the "
                "share of the year in scope, and the model still runs high. Sites that closed are missing from HRSA's October 2026 list, which also shifts "
                "the competition around the 2025 additions.",
    }
    return out, e


# ------------------------------------------------------------------ E: HRSA's published penetration
def check_hrsa(zcta, uns, table):
    u = uns[uns.zip == uns.zcta].drop_duplicates("zcta").set_index("zcta")
    t = table.join(u[["pen_low", "pen_total", "uns"]])
    ok = (t["low"] > 500) & t.pen_low.notna() & (t.pen_low > 0) & (t.pen_p50 > 0)
    ratio = t.pen_p50[ok] / t.pen_low[ok]
    ok_tot = (t["pop"] > 500) & t.pen_total.notna() & (t.pen_total > 0) & (t.patients_total > 0)
    ratio_tot = (t.patients_total / t["pop"])[ok_tot] / t.pen_total[ok_tot]
    # largest gaps among bigger ZCTAs
    big = t[ok & (t["low"] > 2000)].assign(ratio=ratio)
    big["lr"] = np.abs(np.log(big.ratio))
    hp = uns.drop_duplicates("zip").set_index("zip").hrsa_pop
    worst = []
    for z, r in big.nlargest(10, "lr").iterrows():
        implied = float(r.pen_total * hp.get(z, np.nan)) if z in hp.index else float("nan")
        worst.append({"zcta": z, "state": r.state, "low_income": int(r["low"]), "ours": round(float(r.pen_p50), 3), "hrsa": round(float(r.pen_low), 3), "ratio": round(float(r.ratio), 2),
                      "our_patients": int(round(r.patients_total)), "hrsa_implied_patients": None if implied != implied else int(round(implied))})
    states = pd.Series([w["state"] for w in worst]).value_counts().to_dict()
    us = t.dropna(subset=["uns"])
    notp = t.notpat_p50
    return {
        "zctas_compared_low_income_penetration": int(ok.sum()), "pearson_low_income_penetration": float(np.corrcoef(t.pen_p50[ok], t.pen_low[ok])[0, 1]),
        "zctas_compared_without_small_zips": int((ok & (t["low"] >= 1000)).sum()),  # the ZIP table leaves reach blank under 1,000 low-income residents
        "pearson_low_income_penetration_without_small_zips": float(np.corrcoef(t.pen_p50[ok & (t["low"] >= 1000)], t.pen_low[ok & (t["low"] >= 1000)])[0, 1]),
        "spearman_low_income_penetration": float(spearmanr(t.pen_p50[ok], t.pen_low[ok])[0]), "median_ratio_ours_to_hrsa": float(ratio.median()),
        "ratio_p10": float(ratio.quantile(0.1)), "ratio_p90": float(ratio.quantile(0.9)),
        "zctas_compared_total_population_penetration": int(ok_tot.sum()), "pearson_total_population_penetration": float(np.corrcoef((t.patients_total / t["pop"])[ok_tot], t.pen_total[ok_tot])[0, 1]),
        "median_ratio_total_population": float(ratio_tot.median()),
        "spearman_not_patients_count_vs_hrsa_uns": float(spearmanr(notp[us.index], us.uns)[0]),
        "spearman_not_patients_share_vs_hrsa_uns": float(spearmanr((1 - t.pen_p50)[us.index], us.uns)[0]),
        "largest_disagreements": worst, "largest_disagreements_by_state": {k: int(v) for k, v in states.items()},
        "largest_disagreements_ours_higher": int(sum(w["ratio"] > 1 for w in worst)),
        "note": "HRSA's published penetration is computed from the same UDS patients-by-ZIP table, so agreement checks our ZIP-to-ZCTA joins, the crosswalk and the "
                "denominators. It does not check the model. Our low-income penetration sits below HRSA's by about the income share we apply to patients (median_ratio_ours_to_hrsa); "
                "HRSA does not scale its numerator.",
    }


# ------------------------------------------------------------------ F: sensitivity
def top_overlap(a, b, k=50):
    return int(len(set(a[:k]) & set(b[:k])))
