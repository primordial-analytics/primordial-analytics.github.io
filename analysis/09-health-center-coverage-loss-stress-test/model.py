"""Monte Carlo model of 2027 coverage loss and revenue for expansion adults, by state.

Structure (all rates are shares of Medicaid adult-group enrollees, per year of operation):
  excluded E and hardship H   -> subject share S = 1 - overlap * (E + H)
  non-compliance              NC  = S * nc                       (people who do not meet the rule)
  paperwork loss              ADM = (1 - NC) * proc              (people who comply or are exempt, but are
                                                                  dropped for process reasons; CMS Table 40)
  coverage loss               L   = NC + ADM
CMS supplies the levels (Tables 37-40 of the interim final rule). PUMS supplies each state's
excluded and non-compliance composition relative to the pooled expansion states. The 2023-24
unwinding supplies how far each state's ex parte matching and paperwork losses sit from the
pooled states, carried forward with the measured persistence. Revenue applies L to the center's
Medicaid adults, using UDS Medicaid payments per Medicaid patient and self-pay per uninsured patient.
"""
import numpy as np
import pandas as pd
from SALib.analyze import sobol
from SALib.sample.sobol import sample as sobol_sample
from scipy.special import expit, logit
from scipy.stats import beta as beta_dist, norm

from common import CMS, EXPANSION, OUT, RAW

SEED = 20261022
N_DRAWS = 20000
N_SOBOL = 4096

# Overlap between exclusions and hardship exceptions: CMS reports 26% excluded or excepted in total
# against 24.2% + 3.45% = 27.65% added up (24.2 is the sum of Table 37 rows).
E_CMS = sum(CMS["excl_components"].values())
OVERLAP = 0.26 / (E_CMS + CMS["hardship_expected"])

# Inputs (column order of the uniform matrix U). SHARED inputs are national assumptions and use the same
# draw in every state; the others are state choices or state-level noise.
INPUTS = [
    ("regime", "Verification regime (CMS scenario)"),
    ("nc_noise", "Non-compliance rate"),
    ("excl_mult", "Share excluded or exempt"),
    ("hardship", "Hardship exception adopted"),
    ("ex_nat", "Share verified by data matching"),
    ("eps_ex", "State's data matching vs peers"),
    ("eps_pd", "State's paperwork loss vs peers"),
    ("theta", "Loss among data-matched members"),
    ("f_ref", "Expansion share of Medicaid adults"),
    ("kappa", "Medicaid pay, adults vs all patients"),
    ("r_keep", "Share who keep coming"),
    ("v_rel", "Visit rate once uninsured"),
    ("eps_M", "Medicaid payment per patient"),
    ("eps_S", "Self-pay per uninsured patient"),
]
NAMES = [n for n, _ in INPUTS]
LABELS = dict(INPUTS)
SHARED = ["nc_noise", "excl_mult", "ex_nat", "theta", "f_ref", "kappa", "r_keep", "v_rel"]
D = len(INPUTS)
IDX = {n: i for i, n in enumerate(NAMES)}

# Scenario order by impact: 1 (lowest), 3, 4, 2 (highest); upper bounds of the cumulative weights.
SCN_ORDER = [0, 2, 3, 1]
SCN_CUM = np.cumsum([CMS["scenario_weight"][i] for i in SCN_ORDER])[:-1]

SIGMA = {"nc": 0.25, "excl": 0.25, "kappa": 0.15}
BETA_PRIORS = {"ex_nat": (CMS["ex_parte_share"], 0.12), "f_ref": (0.60, 0.08),
               "r_keep": (0.70, 0.12), "v_rel": (0.70, 0.07)}
THETA_MAX = 0.30
EX_CENTRAL = CMS["ex_parte_share"]


def beta_ppf(u, mean, sd):
    k = mean * (1 - mean) / sd ** 2 - 1
    return beta_dist.ppf(u, mean * k, (1 - mean) * k)


