# Medicaid coverage loss and health center revenue (stress test)

Example project on public data: state-by-state ranges for the share of Medicaid expansion adults who could lose coverage
under the 2027 community engagement rule, split into non-compliance and administrative loss, plus the net revenue effect
for health centers and a ranking of the assumptions that matter. Page: `_casestudies/09-health-center-coverage-loss-stress-test.md`.

Run: `pip install -r requirements.txt`, then from this directory `python -I run.py` (about a minute after the downloads;
`python -I run.py model report` reruns single steps). Raw files go to `data/raw/` (gitignored, about 2 GB unzipped);
`output/sources.json` records every URL and download date.

Sources: CMS interim final rule 2026-11094 (Tables 37-41 read from the PDF, constants in `common.py`); ACS 2024 PUMS for the
40 expansion states and DC; CMS Updated Renewal Outcomes (Oct 2024 release); HRSA UDS 2025 awardee file (Tables 4, 9D, 9E)
and HRSA's national Table 9D page for validation.

Method: reproduce CMS's arithmetic (15.3%, 2.29M in FY2027); scale CMS's exclusion and non-compliance levels by each state's
PUMS ratio to the pooled states (empirical-Bayes shrinkage, replicate-weight errors); take state positions on data matching
and paperwork loss from the unwinding (two-level logit model, split-half persistence; state-months with under 1,000 people in
the denominator or a zero count among more are dropped), applied around CMS's net rate; 20,000
Monte Carlo draws per state over CMS's four scenarios and uncertain inputs; revenue from UDS Medicaid adults, Medicaid payments
per patient and sliding-fee recapture; Sobol indices (SALib) and one-at-a-time swings. Administrative vs non-compliance is a
model construct. PUMS and the unwinding supply spread only, not levels. Seeds are fixed, so reruns match.
Outputs: `output/numbers.json` (every number in the page prose), `state_ranges.csv`, `state_inputs_for_whatif_workbook.csv`
(copied to `downloads/`), `peer_benchmark.csv` (aggregated bands, no named centers), Sobol and tornado tables, `model_summary.json`.
Limits: scenarios, not forecasts; center totals treat states' scenarios and paperwork shocks as independent; the unwinding covers
all Medicaid and CHIP enrollees; no patient-level or margin data; Table 9D is blank for about half of centers.
