"""Build assets/examples/11/data.json, the one file the example page reads, from output/.

The page recomputes the Excel planner's formulas in the browser, so the per-county model results are copied from
output/county_table.csv exactly as the workbook's Counties sheet holds them (4 decimals). Nothing is modeled here.

Run on its own (python web_data.py) or from the last line of run.py. Prints the stat-tile strings for the page's front matter.

County row: [fips, name, state index, uninsured adults <=200% FPL 2024, SAHIE 90% margin, flags,
             low-income selections 2025, 2026, % change, stability-adjusted % change, G, C, A]
  flags (bit sum): 1 small pool (<500 adults), 2 wide margin (>20% of estimate), 4 fewer than 100 selections in a year,
                   8 a suppressed CMS cell was redrawn
  G  growth of the uninsured pool, in ten-thousandths (666 = 6.66%): the workbook's g_ columns
  C  growth a clinic has not yet seen in its last 12 months of visits: the cg_ columns
  A  additional uninsured adults, whole people: the add_ columns
  Order inside G and C: scenario (lower, central, higher) x layers (with Medicaid layer, marketplace only) x
  probability (50, 80, 95). Inside A the probabilities are 10, 50, 90. A county in a state that did not expand
  Medicaid has no Medicaid layer (the two layers are identical in the workbook), so it carries only the marketplace
  half: scenario x probability.

The page and the workbook both use the 4-decimal county growth values, so dollar figures can differ from numbers.json
(which comes from the unrounded model) by $1 or $2. Sessions, volunteers and hours match.
State paid shares are eff / sel rounded once, half up, so they match numbers.json.
"""
import csv
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
DEST = HERE.parents[1] / "assets" / "examples" / "11" / "data.json"

SCEN = ["lower", "central", "higher"]
VARS = ["all", "mkt"]
Q_G = ["p50", "p80", "p95"]
Q_A = ["p10", "p50", "p90"]
WEEKS_PER_YEAR = 50  # the Planner sheet's default (cell B27 in workbook.py); not stored in numbers.json
TOPO = HERE.parents[1] / "assets" / "examples" / "shared" / "us-counties-albers-10m.json"
# 2-digit state FIPS to postal code. A label table only; it carries no data.
FIPS_ST = dict(zip(
    "01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split(),
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()))
SHAPE_ALIAS = {"02261"}  # the map file still has Alaska's Valdez-Cordova; the data has its two successors (02063, 02066)


def half_up(x, places=0):
    """Round the way Excel does (half away from zero), so page and workbook agree on .5 cases."""
    q = Decimal(1).scaleb(-places)
    return int(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP)) if places == 0 else float(Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP))


def keys(prefix, qs, with_layers):
    return [f"{prefix}_{s}_{v}_{q}" for s in SCEN for v in (VARS if with_layers else ["mkt"]) for q in qs]


def num(x):
    f = float(x)
    return int(f) if f == int(f) else f


