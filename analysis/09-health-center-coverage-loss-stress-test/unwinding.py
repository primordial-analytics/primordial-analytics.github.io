"""CMS Updated Renewal Outcomes (unwinding, 2023-03 to 2024-03): how states differ.

Used only for the spread between states, never for the level. Per state-month:
  ex parte share   = renewed ex parte (5a1) / (due (5) - pending (5d))
  paperwork loss   = terminated for procedural reasons (5c) / people who were not renewed
                     ex parte and had an outcome (5a2 + 5b + 5c)
State-months with fewer than 1,000 people in the denominator, and zero counts among 1,000 or more
(a reporting gap, not a rate), are dropped. Both are modeled on the logit scale as  y_sm = mu_m + u_s + e_sm  (month effect, state
effect u_s ~ N(0, tau^2), month noise e_sm ~ N(0, sigma^2)), fit by the method of
moments, with empirical-Bayes (partially pooled) state effects. Split-half correlation
of the state means, divided by the reliability of a half-window mean, gives the
persistence of a state's true position over the window.
"""
import numpy as np
import pandas as pd

from common import EXPANSION, OUT, RAW


MIN_N = 1000        # state-months with fewer people in the denominator are dropped


def logit(p):
    return np.log(p / (1 - p))


def fit(x, n, label):
    """x, n: DataFrames state x month (NaN where a state did not report that month)."""
    y = logit((x / n).clip(1e-4, 1 - 1e-4))
    y = y.sub(y.median(axis=0), axis=1)            # remove the common month effect
    T = y.notna().sum(axis=1)
    dev = y.sub(y.mean(axis=1), axis=0)
    sigma2 = float((dev ** 2).sum().sum() / (T - 1).sum())      # pooled within-state month variance
    ybar = y.mean(axis=1)
    tau2 = max(float(ybar.var(ddof=1) - (sigma2 / T).mean()), 1e-4)
    B = tau2 / (tau2 + sigma2 / T)                 # weight on each state's own mean
    u = B * (ybar - ybar.mean())
    sd = np.sqrt(B * sigma2 / T)
    cols = list(y.columns)
    h1, h2 = y[cols[: len(cols) // 2]], y[cols[len(cols) // 2:]]
    ok = (h1.notna().sum(axis=1) >= 3) & (h2.notna().sum(axis=1) >= 3)
    split = float(np.corrcoef(h1[ok].mean(axis=1), h2[ok].mean(axis=1))[0, 1])
    t_half = float((h1[ok].notna().sum(axis=1).mean() + h2[ok].notna().sum(axis=1).mean()) / 2)
    reliability = tau2 / (tau2 + sigma2 / t_half)  # reliability of one half-window state mean
    persistence = float(min(split / reliability, 1.0))
    pooled = float(np.nansum(x.to_numpy()) / np.nansum(n.to_numpy()))
    tbl = pd.DataFrame({f"{label}_u": u, f"{label}_u_sd": sd, f"{label}_raw": x.sum(axis=1) / n.where(x.notna()).sum(axis=1)})
    return tbl, {f"{label}_tau": float(np.sqrt(tau2)), f"{label}_sigma_month": float(np.sqrt(sigma2)),
                 f"{label}_mean_shrink_weight": float(B.mean()), f"{label}_split_half_r": split, f"{label}_persistence": persistence,
                 f"{label}_pooled": pooled, f"{label}_split_half_states": int(ok.sum())}


def main():
    d = pd.read_csv(RAW / "renewals.csv")
    d.columns = [c.strip() for c in d.columns]
    key = {"(Metric 5)": "due", "(Metric 5a1)": "ex", "(Metric 5a2)": "form", "(Metric 5b)": "inel",
           "(Metric 5c)": "proc", "(Metric 5d)": "pend"}
    d["m"] = d["Metric name"].str.strip().map(lambda s: next((v for k, v in key.items() if s.endswith(k)), None))
    d = d.dropna(subset=["m"])
    d["Value"] = pd.to_numeric(d["Value"].astype(str).str.replace(",", ""), errors="coerce")
    w = d.pivot_table(index=["State", "Reporting period"], columns="m", values="Value", aggfunc="first").reset_index()
    w = w.dropna(subset=["due", "ex", "form", "inel", "proc", "pend"])
    w = w[(w.due > 0) & w.State.isin(EXPANSION)]
    w["decided"] = w.due - w.pend
    w["asked"] = w.form + w.inel + w.proc
    w = w[(w.decided > 0) & (w.asked > 0)]
    months = w.groupby("State")["Reporting period"].nunique()
    w = w[w.State.isin(months[months >= 6].index)]      # at least six reporting months
    tabs, comps = [], {}
    for label, num, den in [("ex", "ex", "decided"), ("proc", "proc", "asked")]:
        x = w.pivot(index="State", columns="Reporting period", values=num)
        n = w.pivot(index="State", columns="Reporting period", values=den)
        small = n < MIN_N                   # a rate from a few dozen people (Hawaii late 2023) is noise, not a month
        comps[f"{label}_small_months_dropped"] = int(small.sum().sum())
        zero = (x == 0) & ~small            # a zero count among 1,000+ people is a gap in reporting, not a rate
        comps[f"{label}_zero_months_dropped"] = int(zero.sum().sum())
        x, n = x.mask(small | zero), n.mask(small | zero)
        t, c = fit(x, n, label)
        tabs.append(t)
        comps.update(c)
    st = pd.concat(tabs, axis=1).reset_index().rename(columns={"State": "state"})
    st.to_csv(OUT / "unwinding_state.csv", index=False, float_format="%.5g")
    comps["states_in_fit"] = int(len(st))
    comps["months"] = int(w["Reporting period"].nunique())
    tot = w[["due", "ex", "form", "inel", "proc", "pend"]].sum()
    comps["pooled_ex_parte_share_of_decided"] = float(tot.ex / (tot.due - tot.pend))
    by_state = w.groupby("State")[["proc", "due"]].sum()
    comps["proc_gross_share_of_due_max_state"] = float((by_state.proc / by_state.due).max())
    comps["proc_gross_share_of_due_min_state"] = float((by_state.proc / by_state.due).min())
    comps["pooled_proc_share_of_due"] = float(tot.proc / tot.due)
    comps["pooled_proc_share_of_asked"] = float(tot.proc / (tot.form + tot.inel + tot.proc))
    pd.Series(comps).to_json(OUT / "unwinding_summary.json", indent=1)
    print(pd.Series(comps).round(4).to_string())
    print(st.round(3).to_string())


if __name__ == "__main__":
    main()
