---
title: Free clinic demand planner
subtitle: How many sessions to plan for in 2027
description: Public data only. No patient information.
layout: example
modal-id: 11
date: 2026-10-22T00:00:00.000Z
thumbnail: free-clinic-thumbnail.webp
kind: example
persona: For free and charitable clinics
need: >-
  How many more low-income uninsured adults to expect in my county in 2027, and
  how many sessions, volunteers and medication dollars to commit at a stated
  probability.
question: >-
  How many sessions, volunteers and medication dollars will your clinic need in
  2027?
stats:
  - value: 1.64M
    label: More low-income adults uninsured in 2027, all 30 states
    note: >-
      Central scenario. About 25.7% of the 2024 pool (the median of the draws'
      ratios). 80% interval 1.04M to 2.45M.
    kind: estimate
  - value: 40.9%
    label: Median county growth in Medicaid expansion states
    note: "15.0% in the other states, central scenario."
    kind: estimate
  - value: −14.8%
    label: "Paid marketplace enrollment, Feb 2025 to Feb 2026"
    note: "2,152,711 fewer people paid up."
    kind: observed
sections:
  - id: tool
    label: Your clinic
  - id: map
    label: Map
  - id: observed
    label: What changed
  - id: scenarios
    label: Scenarios
  - id: drivers
    label: What moves it
  - id: limits
    label: Limits
  - id: methods
    label: Method
downloads:
  - title: Excel planner
    file: /downloads/11-free-clinic-surge-planner-demand-planner.xlsx
    type: XLSX
    size: 970 KB
    description: >-
      The same formulas as the tool above, live in Excel. Pick your county,
      enter 12 months of visits, and copy the Need statement sheet into an
      application.
  - title: County table
    file: /downloads/11-free-clinic-surge-planner-county-table.csv
    type: CSV
    size: 1.1 MB
    description: >-
      Observed changes, risk flags, ranking and scenario quantiles for all 2,054
      counties.
  - title: County table codebook
    file: /downloads/11-free-clinic-surge-planner-county-table-codebook.csv
    type: CSV
    size: 14 KB
    description: One line for each column of the county table.
cta:
  heading: Want your own intake counts in this?
  text: >-
    Tell us your county and how you track new patients. We will answer your
    questions about the planner. The Excel version is in the downloads above if
    you would rather work on your own.
  button: Ask about your clinic
data: /assets/examples/11/data.json
extra_css:
  - /assets/examples/11/page.css
extra_scripts:
  - src: "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
    integrity: >-
      sha512-4UKI/XKm3xrvJ6pZS5oTRvIQGIzZFoXR71rRBb1y2N+PbwAsKa5tPl2J6WvbEvwN3TxQCm8hMzsl/pO+82iRlg==
  - /assets/examples/11/page.js
---

[aspe]: https://www.aspe.hhs.gov/sites/default/files/documents/f5f29954221d5b5713070ac2541fda8e/aca-enrollment-report-2026-final-version.pdf

[what-if]: {{ site.baseurl }}/blog/medicaid-what-if-template/
[code]: <https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/11-free-clinic-surge-planner>

<section class="ex-section" id="tool">
<div class="ex-prose ex-toolhead" markdown="1">

## Plan your 2027 sessions

Pick your county and enter your last 12 months. The clinic filled in below is made up: replace it with yours. The Excel planner gives the same answer.
{: .ex-lede}

</div>

<div class="ex-wide">
<div class="ex-panel">
<div class="ex-tool ex-tool--split p11-tool">

<div class="ex-tool__controls">
<div class="p11-headrow">
<p class="ex-tool__title">Your clinic</p>
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="reset" aria-label="Reset to the example clinic">Reset</button>
</div>
<p class="ex-hint">Example values are filled in. Nothing you type leaves your browser.</p>

<div id="pick-county"></div>
<div class="p11-try" id="try-row"></div>
<p class="ex-hint" id="cover-note"></p>
<details class="p11-states">
<summary>Which states are covered</summary>
<div class="p11-states__body" id="states-list"></div>
</details>

