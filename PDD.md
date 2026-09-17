# Project Design Document
## AI-Assisted Mini-Audit: Northfield Supply Co. (FY2025)

**Author:** [Your name] · **Target role:** AI-Native Auditor, Modus Audit · **Version:** 1.0 · **Session length:** 8 hours

---

## 1. Purpose

This project shows, in one working day, the three things the AI-Native Auditor role asks for:

| What the role asks for | How this project shows it |
|---|---|
| Complete audit workpapers end-to-end with an AI platform | Planning memo, lead sheet and three substantive workpapers, finished in 8 hours |
| Own the quality of what you ship, through reviewer sign-off | Planted-error benchmark with a detection rate, plus a reviewer-agent cycle with responses to every note |
| Be a heavy user whose feedback shapes the product | AI failure log and a short product memo with specific tool suggestions |

The hiring thesis in one line: *"I can take messy client data to a reviewed set of workpapers in a day, I can tell you exactly where the AI helped and where it failed, and I can prove my quality with a number."*

### 1.1 Why this design

The role is for an auditor, not an engineer, so the output is audit documentation, not an app. Modus's platform normalizes client files, generates source-linked workpapers, and runs review assistants trained on partner standards. This project mirrors those three workflows at small scale, which gives you a natural way to talk about their product in an interview.

### 1.2 Non-goals

- No web app, dashboard or user interface.
- No real client data of any kind. Everything is synthetic.
- No attempt to replicate Modus's actual product.
- Not a complete audit. Cash, inventory, PP&E, debt, equity and payroll are out of scope. Their lead sheet lines carry placeholder WP references (C through J).

---

## 2. The fictional client

| Item | Detail |
|---|---|
| Name | Northfield Supply Co. (fictional) |
| Business | Wholesale distributor of janitorial and facility supplies, Cleveland, OH |
| Customers | ~40 commercial accounts (property managers, hospitals, schools, hotels), Net 30/45 terms |
| Year end | December 31, 2025 |
| Revenue | ~$40M; ~3,600 invoices |
| Framework | US GAAP; audit under AICPA AU-C standards (private company) |
| Revenue recognition | When goods ship (FOB shipping point) |
| Key people | J. Marsh (CFO), K. Doyle (Controller) |
| Allowance policy | Flat 1% of gross A/R |

Management's planning inquiry notes (`pbc/management_inquiry_notes.txt`) contain several claims. Some are true and some are not. Treat them as representations to corroborate, not evidence.

---

## 3. What you are given (pre-built components)

These were built before the session so the 8 hours go to audit work. Say this openly in your README: it is an honest, AI-native way to work.

| File | What it does | When you use it |
|---|---|---|
| `generate_pbc.py` | Creates 10 messy client files and a hidden answer key. Error details are randomized by seed. | Block 1 |
| `normalize.py` | Standardizes headers, dates, amounts and customer names; removes subtotal rows; ties files to the TB; writes a log with flags. It makes no audit judgments. | Block 1 |
| `build_workbook.py` | Builds `Northfield_FY2025_Workpapers.xlsx`: planning, lead sheet, WP1-WP3, findings, review notes, AI log, time log, and data tabs. Mechanical steps are live formulas; judgments are yellow input cells. | Block 1 |
| `score_results.py` | Compares your Findings sheet to the answer key and writes `results.md`. | Block 8 only |
| `prompts/review_agent_prompt.md` | A 22-point partner-style review checklist prompt. | Block 7 |

### 3.1 Data flow

```
generate_pbc.py ──► pbc/ (messy client files)          answer_key/ (sealed)
                        │                                     │
                   normalize.py ──► clean/ + normalization_log.md
                        │                                     │
                 build_workbook.py ──► Workpapers.xlsx        │
                        │                                     │
         you + AI: planning, WP1, WP2, WP3, Findings          │
                        │                                     │
         reviewer agent ──► Review_Notes ──► your responses   │
                        │                                     │
                 score_results.py ◄───────────────────────────┘
                        │
                  results.md ──► README + Loom
```

