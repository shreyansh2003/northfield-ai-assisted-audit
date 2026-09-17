#!/usr/bin/env python3
"""
generate_pbc.py
Synthetic "Prepared By Client" (PBC) data for the Northfield Supply Co. FY2025 mini-audit.

Northfield Supply Co. is a FICTIONAL wholesale distributor of janitorial and facility
supplies (Cleveland, OH). Fiscal year ends 12/31/2025. All data is synthetic.

What it writes
  pbc/                      <- the "client" files (deliberately messy)
    trial_balance_12312025.xlsx
    sales_ledger_fy2025.csv
    shipping_documents_dec_jan.csv
    ar_aging_12312025.xlsx
    cash_receipts_jan_feb_2026.csv
    ap_listing_12312025.csv
    jan2026_disbursements.xlsx
    customer_master.csv
    prior_year_monthly_sales_2024.csv
    management_inquiry_notes.txt
  answer_key/answer_key.json   <- planted errors. DO NOT OPEN until the Results block.

Six planted error types (specific invoices, customers, months and amounts are randomized
by --seed, so you know the categories but not the details):
  E1 revenue cutoff, E2 duplicate invoice, E3 unexplained revenue spike,
  E4 allowance for doubtful accounts, E5 unrecorded liability, E6 data-integrity traps.

Usage
  python generate_pbc.py                 # seed 2025
  python generate_pbc.py --seed 7 --out pbc --key answer_key
Best practice: have a friend pick the seed so you do not know it.
"""
import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

FY_START = date(2025, 1, 1)
FY_END = date(2025, 12, 31)
SUB_END = date(2026, 2, 28)  # subsequent-receipts / disbursements window end

CUSTOMERS = [
    ("C1001", "Allegheny Property Management LLC", 30),
    ("C1002", "Bayview Medical Center Inc.", 45),
    ("C1003", "Cardinal Hospitality Group LLC", 30),
    ("C1004", "Cedar Point Facility Services", 30),
    ("C1005", "Clearwater Janitorial Company", 30),
    ("C1006", "Delmar Janitorial Services LLC", 30),
    ("C1007", "Eastgate Office Partners", 30),
    ("C1008", "Evergreen Senior Living Inc.", 45),
    ("C1009", "Fairlawn Public Schools", 45),
    ("C1010", "Forest City Hotels and Resorts", 30),
    ("C1011", "Garfield Industrial Company", 30),
    ("C1012", "Great Lakes Logistics Inc.", 30),
    ("C1013", "Hamilton County Services", 45),
    ("C1014", "Harborview Apartments LLC", 30),
    ("C1015", "Heritage Food Services Inc.", 30),
    ("C1016", "Highland Manufacturing Company", 30),
    ("C1017", "Ironwood Property Services", 30),
    ("C1018", "Kent Valley Hospital", 45),
    ("C1019", "Lakeshore Cleaning Services Inc.", 30),
    ("C1020", "Lorain Distribution Company", 30),
    ("C1021", "Maple Heights Facilities LLC", 30),
    ("C1022", "Medina Auto Group", 30),
    ("C1023", "Midwest Stadium Services Inc.", 30),
    ("C1024", "North Coast Restaurants LLC", 30),
    ("C1025", "Oak Ridge Office Parks", 30),
    ("C1026", "Parma Community College", 45),
    ("C1027", "Pinnacle Building Services Inc.", 30),
    ("C1028", "Portage Cold Storage Company", 30),
    ("C1029", "Riverside Fitness Clubs LLC", 30),
    ("C1030", "Sandusky Marine and Supply", 30),
    ("C1031", "Shaker Square Retail Partners", 30),
    ("C1032", "Stark County Services", 45),
    ("C1033", "Summit Healthcare Group Inc.", 45),
    ("C1034", "Tri-State Warehouse Company", 30),
    ("C1035", "Twinsburg Industrial Park LLC", 30),
    ("C1036", "University Circle Services", 45),
    ("C1037", "Valley View Hotels Inc.", 30),
    ("C1038", "Westlake Commercial Cleaning Company", 30),
    ("C1039", "Willoughby Tech Center", 30),
    ("C1040", "Youngstown Metal Works Inc.", 30),
]
DELMAR = "Delmar Janitorial Services LLC"
KEYSTONE = "Keystone Facilities Group"  # E3: not in customer master

INVENTORY_VENDORS = [
    "Apex Paper Products Inc.", "Buckeye Chemical Supply", "CleanCo Manufacturing",
    "Great Lakes Packaging LLC", "Hilltop Plastics Company", "Keller Dispenser Systems",
    "Lakeside Chemical Company", "Nova Tissue Mills", "Premier Glove Supply",
    "Summit Trash Liner Co.",
]
FREIGHT = "Midstate Freight Lines"
UTILITIES = "Ohio Valley Power and Light"
RENT = "Crossroads Realty Partners"
INSURANCE = "Beacon Benefits Insurance"
IT = "Northpoint IT Services"
STAFFING = "Wellman Staffing Group"
WASTE = "Lakeview Waste Hauling"

