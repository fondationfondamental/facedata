# FACE SZ — progress, decisions and open questions

Extraction: `SZALL_20261113.tsv` (6,616 rows × 1,720 columns, 2,353 patients); before it,
`SZALL_20261030.tsv` (6,569 rows × 1,721 columns, 2,336 patients). See D1.
Dictionary: `FACESZ_thesaurus_V4.20.xlsx`.

The architecture and the schema fields are those of FACE BP
([ARCHITECTURE.md](../ARCHITECTURE.md), [SCHEMA_SPEC.md](../SCHEMA_SPEC.md)). The
decisions of [the BP file](../bp/PROGRESS.md) are quoted as "BP D9"; the answers that
the data managers gave for BP are in [the BP questions](../bp/QUESTIONS.md).

## Stages

| Stage | Content | State |
|---|---|---|
| 0 | The module `facedata.sz` with no schema, this file, the tests, the comparison of the two extractions and the scan of the columns | Done on 2026-11-13 |
| 1 | SZ tab by tab, in the order of the checklist below, each tab finished before the next | Written on 2026-11-13, waiting for review: the 14 tabs, 125 schema files, 127 instruments, 1,963 variables. 1,668 columns read and 52 ignored of 1,720: no column is left unassigned |
| 2 | Closing: no column left unassigned, `QUESTIONS.md` for the EMR developers, the data managers and the PI | Done on 2026-11-13 (D21). The schemas are drafts until the questions are answered and the project lead has reviewed them |
| 3 | A review of the database for the project lead and the data managers, and a tutorial notebook | Done on 2026-11-14 (D23, D24): `reports/executive/FACE-SZ-database-review.html` (not in git) and `schizophrenia-tutorial.ipynb` |

## Decisions taken

