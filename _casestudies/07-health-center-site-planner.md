---
title: Which ZIP codes do health centers not reach?
subtitle: "Low-income people no health center reaches, by ZIP code"
description: >-
  A ZIP-level map of low-income residents who are not health center patients,
  with ranges, and a calculator for who a new site would draw. Public data
  only.
layout: example
modal-id: 7
redirect_from:
  - /casestudies/07-health-center-medicaid-share/
date: 2026-10-22T00:00:00.000Z
thumbnail: health-center-site-thumbnail.webp
kind: example
persona: For health center planning and expansion teams
need: >-
  Which ZIP codes hold the most low-income people who are not health center
  patients, how sure are we, and who would a site at this point with this
  capacity draw, from where, and with what payer mix?
question: >-
  Where are the most low-income people that health centers do not reach, and
  who would a new site there draw?
brief: >-
  HRSA reports each health center's patients by ZIP code. We compare them with
  Census counts of low-income residents and fit a model of where a center's
  patients come from. It shows who a new site would draw, not how many: the
  model ranked the 2025 openings poorly, so patient volume is your input. These
  are scenarios with ranges, not forecasts.
stats:
  - value: 51 million
    label: low-income residents where centers reach under 25%
    kind: estimate
    note: Estimate, 80% range 49.8 to 52.4 million
  - value: 65%
    label: of a new site's patients use no center today, in the median ZIP
    kind: estimate
    note: Estimate, ZIPs run from 30% to 88% (10th to 90th percentile)
  - value: 76 of 100
    label: patients of unseen centers in top 20 ZIPs
    kind: observed
    note: Observed, 226 centers held out one at a time
sections:
  - id: tool
    label: Your center
  - id: gaps
    label: Gaps
  - id: checks
    label: Checks
  - id: limits
    label: Limits
  - id: methods
    label: Method
downloads:
  - title: ZIP table
    file: /downloads/07-health-center-site-planner-zip-table.csv
    type: CSV
    size: 5.5 MB
    description: "Reach, people who are not patients and site screening for each ZIP area."
  - title: ZIP table codebook
    file: /downloads/07-health-center-site-planner-zip-table-codebook.csv
    type: CSV
    size: 6.1 KB
    description: What each column in the ZIP table means and its source.
  - title: Site screening workbook
    file: /downloads/07-health-center-site-planner-site-screening.xlsx
    type: XLSX
    size: 4.3 MB
    description: "Enter ZIPs and capacity; get patients, source split and payer mix."
cta:
  heading: Planning a site or a service area?
  text: >-
    Tell us your service area and the decision. We would build the same screen
    for your board.
  button: Tell us about your center
data: /assets/examples/07/data.json
extra_css:
  - /assets/examples/07/page.css
extra_scripts:
  - src: "https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"
    integrity: >-
      sha512-4UKI/XKm3xrvJ6pZS5oTRvIQGIzZFoXR71rRBb1y2N+PbwAsKa5tPl2J6WvbEvwN3TxQCm8hMzsl/pO+82iRlg==
  - /assets/examples/07/page.js
---

[code]: https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/07-health-center-site-planner

<section class="ex-section" id="tool">
<div class="ex-prose ex-toolhead" markdown="1">

## Find the ZIP codes your center misses

</div>

<div class="ex-wide ex-panel">
<div class="ex-tool ex-tool--split p7-tool">

<div class="ex-tool__controls">
<fieldset class="ex-field">
<legend class="ex-label">Start from</legend>
<div class="ex-seg" id="seg-start">
<label><input type="radio" name="start" value="center" checked><span>A center</span></label>
<label><input type="radio" name="start" value="zip"><span>A ZIP</span></label>
<label><input type="radio" name="start" value="point"><span>A point</span></label>
</div>
</fieldset>

<div id="pick-start"></div>

<div class="ex-field">
<label class="ex-label" for="f-cap">Patients a year at the new site</label>
<div class="ex-input-group"><input class="ex-input" id="f-cap" type="number" inputmode="numeric" min="100" max="15000" step="50" aria-describedby="e-cap"><span class="ex-affix">patients</span></div>
<div class="ex-range"><input id="f-capr" type="range" min="100" max="15000" step="100" aria-label="Patients a year, slider"></div>
<div class="ex-error" id="e-cap" hidden></div>
</div>

