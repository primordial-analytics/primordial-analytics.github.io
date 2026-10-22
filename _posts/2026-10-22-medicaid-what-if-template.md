---
layout: post
title: A Medicaid What-If Spreadsheet for Health Centers
description: >-
  A free, editable spreadsheet that helps a health center estimate what happens
  to its revenue if some Medicaid expansion adults lose coverage.
---

## Why now

The Medicaid changes in the 2025 budget law (H.R. 1) have stopped being abstract. In early June, CMS issued its [interim final rule](https://www.cms.gov/newsroom/fact-sheets/medicaid-community-engagement-requirement-certain-individuals-interim-final-rule-comment-period-cms) on work requirements for expansion adults aged 19 to 64. States must start by January 1, 2027, and Nebraska started early. Nebraska began on May 1: KFF's [September 29 look at its early data](https://www.kff.org/medicaid/early-medicaid-work-requirement-insights-from-nebraska/) found 7% of renewing enrollees subject to the rule lost coverage, and 14% of applications subject to the rule were denied. The numbers are early and come from draft state minutes, so treat them as a first glimpse.

Nothing is settled. HHS can approve a state's [good-faith-effort exemption](https://www.federalregister.gov/documents/2026/06/03/2026-11094/medicaid-program-community-engagement-requirement-for-certain-individuals), but CMS says it expects initial approvals of six months or less, with extensions possible until the end of 2028. As of October 22 we found none approved, though five governors, [Oregon's among them](https://www.healthcaredive.com/news/medicaid-work-requirements-governors-ask-hhs-delay-letter/831992/), have asked HHS to delay. A federal judge in Massachusetts declined to pause the rule in late July, and the case continues. Six-month renewals for expansion adults arrive around the same time.

For a health center, the question is concrete: how many of our patients, and how many dollars? In the national data for 2025, [47.5% of health center patients had Medicaid (including CHIP-Medicaid) and 17.2% were uninsured](https://data.hrsa.gov/topics/healthcenters/uds/overview/national/table?tableName=4&year=2025) (HRSA UDS Table 4). HRSA's own headline figure, 47.9%, also counts a separate other-CHIP line; our [worked example]({{ site.baseurl }}/casestudies/07-health-center-medicaid-share/) uses that one. Your center's mix is different, which is why we built something you can change.

## What the template does

It is an Excel workbook with live formulas. You enter how many Medicaid expansion adults you serve, how often they visit, and what Medicaid pays you per visit. It then runs three scenarios, Low, Mid and High, for the share who lose coverage. For each one it shows:

- how many patients lose coverage, and how many keep coming as uninsured patients
- the Medicaid visit revenue you would lose and the sliding-fee revenue you would gain back
- the net change, as dollars and as a share of total revenue
- your uninsured share of patients, before and after

## What it does not do

It is a scenario tool, not a forecast. It covers only expansion adults. It does not model children, the shorter retroactive-coverage window, the expired ACA subsidies, grant funding, or your state's specific rules. We do not know your center's real numbers, so every default is editable, and the one for how many people keep coming after losing coverage has no direct study behind it. The workbook says so, and its Sources & assumptions sheet lists where each default came from, with dates.

## How to fill it in

1. **Patient counts.** UDS Table 4 gives your patients by payer, including uninsured and Medicaid. Table 4 does not split expansion adults from other Medicaid patients, so ask your billing team or check the payer plan or eligibility category in your EHR.
2. **Visits.** Take Table 5 Line 34 (clinic plus virtual visits) and divide by your total patients on Table 4.
3. **Medicaid revenue per visit.** Use your state's Medicaid rate for your center, or your Table 9D Medicaid collections divided by Medicaid visits (Medicaid visit counts come from your billing system; UDS does not report them).
4. **Sliding-fee collections and total revenue.** Table 9D has your self-pay collections, and Tables 9D and 9E together give total revenue. Total revenue is optional.
5. **Scenarios.** Keep ours or type your own.

The yellow cells are the ones to edit. The file opens with example numbers for a hypothetical 10,000-patient center, scaled from national averages. It is not a real center, and it is there only so you can see the workbook work.

## How to read the scenarios

Our defaults put the share of expansion adults losing coverage at about 13.5% (Low), 28% (Mid) and 50% (High), counting work requirements and six-month renewals together. They come from a spread of sources: Nebraska's early data, CMS's own 15% projection, and Urban Institute and CBO estimates. The percentages are our judgment, informed by their published totals, not official rates, and the Mid value is a judgment call.

With the example numbers, the Mid scenario has about 452 of 1,615 expansion adults losing coverage. The workbook then estimates a net loss of roughly $532,000 a year, about 3% of the example center's revenue, with a range from about $256,000 (Low) to $949,000 (High). Those figures belong to the made-up example only. Yours will differ, and the point is to see which input moves the answer most. A small table on the Results sheet shows how the Mid result shifts if fewer or more people keep coming, or if your Medicaid payment per visit is higher or lower.

## Get the spreadsheet

<strong><a href="{{ site.baseurl }}/downloads/medicaid-what-if-template.xlsx">Download the Medicaid what-if template (Excel .xlsx, about 23 KB)</a></strong>

It is free to use, copy and share, and nothing in it is locked. Policy details in it are current as of October 22, 2026, and they may change before January.

## Want a hand?

If you would like a second pair of eyes, we are happy to walk through the template on your own summarized counts, or sanity-check one you have already built. It is free, and de-identified totals are plenty. See [how we help]({{ site.baseurl }}/community-health-data-help/) or [get in touch]({{ site.baseurl }}/#contact). Small questions are welcome.
