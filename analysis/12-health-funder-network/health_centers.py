"""Which registered nonprofits are health centers: HRSA's list of health center organizations (federally funded
health centers and look-alikes), matched to the IRS Business Master File by the same name rules as grant recipients
(match.rules), then by a near-identical name in the same ZIP code.
"""
import pandas as pd
from rapidfuzz import fuzz

import match

NEAR = 92  # token-set likeness for a name in the same ZIP code


def load(path):
    d = pd.read_csv(path, dtype=str)
    d = d.rename(columns={"Health Center Name": "name", "Health Center Organization City": "city",
                          "Health Center Organization State": "state", "Health Center Organization ZIP Code": "zip",
                          "Health Center Type": "type"})
    d["zip"] = d.zip.str[:5]
    return d.drop_duplicates(["name", "state", "zip"])[["name", "city", "state", "zip", "type"]].reset_index(drop=True)


def match_bmf(hc, bmf):
    """Returns hc with an `ein` column ('' when not found)."""
    b = match.prepare(bmf)
    rec = hc.assign(n=hc.name.map(match.norm), ein="", cityn=hc.city.fillna("").map(match.norm))
    rec["ein"], rec["how"] = match.rules(rec, b, set())
    by_zip = b.groupby("zip5")
    for i, r in rec[rec.ein == ""].iterrows():
        if r.zip not in by_zip.groups:
            continue
        pool = by_zip.get_group(r.zip)
        scores = pool.n.map(lambda n: fuzz.token_set_ratio(r.n, n))
        if scores.max() >= NEAR and (scores == scores.max()).sum() == 1:
            rec.loc[i, ["ein", "how"]] = [pool.EIN[scores.idxmax()], "near name+zip"]
    return rec.drop(columns=["n", "cityn"])