<div class="ex-field">
<label class="ex-label" for="f-patients">Uninsured adult patients, last 12 months</label>
<div class="ex-input-group"><input class="ex-input" id="f-patients" type="number" inputmode="numeric" min="0" step="any" aria-describedby="e-patients"><span class="ex-affix">patients</span></div>
<div class="ex-error" id="e-patients" hidden></div>
</div>

<div class="ex-field">
<label class="ex-label" for="f-visits">Visits by those patients, last 12 months</label>
<div class="ex-input-group"><input class="ex-input" id="f-visits" type="number" inputmode="numeric" min="0" step="any" aria-describedby="h-visits e-visits"><span class="ex-affix">visits</span></div>
<div class="ex-hint" id="h-visits">Add up your 12 months. The Excel planner asks for each month.</div>
<div class="ex-error" id="e-visits" hidden></div>
</div>

<fieldset class="ex-field">
<legend class="ex-label">Scenario</legend>
<div class="ex-seg" id="seg-scen">
<label><input type="radio" name="scen" value="0"><span>Lower</span></label>
<label><input type="radio" name="scen" value="1" checked><span>Central</span></label>
<label><input type="radio" name="scen" value="2"><span>Higher</span></label>
</div>
<div class="ex-hint" id="gloss-scen" aria-live="polite"></div>
</fieldset>

<fieldset class="ex-field" id="layers-field">
<legend class="ex-label">Include Medicaid work requirements</legend>
<div class="ex-seg" id="seg-layers">
<label><input type="radio" name="layers" value="0" checked><span>Yes</span></label>
<label><input type="radio" name="layers" value="1"><span>No</span></label>
</div>
<div class="ex-hint">Adds adults who lose Medicaid in expansion states. It is a placeholder. <a href="#drivers">What moves your answer</a></div>
</fieldset>

<div class="ex-field">
<label class="ex-label" for="f-cert">How sure you want to be</label>
<div class="ex-range"><input id="f-cert" type="range" min="0" max="2" step="1" value="1" aria-describedby="h-cert"><output for="f-cert"></output></div>
<div class="ex-range__ends"><span>50%</span><span>80%</span><span>95%</span></div>
<div class="ex-hint" id="h-cert"></div>
</div>

<details class="p11-more">
<summary>More settings</summary>
<div class="p11-more__body">
<div class="ex-field">
<label class="ex-label" for="f-rho">New patients, compared with your rate today</label>
<div class="ex-range"><input id="f-rho" type="range" min="0" max="5" step="0.05" aria-describedby="h-rho"><output for="f-rho"></output></div>
<div class="ex-hint" id="h-rho">1.00x means newly uninsured adults come at the rate your current patients do. Replace it with your intake counts.</div>
</div>

<div class="p11-pair">
<div class="ex-field">
<label class="ex-label" for="f-perSession">Patients a session</label>
<input class="ex-input" id="f-perSession" type="number" inputmode="decimal" min="1" step="any" aria-describedby="e-perSession">
<div class="ex-error" id="e-perSession" hidden></div>
</div>
<div class="ex-field">
<label class="ex-label" for="f-weeks">Weeks open a year</label>
<input class="ex-input" id="f-weeks" type="number" inputmode="numeric" min="1" max="52" step="any" aria-describedby="e-weeks">
<div class="ex-error" id="e-weeks" hidden></div>
</div>
<div class="ex-field">
<label class="ex-label" for="f-volPerSession">Volunteers a session</label>
<input class="ex-input" id="f-volPerSession" type="number" inputmode="numeric" min="0" step="any" aria-describedby="e-volPerSession">
<div class="ex-error" id="e-volPerSession" hidden></div>
</div>
<div class="ex-field">
<label class="ex-label" for="f-hoursPerShift">Hours a shift</label>
<input class="ex-input" id="f-hoursPerShift" type="number" inputmode="decimal" min="0" max="24" step="any" aria-describedby="e-hoursPerShift">
<div class="ex-error" id="e-hoursPerShift" hidden></div>
</div>
<div class="ex-field">
<label class="ex-label" for="f-shiftsPerVol">Shifts a volunteer works a year</label>
<input class="ex-input" id="f-shiftsPerVol" type="number" inputmode="numeric" min="1" step="any" aria-describedby="e-shiftsPerVol">
<div class="ex-error" id="e-shiftsPerVol" hidden></div>
</div>
<div class="ex-field">
<label class="ex-label" for="f-medPerVisit">Medication per visit</label>
<div class="ex-input-group"><span class="ex-affix">$</span><input class="ex-input" id="f-medPerVisit" type="number" inputmode="decimal" min="0" step="any" aria-describedby="e-medPerVisit"></div>
<div class="ex-error" id="e-medPerVisit" hidden></div>
</div>
</div>
</div>
</details>
</div>

