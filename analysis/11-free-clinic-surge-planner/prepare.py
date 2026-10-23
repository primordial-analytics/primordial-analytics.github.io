"""Load and clean the raw files into county and state tables.

Conventions
- Plan-selection counts are comma-formatted text. '*' marks a suppressed small cell (1-10 people).
- Both CMS files carry a 'Total' row that is dropped before any sum.
- Counties are matched on 5-digit FIPS. Illinois is in 2025 only (it left HealthCare.gov for 2026).
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw"
SUPP = "*"  # CMS small-cell marker
LOW_BANDS = ["FPL_100_150", "FPL_150_200"]  # 100-200% of the federal poverty level


def _num(s):
    s = s.str.strip().str.replace(",", "").str.replace("$", "", regex=False)
    return pd.to_numeric(s.where(s != SUPP), errors="coerce")


def _find(d, pattern):
    return next(Path(d).rglob(pattern))


def load_oep(folder, year):
    raw = pd.read_csv(_find(RAW / folder, "*.csv"), dtype=str)
    total = raw[raw.State_Abrvtn == "Total"]
    raw = raw[raw.State_Abrvtn != "Total"]
    out = pd.DataFrame({"state": raw.State_Abrvtn, "fips": raw.County_FIPS_Cd})
    cols = ["Cnsmr", "New_Cnsmr", "Auto_Renrl", "Avg_Prm_Aftr_APTC", "Cnsmr_Prm_Aftr_APTC_LTEQ10",
            "Age_0_17", "Age_GE65", *LOW_BANDS]
    for c in cols:
        out[f"{c}_{year}"] = _num(raw[c])
        out[f"{c}_supp_{year}"] = raw[c].str.strip() == SUPP
    return out, int(_num(total.Cnsmr).iloc[0])


def load_sahie():
    path = _find(RAW / "sahie", "sahie_*.csv")
    keep = ["statefips", "countyfips", "geocat", "agecat", "racecat", "sexcat", "iprcat", "NIPR", "NUI", "nui_moe",
            "state_name", "county_name"]
    d = pd.read_csv(path, skiprows=85, dtype=str, skipinitialspace=True, usecols=lambda c: c.strip() in keep)
    d.columns = [c.strip() for c in d.columns]
    for c in ["agecat", "racecat", "sexcat"]:
        d[c] = d[c].str.strip()
    adults = d[(d.agecat == "1") & (d.racecat == "0") & (d.sexcat == "0")].copy()
    for c in adults.columns:
        adults[c] = adults[c].str.strip()
    county = adults[adults.geocat == "50"].copy()
    county["fips"] = county.statefips + county.countyfips
    for c in ["NIPR", "NUI", "nui_moe"]:
        county[c] = pd.to_numeric(county[c], errors="coerce")  # "." marks N/A (Kalawao, HI)
    le200 = county[county.iprcat == "1"].set_index("fips")
    le138 = county[county.iprcat == "3"].set_index("fips")
    base = pd.DataFrame({
        "county_name": le200.county_name, "state_name": le200.state_name,
        "pop_le200": le200.NIPR, "uninsured_le200": le200.NUI, "uninsured_moe90": le200.nui_moe,
        "pop_le138": le138.NIPR,
    })
    # Weight for allocating state Medicaid enrollment to counties: share of the state's 18-64 population at or below 138% of poverty.
    base["pop138_share"] = base.pop_le138 / base.pop_le138.groupby(base.index.str[:2]).transform("sum")
    state_le200 = adults[(adults.geocat == "40") & (adults.iprcat == "1")]
    check = {"state_rows_uninsured_le200": float(pd.to_numeric(state_le200.NUI).sum()),
             "county_rows_uninsured_le200": float(le200.NUI.sum())}
    return base.reset_index(), check


def load_effectuated():
    e = pd.read_csv(RAW / "effectuated.csv")
    e = e[(e.Platform == "HealthCare.gov") & (e.Month == "February") & (e.State != "Total")]
    return e.pivot_table(index="State", columns="Year", values="Effectuated_Enr")[[2025, 2026]]


def load_medicaid():
    p = pd.read_csv(RAW / "medicaid_pi.csv", dtype=str)
    p = p[p["Reporting Period"] == p["Reporting Period"].max()]
    out = pd.DataFrame({
        "state": p["State Abbreviation"],
        "expansion": p["State Expanded Medicaid"] == "Y",
        "medicaid_chip": pd.to_numeric(p["Total Medicaid and CHIP Enrollment"], errors="coerce"),
    }).set_index("state")
    return out, p["Reporting Period"].max()


def adult_share(df, y):
    """Share of selectors aged 18-64: the county value where both age cells are published, else the state's pooled share."""
    ok = df[f"Age_0_17_{y}"].notna() & df[f"Age_GE65_{y}"].notna()
    own = 1 - (df[f"Age_0_17_{y}"] + df[f"Age_GE65_{y}"]) / df[f"Cnsmr_{y}"]
    g = df[ok].groupby("state")
    pooled = 1 - (g[f"Age_0_17_{y}"].sum() + g[f"Age_GE65_{y}"].sum()) / g[f"Cnsmr_{y}"].sum()
    return own.where(ok, df.state.map(pooled)).clip(0.5, 1.0)


