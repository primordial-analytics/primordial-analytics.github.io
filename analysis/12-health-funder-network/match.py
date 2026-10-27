"""Link each grant's recipient to a registered nonprofit (an EIN in the IRS Business Master File).

Rules first, in order, and the first that gives exactly one organization wins:
  1. the EIN printed on Schedule I, when the Business Master File or a filing knows it;
  2. the same cleaned name in the same ZIP code;
  3. the same cleaned name in the same city and state;
  4. the same cleaned name in the same state.
What is left goes to the model only when it could be a peer organization (peers() below): its name or the grant's
purpose has a care word, and one of the five closest registered names nearby (same state, and same 3-digit ZIP or city)
is a peer whose name scores at least MIN_SCORE out of 100 for likeness. The model sees those five and picks one or says none; a pick outside the five counts as none.
"""
import re

import pandas as pd
from rapidfuzz import fuzz, process

import llm

STOP = {"INC", "INCORPORATED", "CORP", "CORPORATION", "THE", "OF", "LLC", "CO", "LTD", "NFP", "NONPROFIT", "AND"}
# NTEE codes of direct-care and community health organizations (NCCS NTEE list): ambulatory and primary care, clinics,
# reproductive health, health support, public health, general health, patient support, other health, substance use and
# mental health treatment. Hospitals, nursing homes and fundraising arms are left out.
PEER_NTEE = re.compile(r"^(?:E3[0-2]|E4[02]|E60|E70|E80|E86|E99|F2[02]|F3[02])")
# whole words or word starts only: "HIV" must not match YESHIVA, nor "NURSE" NURSERY
CARE_WORDS = re.compile(r"\b(?:CLINIC|HEALTH|MEDIC|DENTAL|WELLNESS|FQHC|PHARMAC|COUNSEL|BEHAVIORAL|RECOVERY|SAMARITAN"
                        r"|PRIMARY CARE|FAMILY PRACTICE|NURSES?\b|NURSING|PATIENT|DOCTOR|PHYSICIAN|HIV\b|MENTAL)")
MIN_SCORE = 70  # a peer candidate this unlike the recipient's name is not worth a question
TOP = 5
SCHEMA = {"type": "object", "properties": {"choice": {"type": "string"},
                                           "confidence": {"type": "string", "enum": ["high", "medium", "low"]}},
          "required": ["choice", "confidence"]}


def norm(s):
    t = re.sub(r"[^A-Z0-9 ]", " ", str(s or "").upper().replace("&", " AND ").replace("'", ""))
    t = re.sub(r"\bST\b", "SAINT", t)
    return " ".join(w for w in t.split() if w not in STOP)


def peers(bmf):
    """Organizations that could be a peer: a PEER_NTEE code, or no NTEE code and a care word in the name.
    The model narrows this down later (classify.py)."""
    return bmf.NTEE_CD.str.contains(PEER_NTEE) | ((bmf.NTEE_CD == "") & bmf.NAME.str.contains(CARE_WORDS))


def prepare(bmf):
    return bmf.assign(n=bmf.NAME.map(norm), zip5=bmf.ZIP.str[:5], cityn=bmf.CITY.map(norm))


def rules(rec, bmf, known_eins):
    """rec: distinct recipients. Returns the EIN ('' when unresolved) and the rule used, per recipient."""
    def unique(cols):
        s = bmf.groupby(cols).EIN.agg(list)
        return s[s.str.len() == 1].str[0].to_dict()
    tables = [("name+zip", unique(["n", "zip5"]), ["n", "zip"]), ("name+city", unique(["n", "cityn", "STATE"]), ["n", "cityn", "state"]),
              ("name+state", unique(["n", "STATE"]), ["n", "state"])]
    ein = rec.ein.where(rec.ein.isin(known_eins), "")
    how = pd.Series("", rec.index).mask(ein != "", "ein")
    for rule, table, cols in tables:
        keys = pd.Series(list(zip(*[rec[c] for c in cols])), rec.index)
        hit = (ein == "") & keys.isin(table.keys())
        ein[hit] = keys[hit].map(table)
        how[hit] = rule
    return ein, how


def candidates(r, near):
    hits = process.extract(r.n, near.n.tolist(), scorer=fuzz.token_set_ratio, limit=TOP)
    return [(near.iloc[i], score) for _, score, i in hits]


INTRO = ("A tax filing lists a grant to the recipient below. Decide which candidate registered nonprofit, if any, is the "
         "same legal organization as the recipient.\n\n")
