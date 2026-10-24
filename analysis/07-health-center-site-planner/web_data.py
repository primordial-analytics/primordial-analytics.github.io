"""Fitted values for the page: assets/examples/07/data.json (small, readable) and zcta.bin.gz (columnar, quantised).

The browser never fits anything. It reads these arrays and applies the formula in project.py (also written out in README.md).
decode() reads the files back the way the page does, and check() compares the decoded formula with the unquantised one.
"""
import gzip
import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import numpy as np
import pandas as pd

import model
import project

N_SETS = 24
NBR = 6
S_SCALE, SB_SCALE, L_SCALE, LAM_SCALE = 5500.0, 400.0, 24.0, 200.0
S_FLOOR, L_FLOOR = 0.01, 10.0  # offsets in the log ratios: tiny S and tiny L do not change the answer, so their ratios need no precision
NA16 = 65535


def _i(a, dtype, scale=1.0):
    return np.round(np.asarray(a, dtype=np.float64) * scale).astype(dtype)


def encode(d, data, rt, table, zd, sets, nbr, S_main):
    """Return (manifest list, bytes) for the column file and the JSON-ready meta."""
    z = d["zcta"]
    nz = len(z)
    states = sorted(z.state.dropna().unique())
    counties = sorted((z.county.fillna("") + "|" + z.state.fillna("")).unique())
    col = {}
    col["lat"] = _i(z.lat, "<i4", 1e4)
    col["lon"] = _i(z.lon, "<i4", 1e4)
    col["dclass"] = z.dclass.to_numpy("<u1")
    col["state"] = pd.Categorical(z.state, categories=states).codes.astype("<u1")
    col["county"] = pd.Categorical(z.county.fillna("") + "|" + z.state.fillna(""), categories=counties).codes.astype("<u2")
    col["low"] = _i(z.low, "<u4")
    col["low_moe90"] = _i(np.minimum(z.low_se * 1.645, 65535), "<u2")
    col["pop"] = _i(z["pop"], "<u4")
    col["unins"] = _i(np.minimum(z.unins_adult_low, 65534), "<u2")
    for q in ("p10", "p50", "p90"):
        col[f"pen_{q}"] = _i(rt[f"pen_{q}"], "<u2", 1e4)
        col[f"notp_{q}"] = _i(rt[f"notpat_{q}"], "<u4")
    col["pat_total"] = _i(rt.patients_total, "<u4")
    col["pat_low"] = _i(rt.patients_low, "<u4")
    hr = table.hrsa_published_penetration.to_numpy(float)
    col["hrsa_pen"] = np.where(np.isnan(hr), NA16, np.round(np.nan_to_num(hr) * 1e4)).clip(0, 65534).astype("<u2")
    col["small"] = rt.small.to_numpy("<u1")
    col["campus"] = rt.campus.to_numpy("<u1")
    col["near_mi"] = _i(np.minimum(table.nearest_site_miles, 6000), "<u2", 10)
    for j, p in enumerate(project.PAYERS):
        col[f"obs_{p}"] = _i(zd.obs_mix[:, j], "<u2", 1e4)
        col[f"new_{p}"] = _i(zd.new_payer[:, j], "<u2", 1e4)
    S0q = np.round(np.log1p(S_main.astype(np.float64)) * S_SCALE).clip(0, 65535).astype("<u2")
    col["S0"] = S0q
    S0 = np.expm1(S0q / S_SCALE)
    for b in range(N_SETS):
        col[f"S_{b}"] = np.round(SB_SCALE * np.log((sets.S[b] + S_FLOOR) / (S0 + S_FLOOR))).clip(-32767, 32767).astype("<i2")
        col[f"L_{b}"] = np.round(L_SCALE * np.log((sets.L[b] + L_FLOOR) / (z.low.to_numpy(float) + L_FLOOR))).clip(-127, 127).astype("<i1")
    for j in range(NBR):
        col[f"nbr_c{j}"] = np.where(nbr["c"][:, j] >= 0, nbr["c"][:, j], NA16).astype("<u2")
        col[f"nbr_lam{j}"] = _i(np.minimum(np.sqrt(nbr["lam"][:, j]) * LAM_SCALE, 65535), "<u2")
    s = data.sites
    col_sites = {"site_lat": _i(s.lat, "<i4", 1e4), "site_lon": _i(s.lon, "<i4", 1e4), "site_center": data.eidx.reindex(s.grant).to_numpy().astype("<u2")}
    manifest, blob, off = [], [], 0
    for name, a in {**col, **col_sites}.items():
        b = a.tobytes()
        manifest.append({"name": name, "dtype": a.dtype.str, "offset": off, "length": int(a.size)})
        blob.append(b)
        off += len(b)
    return manifest, b"".join(blob), {"states": states, "counties": counties}


