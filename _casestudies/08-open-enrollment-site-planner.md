---
title: Where to hold your open enrollment events
subtitle: "Uninsured people by neighborhood, and what they could enroll in"
description: >-
  A tract-level estimate of uninsured people by what they could enroll in, with
  ranges, and a planner that places 1 to 8 enrollment sites to reach the most.
  Public data only.
layout: example
modal-id: 8
redirect_from:
  - /casestudies/08-us-county-uninsured-rates/
date: 2026-10-23T00:00:00.000Z
thumbnail: example-county-thumbnail.webp
kind: example
persona: For enrollment assisters
need: >-
  Which neighborhoods in my county hold the most uninsured people who could get
  coverage, split by what they could enroll in, how sure are we, and where
  should my 3 to 6 event sites go to reach the most of them before the
  deadlines?
question: >-
  Where in your county are the uninsured people who could enroll, and where
  should 3 to 6 event sites go?
hero_note: "An example on public data, not client work. No personal information."
brief: >-
  One tract's count of uninsured people is too noisy to rank on. We borrow from
  nearby tracts and the county, split the estimate by what people could enroll
  in, and pick event sites that reach the most. Every estimate has a range.
stats:
  - value: 14.8 million
    label: uninsured people who could enroll
    note: Modeled. Range 14.2 to 15.5 million
    kind: estimate
  - value: 50%
    label: of eligible people reached by 5 venues
    note: "Modeled, distance-weighted. Middle half 38% to 62%"
    kind: estimate
  - value: 22%
    label: more reach than picking by tract count
    note: "Modeled, planner's own rule. Middle half 11% to 39%"
    kind: estimate
sections:
  - id: tool
    label: Your county
  - id: tracts
    label: Tracts
  - id: sites
    label: Sites
  - id: limits
    label: Limits
  - id: methods
    label: Method
downloads:
  - title: Tract table
    file: /downloads/08-open-enrollment-site-planner-tract-table.csv
    type: CSV
    size: 8.5 MB
    description: Every tract, by group, with 90% ranges.
  - title: County table
    file: /downloads/08-open-enrollment-site-planner-county-table.csv
    type: CSV
    size: 639 KB
    description: County totals, SAHIE comparison and plan selections.
  - title: Codebook
    file: /downloads/08-open-enrollment-site-planner-tables-codebook.csv
    type: CSV
    size: 19 KB
    description: What each column means and its source.
  - title: Example plan
    file: /downloads/08-open-enrollment-site-planner-example-plan.xlsx
    type: XLSX
    size: 31 KB
    description: Five-site plan for Comal County, Texas, with staff formulas.
cta:
  heading: Planning enrollment events in your county?
  text: >-
    Tell us your county and your sites. We would build the plan around them.
  button: Tell us about your program
data: /assets/examples/08/data.json
extra_css:
  - href: "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/5.6.0/maplibre-gl.min.css"
    integrity: >-
      sha512-ThCFU5nYVz8ubpOnjGHNGrTjZimTQ63X6t4een1DAWfKP8t39iSw2x3WlUr8EkePjBj48HeNkrAg9t9GRu+s2w==
  - /assets/examples/08/page.css
extra_scripts:
  - src: "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
    integrity: >-
      sha512-4UKI/XKm3xrvJ6pZS5oTRvIQGIzZFoXR71rRBb1y2N+PbwAsKa5tPl2J6WvbEvwN3TxQCm8hMzsl/pO+82iRlg==
  - src: "https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/5.6.0/maplibre-gl.min.js"
    integrity: >-
      sha512-UYgyVPlwHX0hwNIQk1W9mgdRepPxiOBEYqCcrIk85RKL6lh3YHujSSG2hf4RnCbRpPXfmJN5TtyauQWTV/wFEA==
  - /assets/examples/08/page.js
---

[code]: https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/08-open-enrollment-site-planner

<section class="ex-section" id="tool">
<div class="ex-prose ex-toolhead" markdown="1">

## Plan your enrollment sites

</div>

