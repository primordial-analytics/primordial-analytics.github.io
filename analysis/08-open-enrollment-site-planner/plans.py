"""Compare ways to choose k sites on the same people, and check the planner's own approximations.

Strategies, all scored by the reach rule in sites.py on the model's expected eligible people (the optimiser's own
objective, so it wins by construction; validation E1 is the independent check):
  rate    take the k tracts with the highest direct eligible RATE (among tracts with 100+ people in the cells counted), site at
          the nearest unused venue
  direct  the k tracts with the highest direct eligible COUNT, same siting
  model   the k tracts with the highest modelled eligible count, same siting
  direct_sep  the direct-count order again, but a venue closer than R to one already chosen is skipped (tests whether spacing
          alone explains the optimiser's gain)
  best    the greedy rule over all venues (what the browser runs), and the exact optimum from a mixed-integer program
The same four are also run with a pop-up at the tract centre in place of a venue (candidate sites are then the 150 tracts
with the most eligible people).
"""
import numpy as np
import pandas as pd

import sites
from common import SEED

K_SITES = 5
MIN_VENUES = 8
MIN_DENOM = 100


def context(t, tr, venues, county, rows=None):
    rows = np.flatnonzero(t.county.to_numpy() == county) if rows is None else rows
    vg = venues[venues.county == county]
    R = sites.county_radius(t.density_class.to_numpy()[rows], t.pop_all.to_numpy()[rows])
    lat, lon = t.lat.to_numpy()[rows], t.lon.to_numpy()[rows]
    return rows, vg, R, lat, lon


def strategies(w, w_direct, rate_direct, denom, a, d_site, vv, R, k=K_SITES, with_exact=True, time_limit=20.0):
    """Reach of each strategy on weights w. a: tracts x sites reach, d_site: tracts x sites distances (for nearest-unused),
    vv: venue-to-venue distances (miles, with the circuity factor), R: the county's travel distance."""
    order_rate = np.argsort(-np.where(denom >= MIN_DENOM, rate_direct, -1))
    order_direct = np.argsort(-w_direct)
    order_model = np.argsort(-w)
    out = {}
    for name, order in (("rate", order_rate), ("direct", order_direct), ("model", order_model)):
        out[name] = sites.reach(a, w, sites.nearest_unused(d_site, order, k))
    sep = sites.nearest_unused(d_site, order_direct, k, vv, R)
    out["direct_sep"] = sites.reach(a, w, sep)
    g = sites.greedy(a, w, k)
    out["greedy"] = sites.reach(a, w, g)
    # the same two plans with the competing-site discount switched off (every site counts in full)
    out["nocap_greedy"] = float(w @ a[:, g].sum(1)) if g else 0.0
    out["nocap_direct"] = float(w @ a[:, sites.nearest_unused(d_site, order_direct, k)].sum(1))
    out["greedy_direct"] = sites.reach(a, w, sites.greedy(a, w_direct, k))  # the optimiser fed the survey's own counts
    out["top3_has_top_rate"] = int(order_rate[0] in set(order_model[:3]))
    if with_exact:
        sel, val, opt, gap = sites.exact(a, w, k, time_limit)
        out["exact"], out["exact_optimal"], out["exact_gap"] = val, opt, gap
    return out


def compare(t, tr, venues, counties, k=K_SITES, exact_counties=(), verbose=True):
    rows_out = []
    for i, c in enumerate(counties):
        rows, vg, R, lat, lon = context(t, tr, venues, c)
        w = tr.elig_mean.to_numpy(float)[rows]
        wd = tr.elig_direct.to_numpy(float)[rows]
        rd = tr.elig_rate_direct.to_numpy(float)[rows]
        den = t.kids_n.to_numpy()[rows] + t.L_n.to_numpy()[rows] + t.C_n.to_numpy()[rows]
        total = w.sum()
        # venues
        a = sites.reach_matrix(lat, lon, vg.lat.to_numpy(), vg.lon.to_numpy(), R)
        d_site = sites.CIRCUITY * sites.haversine_miles(lat, lon, vg.lat.to_numpy(), vg.lon.to_numpy())
        vv = sites.CIRCUITY * sites.haversine_miles(vg.lat.to_numpy(), vg.lon.to_numpy(), vg.lat.to_numpy(), vg.lon.to_numpy())
        r = strategies(w, wd, rd, den, a, d_site, vv, R, k, with_exact=c in exact_counties)
        row = {"county": c, "state": t.state.to_numpy()[rows[0]], "tracts": len(rows), "venues": len(vg), "radius": R, "eligible_total": total,
               "population": float(t.pop_all.to_numpy()[rows].sum()), "expansion": int(t.expansion.to_numpy()[rows[0]])}
        row.update({f"venue_{k_}": v for k_, v in r.items()})
        # pop-up at tract centres: candidates are the 150 tracts with the most modelled eligible people
        cand = np.argsort(-w)[:150]
        at = sites.reach_matrix(lat, lon, lat[cand], lon[cand], R)
        pos = {int(j): n for n, j in enumerate(cand)}
        def tract_sites(order):
            sel = [pos[int(j)] for j in order if int(j) in pos][:k]
            return sel
        order_rate = np.argsort(-np.where(den >= MIN_DENOM, rd, -1))
        row["popup_rate"] = sites.reach(at, w, tract_sites(np.argsort(-np.where(np.isin(np.arange(len(w)), cand) & (den >= MIN_DENOM), rd, -1))))
        row["popup_direct"] = sites.reach(at, w, tract_sites(np.argsort(-np.where(np.isin(np.arange(len(w)), cand), wd, -1))))
        row["popup_model"] = sites.reach(at, w, tract_sites(np.argsort(-w)))
        row["popup_greedy"] = sites.reach(at, w, sites.greedy(at, w, k))
        row["popup_greedy_direct"] = sites.reach(at, w, sites.greedy(at, wd, k))
        rows_out.append(row)
        if verbose and i % 50 == 0:
            print(f"  plans {i}/{len(counties)}", flush=True)
    return pd.DataFrame(rows_out).set_index("county")


def pick_counties(t, venues, n=300):
    sz = t.groupby("county").size()
    vn = venues.groupby("county").size().reindex(sz.index).fillna(0)
    ok = sz[(vn >= MIN_VENUES)].sort_values(ascending=False)
    return list(ok.index[:n])