def build():
    o26, total26 = load_oep("oep2026", 2026)
    o25, total25 = load_oep("oep2025", 2025)
    c = o26.merge(o25.drop(columns="state"), on="fips")
    for y in (2025, 2026):
        c[f"adult_share_{y}"] = adult_share(c, y)
    sahie, sahie_check = load_sahie()
    c = c.merge(sahie, on="fips", how="left")
    eff = load_effectuated()
    medicaid, pi_period = load_medicaid()
    allp = pd.read_csv(RAW / "effectuated.csv")
    allp = allp[(allp.State == "Total") & (allp.Platform == "All") & (allp.Month == "February")].set_index("Year").Effectuated_Enr

    # State effectuation: February paid enrollment over open-enrollment selections (all counties in each file).
    sel = pd.DataFrame({"sel_2026": o26.groupby("state").Cnsmr_2026.sum(),
                        "sel_2025": o25.groupby("state").Cnsmr_2025.sum()})
    st = sel.join(eff.rename(columns={2025: "eff_2025", 2026: "eff_2026"}), how="inner")
    st["rate_2025"] = st.eff_2025 / st.sel_2025
    st["rate_2026"] = st.eff_2026 / st.sel_2026
    st = st.join(medicaid, how="left")
    g = c.groupby("state")
    st["auto_share_2026"] = g.Auto_Renrl_2026.sum() / g.Cnsmr_2026.sum()
    st["auto_share_2025"] = g.Auto_Renrl_2025.sum() / g.Cnsmr_2025.sum()
    st["le10_share_2026"] = g.Cnsmr_Prm_Aftr_APTC_LTEQ10_2026.sum() / g.Cnsmr_2026.sum()
    st["low_sel_2025"] = g.FPL_100_150_2025.sum() + g.FPL_150_200_2025.sum()
    st["low_sel_2026"] = g.FPL_100_150_2026.sum() + g.FPL_150_200_2026.sum()
    st["premium_med_2025"] = g.Avg_Prm_Aftr_APTC_2025.median()
    st["premium_med_2026"] = g.Avg_Prm_Aftr_APTC_2026.median()
    c = c.merge(st[["rate_2025", "rate_2026", "expansion", "medicaid_chip"]], left_on="state", right_index=True, how="left")
    checks = {"oep2026_total_row": total26, "oep2026_county_sum": float(o26.Cnsmr_2026.sum()),
              "oep2025_total_row": total25, "oep2025_county_sum": float(o25.Cnsmr_2025.sum()),
              "oep2025_counties": len(o25), "oep2026_counties": len(o26), "matched_counties": len(c),
              "pi_period": pi_period, "cms_all_platform_feb2025": int(allp[2025]), "cms_all_platform_feb2026": int(allp[2026]), **sahie_check}
    return c, st, checks