<div class="ex-wide ex-panel">
<div class="ex-tool ex-tool--split p8-tool">

<div class="ex-tool__controls">
<div class="p8-pick">
<div id="pick-state"></div>
<div id="pick-county"></div>
</div>

<div class="ex-field">
<label class="ex-label" for="f-sites">Number of sites</label>
<div class="ex-range"><input id="f-sites" type="range" min="1" max="8" step="1" value="5"><output for="f-sites"></output></div>
</div>

<p class="ex-hint" id="state-hint" hidden></p>

<div class="p8-moves" id="p8-moves">
<fieldset class="ex-field p8-who">
<legend class="ex-label">Who counts</legend>
<label class="ex-check"><input type="checkbox" name="who" value="kids" checked><span>Children</span><span class="ex-check__n" id="n-kids"></span></label>
<label class="ex-check"><input type="checkbox" name="who" value="medicaid" checked><span>Medicaid range</span><span class="ex-check__n" id="n-medicaid"></span></label>
<label class="ex-check"><input type="checkbox" name="who" value="subsidy" checked><span>Subsidy range</span><span class="ex-check__n" id="n-subsidy"></span></label>
<label class="ex-check"><input type="checkbox" name="who" value="gap"><span>Coverage gap</span><span class="ex-check__n" id="n-gap"></span></label>
<label class="ex-check"><input type="checkbox" name="who" value="d400"><span>400% and over</span><span class="ex-check__n" id="n-d400"></span></label>
</fieldset>
<p class="ex-hint" id="cal-line"></p>
</div>

<details class="ex-notes p8-more">
<summary>About these inputs</summary>
<div class="p8-more__body">
<div class="ex-field">
<label class="ex-label" for="f-miles">How far people will travel</label>
<div class="ex-input-group"><input class="ex-input" id="f-miles" type="number" inputmode="decimal" min="1" max="25" step="0.5" aria-describedby="h-miles"><span class="ex-affix">miles</span></div>
<div class="ex-hint" id="h-miles"></div>
</div>

<fieldset class="ex-field">
<legend class="ex-label">Where sites can go</legend>
<div class="ex-seg" id="seg-mode">
<label><input type="radio" name="mode" value="venue" checked><span>Venues</span></label>
<label><input type="radio" name="mode" value="popup"><span>Any tract</span></label>
</div>
<div class="ex-hint" id="h-mode"></div>
</fieldset>

<div class="ex-field">
<label class="ex-label" for="f-nc">Noncitizen adults counted</label>
<div class="ex-range"><input id="f-nc" type="range" min="0" max="70" step="5" value="0" aria-describedby="h-nc"><output for="f-nc"></output></div>
<div class="ex-hint" id="h-nc"></div>
</div>

<div class="ex-field">
<label class="ex-label" for="f-scen">More uninsured than the survey shows</label>
<div class="ex-range"><input id="f-scen" type="range" min="0" max="30" step="5" value="0" aria-describedby="h-scen"><output for="f-scen"></output></div>
<div class="ex-hint" id="h-scen"></div>
</div>

<div class="ex-field">
<div id="pick-existing"></div>
<ul class="p8-existing" id="used-list" aria-label="Sites you already use"></ul>
</div>

<dl class="p8-defs" id="tier-defs"></dl>
</div>
</details>

<p class="ex-actions"><button class="ex-link" type="button" id="reset">Reset</button></p>
</div>

<div class="ex-tool__out">
<div class="ex-results" id="results" aria-live="polite">
<div class="ex-result ex-result--lead">
<span class="ex-result__label" id="r1-label">People reached, weighted by distance</span>
<span class="ex-result__value" id="r1">--</span>
<span class="ex-result__range" id="r1-range"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="r2-label"></span>
<span class="ex-result__value" id="r2">--</span>
<span class="ex-result__range" id="r2-range"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="r3-label"></span>
<span class="ex-result__value" id="r3">--</span>
<span class="ex-result__range" id="r3-range"></span>
</div>
</div>

<p class="ex-hint" id="r-hint"></p>
<p class="ex-hint" id="msg" role="status" hidden></p>

