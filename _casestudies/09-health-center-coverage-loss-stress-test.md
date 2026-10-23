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
sections:
  - id: tool
    label: Your center
  - id: states
    label: States
  - id: peers
    label: Peers
  - id: drivers
    label: Drivers
  - id: limits
    label: Limits
  - id: methods
    label: Method
stats:
  - value: 15.9%
    label: National median share of expansion adults who lose Medicaid in a year
    note: "11.7% to 21.6% across draws. CMS's central case is 15.3%."
    kind: estimate
  - value: 41%
    label: Administrative share of the loss, median state
    note: People who comply or are exempt, dropped anyway.
    kind: estimate
  - value: 1.9%
    label: Net revenue lost by the median center, as a share of revenue
    note: 0.8% to 3.5%, 10th to 90th percentile of centers.
    kind: estimate
  - value: $1.5 billion
    label: Net revenue lost a year across 1,042 expansion-state centers
    note: $0.9 to $2.5 billion.
    kind: estimate
downloads:
  - title: State ranges
    file: /downloads/09-health-center-coverage-loss-stress-test-state-ranges.csv
    type: CSV
    size: 6 KB
    description: >-
      Coverage loss, the administrative part, and revenue effect for each of the
      41 states, plus the columns for the what-if workbook.
  - title: Peer benchmark
    file: /downloads/09-health-center-coverage-loss-stress-test-peer-benchmark.csv
    type: CSV
    size: 1 KB
    description: >-
      Revenue effect for eight groups of centers by size and setting. Grouped
      figures only; no center is named.
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


<section class="ex-section p9-toolsec" id="tool">
  <div class="ex-wide">
    <div class="ex-panel p9-panel">
      <div class="ex-tool ex-tool--split">
        <div class="ex-tool__controls">
          <div>
            <h2 class="p9-h2">Your center</h2>
            <p class="p9-lede">Pick your state. Add your Medicaid patients. See what 2027 could cost.</p>
          </div>
          <div id="pick-state"></div>
          <div class="p9-pair">
            <div class="ex-field">
              <label class="ex-label" for="in-pts">Medicaid patients</label>
              <input class="ex-input" id="in-pts" type="text" inputmode="numeric" aria-describedby="hint-pts err-pts" placeholder="Average center" autocomplete="off">
              <div class="ex-error" id="err-pts" role="alert" hidden></div>
            </div>
            <div class="ex-field">
              <label class="ex-label" for="in-rev">Total revenue <span class="p9-opt">(optional)</span></label>
              <div class="ex-input-group">
                <span class="ex-affix">$</span><input class="ex-input" id="in-rev" type="text" inputmode="numeric" aria-describedby="hint-rev err-rev" placeholder="Per year" autocomplete="off">
              </div>
              <div class="ex-error" id="err-rev" role="alert" hidden></div>
              <div class="ex-hint" id="hint-rev"></div>
            </div>
          </div>
          <div class="p9-helpers">
            <p class="ex-hint" id="hint-pts"></p>
            <button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="btn-avg">Use the average center</button>
            <p class="ex-hint">What you type stays in your browser. You can type 800K or 30M.</p>
          </div>
        </div>
        <div class="ex-tool__out">
          <p class="p9-tag" id="p9-tag">Loading</p>
          <div class="p9-results" id="p9-results">
            <div class="p9-answer" id="p9-answer">
              <span class="p9-answer__label" id="r3-label">Net revenue lost per year</span>
              <span class="p9-answer__value" id="r3-val">&mdash;</span>
              <span class="p9-answer__range" id="r3-range"></span>
              <p class="p9-answer__share"><strong id="r4-val">&mdash;</strong> <span id="r4-text"></span></p>
              <span class="p9-answer__note" id="r3-note"></span>
            </div>
            <div class="p9-subs">
              <div class="p9-sub">
                <span class="p9-sub__label" id="r1-label">Expansion adults who lose coverage</span>
                <span class="p9-sub__value" id="r1-val">&mdash;</span>
                <span class="p9-sub__range" id="r1-range"></span>
                <span class="p9-sub__note" id="r1-note"></span>
              </div>
              <div class="p9-sub">
                <span class="p9-sub__label" id="r2-label">Expansion adults at your center who lose coverage</span>
                <span class="p9-sub__value" id="r2-val">&mdash;</span>
                <span class="p9-sub__range" id="r2-range"></span>
                <span class="p9-sub__note" id="r2-note"></span>
              </div>
              <div class="p9-sub">
                <span class="p9-sub__label" id="r5-label">Compared with peer centers</span>
                <span class="p9-sub__value" id="r5-val">&mdash;</span>
                <span class="p9-sub__range" id="r5-range"></span>
                <span class="p9-sub__note" id="r5-note"></span>
              </div>
            </div>
          </div>
          <div class="p9-summary">
            <p class="p9-summary__title">For the board deck</p>
            <p id="p9-summary" class="p9-summary__text"></p>
            <div class="p9-summary__actions">
              <button class="ex-btn ex-btn--ink ex-btn--sm" type="button" data-ex-copy-from="#p9-summary" id="btn-copy">Copy summary</button>
              <button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" data-ex-copy="" id="btn-tsv">Copy numbers as table</button>
              <button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" id="btn-png">Download as slide (PNG)</button>
              <button class="ex-btn ex-btn--ghost ex-btn--sm" type="button" data-ex-copy="url" id="btn-link">Copy link to this state</button>
            </div>
            <p class="ex-hint" id="p9-png-msg" role="status">The link carries the state only, not your patient or revenue figures. The table pastes into Excel.</p>
          </div>
          <div class="p9-cta">
            <p><strong>Want this built on your real patient and payer data?</strong> Tell us your state and center type.</p>
            <a class="ex-btn ex-btn--gold ex-btn--sm" href="{{ site.baseurl }}/#contact">Get this for my centers</a>
          </div>
        </div>
      </div>
      <div class="p9-mini" id="p9-mini" aria-hidden="true"><span id="p9-mini-text"></span><a href="#p9-results" tabindex="-1">Details</a></div>
    </div>
  </div>

  <figure class="ex-wide ex-figure" id="fig-split">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="split-title">Where the loss comes from</h3>
      <p class="ex-figure__sub" id="split-sub"></p>
    </div>
    <div class="p9-stack" id="p9-stack" role="img" aria-label="Split of the loss"></div>
    <dl class="p9-split-list" id="p9-split-list"></dl>
    <figcaption id="split-cap"></figcaption>
    <p class="ex-source">Source: Primordial Analytics model on CMS interim final rule parameters, ACS 2024 PUMS and CMS renewal data. Not a forecast.</p>
    <details class="ex-data">
      <summary>Data table for this figure</summary>
      <div id="table-split"></div>
    </details>
  </figure>
