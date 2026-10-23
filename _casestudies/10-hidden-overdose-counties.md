---
title: Overdose rates where counts are hidden
subtitle: Estimating the county counts the CDC file hides
description: >-
  A county map of overdose death rates with the hidden counties filled in, each
  with a 90% interval and a chance of being above its state. Public data only.
  No patient information.
layout: example
modal-id: 10
date: 2026-10-22T00:00:00.000Z
thumbnail: example-overdose-thumbnail.webp
kind: example
persona: For small health departments
need: >-
  Defensible county overdose death rates with uncertainty for the counties where
  the national file hides the count.
question: >-
  In the 1,626 counties where the CDC file hides the overdose count, what rate
  can you defend, and how unsure should you be?
stats:
  - value: "1,626"
    label: Counties with a blank count in the CDC file
    note: "52% of 3,142 counties and 42.2 million people (12.4%)"
    kind: observed
  - value: "5,800"
    label: Deaths the model puts in those counties
    note: "Median 5,818. Range after checks: 5,400 to 6,200"
    kind: estimate
  - value: "13.4"
    label: "Median hidden-county rate per 100,000"
    note: "Counties with 10 or more published deaths: 20.6"
    kind: estimate
  - value: 22 of 37
    label: States where our 90% interval held the state check
    note: "So the intervals are too narrow, and we say so"
sections:
  - id: tool
    label: Your county
  - id: findings
    label: What we found
  - id: check
    label: Does it hold up?
  - id: limits
    label: Limits
  - id: methods
    label: How we did it
downloads:
  - title: "County overdose rates, all 3,142 counties"
    file: /downloads/10-hidden-overdose-county-rates.csv
    type: CSV
    size: 377 KB
    description: >-
      Published count, the file's 1-to-9 bounds as rates, the model estimate
      with a 90% interval, chance above state rate, chance in the top decile,
      and a rank range.
cta:
  heading: Want this for your health department?
  text: >-
    Tell us your state and what you have been asked to decide. We will build the
    county table and a one-page memo you can hand to your board.
  button: Tell us about your department
data: /assets/examples/10/data.json
extra_css:
  - /assets/examples/10/page.css
extra_scripts:
  - src: "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
    integrity: >-
      sha512-4UKI/XKm3xrvJ6pZS5oTRvIQGIzZFoXR71rRBb1y2N+PbwAsKa5tPl2J6WvbEvwN3TxQCm8hMzsl/pO+82iRlg==
  - /assets/examples/10/page.js
---

[quick]: https://www.cdc.gov/pcd/issues/2019/18_0441.htm

<section class="ex-section" id="tool">
<div class="ex-prose ex-toolhead" markdown="1">

## Find your county

</div>

<div class="ex-wide">
<div class="ex-panel ov">

<div class="ov-bar">
<div id="pick-state"></div>
<div id="pick-county"></div>
<div class="ov-try" id="try" hidden>
<span class="ov-try__label" id="try-label">Try one</span>
<ul class="ov-try__list" id="try-list" aria-labelledby="try-label"></ul>
</div>
</div>

<div class="ov-grid">

<figure class="ov-map ex-figure" id="fig-map">
<div class="ov-map__head">
<h3 class="ex-figure__title" id="map-title" aria-live="polite">The file is blank for 1,626 counties</h3>
<fieldset class="ex-field ov-mode">
<legend class="ex-label">Color the map by</legend>
<div class="ex-seg">
<label><input type="radio" name="mapmode" value="file" checked><span><em class="ov-long">CDC file</em><em class="ov-short">CDC file</em></span></label>
<label><input type="radio" name="mapmode" value="est"><span><em class="ov-long">With estimates</em><em class="ov-short">Estimates</em></span></label>
<label><input type="radio" name="mapmode" value="above"><span><em class="ov-long">Chance above state</em><em class="ov-short">Chance above</em></span></label>
</div>
</fieldset>
</div>
<div class="ov-mapwrap">
<div class="ex-chart ov-mapchart" id="chart-map"></div>
<div class="ov-maptag" id="map-tag" hidden>
<button class="ex-btn ex-btn--ink ex-btn--sm" type="button" id="map-reset">All states</button>
<span class="ov-maptag__name" id="map-tag-name"></span>
</div>
</div>
<div class="ov-legend">
<div id="ramp-map"></div>
<ul class="ex-legend" aria-label="Map legend" id="legend-map">
<li><span class="ex-key ex-key--hatch" aria-hidden="true"></span><span id="legend-hatch">Blank in the CDC file</span></li>
<li><span class="ex-key ex-key--ring" aria-hidden="true"></span>Selected county</li>
</ul>
</div>
<p class="ov-hint" id="map-hint">Click a county to zoom to its state and read it. <a href="{{ site.baseurl }}/downloads/10-hidden-overdose-county-rates.csv">Download all 3,142 counties (CSV)</a><span class="ex-vh">. Without a mouse, use the State and County boxes; the data table under the map lists every county.</span></p>
<figcaption id="map-caption">Published rate per 100,000 people per year, 12 months ending March 2026.</figcaption>
<p class="ex-source">Source: CDC NCHS provisional county overdose deaths; Census population; Primordial Analytics model.</p>
<details class="ex-data">
<summary>Data table for the map (all 3,142 counties)</summary>
<div id="table-map"></div>
</details>
</figure>

