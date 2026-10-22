---
title: Uninsured Rates by County
subtitle: Where uninsured rates are highest
description: "Public data only. No patient information."
lead: "Public data only. No patient information."
layout: default
modal-id: 8
date: 2026-10-22
thumbnail: example-county-thumbnail.webp
kind: example
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

[sahie]: https://www.census.gov/programs-surveys/sahie.html
[places]: https://data.cdc.gov/Health-Pol/PLACES-Local-Data-for-Better-Health-County-Data-20/swc5-untb

## Question

Where are uninsured rates highest across the country, and do two public sources agree?

## Data

- **Census SAHIE, 2024.** County estimates of people under 65 without health insurance, with 90% margins of error ([program page][sahie]).
- **CDC PLACES, 2025 release.** Modeled county estimates of adults 18-64 without insurance, from 2023 survey data ([data.cdc.gov][places]).

Both downloaded 2026-10-22.

## What we did

We joined the two files on the 5-digit county code. SAHIE has 3,143 counties with an estimate, and 2,955 of them match PLACES, whose 2025 release has no values for Kentucky, Pennsylvania or one Texas county. We then grouped and ranked counties by rate and compared the two sources.

## What it shows

SAHIE estimates **26,698,044 people under 65 without insurance, 9.8% of 272,330,940**. Across all 3,143 counties, the typical (median) county is also at 9.8%.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-county-uninsured.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-county-uninsured.webp" width="1200" height="620" loading="lazy" alt="Two charts. Left: histogram of uninsured rates across 3,143 U.S. counties, peaking near 8 percent with a median of 9.8 percent and a long tail to 38.5 percent. Right: dot plot with margins of error of the 15 highest county rates, led by Gaines County, Texas at 38.5 percent, with 13 of the 15 in Texas."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Estimated percent of people under 65 without insurance, by county, 2024. Bars show 90% margins of error. Source: U.S. Census Bureau SAHIE.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data tables for this chart</summary>
<table class="table table-sm">
<caption>U.S. counties by uninsured rate, 2024</caption>
<thead><tr><th scope="col">Uninsured rate</th><th scope="col" class="text-end">Counties</th><th scope="col" class="text-end">Share of counties</th><th scope="col" class="text-end">People uninsured</th><th scope="col" class="text-end">Share of uninsured people</th></tr></thead>
<tbody>
<tr><th scope="row">Under 5%</th><td class="text-end">109</td><td class="text-end">3.5%</td><td class="text-end">992,299</td><td class="text-end">3.7%</td></tr>
<tr><th scope="row">5% to under 10%</th><td class="text-end">1,499</td><td class="text-end">47.7%</td><td class="text-end">10,245,945</td><td class="text-end">38.4%</td></tr>
<tr><th scope="row">10% to under 15%</th><td class="text-end">1,043</td><td class="text-end">33.2%</td><td class="text-end">9,157,833</td><td class="text-end">34.3%</td></tr>
<tr><th scope="row">15% to under 20%</th><td class="text-end">357</td><td class="text-end">11.4%</td><td class="text-end">3,586,247</td><td class="text-end">13.4%</td></tr>
<tr><th scope="row">20% to under 25%</th><td class="text-end">108</td><td class="text-end">3.4%</td><td class="text-end">2,258,984</td><td class="text-end">8.5%</td></tr>
<tr><th scope="row">25% or more</th><td class="text-end">27</td><td class="text-end">0.9%</td><td class="text-end">456,736</td><td class="text-end">1.7%</td></tr>
</tbody>
</table>
<table class="table table-sm">
<caption>The 15 counties with the highest uninsured rates, 2024</caption>
<thead><tr><th scope="col">County</th><th scope="col" class="text-end">Percent uninsured</th><th scope="col" class="text-end">90% margin of error (points)</th><th scope="col" class="text-end">People uninsured</th><th scope="col" class="text-end">People under 65</th></tr></thead>
<tbody>
<tr><th scope="row">Gaines, TX</th><td class="text-end">38.5%</td><td class="text-end">±2.5</td><td class="text-end">7,913</td><td class="text-end">20,533</td></tr>
<tr><th scope="row">Holmes, OH</th><td class="text-end">33.4%</td><td class="text-end">±2.8</td><td class="text-end">12,598</td><td class="text-end">37,734</td></tr>
<tr><th scope="row">Lagrange, IN</th><td class="text-end">31.3%</td><td class="text-end">±2.7</td><td class="text-end">10,862</td><td class="text-end">34,724</td></tr>
<tr><th scope="row">Presidio, TX</th><td class="text-end">29.6%</td><td class="text-end">±2.7</td><td class="text-end">1,261</td><td class="text-end">4,261</td></tr>
<tr><th scope="row">Moore, TX</th><td class="text-end">28.5%</td><td class="text-end">±2.4</td><td class="text-end">5,418</td><td class="text-end">18,992</td></tr>
<tr><th scope="row">Ochiltree, TX</th><td class="text-end">27.6%</td><td class="text-end">±2.4</td><td class="text-end">2,292</td><td class="text-end">8,310</td></tr>
<tr><th scope="row">Parmer, TX</th><td class="text-end">27.2%</td><td class="text-end">±2.3</td><td class="text-end">2,207</td><td class="text-end">8,100</td></tr>
<tr><th scope="row">Edwards, TX</th><td class="text-end">27.2%</td><td class="text-end">±2.4</td><td class="text-end">255</td><td class="text-end">939</td></tr>
<tr><th scope="row">Starr, TX</th><td class="text-end">27.1%</td><td class="text-end">±2.2</td><td class="text-end">15,562</td><td class="text-end">57,390</td></tr>
<tr><th scope="row">Crockett, TX</th><td class="text-end">26.8%</td><td class="text-end">±2.3</td><td class="text-end">583</td><td class="text-end">2,174</td></tr>
<tr><th scope="row">San Saba, TX</th><td class="text-end">26.8%</td><td class="text-end">±2.2</td><td class="text-end">1,030</td><td class="text-end">3,839</td></tr>
<tr><th scope="row">Zapata, TX</th><td class="text-end">26.8%</td><td class="text-end">±2.2</td><td class="text-end">3,095</td><td class="text-end">11,565</td></tr>
<tr><th scope="row">Hidalgo, TX</th><td class="text-end">26.7%</td><td class="text-end">±1.1</td><td class="text-end">209,777</td><td class="text-end">785,748</td></tr>
<tr><th scope="row">Cameron, TX</th><td class="text-end">26.6%</td><td class="text-end">±1.4</td><td class="text-end">95,700</td><td class="text-end">359,179</td></tr>
<tr><th scope="row">Dallam, TX</th><td class="text-end">26.4%</td><td class="text-end">±2.8</td><td class="text-end">1,757</td><td class="text-end">6,648</td></tr>
</tbody>
</table>
</details>