<ol class="p8-sites" id="site-list" aria-label="Sites in the plan"></ol>

<p class="ex-actions">
<button class="ex-link" type="button" id="dl-call">Download call sheet</button>
<button class="ex-link" type="button" id="dl-book">Download workbook</button>
<button class="ex-link" type="button" id="copy-need" data-ex-copy-from="#need-text">Copy need statement</button>
</p>

<figure class="ex-figure" id="fig-map" aria-labelledby="t-map">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-map">Uninsured people who could enroll, by tract</h3>
</div>
<ul class="ex-legend" aria-label="Map key">
<li><span class="p8-key p8-key--bubble" aria-hidden="true"></span>People in a tract (modeled)</li>
<li><span class="p8-key p8-key--site" aria-hidden="true"></span>Site</li>
<li><span class="p8-key p8-key--ring" aria-hidden="true"></span>Reach limit</li>
</ul>
<p class="ex-hint">Rings overlap where tracts are dense; each person counts once.</p>
<div class="ex-map" id="chart-map"></div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the map</span></summary>
<p id="map-def"></p>
<p class="ex-source">Source: ACS 2020-2024 5-year tables C27016 and B27020; CDC PLACES 2025; Census SAHIE 2024; ACS 2024 PUMS; IMLS and HRSA site files; Primordial Analytics model. County shapes: us-atlas 3.0.1 (Census).</p>
<div id="table-tracts"></div>
</details>
</figure>

<details class="ex-notes" id="full-plan">
<summary>Full plan</summary>
<div class="p8-staff">
<div class="ex-field"><label class="ex-label" for="f-staff">People at each event</label><input class="ex-input" id="f-staff" type="number" inputmode="numeric" min="1" step="1"></div>
<div class="ex-field"><label class="ex-label" for="f-apd">Appointments a person does in a day</label><input class="ex-input" id="f-apd" type="number" inputmode="numeric" min="1" step="1"></div>
<div class="ex-field"><label class="ex-label" for="f-dpw">Days a week each site is open</label><input class="ex-input" id="f-dpw" type="number" inputmode="numeric" min="1" max="7" step="1"></div>
<div class="ex-field"><label class="ex-label" for="f-weeks">Weeks to plan for</label><input class="ex-input" id="f-weeks" type="number" inputmode="decimal" min="0" step="1"></div>
</div>
<p id="staff-line"></p>
<div id="table-sites"></div>
<p id="selections-line"></p>
</details>

<details class="ex-notes" id="need-box">
<summary>Need statement</summary>
<div id="need-text" class="p8-need"></div>
</details>
</div>

</div>
</div>
</section>

<section class="ex-section" id="tracts">
<div class="ex-prose" markdown="1">

## A tract's own count is too noisy to rank

On a typical tract with 50 or more adults in this group, the survey's margin of error is <span data-n="numbers.observed.median_moe_pct_of_estimate_50_plus" data-f="pct0">85%</span> of its estimate. Pooling with nearby tracts and the county cuts the typical range by <span data-n="numbers.tracts.interval_width_reduction_pct" data-f="pct0">56%</span>.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-tracts" aria-labelledby="t-tracts">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-tracts">Uninsured adults at or below 138% of poverty</h3>
</div>
<div class="ex-chart" id="chart-tracts"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Ranking.</strong> At equal 90% coverage in a simulation, <span data-n="numbers.tracts.rankable_adults_le138.equal_90pct_simulated_coverage.model" data-f="fpct0">11%</span> of tracts can be told apart from the county median with the model, <span data-n="numbers.tracts.rankable_adults_le138.equal_90pct_simulated_coverage.direct" data-f="fpct0">4%</span> with the survey's counts. At the published intervals the survey separates <span data-n="numbers.tracts.rankable_adults_le138.published_intervals.direct" data-f="fpct0">19%</span> and the model <span data-n="numbers.tracts.rankable_adults_le138.published_intervals.model" data-f="fpct0">12%</span>, but its intervals cover the truth only <span data-n="numbers.validation.D_simulation.L.direct_coverage90" data-f="fpct0">83%</span> of the time.</p>
</div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the tracts chart</span></summary>
<p id="tracts-def"></p>
<p><span data-n="numbers.observed.tracts_reporting_zero_among_100_or_more_pct" data-f="pct1">11.6%</span> of tracts with 100 or more adults in this group report exactly zero. <span data-n="numbers.observed.adults_in_tracts_with_cv_over_30_pct" data-f="pct0">91%</span> of these adults live in tracts whose own standard error is over 30% of the estimate.</p>
<p id="width-note"></p>
<p class="ex-source">Source: ACS 2020-2024 5-year table C27016; Primordial Analytics model.</p>
<div id="table-tr"></div>
</details>
</figure>
</section>

