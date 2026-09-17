# Normalization log


## Trial balance
- 25 accounts. CY nets to 0.00; PY nets to 0.00 (both should be 0.00).

## Sales ledger
- Raw file: 3593 rows. Removed 12 subtotal rows totaling 39,862,443.61.
  - Naive SUM of the raw Amount column = 79,724,887.22 (subtotals double-count revenue).
- Parsed mixed date formats (m/d/Y: 1219, ISO: 1179, other: 1183). Unparseable invoice dates: 0.
  - **FLAG** 1 invoice(s) have no ship date: INV-252650.
- Sales ledger: 209 rows used a name variant and were mapped to the customer master.
  - **FLAG** Sales ledger: 'Keystone Facilities Group' is NOT in the customer master (1 rows). Kept under its original name. Investigate.
- Clean ledger total 39,862,443.61 vs TB 4000 39,862,443.61: difference 0.00.
- NOTE: duplicate-invoice testing is intentionally left to WP1 (not done here).

## Shipping documents
- 83 documents supplied for the late-December cutoff window.
- All selected cutoff invoices have one shipping document and the dates agree to the ledger.

## A/R aging
- Skipped 4 report-header rows and 1 GRAND TOTAL row.
- A/R aging: 13 rows used a name variant and were mapped to the customer master.
  - **FLAG** A/R aging: 'Keystone Facilities Group' is NOT in the customer master (1 rows). Kept under its original name. Investigate.
- Detail total 4,737,696.16 | report GRAND TOTAL 4,737,696.16 | buckets cross-foot 4,737,696.16 | TB 1100 4,737,696.16.
- Aging invoices not found in the sales ledger: 0.
- Cash receipts: 23 rows used a name variant and were mapped to the customer master.

## Cash receipts (Jan-Feb 2026)
- 457 receipts totaling 5,805,902.37. 17 have no invoice reference ('see remit'); match these by customer and amount.

## A/P listing
- 50 open invoices totaling 2,263,256.84 vs TB 2000 2,263,256.84: difference 0.00.

## January 2026 disbursements
- 58 payments totaling 2,431,818.64.

## Prior-year monthly sales
- 12 months totaling 36,694,843.82 vs PY TB 4000 36,694,843.82.
