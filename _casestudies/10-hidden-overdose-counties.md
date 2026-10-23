---
title: Overdose Rates Where Counts Are Hidden
subtitle: Estimating the county counts the CDC file hides
description: "Public data only. No patient information."
lead: "Public data only. No patient information."
layout: default
modal-id: 10
date: 2026-10-22
thumbnail: example-overdose-thumbnail.webp
kind: example
persona: "For small health departments"
need: "Defensible county overdose death rates with uncertainty for the counties where the national file hides the count."
---

<div class="container py-5" style="max-width: 800px;" markdown="1">

[nchs-county]: https://data.cdc.gov/d/gb4e-yj24
[nchs-state]: https://data.cdc.gov/d/xkb8-kh2a
[sahie]: https://www.census.gov/programs-surveys/sahie.html
[quick]: https://www.cdc.gov/pcd/issues/2019/18_0441.htm
[code]: https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/10-hidden-overdose-counties

## Who this is for

A health department with one epidemiologist, or half of one. Someone has asked where naloxone, syringe services and opioid-settlement money should go, and the CDC county file is blank for 1,626 of 3,142 counties. This is an example built on public data, not a client engagement.

## Question

For counties where the file hides the count, what overdose death rate is defensible, with what uncertainty, and does the method pass a check we can run?

## Data

- **CDC NCHS provisional county overdose deaths** ([data.cdc.gov][nchs-county]), 12 months ending March 2026, as of 2026-10-04. Counts of 1 to 9 are suppressed; 0 and 10 or more are published. That gives 3,142 counties: 1,514 published (554 zeros), 1,626 suppressed at 1 to 9, and 2 suppressed for data quality.
- **NCHS state totals** for the same window ([data.cdc.gov][nchs-state]), which are not suppressed.
- **Census** 2024 county population, county boundaries, and 2024 [SAHIE][sahie] uninsured and low-income shares.

All aggregate, downloaded 2026-10-22.

## Method

A hidden cell says the count is at least 1 and at most 9, so the county is neither a zero nor a county with 10 or more. Published counts enter a Poisson model as exact values; a suppressed cell enters as the probability of 1 to 9 deaths at that county's rate. [Quick (2019)][quick] did this for suppressed CDC WONDER deaths.

Each county's log rate is an intercept, four county measures (density, uninsured share, low-income share, urban-rural class), a state effect, and a spatial effect that lets neighbors inform each other (a Leroux CAR prior). The fit has 0 divergences and a largest R-hat of 1.02; effective sample size is at least 2,172 for county rates and 259 for hyperparameters.

A state's total minus its published county counts is roughly the deaths in its suppressed counties. The files do not always agree, so we use that difference as a soft constraint only (standard deviation 5% of the state total), in the 37 states where it falls between 1 and 9 per hidden county and none has a data-quality county. A hidden county's own data say only "1 to 9," so its estimate rests mostly on covariates, neighbors and the state total.

## What it shows