<section class="ex-section" id="sites">
<div class="ex-prose" markdown="1">

## Picking sites for reach gives <span data-n="numbers.sites.lead.median_gain_pct" data-f="pct0n">22</span>% more reach than picking by count

A site near the busiest tract may not reach the most people. We pick venues by reach and count each person once.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-sites" aria-labelledby="t-sites">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-sites">Share of eligible people reached by 5 sites</h3>
</div>
<div class="ex-toolbar">
<fieldset class="ex-field">
<legend class="ex-label">Sites at</legend>
<div class="ex-seg" id="seg-sites">
<label><input type="radio" name="sitesmode" value="venue" checked><span>Venues</span></label>
<label><input type="radio" name="sitesmode" value="popup"><span>Any tract</span></label>
</div>
</fieldset>
</div>
<div class="ex-chart" id="chart-sites"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>By construction.</strong> Every way is scored with the planner's reach rule, so best reach wins. <span id="nodisc-s">Without the overlap discount the median gain is <span id="n-nodisc"></span>%.</span></p>
<p class="ex-note"><strong>The model.</strong> Choosing by the model's count instead of the survey's changes reach little: median <span id="n-mod-med"></span>%, middle half <span id="n-mod-q1"></span>% to <span id="n-mod-q3"></span>%.</p>
</div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the sites chart</span></summary>
<p id="sites-def"></p>
<p>This chart's setting is separate from the planner's.</p>
<p id="sites-extra"></p>
<p>At venues the planner's rule comes within <span data-n="numbers.sites.greedy_vs_exact.median_gap_pct" data-f="pct1">1.5%</span> of the exact best plan, median of <span data-n="numbers.sites.greedy_vs_exact.counties" data-f="int">50</span> counties.</p>
<p>On simulated truth, plans chosen by the model's count did better than plans chosen by the survey's count in <span data-n="numbers.validation.E1_regret.share_counties_model_better_pct" data-f="pct0n">50</span>% of <span data-n="numbers.validation.E1_regret.counties" data-f="int">20</span> counties.</p>
<p class="ex-source">Source: Primordial Analytics model; IMLS FY2023 library outlets and HRSA health center sites as venues.</p>
<div id="table-sites-all"></div>
</details>
</figure>
</section>

<section class="ex-section" id="limits">
<div class="ex-prose" markdown="1">

## Six limits on these numbers

<ul class="ex-limits">
<li>A plan is a scenario, not a forecast of who will come.</li>
<li>The survey years are 2020 to 2024, before the 2026 drop in enrollment.</li>
<li>Noncitizens are shown apart because the data cannot tell who is eligible.</li>
<li>Distance is straight-line, with no transit, hours or language.</li>
<li>Libraries and health centers stand in for where assisters can meet people.</li>
<li>Tract ranks are guidance. Many tracts cannot be told apart.</li>
</ul>

</div>

<details class="ex-notes p8-detail">
<summary>Detail on each limit</summary>
<div class="ex-prose" markdown="1">

