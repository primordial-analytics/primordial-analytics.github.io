---
title: Medicaid coverage loss and health center revenue
subtitle: "Who could lose coverage in 2027, and what it costs"
description: >-
  Pick your state and see how many expansion adults could lose Medicaid in 2027
  and what it costs a health center. Public data, not client work.
layout: example
modal-id: 9
date: 2026-10-22T00:00:00.000Z
thumbnail: stress-thumbnail.webp
kind: example
persona: For health center CEOs and CFOs
need: >-
  A range for my own state and center type of how many expansion adult patients
  could lose Medicaid in 2027, how much is administrative versus non-compliance,
  the revenue effect, and which assumptions matter most.
question: >-
  Under CMS's 2027 work-requirement rules, how many of your expansion adults
  could lose Medicaid, and what does it cost your health center?
brief: >-
  Under CMS's 2027 rules, the share of expansion adults who lose Medicaid runs
  from about 10% in Kentucky to 21% in Utah. About 4 in 10 of those losses are
  people who meet the rule but are dropped over paperwork. The tool puts your
  state and center type on that range.
sections:
  - id: tool
    label: Your center
  - id: compare
    label: Compare
  - id: drivers
    label: Drivers
  - id: limits
    label: Limits
  - id: methods
    label: Method
stats:
  - value: About 1 in 6
    label: expansion adults lose Medicaid in a year, nationally
    note: Modeled. Median 15.9%, range 11.7% to 21.6% across draws
  - value: 1.9%
    label: of net revenue lost by the median center
    note: Modeled. Middle 80% of centers 0.7% to 3.5%
  - value: $1.5 billion
    label: net revenue lost a year, 1,042 expansion-state centers
    note: Modeled. Range $0.9 to $2.5 billion
downloads:
  - title: State ranges
    file: /downloads/09-health-center-coverage-loss-stress-test-state-ranges.csv
    type: CSV
    size: 6 KB
    description: Coverage loss, administrative part and revenue effect for all 41 states.
  - title: Peer benchmark
    file: /downloads/09-health-center-coverage-loss-stress-test-peer-benchmark.csv
    type: CSV
    size: 1 KB
    description: Eight peer groups, by size and setting. No center is named.
cta:
  heading: Want this for your health centers?
  text: >-
    Tell us your state and your center type. We will build the same range around
    your own patient and revenue counts.
  button: Get this for my centers
data: /assets/examples/09/data.json
extra_css:
  - /assets/examples/09/page.css
extra_scripts:
  - /assets/examples/09/page.js
---