<div class="ov-card" id="card" aria-label="Selected county"></div>

</div>

<div class="ov-strip" id="strip">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="strip-title">Pick a state to see its counties side by side</h3>
<p class="ex-figure__sub" id="strip-sub" aria-live="polite">Each row is a county. The gold bar is the model's 90% interval for its rate.</p>
</div>
<div class="ex-toolbar ov-strip__bar" id="strip-bar" hidden>
<fieldset class="ex-field">
<legend class="ex-label">Show</legend>
<div class="ex-seg">
<label><input type="radio" name="stripfilter" value="all" checked><span>All counties</span></label>
<label><input type="radio" name="stripfilter" value="hidden"><span>Blank in file</span></label>
<label><input type="radio" name="stripfilter" value="published"><span>Published</span></label>
</div>
</fieldset>
<div class="ex-field">
<label class="ex-label" for="stripsort">Sort by</label>
<select class="ex-select" id="stripsort">
<option value="pa">Chance above state rate</option>
<option value="med">Estimated rate</option>
<option value="pop">Population</option>
<option value="name">Name</option>
</select>
</div>
<div class="ex-field ov-strip__btns">
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="copy-table">Copy table</button>
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="dl-table">Download CSV</button>
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="strip-more" hidden>Show all</button>
</div>
</div>
<ul class="ex-legend" aria-label="Strip legend" id="legend-strip" hidden>
<li><span class="ov-key ov-key--ibar" aria-hidden="true"></span>Model median and 90% interval</li>
<li><span class="ov-key ov-key--dot" aria-hidden="true"></span>Published rate</li>
<li><span class="ov-key ov-key--bar" aria-hidden="true"></span>What the file allows: 1 to 9 deaths</li>
<li><span class="ex-key ex-key--ref" aria-hidden="true"></span><span id="legend-state">State rate</span></li>
<li><span class="ex-key ex-key--hatch" aria-hidden="true"></span>Blank in the file</li>
</ul>
<div class="ex-chart ov-stripchart" id="chart-strip"></div>
<p class="ex-source" id="strip-source" hidden>Source: CDC NCHS provisional counts; Primordial Analytics model. Rates per 100,000 per year, 12 months ending March 2026.</p>
<details class="ex-data" id="strip-details" hidden>
<summary>Data table for this state</summary>
<div id="table-strip"></div>
</details>
</div>

</div>
</div>

<div class="ex-callout" markdown="1">
<p class="ex-callout__title">Two ranges, two meanings</p>
<p>The pale bar is what the file allows: 1 to 9 deaths, written as a rate. The gold bar is the model's 90% interval for the county's underlying rate. One is a count, the other a rate, so narrower is not better. The model interval is a median 13.6 per 100,000 wide and the file's bounds are 39.0 wide. A county expecting 0.5 deaths can still record one: in 246 hidden counties the model median falls outside the bounds, and in 77 the whole interval sits below the lower bound.</p>
</div>
</section>

<section class="ex-section ex-band ex-band--tint" id="findings">
<div class="ex-prose" markdown="1">

## What we found

Hidden does not mean low risk. Read these before you use a county number.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure" id="fig-total">
<div class="ex-figure__head">
<h3 class="ex-figure__title">The hidden counties hold about 5,800 deaths; plan on 5,400 to 6,200</h3>
<p class="ex-figure__sub">Deaths in the 1,626 hidden counties, 12 months ending March 2026. These counties have 42.2 million people (12.4%).</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ex-key ex-key--ci" aria-hidden="true"></span>Range</li>
<li><span class="ov-key ov-key--dot ov-key--est" aria-hidden="true"></span>Median</li>
</ul>
<div class="ex-chart" id="chart-total"></div>
<figcaption>The model's own 90% interval holds only if the model is right, and the state check below shows it is too narrow. We multiplied its half-widths by <span data-n="agg_coverage_scale" data-d="2">2.54</span>, the factor that put 90% of the checked states inside. That is a rough planning range fitted on state totals, not a formal interval. The last row is the lowest and highest of five totals (the main model and four variants), so it shows two totals, not an interval.</figcaption>
<p class="ex-source">Source: Primordial Analytics model; CDC NCHS provisional counts.</p>
<details class="ex-data">
<summary>Data table for this chart</summary>
<div id="table-total"></div>
</details>
</figure>

