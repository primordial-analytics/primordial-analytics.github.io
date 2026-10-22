---
title: Oregon County Snapshot
subtitle: Worked example. Uninsured rates versus headcounts
description: "A worked example on public data (not a client project): uninsured rates and head counts for Oregon's 36 counties from Census SAHIE, with a look at CDC PLACES health measures."
layout: default
modal-id: 8
date: 2026-10-22
thumbnail: example-oregon-thumbnail.webp
kind: example
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

<div class="p-3 p-md-4 mb-5 rounded-3 bg-light border-start border-4" style="border-color: #645211 !important;" markdown="1">
**This is a worked example on public data, not a client project.** No client, patient, or organization is involved. Oregon is used because it is where Primordial Analytics is based; the same steps work for any state.
</div>

[sahie]: https://www.census.gov/programs-surveys/sahie.html
[places]: https://data.cdc.gov/Health-Pol/PLACES-Local-Data-for-Better-Health-County-Data-20/swc5-untb

## The question

*"We serve a few counties. Where are the people without insurance, and does it make more sense to focus on the counties with the highest rate or the counties with the most people?"*

It is a common planning question for a clinic or outreach program: a rate tells you how common something is, a headcount tells you how many people it is.

## The data

- **Census Small Area Health Insurance Estimates (SAHIE), 2024.** Published by the U.S. Census Bureau ([program page][sahie]), 2024 estimates from the 2026 release. County estimates of people under 65 without health insurance, each with a 90% margin of error. Downloaded 2026-10-22. The file has 402,786 rows across the country; filtered to Oregon counties, all ages under 65, all races, both sexes and all income levels, that leaves 36 rows (one per county).
- **CDC PLACES, county data, 2025 release.** Published by the Centers for Disease Control and Prevention ([data.cdc.gov][places]). Model-based estimates built from the 2023 Behavioral Risk Factor Surveillance System survey, with 95% confidence limits. Downloaded 2026-10-22. The file has 229,298 rows; for Oregon, the "crude prevalence" rows give all 36 counties for the measures used here.

Both are county-level summaries. Neither contains information about any individual.

## What was done

1. Filtered the SAHIE file to Oregon counties and the all-people, under-65 group, and built each county's 5-digit FIPS code (state plus county) to use as the join key.
2. Pulled the PLACES crude-prevalence rows for Oregon: adults 18-64 without insurance, diagnosed diabetes, and depression. Joined them to SAHIE on the same FIPS code. All 36 counties matched.
3. Ranked the counties by uninsured rate and plotted each with its 90% margin of error, next to the estimated number of uninsured people.
4. Compared the PLACES measures across counties with a simple correlation, sizing each dot by county population.

## What it shows