<p class="ex-hint">Everything runs in your browser.</p>

<details class="ex-notes p7-more">
<summary>About these inputs</summary>
<div class="p7-more__body">
<fieldset class="ex-field">
<legend class="ex-label">Type of center for a new site</legend>
<div class="ex-seg" id="seg-type">
<label><input type="radio" name="ctype" value="0" checked><span>Health center</span></label>
<label><input type="radio" name="ctype" value="1"><span>Special population</span></label>
</div>
<div class="ex-hint" id="h-type"></div>
</fieldset>

<fieldset class="ex-field">
<legend class="ex-label">Rank ZIPs by</legend>
<div class="ex-seg" id="seg-rank">
<label><input type="radio" name="rank" value="people" checked><span>People</span></label>
<label><input type="radio" name="rank" value="share"><span>Share</span></label>
</div>
<div class="ex-hint" id="h-rank"></div>
</fieldset>

<div class="ex-hint" id="h-cap"></div>
<div class="ex-hint" id="h-area"></div>
<div class="ex-hint" id="h-rankn"></div>
</div>
</details>

<p class="ex-actions"><button class="ex-link" type="button" id="reset">Reset</button></p>
</div>

<div class="ex-tool__out">
<p class="ex-hint" id="msg" role="status" hidden></p>

<div class="p7-site" id="site" hidden>
<h3 class="ex-figure__title" id="site-title"></h3>
<div class="ex-results" id="res-site" aria-live="polite">
<div class="ex-result ex-result--lead">
<span class="ex-result__label" id="rs-label">Patients who use no center today</span>
<span class="ex-result__value" id="rs">--</span>
<span class="ex-result__range" id="rs-range"></span>
</div>
<div class="ex-result">
<span class="ex-result__label">Taken from other centers</span>
<span class="ex-result__value" id="rt">--</span>
<span class="ex-result__range" id="rt-range"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="rr-label">Rank among nearby ZIPs</span>
<span class="ex-result__value" id="rr">--</span>
<span class="ex-result__range" id="rr-range"></span>
</div>
</div>
<p class="ex-hint" id="cap-note" hidden></p>
<dl class="p7-pay" id="pay" aria-label="Expected payer mix of the site's patients"></dl>
<p class="p7-line" id="nb-line"></p>
<p class="ex-hint" id="range-note">Ranges cover model and survey error only. On the 2025 openings the observed change fell inside the 80% range for <span data-n="numbers.checks.D.observed_inside_80_interval_params_only" data-f="f0">12%</span> of sites. With all residents as the market, the median share who use no center today is <span data-n="numbers.checks.F.share_new_by_zip_p10_p50_p90.total_population_base.1" data-f="f0">90%</span>, not <span data-n="numbers.projection.share_new_p50_median_zip" data-f="f0">65%</span>.</p>
</div>

<figure class="ex-figure" id="fig-map" aria-labelledby="t-map">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-map">Low-income residents who are not patients, by ZIP</h3>
</div>
<div id="ramp"></div>
<div class="ex-chart p7-map" id="chart-map"></div>
<p class="ex-hint" id="map-hint"></p>
</figure>

<p class="p7-line" id="area-line"></p>

<div class="p7-ziplist" id="ziplist" hidden>
<h3 class="ex-figure__title" id="t-zips"></h3>
<div id="table-zips"></div>
<p class="ex-hint">Campus ZIPs, where 20% or more of residents are college students, come last: the Census counts students as low-income.</p>
<p class="ex-actions"><button class="ex-link" type="button" id="more-zips">Show more</button></p>
</div>