<section class="ex-section" id="tool">
  <div class="ex-prose ex-toolhead"><h2>See what 2027 could cost your center</h2></div>

  <div class="ex-wide ex-panel">
    <div class="ex-tool ex-tool--split">
      <div class="ex-tool__controls">
        <div id="pick-state"></div>
        <div class="p9-pair">
          <div class="ex-field">
            <label class="ex-label" for="in-pts">Medicaid patients</label>
            <input class="ex-input" id="in-pts" type="text" inputmode="numeric" aria-describedby="hint-pts err-pts" autocomplete="off">
            <div class="ex-error" id="err-pts" role="alert" hidden></div>
          </div>
          <div class="ex-field">
            <label class="ex-label" for="in-rev">Total revenue <span class="p9-opt">(optional)</span></label>
            <div class="ex-input-group">
              <span class="ex-affix">$</span><input class="ex-input" id="in-rev" type="text" inputmode="numeric" aria-describedby="hint-rev err-rev" placeholder="Per year" autocomplete="off">
            </div>
            <div class="ex-error" id="err-rev" role="alert" hidden></div>
          </div>
        </div>
        <p class="ex-hint p9-privacy">What you type stays in your browser.</p>
        <p class="ex-actions"><button class="ex-link" type="button" id="btn-avg">Use the average center</button></p>
      </div>

      <div class="ex-tool__out">
        <div class="ex-results p9-results" id="p9-results" aria-live="polite" aria-atomic="true">
          <div class="ex-result ex-result--lead" id="p9-answer">
            <span class="ex-result__label" id="r3-label">Net revenue at risk a year</span>
            <span class="ex-result__value" id="r3-val">&mdash;</span>
            <span class="ex-result__range" id="r3-range"></span>
          </div>
          <div class="ex-result">
            <span class="ex-result__label" id="r2-label">Adults who lose coverage</span>
            <span class="ex-result__value" id="r2-val">&mdash;</span>
            <span class="ex-result__range" id="r2-range"></span>
          </div>
          <div class="ex-result">
            <span class="ex-result__label" id="r4-label">Share of revenue</span>
            <span class="ex-result__value" id="r4-val">&mdash;</span>
            <span class="ex-result__range" id="r4-range"></span>
          </div>
        </div>

        <div>
          <p class="ex-actions">
            <button class="ex-link" type="button" data-ex-copy-from="#p9-summary" id="btn-copy">Copy summary</button>
            <button class="ex-link" type="button" data-ex-copy="" id="btn-tsv">Copy table</button>
            <button class="ex-link" type="button" id="btn-png">Download slide</button>
            <button class="ex-link" type="button" data-ex-copy="url" id="btn-link">Copy link</button>
          </p>
          <p class="ex-hint" id="p9-png-msg" role="status"></p>
        </div>

        <figure class="ex-figure" id="fig-split" aria-labelledby="split-title">
          <div class="ex-figure__head">
            <h3 class="ex-figure__title" id="split-title"></h3>
            <p class="ex-hint" id="split-warn" hidden></p>
          </div>
          <div class="p9-stack" id="p9-stack" role="img" aria-label="Split of the loss"></div>
          <p class="ex-hint">The paperwork part is administrative loss. Outreach and renewal support could in principle reduce it.</p>
        </figure>

        <details class="ex-notes">
          <summary>Notes, summary and data table</summary>
          <h4 class="ex-h3">Board summary</h4>
          <p id="p9-summary"></p>
          <ul>
            <li id="r1-note"></li>
            <li id="r2-note"></li>
            <li id="r3-note"></li>
            <li id="r5-note"></li>
          </ul>
          <h4 class="ex-h3">The two causes</h4>
          <p id="split-sub"></p>
          <dl class="p9-split-list" id="p9-split-list"></dl>
          <p id="split-cap"></p>
          <p class="ex-source">Source: Primordial Analytics model on CMS interim final rule parameters, ACS 2024 PUMS and CMS renewal data. Not a forecast.</p>
          <div id="table-split"></div>
          <h4 class="ex-h3">How the inputs work</h4>
          <p>Type a state name or 2-letter code. You can type 800K or 30M.</p>
          <p class="ex-hint" id="hint-pts"></p>
          <p class="ex-hint" id="hint-rev"></p>
          <p>The link carries the state only, not your patient or revenue figures. The table pastes into Excel.</p>
        </details>
      </div>
    </div>
  </div>
</section>

