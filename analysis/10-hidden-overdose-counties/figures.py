"""Figures for the case study. Reads the county table and validation results written by run.py."""
import io
import json
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely import affinity

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import data  # noqa: E402

HERE = Path(__file__).resolve().parent
IMG = HERE.parent.parent / "img" / "case_studies"
PREFIX = "example-overdose"
NAVY, GOLD, GREY, LIGHT = "#191445", "#B3A369", "#595959", "#E9E4D0"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": GREY, "axes.labelcolor": NAVY,
    "xtick.color": NAVY, "ytick.color": NAVY, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 100, "hatch.linewidth": 0.5,
})
BINS = [0, 10, 15, 20, 30, 45, 200]
COLORS = ["#ECE6CC", "#DDD3AE", "#B3A369", "#7A6F44", "#6F79B0", NAVY]   # 30-44 is a mid blue so it reads apart from 45+


def save(fig, name, width=1200):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, facecolor="white")
    plt.close(fig)
    im = Image.open(buf).convert("RGB")
    assert im.width == width, im.width
    im.save(IMG / name, "WEBP", quality=85, method=6)
    print(name, im.size, f"{(IMG / name).stat().st_size / 1024:.0f} KB")
    return im


def title(fig, text, y=0.975):
    fig.text(0.012, y, text, fontsize=17, fontweight="bold", color=NAVY, va="top", ha="left")


def source(fig, text, y=0.012):
    fig.text(0.012, y, text, fontsize=10, color=GREY, va="bottom", ha="left", linespacing=1.4)


def _geo(county_table):
    """County polygons in an Albers projection, with Alaska and Hawaii moved under the lower 48."""
    g = data._boundaries().set_index("GEOID").loc[county_table.fips]
    geom = g.geometry.copy()
    for prefix, scale, corner in (("02", 0.28, (-2.4e6, -0.75e6)), ("15", 1.0, (-1.2e6, -0.75e6))):
        sel = g.index.str.startswith(prefix)
        minx, miny, _, _ = geom[sel].total_bounds
        geom[sel] = geom[sel].apply(lambda s: affinity.translate(
            affinity.scale(s, scale, scale, origin=(minx, miny)), corner[0] - minx, corner[1] - miny))
    g["geometry"] = geom
    return g.reset_index()


def _draw_map(ax, g, values, hatch_mask, legend=True):
    ax.set_axis_off()
    idx = np.digitize(values.fillna(-1).values, BINS[1:-1], right=False)
    cols = np.array(COLORS)[np.clip(idx, 0, len(COLORS) - 1)].astype(object)
    cols[values.isna().values] = "#FFFFFF"
    g.plot(ax=ax, color=list(cols), edgecolor="white", linewidth=0.15)
    if hatch_mask.any():
        dark = idx >= 4   # the two darkest classes get a light hatch, or it vanishes
        for m, ec in ((hatch_mask & ~dark, (0.1, 0.08, 0.27, 0.6)), (hatch_mask & dark, (1, 1, 1, 0.75))):
            if m.any():
                g[m].plot(ax=ax, facecolor="none", edgecolor=ec, hatch="////", linewidth=0)
    ax.set_aspect("equal")


def fig_map(cs):
    g = _geo(cs)
    cs = cs.set_index("fips")
    g = g.set_index("GEOID").loc[cs.index].reset_index()
    hidden = cs.count_status.isin(["suppressed_1_to_9", "suppressed_data_quality"]).values
    fig = plt.figure(figsize=(12, 8.2))
    title(fig, "Overdose death rates in every U.S. county, 12 months ending March 2026")
    ax = fig.add_axes([0.0, 0.06, 1.0, 0.86])
    _draw_map(ax, g, cs.rate_median_per_100k, hidden)
    handles = [Patch(facecolor=c, edgecolor="#BBBBBB", linewidth=0.5) for c in COLORS]
    labels = ["under 10", "10-14", "15-19", "20-29", "30-44", "45 or more"]
    fig.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.012, 0.085), ncol=1, frameon=False, fontsize=10.5,
               title="Model median,\ndeaths per 100,000\nper year", title_fontsize=10.5, alignment="left")
    fig.legend([Patch(facecolor="white", edgecolor=(0.1, 0.08, 0.27, 0.7), hatch="////", linewidth=0.5)],
               [f"Hatched: count hidden in the national file\n({int((cs.count_status == 'suppressed_1_to_9').sum()):,} counties at 1 to 9 deaths,\nplus {int((cs.count_status == 'suppressed_data_quality').sum())} suppressed for data quality)"],
               loc="lower right", bbox_to_anchor=(0.99, 0.085), frameon=False, fontsize=10.5)
    source(fig, "Source: CDC NCHS Vital Statistics Rapid Release, provisional county counts (data as of 2026-10-04); Census population estimates.\n"
                "Model: Poisson with an interval-censored likelihood and a spatial prior. Analysis by Primordial Analytics.")
    return save(fig, f"{PREFIX}-map.webp")