<figure class="ex-figure p7-srcfig" id="fig-src" aria-labelledby="t-src" hidden>
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-src">Where the site's patients would live</h3>
</div>
<div class="ex-chart" id="chart-src"></div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the site</span></summary>
<p id="site-def"></p>
<p class="ex-source">Source: HRSA UDS 2025 and site list; Census ACS 2020-2024 tables C17002 and C27016; Primordial Analytics model.</p>
<div id="table-src"></div>
</details>
<p class="ex-actions">
<button class="ex-link" type="button" id="copy-sum">Copy summary</button>
<button class="ex-link" type="button" id="print-brief">Print brief</button>
<button class="ex-link" type="button" id="dl-table">Download table</button>
<button class="ex-link" type="button" id="b-keep">Keep to compare</button>
</p>
<details class="ex-notes" id="cmp-box" hidden>
<summary>Compare two sites</summary>
<div id="table-cmp"></div>
</details>
</figure>
</div>

</div>
</div>
</section>

<section class="ex-section" id="gaps">
<div class="ex-prose" markdown="1">

## Reach is thinnest in <span id="gap-class">the suburbs</span>

<span data-n="numbers.reach.by_density_class.suburban.share_in_zctas_under_25pct_pct.1" data-f="pct0n" id="g-top">61</span>% of low-income residents there live in ZIPs where centers reach under a quarter of them, against <span data-n="numbers.reach.by_density_class.rural.share_in_zctas_under_25pct_pct.1" data-f="pct0n">55</span>% in rural and <span data-n="numbers.reach.by_density_class.urban.share_in_zctas_under_25pct_pct.1" data-f="pct0n">48</span>% in urban ZIPs.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-gaps" aria-labelledby="t-gaps">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-gaps">Low-income residents in thinly reached ZIPs</h3>
</div>
<div class="ex-chart" id="chart-gaps"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Cut-offs.</strong> Under 10% and under 25% are our thresholds, not an HRSA rule. Reach is low-income patients over low-income residents.</p>
<p class="ex-note"><strong>Range.</strong> Nationally <span data-n="numbers.reach.under_25pct.low_income_residents.0" data-f="mil1">49.8 million</span> to <span data-n="numbers.reach.under_25pct.low_income_residents.2" data-f="mil1">52.4 million</span>, from survey margins and hidden cells. If survey error is shared within a state, <span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.interval_if_acs_errors_shared_within_state.0" data-f="mil1">48.4 million</span> to <span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.interval_if_acs_errors_shared_within_state.2" data-f="mil1">53.7 million</span>.</p>
<p class="ex-note"><strong>2027.</strong> HRSA funded <span data-n="facts.new_access_points_2026.new_sites" data-f="int">415</span> new sites in August 2026, and Medicaid work rules start in 2027. Your neighbors will change. <a href="{{ site.baseurl }}/casestudies/09-health-center-coverage-loss-stress-test/">Example 09</a> has the revenue side.</p>
</div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the gaps chart</span></summary>
<p id="gaps-def"></p>
<p class="ex-source">Source: HRSA UDS 2025 ZIP table; Census ACS 2020-2024 table C17002; Primordial Analytics model. New site funding: <a href="https://content.govdelivery.com/accounts/USHHSHRSA/bulletins/426df8a">HRSA bulletin of 2026-08-27</a>.</p>
<div id="table-gaps"></div>
</details>
</figure>

<details class="ex-notes">
<summary>Notes</summary>
<ul>
<li><span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.uninsured_adults_same_zips_p10_p50_p90.1" data-f="mil1">6.1 million</span> uninsured adults below 200% of poverty live in the ZIPs under 25%.</li>
<li>If each center's patients are not scaled to its share below 200% of poverty, the national figure falls to <span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.if_patients_not_scaled_to_income_share_p10_p50_p90.1" data-f="mil1">47.4 million</span>. At a 20% cut-off it is <span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.at_20pct_p50" data-f="mil1">43.0 million</span>, at 30% <span data-n="numbers.headline.tile_1_residents_where_under_25pct_reached.at_30pct_p50" data-f="mil1">58.0 million</span>.</li>
<li>Patients per low-income resident, all centers: <span data-n="numbers.reach.by_density_class.urban.penetration_p10_p50_p90.1" data-f="f0">32%</span> urban, <span data-n="numbers.reach.by_density_class.suburban.penetration_p10_p50_p90.1" data-f="f0">27%</span> suburban, <span data-n="numbers.reach.by_density_class.rural.penetration_p10_p50_p90.1" data-f="f0">32%</span> rural.</li>
<li><span data-n="numbers.reach.small_zctas.count" data-f="int">19,037</span> ZIP areas with under 1,000 low-income residents (<span data-n="numbers.reach.small_zctas.share_of_residents_pct" data-f="pct1">6.0%</span> of residents) are in the totals but left out of ranked lists. Without them the national figure is <span data-n="numbers.reach.under_25pct_excluding_small.low_income_residents.1" data-f="mil1">47.6 million</span>.</li>
<li>Ranking by people favors large, dense ZIPs. The tool also ranks by share.</li>
</ul>
</details>
</section>