| # | Date | Decision |
|---|---|---|
| D1 | 2026-11-13 | Extraction. `SZALL_20261113.tsv` is the file: 6,616 rows (no duplicated row), 1,720 columns, 2,353 patients, 12 centres, visits from 2010 to 2026. The data managers ran it again after correcting their cleaning step, which lost every answer whose text holds an apostrophe (BP D63, BP D74). Compared cell by cell with the file of 30 October: the column `rad_tb_subst_raw` is gone; 18 patients are new and 1 is gone, 49 rows are new and 2 are gone; the eight Birchwood items are now filled (3,302 to 3,706 cells each), a physical-activity item (`ipa0106c`, 2,798), Fagerström item 3 and its total (692 and 683) and nine SOGS items (16 to 121). `lost_to_followup_stopsuivi` and `causedec_stopsuivi` are filled on 34 and 27 more rows. The other differences are a few rows of treatments and biology, the live database |
| D2 | 2026-11-13 | Method. The module mirrors `facedata.bp`: `sz.load`, `sz.report`, `sz.coverage`, schemas in `facedata/sz/schemas/<tab>/`, ignored columns in `facedata/sz/ignored.yaml`. The dictionary is walked tab by tab, section by section. An instrument that BP also has starts as a copy of the BP schema and keeps its name, its output columns and its scoring key, so that the tables of the two cohorts can be put together; the copy is then checked on the SZ data like any other schema. `tests/test_cohorts.py` compares the schemas of the same name in the two cohorts (`defaults`, `variables`, `scores`, `version`), and a difference must be listed with its reason in `facedata/sz/differences.yaml`. The generic code changes only when a tab needs a rule that the schema fields cannot say, and `SCHEMA_SPEC.md` changes first |
| D3 | 2026-11-13 | The kinds of errors found in BP are looked for in every section (the list is under "Findings" below). Before any schema, every column was scanned for a change over the years in when it is filled, in the level and range of its values, in the share of non-numeric values and in its set of codes (the scan of BP, "Instrument changes"). The result is under "Instrument changes found in the extraction" |
| D4 | 2026-11-13 | PATIENT. Five schemas with the names and the output columns of BP: `identite`, `inclusion`, `provenance`, `fin_de_suivi`, `visit_record`. No value changes between the visits of a patient, and nothing is unparsed or out of range. (1) The diagnosis has three values: schizophrenia (1,797 patients), schizoaffective (513), schizophreniform (43). (2) `inclusion` has the non-opposition form only: `social_protec` is not in the extraction. (3) `provenance` reads the same questions under other column names (`adresseur_autres`, `dsstdtc`, `connaissance_autre`); the date at which the information was collected is not in the extraction. (4) `fin_de_suivi`: three columns, none in the dictionary. The column named for the cause of death, `causedec_stopsuivi`, holds dates: the empty date for about a thousand patients and a real date for 8, all among the 12 patients recorded as deceased. The export filled it from the date of death, the kind of error found in BP for `mere_dthfl` (BP D70); it is delivered as `death_date`, and the cause of death is not in the extraction. (5) Ignored: eleven `siteid_<tab>` columns, copies of `siteid` written without its leading zero, and at first `subjid`, delivered as `fondacode` since D9. All 35 columns of the tab are covered (24) or ignored (11) |
| D5 | 2026-11-13 | HETERO-QUESTIONNAIRE. Ten schemas: `aims`, `barnes`, `bars`, `calgary`, `cgi_egf`, `panss`, `sumd`, `ymrs`, `extrapyramidal`, `psp`; `ymrs` is the BP schema and `cgi_egf` the BP schema under the SZ column names. Every stored score was compared with its items, in every year. (1) PANSS: the three scales and the total are exactly the sums of their items (4,646 to 4,670 visits). The fifteen five-factor scores were fitted on the 30 items: all are plain sums, exact on the 4,646 complete visits; they are recomputed, compared, and labelled with their items. Two do not follow their publication (O5). (2) Calgary: `calgar08` is a copy of `calgar07` on every row, and the stored total is the sum of the nine columns as extracted, so it counts item 7 twice and holds no item 8, the suicide item. The column behaves like item 7: its closest neighbours are the sleep questions of the PSQI, not the suicide questions. The eight items that exist are delivered with their sum, `calgary_sum8` (0 to 24), which is not the CDSS total; `calgar08` and `calgar` are ignored (O4). (3) Barnes: the stored sum is the sum of the three items (3 `score_mismatch`); the "total score" `bars0106` is the global item again and is ignored. (4) BARS: the percentage is the clinician's estimate, not a formula, and is delivered as stored; 250 numbers of doses per day above 20 are `out_of_range`, two thirds of them from one centre. (5) SUMD: 0 means "cannot be rated" and is a missing code (a third to a half of the visits for each symptom); the three stored scores are the three general items again and are ignored; the twelve symptom columns are not in the dictionary. (6) Extrapyramidal scale: the stored score is the mean of the ten items rounded to one decimal (10 `score_mismatch`). (7) PSP: the ten-point band is the band of the score on 3,047 of 3,262 visits; a new custom check, `psp_band_differs`, flags the 215 others (`check_failed`). (8) AIMS: no stored score; `aims_movements` is the sum of the seven movement items. (9) CGI: the efficacy index follows its formula on 2,644 of 2,676 rows (32 `check_failed`). The scan's lead on lost answers is closed for AIMS, PANSS and YMRS: every level occurs, the highest ones rarely. All 134 columns of the tab are covered (128) or ignored (6) |
| D6 | 2026-11-13 | CONSTANTES et ECG. Three schemas with the BP names: `parametres_physiques` (the BP schema as it is), `pression_arterielle` (the two lying pressures; no standing pressure, no heart rate) and `ecg` (the stored QTc only: the QT and RR from which BP recomputes it are not extracted). The typing errors of BP are almost absent: no height in millimetres, no weight with a lost decimal point, one diastolic pressure in cmHg, one QTc in milliseconds. Out of range: 3 heights, 1 weight, 9 waists, 27 QTc (the absurd values that the EMR computes when QT and RR are not on the same scale, as in BP). The body mass index recomputed from weight and height equals the stored one on every visit. All 7 columns of the tab are covered |
| D7 | 2026-11-13 | BILAN BIOLOGIQUE. Seven schemas. Five have the BP names and read the BP definitions of the analytes (units, expected sizes, limits) in the SZ columns, which are named for the analyte (`gluc`, not `gluc_lbstresc`): `biochimie` (uric acid, CRP, glucose, HbA1c), `bilan_lipidique`, `nfs` (seven values), `bhcg_prolactine` (prolactin) and `dosage_psychotropes` (clozapine). Two are new: `vitamine_d` and `toxoplasmose`. The errors of BP are all there, at lower rates: the unit column holds the form's default label, also on 400 to 930 visits with no result; results on another scale under that label (haemoglobin in g/L on 32 visits, glucose in g/L on 17, neutrophils as a percentage on 20, counts per mm3, clozapine in mg/L on 11); prolactin with no chosen unit, read with the BP rule (633 converted from mUI/L, 139 `unit_inferred`, 162 `unit_unknown`, 36 `unit_doubt`). The stored cholesterol ratio is not the ratio of the stored values on 157 visits (4%), more and more often since 2019; part of them look typed by hand. The recomputed ratio is delivered. Vitamin D has no unit and may be on two scales (O7). The toxoplasmosis IgG titre has a median that goes from 14 to 137 between centres: the assays differ, and titres of two centres should not be compared. All 45 columns of the tab are covered (43) or ignored (2) |
| D8 | 2026-11-13 | AUTO-QUESTIONNAIRE. Twenty-one schemas, 475 variables. (1) Five are BP schemas: `ctq`, `eq5d` and `fagerstrom` as they are; `psqi` with six more questions about the bed partner; `mars` with item 10 in the column `mars010` and without the question on current medication. Their stored scores follow the BP formulas (MARS: fitted again, same key). (2) `wurs`: 25 items and their sum under names of its own, because nothing tells the 61-item from the 25-item form here (O9). (3) Lost answers: items 17 and 18 of the S-QoL hold only the answers 2, 4 and 5, in every year; 1 and 3 are not in the extraction, although the stored dimension exists on 782 visits where item 17 is empty (O8). The two items are delivered as extracted, the stored dimension as it is, and the index is computed with it. (4) New scoring keys, each fitted on the items and compared with the stored score: Birchwood (awareness of symptoms = items 1 + 8; of illness = item 7 + item 2 reversed; need for treatment = items 4, 5 and items 3, 6 reversed, halved), S-QoL (a dimension is (mean - 1) x 25, the index the mean of the eight), STORI (each stage is the sum of every fifth item), EPHP (sums of items 1 to 4, 5 to 8, 9 to 11, 12 and 13; 7 means "cannot be assessed" and is a missing code), Yale-Brown (two sums of five items). (5) A new score field, `scale: [factor, offset]`, applied to a sum or a mean: the S-QoL dimensions and the halved Birchwood score need it (SCHEMA_SPEC, section 8; 10 lines of generic code). (6) Delivered as typed, with impossible numbers out of range: `presenteeism` (13), `physical_activity` (4; hours and minutes are two fields that patients fill in three ways). (7) `sogs`: the total as stored, on 122 visits. (8) Seven schemas `dsm5_<substance>` with the same 24 variables: twelve criteria, ever and in the last 12 months (`asked_if`), 2 = "do not know" a missing code. (9) Ignored: `ctq41` ("denial score above 0"), `psqi15` and `psqi16` (copies of items), ten Yale-Brown "level" columns (O10). The scan's lead on lost answers is closed for the CTQ and confirmed for the S-QoL. All 488 columns of the tab are covered (475) or ignored (13) |
| D9 | 2026-11-13 | The tables of the two cohorts can be put together (was O3; decided by the project lead, for transdiagnostic research; BP D76). (1) Every table gets a first column `cohort` (`sz`). A `usubjid` is a number given inside a cohort: 824 numbers are used in both FACE BP and FACE SZ, for different patients; the key across cohorts is (`cohort`, `usubjid`, `visit`). (2) `patients` delivers `fondacode` (the column `subjid`), the patient code of the foundation, unique across the two cohorts and stable from one extraction to the next; no fondacode is in both cohorts. `subjid` leaves `ignored.yaml`. (3) Shared instruments keep the BP names: the PATIENT schemas, `cgi_egf`, `ymrs`, the biology, `ctq`, `eq5d`, `fagerstrom`, `psqi` and `mars` deliver the BP columns. One exception: `wurs`, whose form is not known (O9), keeps names of its own until it is |
| D10 | 2026-11-13 | PANSS five-factor scores: three stored scores sum a wrong item and are corrected (asked by the project lead; was the first half of O5). The stored formulas were fitted on the 30 items (D5), then compared with the publications. (1) Wallwork 2012, positive factor: the table of the paper gives P1, P3, P5, G9; the stored score is P1 + P3 + P5 + N2. G9 is the 23rd of the 30 items and the formula takes the 9th. The two differ on 3,282 of 4,667 visits. (2) Wallwork 2012, negative factor: published N1, N2, N3, N4, N6, G7; stored with N5 in place of N6 (2,973 of 4,656 visits differ). With these two slips the stored model has 18 items, two of them twice; the paper has 20, each in one factor. (3) Lançon 1998, negative factor: stored N1, N2, N3, N4, N6, N7, G16. The abstract of the paper says that six items, N7 among them, were left out of the analysis, which kept 24. The stored formulas use 24 items, each once: the 23 others that the paper kept, and N7; the one kept item they do not use is G7. So the published factor has G7 where the formula has N7 (2,830 of 4,660 visits differ). This one rests on the abstract and on the number of items per factor given by later papers of the same group, not on the table of the 1998 paper, which could not be read. (4) Cause: three single wrong item references in formulas. A program computes these scores: they are exact sums on every visit since 2010, older than the Wallwork paper, and exist exactly where the items of the stored formula are filled (on 6 visits the positive factor is stored although G9 is empty). Whether the program is the EMR or the score step of the data managers is for them to say; either way the stored columns are wrong. (5) What the package does: the three scores delivered follow the publication; for each, a second score that is not delivered repeats the stored formula and is compared with the stored column, so that a correction upstream will show (no mismatch today). (6) Sums are delivered for the three models; the Wallwork paper reports the mean of the items, which is the sum divided by their number. (7) The van der Gaag scores are not slips but a shorter version of the published formula, and stay as stored (the new O5). Sources: the Wallwork paper and its table, doi 10.1016/j.schres.2012.01.031; Lançon et al. 1998, abstract, doi 10.1111/j.1600-0447.1998.tb10101.x; the van der Gaag formula as quoted by two later papers, doi 10.1007/s10548-018-0677-0 and 10.3390/genes16091092 (the 2006 paper itself, doi 10.1016/j.schres.2006.03.021, could not be read) |
| D11 | 2026-11-13 | NEUROPSYCHOLOGIE, first part: eight schemas with BP names, each read against the SZ dictionary and data. (1) `neuropsy_conditions`: the form is filled from 2010 to 2016 only (781 visits). Two columns hold other questions than in BP and get names of their own (`neuropsy_state_compatible`, `neuropsy_no_ect_6_months`); three questions exist here only. (2) `tmt`: the BP schema, with the two times read in `tmt0101_` and `tmt0102_`. One centre wrote five z-scores with the opposite sign in 2011 and 2012 (23 visits each, flipped); afterwards the rank correlation between a time and its z-score is -0.93 to -0.97 every year. "DCM" is a missing code of this cohort. The four error percentile columns are ignored, as in BP (three rules over the years). The error bands are read again in the norm tables, which need the years of education: about 750 visits have a band and about 2,300 per band get `norm_missing`, because the education is recorded until 2015 only (O11). (3) `errands_test` and `verbal_fluency`: the BP schemas without the columns that SZ does not hold; no stored score disagrees. (4) `wais3_matrices` is the BP schema (4 `score_mismatch`). `wais4_matrices`: on the WAIS-IV visits the columns of items 25 and 26 are copies of item 24, on every visit of every year, while the stored total is the true total (it exceeds the sum of items 1 to 23 by up to 3). The two items are not delivered and the total is delivered as stored (O12). This is what gave 636 mismatches with the BP schema. (5) `wais3_memoire_chiffres` and `wais4_memoire_chiffres`: the summary scores only (the items are not extracted). Unlike BP, the WAIS-IV columns are not shifted against their labels: the raw total is in `nbrut_w` and equals forward + backward + sequencing on all 2,494 visits. The same output names as BP are therefore read in other columns. 32 WAIS-III visits hold a sequencing score, which only the WAIS-IV has: 30 `score_mismatch` on the total. The rest of the tab is D12 to D15 |
| D12 | 2026-11-13 | WAIS-IV: two stored indices are wrong by a constant and are corrected (the rule the project lead gave for the PANSS: a wrong computation that the data confirm is corrected, D10). The stored working memory index (`imt02_wais4`) always ends in .3 and the stored full-scale IQ (`ei23_wais4`) in .1, while an index is a whole number. Three facts, true on every visit, in every year and in each of the 10 centres: (1) at the centre of the sum of scaled scores, where every index is 100, the two are 99.3 and 97.1; (2) their percentile ranks are those of the normal curve for the stored value plus 0.7 and plus 2.9, exactly as the percentile ranks of the verbal comprehension, perceptual reasoning and processing speed indices are for their stored value; (3) the Barona difference of the same visit is the expected IQ minus the stored IQ plus 2.9 (292 of 293 visits): the EMR itself used the right IQ. `wais4_imt_index` is the stored value plus 0.7 (447 visits) and `wais4_qit` the stored value plus 2.9 (430), written with `scale` on a score; the stored values are read and not delivered. Why the two are stored too low is O15 |
| D13 | 2026-11-13 | Barona estimate: the occupation is not reliable, and the expected IQs that use it are flagged. The form lists seven occupations and seven diplomas. On 1,111 of the 1,546 visits that have both (72%; 15% if the two were independent) the occupation holds the same place in its list as the diploma: 221 of 225 farmers have a CAP or BEP, 218 of 237 retired patients a general baccalauréat, in a cohort whose median age is about 30. In every year and every centre (27% to 91% of the visits). The diploma agrees with `edulevel` of the patient tab, so it is the answer, and the occupation is on most of these visits a copy of its place in the list: a column filled from another field, as `mere_dthfl` was in BP. The expected IQ depends on the occupation (among visits with the same diploma, age and sex, it changes with the occupation in all 72 groups that have two), so it carries the error. A copy cannot be told from a true coincidence (a higher professional with a university degree): on these visits the occupation, the three expected IQs and the three differences keep their value and get `check_failed` (`barona_occupation_follows_diploma` in `facedata/custom.py`). O17, to send first |
| D14 | 2026-11-13 | NEUROPSYCHOLOGIE, second part: 22 schemas. (1) `cvlt`: the BP schema with ten raw scores in columns named `avl01...` and two standardised columns per mixed measure (`cvltNNz_`, `cvltNNp_`), each variable reading both. The z-score of trials 1 to 5 is wrong from 2022 to mid-2025 (median -1.5 until 2021, 0.8 in 2022, 4.0 in 2023, 5.3 in 2024, -1.2 again from the third quarter of 2025, while the raw total does not move; twelve centres; BP does not show it): 240 are out of range, the 260 others of the period and their bands get `period_doubt` (O13). "xxx", "DCM" and "NF" are missing codes. (2) Eleven WAIS subtest schemas, one per edition: similarities, picture completion, arithmetic, information, letter-number sequencing (WAIS-III only) and coding, with BP names where BP has the subtest. Totals are recomputed from the items with `min_items: 1`, because the items after the stopping rule are empty: `wais3_simil_total` 570 visits (12 mismatches), `wais3_pc_total` 571 (1), `wais3_arith_total` 558 (1), `wais3_info_total` 564 (0), `wais3_lns_total` 477 (0), `wais4_arith_total` 464 (0), `wais4_pc_total` 465 (0), `wais4_info_total` 466 (6). WAIS-IV similarities: the columns of items 10 and 11 hold the same value on every WAIS-IV visit, so one item is lost; items 1 to 9 and 12 to 18 are delivered and the total as stored (1,865 visits; added to O12). The scaled score as a z-score is (scaled score - 10) / 3 everywhere. (3) `wais3_efficience` and `wais4_efficience`, the IQs and indices that the EMR estimated from seven subtests. The dictionary gives no formula; the sums of scaled scores are those of a seven-subtest short form on every visit that has the scaled scores (WAIS-III verbal = 2 x similarities + 2 x information + arithmetic + digit span, performance = 2 x picture completion + 2 x matrices + coding; WAIS-IV verbal comprehension = 1.5 x (similarities + information), perceptual reasoning = 1.5 x (matrices + picture completion), full scale = 10/7 x the seven subtests), and the percentile ranks are those of the normal curve. The scaled scores are in other schemas, so the sums are delivered as stored and `tests/test_real_data_sz.py` checks the formulas. From 2019 the WAIS-IV battery keeps three subtests and the only estimate is a two-subtest IQ (`wais4_qi_two_subtests`, 537 visits). The WAIS-III estimated full-scale IQ is not in the extraction (O14). (4) `barona` (D13). (5) Seven tests that BP does not have. `sstics`: 21 items, the six factor scores and the total of the publication, recomputed (2,338 totals, 2 mismatches); the z-score as stored. `lis` (six films): 30 ratings and the score as stored; one set of 30 reference ratings gives the stored score on 983 of 1,011 visits, which confirms the published rule, but the reference ratings are not copied into the repository (O18). `fnart`: total recomputed (684, no mismatch), three IQs as stored, each an exact straight line of the total. `cpt_ip`: counts and d-prime as typed, the mean d-prime recomputed (999, no mismatch), the hand-typed percentile with its bands read as their middle. `six_elements`: three sums recomputed (points, rule breaks, total error score) and five z-scores as stored, four of which the dictionary does not label; 83 times written in words are `unparsed`. `doors_test`: total recomputed (771); the percentile of part B is "<1" on 172 visits where part B is empty, an EMR computation on an empty cell, flagged `derived_doubt`. `laterality`: the quotient recomputed on the ten activities of the inventory (502); one centre computed it on the 12 lines (41 `score_mismatch`), so the delivered quotient is on one scale. Every column of the tab is now read or ignored: 659 variables in 30 instruments |
| D15 | 2026-11-13 | Two small changes of the generic code, written in `docs/SCHEMA_SPEC.md` first. (1) A custom check never flags an empty cell (section 10), so that one function can be named for several variables that depend on the same fact: the Barona check is named for seven variables. No BP number changes. (2) `derived_from` may name a variable, not only a score that has `compare` (section 8): the derived value is flagged `derived_doubt` where that variable is empty. It says in the schema what the CVLT recency needed a custom function for in BP; the doors test is the second instrument with the case, and the spec asks for a field then. The BP CVLT keeps its function for now, so that its flags do not change code |
| D16 | 2026-11-13 | SUICIDE: the three BP schemas. The two forms in the same columns are confirmed on the SZ data: at inclusion the five questions are about the whole life (64% yes to the first, 30% have attempted suicide), at follow-up about the time since the last visit (31% and 2%; 631 of the 665 later answers of patients who said yes at inclusion are no), and the "when" lists differ. `isf_lifetime` and `suicide_attempts` are the BP schemas unchanged. `isf_since_visit` drops the doubtful period of BP: the share of follow-up visits with an attempt stays between 0% and 8% in every year (4 of 210 in 2022, 5 of 182 in 2023), where BP rises to 16%. The date of the first attempt holds 114 placeholders (1000-01-01), none of the 2011-11-11 of BP |
| D17 | 2026-11-13 | SUBSTANCES ET COMORBIDITE: eleven schemas. (1) `anxiety_v0`: another form than BP. From 2012 each disorder comes after a screening question, in columns that the dictionary does not list (`rad_attaq_paniq`, `rad_peur_*`, `rad_trouble_compulsif`); the data show the tree (a disorder is filled only after a yes to its screening question, on 95% to 99% of the cells). A question that the form did not show after a "no" is delivered as 0 (`asked_if`, chained: no anxiety disorder, then no screening symptom, then no disorder). One answer is lost: the box "panic disorder with agoraphobia" holds the screening answer on all its 634 rows (O19). `anxiety_fu` holds the first question only. (2) `eating_disorder_v0` is the BP schema; no follow-up answers. (3) `substance_v0` and `substance_fu`: the two periods of BP are confirmed (of the patients with an alcohol disorder at inclusion, 147 of 319 later answers are no: the follow-up question is about the time since the last visit). At inclusion the first question holds "Ne sais pas" on 975 of 1,583 visits and "Non" on 18: "Ne sais pas" stands where "no" is expected, since every substance box of these visits says no (O20). It is read as a missing code and nothing is guessed; the boxes are complete. No type of disorder and no duration in SZ. (4) `tobacco`: the BP schema and five more questions. (5) The consumption modules, which BP does not have: `alcohol_use`, `cannabis_use`, `drug_use` (one opening question, `rad_add_4`, then sedatives, heroin, cocaine, opiates and other products) and `tea_coffee`. Their "whole life" questions keep that meaning at follow-up (75% have ever drunk alcohol at inclusion, 73% at follow-up), so there is one column per question, not two. 999 and 9999 are "does not know"; the ways of use and the lists of several boxes are one yes/no per box. (6) `depressive_episodes`, asked at inclusion. Five columns are ignored: two copies, the list `chk_substances_type` (contained in the boxes), and two questions that the dictionary does not have |
| D18 | 2026-11-13 | PERINATALITE, EVALUATION MEDICALE, SOIN SUIVI HOSP ARRET TRAVAIL, SOCIAL - PERINATALITE: ten schemas. `perinatal`, `recommendations` and `social` are the BP schemas with the columns that SZ holds and the questions it adds; `hospitalisations_v0`, `sick_leave_v0` and `sick_leave_fu` keep the BP names where the question is the same but read other columns, and `hospitalisations_12m` is asked at every visit. Three instruments exist in SZ only: `psychosis_course` (ages at the first episode and at the first treatment, untreated psychosis, number of episodes, course, episode and attempt of the past year), `lifetime_symptoms` (22 symptoms, ever and in the last month) and `violent_behaviours` (four kinds, with their details). Social: the way of living is read in the column `vie`, which holds the list that BP has in `lvsbjind`. Lost answers: the marital status never holds "married or living as a couple", the source of income never holds "salary" or "disability pension" (O22); the work status and the source of income are empty from mid-2015 to 2018 (O23). "Arme à feu" is written "Arme ? feu": an accented letter lost by the export. Marks such as ">20" are read as censored values; "Pas d'hospitalisations", "Jamais travaillé", "Non applicable" and 999 are missing codes |
| D19 | 2026-11-13 | TRAITEMENTS: five schemas. (1) `medications`, the BP schema: the lists of the 11 medication columns are the same on every row of a patient (1,975 patients, 11,038 medications), the patient's whole history, opened into the table `treatments`; the columns `on_*` say what a patient takes at each visit, with four molecules more than BP (clozapine, amisulpride, haloperidol, paliperidone). The table of names is now shared by the cohorts: `facedata/medications.csv`, found in the cohort folder or else in the package folder (SCHEMA_SPEC section 15, changed first; BP D77). 97% of the SZ names were in the table written for BP; 27 names were added, and 158 medications keep an unknown name. The SZ extraction also gives the ATC code of the EMR's own drug list for 3,331 medications: it equals the code of the table on 3,305 of the 3,313 that have both, a first check of a table that a pharmacist has still to read. No total daily dose in SZ; the interval in weeks of the long-acting forms is added. (2) `medication_classes`: the six counts that the export computes (antipsychotics, antidepressants, anxiolytics, anticholinergic correctors, mood stabilisers, hypnotics) are delivered once per patient. The dictionary calls them "at the time of the visit", but each is the same on every row of a patient: it counts the whole list (O25). The six yes/no columns of the same classes are ignored: 1 where the count is above 0, and 0 on the rows without a list, where nothing is known. (3) `treatment_help`, `non_drug_fu` (the BP names for the questions that BP has, in columns without `_sem`; four treatments that BP does not ask) and `care_changes`; lists of several boxes are one yes/no per box |
| D20 | 2026-11-13 | ANTECEDENTS: twenty schemas. (1) Medical history: nine body systems, each in an inclusion and a follow-up schema (`neurological_history_v0`, `_fu`, and so on; `autoimmune_history` exists in SZ only). The two forms of BP are confirmed: at follow-up a disease answered yes at inclusion is most often answered no (39 of 47 for a head injury, 43 of 54 for acne), so the follow-up form seems to ask about the time since the last visit (BP O38 holds here too). The SZ form is shorter than the BP one: one question "treated" per disease, no date of onset, no "controlled"; the BP names are kept where the question is the same. The section is answered at 85% to 95% of the inclusion visits in every year: the fall that BP shows from 2022 (BP O37) is not seen. (Corrected on 2026-11-14 by D23: this holds for five sections; the digestive, autoimmune and other diseases do fall in 2022, O26.) The two migraine columns are swapped: `migraine_mhdecod`, named for "treated", holds the answer of every patient, and `migraine_mhoccur` is filled only after a yes; they are read the other way round (O24). Asthma and allergy are read in the list `chk_somat_all_specifier`, as in BP; the two columns that repeat its boxes are ignored. (2) `family_structure` and `family_history` are the BP schemas without the grandparents and with the two questions that the SZ form asks per relative (disorder, suicide): 1,887 relatives of 1,200 patients in the table `relatives`, and five columns `fdr_*` in the table `patients` |
| D21 | 2026-11-13 | Stage 1 is complete and stage 2 is closed. Every column of the extraction is read by a schema (1,668) or listed in `facedata/sz/ignored.yaml` with its reason (52): copies of another column, values that the export computes and that add nothing, questions that the dictionary does not have, and four TMT percentile columns that hold several rules, as in BP. 127 instruments, 1,963 variables, five tables (`data` 6,616 visits, `patients` 2,353, `treatments` 11,038, `relatives` 1,887, `flags`). In the whole file 159 cells have an unknown code (158 medication names) and 351 could not be parsed, each explained in the notes of its schema. `docs/sz/QUESTIONS.md` holds the questions for the EMR developers, the data managers and the PI. The generic code grew by about 30 lines for the whole cohort (`scale`, the cohort column, checks on filled cells, `derived_from` a variable, the shared names table): 2,768 lines |
| D22 | 2026-11-14 | The project lead agreed to the corrections and readings that were waiting for an answer (PI-2 and PI-4 of QUESTIONS.md): the three PANSS factor scores (D10), the WAIS-IV working memory index and full-scale IQ (D12), the laterality quotient on ten activities (D14), the two migraine columns read the other way round (D20), and the 0 delivered where the form did not ask a question after a "no" (D17). They follow the rules already applied to FACE BP: a score or a sub-score that is proven wrong is delivered corrected, and the stored value is kept as a check; a value given as "less than" or "more than" keeps its mark; two editions or two forms are never delivered in one column. So that each case can be found as in the BP file, the section "Instrument changes found in the extraction" now lists every case with its handling and its state |
| D23 | 2026-11-14 | A review of the database for the project lead and the data managers, in the form of the BP one: `reports/executive/FACE-SZ-database-review.html` (not in git; `aggregate.py`, `charts.py` and `build.py` in `reports/executive/sz/` build it again; counts only). Its grids by year and by centre showed four things that the tab-by-tab work had missed. (1) Three sections of the medical history are mostly empty since 2022. The digestive section is answered at 83% of the inclusion visits of 2016 to 2021 and at 42% of those of 2022 to 2026, the other diseases at 82% and 46%, the autoimmune diseases at 81% and 32%; the neurological, cardiovascular, endocrine, skin and allergic sections stay at 85% to 88%. The share of all inclusions with a digestive disease does not change (17%), so it is the "no" that are no longer written, and among the answered sections the share doubles (21% to 40%): the pattern of BP O37, for three sections here. 288 of the 609 inclusions since 2022 hold none of the three. This corrects D20, which said that the fall of BP was not seen: true of five sections, not of these three (O26). (2) Migraine is answered "yes" by 10% to 15% of the patients until 2017 and by 4% to 7% since 2018, while no other neurological disease moves (O27). (3) The two-subtest IQ of the WAIS-IV is stored for 41% to 68% of the inclusions of 2019 to 2021 and for 10% to 28% since 2022, while its subtests are done at 67% to 81% of them (O28). (4) All 79 `score_mismatch` of the three Yale-Brown sums are on visits of 2015 and 2016 (added to O10). Also measured for the review: 46% of the patients are seen at one year, 25% at three years and 12% at four; the whole neuropsychological battery is done at inclusion, at three years and at five years, and only the TMT, the digit span and the SSTICS at one year; 1,675 patients have a screening record, which holds an EQ-5D only |
| D24 | 2026-11-14 | A tutorial notebook, `schizophrenia-tutorial.ipynb`, the SZ twin of `bipolar-tutorial.ipynb` (BP D61), for people who have never used the cohort and do not code much: the six tables, how to find a variable and read its notes, rating scales, lab results, neuropsychology with its two editions and its two batteries, treatments, history, a few patients and the whole cohort over time, the flags, twelve traps of this cohort (among them the scores that were corrected and the answers that the export loses), a first table saved in `data/exports/`. Its last section loads nine instruments that both cohorts have from the two extractions, stacks the tables with `pd.concat`, explains the key (`cohort` with `usubjid`; `fondacode` across cohorts), compares the cohorts at inclusion and over time, and reads `facedata/sz/differences.yaml`. Every cell was run on the two extractions; the notebook is saved without results, and `tests/test_notebook.py` checks it |
| D25 | 2026-11-14 | Audit of the package (BP D79 for the generic changes). In SZ: (1) 2,723 stored scores had no recomputed score and no flag; they are now `score_not_recomputed`. The largest is the S-QoL index: 1,194 of its 4,227 stored values (28%), with a lower stored mean (48.8) than the delivered ones (56.9) (O29). (2) The TMT z-scores of one centre are no longer flipped: its 23 early visits correlate 0.24 the wrong way, a mixture of the two conventions; the 115 scores are kept as written with `sign_doubt`. (3) The answers about the birth are per patient, as in BP (`level: patient`; 39 `patient_value_varies`). (4) `vitamin_d` is renamed `vitamin_d_as_written`: it has no unit and must not stack with the nmol/L of DR and ASP (O30). (5) `psqi10e_text`: the free text of SZ is not the 0-to-3 answer that DR and ASP call `psqi10e`. (6) The labels of the PANSS factors called van der Gaag say that they are the shortened sums of the EMR. (7) 43 mismatches of check scores are filed under the stored value. |
| D26 | 2026-11-14 | YMRS: three items delivered in points, and the published total (found while the common instruments of the four cohorts were compared, BP D80). Items 5, 6, 8 and 9 of the YMRS count double (0, 2, 4, 6, 8). In this extraction items 5, 8 and 9 hold 0, 1, 2, 3 or 4: never a value above 4, and an odd value on 80%, 56% and 96% of the visits where the item is not 0, in every year from 2010 to 2026 and in each of the 12 centres; item 6 holds 0, 2, 4, 6 or 8. In BP and DR the four items never hold an odd value (17,246 and 1,033 visits). The SZ form therefore stores the level of the three items, and the stored total, which adds the eleven columns, counts them once. `ymrs05`, `ymrs08` and `ymrs09` are now delivered in points (twice the level) and `ymrs_total` is the published sum; the stored total is not delivered and is reproduced by the twin `ymrs_total_as_stored` on all its 4,538 visits. The delivered total is higher than the stored one on 776 visits (17%), by 2.1 points on average and 9 at most; at inclusion its mean is 2.25 against 1.86, and 81 patients reach 12 or more against 51. `ymrs` is now listed in `differences.yaml`. A YMRS total of SZ computed before this date is not comparable with BP and DR. |
| D27 | 2026-11-16 | Slide deck for the Expert Centres (BP D81: one method for the four cohorts, a tab measured on its routine instruments; `reports/slides/`, not in git). In SZ: 71 of the 81 instruments in use since 2022 count as routine; 3 of the 9 centres shown almost never fill a routine instrument that half of the cohort holds, 16 such cases, eleven of them in one centre (the laboratory and the vital signs); 44% of the patients included at least 18 months ago were never seen again; 46% are seen at one year, as in the review. |

