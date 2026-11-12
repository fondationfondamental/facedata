# FACE BP — progress, decisions and open questions

Extraction: `BPALL_20261030.tsv` (22,077 rows × 2,236 columns, 6,476 patients).
Dictionary: `FACEBP_thesaurus_V4.34.xlsx`.

## Stages

| Stage | Content | State |
|---|---|---|
| 1 | Specs: `ARCHITECTURE.md`, `SCHEMA_SPEC.md`, the first 17 schemas, this file | Written, waiting for review |
| 2 | Generic pipeline, proven on those 17 schemas | Done on 2026-11-12: 40 tests pass, the numbers below are reproduced, the report renders |
| 3 | BP tab by tab, in the order below | Not started |

## Decisions taken

| # | Date | Decision |
|---|---|---|
| D1 | 2026-11-11 | Schemas are YAML, one file per instrument, read as text (`yaml.BaseLoader`) |
| D2 | 2026-11-11 | `load()` returns a clean wide table plus a long flag log |
| D3 | 2026-11-11 | Winsorising at percentiles (default 1% and 99%), with schema override |
| D4 | 2026-11-11 | QC as one HTML report per cohort: an index page plus one page per instrument |
| D5 | 2026-11-11 | The `.tsv` is the source file; the `.xlsx` is never read |
| D6 | 2026-11-11 | Tab order as listed below, not strict dictionary order |
| D7 | 2026-11-11 | BIS-10 (34 items) and BIS-12 (12 items) are two instruments. An EMR error stored the BIS-12 answers in BIS-10 columns, so those columns are split by form into the schemas `bis10` and `bis12`, with separate output columns |
| D8 | 2026-11-12 | The BIS-12 questions are the same twelve BIS-10 items (1, 6, 8, 9, 12, 14, 17, 20, 21, 23, 25, 28), numbered 1 to 12 in that order. `bis12_01` to `bis12_12` follow it and are scored like those BIS-10 items |
| D9 | 2026-11-12 | General rule: a change of instrument, edition or form is never hidden inside one output column. Each edition or form is its own instrument, with its own schema and output columns, and a version column says which one was used at each visit |
| D10 | 2026-11-12 | WAIS-III and WAIS-IV are two instruments. Every WAIS subtest is split by `wais_version` into `wais3_*` and `wais4_*` schemas. Scores that may be comparable across editions (age-scaled scores, spans) are still delivered as separate columns |
| D11 | 2026-11-12 | WAIS-III vocabulary: the EMR derived the stored scaled score, and its z-score, from the wrong raw total. Both are delivered as stored and flagged `derived_doubt` on every row, until they can be recomputed from the norm table (O12). General rule: a stored value that the EMR computed from a stored score is marked `derived_from` that score and is flagged wherever the stored score is wrong |
| D12 | 2026-11-12 | A follow-up visit takes the DSM version of the patient's inclusion. `dsm_criteria` is read once per patient (`level: patient` in the `version` block) and given to all the visits of that patient |
| D13 | 2026-11-12 | TMT z-scores written in the old sign convention are flipped, so that a higher z-score always means a better performance. The date of the change is found for each centre from the data (`sign` block, pipeline step 8). Values within 90 days of it get `sign_doubt` |
| D14 | 2026-11-12 | From 2022 the follow-up form is the DSM-5 form for everyone. A follow-up visit dated from 1 January 2022 is read as DSM-5, whatever the patient's inclusion (`follow_up` in the `version` block). The centres changed between the end of 2021 and May 2022; 31 visits of early 2022 still hold a mixed-episode count, which is then not read |
| D15 | 2026-11-12 | A patient with no DSM criteria recorded at inclusion gets the version of the inclusion year: DSM-IV before 2020, DSM-5 from 2023 (`by_inclusion_date`, flag `version_inferred`). Included in 2020 to 2022, the version stays unknown |

## Open questions

Each has a default that the schemas already follow. Answer when the
instrument is reached, or earlier.

