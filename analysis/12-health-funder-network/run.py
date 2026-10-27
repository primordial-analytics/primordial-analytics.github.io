"""Entry point: python run.py [--cache]

Downloads the IRS and HRSA files, parses every Form 990, 990-EZ and 990-PF, links grant recipients to registered
nonprofits, labels organizations and grants with the local model (answers replayed from llm_cache/, so a rerun needs
no model unless an input changed), checks the model against the reference samples in check/, runs the backtest and
writes output/ (numbers.json holds every number on the page), the page data in assets/examples/12/ and the downloads.

The first run on new data stops after drawing the reference samples for organizations and grants: label them blind
(check/<task>_labels.csv), then run again. --cache keeps slow intermediate tables in data/raw/_cache for quick
reruns while editing (development only: delete the folder to recompute).
"""
import json
import pickle
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True  # python -I ignores PYTHONDONTWRITEBYTECODE; keep __pycache__ out of the repo
sys.path.insert(0, str(Path(__file__).resolve().parent))  # also works under python -I

import check  # noqa: E402
import classify  # noqa: E402
import fetch  # noqa: E402
import graph  # noqa: E402
import health_centers  # noqa: E402
import llm  # noqa: E402
import match  # noqa: E402
import parse  # noqa: E402
import prepare  # noqa: E402
import results  # noqa: E402
import thumbnail  # noqa: E402
import web_data  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
OUT = HERE / "output"
SITE = HERE.parents[1]
SLUG = "12-health-funder-network"
USE_CACHE = "--cache" in sys.argv
CACHE = RAW / "_cache"
PEER_KINDS = ("free_clinic", "health_center", "care_provider")
SPLITS = [((2020, 2021), (2022, 2023)), ((2020, 2021, 2022), (2023, 2024))]  # backtest: choose on the first
T0 = time.time()


def stage(msg):
    print(f"[{time.time() - T0:6.0f}s] {msg}", flush=True)


def cached(name, fn):
    f = CACHE / f"{name}.pkl"
    if USE_CACHE and f.exists():
        return pickle.loads(f.read_bytes())
    out = fn()
    if USE_CACHE:
        CACHE.mkdir(exist_ok=True)
        f.write_bytes(pickle.dumps(out))
    return out


def load():
    bmf = prepare.bmf()
    f = prepare.returns()
    g = prepare.grants(f)
    g = g[~g.person & ~g.foreign & (g.amount > 0)].reset_index(drop=True)
    related = pd.concat([pd.read_parquet(p) for p in (RAW / "_parsed").glob("*.related.parquet")])
    related = related.merge(f[["object_id", "ein"]], on="object_id")
    pairs = set(zip(related.ein, related.related_ein)) | set(zip(related.related_ein, related.ein))
    return bmf, f, g, pairs


def link(bmf, f, g):
    rec = match.link(g, bmf, set(bmf.EIN) | set(f.ein))
    keys = ["n", "city", "state", "zip", "recipient_ein"]
    g = g.assign(n=g.name.map(match.norm)).merge(rec[keys + ["ein", "how"]], on=keys, how="left")
    return rec, g.drop(columns="n")


def organizations(bmf, g, hc_eins):
    """Every matched recipient that could be a peer, with its own latest mission and revenue, and its kind."""
    eins = sorted((set(bmf.EIN[match.peers(bmf)]) | hc_eins) & set(g.ein.dropna()))
    m = prepare.returns(["ein", "form", "tax_year", "period_end", "object_id", "mission", "revenue"])
    m = m[m.form.isin(["990", "990EZ"])].sort_values("tax_year").drop_duplicates("ein", keep="last").set_index("ein")
    o = bmf.set_index("EIN").loc[eins, ["NAME", "CITY", "STATE", "ZIP", "NTEE_CD"]]
    o["mission"] = m.mission.reindex(o.index).fillna("").str[:600]
    o["revenue"] = m.revenue.reindex(o.index).fillna(0)
    model_kind = classify.orgs(o)
    o["model_kind"] = o.index.map(model_kind)
    o["hrsa"] = o.index.isin(hc_eins)
    o["kind"] = np.where(o.hrsa, "health_center", o.model_kind)
    return o


def edges_of(g, o, pairs):
    peers = o[o.kind.isin(PEER_KINDS)]
    e = g[g.ein.isin(set(peers.index))].rename(columns={"ein": "peer_ein"}).copy()
    e["related"] = [(a, b) in pairs for a, b in zip(e.funder_ein, e.peer_ein)]
    e["peer_state"] = e.peer_ein.map(peers.STATE)
    recent = e.tax_year.isin(results.RECENT)
    kinds = classify.grants(e.purpose[recent & ~e.related])
    e["kind"] = e.purpose.map(classify.purpose_key).map(kinds).fillna("unclear").where(recent & ~e.related, "unclear")
    return e, peers


