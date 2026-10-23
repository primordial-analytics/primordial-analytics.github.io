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
  Where the CDC file hides a county's count, what rate can you defend, and how
  unsure should you be?
brief: >-
  For each county where the file hides the count, we estimate the death rate
  and give a 90% interval. Of those counties, 87 have better than an 80%
  chance of being above their state's rate. The intervals did not hold in
  every state we checked, so read them as a guide, not a guarantee.
stats:
  - value: "1,626"
    label: counties with a blank count
    note: Observed. Of 3,142 counties; the CDC file hides counts of 1 to 9
  - value: "5,800"
    label: deaths in those counties
    note: Modeled. Plan on 5,400 to 6,200
  - value: 22 of 37
    label: states where our 90% interval held
    note: Checked against state totals
sections:
  - id: tool
    label: Your county
  - id: findings
    label: Findings
  - id: check
    label: Checks
  - id: limits
    label: Limits
  - id: methods
    label: Method
downloads:
  - title: "County overdose rates, all 3,142 counties"
    file: /downloads/10-hidden-overdose-county-rates.csv
    type: CSV
    size: 377 KB
    description: >-
      Published count, model rate with 90% interval, chance above state, rank
      range.
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

<div class="ex-wide ex-panel ov">

<div class="ov-bar">
<div id="pick-state"></div>
<div id="pick-county"></div>
</div>
<p class="ex-hint ov-try" id="try" hidden>Search, click the map to zoom, or try <span id="try-list"></span>.</p>

<div class="ov-grid">

<figure class="ov-map ex-figure" id="fig-map" aria-labelledby="map-title">
<h3 class="ex-vh" id="map-title" aria-live="polite">Where the CDC file is blank</h3>
<fieldset class="ex-field ov-mode">
<legend class="ex-vh">Color the map by</legend>
<div class="ex-seg">
<label><input type="radio" name="mapmode" value="file" checked><span><em class="ov-long">CDC file</em><em class="ov-short">CDC file</em></span></label>
<label><input type="radio" name="mapmode" value="est"><span><em class="ov-long">With estimates</em><em class="ov-short">Estimates</em></span></label>
<label><input type="radio" name="mapmode" value="above"><span><em class="ov-long">Chance above state</em><em class="ov-short">Chance above</em></span></label>
</div>
</fieldset>
<div class="ov-keys">
<div id="ramp-map"></div>
<ul class="ex-legend" aria-label="Map legend" id="legend-map">
<li><span class="ex-key ex-key--hatch" aria-hidden="true"></span><span id="legend-hatch">Blank in the CDC file</span></li>
</ul>
</div>
<div class="ov-mapwrap">
<div class="ex-chart ov-mapchart" id="chart-map"></div>
<div class="ov-maptag" id="map-tag" hidden>
<button class="ex-btn ex-btn--ink ex-btn--sm" type="button" id="map-reset">All states</button>
<span class="ov-maptag__name" id="map-tag-name"></span>
</div>
</div>
<details class="ex-notes">
<summary>Source and data</summary>
<p id="map-caption">Published rate per 100,000 people per year, 12 months ending March 2026.</p>
<p>Blank counties are <span id="facts-share">52%</span> of <span data-n="counties">3,142</span> and hold <span id="facts-pop">42.2 million</span> people (<span data-n="suppressed_population_share_pct" data-d="1">12.4</span>%). The states with the most blank counties: <span id="facts-top">Texas 136 of 254, Georgia 96 of 159, Virginia 88 of 133, Kentucky 83 of 120, Missouri 76 of 115</span>.</p>
<p>The State box zooms the map and lists the state's counties. The County box takes a name or a FIPS code. Without a mouse, use these two boxes; the table below lists every county. <a href="{{ site.baseurl }}/downloads/10-hidden-overdose-county-rates.csv">Download all 3,142 counties (CSV)</a>.</p>
<p class="ex-source">Source: CDC NCHS provisional county overdose deaths; Census population; Primordial Analytics model.</p>
<div id="table-map"></div>
</details>
</figure>

<div class="ov-card" id="card" role="group" aria-label="Selected county"></div>

</div>

