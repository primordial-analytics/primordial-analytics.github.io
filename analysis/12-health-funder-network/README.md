# Who Funds Organizations Like Yours

An example on public data for a free clinic, health center or other community care nonprofit: every foundation, charity and hospital that made a grant to an organization like it in tax years 2022--2025, from the grant lists in IRS Form 990 e-files, with how open each funder is to new grantees. A local open-weight model (no paid API, nothing leaves the machine) links grant recipients to registered nonprofits and labels organizations and grants; every model step is checked against a blind reference sample.

Run: `pip install -r requirements.txt && python run.py`. The first run downloads about 23 GB of IRS e-file batches and parses them (a few hours). Every model answer is in `llm_cache/`, so a rerun on the same data needs no model and takes minutes.

- `fetch.py` downloads raw files to `data/raw/` (gitignored) and keeps `data/raw/SOURCES.txt` (URL, bytes, sha256, download date).
- `parse.py` reads each return's header, Schedule I, Schedule R and Form 990-PF grant lines into parquet files.
- `prepare.py` keeps the latest return per filer and period and drops returns whose listed grants exceed ten times their reported grants paid.
- `match.py` links recipients to the IRS Business Master File: EIN, then name with ZIP, city or state, then the model choosing among five candidates (or none) for recipients that look like care providers.
- `classify.py` labels each organization (free clinic, other care provider, not a peer) and each grant purpose (general, program, capital, in-kind, event, unclear). `health_centers.py` marks health centers from HRSA's list instead.
- `check.py` draws the reference samples (fixed seeds) and computes accuracy with Wilson intervals and corrected shares (prediction-powered inference). Labels are in `check/`.
- `graph.py` backtests ways to rank likely funders on earlier years; `results.py` builds the funder and organization tables and the findings.
- `web_data.py` writes `assets/examples/12/` and `thumbnail.py` the card image; `run.py` also copies the tables and `codebook.csv` to `downloads/`. Every number on the page is in `output/numbers.json`.

The model: `gpt-oss:20b` in Ollama 0.40.2, temperature 0, fixed seed. On an AMD laptop chip the integrated GPU runs it through Vulkan:

```bash
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_IGPU_ENABLE=1 OLLAMA_NUM_PARALLEL=4 OLLAMA_FLASH_ATTENTION=1 ollama serve
ollama pull gpt-oss:20b   # with OLLAMA_HOST set the same way
```

`llm.py` talks to `http://127.0.0.1:11435` (set `OLLAMA_URL` to change it). Answers are cached by a hash of the exact prompt, so the cache, not the model, is the record: the model is not bit-for-bit repeatable when requests run in parallel.

Sources: IRS Form 990 series e-file XML, processing years 2021--2026; IRS Exempt Organizations Business Master File; HRSA health center and look-alike sites.

Limits: only e-filed returns that list grants; Form 990-PF grant lines carry no recipient EIN, so those matches rest on names; 2025 returns are still arriving; a grant is a past decision, not an open call.
