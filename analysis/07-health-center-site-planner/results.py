"""Turn the fits and the reach accounting into the ZIP table, the national and class aggregates, the screening table and the fixtures."""
import numpy as np
import pandas as pd

import model
import project
import reach

K_SCREEN = 5000  # patients a year for the screening columns of the ZIP table (new patients if a site sees this many)
UNDER = (0.10, 0.25)  # penetration thresholds (ours, named as such on the page)
CLASS_NAMES = ["rural", "suburban", "urban"]
PCT = (10, 50, 90)


def q3(a, axis=0, r=0):
    q = np.percentile(a, PCT, axis=axis)
    return [round(float(v), r) if r else int(round(float(v))) for v in q]


def national(zcta, L_draws, U_draws, lowd, pen):
    """National totals and the 'under X% reached' aggregates, each with a 10th-90th percentile range over the Monte Carlo draws."""
    L = L_draws.astype(np.float64)
    out = {"low_income_residents": {"point": int(zcta.low.sum()), "p10_p50_p90": q3(L.sum(0))},
           "uninsured_adults_below_200": {"point": int(zcta.unins_adult_low.sum()), "p10_p50_p90": q3(U_draws.sum(0))},
           "low_income_patients": {"p10_p50_p90": q3(lowd.sum(0))}}
    out["penetration"] = {"p10_p50_p90": q3(lowd.sum(0) / L.sum(0), r=4)}
    notp = np.clip(L_draws - lowd, 0, None)
    out["not_patients"] = {"p10_p50_p90": q3(notp.sum(0)), "note": "sum over ZIPs of low-income residents minus low-income patients, floored at 0 in each ZIP"}
    out["low_income_residents_minus_patients"] = {"p10_p50_p90": q3(L.sum(0) - lowd.sum(0)), "note": "national difference with no flooring; the floored sum is larger by the patients who live in ZIPs where they exceed residents"}
    out["low_income_patients_in_zips_exceeding_residents"] = {"p10_p50_p90": q3(np.clip(lowd - L_draws, 0, None).sum(0))}
    small = (zcta.low < 1000).to_numpy()
    out["small_zctas"] = {"count": int(small.sum()), "low_income_residents": int(zcta.low[small].sum()), "share_of_residents_pct": round(100 * zcta.low[small].sum() / zcta.low.sum(), 2)}
    campus = (zcta.college_pct >= reach.CAMPUS_COLLEGE_PCT).to_numpy() & ~small
    out["campus_zctas"] = {"count": int(campus.sum()), "low_income_residents": int(zcta.low[campus].sum()), "share_of_residents_pct": round(100 * zcta.low[campus].sum() / zcta.low.sum(), 2)}
    for t in UNDER:
        m = pen < t
        key = f"under_{int(t * 100)}pct"
        out[key] = {"zctas": q3(m.sum(0)), "low_income_residents": q3((L_draws * m).sum(0)), "uninsured_adults_below_200": q3((U_draws * m).sum(0)),
                    "share_of_residents_pct": q3(100 * (L_draws * m).sum(0) / L.sum(0), r=1),
                    "not_patients": q3((notp * m).sum(0))}
        ms = m[~small]
        out[key + "_excluding_small"] = {"low_income_residents": q3((L_draws[~small] * ms).sum(0)), "zctas": q3(ms.sum(0))}
    by = {}
    for k, name in enumerate(CLASS_NAMES):
        c = (zcta.dclass == k).to_numpy()
        m25 = pen[c] < UNDER[1]
        Lc = L_draws[c]
        by[name] = {"zctas": int(c.sum()), "low_income_residents": int(zcta.low[c].sum()),
                    "penetration_p10_p50_p90": q3(lowd[c].sum(0) / Lc.sum(0), r=4), "not_patients": q3(notp[c].sum(0)),
                    "residents_in_zctas_under_25pct": q3((Lc * m25).sum(0)), "share_in_zctas_under_25pct_pct": q3(100 * (Lc * m25).sum(0) / Lc.sum(0), r=1),
                    "share_in_zctas_under_10pct_pct": q3(100 * (Lc * (pen[c] < UNDER[0])).sum(0) / Lc.sum(0), r=1)}
    out["by_density_class"] = by
    return out


def under_threshold_sensitivity(zcta, patients, L_draws, lowd):
    """Residents in ZIPs where under X% of low-income residents are patients, under the choices that move it more than ACS error does:
    the threshold (ours), and whether each center's patients are scaled to its low-income share (assumes a center's ZIP mix equals its mix)."""
    k = patients["total"].shape[1]
    unscaled = patients["total"].astype(np.float32)[:, np.arange(L_draws.shape[1]) % k]
    out = {}
    for label, pat in (("patients_scaled_to_income_share", lowd), ("patients_not_scaled", unscaled)):
        pen = pat / np.maximum(L_draws, 1)
        out[label] = {f"under_{int(t * 100)}pct": {"low_income_residents": q3((L_draws * (pen < t)).sum(0)), "zctas": q3((pen < t).sum(0))} for t in (0.10, 0.20, 0.25, 0.30)}
    return out


