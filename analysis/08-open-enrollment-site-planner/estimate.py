"""Run the model county by county: draws, calibration, SAHIE benchmark, tiers, summaries, and each county's plan inflation factor."""
import numpy as np
import pandas as pd

import sae
import sites
import tiers
from common import DEFAULT_TIERS, K, TIERS



def county_slices(t):
    c = t.county.to_numpy()
    starts = np.flatnonzero(np.r_[True, c[1:] != c[:-1]])
    ends = np.r_[starts[1:], len(c)]
    return {c[s]: np.arange(s, e) for s, e in zip(starts, ends)}


def direct_tiers(t, rows, frac_A, shares, expansion, state, kid_hi):
    """Tier counts from the survey's own tract counts (one 'draw'), for the strategies that rank on direct numbers."""
    cnt = {tg: t[f"{tg}_u"].to_numpy()[rows][:, None] for tg in ("kids", "L", "C", "D")}
    return tiers.make_tiers(cnt, frac_A, shares, expansion, state, kid_hi)


def scale_interval(mean, lo, hi, f):
    """Widen (or narrow) a tract's interval around its mean by the factor f."""
    return mean - f * (mean - lo), mean + f * (hi - mean)


def run(t, nbr, sahie, venues, orr, model=None, K_=K, seed=1, calibrate=True, benchmark=True, use_sahie=True, odds_scale=1.0,
        keep=(), keep_tiers=None, tract_scale=None, split=None, verbose=True):
    """Returns (tract table, county table, kept draws, model, county draw sums). `keep` is a set of county FIPS whose elig
    draws are kept in memory; `keep_tiers` is one county whose draws of every tier are kept too. `tract_scale` maps a tier (or "L", the
    adults at or below 138%) to the factor that widens its tract-level 90% interval around the tract mean (found by validation D); county and
    national intervals are not scaled."""
    tract_scale = tract_scale or {}
    # split: (share under 100% of poverty, share of children at 400%+) held fixed; the simulation passes the truth's, because it
    # simulates the four targets only and the real table's cells for the split would not match the simulated totals
    rng = np.random.default_rng(seed)
    if model is None:
        model = sae.Model(t, nbr).fit(use_sahie=use_sahie)
    tiers.prepare_model(model, t)
    model.start_draws(rng, K_)
    frac_A, kid_hi = split if split is not None else (tiers.split_fraction(t), tiers.kids_hi_share(t))
    shares = tiers.noncitizen_shares(t, orr, odds_scale)
    sl = county_slices(t)
    vgroups = {c: g for c, g in venues.groupby("county")}
    cols = {}
    names = list(TIERS) + ["elig"]
    for nm in names:
        for stat in ("mean", "q05", "q50", "q95"):
            cols[f"{nm}_{stat}"] = np.zeros(len(t), np.float32)
    for nm in ("elig_direct", "elig_rate_direct", "rate_lo", "rate_hi", "rate_mid", "bandL_mean", "bandL_q05", "bandL_q95",
               "bandA_mean", "bandB_mean", "bandC_mean", "bandD_mean", "bandKids_mean", "nb_L", "nb_C", "nb_D", "nb_kids", "elig_sd"):
        cols[nm] = np.zeros(len(t), np.float32)
    cols["can_rank"] = np.zeros(len(t), np.int8)
    crow, kept = [], {}
    dsum = {nm: np.zeros((len(sl), K_), np.float32) for nm in names}  # per-county sums of every draw, for national and state intervals
    n_sites_ctx = {}
    pop_all = t.pop_all.to_numpy(float)
    for ci, (c, rows) in enumerate(sl.items()):
        state = t.state.to_numpy()[rows[0]]
        expansion = bool(t.expansion.to_numpy()[rows[0]])
        cnt, fac = tiers.county_counts(model, t, rows, rng, K=K_, calibrate=calibrate)
        sf = {"L": 1.0, "C": 1.0, "kids": 1.0, "D": 1.0}
        for tg, nb in (("L", "nb_L"), ("C", "nb_C"), ("D", "nb_D"), ("kids", "nb_kids")):  # calibrated means before the SAHIE benchmark
            cols[nb][rows] = cnt[tg].mean(1)
        if benchmark and c in sahie.index:
            sf = tiers.sahie_adjust(cnt, sahie.loc[c], len(rows))
        td = tiers.make_tiers(cnt, frac_A[rows], {b: shares[b][rows] for b in shares}, expansion, state, kid_hi[rows])
        td["elig"] = sum(td[x] for x in DEFAULT_TIERS)
        for nm in names:
            m, q05, q50, q95 = tiers.summarize(td[nm])
            if tract_scale.get(nm, 1.0) != 1.0:
                q05, q95 = scale_interval(m, q05, q95, tract_scale[nm])
            cols[f"{nm}_mean"][rows], cols[f"{nm}_q05"][rows], cols[f"{nm}_q50"][rows], cols[f"{nm}_q95"][rows] = m, q05, q50, q95
        cols["elig_sd"][rows] = td["elig"].std(1)  # the page's plan range uses it
        cols["bandL_mean"][rows] = cnt["L"].mean(1)
        cols["bandA_mean"][rows], cols["bandB_mean"][rows] = cnt["L"].mean(1) * frac_A[rows], cnt["L"].mean(1) * (1 - frac_A[rows])
        cols["bandC_mean"][rows], cols["bandD_mean"][rows], cols["bandKids_mean"][rows] = cnt["C"].mean(1), cnt["D"].mean(1), cnt["kids"].mean(1)
        lq = np.quantile(cnt["L"], [0.05, 0.95], axis=1)
        cols["bandL_q05"][rows], cols["bandL_q95"][rows] = scale_interval(cnt["L"].mean(1), lq[0], lq[1], tract_scale.get("L", 1.0))
        dtd = direct_tiers(t, rows, frac_A[rows], {b: shares[b][rows] for b in shares}, expansion, state, kid_hi[rows])
        de = sum(dtd[x] for x in DEFAULT_TIERS)[:, 0]
        cols["elig_direct"][rows] = de
        den = t.kids_n.to_numpy()[rows] + t.L_n.to_numpy()[rows] + t.C_n.to_numpy()[rows]
        cols["elig_rate_direct"][rows] = np.where(den > 0, de / np.maximum(den, 1), 0.0)
        rate = td["elig"] / np.maximum(pop_all[rows], 1)[:, None]
        rq = np.quantile(rate, [0.05, 0.5, 0.95], axis=1)
        med = np.median(rq[1][pop_all[rows] > 0]) if (pop_all[rows] > 0).any() else 0.0
        cols["rate_lo"][rows], cols["rate_mid"][rows], cols["rate_hi"][rows] = rq
        cols["can_rank"][rows] = ((pop_all[rows] > 0) & ((rq[0] > med) | (rq[2] < med))).astype(np.int8)  # unscaled draws
        # plan context: candidate venues, radius, inflation factor
        r_miles = sites.county_radius(t.density_class.to_numpy()[rows], pop_all[rows])
        infl, n_venues = 1.0, 0
        if c in vgroups:
            vg = vgroups[c]
            n_venues = len(vg)
            if n_venues >= 2:
                a = sites.reach_matrix(t.lat.to_numpy()[rows], t.lon.to_numpy()[rows], vg.lat.to_numpy(), vg.lon.to_numpy(), r_miles)
                infl = sites.inflation_factor(a, td["elig"].mean(1), td["elig"])
        if c in keep:
            kept[c] = {"elig": td["elig"].astype(np.float32), "rows": rows}
        if c == keep_tiers:
            kept[c] = {**kept.get(c, {"rows": rows}), "tiers": {nm: td[nm].astype(np.float32) for nm in names}}
        row = {"county": c, "state": state, "radius_miles": r_miles, "venues": n_venues, "plan_inflation": infl}
        for tg in ("kids", "L", "C", "D"):
            row[f"calib_{tg}"] = fac[tg]
            row[f"sahie_factor_{tg}"] = sf[tg]
        for nm in names:
            s = td[nm].sum(0)
            dsum[nm][ci] = s
            row[f"{nm}_mean"], row[f"{nm}_q05"], row[f"{nm}_q95"] = s.mean(), *np.quantile(s, [0.05, 0.95])
        for tg in ("kids", "L", "C", "D"):  # band totals (all citizenship), for comparison with SAHIE
            bt = cnt[tg].sum(0)
            row[f"band_{tg}_mean"], row[f"band_{tg}_q05"], row[f"band_{tg}_q95"] = bt.mean(), *np.quantile(bt, [0.05, 0.95])
            row[f"band_{tg}_n"] = float(model.n[tg][rows].sum())
            row[f"band_{tg}_direct"] = float(t[f"{tg}_u"].to_numpy()[rows].sum())
        row["elig_direct"] = float(de.sum())
        crow.append(row)
        if verbose and ci % 500 == 0:
            print(f"  county {ci}/{len(sl)}", flush=True)
    tr = pd.DataFrame(cols, index=t.index)
    return tr, pd.DataFrame(crow).set_index("county"), kept, model, dsum
