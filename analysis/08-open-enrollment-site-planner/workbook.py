"""The downloadable example plan: one county, five sites, live formulas for who counts, reach, its interval, and staff capacity.

Values come from the model (tract estimates, the five sites, each site's reach of each tract); everything that depends on
the inputs on the Plan sheet is a formula, so changing who counts or the staff hours recalculates the sheet.
"""
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

import prepare
import sites
import sources
from common import DEFAULT_TIERS, SITE, SLUG, TIER_LABEL, TIERS

NAVY, GOLD = "191345", "B3A369"
HEAD = PatternFill("solid", fgColor=GOLD)
INPUT = PatternFill("solid", fgColor="FFF2B3")
CALC = PatternFill("solid", fgColor="EFEFEF")
BOLD = Font(bold=True, color=NAVY)
TITLE = Font(bold=True, size=16, color=NAVY)
THIN = Side(style="thin", color="BBBBBB")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
TIER_SHORT = {"kids": "Children", "medicaid": "Medicaid range", "subsidy": "Subsidy range", "gap": "Coverage gap", "d400": "400% and over", "noncit": "Noncitizen adults"}
DEFAULT_ON = {"kids": "Yes", "medicaid": "Yes", "subsidy": "Yes", "gap": "No", "d400": "No", "noncit": "No"}


STAFF = {"people": 2, "appointments_per_day": 6, "days_per_week": 3}  # example staffing on the Plan sheet; the yellow cells change it
PAIRS = [(i, j) for i in range(len(TIERS)) for j in range(i + 1, len(TIERS))]


