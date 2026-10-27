"""Two labels from the model, both cached in llm_cache/ and both checked against a reference sample (check.py):

kind of organization, for every matched recipient in the peer universe: free or charitable clinic, another nonprofit
    that delivers care itself, or not a peer. The model reads the name, place, NTEE code, revenue and the mission
    statement from the organization's own latest Form 990 or 990-EZ. Whether a care provider is a health center is
    not the model's call: it comes from HRSA's list (health_centers.py).
kind of grant, for every distinct purpose text on a grant to a peer: general support, a program, capital, donated goods, an
    event or sponsorship, or unclear.
"""
import re

import llm

ORG_KINDS = {
    "free_clinic": "a free or charitable clinic: it gives medical, dental, vision, pharmacy or behavioral health care "
                   "itself, free or for a nominal fee, mostly with volunteers, to people who are uninsured or "
                   "underinsured",
    "care_provider": "another nonprofit that itself gives health care or health services directly to people in a "
                     "community: a community health center, community clinic, mobile clinic, dental or vision clinic, "
                     "community mental health center, addiction treatment program, harm reduction service, or a "
                     "community health worker or insurance enrollment program",
    "not_peer": "anything else, including: a hospital or health system and its medical groups; a foundation, "
                "auxiliary or fundraising arm; a pregnancy resource center; a support group, fellowship club or "
                "sober house without treatment; advocacy, awareness, education or research; a disease or "
                "patient-family charity; a professional or trade association; a nursing home, home health or "
                "hospice agency; a government agency; or an organization whose main work is not health",
}
GRANT_KINDS = {
    "general": "unrestricted or general operating support: 'general support', 'operations', 'unrestricted', "
               "'area of greatest need', 'annual fund', 'charitable purposes', 'exempt purpose', or a donation, "
               "contribution or matching gift with no use stated",
    "program": "for a named service, program, project, population or staff position",
    "capital": "for a building, renovation, equipment, a vehicle, furnishings or another capital purchase",
    "in_kind": "donated goods rather than money: medicines, vaccines, medical or dental supplies, food or equipment",
    "event": "an event sponsorship, gala, golf outing, dinner, table or tickets",
    "unclear": "blank, a reference such as 'see Schedule O', a memorial or tribute with no use stated, or only a "
               "field or topic with no use (such as 'health', 'health services', 'medical care', 'human services', "
               "'community health', 'humanitarian')",
}


ORG_BATCH = 5
GRANT_BATCH = 15


def _schema(kinds, n):
    return {"type": "object", "properties": {"kinds": {"type": "array", "minItems": n, "maxItems": n,
                                                       "items": {"type": "string", "enum": list(kinds)}}},
            "required": ["kinds"]}


def _menu(kinds):
    return "\n".join(f"- {k}: {v}" for k, v in kinds.items())


def org_text(o):
    revenue = f"${o.revenue:,.0f}" if o.revenue else "not reported"
    return (f"Name: {o.NAME}\nPlace: {o.CITY}, {o.STATE}\nNTEE code: {o.NTEE_CD or 'none'}\nAnnual revenue: {revenue}\n"
            f"Mission or main activity, from its own tax filing: {o.mission or 'not available'}")


def org_prompt(texts):
    items = "\n\n".join(f"Organization {i + 1}:\n{t}" for i, t in enumerate(texts))
    return (f"Classify each of these {len(texts)} US nonprofit organizations.\n\nKinds:\n{_menu(ORG_KINDS)}\n\n"
            "Judge by each organization's main work. Choose free_clinic or care_provider only when the mission (or, "
            "if there is none, the name) shows that it delivers care itself; otherwise answer not_peer.\n\n" + items +
            f"\n\nAnswer with {len(texts)} kinds, in order.")


def grant_prompt(purposes):
    items = "\n".join(f"{i + 1}. \"{p}\"" for i, p in enumerate(purposes))
    return (f"Each line is the stated purpose of a grant to a health nonprofit.\n\nKinds:\n{_menu(GRANT_KINDS)}\n\n"
            f"Purposes:\n{items}\n\nAnswer with {len(purposes)} kinds, in order.")


def purpose_key(s):
    """Purpose texts that differ only in case, spacing or punctuation get one label."""
    return re.sub(r"[^A-Z0-9]+", " ", str(s).upper()).strip()


def _batched(task, ids, texts, make_prompt, kinds, size):
    """Label texts in fixed batches (sorted by id, so the same inputs give the same prompts). Returns {id: kind}."""
    order = sorted(ids)
    chunks = [order[i:i + size] for i in range(0, len(order), size)]
    prompts = {j: make_prompt([texts[i] for i in c]) for j, c in enumerate(chunks)}
    answers = {}
    for n in {len(c) for c in chunks}:  # one schema per batch length (only the last batch is short)
        part = {j: p for j, p in prompts.items() if len(chunks[j]) == n}
        answers |= llm.ask_many(task, part, _schema(kinds, n))
    return {i: k for j, c in enumerate(chunks) for i, k in zip(c, answers[j]["kinds"])}


def orgs(o):
    """o: one row per organization (index EIN) with NAME, CITY, STATE, NTEE_CD, revenue, mission. Returns {EIN: kind}."""
    return _batched("org_kind", list(o.index), {e: org_text(r) for e, r in o.iterrows()}, org_prompt, ORG_KINDS,
                    ORG_BATCH)


def grants(purposes):
    """purposes: iterable of purpose texts. Returns {purpose_key: kind}."""
    keys = {purpose_key(p) for p in purposes}
    return _batched("grant_kind", list(keys), {k: k for k in keys}, grant_prompt, GRANT_KINDS, GRANT_BATCH)