The 1,626 hidden counties hold 42.2 million people (12.4%). The model puts about 5,800 deaths in them. Its 90% interval, 5,670 to 5,965, holds only if the model is right, and the state check below shows it is too narrow. Widened until 90% of checked states fall inside, the range is 5,400 to 6,200 (model variants give 5,818 to 5,880). The median rate is 13.4 per 100,000, against 20.6 in counties with 10 or more deaths.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-overdose-map.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-overdose-map.webp" width="1200" height="820" loading="lazy" alt="Map of the United States with every county shaded by its estimated overdose death rate for the 12 months ending March 2026. Rates run from under 10 per 100,000 across much of the Plains to 45 or more in 56 counties, mostly in New Mexico (14) and West Virginia (13), with a few each in California, Colorado and Kentucky. Counties whose count the national file hides are hatched and still shaded with the model estimate: 1,626 at 1 to 9 deaths, plus 2 more suppressed for data quality."><span class="visually-hidden"> (open full-size map)</span></a>
<figcaption class="small text-muted mt-2">Estimated overdose deaths per 100,000 people by county, 12 months ending March 2026. Hatched counties are blank in the national file (1,626 at 1 to 9 deaths, plus 2 for data quality). Tap the image to open it full size. Source: CDC NCHS provisional counts; Primordial Analytics model.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Summary table for this map</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Counties by NCHS urban-rural class, with suppression and median rates per 100,000. Over half of published noncore counties report zero deaths (439 of 493), which is why their median including zeros is 0.0.</caption>
<thead><tr><th scope="col">Urban-rural class</th><th scope="col" class="text-end">Counties</th><th scope="col" class="text-end">Suppressed (1 to 9)</th><th scope="col" class="text-end">Share suppressed</th><th scope="col" class="text-end">Median model rate, suppressed counties</th><th scope="col" class="text-end">Median published rate, including zeros</th><th scope="col" class="text-end">Median published rate, 10+ deaths only</th></tr></thead>
<tbody>
<tr><th scope="row">Large central metro</th><td class="text-end">68</td><td class="text-end">0</td><td class="text-end">0%</td><td class="text-end">n/a</td><td class="text-end">22.9</td><td class="text-end">22.9</td></tr>
<tr><th scope="row">Large fringe metro</th><td class="text-end">368</td><td class="text-end">127</td><td class="text-end">35%</td><td class="text-end">12.5</td><td class="text-end">14.6</td><td class="text-end">15.1</td></tr>
<tr><th scope="row">Medium metro</th><td class="text-end">372</td><td class="text-end">124</td><td class="text-end">33%</td><td class="text-end">14.2</td><td class="text-end">20.2</td><td class="text-end">21.0</td></tr>
<tr><th scope="row">Small metro</th><td class="text-end">358</td><td class="text-end">135</td><td class="text-end">38%</td><td class="text-end">12.9</td><td class="text-end">17.4</td><td class="text-end">19.8</td></tr>
<tr><th scope="row">Micropolitan</th><td class="text-end">641</td><td class="text-end">398</td><td class="text-end">62%</td><td class="text-end">13.4</td><td class="text-end">22.1</td><td class="text-end">26.0</td></tr>
<tr><th scope="row">Noncore</th><td class="text-end">1,335</td><td class="text-end">842</td><td class="text-end">63%</td><td class="text-end">13.4</td><td class="text-end">0.0</td><td class="text-end">35.2</td></tr>
</tbody>
</table>
</div>
<p class="small text-muted">The full list of counties is in the download below.</p>
</details>

