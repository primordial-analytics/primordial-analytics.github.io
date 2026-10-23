# Overdose rates where counts are hidden (case study 10)

County overdose death rates with 90% intervals for the counties where the CDC/NCHS provisional file hides the count (1 to 9 deaths). Public aggregate data only; no patient-level data.

**Run it.** `pip install -r requirements.txt`, then `python run.py` (about 25 minutes on 4 cores; `--quick` is a 5-minute smoke test). `python run.py --states WA OR` also writes a county table for just those states; the model still fits all counties because neighbors carry information. `python run.py --refresh` re-downloads the NCHS files and refits (the window defaults to `--end 2026-03`; Census population vintages end at July 2024).

**Outputs** (in `output/`): `county_rates.csv` (one row per county: published count, hard 1-to-9 bounds, posterior median and 90% interval per 100,000, probability above the state rate, probability of being in the top decile, rank interval, run date), `model_results.json` (diagnostics, sensitivity, validation), `numbers.json` (every figure quoted on the page). Raw downloads go to `data/raw/` (gitignored) with URLs and download dates in `data/raw/SOURCES.json`.

**Sources.** NCHS VSRR provisional county overdose counts (data.cdc.gov `gb4e-yj24`) and state counts (`xkb8-kh2a`); Census county population estimates (2024 vintage; 2020 vintage for Connecticut's old counties); Census SAHIE 2024 (uninsured, low-income share); Census 2020 cartographic boundaries (adjacency, land area).

**Method.**

1. Likelihood: published counts are Poisson (zeros are exact); a suppressed cell contributes P(1 <= Y <= 9); the 2 data-quality cells carry no information.
2. Rate model: log rate = intercept + covariates (density, uninsured, low-income, NCHS urban-rural class) + state effect + Leroux CAR spatial effect on the county adjacency graph. NUTS in NumPyro, 4 chains. BYM2 was tried first and did not converge on 3,100 counties.
3. State constraint: state total minus published county counts as a soft constraint on the suppressed total, only where it falls inside the logical 1-to-9 bounds and the state has no data-quality county. The cause of the mismatches (residence versus occurrence, timing, other) is not confirmed.
4. Validation (`validate.py`, each check seeded separately): hide all counts under 20 and under 30 and score the counties with known counts of 10 to T-1 (the upper part of the range only); compare with a covariates-only variant (the like-for-like test of the spatial term) and a Poisson-gamma model with no covariates and no constraint; fit March 2025 and predict March 2026; compare the modelled suppressed total with each state residual (model fit without it).

**Limits.** The total for hidden counties is model-conditional: the page widens its interval because only 22 of 37 states fell inside their own 90% interval. Provisional, incomplete counts; crude (not age-adjusted) rates; Connecticut and Kalawao covariates imputed; no prior-sensitivity analysis; minimum effective sample size for the hyperparameters is 259; suppressed-county estimates rest on covariates, neighbors and state totals, not on their own data; pseudo-suppressed counties are larger than truly suppressed ones. Do not rank counties or infer individual risk.