<div class="ex-tool__out">
<div id="tool-notes" class="p11-notes"></div>

<div id="tool-body" class="p11-body">
<div class="ex-results" id="results">
<div class="ex-result">
<span class="ex-result__label" id="r1-label">Sessions a year</span>
<span class="ex-result__value" id="r1">--</span>
<span class="ex-result__range" id="r1-range"></span>
<span class="ex-result__note" id="r1-note"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="r2-label">Volunteers needed</span>
<span class="ex-result__value" id="r2">--</span>
<span class="ex-result__range" id="r2-range"></span>
<span class="ex-result__note" id="r2-note"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="r3-label">Medication dollars</span>
<span class="ex-result__value" id="r3">--</span>
<span class="ex-result__range" id="r3-range"></span>
<span class="ex-result__note" id="r3-note"></span>
</div>
</div>

<div class="p11-summary">
<p class="p11-summary__line" id="summary-line"></p>
<div class="p11-summary__btns">
<button class="ex-btn ex-btn--gold ex-btn--sm" type="button" id="copy-line" data-ex-copy="">Copy this line</button>
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" data-p11-need data-ex-copy="">Copy funding paragraphs</button>
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="print-plan">Print or save as PDF</button>
</div>
</div>

<figure class="ex-figure" id="fig-sessions">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-sessions">Sessions to plan for</h3>
<p class="ex-figure__sub" id="s-sessions"></p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="p11-key p11-key--est" aria-hidden="true"></span>Selected scenario, modeled</li>
<li><span class="p11-key p11-key--whisker" aria-hidden="true"></span>Range from the lower to the higher scenario</li>
<li><span class="ex-key ex-key--ref" aria-hidden="true"></span>Sessions today</li>
</ul>
<div class="ex-chart" id="chart-sessions"></div>
<figcaption>Each row is a different level of certainty. The bar follows the scenario you picked.</figcaption>
<p class="ex-source">Source: CMS Open Enrollment 2025 and 2026; CMS effectuated enrollment; Census SAHIE 2024; Primordial Analytics model. Scenario inputs are assumptions.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-sessions"></div></details>
</figure>
</div>
</div>

</div>
</div>
</div>

<div class="ex-wide p11-plan" data-needs-plan>
<div class="p11-plan__head">
<h3 class="ex-h3">The full plan</h3>
<div class="p11-plan__btns">
<button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="toggle-steps" aria-expanded="false" aria-controls="plan-steps">Show how we got there</button>
<button class="ex-btn ex-btn--ghost ex-btn--sm p11-only-narrow" type="button" id="toggle-cols" aria-pressed="false">Show all certainty levels</button>
</div>
</div>
<div class="ex-table-wrap p11-full" role="region" tabindex="0" aria-label="Scrollable table of the plan for 2027">
<table class="ex-table p11-table" id="plan-table" data-view="pick">
<caption>Your plan for 2027. Today is your last 12 months.</caption>
<thead><tr><th scope="col">Row</th><th scope="col" data-q="0">Today</th><th scope="col" data-q="1">Even odds (50%)</th><th scope="col" data-q="2">80% sure</th><th scope="col" data-q="3">95% sure</th></tr></thead>
<tbody id="plan-main"></tbody>
<tbody id="plan-steps" hidden></tbody>
</table>
</div>
</div>