## Open questions

Each has a default that the schemas already follow. Answer when the
instrument is reached, or earlier.

| # | Question | Default used | Needed for |
|---|---|---|---|
| O1 | `formoppos` is filled for 1,099 of the 2,353 patients (about half of those included since 2015): code 1 for 1,012 and code 2 for 87, in nine centres and in every year from 2012. In BP code 2 is given to 3 patients of 619, and the data managers have no documented definition of codes 1 and 2 (BP O16). What does code 2 mean, and why is it so much more frequent here? The export removes the patients with code 3 or 4, the oppositions (BP D68) | Delivered with its codes as written (`opposition_form`) | PATIENT |
| O4 | Calgary scale: item 8 (suicide) is not in the extraction. `calgar08` is filled from the field of item 7 on every row, and the stored total counts item 7 twice (D5). Can the export read the right field? Until then no CDSS total can be delivered: on one visit in ten the stored total is wrong, wherever items 7 and 8 differ. **To send first**: the CDSS total is a main outcome of the cohort, and its threshold of 6 defines depression | Eight items and their sum, `calgary_sum8`; `calgar08` and `calgar` ignored | HETERO-QUESTIONNAIRE |
| O5 | PANSS five-factor scores, what is left after D10. (1) Lançon 1998: the items of each factor could not be read in the paper. The corrected negative factor (G7 in place of N7) rests on its abstract and on the number of items per factor; can the PI or the centre of the authors confirm the five lists? (2) van der Gaag 2006: the stored scores keep 29 of the 45 terms of the published formula as two later papers quote it, and neither of its two subtractions (N5 from the positive factor, P2 from the negative one). Which version is wanted: the stored one, or the full formula? (3) To the data managers: which program computes the fifteen scores, the EMR or the export? The three wrong items of D10 are to correct there | Wallwork (two factors) and Lançon (one factor) corrected; van der Gaag as stored, labelled with its items | HETERO-QUESTIONNAIRE |
| O6 | AIMS, items 11 and 12 (teeth): the dictionary names them in two orders in the same line ("11: portprothese, 12: pbactu" for the labels, `rad_pbactu` then `rad_portprothese` for the fields). Which column is "current problems with teeth or dentures" and which is "wears dentures"? `aims0111` is yes on 13% of the visits and `aims0112` on 6% | The order of the published scale: 11 problems, 12 dentures | HETERO-QUESTIONNAIRE |
| O7 | Vitamin D (`vitd`): which unit? The dictionary gives none and the unit column is empty. Most centres have a median of 38 to 65, the size of nmol/L; one centre has a median of 24 and a third of its results under 30, the size of ng/mL (1 ng/mL is 2.5 nmol/L). Did that centre report in ng/mL, always or for a period? With the answer the results can be brought to one unit, as for prolactin | Delivered as written, with no unit (`vitamin_d_as_written`) | BILAN BIOLOGIQUE |
| O8 | S-QoL, items 17 and 18: the answers 1 and 3 are not in the extraction, in any year. The two items hold only 2, 4 and 5, while item 16 of the same dimension holds 1 to 5; 1,549 visits have item 16 and no item 17, and the stored dimension exists on 782 of them, so the patients did answer. Items 16 to 18 have their own list of answers ("more than expected"...): the export loses the answers whose text it does not find, as for Epworth in BP. Can the lookup be corrected? **To send early**: two items of 18 are unusable and a dimension cannot be recomputed | The items as extracted (missing where the answer was 1 or 3); the stored dimension `sqol_psychological_wellbeing` as it is | AUTO-QUESTIONNAIRE |
| O9 | WURS: which form did the SZ centres use, and when did it change? In BP the 61-item questionnaire was filled until 2021 and the 25-item one after, in the same columns. Here 305 visits from 2012 to 2026 hold the 25 items, 127 of them dated before 2021, and SZ has no ALS and no BIS to read the form from | One schema, `wurs`, with the 25 items and their sum (`wurs_sum25`), not called WURS-25 or WURS-61 | AUTO-QUESTIONNAIRE |
| O10 | Yale-Brown: what are `ybobse1` to `ybobse5` and `ybcomp1` to `ybcomp5`, called "scores, level" in the dictionary? They are rated 0 to 4 like the items (`ybobse01`...), equal the item on about 60% of the visits, and the stored sub-totals are the sums of the items, not of these columns All 79 `score_mismatch` of the three sums are on visits of 2015 and 2016, none later (D23): were the sums computed from the "level" columns in those two years? | The ten items and their sums; the ten "level" columns ignored | AUTO-QUESTIONNAIRE |
| O11 | Years of education after 2015. The form that holds them (`cclin08_`, conditions of the neuropsychological assessment) is filled until 2016 only, while the tests go on to 2026. The norms of the TMT errors need them, so their bands cannot be read for about 2,300 visits per band. A two-level education (`rad_nsc_`, below or from the baccalauréat) exists on 816 visits from 2017, with the errands test. Is the education of the later patients recorded elsewhere (the social module has an education level)? Could the export give the years of education at every visit? | Bands missing with `norm_missing` where the education is not known | NEUROPSYCHOLOGIE |
| O12 | WAIS-IV matrices: items 25 and 26 are not in the extraction. On every WAIS-IV visit the columns `mat25_w` and `mat26_w` hold the value of `mat24_w`, while the stored total counts three different items (D11). The export fills them from the field of item 24. The same for the WAIS-IV similarities: `simil10_w` and `simil11_w` hold the same value on every WAIS-IV visit (D14). Can the export read the right fields? | Matrices: items 1 to 24 and the total as stored. Similarities: items 1 to 9 and 12 to 18, the total as stored | NEUROPSYCHOLOGIE |
| O13 | CVLT: the z-score of trials 1 to 5 (`cvlt01z_`) does not follow the raw total from January 2022 to June 2025, in twelve centres: its median goes from -1.5 to 5.3 while the median total stays at 46 to 51 words, and comes back to -1.2 in the third quarter of 2025 (D14). Which rule computed it in that period, and can the values be computed again? | 240 values out of range, 260 kept with `period_doubt`, and their bands | NEUROPSYCHOLOGIE |
| O14 | WAIS-III: the estimated full-scale IQ (`ei06_wais3` in the dictionary) and `ei08_wais3` are not in the extraction, although the percentile rank and the confidence interval of that IQ are. Can they be added? The expected IQ minus the Barona difference gives the IQ back on 522 of 525 visits | Not delivered | NEUROPSYCHOLOGIE |
| O15 | WAIS-IV: why are the working memory index (`imt02_wais4`) and the full-scale IQ (`ei23_wais4`) stored 0.7 and 2.9 under the value that their percentile rank and the Barona difference use (D12)? Is it the export or the EMR, and can it be corrected at the source? | The stored value plus 0.7 and plus 2.9 | NEUROPSYCHOLOGIE |
| O16 | 33 visits of 2013, 2015 and 2016 are labelled WAIS3 in `wais_version` but were given the WAIS-IV: their digit-span total counts the sequencing task (32 of 33), all 33 have cells in the WAIS-IV index columns (25 with an index), none has the letter-number sequencing, one has a WAIS-III index. In 2016 it is every visit labelled WAIS3. Can the label be corrected? | The label is followed: these visits are read by the WAIS-III schemas, 30 get `score_mismatch` on the digit-span total, and their WAIS-IV indices are not read (they count as unread cells in the coverage) | NEUROPSYCHOLOGIE |
| O17 | **To send first.** Barona estimate: the occupation (`barona01_w`) holds the same place in its list as the diploma (`barona02_w`) on 72% of the visits (D13). Does the form fill the occupation from the diploma, or does the export read the wrong field? The expected IQs (`barona03_w`, `barona05_wais3`, `barona07_wais3`) are computed with it. Which equation computes them? | Values kept, `check_failed` on the occupation, the expected IQs and the differences of these 1,111 visits | NEUROPSYCHOLOGIE |
| O18 | Six films (LIS). (1) Which reference ratings does the score use? One set of 30 gives the stored score on 983 of 1,011 visits, so the published rule is applied, but the ratings are not in the dictionary. (2) 28 visits of 2022 to 2024, in 6 centres, hold a score that their ratings do not give. (3) 137 visits with the 30 ratings have no score (2018 to 2024, 53 in 2022). With the reference ratings in `norms/` the score could be computed for every visit | The score as stored | NEUROPSYCHOLOGIE |
| O19 | Anxiety disorders at inclusion: the column of the panic disorder with agoraphobia (`ceoccurtroubpanago`) holds, on all its 634 rows, the answer to the screening question `rad_peur_agoraphobie` (D17). Can the export read the right field? What are the exact questions of `rad_attaq_paniq`, `rad_peur_agoraphobie`, `rad_peur_sociale`, `rad_peur_specifique`, `rad_peur_obsessionnel`, `rad_peur_compulsif`, `rad_trouble_compulsif` and `rad_trouble_panique`, which the dictionary does not list? | The screening answer is delivered under its own name, the box is ignored; the labels of the screening questions are read from the column names | SUBSTANCES ET COMORBIDITE |
| O20 | **To send first.** `rad_tb_subst` at the inclusion visit: "Ne sais pas" on 975 of 1,583 visits (45% to 75% in every year), "Non" on 18, against 2% "Ne sais pas" at follow-up; on these visits every substance box says no (D17). Is "No" exported as "Ne sais pas" at inclusion? | Read as a missing code; the boxes of the substances are delivered and complete | SUBSTANCES ET COMORBIDITE |
| O21 | Three columns that the dictionary does not have: `rad_add_4` (opens the questions on sedatives, heroin, cocaine, opiates and other products; its label is read from the data), `rad_add_heroin7a` (38 cells after heroin) and `rad_ecv_vp5` (603 cells in the physical violence, yes on 8). What are the questions? | `rad_add_4` delivered as `illicit_drugs_ever`; the two others ignored | SUBSTANCES ET COMORBIDITE, EVALUATION MEDICALE |
| O22 | **To send first.** Social module, answers lost by the export. `maristat` never holds code 2 (married or living as a couple) and is empty on 12% to 20% of the visits of every year, where patients who live in their own family home and have children are found. `saltyp` never holds code 1 (salary) or 4 (disability pension). Can the export keep these answers? | Delivered as extracted; the notes warn that an empty cell is often a lost answer | SOCIAL - PERINATALITE |
| O23 | `stprof` (work status) and `saltyp` (source of income) are empty on almost every inclusion visit from mid-2015 to 2018 (137 of 148 in 2016, 149 of 153 in 2017), and filled before and after, while the housing and the income level are filled all along. Was another form in use, and are the answers in the source database? | Missing in that period | SOCIAL - PERINATALITE |
| O24 | Medical history: the two migraine columns are swapped. `migraine_mhdecod` (named for "treated") holds yes, no or unknown for every patient (2,488 cells), and `migraine_mhoccur` (named for the disease) is filled only after a yes (164 of its 166 cells). Every other disease has its answer in `_mhoccur` and "treated" in `_mhdecod`. Can the export be corrected? | Read the other way round: `migraine_v0` from `migraine_mhdecod`, `migraine_treated_v0` from `migraine_mhoccur` | ANTECEDENTS |
| O25 | The twelve columns "treatments at the time of the visit" (`psychotic`, `psychotic_nb` and the five other classes) are the same on every row of a patient, as the medication lists are: they describe the whole list, not the visit. Is that intended? Which rule puts a medication in a class? The number of antipsychotics equals the number that `facedata/medications.csv` finds for 1,391 of 1,975 patients | The six counts delivered once per patient (`medication_classes`), the six flags ignored; what a patient takes at a visit is computed from the dates (`on_*`) | TRAITEMENTS |
| O2 | `empjob` holds one code, 5, on 41 rows: the defect found in BP, where the form's list of about 17 classes is looked up in the nine classes of the dictionary (BP D74, BP O43). The mapping proposed for BP applies here too | To settle with the SOCIAL tab | SOCIAL - PERINATALITE |
| O26 | Medical history at inclusion: since 2022 the digestive section, the other diseases and the autoimmune diseases are answered at 42%, 46% and 32% of the inclusion visits, against 81% to 83% from 2016 to 2021; the five other sections do not move (D23). The share of all inclusions with a disease of these sections is unchanged, so the "no" are no longer written. Between centres, the autoimmune section is answered at 3% to 83% of the inclusions since 2022. Did the form of these three sections change in 2022, and is an empty section a "no"? The question of BP O37, for three sections here. **To send early** | Delivered as extracted: missing where the section is empty. No prevalence of these diseases should be computed on the inclusions from 2022 | ANTECEDENTS |
| O27 | Migraine at inclusion is "yes" for 10% to 15% of the answers of 2011 to 2017 and for 4% to 7% of those of 2018 to 2026 (1% in 2024), in the column that holds the answer of every patient (O24). Head injury, epilepsy and the other neurological diseases do not move. Did the wording or the place of the question change in 2018? | Delivered as extracted | ANTECEDENTS |
| O28 | WAIS-IV, the IQ estimated from two subtests (`wais4_qi_two_subtests`): stored for 41%, 68% and 57% of the inclusions of 2019, 2020 and 2021, and for 10% to 28% of those of 2022 to 2026, while the matrices are done at 67% to 81% of the same inclusions; almost no estimate in 2018 (6%). Is the estimate no longer computed, or no longer exported? | Delivered where it is stored | NEUROPSYCHOLOGIE |
| O29 | S-QoL 18: which index when a dimension is missing? The EMR averages the dimensions that it has (744 of the 1,194 indices that we do not recompute follow this rule); 760 of them lack only the psychological well-being dimension, which the extraction stores without its items. | Not delivered where a dimension is missing; flagged `score_not_recomputed` with the stored value | `sqol_index` |
| O30 | Vitamin D: in which unit does each centre report? One centre has a median of 24, the others 38 to 65 (O7). | Delivered as written under `vitamin_d_as_written`, not under the name of the nmol/L variable of DR and ASP | `vitamin_d_as_written` |
| O31 | YMRS: the form stores items 5, 8 and 9 as levels (0 to 4) where the scale gives points (0 to 8), and the stored total counts them once (D26). Is it the form of every centre since 2010, and can the EMR store the points and the published total? | The three items in points and the published total; the stored total kept as a check | `ymrs05`, `ymrs08`, `ymrs09`, `ymrs_total` |

