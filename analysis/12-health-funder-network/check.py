"""Reference samples for the model's work, and what they say about its accuracy.

Samples are drawn at random (fixed seed) from the full set of questions before any answer is read, and labeled blind:
the labeler sees what the model sees, never the model's answer. The labels were written by Claude (Anthropic), a larger
model than the one in the pipeline, reading each record in full; check/<task>_labels.csv holds them with a short note
for each. The samples are:

  match_tune  300 matching questions used to write the matching prompt (three versions were tried on it); not used for
              any reported accuracy
  match    300 further matching questions, drawn after the prompt was fixed: the reported accuracy
  missed_care   200 unresolved recipients with a care word that the model was not asked about (no peer candidate)
  missed_other  300 unresolved recipients without a care word
                (could any be a peer the pipeline missed? Each stratum is sampled at random; estimates weight by size.)
  org_tune, grant_tune  100 organizations and 150 grants from the rule-matched data, used to write the batched
              classification prompts; not used for any reported accuracy
  org      300 organizations given a kind
  grant    300 grants to peers given a kind (sampled by grant, so shares of grants need no reweighting)
"""
import json
from pathlib import Path

import numpy as np

CHECK = Path(__file__).parent / "check"
SEEDS = {"org_tune": 14, "grant_tune": 14, "match_tune": 12, "missed_care": 12, "missed_other": 12, "match": 13, "org": 13, "grant": 13}
SIZES = {"org_tune": 100, "grant_tune": 150, "match_tune": 300, "match": 300, "missed_care": 200, "missed_other": 300, "org": 300, "grant": 300}


def draw(task, items):
    """items: {id: text shown to the labeler}. Writes check/<task>_sample.jsonl once; a later call keeps the sample."""
    CHECK.mkdir(exist_ok=True)
    f = CHECK / f"{task}_sample.jsonl"
    if f.exists():
        return [json.loads(x) for x in f.read_text().splitlines()]
    ids = sorted(items)
    rng = np.random.default_rng(SEEDS[task])
    pick = rng.choice(len(ids), size=min(SIZES[task], len(ids)), replace=False)
    rows = [{"id": str(ids[i]), "text": items[ids[i]]} for i in sorted(pick)]
    f.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def labels(task):
    import pandas as pd
    return pd.read_csv(CHECK / f"{task}_labels.csv", dtype=str, keep_default_na=False).set_index("id")


def wilson(k, n, z=1.96):
    """95% Wilson interval for k successes in n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def match_accuracy(answers, task="match"):
    """answers: {sample id: the model's choice (EIN or 'NONE')}. A choice is right when it is among the accepted
    answers (several when one name is registered more than once). Precision: of the model's picks, how many are right.
    Recall: of the questions with a right organization among the candidates, how often the model picked one."""
    lab = labels(task)
    rows = []
    for i, acc in lab.accept.items():
        ok = set(acc.split("|"))
        a = answers[i]
        rows.append((a != "NONE", a in ok))
    pick = [r for r in rows if r[0]]
    n_ok = sum(r[1] for r in rows)
    out = {"n": len(rows), "right": n_ok, "accuracy": n_ok / len(rows), "accuracy_ci": wilson(n_ok, len(rows)),
           "picks": len(pick), "picks_right": sum(r[1] for r in pick)}
    out["precision"] = out["picks_right"] / max(len(pick), 1)
    out["precision_ci"] = wilson(out["picks_right"], len(pick))
    must = [r for i, r in zip(lab.index, rows) if "NONE" not in lab.accept[i].split("|")]
    out["findable"] = len(must)
    out["found"] = sum(r[0] and r[1] for r in must)
    out["recall"] = out["found"] / max(len(must), 1)
    out["recall_ci"] = wilson(out["found"], len(must))
    return out


def missed_peers():
    """Share of recipients never sent to the model that are peers, by stratum, with 95% intervals, and the implied
    number of recipient entries. Stratum sizes come from the sample files' headers (written by run.py)."""
    out = {}
    for task in ("missed_care", "missed_other"):
        lab = labels(task)
        k = int((lab.peer == "yes").sum())
        out[task] = {"n": len(lab), "peers": k, "share": k / len(lab), "share_ci": wilson(k, len(lab))}
    return out


def ppi_share(y, yhat, yhat_all, alpha=0.05):
    """Prediction-powered estimate of a share: model labels on everything, corrected by the reference sample."""
    from ppi_py import ppi_mean_ci, ppi_mean_pointestimate
    y, yhat, yhat_all = (np.asarray(v, float) for v in (y, yhat, yhat_all))
    lo, hi = ppi_mean_ci(y, yhat, yhat_all, alpha=alpha)
    return float(ppi_mean_pointestimate(y, yhat, yhat_all)[0]), (float(lo[0]), float(hi[0]))
