"""Figures, the numbers file behind the page, and the downloadable CSV."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from PIL import Image

from common import CMS, EXPANSION, OUT, ROOT

GOLD, NAVY, GREY, LIGHT = "#B3A369", "#1B1446", "#6b6b6b", "#E4DCC0"
IMG = ROOT.parent.parent / "img" / "case_studies"
PREFIX = "stress"
SOURCE = ("Sources: CMS interim final rule (91 FR 33348), ACS 2024 PUMS, CMS renewal outcomes 2023-24, HRSA UDS 2025. "
          "Model outputs for planning, not forecasts. Primordial Analytics.")

plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": NAVY, "axes.labelcolor": NAVY,
                     "xtick.color": NAVY, "ytick.color": NAVY, "axes.edgecolor": NAVY})


def clean(ax, grid="x"):
    for s in ("top", "right", "bottom"):
        ax.spines[s].set_visible(False)
    ax.grid(axis=grid, color="#dddddd", lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def save(fig, name, width=1200):
    tmp = OUT / f"_{name}.png"
    fig.savefig(tmp, dpi=100)
    plt.close(fig)
    im = Image.open(tmp).convert("RGB")
    h = round(im.height * width / im.width)
    im.resize((width, h), Image.LANCZOS).save(IMG / f"{PREFIX}-{name}.webp", quality=85)
    tmp.unlink()
    return width, h


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def fig_states(st):
    s = st.sort_values("total_p50")
    n = len(s)
    fig, ax = plt.subplots(figsize=(12, 11.6))
    fig.subplots_adjust(left=0.2, right=0.97, top=0.93, bottom=0.085)
    y = np.arange(n)
    ax.barh(y, s.work_req_p50, color=GOLD, height=0.72, label="Non-compliance")
    ax.barh(y, s.paperwork_p50, left=s.work_req_p50, color=NAVY, height=0.72,
            label="Administrative")
    ax.hlines(y, s.total_p5, s.total_p95, color="#555555", lw=1.2, zorder=3)
    for v in (s.total_p5, s.total_p95):
        ax.vlines(v, y - 0.22, y + 0.22, color="#555555", lw=1.2, zorder=3)
    for yi, (_, r) in zip(y, s.iterrows()):
        ax.text(r.total_p95 + 0.008, yi, f"{r.total_p50 * 100:.0f}%", va="center", fontsize=9.5, fontweight="bold")
    ax.axvline(CMS["combined_central"], color=NAVY, ls="--", lw=1.6)
    ax.text(CMS["combined_central"] + 0.006, -1.2, "CMS central estimate: 15%", fontsize=10.5, fontweight="bold", va="center")
    ax.set_yticks(y)
    ax.set_yticklabels(s.name, fontsize=10)
    ax.set_ylim(-1.8, n - 0.4)
    ax.set_xlim(0, 0.6)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v * 100:.0f}%")
    ax.tick_params(axis="x", labelsize=11)
    clean(ax)
    fig.text(0.012, 0.965, "Expansion adults who could lose Medicaid in a year, by state", fontsize=16.5, fontweight="bold", va="center")
    h = [Patch(color=GOLD, label="Non-compliance (median)"), Patch(color=NAVY, label="Administrative (median)"),
         plt.Line2D([0], [0], color="#555555", lw=1.2, label="Total: 5th to 95th percentile")]
    ax.legend(handles=h, loc="lower right", frameon=False, fontsize=10, bbox_to_anchor=(1.0, 0.0))
    fig.text(0.012, 0.022, SOURCE + "\n41 expansion jurisdictions; share of adult-group enrollees per year of operation. Bold label: median total (the parts are medians and do not sum to it).", fontsize=8.6, color=GREY, va="center")
    return save(fig, "coverage-loss-states")


def fig_revenue(bench, hist, med, n_centers):
    b = bench.dropna(subset=["median_pct_of_total_revenue_p50"]).copy()
    b["label"] = b.size_band_patients + " patients, " + b.setting.str.lower()
    order = ["Under 5,000", "5,000-14,999", "15,000-39,999", "40,000+"]
    b["o"] = b.size_band_patients.map({k: i for i, k in enumerate(order)}) * 2 + (b.setting == "Urban")
    b = b.sort_values("o", ascending=False)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.8), gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.55})
    fig.subplots_adjust(left=0.2, right=0.975, top=0.80, bottom=0.2)
    y = np.arange(len(b))
    a1.hlines(y, b.median_pct_of_total_revenue_p5, b.median_pct_of_total_revenue_p95, color=GOLD, lw=9, zorder=2)
    a1.scatter(b.median_pct_of_total_revenue_p50, y, color=NAVY, s=75, zorder=3)
    for yi, (_, r) in zip(y, b.iterrows()):
        a1.text(r.median_pct_of_total_revenue_p95 + 0.15, yi, f"{r.median_pct_of_total_revenue_p50:.1f}%", va="center", fontsize=10, fontweight="bold")
    a1.set_yticks(y)
    a1.set_yticklabels(b.label, fontsize=10)
    a1.set_xlim(0, 8.2)
    a1.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    a1.set_xlabel("Net loss as % of total revenue (dot: median, bar: 5th-95th)", fontsize=10)
    clean(a1)
    a1.set_title("By size and setting (median center in each group)", loc="left", fontsize=11.5, fontweight="bold", color=NAVY, pad=10)
    a2.bar(hist.pct_from, hist.centers, width=0.4, align="edge", color=GOLD, edgecolor="white")
    a2.axvline(med, color=NAVY, ls="--", lw=1.6)
    a2.text(med + 0.15, a2.get_ylim()[1] * 0.95, f"Median: {med:.1f}%", fontsize=10.5, fontweight="bold", va="top")
    a2.set_xlabel("Net loss, % of total revenue (middle estimate)", fontsize=10)
    a2.set_ylabel("Number of centers", fontsize=10)
    a2.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    clean(a2, "y")
    a2.set_title(f"All {n_centers} centers", loc="left", fontsize=11.5, fontweight="bold", color=NAVY, pad=10)
    fig.text(0.012, 0.93, "Net revenue change at expansion-state health centers if expansion adults lose coverage", fontsize=14.5, fontweight="bold", va="center")
    fig.text(0.012, 0.045, SOURCE + "\nCenters in 41 expansion jurisdictions that report UDS Table 9D and have 200+ Medicaid patients. Revenue includes grants. "
             "Net of sliding-fee collections from patients who keep coming.", fontsize=8.6, color=GREY, va="center")
    return save(fig, "revenue-at-risk")


def fig_drivers(tor, sob):
    t = tor[tor.output == "pct_rev"].copy()
    s = sob[sob.output == "pct_rev"].set_index("input")
    t["ST"], t["S1"] = t.input.map(s.ST), t.input.map(s.S1)
    t = t.sort_values("ST").tail(10)
    base = t.base.iloc[0] * 100
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 6.2), gridspec_kw={"width_ratios": [1.5, 1], "wspace": 0.06}, sharey=True)
    fig.subplots_adjust(left=0.265, right=0.97, top=0.80, bottom=0.17)
    y = np.arange(len(t))
    lo, hi = t[["p10", "p90"]].min(axis=1) * 100, t[["p10", "p90"]].max(axis=1) * 100
    a1.barh(y, hi - base, left=base, color=NAVY, height=0.62, label="Navy: higher revenue loss")
    a1.barh(y, lo - base, left=base, color=GOLD, height=0.62, label="Gold: lower revenue loss")
    a1.legend(loc="lower right", frameon=False, fontsize=9.5)
    for yi, l, h in zip(y, lo, hi):
        a1.text(l - 0.05, yi, f"{l:.1f}%", ha="right", va="center", fontsize=9.5)
        a1.text(h + 0.05, yi, f"{h:.1f}%", ha="left", va="center", fontsize=9.5)
    a1.axvline(base, color=NAVY, lw=1.4)
    a1.set_yticks(y)
    a1.set_yticklabels(t.label, fontsize=10.5)
    a1.set_xlim(base - 0.95, base + 1.55)
    a1.xaxis.set_major_formatter(lambda v, _: f"{v:.1f}%")
    a1.set_xlabel("Net loss, % of total revenue; other inputs held at their middle value", fontsize=9.6)
    clean(a1)
    a1.set_title(f"One input at a time, 10th to 90th percentile\n(typical state; middle estimate {base:.1f}%)",
                 loc="left", fontsize=10.8, fontweight="bold", color=NAVY, pad=10)
    a2.barh(y, t.ST, color=LIGHT, height=0.62)
    a2.barh(y, t.S1.clip(lower=0), color=GOLD, height=0.62)
    for yi, v in zip(y, t.ST):
        a2.text(v + 0.01, yi, f"{v:.2f}", va="center", fontsize=9.5, fontweight="bold")
    a2.set_xlim(0, 0.62)
    a2.set_xlabel("Share of the spread in the answer (Sobol index)", fontsize=9.6)
    a2.tick_params(axis="y", length=0)
    clean(a2)
    a2.set_title("Variance explained, 41-state median\n(gold: alone; pale: with interactions)", loc="left", fontsize=10.8,
                 fontweight="bold", color=NAVY, pad=10)
    fig.text(0.012, 0.94, "Which assumptions move the revenue answer most", fontsize=16, fontweight="bold", va="center")
    fig.text(0.012, 0.04, SOURCE, fontsize=8.6, color=GREY, va="center")
    return save(fig, "what-matters")


def fig_thumb(st, med):
    pick = [("Utah", st.set_index("name").loc["Utah"]), ("New York", st.set_index("name").loc["New York"]),
            ("All states\n(median)", None), ("Virginia", st.set_index("name").loc["Virginia"]), ("Kentucky", st.set_index("name").loc["Kentucky"])]
    fig, ax = plt.subplots(figsize=(4, 3))
    fig.subplots_adjust(left=0.30, right=0.93, top=0.74, bottom=0.05)
    y = np.arange(len(pick))[::-1]
    for yi, (lab, r) in zip(y, pick):
        val = med if r is None else r.total_p50
        ax.barh(yi, val, color=NAVY if r is None else GOLD, height=0.68)
        ax.text(val + 0.012, yi, f"{val * 100:.0f}%", va="center", fontsize=11.5, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([p[0] for p in pick], fontsize=10.5)
    ax.set_xlim(0, 0.62)
    ax.set_xticks([])
    for sp in ("top", "right", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0)
    fig.text(0.03, 0.88, "Expansion adults who could\nlose Medicaid in a year", fontsize=12.2, fontweight="bold", va="center", linespacing=1.15)
    out = OUT / "_thumb.png"
    fig.savefig(out, dpi=100)
    plt.close(fig)
    Image.open(out).convert("RGB").save(IMG / f"{PREFIX}-thumbnail.webp", quality=85)
    out.unlink()


def build_numbers(st, bench, tor, sob):
    """Every number quoted in the page prose, with the quantities it is computed from."""
    j = lambda f: json.load(open(OUT / f))
    ms, pu, uds, unw = j("model_summary.json"), j("pums_pooled.json"), j("uds_summary.json"), j("unwinding_summary.json")
    src = j("sources.json")["files"]
    n = {"run_date": next(f["downloaded"] for f in src if f["file"] == "H80-2025.xlsx")}
    n["cms"] = {**{k: v for k, v in CMS.items() if not isinstance(v, (dict, list))},
                "excl_components": CMS["excl_components"], "scenarios": {
                    "weights": CMS["scenario_weight"], "noncomp": CMS["scenario_noncomp"], "proc": CMS["scenario_proc"]},
                **{k: ms[k] for k in ["cms_noncomp_share_total", "cms_proc_share_total", "cms_combined", "cms_full_year_m",
                                      "cms_fy2027_m", "table39_weighted_noncomp", "table39_weighted_proc", "table39_combined",
                                      "overlap_factor", "excl_sum_table37"]}}
    n["pums"] = {**pu, "target_pop_m": pu["target_pop"] / 1e6, "mcd_adult_pop_m": pu["mcd_adult_pop"] / 1e6,
                 "target_share_of_cms_adults": pu["target_pop"] / 1e6 / CMS["applicable_adults_m"]}
    from model import BETA_PRIORS, SIGMA, THETA_MAX
    n["assumptions"] = {"expansion_share_prior_mean": BETA_PRIORS["f_ref"][0], "expansion_share_prior_sd": BETA_PRIORS["f_ref"][1],
                        "keep_coming_mean": BETA_PRIORS["r_keep"][0], "keep_coming_sd": BETA_PRIORS["r_keep"][1],
                        "visit_rate_mean": BETA_PRIORS["v_rel"][0], "visit_rate_sd": BETA_PRIORS["v_rel"][1],
                        "ex_parte_prior_mean": BETA_PRIORS["ex_nat"][0], "ex_parte_prior_sd": BETA_PRIORS["ex_nat"][1],
                        "lognormal_sigma": SIGMA, "theta_max": THETA_MAX}
    n["unwinding"] = unw
    n["uds"] = uds
    n["validation"] = {
        "reporting_centers_all": uds["centers_reporting_9d"], "centers_all": uds["centers_total"],
        "mcd_pay_per_mcd_patient_reporting": uds["rep_all_mcd_pay_per_mcd_patient"],
        "mcd_pay_per_mcd_patient_hrsa_national": uds["hrsa_mcd_pay_per_mcd_patient"],
        "selfpay_per_uninsured_reporting": uds["rep_all_selfpay_per_uninsured"],
        "selfpay_per_uninsured_hrsa_national": uds["hrsa_selfpay_per_uninsured"],
        "reporting_share_of_patients": uds["rep_all_share_of_patients"],
        "reporting_share_of_hrsa_medicaid_payments": uds["rep_all_share_of_hrsa_mcd_payments"],
        "medicaid_adults_all_centers_m": uds["all_mcd_18p"] / 1e6,
        "hrsa_medicaid_payments_b": uds["hrsa_medicaid_payments"] / 1e9,
        "centers_not_reporting_9d": uds["centers_total"] - uds["centers_reporting_9d"],
        "medicaid_payment_gap": abs(uds["rep_all_mcd_pay_per_mcd_patient"] / uds["hrsa_mcd_pay_per_mcd_patient"] - 1),
        "selfpay_gap": abs(uds["rep_all_selfpay_per_uninsured"] / uds["hrsa_selfpay_per_uninsured"] - 1),
    }
    n["national"] = {k: ms[k] for k in ms if k.startswith(("model_", "share_of_draws", "state_median", "centers_", "typical"))}
    n["national"]["centers_expansion_adults_m"] = ms["centers_expansion_adults_p50"] / 1e6
    n["national"]["centers_net_loss_usd_b"] = [ms[f"centers_net_loss_usd_p{p}"] / 1e9 for p in (5, 50, 95)]
    n["national"]["centers_lost_adults_thousands"] = [ms[f"centers_lost_adults_p{p}"] / 1e3 for p in (5, 50, 95)]
    n["national"]["centers_admin_share_of_lost"] = ms["centers_admin_lost_adults_p50"] / ms["centers_lost_adults_p50"]
    n["states"] = {r["state"]: {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in r.items()}
                   for r in st.to_dict("records")}
    lo, hi = st.loc[st.total_p50.idxmin()], st.loc[st.total_p50.idxmax()]
    n["extremes"] = {"lowest_total": [lo["name"], lo.total_p50], "highest_total": [hi["name"], hi.total_p50],
                     "highest_paperwork": [st.loc[st.paperwork_p50.idxmax(), "name"], st.paperwork_p50.max()],
                     "lowest_paperwork": [st.loc[st.paperwork_p50.idxmin(), "name"], st.paperwork_p50.min()],
                     "states_n": int(len(st)),
                     "state_p50_min": st.total_p50.min(), "state_p50_max": st.total_p50.max(),
                     "state_p5_min": st.total_p5.min(), "state_p95_max": st.total_p95.max(),
                     "state_p95_min": st.total_p95.min(),
                     "work_req_p50_min": st.work_req_p50.min(), "work_req_p50_max": st.work_req_p50.max(),
                     "paperwork_share_p50_median": st.admin_share_of_loss_p50.median(),
                     "rev_pct_p50_min": st.pct_of_total_revenue_p50.min(), "rev_pct_p50_max": st.pct_of_total_revenue_p50.max(),
                     "rev_pct_highest_state": st.loc[st.pct_of_total_revenue_p50.idxmax(), "name"],
                     "rev_pct_lowest_state": st.loc[st.pct_of_total_revenue_p50.idxmin(), "name"],
                     "workbook_sum_low_gap_median": float((st.work_req_p5 + st.paperwork_p5 - st.total_p5).median()),
                     "workbook_sum_high_gap_median": float((st.work_req_p95 + st.paperwork_p95 - st.total_p95).median()),
                     "workbook_generic": {"low": 0.135, "mid": 0.28, "high": 0.50},
                     "states_with_p50_above_workbook_mid": int((st.total_p50 > 0.28).sum()),
                     "states_with_workbook_mid_inside_p5_p95": int(((st.total_p5 < 0.28) & (st.total_p95 > 0.28)).sum())}
    t = tor[tor.output == "pct_rev"].set_index("input")
    s_ = sob[sob.output == "pct_rev"].set_index("input")
    sl = sob[sob.output == "L"].set_index("input")
    allsob = pd.read_csv(OUT / "sobol_by_state.csv")
    first = lambda out: allsob[allsob.output == out].sort_values(["state", "ST"], ascending=[True, False]).groupby("state").head(1).input.value_counts().to_dict()
    n["drivers"] = {
        "revenue_ST": s_.ST.round(4).to_dict(), "revenue_S1": s_.S1.round(4).to_dict(),
        "loss_ST": sl.ST.round(4).to_dict(), "loss_S1": sl.S1.round(4).to_dict(),
        "top_driver_count_loss": first("L"), "top_driver_count_revenue": first("pct_rev"),
        "tornado_revenue_pct": {k: [float(r.p10 * 100), float(r.p90 * 100)] for k, r in t.iterrows()},
        "tornado_base_pct": float(t.base.iloc[0] * 100), "typical_state": ms["typical_state"],
        "sum_S1_loss": ms["sobol_sum_S1_median_L"], "sum_S1_revenue": ms["sobol_sum_S1_median_rev"],
        "sobol_runs_per_state_output": 4096 * 16, "mc_draws": 20000,
    }
    b = bench.to_dict("records")
    n["benchmark"] = {"bands": b, **{k: ms[k] for k in ms if k.startswith("benchmark_")}}
    n["nebraska"] = {k: ms[k] for k in ms if k.startswith("ne_")}
    from unwinding import MIN_N
    n["unwinding"]["min_denominator"] = MIN_N
    n["national"]["model_minus_cms_pts"] = ms["model_national_loss_pct_p50"] - 100 * ms["cms_combined"]
    n["benchmark"]["centers_expansion_reporting_9d"] = uds["expansion_centers_reporting_9d"]
    n["benchmark"]["centers_dropped_by_filters"] = uds["expansion_centers_reporting_9d"] - ms["benchmark_centers"]
    return n


def main():
    st = pd.read_csv(OUT / "state_ranges.csv")
    bench = pd.read_csv(OUT / "peer_benchmark.csv")
    tor = pd.read_csv(OUT / "tornado_typical_state.csv")
    sob = pd.read_csv(OUT / "sobol_median_across_states.csv")
    hist = pd.read_csv(OUT / "peer_histogram.csv")
    ms = json.load(open(OUT / "model_summary.json"))
    sizes = {"coverage-loss-states": fig_states(st)}
    sizes["revenue-at-risk"] = fig_revenue(bench, hist, ms["benchmark_pct_p50_median"], ms["benchmark_centers"])
    sizes["what-matters"] = fig_drivers(tor, sob)
    fig_thumb(st, st.total_p50.median())
    json.dump(sizes, open(OUT / "figure_sizes.json", "w"))
    json.dump(build_numbers(st, bench, tor, sob), open(OUT / "numbers.json", "w"), indent=1, default=float)
    dl = ROOT.parent.parent / "downloads"
    slug = ROOT.name
    pd.read_csv(OUT / "state_inputs_for_whatif_workbook.csv").to_csv(dl / f"{slug}-state-ranges.csv", index=False)
    bench.to_csv(dl / f"{slug}-peer-benchmark.csv", index=False)
    print(sizes)


if __name__ == "__main__":
    main()
