# Northfield Supply Co. — AI-Assisted Mini-Audit (FY2025)

This project demonstrates an end-to-end, AI-assisted audit workflow for a fictional wholesale distributor. It starts with intentionally messy client files, normalizes and reconciles the data, builds formula-driven Excel workpapers, performs planning and substantive procedures, records audit findings, completes a skeptical reviewer cycle, and benchmarks the results against a sealed answer key.

Northfield Supply Co. and all underlying information are fictional and synthetic. This is a portfolio exercise, not an audit or assurance engagement.

## Results at a glance

| Metric | Result |
|---|---:|
| Official detection score | 5.00 / 6 (83%) |
| Manually verified category coverage | 6 / 6 |
| Bonus item | Found |
| False positives / unmatched findings | 0 |
| Gross identified misstatements | $1,095,267.87 |
| Overall materiality | $239,000 |
| Performance materiality | $167,000 |
| Logged time through results analysis | 215 minutes |
| Reviewer notes | 4 raised, 4 cleared |

The official score remains 83%. The data-integrity category was documented in finding F-01 before the answer key was opened, but the scoring script first assigned F-01 to the revenue-spike category because both findings mentioned the unmatched Keystone customer. The script then prevented F-01 from matching data integrity. The collision and manual adjudication are documented in `results.md`; the finalized Findings sheet was not changed after scoring.

## Key findings

| Finding | Audit area | Amount | Result |
|---|---|---:|---|
| F-01 | Data integrity | $0.00 | Subtotals, name variants, mixed formats, report headers/totals, and an unmatched customer were identified and addressed during normalization. |
| F-02 | Revenue occurrence / fraud risk | $642,000.00 | Unsupported quarter-end revenue for an unapproved customer; escalated as a possible management-override or fraud indicator. |
| F-03 | Revenue cutoff | $158,067.83 | Three December invoices shipped in January 2026 and belonged in FY2026. |
| F-04 | Duplicate revenue | $56,820.17 | One invoice was posted twice. |
| F-05 | A/R valuation | $145,957.67 | The recorded allowance did not adequately reserve a fully aged, credit-hold customer balance. |
| F-06 | Liability completeness | $92,422.20 | December freight and IT services were paid in January but omitted from the year-end liability listing. |

## Workflow

```text
generate_pbc.py
      ↓
messy synthetic client files in pbc/
      ↓
normalize.py → clean/ + normalization_log.md
      ↓
build_workbook.py → Northfield_FY2025_Workpapers.xlsx
      ↓
planning → lead sheet → WP1 revenue → WP2 A/R → WP3 liabilities
      ↓
Findings → reviewer notes → cleared workpapers
      ↓
score_results.py → results.md → product_memo.md
```

The workbook uses live formulas for mechanical calculations and yellow cells for documented auditor inputs and conclusions. It should be opened in desktop Excel, allowed to recalculate, and saved before running the scorer.

## Audit approach

The project focuses on four risks:

1. Improper revenue recognition, including presumed fraud risk.
2. Accounts-receivable valuation under a flat 1% allowance policy.
3. Completeness of accounts payable and accrued liabilities after a rushed year-end close.
4. Reliability of client-prepared information and normalized data.

The substantive work includes monthly revenue analytics, full-population duplicate testing, shipping-document cutoff testing, A/R aging and subsequent-receipt procedures, allowance recalculation, and a search for unrecorded liabilities using January disbursements.

## Reviewer cycle

An independent 22-point checklist raised four medium-severity notes:

- Reviewer sign-offs were incomplete.
- The revenue-growth expectation overstated the strength of its corroboration.
- Revenue completeness cutoff needed an alternative procedure.
- WP3 did not identify the evidence supporting inventory-period conclusions.

All four notes were addressed and cleared. The final workpapers describe the remaining evidence limitations rather than claiming more assurance than the available documents support.

## What AI did and what remained a human responsibility

AI assisted with data normalization, population analysis, formula-driven workpaper preparation, anomaly identification, audit-documentation drafting, reviewer checks, and failure analysis. The project also used AI to help create the scripts before the timed session.

Human responsibility remained essential. The user directed the workflow, controlled when the sealed answer key could be opened, opened and recalculated the workbook in Excel, evaluated whether evidence was sufficient, required review notes to be resolved, and retained responsibility for the final conclusions and limitations.

The main AI and tool failures are recorded in the `AI_Log` sheet. They include overstating analytical corroboration, overlooking an alternative completeness procedure, inferring receipt evidence too confidently, and ambiguous matching in the scoring script.

## Repository contents

| Path | Purpose |
|---|---|
| `PDD.md` | Project design, audit approach, and timed runbook |
| `PROJECT_GUIDE.md` | Private, plain-language explanation of the complete project |
| `Northfield_FY2025_Workpapers.xlsx` | Final reviewed Excel workpapers |
| `pbc/` | Messy synthetic client-provided files |
| `clean/` | Normalized audit populations and normalization log |
| `generate_pbc.py` | Generates the synthetic PBC files and sealed answer key |
| `normalize.py` | Standardizes the client data and writes the normalization log |
| `build_workbook.py` | Builds the formula-driven workbook template |
| `score_results.py` | Compares finalized Findings with the answer key |
| `results.md` | Official score, answer-key comparison, and manual adjudication |
| `reviewer_report.md` | 22-point manager review and note-clearance summary |
| `product_memo.md` | Product recommendations based on observed workflow failures |
| `planning_memo.md` | Planning, risk, and materiality summary |
| `wp1_revenue_analysis.md` | Revenue analysis and conclusions |
| `wp2_ar_analysis.md` | A/R existence and allowance analysis |
| `wp3_surl_analysis.md` | Search for unrecorded liabilities |
| `prompts/review_agent_prompt.md` | Reviewer-agent instructions and checklist |
| `answer_key/` | Benchmark data; kept sealed until the Results block |

## Reproducing the workflow

Create an isolated environment and install the requirements:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the pipeline with a chosen seed:

```bash
.venv/bin/python generate_pbc.py --seed 641907
.venv/bin/python normalize.py
.venv/bin/python build_workbook.py
```

Then:

1. Open `Northfield_FY2025_Workpapers.xlsx` in desktop Excel.
2. Allow formulas to calculate and save the workbook.
3. Complete the audit procedures described in `PDD.md`.
4. Run the reviewer checklist and clear every review note.
5. Open the answer key only after Findings are final.
6. Run the scorer:

```bash
.venv/bin/python score_results.py \
  --wb Northfield_FY2025_Workpapers.xlsx \
  --key answer_key/answer_key.json
```

Regenerating the PBC files can replace the current synthetic dataset. Work in a copy if the completed seed-641907 results must be preserved.

## Limitations

- The company and evidence are synthetic.
- The work covers selected audit areas, not a complete financial-statement audit.
- No audit opinion is expressed.
- Cash, inventory, PP&E, debt, equity, payroll, and other areas are outside scope.
- No external confirmations were sent.
- A January sales register and inventory receiving reports were not supplied; the workpapers identify the alternative procedures and remaining limitations.
- The benchmark includes a known finding-matching collision described in `results.md`.

## Current status

The workbook, reviewer cycle, results analysis, README, private project guide, and product memo are complete. The Loom walkthrough is intentionally deferred.