<figure class="ov-strip ex-figure ex-figure--notes" id="strip" aria-labelledby="strip-title" hidden>
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="strip-title"></h3>
</div>
<div class="ex-toolbar ov-strip__bar" id="strip-bar">
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
</div>
<div class="ex-chart ov-stripchart" id="chart-strip"></div>
<p class="ex-hint ov-strip__limit" id="strip-limit" aria-live="polite" hidden></p>
<p class="ex-actions ov-strip__acts">
<button class="ex-link" type="button" id="copy-table">Copy table</button>
<button class="ex-link" type="button" id="dl-table">Download CSV</button>
<button class="ex-link" type="button" id="strip-more" hidden>Show all</button>
</p>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Two ranges.</strong> Pale bar: what the file allows, 1 to 9 deaths. Gold bar: the model's 90% interval. Tick: model median. Dot: published rate. Arrow: runs past the axis.</p>
</div>
<details class="ex-notes">
<summary>Notes and data</summary>
<p id="strip-sub" aria-live="polite"></p>
<p>The pale bar is what the file allows: 1 to 9 deaths, written as a rate. The gold bar is the model's 90% interval for the county's underlying rate. One is a count, the other a rate, so narrower is not better. The model interval is a median <span data-n="model_width_median" data-d="1">13.6</span> per 100,000 wide and the file's bounds are <span data-n="hard_width_median" data-d="1">39.0</span> wide. A county expecting 0.5 deaths can still record one: in <span data-n="hidden_median_outside_hard_bounds">246</span> hidden counties the model median falls outside the bounds, and in <span data-n="hidden_interval_below_hard_lo">77</span> the whole interval sits below the lower bound.</p>
<p class="ex-source" id="strip-source">Source: CDC NCHS provisional counts; Primordial Analytics model. Rates per 100,000 per year, 12 months ending March 2026.</p>
<div id="table-strip"></div>
</details>
</figure>

</div>
</section>

<section class="ex-section" id="findings">
<div class="ex-prose" markdown="1">

## Hidden does not mean low risk

<span data-n="hidden_p_above_state_gt_80">87</span> hidden counties have better than an 80% chance of being above their state's rate. A published zero is not safe either.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-above" aria-labelledby="t-above">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-above">Chance a county is above its state's rate</h3>
</div>
<div class="ex-chart" id="chart-above"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Top decile.</strong> <span data-n="hidden_p_top_decile_gt_50">78</span> hidden counties are more likely than not in the top 10%.</p>
<p class="ex-note"><strong>Published zero.</strong> Of <span data-n="published_zero">554</span> zero counties, <span data-n="zero_counties_p_above_state_gt_20">146</span> have more than a 20% chance of exceeding the state rate.</p>
<p class="ex-note"><strong>Do not rank.</strong> A hidden county's rank is uncertain by about <span data-n="hidden_rank_interval_median_span" data-a="2">1,800</span> places of 3,142, against about <span data-n="published_rank_interval_median_span" data-a="2">850</span> for a published one. Use ranges, not ranks.</p>
</div>
</figure>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-class" aria-labelledby="t-class">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-class">Median rate by urban-rural class</h3>
</div>
<div class="ex-chart" id="chart-class"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Lower by design.</strong> Hidden counties model below published ones in every class that has them. A county can only be hidden with under 10 deaths, so some of the gap is built in.</p>
</div>
</figure>

