---
title: Medicaid Coverage Loss and Health Center Revenue
subtitle: Who could lose coverage in 2027, and what it costs
description: "Public data only. No patient information."
lead: "Public data only. No patient information."
layout: default
modal-id: 9
date: 2026-10-22
thumbnail: stress-thumbnail.webp
kind: example
persona: "For health center CEOs and CFOs"
need: "A range for my own state and center type of how many expansion adult patients could lose Medicaid in 2027, how much is administrative versus non-compliance, the revenue effect, and which assumptions matter most."
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

[fr]: https://www.federalregister.gov/documents/2026/06/03/2026-11094/medicaid-program-community-engagement-requirement-for-certain-individuals
[pums]: https://www.census.gov/programs-surveys/acs/microdata.html
[renewals]: https://data.medicaid.gov/dataset/e6205a51-e6d7-4849-9882-4483b8a28c41
[hrsa-download]: https://data.hrsa.gov/data/download
[hrsa-9d]: https://data.hrsa.gov/topics/healthcenters/uds/overview/national/table?tableName=9D&year=2025
[kff]: https://www.kff.org/medicaid/early-medicaid-work-requirement-insights-from-nebraska/
[whatif]: {{ site.baseurl }}/blog/medicaid-what-if-template/

## Who this is for

A CEO or CFO at an independent or rural health center in a Medicaid expansion state. The board wants a 2027 plan and has only a national headline. The decisions: how big an eligibility or navigator team to fund, how much reserve to hold, and what to tell lenders. This is an example on public data, not a client engagement.

## Question

With CMS's own 2027 work-requirement parameters as the central case, how far do states differ in the share of expansion adults who lose Medicaid, how much of that is administrative rather than non-compliance, what does it do to health center revenue, and which assumptions matter most?

## Data

All downloaded 2026-10-22.

- **CMS interim final rule**, Federal Register 2026-11094 ([text][fr]). Tables 37 to 41 are images online, so we read them from the PDF.
- **ACS 2024 PUMS** ([Census][pums]) for the 40 expansion states and DC. "State" below includes DC.
- **CMS Updated Renewal Outcomes** ([medicaid.gov][renewals]), by state and month, March 2023 to March 2024.
- **HRSA UDS 2025** ([Data Downloads][hrsa-download]): payers (Table 4) for 1,356 centers, collections (Table 9D) for 661 of them.

## Method

**Reproduce CMS.** CMS applies 12% non-compliance to the 74% of adult-group enrollees who are not excluded or excepted (8.9% of all), then 7% net procedural loss to everyone left (6.4%): 15.3% together. On 20 million adults that is 3.05 million a year, or 2.29 million in fiscal 2027 (three quarters of a year), matching CMS's Table 41. We treat it as an assumption set, not an observation.

**Let states differ.** Each state draws one of CMS's four Table 39 scenarios (weights 50/10/20/20). CMS's exclusion rates are scaled by how a state's Medicaid adults differ from the pooled states in Census survey data: disability, caregiving, American Indian or Alaska Native status, recent birth. The survey cannot identify the adult group, so only each state's ratio to the pooled states is used, pulled toward 1 where the sample is thin.

**Use the unwinding for spread only.** In the 2023-24 renewal data, a state's paperwork loss is the share of people asked for paperwork who were dropped for procedural reasons, and its data matching is the share renewed without asking. State-months with under 1,000 people in the denominator, or a zero count among more, are dropped. A state keeps 75% of its data-matching position and 61% of its paperwork position from the first half of the window to the second, so we carry that share forward and add fresh noise. The unwinding's own level is never used.

