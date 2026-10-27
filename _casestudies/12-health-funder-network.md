---
title: Who funds organizations like yours?
subtitle: >-
  Foundations and charities that fund free clinics, health centers and community
  health nonprofits
description: >-
  A ranked list of the foundations and charities that fund organizations like
  yours in your state, from IRS Form 990 grant records for tax years 2022 to
  2025. Public data only.
layout: example
modal-id: 12
date: 2026-10-26T00:00:00.000Z
thumbnail: health-funder-thumbnail.webp
kind: example
persona: >-
  For development staff at free clinics, health centers and community health
  nonprofits
need: >-
  Which foundations and charities already fund organizations like mine in my
  state, who funds us now, and which funders of my peers should I approach next?
question: "Which funders give to organizations like yours, and are not yet giving to you?"
hero_note: "An example on public IRS filings, not client work. No personal information."
brief: >-
  Foundations and charities list their grants on their Form 990. We matched the
  recipients to registered nonprofits and labeled each organization's kind and
  each grant's purpose with a local language model run offline. Every model step
  was checked against a blind reference sample. The tool ranks funders by how
  many organizations like yours they gave to near you and in your state.
stats:
  - value: 16,061
    label: funders gave to organizations like yours
    note: Observed. Tax years 2022 to 2025
    kind: observed
  - value: 65%
    label: of those funders gave to only one
    note: Observed
    kind: observed
  - value: 37%
    label: of organizations that gained a funder had one in our top 10
    note: Backtest on 2023 and 2024. 95% interval 35% to 39%
    kind: estimate
sections:
  - id: tool
    label: Your funders
  - id: findings
    label: Findings
  - id: checks
    label: Checks
  - id: limits
    label: Limits
  - id: methods
    label: Method
downloads:
  - title: Funder table
    file: /downloads/12-health-funder-network-funder-table.csv
    type: CSV
    size: 2.4 MB
    description: >-
      Every funder with a grant to an organization like yours, with its type,
      channel and counts.
  - title: Grant table
    file: /downloads/12-health-funder-network-grant-table.csv
    type: CSV
    size: 7.7 MB
    description: "Every grant, with year, amount, purpose text and our label for its kind."
  - title: Organization table
    file: /downloads/12-health-funder-network-organization-table.csv
    type: CSV
    size: 1.7 MB
    description: "The organizations like yours, with our label for each one's kind."
  - title: Reference labels
    file: /downloads/12-health-funder-network-reference-labels.csv
    type: CSV
    size: 477 KB
    description: "The blind reference sample for each step, next to the pipeline's answer."
  - title: Codebook
    file: /downloads/12-health-funder-network-codebook.csv
    type: CSV
    size: 4 KB
    description: What each column means and its source.
cta:
  heading: Want this list checked against who funds you?
  text: >-
    Tell us your state and your current funders. We will answer your questions
    about the list and how it was made.
  button: Ask about your organization
data: /assets/examples/12/data.json
extra_css:
  - /assets/examples/12/page.css
extra_scripts:
  - /assets/examples/12/page.js
---

[code]: https://github.com/primordial-analytics/primordial-analytics.github.io/tree/master/analysis/12-health-funder-network

<section class="ex-section" id="tool">
<div class="ex-prose ex-toolhead" markdown="1">

## Find your funders

</div>

<div class="ex-wide ex-panel">
<div class="ex-tool ex-tool--split p12-tool">

<div class="ex-tool__controls">
<div id="pick-state"></div>
<div id="pick-org"></div>

<details class="ex-notes p12-more" id="p12-more" open>
<summary>Who counts and which funders</summary>
<div class="p12-more__body">
<fieldset class="ex-field p12-who">
<legend class="ex-label">Organizations like yours</legend>
<label class="ex-check"><input type="checkbox" name="kind" value="free_clinic" checked><span>Free clinics</span><span class="ex-check__n" id="n-free_clinic"></span></label>
<label class="ex-check"><input type="checkbox" name="kind" value="health_center" checked><span>Health centers</span><span class="ex-check__n" id="n-health_center"></span></label>
<label class="ex-check"><input type="checkbox" name="kind" value="care_provider" checked><span>Other care nonprofits</span><span class="ex-check__n" id="n-care_provider"></span></label>
</fieldset>

