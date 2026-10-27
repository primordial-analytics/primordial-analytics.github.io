"""Money between grantmakers, for following a funder's money end to end: where its grant money comes from (two steps
back) and where it goes (straight to organizations like yours, or through grantmakers that fund them).

A flow is the sum of the grants in RECENT years from one filer to a matched recipient that itself lists grants.
  related  the two list each other on Schedule R
  back     the recipient also gave to the giver in those years: money that goes round
A path through a grantmaker shows where money could have gone, not that the same dollars moved: a grantmaker pools what
it receives before it gives.
"""
import pandas as pd

import results


def flows(g, pairs):
    """g: every linked grant (funder_ein, ein, tax_year, amount). Returns src, dst, dollars, grants, related, back."""
    r = g[g.tax_year.isin(results.RECENT) & g.ein.notna() & (g.ein != "")]
    r = r[r.ein.isin(set(g.funder_ein)) & (r.ein != r.funder_ein)]
    fl = (r.groupby(["funder_ein", "ein"]).amount.agg(dollars="sum", grants="size").reset_index()
          .rename(columns={"funder_ein": "src", "ein": "dst"}))
    fl["related"] = [(a, b) in pairs for a, b in zip(fl.src, fl.dst)]
    given = set(zip(fl.src, fl.dst))
    fl["back"] = [(b, a) in given for a, b in zip(fl.src, fl.dst)]
    return fl


def grantmakers(u, fl, g, latest, bmf, funders):
    """Every grantmaker in the flows u, and every funder: name, city and state (its latest return, else the Business Master File), the
    grant dollars it received from other grantmakers (all flows fl) and the dollars of all the grants it listed, both
    in RECENT years."""
    eins = sorted(set(u.src) | set(u.dst) | set(funders))
    out = latest.set_index("ein").reindex(eins)[["name", "city", "state"]]
    b = bmf.set_index("EIN").reindex(eins)
    for c, bc in (("name", "NAME"), ("city", "CITY"), ("state", "STATE")):
        out[c] = out[c].where(out[c].notna() & (out[c] != ""), b[bc])
    out["received"] = fl.groupby("dst").dollars.sum().reindex(eins).fillna(0)
    out["given"] = g[g.tax_year.isin(results.RECENT)].groupby("funder_ein").amount.sum().reindex(eins).fillna(0)
    return out.fillna("").rename_axis("ein")


TOP_IN, TOP_IN2, TOP_MID = 8, 3, 8


def _top(fl, key, n):
    """The n largest flows for each value of `key`, largest first (ties by EIN, so the choice is fixed)."""
    return fl.sort_values(["dollars", "src", "dst"], ascending=[False, True, True]).groupby(key, sort=False).head(n)


def traces(fl, funders):
    """Each funder's trace, as rows (center, hop, src, dst, dollars, grants, related, back):
      in1  its TOP_IN largest sources
      in2  the TOP_IN2 largest sources of each of those
      mid  the TOP_MID largest grantmakers it gave to that themselves fund organizations like yours (funders)
    The organizations like yours at the end of each path come from the grant table."""
    in1 = _top(fl[fl.dst.isin(set(funders))], "dst", TOP_IN).assign(center=lambda d: d.dst, hop="in1")
    src2 = _top(fl[fl.dst.isin(set(in1.src))], "dst", TOP_IN2)
    in2 = in1[["center", "src"]].merge(src2, left_on="src", right_on="dst", suffixes=("_1", "")).drop(columns="src_1")
    in2 = in2.assign(hop="in2")
    mid = _top(fl[fl.src.isin(set(funders)) & fl.dst.isin(set(funders))], "src", TOP_MID).assign(center=lambda d: d.src, hop="mid")
    cols = ["center", "hop", "src", "dst", "dollars", "grants", "related", "back"]
    return pd.concat([in1[cols], in2[cols], mid[cols]], ignore_index=True)


def used(fl, funders):
    """The flows any trace uses. traces() on these gives the same traces as on all flows: each top-n is drawn from a
    set that holds the full top-n, and every other flow in it is real, so none can outrank them."""
    t = traces(fl, funders)
    return fl.merge(t[["src", "dst"]].drop_duplicates(), on=["src", "dst"])
