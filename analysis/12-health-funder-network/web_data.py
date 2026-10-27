"""Build the files the example page reads, from output/: assets/examples/12/data.json (national findings, the state list
and the checks), one assets/examples/12/state-XX.json per state, loaded when a state is picked, and state-US.json for
all states together, and assets/examples/12/flow-NN.json: each funder's money trace, filed by the last two digits of
its EIN and loaded when someone follows a funder's money.

State file:
  peers    [ein, name, city, kind, funders in RECENT years, dollars in RECENT years, top funder's share or null,
            3-digit ZIP, state]
  funders  [ein, name, city, state, type, channel, preselected, website, peers anywhere, states, median grant,
            last year, general-support share or null, share of grantees new to it or null]
           every funder with a grant in RECENT years to a peer in the state (related-party grants excluded)
  grants   [funder index, peer index, tax year, amount, kind code, purpose index]
  purposes the distinct purpose texts, cut to 90 characters
The all-states file has the same rows, for every funder that ranks in the top TOP_US under some choice of peer kinds
and funder filters (with ties), and every peer those funders gave to. It adds
  kindN    peers of each kind in all states
  counts   {"fc.hc.cp|daf|pre": funders with a grant to a peer of those kinds}, for every choice, since the file holds
           only the leading funders
  top      TOP_US: the page lists only that many (with ties), the ranks the file holds in full for every choice
Flow file: {"o": {ein: [name, city, state, role, kind]}, "t": {center ein: trace}}. role: "f" a funder (it has its
own trace), "g" another grantmaker, or "p" an organization like yours; kind: the peer kind code, or "" (a funder can be
a peer too). A trace (dollars and grants in RECENT years; flag 1 = related on
Schedule R, 2 = the money also goes the other way):
  in1   [source, dollars, grants, flag]          its largest sources (flows.traces)
  in2   [source, via, dollars, grants, flag]     the largest sources of each of those
  mid   [grantmaker, dollars, grants, flag]      the largest funders it gave to
  peers [peer, dollars, grants, flag]            the TOP_PEERS organizations like yours it gave the most
  midp  [grantmaker, peer, dollars, grants, flag]  the TOP_MID_PEERS each of those funders gave the most
  tot   [received from grantmakers, all grants listed, to peers (unrelated), peers (unrelated), to related peers]
Kind codes: see KINDS. Nothing is modeled here; the page ranks funders itself from these rows.
"""
import itertools
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True  # python -I ignores PYTHONDONTWRITEBYTECODE; keep __pycache__ out of the repo
sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works under python -I
import flows  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
DEST = HERE.parents[1] / "assets" / "examples" / "12"
KINDS = ["general", "program", "capital", "in_kind", "event", "unclear"]
PEER_KINDS = {"free_clinic": "fc", "health_center": "hc", "care_provider": "cp"}  # the page's checkbox order and codes
TOP_US = 100
TOP_PEERS, TOP_MID_PEERS = 12, 4


def clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, float):
        return round(v, 3) if abs(v) < 1 else round(v)
    return v


def network_file(p, funders, grants):
    p = p.sort_values("name")
    g = grants[grants.peer_ein.isin(set(p.index))]
    f = funders.loc[sorted(set(g.funder_ein))]
    pi = {e: i for i, e in enumerate(p.index)}
    fi = {e: i for i, e in enumerate(f.index)}
    purposes = sorted(set(g.purpose.fillna("").str.slice(0, 90)))
    pu = {t: i for i, t in enumerate(purposes)}
    return {
        "peers": [[e, r["name"], r.city, r.kind, int(r.funders), clean(r.dollars), clean(r.top_share),
                   r.zip[:3], r.state]
                  for e, r in p.iterrows()],
        "funders": [[e, r["name"], r.city, r.state, r.type, r.channel, bool(r.preselected), r.website or "",
                     int(r.peers_all_years), int(r.states_all), clean(r.median_grant), int(r.last_year),
                     clean(r.general_share), clean(r.open)] for e, r in f.iterrows()],
        "grants": [[fi[r.funder_ein], pi[r.peer_ein], int(r.tax_year), clean(r.amount), KINDS.index(r.kind),
                    pu[(r.purpose or "")[:90]]] for r in g.itertuples()],
        "purposes": purposes,
    }


def us_file(peers, funders, grants):
    pairs = grants[["funder_ein", "peer_ein"]].drop_duplicates().merge(peers[["kind"]], left_on="peer_ein", right_index=True)
    by_kind = pairs.groupby(["funder_ein", "kind"]).size().unstack(fill_value=0).reindex(columns=list(PEER_KINDS), fill_value=0)
    f = funders.loc[by_kind.index]
    keep, counts = set(), {}
    for r in range(1, len(PEER_KINDS) + 1):
        for ks in itertools.combinations(PEER_KINDS, r):
            n = by_kind[list(ks)].sum(axis=1)
            for daf, pre in itertools.product((0, 1), (0, 1)):
                s = n[(n > 0) & (bool(daf) | (f.channel == "direct")) & ~(bool(pre) & f.preselected.astype(bool))]
                counts[f"{'.'.join(PEER_KINDS[k] for k in ks)}|{daf}|{pre}"] = int(len(s))
                keep |= set(s[s >= s.nlargest(TOP_US).min()].index) if len(s) else set()
    g = grants[grants.funder_ein.isin(keep)]
    d = network_file(peers.loc[sorted(set(g.peer_ein))], funders, g)
    d["kindN"] = peers.kind.value_counts().to_dict()
    d["counts"] = counts
    d["top"] = TOP_US
    return d