<section class="ex-section" id="compare">
  <div class="ex-prose">
    <h2 id="compare-h">Coverage loss differs widely across states</h2>
    <p class="ex-lede">These are medians. Each state's own range is wide, so close ranks mean little.</p>
  </div>

  <figure class="ex-wide ex-figure ex-figure--notes" id="fig-states" aria-labelledby="states-title">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="states-title">States ranked</h3>
    </div>
    <div class="ex-toolbar">
      <fieldset class="ex-field p9-wide-field">
        <legend class="ex-label">Rank by</legend>
        <div class="ex-seg p9-seg-wrap" id="metric-seg">
          <label><input type="radio" name="metric" value="t" checked><span>Coverage loss</span></label>
          <label><input type="radio" name="metric" value="s"><span>Administrative share</span></label>
          <label><input type="radio" name="metric" value="r"><span>% of revenue</span></label>
        </div>
      </fieldset>
    </div>
    <p class="ex-hint" id="states-hint"></p>
    <div class="ex-chart" id="chart-states"></div>
    <p class="ex-actions"><button class="ex-link" type="button" id="btn-all" aria-controls="chart-states" aria-expanded="false"></button></p>
    <div class="ex-sidenotes">
      <p class="ex-note" id="note-spread"></p>
      <p class="ex-note" id="note-cms"></p>
    </div>
  </figure>

  <figure class="ex-wide ex-figure ex-figure--notes" id="fig-peers" aria-labelledby="peers-title">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="peers-title">Revenue lost, by center size and setting</h3>
    </div>
    <p class="ex-hint">Net revenue lost as a share of total revenue, by center size and setting. Click a row to use it as your peer group.</p>
    <div class="ex-chart" id="chart-peers"></div>
    <div class="ex-sidenotes">
      <p class="ex-note"><strong>Range.</strong> The dot is the middle estimate for the median center in each group; the line is the 5th to 95th percentile.</p>
    </div>
  </figure>

  <details class="ex-notes ex-wide">
    <summary>Notes and data tables</summary>
    <h4 class="ex-h3">All states</h4>
    <ul id="compare-notes"></ul>
    <p id="states-sub"></p>
    <p>The line on the selected state is the 5th to 95th percentile. Hover, tap or use the arrow keys to read any state; click, tap or press Enter to use it in the tool above.</p>
    <p class="ex-source">Source: Primordial Analytics model; CMS interim final rule; ACS 2024 PUMS; CMS renewal outcomes; HRSA UDS 2025.</p>
    <div id="table-states"></div>
    <h4 class="ex-h3">Peer centers</h4>
    <p id="peers-lede"></p>
    <p id="peer-basis"></p>
    <p id="peer-more"></p>
    <p class="ex-source">Source: HRSA UDS 2025 (Tables 4, 9D, 9E); Primordial Analytics model.</p>
    <div id="table-peers"></div>
    <p id="hist-cap">The distribution behind the percentile, one row per 0.4 points of net loss as a share of total revenue. The last row holds every center at 7.6% or more. Your position is read off these counts, so it is approximate.</p>
    <div id="table-hist"></div>
  </details>
</section>

<section class="ex-section" id="drivers">
  <div class="ex-prose">
    <h2 id="drv-h">What drives your state's answer</h2>
  </div>

  <figure class="ex-wide ex-figure ex-figure--notes" id="fig-sobol" aria-labelledby="sobol-title">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="sobol-title">Share of uncertainty explained, by input</h3>
    </div>
    <div class="ex-toolbar">
      <fieldset class="ex-field">
        <legend class="ex-label">Answer</legend>
        <div class="ex-seg">
          <label><input type="radio" name="out" value="L" checked><span>Coverage loss</span></label>
          <label><input type="radio" name="out" value="R"><span>Revenue effect</span></label>
        </div>
      </fieldset>
    </div>
    <div class="ex-chart" id="chart-sobol"></div>
    <div class="ex-sidenotes" id="drv-notes"></div>
  </figure>

  <details class="ex-notes ex-wide" id="drivers-details">
    <summary>Notes, data table and one-at-a-time chart</summary>
    <p id="sobol-sub"></p>
    <p id="sobol-cap"></p>
    <p id="drv-more"></p>
    <p class="ex-source">Source: Primordial Analytics model; variance shares (Sobol indices) from 20,000-draw simulations per state.</p>
    <div id="table-sobol"></div>
    <figure class="ex-figure" id="fig-tornado" aria-labelledby="tornado-title">
      <div class="ex-figure__head">
        <h3 class="ex-figure__title" id="tornado-title">One assumption at a time</h3>
        <p class="ex-figure__sub" id="tornado-sub"></p>
        <p class="ex-figure__sub" id="tornado-tag"></p>
      </div>
      <fieldset class="ex-field">
        <legend class="ex-label">Answer</legend>
        <div class="ex-seg">
          <label><input type="radio" name="tout" value="L" checked><span>Coverage loss</span></label>
          <label><input type="radio" name="tout" value="R"><span>Revenue effect</span></label>
        </div>
      </fieldset>
      <div class="ex-chart" id="chart-tornado"></div>
      <p class="ex-caption" id="tornado-cap">For some inputs a higher value lowers the loss, so the filled dot sits to the left of the hollow one.</p>
      <p class="ex-source">Source: Primordial Analytics model, one input moved at a time with the rest at their middle values.</p>
      <div id="table-tornado"></div>
    </figure>
  </details>