### 3.2 The client files

| File | Contents | Built-in messiness |
|---|---|---|
| `trial_balance_12312025.xlsx` | 25 accounts, CY debit/credit, PY signed balance | Title rows above the header, a totals row |
| `sales_ledger_fy2025.csv` | Every FY2025 invoice with ship date | Monthly subtotal rows, three date formats, `$` amounts, customer-name variants |
| `shipping_documents_dec_jan.csv` | Shipping documents for the late-December cutoff window | Separate corroborating evidence for the recorded ledger ship date |
| `ar_aging_12312025.xlsx` | Open invoices by age bucket, credit-hold flag | Report header block, GRAND TOTAL row, name variants |
| `cash_receipts_jan_feb_2026.csv` | Subsequent receipts | Some receipts say "see remit" instead of an invoice number; includes payments on 2026 invoices |
| `ap_listing_12312025.csv` | Open A/P at year end | None |
| `jan2026_disbursements.xlsx` | All January 2026 payments | Mix of 2025 and 2026 obligations |
| `customer_master.csv` | Approved customers | None |
| `prior_year_monthly_sales_2024.csv` | PY audited monthly sales | Different month format |
| `management_inquiry_notes.txt` | CFO/controller representations | Some are wrong |

---

## 4. Planted-error benchmark

### 4.1 Design

The generator plants six error types. You know the categories (from this document), but the seed randomizes which invoices, customers, month and amounts are involved, and it adds decoys that look like errors but are not.

| ID | Category | Where it shows up | Primary assertion |
|---|---|---|---|
| E1 | Revenue cutoff | Late-December invoices | Cutoff |
| E2 | Duplicate invoice | Sales ledger / aging | Occurrence |
| E3 | Unexplained revenue spike | One month's analytics | Occurrence (fraud risk) |
| E4 | Allowance understated | Aging / allowance analysis | Valuation |
| E5 | Unrecorded liability | January disbursements | Completeness |
| E6 | Data-integrity traps | Every file | Reliability of information |

Decoys include slow-paying customers who did pay in January or February, large late-December invoices that shipped on time, a properly accrued November freight bill, and January invoices for January services. There is also one bonus item below the clearly-trivial threshold that is not scored.

### 4.2 Keeping it honest

Because you wrote down the categories, this is not a fully blind test. To strengthen it:

1. Have a friend run `generate_pbc.py --seed <their number>` and send you only the `pbc/` folder. They keep `answer_key/`.
2. If that is not possible, use a seed you have not seen before and do not open `answer_key/` until Block 8.
3. In your write-up, state which approach you used.

### 4.3 Metrics

| Metric | Definition | Where it comes from |
|---|---|---|
| Detection score | Detection credit ÷ 6; cutoff receives proportional credit for invoices identified | `results.md` |
| Detection by method | Share caught during AI-assisted work vs your own review vs the reviewer agent | Findings "Caught by" column |
| False positives | Findings that match no planted error (review each; some may be valid) | `results.md` |
| Amount accuracy | Your quantified amount vs the planted amount | `results.md` |
| AI error count | Material AI mistakes you caught | AI_Log |
| Time per block | Actual vs planned minutes | Time_Log |

---

## 5. Audit approach

### 5.1 Materiality (AU-C 320)

The workbook defaults to 0.6% of net sales for overall materiality, 75% of that for performance materiality, and 5% of overall for the clearly-trivial threshold. With ~$40M in sales, that is roughly $240K / $180K / $12K. You must write your own rationale.

Things to consider: pretax income is small relative to revenue and changed sharply from the prior year, which argues against a pretax-income benchmark. First-year engagement status and management's "rushed close" comment could justify a lower performance materiality percentage.

### 5.2 Significant risks

