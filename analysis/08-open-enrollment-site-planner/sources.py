"""Policy facts the page quotes, each with its source URL and the date it was checked. Written to output/facts.json.

These are typed in here on purpose (they are not in any downloadable table). Nothing on the page states a policy fact
that is not in this file. Change a date or a list here and re-run; the page reads facts.json through data.json.
"""
import json

from common import OUT

CHECKED = "2026-10-23"

# States that have not adopted the Medicaid expansion (KFF state tracker, fetched 2026-10-23).
NON_EXPANSION = ["AL", "FL", "GA", "KS", "MS", "SC", "TN", "TX", "WI", "WY"]
# Wisconsin covers adults to 100% of poverty under a waiver, so its adults under 100% are placed in the Medicaid range and
# flagged. Georgia's Pathways program is also a waiver, but it has a work requirement and very small enrollment, and KFF lists
# Georgia as a state with a coverage gap: Georgia is treated like the other gap states and its program is a text note only.
WAIVER_STATES = {"WI": "BadgerCare Plus covers adults to 100% of poverty under a waiver"}
STATE_NOTES = {**WAIVER_STATES, "GA": "Georgia Pathways covers some adults to 100% of poverty, with a work requirement; adults under 100% are counted in the coverage gap here"}

# States that run their own marketplace and enrollment site, so HealthCare.gov dates do not apply. CMS "State-based Exchanges" page,
# updated 2026-08-13: the 21 full state-based exchanges for plan year 2026 plus one state it lists as moving to its own platform for 2027.
STATE_MARKETPLACES = ["CA", "CO", "CT", "DC", "GA", "ID", "IL", "KY", "ME", "MD", "MA", "MN", "NV", "NJ", "NM", "NY", "OR", "PA", "RI", "VT", "VA", "WA"]

FACTS = {
    "checked": CHECKED,
    "open_enrollment": {
        "start": "2026-11-01", "deadline_jan1_coverage": "2026-12-15", "end": "2027-01-15",
        "text": "HealthCare.gov: enroll by Dec 15 for Jan 1 coverage; open until Jan 15.",
        "state_text": "runs its own marketplace, with its own dates.",
        "source": "https://content.naic.org/article/what-are-my-health-plan-options-2027", "also": "https://www.healthcare.gov/",
        "checked": CHECKED,
    },
    "state_marketplaces": {
        "states": STATE_MARKETPLACES, "find": "https://www.healthcare.gov/marketplace-in-your-state/",
        "source": "https://www.cms.gov/CCIIO/Resources/Fact-Sheets-and-FAQs/state-marketplaces", "list_updated": "2026-08-13", "checked": CHECKED,
        "note": "These states enroll people on their own sites, with their own deadlines, so the page shows no HealthCare.gov dates for them. The other states use HealthCare.gov.",
    },
    "navigator_funding": {
        "plan_year_2024_million_usd": 98, "per_year_now_million_usd": 10, "release_date": "2025-02-14",
        "source": "https://cms.gov/newsroom/press-releases/cms-announcement-federal-navigator-program-funding", "checked": CHECKED,
    },
    "effectuated_enrollment": {
        "feb_2025_million": 21.8, "feb_2025_million_aspe": 22.1, "feb_2026_million": 19.2,
        "note": "Cited, not recomputed. KFF published 2026-07-28 from CMS monthly effectuated enrollment data (as of 2026-05-05 for 2026).",
        "source": "https://www.kff.org/affordable-care-act/how-has-aca-marketplace-enrollment-changed-across-states-in-2026/", "checked": CHECKED,
    },
    "immigrant_eligibility": {
        "note": "From 2027 certain other lawfully present immigrants lose premium tax credit eligibility. The KFF FAQ does not list the groups, so neither does this analysis. Noncitizen adults are a separate tier labelled 'eligibility varies'.",
        "source": "https://www.kff.org/faqs/faqs-health-insurance-marketplace-and-the-aca/immigrants/can-immigrants-get-help-paying-premiums-and-or-cost-sharing-for-health-insurance-in-the-marketplaces/", "published": "2025-09-29", "checked": CHECKED,
    },
    "medicaid_expansion": {
        "not_adopted": NON_EXPANSION, "waiver_flags": WAIVER_STATES, "adopted_count_with_dc": 51 - len(NON_EXPANSION),
        "source": "https://www.kff.org/affordable-care-act/state-indicator/state-activity-around-expanding-medicaid-under-the-affordable-care-act/",
        "checked": CHECKED,
    },
    "tier_rules": {
        "medicaid_range": "Adults 19 to 64 at or below 138% of poverty in expansion states (bands under 1.00 and 1.00 to 1.37). In Wisconsin, adults under 100% are placed here and flagged.",
        "coverage_gap": "Adults 19 to 64 under 100% of poverty in the other non-expansion states, Georgia included (its Pathways program has a work requirement and small enrollment).",
        "subsidy_range": "Adults 138% to 399% of poverty in expansion states; 100% to 399% in non-expansion states.",
        "d400": "People at 400% of poverty and over, adults and children: full price, no premium credit for adults, and most children are above the Medicaid and CHIP limits.",
        "children": "Under 19 and under 400% of poverty: most are eligible for Medicaid or CHIP; the income limit varies by state. Children at 400% and over are in the 400% tier.",
        "noncitizen": "Noncitizen adults are carved out of every adult tier. The survey cannot tell green card holders from other noncitizens.",
    },
    "federal_law_2027": {
        "work_requirements": "From 2027-01-01, expansion-state Medicaid adults to age 64 must show work or similar activity (80 hours a month) unless exempt; HHS can let a state wait until no later than 2028-12-31 if it shows a good-faith effort. Not modelled here: the tiers use income only.",
        "immigrants": "Federal law limits Medicaid for some lawfully present immigrants from 2026-10-01 and premium tax credits for some from 2027-01-01. The groups are not modelled: noncitizen adults are their own tier, 'eligibility varies'.",
        "source": "https://www.kff.org/medicaid/a-closer-look-at-the-work-requirement-provisions-in-the-2025-federal-budget-reconciliation-law/",
        "also": "https://www.kff.org/medicaid/health-provisions-in-the-2025-federal-budget-reconciliation-law/", "published": "2025-07-30", "checked": CHECKED,
    },
    "not_modelled": ["employer coverage offers", "household income as Medicaid and premium credits define it (the tiers use the survey's income-to-poverty ratio)",
                     "immigration status beyond the noncitizen carve-out", "work requirements and other 2027 federal rules"],
    "prior_art": {"name": "SHADAC Minnesota ZIP-level uninsured profiles for navigators",
                  "source": "https://www.shadac.org/news/minnesota-uninsured-profile-population-duluth-mn-case-study"},
    "kff_immigrant_faq": "https://www.kff.org/faqs/faqs-health-insurance-marketplace-and-the-aca/immigrants/can-immigrants-get-help-paying-premiums-and-or-cost-sharing-for-health-insurance-in-the-marketplaces/",
}


def main():
    (OUT / "facts.json").write_text(json.dumps(FACTS, indent=1))


if __name__ == "__main__":
    main()