def fig_widths(cs, state="KY"):
    s = cs[cs.count_status == "suppressed_1_to_9"].copy()
    s["hard_w"] = s.hard_hi_per_100k - s.hard_lo_per_100k
    s["model_w"] = s.rate_hi90_per_100k - s.rate_lo90_per_100k
    fig = plt.figure(figsize=(12, 6.9))
    title(fig, "What the model adds to the 1-to-9 bounds")
    ax = fig.add_axes([0.075, 0.27, 0.37, 0.58])
    ax.scatter(s.hard_w, s.model_w, s=9, color=GOLD, alpha=0.7, linewidths=0)
    lim = [s.model_w.min() * 0.8, s.hard_w.max() * 1.2]
    ax.plot(lim, lim, color=NAVY, linestyle="--", linewidth=1.2)
    ax.set_xscale("log"), ax.set_yscale("log")
    ax.set_xlim(lim), ax.set_ylim(lim)
    ratio = (s.model_w / s.hard_w).median()
    ax.text(0.04, 0.95, f"Median model interval is {ratio:.0%}\nof the width of the hard bounds", transform=ax.transAxes,
            va="top", fontsize=11.5, fontweight="bold", color=NAVY)
    ax.text(0.03, 0.62, "above the line: model wider", transform=ax.transAxes, fontsize=10, color=GREY)
    ax.text(0.97, 0.04, "below the line:\nmodel narrower", transform=ax.transAxes, ha="right", fontsize=10, color=GREY)
    ax.set_xlabel("Width of hard bounds, 1 to 9 deaths\n(per 100,000)")
    ax.set_ylabel("Width of model 90% interval (per 100,000)")
    fig.text(0.075, 0.895, f"All {len(s):,} suppressed counties", fontsize=13, fontweight="bold", color=NAVY)
    ax2 = fig.add_axes([0.6, 0.27, 0.385, 0.58])
    k = s[s.state == state].sort_values("population", ascending=False).head(12).iloc[::-1]
    y = np.arange(len(k))
    for i, (_, r) in enumerate(k.iterrows()):
        ax2.plot([r.hard_lo_per_100k, r.hard_hi_per_100k], [i, i], color=LIGHT, linewidth=9, solid_capstyle="butt", zorder=1)
    ax2.hlines(y, k.rate_lo90_per_100k, k.rate_hi90_per_100k, color=GREY, linewidth=1.8, zorder=2)
    ax2.scatter(k.rate_median_per_100k, y, s=48, color=NAVY, zorder=3)
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"{c}, {state}" for c in k.county], fontsize=10.5)
    ax2.set_xscale("log")
    ax2.set_xticks([5, 10, 20, 50, 100])
    ax2.set_xticklabels(["5", "10", "20", "50", "100"])
    ax2.set_xlim(2, 150)
    ax2.set_xlabel("Deaths per 100,000 (log scale)")
    fig.text(0.6, 0.895, f"Twelve largest suppressed counties in {state}", fontsize=13, fontweight="bold", color=NAVY)
    ax2.legend(handles=[Line2D([0], [0], color=LIGHT, lw=9, label="hard bounds (1 to 9 deaths)"),
                        Line2D([0], [0], color=GREY, lw=1.8, marker="o", markerfacecolor=NAVY, markeredgecolor=NAVY,
                               label="model median, 90% interval")],
               loc="upper center", bbox_to_anchor=(0.4, -0.2), frameon=False, fontsize=10, ncol=2)
    source(fig, "Source: CDC NCHS provisional county counts, 12 months ending March 2026; Primordial Analytics model.\n"
                "Hard bounds are for the observed count; the model interval is for the underlying rate.")
    return save(fig, f"{PREFIX}-intervals.webp")