def build():
    numbers = json.loads((OUT / "numbers.json").read_text())
    counties = list(csv.DictReader((OUT / "county_table.csv").open()))
    states_csv = {r["state"]: r for r in csv.DictReader((OUT / "state_table.csv").open())}
    names = {r["state"]: r["state_name"] for r in counties}
    st_order = sorted(states_csv, key=lambda s: names[s])
    st_index = {s: i for i, s in enumerate(st_order)}

    rows = []
    for r in counties:
        exp = r["medicaid_expansion_state"] == "Y"
        flag = r["uninsured_estimate_flag"]
        flags = (1 if "small pool" in flag else 0) | (2 if "wide margin" in flag else 0) \
            | (4 if r["low_income_small_count"] == "Y" else 0) | (8 if r["low_income_suppressed_cell"] == "Y" else 0)
        G = [half_up(Decimal(r[k]) * 10000) for k in keys("g", Q_G, exp)]
        C = [half_up(Decimal(r[k]) * 10000) for k in keys("cg", Q_G, exp)]
        A = [half_up(Decimal(r[k])) for k in keys("add", Q_A, exp)]
        if not exp:  # the layers must really be identical, or dropping one would change the answer
            for k in keys("g", Q_G, True) + keys("cg", Q_G, True) + keys("add", Q_A, True):
                if "_all_" in k:
                    assert r[k] == r[k.replace("_all_", "_mkt_")], (r["fips"], k)
        rows.append([r["fips"], r["county"], st_index[r["state"]], num(r["uninsured_adults_le200_2024"]), num(r["uninsured_moe90"]), flags,
                     num(r["low_income_selections_2025"]), num(r["low_income_selections_2026"]),
                     float(r["low_income_pct_change"]), float(r["stability_adjusted_pct_change"]), G, C, A])

    states = []
    for s in st_order:
        t = states_csv[s]
        exp_row = next(r for r in counties if r["state"] == s)["medicaid_expansion_state"] == "Y"
        states.append({"st": s, "name": names[s], "exp": int(exp_row), "s25": num(t["low_sel_2025"]), "s26": num(t["low_sel_2026"]),
                       "r25": half_up(Decimal(t["eff_2025"]) / Decimal(t["sel_2025"]) * 100, 1),
                       "r26": half_up(Decimal(t["eff_2026"]) / Decimal(t["sel_2026"]) * 100, 1)})

    sc = numbers["scenarios_2054_counties"]
    nat = {s: {k: sc[s][k] for k in sc[s] if k.startswith(("total_", "marketplace_", "medicaid_"))} for s in SCEN}
    ex = numbers["example_clinic"]
    inp = ex["inputs"]
    data = {
        "_source": "analysis/11-free-clinic-surge-planner/web_data.py from output/county_table.csv, state_table.csv, numbers.json "
                   "(tornado and example clinic rows inside it). Built 2026-10-22 outputs; not edited by hand.",
        "layout": "see the docstring of web_data.py for the county row layout",
        "defaults": {"fips": inp["fips"], "patients": inp["patients"], "visits": ex["today_visits"], "perSession": inp["patients_per_session"],
                     "weeks": WEEKS_PER_YEAR, "volPerSession": inp["volunteers_per_session"], "hoursPerShift": inp["hours_per_shift"],
                     "shiftsPerVol": inp["shifts_per_volunteer"], "medPerVisit": inp["medication_per_visit"], "rho": inp["rho"]},
        "phi": numbers["assumptions"]["phi_share_of_2026_loss_in_trailing_year"],
        "states": states,
        "counties": rows,
        "outside": outside(rows, states),
        "nat": nat,
        "natBase": numbers["observed"]["uninsured_le200_baseline"],
        "tornado": {"base": numbers["tornado_example_county"]["base_sessions_p80"], "county": ex["county"],
                    "rows": [[t["assumption"], t["sessions_low"], t["sessions_high"]] for t in numbers["tornado_example_county"]["rows"]]},
        "top10": [[t["county"], t["state"], t["low_income_selections_2025"], t["low_income_selections_2026"], t["low_income_pct_change"],
                   t["stability_adjusted_pct_change"]] for t in numbers["ranking_top10_min500"]],
        "exampleRows": [[r["scenario"], r["layers"], r["probability"], r["sessions"], r["volunteers"], r["medication_dollars"]] for r in ex["rows"]],
    }
    return data, numbers


def outside(rows, states):
    """States and counties of the map file that the CMS county files do not cover, so the page can say so when a
    director searches for one. {"states": [[postal, name, covered 0/1]], "counties": {postal: [names]}}; counties of a
    covered state appear only when the data lacks them (for example Kalawao, HI)."""
    topo = json.loads(TOPO.read_text())
    have = {r[0] for r in rows}
    covered = {s["st"] for s in states}
    names = {FIPS_ST[g["id"]]: g["properties"]["name"] for g in topo["objects"]["states"]["geometries"] if g["id"] in FIPS_ST}
    counties = {}
    for g in topo["objects"]["counties"]["geometries"]:
        st = FIPS_ST[g["id"][:2]]
        if g["id"] not in have and g["id"] not in SHAPE_ALIAS:
            counties.setdefault(st, []).append(g["properties"]["name"])
    return {"states": sorted([[st, nm, int(st in covered)] for st, nm in names.items()], key=lambda r: r[1]),
            "counties": {st: sorted(v) for st, v in sorted(counties.items())}}


def tiles(numbers):
    sc = numbers["scenarios_2054_counties"]["central"]
    d = numbers["derived_example"]
    m = lambda v: f"{v / 1e6:.2f}M"
    return [
        (m(sc["total_p50"]), f"{sc['growth_total_p50_pct']}% above the 2024 pool; 80% interval {m(sc['total_p10'])} to {m(sc['total_p90'])}"),
        (f"{sc['median_county_growth_p50_expansion_pct']}%", f"Median county in Medicaid expansion states; {sc['median_county_growth_p50_other_pct']}% elsewhere"),
        (f"−{abs(numbers['observed']['paid_pct_change'])}%", f"Paid marketplace enrollment, Feb 2025 to Feb 2026: {numbers['observed']['paid_lost_feb2026_vs_feb2025']:,} fewer people"),
        (f"{d['central_sessions_p80']}", f"Sessions a year for the example clinic at 80% certainty, up from {numbers['example_clinic']['today_sessions']:.0f}"),
    ]


def main():
    data, numbers = build()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    print(f"wrote {DEST} ({DEST.stat().st_size / 1024:.0f} KB)")
    for v, n in tiles(numbers):
        print("tile:", v, "|", n)


if __name__ == "__main__":
    main()
