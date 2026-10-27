"""Read every 990, 990-EZ and 990-PF in the IRS zip batches and write two tables per batch to data/raw/_parsed/:

filings: one row per return (filer EIN, name, address, form, tax year, mission, revenue, grants paid; for charities
         whether they hold donor-advised funds or run a hospital; for private foundations the "only contributes to
         preselected organizations" box and the how-to-apply text).
grants:  one row per grant listed on Schedule I (charities) or the 990-PF grants-paid list (private foundations).
related: one row per related organization with an EIN on Schedule R (tax-exempt, or a taxable corporation or trust),
         so that money moving inside a health system is not mistaken for a grant anyone could apply for.

Batches are parsed in parallel, one process per batch, and a batch already parsed is skipped.
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
import zipfile_deflate64 as zipfile  # zipfile plus Deflate64, which some 2025 batches use
from lxml import etree

RAW = Path(__file__).parent / "data" / "raw"
OUT = RAW / "_parsed"
WORKERS = 4
FORMS = {"990", "990EZ", "990PF"}
YES = {"1", "true", "X"}


def txt(e, path):
    r = e.find(path)
    return r.text.strip() if r is not None and r.text else ""


def num(e, path):
    try:
        return float(txt(e, path) or 0)
    except ValueError:
        return 0.0


def name_of(e, base):
    """Business name lines 1 and 2 under `base`, or a person name when the filer typed the recipient there."""
    lines = [txt(e, f"{base}/{{*}}BusinessNameLine1Txt"), txt(e, f"{base}/{{*}}BusinessNameLine2Txt")]
    return " ".join(x for x in lines if x)


def filing_row(root, object_id):
    h = root.find("{*}ReturnHeader")
    form = txt(h, "{*}ReturnTypeCd")
    body = root.find("{*}ReturnData/{*}IRS" + form)
    row = dict(object_id=object_id, ein=txt(h, "{*}Filer/{*}EIN"), name=name_of(h, "{*}Filer/{*}BusinessName"),
               city=txt(h, "{*}Filer/{*}USAddress/{*}CityNm"), state=txt(h, "{*}Filer/{*}USAddress/{*}StateAbbreviationCd"),
               zip=txt(h, "{*}Filer/{*}USAddress/{*}ZIPCd")[:5], form=form, tax_year=txt(h, "{*}TaxYr"),
               period_end=txt(h, "{*}TaxPeriodEndDt"), amended=False, mission="", revenue=0.0, website="",
               grants_paid=0.0, daf=False, hospital=False, preselected=False, apply_form="", apply_deadlines="",
               apply_restrictions="")
    if body is None:
        return row
    row["amended"] = txt(body, "{*}AmendedReturnInd") in YES
    if form == "990":
        row.update(mission=txt(body, "{*}ActivityOrMissionDesc") or txt(body, "{*}MissionDesc"),
                   revenue=num(body, "{*}CYTotalRevenueAmt"), website=txt(body, "{*}WebsiteAddressTxt"),
                   grants_paid=num(body, "{*}CYGrantsAndSimilarPaidAmt"),
                   daf=txt(body, "{*}DonorAdvisedFundInd") in YES, hospital=txt(body, "{*}OperateHospitalInd") in YES)
    elif form == "990EZ":
        row.update(mission=txt(body, "{*}PrimaryExemptPurposeTxt"), revenue=num(body, "{*}TotalRevenueAmt"),
                   website=txt(body, "{*}WebsiteAddressTxt"), grants_paid=num(body, "{*}GrantsAndSimilarAmountsPaidAmt"))
    else:
        s = body.find("{*}SupplementaryInformationGrp")
        row.update(revenue=num(body, "{*}AnalysisOfRevenueAndExpenses/{*}TotalRevAndExpnssAmt"),
                   grants_paid=num(body, "{*}AnalysisOfRevenueAndExpenses/{*}ContriPaidRevAndExpnssAmt"),
                   website=txt(body, "{*}StatementsRegardingActyGrp/{*}WebsiteAddressTxt"))
        if s is not None:
            a = s.find("{*}ApplicationSubmissionInfoGrp")
            row.update(preselected=txt(s, "{*}OnlyContriToPreselectedInd") in YES,
                       apply_form=txt(a, "{*}FormAndInfoAndMaterialsTxt") if a is not None else "",
                       apply_deadlines=txt(a, "{*}SubmissionDeadlinesTxt") if a is not None else "",
                       apply_restrictions=txt(a, "{*}RestrictionsOnAwardsTxt") if a is not None else "")
    return row


def grant_rows(root, object_id):
    out = []
    for i, g in enumerate(root.iter("{*}RecipientTable")):
        out.append(dict(object_id=object_id, line=i, src="I", recipient_ein=txt(g, "{*}RecipientEIN"),
                        name=name_of(g, "{*}RecipientBusinessName"), person=False,
                        city=txt(g, "{*}USAddress/{*}CityNm"), state=txt(g, "{*}USAddress/{*}StateAbbreviationCd"),
                        zip=txt(g, "{*}USAddress/{*}ZIPCd")[:5], foreign=g.find("{*}ForeignAddress") is not None,
                        amount=num(g, "{*}CashGrantAmt") + num(g, "{*}NonCashAssistanceAmt"),
                        purpose=txt(g, "{*}PurposeOfGrantTxt"), status=txt(g, "{*}IRCSectionDesc")))
    for i, g in enumerate(root.iter("{*}GrantOrContributionPdDurYrGrp")):
        person = txt(g, "{*}RecipientPersonNm")
        out.append(dict(object_id=object_id, line=i, src="PF", recipient_ein="",
                        name=name_of(g, "{*}RecipientBusinessName") or person, person=bool(person),
                        city=txt(g, "{*}RecipientUSAddress/{*}CityNm"),
                        state=txt(g, "{*}RecipientUSAddress/{*}StateAbbreviationCd"),
                        zip=txt(g, "{*}RecipientUSAddress/{*}ZIPCd")[:5],
                        foreign=g.find("{*}RecipientForeignAddress") is not None, amount=num(g, "{*}Amt"),
                        purpose=txt(g, "{*}GrantOrContributionPurposeTxt"),
                        status=txt(g, "{*}RecipientFoundationStatusTxt")))
    return out


def related_rows(root, object_id):
    return [dict(object_id=object_id, related_ein=txt(g, "{*}EIN"))
            for tag in ("IdRelatedTaxExemptOrgGrp", "IdRelatedOrgTxblCorpTrGrp")
            for g in root.iter("{*}" + tag) if txt(g, "{*}EIN")]


def parse_batch(path):
    done = OUT / f"{path.stem}.filings.parquet"
    if not (OUT / f"{path.stem}.related.parquet").exists():
        done.unlink(missing_ok=True)  # parsed before Schedule R was read
    if done.exists():
        return path.name, "cached"
    filings, grants, related, bad = [], [], [], 0
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if not member.endswith(".xml"):
                continue
            x = z.read(member)
            if not any(f"<ReturnTypeCd>{f}</ReturnTypeCd>".encode() in x for f in FORMS):
                continue  # 990-T and 990-O carry no grants
            try:
                root = etree.fromstring(x)
            except etree.XMLSyntaxError:
                bad += 1
                continue
            oid = Path(member).stem.split("_")[0]
            filings.append(filing_row(root, oid))
            if b"RecipientTable" in x or b"GrantOrContributionPdDurYrGrp" in x:
                grants.extend(grant_rows(root, oid))
            if b"IRS990ScheduleR" in x:
                related.extend(related_rows(root, oid))
    pd.DataFrame(grants).to_parquet(OUT / f"{path.stem}.grants.parquet", index=False)
    pd.DataFrame(related, columns=["object_id", "related_ein"]).to_parquet(OUT / f"{path.stem}.related.parquet", index=False)
    pd.DataFrame(filings).to_parquet(done, index=False)  # written last: marks the batch complete
    return path.name, f"{len(filings)} filings, {len(grants)} grants, {len(related)} related, {bad} unreadable"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    zips = sorted(RAW.glob("*.zip"), key=lambda p: -p.stat().st_size)  # big batches first
    with ProcessPoolExecutor(WORKERS, initializer=os.nice, initargs=(15,)) as ex:
        for name, msg in ex.map(parse_batch, zips):
            print(f"  {name}: {msg}", flush=True)


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    main()