Answered on 2026-11-13: O3 became D9, O5 became D10 and the new O5. Agreed by the project lead on 2026-11-14 (D22): the corrections of D10, D12, D14 and D20 and the reading of D17.

## Instrument changes found in the extraction

Scan of 2026-11-13, on the 1,542 columns that hold 50 values or more (27 columns are
empty, 151 hold 1 to 49 values). Each line is a lead to follow when its tab is reached,
not yet a decision.

| What the scan shows | Columns | To check |
|---|---|---|
| Columns that come into use late | 546 are in use only from 2013 or later: 113 from 2013, 290 from 2015, the others one year at a time until 2026. Among them STORI, PSQI, SSTICS, WURS, SOGS, EPHP, physical activity, presenteeism, Yale-Brown, the six films | A new set of forms in 2015: which instruments it added, and whether it replaced older ones in the same columns |
| Columns that go out of use | 341 are no longer in use after 2023 or earlier: 81 stop in 2015, 63 in 2016, 151 in 2017. Among them fNART, information, letter-number sequencing, six elements, laterality, picture completion, arithmetic, CPT-IP | The battery of the first years was retired between 2015 and 2017. One schema per edition (BP D9); the WAIS sections are already named "old" and "new" version |
| A level that moves with the year | 138 numeric columns have a yearly median that moves by one interquartile range or more: WAIS similarities, picture completion, arithmetic, matrices and information, CVLT, SSTICS, SUMD, the films | Another edition, another scoring rule, or another population of patients in those years |
| Extreme values | 60 numeric columns have a largest value of 20 times the median or more: doses and frequencies of substances, physical activity, CVLT, durations | Typing errors, another unit, a free-typed number |
| Numbers and words in one column | 59 columns: 19 of the CVLT, the TMT percentiles, the errands test, craving. For 13 of them the share of numbers changes by 20 points or more between periods | Bands, percentiles and z-scores in one column, as in BP (BP D38, BP D44) |
| A code absent from a whole period | 21 columns outside the keys: arithmetic, similarities, the TMT percentiles, EPHP, craving | A coding that changed, or an answer that the export loses |