def flow_files(peers, grants, out, dest):
    """grants: the grant table with related-party grants, which a trace shows (flagged) and the page counts leave out."""
    fl = pd.read_csv(out / "flows.csv", dtype={"src": str, "dst": str})
    gm = pd.read_csv(out / "grantmakers.csv", dtype={"ein": str}, keep_default_na=False).set_index("ein")
    funders = set(pd.read_csv(out / "funders.csv", dtype={"ein": str}, usecols=["ein"]).ein)
    t = flows.traces(fl, funders)
    t["flag"] = t.related.astype(int) + 2 * t.back.astype(int)
    pp = (grants.groupby(["funder_ein", "peer_ein"]).agg(dollars=("amount", "sum"), grants=("amount", "size"),
                                                          related=("related", "any")).reset_index()
          .sort_values(["dollars", "peer_ein"], ascending=[False, True]))
    pp["flag"] = pp.related.astype(int)
    direct = dict(tuple(pp.groupby("funder_ein", sort=False).head(TOP_PEERS).groupby("funder_ein", sort=False)))
    via = dict(tuple(pp.groupby("funder_ein", sort=False).head(TOP_MID_PEERS).groupby("funder_ein", sort=False)))
    un = pp[~pp.related].groupby("funder_ein").agg(dollars=("dollars", "sum"), n=("peer_ein", "size"))
    rel = pp[pp.related].groupby("funder_ein").dollars.sum()
    hops = {(c, h): d for (c, h), d in t.groupby(["center", "hop"], sort=False)}
    none = t.iloc[:0]
    n = lambda v: int(round(v))
    rows = lambda d, cols: [[n(v) if isinstance(v, float) else int(v) if not isinstance(v, str) else v for v in r]
                            for r in d[cols].itertuples(index=False)]
    shards = {}
    for c in sorted(funders):
        mids = hops.get((c, "mid"), none)
        tr = {"in1": rows(hops.get((c, "in1"), none), ["src", "dollars", "grants", "flag"]),
              "in2": rows(hops.get((c, "in2"), none), ["src", "dst", "dollars", "grants", "flag"]),
              "mid": rows(mids, ["dst", "dollars", "grants", "flag"]),
              "peers": rows(direct.get(c, pp.iloc[:0]), ["peer_ein", "dollars", "grants", "flag"]),
              "midp": [r for m in mids.dst for r in rows(via.get(m, pp.iloc[:0]), ["funder_ein", "peer_ein", "dollars", "grants", "flag"])],
              "tot": [n(gm.received.get(c, 0)), n(gm.given.get(c, 0)), n(un.dollars.get(c, 0)), int(un.n.get(c, 0)), n(rel.get(c, 0))]}
        sh = shards.setdefault(c[-2:], {"o": {}, "t": {}})
        sh["t"][c] = tr
        for e in {c} | {r[0] for k in ("in1", "mid", "peers") for r in tr[k]} | {x for r in tr["in2"] + tr["midp"] for x in r[:2]}:
            if e not in sh["o"]:
                kind = PEER_KINDS[peers.kind[e]] if e in peers.index else ""
                r = peers.loc[e] if kind and e not in gm.index else gm.loc[e]
                sh["o"][e] = [r["name"], r.city, r.state, "f" if e in funders else "p" if kind else "g", kind]
    for k, sh in shards.items():
        (dest / f"flow-{k}.json").write_text(json.dumps(sh, separators=(",", ":")))


def build(out=OUT, dest=DEST):
    peers = pd.read_csv(out / "peers.csv", dtype={"ein": str, "zip": str}).set_index("ein")
    funders = pd.read_csv(out / "funders.csv", dtype={"ein": str}, keep_default_na=False,
                          na_values={"median_grant": [""], "general_share": [""], "open": [""]}).set_index("ein")
    with_related = pd.read_csv(out / "grants.csv", dtype={"funder_ein": str, "peer_ein": str}, keep_default_na=False)
    grants = with_related[~with_related.related]
    numbers = json.loads((out / "numbers.json").read_text())
    dest.mkdir(parents=True, exist_ok=True)
    states = []
    for st in sorted(set(peers.state)):
        d = network_file(peers[peers.state == st], funders, grants)
        (dest / f"state-{st}.json").write_text(json.dumps(d, separators=(",", ":")))
        states.append({"st": st, "peers": len(d["peers"]), "funders": len(d["funders"])})
    flow_files(peers, with_related, out, dest)
    (dest / "state-US.json").write_text(json.dumps(us_file(peers, funders, grants), separators=(",", ":")))
    data = {"_source": "analysis/12-health-funder-network/web_data.py from output/; not edited by hand.",
            "kinds": KINDS, "states": states, "numbers": numbers}
    (dest / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    return data


if __name__ == "__main__":
    build()