</section>

<section class="ex-section" id="states">
  <div class="ex-wide">
    <div class="ex-prose">
      <h2>How far states differ</h2>
      <p class="ex-lede" id="states-lede">Pick a ranking, then click a state to use it above.</p>
    </div>
  </div>

  <div class="ex-wide ex-toolbar p9-statebar">
    <div id="pick-state-3"></div>
    <fieldset class="ex-field p9-wide-field">
      <legend class="ex-label">Rank the 40 expansion states and DC by</legend>
      <div class="ex-seg p9-seg-wrap" id="metric-seg">
        <label><input type="radio" name="metric" value="t" checked><span>Coverage loss</span></label>
        <label><input type="radio" name="metric" value="s"><span>Administrative share</span></label>
        <label><input type="radio" name="metric" value="r"><span>% of revenue</span></label>
        <label><input type="radio" name="metric" value="d"><span>$ per 1,000 patients</span></label>
      </div>
    </fieldset>
    <div class="ex-field p9-check" id="wrap-ranges">
      <label><input type="checkbox" id="show-ranges"> <span>Show 5th to 95th ranges for every state</span></label>
    </div>
  </div>

  <figure class="ex-wide ex-figure" id="fig-states">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="states-title">States ranked</h3>
      <p class="ex-figure__sub" id="states-sub"></p>
    </div>
    <div class="p9-sel" id="p9-sel" role="group" aria-label="Selected state">
      <div class="p9-sel__body">
        <p class="p9-sel__head"><span class="p9-sel__tag" id="sel-tag">Example</span> <strong id="sel-name"></strong> <span id="sel-rank"></span></p>
        <p class="p9-sel__text" id="sel-text"></p>
      </div>
      <a class="ex-btn ex-btn--ink ex-btn--sm" href="#tool">Open in tool</a>
    </div>
    <p class="p9-hint-line">Hover, tap or use the arrow keys to read a state. Click, tap or press Enter to use it above.</p>
    <ul class="ex-legend" aria-label="Legend">
      <li><span class="ex-key ex-key--est" aria-hidden="true"></span>Median</li>
      <li><span class="p9-key p9-key--sel" aria-hidden="true"></span>Your state</li>
      <li id="states-leg-ci"><span class="p9-key p9-key--band" aria-hidden="true"></span>5th to 95th percentile</li>
      <li><span class="ex-key ex-key--ref" aria-hidden="true"></span><span id="states-leg-ref">Reference</span></li>
    </ul>
    <div class="ex-chart" id="chart-states"></div>
    <figcaption id="states-cap">Model output, not a forecast.</figcaption>
    <p class="ex-source">Source: Primordial Analytics model; CMS interim final rule; ACS 2024 PUMS; CMS renewal outcomes; HRSA UDS 2025.</p>
    <details class="ex-data">
      <summary>Data table for this chart</summary>
      <div id="table-states"></div>
    </details>
  </figure>

  <div class="ex-wide p9-finds" id="finds-states"></div>