def write(out_dir, manifest, blob, lists, meta):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gz = gzip.compress(blob, 9, mtime=0)
    (out_dir / "zcta.bin.gz").write_bytes(gz)
    meta = {**meta, "columns": manifest, "bin_bytes": len(blob), "bin_gz_bytes": len(gz), **lists}
    (out_dir / "data.json").write_text(json.dumps(meta, separators=(",", ":")))
    return len(gz), (out_dir / "data.json").stat().st_size


def decode(out_dir):
    """Read the files as the page does. Returns (meta, dict of float64 arrays)."""
    out_dir = Path(out_dir)
    meta = json.loads((out_dir / "data.json").read_text())
    blob = gzip.decompress((out_dir / "zcta.bin.gz").read_bytes())
    cols = {c["name"]: np.frombuffer(blob, dtype=c["dtype"], count=c["length"], offset=c["offset"]) for c in meta["columns"]}
    return meta, cols


def decoded_sets(meta, cols):
    """Rebuild a project.Sets-like object and ZData from the decoded columns."""
    nz = len(cols["lat"])
    S0 = np.expm1(cols["S0"].astype(np.float64) / S_SCALE)
    L0 = cols["low"].astype(np.float64)
    s = object.__new__(project.Sets)
    s.B = len(meta["sets"])
    s.rho = np.array([m["rho"] for m in meta["sets"]])
    s.gamma = np.array([m["gamma"] for m in meta["sets"]])
    s.theta = np.array([m["theta"] for m in meta["sets"]])
    s.S = np.stack([(S0 + S_FLOOR) * np.exp(cols[f"S_{b}"] / SB_SCALE) - S_FLOOR for b in range(s.B)])
    s.L = np.stack([np.maximum((L0 + L_FLOOR) * np.exp(cols[f"L_{b}"] / L_SCALE) - L_FLOOR, 0.0) for b in range(s.B)])
    zd = object.__new__(project.ZData)
    zd.lat, zd.lon = cols["lat"] / 1e4, cols["lon"] / 1e4
    zd.k = cols["dclass"].astype(int)
    zd.obs_mix = np.stack([cols[f"obs_{p}"] / 1e4 for p in project.PAYERS], axis=1)
    zd.new_payer = np.stack([cols[f"new_{p}"] / 1e4 for p in project.PAYERS], axis=1)
    nbr = {"c": np.stack([np.where(cols[f"nbr_c{j}"] == NA16, -1, cols[f"nbr_c{j}"]) for j in range(NBR)], axis=1).astype(np.int32),
           "lam": np.stack([(cols[f"nbr_lam{j}"] / LAM_SCALE) ** 2 for j in range(NBR)], axis=1)}
    return s, zd, nbr


def summarize(z, d_, res, nbr, K):
    """Percentiles across parameter sets of what the page shows for one candidate."""
    D = np.array([r["D"] for r in res])
    N = np.array([r["new"] for r in res])
    share = np.where(D > 0, N / np.maximum(D, 1e-9), np.nan)
    return {"patients_p10_p50_p90": np.percentile(D, [10, 50, 90]), "share_new_p50": float(np.nanmedian(share))}