</section>

<section class="ex-section" id="limits">
  <div class="ex-prose">
    <h2>Six limits on these numbers</h2>
  </div>
  <div class="ex-wide">
    <ul class="ex-limits">
      <li>Exposure is a proxy: the <span id="lim-exp1">60%</span> expansion share is an assumption.</li>
      <li>The 2023-24 Medicaid unwinding was a different process; Kentucky and Maine are least certain.</li>
      <li>Every state starts January 1, 2027; delays or litigation would change that.</li>
      <li>UDS Table 9D (collections by payer) is blank for many centers, and reporters skew smaller.</li>
      <li>Retroactive coverage, churn, grants and costs are not modeled.</li>
      <li>Your dollars scale your state's per-patient rate; unusual payer mix will sit outside it.</li>
    </ul>
    <details class="ex-notes">
      <summary>Detail on each limit</summary>
      <ul>
        <li>The survey cannot see eligibility group, monthly hours or frailty, so exposure is a proxy, and the <span id="lim-exp">60%</span> expansion share is an assumption.</li>
        <li>The unwinding was a different process and covers all Medicaid and CHIP enrollees, children included. Kentucky and Maine report near-zero procedural terminations for months, a pause or a reporting artifact, so their low administrative figures (<span id="lim-kyme"></span>) are the least certain.</li>
        <li>We assume every state starts January 1, 2027. Delays and litigation can change that.</li>
        <li>Table 9D is blank for <span id="lim-nr"></span> of <span id="lim-all"></span> centers, and the <span id="lim-rep"></span> that report skew smaller. UDS has no margin data.</li>
        <li>Retroactive coverage, churn, grants and costs are not modeled. Peer groups are aggregates; no center is projected.</li>
        <li>Your dollars and share of revenue are your state's per-1,000-patient rates scaled to your Medicaid count. They do not know your payer mix, so a center with an unusual payer mix or revenue base will sit away from its state's range.</li>
      </ul>
    </details>
  </div>
</section>