| # | Question | Default used | Needed for |
|---|---|---|---|
| O1 | BIS reversed items: the extraction scores them `6 − value`, the usual rule on a 1 to 4 scale is `5 − value`. Which do we keep? | `5 − value`; stored scores are compared with a documented offset | BIS-10, BIS-12 |
| O2 | A left-censored result `<5`: is the value the limit (5) or half of it (2.5)? | The limit, with `<variable>_cens` = −1 | Biology |
| O3 | CRP has 389 results that are exactly 0. Real zeros, or "below the limit" with an unknown limit? | Kept as 0 | Biology |
| O4 | `screening` and `V0` are separate rows (3,973 and 6,476). Is screening its own visit, and what is its `visit_month`? | Own visit, `visit_month` empty | PATIENT |
| O5 | What are the `_n1` ratings of MADRS and YMRS (about 350 visits, mostly 2011 to 2012), and which rating is the reference? | Not loaded yet | HETERO-QUESTIONNAIRES |
| O7 | Family history (about 380 columns): summaries per patient, a long table, or left out? | Undecided | ANTECEDENTS |
| O8 | Current treatments are exported as Python lists in one cell (`med_psy_*`). What should a treatment variable look like for modelling? | Undecided | TRAITEMENTS |
| O12 | Norm tables to be supplied by the project lead (announced on 2026-11-12): WAIS-III vocabulary (age band × raw total → scaled score), CVLT and others. With the WAIS-III table the scaled score is recomputed from the true total instead of being flagged. A lookup-table field must then be added to the spec. Estimated from the extraction itself, the stored scaled score is 1 point too low on 75% of rows, 2 points on 9%, and right on 17% | Stored scaled score and z-score delivered with `derived_doubt` on every row (D11) | WAIS-III vocabulary, CVLT |
| O15 | The generic code is 1,658 lines (blank lines and comments included), against a budget of about 1,300. The largest files: `harmonise.py` 291, `schema.py` 258, `plots.py` 208. Trim, or raise the budget? | Left as it is | All |

Answered on 2026-11-12: O9 became D11, O10 became D12, O11 became D13, O13 became D14, O14 became D15.

## Instrument changes found in the extraction

On 2026-11-12 every column was scanned for a change over the years in four
things: which columns of an instrument are filled, the level or range of the
values, the share of non-numeric values, and the set of codes. Rule applied:
decision D9.

### Two editions or forms in the same columns

| Case | What the data show | Handling | State |
|---|---|---|---|
| BIS-10 / BIS-12 | The 12-item form is stored in 12 of the 34 BIS-10 columns (1,438 visits, most from 2021 on) | Two schemas, split by which items are filled | Done: `bis10`, `bis12` |
| WAIS vocabulary | The columns `vocab*_wais3` hold the 33-item WAIS-III test (1,219 visits) and the 30-item WAIS-IV test (2,107 visits, 2011 to 2021) | Two schemas, split by `wais_version` | Done: `wais3_vocabulaire`, `wais4_vocabulaire` |
| WAIS matrices | The same 26 item columns for both editions (1,215 and 4,277 visits) | Same | Done: `wais3_matrices`, `wais4_matrices` |
| WAIS coding, symbol search, processing speed | The same 14 columns for both editions | Same | Done: `wais3_code_symboles_ivt`, `wais4_code_symboles_ivt` |
| WAIS digit span | The same columns; WAIS-IV adds the sequencing task and its summary columns are shifted against their labels | Same | Done for the summary scores: `wais3_memoire_chiffres`, `wais4_memoire_chiffres`. Trial-level columns come with the NEUROPSYCHOLOGIE tab |
| DSM-IV / DSM-5 mood evaluation | `dsm_criteria` at V0: 4,526 DSM-IV (until 2022), 1,100 DSM-5 (from 2020). Same columns. Eight mixed-episode variables and the episode type "Mixte" exist under DSM-IV only; some category wordings differ | Two schemas per section, split by `dsm_criteria`, which is read once per patient (D12) | Done for the follow-up section: `dsm4_depuis_derniere_visite`, `dsm5_depuis_derniere_visite`. The inclusion sections come with EVALUATION MEDICALE |

### Related cases that are not two editions in one column

