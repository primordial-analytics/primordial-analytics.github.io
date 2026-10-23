"""Run the whole analysis: python run.py [step ...]

Steps, in order: fetch, pums, uds, unwinding, model, report.
With no arguments every step runs. Raw downloads go to data/raw/ (gitignored)
and everything else to output/.
"""
import importlib, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

STEPS = ["fetch", "pums", "uds", "unwinding", "model", "report"]

if __name__ == "__main__":
    for step in sys.argv[1:] or STEPS:
        print(f"== {step}", flush=True)
        importlib.import_module(step).main()