def ppi_kind_share(sample_labels, model_labels_sample, model_labels_all, kind):
    y = [k == kind for k in sample_labels]
    yhat = [k == kind for k in model_labels_sample]
    yall = [k == kind for k in model_labels_all]
    return check.ppi_share(y, yhat, yall)


def missed(rec):
    """Draw the samples of recipients that neither the rules nor the model resolved, split on care words. Returns the
    size of each stratum."""
    un = rec[(rec.ein == "") & (rec.n != "") & ~rec.asked].drop_duplicates(["n", "state", "zip"])
    care = un.name.str.upper().str.contains(match.CARE_WORDS) | un.purpose.str.upper().str.contains(match.CARE_WORDS)
    sizes = {}
    for task, part in (("missed_care", un[care]), ("missed_other", un[~care])):
        check.draw(task, {f"{r.n}|{r.state}|{r.zip}": f"Recipient: {r.name}\nAddress: {r.city}, {r.state} {r.zip}\n"
                          f"Purpose of grant: {r.purpose or 'not given'}" for r in part.itertuples()})
        sizes[task] = len(part)
    return sizes


def reference_rows(task, answers, key="kind"):
    """The reference sample of one step next to the pipeline's answers, for the reference-labels download."""
    lab = check.labels(task)
    text = {r["id"]: r["text"] for r in check.draw(task, {})}
    return pd.DataFrame({"step": task, "id": lab.index, "item": [text[i].split("\n\nMost recipients")[0] for i in lab.index],
                         "reference": lab[key].values, "pipeline": [answers.get(i, "") for i in lab.index],
                         "note": lab["note"].values if "note" in lab else ""})


def checks(o, e, sizes):
    """Accuracy of each model step against its reference sample, and corrected shares. Stops if labels are missing.
    Returns the numbers and the reference table."""
    out = {}
    cache = llm.load("match")
    lab = check.labels("match")
    got = {i: re.sub(r"\D", "", cache[i]["answer"]["choice"]) or "NONE" for i in lab.index}
    out["match"] = check.match_accuracy(got)
    out["missed"] = check.missed_peers()
    for task, m in out["missed"].items():
        m["stratum"], m["implied"] = sizes[task], [round(s * sizes[task]) for s in (m["share"], *m["share_ci"])]
    # organization kinds: a sample over every organization the model labeled, compared on its three-way call
    rows = check.draw("org", {e_: classify.org_text(r) for e_, r in o.iterrows()})
    grants_recent = e[e.tax_year.isin(results.RECENT) & ~e.related].reset_index(drop=True)
    check.draw("grant", {str(i): f"Purpose: {p}" for i, p in grants_recent.purpose.items()})
    missing = [t for t in ("org", "grant") if not (check.CHECK / f"{t}_labels.csv").exists()]
    if missing:
        sys.exit(f"Label the reference samples first: {', '.join(f'check/{t}_sample.jsonl' for t in missing)}")
    lo = check.labels("org")
    ok = sum(o.model_kind[i] == k for i, k in lo.kind.items())
    out["org"] = {"n": len(lo), "right": ok, "accuracy": ok / len(lo), "accuracy_ci": check.wilson(ok, len(lo))}
    peer_ref = [k != "not_peer" for k in lo.kind]
    peer_mod = [o.model_kind[i] != "not_peer" for i in lo.index]
    out["org"]["peer_share"] = check.ppi_share(peer_ref, peer_mod, list(o.model_kind != "not_peer"))
    out["org"]["free_clinic_share"] = ppi_kind_share(lo.kind, [o.model_kind[i] for i in lo.index], o.model_kind, "free_clinic")
    lg = check.labels("grant")
    mk = [grants_recent.kind[int(i)] for i in lg.index]
    ok = sum(a == b for a, b in zip(mk, lg.kind))
    out["grant"] = {"n": len(lg), "right": ok, "accuracy": ok / len(lg), "accuracy_ci": check.wilson(ok, len(lg))}
    for k in ("general", "program", "capital", "in_kind"):
        out["grant"][f"{k}_share"] = ppi_kind_share(lg.kind, mk, grants_recent.kind, k)
    # links the model made into the final peer set: how many of the sampled ones are right
    peer_eins = set(o.index[o.kind.isin(PEER_KINDS)])
    picks = [(i, got[i]) for i in lab.index if got[i] != "NONE" and got[i] in peer_eins]
    right = sum(p in set(lab.accept[i].split("|")) for i, p in picks)
    out["match"]["peer_picks"], out["match"]["peer_picks_right"] = len(picks), right
    out["match"]["peer_precision_ci"] = check.wilson(right, len(picks))
    ref = pd.concat([reference_rows("match", got, "accept"),
                     *(reference_rows(t, {}, "peer").assign(pipeline="not asked") for t in ("missed_care", "missed_other")),
                     reference_rows("org", o.model_kind.to_dict()),
                     reference_rows("grant", dict(zip(lg.index, mk)))])
    return out, ref


