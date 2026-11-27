# The gold quality pass and facedata: comparison and risks

The FACE extractions that `facedata` reads come from the dataflow gold layer,
**after** its quality pass (QA). This note compares the two passes and lists
where the gold pass can break `facedata` or make its output misleading.

**Sources.** The two dataflow documents in this folder, dated 2026-11-20
(config commit `bef50da9`): `face_gold_pass_overview.pdf` (Part 1, "How It
Works") and `face_gold_pass_rules.pdf` (Part 2, "Full Thresholds & Rules"). On
the facedata side: `docs/ARCHITECTURE.md`, the cohort schemas and the tests,
at the state of 2026-11-20. No extraction was read for this note. Where a
claim rests on what facedata found in the data, it comes from the progress
logs.

## Summary

- The two passes overlap a great deal: placeholder dates, missing codes,
  whitespace and encoding, decimal commas, yes/no answers, units and scale
  errors, and range checks. facedata repeats most gold repairs and finds
  cases gold leaves behind, so its copies are a safety net and should stay.
- The main difference is the range check. Gold sets aside **the whole visit**
  for one out-of-range value; facedata removes **that cell** and logs it.
  Visits removed by gold never reach facedata, so facedata cannot flag them.
- Three risks would show up loudly: category labels that replace numeric codes
  (R3), new patient-table columns that fail the coverage tests (R4), and
  contradictions inside the gold config (R7).
- Two risks are silent: whole-visit removal (R1) and rewrites with no trace in
  the extraction (R5). The QA pass being optional per run (R2) makes every
  other risk vary from one extraction to the next.

## 1. Comparison of the two passes

### 1a. Done by both

| Rule | Gold pass | facedata | Difference |
|---|---|---|---|
| Placeholder dates | `1900-01-01` and `####` on 133 date columns → missing | `1000-01-01`, `1850-01-01`, `1900-01-01`, plus `1950-01-01` on visit dates; partial dates `YYYY-00-00` → middle of the period | facedata catches more and flags them (`date_placeholder`, `date_partial`) |
| Zero or code meaning "unknown" | 70 columns where 0 → missing; sentinels 999, 9999, 2, 3 on named columns | Per-variable `missing:` codes (e.g. `agemere {0, 99}`, `mere_structure {"2"}`) | Same idea. Gold blanks silently; facedata records the reason (`missing_code`) |
| `N/A` typed as text | Exactly `N/A`, `NA`, `n/a`, `na` → missing, in every text column | `NA`, `N/A`, `Non applicable`, plus `NSP`, `NR`, `NC`, `?`, `.`, `NaN`… in any case | facedata has the wider token list |
| Whitespace, encoding | Trimmed; `Ã©` repaired | Trimmed; ASP accents repaired (`repair_accents`) | facedata still finds double-encoded accents (all of ASP, a few hundred free-text cells in SZ and DR), so gold misses some |
| Decimal comma, `oui` → number | Type coercion | `27,90`, `.45`, `28.2.`, trailing `%` → `format_repaired` | facedata still finds these in the extractions, so gold misses some |
| Yes / No / Unknown | 500 columns → `Y` / `N` / `U` | Schemas accept `{Y: 1, N: 0, Oui: 1, Non: 0}` with `U: unknown` | Compatible either way |
| Unit conversion, correct label | §5: 12 measurements, factor applied and label rewritten | Per-variable `units`, each with a factor and an expected range | Same factors |
| Scale errors, wrong or missing label | §4: 34 rules with fixed thresholds | Unit taken from the value's magnitude (`unit_inferred`, `unit_doubt`, `unit_unknown`) | Same cases, see the table below |
| Range check | 174 columns; out of range sets **the whole visit** aside | Every variable; out of range removes **that cell only** (`out_of_range`) | The main difference; see R1 |
| Interval entries | `tmta01` `[45-50]` and `egf` `100-91` → midpoint, silently | Bands → `band_middle`, or censored values, flagged | Gold hides that the value was imprecise |
| Apgar | Out-of-range cell blanked | Cell-level for every variable | Same behaviour |

How facedata covers the gold scale fixes (§4), through units chosen by
magnitude in the BP schemas:

| Gold §4 rule | facedata equivalent |
|---|---|
| Height > 1000 → ×0.1 | Unit `"cm, decimal point lost"`; also `m` and two lost decimals |
| Weight > 1000 → ×0.1 | Unit `"0.1 kg"` |
| QT, QTc, RR in ms | Units `ms` and `cs` |
| WBC, platelets, RBC as a count per µL | Units `/mm3` and `G/L` |
| Hb in g/L under a g/dL label | Unit `g/L`, expected 50–250 |
| Phosphorus, calcium in mg/L under mmol/L | Units `mg/L` and `mg/dL` |
| Systolic BP 11 → 110 | Unit `cmHg` (×10) |
| PSQI value ×1/60 | Unit `"min x 60"` |

Not checked one by one: urate, BMI < 5 → ×10, free T3 and T4 mislabelled,
total cholesterol < 1.5.

### 1b. Done by the gold pass only

| Gold rule | Does facedata need it? |
|---|---|
| Per-patient confirmed corrections | Yes. facedata has no such mechanism |
| Research opt-out removal | Yes. It is a legal obligation, and facedata cannot do it |
| Most-common-spelling clean-up of free text | No. facedata delivers text as written |
| Canonical labels for `maristat`, `edulevel`, `stprof`, `empjob`, `egf` | Conflicts with facedata; see R3 |
| `"5 fois"` → 5 (`recours_soin_psy_psychiatre_nb`) | facedata does not read this column in BP |
| `com05_` separators → hyphens | Harmless: facedata keeps the column as typed text |
| Sibling substance flags 3–5 all zero → missing | facedata already lists `soeur3_alcool`… in `ignored.yaml` and reads the relatives' lists instead |
| Quarantine area, `qa_changelog`, `is_quarantined` | facedata keeps its own record (`flags`) but sees none of gold's |

### 1c. Done by facedata only

| facedata step | Why it matters |
|---|---|
| Duplicate visit rows; visit dates before the cohort opened or in the future; impossible ages; visit dates out of visit order | Gold has no visit-level logic |
| Censored values `<5`, `>95` → value plus a `_cens` column | Gold would read `<5` as text or lose it |
| Editions in the same columns (WAIS-III/IV, BIS-10/12, DSM-IV/5, child and adult forms) | Gold has no notion of edition |
| Z-score sign flips per centre | Not in gold |
| Range checks on scale items and totals (PANSS, MADRS, CTQ, FAST…) | Gold switched these off on 2026-06-04 |
| Score recomputation, compared with the stored score (`score_mismatch`, `score_not_recomputed`) | Gold relies on its separate scoring step, which nothing checks against the items |
| Norm tables (scaled scores, percentile bands) | Not in gold |
| HTML entities, `d\'une`, literal `\n` in cells | Not in gold |
| Two raw columns for one variable (`column_conflict`); periods in which a column is unreliable (`period_doubt`) | Not in gold |
| Units as a percentage of another variable (white cell types) | Not in gold |
| Patient-level values that change between visits (`patient_value_varies`) | Gold does not range-check the patients table |
| `asked_if`: a 0 after a "no" to the gating question | Not in gold |
| Treatment lists, packed records, relatives as rows | Not in gold |
| Winsorising, the `qc` table, site and year shifts, the HTML report | Not in gold |
| Same names across cohorts; catalogue of shared instruments | Not in gold |

### 1d. Points that differ in meaning, not just in method

- **`psqi02`.** Gold calls it "bedtime, 0–1440 minutes after midnight".
  facedata reads it as **sleep latency**, 0–240 minutes. The ÷60 fix is the
  same, but one of the two labels is wrong.
- **Range bounds.** Where gold is looser than facedata (HDL ceiling 5.0 vs 4;
  TMT-A floor 5 s vs 10 s), facedata drops only the cell, which is fine. Where
  gold is stricter, the whole visit is lost before facedata sees it. The 174
  enforced bounds have not yet been compared with the facedata ranges one by
  one.

## 2. Risks that facedata breaks or misleads after the gold pass

| # | Risk | Trigger | Effect on facedata | Severity | Fix |
|---|---|---|---|---|---|
| R1 | Whole-visit removal | One value out of any of the 174 enforced bounds | The visit is missing from the extraction, with no flag: facedata's rule "nothing disappears silently" no longer holds end to end. The losses are not random (extreme patients, typo-prone sites). `common.baseline()` silently falls back to the screening visit. Follow-up series get gaps | **High**, silent | Ship the quarantine area with the extraction; facedata adds a `quarantined` flag. Better: gold marks cells instead of removing visits |
| R2 | The QA pass is optional and continues on failure | A run with QA off, or a failed QA | facedata cannot tell which kind of extraction it got. Flag counts and `qc` shift between extractions; R3 can appear or disappear | **High** | Put the QA state, run id and config commit in every extraction |
| R3 | Category labels replace codes | §7 applied to `maristat`, `edulevel`, `stprof`, `empjob` | facedata expects `1`, `2`… (e.g. `facedata/bp/schemas/social/social.yaml`), so every value becomes `unknown_code` (danger) and the whole column goes missing | **High**, loud | Agree on one coding. facedata can accept both, as it does for `Y`/`Oui` |
| R4 | New patient-table columns | `is_quarantined` and `quarantine_reason` in the extraction | Coverage tests fail: `not_assigned == 0` in `tests/test_real_data_sz.py`, `_dr.py`, `_asp.py` | Medium, loud | Read them through a patient-level schema |
| R5 | Silent rewrites | §4, §5, §7, the spelling clean-up, patient corrections | facedata's `raw` is not raw. `unit_*` counts, site and year shifts can't see unit mixtures gold already fixed. The "as written" plot shows gold's values | Medium, silent | Ship `qa_changelog`; facedata adds a `gold_fix` flag holding the value before the fix |
| R6 | Dictionary and spelling clean-up drift | The config changes ("living configuration"); the most common spelling is picked again on each run | Codes change between extractions → `unknown_code`, or two answers merged | Medium | Config commit in the extraction; a changelog of the mappings |
| R7 | Contradictions inside the gold config | `edulevel` range "0–35 years" and `stprof` 0–6 on columns mapped to text; range 0–1 on flags mapped to `Y`/`N` | The order of the steps decides whether those visits are set aside: visits lost for no clinical reason | Medium | Fix the gold config |
| R8 | "Unknown" codes not declared as sentinels | A `9` or `99` (ASP writes these for "not known") in a 0/1 flag other than `vih`, `hvc`, `genetique` | Whole visit set aside | Medium, not confirmed | Check ASP's codes in the gold config |
| R9 | Meaningful zeros erased | C-SSRS 06/08/09: 0 → missing; vitamin D: 0 → missing | facedata cannot tell "not asked" from "not recorded", nor deliver "below assay" as left-censored | Low–medium | Deliver a code, or `<limit` |
| R10 | Intervals collapsed | `egf`, `tmta01` | No `band_middle` flag: imprecise values look exact | Low | Keep the raw interval |
| R11 | Stored scores come from dataflow | The separate scoring step | facedata's `score_mismatch` findings may describe dataflow's formula, not the EMR's, so some "to correct in the EMR" questions may belong to the dataflow team | Medium | Mark which stored totals dataflow computes |
| R12 | Opt-out is a true delete | A new opt-out | Older `.tsv` files in `data/` are the only remaining copy of that patient | Legal | Delete old extractions when a new one arrives |

R1 and R5 are silent. R3 and R4 show up at once, as a failing test or a
column of danger flags. R2 makes all the others vary from one extraction to
the next.

## 3. Recommendations

1. **Put the QA state in every extraction:** whether the pass ran, the run id
   and the config commit (R2, R6).
2. **Ship the quarantine area and `qa_changelog` with the extraction.**
   facedata turns them into flags (`quarantined`, `gold_fix`), which makes its
   invariant true end to end (R1, R5). Read `is_quarantined` and
   `quarantine_reason` through a patient-level schema rather than ignoring
   them (R4).
3. **Settle the coding of `maristat`, `edulevel`, `stprof` and `empjob`.**
   If the labels are the future, add them to the facedata `codes` beside the
   numbers (R3).
4. **Send to the dataflow team:** the contradictions of R7; the sentinels of
   R8; the requests to keep the C-SSRS "not asked", vitamin D "below assay" and
   interval information (R9, R10); the `psqi02` label (§1d); which stored
   totals dataflow computes (R11).
5. **Compare the 174 enforced gold bounds with the facedata ranges** and list
   where gold is stricter, since each of those costs whole visits (§1d).
6. **Record the decision in facedata:** a line in `docs/ARCHITECTURE.md` §1
   saying that the extraction comes after the gold pass, and an entry in the
   four `PROGRESS.md` files.

## Appendix: what changed in the gold pass between 2026-09-01 and 2026-11-20

As stated in the appendices of the two PDFs, and what it means for facedata:

| Change | For facedata |
|---|---|
| The patients table keeps every patient and adds `is_quarantined`, `quarantine_reason` | Patients are no longer lost from the gold patients table; the two columns need a schema (R4) |
| Psychometric scale bounds are not enforced (since 2026-06-04) | Scale items and totals never cause a visit to be set aside; facedata is the only range check on them |
| 14 documented repair steps instead of 8 (`N/A` text, free-text counts, interval midpoints, digit separators) | R10; the others are harmless or already handled |
| Unit conversion runs before the scale corrections | No effect |
| Yes / No / Unknown → `Y` / `N` / `U` on 500 columns | facedata already accepts both spellings |
| A per-run change log (`qa_changelog`, JSON lines) and five audit columns in the quarantine area | The trace facedata needs exists; it must be shipped (recommendation 2) |
| Corrections and opt-outs run on every run; an opt-out is a true delete | R12 |
| The QA pass is optional per run and continues on failure | R2 |