- **A model, not a count.** The groups are probabilities from the model. Nothing here says anything about a person.
- **Survey years.** Coverage may have changed since 2024: SAHIE 2024 is one year, the ACS is a five-year pool, and 2026 plan selections are not effectuated enrollment.
- **Noncitizens.** The share of noncitizen adults by income comes from a one-year survey ratio at state or division level, applied to every tract in it, and the survey cannot tell green card holders from others. The tool counts none of them unless you move the slider. A plus or minus 30% change in the odds moves the national noncitizen total from <span data-n="numbers.national.scenarios.envelope.noncit.min" data-f="mil">5.3 million</span> to <span data-n="numbers.national.scenarios.envelope.noncit.max" data-f="mil">6.9 million</span>.
- **2027 federal rules.** Work requirements and the new limits on immigrant eligibility are not modeled. The groups use income only.
- **Where assisters meet people.** CMS Find Local Help has no bulk file, so your existing sites are not known. Libraries and health center sites stand in. Some libraries will have closed.
- **PLACES.** The CDC file is modeled from the same survey, so its link to our estimates is partly built in. Kentucky and Pennsylvania have no values in the 2025 release.
- **SAHIE.** We use it as an input and a soft benchmark, so agreement with it proves little. The independent check refits without it: <span data-n="numbers.validation.B_sahie_independent_refit.L.interval_overlap_share" data-f="fpct0">81%</span> of counties overlap for low-income adults.
- **Rules typed in.** The Medicaid expansion list, the list of states that run their own marketplace and the HealthCare.gov dates are typed constants with sources and dates in the methods. The page gives no dates for those states. Wisconsin and Georgia have waiver programs.
- **The plan range.** It combines tract ranges and a county factor. In a test on 20 counties, <span data-n="numbers.validation.E2_browser_interval.greedy_5.mean_share_of_draws_inside_interval_pct" data-f="pct0">90%</span> of simulated outcomes fell inside it for a 5-site plan at the default distance and <span data-n="numbers.validation.E2_browser_interval.greedy_5_largest_radius.mean_share_of_draws_inside_interval_pct" data-f="pct0">77%</span> at the longest. For other groups, distances, scenarios and your own sites the tool calls it a rough range.
- **The headline range.** <span data-n="numbers.national.scenarios.envelope.elig.min" data-f="mil">14.2 million</span> to <span data-n="numbers.national.scenarios.envelope.elig.max" data-f="mil">15.5 million</span> comes from switching the SAHIE benchmark and the noncitizen odds. It is wider than the draws' own interval, which only counts sampling and model noise.

</div>
</details>
</section>

<section class="ex-section" id="methods">
<div class="ex-prose">
<h2>Method and downloads</h2>
<p>We combined public Census, CDC, HRSA and library files and fitted a model that borrows from nearby tracts. Sources and checks are in the notes below.</p>
</div>
<details class="ex-methods ex-wide">
<summary><span>Methods, sources and checks</span></summary>
<div class="ex-methods__body">

<div class="ex-prose" markdown="1">

Everything on this page comes from `analysis/08-open-enrollment-site-planner` in the [site repository][code], and every number is in its `numbers.json`. The planner in the tool runs the same reach rule as the Python code, on tract results computed once.

</div>