- The model interval (a median 13.6 per 100,000 wide) is for the rate and the hard bounds (39.0 wide) are for the count, so narrower is not better. A county expecting 0.5 deaths can still record one: in 246 hidden counties the model median is outside the bounds, in 77 the whole interval is below the lower bound.
- 87 hidden counties have better than an 80% chance of a rate above their state's, and 78 better than 50% of being in the top decile (above 27.3).
- A published zero is not safe. The 554 zero counties have a median population of 5,948 and a modelled median rate of 9.4; in 146 the chance of exceeding the state rate is above 20%.
- Do not rank: a hidden county's rank interval spans a median 1,819 places of 3,142.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-overdose-intervals.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-overdose-intervals.webp" width="1200" height="690" loading="lazy" alt="Two charts. Left: scatter of the width of the model 90 percent interval against the width of the hard 1-to-9 bounds for 1,626 suppressed counties, on log axes. Nearly all points fall below the equal-width line, with the model interval about 40 percent as wide at the median. Right: for the twelve most populous suppressed Kentucky counties, a pale bar for the hard bounds and a dark dot and line for the model median and 90 percent interval, eleven with medians of 11 to 18 deaths per 100,000 and Knox higher, at 31 (20 to 47)."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Hard bounds on the observed count against the model's 90% interval for the underlying rate; they measure different things. Tap the image to open it full size. Source: CDC NCHS; Primordial Analytics model.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data table for the Kentucky example</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Twelve most populous suppressed Kentucky counties, rates per 100,000</caption>
<thead><tr><th scope="col">County</th><th scope="col" class="text-end">Population</th><th scope="col" class="text-end">Hard bounds</th><th scope="col" class="text-end">Model median</th><th scope="col" class="text-end">Model 90% interval</th><th scope="col" class="text-end">Chance above state rate</th></tr></thead>
<tbody>
<tr><th scope="row">Oldham</th><td class="text-end">70,525</td><td class="text-end">1.4 to 12.8</td><td class="text-end">11.1</td><td class="text-end">7.1 to 16.9</td><td class="text-end">0%</td></tr>
<tr><th scope="row">McCracken</th><td class="text-end">67,550</td><td class="text-end">1.5 to 13.3</td><td class="text-end">14.5</td><td class="text-end">9.6 to 21.3</td><td class="text-end">1%</td></tr>
<tr><th scope="row">Scott</th><td class="text-end">61,700</td><td class="text-end">1.6 to 14.6</td><td class="text-end">15.1</td><td class="text-end">10.5 to 21.9</td><td class="text-end">2%</td></tr>
<tr><th scope="row">Nelson</th><td class="text-end">48,706</td><td class="text-end">2.1 to 18.5</td><td class="text-end">14.6</td><td class="text-end">9.3 to 21.7</td><td class="text-end">2%</td></tr>
<tr><th scope="row">Barren</th><td class="text-end">45,609</td><td class="text-end">2.2 to 19.7</td><td class="text-end">16.1</td><td class="text-end">10.0 to 24.3</td><td class="text-end">6%</td></tr>
<tr><th scope="row">Hopkins</th><td class="text-end">45,218</td><td class="text-end">2.2 to 19.9</td><td class="text-end">14.9</td><td class="text-end">9.2 to 22.9</td><td class="text-end">4%</td></tr>
<tr><th scope="row">Henderson</th><td class="text-end">44,175</td><td class="text-end">2.3 to 20.4</td><td class="text-end">17.7</td><td class="text-end">11.8 to 26.4</td><td class="text-end">12%</td></tr>
<tr><th scope="row">Calloway</th><td class="text-end">38,975</td><td class="text-end">2.6 to 23.1</td><td class="text-end">15.8</td><td class="text-end">9.7 to 25.2</td><td class="text-end">8%</td></tr>
<tr><th scope="row">Graves</th><td class="text-end">36,821</td><td class="text-end">2.7 to 24.4</td><td class="text-end">16.5</td><td class="text-end">10.3 to 25.2</td><td class="text-end">8%</td></tr>
<tr><th scope="row">Muhlenberg</th><td class="text-end">30,512</td><td class="text-end">3.3 to 29.5</td><td class="text-end">13.7</td><td class="text-end">8.6 to 21.6</td><td class="text-end">2%</td></tr>
<tr><th scope="row">Meade</th><td class="text-end">30,442</td><td class="text-end">3.3 to 29.6</td><td class="text-end">15.1</td><td class="text-end">8.9 to 24.9</td><td class="text-end">7%</td></tr>
<tr><th scope="row">Knox</th><td class="text-end">29,657</td><td class="text-end">3.4 to 30.3</td><td class="text-end">31.3</td><td class="text-end">19.9 to 46.8</td><td class="text-end">85%</td></tr>
</tbody>
</table>
</div>
</details>

### Does it hold up?

Three checks, none on a truly suppressed cell, because no published cell is 1 to 9.

- **State totals.** A version of the model that never saw the state differences put 5,334 deaths in the hidden counties of the 37 plausible states, against 5,441 from the totals. 25 of the 37 agree within 20%, and the log correlation is 0.959. A naive rule comes close: hidden-county counts alone correlate 0.90 with the difference, and times the average per hidden county they put 18 of 37 within 20%. The 90% interval contains the state difference in only 22 of 37 states (59%), so the intervals are too narrow.
- **Hide and score.** We treated every count under 30 as suppressed, refit, and scored the 537 counties with a known count of 10 to 29. Counts of 1 to 9 cannot be scored, so this tests only the upper range and is not a calibration estimate. The spatial model's ranked probability score (lower is better) is 3.04, against 3.20 for the same model without the spatial term (4.8% lower) and 3.37 for a Poisson-gamma model with no covariates and no state constraint. Its 90% interval holds 88% of true counts, against 87% without it. Its average miss is 4.16 deaths, against 5.20 for splitting the state difference by population and 4.63 for the range midpoint.
- **Forecast.** Fit to March 2025, predict the 1,514 counties published for March 2026, using each state's 2026 total. The spatial and Poisson-gamma models score 3.25 and 3.35 (CRPS). On the 1,175 counties published in both years, the average miss is 5.66 for the spatial model, 5.75 for Poisson-gamma and 6.04 for last year's count with the same state adjustment.

Dropping the covariates moves a hidden county's rate by a median 11.3%, dropping the spatial term 9.4%.