def fig_validation(res):
    fig = plt.figure(figsize=(12, 6.6))
    title(fig, "Checking the model against numbers it did not use")
    agg = pd.DataFrame(res["aggregate"])
    ax = fig.add_axes([0.075, 0.2, 0.38, 0.62])
    agg = agg[agg.residual > 0]   # three states with a negative residual are left out
    ok = agg.within_bounds & ~agg.has_dq
    bad = ~ok
    ax.errorbar(agg.residual[ok], agg.model_median[ok], yerr=[agg.model_median[ok] - agg.model_lo90[ok],
                                                               agg.model_hi90[ok] - agg.model_median[ok]],
                fmt="o", color=NAVY, ecolor=GREY, elinewidth=1.2, markersize=5, label="state residual plausible")
    ax.scatter(agg.residual[bad], agg.model_median[bad], s=34, facecolor="none", edgecolor=GOLD,
               linewidth=1.8, label="residual excluded (see text)", zorder=3)
    lim = [1.5, 700]
    ax.plot(lim, lim, color=NAVY, linestyle="--", linewidth=1)
    ax.set_xscale("log"), ax.set_yscale("log")
    ax.set_xlim(10, 700), ax.set_ylim(lim)
    ax.set_xticks([10, 30, 100, 300]), ax.set_xticklabels(["10", "30", "100", "300"])
    ax.set_yticks([3, 10, 30, 100, 300]), ax.set_yticklabels(["3", "10", "30", "100", "300"])
    ax.set_xlabel("State total minus published county counts")
    ax.set_ylabel("Model total for the suppressed counties")
    ax.legend(loc="upper left", frameon=False, fontsize=9.5)
    fig.text(0.075, 0.895, "Deaths in suppressed counties, by state", fontsize=13, fontweight="bold", color=NAVY)
    ax2 = fig.add_axes([0.6, 0.25, 0.385, 0.6])
    lv = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
    ax2.plot([0.45, 1], [0.45, 1], color=NAVY, linestyle="--", linewidth=1)
    p30 = res["validation"]["pseudo_30"]["models"]
    ax2.plot(lv, p30["spatial"]["coverage"], color=NAVY, marker="o", linewidth=2, label="Spatial model")
    ax2.plot(lv, p30["covariates_only"]["coverage"], color=GOLD, marker="s", linewidth=2, label="Same model, no spatial term")
    ax2.plot(lv, p30["poisson_gamma"]["coverage"], color=GREY, marker="^", linewidth=1.3, linestyle=":",
             label="No covariates, no state-total constraint")
    ax2.set_xlim(0.45, 1), ax2.set_ylim(0.45, 1)
    ax2.set_xlabel("Nominal interval level")
    ax2.set_ylabel("Share of scored true counts inside")
    ax2.legend(loc="upper left", frameon=False, fontsize=9.5)
    fig.text(0.6, 0.895, "Hide counts of 1-29, refit, score 10-29", fontsize=13, fontweight="bold", color=NAVY)
    source(fig, "Left: model fit without the state totals; dashed line is equality; 3 states with a negative residual are not shown.\n"
                "Right: every count under 30 treated as suppressed; only the counties with true counts of 10-29 can be scored "
                f"({res['validation']['pseudo_30']['n_scored']}), so this covers the upper part of the range.\n"
                "Source: CDC NCHS provisional county and state counts; Primordial Analytics.")
    return save(fig, f"{PREFIX}-validation.webp")


def thumbnail(cs):
    """400x300 thumbnail: the estimate map with a short title, rendered at that size."""
    g = _geo(cs)
    cs = cs.set_index("fips")
    g = g.set_index("GEOID").loc[cs.index].reset_index()
    hidden = cs.count_status.isin(["suppressed_1_to_9", "suppressed_data_quality"]).values
    fig = plt.figure(figsize=(4, 3))
    fig.text(0.03, 0.97, "Overdose rates where\ncounts are hidden", fontsize=12.5, fontweight="bold", color=NAVY, va="top", linespacing=1.15)
    ax = fig.add_axes([0.0, -0.02, 1.0, 0.82])
    _draw_map(ax, g, cs.rate_median_per_100k, np.zeros(len(g), bool))
    fig.savefig(IMG / f"{PREFIX}-thumbnail.webp", dpi=100, facecolor="white", pil_kwargs={"quality": 85, "method": 6})
    plt.close(fig)
    print("thumbnail", Image.open(IMG / f"{PREFIX}-thumbnail.webp").size)


def main(cs, res):
    fig_map(cs)
    thumbnail(cs)
    fig_widths(cs)
    fig_validation(res)


if __name__ == "__main__":
    cs = pd.read_pickle(data.RAW / "cache" / "full_county_table.pkl")
    main(cs, json.load(open(HERE / "output" / "model_results.json")))