<figure class="ex-wide ex-figure" id="fig-class">
<div class="ex-figure__head">
<h3 class="ex-figure__title">In every class that has hidden counties, the modeled hidden median is below the published median</h3>
<p class="ex-figure__sub">Median rate per 100,000 by NCHS urban-rural class. The published dot is the median of counties with 10 or more deaths. A county can only be hidden if it had under 10 deaths, so some of the gap is built in. Over all counties the hidden median is <span data-n="rate_median_hidden_counties" data-d="1">13.4</span>, the published median with 10 or more deaths is <span data-n="rate_median_published_10_plus" data-d="1">20.6</span> and the published median including zeros is <span data-n="rate_median_published_incl_zeros" data-d="1">13.5</span>.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ov-key ov-key--dot ov-key--est" aria-hidden="true"></span>Hidden counties, model median</li>
<li><span class="ov-key ov-key--dot ov-key--obs" aria-hidden="true"></span>Published counties with 10 or more deaths</li>
</ul>
<div class="ex-chart" id="chart-class"></div>
<figcaption>Over half of published noncore counties report zero deaths (439 of 493), which is why their median including zeros is 0.0. The table has that column too.</figcaption>
<p class="ex-source">Source: CDC NCHS provisional counts; NCHS 2013 urban-rural classification; Primordial Analytics model.</p>
<details class="ex-data">
<summary>Data table for this chart</summary>
<div id="table-class"></div>
</details>
</figure>

<figure class="ex-wide ex-figure" id="fig-above">
<div class="ex-figure__head">
<h3 class="ex-figure__title">87 hidden counties are very likely above their state's rate</h3>
<p class="ex-figure__sub">Counties grouped by the model's chance that the county's rate is above its state's. A 50% chance is a coin flip.</p>
</div>
<ul class="ex-legend" aria-label="Chance above state rate" id="legend-above"></ul>
<div class="ex-chart" id="chart-above"></div>
<figcaption>District of Columbia is left out because it is its own state.</figcaption>
<p class="ex-source">Source: Primordial Analytics model. Counts of counties computed from the county table.</p>
<details class="ex-data">
<summary>Data table for this chart</summary>
<div id="table-above"></div>
</details>
</figure>

<div class="ex-prose" markdown="1">

- 87 hidden counties have a better than 80% chance of a rate above their state's, and 78 have better than a 50% chance of being in the top decile (above 27.3 per 100,000).
- A published zero is not safe. The 554 zero counties have a median population of 5,948 and a modeled median rate of 9.4. In 146 of them the chance of exceeding the state rate is above 20%.

<div class="ex-keyfig">
<span class="ex-keyfig__value">1,819</span>
<p class="ex-keyfig__text"><strong>Do not rank.</strong> A hidden county's rank interval spans a median 1,819 places of 3,142, against 852 for a published county. Use ranges and probabilities, not a league table.</p>
</div>

</div>
</section>

<section class="ex-section" id="check">
<div class="ex-prose" markdown="1">

## Does it hold up?

Three checks, none on a truly suppressed cell, because no published cell is 1 to 9. They are evidence, not proof.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure" id="fig-agg">
<div class="ex-figure__head">
<h3 class="ex-figure__title">Modeled totals follow the state differences, but 15 of 37 intervals miss</h3>
<p class="ex-figure__sub">For each state, the model's deaths in hidden counties (fit without the state totals) against the state total minus published county counts. Log axes.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ov-key ov-key--circle" aria-hidden="true"></span>State used in the check (37)</li>
<li><span class="ov-key ov-key--diamond" aria-hidden="true"></span>Difference not plausible, left out of the fit</li>
<li><span class="ov-key ov-key--whisk" aria-hidden="true"></span>90% interval holds the state difference</li>
<li><span class="ov-key ov-key--whisk ov-key--miss" aria-hidden="true"></span>Interval misses it</li>
<li><span class="ex-key ex-key--ref" aria-hidden="true"></span>Equal</li>
</ul>
<div class="ex-chart" id="chart-agg"></div>
<figcaption>A version of the model that never saw the state differences put 5,334 deaths in the hidden counties of the 37 plausible states, against 5,441 from the totals. 25 of 37 agree within 20% and the log correlation is 0.959. A naive rule comes close: hidden-county counts alone correlate 0.90 with the difference and put 18 of 37 within 20%. The 90% interval holds the state difference in only 22 of 37 states (59%). Three states with negative differences are not plotted.</figcaption>
<p class="ex-source">Source: CDC NCHS provisional county and state counts; Primordial Analytics model.</p>
<details class="ex-data">
<summary>Data table for this chart (47 states)</summary>
<div id="table-agg"></div>
</details>
</figure>

