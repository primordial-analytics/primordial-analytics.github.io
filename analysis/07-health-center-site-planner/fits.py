"""Model fits for every variant of the data (main, sensitivities, 2024), run in parallel worker processes.

A job is a dict: variant (name below), tag, optional w (weight of each center in the likelihood), pm (weight of each pair),
x0 (start values). Results are cached under data/raw/cache so a re-run of run.py does not refit.
"""
import multiprocessing as mp
import os
import pickle
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # worker processes import this module first

import numpy as np
import pandas as pd

import model
import prepare

CACHE = prepare.CACHE
MAXITER = 1500
BOOT_ITER = 2500
N_BOOT = 100
_V = {}


def variant(name):
    """(prepared tables, Data, jnp arrays) for a named variant of the inputs."""
    if name in _V:
        return _V[name]
    year = 2024 if name == "y2024" else 2025
    d = prepare.build(year)
    sites = d["sites"]
    radius = {"r40": 40.0, "r100": 100.0}.get(name, model.RADIUS)
    if name == "late":
        sites = pd.concat([sites, d["late_sites"]], ignore_index=True)
    zcta = d["zcta"]
    if name == "popbase":
        zcta = zcta.assign(low=zcta["pop"])
    data = model.Data(zcta, d["centers"], d["lookalikes"], sites, d["cells"], radius=radius)
    _V[name] = (d, data, model.arrays(data))
    return _V[name]


def _init(queue):
    os.sched_setaffinity(0, queue.get())


def _run(job):
    d, data, a = variant(job["variant"])
    w = job.get("w")
    if w is None:
        w = np.where(data.free > 0, 1.0, 0.0)
    a = dict(a)
    if job.get("pm") is not None:
        import jax.numpy as jnp
        a["pm"] = jnp.asarray(job["pm"])
    x, r = model.fit(data, a, w, x0=job.get("x0"), maxiter=job.get("maxiter", MAXITER), fixed=job.get("fixed"))
    return job["tag"], x, {"nit": int(r.nit), "fun": float(r.fun), "ok": bool(r.success), "message": str(r.message), "gmax": float(np.abs(r.jac).max())}


def run_jobs(jobs, workers=8, name=None):
    """Run jobs in worker processes, each pinned to its own cores; return {tag: (x, info)}. Cached under `name` when given."""
    path = CACHE / f"fits_{name}.pkl" if name else None
    if path is not None and path.exists():
        return pickle.loads(path.read_bytes())
    cpus = sorted(os.sched_getaffinity(0))
    workers = min(workers, len(jobs))
    per = max(1, len(cpus) // workers)
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    for i in range(workers):
        queue.put(set(cpus[i * per:(i + 1) * per]))
    out = {}
    with ctx.Pool(workers, initializer=_init, initargs=(queue,)) as pool:
        for tag, x, info in pool.imap_unordered(_run, jobs):
            out[tag] = (x, info)
    if path is not None:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(pickle.dumps(out))
    return out


def main_fit():
    """The fit every other number rests on."""
    res = run_jobs([{"variant": "main", "tag": "main"}], workers=1, name="main")
    return res["main"]


def bootstrap_jobs(variant_name, x_ref, n, seed):
    """Cluster bootstrap over centers, Bayesian form: each refit weights every center's rows by an independent Exponential(1) draw
    (mean 1). Unlike a with-replacement resample no center is dropped, so every competitor keeps an estimated attractiveness."""
    d, data, a = variant(variant_name)
    rng = np.random.default_rng(seed)
    free = data.free > 0
    jobs = []
    for b in range(n):
        w = np.where(free, rng.exponential(1.0, len(free)), 0.0)
        jobs.append({"variant": variant_name, "tag": b, "w": w, "x0": x_ref, "maxiter": BOOT_ITER})
    return jobs


def bootstrap(x_main, n=N_BOOT, seed=model.SEED, workers=8):
    """The main model's bootstrap. Returns an (n, n_params) array and the fit infos."""
    res = run_jobs(bootstrap_jobs("main", x_main, n, seed), workers=workers, name=f"boot{n}")
    return np.stack([res[b][0] for b in range(n)]), [res[b][1] for b in range(n)]
