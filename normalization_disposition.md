# Normalization review and flag disposition

**Client:** Northfield Supply Co. (fictional)  
**Period:** Year ended December 31, 2025  
**Prepared by:** Shreyansh Agrawal  
**Date:** September 16, 2026

## Reconciliations

- Trial balance debits and credits net to zero for both years.
- The clean sales ledger totals $39,862,443.61 and agrees to trial-balance account 4000 with no difference.
- The A/R detail, aging buckets, report total, and trial-balance account 1100 agree at $4,737,696.16.
- The A/P listing agrees to trial-balance account 2000 at $2,263,256.84.
- Prior-year monthly sales agree to prior-year trial-balance account 4000 at $36,694,843.82.

## Flag disposition

1. **Monthly sales subtotal rows.** Twelve subtotal rows totaling $39,862,443.61 were removed. A naive sum of the raw amount column would have doubled revenue to $79,724,887.22. The clean population was re-summed and tied to the trial balance. Disposition: normalization issue resolved; documented as a data-reliability finding and considered in WP1.
2. **Mixed formats and customer-name variants.** All invoice dates parsed successfully. The process standardized currency strings and mapped 209 sales-ledger rows, 13 aging rows, and 23 receipt rows to the customer master. Five raw-to-clean sales rows were traced with no exceptions, including two customer-name variants. Disposition: resolved for analysis, with the mapping retained in the normalization log.
3. **Missing shipping date, invoice INV-252650.** The item remains in the clean population with a blank shipping date. Disposition: unresolved substantive exception; investigate in WP1 and consider the related A/R evidence in WP2.
4. **Keystone Facilities Group is absent from the customer master.** One sales-ledger row and one aging row remain coded as unmatched. Management stated that new customers require credit approval before shipment. Disposition: unresolved control and possible revenue-recognition exception; investigate in WP1 and WP2 and escalate if the evidence suggests management override or a fictitious sale.
5. **Shipping-document population.** Eighty-three documents were supplied for the late-December cutoff window. Every selected cutoff invoice has one document, and the document dates agree to the sales-ledger dates. Disposition: population ready for WP1 cutoff testing; the correct-period conclusion remains an audit judgment.
6. **Receipts without invoice references.** Seventeen subsequent receipts state “see remit.” Disposition: perform manual customer-and-amount matching for any sampled A/R item affected in WP2; do not treat a missing invoice reference as evidence of nonpayment.

## Five-row raw-to-clean spot check

| Invoice | Raw invoice date | Clean date | Raw amount | Clean amount | Customer normalization | Result |
|---|---|---|---:|---:|---|---|
| INV-250001 | 2025-01-01 | 2025-01-01 | $8,468.39 | $8,468.39 | No change | Pass |
| INV-251802 | 2025-07-09 | 2025-07-09 | $7,288.28 | $7,288.28 | No change | Pass |
| INV-253580 | 12/31/2025 | 2025-12-31 | $6,201.55 | $6,201.55 | No change | Pass |
| INV-250016 | 2025-01-02 | 2025-01-02 | $8,716.22 | $8,716.22 | Uppercase variant mapped to master name | Pass |
| INV-253556 | 2025-12-30 | 2025-12-30 | $1,317.30 | $1,317.30 | Uppercase variant mapped to master name | Pass |

**Conclusion:** The normalized populations reconcile to the trial balance and are suitable for the planned procedures, subject to specific follow-up of INV-252650, Keystone Facilities Group, and receipt records without invoice references.