| Risk | Why | Response |
|---|---|---|
| Improper revenue recognition (presumed fraud risk, AU-C 240) | Required presumption. Watch the gross margin and pretax income changes on the lead sheet. | WP1 analytics, cutoff, duplicates; WP2 receipts |
| A/R valuation (AU-C 540) | Flat 1% estimate; management says collections are fine | WP2 aging review and allowance recalculation |
| Completeness of liabilities | Controller described a rushed December close | WP3 search for unrecorded liabilities |
| Reliability of client-prepared data (AU-C 500) | Data comes from exported reports | Normalization log, tie-outs to TB |

### 5.3 Procedures by workpaper

**WP1 Revenue.** (a) Monthly substantive analytics: the expectation is prior-year month × (1 + growth). Investigate any month where the difference exceeds 50% of performance materiality, and corroborate each explanation with evidence (invoice, ship date, customer master, receipts), not just inquiry. (b) Cutoff: agree late-December invoices to the separate shipping-document file and evaluate the shipping date under the FOB shipping point policy. (c) Duplicate test: check the full population for repeated invoice numbers and for same customer, amount and date.

**WP2 Accounts receivable.** (a) Tie the aging to the TB and cross-foot the buckets. (b) Select a sample: all key items at or above performance materiality, then a documented method (monetary unit sampling or haphazard) for the rest. (c) Test subsequent receipts; for items with no receipt, document an alternative procedure. Note that subsequent receipts prove existence, but a receipt does not prove the sale belonged in 2025. (d) Recalculate the allowance with specific reserves where evidence supports them.

**WP3 Search for unrecorded liabilities.** Review every January payment at or above the threshold. The key question is when the goods or services were received, not the invoice date or payment date. The workbook shows whether each invoice is on the 12/31 A/P listing; you decide whether it should have been.

### 5.4 Evaluating misstatements (AU-C 450)

Log every finding in the Findings sheet with an amount, the accounts affected and a classification (factual, judgmental or projected). The sheet compares the total to overall and performance materiality. Any indicator of possible fraud should be written up as an escalation to the engagement partner, not only as a number.

---

## 6. The 8-hour runbook

**Rules for the day:**
- Log every AI mistake the moment it happens (AI_Log sheet). Reconstructing them later costs time.
- Record the clock time when you log each finding.
- Timebox each block. If you are behind, cut in this order: WP2 allowance write-up detail → planning risk table detail → WP1 duplicate write-up. Never cut Block 7 or Block 8.

### Block 0 — Setup (the day before, 20 min, not counted)
- Install Python 3.10+, create an isolated environment, and run `python -m pip install -r requirements.txt`.
- Run the full pipeline once with a throwaway seed to confirm it works, then delete the outputs.
- Open the workbook once in Excel to confirm formulas calculate.
- Have a timer and a screen recorder ready.

### Block 1 — Run the pipeline and inspect the data (0:00–1:00)
**Goal:** trusted, tied-out data.
```bash
python generate_pbc.py --seed <seed>     # skip if a friend sent you pbc/
python normalize.py
python build_workbook.py
```
1. Open the workbook in Excel and let it calculate.
2. Read `clean/normalization_log.md` line by line. Every **FLAG** needs a note on what it means and where you will address it.
3. Confirm all tie-outs are zero: ledger to TB, aging to TB, A/P listing to TB, lead sheet check row.
4. Spot-check 5 rows of clean data against the raw files.
5. Log any data-integrity issue as a Findings row (WP ref "Norm").

*Prompt:* "Here is the raw sales ledger and my normalization log. What else could go wrong importing this file that the log does not check? List specific tests."

**Done when:** all tie-outs are zero and every flag has a disposition.

### Block 2 — Planning memo (1:00–1:30)
**Goal:** materiality and significant risks documented.
1. Read `management_inquiry_notes.txt` and review the calculated lead-sheet benchmarks.
2. Complete the Planning sheet: benchmark rationale, percentages, 3–4 significant risks with responses and WP references.
3. Write a half-page planning memo (a text cell or separate doc) summarizing the business, risks and approach.

*Prompt:* "Here are the inquiry notes and the lead sheet for a fictional distributor. Draft a half-page planning memo covering business overview, materiality rationale, significant risks under AU-C 315 and 240, and planned responses. Flag any management statement that should be corroborated."

