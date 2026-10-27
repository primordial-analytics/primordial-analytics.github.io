"""Funder and peer profiles and the national findings, from the grant edges.

edges: one row per grant to a peer, with funder_ein, peer_ein, tax_year, amount, purpose, grant kind and `related`
(the two organizations list each other on Schedule R). Related grants are kept in the downloads but left out of every
count of funders, since money moving inside a health system is not a grant another organization could seek.
"""
import numpy as np
import pandas as pd

RECENT = (2022, 2023, 2024, 2025)  # the years the tool shows; 2025 returns are still arriving
NEW_YEARS = (2023, 2024)  # years complete enough to ask "was this grantee new to the funder?"
LOOKBACK = 3


def funder_type(r):
    if r.form == "990PF":
        return "private"
    if r.hospital:
        return "hospital"
    if r.daf:
        return "daf"
    return "charity"


def channel(f):
    """How money reaches the peer. 'national_daf': a donor-advised fund sponsor giving in 10+ states (donors choose the
    grantees); 'matching': median grant under $1,000 in 10+ states (employee or customer matching gifts); 'direct':
    everything else, the funders an organization can approach."""
    wide = f.states_all >= 10
    out = pd.Series("direct", f.index)
    out[wide & (f.type == "daf")] = "national_daf"
    out[wide & (f.type != "daf") & (f.median_grant_all < 1000)] = "matching"
    return out


def openness(e):
    """Per funder: share of the peers it funded in NEW_YEARS that it had not funded in the LOOKBACK years before."""
    rows = []
    for y in NEW_YEARS:
        now = e[e.tax_year == y][["funder_ein", "peer_ein"]].drop_duplicates()
        before = set(map(tuple, e[e.tax_year.between(y - LOOKBACK, y - 1)][["funder_ein", "peer_ein"]].values))
        now["new"] = [t not in before for t in map(tuple, now.values)]
        rows.append(now)
    d = pd.concat(rows)
    g = d.groupby("funder_ein").new.agg(["mean", "size"])
    return g["mean"].where(g["size"] >= 3)  # too few grantees to say


def funders(e, latest):
    """latest: each funder's latest return (name, city, state, form, daf, hospital, preselected, website, grants_paid)."""
    u = e[~e.related]
    rec = u[u.tax_year.isin(RECENT)]
    g = rec.groupby("funder_ein")
    out = pd.DataFrame({
        "peers": g.peer_ein.nunique(),
        "grants": g.size(),
        "dollars": g.amount.sum(),
        "median_grant": g.amount.median(),
        "last_year": g.tax_year.max(),
        "states": g.peer_state.nunique(),
        "general_share": g.kind.apply(lambda k: (k == "general").sum() / max((k != "unclear").sum(), 1)),
        "peers_all_years": u.groupby("funder_ein").peer_ein.nunique(),
        "states_all": u.groupby("funder_ein").peer_state.nunique(),
        "median_grant_all": u.groupby("funder_ein").amount.median(),
    }).dropna(subset=["peers"])
    out["open"] = openness(u)
    info = latest.set_index("ein").reindex(out.index)
    out["type"] = info.apply(funder_type, axis=1)
    for c in ("name", "city", "state", "preselected", "website", "grants_paid"):
        out[c] = info[c]
    out["channel"] = channel(out)
    return out


def peers(e, p):
    """p: peer table (name, city, state, kind, revenue). Adds funder counts and how concentrated the funding is."""
    u = e[~e.related & e.tax_year.isin(RECENT)]
    by = u.groupby(["peer_ein", "funder_ein"]).amount.sum()
    tot = by.groupby(level=0).sum()
    out = p.copy()
    out["funders"] = by.groupby(level=0).size().reindex(out.index).fillna(0).astype(int)
    out["dollars"] = tot.reindex(out.index).fillna(0)
    out["top_share"] = (by.groupby(level=0).max() / tot).reindex(out.index)
    return out


def findings(e, f, p):
    u = e[~e.related & e.tax_year.isin(RECENT)]
    priv = f[f.type == "private"]
    by_type = u.merge(f[["type"]], left_on="funder_ein", right_index=True).groupby("type").amount.sum()
    deg = f.peers
    return {
        "grants": int(len(u)), "dollars": float(u.amount.sum()), "funders": int(len(f)), "peers_funded": int(u.peer_ein.nunique()),
        "funders_one_peer_pct": float((deg == 1).mean() * 100),
        "peers_per_funder": pd.cut(deg, [0, 1, 2, 5, np.inf], labels=["1", "2", "3-5", "6+"]).value_counts(sort=False)
                                .astype(int).to_dict(),
        "grant_kinds_pct": (u.kind.value_counts(normalize=True) * 100).to_dict(),
        "top_funders_half_dollars": int(np.searchsorted(np.cumsum(np.sort(f.dollars.values)[::-1]) / f.dollars.sum(), 0.5) + 1),
        "dollars_by_type": {k: float(v) for k, v in by_type.items()},
        "private_preselected_pct": float(priv.preselected.mean() * 100),
        "related_dollars_pct": float(e[e.related & e.tax_year.isin(RECENT)].amount.sum()
                                     / e[e.tax_year.isin(RECENT)].amount.sum() * 100),
        "median_open_pct": float(f.open.median() * 100),
        "peers_one_funder_pct": float((p[p.funders > 0].funders == 1).mean() * 100),
    }