<section class="ex-section" id="checks">
<div class="ex-prose" markdown="1">

## The model finds <span data-n="numbers.headline.tile_3_of_100_patients_in_model_top20" data-f="pct0n">76</span> of 100 patients of centers it never saw

We hid each of <span data-n="numbers.checks.C.centers" data-f="int">226</span> centers and asked for its 20 best ZIPs. The 20 nearest ZIPs find <span data-n="numbers.headline.tile_3_nearest_20_zips_patient_weighted" data-f="pct0n">66</span>. The test on 2025 openings failed: predicted gains ran <span data-n="numbers.checks.D.predicted_over_observed_median" data-f="num1">2.0</span> times the observed ones.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-checks" aria-labelledby="t-checks">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-checks">Patients living in the 20 ZIPs each rule picks</h3>
</div>
<div class="ex-chart" id="chart-checks"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>Openings.</strong> On <span data-n="numbers.checks.D.sites_evaluated" data-f="int">272</span> sites opened in 2025 the model ranked them poorly (rank correlation <span data-n="numbers.checks.D.spearman_predicted_vs_observed" data-f="num2">0.10</span>). That is why capacity is your input.</p>
<p class="ex-note"><strong>HRSA.</strong> For <span data-n="numbers.checks.E.zctas_compared_low_income_penetration" data-f="int">18,436</span> ZIPs, small ones included, our reach correlates <span data-n="numbers.checks.E.pearson_low_income_penetration" data-f="num2">0.89</span> with HRSA's published figure, which checks our joins, not the model.</p>
<p class="ex-note"><strong>Hidden cells.</strong> <span data-n="numbers.hidden_cells.hidden_patients" data-f="k">177,000</span> patients (<span data-n="numbers.hidden_cells.hidden_patients_pct_of_center_totals" data-f="pct1">0.5%</span>) sit in cells HRSA hides. We placed them from exact center totals.</p>
</div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the checks chart</span></summary>
<p id="checks-def"></p>
<p class="ex-source">Source: HRSA UDS 2025 ZIP table and site list; Primordial Analytics model, leave-one-center-out check.</p>
<div id="table-checks"></div>
</details>
</figure>
</section>

<section class="ex-section" id="limits">
<div class="ex-prose" markdown="1">

## Six limits on these numbers

<ul class="ex-limits">
<li>Patients a year is your input. The model ranked the 2025 openings poorly, so nothing here forecasts volume.</li>
<li>Distance is straight-line miles, not drive time or transit. A projection assumes a typical center: staffing, hours and language are not in the data.</li>
<li>Each patient's income is scaled from the center's overall mix, not measured by ZIP.</li>
<li>Data years differ: UDS 2025, ACS 2020-2024, a site list from October 2026.</li>
<li>The Census counts college students as low-income. ZIPs where they are 20% or more of residents are ranked last; elsewhere they still lift the count.</li>
<li>People who are not patients may get care elsewhere. Look-alike centers' patients are not in the data, so their ZIPs look less reached than they are.</li>
</ul>

</div>