- Rates run from 2.4% to 38.5%. Nearly half of counties (1,499) fall between 5% and 10%.
- 135 counties are at 20% or more, and 116 of them are in Texas. Gaines County, Texas is highest at 38.5% (margin 2.5 points).
- Headcounts point elsewhere. Harris County, Texas has the most uninsured people, 981,214, at 22.8%. Los Angeles County is second with 671,007, at 8.3%.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-county-places.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-county-places.webp" width="1200" height="640" loading="lazy" alt="Scatter plot with one dot per county, comparing the SAHIE uninsured rate on the horizontal axis with the PLACES adult uninsured rate on the vertical axis for 2,955 counties. Dots rise together with a correlation of 0.79, scattered around a dashed line of equal rates."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">SAHIE (under 65) against PLACES (adults 18-64) uninsured rates, 2,955 counties. Sources: Census SAHIE 2024; CDC PLACES 2025 release.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<table class="table table-sm">
<caption>Agreement between SAHIE and PLACES uninsured rates across matched counties</caption>
<thead><tr><th scope="col">Measure</th><th scope="col" class="text-end">Value</th></tr></thead>
<tbody>
<tr><th scope="row">Counties matched</th><td class="text-end">2,955</td></tr>
<tr><th scope="row">Correlation</th><td class="text-end">0.79</td></tr>
<tr><th scope="row">Rank correlation (Spearman)</th><td class="text-end">0.85</td></tr>
<tr><th scope="row">Correlation, 483 counties with 100,000+ people under 65</th><td class="text-end">0.86</td></tr>
<tr><th scope="row">Median county rate, SAHIE (2,955 matched counties)</th><td class="text-end">10.1%</td></tr>
<tr><th scope="row">Median county rate, PLACES</th><td class="text-end">9.9%</td></tr>
</tbody>
</table>
</details>

- The two sources rank counties alike: correlation **0.79**, and 0.86 among the 483 counties with 100,000 or more people under 65.

## Limits

- Both sources are modeled estimates, not counts. The 15 highest rates have margins of 1.1 to 2.8 points, so close ranks are not firm.
- The groups differ (everyone under 65, adults 18-64), and the data is from 2023 and 2024.

{% include casestudy_cta.html %}

</div>