<fieldset class="ex-field p12-who">
<legend class="ex-label">Funders</legend>
<label class="ex-check"><input type="checkbox" id="f-daf"><span>Include donor-advised funds and matching-gift programs</span><span class="ex-check__n" id="n-daf"></span></label>
<label class="ex-check"><input type="checkbox" id="f-pre"><span>Hide funders that fund only preselected organizations</span><span class="ex-check__n" id="n-pre"></span></label>
</fieldset>
</div>
</details>

<p class="ex-hint" id="state-hint" hidden></p>
<p class="ex-actions"><button class="ex-link" type="button" id="reset">Reset</button></p>
</div>

<div class="ex-tool__out">
<div class="ex-results" id="results" aria-live="polite">
<div class="ex-result ex-result--lead">
<span class="ex-result__label" id="r1-label">Funders of organizations like yours</span>
<span class="ex-result__value" id="r1">--</span>
<span class="ex-result__range" id="r1-range"></span>
</div>
<div class="ex-result">
<span class="ex-result__label" id="r2-label">Organizations like yours counted</span>
<span class="ex-result__value" id="r2">--</span>
<span class="ex-result__range" id="r2-range"></span>
</div>
<div class="ex-result" id="r3-box" hidden>
<span class="ex-result__label" id="r3-label">Your current funders</span>
<span class="ex-result__value" id="r3">--</span>
<span class="ex-result__range" id="r3-range"></span>
</div>
</div>

<p class="ex-hint" id="msg" role="status" hidden></p>

<figure class="ex-figure p12-net" id="fig-net" aria-labelledby="t-net" hidden>
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-net">Funders and the organizations like yours they fund</h3>
<p class="ex-hint" id="net-hint"></p>
</div>
<ul class="ex-legend" id="key-state" aria-label="Key">
<li><span class="p12-key p12-key--sugg" aria-hidden="true"></span>A funder, numbered as in the list; larger means more organizations like yours</li>
<li><span class="p12-key p12-key--peer" aria-hidden="true"></span>An organization like yours</li>
</ul>
<ul class="ex-legend" id="key-ego" aria-label="Key" hidden>
<li><span class="p12-key p12-key--org" aria-hidden="true"></span>Your organization</li>
<li><span class="p12-key p12-key--funder" aria-hidden="true"></span>A current funder</li>
<li><span class="p12-key p12-key--peer" aria-hidden="true"></span>A peer that shares a funder with you</li>
<li><span class="p12-key p12-key--sugg" aria-hidden="true"></span>A suggested funder, numbered as in the list</li>
</ul>
<div class="ex-chart p12-netchart" id="chart-net"></div>
<p class="ex-actions"><button class="ex-link" type="button" id="net-all" hidden>Show the whole state</button></p>
<details class="ex-notes">
<summary>Text version<span class="ex-vh"> of the figure</span></summary>
<div id="net-text" class="p12-nettext"></div>
<p class="ex-source">Source: IRS Form 990 Schedule I and Form 990-PF grant lists, tax years 2022 to 2025; Primordial Analytics matching and labels.</p>
</details>
</figure>

<figure class="ex-figure p12-net p12-flowfig" id="fig-flow" aria-labelledby="t-flow" hidden>
<div class="ex-figure__head">
<p class="p12-trail" id="flow-trail"></p>
<h3 class="ex-figure__title" id="t-flow">Follow the money</h3>
<p class="ex-hint" id="flow-sum"></p>
</div>
<ul class="ex-legend" aria-label="Key">
<li><span class="p12-key p12-key--org" aria-hidden="true"></span>The funder you are following</li>
<li><span class="p12-key p12-key--funder" aria-hidden="true"></span>A funder you can follow next</li>
<li><span class="p12-key p12-key--other" aria-hidden="true"></span>Another grantmaker</li>
<li><span class="p12-key p12-key--peer" aria-hidden="true"></span>An organization like yours</li>
<li><span class="p12-key p12-key--rel" aria-hidden="true"></span>Between related organizations</li>
<li><span class="p12-key p12-key--back" aria-hidden="true"></span>Money also goes the other way</li>
</ul>
<div class="ex-chart p12-flowchart" id="chart-flow"></div>
<p class="ex-note">Line width is dollars, 2022 to 2025. A path shows where money could have gone, not that the same dollars moved: a grantmaker pools what it receives. Only the largest flows are drawn: 8 sources, 3 sources of each, 8 funders it gives to, 12 organizations it funds and 4 for each of those funders. Point at a circle to light every path through it.</p>
<p class="ex-actions"><button class="ex-link" type="button" id="flow-close">Back to the network</button></p>
<details class="ex-notes">
<summary>Text version<span class="ex-vh"> of the money trace</span></summary>
<div id="flow-text" class="p12-nettext"></div>
<p class="ex-source">Source: IRS Form 990 Schedule I, Schedule R and Form 990-PF grant lists, tax years 2022 to 2025; Primordial Analytics matching.</p>
</details>
</figure>