<details class="ex-notes p7-detail">
<summary>Detail on each limit</summary>
<div class="ex-prose">
<ul id="limits-list"></ul>
<ul id="limits-more">
<li><strong>Not a ZIP.</strong> <span data-n="numbers.data_checks.visible_patients_via_crosswalk" data-f="int">104,852</span> patients sit in HRSA ZIP codes that are not Census ZIP areas (post office boxes, single-building codes). HRSA's crosswalk places them. <span data-n="numbers.data_checks.zip_rows_mapped_without_acs" data-f="int">42</span> mapped ZIP areas have no Census income table; their <span data-n="numbers.data_checks.visible_patients_mapped_without_acs" data-f="int">103,003</span> patients are counted and left out of the ZIP tables.</li>
<li><strong>Closed sites.</strong> HRSA's file lists open sites only, so the openings test sees what opened and none of what closed.</li>
<li><strong>Small ZIPs.</strong> Rows with under 1,000 low-income residents are marked small. Their survey margins are wide.</li>
<li><strong>Campus ZIPs.</strong> <span data-n="numbers.reach.campus_zctas.count" data-f="int">323</span> ZIP areas where college and graduate students are 20% or more of residents (ACS B14001) are counted in totals and ranked last.</li>
<li><strong>HRSA's rules.</strong> HRSA's own pages for service area competition and new sites could not be read by a script, so none of their dates, points or thresholds are stated here. See <a href="https://www.hrsa.gov/grants/find-funding/HRSA-27-005">HRSA's funding page</a>.</li>
</ul>
</div>
</details>
</section>

<section class="ex-section" id="methods">
<div class="ex-prose">
<h2>Method and downloads</h2>
<p>We combined public HRSA and Census files and fitted a model of where each center's patients live. Sources and checks are in the notes below.</p>
</div>
<details class="ex-methods ex-wide">
<summary><span>Methods, sources and checks</span></summary>
<div class="ex-methods__body">

<div class="ex-prose" markdown="1">

Everything on this page comes from `analysis/07-health-center-site-planner` in the [site repository][code], and every number is in its `numbers.json`. The tool runs the formulas in steps 4 to 6 in your browser on fitted values computed once. Data were downloaded <span data-n="numbers.data_downloaded" data-f="str">2026-10-23</span>.

</div>

