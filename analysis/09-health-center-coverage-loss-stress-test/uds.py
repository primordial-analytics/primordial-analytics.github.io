"""HRSA UDS 2025 (awardee file): patients by payer and Table 9D collections for expansion-state centers.

Center rows stay in data/raw (gitignored). Only state totals and the model's
center-level inputs are used downstream; no center is named in any output.
"""
import html
import re

import numpy as np
import pandas as pd

from common import EXPANSION, OUT, RAW


def load():
    x = pd.ExcelFile(RAW / "H80-2025.xlsx")

    def sheet(name, skip_label_row=True):
        d = pd.read_excel(x, name, header=0, dtype=object)
        return d.iloc[1:] if skip_label_row else d

    info = sheet("HealthCenterInfo", False)[["BHCMISID", "HealthCenterState", "UrbanRuralFlag"]]
    t4 = sheet("Table4")
    t9 = sheet("Table9D")
    t9e = sheet("Table9E")

    def num(s):
        return pd.to_numeric(s.replace({"-": np.nan, "---": np.nan}), errors="coerce")

    def ids(d):
        return d["BHCMISID"].astype(str).where(d["BHCMISID"].notna())

    info = info.assign(id=ids(info)).drop(columns="BHCMISID")
    c = pd.DataFrame({"id": ids(t4)})
    for col, name in [("T4_L7_Ca", "unins_0_17"), ("T4_L7_Cb", "unins_18p"),
                      ("T4_L8_Ca", "mcd_0_17"), ("T4_L8_Cb", "mcd_18p"),
                      ("T4_L12_Ca", "pts_0_17"), ("T4_L12_Cb", "pts_18p")]:
        c[name] = num(t4[col]).to_numpy()
    n9 = pd.DataFrame({"id": ids(t9)})
    for k in ["Cb", "Cc1", "Cc2", "Cc3", "Cc4"]:
        n9[f"mcd_{k}"] = num(t9[f"T9d_L3_{k}"]).to_numpy()
        n9[f"all_{k}"] = num(t9[f"T9d_L14_{k}"]).to_numpy()
    n9["selfpay"] = num(t9["T9d_L13_Cb"]).to_numpy()
    e = pd.DataFrame({"id": ids(t9e), "nonpatient_rev": num(t9e["T9e_L11_Ca"]).to_numpy()})
    c, n9, e = (t.dropna(subset=["id"]).drop_duplicates("id") for t in (c, n9, e))
    d = info.merge(c, on="id").merge(n9, on="id", how="left").merge(e, on="id", how="left")
    d = d.rename(columns={"HealthCenterState": "state", "UrbanRuralFlag": "urban_rural"})
    d["patients"] = d.pts_0_17.fillna(0) + d.pts_18p
    d["mcd_pts"] = d.mcd_0_17.fillna(0) + d.mcd_18p
    d["unins_pts"] = d.unins_0_17.fillna(0) + d.unins_18p
    # Medicaid payments: collected this period + reconciliation/wraparound (current and prior years)
    # + other payments, less paybacks; blanks inside a reporting center count as zero.
    d["reports_9d"] = d.mcd_Cb.notna() & d.all_Cb.notna()
    z = lambda p, k: d[f"{p}_{k}"].fillna(0)
    d["mcd_pay"] = np.where(d.reports_9d, z("mcd", "Cb") + z("mcd", "Cc1") + z("mcd", "Cc2") + z("mcd", "Cc3") - z("mcd", "Cc4"), np.nan)
    d["all_pay"] = np.where(d.reports_9d, z("all", "Cb") + z("all", "Cc1") + z("all", "Cc2") + z("all", "Cc3") - z("all", "Cc4"), np.nan)
    d["total_rev"] = d.all_pay + d.nonpatient_rev.fillna(0)
    return d


