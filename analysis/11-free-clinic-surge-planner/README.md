# Free Clinic Demand Planner

An example on public data for a volunteer-run free or charitable clinic: a planning range for how many more low-income uninsured adults a county may have in 2027, turned into sessions, volunteers and medication dollars at a stated probability. No patient data; the clinic in the figures is hypothetical.

Run: `pip install -r requirements.txt && python run.py` (about 25 seconds after the first download).
- `fetch.py` downloads raw files to `data/raw/` (gitignored) and keeps `data/raw/SOURCES.txt` (URL, bytes, sha256, first download date).
- `prepare.py` cleans them: '*' small cells, 'Total' rows, 5-digit FIPS matching, comma and dollar strings.
- `model.py` runs the stability-adjusted ranking, a cross-band backtest and a 10,000-draw scenario model.
- `results.py` builds the county table (with codebook), an example clinic and a tornado of assumptions.
- `figures.py` and `workbook.py` write `img/case_studies/free-clinic-*.webp` and `downloads/11-free-clinic-surge-planner-*` (the workbook gets cached results from a LibreOffice recalculation if `soffice` is installed).
- Every number on the case-study page is in `output/numbers.json`.

Sources (downloaded 2026-10-22): CMS 2025 and 2026 Open Enrollment county files; CMS monthly effectuated enrollment (dated snapshot, as of 2026-05-05); Census SAHIE 2024; Medicaid.gov performance indicators (June 2026).

Method: selections are exact counts, so county change is described, not modeled. Additional uninsured adults at or below 200% of poverty are marketplace losses, u x (net paid-coverage loss Feb 2025 to Feb 2026 + d x Feb 2026 paid), using the state paid share on county selections, plus a placeholder Medicaid work-requirement layer. Each parameter is a Beta prior, drawn against the SAHIE baseline and its margin of error. The county pool (`g_` columns) counts the whole marketplace loss. Only the clinic step removes 80% of the 2026 loss (`PHI` in `model.py`), because a clinic's trailing-year visits already hold it (`cg_` columns). Clinic visits scale with that growth through one rate the clinic overwrites with its own intake counts; sessions are the demand quantile over patients per session.

Limits: selections are not paid coverage; 30 HealthCare.gov states only; scenario inputs are assumptions; the 80% interval and session answers are conditional on one scenario and cannot be validated with these data. The Medicaid layer uses the loss shares in the site's Medicaid what-if post. KFF's expansion-adult share is 31% of Medicaid enrollment (June 2024); the model uses 30% of Medicaid plus CHIP.