<div class="p12-ranked">
<h3 class="ex-tool__title" id="t-rank">Funders of organizations like yours</h3>
<p class="ex-hint" id="rank-hint"></p>
<div class="p12-list" id="rank-list"></div>
<p class="ex-actions"><button class="ex-link" type="button" id="more" hidden>Show more</button></p>
<details class="ex-notes p12-cols-help">
<summary>What the columns mean</summary>
<p><strong>Organizations funded here:</strong> organizations like yours in this state that the funder gave to, 2022 to 2025. <strong>Median grant:</strong> the funder's median grant to organizations like yours, in all states. <strong>Latest year:</strong> the latest tax year with such a grant. <strong>For general support:</strong> the share of its grants with a stated purpose that we labeled general support. <strong>Grantees new to it:</strong> of the organizations it funded in 2023 and 2024, the share it had not funded in the three years before. A dash means too few grants to say.</p>
</details>
</div>

<div class="p12-current" id="current" hidden>
<h3 class="ex-tool__title" id="t-current">Your current funders</h3>
<p class="ex-hint" id="conc-line"></p>
<div id="table-current"></div>
</div>

</div>

</div>
</div>
</section>

<section class="ex-section" id="findings">
<div class="ex-prose" markdown="1">

## <span data-n="numbers.findings.funders_one_peer_pct" data-f="pct0n">65</span>% of funders give to only one organization like yours

Half of the dollars come from <span data-n="numbers.findings.top_funders_half_dollars" data-f="int">31</span> funders.
{: .ex-lede}

</div>

<figure class="ex-wide ex-figure ex-figure--notes" id="fig-degree" aria-labelledby="t-degree">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-degree">How many organizations like yours each funder gave to</h3>
</div>
<div class="ex-chart" id="chart-degree"></div>
<div class="ex-sidenotes">
<p class="ex-note"><strong>The other side.</strong> <span data-n="numbers.findings.peers_one_funder_pct" data-f="pct0n">23</span>% of the organizations that have a funder have only one.</p>
</div>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the funders chart</span></summary>
<p>Funders with at least one grant to an organization like yours in tax years 2022 to 2025, across all states. Grants between related organizations are left out.</p>
<p class="ex-source">Source: IRS Form 990 Schedule I and Form 990-PF grant lists; Primordial Analytics matching and labels.</p>
<div id="table-degree"></div>
</details>
</figure>

<div class="ex-wide ex-cols p12-cols">
<figure class="ex-figure" id="fig-type" aria-labelledby="t-type">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-type">Dollars by kind of funder</h3>
</div>
<div class="ex-chart" id="chart-type"></div>
<p class="ex-note">Grants between related organizations, <span data-n="numbers.findings.related_dollars_pct" data-f="pct0n">35</span>% of the dollars, are left out.</p>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the funder kinds chart</span></summary>
<p>Grant dollars to organizations like yours, tax years 2022 to 2025. A hospital or health system is flagged on its return; a private foundation files Form 990-PF.</p>
<div id="table-type"></div>
</details>
</figure>

<figure class="ex-figure" id="fig-pre" aria-labelledby="t-pre">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-pre">Private foundations that fund only preselected organizations</h3>
</div>
<div class="ex-chart" id="chart-pre"></div>
<p class="ex-note">The form has a box for foundations that do not take unsolicited requests. We show it as a badge in the list.</p>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the preselected chart</span></summary>
<p>Share of the private foundations in the funder table that ticked the box on their latest Form 990-PF.</p>
<div id="table-pre"></div>
</details>
</figure>

