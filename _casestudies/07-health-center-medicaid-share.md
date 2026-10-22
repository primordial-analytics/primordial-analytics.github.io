---
title: Medicaid at Health Centers
subtitle: Worked example. Who relies on Medicaid, state by state
description: "A worked example on public data (not a client project): the share of health-center patients covered by Medicaid or CHIP in each state, from HRSA's 2025 Uniform Data System."
layout: default
modal-id: 7
date: 2026-10-22
thumbnail: example-uds-thumbnail.webp
kind: example
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

<div class="p-3 p-md-4 mb-5 rounded-3 bg-light border-start border-4" style="border-color: #645211 !important;" markdown="1">
**This is a worked example on public data, not a client project.** No client, patient, or organization is involved. It shows what a small, free analysis could look like, using numbers anyone can download.
</div>

[hrsa-download]: https://data.hrsa.gov/data/download
[hhs]: https://www.hhs.gov/press-room/hrsa-health-centers-serve-record-32-million-patients.html
[snapshot]: https://data.hrsa.gov/tools/data-reporting/data-snapshot?year=2025

## The question

*"Our board keeps hearing that Medicaid changes will hit health centers hard. How much of a health center's patient base does Medicaid actually cover, and how does our state compare?"*

It is a fair thing to wonder before you build a budget scenario. Before modeling your own patients, it helps to know where you sit among your peers.

## The data

- **Name:** Uniform Data System (UDS), awardee-level file for calendar year 2025 (`H80-2025.xlsx`), Table 4 (patients by insurance) and the health center info sheet.
- **Publisher:** the Health Resources and Services Administration (HRSA), on its [Data Downloads page][hrsa-download].
- **Vintage:** reporting year 2025, as refreshed by HRSA on 2026-05-07. Downloaded 2026-10-22.
- **Shape:** one row per HRSA health center awardee, 1,356 in all, with patient counts by insurance type. It is organization-level counts, not patient-level records, so there is no protected health information in it.

## What was done

1. Read the two sheets that matter (Table 4 and the info sheet) and joined them on each awardee's ID and grant number.
2. Added up each awardee's patients, its Medicaid/CHIP patients, and its uninsured patients. "Medicaid/CHIP" follows HRSA's own definition: Table 4 line 8 (Medicaid) plus line 10b (other public insurance, CHIP).
3. Treated cells that HRSA marks with a dash as zero (a single dash means no data entered; two dashes mean a suppressed count of 1 to 15, so treating those as zero gives a slight lower bound). Fewer than 25 awardees have a dash in a Medicaid or total-patients column, and many more have one on the line 10b (other public insurance) columns. This barely matters: the national shares still come out at the published values (see step 5).
4. Summed by state, then kept the 48 jurisdictions (states, DC and Puerto Rico) with at least 100,000 health-center patients for the state comparison. The eleven left out are small (American Samoa, Delaware, Micronesia, Guam, Marshall Islands, North Dakota, New Hampshire, Northern Mariana Islands, Palau, the Virgin Islands and Wyoming).
5. Checked the national result against the published one. [HHS reported][hhs] a record 32.7 million health-center patients for 2025, and HRSA's [Data Snapshot for 2025][snapshot] gives 47.92% on Medicaid/CHIP and 17.21% uninsured. The file gives 32.75 million patients, 47.92% and 17.21%.
6. Published only state totals. The source file also lists health center names and contact people, and none of that is reproduced here.

## What it shows

Across all 1,356 awardees, **32,746,371 patients** were counted in 2025. Of those, **15,692,019 (47.9%)** were covered by Medicaid or CHIP and **5,634,320 (17.2%)** were uninsured.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-uds-medicaid-share.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-uds-medicaid-share.webp" width="1200" height="1120" loading="lazy" alt="Horizontal bar chart of 48 states and territories ranked by the share of health-center patients covered by Medicaid or CHIP in 2025. California is highest at 71.8 percent, Oregon second at 61.4 percent, Puerto Rico 60.1 percent. Utah is lowest at 18.5 percent. A dashed line marks the all-health-center average of 47.9 percent. Oregon is highlighted."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Medicaid/CHIP share of health-center patients by state, 2025. Oregon is highlighted. Source: HRSA UDS, calendar year 2025, downloaded 2026-10-22.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<table class="table table-sm">
<caption>Medicaid/CHIP share of health-center patients by state, 2025, highest to lowest</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Medicaid/CHIP share of patients</th><th scope="col" class="text-end">Medicaid/CHIP patients</th><th scope="col" class="text-end">All patients</th></tr></thead>
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

