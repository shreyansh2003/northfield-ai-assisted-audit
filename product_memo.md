# Product memo: audit workflow improvements

Northfield Supply Co. — FY2025 AI-assisted mini-audit  
Prepared September 16, 2026

## Summary

The project moved a synthetic client package from inconsistent source files to reviewed workpapers in under four logged hours. The largest quality risks arose when evidence strength was unclear, a preferred source was missing, or an automated scorer matched one finding to more than one error. The following changes would reduce review time and make the audit trail easier to defend.

| Priority | Problem observed | Frequency and cost | Proposed change |
|---:|---|---|---|
| 1 | The result scorer assigned the data-integrity finding to the revenue-spike error because both mentioned Keystone. It then marked data integrity as missed. | One scoring collision changed the official score from apparent 6/6 category coverage to 5/6 and required about 10 minutes to trace. | Use best-match, one-to-one assignment. Show every candidate match before final scoring and let the reviewer approve ambiguous mappings without editing finalized findings. |
| 2 | The revenue-growth expectation was initially described as corroborated by internal financial relationships and the adjusted audit result. That was not independent or sufficiently precise. | One high-risk analytic required a reviewer note and approximately 15 minutes of rework. Similar issues can occur whenever management explanations are compared with internally generated outcomes. | Tag each expectation input by evidence type: management representation, client-generated data, external evidence, or audit result. Warn when the expectation depends on the population being tested or on downstream audit adjustments. |
| 3 | The missing January sales register initially stopped completeness testing even though a complete shipping-document population was available. | One assertion remained unresolved until reviewer follow-up, costing approximately 15 minutes. | When a requested source is unavailable, suggest alternative procedures by assertion. For cutoff completeness, surface source-to-ledger options such as shipping logs, dispatch records, or sequential documents. |
| 4 | The liability workpaper initially stated that generic inventory was received by year-end without naming receiving evidence. | The issue affected dozens of rows and added approximately 20 minutes of documentation work. | Require every period conclusion to cite its evidence type and source row. Add a visible “primary document unavailable” status when a conclusion relies on invoice date, A/P status, or a description instead of a receiving report. |
| 5 | Normalization removed subtotals, header rows, total rows, name variants, and mixed formats, but the resulting integrity finding was not naturally linked to every downstream use. | The issue affected all major populations. Manual documentation and reviewer tracing took approximately 20 minutes. | Create source-to-clean lineage for every normalized row and an automatic AU-C 500 summary showing removed subtotals, excluded report totals, standardized fields, unmatched master-data records, and tie-outs to control totals. |

## Recommended first release

Prioritize evidence-type tagging and alternative-procedure suggestions in the workpaper workflow, then add one-to-one result matching. These changes directly address the three issues that generated reviewer notes or distorted the benchmark score. Source-lineage enhancements should follow because they improve every workpaper built from client-prepared data.