<ol class="ex-steps">
<li><strong>Tract table.</strong> ACS 2020-2024 5-year tables C27016 (insured and uninsured by income to poverty, children and adults 19 to 64) and B27020 (by citizenship) for <span data-n="numbers.data_checks.tracts" data-f="int">84,401</span> tracts in the 50 states and DC. Margins of error become standard errors (margin divided by 1.645). CDC PLACES 2025 and Census SAHIE 2024 are inputs to the model.</li>
<li><strong>Small-area model.</strong> For children and three adult income bands, a model on the rate scale, fit for each Census region: the survey's rate is the true rate plus sampling error, and the true rate is a function of the inputs plus a county effect and a tract effect. The sampling error comes from a smoothed function of cell size and rate, so a zero count gets a real range. We keep <span data-n="numbers.run.draws" data-f="int">1,000</span> draws per tract.</li>
<li><strong>Calibration and benchmark.</strong> County totals are scaled to the survey's own totals. A county outside SAHIE's 90% interval is moved to its nearest edge. The survey and SAHIE differ by more than the draws' interval, so the headline range is the spread across the benchmark on and off and the noncitizen odds at three values.</li>
<li><strong>Groups.</strong> Each tract's people are split by what they could enroll in, with the rules under Groups below. Adults at or below 138% are split at 100% from the tract's own two bands.</li>
<li><strong>Noncitizens.</strong> The tract's noncitizen share of the uninsured (all ages) is moved by state-by-income-band odds from the ACS 2024 person file. Small states take their Census division's odds. The tool counts none unless you move the slider.</li>
<li><strong>Tract ranges.</strong> In a simulation, any group whose tract range covered the truth less than 88% of the time is widened until it covers 90%. The coverage after widening is in the codebook.</li>
<li><strong>Sites.</strong> A site reaches a tract with weight exp(-2 (d / R)^2) up to R miles, where d is straight-line miles times 1.3. A tract at the limit counts <span data-n="derived.limit_weight_pct" data-f="pct0">14%</span> of its people, so this is a distance-weighted count, not a headcount of who will come. A tract's share is the sum over sites, capped at 1, so one person is counted once. The planner adds sites one at a time, each the one that adds the most reach.</li>
<li><strong>The plan range.</strong> Tract ranges are combined as if tracts were independent, then multiplied by a county factor from the draws. For groups other than the default the range uses the sum of the groups' spreads, so it is an upper bound.</li>
<li><strong>Comparing ways to choose.</strong> In <span data-n="numbers.sites.counties" data-f="int">300</span> counties with the most tracts among those with 8 or more venues, we chose 5 sites by highest rate, highest survey count, highest model count and best reach, and scored each with the same rule.</li>
</ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Groups</h3>
<dl class="ex-sources" id="rules-list"></dl>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Checks</h3>
<ol class="ex-steps" id="checks-list"></ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Dates and rules typed in</h3>
<dl class="ex-sources" id="facts-list"></dl>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
<dl class="ex-sources">
<dt>ACS 2020-2024 5-year tables C27016 and B27020</dt>
<dd><a href="https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/">Census table-based summary files</a>. Tract counts and margins of error. Downloaded 2026-10-23.</dd>
<dt>ACS 2024 1-year PUMS</dt>
<dd><a href="https://www2.census.gov/programs-surveys/acs/data/pums/2024/1-Year/csv_pus.zip">Person file</a>. Used only for the noncitizen share by state and income band. Downloaded 2026-10-23.</dd>
<dt>Census SAHIE 2024</dt>
<dd><a href="https://www.census.gov/programs-surveys/sahie.html">Program page</a>. County uninsured rates by income band, from administrative records.</dd>
<dt>CDC PLACES 2025 release</dt>
<dd><a href="https://data.cdc.gov/resource/cwsq-ngmh.csv">data.cdc.gov</a>. Lack of health insurance, adults 18 to 64, by tract. Modeled by CDC; Kentucky and Pennsylvania are absent.</dd>
<dt>CMS 2026 Open Enrollment county file</dt>
<dd><a href="https://www.cms.gov/files/zip/2026-oep-county-level-public-use-file.zip">County public use file</a>. Plan selections, not effectuated enrollment; HealthCare.gov states only.</dd>
<dt>HRSA health center sites and IMLS libraries</dt>
<dd><a href="https://data.hrsa.gov/data/download">HRSA download page</a> and <a href="https://www.imls.gov/sites/default/files/2025-08/pls_fy2023_csv.zip">IMLS Public Libraries Survey file</a>, FY2023 outlets. Some will have closed.</dd>
<dt>Census Gazetteer and ZIP-tract relationship file</dt>
<dd><a href="https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html">Tract points</a> and the <a href="https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html">2020 relationship file</a> for the nearest ZIP area.</dd>
<dt>Prior art</dt>
<dd>SHADAC built <a href="https://www.shadac.org/news/minnesota-uninsured-profile-population-duluth-mn-case-study">ZIP-level uninsured profiles for Minnesota navigators</a>. This example goes to the tract, splits by what people could enroll in, and gives ranges.</dd>
</dl>

</div>
</details>
</section>