The leads of the scan were followed tab by tab. What was decided for each case
is below, in the layout of the BP file (D22). The rules are those of BP: one
schema per edition or form (BP D9); a score that is proven wrong is delivered
corrected and the stored one kept as a check (D10); a value given as "less
than" or "more than" keeps its mark.

### Two editions or forms in the same columns

| Case | What the data show | Handling | State |
|---|---|---|---|
| WAIS-III / WAIS-IV, every subtest | `wais_version`: WAIS3 on 781 visits (2010 to 2016), WAIS4 on 2,654 (2014 to 2026). Matrices, digit span, similarities, picture completion, arithmetic, information and coding hold both editions in the same columns | Two schemas per subtest, split by `wais_version` (D11, D14) | Done: `wais3_*` and `wais4_*` for `matrices`, `memoire_chiffres`, `similitudes`, `complement_images`, `arithmetique`, `information`, `code_symboles_ivt`; `wais3_sequences_lettres_chiffres` exists for the WAIS-III only |
| WAIS IQs and indices | Own columns per edition; the WAIS-IV has a seven-subtest IQ until 2017 and a two-subtest IQ from 2019 | Two schemas (D14) | Done: `wais3_efficience`, `wais4_efficience`. Open: O14, O15, O28 |
| Visits labelled WAIS3 that were given the WAIS-IV | 33 visits of 2013, 2015 and 2016 | The label is followed; 30 get `score_mismatch` on the digit-span total | Open: O16 |
| Suicide questions, lifetime / since the last visit | At inclusion 64% answer yes to the first question and 30% have attempted suicide; at follow-up 31% and 2%, and 631 of the 665 later answers of patients who said yes at inclusion are no | Two schemas, split by the visit label (BP D46) | Done: `isf_lifetime`, `isf_since_visit` (D16) |
| Comorbidities, inclusion / yearly visits | Of the patients with an alcohol use disorder at inclusion, 147 of 319 later answers are no: the yearly form is about the time since the last visit | Two schemas per section, split by the visit label (BP D49) | Done: `anxiety_v0`, `anxiety_fu`, `substance_v0`, `substance_fu`, `eating_disorder_v0` (D17) |
| Medical history, inclusion / follow-up | A disease answered yes at inclusion is most often answered no later (39 of 47 for a head injury, 43 of 54 for acne) | Two schemas per body system, split by the visit label | Done: nine systems, `_v0` and `_fu` (D20). Open: O26 |
| Hospitalisations and sick leave | Whole life at inclusion, the last twelve months or the time since the last visit afterwards, in columns of their own | One schema per period | Done: `hospitalisations_v0`, `hospitalisations_12m`, `sick_leave_v0`, `sick_leave_fu` (D18) |
| WURS | The 25 items on 305 visits from 2012 to 2026; nothing tells the 61-item from the 25-item form, and SZ has no ALS and no BIS to read it from | One schema with names of its own, not called WURS-25 or WURS-61 | Open: O9 |

### Scores and sub-scores: corrected, recomputed or flagged

| Case | What the data show | Handling | State |
|---|---|---|---|
| PANSS five-factor scores | Three of the fifteen stored scores sum a wrong item: Wallwork positive (N2 for G9), Wallwork negative (N5 for N6), Lançon negative (N7 for G7); each differs from the published score on about 2,800 to 3,300 visits | Delivered as published; a second score that is not delivered repeats the stored formula and is compared with the stored column (D10) | Done, agreed (D22). Open: O5 for the van der Gaag scores and the other Lançon factors, delivered as stored |
| WAIS-IV working memory index and full-scale IQ | Stored 0.7 and 2.9 under the value that their percentile rank and the Barona difference use, on every visit | The stored value plus the constant, written with `scale` (447 and 430 visits); the stored values are not delivered (D12) | Done, agreed (D22). Open: O15 |
| Laterality quotient | One centre computed it on 12 lines instead of the 10 activities (41 visits, 2010 to 2015) | Recomputed on the ten activities (D14) | Done, agreed (D22) |
| Migraine | The two columns are swapped | Read the other way round (D20) | Done, agreed (D22). Open: O24, O27 |
| Calgary total | Counts item 7 twice and holds no item 8 | Not delivered; the eight items and `calgary_sum8` (D5) | Open: O4 |
| Cholesterol ratio | Not the ratio of the stored values on 157 visits, more and more since 2019 | The recomputed ratio is delivered (D7) | Done |
| TMT z-scores | One centre wrote five z-scores with the opposite sign in 2011 and 2012 (23 visits each) | Flipped, `sign_flipped` (D11) | Done |
| Sub-scores whose key the dictionary does not give | Birchwood (three sub-scores), S-QoL (seven dimensions and the index), STORI (five stages), EPHP (four sub-scores), Yale-Brown (two sums), SSTICS (six factors), six elements (three sums) | Each key was fitted on the items, the score is recomputed and compared with the stored one (D8, D14) | Done; a few `score_mismatch` each, apart from the Yale-Brown sums of 2015 and 2016 (79, O10) |
| Totals after a stopping rule | WAIS subtests: the items after the stopping rule are empty | Recomputed with `min_items: 1` and compared (D14) | Done. WAIS-IV matrices and similarities: the totals as stored, because items are lost (O12) |
| S-QoL psychological well-being | Cannot be recomputed: items 17 and 18 lose two answers | Delivered as stored | Open: O8 |
| Barona expected IQs | The occupation follows the diploma on 72% of the visits | Kept, `check_failed` on the occupation, the three expected IQs and the three differences of 1,111 visits (D13) | Open: O17 |
| CVLT z-score of trials 1 to 5 | Does not follow the raw total from 2022 to mid-2025 | 240 values out of range and removed, 260 kept with `period_doubt`, with their bands (D14) | Open: O13 |
| Values derived from an empty cell or from another value | PSP ten-point band (215 visits), CGI efficacy index (32), percentile of part B of the doors test (172) | Kept and flagged: `check_failed`, `derived_doubt` (D5, D14) | Done |