| Case | What the data show | Handling | State |
|---|---|---|---|
| WAIS-IV similarities | Own columns, WAIS-IV only (802 visits from 2018). It replaced vocabulary in the WAIS-IV battery | One schema | Done: `wais4_similitudes` |
| CPT-II / CPT-3 | Separate columns: `cpt2xx` on 3,152 visits until 2021, `cpt3xx` on 509 visits from 2022; only 2 visits have both. `cpt_version` is filled on every row and mislabelled | Two schemas, nothing to split; `cpt_version` ignored | Planned with NEUROPSYCHOLOGIE |
| TMT z-scores | Same test, but the sign of five of the six z-scores flipped centre by centre between 2012 and 2014: their rank correlation with the raw time is +0.8 before and −0.85 after. Eight centres changed; about 770 of 5,863 visits use the old sign | Old values flipped, one switch date per centre found from the data (D13) | Done: `tmt` (draft; the percentile columns are still to add) |
| TMT percentile columns | Numbers (`95`) until 2015, classes (`>10`, `>25`) from 2016 | A percentile-band type, to be added to the spec | Planned with NEUROPSYCHOLOGIE |
| CVLT standardised columns | Bands, percentiles and z-scores mixed in the same column in every year; `cvlt20z_` held "Non applicable" until 2015 | Same percentile-band type | Planned with NEUROPSYCHOLOGIE |
| Unit labels in biology | MCH `%` to `pg`, MCHC and prolactin labels change over the years; from 2022 `rad_ht` and `rad_ccmh` hold a unit choice | The unit rule | Planned with BILAN BIOLOGIQUE |

### Checked, no change found

Same columns and same coding in every year: PSQI, ALS, AIM, WURS, AQ-12, CTQ,
EQ-5D (five levels throughout), Altman, MAThyS, QIDS, STAI, PRISE-M, CSM,
MDQ, FAST, MADRS, YMRS, Stroop, COBRA, SCIP, spatial memory. The
questionnaires that the dictionary's contents tab calls "reduced since 2021"
show no change inside their columns, apart from BIS.

Columns that exist only for a period, and are simply empty elsewhere: MARS
item 11 (from 2019), the ALS anxiety and bipolar subscale scores (`als58`,
`als60`, until 2022), six verbal-fluency columns (2011 to 2024), the TMT-B
perseveration columns (from 2011), four CGI columns (from 2013), BDHI, LTSV
and LTSG (retired by 2021), the `_n1` second ratings (2010 to 2019),
`lost_to_follow_up_*_patient` (replaced by `*_stopsuivi`), and the
family-history date columns (from 2024).

## Findings to report to whoever produces the extraction

| Finding | Evidence |
|---|---|
| Epworth items are all zero | `ess0101` to `ess0109`: 56,135 values, all `0` |
| BIS reversed items are scored `6 − value` on a 1 to 4 scale | Stored scores recovered exactly from the items on all complete rows |
| BIS-12 answers are stored in BIS-10 columns | 1,438 visits (a few from 2018, most from 2021 on) have only twelve of the 34 item columns filled |
| On BIS-12 visits the EMR still fills the BIS-10 subscales, the BIS-10 total and `bis11` | Computed from the 4, 4, 4, 12 and 9 items that happen to exist |
| Dictionary formula of the BIS planning subscale is incomplete | The stored score also uses items 14, 18 and 31 |
| WAIS-IV digit-span summary columns are shifted against their dictionary labels | `mcodemp_w` = raw total, `mcoiemp_w` = forward span, `empdid_w` = backward span, `nbrut_w` = span difference |
| WAIS-IV vocabulary is stored in columns named for WAIS-III | `vocab*_wais3` on 2,107 WAIS-IV visits |
| The WAIS-III vocabulary raw total is 3 points too low | The stored total equals the sum of the 33 items minus 3 on 1,207 of 1,210 rows, and is never the sum itself. The scaled score and its z-score were derived from it |
| TMT z-scores changed sign convention between 2012 and 2014 | Rank correlation with the raw time: +0.8 until 2011, −0.85 from 2014. Eight centres changed, each at its own date; the z-score of the B−A error difference never changed |
| `dsm_criteria` is empty at inclusion for 850 of 6,476 patients | 364 of them have follow-up mood evaluations (731 visits) whose DSM version is then unknown |
| Three lifetime answers are stored in columns named for the follow-up section | `mhoccur_edm_psy_spv`, `mhoccur_epman_psy_spv` and `mhoccur_epmixt_psy_spv` are filled at inclusion only |
| `cpt_version` is filled on every row with WAIS labels | Values `wais3` / `wais4` on all 22,077 rows |
| Unit columns are filled where the result is empty | 796 to 10,809 rows per analyte |
| Current treatments are exported as Python list literals | `med_psy_*`, 18,107 rows |
| Duplicated visit records | 7 exact duplicate rows |
| `nom_centre` is empty | 100% of rows |