<div class="ex-wide ex-panel ov-hide" id="hide">
<div class="ov-hide__head">
<div>
<h3 class="ex-figure__title" id="hide-title">Hide the counts, then score the guesses</h3>
<p class="ex-figure__sub" id="hide-sub">We treat every county below a cutoff as suppressed, refit, and score the counties whose true count we know.</p>
</div>
<fieldset class="ex-field">
<legend class="ex-label">Counts hidden below</legend>
<div class="ex-seg">
<label><input type="radio" name="hidecut" value="20"><span>20 deaths</span></label>
<label><input type="radio" name="hidecut" value="30" checked><span>30 deaths</span></label>
</div>
</fieldset>
</div>
<div class="ex-cols" style="--ex-col-min: 24rem">
<figure class="ex-figure" id="fig-mae">
<div class="ex-figure__head">
<h4 class="ex-figure__title" id="mae-title">Average miss, in deaths per county</h4>
<p class="ex-figure__sub">Lower is better.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ex-key ex-key--est" aria-hidden="true"></span>Model</li>
<li><span class="ov-key ov-key--rule" aria-hidden="true"></span>Simple rule</li>
</ul>
<div class="ex-chart" id="chart-mae"></div>
<details class="ex-data">
<summary>Data table for this chart</summary>
<div id="table-mae"></div>
</details>
</figure>
<figure class="ex-figure" id="fig-cal">
<div class="ex-figure__head">
<h4 class="ex-figure__title" id="cal-title">Intervals hold a little less than they claim</h4>
<p class="ex-figure__sub">Share of true counts inside each interval, minus the interval level. At zero, an interval would be exactly right.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ex-key ex-key--line-est" aria-hidden="true"></span>Spatial model</li>
<li><span class="ov-key ov-key--l2" aria-hidden="true"></span>No spatial term</li>
<li><span class="ov-key ov-key--l3" aria-hidden="true"></span>Poisson-gamma</li>
<li><span class="ex-key ex-key--ref" aria-hidden="true"></span>Exactly right (zero)</li>
</ul>
<div class="ex-chart" id="chart-cal"></div>
<details class="ex-data">
<summary>Data table for this chart</summary>
<div id="table-cal"></div>
</details>
</figure>
</div>
<p class="ex-caption" id="hide-caption" aria-live="polite"></p>
</div>

<div class="ex-prose" markdown="1">

Counts of 1 to 9 cannot be scored, so this tests only the upper range and is not a calibration estimate.

**Forecast.** We fit to March 2025 and predicted the 1,514 counties published for March 2026, using each state's 2026 total. The spatial and Poisson-gamma models score 3.25 and 3.35 (CRPS). On the 1,175 counties published in both years, the average miss is 5.66 for the spatial model, 5.75 for Poisson-gamma and 6.04 for last year's count with the same state adjustment.

Dropping the covariates moves a hidden county's rate by a median 11.3%, and dropping the spatial term by 9.4%.

</div>
</section>

<section class="ex-section ex-band ex-band--tint" id="limits">
<div class="ex-prose" markdown="1">

## What this does not tell you

</div>

<div class="ex-wide ex-callout" markdown="1">
<p class="ex-callout__title">Read these before the numbers go in a memo</p>

- Counts are provisional and get revised. Every run is date-stamped.
- The hidden total depends on the model. We did no prior-sensitivity analysis.
- 10 states are left out of the state constraint: 9 with differences outside the 1-to-9 bounds (3 of them negative) and Oklahoma, which has data-quality counties. Their differences sum to 1,737 deaths, against 501 in the model. We do not know why the files differ, and the dataset description does not say.
- Hide-and-score counties are larger than truly hidden ones. That makes the check evidence, not proof.
- The interval is for the underlying rate, not the observed count. Rates are crude, not age-adjusted.
- Connecticut and Kalawao have no SAHIE values, so their covariates are filled with medians.
- Geography follows the CDC file, not the newest Census names. Connecticut is the 8 old counties, not the 9 planning regions, and their population is the 2020 county figure scaled to the state's 2024 growth. Valdez-Cordova (Alaska) is the area the Census split in 2019, merged back together. A "(CA)" after a name marks a census area. Search finds Kusilvak and Oglala Lakota under the file's older names.
- The state rate on a card is the model's own: county medians weighted by population. It can run a little below the rate from the CDC state total, so the state card shows both when the file allows. The chance above the state rate is measured against the model's rate.
- A hidden county's own data say only "1 to 9," so its estimate rests mostly on covariates, neighbors and the state total.
- Not for inferring individual risk.

