---
title: Free Clinic Demand Planner
subtitle: How many sessions to plan for in 2027
description: "Public data only. No patient information."
lead: "Public data only. No patient information."
layout: default
modal-id: 11
date: 2026-10-22
thumbnail: free-clinic-thumbnail.webp
kind: example
persona: "For free and charitable clinics"
need: "How many more low-income uninsured adults to expect in my county in 2027, and how many sessions, volunteers and medication dollars to commit at a stated probability."
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

[cms-oep]: https://www.cms.gov/data-research/statistics-trends-reports/marketplace-products/2026-marketplace-open-enrollment-period-public-use-files
[cms-eff]: https://data.cms.gov/summary-statistics-on-beneficiary-enrollment/health-insurance-marketplace/health-insurance-exchanges-monthly-effectuated-enrollment
[sahie]: https://www.census.gov/programs-surveys/sahie.html
[pi]: https://download.medicaid.gov/data/pi-dataset-september-2026-release.csv
[kff-may]: https://www.kff.org/affordable-care-act/what-we-know-so-far-about-2026-aca-marketplace-enrollment-premiums-and-deductibles/
[kff-exp]: https://www.kff.org/medicaid/5-key-facts-about-medicaid-expansion/
[aspe]: https://www.aspe.hhs.gov/sites/default/files/documents/f5f29954221d5b5713070ac2541fda8e/aca-enrollment-report-2026-final-version.pdf
[bridge]: https://healthcare.oregon.gov/Documents/HIMAC%20Materials/2-CY2026%20Assessment%20Analysis%20HIMAC%20FINAL%2006.17.25.pdf
[what-if]: {{ site.baseurl }}/blog/medicaid-what-if-template/

## Who this is for

The director of a volunteer-run free or charitable clinic who must commit sessions, volunteers and donated medicine for 2027 and write the funding request now. This is an example on public data, not a client engagement, and the clinic in the figures is hypothetical.

## Question

How many more adults at or below 200% of poverty will be uninsured in a county in 2027, and how many clinic sessions cover that demand with 80% or 95% probability?

## Data

- **CMS Open Enrollment county files, 2025 and 2026** ([2026 page][cms-oep]): plan selections by income band, premiums, automatic re-enrollment. 2,054 counties match across the HealthCare.gov states; state exchanges such as California and New York are not in them.
- **CMS monthly effectuated enrollment**, February 2025 and 2026, by state ([data.cms.gov][cms-eff]): people who paid.
- **Census SAHIE 2024** ([program page][sahie]): uninsured adults 18 to 64 at or below 200% of poverty, with 90% margins of error (median 16% of the estimate).
- **Medicaid.gov enrollment, June 2026** ([download][pi]), for the Medicaid layer.

All downloaded 2026-10-22; hashes are in `numbers.json`.

## Method

**Observed.** Selections count everyone who picked a plan, paid or not, so county change is observed, apart from suppressed cells (1 to 10 people), which we redraw at random.

**Scenarios.** The 2027 increase in uninsured adults, relative to the SAHIE 2024 baseline, has two layers.