In Oregon in 2024, SAHIE estimates **223,111 people under 65 without insurance, 6.6% of the 3,393,289 in that age group**.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-oregon-uninsured.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-oregon-uninsured.webp" width="1200" height="1060" loading="lazy" alt="Dot plot with error bars ranking Oregon's 36 counties by estimated percent of people under 65 without health insurance in 2024. Morrow County is highest at 10.7 percent with about 1,077 people. Multnomah County is at 6.1 percent but has the most uninsured people, 40,808. Clackamas County has the lowest rate, 5.1 percent. Estimated uninsured head counts are listed at the right of each row."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Estimated percent of people under 65 without health insurance, by Oregon county, 2024. Bars show 90% margins of error. Source: U.S. Census Bureau SAHIE, downloaded 2026-10-22.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for this chart</summary>
<table class="table table-sm">
<caption>Estimated percent of people under 65 without health insurance, by Oregon county, 2024, highest rate first</caption>
<thead><tr><th scope="col">County</th><th scope="col" class="text-end">Percent uninsured</th><th scope="col" class="text-end">90% margin of error (percentage points)</th><th scope="col" class="text-end">People uninsured</th></tr></thead>
<tbody>
<tr><th scope="row">Morrow</th><td class="text-end">10.7%</td><td class="text-end">±1.3</td><td class="text-end">1,077</td></tr>
<tr><th scope="row">Hood River</th><td class="text-end">10.6%</td><td class="text-end">±1.1</td><td class="text-end">2,015</td></tr>
<tr><th scope="row">Malheur</th><td class="text-end">9.5%</td><td class="text-end">±1.1</td><td class="text-end">2,226</td></tr>
<tr><th scope="row">Marion</th><td class="text-end">9.1%</td><td class="text-end">±0.8</td><td class="text-end">25,815</td></tr>
<tr><th scope="row">Wasco</th><td class="text-end">8.8%</td><td class="text-end">±1.0</td><td class="text-end">1,795</td></tr>
<tr><th scope="row">Lake</th><td class="text-end">8.6%</td><td class="text-end">±1.1</td><td class="text-end">477</td></tr>
<tr><th scope="row">Umatilla</th><td class="text-end">8.5%</td><td class="text-end">±0.9</td><td class="text-end">5,388</td></tr>
<tr><th scope="row">Curry</th><td class="text-end">8.4%</td><td class="text-end">±1.0</td><td class="text-end">1,169</td></tr>
<tr><th scope="row">Tillamook</th><td class="text-end">8.4%</td><td class="text-end">±1.0</td><td class="text-end">1,594</td></tr>
<tr><th scope="row">Lincoln</th><td class="text-end">8.2%</td><td class="text-end">±0.9</td><td class="text-end">2,734</td></tr>
<tr><th scope="row">Wheeler</th><td class="text-end">8.1%</td><td class="text-end">±1.1</td><td class="text-end">72</td></tr>
<tr><th scope="row">Jefferson</th><td class="text-end">8.0%</td><td class="text-end">±0.9</td><td class="text-end">1,481</td></tr>
<tr><th scope="row">Josephine</th><td class="text-end">7.8%</td><td class="text-end">±0.9</td><td class="text-end">4,935</td></tr>
<tr><th scope="row">Klamath</th><td class="text-end">7.6%</td><td class="text-end">±0.9</td><td class="text-end">4,051</td></tr>
<tr><th scope="row">Clatsop</th><td class="text-end">7.5%</td><td class="text-end">±0.9</td><td class="text-end">2,250</td></tr>
<tr><th scope="row">Wallowa</th><td class="text-end">7.4%</td><td class="text-end">±0.9</td><td class="text-end">389</td></tr>
<tr><th scope="row">Coos</th><td class="text-end">7.3%</td><td class="text-end">±0.9</td><td class="text-end">3,248</td></tr>
<tr><th scope="row">Yamhill</th><td class="text-end">7.3%</td><td class="text-end">±0.8</td><td class="text-end">6,148</td></tr>
<tr><th scope="row">Harney</th><td class="text-end">7.3%</td><td class="text-end">±1.0</td><td class="text-end">384</td></tr>
<tr><th scope="row">Grant</th><td class="text-end">7.2%</td><td class="text-end">±0.9</td><td class="text-end">339</td></tr>
<tr><th scope="row">Lane</th><td class="text-end">6.9%</td><td class="text-end">±0.6</td><td class="text-end">20,224</td></tr>
<tr><th scope="row">Linn</th><td class="text-end">6.9%</td><td class="text-end">±0.8</td><td class="text-end">7,304</td></tr>
<tr><th scope="row">Jackson</th><td class="text-end">6.9%</td><td class="text-end">±0.7</td><td class="text-end">11,443</td></tr>
<tr><th scope="row">Douglas</th><td class="text-end">6.8%</td><td class="text-end">±0.8</td><td class="text-end">5,523</td></tr>
<tr><th scope="row">Union</th><td class="text-end">6.6%</td><td class="text-end">±0.8</td><td class="text-end">1,317</td></tr>
<tr><th scope="row">Gilliam</th><td class="text-end">6.6%</td><td class="text-end">±0.9</td><td class="text-end">88</td></tr>
<tr><th scope="row">Baker</th><td class="text-end">6.5%</td><td class="text-end">±0.8</td><td class="text-end">754</td></tr>
<tr><th scope="row">Multnomah</th><td class="text-end">6.1%</td><td class="text-end">±0.5</td><td class="text-end">40,808</td></tr>
<tr><th scope="row">Polk</th><td class="text-end">6.0%</td><td class="text-end">±0.7</td><td class="text-end">4,281</td></tr>
<tr><th scope="row">Benton</th><td class="text-end">5.9%</td><td class="text-end">±0.8</td><td class="text-end">4,429</td></tr>
<tr><th scope="row">Sherman</th><td class="text-end">5.9%</td><td class="text-end">±0.8</td><td class="text-end">87</td></tr>
<tr><th scope="row">Deschutes</th><td class="text-end">5.9%</td><td class="text-end">±0.6</td><td class="text-end">9,894</td></tr>
<tr><th scope="row">Columbia</th><td class="text-end">5.8%</td><td class="text-end">±0.7</td><td class="text-end">2,479</td></tr>
<tr><th scope="row">Crook</th><td class="text-end">5.6%</td><td class="text-end">±0.7</td><td class="text-end">1,132</td></tr>
<tr><th scope="row">Washington</th><td class="text-end">5.5%</td><td class="text-end">±0.4</td><td class="text-end">28,450</td></tr>
<tr><th scope="row">Clackamas</th><td class="text-end">5.1%</td><td class="text-end">±0.5</td><td class="text-end">17,311</td></tr>
</tbody>
</table>
</details>