def eb_log_ratios(df, comp):
    lr, se = np.log(df[f"{comp}_ratio"].to_numpy()), df[f"{comp}_ratio_se_log"].to_numpy()
    tau2 = max(np.var(lr, ddof=1) - np.mean(se ** 2), 1e-4)
    B = tau2 / (tau2 + se ** 2)
    return B * lr, np.sqrt(B * se ** 2)


def load_params():
    p = pd.read_csv(OUT / "pums_state_ratios.csv").set_index("state")
    u = pd.read_csv(OUT / "uds_state.csv").set_index("state")
    w = pd.read_csv(OUT / "unwinding_state.csv").set_index("state")
    us = pd.read_json(OUT / "unwinding_summary.json", typ="series")
    P = pd.DataFrame(index=list(EXPANSION))
    for comp in ["aian", "preg", "care", "frail", "notmeet"]:
        m, sd = eb_log_ratios(p.loc[P.index].reset_index(), comp)
        P[f"{comp}_lr"], P[f"{comp}_lr_sd"] = m, sd
    f = p.expansion_share_of_medicaid_adults
    fr = np.log(f / np.average(f, weights=p.target_pop))
    fse = p.expansion_share_se / f
    tau2 = max(np.var(fr, ddof=1) - np.mean(fse ** 2), 1e-4)
    B = tau2 / (tau2 + fse ** 2)
    P["f_lr"], P["f_lr_sd"] = (B * fr).loc[P.index], np.sqrt(B * fse ** 2).loc[P.index]
    for k in ["ex", "proc"]:
        P[f"{k}_u"], P[f"{k}_u_sd"] = w[f"{k}_u"], w[f"{k}_u_sd"]
    P["target_pop"] = p.target_pop
    P["adult_per_mcd"] = u.mcd_adults_18p / u.mcd_patients
    P["mcd_per_patient"] = u.mcd_pts_per_patient
    P["M"], P["M_sd"] = u.mcd_pay_per_mcd_patient_eb, u.mcd_pay_per_mcd_patient_eb_sd
    P["S"], P["S_sd"] = u.selfpay_per_unins_patient_eb, u.selfpay_per_unins_patient_eb_sd
    P["rev_pp"] = u.total_rev_per_patient_eb
    P["mcd_adults"] = u.mcd_adults_18p
    P["mcd_patients"] = u.mcd_patients
    P["patients"] = u.patients
    return P, {"ex_tau": us.ex_tau, "proc_tau": us.proc_tau, "rho_ex": us.ex_persistence,
               "rho_proc": us.proc_persistence, "proc_cap": 0.5 * us.proc_gross_share_of_due_max_state, "ex_pooled": us.ex_pooled, "proc_pooled": us.proc_pooled}