<div class="ex-prose">
<details class="ex-notes">
<summary>Notes and data</summary>
<p><strong>Chance above the state rate.</strong> Counties are grouped by the model's chance that the county's rate is above its state's. A 50% chance is a coin flip. District of Columbia is left out because it is its own state. The top decile starts above <span data-n="top_decile_cut_per_100k" data-d="1">27.3</span> per 100,000. The <span data-n="published_zero">554</span> zero counties have a median population of <span data-n="zero_median_population">5,948</span> and a modeled median rate of <span data-n="rate_median_published_zero_modelled" data-d="1">9.4</span>. A hidden county's rank interval spans a median <span data-n="hidden_rank_interval_median_span">1,819</span> places of 3,142, against <span data-n="published_rank_interval_median_span">852</span> for a published county.</p>
<p class="ex-source">Source: Primordial Analytics model. Counts of counties computed from the county table.</p>
<div id="table-above"></div>
<p><strong>Urban-rural class.</strong> Median rate per 100,000 by NCHS urban-rural class. The published dot is the median of counties with 10 or more deaths. Over all counties the hidden median is <span data-n="rate_median_hidden_counties" data-d="1">13.4</span>, the published median with 10 or more deaths is <span data-n="rate_median_published_10_plus" data-d="1">20.6</span> and the published median including zeros is <span data-n="rate_median_published_incl_zeros" data-d="1">13.5</span>. Over half of published noncore counties report zero deaths (<span id="noncore-zero">439</span> of <span id="noncore-n">493</span>), so their median including zeros is 0.0.</p>
<p class="ex-source">Source: CDC NCHS provisional counts; NCHS 2013 urban-rural classification; Primordial Analytics model.</p>
<div id="table-class"></div>
<p><strong>Hidden total.</strong> The hidden counties hold about <span data-n="hidden_total_deaths_median">5,818</span> deaths; plan on <span data-n="hidden_total_widened_lo90">5,400</span> to <span data-n="hidden_total_widened_hi90">6,200</span>. These are deaths in the <span data-n="suppressed_1_to_9">1,626</span> hidden counties, 12 months ending March 2026, in counties with <span id="notes-pop">42.2 million</span> people.</p>
<p>The model's own 90% interval holds only if the model is right, and the state check below shows it is too narrow. We multiplied its half-widths by <span data-n="agg_coverage_scale" data-d="2">2.54</span>, the factor that put 90% of the checked states inside. That is a rough planning range fitted on state totals, not a formal interval. The last row of the table is the lowest and highest of five totals (the main model and four variants), so it shows two totals, not an interval.</p>
<p class="ex-source">Source: Primordial Analytics model; CDC NCHS provisional counts.</p>
<div id="table-total"></div>
</details>
</div>
</section>

<section class="ex-section" id="check">
<div class="ex-prose" markdown="1">

## The checks support the model but show intervals are too narrow

Modeled totals track state totals, but only <span data-n="agg_inside_90">22</span> of <span data-n="agg_states_plausible">37</span> state intervals hold.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-agg" aria-labelledby="t-agg">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-agg">Model total against state total, by state</h3>
</div>
<div class="ex-chart" id="chart-agg"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Agreement.</strong> <span data-n="agg_within_20pct">25</span> of <span data-n="agg_states_plausible">37</span> states agree within 20%. The log correlation is <span data-n="agg_corr_log" data-d="2">0.96</span>.</p>
</div>
</figure>

<figure class="ex-wide ex-figure" id="fig-cal" aria-labelledby="cal-title">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="cal-title">On held-out counties, intervals run a few points short</h3>
<p class="ex-figure__sub">Test: hide every count under 20, or under 30, refit, and score the counties whose true count we know.</p>
</div>
<div class="ov-cal">
<div class="ov-cal__panel"><h4 class="ov-cal__t">Counts under 20 hidden</h4><div class="ex-chart" id="chart-cal-20"></div></div>
<div class="ov-cal__panel"><h4 class="ov-cal__t">Counts under 30 hidden</h4><div class="ex-chart" id="chart-cal-30"></div></div>
</div>
</figure>