RULES = ("\n\nMost recipients are not in the list, so answer NONE unless the recipient and one candidate are clearly "
         "the same organization.\n"
         "Same organization: the same name shortened, misspelled, abbreviated or renamed, a 'doing business as' name, or "
         "its name followed by one of its own programs, sites or funds (a grant to 'Asian Health Services - Madison Park' "
         "is a grant to Asian Health Services).\n"
         "Different organizations: a foundation, auxiliary, guild or fund of a hospital is not the hospital, and the "
         "hospital is not its foundation; a parent system, subsidiary, medical group or chapter is not the same; names "
         "that differ in a place or a distinctive word are different (Fairfield is not Litchfield); sharing only a "
         "common word such as health, recovery or foundation is not enough. A government agency, school, university "
         "department or company is not any of these candidates.\n"
         "If two candidates share the name, pick the one whose place fits best.\n"
         "Answer with the candidate's EIN, or NONE.")


def prompt(r, cands):
    """The question for one recipient. Written and tested against the tuning sample (check/match_tune_*): it gets the
    model to say none unless the names clearly agree, while still accepting misspellings, renames and site names."""
    lines = [f"{i + 1}. EIN {c.EIN} | {c.NAME} | {c.STREET}, {c.CITY} {c.STATE} {c.zip5} | NTEE {c.NTEE_CD or 'none'}"
             for i, (c, _) in enumerate(cands)]
    return (INTRO + f"Name: {r['name']}\nAddress: {r.city}, {r.state} {r.zip}\nPurpose of grant: {r.purpose or 'not given'}"
            "\n\nCandidate registered nonprofits:\n" + "\n".join(lines) + RULES)


def link(grants, bmf, known_eins, ask=True):
    """grants: grant rows. Returns one row per distinct recipient (n, city, state, zip, recipient_ein) with the matched
    ein ('' if none), the rule ('ein', 'name+zip', 'name+city', 'name+state', 'model' or ''), whether it passed the
    screen for the model, and the model's prompt id."""
    bmf = prepare(bmf)
    g = grants.assign(n=grants.name.map(norm))
    keycols = ["n", "city", "state", "zip", "recipient_ein"]
    rec = g.drop_duplicates(keycols)[keycols + ["name", "purpose"]].reset_index(drop=True)  # first grant's text
    rec = rec.rename(columns={"recipient_ein": "ein"}).assign(cityn=lambda d: d.city.map(norm))
    rec["m_ein"], rec["how"] = rules(rec, bmf, known_eins)

    peer_eins = set(bmf.EIN[peers(bmf)])
    screen = (rec.m_ein == "") & (rec.n != "") & rec.state.isin(set(bmf.STATE)) & \
        (rec.name.str.upper().str.contains(CARE_WORDS) | rec.purpose.str.upper().str.contains(CARE_WORDS))
    rec["screened"] = screen
    # one question per cleaned name, state and ZIP; its answer goes to every spelling of the city or EIN
    rec["q"] = rec.groupby(["n", "state", "zip"]).ngroup()
    prompts, allowed = {}, {}
    for st, grp in rec[screen].drop_duplicates("q").groupby("state"):
        pool = bmf[bmf.STATE == st]
        for _, r in grp.iterrows():
            near = pool[(pool.zip5.str[:3] == r.zip[:3]) | (pool.cityn == r.cityn)]
            cs = candidates(r, near if len(near) else pool)
            if any(c.EIN in peer_eins and score >= MIN_SCORE for c, score in cs):
                prompts[r.q], allowed[r.q] = prompt(r, cs), {c.EIN for c, _ in cs}
    rec["asked"] = screen & rec.q.isin(list(prompts))
    answers = llm.ask_many("match", prompts, SCHEMA) if ask else {}
    picked = {q: re.sub(r"\D", "", str(a.get("choice", ""))) for q, a in answers.items()}
    picked = {q: e for q, e in picked.items() if e in allowed[q]}
    hit = rec.asked & rec.q.isin(list(picked))
    rec.loc[hit, "m_ein"] = rec.q[hit].map(picked)
    rec.loc[hit, "how"] = "model"
    rec["prompt_key"] = rec.q.map({q: llm.key_of(p) for q, p in prompts.items()}).where(rec.asked)
    return rec.drop(columns=["cityn", "q"]).rename(columns={"ein": "recipient_ein", "m_ein": "ein"})