</div>
</section>

<section class="ex-section" id="methods">
<h2 class="ex-h2">How we did it</h2>
<details class="ex-methods ex-wide">
<summary><span>Methods and sources<small>For the analyst who will check the work</small></span></summary>
<div class="ex-methods__body">

<div class="ex-prose" markdown="1">

A hidden cell says the count is at least 1 and at most 9, so the county is neither a zero nor a county with 10 or more. [Quick (2019)][quick] used the same idea for suppressed CDC WONDER deaths.

</div>

<ol class="ex-steps">
<li><strong>Likelihood.</strong> Published counts enter a Poisson model as exact values, zeros included. A suppressed cell enters as the probability of 1 to 9 deaths at that county's rate. The 2 data-quality cells carry no information.</li>
<li><strong>Rate model.</strong> Each county's log rate is an intercept, four county measures (density, uninsured share, low-income share, urban-rural class), a state effect, and a spatial effect that lets neighbors inform each other (a Leroux CAR prior). NUTS in NumPyro, 4 chains, 1,000 warm-up and 1,000 draws each. The fit has 0 divergences and a largest R-hat of 1.02. Effective sample size is at least 2,172 for county rates and 259 for hyperparameters.</li>
<li><strong>State constraint.</strong> A state's total minus its published county counts is roughly the deaths in its suppressed counties. The files do not always agree, so we use that difference as a soft constraint only (standard deviation 5% of the state total), in the 37 states where it falls between 1 and 9 per hidden county and none has a data-quality county.</li>
<li><strong>Validation.</strong> Compare the modeled hidden total with each state's difference. Hide all counts under 20 and under 30 and score the counties with known counts. Fit to March 2025 and predict March 2026. Each check is seeded separately.</li>
<li><strong>Intervals.</strong> Draws give each county's median and 90% interval, the chance its rate is above its state's, the chance it is in the top decile, and a rank interval. The hidden-total range is widened, by a factor of <span data-n="agg_coverage_scale" data-d="2">2.54</span> on its half-widths, until 90% of checked states fall inside. That factor is fitted on state totals and applied to the national hidden total.</li>
</ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
<dl class="ex-sources">
<dt>CDC NCHS provisional county overdose deaths</dt>
<dd><a href="https://data.cdc.gov/d/gb4e-yj24">data.cdc.gov</a>. 12 months ending March 2026, as of 2026-10-04. Counts of 1 to 9 are suppressed; 0 and 10 or more are published. That gives 3,142 counties: 1,514 published (554 zeros), 1,626 suppressed at 1 to 9, and 2 suppressed for data quality.</dd>
<dt>NCHS state totals</dt>
<dd><a href="https://data.cdc.gov/d/xkb8-kh2a">data.cdc.gov</a>. Same window, not suppressed.</dd>
<dt>Census</dt>
<dd>2024 county population (Connecticut: 2020 county population scaled to the state's 2024 growth), 2020 boundaries, and 2024 <a href="https://www.census.gov/programs-surveys/sahie.html">SAHIE</a> uninsured and low-income shares. Map shapes: us-atlas, from the Census cartographic boundaries.</dd>
<dt>Downloaded</dt>
<dd>All aggregate, public files, downloaded 2026-10-22.</dd>
</dl>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Reading a row of the CSV</h3>
<dl class="ex-sources">
<dt>Rates</dt>
<dd>Expected deaths per 100,000 people per year, with a 90% interval.</dd>
<dt>Probability above state rate, top decile</dt>
<dd>Shares of model draws. 0.90 is fairly sure and 0.50 is a coin flip.</dd>
<dt>Hard bounds</dt>
<dd>The file's 1 and 9 deaths written as rates.</dd>
<dt>Code</dt>
<dd><a href="https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/10-hidden-overdose-counties">GitHub</a>. <code>python run.py</code> rebuilds everything from public files.</dd>
</dl>

<div class="ex-prose" markdown="1">

### Every validation number

</div>
<div id="table-val"></div>
</div>
</details>
</section>