<figure class="my-4">
<a href="{{ site.baseurl }}/img/case_studies/example-overdose-validation.webp"><img class="img-fluid" src="{{ site.baseurl }}/img/case_studies/example-overdose-validation.webp" width="1200" height="660" loading="lazy" alt="Two charts. Left: for each state, the model's total deaths in suppressed counties (fit without the state totals) against the state total minus published county counts, on log axes. States where the difference is plausible lie close to the equal line, with a log correlation of 0.959. The 37 states where the difference is plausible lie close to it, though the 90 percent interval contains the state value in only 22 of them. The seven excluded states that are plotted, such as California, all lie below it; three states with negative differences are not plotted. Right: share of scored true counts (counties with 10 to 29 deaths) inside intervals of nominal level 50 to 95 percent, for the spatial model, the same model without a spatial term, and a Poisson-gamma model with no covariates or constraint. All three track the equal line slightly below it, with 88 percent inside the 90 percent interval for the spatial model."><span class="visually-hidden"> (open full-size chart)</span></a>
<figcaption class="small text-muted mt-2">Left: modelled deaths in suppressed counties against the state residual. Right: calibration when counts under 30 are hidden, scored on counties with 10 to 29 deaths. Tap the image to open it full size. Source: CDC NCHS; Primordial Analytics.</figcaption>
</figure>
<details class="mt-3" markdown="0">
<summary>Data tables for these charts</summary>
<div class="table-responsive">
<table class="table table-sm">
<caption>Hide-and-score results on counties with true counts of 10 to 19 (under 20) or 10 to 29 (under 30): average miss in deaths per county (MAE), ranked probability score (RPS) and 90% interval coverage</caption>
<thead><tr><th scope="col">Method</th><th scope="col" class="text-end">MAE, under 20</th><th scope="col" class="text-end">RPS, under 20</th><th scope="col" class="text-end">90% coverage, under 20</th><th scope="col" class="text-end">MAE, under 30</th><th scope="col" class="text-end">RPS, under 30</th><th scope="col" class="text-end">90% coverage, under 30</th></tr></thead>
<tbody>
<tr><th scope="row">Spatial model (this page)</th><td class="text-end">3.30</td><td class="text-end">2.38</td><td class="text-end">88%</td><td class="text-end">4.16</td><td class="text-end">3.04</td><td class="text-end">88%</td></tr>
<tr><th scope="row">Same model, no spatial term</th><td class="text-end">3.48</td><td class="text-end">2.53</td><td class="text-end">87%</td><td class="text-end">4.34</td><td class="text-end">3.20</td><td class="text-end">87%</td></tr>
<tr><th scope="row">Poisson-gamma, no covariates, no state constraint</th><td class="text-end">3.68</td><td class="text-end">2.65</td><td class="text-end">87%</td><td class="text-end">4.63</td><td class="text-end">3.37</td><td class="text-end">90%</td></tr>
<tr><th scope="row">State difference split by population</th><td class="text-end">4.06</td><td class="text-end">n/a</td><td class="text-end">n/a</td><td class="text-end">5.20</td><td class="text-end">n/a</td><td class="text-end">n/a</td></tr>
<tr><th scope="row">Midpoint of the hidden range</th><td class="text-end">3.46</td><td class="text-end">n/a</td><td class="text-end">n/a</td><td class="text-end">4.63</td><td class="text-end">n/a</td><td class="text-end">n/a</td></tr>
</tbody>
</table>
</div>
<div class="table-responsive">
<table class="table table-sm">
<caption>Deaths in suppressed counties by state: the state total minus published county counts, and the model's total (90% interval)</caption>
<thead><tr><th scope="col">State</th><th scope="col" class="text-end">Suppressed counties</th><th scope="col" class="text-end">State difference</th><th scope="col" class="text-end">Model total (90% interval)</th><th scope="col">Difference plausible?</th></tr></thead>
<tbody>
<tr><th scope="row">AK</th><td class="text-end">14</td><td class="text-end">50</td><td class="text-end">38 (28 to 49)</td><td>yes</td></tr>
<tr><th scope="row">AL</th><td class="text-end">38</td><td class="text-end">102</td><td class="text-end">150 (129 to 174)</td><td>yes</td></tr>
<tr><th scope="row">AR</th><td class="text-end">53</td><td class="text-end">169</td><td class="text-end">160 (137 to 184)</td><td>yes</td></tr>
<tr><th scope="row">AZ</th><td class="text-end">1</td><td class="text-end">94</td><td class="text-end">2 (1 to 5)</td><td>no</td></tr>
<tr><th scope="row">CA</th><td class="text-end">11</td><td class="text-end">582</td><td class="text-end">45 (35 to 56)</td><td>no</td></tr>
<tr><th scope="row">CO</th><td class="text-end">35</td><td class="text-end">156</td><td class="text-end">118 (99 to 138)</td><td>yes</td></tr>
<tr><th scope="row">FL</th><td class="text-end">21</td><td class="text-end">228</td><td class="text-end">76 (61 to 91)</td><td>no</td></tr>
<tr><th scope="row">GA</th><td class="text-end">96</td><td class="text-end">315</td><td class="text-end">323 (292 to 357)</td><td>yes</td></tr>
<tr><th scope="row">IA</th><td class="text-end">63</td><td class="text-end">150</td><td class="text-end">154 (136 to 174)</td><td>yes</td></tr>
<tr><th scope="row">ID</th><td class="text-end">26</td><td class="text-end">42</td><td class="text-end">75 (62 to 91)</td><td>yes</td></tr>
<tr><th scope="row">IL</th><td class="text-end">66</td><td class="text-end">201</td><td class="text-end">229 (204 to 255)</td><td>yes</td></tr>
<tr><th scope="row">IN</th><td class="text-end">57</td><td class="text-end">228</td><td class="text-end">239 (210 to 267)</td><td>yes</td></tr>
<tr><th scope="row">KS</th><td class="text-end">47</td><td class="text-end">130</td><td class="text-end">122 (105 to 141)</td><td>yes</td></tr>
<tr><th scope="row">KY</th><td class="text-end">83</td><td class="text-end">333</td><td class="text-end">329 (295 to 363)</td><td>yes</td></tr>
<tr><th scope="row">LA</th><td class="text-end">34</td><td class="text-end">157</td><td class="text-end">145 (125 to 164)</td><td>yes</td></tr>
<tr><th scope="row">MA</th><td class="text-end">2</td><td class="text-end">-3</td><td class="text-end">6 (2 to 13)</td><td>no</td></tr>
<tr><th scope="row">MD</th><td class="text-end">7</td><td class="text-end">-11</td><td class="text-end">36 (27 to 47)</td><td>no</td></tr>
<tr><th scope="row">ME</th><td class="text-end">4</td><td class="text-end">18</td><td class="text-end">24 (17 to 30)</td><td>yes</td></tr>
<tr><th scope="row">MI</th><td class="text-end">52</td><td class="text-end">187</td><td class="text-end">202 (176 to 229)</td><td>yes</td></tr>
<tr><th scope="row">MN</th><td class="text-end">55</td><td class="text-end">213</td><td class="text-end">183 (159 to 209)</td><td>yes</td></tr>
<tr><th scope="row">MO</th><td class="text-end">76</td><td class="text-end">263</td><td class="text-end">244 (216 to 274)</td><td>yes</td></tr>
<tr><th scope="row">MS</th><td class="text-end">55</td><td class="text-end">142</td><td class="text-end">198 (172 to 226)</td><td>yes</td></tr>
<tr><th scope="row">MT</th><td class="text-end">22</td><td class="text-end">59</td><td class="text-end">58 (47 to 71)</td><td>yes</td></tr>
<tr><th scope="row">NC</th><td class="text-end">41</td><td class="text-end">180</td><td class="text-end">187 (166 to 209)</td><td>yes</td></tr>
<tr><th scope="row">ND</th><td class="text-end">21</td><td class="text-end">47</td><td class="text-end">49 (40 to 61)</td><td>yes</td></tr>
<tr><th scope="row">NE</th><td class="text-end">25</td><td class="text-end">38</td><td class="text-end">47 (38 to 59)</td><td>yes</td></tr>
<tr><th scope="row">NH</th><td class="text-end">2</td><td class="text-end">18</td><td class="text-end">13 (7 to 17)</td><td>yes</td></tr>
<tr><th scope="row">NJ</th><td class="text-end">1</td><td class="text-end">-6</td><td class="text-end">7 (3 to 9)</td><td>no</td></tr>
<tr><th scope="row">NM</th><td class="text-end">10</td><td class="text-end">40</td><td class="text-end">43 (34 to 53)</td><td>yes</td></tr>
<tr><th scope="row">NV</th><td class="text-end">10</td><td class="text-end">215</td><td class="text-end">35 (27 to 43)</td><td>no</td></tr>
<tr><th scope="row">NY</th><td class="text-end">22</td><td class="text-end">236</td><td class="text-end">118 (101 to 133)</td><td>no</td></tr>
<tr><th scope="row">OH</th><td class="text-end">45</td><td class="text-end">201</td><td class="text-end">224 (201 to 247)</td><td>yes</td></tr>
<tr><th scope="row">OK</th><td class="text-end">44</td><td class="text-end">383</td><td class="text-end">165 (145 to 188)</td><td>no (data-quality counties)</td></tr>
<tr><th scope="row">OR</th><td class="text-end">17</td><td class="text-end">88</td><td class="text-end">71 (59 to 86)</td><td>yes</td></tr>
<tr><th scope="row">PA</th><td class="text-end">24</td><td class="text-end">122</td><td class="text-end">106 (89 to 122)</td><td>yes</td></tr>
<tr><th scope="row">RI</th><td class="text-end">2</td><td class="text-end">19</td><td class="text-end">11 (6 to 16)</td><td>no</td></tr>
<tr><th scope="row">SC</th><td class="text-end">17</td><td class="text-end">98</td><td class="text-end">82 (68 to 96)</td><td>yes</td></tr>
<tr><th scope="row">SD</th><td class="text-end">26</td><td class="text-end">37</td><td class="text-end">59 (47 to 73)</td><td>yes</td></tr>
<tr><th scope="row">TN</th><td class="text-end">48</td><td class="text-end">267</td><td class="text-end">221 (195 to 248)</td><td>yes</td></tr>
<tr><th scope="row">TX</th><td class="text-end">136</td><td class="text-end">501</td><td class="text-end">409 (373 to 444)</td><td>yes</td></tr>
<tr><th scope="row">UT</th><td class="text-end">17</td><td class="text-end">109</td><td class="text-end">58 (47 to 70)</td><td>yes</td></tr>
<tr><th scope="row">VA</th><td class="text-end">88</td><td class="text-end">331</td><td class="text-end">333 (299 to 368)</td><td>yes</td></tr>
<tr><th scope="row">VT</th><td class="text-end">7</td><td class="text-end">33</td><td class="text-end">36 (26 to 45)</td><td>yes</td></tr>
<tr><th scope="row">WA</th><td class="text-end">13</td><td class="text-end">84</td><td class="text-end">56 (46 to 67)</td><td>yes</td></tr>
<tr><th scope="row">WI</th><td class="text-end">48</td><td class="text-end">187</td><td class="text-end">177 (154 to 203)</td><td>yes</td></tr>
<tr><th scope="row">WV</th><td class="text-end">31</td><td class="text-end">112</td><td class="text-end">132 (111 to 150)</td><td>yes</td></tr>
<tr><th scope="row">WY</th><td class="text-end">13</td><td class="text-end">33</td><td class="text-end">40 (30 to 52)</td><td>yes</td></tr>
</tbody>
</table>
</div>
</details>

## Limits

- Counts are provisional and get revised. Every run is date-stamped.
- The hidden total depends on the model; we did no prior-sensitivity analysis.
- 10 states are left out of the constraint: 9 with differences outside the bounds (3 negative) and Oklahoma, which has data-quality counties. Their differences sum to 1,737 deaths, against 501 in the model. We do not know why the files differ; the dataset description does not say.
- Hide-and-score counties are larger than truly hidden ones: evidence, not proof.
- The interval is for the underlying rate, not the observed count. Rates are crude, not age-adjusted.
- Connecticut and Kalawao have no SAHIE values, so their covariates are filled with medians.
- Not for inferring individual risk.

## Use it

Download the table: **[county overdose rates, all 3,142 counties (CSV)]({{ site.baseurl }}/downloads/10-hidden-overdose-county-rates.csv)**. Rates are expected deaths per 100,000 people per year, with a 90% interval. Reading a row:

- **Probability above state rate** and **top decile** are shares of model draws: 0.90 is fairly sure, 0.50 a coin flip.
- **Hard bounds** are the file's 1 and 9 deaths as rates.

Code: [GitHub][code]. `python run.py` rebuilds everything from public files.

{% include casestudy_cta.html %}

</div>