def shrink(st, d, col, num_col, den_col, floor):
    """Empirical-Bayes shrinkage of a state dollars-per-patient ratio toward the pooled ratio.

    On the log scale: state ratio R_s, within-state spread sigma^2 of the center ratios,
    between-state variance tau^2 = var(log R_s) - mean(sigma^2 / n_s). The weight on the
    state's own value is B_s = tau^2 / (tau^2 + sigma^2 / n_s); n_s is the number of
    reporting centers. The posterior variance is B_s * sigma^2 / n_s. Writes <col>_eb and <col>_eb_sd (posterior sd on the log scale).
    """
    c = d[d.state.isin(EXPANSION) & d.reports_9d & (d[den_col] >= floor) & (d[num_col] > 0)].copy()
    c["lr"] = np.log(c[num_col] / c[den_col])
    sigma2 = c.groupby("state").lr.var(ddof=1)
    n = c.groupby("state").lr.size()
    pooled_sigma2 = float(np.average(sigma2.dropna(), weights=(n[sigma2.dropna().index] - 1)))
    sigma2 = sigma2.reindex(st.state).fillna(pooled_sigma2).to_numpy()
    n = n.reindex(st.state).fillna(0).to_numpy()
    lr_s = np.log(st[col].to_numpy())
    ok = np.isfinite(lr_s) & (n >= 2)
    mu = np.log(c[num_col].sum() / c[den_col].sum())
    tau2 = max(np.var(lr_s[ok], ddof=1) - np.mean(pooled_sigma2 / n[ok]), 1e-4)
    se2 = pooled_sigma2 / np.maximum(n, 1)
    B = np.where(np.isfinite(lr_s) & (n >= 1), tau2 / (tau2 + se2), 0.0)
    post = B * np.nan_to_num(lr_s) + (1 - B) * mu
    st[col + "_eb"] = np.exp(post)
    st[col + "_eb_sd"] = np.sqrt(B * se2)
    st[col + "_weight_on_state"] = B
    return st


def hrsa_national():
    """Published national Table 9D totals (HRSA's national data page), parsed from the saved HTML."""
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", (RAW / "hrsa_national_table9d_2025.html").read_text(errors="ignore"), flags=re.S)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    money = lambda chunk: [float(x.replace(",", "")) for x in re.findall(r"\$([\d,]+)", chunk)]
    med = [m.start() for m in re.finditer(re.escape("3. Total Medicaid (Sum of Lines 1 + 2a + 2b)"), t)]
    tot = [m.start() for m in re.finditer(re.escape("14. TOTAL (Sum of Lines 3 + 6 + 9 + 12 + 13)"), t)]
    sp = t.index("13. Self-Pay")
    out = {
        "medicaid_collected": money(t[med[0]:med[0] + 300])[1],
        "medicaid_net_retros": money(t[med[1]:med[1] + 300])[4],
        "all_collected": money(t[tot[0]:tot[0] + 300])[1],
        "all_net_retros": money(t[tot[1]:tot[1] + 300])[4],
        "selfpay_collected": money(t[sp:sp + 200])[1],
    }
    out["medicaid_payments"] = out["medicaid_collected"] + out["medicaid_net_retros"]
    out["all_payments"] = out["all_collected"] + out["all_net_retros"]
    return out


