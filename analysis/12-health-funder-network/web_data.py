"""Build the files the example page reads, from output/: assets/examples/12/data.json (national findings, the state list
and the checks) and one assets/examples/12/state-XX.json per state, loaded when a state is picked.

State file:
  peers    [ein, name, city, kind, funders in RECENT years, dollars in RECENT years, top funder's share or null,
            3-digit ZIP]
  funders  [ein, name, city, state, type, channel, preselected, website, peers anywhere, states, median grant,
            last year, general-support share or null, share of grantees new to it or null]
           every funder with a grant in RECENT years to a peer in the state (related-party grants excluded)
  grants   [funder index, peer index, tax year, amount, kind code, purpose index]
  purposes the distinct purpose texts, cut to 90 characters
Kind codes: see KINDS. Nothing is modeled here; the page ranks funders itself from these rows.
"""
import json
import math
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
DEST = HERE.parents[1] / "assets" / "examples" / "12"
KINDS = ["general", "program", "capital", "in_kind", "event", "unclear"]


def clean(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, float):
        return round(v, 3) if abs(v) < 1 else round(v)
    return v


def state_file(st, peers, funders, grants):
    p = peers[peers.state == st].sort_values("name")
    g = grants[grants.peer_ein.isin(set(p.index))]
    f = funders.loc[sorted(set(g.funder_ein))]
    pi = {e: i for i, e in enumerate(p.index)}
    fi = {e: i for i, e in enumerate(f.index)}
    purposes = sorted(set(g.purpose.fillna("").str.slice(0, 90)))
    pu = {t: i for i, t in enumerate(purposes)}
    return {
        "peers": [[e, r["name"], r.city, r.kind, int(r.funders), clean(r.dollars), clean(r.top_share),
                   r.zip[:3]]
                  for e, r in p.iterrows()],
        "funders": [[e, r["name"], r.city, r.state, r.type, r.channel, bool(r.preselected), r.website or "",
                     int(r.peers_all_years), int(r.states_all), clean(r.median_grant), int(r.last_year),
                     clean(r.general_share), clean(r.open)] for e, r in f.iterrows()],
        "grants": [[fi[r.funder_ein], pi[r.peer_ein], int(r.tax_year), clean(r.amount), KINDS.index(r.kind),
                    pu[(r.purpose or "")[:90]]] for r in g.itertuples()],
        "purposes": purposes,
    }


def build(out=OUT, dest=DEST):
    peers = pd.read_csv(out / "peers.csv", dtype={"ein": str, "zip": str}).set_index("ein")
    funders = pd.read_csv(out / "funders.csv", dtype={"ein": str}, keep_default_na=False,
                          na_values={"median_grant": [""], "general_share": [""], "open": [""]}).set_index("ein")
    grants = pd.read_csv(out / "grants.csv", dtype={"funder_ein": str, "peer_ein": str}, keep_default_na=False)
    grants = grants[~grants.related]
    numbers = json.loads((out / "numbers.json").read_text())
    dest.mkdir(parents=True, exist_ok=True)
    states = []
    for st in sorted(set(peers.state)):
        d = state_file(st, peers, funders, grants)
        (dest / f"state-{st}.json").write_text(json.dumps(d, separators=(",", ":")))
        states.append({"st": st, "peers": len(d["peers"]), "funders": len(d["funders"])})
    data = {"_source": "analysis/12-health-funder-network/web_data.py from output/; not edited by hand.",
            "kinds": KINDS, "states": states, "numbers": numbers}
    (dest / "data.json").write_text(json.dumps(data, separators=(",", ":")))
    return data


if __name__ == "__main__":
    build()
