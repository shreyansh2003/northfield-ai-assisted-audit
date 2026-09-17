# Results vs answer key

Seed 641907. Findings logged: 6.

| Error | Type | Planted amount | Found? | Credit | Your amount | Caught by |
|---|---|---:|---|---:|---:|---|
| E1 | Revenue cutoff | 158,067.83 | Yes | 1.00 | 158,067.83 | AI-assisted |
| E2 | Duplicate invoice | 56,820.17 | Yes | 1.00 | 56,820.17 | AI-assisted |
| E3 | Unexplained revenue spike / possible fictitious sale | 642,000.00 | Yes | 1.00 | 642,000.00 | AI-assisted |
| E4 | Allowance for doubtful accounts understated | 152,968.91 | Yes | 1.00 | 145,957.67 | AI-assisted |
| E5 | Unrecorded liability | 88,519.11 | Yes | 1.00 | 92,422.20 | AI-assisted |
| E6 | Data-integrity traps | 0.00 | **Missed** | 0.00 | - | - |

**Detection score: 5.00/6 (83%)**

Caught by: AI-assisted 5.00
Bonus (not scored): B1

## Findings that match no planted error
These are either false positives or legitimate extra observations. Review each one.

- none

## Answer key detail

- **E1 Revenue cutoff**: Invoices dated 12/29-12/31/2025 that shipped in January 2026 (FOB shipping point). Revenue and A/R overstated; COGS understated and inventory understated by ~74.5% of the amount. Management said all December orders shipped before year-end. The customers paid in Jan/Feb, so subsequent receipts alone do NOT catch this.
- **E2 Duplicate invoice**: INV-253100 posted twice in the sales ledger. The payment was applied to the first posting, so the duplicate sits open in the aging with no subsequent receipt.
- **E3 Unexplained revenue spike / possible fictitious sale**: September revenue spike from one invoice to Keystone Facilities Group: no ship date, memo 'Q-end - per J. Marsh', customer not in customer master, never paid. Management said there were no unusual transactions. Treat as a fraud-risk indicator (presumed revenue risk).
- **E4 Allowance for doubtful accounts understated**: Delmar Janitorial Services LLC balance of $154,514.05 is entirely over 120 days, on credit hold, and has no subsequent receipts. The flat 1% allowance does not cover it. Understatement is approximately the Delmar balance less the 1% general reserve already attributable to it.
- **E5 Unrecorded liability**: Midstate Freight Lines invoice MID-55837 dated 12/19/2025 for December 2025 freight, paid 01/16/2026 (ACH5033), not on the 12/31 A/P listing. The November Midstate invoice IS on the listing (decoy).
- **E6 Data-integrity traps**: Sales ledger contains 12 monthly subtotal rows totaling $39,862,443.61 (a naive SUM doubles revenue); 325 ledger rows use customer-name variants; mixed date formats and '$' amounts; Keystone Facilities Group does not exist in the customer master; aging report has a header block and a GRAND TOTAL row.

Decoys: Slow-paying customers with 61-120 day items that were collected in Jan/Feb 2026. A few small (<$5,000) Aug-Sep items still open with no receipts (below trivial). Two large late-December invoices that shipped in December (not cutoff errors). Midstate November invoice on the A/P listing, paid in January (properly accrued). January rent, insurance, staffing and IT invoices for January services.

## Manual adjudication and failure analysis

The official script score is **5.00/6 (83%)** and is preserved above. A manual trace shows that E6 was documented in F-01 before the answer key was opened. F-01 records the 12 subtotal rows, customer-name variants, mixed date and amount formats, the A/R header and grand-total rows, and the unmatched Keystone customer.

The apparent miss is caused by the scorer's one-use matching order. E3 matches both F-01 and F-02 because F-01 mentions Keystone. The scorer assigns both findings to E3 and marks them used. When E6 is evaluated later, F-01 is no longer available even though it satisfies the E6 keyword rule. Manual category coverage is therefore 6/6, but the reported benchmark remains the unmodified official 5/6.

### Amount differences

- **E4 allowance:** The planted benchmark is $152,968.91, calculated as Delmar's $154,514.05 balance less the 1% reserve already attributable to Delmar. The workpaper adjustment is $145,957.67 because it recalculates the complete allowance after the separate revenue and A/R corrections, applies 1% to the remaining adjusted A/R population, and nets the full $47,400 recorded allowance. The detection received full credit; the $7,011.24 difference is a reserve-basis difference.
- **E5 liability:** The $92,422.20 workpaper finding includes the scored Midstate freight item of $88,519.11 and the separately recognized $3,903.09 Northpoint bonus item. The scorer correctly grants E5 credit and recognizes bonus B1, but its “Your amount” column displays the combined finding amount.

### Miss-prevention conclusion

No planted category was absent from the workpapers. The main process improvement is to require one-to-one finding assignment in the scoring tool, or to score each error against the best single finding without consuming unrelated matches.
