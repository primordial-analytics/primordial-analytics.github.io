"""Shared paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

# Medicaid expansion states and DC with the adult group in place on 2026-10-22
# (the 41 jurisdictions that expanded; Georgia and Wisconsin are not in it).
EXPANSION = {
    "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SD": "South Dakota",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia",
}

# CMS interim final rule (91 FR 33348, Federal Register 2026-11094), the
# published parameters. Tables 37-40 are images in the Federal Register text;
# values below were read from the PDF pages (33458-33460).
CMS = {
    "applicable_adults_m": 20.0,        # about 20 million adult-group enrollees
    "excl_components": {                # Table 37
        "aian": 0.025, "pregnant_postpartum": 0.017,
        "caretaker": 0.085, "inmate": 0.015, "medically_frail": 0.10,
    },
    "hardship_if_adopted": 0.046,       # Table 38: 0.0 + 0.4 + 0.8 + 3.4 percent
    "hardship_adoption": 0.75,          # 75 percent of states assumed to adopt
    "hardship_expected": 0.0345,        # text: 3.45 percent of applicable adults
    "excl_combined": 0.24,              # text: 24 percent
    "subject_share": 0.74,              # text: 26 percent excluded or hardship
    "noncomp_central": 0.12, "proc_central": 0.07, "combined_central": 0.15,
    "ex_parte_share": 0.56,             # 56 percent verified ex parte
    # Table 39: scenario weights, noncompliance and net procedural disenrollment
    "scenario_weight": [0.5, 0.1, 0.2, 0.2],
    "scenario_noncomp": [0.10, 0.19, 0.14, 0.14],
    "scenario_proc": [0.05, 0.10, 0.05, 0.10],
    "fy2027_enrollment_reduction_m": 2.3,   # Table 41
    "fy2027_share_of_full_year": 0.75,
}
