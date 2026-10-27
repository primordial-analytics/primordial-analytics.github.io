"""Combine the parsed batches into one table of returns and one of grants.

A return can appear more than once (an amended return, or the same return in two processing years). For each filer,
form and tax period only the latest submission is kept: object IDs grow with submission time. Grants from a return whose
listed grants add to more than 10 times the total it reports are dropped.
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw"
TAX_YEARS = range(2020, 2026)  # 2019 returns are only partly in these batches


def bmf():
    return pd.concat([pd.read_csv(RAW / f"eo{i}.csv", dtype=str, keep_default_na=False) for i in range(1, 5)],
                     ignore_index=True).drop_duplicates("EIN")


RETURN_COLS = ["object_id", "ein", "name", "city", "state", "zip", "form", "tax_year", "period_end", "revenue",
               "grants_paid", "daf", "hospital", "preselected", "website"]


def returns(columns=RETURN_COLS):
    """Latest return per filer, form and tax period. The long text fields (mission, how to apply) are left out unless
    asked for: they triple the memory."""
    f = pd.concat([pd.read_parquet(p, columns=columns) for p in sorted((RAW / "_parsed").glob("*.filings.parquet"))],
                  ignore_index=True)
    f = f[f.tax_year.str.isdigit()].assign(tax_year=lambda d: d.tax_year.astype(int))
    f = f[f.tax_year.isin(TAX_YEARS)]
    return f.sort_values("object_id").drop_duplicates(["ein", "form", "period_end"], keep="last").reset_index(drop=True)


def grants(kept):
    g = pd.concat([pd.read_parquet(p) for p in sorted((RAW / "_parsed").glob("*.grants.parquet"))], ignore_index=True)
    g = g[g.object_id.isin(set(kept.object_id))]
    # a return whose listed grants add to more than 10 times the grants it reports paying has mis-keyed amounts
    listed = g.groupby("object_id").amount.sum()
    paid = kept.set_index("object_id").grants_paid.reindex(listed.index)
    g = g[~g.object_id.isin(listed.index[(paid > 0) & (listed > 10 * paid)])]
    return g.merge(kept[["object_id", "ein", "form", "tax_year"]].rename(columns={"ein": "funder_ein"}), on="object_id")
