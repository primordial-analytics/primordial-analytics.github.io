"""Build assets/examples/09/data.json for the interactive page from output/*.

Run: python -I web_data.py   (also the last step of run.py)

Nothing is estimated here. Every value is copied from, or a plain ratio of, files in output/:
  state_ranges.csv, uds_state.csv, sobol_by_state.csv, sobol_median_across_states.csv,
  tornado_typical_state.csv, peer_benchmark.csv, peer_histogram.csv, numbers.json.
Derived values (each checked below):
  * lost adults per 1,000 Medicaid patients = lost_adults_at_centers_q / UDS Medicaid patients x 1,000
    (the state's modeled loss at its centers, put on the same per-1,000 basis as the dollar columns)
  * average Medicaid patients per center = UDS Medicaid patients / centers (the page's starting value)
  * reference lines for the ranked chart = medians of the state medians
It also prints the stat-tile strings the page's front matter uses.
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
DEST = HERE.parent.parent / "assets" / "examples" / "09" / "data.json"

# One plain-language line per model input, shown beside the Sobol bars. Text only; no numbers.
HINTS = {
    "eps_pd": "How many people your state's renewal process drops for paperwork, compared with other states.",
    "regime": "Which of CMS's four scenarios for checking work requirements applies to the state.",
    "eps_M": "What Medicaid pays your state's health centers per patient.",
    "kappa": "How Medicaid pay for adults compares with pay for all patients.",
    "f_ref": "How many of the state's Medicaid adults are in the expansion group.",
    "nc_noise": "How many people do not meet the work requirement.",
    "eps_ex": "How many renewals your state completes from its own data, compared with other states.",
    "ex_nat": "The share of members the state can verify from data it already holds.",
    "excl_mult": "How many adults are excluded or exempt from the requirement.",
    "r_keep": "The share of people who lose coverage but keep coming to the center.",
    "v_rel": "How often they visit after losing coverage, compared with before.",
    "eps_S": "What an uninsured patient pays at the center per year.",
    "hardship": "Whether the state adopts CMS's hardship exception.",
    "theta": "Loss among members the state verifies from data.",
}


# Plain-language names for the five inputs whose column label is analyst shorthand. Text only.
LABELS = {
    "eps_pd": "How many people the state drops for paperwork",
    "eps_ex": "How many renewals the state completes from data it holds",
    "ex_nat": "Share the state can verify from data it holds",
    "nc_noise": "Share who do not meet the rule",
    "regime": "How the state checks work requirements (CMS scenario)",
}

# One question a center can take to its state or its own records, for the inputs where one exists. Text only.
ASK = {
    "eps_pd": "Ask your state Medicaid agency how many people lose coverage at renewal because paperwork was not returned, and what it plans to change.",
    "regime": "Ask which of CMS's verification approaches your state will use, and when it starts.",
    "eps_M": "Check what Medicaid pays your center per patient. Your own figure is better than the state average.",
    "kappa": "Check how your Medicaid payments for adults compare with your payments for all patients.",
    "f_ref": "Check how many of your Medicaid adults are in the expansion group.",
    "eps_ex": "Ask what share of renewals your state completes from data it already holds.",
}


def r(x, n):
    return None if pd.isna(x) else round(float(x), n)


def trio(row, stem, n):
    return [r(row[f"{stem}_p{p}"], n) for p in (5, 50, 95)]


def main():
    st = pd.read_csv(OUT / "state_ranges.csv").set_index("state")
    uds = pd.read_csv(OUT / "uds_state.csv").set_index("state")
    sob = pd.read_csv(OUT / "sobol_by_state.csv")
    sob_med = pd.read_csv(OUT / "sobol_median_across_states.csv")
    tor = pd.read_csv(OUT / "tornado_typical_state.csv")
    bench = pd.read_csv(OUT / "peer_benchmark.csv")
    hist = pd.read_csv(OUT / "peer_histogram.csv")
    nums = json.loads((OUT / "numbers.json").read_text())
    ms = json.loads((OUT / "model_summary.json").read_text())

    st = st.sort_values("total_p50", ascending=False)
    mcd = uds["mcd_patients"].reindex(st.index)
    avg = (mcd / uds["centers"].reindex(st.index))

    # check: the per-1,000 basis implied by the exposure columns is the UDS Medicaid patient count
    implied = st.expansion_adults_at_centers_p50 / st.expansion_adults_per_1000_mcd_patients * 1000
    assert (implied / mcd - 1).abs().max() < 0.001, "Medicaid patient basis does not match uds_state.csv"

    states = []
    for a, row in st.iterrows():
        lost = [r(row[f"lost_adults_at_centers_p{p}"] / mcd[a] * 1000, 1) for p in (5, 50, 95)]
        states.append({
            "a": a, "n": row["name"],
            "t": trio(row, "total", 6),                   # share of expansion adults who lose coverage
            "w": trio(row, "work_req", 6),                # non-compliance part
            "p": trio(row, "paperwork", 6),               # administrative part
            "s": r(row["admin_share_of_loss_p50"], 4),    # administrative share of the loss, median
            "d": [int(round(v)) for v in trio(row, "net_loss_per_1000_mcd_patients", 0)],  # $ per year per 1,000 Medicaid patients
            "r": trio(row, "pct_of_total_revenue", 4),    # % of total revenue
            "m": trio(row, "pct_of_mcd_payments", 4),     # % of Medicaid payments
            "e": r(row["expansion_adults_per_1000_mcd_patients"], 1),
            "l": lost,                                    # lost adults per 1,000 Medicaid patients
            "c": int(round(avg[a])),                      # average Medicaid patients per center
        })

    order = list(sob_med[sob_med.output == "L"].sort_values("ST", ascending=False).input)
    labels = dict(zip(sob.input, sob.label))
    inputs = [{"k": k, "n": LABELS.get(k, labels[k]), "h": HINTS[k], "a": ASK.get(k)} for k in order]
    sobol = {}
    for a, g in sob.groupby("state"):
        sobol[a] = {}
        for out, key in (("L", "L"), ("pct_rev", "R")):
            t = g[g.output == out].set_index("input").reindex(order)
            sobol[a][key] = [[r(t.loc[k, "S1"], 4), r(t.loc[k, "ST"], 4)] for k in order]
    sobol_median = {}
    for out, key in (("L", "L"), ("pct_rev", "R")):
        t = sob_med[sob_med.output == out].set_index("input").reindex(order)
        sobol_median[key] = [[r(t.loc[k, "S1"], 4), r(t.loc[k, "ST"], 4)] for k in order]

    tornado = {}
    for out, key in (("L", "L"), ("pct_rev", "R")):
        t = tor[tor.output == out]
        scale = 100  # fractions in the file; the page shows percent
        tornado[key] = {"base": r(t.base.iloc[0] * scale, 4),
                        "rows": [{"k": x.input, "lo": r(x.p10 * scale, 4), "hi": r(x.p90 * scale, 4)} for x in t.itertuples()]}

    bands = []
    for x in bench.itertuples():
        bands.append({"size": x.size_band_patients, "set": x.setting, "n": int(x.centers_reporting_9d),
                      "ms": r(x.median_medicaid_share_of_patients, 4), "ea": int(round(x.median_expansion_adults_est)),
                      "d": [int(round(v, -2)) for v in (x.median_net_loss_usd_p5, x.median_net_loss_usd_p50, x.median_net_loss_usd_p95)],
                      "r": [r(v, 4) for v in (x.median_pct_of_total_revenue_p5, x.median_pct_of_total_revenue_p50, x.median_pct_of_total_revenue_p95)],
                      "o3": r(x.share_of_centers_losing_over_3pct_of_revenue_p50, 3)})
    histo = [[float(x.pct_from), float(x.pct_to), int(x.centers)] for x in hist.itertuples()]

    n = nums["national"]
    nb = nums["benchmark"]
    ne = nums["nebraska"]
    ex = nums["extremes"]
    val = nums["validation"]
    ref = {
        "adm_share": r(st.admin_share_of_loss_p50.median(), 3),
        "r": r(st.pct_of_total_revenue_p50.median(), 4),
        "d": int(round(st.net_loss_per_1000_mcd_patients_p50.median(), -2)),
        "t": r(st.total_p50.median(), 4),
    }
    assert abs(ref["adm_share"] - ex["paperwork_share_p50_median"]) < 0.001
    meta = {
        "cms": r(ms["cms_combined"], 4), "cms_fy27_m": r(ms["cms_fy2027_m"], 2),
        "nat": [r(n[f"model_national_loss_pct_p{p}"], 1) for p in (5, 50, 95)],
        "nat_nc": r(n["model_national_noncomp_pct_p50"], 1), "nat_adm": r(n["model_national_admin_pct_p50"], 1),
        "vs_cms": r(n["model_minus_cms_pts"], 1),
        "below_cms": r(n["share_of_draws_nat_below_cms"], 3),
        "typical": nums["national"]["typical_state"],
        "drivers": {"loss": nums["drivers"]["top_driver_count_loss"], "revenue": nums["drivers"]["top_driver_count_revenue"]},
        "ref": ref,
        "centers": {"adults": int(round(n["centers_expansion_adults_p50"], -3)),
                    "lost": [int(round(n[f"centers_lost_adults_p{p}"], -3)) for p in (5, 50, 95)],
                    "usd_b": [r(n[f"centers_net_loss_usd_p{p}"] / 1e9, 2) for p in (5, 50, 95)],
                    "admin_share": r(n["centers_admin_lost_adults_p50"] / n["centers_lost_adults_p50"], 3),
                    "n": int(nums["uds"]["expansion_centers"])},
        "bench": {"n": nb["benchmark_centers"], "reporting": int(nb["centers_expansion_reporting_9d"]), "dropped": int(nb["centers_dropped_by_filters"]), "med": r(nb["benchmark_pct_p50_median"], 2),
                  "p10": r(nb["benchmark_pct_p50_p10"], 3), "p90": r(nb["benchmark_pct_p50_p90"], 3),
                  "o3": r(nb["benchmark_share_over_3pct"], 3)},
        "ne": {"subj": [r(ne[f"ne_subject_loss_p{p}"] * 100, 1) for p in (5, 50, 95)],
               "half": [r(ne[f"ne_half_year_equiv_p{p}"] * 100, 1) for p in (5, 50, 95)],
               "obs": r(ne["ne_observed_renewal_loss"] * 100, 1)},
        "uds": {"centers": int(val["centers_all"]), "reporting": int(val["reporting_centers_all"]),
                "not_reporting": int(val["centers_not_reporting_9d"]), "exp_share": r(nums["assumptions"]["expansion_share_prior_mean"], 2),
                "keep": r(nums["assumptions"]["keep_coming_mean"], 2)},
        "val": {"pay_rep": int(round(val["mcd_pay_per_mcd_patient_reporting"])),
                "self_rep": int(round(val["selfpay_per_uninsured_reporting"])),
                "pay_hrsa": int(round(val["mcd_pay_per_mcd_patient_hrsa_national"])),
                "gap": r(val["medicaid_payment_gap"], 3)},
    }

    data = {"_source": "analysis/09-health-center-coverage-loss-stress-test/web_data.py from output/ (state_ranges, uds_state, "
                       "sobol_by_state, sobol_median_across_states, tornado_typical_state, peer_benchmark, peer_histogram, "
                       "numbers.json, model_summary.json); run " + str(nums["run_date"]),
            "meta": meta, "states": states, "inputs": inputs, "sobol": sobol, "sobol_median": sobol_median,
            "tornado": tornado, "bands": bands, "hist": histo}
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {DEST} ({DEST.stat().st_size / 1024:.0f} KB)")

    # strings for the front matter stat tiles
    print("stat tiles:")
    print(f'  {n["model_national_loss_pct_p50"]:.1f}%  ({n["model_national_loss_pct_p5"]:.1f}% to {n["model_national_loss_pct_p95"]:.1f}%)')
    print(f'  {ex["paperwork_share_p50_median"] * 100:.0f}% administrative share, median state')
    print(f'  {nb["benchmark_pct_p50_median"]:.1f}% of revenue, median center ({nb["benchmark_pct_p50_p10"]:.1f}% to {nb["benchmark_pct_p50_p90"]:.1f}%)')
    print(f'  ${n["centers_net_loss_usd_p50"] / 1e9:.1f} billion ({n["centers_net_loss_usd_p5"] / 1e9:.1f} to {n["centers_net_loss_usd_p95"] / 1e9:.1f})')
    print(f'  states {ex["state_p50_min"] * 100:.1f}% to {ex["state_p50_max"] * 100:.1f}%')


if __name__ == "__main__":
    main()