## What the first schemas must produce (stage 2 acceptance)

First measured on the extraction with a throwaway script that follows the
spec. The pipeline reproduces every number; `tests/test_real_data.py` checks
the main ones each time the tests run on a computer that has the extraction.

| Schema | Expected |
|---|---|
| all | 22,070 visit rows after dropping duplicated visit records |
| `madrs` | `madrs_total` on 17,243 rows; no `score_mismatch` |
| `bis10` | 4,688 visits with `bis_form` = `bis10` (4,579 complete, 109 partial). `bis10_total` on 4,636 rows, range 36 to 113; `bis10_sum12` on 4,661 rows. All seven compared scores agree with the stored ones once the offset is applied |
| `bis12` | 1,438 visits with `bis_form` = `bis12` (1,428 complete, 10 partial). `bis12_total` on 1,428 rows, range 13 to 48. Both compared scores agree with the stored ones once the offset is applied |
| `biochimie` CRP | 13,026 results: 2,323 `censored_left`, 5 `censored_right`, 30 more censored through the unit column; none unparsed |
| `biochimie` glucose | 12,930 results: 354 `unit_converted`, 124 `unit_inferred`, 23 `unit_doubt`, 6 `out_of_range`, 2 censored |
| `nfs` haemoglobin | 13,435 results: 485 `unit_inferred` (473 labelled g/dL, 12 with an unusable label), 12 `out_of_range` |
| all WAIS schemas | `wais_version`: 1,302 `wais3` visits, 4,978 `wais4` visits |
| `wais3_memoire_chiffres` | Total check: no mismatch on 1,249 rows |
| `wais4_memoire_chiffres` | Total check: 13 `score_mismatch` on 4,639 rows, and 13 `derived_doubt` on the scaled score and on its z-score. 21 span differences `out_of_range` |
| `wais3_vocabulaire` | `wais3_vocab_total` on 1,212 rows, range 8 to 64; 3 `score_mismatch` once the offset of −3 is applied. 1,210 `derived_doubt` on the scaled score and 1,210 on its z-score (every row that has one) |
| `wais4_vocabulaire` | `wais4_vocab_total` on 2,085 rows, range 9 to 57; 3 `score_mismatch`, and 3 `derived_doubt` on the scaled score and on its z-score. 27 cells of items 1 to 3 `out_of_range` |
| `wais3_matrices` | `wais3_mat_total` on 1,215 rows; no mismatch |
| `wais4_matrices` | `wais4_mat_total` on 4,271 rows; 1 `score_mismatch`, and 1 `derived_doubt` on the scaled score and on its z-score |
| `wais4_similitudes` | `wais4_simil_total` on 802 rows; no mismatch |
| `wais4_code_symboles_ivt` | 5 `out_of_range` on symbol search correct answers and 5 on its raw score |
| `tmt` sign | A switch date in 8 centres: 4 in 2012, 2 in 2013, 2 in 2014. `sign_flipped`: 778 (A time), 769 (B time), 770 (B−A time), 771 (A errors), 759 (B errors) z-scores. `sign_doubt`: 193 on the A time z-score. After the flip, the rank correlation between each time and its z-score is negative in every centre and year that has 8 visits or more (worst −0.30) |
| `tmt` values | `tmt_a_time` valid on 5,895 rows (4 unparsed, 2 `out_of_range`). `tmt_b_time` valid on 5,840 rows (16 missing codes, 4 unparsed, 7 `out_of_range`, 1 right-censored). `tmt_a_errors` on 5,844 rows, `tmt_b_errors` on 5,800 |
| both DSM schemas | `dsm_version` (decisions D12, D14, D15): 16,313 visits `dsm4`, 5,458 `dsm5`, 299 without; no patient with two values. 316 visits with data get `version_inferred`, 22 get `version_unknown` |
| `dsm4_depuis_derniere_visite` | `dsm4_fu_any_episode` filled on 7,186 visits (84 missing codes). 23 counts right-censored at 20. No unparsed value, no unknown code |
| `dsm5_depuis_derniere_visite` | `dsm5_fu_any_episode` filled on 2,341 visits (20 missing codes). No unparsed value, no unknown code |
| unread cells (`coverage()`) | 1,437 or 1,438 per column for the five BIS-10 score columns that the EMR fills on BIS-12 visits; 11 per column for vocabulary items 31 to 33 on WAIS-IV visits; 44 and 22 in the two mixed-episode columns, on visits read as DSM-5 or of unknown version; 8 to 22 in the other follow-up columns, on the 22 visits of unknown version |
| visits | 3 visits had duplicated records (7 rows dropped); 5 placeholder visit dates; 31 visits dated before the patient's previous visit |
| coverage | 206 columns covered, 2 ignored, 2,028 not assigned yet |