<ol class="ex-steps">
<li><strong>Clean and reconcile.</strong> HRSA's UDS 2025 ZIP table has <span data-n="numbers.data_checks.uds_rows" data-f="int">99,299</span> rows for <span data-n="numbers.data_checks.centers" data-f="int">1,356</span> centers. ZIPs are read as text and mapped to Census ZIP areas with HRSA's crosswalk. Cells of 1 to 15 patients are hidden. Each center's hidden cells must add to its Table 4 total minus its visible ZIP total, so we place them with an exact sampler (<span data-n="numbers.hidden_cells.draws_per_center" data-f="int">200</span> draws a center). They hold <span data-n="numbers.hidden_cells.hidden_patients" data-f="int">176,902</span> patients (<span data-n="numbers.hidden_cells.hidden_patients_pct_of_center_totals" data-f="pct1">0.5%</span>). Placement changes small ZIPs a lot (median <span data-n="numbers.hidden_cells.median_change_pct_zctas_under_100_visible" data-f="pct0n">87</span>% for ZIPs with under 100 visible patients) and the national total not at all.</li>
<li><strong>Need.</strong> Low-income residents are under 200% of the federal poverty level (ACS C17002). Uninsured adults 19 to 64 below 200% come from C27016. Margins of error become standard errors (margin divided by 1.645) and we draw <span data-n="page_constants.mc_draws" data-f="int">2,000</span> Monte Carlo samples of them, with an assumed correlation of <span data-n="page_constants.acs_state_corr" data-f="num2">0.25</span> between ZIP areas of a state. ZIP areas under 1,000 low-income residents are marked small and left out of ranked lists.</li>
<li><strong>Reach.</strong> A center's low-income patients in a ZIP are its patients there times its overall share at or below 200% of poverty (Table 4), which assumes a ZIP's mix equals the center's. Reach is low-income patients of all centers over low-income residents. Residents who are not patients are residents minus low-income patients, floored at zero in each ZIP. We also give patients per 100 residents, with no income scaling.</li>
<li><strong>Where patients come from.</strong> A competitive gravity model. Expected patients from ZIP z to center c are L(z) × θ(c) × f(d) / (1 + S(z)), where L is low-income residents, S(z) is the sum of θ × f over all centers, and the 1 is the outside option, people who use no center. Distance d is straight-line miles to the center's nearest permanent site, and f(d) = exp(−(d / ρ)^γ) with one ρ and γ for urban, suburban and rural ZIPs (under <span data-n="numbers.model.density_cuts_per_sq_mile.0" data-f="int">200</span>, <span data-n="numbers.model.density_cuts_per_sq_mile.0" data-f="int">200</span> to <span data-n="numbers.model.density_cuts_per_sq_mile.1" data-f="int">2,000</span>, over <span data-n="numbers.model.density_cuts_per_sq_mile.1" data-f="int">2,000</span> residents per square mile). Each center's θ has a type level, a trend in its number of sites and a random effect. We fit by maximum likelihood, with a Poisson likelihood on visible cells (zeros within 60 miles count) and the chance of 1 to 15 on hidden cells. <span data-n="numbers.data_checks.lookalike_competitors" data-f="int">170</span> look-alike centers compete at a typical θ. Uncertainty comes from <span data-n="numbers.model.bootstrap_sets" data-f="int">100</span> refits that weight each center by an independent Exponential(1) draw.</li>
<li><strong>A new site.</strong> For a site at point x with a typical θ for its type, w(z) = θ × f(d). The draw from ZIP z is L × w / (1 + S + w). People newly reached, taken from the outside option, are L × w / ((1 + S)(1 + S + w)). The rest come from neighbors, and neighbor c loses its expected patients at z times w / (1 + S + w). If the total draw is above the capacity you set, every flow is scaled down to it. A typical θ is the type level at one site plus the median center effect of the fitted single-site centers of that type. For a health center that is <span data-n="numbers.model.typical_theta_new_site.chc" data-f="num2">2.49</span>; a zero effect would give <span data-n="numbers.model.typical_theta_if_center_effect_zero.chc" data-f="num2">3.63</span>, which overstates a new site.</li>
<li><strong>Capacity is an input.</strong> The model's draw for a typical single site is above <span data-n="numbers.projection.capacity_for_screening" data-f="int">5,000</span> patients a year in most ZIPs, against a median real site of <span data-n="numbers.projection.site_size_patients_per_site_p25_p50_p75.1" data-f="int">2,734</span>. We do not publish it as a volume. We publish what does not depend on capacity: the share of patients with no center today, the payer mix, the source ZIPs and what each neighbor loses.</li>
<li><strong>Payer mix.</strong> Patients taken from neighbors keep their ZIP's observed payer mix (hidden cells filled from row totals, shrunk toward the state and density class). Newly reached patients are uninsured at the ACS uninsured share of low-income residents of all ages in the ZIP, and the insured remainder follows the ZIP's observed pattern of Medicaid, Medicare and private insurance. <a href="{{ site.baseurl }}/casestudies/09-health-center-coverage-loss-stress-test/">Example 09</a> turns Medicaid patients into revenue.</li>
<li><strong>Comparison.</strong> A two-step floating catchment area score from the same sites and population, with the best radius (<span data-n="numbers.checks.sfca_vs_gravity.radius_miles" data-f="int">15</span> miles). It has no capacity, no competition among sites, no source split and no payer mix.</li>
<li><strong>What your browser gets.</strong> <span data-n="page_constants.page_sets" data-f="int">24</span> fitted parameter sets, per ZIP area the competition S and low-income residents in each set (quantized), the payer mixes, the six largest neighbors, and <span data-n="numbers.data_checks.sites.permanent_nonschool_delivery" data-f="int">11,917</span> permanent site locations. The same formulas run in Python and in the browser; the run checks them on <span data-n="numbers.tool_checks.browser_formula_vs_python.candidates" data-f="int">200</span> random candidates (largest difference <span data-n="numbers.tool_checks.browser_formula_vs_python.patients_rel" data-f="f1">1.7%</span> of patients). The Excel workbook uses the same sets and agrees with the ZIP table.</li>
</ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Model parameters</h3>
<div id="table-params"></div>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Checks</h3>
<ol class="ex-steps" id="checks-list"></ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Dates and rules typed in</h3>
<dl class="ex-sources" id="facts-list"></dl>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
<dl class="ex-sources" id="sources-list"></dl>

</div>
</details>
</section>

<section class="p7-brief" id="p7-brief"></section>