def check(out_dir, zd_ref, sets_ref, nbr_ref, n=200, seed=3):
    """Max differences between the formula on decoded (quantised) arrays and on the unquantised ones for random candidates."""
    meta, cols = decode(out_dir)
    s_dec, zd_dec, nbr_dec = decoded_sets(meta, cols)
    rng = np.random.default_rng(seed)
    nz = len(zd_ref.lat)
    s_ref = sets_ref.subset(len(meta["sets"]))
    worst = {"patients_rel": 0.0, "share_new_abs": 0.0, "payer_abs": 0.0, "patients_abs": 0.0, "neighbour_loss_rel": 0.0}
    for i in range(n):
        j = rng.integers(nz)
        lat = zd_ref.lat[j] + (rng.normal(0, 0.05) if i % 2 else 0.0)
        lon = zd_ref.lon[j] + (rng.normal(0, 0.05) if i % 2 else 0.0)
        K = float(rng.choice([500, 1500, 3000, 5000, 10000, 20000]))
        t = int(rng.integers(2))
        out = []
        for zd, sets, nbr in ((zd_ref, s_ref, nbr_ref), (zd_dec, s_dec, nbr_dec)):
            z, dd, res = project.candidate(lat, lon, zd, sets, t, K, nbr, None)
            D = np.array([r["D"] for r in res])
            N = np.array([r["new"] for r in res])
            pay = np.zeros((len(res), 4))
            for b, r in enumerate(res):
                nb_f = r["draw_z"] - r["new_z"]
                pay[b] = (r["new_z"][:, None] * zd.new_payer[z] + nb_f[:, None] * zd.obs_mix[z]).sum(axis=0)
            sh = pay / np.maximum(pay.sum(axis=1, keepdims=True), 1e-9)
            loss = project.neighbour_loss(z, res, nbr)
            top = sorted(((np.median(v), c) for c, v in loss.items()), reverse=True)[:1]
            out.append((np.percentile(D, [10, 50, 90]), np.median(N / np.maximum(D, 1e-9)), np.median(sh, axis=0), top[0][0] if top else 0.0))
        (p0, s0, m0, l0), (p1, s1, m1, l1) = out
        worst["patients_abs"] = max(worst["patients_abs"], float(np.abs(p0 - p1).max()))
        worst["patients_rel"] = max(worst["patients_rel"], float(np.abs(p0 - p1).max() / max(p0[1], 25)))
        worst["share_new_abs"] = max(worst["share_new_abs"], float(abs(s0 - s1)))
        worst["payer_abs"] = max(worst["payer_abs"], float(np.abs(m0 - m1).max()))
        worst["neighbour_loss_rel"] = max(worst["neighbour_loss_rel"], float(abs(l0 - l1) / max(l0, 25)))
    return {"candidates": n, **{k: round(v, 5) for k, v in worst.items()}}


def check_c_groups(out_dir):
    """Share of a held-out center's patients living in the 20 ZIPs each rule picked (check C), by group, weighted by patients and as a plain mean over centers."""
    c = pd.read_csv(Path(out_dir) / "check_c_leave_one_center_out.csv")
    groups = {"all": c, "urban": c[c.urban == "Urban"], "rural": c[c.urban == "Rural"], "single_site": c[c.sites_bin.astype(str) == "1"]}
    out = {}
    for name, g in groups.items():
        w = g.patients / g.patients.sum()
        out[name] = {"centers": int(len(g)),
                     **{f"{k}_weighted": float((g[f"top20_{k}"] * w).sum()) for k in ("model", "nearest", "population")},
                     **{f"{k}_mean": float(g[f"top20_{k}"].mean()) for k in ("model", "nearest", "population")}}
    return out


def finish(site_dir, out_dir):
    """What the page needs beyond the fitted arrays, added to data.json and zcta.bin.gz. Run at the end of run.py, or alone (it only reads output/):
    ZIP codes as a column (the arrays are in the order of output/zip_table.csv, checked here), output/numbers.json as `numbers`
    (every number in the page's text and charts), and check C by group as `check_c_groups`. Running it again changes nothing."""
    site_dir, out_dir = Path(site_dir), Path(out_dir)
    meta = json.loads((site_dir / "data.json").read_text())
    if "zip" not in {c["name"] for c in meta["columns"]}:
        blob = gzip.decompress((site_dir / "zcta.bin.gz").read_bytes())
        cols = {c["name"]: np.frombuffer(blob, dtype=c["dtype"], count=c["length"], offset=c["offset"]) for c in meta["columns"]}
        zt = pd.read_csv(out_dir / "zip_table.csv", dtype={"zcta": str})
        assert len(zt) == len(cols["low"]) and (cols["low"] == zt.low_income_residents.to_numpy()).all()
        assert (np.array(meta["states"])[cols["state"]] == zt.state.to_numpy()).all()
        blob += b"\0" * (-len(blob) % 4)
        zips = zt.zcta.astype(int).to_numpy("<u4")
        meta["columns"].append({"name": "zip", "dtype": "<u4", "offset": len(blob), "length": int(zips.size)})
        blob += zips.tobytes()
        gz = gzip.compress(blob, 9, mtime=0)
        (site_dir / "zcta.bin.gz").write_bytes(gz)
        meta["bin_bytes"], meta["bin_gz_bytes"] = len(blob), len(gz)
    import reach  # the constants the page text quotes, read from where they are set
    meta["numbers"] = json.loads((out_dir / "numbers.json").read_text())
    meta["page_constants"] = {"mc_draws": reach.MC_DRAWS, "acs_state_corr": reach.ACS_STATE_CORR, "page_sets": len(meta["sets"])}
    meta["check_c_groups"] = check_c_groups(out_dir)
    (site_dir / "data.json").write_text(json.dumps(meta, separators=(",", ":")))
    return meta["bin_gz_bytes"], (site_dir / "data.json").stat().st_size


