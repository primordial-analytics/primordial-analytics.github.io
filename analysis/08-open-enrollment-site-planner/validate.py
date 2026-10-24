"""Validation of the tract model. Each check is seeded separately and reports into numbers.json.

A. Masked-tract holdout: 20% of tracts with min_pop or more people (3,000 in the main run; any size in the second) are withheld at random and refit without them. The weight function and
   each county's pooled rate are fit on the tracts that were not withheld. A masked
   tract is scored if its own direct estimate is good enough to serve as a stand-in for truth (CV below 20%). The
   predictive interval is the model's 90% interval for the tract (covariates, neighbours and county only) plus the direct
   estimate's own sampling noise. Compared with PLACES alone and with the county rate.
"""
import numpy as np
import pandas as pd

import sae
import tiers
from common import K


def observe(counts, n, gvf, rng):
    """What the survey would report for true counts: a scaled Poisson with one 'unit' worth W persons, W taken from the
    weight function (var = W x count), so cells can read zero and the error is skewed as the survey's is."""
    W = gvf(n[:, None], counts / np.maximum(n[:, None], 1))[1]
    return W * rng.poisson(counts / W)


def holdout(t, nbr, seed=11, frac=0.2, K_=400, min_pop=3000, verbose=False):
    rng = np.random.default_rng(seed)
    big = (t.pop_all.to_numpy() >= max(min_pop, 1))
    mask = big & (rng.random(len(t)) < frac)
    model = sae.Model(t, nbr).fit(hold=mask)
    tiers.prepare_model(model, t)
    model.start_draws(rng, K_)
    county = t.county.to_numpy()
    pos = pd.Series(np.arange(len(t))).groupby(county).apply(lambda s: s.to_numpy())
    mrows = pd.Series(np.flatnonzero(mask)).groupby(county[mask]).apply(lambda s: s.to_numpy())
    res = {tg: [] for tg in ("L", "C", "kids", "D", "adults")}
    for c, dr in mrows.items():
        rows = pos[c]
        cnt, _ = tiers.county_counts(model, t, rows, rng, K=K_, draw_rows=dr)
        noisy = {tg: observe(cnt[tg], model.n[tg][dr], model.gvf[tg], rng) for tg in ("kids", "L", "C", "D")}
        noisy["adults"] = noisy["L"] + noisy["C"] + noisy["D"]
        cnt["adults"] = cnt["L"] + cnt["C"] + cnt["D"]
        for tg in res:
            u = t[f"{tg}_u" if tg != "adults" else "adult_u"].to_numpy()[dr]
            se = t[f"{tg}_se" if tg != "adults" else "adult_se"].to_numpy()[dr]
            n = model.n[tg][dr] if tg != "adults" else t.adult_n.to_numpy()[dr]
            q = np.quantile(noisy[tg], [0.05, 0.5, 0.95], axis=1)
            res[tg].append(pd.DataFrame({"geoid": t.index[dr], "county": c, "state": t.state.to_numpy()[dr], "region": t.region.to_numpy()[dr],
                                         "density_class": t.density_class.to_numpy()[dr], "u": u, "se": se, "n": n,
                                         "lo": q[0], "med": q[1], "hi": q[2], "mean": cnt[tg].mean(1)}))
    return {tg: pd.concat(v, ignore_index=True) for tg, v in res.items()}, mask


def baselines(res, t, mask):
    """Add two benchmark predictions for the masked tracts: PLACES alone (n-weighted regression of the rate on the PLACES
    rate and its missing flag) and the county's rate from the tracts that were not masked."""
    idx = pd.Series(np.arange(len(t)), index=t.index)
    X = np.column_stack([np.ones(len(t)), t.places.to_numpy() * 100, t.places_missing.to_numpy(float)])
    county = t.county.to_numpy()
    for tg in ("kids", "L", "C", "D"):
        n = t[f"{tg}_n"].to_numpy(float)
        u = t[f"{tg}_u"].to_numpy(float)
        ok = (~mask) & (n > 0)
        W = n[ok]
        beta = np.linalg.solve((X[ok] * W[:, None]).T @ X[ok], (X[ok] * W[:, None]).T @ (u[ok] / n[ok]))
        cu = pd.Series(np.where(ok, u, 0)).groupby(county).transform("sum").to_numpy()
        cn = pd.Series(np.where(ok, n, 0)).groupby(county).transform("sum").to_numpy()
        x = res[tg]
        i = idx.reindex(x.geoid).to_numpy()
        x["pred_places"] = np.clip(X[i] @ beta, 0, 1) * n[i]
        x["pred_county"] = np.where(cn[i] > 0, cu[i] / np.maximum(cn[i], 1), 0) * n[i]


