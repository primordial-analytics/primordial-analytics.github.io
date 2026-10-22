---
title: Medicaid at Health Centers
subtitle: Who relies on Medicaid, state by state
description: "Public data only. No patient information."
lead: "Public data only. No patient information."
layout: default
modal-id: 7
date: 2026-10-22
thumbnail: example-uds-thumbnail.webp
kind: example
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

[hrsa-download]: https://data.hrsa.gov/data/download
[snapshot]: https://data.hrsa.gov/tools/data-reporting/data-snapshot?year=2025

## Question

How much of a health center's patient base does Medicaid cover, state by state?

## Data

HRSA's Uniform Data System, calendar year 2025: one row per health center (1,356), with patient counts by insurance type. From HRSA's [Data Downloads page][hrsa-download], downloaded 2026-10-22. These are organization-level counts.

## What we did

We summed each health center's patients, Medicaid/CHIP patients (Table 4 lines 8 and 10b) and uninsured patients, then totaled them by state. We show the 48 states and territories with at least 100,000 patients. Dashes in the file count as zero. Our national totals match HRSA's [published figures][snapshot] of 47.92% Medicaid/CHIP and 17.21% uninsured.

## What it shows

Of 32,746,371 patients, **15,692,019 (47.9%)** had Medicaid or CHIP and **5,634,320 (17.2%)** were uninsured.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-uds-medicaid-share.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-uds-medicaid-share.webp" width="1200" height="1120" loading="lazy" alt="Horizontal bar chart of 48 states and territories ranked by the share of health-center patients covered by Medicaid or CHIP in 2025. California is highest at 71.8 percent and Utah lowest at 18.5 percent. A dashed line marks the all-health-center average of 47.9 percent."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Medicaid/CHIP share of health-center patients by state, 2025. Source: HRSA UDS, calendar year 2025.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<table class="table table-sm">
<caption>Medicaid/CHIP share of health-center patients by state, 2025, highest to lowest</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Medicaid/CHIP share</th><th scope="col" class="text-end">Medicaid/CHIP patients</th><th scope="col" class="text-end">All patients</th></tr></thead>
<tbody>
<tr><th scope="row">California</th><td class="text-end">71.8%</td><td class="text-end">4,235,855</td><td class="text-end">5,900,535</td></tr>
<tr><th scope="row">Oregon</th><td class="text-end">61.4%</td><td class="text-end">270,052</td><td class="text-end">440,152</td></tr>
<tr><th scope="row">Puerto Rico</th><td class="text-end">60.1%</td><td class="text-end">305,501</td><td class="text-end">508,068</td></tr>
<tr><th scope="row">Connecticut</th><td class="text-end">57.0%</td><td class="text-end">254,754</td><td class="text-end">447,075</td></tr>
<tr><th scope="row">Wisconsin</th><td class="text-end">56.3%</td><td class="text-end">168,594</td><td class="text-end">299,686</td></tr>
<tr><th scope="row">Hawaii</th><td class="text-end">56.0%</td><td class="text-end">87,984</td><td class="text-end">157,004</td></tr>
<tr><th scope="row">Washington</th><td class="text-end">54.4%</td><td class="text-end">704,637</td><td class="text-end">1,294,656</td></tr>
<tr><th scope="row">Illinois</th><td class="text-end">53.4%</td><td class="text-end">774,676</td><td class="text-end">1,450,397</td></tr>
<tr><th scope="row">New York</th><td class="text-end">52.3%</td><td class="text-end">1,211,258</td><td class="text-end">2,314,742</td></tr>
<tr><th scope="row">District of Columbia</th><td class="text-end">52.1%</td><td class="text-end">93,534</td><td class="text-end">179,535</td></tr>
<tr><th scope="row">Missouri</th><td class="text-end">51.8%</td><td class="text-end">353,589</td><td class="text-end">681,965</td></tr>
<tr><th scope="row">Louisiana</th><td class="text-end">51.4%</td><td class="text-end">257,646</td><td class="text-end">501,384</td></tr>
<tr><th scope="row">Rhode Island</th><td class="text-end">50.4%</td><td class="text-end">117,189</td><td class="text-end">232,629</td></tr>
<tr><th scope="row">New Jersey</th><td class="text-end">50.2%</td><td class="text-end">323,002</td><td class="text-end">643,753</td></tr>
<tr><th scope="row">Colorado</th><td class="text-end">50.0%</td><td class="text-end">319,256</td><td class="text-end">638,538</td></tr>
<tr><th scope="row">Iowa</th><td class="text-end">48.7%</td><td class="text-end">128,071</td><td class="text-end">263,006</td></tr>
<tr><th scope="row">Indiana</th><td class="text-end">48.5%</td><td class="text-end">346,864</td><td class="text-end">714,585</td></tr>
<tr><th scope="row">Ohio</th><td class="text-end">47.6%</td><td class="text-end">444,083</td><td class="text-end">933,414</td></tr>
<tr><th scope="row">Maryland</th><td class="text-end">46.4%</td><td class="text-end">171,122</td><td class="text-end">368,723</td></tr>
<tr><th scope="row">Michigan</th><td class="text-end">45.0%</td><td class="text-end">311,808</td><td class="text-end">693,367</td></tr>
<tr><th scope="row">Minnesota</th><td class="text-end">42.8%</td><td class="text-end">67,667</td><td class="text-end">158,039</td></tr>
<tr><th scope="row">Pennsylvania</th><td class="text-end">42.8%</td><td class="text-end">372,010</td><td class="text-end">869,212</td></tr>
<tr><th scope="row">Kentucky</th><td class="text-end">42.8%</td><td class="text-end">289,187</td><td class="text-end">675,713</td></tr>
<tr><th scope="row">Arizona</th><td class="text-end">41.7%</td><td class="text-end">357,222</td><td class="text-end">856,192</td></tr>
<tr><th scope="row">Massachusetts</th><td class="text-end">41.0%</td><td class="text-end">363,104</td><td class="text-end">884,863</td></tr>
<tr><th scope="row">Nebraska</th><td class="text-end">39.0%</td><td class="text-end">47,381</td><td class="text-end">121,579</td></tr>
<tr><th scope="row">Oklahoma</th><td class="text-end">38.6%</td><td class="text-end">137,643</td><td class="text-end">356,851</td></tr>
<tr><th scope="row">Florida</th><td class="text-end">37.9%</td><td class="text-end">634,910</td><td class="text-end">1,673,307</td></tr>
<tr><th scope="row">New Mexico</th><td class="text-end">35.9%</td><td class="text-end">105,570</td><td class="text-end">294,403</td></tr>
<tr><th scope="row">Nevada</th><td class="text-end">35.2%</td><td class="text-end">47,905</td><td class="text-end">135,913</td></tr>
<tr><th scope="row">Virginia</th><td class="text-end">35.1%</td><td class="text-end">143,785</td><td class="text-end">410,092</td></tr>
<tr><th scope="row">Alaska</th><td class="text-end">33.5%</td><td class="text-end">38,140</td><td class="text-end">113,867</td></tr>
<tr><th scope="row">Texas</th><td class="text-end">31.8%</td><td class="text-end">604,229</td><td class="text-end">1,898,301</td></tr>
<tr><th scope="row">Idaho</th><td class="text-end">31.7%</td><td class="text-end">78,615</td><td class="text-end">247,642</td></tr>
<tr><th scope="row">Arkansas</th><td class="text-end">31.6%</td><td class="text-end">121,715</td><td class="text-end">385,249</td></tr>
<tr><th scope="row">West Virginia</th><td class="text-end">31.3%</td><td class="text-end">185,828</td><td class="text-end">593,315</td></tr>
<tr><th scope="row">Alabama</th><td class="text-end">31.0%</td><td class="text-end">98,241</td><td class="text-end">316,993</td></tr>
<tr><th scope="row">North Carolina</th><td class="text-end">30.6%</td><td class="text-end">224,422</td><td class="text-end">732,318</td></tr>
<tr><th scope="row">Tennessee</th><td class="text-end">28.8%</td><td class="text-end">123,147</td><td class="text-end">427,688</td></tr>
<tr><th scope="row">Maine</th><td class="text-end">28.2%</td><td class="text-end">57,772</td><td class="text-end">205,142</td></tr>
<tr><th scope="row">Montana</th><td class="text-end">27.8%</td><td class="text-end">34,599</td><td class="text-end">124,474</td></tr>
<tr><th scope="row">South Carolina</th><td class="text-end">27.6%</td><td class="text-end">121,867</td><td class="text-end">442,323</td></tr>
<tr><th scope="row">Kansas</th><td class="text-end">26.5%</td><td class="text-end">83,990</td><td class="text-end">316,544</td></tr>
<tr><th scope="row">Mississippi</th><td class="text-end">25.8%</td><td class="text-end">79,197</td><td class="text-end">306,400</td></tr>
<tr><th scope="row">Georgia</th><td class="text-end">24.9%</td><td class="text-end">190,429</td><td class="text-end">766,045</td></tr>
<tr><th scope="row">Vermont</th><td class="text-end">24.8%</td><td class="text-end">51,598</td><td class="text-end">207,752</td></tr>
<tr><th scope="row">South Dakota</th><td class="text-end">23.0%</td><td class="text-end">28,359</td><td class="text-end">123,557</td></tr>
<tr><th scope="row">Utah</th><td class="text-end">18.5%</td><td class="text-end">25,792</td><td class="text-end">139,551</td></tr>
</tbody>
</table>
</details>

- Seventeen states sit above the 47.9% average and ten are below 30%.
- Texas has 31.8% on Medicaid/CHIP and 32.2% uninsured, so more uninsured patients than Medicaid patients.
- California, New York, Illinois, Washington and Florida hold 48.2% of all Medicaid/CHIP health-center patients.

To turn a share into a count for your own health center, try the [Medicaid what-if template]({{ site.baseurl }}/blog/medicaid-what-if-template/).

## Limits

- These are health-center patients, not statewide Medicaid enrollment.
- Each health center reports its own numbers to HRSA. This is one year only.
- Patients covered by both Medicare and Medicaid are counted as Medicare, so they are not in the Medicaid/CHIP figure.
- These are our own totals from HRSA's file, not HRSA's official statistics.

{% include casestudy_cta.html %}

</div>