SEASONALITY = np.array([0.88, 0.86, 0.97, 1.00, 1.04, 1.06, 1.02, 1.05, 1.07, 1.08, 0.98, 0.99])
DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%d-%b-%y"]


def biz_day(d: date) -> date:
    """Roll weekends back to Friday."""
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def last_biz_day(year: int, month: int) -> date:
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    return biz_day(nxt - timedelta(days=1))


def rand_day_in_month(rng: random.Random, year: int, month: int) -> date:
    """Random business day that stays inside the month."""
    nxt = date(year + (month == 12), month % 12 + 1, 1)
    days = [date(year, month, d) for d in range(1, (nxt - date(year, month, 1)).days + 1)]
    return rng.choice([d for d in days if d.weekday() < 5])


def name_variant(rng: random.Random, name: str) -> str:
    """Messy-but-resolvable variants of a customer name (E6 trap)."""
    choice = rng.randint(0, 5)
    if choice == 0:
        return name.upper()
    if choice == 1:
        return name + "  "
    if choice == 2:
        return name.replace("Services", "Svcs").replace("Company", "Co.")
    if choice == 3:
        return name.replace(" LLC", "").replace(" Inc.", "")
    if choice == 4:
        return name.replace(" and ", " & ")
    return name.lower().title().replace("Llc", "LLC")


def money_str(rng: random.Random, x: float) -> str:
    if rng.random() < 0.35:
        return f"${x:,.2f}"
    return f"{x:.2f}"