<div class="ex-wide" data-needs-plan>
<div class="ex-callout" id="choose">
<p class="ex-callout__title">Choosing between 80% and 95%</p>
<p id="choose-text"></p>
</div>
</div>

<div class="ex-wide p11-need" data-needs-plan>
<div class="p11-need__head">
<h3 class="ex-h3">Draft paragraphs for a funding request</h3>
<button class="ex-btn ex-btn--gold ex-btn--sm" type="button" id="copy-need" data-p11-need data-ex-copy="">Copy the text</button>
</div>
<p class="ex-hint">The same wording as the Need statement sheet in the Excel planner, with the scenario named. Edit it before you send it.</p>
<div id="need-text" class="p11-need__text"></div>
<p class="ex-hint p11-need__check" id="need-check"></p>
</div>
</section>

<section class="ex-section" id="map">
<div class="ex-prose" markdown="1">

## Where the uninsured pool grows fastest

Losses are not spread evenly. The marketplace losses depend on the state, and the Medicaid layer lands only in states that expanded Medicaid. Switch the map between the modeled growth, the number of adults added, and what already happened to plan selections. Click a county to set the planner to it. [Go to the planner](#tool).
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure" id="fig-map">
<div class="ex-toolbar p11-maptools">
<fieldset class="ex-field">
<legend class="ex-label">Show</legend>
<div class="ex-seg" id="seg-metric">
<label><input type="radio" name="metric" value="growth" checked><span>Growth</span></label>
<label><input type="radio" name="metric" value="added"><span>Adults added</span></label>
<label><input type="radio" name="metric" value="obs"><span>Fall in selections</span></label>
</div>
</fieldset>
<fieldset class="ex-field" id="map-scen-field">
<legend class="ex-label">Scenario</legend>
<div class="ex-seg" id="seg-scen2">
<label><input type="radio" name="scen2" value="0"><span>Lower</span></label>
<label><input type="radio" name="scen2" value="1" checked><span>Central</span></label>
<label><input type="radio" name="scen2" value="2"><span>Higher</span></label>
</div>
</fieldset>
<div class="ex-field">
<label class="ex-label" for="zoom-state">Zoom to</label>
<select class="ex-select" id="zoom-state"><option value="">All 30 states</option></select>
</div>
</div>
<p class="ex-hint" id="map-scen-note" hidden>Plan selections are observed, so the scenario does not apply.</p>
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-map"></h3>
<p class="ex-figure__sub" id="s-map"></p>
</div>
<div class="p11-maplegend">
<div id="ramp-map"></div>
<ul class="ex-legend" aria-label="Legend" id="legend-map"></ul>
</div>
<div class="ex-chart p11-map" id="chart-map"></div>
<div class="p11-pin" id="map-pin" hidden>
<p class="p11-pin__title" id="pin-title"></p>
<p class="p11-pin__text" id="pin-text"></p>
<a class="ex-btn ex-btn--gold ex-btn--sm" href="#tool" id="pin-go">See the plan for this county</a>
</div>
<figcaption>Hover, tap or click a county to read it and set the planner to it. On a phone, use Zoom to for your state. With a keyboard, use the county search in the planner and the data table below.</figcaption>
<p class="ex-source">Source: CMS Open Enrollment 2025 and 2026; CMS effectuated enrollment; Census SAHIE 2024; Medicaid.gov; Primordial Analytics model. County shapes: us-atlas 3.0.1 (Census).</p>
<details class="ex-data"><summary>Data table for this map (2,054 counties)</summary><div id="table-map"></div></details>
</figure>

<figure class="ex-wide ex-figure" id="fig-rank">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-rank"></h3>
<p class="ex-figure__sub" id="s-rank"></p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="p11-key p11-key--est" aria-hidden="true"></span>Median county, modeled</li>
<li><span class="p11-key p11-key--dot" aria-hidden="true"></span>Medicaid expansion state</li>
<li><span class="ex-key ex-key--ring" aria-hidden="true"></span>Your state</li>
</ul>
<div class="ex-chart" id="chart-rank"></div>
<div class="p11-figbtn"><button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="toggle-rank" aria-pressed="false">Show all 30 states</button></div>
<figcaption>The 30 HealthCare.gov states. Other states run their own exchanges and are not in the CMS county files.</figcaption>
<p class="ex-source">Source: Primordial Analytics model on CMS, Census and Medicaid.gov data.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-rank"></div></details>
</figure>
</section>

<section class="ex-section" id="observed">
<div class="ex-prose" markdown="1">

## What already changed

In the 2,054 matched counties, plan selections fell 5.4% between the 2025 and 2026 enrollment periods, from 16,662,905 to 15,771,373. Selections at 100 to 200% of poverty fell 3.9%. The larger change is who paid.
{: .ex-lede}

<div class="ex-keyfig">
<span class="ex-keyfig__value">14.8%</span>
<p class="ex-keyfig__text"><strong>Fewer people with paid marketplace coverage.</strong> 87.4% of selections were paid up by February 2025 and 78.7% by February 2026: 2,152,711 fewer people. We estimate 1,344,887 fewer paid adults at 100 to 200% of poverty.</p>
</div>

</div>

<figure class="ex-wide ex-figure" id="fig-states">
<div class="ex-toolbar">
<div class="ex-field">
<label class="ex-label" for="sort-states">Sort states by</label>
<select class="ex-select" id="sort-states">
<option value="paid">Paid share, February 2026</option>
<option value="change">Change in selections</option>
<option value="name">State name</option>
</select>
</div>
</div>
<p class="p11-stateline" id="state-line" hidden></p>
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-states"></h3>
<p class="ex-figure__sub">Low-income plan selections (100 to 200% of poverty) and the share of all selections paid up by February, 30 HealthCare.gov states.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="ex-key ex-key--obs" aria-hidden="true"></span>Change in selections, 2025 to 2026</li>
<li><span class="p11-key p11-key--open" aria-hidden="true"></span>Paid share, Feb 2025</li>
<li><span class="p11-key p11-key--solid" aria-hidden="true"></span>Paid share, Feb 2026</li>
<li><span class="ex-key ex-key--ring" aria-hidden="true"></span>Your state</li>
</ul>
<div class="ex-chart" id="chart-states"></div>
<figcaption>Every state's paid share fell except North Carolina's and West Virginia's. Paid share falls as automatic re-enrollment rises across states (r = −0.76).</figcaption>
<p class="ex-source">Source: CMS Open Enrollment 2025 and 2026; CMS monthly effectuated enrollment, February 2025 and 2026.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-states"></div></details>
</figure>

<div class="ex-prose" markdown="1">

### Your state tells you most of it

States explain 43% of the variance in county change in the 100 to 150% band. For a county's 150 to 200% change, the average of the state's other counties beat the national average and no change (error 0.111 against 0.135 and 0.175). The state's other counties predict your county better than your county's own numbers do.

The counties below fell furthest after adjusting for noise (pulling each county toward its state average), among those with at least 500 selections in 2025. Seven of the ten are in North Carolina.

</div>

<div class="ex-wide">
<div class="ex-table-wrap p11-full" role="region" tabindex="0" aria-label="Scrollable table of the ten counties with the largest fall in selections">
<table class="ex-table" id="top10-table">
<caption>Ten counties with the largest stability-adjusted fall in low-income selections (at least 500 in 2025)</caption>
<thead><tr><th scope="col">County</th><th scope="col">Selections 2025</th><th scope="col">Selections 2026</th><th scope="col">Raw change</th><th scope="col">Adjusted change</th></tr></thead>
<tbody></tbody>
</table>
</div>
</div>

<div class="ex-callout ex-callout--caution">
<p class="ex-callout__title">Read the 43% fall with care</p>
<p>In the state with the 43% fall, some people moved to a <a href="https://healthcare.oregon.gov/Documents/HIMAC%20Materials/2-CY2026%20Assessment%20Analysis%20HIMAC%20FINAL%2006.17.25.pdf">state program</a> for adults at 138 to 200% of poverty rather than becoming uninsured. We did not adjust, so its counties, including the first and third rows of the table, are likely overstated.</p>
</div>
</section>

<section class="ex-section" id="scenarios">
<div class="ex-prose" markdown="1">

## What 2027 could look like

The central scenario adds a median of 1,640,179 uninsured adults at or below 200% of poverty (80% interval 1,039,504 to 2,454,496), about 25.7% of the 2024 pool of 6,364,883 (the median of the draws' ratios). Marketplace losses alone add 965,227; the Medicaid layer alone adds 609,298. These are medians of separate draws, so the two layers do not add up to the total.
{: .ex-lede}

This counts the whole rise from the 2024 baseline, including the losses your last 12 months of visits already hold. The clinic planner above removes that part.

</div>

<figure class="ex-wide ex-figure" id="fig-nat">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-nat"></h3>
<p class="ex-figure__sub">Additional uninsured adults at or below 200% of poverty in 2027 compared with 2024, across 2,054 counties. Lines show the 10th to 90th percentile of 10,000 draws.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="p11-key p11-key--est" aria-hidden="true"></span>Median, modeled</li>
<li><span class="p11-key p11-key--whisker" aria-hidden="true"></span>10th to 90th percentile</li>
</ul>
<div class="ex-chart" id="chart-nat"></div>
<figcaption>The Medicaid layer roughly doubles the higher scenario. Scenario inputs are assumptions, not forecasts.</figcaption>
<p class="ex-source">Source: Primordial Analytics model, 10,000 draws per scenario.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-nat"></div></details>
</figure>

<figure class="ex-wide ex-figure" id="fig-hist">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-hist"></h3>
<p class="ex-figure__sub" id="s-hist"></p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="p11-key p11-key--est" aria-hidden="true"></span>With the Medicaid layer</li>
<li><span class="ex-key ex-key--line-strong" aria-hidden="true"></span>Marketplace losses only</li>
<li><span class="p11-key p11-key--vline" aria-hidden="true"></span>Your county</li>
</ul>
<div class="ex-chart" id="chart-hist"></div>
<figcaption>Marketplace losses alone cluster in one group of counties. The Medicaid layer adds a second group in expansion states. The scenario follows the planner.</figcaption>
<p class="ex-source">Source: Primordial Analytics model. Counties at 95% growth or more are in the last bar.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-hist"></div></details>
</figure>
</section>

<section class="ex-section" id="drivers">
<div class="ex-prose" markdown="1">

## What moves your answer

For the example clinic (480 patients, 1,440 visits and 120 sessions a year, in a county with 5,917 uninsured low-income adults), the central scenario needs 156 sessions at 50% certainty, **174 at 80%** and **196 at 95%**. Going from 80% to 95% costs 22 sessions, 396 volunteer hours and 11 more volunteers.
{: .ex-lede}

Two assumptions move the 80% answer by about 50 sessions each. Each marketplace assumption moves it by 10 sessions or less.

</div>

<figure class="ex-wide ex-figure" id="fig-tornado">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-tornado"></h3>
<p class="ex-figure__sub">Sessions a year at 80% certainty for the example clinic when one assumption moves from its low to its high end. All others stay central.</p>
</div>
<ul class="ex-legend" aria-label="Legend">
<li><span class="p11-key p11-key--est" aria-hidden="true"></span>Sessions with that assumption moved, modeled</li>
<li><span class="ex-key ex-key--ref" aria-hidden="true"></span>Central case</li>
</ul>
<div class="ex-chart" id="chart-tornado"></div>
<figcaption>A larger pool, or more of the 2026 loss already in your visits, means fewer sessions. That is why some bars run the other way.</figcaption>
<p class="ex-source">Source: Primordial Analytics model, example clinic in a mid-sized Medicaid expansion county.</p>
<details class="ex-data"><summary>Data table for this chart</summary><div id="table-tornado"></div></details>
</figure>

<div class="ex-prose" markdown="1">

<div class="ex-callout">
<p class="ex-callout__title">The number you control</p>
<p>The new-patient rate is the weakest link in the model and the one only you can replace. Log new uninsured patients each month, and the month their coverage ended. After three months of 2027, compare your count with the planner's "new patients expected" row and move up or down a scenario. The Excel planner has an intake guide for this.</p>
</div>

</div>
</section>

<section class="ex-section ex-band ex-band--tint" id="limits">
<div class="ex-prose" markdown="1">

## What this does not tell you

</div>

<div class="ex-wide ex-callout" markdown="1">
<p class="ex-callout__title">A planning range, not a forecast</p>

Read these before you put a number in a request.

- **Selections are not paid coverage.** Paid share is observed by state only, and we apply it to every county and income level.
- **Some of the drop is people who never used care.** HHS's [ASPE brief][aspe] estimates 2.6 million improper or phantom enrollments remain after 2.9 million were removed or blocked. Our assumed uninsured share (30% to 70%) absorbs that.
- **Nothing here is causal.** Credit expiry, enrollment cleanup, North Carolina's Medicaid expansion and the economy move the same numbers. Losses are counted from February 2025 against a 2024 baseline, so any change in between is missing.
- **The Medicaid layer is a placeholder.** Hawaii shows the problem: 73% median county growth. Counties with under 500 uninsured low-income adults (785) have unstable growth rates, and the CSV flags them. The map hatches them.
- **The intervals are conditional.** The 80% interval and the 80% and 95% session answers hold within one scenario's assumptions and leave out the spread between scenarios. Nothing here can be checked against outcomes, so an 80% is a statement about our assumptions, not a hit rate.

</div>
</section>

<section class="ex-section" id="methods">
<h2 class="ex-h2">How we did it</h2>
<details class="ex-methods ex-wide">
<summary><span>Methods, validation and sources<small>For the analyst who will check the work</small></span></summary>
<div class="ex-methods__body">

<div class="ex-prose" markdown="1">

Everything on this page comes from `analysis/11-free-clinic-surge-planner` in the [site repository][code], and every number is in its `numbers.json`. The tool above runs the Excel planner's formulas on county results that the model computed once. The page and the workbook use county growth rounded to 4 decimals, so a dollar figure can differ from `numbers.json` by $1 or $2. Sessions, volunteers and hours match.

</div>

<ol class="ex-steps">
<li><strong>Observed.</strong> Selections count everyone who picked a plan, paid or not, so county change is observed, apart from suppressed cells (1 to 10 people), which we redraw at random.</li>
<li><strong>Marketplace layer.</strong> The loss of paid coverage among adults at 100 to 200% of poverty, February 2025 to February 2026 (county selections times the state's paid share), plus further loss after February (4%, 9% or 16%; <a href="https://www.kff.org/affordable-care-act/what-we-know-so-far-about-2026-aca-marketplace-enrollment-premiums-and-deductibles/">KFF projects</a> 2026 paid enrollment averaging 17.5 million), times the share who end up uninsured.</li>
<li><strong>Medicaid layer, expansion states only.</strong> State Medicaid and CHIP enrollment times the 30% who are expansion adults (<a href="https://www.kff.org/medicaid/5-key-facts-about-medicaid-expansion/">KFF</a> reports 31% of Medicaid enrollment in June 2024; our base includes CHIP), split to counties by adults below 138% of poverty, times the share losing coverage under work requirements (13.5%, 28%, 50%, from our <a href="{{ site.baseurl }}/blog/medicaid-what-if-template/">Medicaid what-if post</a>), a phase-in share and the share left uninsured. These are placeholders.</li>
<li><strong>Ranges, not points.</strong> Each assumption is a range, with 10,000 draws per scenario against the 2024 baseline and its 90% margin of error.</li>
<li><strong>Clinic step.</strong> Most of the 2026 marketplace loss is already in a clinic's last 12 months of visits, so only the rest adds to them. We assume 80% is already there; with none, the example needs 186 sessions at 80%, not 174. Visits in 2027 equal visits today times one plus that growth, scaled by the new-patient rate. Public data cannot identify that rate, so the clinic overwrites it with intake counts.</li>
<li><strong>Decision.</strong> Sessions are visits divided by patients a session, rounded up, at the chosen probability. Choosing 80% treats a session of turned-away patients as 4 times as costly as an idle one; 95%, 19 times.</li>
</ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Validation</h3>
<div class="ex-prose" markdown="1">

We predicted each county's 150 to 200% change without that county's own 150 to 200% change, in the 1,529 counties with at least 100 selections in every band and year. The average of the state's other counties beat the national average and no change (error 0.111 against 0.135 and 0.175). Adding the county's own 100 to 150% change trims the error 4.5% more (95% interval 2.0% to 7.2%), and within a state the two bands correlate at only 0.31. We cannot check the 2027 range against outcomes. This tests only whether county change is predictable from the state.

</div>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Scenario assumptions</h3>
<div class="ex-table-wrap p11-full" role="region" tabindex="0" aria-label="Scrollable table of scenario assumptions">
<table class="ex-table">
<caption>Scenario means. Each is a Beta draw, so the spread inside a scenario is part of the 80% interval.</caption>
<thead><tr><th scope="col">Assumption</th><th scope="col">Lower</th><th scope="col">Central</th><th scope="col">Higher</th></tr></thead>
<tbody>
<tr><th scope="row">Lost marketplace coverage that ends uninsured</th><td>30%</td><td>50%</td><td>70%</td></tr>
<tr><th scope="row">Further marketplace loss after February 2026</th><td>4%</td><td>9%</td><td>16%</td></tr>
<tr><th scope="row">Expansion adults who lose Medicaid</th><td>13.5%</td><td>28%</td><td>50%</td></tr>
<tr><th scope="row">Medicaid losers left uninsured</th><td>70%</td><td>85%</td><td>95%</td></tr>
<tr><th scope="row">Share of that loss in place in 2027</th><td>35%</td><td>50%</td><td>65%</td></tr>
</tbody>
</table>
</div>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
<dl class="ex-sources">
<dt>CMS Open Enrollment county files, 2025 and 2026</dt>
<dd><a href="https://www.cms.gov/data-research/statistics-trends-reports/marketplace-products/2026-marketplace-open-enrollment-period-public-use-files">2026 page</a>. Plan selections by income band, premiums, automatic re-enrollment. 2,054 counties match across the HealthCare.gov states; state exchanges such as California and New York are not in them. Downloaded 2026-10-22.</dd>
<dt>CMS monthly effectuated enrollment</dt>
<dd><a href="https://data.cms.gov/summary-statistics-on-beneficiary-enrollment/health-insurance-marketplace/health-insurance-exchanges-monthly-effectuated-enrollment">data.cms.gov</a>. February 2025 and 2026, by state: people who paid. Downloaded 2026-10-22.</dd>
<dt>Census SAHIE 2024</dt>
<dd><a href="https://www.census.gov/programs-surveys/sahie.html">Program page</a>. Uninsured adults 18 to 64 at or below 200% of poverty, with 90% margins of error (median 16% of the estimate). Downloaded 2026-10-22.</dd>
<dt>Medicaid.gov enrollment, June 2026</dt>
<dd><a href="https://download.medicaid.gov/data/pi-dataset-september-2026-release.csv">Download</a>. Used for the Medicaid layer. Downloaded 2026-10-22.</dd>
<dt>File hashes and checks</dt>
<dd>File sizes and hashes are in <code>numbers.json</code>. The county rows sum to 15,771,373 selections; the file's own total row is 24 higher.</dd>
</dl>

</div>
</details>
</section>