def pick_example(t, venues):
    """The median-population county among those in states that have not expanded Medicaid (so the coverage gap is not zero) and
    have 8 or more candidate venues: a county whose plan a small team could deliver."""
    pop = t.groupby("county").pop_all.sum()
    nv = venues.groupby("county").size().reindex(pop.index).fillna(0)
    st = t.groupby("county").state.first()
    ok = pop[st.isin(sources.NON_EXPANSION) & (nv >= 8)].sort_values()
    return ok.index[(len(ok) - 1) // 2]


def tier_stats(draws):
    """Per-tract standard deviations (n x 6) and correlations (n x 15, in PAIRS order) of the six tiers from their draws
    (draws: dict tier -> n x K)."""
    D = np.stack([np.asarray(draws[k], float) for k in TIERS], axis=1)  # n x 6 x K
    sd = D.std(2)
    c = D - D.mean(2, keepdims=True)
    cov = np.einsum("nik,njk->nij", c, c) / D.shape[2]
    corr = np.stack([np.where(sd[:, i] * sd[:, j] > 1e-9, cov[:, i, j] / np.maximum(sd[:, i] * sd[:, j], 1e-9), 0.0) for i, j in PAIRS], axis=1)
    return sd, np.clip(corr, -1, 1)


def eligible_sd(flags, sd, corr):
    """sd of the sum of the flagged tiers, with their correlations: the formula the Call sheet uses."""
    f = np.asarray(flags, float)
    var = (f ** 2 * sd ** 2).sum(1)
    for p, (i, j) in enumerate(PAIRS):
        var = var + 2 * f[i] * f[j] * corr[:, p] * sd[:, i] * sd[:, j]
    return np.sqrt(np.maximum(var, 0))


def plan_for(t, tr, venues, county, k=5):
    rows = np.flatnonzero(t.county.to_numpy() == county)
    vg = venues[venues.county == county].reset_index(drop=True)
    R = sites.county_radius(t.density_class.to_numpy()[rows], t.pop_all.to_numpy()[rows])
    a = sites.reach_matrix(t.lat.to_numpy()[rows], t.lon.to_numpy()[rows], vg.lat.to_numpy(), vg.lon.to_numpy(), R)
    w = tr.elig_mean.to_numpy(float)[rows]
    sel = sites.greedy(a, w, k)
    return rows, vg, R, a, sel


def header(ws, row, text, cols=8):
    for c in range(1, cols + 1):
        ws.cell(row, c).fill = HEAD
    ws.cell(row, 1, text).font = BOLD


def put(ws, ref, value, fmt=None, fill=None, bold=False):
    cell = ws[ref]
    cell.value = value
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
        cell.border = BOX
    if bold:
        cell.font = BOLD
    return cell


def add_cached_values(path):
    """openpyxl writes formulas without results; recalculate a copy in LibreOffice and write its results into the original."""
    soffice = shutil.which("soffice")
    if not soffice:
        print("soffice not found: workbook saved without cached values")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([soffice, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", tmp, str(path)], check=True, capture_output=True)
        calc = load_workbook(Path(tmp) / path.name, data_only=True)
    names = load_workbook(path, read_only=True).sheetnames
    cell = re.compile(r'<c r="([A-Z]+[0-9]+)"((?: [a-z]+="[^"]*")*)><f>(.*?)</f><v ?/></c>', re.S)
    with zipfile.ZipFile(path) as z:
        members = {n: z.read(n) for n in z.namelist()}
    for i, name in enumerate(names, start=1):
        ws = calc[name]

        def fill(m):
            v = ws[m.group(1)].value
            if v is None:
                return m.group(0)
            if isinstance(v, str):
                return f'<c r="{m.group(1)}"{m.group(2)} t="str"><f>{m.group(3)}</f><v>{escape(v)}</v></c>'
            return f'<c r="{m.group(1)}"{m.group(2)}><f>{m.group(3)}</f><v>{v!r}</v></c>'
        key = f"xl/worksheets/sheet{i}.xml"
        members[key] = cell.sub(fill, members[key].decode()).encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    return calc


def make(t, tr, co, venues, sahie, example, facts, zip_w, tier_draws, out_dir=None):
    out_dir = Path(out_dir or SITE / "downloads")
    rows, vg, R, a, sel = plan_for(t, tr, venues, example)
    sub = t.iloc[rows]
    ctr = tr.iloc[rows]
    order = np.argsort(-ctr.elig_mean.to_numpy(float))
    state = sub.state.iloc[0]
    cname = sahie.county_name.str.strip().get(example, example)
    label = f"{cname}, {state}"
    wb = Workbook()
    start, plan, call, zips, parts, ven, ass = (wb.active, wb.create_sheet("Plan"), wb.create_sheet("Call sheet"), wb.create_sheet("ZIP roll-up"),
                                                 wb.create_sheet("ZIP parts"), wb.create_sheet("Venues"), wb.create_sheet("Assumptions and sources"))
    start.title = "Start here"
    n = len(rows)
    last = n + 1
    oe = facts["open_enrollment"]
    weeks = round((date.fromisoformat(oe["deadline_jan1_coverage"]) - date.fromisoformat(oe["start"])).days / 7)  # open enrollment start to the Jan 1 coverage deadline

    # ---- Call sheet: one row per tract
    sd_t, corr_t = tier_stats({k: tier_draws[k][order] for k in TIERS})
    nt = len(TIERS)
    heads = ["Tract", "Nearest ZIP area", "Population"] + [TIER_SHORT[k] for k in TIERS] + [f"sd {TIER_SHORT[k]}" for k in TIERS] + \
            [f"corr {TIER_SHORT[TIERS[i]]} / {TIER_SHORT[TIERS[j]]}" for i, j in PAIRS] + \
            ["Eligible (who counts)", "Spread of eligible (sd)", "Share of the tract reached by the plan (distance-weighted)"] + [f"Reach weight of site {i + 1}" for i in range(len(sel))] + ["Survey's own count (default tiers)", "Can be ranked"]
    call.append(heads)
    c_tier = {k: 4 + i for i, k in enumerate(TIERS)}
    c_sd = {k: 4 + nt + i for i, k in enumerate(TIERS)}
    c_corr0 = 4 + 2 * nt
    c_el = c_corr0 + len(PAIRS)
    c_sdel, c_share = c_el + 1, c_el + 2
    c_site0 = c_share + 1
    c_direct = c_site0 + len(sel)
    L = get_column_letter
    tier_rng = f"{L(c_tier[TIERS[0]])}{{r}}:{L(c_tier[TIERS[-1]])}{{r}}"
    flag = lambda i: f"Plan!${L(3 + i)}$6"
    sd_ref = lambda i, r: f"{L(c_sd[TIERS[i]])}{r}"

    def sd_formula(r):
        terms = [f"{flag(i)}*{sd_ref(i, r)}^2" for i in range(nt)]
        terms += [f"2*{flag(i)}*{flag(j)}*{L(c_corr0 + p)}{r}*{sd_ref(i, r)}*{sd_ref(j, r)}" for p, (i, j) in enumerate(PAIRS)]
        return "=SQRT(MAX(0," + "+".join(terms) + "))"
    for r, i in enumerate(order, start=2):
        tid = sub.index[i]
        o = r - 2
        row = [tid, sub.zcta.iloc[i] if isinstance(sub.zcta.iloc[i], str) else "", int(sub.pop_all.iloc[i])]
        row += [float(round(ctr[f"{k}_mean"].iloc[i], 1)) for k in TIERS]
        row += [float(round(sd_t[o, q], 3)) for q in range(nt)]
        row += [float(round(corr_t[o, p], 3)) for p in range(len(PAIRS))]
        row += [f"=SUMPRODUCT(Plan!$C$6:$H$6,{tier_rng.format(r=r)})", sd_formula(r),
                f"=MIN(1,SUM({L(c_site0)}{r}:{L(c_site0 + len(sel) - 1)}{r}))"]
        row += [float(round(a[i, j], 4)) for j in sel]
        row += [float(round(ctr.elig_direct.iloc[i], 1)), int(ctr.can_rank.iloc[i])]
        call.append(row)
    for c in range(1, len(heads) + 1):
        call.cell(1, c).font = BOLD
        call.cell(1, c).fill = HEAD
        call.cell(1, c).alignment = WRAP
        call.column_dimensions[L(c)].width = 13
    call.column_dimensions["A"].width = 14
    call.row_dimensions[1].height = 45
    call.freeze_panes = "D2"
    call.auto_filter.ref = f"A1:{L(len(heads))}{last}"
    el_col, sd_col, sh_col = (f"'Call sheet'!${L(c)}$2:${L(c)}${last}" for c in (c_el, c_sdel, c_share))

    # ---- Plan sheet
    ws = plan
    ws.column_dimensions["A"].width = 58
    for col in "BCDEFGHI":
        ws.column_dimensions[col].width = 16
    ws["A1"] = f"Open enrollment site plan: {label}"
    ws["A1"].font = TITLE
    ws["A2"] = "An example on public data, not client work. Yellow cells are yours to change; the rest recalculates."
    header(ws, 4, "1. Who counts")
    ws["A5"] = "Count these groups (Yes or No)"
    for j, k in enumerate(TIERS):
        ws.cell(5, 3 + j, TIER_SHORT[k]).font = BOLD
        ws.cell(5, 3 + j).alignment = WRAP
        put(ws, f"{L(3 + j)}6", 1 if DEFAULT_ON[k] == "Yes" else 0, fill=INPUT)
    ws["A6"] = "1 counts the group, 0 leaves it out"
    ws["A7"] = "Noncitizen adults: eligibility varies; the survey cannot tell who can get help paying premiums. Children at 400% of poverty and over are in the 400% group."
    dv = DataValidation(type="list", formula1='"0,1"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("C6:H6")
    header(ws, 9, f"2. What the five sites reach (distance {R:g} miles, straight line x {sites.CIRCUITY})")
    ws["A8"] = ("Expected reach = sum over tracts of eligible people x min(1, sum of the sites' weights for the tract). A site's weight for a tract is "
                "exp(-2 (d / R)^2) up to R miles, so a tract at the limit counts " + f"{100 * np.exp(-2):.0f}" + "% of its people. It is not a headcount of people who will come.")
    ws["A8"].alignment = WRAP
    ws.row_dimensions[8].height = 48
    put(ws, "A10", "Eligible uninsured people in the county")
    put(ws, "B10", f"=SUM({el_col})", "#,##0", CALC)
    put(ws, "A11", "Expected reach of the plan (people, distance-weighted)")
    put(ws, "B11", f"=SUMPRODUCT({el_col},{sh_col})", "#,##0", CALC, bold=True)
    put(ws, "A12", "Expected reach as a share of the county's eligible people")
    put(ws, "B12", "=B11/B10", "0%", CALC)
    put(ws, "A13", "County factor for the interval (from the model draws)")
    put(ws, "B13", float(round(co.plan_inflation[example], 3)), "0.00", CALC)
    put(ws, "A14", "Expected reach, 90% interval low")
    put(ws, "B14", f"=MAX(0,B11-1.645*B13*SQRT(SUMPRODUCT({sh_col}^2,{sd_col}^2)))", "#,##0", CALC)
    put(ws, "A15", "Expected reach, 90% interval high")
    put(ws, "B15", f"=MIN(B10,B11+1.645*B13*SQRT(SUMPRODUCT({sh_col}^2,{sd_col}^2)))", "#,##0", CALC)
    ws["A16"] = "The interval is for the default settings (five sites, the default distance). It counts the model's tract ranges and the correlation between the groups you switch on."
    ws["A16"].alignment = WRAP
    ws.row_dimensions[16].height = 32
    header(ws, 17, "3. Staff hours")
    put(ws, "A18", "Navigators or counselors at each event")
    put(ws, "B18", STAFF["people"], "0", INPUT)
    put(ws, "A19", "Appointments one person can do in a day")
    put(ws, "B19", STAFF["appointments_per_day"], "0", INPUT)
    put(ws, "A20", "Days a week each site is open")
    put(ws, "B20", STAFF["days_per_week"], "0", INPUT)
    put(ws, "A21", "Weeks before the date that matters to you")
    put(ws, "B21", weeks, "0.0", INPUT)
    put(ws, "A22", "Appointments a site can do in a week")
    put(ws, "B22", "=B18*B19*B20", "#,##0", CALC)
    put(ws, "A23", "Appointments the staff hours provide before that date, all sites")
    put(ws, "B23", "=B22*B21*" + str(len(sel)), "#,##0", CALC)
    put(ws, "A24", "Each person needs one appointment: share of the expected reach the staff hours can see")
    put(ws, "B24", "=MIN(1,B23/B11)", "0%", CALC, bold=True)
    header(ws, 25, "4. The sites", 9)
    for j, h in enumerate(["Site", "Kind", "Address", "Expected reach of this site (people)", "Weeks to see them all", "Share seen in the weeks you have"]):
        ws.cell(26, 1 + j, h).font = BOLD
        ws.cell(26, 1 + j).alignment = WRAP
    for s_i, j in enumerate(sel):
        r = 27 + s_i
        v = vg.iloc[j]
        put(ws, f"A{r}", str(v["name"]))
        put(ws, f"B{r}", "Library" if v.kind == "library" else "Health center")
        put(ws, f"C{r}", f"{v.address}, {v.city} {v.zip}")
        col = L(c_site0 + s_i)
        put(ws, f"D{r}", f"=SUMPRODUCT({el_col},'Call sheet'!${col}$2:${col}${last})", "#,##0", CALC)
        put(ws, f"E{r}", f"=D{r}/$B$22", "0.0", CALC)
        put(ws, f"F{r}", f"=MIN(1,$B$21/E{r})", "0%", CALC)
    ws["A33"] = "Sites overlap, so the expected reach of each site adds up to more than the plan's expected reach in B11."
    ws["A33"].alignment = WRAP

    # ---- ZIP parts and roll-up
    w = zip_w[zip_w.geoid.isin(sub.index)]
    parts.append(["Tract", "ZIP area", "Share of the tract's land in the ZIP area", "Tract eligible (from Call sheet)", "Eligible in this part", "Reach share of the plan"])
    call_tract_col = f"'Call sheet'!$A$2:$A${last}"
    for r, (_, p) in enumerate(w.iterrows(), start=2):
        parts.append([p.geoid, p.zcta, float(round(p.w, 4)),
                      f"=INDEX({el_col},MATCH(A{r},{call_tract_col},0))", f"=C{r}*D{r}",
                      f"=INDEX({sh_col},MATCH(A{r},{call_tract_col},0))*E{r}"])
    for c in range(1, 7):
        parts.cell(1, c).font = BOLD
        parts.cell(1, c).fill = HEAD
        parts.cell(1, c).alignment = WRAP
        parts.column_dimensions[L(c)].width = 18
    parts_last = len(w) + 1
    zlist = pd.Series(w.w.to_numpy() * ctr.elig_mean.reindex(w.geoid).to_numpy(), index=w.zcta.to_numpy()).groupby(level=0).sum().sort_values(ascending=False)
    zips.append(["ZIP area (ZCTA, not always the mailing ZIP)", "Eligible uninsured (who counts)", "Of them, within reach of the plan"])
    for r, z in enumerate(zlist.index, start=2):
        zips.append([z, f"=SUMIF('ZIP parts'!$B$2:$B${parts_last},A{r},'ZIP parts'!$E$2:$E${parts_last})",
                     f"=SUMIF('ZIP parts'!$B$2:$B${parts_last},A{r},'ZIP parts'!$F$2:$F${parts_last})"])
    for c in range(1, 4):
        zips.cell(1, c).font = BOLD
        zips.cell(1, c).fill = HEAD
        zips.cell(1, c).alignment = WRAP
        zips.column_dimensions[L(c)].width = 28
    zips.freeze_panes = "A2"

    # ---- Venues
    ven.append(["Venue", "Kind", "Address", "City", "ZIP", "Latitude", "Longitude", "Tract", "In the plan"])
    chosen = set(vg.venue_id.iloc[sel])
    for _, v in vg.iterrows():
        ven.append([v["name"], "Library" if v.kind == "library" else "Health center", v.address, v.city, v.zip, float(v.lat), float(v.lon), v.tract,
                    "Yes" if v.venue_id in chosen else ""])
    for c in range(1, 10):
        ven.cell(1, c).font = BOLD
        ven.cell(1, c).fill = HEAD
        ven.column_dimensions[L(c)].width = 24
    ven.freeze_panes = "A2"

    # ---- Start here and assumptions
    start.column_dimensions["A"].width = 110
    lines = [("Open enrollment site plan (example)", TITLE),
             (f"County: {label}. Chosen by rule: {EXAMPLE_RULE_TEXT}.", None),
             ("An example on public data, not client work. Model outputs are estimate ranges, not forecasts.", None),
             ("", None),
             ("Plan: choose who counts and your staff hours (yellow); expected reach, its 90% interval and the weeks to see everyone recalculate.", None),
             ("Call sheet: one row per census tract with the modelled number of uninsured people in each group, their spread and correlation, and how much of the tract each site reaches.", None),
             ("ZIP roll-up: the same numbers by ZIP area, split by the share of each tract's land in the ZIP area (so some people are placed on empty land).", None),
             ("Venues: every library and health center site in the county that the planner considered. The five in the plan are marked.", None),
             ("To pick different sites, use the planner on the page, which runs the same rule.", None)]
    for i, (txt, font) in enumerate(lines, start=1):
        start.cell(i, 1, txt)
        start.cell(i, 1).alignment = WRAP
        if font:
            start.cell(i, 1).font = font
    ass.column_dimensions["A"].width = 120
    ass_lines = [
        "Estimates: ACS 2020-2024 5-year tables C27016 and B27020 (Census), small-area model with CDC PLACES 2025, Census SAHIE 2024 and ACS 2024 1-year PUMS. Ranges are 5th to 95th percentiles of 1,000 draws.",
        f"Reach rule: each site reaches a tract with weight exp(-2 (d / R)^2) up to R = {R:g} miles; d is straight-line miles x {sites.CIRCUITY}. A tract's share is the sum over sites, capped at 1.",
        "Sites: libraries (IMLS FY2023; some will have closed) and permanent health center service sites open 20 or more hours a week (HRSA, " + str(facts["checked"]) + "). They stand in for places an assister can meet people.",
        "The interval: tract ranges are combined with their correlations as if tracts were independent, then multiplied by the county factor in Plan!B13 (checked against Monte Carlo on the page). It is for the default settings.",
        "Noncitizen adults are shown apart. The survey cannot tell green card holders from other noncitizens, so eligibility varies.",
        f"Open enrollment: {facts['open_enrollment']['text']} (checked {facts['open_enrollment']['checked']}; {facts['open_enrollment']['source']}).",
        f"Medicaid expansion: not adopted in {', '.join(sources.NON_EXPANSION)} (KFF, checked {sources.CHECKED}). Wisconsin has a waiver program that covers adults under 100%; Georgia's Pathways has a work requirement and is not counted.",
        "Survey years are 2020-2024 and predate the 2026 drop in enrollment. Distance is straight-line, with no transit, hours or language.",
    ]
    for i, txt in enumerate(ass_lines, start=1):
        ass.cell(i, 1, txt)
        ass.cell(i, 1).alignment = WRAP
    path = out_dir / f"{SLUG}-example-plan.xlsx"
    wb.save(path)
    calc = add_cached_values(path)
    info = {"county": example, "label": label, "sites": [str(vg.iloc[j]["name"]) for j in sel], "radius_miles": R, "tract_rows": n,
            "venues": int(len(vg)), "population": int(sub.pop_all.sum()), "state": state, "staff": STAFF, "weeks": weeks}
    if calc is not None:
        pv = calc["Plan"]
        info["workbook_reach"], info["workbook_lo"], info["workbook_hi"] = pv["B11"].value, pv["B14"].value, pv["B15"].value
        info["workbook_county_eligible"] = pv["B10"].value
    # the same quantities from the code the page's rule mirrors
    w_default = ctr.elig_mean.to_numpy(float)
    cov = sites.plan_coverage(a, sel)
    sd_el = eligible_sd([1 if k in DEFAULT_TIERS else 0 for k in TIERS], sd_t, corr_t)
    mid = float(w_default[order] @ cov[order])
    half = 1.645 * float(co.plan_inflation[example]) * float(np.sqrt((cov[order] ** 2 * sd_el ** 2).sum()))
    info["county_eligible"] = float(w_default.sum())
    info["python_reach"], info["python_lo"], info["python_hi"] = mid, max(0.0, mid - half), min(info["county_eligible"], mid + half)
    info["appointments_available"] = STAFF["people"] * STAFF["appointments_per_day"] * STAFF["days_per_week"] * weeks * len(sel)
    info["share_of_expected_reach_seen"] = min(1.0, info["appointments_available"] / mid)
    if "workbook_reach" in info:
        info["max_abs_difference"] = float(max(abs(info["workbook_reach"] - mid), abs(info["workbook_lo"] - info["python_lo"]), abs(info["workbook_hi"] - info["python_hi"])))
    return info


EXAMPLE_RULE_TEXT = ("the median-population county among those in states that have not expanded Medicaid (so the coverage gap is not zero) "
                     "with 8 or more candidate venues")