<figure class="ex-figure" id="fig-kinds" aria-labelledby="t-kinds">
<div class="ex-figure__head">
<h3 class="ex-figure__title" id="t-kinds">What the grants are for</h3>
</div>
<div class="ex-chart" id="chart-kinds"></div>
<p class="ex-note" id="kinds-note">48% of grants are labeled general support. Corrected for the label errors found in the check, the share is 49% (45% to 53%).</p>
<details class="ex-notes">
<summary>Source and data<span class="ex-vh"> for the grant purposes chart</span></summary>
<p>Share of grants by purpose, as labeled by the model from the purpose text on the form. Blank or unclear purposes are their own bar. The checks below say how often the label was right.</p>
<div id="table-kinds"></div>
</details>
</figure>
</div>
</section>

<section class="ex-section" id="checks">
<div class="ex-prose" markdown="1">

## Each model step was checked against labels written blind

The reference labels were written by Claude (Anthropic), a larger model than the one in the pipeline, labeling blind: it saw the record but not the pipeline's answer.
{: .ex-lede}

</div>

<div class="ex-wide">
<div class="ex-table-wrap is-short" role="region" tabindex="0" aria-label="Scrollable table of the accuracy of each model step">
<table class="ex-table p12-checks">
<caption>Accuracy of each model step against the blind reference sample, with 95% intervals</caption>
<thead><tr><th scope="col">Step</th><th scope="col">Records labeled</th><th scope="col">Accuracy</th><th scope="col">Precision</th><th scope="col">Recall</th></tr></thead>
<tbody>
<tr><th scope="row">Matching a recipient to a registered nonprofit</th><td data-n="numbers.checks.match.n" data-f="int">300</td><td data-n="numbers.checks.match" data-f="acc">89% (85% to 92%)</td><td data-n="numbers.checks.match" data-f="prec">82% (75% to 87%)</td><td data-n="numbers.checks.match" data-f="rec">94% (88% to 97%)</td></tr>
<tr><th scope="row">Kind of organization</th><td data-n="numbers.checks.org.n" data-f="int">300</td><td data-n="numbers.checks.org" data-f="acc">87% (83% to 91%)</td><td>&mdash;</td><td>&mdash;</td></tr>
<tr><th scope="row">Kind of grant</th><td data-n="numbers.checks.grant.n" data-f="int">300</td><td data-n="numbers.checks.grant" data-f="acc">78% (73% to 83%)</td><td>&mdash;</td><td>&mdash;</td></tr>
</tbody>
</table>
</div>
<p class="ex-note p12-after">Precision is the share of matches that were right; recall is the share of true matches we found. Where the reference allowed more than one answer, any of them counts as right.</p>
<p class="ex-note p12-after"><strong>Recipients the screen missed.</strong> Before the model sees them, a screen drops recipients that do not look like health care. Of <span data-n="numbers.checks.missed.missed_care.n" data-f="int">200</span> dropped recipients whose names suggest care, <span data-n="numbers.checks.missed.missed_care.peers" data-f="int">12</span> were organizations like yours, so some peers and their grants are missing. Of <span data-n="numbers.checks.missed.missed_other.n" data-f="int">300</span> other dropped recipients, none were.</p>
</div>

<div class="ex-prose" markdown="1">

### Would the ranking have found the funders that came next?

We hid the last two years of grants, ranked funders from the earlier years, and checked whether the funders each organization gained appeared in its top 10.
{: .ex-lede}

</div>