def simulate(P, U, up=None):
    """P: one state's parameters (Series); U: (n, D) uniforms in (0,1). Returns a dict of arrays."""
    z = lambda name: norm.ppf(U[:, IDX[name]])
    scn = np.array(SCN_ORDER)[np.searchsorted(SCN_CUM, U[:, IDX["regime"]], side="right")]
    nc_k = np.array(CMS["scenario_noncomp"])[scn]
    proc_k = np.array(CMS["scenario_proc"])[scn]

    # exclusions: CMS Table 37 rows scaled by the state's PUMS ratio; inmates have no PUMS proxy
    comps = CMS["excl_components"]
    E_state = (comps["aian"] * np.exp(P.aian_lr) + comps["pregnant_postpartum"] * np.exp(P.preg_lr)
               + comps["caretaker"] * np.exp(P.care_lr) + comps["medically_frail"] * np.exp(P.frail_lr)
               + comps["inmate"])
    sd_e = (comps["aian"] * P.aian_lr_sd + comps["pregnant_postpartum"] * P.preg_lr_sd
            + comps["caretaker"] * P.care_lr_sd + comps["medically_frail"] * P.frail_lr_sd) / E_CMS
    E = E_state * np.exp(np.hypot(SIGMA["excl"], sd_e) * z("excl_mult"))
    H = np.where(U[:, IDX["hardship"]] < CMS["hardship_adoption"], CMS["hardship_if_adopted"], 0.0)
    S = np.clip(1 - OVERLAP * (E + H), 0.25, 1.0)
    nc = np.clip(nc_k * np.exp(P.notmeet_lr) * np.exp(np.hypot(SIGMA["nc"], P.notmeet_lr_sd) * z("nc_noise")), 0, 0.6)
    NC = S * nc

    # paperwork loss: CMS net rate for the scenario, moved on the log-odds scale by the state's
    # unwinding position (persistent part plus new noise), then scaled by how many members are
    # verified by data matching
    def state_shift(k, rho, tau, eps):
        sd = np.sqrt(rho ** 2 * P[f"{k}_u_sd"] ** 2 + (1 - rho ** 2) * tau ** 2)
        return rho * P[f"{k}_u"] + sd * eps
    d_pd = state_shift("proc", up["rho_proc"], up["proc_tau"], z("eps_pd"))
    d_ex = state_shift("ex", up["rho_ex"], up["ex_tau"], z("eps_ex"))
    ex_nat = beta_ppf(U[:, IDX["ex_nat"]], *BETA_PRIORS["ex_nat"])
    ex_s = expit(logit(ex_nat) + d_ex)
    theta = THETA_MAX * U[:, IDX["theta"]]
    ex_factor = ((1 - ex_s) + theta * ex_s) / ((1 - EX_CENTRAL) + theta * EX_CENTRAL)
    proc = np.clip(expit(logit(proc_k) + d_pd) * ex_factor, 0, up["proc_cap"])  # capped at half the worst gross rate seen (CMS nets out 50% baseline)
    ADM = (1 - NC) * proc
    L = NC + ADM
    L_subject = nc + (1 - nc) * proc

    # revenue
    f = np.clip(beta_ppf(U[:, IDX["f_ref"]], *BETA_PRIORS["f_ref"]) * np.exp(P.f_lr), 0.1, 0.95)
    kappa = np.exp(SIGMA["kappa"] * z("kappa"))
    M = P.M * np.exp(P.M_sd * z("eps_M"))
    S_pay = P.S * np.exp(P.S_sd * z("eps_S"))
    keep = beta_ppf(U[:, IDX["r_keep"]], *BETA_PRIORS["r_keep"]) * beta_ppf(U[:, IDX["v_rel"]], *BETA_PRIORS["v_rel"])
    net_per_lost = kappa * M - keep * S_pay                  # dollars per adult who loses coverage, per year
    exposed = P.adult_per_mcd * f                            # expansion adults per Medicaid patient
    net_per_1000 = 1000 * exposed * L * net_per_lost
    pct_mcd = exposed * L * net_per_lost / P.M
    pct_rev = P.mcd_per_patient * exposed * L * net_per_lost / P.rev_pp
    return {"L": L, "NC": NC, "ADM": ADM, "L_subject": L_subject, "E": E, "H": H, "S": S, "nc": nc,
            "proc": proc, "ex_s": ex_s, "f": f, "kappa": kappa, "keep": keep, "S_pay": S_pay,
            "net_per_1000": net_per_1000, "pct_mcd": pct_mcd, "pct_rev": pct_rev, "net_per_lost": net_per_lost}


def build_U(n, rng):
    shared = rng.uniform(1e-6, 1 - 1e-6, size=(n, D))
    return shared


def state_U(shared, rng):
    U = rng.uniform(1e-6, 1 - 1e-6, size=shared.shape)
    for name in SHARED:
        U[:, IDX[name]] = shared[:, IDX[name]]
    return U


def q(x, qs=(5, 50, 95)):
    return np.percentile(x, qs)


def sobol_state(P, up, outputs, n=N_SOBOL):
    problem = {"num_vars": D, "names": NAMES, "bounds": [[1e-6, 1 - 1e-6]] * D}
    X = sobol_sample(problem, n, calc_second_order=False, seed=SEED)
    sim = simulate(P, X, up)
    res = {}
    for out in outputs:
        r = sobol.analyze(problem, sim[out], calc_second_order=False)
        res[out] = pd.DataFrame({"input": NAMES, "S1": r["S1"], "ST": r["ST"]})
    return res