**Done when:** Planning sheet has no empty yellow cells in the materiality block; at least 3 risks listed.

### Block 3 — Lead sheet review (1:30–2:00)
**Goal:** planning analytics that point you at the risks.
1. Review every line with a large $ or % change.
2. Note especially gross margin, pretax income and A/R days.
3. Write a short note on each significant change and which WP addresses it.

**Done when:** each significant fluctuation has a note in column G.

### Block 4 — WP1 Revenue (2:00–3:15)
**Goal:** revenue analytics, cutoff and duplicates done and concluded.
1. Decide whether 6.5% growth is a supportable expectation. Document why.
2. For each INVESTIGATE month, drill into D_Sales for that month: largest invoices, new customers, missing ship dates, unusual memos.
3. Agree the selected invoices to D_Shipping, then complete the cutoff table: shipping document agreed, correct period Y/N and misstatement for each item.
4. Run the duplicate test on D_Sales (Excel COUNTIF, pivot, or AI-written pandas).
5. Log findings and write the conclusion.

*Prompts:*
- "Here is the sales data for [month]. Rank the 10 largest invoices and flag anything unusual: customers not in the master file, missing ship dates, memo text, round amounts, month-end dating."
- "Write pandas code to find duplicate invoice numbers, and separately, rows with the same customer, amount and invoice date."

**Done when:** every INVESTIGATE month is explained, every cutoff item concluded, duplicate test documented.

### Block 5 — WP2 Accounts receivable (3:15–4:30)
**Goal:** existence and valuation concluded.
1. Confirm the Section A tie-outs.
2. Select the sample: key items first, then your method. Document the sample size rationale in the dedicated sample-design cell.
3. For each item with no receipt, perform and document an alternative procedure (for this exercise: ledger history, credit-hold status, customer master, ship date).
4. Review items over 90 days and credit-hold customers.
5. Build the allowance: enter specific reserves with evidence, confirm the general rate, and read the difference.
6. Log findings and write the conclusion.

*Prompts:*
- "Given this aging and a performance materiality of $[PM], propose a sample: all key items, then a monetary unit sample of the remainder at [n] items with a fixed seed. Show the interval and random start."
- "For these open invoices with no subsequent receipt, what alternative procedures would an auditor perform under AU-C 505, and what evidence here supports or contradicts existence?"

**Done when:** every sample item has a conclusion, the allowance difference is explained, and the conclusion is written.

### Break (4:30–4:45)

### Block 6 — WP3 Search for unrecorded liabilities (4:45–5:45)
**Goal:** completeness of A/P concluded.
1. For every payment marked "Test", enter the goods/services period from the description and invoice date.
2. Mark Y/N for whether it was a 12/31 liability.
3. Review items marked "No" on the A/P listing carefully; the workbook calculates the unrecorded amount.
4. Glance at items below the threshold too, and note anything relevant.
5. Log findings and write the conclusion.

*Prompt:* "For each payment below, state the service or delivery period implied by the description and invoice date, and whether it represents a liability at 12/31/2025. Do not guess: say 'unclear' where the evidence does not say."

**Done when:** every tested row has J and K filled in, and the unrecorded total is carried to Findings.

### Block 7 — Reviewer agent and clearing notes (5:45–6:45)
**Goal:** a documented review cycle.
1. Save the workbook. Open a new Claude chat, attach the workbook and normalization log, and paste `prompts/review_agent_prompt.md`.
2. Paste the returned table into Review_Notes.
3. For every note: fix the workpaper and describe the fix, or rebut it with reasons. Mark it Cleared.
4. If the review surfaces a new finding, log it with "Caught by" = Reviewer agent.
5. Log reviewer-agent mistakes (wrong cell, invented issue) in AI_Log.

**Done when:** every review note has a response and status.