<div class="ex-wide">
<div class="ex-table-wrap is-short" role="region" tabindex="0" aria-label="Scrollable table of the backtest results">
<table class="ex-table p12-checks" id="table-backtest">
<caption>Backtest of six ways to rank funders, trained on tax years 2020 to 2022 and tested on 2023 and 2024. The tool ranks by the bold row.</caption>
<thead><tr><th scope="col">Method</th><th scope="col">Hit rate (95% interval)</th><th scope="col">Share of new funders found</th></tr></thead>
<tbody>
<tr class="is-sel"><th scope="row">Most peers funded nearby</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular_near" data-f="hit">37% (35% to 39%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular_near.recall" data-f="pct0frac">18%</td></tr>
<tr><th scope="row">PageRank</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.pagerank" data-f="hit">36% (35% to 38%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.pagerank.recall" data-f="pct0frac">17%</td></tr>
<tr><th scope="row">Shared funders</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.shared" data-f="hit">33% (31% to 34%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.shared.recall" data-f="pct0frac">14%</td></tr>
<tr><th scope="row">Most peers funded in your state</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular_state" data-f="hit">31% (29% to 32%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular_state.recall" data-f="pct0frac">14%</td></tr>
<tr><th scope="row">Funders adding grantees in your state</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.adding_state" data-f="hit">27% (25% to 29%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.adding_state.recall" data-f="pct0frac">11%</td></tr>
<tr><th scope="row">Most peers funded nationally</th><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular" data-f="hit">15% (13% to 16%)</td><td data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular.recall" data-f="pct0frac">6%</td></tr>
</tbody>
</table>
</div>
<p class="ex-note p12-after"><strong>Hit rate</strong> is the share of the <span data-n="numbers.backtest.2020-2022 to 2023-2024.methods.popular_near.peers" data-f="int">2,806</span> organizations that gained a funder whose top 10 held at least one of the new funders. Training on 2020 and 2021 and testing on 2022 and 2023 put the methods in the same order.</p>
<p class="ex-note p12-after">About <span data-n="numbers.backtest.2020-2022 to 2023-2024.unreachable_pct" data-f="pct0n">43</span>% of new funders had given to no organization like yours before, so no method could have found them.</p>
</div>
</section>

<section class="ex-section" id="limits">
<div class="ex-prose" markdown="1">

## Six limits on these numbers

<ul class="ex-limits">
<li>A funder that gave to your peers may not take your request. Only a ticked box on the form tells us it does not.</li>
<li>The grants are from tax years 2022 to 2025, and some 2025 returns are still arriving.</li>
<li>A public charity lists only grants above $5,000 to one recipient, so its smaller grants are missing.</li>
<li>Matching and labels are a model's work. They are right most of the time, not always.</li>
<li>Donor-advised funds and matching gifts follow a donor's choice, so they are hidden unless you ask.</li>
<li>Grants between related organizations are left out, which removes most of a hospital's giving.</li>
</ul>

</div>

<details class="ex-notes p12-detail">
<summary>Detail on each limit</summary>
<div class="ex-prose" markdown="1">

- **Past grants, not open calls.** The list ranks by overlap with organizations like yours. It does not know a funder's mission, its size limits or its calendar. Read its guidelines before you write. The backtest asks whether a funder later gave to a peer, not whether it would have funded you.
- **Years.** A return for tax year 2025 arrives late, so recent giving is undercounted. The share of grantees new to a funder uses only 2023 and 2024.
- **Smaller grants.** Form 990-PF lists every grant a private foundation makes. Schedule I, used by public charities, lists recipients that received more than $5,000. A community foundation's small grants to you may not show.
- **Model labels.** Accuracy for each step is in the checks above. A recipient matched to the wrong nonprofit puts a grant under the wrong organization, and a peer labeled as another kind drops out of the list. The reference labels were written by a model, not a person.
- **Donor-advised funds and matching gifts.** Fidelity Charitable and similar sponsors pay out what donors recommend. A funder that gives in 10 or more states, either as a donor-advised fund or with a median grant under $1,000, is treated this way. The test is a rule, not a fact about each funder.
- **Related organizations.** Schedule R lists organizations a filer controls or is controlled by. Grants between them are left out of every count: they are <span data-n="numbers.findings.related_dollars_pct" data-f="pct0n">35</span>% of the dollars.

</div>
</details>
</section>

<section class="ex-section" id="methods">
<div class="ex-prose">
<h2>Method and downloads</h2>
<p>We read the grant lists on IRS Form 990 filings, matched recipients to registered nonprofits and ranked funders by how many organizations like yours they fund. Sources and checks are in the notes below.</p>
</div>
<details class="ex-methods ex-wide">
<summary><span>Methods, sources and checks</span></summary>
<div class="ex-methods__body">

<div class="ex-prose" markdown="1">

Everything on this page comes from `analysis/12-health-funder-network` in the [site repository][code], and every number is in its `numbers.json`. The tool ranks in your browser from the grant rows for your state; nothing is sent anywhere. The model is gpt-oss:20b, an open-weight model, run with Ollama on a laptop's built-in graphics chip: 27,256 prompts and no paid service. Reruns replay every model answer from a saved cache, so they give the same result.