## Checklist

State: ☐ not started · ◐ tracer schema (draft) · ☑ reviewed.
Numbers are variables in the dictionary section, item ranges expanded.

### 1. PATIENT (`patient/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Identity and demographics (no header) | 10 |
| ☐ | Inclusion | 2 |
| ☐ | Provenance | 6 |
| ☐ | Fin de suivi | 12 |
| ☐ | patient | 8 |
| ☐ | visit | 7 |

### 2. HETERO-QUESTIONNAIRES (`hetero_questionnaires/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Questionnaire CGI-EGF | 6 |
| ☐ | Questionnaire FAST | 31 |
| ◐ | Questionnaire MADRS | 11 |
| ☐ | Questionnaire MADRS_n1 | 11 |
| ☐ | Questionnaire YMRS | 12 |
| ☐ | Questionnaire YMRS_n1 | 12 |
| ☐ | Episode depressif majeur actuel | 15 |
| ☐ | Episode maniaque actuel | 10 |
| ☐ | Questionnaire ALDA | 10 |

### 3. CONSTANTES et ECG (`constantes_et_ecg/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Paramètres physiques | 4 |
| ☐ | Pression artérielle / fréquence cardiaque | 6 |
| ☐ | ECG | 5 |

### 4. BILAN BIOLOGIQUE (`bilan_biologique/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Biochimie (CRP and glucose done as tracers) | 32 |
| ☐ | Bilan lipidique | 9 |
| ☐ | Bilan hépatique | 10 |
| ☐ | Bilan thyroidien | 6 |
| ◐ | NFS (haemoglobin done as tracer) | 26 |
| ☐ | bHCG and prolactin | 4 |
| ☐ | Dosage des psychotropes | 8 |
| ☐ | tests speciaux | 10 |

### 5. AUTO-QUESTIONNAIRES (`auto_questionnaires/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Questionnaire PRISEM | 33 |
| ☐ | Questionnaire STAI Y_A | 21 |
| ☐ | Questionnaire MARS | 12 |
| ☐ | Questionnaire MATHYS | 33 |
| ☐ | Questionnaire ALTMAN | 6 |
| ☐ | Questionnaire QIDS-SR16 | 17 |
| ☐ | Questionnaire PSQI | 27 |
| ☐ | Questionnaire EPWORTH | 10 |
| ☐ | Questionnaire EQ5D | 7 |
| ☐ | FAGERSTROM | 7 |
| ☐ | APNEES DU SOMMEIL | 9 |
| ☐ | Questionnaire ASRS | 19 |
| ☐ | Questionnaire AQ12 | 16 |
| ☐ | Questionnaire CTQ | 41 |
| ◐ | Questionnaire BIS10, split into `bis10` (34 items) and `bis12` (12 items) | 43 |
| ☐ | Questionnaire ALS | 25 |
| ☐ | Questionnaire AIM | 21 |
| ☐ | Questionnaire WURS | 26 |
| ☐ | Questionnaire BDHI | 85 |
| ☐ | Questionnaire CSM | 14 |
| ☐ | Inventaire du rythme circadien | 13 |
| ☐ | MDQ | 17 |