def oat(P, up, out, lo=0.1, hi=0.9):
    base = np.full((1, D), 0.5)
    b = simulate(P, base, up)[out][0]
    rows = []
    for name in NAMES:
        r = {}
        for tag, val in (("lo", lo), ("hi", hi)):
            U = base.copy()
            U[0, IDX[name]] = val
            r[tag] = simulate(P, U, up)[out][0]
        rows.append({"input": name, "label": LABELS[name], "base": b, "p10": r["lo"], "p90": r["hi"]})
    return pd.DataFrame(rows)


def main():
    P, up = load_params()
    rng = np.random.default_rng(SEED)
    shared = build_U(N_DRAWS, rng)
    sims = {st: simulate(P.loc[st], state_U(shared, rng), up) for st in P.index}

    # ---- state table
    rows = []
    for st, name in EXPANSION.items():
        s = sims[st]
        row = {"state": st, "name": name}
        for key, col in [("L", "total"), ("NC", "work_req"), ("ADM", "paperwork")]:
            lo, mid, hi = q(s[key])
            row[f"{col}_p5"], row[f"{col}_p50"], row[f"{col}_p95"] = lo, mid, hi
        row["admin_share_of_loss_p50"] = np.median(s["ADM"] / s["L"])
        lo, mid, hi = q(s["net_per_1000"])
        row["net_loss_per_1000_mcd_patients_p5"], row["net_loss_per_1000_mcd_patients_p50"], row["net_loss_per_1000_mcd_patients_p95"] = lo, mid, hi
        lo, mid, hi = q(s["pct_mcd"] * 100)
        row["pct_of_mcd_payments_p5"], row["pct_of_mcd_payments_p50"], row["pct_of_mcd_payments_p95"] = lo, mid, hi
        lo, mid, hi = q(s["pct_rev"] * 100)
        row["pct_of_total_revenue_p5"], row["pct_of_total_revenue_p50"], row["pct_of_total_revenue_p95"] = lo, mid, hi
        row["expansion_share_of_mcd_adults_p50"] = np.median(s["f"])
        row["expansion_adults_per_1000_mcd_patients"] = 1000 * P.loc[st, "adult_per_mcd"] * np.median(s["f"])
        row["mcd_pay_per_mcd_patient"] = P.loc[st, "M"]
        row["selfpay_per_uninsured_patient"] = P.loc[st, "S"]
        row["mcd_adults_uds_2025"] = P.loc[st, "mcd_adults"]
        row["expansion_adults_at_centers_p50"] = P.loc[st, "mcd_adults"] * np.median(s["f"])
        row["lost_adults_at_centers_p5"], row["lost_adults_at_centers_p50"], row["lost_adults_at_centers_p95"] = \
            q(P.loc[st, "mcd_adults"] * s["f"] * s["L"])
        row["subject_loss_p50"] = np.median(s["L_subject"])
        rows.append(row)
    states = pd.DataFrame(rows)

    # ---- national check against CMS Table 40/41
    w = P.target_pop / P.target_pop.sum()
    L_nat = sum(w[st] * sims[st]["L"] for st in P.index)
    NC_nat = sum(w[st] * sims[st]["NC"] for st in P.index)
    ADM_nat = sum(w[st] * sims[st]["ADM"] for st in P.index)
    adults_m = CMS["applicable_adults_m"]
    n_chk = {
        "cms_noncomp_share_total": CMS["subject_share"] * CMS["noncomp_central"],
        "cms_proc_share_total": CMS["proc_central"] * (1 - CMS["subject_share"] * CMS["noncomp_central"]),
    }
    n_chk["cms_combined"] = n_chk["cms_noncomp_share_total"] + n_chk["cms_proc_share_total"]
    n_chk["cms_full_year_m"] = adults_m * n_chk["cms_combined"]
    n_chk["cms_fy2027_m"] = n_chk["cms_full_year_m"] * CMS["fy2027_share_of_full_year"]
    wt, nct, pt = CMS["scenario_weight"], CMS["scenario_noncomp"], CMS["scenario_proc"]
    nc_w, pr_w = float(np.dot(wt, nct)), float(np.dot(wt, pt))
    n_chk["table39_weighted_noncomp"], n_chk["table39_weighted_proc"] = nc_w, pr_w
    n_chk["table39_combined"] = CMS["subject_share"] * nc_w + pr_w * (1 - CMS["subject_share"] * nc_w)
    n_chk["overlap_factor"] = OVERLAP
    n_chk["excl_sum_table37"] = E_CMS
    lo, mid, hi = q(L_nat * 100)
    n_chk["model_national_loss_pct_p5"], n_chk["model_national_loss_pct_p50"], n_chk["model_national_loss_pct_p95"] = lo, mid, hi
    lo, mid, hi = q(NC_nat * 100)
    n_chk["model_national_noncomp_pct_p50"] = mid
    n_chk["model_national_admin_pct_p50"] = float(np.median(ADM_nat) * 100)
    lo, mid, hi = q(L_nat * adults_m * CMS["fy2027_share_of_full_year"])
    n_chk["model_fy2027_m_p5"], n_chk["model_fy2027_m_p50"], n_chk["model_fy2027_m_p95"] = lo, mid, hi
    lo, mid, hi = q(L_nat * adults_m)
    n_chk["model_full_year_m_p5"], n_chk["model_full_year_m_p50"], n_chk["model_full_year_m_p95"] = lo, mid, hi
    n_chk["share_of_draws_nat_below_cms"] = float((L_nat < n_chk["cms_combined"]).mean())
    n_chk["state_median_of_p50_total"] = float(states.total_p50.median())
    # all expansion-state centers together (national assumptions shared across states, so these add up)
    lost = sum(P.loc[st, "mcd_adults"] * sims[st]["f"] * sims[st]["L"] for st in P.index)
    usd = sum(P.loc[st, "mcd_adults"] * sims[st]["f"] * sims[st]["L"] * sims[st]["net_per_lost"] for st in P.index)
    exp_adults = sum(P.loc[st, "mcd_adults"] * sims[st]["f"] for st in P.index)
    n_chk["centers_expansion_adults_p50"] = float(np.median(exp_adults))
    n_chk["centers_lost_adults_p5"], n_chk["centers_lost_adults_p50"], n_chk["centers_lost_adults_p95"] = q(lost)
    n_chk["centers_net_loss_usd_p5"], n_chk["centers_net_loss_usd_p50"], n_chk["centers_net_loss_usd_p95"] = q(usd)
    n_chk["centers_admin_lost_adults_p50"] = float(np.median(sum(P.loc[st, "mcd_adults"] * sims[st]["f"] * sims[st]["ADM"] for st in P.index)))
    # Nebraska plausibility check (one early datum, not used to tune anything)
    ne = sims["NE"]["L_subject"]
    n_chk["ne_subject_loss_p5"], n_chk["ne_subject_loss_p50"], n_chk["ne_subject_loss_p95"] = q(ne)
    n_chk["ne_total_loss_p5"], n_chk["ne_total_loss_p50"], n_chk["ne_total_loss_p95"] = q(sims["NE"]["L"])
    n_chk["ne_observed_renewal_loss"] = 0.07
    n_chk["ne_observed_application_denials"] = 0.14
    # KFF's 7% covers about five months (May to Sept 2026): compare with a half-year equivalent of our annual rate
    n_chk["ne_half_year_equiv_p5"], n_chk["ne_half_year_equiv_p50"], n_chk["ne_half_year_equiv_p95"] = q(ne / 2)

    # ---- Sobol (per state) and one-at-a-time swings (typical state)
    sob = {}
    for st in P.index:
        r = sobol_state(P.loc[st], up, ["L", "pct_rev"])
        for out, t in r.items():
            t.insert(0, "state", st)
            t.insert(1, "output", out)
            sob.setdefault(out, []).append(t)
    sob_all = pd.concat([t for v in sob.values() for t in v])
    sob_all["label"] = sob_all.input.map(LABELS)
    sob_all.to_csv(OUT / "sobol_by_state.csv", index=False, float_format="%.4f")
    sob_med = (sob_all.groupby(["output", "input"])[["S1", "ST"]].median().reset_index())
    sob_med["label"] = sob_med.input.map(LABELS)
    # typical state: the one whose median loss is closest to the median across states
    typ = states.loc[(states.total_p50 - states.total_p50.median()).abs().idxmin(), "state"]
    tor = []
    for out in ["L", "pct_rev"]:
        t = oat(P.loc[typ], up, out)
        t.insert(0, "output", out)
        tor.append(t)
    tor = pd.concat(tor)
    tor.to_csv(OUT / "tornado_typical_state.csv", index=False, float_format="%.5g")
    sob_med.to_csv(OUT / "sobol_median_across_states.csv", index=False, float_format="%.4f")
    # top two inputs by total-order index, per state, per output
    top = {}
    for out in ["L", "pct_rev"]:
        t = sob_all[sob_all.output == out]
        top[out] = t.sort_values(["state", "ST"], ascending=[True, False]).groupby("state").head(3)
    n_chk["typical_state"] = typ
    n_chk["sobol_sum_S1_median_L"] = float(sob_all[sob_all.output == "L"].groupby("state").S1.sum().median())
    n_chk["sobol_sum_S1_median_rev"] = float(sob_all[sob_all.output == "pct_rev"].groupby("state").S1.sum().median())
    top["L"].to_csv(OUT / "sobol_top3_L.csv", index=False, float_format="%.4f")

    # ---- peer benchmark (aggregated bands only; no center is named)
    d = pd.read_pickle(RAW / "uds_centers.pkl")
    d = d[d.state.isin(EXPANSION) & d.reports_9d & (d.mcd_18p > 0) & (d.mcd_pts >= 200) & d.total_rev.gt(0)].copy()
    d["band"] = pd.cut(d.patients, [0, 5000, 15000, 40000, 1e9], right=False,
                       labels=["Under 5,000", "5,000-14,999", "15,000-39,999", "40,000+"])
    d["Mi"] = d.mcd_pay / d.mcd_pts
    cp = []
    for _, c in d.iterrows():
        s, Pst = sims[c.state], P.loc[c.state]
        Mi = float(np.clip(c.Mi, 0.4 * Pst.M, 2.5 * Pst.M))
        loss = c.mcd_18p * s["f"] * s["L"] * (s["kappa"] * Mi - s["keep"] * s["S_pay"])
        pr = loss / c.total_rev * 100
        cp.append([*q(pr), *q(loss), float(c.mcd_18p * np.median(s["f"]))])
    cp = pd.DataFrame(cp, columns=["pct_p5", "pct_p50", "pct_p95", "usd_p5", "usd_p50", "usd_p95", "exp_adults"], index=d.index)
    d = d.join(cp)
    bench = []
    for (band, ur), g in d.groupby(["band", "urban_rural"], observed=True):
        n_all = len(d[(d.band == band) & (d.urban_rural == ur)])
        row = {"size_band_patients": band, "setting": ur, "centers_reporting_9d": n_all}
        if n_all < 5:
            row["note"] = "fewer than 5 centers; suppressed"
        else:
            row.update({
                "median_medicaid_share_of_patients": float((g.mcd_pts / g.patients).median()),
                "median_expansion_adults_est": float(g.exp_adults.median()),
                "median_net_loss_usd_p5": float(g.usd_p5.median()), "median_net_loss_usd_p50": float(g.usd_p50.median()),
                "median_net_loss_usd_p95": float(g.usd_p95.median()),
                "median_pct_of_total_revenue_p5": float(g.pct_p5.median()),
                "median_pct_of_total_revenue_p50": float(g.pct_p50.median()),
                "median_pct_of_total_revenue_p95": float(g.pct_p95.median()),
                "share_of_centers_losing_over_3pct_of_revenue_p50": float((g.pct_p50 > 3).mean()),
            })
        bench.append(row)
    bench = pd.DataFrame(bench)
    bench.to_csv(OUT / "peer_benchmark.csv", index=False, float_format="%.4g")
    edges = np.arange(0, 8.01, 0.4)
    counts, _ = np.histogram(d.pct_p50.clip(upper=8 - 1e-9), bins=edges)
    pd.DataFrame({"pct_from": edges[:-1], "pct_to": edges[1:], "centers": counts}).to_csv(
        OUT / "peer_histogram.csv", index=False, float_format="%.1f")
    n_chk["benchmark_centers"] = int(len(d))
    n_chk["benchmark_pct_p50_median"] = float(d.pct_p50.median())
    n_chk["benchmark_pct_p50_p10"], n_chk["benchmark_pct_p50_p90"] = [float(x) for x in np.percentile(d.pct_p50, [10, 90])]
    n_chk["benchmark_share_over_3pct"] = float((d.pct_p50 > 3).mean())
    n_chk["benchmark_share_over_5pct"] = float((d.pct_p50 > 5).mean())

    # ---- the downloadable state table; Low/Mid/High columns paste into the Medicaid what-if workbook
    # (Inputs C24:E24 and C25:E25). Shares are fractions of expansion adults per year of operation.
    wb = pd.DataFrame({
        "state": states.state, "state_name": states.name,
        "low_work_requirement": states.work_req_p5, "mid_work_requirement": states.work_req_p50,
        "high_work_requirement": states.work_req_p95,
        "low_paperwork": states.paperwork_p5, "mid_paperwork": states.paperwork_p50, "high_paperwork": states.paperwork_p95,
        "total_loss_p5": states.total_p5, "total_loss_p50": states.total_p50, "total_loss_p95": states.total_p95,
        "paperwork_share_of_loss_p50": states.admin_share_of_loss_p50,
        "expansion_adults_per_1000_medicaid_patients": states.expansion_adults_per_1000_mcd_patients,
        "net_loss_usd_per_1000_medicaid_patients_p5": states.net_loss_per_1000_mcd_patients_p5,
        "net_loss_usd_per_1000_medicaid_patients_p50": states.net_loss_per_1000_mcd_patients_p50,
        "net_loss_usd_per_1000_medicaid_patients_p95": states.net_loss_per_1000_mcd_patients_p95,
        "net_loss_pct_of_total_revenue_p5": states.pct_of_total_revenue_p5,
        "net_loss_pct_of_total_revenue_p50": states.pct_of_total_revenue_p50,
        "net_loss_pct_of_total_revenue_p95": states.pct_of_total_revenue_p95,
    }).sort_values("state")
    for c in wb.columns[2:12]:
        wb[c] = wb[c].round(4)
    wb.iloc[:, 12:] = wb.iloc[:, 12:].round(1)
    wb.to_csv(OUT / "state_inputs_for_whatif_workbook.csv", index=False)
    states = states.sort_values("total_p50", ascending=False)
    states.to_csv(OUT / "state_ranges.csv", index=False, float_format="%.5g")
    pd.Series(n_chk).to_json(OUT / "model_summary.json", indent=1)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(pd.Series(n_chk).to_string())
    print(states[["state", "total_p5", "total_p50", "total_p95", "work_req_p50", "paperwork_p50", "pct_of_total_revenue_p5", "pct_of_total_revenue_p50", "pct_of_total_revenue_p95"]].round(3).to_string())
    print(sob_med[sob_med.output == "L"].sort_values("ST", ascending=False).round(3).to_string())
    print(sob_med[sob_med.output == "pct_rev"].sort_values("ST", ascending=False).round(3).to_string())
    print(tor.round(4).to_string())
    print(bench.round(3).to_string())


if __name__ == "__main__":
    main()