### Block 8 — Results and failure log (6:45–7:30)
**Goal:** your quality measured and your product feedback written.
1. Finalize Findings; check the aggregate against materiality.
2. Run `python score_results.py`. Only now open the answer key.
3. For each missed error, write one sentence on why it was missed and what procedure or tool change would have caught it.
4. Complete AI_Log and Time_Log.
5. Write a one-page product memo (section 7.2).

**Done when:** `results.md` contains the detection score and the memo is written.

### Block 9 — Package (7:30–8:00)
1. Write the README (section 7.1).
2. Record a 3–5 minute Loom (section 7.3).
3. Push to GitHub. Include `pbc/`, `clean/`, the workbook, `results.md`, the memo and scripts. Include `answer_key/` last, with a note that it was sealed until Block 8.

---

## 7. Deliverables

### 7.1 README outline
1. **One-paragraph summary:** what you did, in how long, and the detection rate.
2. **Results table:** from `results.md`, plus time per block.
3. **How it works:** the data-flow diagram and how to rerun it.
4. **What the AI did vs what I did:** be specific and honest, including that the scripts were built with AI before the session.
5. **Where the AI failed:** top 3 from AI_Log.
6. **What I missed and why.**
7. **Disclaimer:** fictional company, synthetic data, not an actual audit.

### 7.2 Product memo (one page)
Write it as feedback to an audit-platform product team. Three to five suggestions, each with: the problem you hit, how often, the cost in time or quality, and the proposed change. Examples of the kind of thing to look for: import-time subtotal detection, source links from every workpaper number, an automatic check of customers against the master file, a service-period extractor for disbursement descriptions, and review notes that cite exact cells.

### 7.3 Loom script (3–5 minutes)
| Time | Content |
|---|---|
| 0:00–0:30 | Who you are and what the project is |
| 0:30–1:15 | Messy data in: show a raw file, the normalization log, the tie-outs |
| 1:15–2:30 | One workpaper in depth: the flagged month, how you investigated, the conclusion |
| 2:30–3:15 | The review cycle: one reviewer-agent note and how you cleared it |
| 3:15–4:15 | The score, one miss, one AI failure and your product suggestion |
| 4:15–4:45 | Close: why this is how you would work at Modus |

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Script fails on the day | Block 0 dry run; `requirements.txt` pinned to common versions |
| Falling behind schedule | Timeboxes and a defined cut order |
| AI states something false confidently | Tie every number to data; log every miss |
| Test isn't blind | Friend-held seed (section 4.2), disclosed in README |
| Looks like an engineering project | Lead with workpapers and conclusions in the README and Loom, not code |
| Technical inaccuracy in a conclusion | Reviewer agent plus a final self-review against the checklist |
| Confusion with real client work | Fictional company, disclaimer on the Index sheet and in the README |

---

## 9. Standards reference

| Standard | Topic | Used in |
|---|---|---|
| AU-C 230 | Audit documentation | All WPs, review notes |
| AU-C 240 | Fraud; presumed revenue risk | Planning, WP1 |
| AU-C 315 | Risk assessment | Planning |
| AU-C 320 | Materiality | Planning |
| AU-C 330 | Responses to assessed risks | WP1–WP3 |
| AU-C 450 | Evaluating misstatements | Findings |
| AU-C 500 | Audit evidence | Normalization, WP2 |
| AU-C 505 | External confirmations | WP2 (simulated) |
| AU-C 520 | Analytical procedures | Lead, WP1 |
| AU-C 530 | Audit sampling | WP2 |
| AU-C 540 | Accounting estimates | WP2 allowance |
| AU-C 560 | Subsequent events | WP3 context |

Check the current AICPA codification for any wording you quote; this table is a map, not a citation source.

---

## 10. Pre-session checklist

- [ ] Python and packages installed; dry run completed
- [ ] Seed chosen by a friend, or unseen seed chosen
- [ ] `answer_key/` moved out of sight
- [ ] Excel opens the workbook and calculates
- [ ] Claude chat ready; review prompt file open
- [ ] Timer, Loom and GitHub repo ready
- [ ] Time_Log open with a clock-start time recorded