</section>

<section class="ex-section ex-band ex-band--tint" id="peers">
  <div class="ex-wide">
    <div class="ex-prose">
      <h2>Where your center sits among peers</h2>
      <p class="p9-plede" id="peers-lede"></p>
    </div>
  </div>

  <div class="ex-wide">
    <div class="ex-panel">
      <div class="p9-peerbar">
        <p class="p9-chip" id="peer-chip"></p>
        <div class="ex-toolbar">
          <div class="ex-field">
            <label class="ex-label" for="sel-size">Your center's total patients, all payers</label>
            <select class="ex-select" id="sel-size"></select>
          </div>
          <fieldset class="ex-field">
            <legend class="ex-label">Setting</legend>
            <div class="ex-seg" id="seg-set"></div>
          </fieldset>
        </div>
        <p class="ex-hint" id="peer-basis"></p>
      </div>
      <p class="p9-readout" id="peer-readout" aria-live="polite"></p>
      <div class="ex-cols" style="--ex-col-min: 26rem">
        <figure class="ex-figure" id="fig-peers">
          <div class="ex-figure__head">
            <h3 class="ex-figure__title" id="peers-title">Eight peer groups</h3>
            <p class="ex-figure__sub">Net revenue loss as a share of total revenue, for the median center in each group. The dot is the middle estimate and the line is the 5th to 95th percentile.</p>
          </div>
          <ul class="ex-legend" aria-label="Legend">
            <li><span class="p9-key p9-key--dot" aria-hidden="true"></span>Middle estimate</li>
            <li><span class="p9-key p9-key--whisker" aria-hidden="true"></span>5th to 95th percentile</li>
            <li><span class="p9-key p9-key--you" aria-hidden="true"></span>Your center</li>
            <li><span class="ex-key ex-key--ring" aria-hidden="true"></span>Your peer group</li>
          </ul>
          <div class="ex-chart" id="chart-peers"></div>
          <figcaption>Click a group to use it as your peer group.</figcaption>
          <p class="ex-source">Source: HRSA UDS 2025 (Tables 4, 9D, 9E); Primordial Analytics model.</p>
          <details class="ex-data">
            <summary>Data table for this chart</summary>
            <div id="table-peers"></div>
          </details>
        </figure>
        <figure class="ex-figure" id="fig-hist">
          <div class="ex-figure__head">
            <h3 class="ex-figure__title" id="hist-title">The centers, one bar per 0.4 points</h3>
            <p class="ex-figure__sub" id="hist-sub">Number of centers by middle-estimate net loss as a share of total revenue.</p>
          </div>
          <ul class="ex-legend" aria-label="Legend">
            <li><span class="ex-key ex-key--est" aria-hidden="true"></span>Centers (modeled)</li>
            <li><span class="ex-key ex-key--ref" aria-hidden="true"></span><span id="hist-leg-med">Median center</span></li>
            <li><span class="p9-key p9-key--you" aria-hidden="true"></span>Your center</li>
          </ul>
          <div class="ex-chart" id="chart-hist"></div>
          <figcaption>The last bar holds every center at 7.6% or more.</figcaption>
          <p class="ex-source">Source: HRSA UDS 2025; Primordial Analytics model. Your position is read off these bars, so it is approximate.</p>
          <details class="ex-data">
            <summary>Data table for this chart</summary>
            <div id="table-hist"></div>
          </details>
        </figure>
      </div>
    </div>
  </div>
</section>

