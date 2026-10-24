"""Noncitizen share of the uninsured by state and income band, from the ACS 2024 1-year person file.

The tract tables give noncitizen uninsured only for all ages and all incomes (B27020). To split each adult income
band we need to know whether, in a state, noncitizens are more or less common among the uninsured at that income than
among the uninsured overall. The odds ratio of the two shares (adult band versus all ages) does that. A state with fewer
than MIN_SAMPLE sampled uninsured noncitizen adults in a band borrows its Census division's ratio. Person weights
(PWGTP) only; uncertainty is carried by a plus or minus 30% odds sensitivity run instead of replicate weights.
"""
import numpy as np
import pandas as pd

from common import DIVISION, OUT, RAW, STATE_FIPS

BANDS = {"A": (0, 100), "B": (100, 138), "C": (138, 400), "D": (400, 10_000)}  # POVPIP, percent of poverty, [lo, hi)
SHRINK_K = 30.0  # pseudo-count of sampled noncitizens in the empirical-Bayes weight
OR_CAP = (0.2, 5.0)
USECOLS = ["STATE", "AGEP", "CIT", "HICOV", "POVPIP", "PWGTP"]


def _chunks():
    for f in sorted((RAW / "pums").glob("psam_pus*.csv")):
        yield from pd.read_csv(f, usecols=USECOLS, chunksize=500_000)


def tabulate():
    """Weighted and unweighted counts of uninsured people by state: all ages, and adults 19-64 by band; noncitizen = CIT 5."""
    acc = {}
    for d in _chunks():
        d = d[(d.HICOV == 2) & d.STATE.isin([int(k) for k in STATE_FIPS])].copy()
        d["state"] = d.STATE.map({int(k): v for k, v in STATE_FIPS.items()})
        d["nc"] = d.CIT == 5
        d["group"] = "all"
        parts = [d.assign(group="all")]
        ad = d[d.AGEP.between(19, 64) & d.POVPIP.notna()]
        for b, (lo, hi) in BANDS.items():
            parts.append(ad[(ad.POVPIP >= lo) & (ad.POVPIP < hi)].assign(group=b))
        x = pd.concat(parts)
        g = x.groupby(["state", "group"])
        s = pd.DataFrame({"w": g.PWGTP.sum(), "w_nc": x.PWGTP.where(x.nc, 0).groupby([x.state, x.group]).sum(),
                          "n": g.size(), "n_nc": x.nc.groupby([x.state, x.group]).sum()})
        acc = s if isinstance(acc, dict) else acc.add(s, fill_value=0)
    return acc


def ratios(tab):
    t = tab.reset_index()
    t["division"] = t.state.map(DIVISION)
    div = t.groupby(["division", "group"])[["w", "w_nc", "n", "n_nc"]].sum()
    odds = lambda p: p / (1 - p)
    logit = lambda p: np.log(p / (1 - p))
    rows = []
    for st in sorted(set(t.state)):
        all_s = t[(t.state == st) & (t.group == "all")].iloc[0]
        dv = DIVISION[st]
        all_d = div.loc[(dv, "all")]
        for b in BANDS:
            db = div.loc[(dv, b)]
            lor_div = logit(db.w_nc / db.w) - logit(all_d.w_nc / all_d.w)
            r = t[(t.state == st) & (t.group == b)]
            r = r.iloc[0] if len(r) else None
            if r is not None and 0 < r.n_nc < r.n:
                lor_st = logit(r.w_nc / r.w) - logit(all_s.w_nc / all_s.w)
                nn = r.n_nc
                w = nn / (nn + SHRINK_K)
                se = float(np.sqrt(1 / nn + 1 / (r.n - nn)))
                p_b, p_all = r.w_nc / r.w, all_s.w_nc / all_s.w
            else:
                lor_st, nn, w, se = lor_div, 0, 0.0, np.nan
                p_b, p_all = db.w_nc / db.w, all_d.w_nc / all_d.w
            orr = float(np.clip(np.exp(w * lor_st + (1 - w) * lor_div), *OR_CAP))
            rows.append({"state": st, "band": b, "share_in_band": p_b, "share_all_ages": p_all, "odds_ratio": orr, "weight_on_state": w,
                         "pooled_by_division": bool(w < 0.5), "sample_noncitizen_uninsured": int(nn), "se_log_odds_ratio_state_cell": se})
    return pd.DataFrame(rows)


def main():
    out = ratios(tabulate())
    out.to_csv(OUT / "pums_noncitizen_ratios.csv", index=False, float_format="%.5g")
    print(f"{len(out)} state-band ratios, {int(out.pooled_by_division.sum())} pooled by division")
    return out


if __name__ == "__main__":
    main()