### Limits of detection, bands, missing codes, units and typing

| Case | What the data show | Handling |
|---|---|---|
| "Less than" and "more than" | `<5`, `>20`, `>95` typed in a number: 481 cells on the left and 7,804 on the right, in 49 variables (CRP 334, months of hospitalisation 105, toxoplasmosis titre 16, and the open-ended percentile bands of the CVLT, the TMT and the errands test) | The value is the limit, the mark goes to the column `<variable>_cens`, flags `censored_left` and `censored_right` (D7, D18) |
| Bands, percentiles and z-scores in one column | 19 CVLT columns, the TMT percentiles, the errands test | Read as bands; the CVLT z-scores are also turned into bands (15,918 `band_from_z`); a band typed in a number is read as its middle (59 `band_middle`) (D11, D14) |
| Missing codes | 48,976 cells: 0 of the SUMD ("cannot be rated"), 7 of the EPHP, 2 of the DSM-5 criteria, "Ne sais pas", 999, 9999 and 99, and words in a number ("Pas d'hospitalisations", "Jamais travaillé", "Non applicable", "DCM", "NF", "xxx", "NaN", "undefined") | Missing, with the reason in the flag `missing_code` (D5, D8, D14, D17, D18) |
| Units | Prolactin with no reliable unit; results on another scale under the default label (haemoglobin in g/L, glucose in g/L, neutrophils as a percentage, clozapine in mg/L) | The BP unit rule: 732 `unit_converted`, 292 `unit_inferred`, 145 `unit_doubt`, 162 `unit_unknown` (D7). Vitamin D has no unit: O7 |
| Extreme values | The 1st and 99th percentiles of each number | 2,960 values of 85 variables brought back to the percentile, `winsorised`; `winsor_limits` of `sz.load` changes or removes the rule |
| Impossible values and unreadable text | 1,253 `out_of_range` (250 doses per day of the BARS, 240 CVLT z-scores, 67 prolactin, 27 QTc) and 353 `unparsed` (83 times of the six elements written in words) | Missing; what was typed stays in `flags` |
| Placeholder dates | 1000-01-01 on 124 cells that are read (114 dates of the first suicide attempt, 10 dates of the referral letter) | Missing, `date_placeholder` (D4, D16) |
| A "no" that the form did not ask | Anxiety disorders after the screening tree; the drugs after "never used" | Delivered as 0 with `asked_if` (D17), agreed (D22) |

### Checked, no change found

The stored score follows one formula in every year, with no `score_mismatch`
or a few that are not gathered in a period: the four PANSS sums and the twelve
factor scores delivered with the stored formula, the CTQ, the EQ-5D
index, the Fagerström, the MARS, the Birchwood scale, the seven S-QoL
dimensions that can be recomputed, the STORI, the EPHP, the SSTICS, the fNART,
the mean d-prime of the CPT-IP and the body mass index.

Mismatches gathered in a period or a centre, each explained above: the
cholesterol ratio (from 2019), the laterality quotient (one centre, 2010 to
2015), the Yale-Brown sums (2015 and 2016, O10) and the WAIS-III totals of
2015 and 2016 (visits given the WAIS-IV, O16).

Looked for and not seen: the peak of suicide attempts "since the last visit"
of 2022 and 2023 in BP (1% to 5% of the follow-up visits in every year here,
D16), duplicated rows, and the flood of placeholder dates of 2025 and 2026.

Columns that exist only for a period, and are simply empty elsewhere. Until
2015 or 2016: the fNART, the laterality inventory, the letter-number
sequencing and the form of the assessment conditions, which holds the years
of education (O11). Until 2017 or 2018: WAIS coding, picture completion,
arithmetic and information, the verbal fluency, the CPT-IP, the six elements
and the doors test. From 2011 to 2014: the EQ-5D. From 2012 to 2017: the PSP.
From 2013: the violent behaviours and the six films. From 2015: the PSQI, the
STORI, the physical activity, the SSTICS, vitamin D, toxoplasmosis, the
substance modules and the autoimmune history. From 2018: the errands test.

## Findings to report to whoever produces the extraction

First screen of 2026-11-13, before any schema. Each line follows a kind of error found in
BP; the tab that owns the columns confirms or drops it.

| Kind of error (BP example) | First screen of the SZ file |
|---|---|
| Answers lost by the export when a text does not match its lookup table (BP: Epworth, Fagerström item 3, CSM item 7) | Corrected on 2026-11-13 for Birchwood, Fagerström, SOGS and one physical-activity item (D1). 13,033 cells still hold a backslash before an apostrophe, the cause of the losses. Five families of items have items that never hold an answer the others have: CTQ, S-QoL, AIMS, PANSS, YMRS. Closed for AIMS, PANSS and YMRS: every level occurs, the highest rarely, and the YMRS has items of 0 to 8 by design (D5). CTQ: closed too, the levels 1 to 4 are scale levels, not items. S-QoL: confirmed, items 17 and 18 lose the answers 1 and 3 (D8, O8) Found later: `maristat` never holds "married or living as a couple" and `saltyp` never holds "salary" or "disability pension" (O22); `rad_tb_subst` holds "Ne sais pas" where "no" is expected at inclusion (O20); "Arme à feu" is written "Arme ? feu". |
| A list looked up in the wrong classes (BP: `empjob`) | The same defect: `empjob` holds one code on 41 rows (O2) |
| A column filled from another field (BP: `mere_dthfl`) | Not screened by a rule. Each column is crossed with its neighbours and its date when its section is reached. The SZ extraction has no `mere_dthfl`. Found: `causedec_stopsuivi`, named for the cause of death, holds the date of death (D4); `calgar08`, item 8 of the Calgary scale, holds item 7, and the stored total with it (D5, O4); `mat25_w` and `mat26_w` hold item 24 of the matrices on the WAIS-IV visits (D11, O12) In NEUROPSYCHOLOGIE: the Barona occupation follows the place of the diploma in its list on 72% of the visits (D13); on the WAIS-IV visits the matrices items 25 and 26 are copies of item 24 and the similarities items 10 and 11 are one cell twice (O12). In the last tabs: the box of the panic disorder with agoraphobia holds a screening answer (O19); the two migraine columns are swapped (O24). |
| Values that the export writes by itself: copies, a value on every row, default unit labels, a 0 when nothing was measured | 35 columns are exact copies of another one, in 12 groups; 6 columns hold two values on every row. Found: eleven `siteid_<tab>` copies (D4), `calgar08` (D5), and the default unit label on every visit of the biology tab, with or without a result (D7) In NEUROPSYCHOLOGIE: the percentile of part B of the doors test is "<1" on 172 visits where part B is empty (D14); "NaN", "undefined", "Qu" and "Ques" are written where a score could not be computed. In TRAITEMENTS: twelve columns called "at the time of the visit" are the same on every row of a patient (O25). |
| Scores written or recomputed by the data managers (BP: `als55`, MAThyS sub-scores) | Each stored score is compared with its items, by year. Found: three of the fifteen PANSS factor scores sum a wrong item, corrected here (D10); three stored scores are an item under another name (`bars0106`, `sumd1` to `sumd3`) In NEUROPSYCHOLOGIE: the WAIS-IV working memory index and full-scale IQ are stored 0.7 and 2.9 too low, corrected here (D12); the CVLT z-score of trials 1 to 5 is wrong from 2022 to mid-2025 (O13); one centre computed the laterality quotient on 12 lines instead of 10 (D14); 28 LIS scores of 2022 to 2024 are not those of their ratings (O18). |
| Two editions or forms in the same columns | `wais_version`: WAIS-III on 781 rows, WAIS-IV on 2,654. The BP schema of the WAIS-IV matrices gives 636 `score_mismatch` here, against 1 in BP. The WURS (305 visits) has no ALS and no BIS to tell its form 33 visits labelled WAIS3 were given the WAIS-IV (O16). Every WAIS subtest has one schema per edition (D14). |
| One column, two questions: lifetime at inclusion, since the last visit at follow-up | Several sections are titled "VIE ENTIERE ou depuis la DERNIERE VISITE". Answers are crossed within patients before one column is delivered |
| Placeholder and impossible dates | 136 cells hold 1000-01-01, none holds 2011-11-11. The day of birth is 15 for every patient, as in BP |
| The dictionary | 201 columns of the extraction are not in it: STORI (50), letter-number sequencing (28), laterality (24), SOGS (22), similarities (19), SUMD (12) and others. Its TAP sheet is not extracted. `edulevel` mixes codes and words |
| A section left empty from a year, in some centres (BP O37, O40) | Not seen: a medical history is filled at 83% to 100% of the inclusions in every year Found later: the work status and the source of income are empty from mid-2015 to 2018 (O23). Found on 2026-11-14, while building the review: the digestive, "other" and autoimmune sections of the medical history are answered at 32% to 46% of the inclusions since 2022, against 81% to 83% before (D23, O26). |
| Suicide attempts "since the last visit" in 2022 and 2023 (BP D48) | Not seen: 1% to 5% of the follow-up visits in every year |
| Structure | No duplicated row. 21 visits are dated before the patient's previous visit. 1,675 screening rows, for 1,675 of the 2,353 patients, with 62 columns filled. No 6-month visit. Patients registered in two centres can change identifier and centre from one extraction to the next (BP D73) |

## What the schemas must produce (acceptance)

`tests/test_real_data_sz.py` holds the current value of every number it checks.