def age_bucket(days: int) -> str:
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    if days <= 120:
        return "91-120"
    return "Over 120"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=2025)
    ap.add_argument("--out", default="pbc")
    ap.add_argument("--key", default="answer_key")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    nrng = np.random.default_rng(args.seed)
    out = Path(args.out)
    keydir = Path(args.key)
    out.mkdir(parents=True, exist_ok=True)
    keydir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ revenue targets
    py_total = rng.uniform(36.2e6, 37.4e6)
    py_month = py_total * SEASONALITY / SEASONALITY.sum() * nrng.normal(1, 0.015, 12)
    py_month = np.round(py_month, 2)
    growth = rng.uniform(0.060, 0.070)
    cy_target = py_month * (1 + growth) * nrng.normal(1, 0.008, 12)

    # customer weights (Pareto-ish) and payment behaviour
    weights = nrng.pareto(1.6, len(CUSTOMERS)) + 0.3
    pay_offset = {c[1]: rng.choice([-5, -3, 0, 0, 2, 5, 8, 12]) for c in CUSTOMERS}
    names = [c[1] for c in CUSTOMERS]
    terms = {c[1]: c[2] for c in CUSTOMERS}

    rows = []  # dicts: inv_date, ship_date, customer, amount, memo, pay_date, tag

    def add_inv(inv_date, customer, amount, ship_date=None, memo="", pay_date="auto", tag=""):
        if ship_date is None:
            ship_date = max(inv_date - timedelta(days=rng.choice([0, 0, 0, 1])), FY_START)
        if pay_date == "auto":
            delay = terms.get(customer, 30) + pay_offset.get(customer, 0) + int(nrng.normal(0, 6))
            pay_date = inv_date + timedelta(days=max(5, delay))
        rows.append(dict(inv_date=inv_date, ship_date=ship_date, customer=customer,
                         amount=round(amount, 2), memo=memo, pay_date=pay_date, tag=tag))

    # ---------------------------------------------------------------- E4: Delmar (allowance)
    delmar_target = rng.uniform(110_000, 150_000)
    delmar_total = 0.0
    while delmar_total < delmar_target:
        amt = round(rng.uniform(9_000, 22_000), 2)
        d = rand_day_in_month(rng, 2025, rng.choice([7, 8]))
        if (FY_END - d).days <= 120:
            d = date(2025, 8, 20)
        add_inv(d, DELMAR, amt, pay_date=None, tag="E4")
        delmar_total += amt
    delmar_total = round(sum(r["amount"] for r in rows if r["tag"] == "E4"), 2)

    # decoys: big late-December sales that DID ship in December
    for d in [date(2025, 12, 22), date(2025, 12, 30)]:
        cust = rng.choice([n for n in names if n != DELMAR])
        add_inv(d, cust, round(rng.uniform(40_000, 70_000), 2), ship_date=d, memo="Standing order",
                tag="DECOY")

    # regular sales: net the legitimate special invoices (Delmar, decoys) out of the targets
    for r in rows:
        cy_target[r["inv_date"].month - 1] -= r["amount"]
    for m in range(12):
        month = m + 1
        running = 0.0
        while running < cy_target[m]:
            cust = rng.choices(names, weights=weights)[0]
            if cust == DELMAR and month >= 7:
                continue  # Delmar handled separately (credit hold from September)
            amt = float(np.clip(nrng.lognormal(np.log(8200), 0.75), 450, 95000))
            memo = rng.choice(["", "", "", f"PO {rng.randint(40000, 49999)}", "Standing order"])
            add_inv(rand_day_in_month(rng, 2025, month), cust, amt, memo=memo)
            running += amt

    # decoys: slow payers. Old items that ARE collected in Jan/Feb, plus a few small ones still open
    slow = [n for n in names if n != DELMAR]
    slow_custs = rng.sample(slow, 3)
    reg = [r for r in rows if r["tag"] == "" and r["customer"] in slow_custs
           and date(2025, 8, 25) <= r["inv_date"] <= date(2025, 10, 20)]
    for r in rng.sample(reg, min(10, len(reg))):
        r["pay_date"] = date(2026, rng.choice([1, 2]), rng.randint(5, 25))
    small = [r for r in rows if r["tag"] == "" and r["amount"] < 5000
             and date(2025, 8, 1) <= r["inv_date"] <= date(2025, 9, 30)]
    for r in rng.sample(small, min(4, len(small))):
        r["pay_date"] = date(2026, 3, rng.randint(5, 25))

    # ---------------------------------------------------------------- E3: spike (Keystone)
    spike_month = rng.choice([6, 7, 8, 9, 10])
    spike_amt = round(rng.uniform(550_000, 700_000), -3)
    spike_date = last_biz_day(2025, spike_month)
    add_inv(spike_date, KEYSTONE, spike_amt, ship_date="", memo="Q-end - per J. Marsh",
            pay_date=None, tag="E3")

    # ---------------------------------------------------------------- E2: duplicate
    dup_cust = rng.choice([n for n in names if n != DELMAR])
    dup_amt = round(rng.uniform(38_000, 58_000), 2)
    dup_date = biz_day(date(2025, 11, rng.randint(3, 14)))
    add_inv(dup_date, dup_cust, dup_amt, memo=f"PO {rng.randint(40000, 49999)}",
            pay_date=dup_date + timedelta(days=rng.randint(18, 26)), tag="E2")

    # ---------------------------------------------------------------- E1: cutoff
    cutoff_rows = []
    for d, s in [(date(2025, 12, 29), date(2026, 1, 2)),
                 (date(2025, 12, 30), date(2026, 1, 5)),
                 (date(2025, 12, 31), date(2026, 1, 6))]:
        cust = rng.choice([n for n in names if n not in (DELMAR, dup_cust)])
        amt = round(rng.uniform(45_000, 85_000), 2)
        add_inv(d, cust, amt, ship_date=s, memo="Standing order",
                pay_date=s + timedelta(days=terms[cust] + rng.randint(0, 6)), tag="E1")
        cutoff_rows.append(rows[-1])
    # ---------------------------------------------------------------- invoice numbers
    rows.sort(key=lambda r: (r["inv_date"], r["customer"]))
    for i, r in enumerate(rows, start=1):
        r["inv_no"] = f"INV-25{i:04d}"
    dup_row = next(r for r in rows if r["tag"] == "E2")
    dup_copy = dict(dup_row)
    dup_copy["tag"] = "E2-DUP"
    dup_copy["pay_date"] = None  # client applied the single payment to the first posting
    idx = rows.index(dup_row)
    rows.insert(idx + 1, dup_copy)

    sales = pd.DataFrame(rows)
    revenue_recorded = round(sales["amount"].sum(), 2)

    # ---------------------------------------------------------------- sales ledger (messy)
    ledger_lines = []
    subtotal_sum = 0.0
    for month in range(1, 13):
        mdf = sales[sales["inv_date"].apply(lambda d: d.month) == month]
        for _, r in mdf.iterrows():
            fmt = rng.choice(DATE_FORMATS)
            ship = "" if r["ship_date"] == "" else r["ship_date"].strftime(fmt)
            cust = name_variant(rng, r["customer"]) if rng.random() < 0.18 else r["customer"]
            ledger_lines.append({"Inv #": r["inv_no"], "Inv Date": r["inv_date"].strftime(fmt),
                                 "Ship Dt": ship, "Customer": cust,
                                 "Amount": money_str(rng, r["amount"]), "Memo": r["memo"]})
        mtot = round(mdf["amount"].sum(), 2)
        subtotal_sum += mtot
        ledger_lines.append({"Inv #": "", "Inv Date": "", "Ship Dt": "",
                             "Customer": f"Subtotal - {date(2025, month, 1):%b %Y}",
                             "Amount": f"${mtot:,.2f}", "Memo": ""})
    pd.DataFrame(ledger_lines).to_csv(out / "sales_ledger_fy2025.csv", index=False)
    n_variants = sum(1 for l in ledger_lines if l["Inv #"] and l["Customer"] not in names + [KEYSTONE])

    # ---------------------------------------------------------------- shipping documents for cutoff testing
    # This is a separate source from the sales ledger so the auditor can corroborate
    # the ledger ship date rather than merely agreeing the ledger to itself.
    ship_docs = []
    ship_scope = sales[
        (sales["inv_date"] >= date(2025, 12, 23))
        & sales["ship_date"].apply(lambda x: x != "")
    ].drop_duplicates("inv_no")
    carriers = ["Midstate Freight Lines", "Lake Erie Parcel", "Buckeye Regional Logistics"]
    for _, r in ship_scope.sort_values(["ship_date", "inv_no"]).iterrows():
        ship_docs.append({
            "Shipment ID": f"SHP-{rng.randint(100000, 999999)}",
            "Invoice": r["inv_no"],
            "Actual Ship Date": r["ship_date"].isoformat(),
            "Carrier": rng.choice(carriers),
            "Tracking / BOL": f"BOL-{rng.randint(1000000, 9999999)}",
        })
    pd.DataFrame(ship_docs).to_csv(out / "shipping_documents_dec_jan.csv", index=False)

    # ---------------------------------------------------------------- AR aging (open items)
    open_mask = sales["pay_date"].apply(lambda p: p is None or p > FY_END)
    ar = sales[open_mask].copy()
    ar["days"] = ar["inv_date"].apply(lambda d: (FY_END - d).days)
    ar["bucket"] = ar["days"].apply(age_bucket)
    ar_total = round(ar["amount"].sum(), 2)
    buckets = ["0-30", "31-60", "61-90", "91-120", "Over 120"]
    aging_rows = []
    for _, r in ar.sort_values(["customer", "inv_date"]).iterrows():
        row = {"Customer Name": name_variant(rng, r["customer"]) if rng.random() < 0.12 else r["customer"],
               "Invoice No": r["inv_no"], "Invoice Date": r["inv_date"],
               "Due Date": r["inv_date"] + timedelta(days=terms.get(r["customer"], 30)),
               "Balance": r["amount"]}
        for b in buckets:
            row[b] = r["amount"] if r["bucket"] == b else 0.0
        row["Credit Hold"] = "Y" if r["customer"] == DELMAR else "N"
        aging_rows.append(row)
    aging = pd.DataFrame(aging_rows)
    total_row = {"Customer Name": "GRAND TOTAL", "Invoice No": "", "Invoice Date": None,
                 "Due Date": None, "Balance": ar_total}
    for b in buckets:
        total_row[b] = round(aging[b].sum(), 2)
    total_row["Credit Hold"] = ""
    aging = pd.concat([aging, pd.DataFrame([total_row])], ignore_index=True)
    with pd.ExcelWriter(out / "ar_aging_12312025.xlsx", engine="openpyxl") as xw:
        aging.to_excel(xw, sheet_name="Aging", startrow=4, index=False)
        ws = xw.sheets["Aging"]
        ws["A1"] = "Northfield Supply Co."
        ws["A2"] = "A/R Aging Detail (days from invoice date)"
        ws["A3"] = "As of 12/31/2025 - run 01/09/2026 by K. Doyle"
        for row in ws.iter_rows(min_row=6, min_col=3, max_col=4):
            for c in row:
                c.number_format = "mm/dd/yyyy"

    # ---------------------------------------------------------------- cash receipts Jan-Feb 2026
    rec = sales[sales["pay_date"].apply(lambda p: p is not None and FY_END < p <= SUB_END)]
    receipts = []
    for _, r in rec.iterrows():
        rd = r["pay_date"]
        while rd.weekday() >= 5 or rd == date(2026, 1, 1):
            rd += timedelta(days=1)  # deposits post on business days
        receipts.append({"Date Rec'd": rd.strftime("%m/%d/%y"),
                         "Payer": name_variant(rng, r["customer"]) if rng.random() < 0.25 else r["customer"],
                         "Ref Inv": "see remit" if rng.random() < 0.06 else r["inv_no"],
                         "Amt": f"{r['amount']:,.2f}"})
    for _ in range(rng.randint(90, 130)):  # payments on 2026 invoices (noise)
        d = biz_day(date(2026, 2, rng.randint(1, 28)))
        receipts.append({"Date Rec'd": d.strftime("%m/%d/%y"), "Payer": rng.choice(names[6:]),
                         "Ref Inv": f"INV-26{rng.randint(1, 450):04d}",
                         "Amt": f"{rng.uniform(900, 30000):,.2f}"})
    receipts.sort(key=lambda x: pd.to_datetime(x["Date Rec'd"], format="%m/%d/%y"))
    pd.DataFrame(receipts).to_csv(out / "cash_receipts_jan_feb_2026.csv", index=False)

    # ---------------------------------------------------------------- AP listing 12/31/2025
    ap_rows = []
    ap_target = rng.uniform(1.95e6, 2.2e6)
    running = 0.0
    while running < ap_target:
        v = rng.choice(INVENTORY_VENDORS)
        d = biz_day(date(2025, 12, 1) + timedelta(days=rng.randint(-12, 30)))
        amt = round(float(np.clip(nrng.lognormal(np.log(38000), 0.6), 3000, 180000)), 2)
        ap_rows.append({"Vendor": v, "Invoice": f"{v[:3].upper()}-{rng.randint(10000, 99999)}",
                        "Invoice Date": d, "Due": d + timedelta(days=30), "Open Amount": amt,
                        "desc": "Inventory purchase"})
        running += amt
    services = [
        (FREIGHT, date(2025, 11, 21), rng.uniform(55_000, 70_000), "Freight - November 2025 outbound shipments"),
        (UTILITIES, date(2025, 12, 18), rng.uniform(14_000, 17_000), "Electric/gas - December 2025"),
        (STAFFING, date(2025, 12, 26), rng.uniform(22_000, 30_000), "Temp warehouse labor - weeks ending 12/19, 12/26"),
        (WASTE, date(2025, 12, 31), rng.uniform(2_500, 3_500), "Waste hauling - December 2025"),
    ]
    for v, d, a, desc in services:
        ap_rows.append({"Vendor": v, "Invoice": f"{v[:3].upper()}-{rng.randint(10000, 99999)}",
                        "Invoice Date": d, "Due": d + timedelta(days=30), "Open Amount": round(a, 2),
                        "desc": desc})
    apdf = pd.DataFrame(ap_rows)
    ap_total = round(apdf["Open Amount"].sum(), 2)
    ap_out = apdf.drop(columns="desc").copy()
    ap_out["Invoice Date"] = ap_out["Invoice Date"].apply(lambda d: d.isoformat())
    ap_out["Due"] = ap_out["Due"].apply(lambda d: d.isoformat())
    ap_out.to_csv(out / "ap_listing_12312025.csv", index=False)

    # ---------------------------------------------------------------- January 2026 disbursements
    disb = []
    for _, r in apdf.iterrows():
        if rng.random() < 0.85:
            pay = min(max(r["Invoice Date"] + timedelta(days=30 + rng.randint(-5, 5)), date(2026, 1, 2)),
                      date(2026, 1, 30))
            disb.append((biz_day(pay), r["Vendor"], r["Invoice"], r["Invoice Date"], r["Open Amount"], r["desc"]))
    # E5 planted unrecorded liability
    e5_amt = round(rng.uniform(60_000, 90_000), 2)
    e5_inv = f"MID-{rng.randint(10000, 99999)}"
    e5_date = biz_day(date(2026, 1, rng.randint(15, 23)))
    disb.append((e5_date, FREIGHT, e5_inv, date(2025, 12, 19), e5_amt,
                 "Freight - December 2025 outbound shipments"))
    # bonus trivial unrecorded item
    bonus_amt = round(rng.uniform(3_800, 4_800), 2)
    bonus_inv = f"NIT-{rng.randint(1000, 9999)}"
    disb.append((date(2026, 1, 16), IT, bonus_inv, date(2026, 1, 5), bonus_amt,
                 "Managed IT support - December 2025"))
    # legitimate January items (not 12/31 liabilities)
    jan_items = [
        (date(2026, 1, 2), RENT, "CRP-2026-01", date(2026, 1, 1), 45_000.00, "Warehouse rent - January 2026"),
        (date(2026, 1, 9), INSURANCE, f"BBI-{rng.randint(1000, 9999)}", date(2026, 1, 2),
         round(rng.uniform(11_000, 13_500), 2), "Group health premium - January 2026"),
        (date(2026, 1, 27), IT, f"NIT-{rng.randint(1000, 9999)}", date(2026, 1, 20),
         round(rng.uniform(3_800, 4_800), 2), "Managed IT support - January 2026"),
        (date(2026, 1, 29), STAFFING, f"WEL-{rng.randint(10000, 99999)}", date(2026, 1, 23),
         round(rng.uniform(9_000, 14_000), 2), "Temp warehouse labor - weeks ending 1/9, 1/16"),
    ]
    disb.extend(jan_items)
    for _ in range(rng.randint(6, 10)):  # January inventory buys paid on short terms
        v = rng.choice(INVENTORY_VENDORS)
        d = biz_day(date(2026, 1, rng.randint(2, 16)))
        disb.append((biz_day(d + timedelta(days=10)), v, f"{v[:3].upper()}-{rng.randint(10000, 99999)}", d,
                     round(rng.uniform(8_000, 60_000), 2), "Inventory purchase - January receipt"))
    disb.sort(key=lambda x: x[0])
    disb_df = pd.DataFrame([{
        "Check/ACH": (f"ACH{5000 + i}" if rng.random() < 0.6 else str(21400 + i)),
        "Paid": x[0], "Payee": x[1], "Vendor Inv": x[2], "Inv Dt": x[3],
        "Amount": x[4], "Description": x[5]} for i, x in enumerate(disb)])
    e5_check = disb_df.loc[disb_df["Vendor Inv"] == e5_inv, "Check/ACH"].iloc[0]
    with pd.ExcelWriter(out / "jan2026_disbursements.xlsx", engine="openpyxl") as xw:
        disb_df.to_excel(xw, sheet_name="Disbursements", index=False)
        ws = xw.sheets["Disbursements"]
        for row in ws.iter_rows(min_row=2, min_col=2, max_col=2):
            for c in row:
                c.number_format = "mm/dd/yyyy"
        for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
            for c in row:
                c.number_format = "mm/dd/yyyy"

    # ---------------------------------------------------------------- customer master
    pd.DataFrame([{"Cust ID": c[0], "Customer Name": c[1], "Terms": f"Net {c[2]}",
                   "Credit Limit": rng.choice([50000, 75000, 100000, 150000, 250000])}
                  for c in CUSTOMERS]).to_csv(out / "customer_master.csv", index=False)

    # ---------------------------------------------------------------- prior-year monthly sales
    pd.DataFrame({"Month": [f"{date(2024, m, 1):%b-%Y}" for m in range(1, 13)],
                  "Net Sales": py_month}).to_csv(out / "prior_year_monthly_sales_2024.csv", index=False)

    # ---------------------------------------------------------------- trial balance
    r2 = lambda x: round(float(x), 2)
    rev_ex_spike = revenue_recorded - spike_amt
    cogs = r2(rev_ex_spike * 0.745)
    freight = r2(rev_ex_spike * 0.021)
    opex = {"6100": ("Salaries and wages", r2(rng.uniform(6.0e6, 6.4e6))),
            "6200": ("Rent expense", 540_000.00),
            "6250": ("Utilities", r2(rng.uniform(175_000, 190_000))),
            "6300": ("Depreciation expense", r2(rng.uniform(300_000, 320_000))),
            "6350": ("Bad debt expense", r2(rng.uniform(40_000, 50_000))),
            "6400": ("Insurance", r2(rng.uniform(145_000, 155_000))),
            "6500": ("Office and general", r2(rng.uniform(400_000, 440_000)))}
    interest = r2(rng.uniform(200_000, 220_000))
    pretax = revenue_recorded - cogs - freight - sum(v[1] for v in opex.values()) - interest
    tax = r2(pretax * 0.25)
    allowance = round(ar_total * 0.01, -2)

    # prior year (audited) balances, signed (debit +)
    py_rev = r2(py_month.sum())
    py = {"1000": 1_600_000.00, "1100": r2(py_rev * rng.uniform(0.115, 0.125)), "1150": -40_000.00,
          "1200": r2(rng.uniform(4.8e6, 5.0e6)), "1300": 150_000.00, "1500": 2_800_000.00,
          "1550": -1_100_000.00, "2000": -r2(rng.uniform(1.9e6, 2.0e6)), "2100": -390_000.00,
          "2150": -90_000.00, "2200": -3_900_000.00, "3000": -500_000.00,
          "4000": -py_rev, "5000": r2(py_rev * 0.748), "5100": r2(py_rev * 0.021),
          "6100": r2(opex["6100"][1] * 0.95), "6200": 510_000.00, "6250": r2(opex["6250"][1] * 0.97),
          "6300": 280_000.00, "6350": 38_000.00, "6400": r2(opex["6400"][1] * 0.96),
          "6500": r2(opex["6500"][1] * 0.97), "7000": 245_000.00}
    py_pretax = -(py["4000"] + py["5000"] + py["5100"] + sum(py[k] for k in opex) + py["7000"])
    py["8000"] = r2(py_pretax * 0.25)
    py["3100"] = -r2(sum(py.values()))  # PY beginning RE plug so PY balances
    py_ni = py_pretax - py["8000"]
    re_beg_cy = r2(-py["3100"] + py_ni)  # CY beginning RE = PY beginning RE + PY NI (credit)

    cy = {"1000": r2(rng.uniform(1.8e6, 2.0e6)), "1100": ar_total, "1150": -allowance,
          "1200": r2(rng.uniform(5.1e6, 5.3e6)), "1300": 160_000.00, "1500": 3_100_000.00,
          "1550": -1_400_000.00, "2000": -ap_total, "2100": -420_000.00, "2150": -100_000.00,
          "3000": -500_000.00, "3100": -re_beg_cy, "4000": -revenue_recorded, "5000": cogs,
          "5100": freight, "7000": interest, "8000": tax}
    for k, (_, v) in opex.items():
        cy[k] = v
    cy["2200"] = -r2(sum(cy.values()))  # line of credit plug so CY balances
    if -cy["2200"] <= 0:
        raise SystemExit("Line of credit plug went non-positive; try another seed.")

    acct_names = {"1000": "Cash - operating", "1100": "Accounts receivable - trade",
                  "1150": "Allowance for doubtful accounts", "1200": "Inventory",
                  "1300": "Prepaid expenses", "1500": "Property and equipment",
                  "1550": "Accumulated depreciation", "2000": "Accounts payable - trade",
                  "2100": "Accrued liabilities", "2150": "Income taxes payable",
                  "2200": "Line of credit", "3000": "Common stock", "3100": "Retained earnings",
                  "4000": "Sales, net", "5000": "Cost of goods sold", "5100": "Freight-out",
                  "6100": opex["6100"][0], "6200": opex["6200"][0], "6250": opex["6250"][0],
                  "6300": opex["6300"][0], "6350": opex["6350"][0], "6400": opex["6400"][0],
                  "6500": opex["6500"][0], "7000": "Interest expense", "8000": "Income tax expense"}
    tb_rows = []
    for k in sorted(acct_names):
        v = cy[k]
        tb_rows.append({"Acct": k, "Account Description": acct_names[k],
                        "Debit": r2(v) if v > 0 else None, "Credit": r2(-v) if v < 0 else None,
                        "PY Balance (audited)": py[k]})
    tb = pd.DataFrame(tb_rows)
    with pd.ExcelWriter(out / "trial_balance_12312025.xlsx", engine="openpyxl") as xw:
        tb.to_excel(xw, sheet_name="TB", startrow=3, index=False)
        ws = xw.sheets["TB"]
        ws["A1"] = "Northfield Supply Co. - Trial Balance (pre-closing, unaudited)"
        ws["A2"] = "Period ending 12/31/2025. PY column is signed: debit (+) / credit (-)"
        n = len(tb) + 5
        ws[f"B{n}"] = "Totals"
        ws[f"C{n}"] = round(tb["Debit"].sum(), 2)
        ws[f"D{n}"] = round(tb["Credit"].sum(), 2)

    # ---------------------------------------------------------------- management inquiry notes
    (out / "management_inquiry_notes.txt").write_text(f"""Northfield Supply Co. - FY2025 audit
Notes from planning inquiry with J. Marsh (CFO) and K. Doyle (Controller), 01/12/2026

- Sales volume grew roughly 6-7% over 2024, mostly from new school district and
  healthcare contracts. A 3% list price increase took effect March 1, 2025 but most
  contract customers were price-protected, so the net effect was small.
- "No unusual or one-time transactions this year." Revenue is recognized when goods ship
  (FOB shipping point).
- "All December orders were shipped and delivered before year-end."
- Allowance for doubtful accounts is set at 1% of gross A/R, consistent with prior year.
  "Collections are in good shape. We have a couple of slow payers but nothing we are
  worried about."
- A/P is recorded when the vendor invoice is received and approved. The controller
  says the December close was "rushed because of the holidays."
- Freight carrier: Midstate Freight Lines bills monthly in arrears.
- No changes in accounting systems. Customer master is maintained by the credit manager;
  new customers require credit approval before first shipment.
""")

    # ---------------------------------------------------------------- answer key
    cutoff_total = round(sum(r["amount"] for r in cutoff_rows), 2)
    key = {
        "seed": args.seed,
        "company": "Northfield Supply Co. (fictional)",
        "recorded_totals": {"revenue": revenue_recorded, "ar_gross": ar_total,
                            "allowance": allowance, "ap": ap_total},
        "errors": [
            {"id": "E1", "type": "Revenue cutoff",
             "description": "Invoices dated 12/29-12/31/2025 that shipped in January 2026 "
                            "(FOB shipping point). Revenue and A/R overstated; COGS understated and "
                            "inventory understated by ~74.5% of the amount. Management said all "
                            "December orders shipped before year-end. The customers paid in "
                            "Jan/Feb, so subsequent receipts alone do NOT catch this.",
             "amount": cutoff_total, "direction": "Revenue and A/R overstated",
             "match_refs": [r["inv_no"] for r in cutoff_rows],
             "where": "Sales ledger Ship Dt column; WP1 cutoff test", "standard": "AU-C 330 / AU-C 500"},
            {"id": "E2", "type": "Duplicate invoice",
             "description": f"{dup_row['inv_no']} posted twice in the sales ledger. The payment "
                            "was applied to the first posting, so the duplicate sits open in the "
                            "aging with no subsequent receipt.",
             "amount": dup_amt, "direction": "Revenue and A/R overstated",
             "match_refs": [dup_row["inv_no"]],
             "where": "Sales ledger duplicate test; WP2 subsequent receipts", "standard": "AU-C 500"},
            {"id": "E3", "type": "Unexplained revenue spike / possible fictitious sale",
             "description": f"{date(2025, spike_month, 1):%B} revenue spike from one invoice to "
                           f"{KEYSTONE}: no ship date, memo 'Q-end - per J. Marsh', customer not in "
                           "customer master, never paid. Management said there were no unusual "
                           "transactions. Treat as a fraud-risk indicator (presumed revenue risk).",
             "amount": spike_amt, "direction": "Revenue and A/R overstated",
             "match_refs": [r["inv_no"] for r in rows if r["tag"] == "E3"] + [KEYSTONE.upper()],
             "where": "WP1 monthly analytics; customer master match; WP2 aging",
             "standard": "AU-C 520 / AU-C 240"},
            {"id": "E4", "type": "Allowance for doubtful accounts understated",
             "description": f"{DELMAR} balance of ${delmar_total:,.2f} is entirely over 120 days, on "
                            "credit hold, and has no subsequent receipts. The flat 1% allowance does "
                            "not cover it. Understatement is approximately the Delmar balance less "
                            "the 1% general reserve already attributable to it.",
             "amount": round(delmar_total * 0.99, 2), "direction": "Allowance and bad debt expense understated",
             "match_refs": ["DELMAR"], "where": "WP2 aging / allowance analysis",
             "standard": "AU-C 540 (accounting estimates)"},
            {"id": "E5", "type": "Unrecorded liability",
             "description": f"{FREIGHT} invoice {e5_inv} dated 12/19/2025 for December 2025 freight, "
                            f"paid {e5_date:%m/%d/%Y} ({e5_check}), not on the 12/31 A/P listing. "
                            "The November Midstate invoice IS on the listing (decoy).",
             "amount": e5_amt, "direction": "A/P and freight-out expense understated",
             "match_refs": [e5_inv, str(e5_check)], "where": "WP3 search for unrecorded liabilities",
             "standard": "AU-C 330 / AU-C 560"},
            {"id": "E6", "type": "Data-integrity traps",
             "description": f"Sales ledger contains 12 monthly subtotal rows totaling "
                            f"${subtotal_sum:,.2f} (a naive SUM doubles revenue); {n_variants} ledger "
                            "rows use customer-name variants; mixed date formats and '$' amounts; "
                            f"{KEYSTONE} does not exist in the customer master; aging report has a "
                            "header block and a GRAND TOTAL row.",
             "amount": 0, "direction": "No misstatement by itself; causes wrong analysis if missed",
             "match_refs": [],
             "match_keywords": ["subtotal", "name variant", "customer master", "date format", "grand total"],
             "min_keyword_hits": 2,
             "where": "Normalization step", "standard": "AU-C 500 (reliability of information)"},
        ],
        "bonus_not_scored": [
            {"id": "B1", "type": "Trivial unrecorded liability",
             "description": f"{IT} invoice {bonus_inv} dated 01/05/2026 for December 2025 IT support "
                            f"(${bonus_amt:,.2f}). Below the clearly-trivial threshold; noting it shows care.",
             "amount": bonus_amt, "match_refs": [bonus_inv]},
        ],
        "decoys": ["Slow-paying customers with 61-120 day items that were collected in Jan/Feb 2026.",
                   "A few small (<$5,000) Aug-Sep items still open with no receipts (below trivial).",
                   "Two large late-December invoices that shipped in December (not cutoff errors).",
                   "Midstate November invoice on the A/P listing, paid in January (properly accrued).",
                   "January rent, insurance, staffing and IT invoices for January services."],
    }
    (keydir / "answer_key.json").write_text(json.dumps(key, indent=2, default=str))

    print(f"Wrote client files to {out}/ and the answer key to {keydir}/ (don't peek).")
    print(f"Recorded revenue ${revenue_recorded:,.2f} | A/R ${ar_total:,.2f} | A/P ${ap_total:,.2f}")
    print(f"TB check: debits ${tb['Debit'].sum():,.2f} vs credits ${tb['Credit'].sum():,.2f}")


if __name__ == "__main__":
    main()