- **The highest rates are in small counties.** Morrow County is highest at 10.7% (margin of error 1.3 points), followed by Hood River at 10.6% and Malheur at 9.5%. Morrow's estimate is about 1,077 people.
- **The biggest headcounts are in big counties.** Multnomah has the most uninsured people, 40,808, at a rate of 6.1% (margin 0.5). Washington County follows with 28,450 and Marion with 25,815.
- **Marion is both.** At 9.1% (margin 0.8) it is the fourth-highest rate and the third-highest headcount.
- **Headcounts are concentrated.** The ten counties with the most uninsured people hold 77.5% of Oregon's total; the top three (Multnomah, Washington, Marion) hold 42.6%. The four counties at 9% or higher hold 14.0%.
- **Not every rank is real.** Many neighboring counties have overlapping margins of error, so small differences in rank should not be over-read. Morrow's range (about 9.4% to 12.0%) is clearly above Multnomah's (5.6% to 6.6%).

The second source adds some health measures. Here is how the counties line up on PLACES's uninsured-adults estimate against diabetes and depression:

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-oregon-places.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-oregon-places.webp" width="1200" height="590" loading="lazy" alt="Two scatter plots with one dot per Oregon county, sized by population. The horizontal axis is the modeled percent of adults 18 to 64 without insurance. Left: diagnosed diabetes on the vertical axis, with a weak positive correlation of 0.28. Right: depression on the vertical axis, with a weak negative correlation of minus 0.29. Multnomah, Morrow and Malheur counties are labeled."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">PLACES modeled uninsured rate (adults 18-64) against diagnosed diabetes and depression, 36 Oregon counties. Source: CDC PLACES county data, 2025 release (BRFSS 2023), downloaded 2026-10-22.</figcaption>
</figure>

- Across the 36 counties, the PLACES uninsured rate has a **weak positive correlation with diabetes (+0.28)** and a **weak negative correlation with depression (-0.29)**.
- Using the SAHIE uninsured rate instead, the same comparison gives +0.45 for diabetes and -0.39 for depression. These are moderate at best.
- The two sources agree on the broad ordering of counties (correlation 0.77 between PLACES and SAHIE uninsured rates), though they measure slightly different groups (adults 18-64 versus everyone under 65) and not always the same value: for Morrow County, PLACES gives 17.8% and SAHIE 10.7%.

## Limits and caveats

- **Everything here is modeled.** SAHIE and PLACES are small-area estimates built from surveys plus statistical models, not head counts. That is why each comes with a margin of error. For the PLACES uninsured estimate, the median 95% confidence interval across Oregon counties is 4.2 percentage points wide.
- **Correlation across 36 counties is not cause.** Counties are not people. A weak link at the county level does not tell you anything about whether insurance affects diabetes or depression for an individual. The negative link with depression is a reminder: a survey measure of depression can reflect who has been seen and asked as much as who is struggling. This data cannot sort that out.
- **Model effects.** PLACES estimates use survey responses together with demographics and county poverty rates, so patterns between counties can be partly a product of the model rather than independent measurement.
- **Dated.** SAHIE is for 2024 and PLACES for 2023 survey data, so neither captures coverage changes since then.
- **Different definitions.** SAHIE covers people under 65; the PLACES measure covers adults 18-64. Do not mix the two in a single number.
- **Not in this example.** PLACES also has social-needs measures (food insecurity, housing insecurity, transportation), but the 2025 release has no values for Oregon, so they are left out.

## Want the same for your own area?

If your organization serves a particular county, region or set of ZIP codes, the same analysis can be re-run for your service area in the same way: rates and headcounts side by side, with the uncertainty shown. Add your own numbers (such as where your patients live) and it gets more useful. It is free and starts with a short conversation. See [free data help for community health organizations]({{ site.baseurl }}/community-health-data-help/).

{% include casestudy_cta.html %}

</div>
