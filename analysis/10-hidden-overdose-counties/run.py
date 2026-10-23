"""One command: download, fit, validate, write the county table, numbers.json and figures.

    python run.py                 # everything (about 25 minutes on 4 cores)
    python run.py --quick         # short chains, for a smoke test
    python run.py --states WA OR  # same model, county table limited to these states
"""
import argparse
import json
import pickle
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import data
import figures
import model
import page_numbers
import validate

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
CACHE = data.RAW / "cache"


def cached(name, fn, refresh):
    path = CACHE / f"{name}.pkl"
    if path.exists() and not refresh:
        return pickle.loads(path.read_bytes())
    CACHE.mkdir(parents=True, exist_ok=True)
    out = fn()
    path.write_bytes(pickle.dumps(out))
    return out


def summarize(t, d, eta, state_totals):
    """Per-county posterior summaries on the rate-per-100,000 scale."""
    draws = eta[np.linspace(0, len(eta) - 1, 2000).astype(int)]
    rate = np.exp(draws)  # eta is log(rate per 100,000)
    n = len(t)
    pop = t["pop"].values
    mu = rate * pop / 1e5
    state = t.state.values
    # state rate in each draw: modelled deaths over population in that state
    st_rate = np.empty_like(rate)
    for s in np.unique(state):
        m = state == s
        st_rate[:, m] = (mu[:, m].sum(1) / pop[m].sum() * 1e5)[:, None]
    ranks = (-rate).argsort(1).argsort(1) + 1            # 1 = highest rate in that draw
    top = ranks <= np.ceil(0.1 * n)
    return pd.DataFrame({
        "rate_median": np.median(rate, 0), "rate_lo90": np.quantile(rate, 0.05, 0),
        "rate_hi90": np.quantile(rate, 0.95, 0),
        "p_above_state": (rate > st_rate).mean(0), "p_top_decile": top.mean(0),
        "rank_median": np.median(ranks, 0), "rank_lo90": np.quantile(ranks, 0.05, 0),
        "rank_hi90": np.quantile(ranks, 0.95, 0),
    }, index=t.index), draws