<div class="ex-prose">
<details class="ex-notes">
<summary>Notes and data</summary>
<p><strong>State totals.</strong> Each state's modeled deaths in hidden counties, from a model fit without the state totals, are plotted against its state total minus published county counts, on log axes. Diamonds are states whose difference is not plausible; they are not in the fit. Labeled: every state left out of the fit and the three whose intervals miss by the most.</p>
<p>That version of the model put <span data-n="agg_model_sum_plausible">5,334</span> deaths in the hidden counties of the <span data-n="agg_states_plausible">37</span> plausible states, against <span data-n="agg_residual_sum_plausible">5,441</span> from the totals. <span data-n="agg_within_20pct">25</span> of <span data-n="agg_states_plausible">37</span> agree within 20% and the log correlation is <span data-n="agg_corr_log" data-d="3">0.959</span>. A naive rule comes close: hidden-county counts alone correlate <span data-n="agg_naive_corr_log" data-d="2">0.90</span> with the difference and put <span data-n="agg_naive_within_20pct">18</span> of <span data-n="agg_states_plausible">37</span> within 20%. The 90% interval holds the state difference in only <span data-n="agg_inside_90">22</span> of <span data-n="agg_states_plausible">37</span> states (59%). Three states with negative differences are not plotted.</p>
<p class="ex-source">Source: CDC NCHS provisional county and state counts; Primordial Analytics model.</p>
<div id="table-agg"></div>
<p><strong>Hide and score.</strong> The charts plot the share of true counts inside each interval, minus the interval level. At zero, an interval would be exactly right. Counts of 1 to 9 cannot be scored, so this check tests only the upper range and is not a calibration estimate.</p>
<div id="hide-notes"></div>
<div id="table-cal-20"></div>
<div id="table-cal-30"></div>
<div id="table-mae"></div>
<p><strong>Three checks.</strong> None is on a truly suppressed cell, because no published cell is 1 to 9. They are evidence, not proof.</p>
<p><strong>Forecast.</strong> We fit to March 2025 and predicted the <span data-n="forecast.n_scored">1,514</span> counties published for March 2026, using each state's 2026 total. The spatial and Poisson-gamma models score <span data-n="forecast.spatial_crps" data-d="2">3.25</span> and <span data-n="forecast.gamma_crps" data-d="2">3.35</span> (CRPS). On the <span data-n="forecast.same_n">1,175</span> counties published in both years, the average miss is <span data-n="forecast.spatial_mae" data-d="2">5.66</span> for the spatial model, <span data-n="forecast.gamma_mae" data-d="2">5.75</span> for Poisson-gamma and <span data-n="forecast.last_year_mae" data-d="2">6.04</span> for last year's count with the same state adjustment.</p>
<p>Dropping the covariates moves a hidden county's rate by a median <span data-n="sensitivity.no_covariates.abs_pct" data-d="1">11.3</span>%, and dropping the spatial term by <span data-n="sensitivity.no_spatial.abs_pct" data-d="1">9.4</span>%.</p>
</details>
</div>
</section>

<section class="ex-section" id="limits">
<div class="ex-prose" markdown="1">

## Six limits on these numbers

</div>

<div class="ex-prose">
<ul class="ex-limits">
<li>Counts are provisional and get revised; every run is date-stamped.</li>
<li>The hidden total depends on the model (plan on <span data-n="hidden_total_widened_lo90">5,400</span> to <span data-n="hidden_total_widened_hi90">6,200</span>); no prior-sensitivity check.</li>
<li>10 states are left out of the state constraint; their files disagree.</li>
<li>Hide-and-score counties are larger than truly hidden ones, so checks are evidence, not proof.</li>
<li>A hidden county's estimate rests mostly on covariates, neighbors and the state total.</li>
<li>Rates are crude, not age-adjusted. Not for inferring individual risk.</li>
</ul>
<details class="ex-notes">
<summary>Detail on each limit</summary>
<ul>
<li>Counts are provisional and get revised. Every run is date-stamped.</li>
<li>The hidden total depends on the model. We did no prior-sensitivity analysis.</li>
<li>10 states are left out of the state constraint: 9 with differences outside the 1-to-9 bounds (3 of them negative) and Oklahoma, which has data-quality counties. Their differences sum to <span data-n="agg_excluded_residual_sum">1,737</span> deaths, against <span data-n="agg_excluded_model_sum">501</span> in the model. We do not know why the files differ, and the dataset description does not say.</li>
<li>Hide-and-score counties are larger than truly hidden ones. That makes the check evidence, not proof.</li>
<li>The interval is for the underlying rate, not the observed count. Rates are crude, not age-adjusted.</li>
<li>Connecticut and Kalawao have no SAHIE values, so their covariates are filled with medians.</li>
<li>Geography follows the CDC file, not the newest Census names. Connecticut is the 8 old counties, not the 9 planning regions, and their population is the 2020 county figure scaled to the state's 2024 growth. Valdez-Cordova (Alaska) is the area the Census split in 2019, merged back together. A "(CA)" after a name marks a census area. Search finds Kusilvak and Oglala Lakota under the file's older names.</li>
<li>The state rate on a card is the model's own: county medians weighted by population. It can run a little below the rate from the CDC state total, so the state card shows both when the file allows. The chance above the state rate is measured against the model's rate.</li>
<li>A hidden county's own data say only "1 to 9," so its estimate rests mostly on covariates, neighbors and the state total.</li>
<li>Not for inferring individual risk.</li>
</ul>
</details>
</div>
</section>

<section class="ex-section" id="methods">
<div class="ex-prose">
<h2>Method and downloads</h2>
<p>We fit a county-level Poisson model with a spatial term to the public CDC counts, then checked it against state totals. Sources and checks are in the notes below.</p>
</div>

<details class="ex-methods ex-wide">
<summary><span>Methods, sources and checks</span></summary>
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