| Check | Expected |
|---|---|
| visits | 6,616 rows in `data`, (`usubjid`, `visit`) unique, 2,353 patients |
| PATIENT | 17 patient-level variables (`fondacode` among them) and `entry_date`. 647 women and 1,706 men. `opposition_form`: 1,012 patients with 1, 87 with 2. `referred_by` for 1,591 patients; 10 `date_placeholder` on the date of the referral letter. `followup_end_reason`: 583 filled, 91 missing codes; 12 deceased, 8 with a `death_date` |
| HETERO-QUESTIONNAIRE | 130 variables in ten instruments. No `score_mismatch` on the four PANSS sums, on the twelve factor scores delivered with the stored formula, and on the three stored formulas kept as checks (`panss_total` on 4,646 visits, 30 to 160; `panss_wallwork_positive` 4,663, `panss_wallwork_negative` 4,662, `panss_lancon_negative` 4,660, the three as published). `calgary_sum8` on 4,672 visits. `ymrs_total` on 4,538: the published total, with items 5, 8 and 9 in points (D26); the stored total is reproduced by its twin on every visit. `barnes_sum` 3 and `esrsa_mean` 10 `score_mismatch`. `cgi_efficacy_index` 32 and `psp_band` 215 `check_failed`. `bars_doses_per_day` 250 `out_of_range`, `psp_total` 3. Missing codes: `cgi_severity` 12, `cgi_improvement` 354, `sumd04_awareness` 2,121. No `unknown_code`, no `unparsed` |
| CONSTANTES et ECG | `height` 4,318 valid (3 `out_of_range`), `weight` 4,322 (1), `waist` 4,112 (9), `bmi` on 4,303 visits with no `score_mismatch`. `systolic_supine` and `diastolic_supine` 4,123 each, 1 `unit_inferred`. `qtc_stored` 2,828 valid, 27 `out_of_range`, 1 `unit_inferred` |
| BILAN BIOLOGIQUE | 27 variables in seven instruments; no `unparsed`. `crp` 3,563 valid, 334 `censored_left`. `glucose` 3,136 valid, 66 `unit_converted`, 17 `unit_inferred`, 3 `out_of_range`. `haemoglobin` 3,658 valid, 34 `unit_inferred`. `neutrophils` 23 `unit_inferred`, `eosinophils` 37 `unit_doubt`. `cholesterol_hdl_ratio` on 3,578 visits, 157 `score_mismatch`. `prolactin` 2,985 valid: 633 `unit_converted`, 139 `unit_inferred`, 162 `unit_unknown`, 36 `unit_doubt`, 67 `out_of_range`. `clozapine` 592 valid, 11 `unit_inferred`; `clozapine_treated` 1,600. `vitamin_d_as_written` 2,718 valid. `toxo_igg_titre` 632 valid, 16 `censored_right` |
| AUTO-QUESTIONNAIRE | 475 variables in 21 instruments; no `unknown_code`. No `score_mismatch` on `ctq_total` (2,166), `eq5d_index` (3,909), `fagerstrom_total` (1,981), `wurs_sum25` (295), the seven recomputed S-QoL dimensions and `sqol_index` (3,033). `mars_total` 4,266 (2 mismatches). `psqi_total` 2,954 (11), `psqi_latency_component` 15, `psqi_latency` 26 `unparsed` and 15 `unit_inferred`. `birchwood_total` 4,244 (5). `sqol17` 2,734 and `sqol18` 2,784 valid against 4,267 for `sqol16`. `stori_stage1` 3,089 (2). `ephp_total` 1,557 (4), 377 missing codes on the EPHP items. `ybocs_total` 281 (28). `sogs_total` 122. `out_of_range`: 13 in `presenteeism`, 4 in `physical_activity`. `alcohol_larger_amounts` 2,035 valid, 9 missing codes |
| NEUROPSYCHOLOGIE, first part | 659 variables in 30 instruments for the whole tab, 1 `unknown_code`; 147 variables in the eight instruments of the first part. `education_years` 776 valid, all before 2017. `tmt_a_time` 3,210; five z-scores with 23 `sign_flipped` each; `tmt_a_errors_band` on 748 visits, 2,359 `norm_missing`. `errands_errors` 1,023 and the two fluency rule-break scores without `score_mismatch`. `wais3_mat_total` 568 (4 mismatches); `wais4_mat_total` 1,867, as stored. `wais4_ds_total` 2,494 with no mismatch on its check; `wais3_ds_total` 737, 30 mismatches on its check. Cells that no schema reads: `mat25_w` and `mat26_w` on the 1,871 WAIS-IV visits, three sequencing columns on 33 WAIS-III visits |
| NEUROPSYCHOLOGIE, second part | `cvlt_total_1_5` 2,275 valid; its z-score 240 `out_of_range` and 260 `period_doubt`. `wais3_simil_total` 570 (12 mismatches), `wais4_simil_total` 1,865 as stored. The stored sums of scaled scores equal the short-form formulas: WAIS-III verbal 528 of 528, performance 539 of 539, working memory 472 of 472; WAIS-IV verbal comprehension 455 of 456, perceptual reasoning 451 of 451, working memory 445 of 447, full scale 428 of 430. `wais4_imt_index` 447 and `wais4_qit` 430, all whole numbers once corrected. Barona differences: verbal 508 of 508, performance 516 of 516, full scale 292 of 293 with the seven-subtest IQ and 154 of 161 with the two-subtest IQ; `barona_occupation` 1,548 valid, 1,111 `check_failed`. `sstics_total` 2,338 (2 mismatches). `lis_total` 1,018. `fnart_total` 684, `cptip_dprime_mean` 999, no mismatch. `six_elements_points` 862 (1 mismatch), 83 `unparsed` on the time. `doors_total` 771; `derived_doubt` on 172 part B bands and 1 part A band. `laterality_quotient` 502 (41 mismatches). Cells that no schema reads: the WAIS-IV index columns on up to 52 visits labelled WAIS3 (O16), `arith21_w` and `arith22_w` on 26 |
| SUICIDE | 26 variables in three instruments. `isf05_lifetime` 2,231 valid, 680 yes; `isf05_since_visit` 2,360, 57 yes; no `period_doubt`. `first_attempt_date` 623 valid, 114 `date_placeholder`; `n_attempts` 694 |
| SUBSTANCES ET COMORBIDITE | 189 variables in eleven instruments; no `unknown_code`, no `unparsed`. `anxiety_disorder_v0` 2,104 valid, 826 yes; `panic_without_agora_v0` 1,911 valid, 99 yes; `social_phobia_v0` 1,905, 146 yes. `substance_disorder_v0` 608 valid, 975 `missing_code`, 590 yes; `alcohol_disorder_v0` 313 yes, `cannabis_disorder_fu` 553 yes. `illicit_drugs_ever` 481 yes, `heroin_ever` 55 yes |
| PERINATALITE, EVALUATION MEDICALE, SOIN SUIVI, SOCIAL | 19, 91, 27 and 11 variables in one, three, five and one instruments; no `unknown_code`. `birth_weight` 1,030 valid, `gestational_age` 830. `n_psychotic_episodes` 1,899; `symptom_persecution_ever` 1,807 yes; `violence_verbal` 925 yes. `first_hospitalisation_age` 1,868 valid; `hospitalisation_months_v0` 105 `censored_right`; `hospitalised_12m` 4,494. `marital_status`: 1,652 single, 42 divorced, 30 separated, 4 widowed, no couple. `income_source`: six classes, no salary and no disability pension |
| TRAITEMENTS | 69 variables in six instruments (with `medications_at_visit`). `treatments`: 11,038 rows, 1,975 patients, 122 molecules; `molecule` 10,889 valid, 149 `unknown_code` (9 more names are found since 31 names were added to the shared table with FACE ASP, on 2026-11-14); 5,278 second-generation and 1,325 first-generation antipsychotics, 1,492 antidepressants. The ATC code of the EMR equals the code of the table on 3,305 of 3,313 medications. `start_date` 11,038 valid, `end_date` 5,792 valid and 1,064 missing codes. `on_antipsychotic_2g` on 5,888 visits, mean 0.88; `on_clozapine` 0.18 at inclusion. `n_listed_antipsychotics` for 1,975 patients. `non_drug_treatment_fu` 2,257 valid, 836 yes; `cbt_fu` 376 yes |
| ANTECEDENTS | 215 variables in 21 instruments (with `family_history_per_patient`); no `unknown_code`, no `unparsed`. `migraine_v0` 2,046 valid, 157 yes; `head_injury_v0` 202 yes, `head_injury_fu` 398 valid and 14 yes; `dyslipidaemia_v0` 233 yes; `asthma_v0` 192 yes. `relatives`: 1,887 rows, 1,200 patients (688 mothers, 659 fathers, 294 brothers, 239 sisters). `fdr_depression` 1 for 506 patients, `fdr_schizophrenia` 158, `fdr_bipolar` 110 |
| coverage | 1,668 columns covered, 52 ignored, none not assigned |

## Checklist

State: ☐ not started · ◐ schema written (draft) · ☑ reviewed · – ignored.
Numbers are variables of the dictionary section that are in the extraction.

### 1. PATIENT (`patient/`)

| State | Section | Variables |
|---|---|---|
| ◐ | IDENTIFICATION PATIENT: `identite` (sex, diagnosis, date of birth, age at inclusion). `subjid` delivered as `fondacode` (D9) | 7 |
| ◐ | Provenance: `provenance` | 8 |
| ◐ | VISITE and ID_VISIT: `visit_record` (the entry date). The other columns are keys | 4 |
| ◐ | Not in the dictionary: `formoppos` (`inclusion`, O1), three end-of-follow-up columns (`fin_de_suivi`, D4), `id_visit` (a key), eleven `siteid_<tab>` copies (ignored) | 16 |

All 35 columns of the tab are covered (24) or ignored (11). The five schemas
meet the definition of done except for the review, so they stay `draft`.

### 2. HETERO-QUESTIONNAIRE (`hetero_questionnaire/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Questionnaire AIMS: `aims`, with the two teeth items that the dictionary names in one line (O6) | 10 + 2 |
| ◐ | Questionnaire BARNES: `barnes`; `bars0106` ignored | 6 |
| ◐ | Questionnaire Brief Adherence Rating Scale BARS: `bars` | 4 |
| ◐ | Questionnaire CALGARY: `calgary`, eight items; `calgar08` and the stored total ignored (D5, O4) | 10 |
| ◐ | Questionnaire CGI-EGF: `cgi_egf` | 6 |
| ◐ | Questionnaire PANSS: `panss`, 30 items, four sums and fifteen factor scores, three of them corrected (D10, O5) | 49 |
| ◐ | Questionnaire SUMD: `sumd`, three general items and twelve symptom columns that the dictionary does not list; the three stored scores ignored | 6 + 12 |
| ◐ | Questionnaire YMRS: `ymrs` | 12 |
| ◐ | Questionnaire EFFETS SECONDAIRES EXTRA-PYRAMIDAUX: `extrapyramidal` | 11 |
| ◐ | Questionnaire PSP: `psp` | 6 |

All 134 columns of the tab are covered (128) or ignored (6). The ten schemas
meet the definition of done except for the review, so they stay `draft`.

### 3. CONSTANTES et ECG (`constantes_et_ecg/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Paramètres physiques: `parametres_physiques` | 4 |
| ◐ | Pression artérielle / fréquence cardiaque: `pression_arterielle`, the lying pressures | 2 |
| ◐ | ECG: `ecg`, the stored QTc | 1 |

All 7 columns of the tab are covered. The three schemas meet the definition
of done except for the review, so they stay `draft`.

### 4. BILAN BIOLOGIQUE (`bilan_biologique/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Uric acid, CRP, glucose, HbA1c and their unit columns: `biochimie` | 8 |
| ◐ | Vitamin D, time outdoors, phototype, supplement: `vitamine_d`; its unit column ignored (O7) | 5 |
| ◐ | Toxoplasmosis serology and IgG titre: `toxoplasmose`; the unit column of the titre ignored | 5 |
| ◐ | HDL, LDL, total cholesterol, triglycerides, ratio and their unit columns: `bilan_lipidique` | 9 |
| ◐ | Leukocytes, erythrocytes, haemoglobin, neutrophils, eosinophils, MCV, platelets and their unit columns: `nfs` | 14 |
| ◐ | Prolactin and its unit column: `bhcg_prolactine` | 2 |
| ◐ | Clozapine level: `dosage_psychotropes`, with `rad_clozapine`, which the dictionary spells `rad_clozapin` | 2 |