<section class="ex-section" id="methods">
  <div class="ex-prose">
    <h2>Method and downloads</h2>
    <p>We combined public Medicaid, Census and health center data and ran 20,000 simulations for each state. Sources and checks are in the notes below.</p>
  </div>
  <details class="ex-methods ex-wide">
    <summary><span>Methods, sources and checks</span></summary>
    <div class="ex-methods__body">
      <ol class="ex-steps">
        <li><strong>Reproduce CMS.</strong> CMS applies 12% non-compliance to the 74% of adult-group enrollees who are not excluded or excepted (8.9% of all), then 7% net procedural loss to everyone left (6.4%): 15.3% together. On 20 million adults that is 3.05 million a year, or 2.29 million in fiscal 2027 (three quarters of a year), matching CMS's Table 41. We treat it as an assumption set, not an observation.</li>
        <li><strong>Let states differ.</strong> Each state draws one of CMS's four Table 39 scenarios (weights 50/10/20/20). CMS's exclusion rates are scaled by how a state's Medicaid adults differ from the pooled states in Census survey data: disability, caregiving, American Indian or Alaska Native status, recent birth. The survey cannot identify the adult group, so only each state's ratio to the pooled states is used, pulled toward 1 where the sample is thin.</li>
        <li><strong>Use the unwinding for spread only.</strong> In the 2023-24 renewal data, a state's paperwork loss is the share of people asked for paperwork who were dropped for procedural reasons, and its data matching is the share renewed without asking. State-months with under 1,000 people in the denominator, or a zero count among more, are dropped. A state keeps 75% of its data-matching position and 61% of its paperwork position from the first half of the window to the second, so we carry that share forward and add fresh noise. The unwinding's own level is never used.</li>
        <li><strong>Simulate and price.</strong> 20,000 draws per state. Administrative loss is people who comply or are exempt and are dropped anyway; that split is a model construct, not an observed category. Revenue starts from UDS Medicaid patients 18 and older times an expansion share no public source gives (we use 60%). Each lost adult costs the state's Medicaid payment per patient, less sliding-fee collections from the 70% who keep coming at 70% of their old visit rate. Centers without Table 9D are priced at their state's payment per patient.</li>
      </ol>

      <h3 class="ex-h3" style="margin:2rem 0 1rem">Checks against outside numbers</h3>
      <p><strong>$1,986 Medicaid payment per patient at the 661 reporting centers</strong>, 5% below the $2,097 we derived from <a href="https://data.hrsa.gov/topics/healthcenters/uds/overview/national/table?tableName=9D&amp;year=2025">HRSA's national figures</a>.</p>
      <figure class="ex-figure" id="fig-ne" style="margin-top:2rem">
        <div class="ex-figure__head">
          <h3 class="ex-figure__title" id="ne-title">Nebraska</h3>
          <p class="ex-figure__sub" id="ne-sub"></p>
        </div>
        <div class="ex-chart" id="chart-ne"></div>
        <p class="ex-source">Sources: <a href="https://www.kff.org/medicaid/early-medicaid-work-requirement-insights-from-nebraska/">KFF</a>; Primordial Analytics model.</p>
        <details class="ex-data">
          <summary>Data table for this chart</summary>
          <div id="table-ne"></div>
        </details>
      </figure>

      <h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
      <p>All downloaded 2026-10-22.</p>
      <dl class="ex-sources">
        <dt>CMS interim final rule</dt>
        <dd>Federal Register 2026-11094 (<a href="https://www.federalregister.gov/documents/2026/06/03/2026-11094/medicaid-program-community-engagement-requirement-for-certain-individuals">text</a>). Tables 37 to 41 are images online, so we read them from the PDF.</dd>
        <dt>ACS 2024 PUMS</dt>
        <dd><a href="https://www.census.gov/programs-surveys/acs/microdata.html">Census</a>, for the 40 expansion states and DC. "State" on this page includes DC.</dd>
        <dt>CMS Updated Renewal Outcomes</dt>
        <dd><a href="https://data.medicaid.gov/dataset/e6205a51-e6d7-4849-9882-4483b8a28c41">medicaid.gov</a>, by state and month, March 2023 to March 2024.</dd>
        <dt>HRSA UDS 2025</dt>
        <dd><a href="https://data.hrsa.gov/data/download">Data Downloads</a>: payers (Table 4) for 1,356 centers, collections (Table 9D) for 661 of them.</dd>
      </dl>

      <h3 class="ex-h3" style="margin:2rem 0 1rem">How the driver chart works</h3>
      <p>For each state we draw the 14 inputs 65,536 times and ask how much of the spread in the answer each input explains. That is a variance decomposition (Sobol indices). "On its own" is the share an input explains by itself. "Including interactions" adds what it explains in combination with other inputs, so those shares can add to more than 100%. The one-at-a-time chart moves a single input from its 10th to its 90th percentile for the typical state and holds the rest at their middle values. With everything at the middle the answer is a little different from the median of the draws, because the model is not linear.</p>

      <h3 class="ex-h3" style="margin:2rem 0 1rem">Using the files</h3>
      <p>The state CSV also holds the columns for the what-if workbook. In the <a href="{{ site.baseurl }}/blog/medicaid-what-if-template/">what-if workbook</a>, paste each state's Low, Mid and High work-requirement columns into Inputs C24:E24 and the paperwork columns into C25:E25. The workbook adds them, so the summed Low and High are wider than the model's range (in the median state 1.8 points under and 4.8 points over). The CSV's <code>total_loss_p5</code>, <code>total_loss_p50</code> and <code>total_loss_p95</code> columns hold the modeled range. For C6, divide "expansion adults per 1,000 Medicaid patients" by 1,000 and multiply by your Medicaid patients of all ages.</p>
      <p>Code, method and sources: <a href="https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/09-health-center-coverage-loss-stress-test">analysis/09-health-center-coverage-loss-stress-test</a>. Every number on this page comes from <code>output/numbers.json</code> or the other files in <code>output/</code>, through <code>web_data.py</code>.</p>
    </div>
  </details>
</section>