def top_decile_precision(x, col):
    """Share of the tracts a predictor puts in its top decile (by count) that are in the top decile of the reported counts."""
    k = max(len(x) // 10, 1)
    pred_top = set(x.nlargest(k, col).index)
    obs_top = set(x.nlargest(k, "u").index)
    return len(pred_top & obs_top) / k


def summarize_holdout(res, t):
    out = {}
    for tg, x in res.items():
        x = x[x.n > 0].reset_index(drop=True)  # a cell with nobody in it is not scored
        r = {"n_masked": int(len(x))}
        inside = (x.u >= x.lo) & (x.u <= x.hi)
        r["coverage90"] = float(inside.mean())
        r["coverage_by_region"] = {k: float(v) for k, v in inside.groupby(x.region).mean().items()}
        r["coverage_by_density"] = {{0: "rural", 1: "suburban", 2: "urban"}[int(k)]: float(v) for k, v in inside.groupby(x.density_class).mean().items()}
        good = (x.u > 0) & (x.se / x.u.clip(lower=1e-9) < 0.2)
        r["n_cv_under_20"], r["coverage90_cv_under_20"] = int(good.sum()), (float(inside[good].mean()) if good.sum() >= 20 else None)
        r["sum_reported"], r["sum_predicted"] = float(x.u.sum()), float(x["mean"].sum())
        if "pred_places" in x:
            for nm, col in (("model", "mean"), ("places_only", "pred_places"), ("county_rate", "pred_county")):
                r[f"rmse_{nm}"] = float(np.sqrt(((x[col] - x.u) ** 2).mean()))
                r[f"top_decile_precision_{nm}"] = top_decile_precision(x, col)
        out[tg] = r
    return out


def sahie_agreement(co, sahie):
    """Compare model county totals with SAHIE 2024. Interval overlap: the model's 90% interval for the county total against
    SAHIE's 90% margin. The rate gap is the model's uninsured rate in the group (ACS population) minus SAHIE's (SAHIE population),
    in percentage points. The log-count correlation is mostly county size and is kept only for reference."""
    out = {}
    for tg, key in (("L", "le138"), ("C", "b138_400"), ("kids", "kids")):
        s = sahie[[f"sahie_{key}_u", f"sahie_{key}_moe"]].reindex(co.index)
        ok = s[f"sahie_{key}_u"].notna() & (s[f"sahie_{key}_u"] > 0)
        lo, hi = s[f"sahie_{key}_u"] - s[f"sahie_{key}_moe"], s[f"sahie_{key}_u"] + s[f"sahie_{key}_moe"]
        overlap = (co[f"band_{tg}_q05"] <= hi) & (co[f"band_{tg}_q95"] >= lo)
        a, b = np.log1p(co[f"band_{tg}_mean"][ok]), np.log1p(s[f"sahie_{key}_u"][ok])
        gap = 100 * (co[f"band_{tg}_mean"] / co[f"band_{tg}_n"].clip(lower=1) - s[f"sahie_{key}_u"] / sahie[f"sahie_{key}_pop"].reindex(co.index).clip(lower=1))
        out[tg] = {"counties": int(ok.sum()), "interval_overlap_share": float(overlap[ok].mean()),
                   "corr_log_counts_mostly_county_size": float(np.corrcoef(a, b)[0, 1]),
                   "median_abs_rate_gap_points": float(gap[ok].abs().median()), "median_rate_gap_points": float(gap[ok].median()),
                   "median_sahie_rate_pct": float(100 * (s[f"sahie_{key}_u"] / sahie[f"sahie_{key}_pop"].reindex(co.index).clip(lower=1))[ok].median()),
                   "median_ratio_model_to_sahie": float((co[f"band_{tg}_mean"][ok] / s[f"sahie_{key}_u"][ok]).median()),
                   "total_model": float(co[f"band_{tg}_mean"][ok].sum()), "total_sahie": float(s[f"sahie_{key}_u"][ok].sum())}
    return out