### 6. NEUROPSYCHOLOGIE (`neuropsychologie/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Clinical criteria (no header) | 12 |
| ☐ | Troubles des acquisitions et des apprentissages | 10 |
| ☐ | CVLT | 40 |
| ◐ | TMT: `tmt` (times, errors and z-scores; the 7 percentile columns are still to add) | 22 |
| ☐ | Stroop (planches A, B, C, interférence) | 21 |
| ☐ | Fluences verbales | 22 |
| ☐ | CPT II | 55 |
| ☐ | CPT III | 18 |
| ☐ | Mémoire spatiale | 57 |
| ☐ | COBRA | 17 |
| ☐ | SCIP | 12 |
| ☐ | Test des commissions | 18 |
| ◐ | Similitudes: `wais4_similitudes` | 22 |
| ◐ | Vocabulaire, split into `wais3_vocabulaire` and `wais4_vocabulaire` | 37 |
| ◐ | Matrices, split into `wais3_matrices` and `wais4_matrices` | 30 |
| ◐ | Code, Symboles & IVT, split into `wais3_code_symboles_ivt` and `wais4_code_symboles_ivt` | 14 |
| ◐ | Mémoire des chiffres, split into `wais3_memoire_chiffres` and `wais4_memoire_chiffres` (summary scores; trial-level columns to add) | 85 |

### 7. Mostly categorical tabs

| State | Tab (`folder/`) | Section | Variables |
|---|---|---|---|
| ☐ | SUICIDE (`suicide/`) | Intentionnalité suicidaire actuelle | 10 |
| ☐ | | Histoire des conduites suicidaires | 7 |
| ☐ | | Columbia TS la plus violente | 10 |
| ☐ | | Columbia TS la plus grave | 8 |
| ☐ | | C-SSRS Idéation suicidaire | 11 |
| ☐ | SUBSTANCES ET COMORBIDITE (`substances_et_comorbidite/`) | Tabac (no header) | 4 |
| ☐ | | Troubles anxieux | 37 |
| ☐ | | Troubles liés à une substance au cours de la vie | 42 |
| ☐ | | Trouble du comportement alimentaire | 4 |
| ☐ | | Trouble somatoforme | 4 |
| ☐ | PERINATALITE (`perinatalite/`) | (no header) | 11 |
| ☐ | EVALUATION MEDICALE (`evaluation_medicale/`) | Premier épisode | 5 |
| ☐ | | Trouble vie entière | 20 |
| ◐ | | Depuis la dernière visite, split into `dsm4_depuis_derniere_visite` and `dsm5_depuis_derniere_visite` (the 12 follow-up columns; 3 hold lifetime answers and go with Trouble vie entière) | 15 |
| ☐ | | Année écoulée | 15 |
| ☐ | | Trouble psychotique | 4 |
| ☐ | | Episode le plus récent | 8 |
| ☐ | | Trouble de l'humeur actuel | 9 |
| ☐ | | DIVA (critères DSM-IV TR) | 40 |
| ☐ | | New Columns | 3 |
| ☐ | SOIN SUIVI HOSP ARRET TRAVAIL (`soin_suivi_hosp_arret_travail/`) | Hospitalisation | 6 |
| ☐ | | Arrêt de travail | 8 |
| ☐ | | Recours aux soins | 24 |
| ☐ | | Suivi des recommandations | 4 |
| ☐ | SOCIAL (`social/`) | (no header) | 20 |

### 8. TRAITEMENTS (`traitements/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Médicament lifetime | 18 |
| ☐ | Traitement non pharmacologique lifetime | 27 |
| ☐ | Traitement non pharmacologique semestriel | 25 |
| ☐ | Traitements psychotropes | 8 |

### 9. ANTECEDENTS (`antecedents/`)

| State | Section | Variables |
|---|---|---|
| ☐ | Pathologies neurologiques | 21 |
| ☐ | Pathologies cardio-vasculaires | 17 |
| ☐ | Pathologies endocriniennes et métaboliques | 20 |
| ☐ | Pathologies dermatologiques | 29 |
| ☐ | Pathologies des voies urinaires | 13 |
| ☐ | Antécédents gynécologiques | 11 |
| ☐ | Pathologies hépato-gastro-entérologiques | 16 |
| ☐ | Pathologies allergiques et inflammatoires | 21 |
| ☐ | Autres pathologies | 33 |
| ☐ | Family structure: enfants, fratrie, parents, grands-parents | 118 |
| ☐ | Family history: filles, fils, sœurs, frères | 200 |
| ☐ | Family history: mère, père, grands-parents | 60 |
