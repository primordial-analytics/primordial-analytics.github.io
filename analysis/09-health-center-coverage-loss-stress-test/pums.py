"""ACS 2024 PUMS: how each expansion state differs from the pooled expansion states.

Target group (a proxy for the Medicaid adult group, which PUMS cannot identify):
ages 19-64, covered by Medicaid or other means-tested public coverage (HINS4),
no Medicare, no SSI, household income at or below 138% of poverty.

For each state we measure, inside that group, the share in each CMS exclusion
category we can proxy and the share not meeting an 80-hour-a-month test. The model
uses only the ratio of the state share to the pooled share, so CMS's own national
levels stay in charge of the level. Sampling error comes from the 80 replicate weights.
"""
import numpy as np
import pandas as pd

from common import EXPANSION, OUT, RAW

REP = [f"PWGTP{i}" for i in range(1, 81)]
COLS = ["SERIALNO", "STATE", "AGEP", "RELSHIPP", "HINS3", "HINS4", "POVPIP", "SSIP",
        "DPHY", "DREM", "DDRS", "DOUT", "FER", "RACAIAN", "SCH", "ESR", "WKHP",
        "WAGP", "SEMP", "ADJINC", "PWGTP"] + REP
MIN_MONTHLY_INCOME = 80 * 7.25  # 80 hours at the federal minimum wage


def state_sums(st):
    path = next((RAW / "pums" / f"p{st.lower()}").glob("psam_p*.csv"))
    d = pd.read_csv(path, usecols=COLS)
    # households with a child 13 or under who is a relative of the householder
    kid = (d.AGEP <= 13) & d.RELSHIPP.isin([25, 26, 27, 28, 30, 33, 35])
    hh_kid = kid.groupby(d.SERIALNO).transform("any")
    caretaker = hh_kid & d.RELSHIPP.isin([20, 21, 22, 23, 24])

    tgt = (d.AGEP.between(19, 64) & (d.HINS4 == 1) & (d.HINS3 != 1)
           & (d.SSIP.fillna(0) == 0) & (d.POVPIP <= 138))
    aian = d.RACAIAN == 1
    preg = d.FER == 1
    frail = (d[["DPHY", "DREM", "DDRS", "DOUT"]] == 1).any(axis=1)
    excl = aian | preg | frail | caretaker
    earn = (d.WAGP.fillna(0) + d.SEMP.fillna(0)) * d.ADJINC / 1e6
    meets = (d.ESR.isin([1, 2, 4, 5]) & (d.WKHP >= 80 / 4.33)) | (earn >= 12 * MIN_MONTHLY_INCOME) \
        | d.SCH.isin([2, 3])
    # all Medicaid adults 18+ who are not on Medicare (the UDS Medicaid 18+ line is the comparable count)
    mcd_adult = (d.AGEP >= 18) & (d.HINS4 == 1) & (d.HINS3 != 1)

    ind = {
        "target": tgt, "aian": tgt & aian, "preg": tgt & preg, "care": tgt & caretaker,
        "frail": tgt & frail, "excl": tgt & excl,
        "subject": tgt & ~excl, "notmeet": tgt & ~excl & ~meets,
        "mcd_adult": mcd_adult,
        "target_part": tgt & (d.POVPIP.notna()),
    }
    W = d[["PWGTP"] + REP].to_numpy(dtype=float)
    sums = {k: v.to_numpy(dtype=float) @ W for k, v in ind.items()}
    sums["n_target_unweighted"] = np.array([float(tgt.sum())])
    return sums


def main():
    allsums = {st: state_sums(st) for st in EXPANSION}
    keys = [k for k in allsums["AK"] if k != "n_target_unweighted"]
    pooled = {k: sum(allsums[s][k] for s in allsums) for k in keys}

    def share(s, num, den):
        return s[num] / s[den]

    rows = []
    comps = {"aian": "target", "preg": "target", "care": "target", "frail": "target",
             "excl": "target", "notmeet": "subject"}
    for st, name in EXPANSION.items():
        s = allsums[st]
        row = {"state": st, "name": name, "n_target_sample": int(s["n_target_unweighted"][0]),
               "target_pop": s["target"][0]}
        for c, den in comps.items():
            sh = share(s, c, den)           # 81 values: full weight, then replicates
            nat = share(pooled, c, den)
            lr = np.log(sh / nat)
            row[f"{c}_share"] = sh[0]
            row[f"{c}_ratio"] = np.exp(lr[0])
            row[f"{c}_ratio_se_log"] = np.sqrt(4 / 80 * np.sum((lr[1:] - lr[0]) ** 2))
        f = s["target"] / s["mcd_adult"]    # expansion proxy share of Medicaid adults 18+
        row["expansion_share_of_medicaid_adults"] = f[0]
        row["expansion_share_se"] = np.sqrt(4 / 80 * np.sum((f[1:] - f[0]) ** 2))
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "pums_state_ratios.csv", index=False, float_format="%.5g")
    nat = {c + "_share": pooled[c][0] / pooled[d][0] for c, d in comps.items()}
    nat["target_pop"] = pooled["target"][0]
    nat["mcd_adult_pop"] = pooled["mcd_adult"][0]
    pd.Series(nat).to_json(OUT / "pums_pooled.json", indent=1)
    print(f"{len(df)} states; target group {nat['target_pop']:,.0f} people")


if __name__ == "__main__":
    main()