<section class="ex-section" id="drivers">
  <div class="ex-wide">
    <div class="ex-prose">
      <h2>What drives your state's answer</h2>
      <p class="p9-plede" id="drv-lede"></p>
    </div>
  </div>

  <div class="ex-wide ex-toolbar">
    <div id="pick-state-2"></div>
    <fieldset class="ex-field">
      <legend class="ex-label">Answer</legend>
      <div class="ex-seg">
        <label><input type="radio" name="out" value="L" checked><span>Coverage loss</span></label>
        <label><input type="radio" name="out" value="R"><span>Revenue effect</span></label>
      </div>
    </fieldset>
    <div class="ex-field p9-check">
      <label><input type="checkbox" id="show-all"> <span id="show-all-label">Show all inputs</span></label>
    </div>
  </div>

  <figure class="ex-wide ex-figure" id="fig-sobol">
    <div class="ex-figure__head">
      <h3 class="ex-figure__title" id="sobol-title">Drivers</h3>
      <p class="ex-figure__sub" id="sobol-sub"></p>
    </div>
    <ul class="ex-legend" aria-label="Legend">
      <li><span class="ex-key ex-key--est" aria-hidden="true"></span>On its own</li>
      <li><span class="p9-key p9-key--dot-ink" aria-hidden="true"></span>Including interactions with other inputs</li>
    </ul>
    <div class="ex-chart" id="chart-sobol"></div>
    <figcaption id="sobol-cap"></figcaption>
    <p class="ex-source">Source: Primordial Analytics model; variance shares (Sobol indices) from 20,000-draw simulations per state.</p>
    <details class="ex-data">
      <summary>Data table for this chart</summary>
      <div id="table-sobol"></div>
    </details>
  </figure>

  <div class="ex-wide ex-callout p9-ask" id="drv-ask" hidden>
    <p class="ex-callout__title">What to ask</p>
    <ul id="drv-ask-list"></ul>
  </div>

  <div class="ex-wide p9-finds" id="finds-drivers"></div>

  <details class="ex-methods ex-wide" id="tornado-details">
    <summary><span id="tornado-sum">One assumption at a time<small>This chart is for the typical state, not your state</small></span></summary>
    <div class="ex-methods__body">
      <figure class="ex-figure" id="fig-tornado">
        <div class="ex-figure__head">
          <p class="p9-tag p9-tag--typ" id="tornado-tag"></p>
          <h3 class="ex-figure__title" id="tornado-title">One assumption at a time</h3>
          <p class="ex-figure__sub" id="tornado-sub"></p>
        </div>
        <fieldset class="ex-field">
          <legend class="ex-label">Answer</legend>
          <div class="ex-seg">
            <label><input type="radio" name="tout" value="L" checked><span>Coverage loss</span></label>
            <label><input type="radio" name="tout" value="R"><span>Revenue effect</span></label>
          </div>
        </fieldset>
        <ul class="ex-legend" aria-label="Legend" style="margin-top:1rem">
          <li><span class="p9-key p9-key--dot-hollow" aria-hidden="true"></span>Input at its 10th percentile</li>
          <li><span class="p9-key p9-key--dot-ink" aria-hidden="true"></span>Input at its 90th percentile</li>
          <li><span class="ex-key ex-key--ref" aria-hidden="true"></span>Middle estimate</li>
        </ul>
        <div class="ex-chart" id="chart-tornado"></div>
        <figcaption id="tornado-cap">For some inputs a higher value lowers the loss, so the filled dot sits to the left of the hollow one.</figcaption>
        <p class="ex-source">Source: Primordial Analytics model, one input moved at a time with the rest at their middle values.</p>
        <details class="ex-data">
          <summary>Data table for this chart</summary>
          <div id="table-tornado"></div>
        </details>
      </figure>
    </div>
  </details>
</section>

<section class="ex-section ex-band ex-band--tint" id="limits">
  <div class="ex-wide">
    <div class="ex-prose">
      <h2>What this does not tell you</h2>
    </div>
  </div>
  <div class="ex-wide">
    <div class="ex-callout">
      <p class="ex-callout__title">What the numbers rest on</p>
      <ul>
        <li>The survey cannot see eligibility group, monthly hours or frailty, so exposure is a proxy, and the <span id="lim-exp">60%</span> expansion share is an assumption.</li>
        <li>The unwinding was a different process and covers all Medicaid and CHIP enrollees, children included. Kentucky and Maine report near-zero procedural terminations for months, a pause or a reporting artifact, so their low administrative figures (<span id="lim-kyme"></span>) are the least certain.</li>
        <li>We assume every state starts January 1, 2027. Delays and litigation can change that.</li>
        <li>Table 9D is blank for <span id="lim-nr"></span> of <span id="lim-all"></span> centers, and the <span id="lim-rep"></span> that report skew smaller. UDS has no margin data.</li>
        <li>Retroactive coverage, churn, grants and costs are not modeled. Peer groups are aggregates; no center is projected.</li>
        <li>Your dollars and share of revenue are your state's per-1,000-patient rates scaled to your Medicaid count. They do not know your payer mix, so a center with an unusual payer mix or revenue base will sit away from its state's range.</li>
      </ul>
    </div>
  </div>