def nearest_site_miles(data, zcta):
    from scipy.spatial import cKDTree
    t = cKDTree(model.xyz(data.sites.lat.to_numpy(), data.sites.lon.to_numpy()))
    dist, _ = t.query(model.xyz(zcta.lat.to_numpy(), zcta.lon.to_numpy()))
    return 2 * model.MILES * np.arcsin(np.clip(dist / 2, 0, 1))


def centers_per_zcta(d):
    r = d["cells"]
    r = r[(r.total.fillna(0) > 0) | r.hid_total]
    return r.groupby("zcta").grant.nunique()


def zip_table(d, data, rt, mix, scr, sets_n):
    """The one-row-per-ZCTA table behind the page and the download. scr: output of project.screen for K_SCREEN, B sets.
    No uncapped patient volume is published: capacity is an input, the table gives who a site's patients would be."""
    z = d["zcta"]
    t = pd.DataFrame(index=z.index)
    t["state"], t["county"] = z.state, z.county.str.replace(r" (County|Parish)$", "", regex=True)
    t["density_class"] = np.array(CLASS_NAMES)[z.dclass.to_numpy()]
    t["residents"] = z["pop"].round().astype(int)
    t["low_income_residents"] = z.low.round().astype(int)
    t["low_income_moe90"] = (z.low_se * 1.645).round().astype(int)
    t["uninsured_adults_below_200"] = z.unins_adult_low.round().astype(int)
    t["centers_with_patients"] = centers_per_zcta(d).reindex(z.index).fillna(0).astype(int)
    t["nearest_site_miles"] = nearest_site_miles(data, z).round(1)
    t["patients_all_centers"] = rt.patients_total.round().astype(int)
    t["low_income_patients"] = rt.patients_low.round().astype(int)
    none = (t.patients_all_centers == 0) & (t.centers_with_patients == 0)  # no center reports a patient here (they may sit in 'Other ZIP Codes')
    blank = rt.small.to_numpy() | none.to_numpy()  # a ratio over a few hundred residents, or over zero patients, says little
    per100 = (100 * rt.patients_total / z["pop"].clip(lower=1)).round(1)
    t["patients_per_100_residents"] = per100.where(~blank)
    for q in ("p10", "p50", "p90"):
        t[f"penetration_{q}"] = rt[f"pen_{q}"].round(3).where(~blank)
    for q in ("p10", "p50", "p90"):
        t[f"not_patients_{q}"] = rt[f"notpat_{q}"].round().astype(int)
    hr = d["uns"][d["uns"].zip == d["uns"].zcta].drop_duplicates("zcta").set_index("zcta").pen_low.reindex(z.index)
    t["hrsa_published_penetration"] = hr.round(3)
    ratio = (rt.pen_p50 / hr).where((hr > 0) & ~rt.small)
    t["ratio_to_hrsa"] = ratio.round(2)
    t["hrsa_disagrees"] = ((ratio < 0.5) | (ratio > 2)).astype(int)
    t["over_100pct"] = (rt.pen_p50 > 1).astype(int)
    t["no_patients_reported"] = none.astype(int)
    t["small_zip"] = rt.small.astype(int)
    t["college_students_pct"] = z.college_pct.round(1)
    t["campus_zip"] = rt.campus.astype(int)
    ok = ~(rt.small | rt.campus)
    t["rank_people"] = rt.notpat_p50.where(ok).rank(ascending=False, method="min").astype("Int64")
    t["rank_share"] = rt.pen_p50.where(ok).rank(ascending=True, method="min").astype("Int64")
    sh = np.nan_to_num(scr["share_new"], nan=0.0)
    for q, p in zip(("p10", "p50", "p90"), PCT):
        t[f"site_share_new_{q}"] = np.percentile(sh, p, axis=0).round(3)
    for q, p in zip(("p10", "p50", "p90"), PCT):
        t[f"site_new_patients_at_{K_SCREEN}_{q}"] = np.percentile(np.nan_to_num(scr["new"]), p, axis=0).round().astype(int)
    t["site_capacity_binds"] = (np.percentile(scr["draw_uncapped"], 10, axis=0) > K_SCREEN).astype(int)
    pm = np.nanmedian(project.payer_shares(scr["pay"]), axis=0)
    for j, p in enumerate(project.PAYERS):
        t[f"site_payer_{p}"] = pm[:, j].round(3)
    return t


def screening(zp, zd, sets, theta_type, K=K_SCREEN, payer_sets=100):
    """Uncapped draws (so any K can be applied later), capped draws for K, shares and payer counts, for every candidate ZCTA."""
    big = project.screen(zp, zd, sets, theta_type, K=1e12, payer_sets=payer_sets)
    out = {"draw_uncapped": big["draw"], "share_new": np.where(big["draw"] > 0, big["new"] / np.maximum(big["draw"], 1e-9), np.nan), "pay": big["pay"],
           "new_uncapped": big["new"]}
    out["draw"] = np.minimum(big["draw"], K)
    out["new"] = out["draw"] * out["share_new"]
    return out
