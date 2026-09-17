#!/usr/bin/env python3
"""
normalize.py
Cleans the messy PBC files into analysis-ready tables and writes a normalization log.
This mirrors a "data normalization agent": it standardizes, but it does not make audit
judgments. It FLAGS things for you; you decide what they mean.

Usage
  python normalize.py --pbc pbc --out clean

Outputs (clean/)
  trial_balance.csv, sales_ledger.csv, shipping_documents.csv, ar_aging.csv, cash_receipts.csv,
  ap_listing.csv, jan_disbursements.csv, prior_year_monthly.csv, normalization_log.md
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

ABBREV = {"SVCS": "SERVICES", "SVC": "SERVICES", "CO": "COMPANY", "CORP": "CORPORATION",
          "INTL": "INTERNATIONAL", "MFG": "MANUFACTURING"}
DROP = {"INC", "LLC", "THE"}

FS_MAP = {  # account -> (financial statement line, workpaper ref)
    "1000": ("Cash", "C"), "1100": ("Accounts receivable, net", "WP2"),
    "1150": ("Accounts receivable, net", "WP2"), "1200": ("Inventory", "D"),
    "1300": ("Prepaid expenses", "E"), "1500": ("Property and equipment, net", "F"),
    "1550": ("Property and equipment, net", "F"), "2000": ("Accounts payable", "WP3"),
    "2100": ("Accrued liabilities", "WP3"), "2150": ("Income taxes payable", "G"),
    "2200": ("Line of credit", "H"), "3000": ("Equity", "I"), "3100": ("Equity", "I"),
    "4000": ("Net sales", "WP1"), "5000": ("Cost of goods sold", "D"),
    "5100": ("Operating expenses", "WP3"), "6100": ("Operating expenses", "J"),
    "6200": ("Operating expenses", "J"), "6250": ("Operating expenses", "J"),
    "6300": ("Operating expenses", "F"), "6350": ("Operating expenses", "WP2"),
    "6400": ("Operating expenses", "J"), "6500": ("Operating expenses", "J"),
    "7000": ("Interest expense", "H"), "8000": ("Income tax expense", "G"),
}

log_lines = []


def log(msg: str):
    log_lines.append(msg)
    print(msg)


def cust_key(name: str) -> str:
    s = str(name).upper().strip()
    s = re.sub(r"[.,']", "", s).replace("&", " AND ")
    tokens = [ABBREV.get(t, t) for t in s.split()]
    return " ".join(t for t in tokens if t not in DROP)


def parse_date(x):
    if pd.isna(x) or str(x).strip() == "":
        return pd.NaT
    if isinstance(x, (datetime, pd.Timestamp)):
        return pd.Timestamp(x)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d-%b-%y", "%m/%d/%y"):
        try:
            return pd.Timestamp(datetime.strptime(str(x).strip(), fmt))
        except ValueError:
            continue
    return pd.NaT


def parse_amount(x) -> float:
    if pd.isna(x):
        return 0.0
    s = str(x).strip().replace("$", "").replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if s == "":
        return 0.0
    v = float(s)
    return -v if neg else v


def find_header_row(path: Path, first_col: str) -> int:
    raw = pd.read_excel(path, header=None)
    for i, v in raw[0].items():
        if str(v).strip() == first_col:
            return i
    raise ValueError(f"Header '{first_col}' not found in {path.name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbc", default="pbc")
    ap.add_argument("--out", default="clean")
    args = ap.parse_args()
    pbc, out = Path(args.pbc), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log("# Normalization log\n")

    # ---------------------------------------------------------------- customer master
    master = pd.read_csv(pbc / "customer_master.csv", dtype=str)
    master["key"] = master["Customer Name"].apply(cust_key)
    key_to_master = dict(zip(master["key"], zip(master["Cust ID"], master["Customer Name"])))

    def map_customer(df, col, label):
        keys = df[col].apply(cust_key)
        df["cust_id"] = keys.map(lambda k: key_to_master.get(k, (None, None))[0])
        df["customer"] = keys.map(lambda k: key_to_master.get(k, (None, None))[1])
        variants = (df[col].str.strip() != df["customer"]) & df["customer"].notna()
        log(f"- {label}: {int(variants.sum())} rows used a name variant and were mapped to the customer master.")
        unmatched = df[df["customer"].isna()]
        if len(unmatched):
            for name, grp in unmatched.groupby(col):
                log(f"  - **FLAG** {label}: '{name.strip()}' is NOT in the customer master "
                    f"({len(grp)} rows). Kept under its original name. Investigate.")
            df.loc[df["customer"].isna(), "customer"] = df.loc[df["customer"].isna(), col].str.strip()
            df.loc[df["cust_id"].isna(), "cust_id"] = "UNMATCHED"
        return df

    # ---------------------------------------------------------------- trial balance
    tb_path = pbc / "trial_balance_12312025.xlsx"
    hdr = find_header_row(tb_path, "Acct")
    tb = pd.read_excel(tb_path, header=hdr)
    tb = tb[tb["Acct"].notna()].copy()
    tb["account"] = tb["Acct"].astype(int).astype(str)
    tb["cy_balance"] = tb["Debit"].fillna(0) - tb["Credit"].fillna(0)
    tb["py_balance"] = tb["PY Balance (audited)"].astype(float)
    tb["fs_line"] = tb["account"].map(lambda a: FS_MAP[a][0])
    tb["wp_ref"] = tb["account"].map(lambda a: FS_MAP[a][1])
    tb = tb.rename(columns={"Account Description": "account_name"})
    tb = tb[["account", "account_name", "fs_line", "wp_ref", "cy_balance", "py_balance"]]
    tb.to_csv(out / "trial_balance.csv", index=False)
    log(f"\n## Trial balance\n- {len(tb)} accounts. CY nets to {tb['cy_balance'].sum():,.2f}; "
        f"PY nets to {tb['py_balance'].sum():,.2f} (both should be 0.00).")
    tb_bal = dict(zip(tb["account"], tb["cy_balance"]))

    # ---------------------------------------------------------------- sales ledger
    raw = pd.read_csv(pbc / "sales_ledger_fy2025.csv", dtype=str, keep_default_na=False)
    naive_total = raw["Amount"].apply(parse_amount).sum()
    is_sub = (raw["Inv #"].str.strip() == "") & raw["Customer"].str.contains("total", case=False)
    log(f"\n## Sales ledger\n- Raw file: {len(raw)} rows. Removed {int(is_sub.sum())} subtotal rows "
        f"totaling {raw.loc[is_sub, 'Amount'].apply(parse_amount).sum():,.2f}.")
    log(f"  - Naive SUM of the raw Amount column = {naive_total:,.2f} (subtotals double-count revenue).")
    sl = raw[~is_sub].copy()
    sl["inv_date"] = sl["Inv Date"].apply(parse_date)
    sl["ship_date"] = sl["Ship Dt"].apply(parse_date)
    sl["amount"] = sl["Amount"].apply(parse_amount)
    fmt_count = sl["Inv Date"].str.contains("/").sum(), sl["Inv Date"].str.contains(r"^\d{4}-").sum()
    log(f"- Parsed mixed date formats (m/d/Y: {fmt_count[0]}, ISO: {fmt_count[1]}, "
        f"other: {len(sl) - sum(fmt_count)}). Unparseable invoice dates: {int(sl['inv_date'].isna().sum())}.")
    blank_ship = sl["ship_date"].isna()
    if blank_ship.any():
        log(f"  - **FLAG** {int(blank_ship.sum())} invoice(s) have no ship date: "
            f"{', '.join(sl.loc[blank_ship, 'Inv #'])}.")
    sl = map_customer(sl, "Customer", "Sales ledger")
    sl["month"] = sl["inv_date"].dt.strftime("%Y-%m")
    sl = sl.rename(columns={"Inv #": "inv_no", "Memo": "memo"})
    sl = sl[["inv_no", "inv_date", "ship_date", "cust_id", "customer", "amount", "memo", "month"]]
    sl.to_csv(out / "sales_ledger.csv", index=False, date_format="%Y-%m-%d")
    diff = round(sl["amount"].sum() + tb_bal["4000"], 2)
    log(f"- Clean ledger total {sl['amount'].sum():,.2f} vs TB 4000 {-tb_bal['4000']:,.2f}: difference {diff:,.2f}.")
    log("- NOTE: duplicate-invoice testing is intentionally left to WP1 (not done here).")

    # ---------------------------------------------------------------- shipping documents
    sd = pd.read_csv(pbc / "shipping_documents_dec_jan.csv", dtype=str, keep_default_na=False)
    sd["ship_date"] = sd["Actual Ship Date"].apply(parse_date)
    sd = sd.rename(columns={"Shipment ID": "shipment_id", "Invoice": "inv_no",
                            "Carrier": "carrier", "Tracking / BOL": "tracking_bol"})
    sd = sd[["shipment_id", "inv_no", "ship_date", "carrier", "tracking_bol"]]
    duplicate_docs = sorted(set(sd.loc[sd.duplicated("inv_no", keep=False), "inv_no"]))
    cutoff_population = sl[(sl["inv_date"] >= "2025-12-23") & (sl["amount"] >= 15000)]
    missing_docs = sorted(set(cutoff_population["inv_no"]) - set(sd["inv_no"]))
    doc_check = cutoff_population[["inv_no", "ship_date"]].merge(
        sd[["inv_no", "ship_date"]], on="inv_no", how="left", suffixes=("_ledger", "_document")
    )
    date_mismatches = doc_check[
        doc_check["ship_date_document"].notna()
        & (doc_check["ship_date_ledger"] != doc_check["ship_date_document"])
    ]
    log(f"\n## Shipping documents\n- {len(sd)} documents supplied for the late-December cutoff window.")
    if duplicate_docs:
        log(f"  - **FLAG** More than one shipping document for invoice(s): {', '.join(duplicate_docs)}.")
    if missing_docs:
        log(f"  - **FLAG** Selected cutoff invoice(s) have no shipping document: {', '.join(missing_docs)}.")
    if len(date_mismatches):
        log(f"  - **FLAG** {len(date_mismatches)} ledger ship date(s) do not agree to the shipping document.")
    if not duplicate_docs and not missing_docs and not len(date_mismatches):
        log("- All selected cutoff invoices have one shipping document and the dates agree to the ledger.")
    sd.to_csv(out / "shipping_documents.csv", index=False, date_format="%Y-%m-%d")

    # ---------------------------------------------------------------- AR aging
    ag_path = pbc / "ar_aging_12312025.xlsx"
    hdr = find_header_row(ag_path, "Customer Name")
    ag = pd.read_excel(ag_path, header=hdr)
    tot = ag["Customer Name"].astype(str).str.contains("TOTAL", case=False)
    report_total = float(ag.loc[tot, "Balance"].sum())
    ag = ag[~tot & ag["Customer Name"].notna()].copy()
    log(f"\n## A/R aging\n- Skipped {hdr} report-header rows and {int(tot.sum())} GRAND TOTAL row.")
    ag = map_customer(ag, "Customer Name", "A/R aging")
    ag = ag.rename(columns={"Invoice No": "inv_no", "Invoice Date": "inv_date", "Due Date": "due_date",
                            "Balance": "balance", "0-30": "b_0_30", "31-60": "b_31_60", "61-90": "b_61_90",
                            "91-120": "b_91_120", "Over 120": "b_over_120", "Credit Hold": "credit_hold"})
    ag = ag[["cust_id", "customer", "inv_no", "inv_date", "due_date", "balance", "b_0_30", "b_31_60",
             "b_61_90", "b_91_120", "b_over_120", "credit_hold"]]
    ag.to_csv(out / "ar_aging.csv", index=False, date_format="%Y-%m-%d")
    bucket_sum = ag[["b_0_30", "b_31_60", "b_61_90", "b_91_120", "b_over_120"]].sum().sum()
    log(f"- Detail total {ag['balance'].sum():,.2f} | report GRAND TOTAL {report_total:,.2f} | "
        f"buckets cross-foot {bucket_sum:,.2f} | TB 1100 {tb_bal['1100']:,.2f}.")
    notinledger = set(ag["inv_no"]) - set(sl["inv_no"])
    log(f"- Aging invoices not found in the sales ledger: {len(notinledger)}.")
    dup_in_aging = ag[ag.duplicated("inv_no", keep=False)]
    if len(dup_in_aging):
        log(f"  - **FLAG** invoice number(s) appear more than once in the aging: "
            f"{', '.join(sorted(set(dup_in_aging['inv_no'])))}.")

    # ---------------------------------------------------------------- cash receipts
    cr = pd.read_csv(pbc / "cash_receipts_jan_feb_2026.csv", dtype=str, keep_default_na=False)
    cr["receipt_date"] = cr["Date Rec'd"].apply(parse_date)
    cr["amount"] = cr["Amt"].apply(parse_amount)
    cr["ref_inv"] = cr["Ref Inv"].str.strip()
    cr = map_customer(cr, "Payer", "Cash receipts")
    no_ref = cr["ref_inv"].str.upper().str.startswith("INV") == False
    log(f"\n## Cash receipts (Jan-Feb 2026)\n- {len(cr)} receipts totaling {cr['amount'].sum():,.2f}. "
        f"{int(no_ref.sum())} have no invoice reference ('see remit'); match these by customer and amount.")
    cr = cr[["receipt_date", "cust_id", "customer", "ref_inv", "amount"]]
    cr.to_csv(out / "cash_receipts.csv", index=False, date_format="%Y-%m-%d")

    # ---------------------------------------------------------------- AP listing
    apl = pd.read_csv(pbc / "ap_listing_12312025.csv")
    apl = apl.rename(columns={"Vendor": "vendor", "Invoice": "vendor_inv", "Invoice Date": "inv_date",
                              "Due": "due_date", "Open Amount": "amount"})
    apl.to_csv(out / "ap_listing.csv", index=False)
    log(f"\n## A/P listing\n- {len(apl)} open invoices totaling {apl['amount'].sum():,.2f} "
        f"vs TB 2000 {-tb_bal['2000']:,.2f}: difference {round(apl['amount'].sum() + tb_bal['2000'], 2):,.2f}.")

    # ---------------------------------------------------------------- January disbursements
    jd = pd.read_excel(pbc / "jan2026_disbursements.xlsx", dtype={"Check/ACH": str})
    jd = jd.rename(columns={"Check/ACH": "check_no", "Paid": "paid_date", "Payee": "vendor",
                            "Vendor Inv": "vendor_inv", "Inv Dt": "inv_date", "Amount": "amount",
                            "Description": "description"})
    jd.to_csv(out / "jan_disbursements.csv", index=False, date_format="%Y-%m-%d")
    log(f"\n## January 2026 disbursements\n- {len(jd)} payments totaling {jd['amount'].sum():,.2f}.")

    # ---------------------------------------------------------------- prior year monthly
    pym = pd.read_csv(pbc / "prior_year_monthly_sales_2024.csv")
    pym["month"] = pd.to_datetime(pym["Month"], format="%b-%Y").dt.strftime("%Y-%m")
    pym = pym.rename(columns={"Net Sales": "py_net_sales"})[["month", "py_net_sales"]]
    pym.to_csv(out / "prior_year_monthly.csv", index=False)
    log(f"\n## Prior-year monthly sales\n- 12 months totaling {pym['py_net_sales'].sum():,.2f} "
        f"vs PY TB 4000 {-tb.loc[tb['account'] == '4000', 'py_balance'].iloc[0]:,.2f}.")

    (out / "normalization_log.md").write_text("\n".join(log_lines) + "\n")
    print(f"\nClean files written to {out}/")


if __name__ == "__main__":
    main()