def backtests(e, peers, f_table):
    direct = set(f_table.index[f_table.channel == "direct"])
    d = e[~e.related & e.funder_ein.isin(direct)]
    p = peers.assign(zip3=peers.ZIP.str[:3])
    out = {}
    for train, test in SPLITS:
        s, _, unseen = graph.backtest(d, p, train, test)
        out[f"{train[0]}-{train[-1]} to {test[0]}-{test[-1]}"] = {"unreachable_pct": 100 * unseen, "methods": s.round(4).to_dict("index")}
    return out


def chosen_method(bt):
    """The rule set before the final data: popular_state unless another method beats it on the first split with a
    95% interval entirely above popular_state's, and is at least as good on the second split."""
    a, b = (list(bt.values())[i]["methods"] for i in (0, 1))
    for m in graph.METHODS:
        if m != "popular_state" and a[m]["hit_lo"] > a["popular_state"]["hit_hi"] and b[m]["hit_rate"] >= b["popular_state"]["hit_rate"]:
            return m
    return "popular_state"


def main():
    stage("fetch and parse")
    fetch.fetch_all()
    parse.main()
    stage("prepare")
    bmf, f, g, pairs = cached("load", load)
    stage("link recipients (model answers from llm_cache/match.jsonl)")
    rec, g = cached("link", lambda: link(bmf, f, g))
    stage("health centers (HRSA)")
    hc = health_centers.match_bmf(health_centers.load(RAW / "hrsa_sites.csv"), bmf)
    stage("organization kinds")
    o = cached("orgs", lambda: organizations(bmf, g, set(hc.ein[hc.ein != ""])))
    stage("grant kinds and edges")
    e, peers = edges_of(g, o, pairs)
    latest = f.sort_values("tax_year").drop_duplicates("ein", keep="last")
    stage("results")
    ft = results.funders(e, latest)
    pt = results.peers(e, peers.rename(columns={"NAME": "name", "CITY": "city", "STATE": "state", "ZIP": "zip", "NTEE_CD": "ntee"}))
    stage("checks")
    ch, ref = checks(o, e, missed(rec))
    stage("backtest")
    bt = backtests(e, peers, ft)
    numbers = {"findings": results.findings(e, ft, pt), "checks": ch, "backtest": bt, "ranking_method": chosen_method(bt),
               "data": {"returns": int(len(f)), "grants": int(len(g)), "recipients": int(len(rec)),
                        "recipients_by_rule": rec.how.value_counts().to_dict(), "questions_to_model": int(rec.asked.sum()),
                        "hrsa_orgs": int(len(hc)), "hrsa_matched": int((hc.ein != "").sum()),
                        "orgs_labeled": int(len(o)), "peers": o.kind.value_counts().to_dict(),
                        "model": llm.MODEL}}
    numbers["sources"] = [line.split("\t") for line in (RAW / "SOURCES.txt").read_text().splitlines()]
    OUT.mkdir(exist_ok=True)
    (OUT / "numbers.json").write_text(json.dumps(numbers, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)))
    pt.rename_axis("ein").to_csv(OUT / "peers.csv")
    ft.rename_axis("ein").to_csv(OUT / "funders.csv")
    e[e.tax_year.isin(results.RECENT)][["funder_ein", "peer_ein", "tax_year", "amount", "kind", "related", "purpose"]].to_csv(OUT / "grants.csv", index=False)
    ref.to_csv(OUT / "reference_labels.csv", index=False)
    stage("page data and downloads")
    web_data.build()
    for name, table in (("funders", "funder-table"), ("grants", "grant-table"), ("peers", "organization-table"),
                        ("reference_labels", "reference-labels")):
        shutil.copy(OUT / f"{name}.csv", SITE / "downloads" / f"{SLUG}-{table}.csv")
    shutil.copy(HERE / "codebook.csv", SITE / "downloads" / f"{SLUG}-codebook.csv")
    thumbnail.make(numbers["findings"], SITE / "img" / "case_studies" / "health-funder-thumbnail.webp")
    stage("done")


if __name__ == "__main__":
    main()
