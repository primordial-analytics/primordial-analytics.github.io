"""Shared paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output"
SITE = ROOT.parent.parent
SLUG = "08-open-enrollment-site-planner"
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(exist_ok=True)

SEED = 20261023
K = 1000  # posterior draws per tract and target

STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
    "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
    "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
    "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
# Census divisions (and the four regions that contain them), used to pool small states and to fit one model per region.
DIVISION = {
    "CT": 1, "ME": 1, "MA": 1, "NH": 1, "RI": 1, "VT": 1, "NJ": 2, "NY": 2, "PA": 2,
    "IL": 3, "IN": 3, "MI": 3, "OH": 3, "WI": 3, "IA": 4, "KS": 4, "MN": 4, "MO": 4, "NE": 4, "ND": 4, "SD": 4,
    "DE": 5, "DC": 5, "FL": 5, "GA": 5, "MD": 5, "NC": 5, "SC": 5, "VA": 5, "WV": 5, "AL": 6, "KY": 6, "MS": 6, "TN": 6,
    "AR": 7, "LA": 7, "OK": 7, "TX": 7, "AZ": 8, "CO": 8, "ID": 8, "MT": 8, "NV": 8, "NM": 8, "UT": 8, "WY": 8,
    "AK": 9, "CA": 9, "HI": 9, "OR": 9, "WA": 9,
}
REGION = {1: "Northeast", 2: "Northeast", 3: "Midwest", 4: "Midwest", 5: "South", 6: "South", 7: "South", 8: "West", 9: "West"}

# Targets modelled for every tract. Adults are 19 to 64. Bands are the C27016 income-to-poverty bands; A (under 100%)
# and B (100-137%) are split from L afterwards.
TARGETS = ["kids", "L", "C", "D"]
TARGET_LABEL = {
    "kids": "children under 19, all incomes", "L": "adults at or below 138% of poverty",
    "C": "adults 138 to 399%", "D": "adults 400% and over",
}
# Tiers shown to the user. The first three are what the tool counts by default.
TIERS = ["kids", "medicaid", "subsidy", "gap", "d400", "noncit"]
TIER_LABEL = {
    "kids": "Children under 19 and under 400% of poverty", "medicaid": "Adults in the Medicaid range", "subsidy": "Adults in the subsidy range",
    "gap": "Adults in the coverage gap", "d400": "People at 400% and over", "noncit": "Noncitizen adults (eligibility varies)",
}
DEFAULT_TIERS = ["kids", "medicaid", "subsidy"]