**Simulate and price.** 20,000 draws per state. Administrative loss is people who comply or are exempt and are dropped anyway; that split is a model construct, not an observed category. Revenue starts from UDS Medicaid patients 18 and older times an expansion share no public source gives (we use 60%). Each lost adult costs the state's Medicaid payment per patient, less sliding-fee collections from the 70% who keep coming at 70% of their old visit rate. Centers without Table 9D are priced at their state's payment per patient. Check: $1,986 per Medicaid patient at the 661 reporting centers, 5% below the $2,097 we derived from [HRSA's national figures][hrsa-9d]. Sobol indices give the share of the spread in the answer that each assumption explains.

## What it shows

CMS's central case is 15.3%. Our national median is **15.9%** (11.7% to 21.6%), and 41% of draws fall below CMS. It sits 0.7 points above CMS because state noise does not preserve the mean. CMS supplied the levels, so this is a consistency check.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/stress-coverage-loss-states.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/stress-coverage-loss-states.webp" width="1200" height="1160" loading="lazy" alt="Horizontal stacked bar chart of the 40 Medicaid expansion states and DC ranked by the median share of expansion adults who could lose Medicaid in a year. Utah is highest at 21 percent and Kentucky lowest at 10 percent; the middle state is 15 percent. Each bar splits into non-compliance and administrative loss, and a line shows the 5th to 95th percentile of the total, which runs from about 6 percent to about 35 percent. A dashed line marks CMS's central estimate of 15 percent. The bold label at the end of each line is the median total."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Share of expansion adults who could lose Medicaid in a year, by state. Bars show medians of each part, so a bar can end short of the median total printed at the right; lines show the 5th to 95th percentile of the total. Tap the chart for full size. Model output, not a forecast.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Share of expansion adults who could lose Medicaid in a year, by state, highest to lowest median</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Median</th><th scope="col" class="text-end">5th percentile</th><th scope="col" class="text-end">95th percentile</th><th scope="col" class="text-end">Non-compliance (median)</th><th scope="col" class="text-end">Administrative (median)</th></tr></thead>
<tbody>
<tr><th scope="row">Utah</th><td class="text-end">21.4%</td><td class="text-end">10.3%</td><td class="text-end">34.7%</td><td class="text-end">8.2%</td><td class="text-end">12.4%</td></tr>
<tr><th scope="row">Nevada</th><td class="text-end">18.3%</td><td class="text-end">9.4%</td><td class="text-end">34.1%</td><td class="text-end">9.0%</td><td class="text-end">8.5%</td></tr>
<tr><th scope="row">Rhode Island</th><td class="text-end">18.1%</td><td class="text-end">9.4%</td><td class="text-end">33.9%</td><td class="text-end">9.1%</td><td class="text-end">8.1%</td></tr>
<tr><th scope="row">New Jersey</th><td class="text-end">17.9%</td><td class="text-end">9.6%</td><td class="text-end">33.9%</td><td class="text-end">9.4%</td><td class="text-end">7.7%</td></tr>
<tr><th scope="row">Oklahoma</th><td class="text-end">17.8%</td><td class="text-end">8.8%</td><td class="text-end">33.2%</td><td class="text-end">7.9%</td><td class="text-end">9.2%</td></tr>
<tr><th scope="row">Idaho</th><td class="text-end">17.4%</td><td class="text-end">8.8%</td><td class="text-end">33.1%</td><td class="text-end">7.7%</td><td class="text-end">9.0%</td></tr>
<tr><th scope="row">Montana</th><td class="text-end">17.4%</td><td class="text-end">8.6%</td><td class="text-end">33.1%</td><td class="text-end">7.8%</td><td class="text-end">8.9%</td></tr>
<tr><th scope="row">North Carolina</th><td class="text-end">17.3%</td><td class="text-end">8.7%</td><td class="text-end">32.5%</td><td class="text-end">8.0%</td><td class="text-end">8.6%</td></tr>
<tr><th scope="row">Colorado</th><td class="text-end">17.0%</td><td class="text-end">9.0%</td><td class="text-end">33.3%</td><td class="text-end">9.1%</td><td class="text-end">7.2%</td></tr>
<tr><th scope="row">Louisiana</th><td class="text-end">16.9%</td><td class="text-end">9.0%</td><td class="text-end">33.4%</td><td class="text-end">9.2%</td><td class="text-end">7.0%</td></tr>
<tr><th scope="row">Michigan</th><td class="text-end">16.8%</td><td class="text-end">8.9%</td><td class="text-end">33.2%</td><td class="text-end">8.9%</td><td class="text-end">7.1%</td></tr>
<tr><th scope="row">Massachusetts</th><td class="text-end">16.8%</td><td class="text-end">9.0%</td><td class="text-end">33.3%</td><td class="text-end">9.0%</td><td class="text-end">7.0%</td></tr>
<tr><th scope="row">West Virginia</th><td class="text-end">16.4%</td><td class="text-end">8.5%</td><td class="text-end">32.4%</td><td class="text-end">8.3%</td><td class="text-end">7.3%</td></tr>
<tr><th scope="row">District of Columbia</th><td class="text-end">16.2%</td><td class="text-end">8.6%</td><td class="text-end">32.4%</td><td class="text-end">9.0%</td><td class="text-end">6.3%</td></tr>
<tr><th scope="row">North Dakota</th><td class="text-end">16.1%</td><td class="text-end">8.1%</td><td class="text-end">32.3%</td><td class="text-end">8.0%</td><td class="text-end">7.3%</td></tr>
<tr><th scope="row">Washington</th><td class="text-end">16.1%</td><td class="text-end">8.6%</td><td class="text-end">32.3%</td><td class="text-end">8.8%</td><td class="text-end">6.5%</td></tr>
<tr><th scope="row">Arkansas</th><td class="text-end">15.7%</td><td class="text-end">8.6%</td><td class="text-end">31.7%</td><td class="text-end">9.4%</td><td class="text-end">5.5%</td></tr>
<tr><th scope="row">Indiana</th><td class="text-end">15.4%</td><td class="text-end">8.3%</td><td class="text-end">31.6%</td><td class="text-end">8.9%</td><td class="text-end">5.8%</td></tr>
<tr><th scope="row">Minnesota</th><td class="text-end">15.4%</td><td class="text-end">8.1%</td><td class="text-end">31.8%</td><td class="text-end">7.9%</td><td class="text-end">6.8%</td></tr>
<tr><th scope="row">Missouri</th><td class="text-end">15.3%</td><td class="text-end">8.1%</td><td class="text-end">31.7%</td><td class="text-end">8.2%</td><td class="text-end">6.4%</td></tr>
<tr><th scope="row">Maryland</th><td class="text-end">15.2%</td><td class="text-end">8.1%</td><td class="text-end">31.5%</td><td class="text-end">8.2%</td><td class="text-end">6.2%</td></tr>
<tr><th scope="row">Illinois</th><td class="text-end">15.1%</td><td class="text-end">8.3%</td><td class="text-end">31.0%</td><td class="text-end">9.0%</td><td class="text-end">5.3%</td></tr>
<tr><th scope="row">New Hampshire</th><td class="text-end">14.5%</td><td class="text-end">7.7%</td><td class="text-end">30.7%</td><td class="text-end">8.3%</td><td class="text-end">5.4%</td></tr>
<tr><th scope="row">New York</th><td class="text-end">14.2%</td><td class="text-end">8.1%</td><td class="text-end">28.0%</td><td class="text-end">9.7%</td><td class="text-end">3.7%</td></tr>
<tr><th scope="row">Pennsylvania</th><td class="text-end">14.1%</td><td class="text-end">7.9%</td><td class="text-end">29.1%</td><td class="text-end">8.7%</td><td class="text-end">4.7%</td></tr>
<tr><th scope="row">Connecticut</th><td class="text-end">14.0%</td><td class="text-end">7.8%</td><td class="text-end">27.7%</td><td class="text-end">9.3%</td><td class="text-end">4.0%</td></tr>
<tr><th scope="row">Vermont</th><td class="text-end">14.0%</td><td class="text-end">7.6%</td><td class="text-end">29.4%</td><td class="text-end">8.5%</td><td class="text-end">4.8%</td></tr>
<tr><th scope="row">Hawaii</th><td class="text-end">13.9%</td><td class="text-end">7.9%</td><td class="text-end">27.0%</td><td class="text-end">9.7%</td><td class="text-end">3.5%</td></tr>
<tr><th scope="row">California</th><td class="text-end">13.9%</td><td class="text-end">7.7%</td><td class="text-end">28.2%</td><td class="text-end">8.7%</td><td class="text-end">4.4%</td></tr>
<tr><th scope="row">Ohio</th><td class="text-end">13.8%</td><td class="text-end">7.7%</td><td class="text-end">28.9%</td><td class="text-end">8.6%</td><td class="text-end">4.5%</td></tr>
<tr><th scope="row">Delaware</th><td class="text-end">13.5%</td><td class="text-end">7.5%</td><td class="text-end">27.7%</td><td class="text-end">8.7%</td><td class="text-end">4.1%</td></tr>
<tr><th scope="row">Arizona</th><td class="text-end">13.5%</td><td class="text-end">7.4%</td><td class="text-end">27.4%</td><td class="text-end">8.5%</td><td class="text-end">4.3%</td></tr>
<tr><th scope="row">Iowa</th><td class="text-end">13.3%</td><td class="text-end">7.1%</td><td class="text-end">28.7%</td><td class="text-end">7.6%</td><td class="text-end">5.0%</td></tr>
<tr><th scope="row">New Mexico</th><td class="text-end">12.8%</td><td class="text-end">6.7%</td><td class="text-end">28.2%</td><td class="text-end">7.2%</td><td class="text-end">5.0%</td></tr>
<tr><th scope="row">Nebraska</th><td class="text-end">12.8%</td><td class="text-end">7.0%</td><td class="text-end">26.5%</td><td class="text-end">8.2%</td><td class="text-end">3.9%</td></tr>
<tr><th scope="row">South Dakota</th><td class="text-end">11.7%</td><td class="text-end">6.0%</td><td class="text-end">26.4%</td><td class="text-end">6.6%</td><td class="text-end">4.5%</td></tr>
<tr><th scope="row">Virginia</th><td class="text-end">11.7%</td><td class="text-end">6.7%</td><td class="text-end">22.5%</td><td class="text-end">8.6%</td><td class="text-end">2.5%</td></tr>
<tr><th scope="row">Maine</th><td class="text-end">11.6%</td><td class="text-end">6.9%</td><td class="text-end">21.0%</td><td class="text-end">10.1%</td><td class="text-end">1.2%</td></tr>
<tr><th scope="row">Alaska</th><td class="text-end">11.5%</td><td class="text-end">5.6%</td><td class="text-end">25.8%</td><td class="text-end">6.4%</td><td class="text-end">4.3%</td></tr>
<tr><th scope="row">Oregon</th><td class="text-end">10.7%</td><td class="text-end">6.2%</td><td class="text-end">20.0%</td><td class="text-end">8.4%</td><td class="text-end">1.8%</td></tr>
<tr><th scope="row">Kentucky</th><td class="text-end">10.2%</td><td class="text-end">6.0%</td><td class="text-end">18.5%</td><td class="text-end">8.9%</td><td class="text-end">0.9%</td></tr>
</tbody>
</table>
</div>
</details>

- The middle state is at 15.2%. State medians run from 10.2% (Kentucky) to 21.4% (Utah), but any one state's range is wide: Illinois is 8.3% to 31.0%.
- Non-compliance loss barely varies by state (6.4% to 10.1%). Administrative loss runs from 0.9% (Kentucky) to 12.4% (Utah) and is 41% of the loss in the median state. That is the part a better renewal process could in principle reduce.
- Across the 1,042 expansion-state centers we estimate 4.6 million expansion adults, of whom 708,000 lose coverage (469,000 to 1.06 million), 40% for administrative reasons. Net revenue falls $1.5 billion a year ($0.9 to $2.5 billion). The totals treat each state's regime and paperwork shock as independent, so the ranges are somewhat narrow.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/stress-revenue-at-risk.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/stress-revenue-at-risk.webp" width="1200" height="580" loading="lazy" alt="Two charts. Left: eight groups of health centers by size and rural or urban setting, each showing the median net revenue loss as a percent of total revenue with a 5th to 95th percentile range; medians run from 1.1 percent for rural centers with under 5,000 patients to 2.7 percent for urban centers with 40,000+ patients. Right: histogram of 513 centers with a median of 1.9 percent and a tail above 5 percent."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Net revenue change at 513 expansion-state health centers that report Table 9D, middle estimate and 5th to 95th percentile. Revenue includes grants. Sources: HRSA UDS 2025; model.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data tables for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Net revenue loss at the 513 expansion-state centers that report Table 9D, by size and setting (519 report; 6 have under 200 Medicaid patients or no revenue)</caption>
<thead><tr><th scope="col">Group</th><th scope="col" class="text-end">Centers</th><th scope="col" class="text-end">Medicaid share of patients (median)</th><th scope="col" class="text-end">Net loss per year, $ (median center: 5th, middle, 95th)</th><th scope="col" class="text-end">% of total revenue (5th, middle, 95th)</th></tr></thead>
<tbody>
<tr><th scope="row">Under 5,000, rural</th><td class="text-end">44</td><td class="text-end">31%</td><td class="text-end">28,270 / 57,030 / 115,500</td><td class="text-end">0.5% / 1.1% / 2.3%</td></tr>
<tr><th scope="row">Under 5,000, urban</th><td class="text-end">41</td><td class="text-end">50%</td><td class="text-end">68,000 / 145,100 / 310,800</td><td class="text-end">0.8% / 1.6% / 3.5%</td></tr>
<tr><th scope="row">5,000-14,999, rural</th><td class="text-end">97</td><td class="text-end">33%</td><td class="text-end">93,690 / 190,600 / 435,800</td><td class="text-end">0.7% / 1.5% / 3.3%</td></tr>
<tr><th scope="row">5,000-14,999, urban</th><td class="text-end">102</td><td class="text-end">52%</td><td class="text-end">177,500 / 375,400 / 807,900</td><td class="text-end">1.1% / 2.2% / 4.7%</td></tr>
<tr><th scope="row">15,000-39,999, rural</th><td class="text-end">63</td><td class="text-end">36%</td><td class="text-end">312,400 / 662,100 / 1,418,000</td><td class="text-end">0.8% / 1.7% / 3.5%</td></tr>
<tr><th scope="row">15,000-39,999, urban</th><td class="text-end">98</td><td class="text-end">53%</td><td class="text-end">377,400 / 813,900 / 1,752,000</td><td class="text-end">1.0% / 2.1% / 4.5%</td></tr>
<tr><th scope="row">40,000+, rural</th><td class="text-end">21</td><td class="text-end">36%</td><td class="text-end">580,100 / 1,185,000 / 2,590,000</td><td class="text-end">0.7% / 1.5% / 3.2%</td></tr>
<tr><th scope="row">40,000+, urban</th><td class="text-end">47</td><td class="text-end">57%</td><td class="text-end">1,565,000 / 3,304,000 / 6,956,000</td><td class="text-end">1.3% / 2.7% / 5.6%</td></tr>
</tbody>
</table>
</div>
<div class="table-responsive">
<table class="table table-sm">
<caption>Number of centers by middle-estimate net loss as a share of total revenue</caption>
<thead><tr><th scope="col">Net loss, % of total revenue</th><th scope="col" class="text-end">Centers</th></tr></thead>
<tbody>
<tr><th scope="row">0.0 to under 0.4</th><td class="text-end">6</td></tr>
<tr><th scope="row">0.4 to under 0.8</th><td class="text-end">54</td></tr>
<tr><th scope="row">0.8 to under 1.2</th><td class="text-end">61</td></tr>
<tr><th scope="row">1.2 to under 1.6</th><td class="text-end">86</td></tr>
<tr><th scope="row">1.6 to under 2.0</th><td class="text-end">73</td></tr>
<tr><th scope="row">2.0 to under 2.4</th><td class="text-end">67</td></tr>
<tr><th scope="row">2.4 to under 2.8</th><td class="text-end">46</td></tr>
<tr><th scope="row">2.8 to under 3.2</th><td class="text-end">41</td></tr>
<tr><th scope="row">3.2 to under 3.6</th><td class="text-end">38</td></tr>
<tr><th scope="row">3.6 to under 4.0</th><td class="text-end">12</td></tr>
<tr><th scope="row">4.0 to under 4.4</th><td class="text-end">13</td></tr>
<tr><th scope="row">4.4 to under 4.8</th><td class="text-end">8</td></tr>
<tr><th scope="row">4.8 to under 5.2</th><td class="text-end">4</td></tr>
<tr><th scope="row">5.2 to under 5.6</th><td class="text-end">1</td></tr>
<tr><th scope="row">5.6 to under 6.0</th><td class="text-end">0</td></tr>
<tr><th scope="row">6.0 to under 6.4</th><td class="text-end">2</td></tr>
<tr><th scope="row">6.4 to under 6.8</th><td class="text-end">0</td></tr>
<tr><th scope="row">6.8 to under 7.2</th><td class="text-end">0</td></tr>
<tr><th scope="row">7.2 to under 7.6</th><td class="text-end">0</td></tr>
<tr><th scope="row">7.6 or more</th><td class="text-end">1</td></tr>
</tbody>
</table>
</div>
</details>

- At the 513 centers that report Table 9D, the median center loses 1.9% of total revenue (0.7% to 3.5% from the 10th to the 90th percentile of centers), and 18% lose more than 3%. By state the middle estimate runs from 0.7% (South Dakota) to 3.4% (California).

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/stress-what-matters.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/stress-what-matters.webp" width="1200" height="620" loading="lazy" alt="Two bar charts ranking the ten assumptions with the largest effect on net revenue loss. Left: the loss for a typical state (middle estimate 1.8 percent of total revenue) when each input in turn moves from its 10th to its 90th percentile; gold bars show the lower loss and navy bars the higher. The state's paperwork loss and the verification regime move it from about 1.4 to about 2.6 and 2.7 percent. Right: the share of variance each input explains: paperwork loss 0.34, verification regime 0.23, then Medicaid payment per patient 0.14, falling to 0.00 for the last bar, self-pay per uninsured patient."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Which inputs move the revenue answer. Left: one input at a time (gold: lower loss, navy: higher loss). Right: Sobol indices, the share of the spread in the answer each input explains. Model output.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Revenue effect (% of total revenue) when one input moves, typical state (MD; middle estimate 1.8%; for some inputs a higher value lowers the loss), and Sobol indices (median of 41 states)</caption>
<thead><tr><th scope="col">Input</th><th scope="col" class="text-end">At 10th percentile</th><th scope="col" class="text-end">At 90th percentile</th><th scope="col" class="text-end">Revenue: alone</th><th scope="col" class="text-end">Revenue: total</th><th scope="col" class="text-end">Coverage loss: total</th></tr></thead>
<tbody>
<tr><th scope="row">State's paperwork loss vs peers</th><td class="text-end">1.4%</td><td class="text-end">2.6%</td><td class="text-end">0.29</td><td class="text-end">0.34</td><td class="text-end">0.49</td></tr>
<tr><th scope="row">Verification regime (CMS scenario)</th><td class="text-end">1.4%</td><td class="text-end">2.7%</td><td class="text-end">0.19</td><td class="text-end">0.23</td><td class="text-end">0.33</td></tr>
<tr><th scope="row">Medicaid payment per patient</th><td class="text-end">1.3%</td><td class="text-end">2.3%</td><td class="text-end">0.12</td><td class="text-end">0.14</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Medicaid pay, adults vs all patients</th><td class="text-end">1.4%</td><td class="text-end">2.2%</td><td class="text-end">0.11</td><td class="text-end">0.13</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Expansion share of Medicaid adults</th><td class="text-end">1.4%</td><td class="text-end">2.0%</td><td class="text-end">0.07</td><td class="text-end">0.09</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Non-compliance rate</th><td class="text-end">1.5%</td><td class="text-end">2.2%</td><td class="text-end">0.06</td><td class="text-end">0.07</td><td class="text-end">0.10</td></tr>
<tr><th scope="row">State's data matching vs peers</th><td class="text-end">2.0%</td><td class="text-end">1.6%</td><td class="text-end">0.03</td><td class="text-end">0.05</td><td class="text-end">0.07</td></tr>
<tr><th scope="row">Share verified by data matching</th><td class="text-end">1.9%</td><td class="text-end">1.6%</td><td class="text-end">0.02</td><td class="text-end">0.03</td><td class="text-end">0.04</td></tr>
<tr><th scope="row">Share excluded or exempt</th><td class="text-end">1.8%</td><td class="text-end">1.6%</td><td class="text-end">0.01</td><td class="text-end">0.01</td><td class="text-end">0.01</td></tr>
<tr><th scope="row">Self-pay per uninsured patient</th><td class="text-end">1.8%</td><td class="text-end">1.7%</td><td class="text-end">0.00</td><td class="text-end">0.00</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Loss among data-matched members</th><td class="text-end">1.7%</td><td class="text-end">1.8%</td><td class="text-end">0.00</td><td class="text-end">0.00</td><td class="text-end">0.01</td></tr>
<tr><th scope="row">Share who keep coming</th><td class="text-end">1.8%</td><td class="text-end">1.7%</td><td class="text-end">0.00</td><td class="text-end">0.00</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Hardship exception adopted</th><td class="text-end">1.8%</td><td class="text-end">1.8%</td><td class="text-end">0.00</td><td class="text-end">0.00</td><td class="text-end">0.00</td></tr>
<tr><th scope="row">Visit rate once uninsured</th><td class="text-end">1.8%</td><td class="text-end">1.7%</td><td class="text-end">0.00</td><td class="text-end">0.00</td><td class="text-end">0.00</td></tr>
</tbody>
</table>
</div>
</details>

- A state's paperwork loss drives coverage loss most in 36 of 41 states, and the verification regime does in the other five. For revenue the same two lead, then Medicaid payment per patient. The share who keep coming barely registers for revenue (under 0.01): an uninsured patient who keeps coming pays $307 a year, against $1,986 for a Medicaid patient. Margin would differ, since that patient still costs care to deliver.
- KFF reported that [7% of renewing enrollees subject to the rule lost coverage in Nebraska][kff], over a few months (May to September 2026) and including ordinary attrition. Our figure for those subject covers a year of operation: median 16.3% (9.4% to 31.2%), or 8.2% (4.7% to 15.6%) halved to a rough half-year equivalent, which contains 7%. The two are not comparable, so 7% is not evidence for or against the low end.

## Limits

- The survey cannot see eligibility group, monthly hours or frailty, so exposure is a proxy, and the 60% expansion share is an assumption.
- The unwinding was a different process and covers all Medicaid and CHIP enrollees, children included. Kentucky and Maine report near-zero procedural terminations for months, a pause or a reporting artifact, so their low administrative figures (0.9% and 1.2%) are the least certain.
- We assume every state starts January 1, 2027; delays and litigation can change that.
- Table 9D is blank for 695 of 1,356 centers, and the 661 that report skew smaller. UDS has no margin data.
- Retroactive coverage, churn, grants and costs are not modeled. Peer groups are aggregates; no center is projected.

## Use it

Download the [state table (CSV)]({{ site.baseurl }}/downloads/09-health-center-coverage-loss-stress-test-state-ranges.csv) and the [peer benchmark (CSV)]({{ site.baseurl }}/downloads/09-health-center-coverage-loss-stress-test-peer-benchmark.csv). In the [what-if workbook][whatif], paste each state's Low, Mid and High work-requirement columns into Inputs C24:E24 and the paperwork columns into C25:E25. The workbook adds them, so the summed Low and High are wider than the model's range (in the median state 1.8 points under and 4.8 points over). The CSV's `total_loss_p5`, `total_loss_p50` and `total_loss_p95` columns hold the modeled range. For C6, divide "expansion adults per 1,000 Medicaid patients" by 1,000 and multiply by your Medicaid patients of all ages.

Code, method and sources: [analysis/09-health-center-coverage-loss-stress-test](https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/09-health-center-coverage-loss-stress-test). Every number above comes from `output/numbers.json`.

{% include casestudy_cta.html %}

</div>
