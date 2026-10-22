---
layout: post
title: A Data Sanity-Check Checklist Before You Submit UDS and Grant Reports
description: >-
  A plain-language checklist of small data checks that catch big reporting
  errors before you submit a UDS or grant report from spreadsheets.
---

## Why small checks catch big problems

Many errors in reports are not hard statistics. They are tie-out errors: the same number says one thing on page two and another thing on page nine, or a total quietly includes people it shouldn't. Each takes minutes to find if you look on purpose, and far longer to explain after you've submitted.

So this is a checklist for the last stretch before you hit submit. It is written for small health centers and health non-profits who build their reports in spreadsheets. We use the federal Uniform Data System (UDS) as the worked example because its rules are public and specific, then widen out to other funders at the end.

A few honest notes first. We do data science. We are not HRSA reviewers or certified UDS trainers, and this is a data-hygiene list, not compliance advice. When it and the manual disagree, the manual wins. UDS details change every year, so check the current one.

**The basics, per the [2026 UDS Manual](https://bphc.hrsa.gov/sites/default/files/bphc/compliance/2026-uds-manual.pdf):** UDS is a calendar-year report (January 1 to December 31) for health centers funded under section 330, look-alikes, and certain Bureau of Health Workforce-funded centers. It is submitted in HRSA's Electronic Handbooks (EHBs) by February 15 at 11:59 p.m. local time. A HRSA reviewer then works with you until March 31, when final corrections are due. For 2026 data, that means February 15 and March 31, 2027. Not every non-profit reports UDS, but the patterns below apply to any multi-table report.

## Before you pull any data

- Download the current manual and the table templates (PDF and Excel) from HRSA's [Reporting Guidance page](https://bphc.hrsa.gov/data-reporting/uds-training-and-technical-assistance/reporting-guidance).
- Write down the exact date range. UDS uses the calendar year, even if your fiscal or grant year is different.
- Write down which sites and services are in scope, and note any changes during the year. The manual says out-of-scope activity is excluded.
- Put the key definitions on one page: what counts as a visit, a patient, a provider, and how age is calculated (UDS uses age on December 31). Say who owns each definition.
- Save every source extract, with the pull date, so you can reproduce your numbers later.
{: .checklist role="list"}

## Count people once, and count the right people

- One row per person. Look for duplicates across sites, systems, and name or date-of-birth variants, especially if you changed record systems mid-year.
- A patient needs at least one countable visit. Per the 2026 manual, people who only received lab, imaging, pharmacy, transportation, or outreach services, and WIC-only clients, are not patients.
- Check dates: visit dates fall inside the year, no birth dates in the future, ages computed as of December 31.
- Count your blanks and unknowns. Do not drop them silently or spread them across other categories. In the 2026 manual, Table 3A has no "unknown" age category, Table 4 has an unknown line for income but not for insurance, and patients with unknown ZIP codes go under "Unknown Residence."
{: .checklist role="list"}

## Make the patient tables tie out

This is the clearest place the manual states hard equality rules (Appendix B of the 2026 manual). The patient total should be the same in the ZIP code table, Table 3A, Table 3B, and Table 4 (both the income and insurance sections).

- ZIP code total = Table 3A total = Table 3B total = Table 4 totals.
- Insurance groups line up between the ZIP code table and Table 4 (for example, uninsured in one equals uninsured in the other).
- Table 3A patients under 18 and 18 and over match the two age columns in Table 4.
- If you file Grant Reports as well as the Universal Report, no cell in a Grant Report is larger than the same cell in the Universal Report.
{: .checklist role="list"}

A good habit: add a "tie-out" tab where each rule above is a formula showing TRUE or FALSE. If any cell says FALSE, find out why before doing anything else.

## Visits, staffing, and clinical measures

- Compute visits per patient for each service category, and explain outliers. The manual's own example of a problem is extremely high visits per patient with no context.
- Compare staff FTEs on Table 5 with costs on Table 8A. The manual says volunteer FTEs with no cost, or paid referrals with no FTEs, should be explained.
- On Tables 6B and 7, confirm the denominator uses the right measure version and age window for the year. The manual describes several measure changes for 2026.
- Records reviewed (column B) must be at least 80% of the denominator (column A), and you can't shrink it by excluding patients on a variable related to the measure.
- Table 7 race and ethnicity counts can't exceed the Table 3B counts in the same category.
{: .checklist role="list"}

## Money

- Tables 8A, 9D, and 9E should closely tie to your financial statements and audit, and you should be able to explain any gap (fiscal year, out-of-scope activity). The 2026 manual moves 9D and 9E to GAAP accrual.
- Revenue appears on 9D or 9E, never both.
- Divide Medicaid collections on 9D by Medicaid patients on Table 4. The manual suggests this as a sense-check. The two tables don't match exactly, but the average should look sensible and similar to last year.
{: .checklist role="list"}

## Compare with last year and explain

- Build a small table with last year, this year, and percent change for every key total: patients, visits, FTEs, revenue, costs, and each clinical rate.
- Pick a personal tripwire (10 to 15 percent is a reasonable place to start, but that is a rule of thumb, not an HRSA rule) and write one plain sentence for anything that moves more.
- Keep those sentences. EHBs generates audit questions, and the manual says you must address each one, with a table comment if the data is correct as reported.
{: .checklist role="list"}

## Before you click submit

- A second person recomputes three key totals from the raw extract, without looking at your formulas.
- Every audit question is answered, in plain language.
- Inputs, queries or scripts, the final report, and comments are in one backup folder. The manual says to keep backups for at least three years.
- You left time. Don't plan to finish on February 15.
{: .checklist role="list"}

## Reporting to other funders

Most of the above transfers. Read the award terms for the funder's definitions, reporting period, and template, and match the funder's definitions rather than your internal ones. Federal awards generally fall under 2 CFR 200: [performance reports](https://www.ecfr.gov/current/title-2/subtitle-A/chapter-II/part-200/subpart-D/subject-group-ECFR4424206eaecd4a1/section-200.329) compare results to the award's objectives and explain misses, and [records are kept](https://www.ecfr.gov/current/title-2/section-200.334) for three years from the date of the final (or, for annually renewed awards, the annual) financial report. State and foundation reports add their own rules. Keep a "definitions and decisions" log so next year's person gets the same numbers you did.

## When to ask for help

For UDS questions about definitions or measures, the best source is HRSA's UDS Support Center (866-UDS-HELP, <udshelp330@bphcdata.net>). For the spreadsheet side, such as a tie-out tab that won't balance, a messy duplicate list, or a year-over-year table, we're happy to help for free. See [free data help for community health organizations](/community-health-data-help/), or [get in touch](/#contact).

If you're also trying to think through coverage changes, there's a [Medicaid what-if spreadsheet template](/blog/medicaid-what-if-template/) you can download and adapt.