All 45 columns of the tab are covered (43) or ignored (2). The seven schemas
meet the definition of done except for the review, so they stay `draft`.

### 5. AUTO-QUESTIONNAIRE (`auto_questionnaire/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Questionnaire BIRCHWOOD: `birchwood` | 12 |
| ◐ | Questionnaire CTQ: `ctq`; `ctq41` ignored | 41 |
| ◐ | Questionnaire MARS: `mars`, with `mars010`, which the dictionary does not list | 10 + 1 |
| ◐ | Questionnaire QUALITE DE VIE: `sqol`; items 17 and 18 lose two answers (O8) | 27 |
| ◐ | Questionnaire FAGERSTROM: `fagerstrom` | 7 |
| ◐ | Questionnaire EQ5D: `eq5d` | 7 |
| ◐ | Questionnaire ACTIVITE PHYSIQUE: `physical_activity` | 14 |
| ◐ | Questionnaire STORI: `stori`, five totals and the 50 items that the dictionary names in one line | 5 + 50 |
| ◐ | Questionnaire PSQI: `psqi`, with four bed-partner questions that the dictionary does not list; `psqi15` and `psqi16` ignored | 29 + 4 |
| ◐ | Questionnaire EPHP: `ephp` | 18 |
| ◐ | Questionnaire WURS: `wurs`; the form is not known (O9) | 26 |
| ◐ | Questionnaire SOGS: `sogs`, with 22 columns that the dictionary names in one line | 13 + 22 |
| ◐ | Questionnaire YALEBROWN: `yale_brown`; ten "level" columns ignored (O10) | 23 |
| ◐ | Questionnaire PRESENTEISM: `presenteeism` | 11 |
| ◐ | Critères DSM5 de troubles liés à l'usage, seven substances: `dsm5_alcohol`, `dsm5_cannabis`, `dsm5_cocaine`, `dsm5_heroin`, `dsm5_opiates`, `dsm5_sedatives`, `dsm5_other_substances` | 7 × 24 |

All 488 columns of the tab are covered (475) or ignored (13). The 21 schemas
meet the definition of done except for the review, so they stay `draft`.

### 6. NEUROPSYCHOLOGIE (`neuropsychologie/`)

Written on 2026-11-13 (D11 to D15): 30 schemas, 659 variables. Every column of the tab is
read or ignored, with the 80 columns of these instruments that the dictionary does not list.

| State | Section | Variables |
|---|---|---|
| ◐ | Critères cliniques (nouvelle version): `neuropsy_conditions` | 11 |
| ◐ | wais_version: `barona` (occupation, diploma, expected full-scale IQ and difference), and the version column | 4 + 1 |
| ◐ | Efficience intellectuelle (WAIS-4): `wais4_efficience`; the processing speed index is in `wais4_code_symboles_ivt` | 16 |
| ◐ | Efficience intellectuelle (WAIS-3): `wais3_efficience`; the four Barona columns are in `barona` | 18 |
| ◐ | Similitudes: `wais3_similitudes` (19 items), `wais4_similitudes` (items 10 and 11 are one cell twice, O12) | 3 + 19 items |
| ◐ | Mémoire des chiffres: `wais3_memoire_chiffres`, `wais4_memoire_chiffres`, summary scores | 13 |
| ◐ | Matrices: `wais3_matrices`, `wais4_matrices` (items 25 and 26 lost on the WAIS-IV visits, O12) | 29 |
| ◐ | Séquences Lettres-Chiffres (WAIS-3): `wais3_sequences_lettres_chiffres` | 3 + 28 items |
| ◐ | Code: `wais3_code_symboles_ivt`, `wais4_code_symboles_ivt` | 5 |
| ◐ | Complètement d'images: `wais3_complement_images`, `wais4_complement_images` | 28 |
| ◐ | Arithmétique: `wais3_arithmetique`, `wais4_arithmetique` | 25 |
| ◐ | Information: `wais3_information`, `wais4_information` | 31 |
| ◐ | SSTICS (WAIS-4): `sstics` | 29 |
| ◐ | CVLT: `cvlt` (two standardised columns per mixed measure; z-score of trials 1 to 5 doubted from 2022 to mid-2025, O13) | 40 + 6 |
| ◐ | Partie A, Partie B, Partie B-A: `tmt`; four error percentile columns ignored | 22 |
| ◐ | Films A to F: `lis` (30 ratings and the score as stored, O18) | 31 |
| ◐ | TEST DES COMMISSIONS: `errands_test` | 17 |
| ◐ | fNART: `fnart` | 44 |
| ◐ | CPT-IP: `cpt_ip` | 14 |
| ◐ | Test des 6 éléments: `six_elements` | 28 |
| ◐ | Test des portes: `doors_test` | 6 |
| ◐ | Fluences: `verbal_fluency` | 16 |
| ◐ | Latéralité: `laterality` (the quotient and the 24 item columns) | 1 + 24 items |

434 columns of the dictionary are in the extraction. 13 names of the dictionary are not
columns of the file: six CVLT percentile columns (`cvlt13p_` to `cvlt18p_`) and seven
lines that name a range of items ("simil01_w à wais3_simil19_w").

### 7. SUICIDE (`suicide/`)

Written on 2026-11-13 (D16).

| State | Section | Variables |
|---|---|---|
| ◐ | Intentionnalité suicidaire: `isf_lifetime` (inclusion), `isf_since_visit` (follow-up) | 10 |
| ◐ | Histoire des conduites suicidaires: `suicide_attempts` | 6 |

All 16 columns of the tab are read.

### 8. SUBSTANCES ET COMORBIDITE (`substances_et_comorbidite/`)

Written on 2026-11-13 (D17).

| State | Section | Variables |
|---|---|---|
| ◐ | Trouble thymique: `depressive_episodes` | 3 |
| ◐ | Troubles ANXIEUX: `anxiety_v0` (with eight screening columns that the dictionary does not list), `anxiety_fu`; `ceoccurtroubpanago` and `rad_trouble_panique` ignored (O19) | 23 |
| ◐ | Trouble du comportement alimentaire: `eating_disorder_v0` | 4 |
| ◐ | Troubles lié à une SUBSTANCE: `substance_v0`, `substance_fu`; `sutrt_autre` and `chk_substances_type` ignored | 22 |
| ◐ | Tabac: `tobacco` | 9 |
| ◐ | Alcool: `alcohol_use` | 16 |
| ◐ | Cannabis: `cannabis_use` | 12 |
| ◐ | Sédatifs, Héroïne, crack/cocaine, opiaces, Autres produits: `drug_use`, opened by `rad_add_4`; `rad_add_heroin7a` ignored (O21) | 50 |
| ◐ | The, Cafe: `tea_coffee` (with `sudosnb_cafelt`) | 9 |

All 148 columns of the tab are read or ignored.

### 9. PERINATALITE (`perinatalite/`)

Written on 2026-11-13 (D18).

| State | Section | Variables |
|---|---|---|
| ◐ | PERINATALITE: `perinatal`, with the birth weight (`poidsna`) that the dictionary files under SOCIAL - PERINATALITE | 10 + 1 |

### 10. EVALUATION MEDICALE (`evaluation_medicale/`)

Written on 2026-11-13 (D18).

| State | Section | Variables |
|---|---|---|
| ◐ | Caractéristiques du trouble vie entière, 12 DERNIERS MOIS, MODE EVOLUTIF: `psychosis_course` | 8 |
| ◐ | SYMPTOMES VIE ENTIERE: `lifetime_symptoms` | 44 |
| ◐ | COMPORTEMENTS VIOLENTS: `violent_behaviours`; `rad_ecv_vp5` ignored (O21) | 24 |

All 76 columns of the tab are read.

### 11. SOIN SUIVI HOSP ARRET TRAVAIL (`soin_suivi_hosp_arret_travail/`)

Written on 2026-11-13 (D18).

| State | Section | Variables |
|---|---|---|
| ◐ | HOSPITALISATION: `hospitalisations_v0` | 6 |
| ◐ | LES 12 DERNIERS MOIS: `hospitalisations_12m` | 4 |
| ◐ | Suivi des Recommandations: `recommendations` | 8 |
| ◐ | ACTUEL, LES 12 DERNIERS MOIS // DEPUIS LA DERNIERE VISITE: `sick_leave_v0`, `sick_leave_fu` | 9 |

All 27 columns of the tab are read.

### 12. SOCIAL - PERINATALITE (`social_perinatalite/`)

Written on 2026-11-13 (D18).

| State | Section | Variables |
|---|---|---|
| ◐ | MODULE SOCIAL: `social`; `empjob` ignored (O2); answers lost in `maristat` and `saltyp` (O22) | 12 |
| ◐ | PERINATALITE: the birth weight, in `perinatal` | 1 |

All 13 columns of the tab are read or ignored.

### 13. TRAITEMENTS (`traitements/`)

Written on 2026-11-13 (D19).

| State | Section | Variables |
|---|---|---|
| ◐ | TRAITEMENTS (help with the treatment): `treatment_help` | 2 |
| ◐ | Traitement non pharmacologique: `non_drug_fu` | 14 |
| ◐ | Modification de la prise en charge non médicamenteuse: `care_changes` | 6 |
| – | Classe de traitements psychotropes: six flags ignored (O25) | 6 |
| ◐ | Nombre de traitements psychotropes: `medication_classes`, once per patient | 6 |
| ◐ | Données détaillées des traitements psychotropes: `medications` (the table `treatments`) and `medications_at_visit` | 11 |

All 45 columns of the tab are read or ignored.

### 14. ANTECEDENTS (`antecedents/`)

Written on 2026-11-13 (D20). Each medical section has an inclusion schema (`_v0`) and a
follow-up schema (`_fu`).

| State | Section | Variables |
|---|---|---|
| ◐ | Pathologies neurologiques: `neurological_history`; the migraine columns are swapped (O24) | 11 |
| ◐ | Pathologies cardio-vasculaires: `cardiovascular_history` | 9 |
| ◐ | Pathologies endocriniennes et métaboliques: `endocrine_history` | 10 |
| ◐ | Pathologies dermatologiques: `skin_history` | 11 |
| ◐ | Antécédents gynécologiques: `gynaecological_history` | 3 |
| ◐ | Pathologies hépato-gastro-entérologiques: `digestive_history` | 14 |
| ◐ | Pathologies allergiques, chk_somat_all_specifier: `allergic_history`; `asthme_mhoccur` and `allergie_mhoccur` ignored | 1 + 2 |
| ◐ | Autres pathologies: `other_history` | 8 |
| ◐ | Pathologies auto-immunes: `autoimmune_history` | 26 |
| ◐ | Enfants, Fratrie, Parents: `family_structure` | 10 |
| ◐ | Antécédents filles, fils, sœurs, frères, maternels, paternels: `family_history` (the table `relatives`) and `family_history_per_patient` | 44 |

All 149 columns of the tab are read or ignored.

### Columns of the extraction that the dictionary does not list

| State | Columns (by the start of their name) | Number |
|---|---|---|
| ◐ | `slc*` | 28 |
| ◐ | `later*` | 24 |
| ◐ | `simil*` | 19 |
| ◐ | `rad*` | 13 |
| ◐ | `cvlt*` | 6 |
| ◐ | `chk*` | 2 |
| ◐ | `wais*` | 1 |
| ◐ | `sudosnb*` | 1 |

201 columns. Each was taken with the tab of its instrument: all are read or ignored.
