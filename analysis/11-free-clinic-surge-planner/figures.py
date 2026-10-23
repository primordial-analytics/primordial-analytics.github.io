"""Figures in the style of the other case studies: gold bars, navy emphasis, direct titles, 1200 px wide webp."""
import io
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import model
import results

GOLD, NAVY, GRID, GRAY = "#B3A369", "#191345", "#DDDDDD", "#555555"
LIGHT_GOLD, DARK_GOLD = "#D9D0AE", "#8C7E45"
PREFIX = "free-clinic"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": NAVY, "axes.labelcolor": NAVY, "xtick.color": NAVY,
                     "ytick.color": NAVY, "axes.edgecolor": NAVY, "axes.spines.top": False, "axes.spines.right": False})


def save_webp(fig, path, width=1200):
    """Render at exactly `width` px. The figure's size in inches sets how big the type is on the page, so figures are
    drawn narrow (7.5 to 9.5 in) to keep 10 pt text near 12 px at the page's 800 px width."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=width / fig.get_figwidth(), facecolor="white")
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    img.save(path, "WEBP", quality=85, method=6)
    return img.size


def footer(fig, text, chars, y=0.008, size=9.2):
    fig.text(0.015, y, "\n".join(textwrap.fill(t, chars) for t in text.split("\n")), fontsize=size, color=GRAY, va="bottom", ha="left")


def fig_observed(st, out):
    s = st.dropna(subset=["rate_2026"]).copy()
    s["chg"] = 100 * (s.low_sel_2026 / s.low_sel_2025 - 1)
    s = s.sort_values("rate_2026")
    y = np.arange(len(s))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 10.6), sharey=True, gridspec_kw={"width_ratios": [1, 1.05], "wspace": 0.1})
    a1.barh(y, s.chg, color=GOLD, height=0.72)
    for yi, v in zip(y, s.chg):
        a1.text(15, yi, f"{v:+.0f}%", va="center", ha="right", fontsize=9.5)   # one column at the right edge, clear of the bars and the dashed line
    tot = 100 * (s.low_sel_2026.sum() / s.low_sel_2025.sum() - 1)
    a1.axvline(tot, color=NAVY, ls="--", lw=1.8)
    a1.text(tot - 1, len(s) + 0.1, f"All {len(s)} states: {tot:+.1f}%", fontsize=11, fontweight="bold", va="bottom", ha="right")
    a1.set_yticks(y, s.index)
    a1.set_xlim(-50, 15)
    a1.set_title("Selections by people at 100-200%\nof poverty, 2026 vs 2025", loc="left", fontsize=11.5, fontweight="bold")
    a1.set_xticks([-40, -20, 0])
    a1.xaxis.set_major_formatter(lambda v, _: f"{v:+.0f}%" if v else "0")
    a2.hlines(y, 100 * s.rate_2026, 100 * s.rate_2025, color=GOLD, lw=3)
    a2.scatter(100 * s.rate_2025, y, s=50, color=LIGHT_GOLD, edgecolor=DARK_GOLD, zorder=3, label="February 2025")
    a2.scatter(100 * s.rate_2026, y, s=50, color=NAVY, zorder=3, label="February 2026")
    a2.set_xlim(55, 100)
    a2.set_xticks([60, 70, 80, 90, 100])
    a2.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    a2.set_title("Share of plan selections paid up\nin February, all incomes", loc="left", fontsize=11.5, fontweight="bold")
    a2.legend(loc="lower right", frameon=False, fontsize=10.5)
    for a in (a1, a2):
        a.grid(axis="x", color=GRID, lw=0.8)
        a.set_axisbelow(True)
        a.tick_params(axis="y", length=0, labelsize=10.5)
        a.tick_params(axis="x", labelsize=10.5)
    fig.suptitle("Fewer low-income selections, and fewer of them paid,\nin HealthCare.gov states", x=0.015, ha="left", fontsize=15, fontweight="bold", y=0.99)
    footer(fig, "Sources: CMS 2025 and 2026 Open Enrollment county files; CMS monthly effectuated enrollment (as of 2026-05-05), HealthCare.gov platform. "
                "Paid share = February paid enrollment divided by open-enrollment selections. Illinois (state exchange in 2026) is excluded. Analysis by Primordial Analytics.", 105)
    fig.subplots_adjust(top=0.9, bottom=0.085, left=0.12, right=0.985)
    return save_webp(fig, out / f"{PREFIX}-observed.webp")


def fig_scenarios(c, qdf, totals, out):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.5, 10.8), gridspec_kw={"height_ratios": [1, 0.95], "hspace": 0.4})
    names = {"lower": "Lower demand", "central": "Central", "higher": "Higher demand"}
    ymax = 5400
    for i, s in enumerate(results.SCEN):
        for off, key, col, lab in ((-0.2, "mkt", GOLD, "Marketplace losses only\n(observed drop in paid coverage, assumed share left uninsured)"),
                                   (0.2, "all", NAVY, "Plus Medicaid work requirements\n(placeholder)")):
            t = totals[(s, key)] / 1e3
            lo, md, hi = np.quantile(t, [0.1, 0.5, 0.9])
            a1.bar(i + off, md, color=col, width=0.38, label=lab if i == 0 else None)
            a1.errorbar(i + off, md, yerr=[[md - lo], [hi - md]], color=GRAY, capsize=4, lw=1.4)
            a1.text(i + off, hi + 0.03 * ymax, f"{md:,.0f}k", ha="center", fontsize=10.5, fontweight="bold")
    a1.set_xticks(range(3), [names[s] for s in results.SCEN], fontsize=11)
    a1.set_ylabel("Additional uninsured adults, thousands", fontsize=11)
    a1.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    a1.tick_params(labelsize=10.5)
    a1.grid(axis="y", color=GRID, lw=0.8)
    a1.set_axisbelow(True)
    a1.legend(loc="upper left", frameon=False, fontsize=10)
    a1.set_ylim(0, ymax)
    a1.set_title("2027, all 2,054 counties: median and\n10th-90th percentile interval", loc="left", fontsize=12, fontweight="bold")
    bins = np.linspace(-0.2, 1.0, 49)
    gm = np.clip(100 * qdf["g_central_mkt_p50"], -20, 100)
    ga = np.clip(100 * qdf["g_central_all_p50"], -20, 100)
    a2.hist(gm, bins=100 * bins, color=GOLD, edgecolor="white", lw=0.5, label="Marketplace losses only")
    a2.hist(ga, bins=100 * bins, histtype="step", color=NAVY, lw=2.2, label="Plus Medicaid work requirements")
    top = a2.get_ylim()[1]
    a2.set_ylim(0, top * 1.3)
    for v, col, h in ((np.median(qdf["g_central_mkt_p50"]), DARK_GOLD, 1.22), (np.median(qdf["g_central_all_p50"]), NAVY, 1.12)):
        a2.axvline(100 * v, color=col, ls="--", lw=1.6)
        a2.text(100 * v + 1.5, top * h, f"median {100 * v:.0f}%", color=col, fontsize=10.5, fontweight="bold", va="center",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    a2.set_xlabel("Growth in the uninsured pool, central scenario (% of 2024 level)", fontsize=11)
    a2.set_ylabel("Number of counties", fontsize=11)
    a2.tick_params(labelsize=10.5)
    a2.legend(loc="center right", frameon=False, fontsize=10)
    a2.grid(axis="y", color=GRID, lw=0.8)
    a2.set_axisbelow(True)
    a2.set_title("Counties by growth in the pool (median draw)", loc="left", fontsize=12, fontweight="bold")
    fig.suptitle("How many more low-income uninsured adults\nin 2027? A range, not a number", x=0.015, ha="left", fontsize=15, fontweight="bold", y=0.99)
    footer(fig, "Sources: CMS Open Enrollment 2025-26 and effectuated enrollment; Census SAHIE 2024 (baseline); Medicaid.gov June 2026 enrollment; Primordial Analytics scenarios, 10,000 draws. "
                "Additional uninsured adults 18-64 at or below 200% of poverty, relative to the 2024 estimate, in 30 HealthCare.gov states. Scenario inputs are assumptions, listed in the text.", 88)
    fig.subplots_adjust(top=0.88, bottom=0.17, left=0.14, right=0.97)
    return save_webp(fig, out / f"{PREFIX}-scenarios.webp")


def fig_decision(c, a, U, j, tor, ex, out):
    fig = plt.figure(figsize=(7.5, 11.2))
    a1 = fig.add_axes([0.13, 0.59, 0.84, 0.33])
    a2 = fig.add_axes([0.5, 0.17, 0.47, 0.33])
    aj, Uj = model.subset(a, U, j)
    ps = np.linspace(0.5, 0.99, 50)
    cols = {"lower": (GOLD, "-", 2.6), "central": (NAVY, "-", 3.2), "higher": (NAVY, (0, (4, 2)), 2.2)}
    for s in results.SCEN:
        _, mkt, mcd, pool, _ = model.simulate(aj, Uj, s)
        g = (mkt + mcd)[:, 0] / pool[:, 0]
        ys = results.clinic_sessions(np.quantile(g, ps), ex)
        a1.plot(100 * ps, ys, color=cols[s][0], ls=cols[s][1], lw=cols[s][2], label=s.capitalize())
        if s == "central":
            for p in (0.8, 0.95):
                v = float(results.clinic_sessions(np.quantile(g, p), ex))
                a1.plot([100 * p], [v], "o", color=NAVY, ms=8)
                a1.annotate(f"{int(100 * p)}%: {v:.0f}", (100 * p, v), textcoords="offset points", xytext=(-8, 9), ha="right", fontsize=11, fontweight="bold")
    today = ex["patients"] * ex["visits_per_patient"] / ex["patients_per_session"]
    a1.axhline(today, color=GRAY, ls=":", lw=1.6)
    a1.text(50.5, today - 3, f"Today: {today:.0f} sessions a year", fontsize=10.5, fontweight="bold", color=GRAY, va="top")
    a1.set_xlabel("Probability that the sessions cover 2027 demand", fontsize=11)
    a1.set_ylabel("Sessions a year", fontsize=11)
    a1.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    a1.tick_params(labelsize=10.5)
    a1.legend(title="Scenario", loc="upper left", frameon=False, fontsize=10.5, title_fontsize=10.5)
    a1.grid(color=GRID, lw=0.8)
    a1.set_axisbelow(True)
    a1.set_ylim(100, None)
    a1.set_title("Sessions to plan for, example clinic", loc="left", fontsize=12, fontweight="bold")
    t = tor[0].iloc[::-1].reset_index(drop=True)
    base = tor[1]
    yy = np.arange(len(t))
    for i, rw in t.iterrows():
        lo, hi = sorted([rw.sessions_low, rw.sessions_high])
        if hi > base:
            a2.barh(i, hi - base, left=base, color=NAVY, height=0.62)
        if lo < base:
            a2.barh(i, lo - base, left=base, color=GOLD, height=0.62)
        a2.text(max(hi, base) + 1.5, i, f"{lo:.0f} to {hi:.0f}", va="center", fontsize=9.8)
    a2.axvline(base, color=NAVY, lw=1.6)
    a2.set_yticks(yy, ["\n".join(textwrap.wrap(x, 30)) for x in t.assumption], fontsize=9.8)
    a2.set_xlim(min(t.sessions_low.min(), t.sessions_high.min()) - 6, max(t.sessions_low.max(), t.sessions_high.max()) + 26)
    a2.set_xlabel(f"Sessions a year at 80% probability\n(central case: {base:.0f})", fontsize=11)
    a2.tick_params(axis="x", labelsize=10.5)
    a2.grid(axis="x", color=GRID, lw=0.8)
    a2.set_axisbelow(True)
    a2.tick_params(axis="y", length=0)
    a2.set_title("Which assumption moves the answer", loc="right", x=1.0, fontsize=12, fontweight="bold")
    fig.suptitle("Sessions to commit, and what drives the number", x=0.015, ha="left", fontsize=15, fontweight="bold", y=0.99)
    footer(fig, f"Hypothetical clinic: {ex['patients']} uninsured adult patients, {ex['visits_per_patient']:g} visits each a year, {ex['patients_per_session']} patients per session, in a mid-sized expansion-state county. "
                "Sources: Primordial Analytics model on CMS, Census SAHIE and Medicaid.gov data. Lower chart: dark bars mean more sessions than the central case, gold means fewer; "
                "other assumptions held at central.", 88)
    return save_webp(fig, out / f"{PREFIX}-decision.webp")


def fig_thumbnail(ex_block, out):
    rows = {(r_["scenario"], r_["layers"], r_["probability"]): r_["sessions"] for r_ in ex_block["rows"]}
    vals = [("Today", ex_block["today_sessions"], NAVY),
            ("Likely (50%)", rows[("central", "all", 0.5)], GOLD),
            ("80% sure", rows[("central", "all", 0.8)], GOLD),
            ("95% sure", rows[("central", "all", 0.95)], GOLD)]
    fig, ax = plt.subplots(figsize=(4, 3))
    y = np.arange(len(vals))[::-1]
    for yi, (lab, v, col) in zip(y, vals):
        ax.barh(yi, v, color=col, height=0.7)
        ax.text(v + 4, yi, f"{v:.0f}", va="center", fontsize=12, fontweight="bold")
    ax.set_yticks(y, [v[0] for v in vals], fontsize=11)
    ax.set_xlim(0, 235)
    ax.set_xticks([])
    for sp in ("bottom", "top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.suptitle("Clinic sessions to plan\nfor in 2027", x=0.03, ha="left", fontsize=12.5, fontweight="bold", y=0.97)
    fig.subplots_adjust(top=0.78, bottom=0.04, left=0.33, right=0.97)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    Image.open(buf).convert("RGB").save(out / f"{PREFIX}-thumbnail.webp", "WEBP", quality=85, method=6)


def make_all(c, st, rank, qdf, totals, tor, ex_block, numbers, out):
    out = Path(out)
    a = model.county_arrays(c)
    U = model.draw_uniforms(len(c))
    j = int(np.where(c.fips == ex_block["fips"])[0][0])
    ex = results.EXAMPLE
    sizes = {"observed": fig_observed(st, out), "scenarios": fig_scenarios(c, qdf, totals, out),
             "decision": fig_decision(c, a, U, j, (tor, ex_block["tornado_base_sessions_p80"]), ex, out)}
    fig_thumbnail(ex_block, out)
    return sizes