</div>

<ol class="ex-steps">
<li><strong>Returns.</strong> IRS Form 990, 990-EZ and 990-PF e-file records, processing years 2021 to 2026, 3,596,451 returns. We keep the latest return for each organization and period, and drop the grants of a return whose listed grants are over ten times the grants it reports paid.</li>
<li><strong>Grants.</strong> Schedule I (recipient name, address and, for most rows, EIN) from 990 filers, and the grants list of Form 990-PF, which never carries an EIN. Tax years 2022 to 2025 are shown.</li>
<li><strong>Registered nonprofits.</strong> The IRS Business Master File of tax-exempt organizations, downloaded October 25, 2026, for EIN, name, address and NTEE code.</li>
<li><strong>Matching.</strong> A recipient is matched by EIN, then by exact normalized name and ZIP code. For the rest, candidates in the same state are narrowed by rule and a local model (gpt-oss:20b, run offline) picks one or none. A screen keeps only recipients whose names or NTEE codes suggest health care.</li>
<li><strong>Kind of organization.</strong> For each matched recipient the model reads its name, place, NTEE code, revenue and the mission on its latest Form 990 and returns one of: free clinic, other nonprofit that gives care itself, or not a peer. Health centers come from the HRSA list instead. All but the last are peers.</li>
<li><strong>Kind of grant.</strong> For each distinct purpose text the model returns general support, program, capital, donated goods, event or sponsorship, or unclear.</li>
<li><strong>Funders.</strong> A funder is a private foundation if it files Form 990-PF, a hospital or health system if its return says so, a charity that holds donor-advised funds if its return says so, and otherwise a community foundation or charity. A charity that holds donor-advised funds and gives in 10 or more states is listed as a donor-advised fund; a funder in 10 or more states with a median grant under $1,000 is a matching program. Both are hidden unless you ask.</li>
<li><strong>Ranking.</strong> A funder's score is the number of distinct peers of the kinds you tick in your state that it gave to in 2022 to 2025. If you choose an organization, peers in its 3-digit ZIP area count first and its current funders are left out. Ties are broken by the peers it gave to anywhere. With all states chosen, the list holds the 100 funders that gave to the most organizations like yours anywhere, more when there are ties.</li>
<li><strong>Following the money.</strong> Grants from one grantmaker to another (a recipient that files its own grant list) are summed by pair for 2022 to 2025. A funder's trace shows its 8 largest sources, the 3 largest sources of each, the 8 largest funders it gives to and the organizations like yours at the end. Flows between organizations that list each other on Schedule R are marked as related; money that goes both ways between two grantmakers is marked too.</li>
<li><strong>Checks.</strong> For each step, a random sample was labeled by Claude (Anthropic) reading the full record without the pipeline's answer. Intervals are 95%. Shares of grant purposes are corrected for the errors the sample found (prediction-powered inference).</li>
<li><strong>Backtest.</strong> We ranked funders from the grants of earlier years and checked them against later ones: 2020 to 2022 against 2023 and 2024, and 2020 and 2021 against 2022 and 2023. An organization is scored if it had a funder before and gained one after; only direct funders count. The rule, set before the final data, was to rank by state unless another method beat it on both splits. Ranking by nearby peers did.</li>
</ol>

<h3 class="ex-h3" style="margin:2rem 0 1rem">Sources</h3>
<dl class="ex-sources">
<dt>IRS Form 990 series electronic filings</dt>
<dd><a href="https://www.irs.gov/charities-non-profits/form-990-series-downloads">IRS download page</a>. Schedule I, Schedule R and Form 990-PF as XML. Downloaded October 25, 2026.</dd>
<dt>IRS Exempt Organizations Business Master File</dt>
<dd><a href="https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf">IRS extract</a>. EIN, name, address and NTEE code for registered nonprofits. Downloaded October 25, 2026.</dd>
<dt>ProPublica Nonprofit Explorer</dt>
<dd><a href="https://projects.propublica.org/nonprofits/">Nonprofit Explorer</a>. Linked from each funder in the list for its filings. We do not use its data.</dd>
<dt>File hashes and checks</dt>
<dd>File sizes and hashes are in <code>numbers.json</code>.</dd>
</dl>

</div>
</details>
</section>