def stat_tiles(out_dir):
    """The three hero numbers as they are written in the page's front matter (value, label, note), from output/numbers.json."""
    n = json.loads((Path(out_dir) / "numbers.json").read_text())
    lo, mid, hi = n["headline"]["tile_1_residents_where_under_25pct_reached"]["p10_p50_p90"]
    sh = n["checks"]["F"]["share_new_by_zip_p10_p50_p90"]["main_page_sets"]
    return [
        {"value": f"{mid / 1e6:.0f} million", "label": "low-income residents where centers reach under 25%", "note": f"Estimate, 80% range {lo / 1e6:.1f} to {hi / 1e6:.1f} million"},
        {"value": f"{100 * n['projection']['share_new_p50_median_zip']:.0f}%", "label": "of a new site's patients use no center today, in the median ZIP",
         "note": f"Estimate, ZIPs run from {100 * sh[0]:.0f}% to {100 * sh[2]:.0f}% (10th to 90th percentile)"},
        {"value": f"{n['headline']['tile_3_of_100_patients_in_model_top20']:.0f} of 100", "label": "patients of unseen centers in top 20 ZIPs", "note": f"Observed, {n['checks']['C']['centers']} centers held out one at a time"},
    ]


def _r(v, d=0, comma=True):
    """Round half up on the decimal text, as the browser's Intl.NumberFormat does (Python's format rounds half to even on the binary value)."""
    q = Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q:,.{d}f}" if comma else f"{q:.{d}f}"


def _approx3(v):
    a = abs(v)
    for u, w in ((1e9, " billion"), (1e6, " million")):
        if a >= u * 0.9995:
            return f"{float(f'{a / u:.3g}'):,}{w}"
    return f"{float(f'{a:.3g}'):,.0f}"


FORMATS = {"int": lambda v: _r(v), "pct0n": lambda v: _r(v), "pct0": lambda v: _r(v) + "%", "pct1": lambda v: _r(v, 1) + "%", "f0": lambda v: _r(100 * v) + "%",
           "f1": lambda v: _r(100 * v, 1) + "%", "num1": lambda v: _r(v, 1), "num2": lambda v: _r(v, 2), "mil1": lambda v: _r(v / 1e6, 1, False) + " million", "k": _approx3, "str": str}


def check_page_text(md_path, out_dir):
    """The page types its numbers twice: in the front matter tiles and in the static text of every data-n span (the page overwrites them from
    data.json). Fail if either differs from what output/ gives, so no number on the page is hand-typed."""
    md = Path(md_path).read_text()
    fm = md.split("---")[1]
    tiles = re.findall(r"- value: (.*)\n\s+label: (.*)\n\s+kind: \w+\n(?:\s+note: (.*)\n)?", fm)
    want = stat_tiles(out_dir)
    assert len(tiles) == len(want), (tiles, want)
    for got, w in zip(tiles, want):
        assert got[0].strip() == w["value"] and got[1].strip() == w["label"] and got[2].strip() == w["note"], (got, w)
    meta = json.loads((Path(out_dir).parents[2] / "assets" / "examples" / "07" / "data.json").read_text())
    bad = []
    for path, fmt, text in re.findall(r'<span data-n="([^"]+)" data-f="(\w+)"[^>]*>([^<]*)</span>', md):
        v = meta
        for k in path.split("."):
            v = v[int(k)] if isinstance(v, list) else v[k]
        if FORMATS[fmt](v) != text:
            bad.append((path, fmt, text, FORMATS[fmt](v)))
    assert not bad, bad
    return len(tiles), len(re.findall(r'<span data-n=', md))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    print(finish(here.parents[1] / "assets" / "examples" / "07", here / "output"))
    for t in stat_tiles(here / "output"):
        print(t["value"], "|", t["label"], "|", t["note"])
    print("front matter and static text agree with output/:", check_page_text(here.parents[1] / "_casestudies" / "07-health-center-site-planner.md", here / "output"))