def hidden_total(d, eta, rng, hi=9):
    """Posterior draws of total deaths in suppressed counties (latent counts, truncated to 1..hi)."""
    from scipy.stats import poisson
    draws = eta[np.linspace(0, len(eta) - 1, 1000).astype(int)][:, d["cens"]]
    mu = np.exp(draws + d["offset"][d["cens"]])
    f0, fh = np.exp(-mu), poisson.cdf(hi, mu)
    y = np.maximum(poisson.ppf(np.clip(f0 + rng.uniform(size=mu.shape) * (fh - f0), 0, 1 - 1e-12), mu), 1)
    return y.sum(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--end", default="2026-03", help="last month of the 12-month window, YYYY-MM")
    ap.add_argument("--refresh", action="store_true", help="re-download the NCHS files and refit")
    ap.add_argument("--states", nargs="*", help="limit the county table to these state abbreviations")
    ap.add_argument("--skip-validation", action="store_true")
    a = ap.parse_args()
    tag = ("quick_" if a.quick else "") + a.end + "_"
    fit_kw = dict(num_warmup=150, num_samples=150) if a.quick else dict(num_warmup=1000, num_samples=1000)
    OUT.mkdir(exist_ok=True)
    manifest = data.download(force=("county_od.csv", "state_od.json") if a.refresh else ())
    END = a.end
    PREV = f"{int(END[:4]) - 1}{END[4:]}"
    pop_year = min(2024, int(END[:4]) - 2)   # latest Census vintage in the file is July 2024
    t = data.county_table(END, pop_year)
    t25 = data.county_table(PREV, pop_year - 1)
    edges, _ = data.graph(t.index)
    st26, st25 = data.state_totals(END), data.state_totals(PREV)
    hi9 = np.full(len(t), 9)

    def fit_variant(name, constrain=True, pending=False, **kw):
        d = model.prepare(t, edges, t.status.values, hi9, st26, constrain=constrain, pending=pending)

        def go():
            f = model.fit(d, **fit_kw, **kw)
            f["n_constrained_states"] = int(len(d["con_state"]))
            f["constrained_states"] = [d["states"][i] for i in d["con_state"]]
            return f
        f = cached(tag + name, go, a.refresh)
        f["hidden_total"] = hidden_total(d, f["eta"], np.random.default_rng(1022))   # seeded here, not in the cache
        return f

    main_fit = fit_variant("main")
    d_main = model.prepare(t, edges, t.status.values, hi9, st26, constrain=True)
    summ, draws = summarize(t, d_main, main_fit["eta"], st26)

    variants = {"no_constraint": dict(constrain=False), "no_covariates": dict(use_covariates=False),
                "no_spatial": dict(use_spatial=False), "pending_adjusted": dict(pending=True)}
    fits = {"main": main_fit}
    for name, kw in variants.items():
        fits[name] = fit_variant(name, **kw)

    sup = (t.status == "censored").values
    sens = {}
    base_med = summ.rate_median.values
    for name, f in fits.items():
        s2, _ = summarize(t, d_main, f["eta"], st26)
        sens[name] = dict(
            median_abs_pct_change=float(np.median(np.abs(s2.rate_median.values[sup] / base_med[sup] - 1) * 100)),
            spearman_vs_main=float(pd.Series(s2.rate_median.values[sup]).corr(pd.Series(base_med[sup]), method="spearman")),
            median_width_ratio=float(np.median((s2.rate_hi90 - s2.rate_lo90).values[sup] / (summ.rate_hi90 - summ.rate_lo90).values[sup])),
            hidden_total_median=float(np.median(f["hidden_total"])),
            hidden_total_lo90=float(np.quantile(f["hidden_total"], 0.05)),
            hidden_total_hi90=float(np.quantile(f["hidden_total"], 0.95)),
            divergences=f["divergences"], hyper_rhat_max=f["hyper_rhat_max"], hyper_ess_min=f["hyper_ess_min"],
            eta_ess_min=f["eta_ess_min"], eta_rhat_max=f["eta_rhat_max"],
            sigma_median=float(np.median(f["params"]["sigma"])) if "sigma" in f["params"] else None,
            rho_median=float(np.median(f["params"]["rho"])) if "rho" in f["params"] else None,
            n_constrained_states=f["n_constrained_states"])
    coefs = {n: [float(np.median(main_fit["params"]["b"][:, i])), float(np.quantile(main_fit["params"]["b"][:, i], 0.05)),
                 float(np.quantile(main_fit["params"]["b"][:, i], 0.95))] for i, n in enumerate(main_fit["names"])}

    # Aggregate check with the model that did not see the state residual
    d_nc = model.prepare(t, edges, t.status.values, hi9, st26, constrain=False)
    agg = validate.aggregate(t, fits["no_constraint"]["eta"], d_nc, st26)

    val = {}
    if not a.skip_validation:
        for T in (20, 30):
            val[f"pseudo_{T}"] = cached(f"{tag}pseudo_{T}",
                                        lambda T=T: validate.pseudo_suppression(t, edges, st26, T, fit_kw), a.refresh)
        val["temporal"] = cached(f"{tag}temporal",
                                 lambda: validate.temporal(t, t25, edges, st25, st26, fit_kw), a.refresh)

    # ---- county table (the deliverable)
    run_date = date.today().isoformat()
    kind = np.where(t.status == "censored", "suppressed_1_to_9",
                    np.where(t.status == "missing", "suppressed_data_quality",
                             np.where(t.y == 0, "published_zero", "published")))
    pop = t["pop"].values
    cs = pd.DataFrame({
        "fips": t.index, "state": t.state.values, "county": t.county.values, "population": pop.astype(int),
        "nchs_urban_rural_2013": t.urban_rural.values, "count_status": kind,
        "published_deaths": np.where(t.status == "exact", t.y, np.nan),
        "published_rate_per_100k": np.where(t.status == "exact", t.y / pop * 1e5, np.nan).round(1),
        "hard_lo_per_100k": np.where(t.status == "censored", 1 / pop * 1e5, np.nan).round(1),
        "hard_hi_per_100k": np.where(t.status == "censored", 9 / pop * 1e5, np.nan).round(1),
        "rate_median_per_100k": summ.rate_median.values.round(1),
        "rate_lo90_per_100k": summ.rate_lo90.values.round(1),
        "rate_hi90_per_100k": summ.rate_hi90.values.round(1),
        "p_rate_above_state": summ.p_above_state.values.round(3),
        "p_top_decile": summ.p_top_decile.values.round(3),
        "rank_lo90": summ.rank_lo90.values.astype(int), "rank_hi90": summ.rank_hi90.values.astype(int),
        "pct_records_pending": t.pct_pending.values,
        "window_ending": END, "nchs_data_as_of": data.data_as_of(), "run_date": run_date,
    })
    cs.to_csv(OUT / "county_rates.csv", index=False)
    if a.states:
        cs[cs.state.isin(a.states)].to_csv(OUT / ("county_rates_" + "_".join(a.states) + ".csv"), index=False)

    # ---- numbers for the page, and figures
    results = dict(sensitivity=sens, coefficients=coefs, aggregate=agg, validation=val,
                   fit={k: v for k, v in main_fit.items() if k not in ("eta", "params", "names", "hidden_total")},
                   hidden_total=[float(np.median(main_fit["hidden_total"])), float(np.quantile(main_fit["hidden_total"], 0.05)),
                                 float(np.quantile(main_fit["hidden_total"], 0.95))])
    json.dump(results, open(OUT / "model_results.json", "w"), indent=1)
    cs.to_pickle(CACHE / "full_county_table.pkl")
    if not a.quick and not a.skip_validation:
        nums = page_numbers.build(cs, results, manifest, st26.sum())
        nums.update(run_date=run_date, window_ending=END, nchs_data_as_of=data.data_as_of())
        json.dump(nums, open(OUT / "numbers.json", "w"), indent=1)
        figures.main(cs, results)
    print("done")


if __name__ == "__main__":
    main()