def main():
    d = load()
    d.to_pickle(RAW / "uds_centers.pkl")
    nat = {
        "centers_total": int(len(d)), "patients_total": float(d.patients.sum()),
        "centers_reporting_9d": int(d.reports_9d.sum()),
    }
    e = d[d.state.isin(EXPANSION)]
    nat.update({"expansion_centers": int(len(e)), "expansion_centers_reporting_9d": int(e.reports_9d.sum()),
                "expansion_mcd_18p": float(e.mcd_18p.sum()), "expansion_mcd_all": float(e.mcd_pts.sum()),
                "expansion_patients": float(e.patients.sum()),
                "all_mcd_18p": float(d.mcd_18p.sum())})
    r = e[e.reports_9d]
    rep, non = e[e.reports_9d], e[~e.reports_9d]
    nat["rep_median_patients"] = float(rep.patients.median())
    nat["nonrep_median_patients"] = float(non.patients.median())
    nat["rep_mcd_share_of_patients"] = float(rep.mcd_pts.sum() / rep.patients.sum())
    nat["nonrep_mcd_share_of_patients"] = float(non.mcd_pts.sum() / non.patients.sum())
    nat["rep_rural_share"] = float((rep.urban_rural == "Rural").mean())
    nat["nonrep_rural_share"] = float((non.urban_rural == "Rural").mean())
    nat["expansion_mcd_pay_per_mcd_patient"] = float(r.mcd_pay.sum() / r.mcd_pts.sum())
    nat["expansion_selfpay_per_uninsured"] = float(r.selfpay.sum() / r.unins_pts.sum())
    # validation against HRSA's published national Table 9D (all 1,356 centers) and Table 4
    h = hrsa_national()
    rep_all = d[d.reports_9d]
    nat.update({f"hrsa_{k}": v for k, v in h.items()})
    nat["all_centers_mcd_pts"] = float(d.mcd_pts.sum())
    nat["all_centers_unins_pts"] = float(d.unins_pts.sum())
    nat["hrsa_mcd_pay_per_mcd_patient"] = h["medicaid_payments"] / d.mcd_pts.sum()
    nat["hrsa_selfpay_per_uninsured"] = h["selfpay_collected"] / d.unins_pts.sum()
    nat["rep_all_mcd_pay_per_mcd_patient"] = float(rep_all.mcd_pay.sum() / rep_all.mcd_pts.sum())
    nat["rep_all_selfpay_per_uninsured"] = float(rep_all.selfpay.sum() / rep_all.unins_pts.sum())
    nat["rep_all_share_of_patients"] = float(rep_all.patients.sum() / d.patients.sum())
    nat["rep_all_share_of_hrsa_mcd_payments"] = float(rep_all.mcd_pay.sum() / h["medicaid_payments"])
    nat["rep_all_share_of_hrsa_all_payments"] = float(rep_all.all_pay.sum() / h["all_payments"])
    nat["rep_all_share_of_hrsa_selfpay"] = float(rep_all.selfpay.sum() / h["selfpay_collected"])
    rows = []
    for st, name in EXPANSION.items():
        s = d[d.state == st]
        rep = s[s.reports_9d & (s.mcd_pts > 0)]
        rows.append({
            "state": st, "name": name, "centers": len(s), "centers_reporting_9d": len(rep),
            "patients": s.patients.sum(), "mcd_patients": s.mcd_pts.sum(), "mcd_adults_18p": s.mcd_18p.sum(),
            "unins_patients": s.unins_pts.sum(),
            "adult_share_of_mcd": s.mcd_18p.sum() / s.mcd_pts.sum(),
            "mcd_pts_per_patient": s.mcd_pts.sum() / s.patients.sum(),
            "mcd_pay_per_mcd_patient": rep.mcd_pay.sum() / rep.mcd_pts.sum() if len(rep) else np.nan,
            "selfpay_per_unins_patient": rep.selfpay.sum() / rep.unins_pts.sum() if len(rep) else np.nan,
            "total_rev_per_patient": rep.total_rev.sum() / rep.patients.sum() if len(rep) else np.nan,
            "mcd_share_of_patient_collections": rep.mcd_pay.sum() / rep.all_pay.sum() if len(rep) else np.nan,
        })
    st = pd.DataFrame(rows)
    for col, num_col, den_col, floor in [("mcd_pay_per_mcd_patient", "mcd_pay", "mcd_pts", 200),
                                         ("selfpay_per_unins_patient", "selfpay", "unins_pts", 200),
                                         ("total_rev_per_patient", "total_rev", "patients", 500)]:
        st = shrink(st, d, col, num_col, den_col, floor)
    st.to_csv(OUT / "uds_state.csv", index=False, float_format="%.6g")
    pd.Series(nat).to_json(OUT / "uds_summary.json", indent=1)
    print(f"{len(st)} states; {nat['expansion_centers']} expansion-state centers, {nat['expansion_centers_reporting_9d']} report Table 9D")


if __name__ == "__main__":
    main()