</section>

<section class="ex-section" id="methods">
  <div class="ex-wide"><h2 class="ex-h2">How we did it</h2></div>
  <details class="ex-methods ex-wide">
    <summary><span>Methods, sources and checks<small>For the analyst who will check the work</small></span></summary>
    <div class="ex-methods__body">
      <ol class="ex-steps">
        <li><strong>Reproduce CMS.</strong> CMS applies 12% non-compliance to the 74% of adult-group enrollees who are not excluded or excepted (8.9% of all), then 7% net procedural loss to everyone left (6.4%): 15.3% together. On 20 million adults that is 3.05 million a year, or 2.29 million in fiscal 2027 (three quarters of a year), matching CMS's Table 41. We treat it as an assumption set, not an observation.</li>
        <li><strong>Let states differ.</strong> Each state draws one of CMS's four Table 39 scenarios (weights 50/10/20/20). CMS's exclusion rates are scaled by how a state's Medicaid adults differ from the pooled states in Census survey data: disability, caregiving, American Indian or Alaska Native status, recent birth. The survey cannot identify the adult group, so only each state's ratio to the pooled states is used, pulled toward 1 where the sample is thin.</li>
        <li><strong>Use the unwinding for spread only.</strong> In the 2023-24 renewal data, a state's paperwork loss is the share of people asked for paperwork who were dropped for procedural reasons, and its data matching is the share renewed without asking. State-months with under 1,000 people in the denominator, or a zero count among more, are dropped. A state keeps 75% of its data-matching position and 61% of its paperwork position from the first half of the window to the second, so we carry that share forward and add fresh noise. The unwinding's own level is never used.</li>
        <li><strong>Simulate and price.</strong> 20,000 draws per state. Administrative loss is people who comply or are exempt and are dropped anyway; that split is a model construct, not an observed category. Revenue starts from UDS Medicaid patients 18 and older times an expansion share no public source gives (we use 60%). Each lost adult costs the state's Medicaid payment per patient, less sliding-fee collections from the 70% who keep coming at 70% of their old visit rate. Centers without Table 9D are priced at their state's payment per patient.</li>
      </ol>

      <h3 class="ex-h3" style="margin:2rem 0 1rem">Checks against outside numbers</h3>
      <div class="ex-keyfig">
        <span class="ex-keyfig__value">$1,986</span>
        <p class="ex-keyfig__text"><strong>Medicaid payment per patient at the 661 reporting centers</strong>, 5% below the $2,097 we derived from <a href="https://data.hrsa.gov/topics/healthcenters/uds/overview/national/table?tableName=9D&amp;year=2025">HRSA's national figures</a>.</p>
      </div>
      <figure class="ex-figure" id="fig-ne" style="margin-top:2rem">
        <div class="ex-figure__head">
          <h3 class="ex-figure__title" id="ne-title">Nebraska</h3>
          <p class="ex-figure__sub" id="ne-sub"></p>
        </div>
        <ul class="ex-legend" aria-label="Legend">
          <li><span class="ex-key ex-key--obs" aria-hidden="true"></span>Observed (KFF)</li>
          <li><span class="p9-key p9-key--dot" aria-hidden="true"></span>Modeled median</li>
          <li><span class="p9-key p9-key--whisker" aria-hidden="true"></span>5th to 95th percentile</li>
        </ul>
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
      <p>In the <a href="{{ site.baseurl }}/blog/medicaid-what-if-template/">what-if workbook</a>, paste each state's Low, Mid and High work-requirement columns into Inputs C24:E24 and the paperwork columns into C25:E25. The workbook adds them, so the summed Low and High are wider than the model's range (in the median state 1.8 points under and 4.8 points over). The CSV's <code>total_loss_p5</code>, <code>total_loss_p50</code> and <code>total_loss_p95</code> columns hold the modeled range. For C6, divide "expansion adults per 1,000 Medicaid patients" by 1,000 and multiply by your Medicaid patients of all ages.</p>
      <p>Code, method and sources: <a href="https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/09-health-center-coverage-loss-stress-test">analysis/09-health-center-coverage-loss-stress-test</a>. Every number on this page comes from <code>output/numbers.json</code> or the other files in <code>output/</code>, through <code>web_data.py</code>.</p>
    </div>

  </details>
</section>