- **The spread is wide.** California is highest at 71.8% (4,235,855 of 5,900,535 patients). Utah is lowest at 18.5%. Seventeen of the 48 jurisdictions sit above the 47.9% average and ten are below 30%.
- **Oregon is second.** Among the 48 jurisdictions, Oregon health centers come second after California: 61.4% of their patients (270,052 of 440,152) are covered by Medicaid or CHIP. Another 8.3% (36,519) are uninsured.
- **Texas is the other kind of picture.** Texas health centers have 31.8% of patients on Medicaid/CHIP (604,229 of 1,898,301) and 32.2% uninsured (611,157), so more uninsured patients than Medicaid patients.

A share tells you how exposed a patient base is. A count tells you how many people are in it. They point at different places:

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-uds-top-states.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-uds-top-states.webp" width="1200" height="620" loading="lazy" alt="Horizontal bar chart of the ten states with the most Medicaid or CHIP health-center patients in 2025. California has 4.24 million, New York 1.21 million, Illinois 0.77 million, Washington 0.70 million, Florida 0.63 million, Texas 0.60 million, then Ohio, Pennsylvania, Massachusetts and Arizona at 0.36 to 0.44 million."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">The ten states with the most Medicaid/CHIP health-center patients, 2025. Source: HRSA UDS, calendar year 2025, downloaded 2026-10-22.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<table class="table table-sm">
<caption>The ten states with the most Medicaid/CHIP health-center patients, 2025</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Medicaid/CHIP patients</th></tr></thead>
<tbody>
<tr><th scope="row">California</th><td class="text-end">4,235,855</td></tr>
<tr><th scope="row">New York</th><td class="text-end">1,211,258</td></tr>
<tr><th scope="row">Illinois</th><td class="text-end">774,676</td></tr>
<tr><th scope="row">Washington</th><td class="text-end">704,637</td></tr>
<tr><th scope="row">Florida</th><td class="text-end">634,910</td></tr>
<tr><th scope="row">Texas</th><td class="text-end">604,229</td></tr>
<tr><th scope="row">Ohio</th><td class="text-end">444,083</td></tr>
<tr><th scope="row">Pennsylvania</th><td class="text-end">372,010</td></tr>
<tr><th scope="row">Massachusetts</th><td class="text-end">363,104</td></tr>
<tr><th scope="row">Arizona</th><td class="text-end">357,222</td></tr>
</tbody>
</table>
</details>

California, New York, Illinois, Washington and Florida together hold **48.2%** of all Medicaid/CHIP health-center patients nationally. Oregon's high share is a smaller number of people (270,052) than in states such as Illinois (774,676) or Washington (704,637).

If you want one planning number: for any health center, a 10% drop in Medicaid/CHIP patients is just 10% of that count. For Oregon health centers overall it would be 27,005 patients. That is arithmetic, not a forecast. Where those patients go (to other coverage, or to uninsured) is the part that needs your own data, and it is what the [Medicaid what-if template]({{ site.baseurl }}/blog/medicaid-what-if-template/) is for.

## Limits and caveats

- **These are health-center patients, not the whole state.** UDS counts people who used HRSA-funded health centers in 2025. It says nothing about statewide Medicaid enrollment, or about people who did not use a health center.
- **The data is self-reported.** Each awardee reports its own numbers to HRSA. HRSA checks them, but small errors are possible.
- **One year, one snapshot.** This looks at 2025 only, so it says nothing about what is changing now.
- **Dashes treated as zero.** See step 3. The national shares still match the published ones.
- **Dual-eligible patients are counted as Medicare.** Patients covered by both Medicare and Medicaid appear on HRSA's Medicare line, not the Medicaid line, so "Medicaid/CHIP" here does not count them.
- **Reprocessing is on us.** HRSA says that any manipulation or reprocessing of its data is the sole responsibility of the user. These figures are our own aggregation of the file, not HRSA's official statistics.

## Want the same for your own area?

If you run or work with a community health organization, a similar look can be done for your state, your service area, or your own numbers: peer comparisons, a chart for a board packet, a Medicaid what-if on your own patient data. It is free and starts with a short conversation. See [free data help for community health organizations]({{ site.baseurl }}/community-health-data-help/).

{% include casestudy_cta.html %}

</div>