- Marketplace: the loss of paid coverage among adults at 100 to 200% of poverty, February 2025 to February 2026 (county selections times the state's paid share), plus further loss after February, times the share who end up uninsured.
- Medicaid, expansion states only: state Medicaid and CHIP enrollment times the 30% who are expansion adults ([KFF][kff-exp] reports 31% of Medicaid enrollment in June 2024; our base includes CHIP), split to counties by adults below 138% of poverty, times the share losing coverage under work requirements (13.5%, 28%, 50%, from our [Medicaid what-if post][what-if]), a phase-in share and the share left uninsured. These are placeholders.

Each assumption is a range, not a point, with 10,000 draws per scenario. Further marketplace loss is 4%, 9% or 16%; [KFF projects][kff-may] 2026 paid enrollment averaging 17.5 million.

**Clinic and decision.** Most of the 2026 marketplace loss is already in a clinic's last 12 months of visits, so only the rest adds to them. We assume 80% is already there; with none, the example below needs 186 sessions at 80%, not 174. Visits in 2027 equal visits today times one plus that growth, scaled by a rate; 1 means newly uninsured adults come at the clinic's current rate. Public data cannot identify it, so the clinic overwrites it with intake counts. Sessions cover visits at the chosen probability: choosing 80% treats a session of turned-away patients as 4 times as costly as an idle one; 95%, 19 times.

## What it shows

**What changed.** In the 2,054 matched counties, selections fell 5.4%, from 16,662,905 to 15,771,373 and selections at 100 to 200% of poverty fell 3.9%. The larger change is payment: 87.4% of selections were paid up by February 2025 and 78.7% in February 2026, so paid enrollment fell 14.8%, or 2,152,711 people. We estimate 1,344,887 fewer paid adults at 100 to 200% of poverty. Across states, paid share falls as automatic re-enrollment rises (r = -0.76).

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/free-clinic-observed.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/free-clinic-observed.webp" width="1200" height="1338" loading="lazy" alt="Two charts of 30 HealthCare.gov states, sharing one list of states. Left: bars showing the change in plan selections by people at 100 to 200 percent of the poverty level, 2026 versus 2025. The steepest fall is 43 percent in one state, then North Carolina 26, West Virginia 25 and Ohio 24. Texas rose 8 percent. The 30-state total fell 3.9 percent. Right: a dot chart of the share of plan selections paid up by February, 2025 and 2026. Every state fell except North Carolina and West Virginia. Mississippi is lowest at 61.1 percent in 2026; South Carolina, Louisiana, Indiana and Oklahoma are also below 70 percent."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Low-income plan selections and share paid up by February, by state. Sources: CMS Open Enrollment 2025 and 2026; CMS monthly effectuated enrollment.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data tables for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Low-income plan selections and share paid up, by state, 2025 and 2026, highest 2026 paid share first</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Selections 2025</th><th scope="col" class="text-end">Selections 2026</th><th scope="col" class="text-end">Change</th><th scope="col" class="text-end">Paid share Feb 2025</th><th scope="col" class="text-end">Paid share Feb 2026</th></tr></thead>
<tbody>
<tr><th scope="row">North Dakota</th><td class="text-end">12,556</td><td class="text-end">12,087</td><td class="text-end">-3.7%</td><td class="text-end">94.8%</td><td class="text-end">91.4%</td></tr>
<tr><th scope="row">Alaska</th><td class="text-end">6,526</td><td class="text-end">6,103</td><td class="text-end">-6.5%</td><td class="text-end">94.1%</td><td class="text-end">90.4%</td></tr>
<tr><th scope="row">South Dakota</th><td class="text-end">17,482</td><td class="text-end">15,629</td><td class="text-end">-10.6%</td><td class="text-end">93.7%</td><td class="text-end">90.1%</td></tr>
<tr><th scope="row">Hawaii</th><td class="text-end">8,804</td><td class="text-end">9,162</td><td class="text-end">+4.1%</td><td class="text-end">93.6%</td><td class="text-end">89.7%</td></tr>
<tr><th scope="row">Oregon</th><td class="text-end">17,966</td><td class="text-end">10,174</td><td class="text-end">-43.4%</td><td class="text-end">92.7%</td><td class="text-end">89.5%</td></tr>
<tr><th scope="row">West Virginia</th><td class="text-end">40,137</td><td class="text-end">30,290</td><td class="text-end">-24.5%</td><td class="text-end">84.9%</td><td class="text-end">88.6%</td></tr>
<tr><th scope="row">New Hampshire</th><td class="text-end">22,349</td><td class="text-end">19,037</td><td class="text-end">-14.8%</td><td class="text-end">89.0%</td><td class="text-end">87.4%</td></tr>
<tr><th scope="row">Montana</th><td class="text-end">27,808</td><td class="text-end">26,049</td><td class="text-end">-6.3%</td><td class="text-end">93.5%</td><td class="text-end">87.3%</td></tr>
<tr><th scope="row">Utah</th><td class="text-end">237,910</td><td class="text-end">221,271</td><td class="text-end">-7.0%</td><td class="text-end">94.9%</td><td class="text-end">87.1%</td></tr>
<tr><th scope="row">Florida</th><td class="text-end">3,798,881</td><td class="text-end">3,690,125</td><td class="text-end">-2.9%</td><td class="text-end">90.6%</td><td class="text-end">84.8%</td></tr>
<tr><th scope="row">Wisconsin</th><td class="text-end">138,576</td><td class="text-end">125,620</td><td class="text-end">-9.3%</td><td class="text-end">92.9%</td><td class="text-end">84.4%</td></tr>
<tr><th scope="row">Iowa</th><td class="text-end">61,765</td><td class="text-end">52,020</td><td class="text-end">-15.8%</td><td class="text-end">90.8%</td><td class="text-end">83.7%</td></tr>
<tr><th scope="row">Wyoming</th><td class="text-end">16,518</td><td class="text-end">16,659</td><td class="text-end">+0.9%</td><td class="text-end">94.9%</td><td class="text-end">83.1%</td></tr>
<tr><th scope="row">Delaware</th><td class="text-end">24,090</td><td class="text-end">19,535</td><td class="text-end">-18.9%</td><td class="text-end">83.7%</td><td class="text-end">81.2%</td></tr>
<tr><th scope="row">Arkansas</th><td class="text-end">98,141</td><td class="text-end">87,813</td><td class="text-end">-10.5%</td><td class="text-end">86.5%</td><td class="text-end">80.9%</td></tr>
<tr><th scope="row">North Carolina</th><td class="text-end">632,020</td><td class="text-end">467,765</td><td class="text-end">-26.0%</td><td class="text-end">79.4%</td><td class="text-end">80.0%</td></tr>
<tr><th scope="row">Texas</th><td class="text-end">3,024,056</td><td class="text-end">3,273,213</td><td class="text-end">+8.2%</td><td class="text-end">86.3%</td><td class="text-end">78.5%</td></tr>
<tr><th scope="row">Nebraska</th><td class="text-end">57,714</td><td class="text-end">57,040</td><td class="text-end">-1.2%</td><td class="text-end">95.4%</td><td class="text-end">78.3%</td></tr>
<tr><th scope="row">Tennessee</th><td class="text-end">474,317</td><td class="text-end">420,325</td><td class="text-end">-11.4%</td><td class="text-end">79.9%</td><td class="text-end">77.6%</td></tr>
<tr><th scope="row">Kansas</th><td class="text-end">133,501</td><td class="text-end">134,385</td><td class="text-end">+0.7%</td><td class="text-end">89.9%</td><td class="text-end">74.6%</td></tr>
<tr><th scope="row">Michigan</th><td class="text-end">300,530</td><td class="text-end">282,006</td><td class="text-end">-6.2%</td><td class="text-end">91.9%</td><td class="text-end">71.9%</td></tr>
<tr><th scope="row">Arizona</th><td class="text-end">251,780</td><td class="text-end">215,250</td><td class="text-end">-14.5%</td><td class="text-end">85.8%</td><td class="text-end">71.7%</td></tr>
<tr><th scope="row">Ohio</th><td class="text-end">356,743</td><td class="text-end">270,439</td><td class="text-end">-24.2%</td><td class="text-end">85.3%</td><td class="text-end">71.6%</td></tr>
<tr><th scope="row">Missouri</th><td class="text-end">283,810</td><td class="text-end">244,051</td><td class="text-end">-14.0%</td><td class="text-end">83.3%</td><td class="text-end">71.4%</td></tr>
<tr><th scope="row">Alabama</th><td class="text-end">375,896</td><td class="text-end">362,601</td><td class="text-end">-3.5%</td><td class="text-end">87.6%</td><td class="text-end">71.2%</td></tr>
<tr><th scope="row">Oklahoma</th><td class="text-end">215,732</td><td class="text-end">184,175</td><td class="text-end">-14.6%</td><td class="text-end">86.1%</td><td class="text-end">68.6%</td></tr>
<tr><th scope="row">Indiana</th><td class="text-end">229,749</td><td class="text-end">191,078</td><td class="text-end">-16.8%</td><td class="text-end">78.3%</td><td class="text-end">67.7%</td></tr>
<tr><th scope="row">Louisiana</th><td class="text-end">213,109</td><td class="text-end">222,346</td><td class="text-end">+4.3%</td><td class="text-end">90.4%</td><td class="text-end">66.0%</td></tr>
<tr><th scope="row">South Carolina</th><td class="text-end">441,048</td><td class="text-end">415,955</td><td class="text-end">-5.7%</td><td class="text-end">86.5%</td><td class="text-end">65.9%</td></tr>
<tr><th scope="row">Mississippi</th><td class="text-end">304,441</td><td class="text-end">284,627</td><td class="text-end">-6.5%</td><td class="text-end">77.0%</td><td class="text-end">61.1%</td></tr>
</tbody>
</table>
</div>
<div class="table-responsive">
<table class="table table-sm">
<caption>Ten counties with the largest stability-adjusted decline in low-income selections (at least 500 in 2025)</caption>
<thead><tr><th scope="col">County</th><th scope="col" class="text-end">Selections 2025</th><th scope="col" class="text-end">Selections 2026</th><th scope="col" class="text-end">Raw change</th><th scope="col" class="text-end">Stability-adjusted change</th></tr></thead>
<tbody>
<tr><th scope="row">Marion County, OR</th><td class="text-end">1,297</td><td class="text-end">484</td><td class="text-end">-62.7%</td><td class="text-end">-60.3%</td></tr>
<tr><th scope="row">Edgecombe County, NC</th><td class="text-end">4,384</td><td class="text-end">1,689</td><td class="text-end">-61.5%</td><td class="text-end">-60.1%</td></tr>
<tr><th scope="row">Jackson County, OR</th><td class="text-end">927</td><td class="text-end">346</td><td class="text-end">-62.7%</td><td class="text-end">-59.6%</td></tr>
<tr><th scope="row">Sherman County, TX</th><td class="text-end">922</td><td class="text-end">356</td><td class="text-end">-61.4%</td><td class="text-end">-51.8%</td></tr>
<tr><th scope="row">Nash County, NC</th><td class="text-end">4,935</td><td class="text-end">2,357</td><td class="text-end">-52.2%</td><td class="text-end">-51.4%</td></tr>
<tr><th scope="row">Wayne County, NC</th><td class="text-end">7,732</td><td class="text-end">3,851</td><td class="text-end">-50.2%</td><td class="text-end">-49.7%</td></tr>
<tr><th scope="row">Caswell County, NC</th><td class="text-end">1,303</td><td class="text-end">622</td><td class="text-end">-52.3%</td><td class="text-end">-49.3%</td></tr>
<tr><th scope="row">Greene County, NC</th><td class="text-end">1,433</td><td class="text-end">696</td><td class="text-end">-51.4%</td><td class="text-end">-48.8%</td></tr>
<tr><th scope="row">Pitt County, NC</th><td class="text-end">10,976</td><td class="text-end">5,595</td><td class="text-end">-49.0%</td><td class="text-end">-48.7%</td></tr>
<tr><th scope="row">Wilson County, NC</th><td class="text-end">6,248</td><td class="text-end">3,173</td><td class="text-end">-49.2%</td><td class="text-end">-48.6%</td></tr>
</tbody>
</table>
</div>
</details>

**Mostly a state story.** States explain 43% of the variance in county change in the 100 to 150% band. We also predicted each county's 150 to 200% change without that county's own 150 to 200% change, in the 1,529 counties with at least 100 selections in every band and year. The average of the state's other counties beat the national average and no change (error 0.111 against 0.135 and 0.175). Adding the county's own 100 to 150% change trims the error 4.5% more (95% interval 2.0% to 7.2%), and within a state the two bands correlate at only 0.31. The ten largest declines, adjusted for noise by pulling each county toward its state average (at least 500 selections), are 49% to 60%, and 7 are in North Carolina.

**2027.** The central scenario adds **1,640,179** uninsured adults at or below 200% of poverty (80% interval 1,039,504 to 2,454,496), 25.7% of the 2024 pool of 6,364,883. Marketplace losses alone add 965,227; the Medicaid layer alone adds 609,298. This counts the whole rise from the 2024 baseline, including losses a clinic's recent visits already hold.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/free-clinic-scenarios.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/free-clinic-scenarios.webp" width="1200" height="1728" loading="lazy" alt="Two stacked charts. Top: bars of additional uninsured adults at or below 200 percent of poverty in 2027 across 2,054 counties, with 10th to 90th percentile whiskers. Marketplace losses only: 460 thousand in the lower scenario, 965 thousand central, 1.72 million higher. With the Medicaid work-requirement layer: 644 thousand, 1.64 million and 3.50 million. Bottom: histogram of counties by growth in the uninsured pool in the central scenario. Marketplace losses only cluster near 14 percent. With the Medicaid layer there is a second hump near 40 percent for expansion states, and the median is 33 percent."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Additional uninsured adults in 2027 relative to 2024, 30 HealthCare.gov states. Scenario inputs are assumptions.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Additional uninsured adults at or below 200% of poverty in 2027 relative to 2024, 2,054 counties (10th, 50th and 90th percentiles)</caption>
<thead><tr><th scope="col">Scenario</th><th scope="col" class="text-end">Marketplace only</th><th scope="col" class="text-end">Medicaid layer only</th><th scope="col" class="text-end">Both layers</th><th scope="col" class="text-end">Both layers, % of 2024 pool (median)</th><th scope="col" class="text-end">Median county, expansion states</th><th scope="col" class="text-end">Median county, other states</th></tr></thead>
<tbody>
<tr><th scope="row">Lower</th><td class="text-end">206,302 / 459,814 / 825,489</td><td class="text-end">34,326 / 142,805 / 410,733</td><td class="text-end">337,706 / 643,905 / 1,081,288</td><td class="text-end">10.1%</td><td class="text-end">14.3%</td><td class="text-end">7.2%</td></tr>
<tr><th scope="row">Central</th><td class="text-end">562,896 / 965,227 / 1,522,057</td><td class="text-end">246,872 / 609,298 / 1,235,077</td><td class="text-end">1,039,504 / 1,640,179 / 2,454,496</td><td class="text-end">25.7%</td><td class="text-end">40.9%</td><td class="text-end">15.0%</td></tr>
<tr><th scope="row">Higher</th><td class="text-end">1,135,442 / 1,724,856 / 2,535,636</td><td class="text-end">919,615 / 1,704,435 / 2,752,104</td><td class="text-end">2,466,873 / 3,500,933 / 4,797,799</td><td class="text-end">55.0%</td><td class="text-end">96.2%</td><td class="text-end">26.2%</td></tr>
</tbody>
</table>
</div>
</details>

**A clinic.** A hypothetical clinic sees 480 uninsured adults in 1,440 visits and 120 sessions a year, in a county with 5,917 uninsured low-income adults. In the central scenario it needs 156 sessions at 50% probability, **174 at 80%** and **196 at 95%**. Going from 80% to 95% costs 22 sessions, 396 volunteer hours and 11 more volunteers. The clinic's own new-patient rate and the Medicaid loss share each move the 80% answer by about 50 sessions (147 to 200 and 154 to 204). Each marketplace assumption moves it by 10 sessions or less.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/free-clinic-decision.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/free-clinic-decision.webp" width="1200" height="1792" loading="lazy" alt="Two stacked charts for a hypothetical clinic that runs 120 sessions a year. Top: sessions needed against the probability of covering 2027 demand, for lower, central and higher scenarios. In the central scenario 156 sessions are needed at 50 percent, 174 at 80 percent and 196 at 95 percent. Bottom: bars showing how far the 80 percent answer moves when one assumption changes, dark for more sessions than the central case and gold for fewer. The clinic's new-patient rate (147 to 200 sessions) and the share of Medicaid expansion adults who lose coverage (154 to 204) matter most. Each marketplace assumption moves the answer by 10 sessions or less."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Sessions to plan for, and what drives the number, for a hypothetical clinic in a mid-sized expansion-state county.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data tables for this chart</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Hypothetical clinic: sessions, volunteers and medication for 2027 (today: 120 sessions, 60 volunteers)</caption>
<thead><tr><th scope="col">Scenario and layers</th><th scope="col" class="text-end">Probability</th><th scope="col" class="text-end">Growth in visits</th><th scope="col" class="text-end">Sessions a year</th><th scope="col" class="text-end">Extra sessions</th><th scope="col" class="text-end">Volunteers</th><th scope="col" class="text-end">Volunteer hours</th><th scope="col" class="text-end">Medication dollars</th></tr></thead>
<tbody>
<tr><th scope="row">Lower, with Medicaid layer</th><td class="text-end">50%</td><td class="text-end">8.1%</td><td class="text-end">130</td><td class="text-end">10</td><td class="text-end">65</td><td class="text-end">2,340</td><td class="text-end">$31,140</td></tr>
<tr><th scope="row">Lower, with Medicaid layer</th><td class="text-end">80%</td><td class="text-end">14.1%</td><td class="text-end">137</td><td class="text-end">17</td><td class="text-end">69</td><td class="text-end">2,466</td><td class="text-end">$32,846</td></tr>
<tr><th scope="row">Lower, with Medicaid layer</th><td class="text-end">95%</td><td class="text-end">22.6%</td><td class="text-end">148</td><td class="text-end">28</td><td class="text-end">74</td><td class="text-end">2,664</td><td class="text-end">$35,299</td></tr>
<tr><th scope="row">Lower, marketplace only</th><td class="text-end">50%</td><td class="text-end">2.3%</td><td class="text-end">123</td><td class="text-end">3</td><td class="text-end">62</td><td class="text-end">2,214</td><td class="text-end">$29,455</td></tr>
<tr><th scope="row">Lower, marketplace only</th><td class="text-end">80%</td><td class="text-end">4.0%</td><td class="text-end">125</td><td class="text-end">5</td><td class="text-end">63</td><td class="text-end">2,250</td><td class="text-end">$29,962</td></tr>
<tr><th scope="row">Lower, marketplace only</th><td class="text-end">95%</td><td class="text-end">7.0%</td><td class="text-end">129</td><td class="text-end">9</td><td class="text-end">65</td><td class="text-end">2,322</td><td class="text-end">$30,803</td></tr>
<tr><th scope="row">Central, with Medicaid layer</th><td class="text-end">50%</td><td class="text-end">29.9%</td><td class="text-end">156</td><td class="text-end">36</td><td class="text-end">78</td><td class="text-end">2,808</td><td class="text-end">$37,424</td></tr>
<tr><th scope="row">Central, with Medicaid layer</th><td class="text-end">80%</td><td class="text-end">44.2%</td><td class="text-end">174</td><td class="text-end">54</td><td class="text-end">87</td><td class="text-end">3,132</td><td class="text-end">$41,541</td></tr>
<tr><th scope="row">Central, with Medicaid layer</th><td class="text-end">95%</td><td class="text-end">62.6%</td><td class="text-end">196</td><td class="text-end">76</td><td class="text-end">98</td><td class="text-end">3,528</td><td class="text-end">$46,837</td></tr>
<tr><th scope="row">Central, marketplace only</th><td class="text-end">50%</td><td class="text-end">6.6%</td><td class="text-end">128</td><td class="text-end">8</td><td class="text-end">64</td><td class="text-end">2,304</td><td class="text-end">$30,701</td></tr>
<tr><th scope="row">Central, marketplace only</th><td class="text-end">80%</td><td class="text-end">10.9%</td><td class="text-end">134</td><td class="text-end">14</td><td class="text-end">67</td><td class="text-end">2,412</td><td class="text-end">$31,945</td></tr>
<tr><th scope="row">Central, marketplace only</th><td class="text-end">95%</td><td class="text-end">16.5%</td><td class="text-end">140</td><td class="text-end">20</td><td class="text-end">70</td><td class="text-end">2,520</td><td class="text-end">$33,560</td></tr>
<tr><th scope="row">Higher, with Medicaid layer</th><td class="text-end">50%</td><td class="text-end">78.1%</td><td class="text-end">214</td><td class="text-end">94</td><td class="text-end">107</td><td class="text-end">3,852</td><td class="text-end">$51,305</td></tr>
<tr><th scope="row">Higher, with Medicaid layer</th><td class="text-end">80%</td><td class="text-end">104.4%</td><td class="text-end">246</td><td class="text-end">126</td><td class="text-end">123</td><td class="text-end">4,428</td><td class="text-end">$58,870</td></tr>
<tr><th scope="row">Higher, with Medicaid layer</th><td class="text-end">95%</td><td class="text-end">133.8%</td><td class="text-end">281</td><td class="text-end">161</td><td class="text-end">141</td><td class="text-end">5,058</td><td class="text-end">$67,328</td></tr>
<tr><th scope="row">Higher, marketplace only</th><td class="text-end">50%</td><td class="text-end">15.3%</td><td class="text-end">139</td><td class="text-end">19</td><td class="text-end">70</td><td class="text-end">2,502</td><td class="text-end">$33,201</td></tr>
<tr><th scope="row">Higher, marketplace only</th><td class="text-end">80%</td><td class="text-end">22.6%</td><td class="text-end">148</td><td class="text-end">28</td><td class="text-end">74</td><td class="text-end">2,664</td><td class="text-end">$35,314</td></tr>
<tr><th scope="row">Higher, marketplace only</th><td class="text-end">95%</td><td class="text-end">30.9%</td><td class="text-end">158</td><td class="text-end">38</td><td class="text-end">79</td><td class="text-end">2,844</td><td class="text-end">$37,708</td></tr>
</tbody>
</table>
</div>
<div class="table-responsive">
<table class="table table-sm">
<caption>Sessions a year at 80% probability when one assumption moves from its low to its high end (central case: 174). A larger pool, or more of the 2026 loss already in your visits, means fewer sessions</caption>
<thead><tr><th scope="col">Assumption (low to high)</th><th scope="col" class="text-end">Sessions at the low end</th><th scope="col" class="text-end">Sessions at the high end</th></tr></thead>
<tbody>
<tr><th scope="row">Your new-patient rate vs today (0.5x-1.5x)</th><td class="text-end">147</td><td class="text-end">200</td></tr>
<tr><th scope="row">Expansion adults losing Medicaid (13.5-50%)</th><td class="text-end">154</td><td class="text-end">204</td></tr>
<tr><th scope="row">Share of that loss in place in 2027 (35-65%)</th><td class="text-end">162</td><td class="text-end">186</td></tr>
<tr><th scope="row">Uninsured pool, SAHIE 90% interval</th><td class="text-end">182</td><td class="text-end">167</td></tr>
<tr><th scope="row">Medicaid losers left uninsured (70-95%)</th><td class="text-end">166</td><td class="text-end">179</td></tr>
<tr><th scope="row">Marketplace attrition after Feb 2026 (4-16%)</th><td class="text-end">170</td><td class="text-end">180</td></tr>
<tr><th scope="row">Expansion adults' share of enrollment (27-33%)</th><td class="text-end">169</td><td class="text-end">178</td></tr>
<tr><th scope="row">Lost marketplace coverage that ends uninsured (30-70%)</th><td class="text-end">170</td><td class="text-end">178</td></tr>
<tr><th scope="row">2026 loss already in your visits (60-100%)</th><td class="text-end">177</td><td class="text-end">171</td></tr>
</tbody>
</table>
</div>
</details>

## Limits

- Selections are not paid coverage. Paid share is observed by state only, and we apply it to every county and income level.
- HHS's [ASPE brief][aspe] estimates 2.6 million improper or phantom enrollments remain after 2.9 million were removed or blocked, so some of the drop is people who never used care. Our assumed uninsured share (30% to 70%) absorbs that.
- In the state with the 43% fall, some people moved to a [state program][bridge] for adults at 138 to 200% of poverty rather than becoming uninsured. We did not adjust, so its counties, including the top two in the county table, are likely overstated.
- Nothing here is causal: credit expiry, enrollment cleanup, North Carolina's Medicaid expansion and the economy move the same numbers. Losses are counted from February 2025 against a 2024 baseline, so any change in between is missing.
- The Medicaid layer is a placeholder. Hawaii shows the problem: 73% median county growth. Counties with under 500 uninsured low-income adults (785) have unstable growth rates; the CSV flags them.
- The 80% interval and the 80% and 95% session answers hold within one scenario's assumptions and leave out the spread between scenarios. Nothing here can be checked against outcomes, so an 80% is a statement about our assumptions, not a hit rate.

## Use it

Download the [Excel planner]({{ site.baseurl }}/downloads/11-free-clinic-surge-planner-demand-planner.xlsx) (live formulas). Pick your county, enter 12 months of visits and your session setup, and read sessions, volunteers and medication dollars. A Need statement sheet drafts a paragraph for a funding application, and an Intake guide names three numbers to log so you can replace our assumption about new arrivals. The [county table]({{ site.baseurl }}/downloads/11-free-clinic-surge-planner-county-table.csv) (CSV, with a [codebook]({{ site.baseurl }}/downloads/11-free-clinic-surge-planner-county-table-codebook.csv)) holds observed changes, risk flags, ranking and quantiles for all 2,054 counties.

Code and method: [analysis/11-free-clinic-surge-planner](https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/11-free-clinic-surge-planner).

{% include casestudy_cta.html %}

</div>
