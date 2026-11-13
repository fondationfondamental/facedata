# FACE BP — progress, decisions and open questions

Extraction: `BPALL_20261030.tsv` (22,077 rows × 2,236 columns, 6,476 patients).
Dictionary: `FACEBP_thesaurus_V4.34.xlsx`.

## Stages

| Stage | Content | State |
|---|---|---|
| 1 | Specs: `ARCHITECTURE.md`, `SCHEMA_SPEC.md`, the first 17 schemas, this file | Written, waiting for review |
| 2 | Generic pipeline, proven on those 17 schemas | Done on 2026-11-12: 40 tests pass, the numbers below are reproduced, the report renders |
| 3 | BP tab by tab, in the order below | In progress. PATIENT (five schemas), HETERO-QUESTIONNAIRES (seven), CONSTANTES et ECG (three), BILAN BIOLOGIQUE (seven) AUTO-QUESTIONNAIRES (23 more, 25 with the two BIS) NEUROPSYCHOLOGIE (11 more, 21 in all), SUICIDE (six), SUBSTANCES ET COMORBIDITE (nine) and PERINATALITE (one) written on 2026-11-12, EVALUATION MEDICALE (13 more, 15 in all) and SOIN SUIVI HOSP ARRET TRAVAIL (six) on 2026-11-13, waiting for review |

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
| D11 | 2026-11-12 | General rule: a stored value that the EMR computed from another stored value is marked `derived_from` it and is flagged `derived_doubt` wherever that other value fails its check. Its first application, to the WAIS-III vocabulary scaled score, rested on a wrong premise and is replaced by D19 |
| D12 | 2026-11-12 | A follow-up visit takes the DSM version of the patient's inclusion. `dsm_criteria` is read once per patient (`level: patient` in the `version` block) and given to all the visits of that patient |
| D13 | 2026-11-12 | TMT z-scores written in the old sign convention are flipped, so that a higher z-score always means a better performance. The date of the change is found for each centre from the data (`sign` block, pipeline step 8). Values within 90 days of it get `sign_doubt` |
| D14 | 2026-11-12 | From 2022 the follow-up form is the DSM-5 form for everyone. A follow-up visit dated from 1 January 2022 is read as DSM-5, whatever the patient's inclusion (`follow_up` in the `version` block). The centres changed between the end of 2021 and May 2022; 31 visits of early 2022 still hold a mixed-episode count, which is then not read |
| D15 | 2026-11-12 | A patient with no DSM criteria recorded at inclusion gets the version of the inclusion year: DSM-IV before 2020, DSM-5 from 2023 (`by_inclusion_date`, flag `version_inferred`). Included in 2020 to 2022, the version stays unknown |
| D16 | 2026-11-12 | `screening` is a visit of its own, before `V0`, with no `visit_month` (was O4). All 3,973 patients with a screening row also have a V0, a median of 70 days later. 137 columns hold values at screening that differ from the patient's V0, and the MDQ is recorded at screening only |
| D17 | 2026-11-12 | One question stored in two columns is one variable. The end-of-follow-up form exists in two generations of columns (`*_patient` until about 2022, `*_stopsuivi` from 2018) with the same answers: each variable reads the new column first, then the old one (`column: [new, old]`, flag `column_conflict` when they differ). This is not a change of instrument, so D9 does not apply |
| D18 | 2026-11-12 | Patient-level variables: flags are given once per patient, on the first visit, and the QC table counts patients. Dates have a hard `range` like numbers. A variable with fewer than 20 values gets no figure in the report. Free-text details are delivered as text and never shown in the report |
| D19 | 2026-11-12 | WAIS-III vocabulary: the stored scaled score is right. The norm table, applied to the sum of the 33 items, gives the stored scaled score on 1,191 of 1,210 rows; applied to the stored total, on 198 only. So the EMR used the true total, and only the total column of the extraction is 3 points too low. The scaled score and its z-score are delivered as stored and checked against the table: 19 rows get `derived_doubt`, 12 of them explained by an age one year off (the date of birth is known to the month). This replaces the vocabulary part of D11 |
| D20 | 2026-11-12 | Norm tables are CSV files in `norms/`, outside the repository (copyright). A score can be read in one (`lookup` and `from`); a raw score for which nothing can be read gets `norm_missing`. The key columns gain `age`, the age at the visit, which the lookup needs (was O17) |
| D21 | 2026-11-12 | HETERO-QUESTIONNAIRES conventions. A code that means "not assessed" (0 in the CGI and the EGF) is a missing code. The DSM-IV checklist answers Y and N are delivered as 1 and 0, so that symptoms can be counted. A score needs all its items, as in the EMR. Stored domain scores are recomputed and compared |
| D22 | 2026-11-12 | Three schema features, each needed by an instrument of this tab: `codes` on an item (letters counted as numbers), `minus` and `floor` on a score (the Alda total), and `checks` that name the variable they concern (the CGI efficacy index, first function of `custom.py`). In the report, a site or a year with fewer than 20 values is left out of the figures |
| D23 | 2026-11-12 | TMT z-scores follow z = (mean − raw) / SD: a positive z-score is a better performance (was O19). The data support it in every centre since 2014, and D13 already brings the older values to it. The other formula, quoted in the note on percentile bands, is not used |
| D24 | 2026-11-12 | An EGF cell that holds a band ("60-51") is read as the middle of the band (55.5) and flagged `band_middle` (was O18). New variable field `bands: middle` |
| D25 | 2026-11-12 | CONSTANTES et ECG. These columns have no unit column; a value written on another scale is recognised from its size and converted (`unit_inferred`): heights in millimetres, weights with a lost decimal point, blood pressures in cmHg, ECG intervals in milliseconds or hundredths of a second. A 0 in the ECG measures is a missing code. The body mass index is recomputed from the harmonised height and weight. The QTc is delivered twice: recomputed with Bazett's formula (`qtc_bazett`) and as stored (`qtc_stored`), because 759 visits have a stored QTc and no RR |
| D26 | 2026-11-12 | Schema features added for that tab: a score computed by a function of `custom.py` (`custom`), a tolerance for the comparison with a rounded stored score (`compare_tolerance`), winsorising of a continuous score that asks for it (`winsor`). `unit_inferred` is no longer raised for a value that has no label and is simply in the schema's unit |
| D27 | 2026-11-12 | The second ratings of MADRS and YMRS (the 23 columns ending in `_n1`) are legacy: residuals of data-management experiments. They are not loaded and are listed in `ignored.yaml` (was O5). The schemas `madrs_n1` and `ymrs_n1`, written the same day, are removed |
| D28 | 2026-11-12 | BILAN BIOLOGIQUE. Output units: mmol/L for the electrolytes, urea, glucose, phosphate, calcium, the lipids and lithium; µmol/L for creatinine, uric acid, iron and bilirubin; g/L for proteins; UI/L for the enzymes; mUI/L for TSH; pmol/L for free T3 and T4; G/L for the cell counts (T/L for the red cells); ng/mL for prolactin; mg/L for the drug levels (µg/L for clozapine). The unit column is a default label and proves little, so each analyte lists the scales that occur and the values expected on each; the size of the value decides when the label cannot be right. A label that the form prints wrongly is read as what it can only mean: "mmol/L" for bilirubin is µmol/L, "µUI/L" for TSH is mUI/L, "%" for MCH and MCHC is pg and g/dL, "mg/L" for prolactin says nothing (D31). The LDL unit is read from the form's unit choice first (`rad_chol_hll`), which the export does not copy for that analyte. White-cell counts written as percentages are converted (D30). The cholesterol ratio is recomputed from the harmonised values. A creatinine clearance of 0 is a missing code |
| D29 | 2026-11-12 | Schema features added for that tab: `unit_column` can list two columns; a unit with no factor is recognised but not convertible (`unit_unknown`; replaced by `percent_of`, D30); a unit label that is a censoring mark is not a unit label |
| D30 | 2026-11-12 | White cells written as percentages are converted with the leukocytes of the same visit: value × leukocytes / 100 (was O21). A percentage is recognised by its label (about 6 per kind) or by its size: from 25 for neutrophils, 12 for lymphocytes, 2.5 for monocytes, 1.5 for eosinophils and 0.3 for basophils, a value cannot be a count in G/L. 844 results are converted (461 basophils, 128 monocytes, 108 eosinophils, 84 lymphocytes, 63 neutrophils); 13 have no valid leukocyte count and get `unit_unknown`. The limits were checked against the visit totals: the five kinds now add up to the leukocytes on 98% of the complete visits (96% before). Known limit: an eosinophil percentage under 1.5 is read as a count (about 65 values between 0.6 and 1.5 only add up as percentages); the visit then fails the sum check. Schema feature: a unit with `percent_of` in place of `factor` |
| D31 | 2026-11-12 | Prolactin unit (was O20; what is left of it is the new O20). The extraction has the form's unit column (`prolctn_lborresu`) and the unit choice itself (`rad_prolactine`); they agree wherever a unit was chosen, which is the case for 1,855 of the 6,523 results. A chosen unit is believed: ng/mL or µg/L up to 500, mUI/L from 30. On the other 4,668 results the column holds the default label "mg/L", which is ignored. There, a result under 30 is ng/mL and one of 500 or more is mUI/L. In between, the centre's other unlabelled results within 180 days decide (at least 10 of them): where a quarter or more reach 100, the centre was reporting in mUI/L, so a result of 100 to 500 is mUI/L (248) and one of 30 to 100 cannot be told (34); elsewhere a result of 30 to 100 is ng/mL (351) and one of 100 to 500 cannot be told (140). The 174 that cannot be told are missing, with `unit_unknown`. Evidence: in ng/mL 2% of the results reach 100 (34 of the 1,681 with a chosen unit, 31 of them women's); one centre has two periods (late 2014 to 2017, mid 2021 to mid 2022) in which most of its unlabelled results reach 100, against a few percent outside them; after the rule that centre's median is between 9 and 15 ng/mL in every half-year; men are 37% of the results read as mUI/L by the period, as among the results labelled mUI/L (36%). Sex is used to check the rule, not by the rule. Schema features: `ignore_units` and `unit_rule`, with the function `prolactin_unit` in `custom.py` |
| D32 | 2026-11-12 | AUTO-QUESTIONNAIRES. The scoring keys come from the data, not from the dictionary, which gives none: each stored score was fitted on the items by least squares, which gives the items that enter it and their sign, and the key found was then checked row by row. Every stored total and sub-score of STAI-YA, MARS, ASRM (Altman), QIDS-SR16, PSQI, Fagerström, AQ-12, CTQ, ALS-18, AIM-20, WURS-25, BDHI, CSM, the circadian inventory, MDQ and PRISE-M is exactly reproduced (a handful of rows apart), so each schema recomputes its scores and compares them. Reversed items: ten in STAI-YA, items 7 and 8 in MARS, seven in CTQ, six in AIM, eight in MAThyS. Two scores are not sums and are functions of `custom.py`: the QIDS total (the highest item of each of nine symptoms) and the PSQI latency component. Classes that the EMR derives are delivered as stored after the rule was checked: CTQ severity classes (the limits of the manual), CTQ denial, ASRS and MDQ screening results, STOP-BANG risk. Scores that the extraction lacks are added: ASRS total, AQ-12 total, BDHI total hostility |
| D33 | 2026-11-12 | Three export defects lose answers (O24). Epworth: only the answers equal to 0 are exported, so the scale is not loaded (ten columns in `ignored.yaml`). Fagerström item 3: only the answer "the first cigarette" is exported; an empty cell on a visit where the five other items are filled is read as "any other" (0 point), so the total is recomputed on 5,755 visits where the extraction has it on 3,628. CSM item 7: one of its five answers is never exported (450 visits); nothing is assumed, and the total is missing there |
| D34 | 2026-11-12 | MAThyS. An item above 10 has lost its decimal point and is divided by 10 or 100 (52 cells). The five sub-scores are recomputed with the reversed items; the stored ones are not read, because the EMR added the items without reversing any until 2021 and reverses them from 2022 on. The seven questions on emotions are a schema of their own (`mathys_emotions`) |
| D35 | 2026-11-12 | PSQI. The minutes to fall asleep above 240 are the minutes multiplied by 60 (300, 600, 900, 1800 and 3600 are frequent, and these patients answer item 5a like those who wrote 5, 10, 15, 30 and 60 minutes): they are divided by 60 (277 values). Values from 1260 to 1439 are bedtimes typed in that field and end `out_of_range` (83). The latency component is recomputed from the corrected minutes, and the total from the components: they differ from the stored ones on 232 and 231 visits. The other components are exactly what the manual says and are delivered as stored. Times are delivered in hours, as written |
| D36 | 2026-11-12 | ALS, AIM and WURS were reduced in 2021 (54 to 18, 40 to 20 and 61 to 25 items). The extraction holds only the items of the reduced forms, for every year, and the scores of those items. One set of columns is delivered for all visits (default of O23). For ALS the data tell the two forms apart: `als_form` is `long54` where a score of the 54-item form is stored (4,650 visits) and `short18` elsewhere (1,487). The three scores of the long form whose items are not exported (anxiety-depression, anxiety, bipolar) are delivered as stored on `long54` visits only. MARS items are read as 1 = no (D37). Superseded by D47 for ALS and WURS |
| D37 | 2026-11-12 | MARS items 1 to 10 are coded 1 = no and 0 = yes, confirmed by the project lead (was O22). The dictionary's coding, 1 = yes, is wrong for these ten items; it is right for `mars11`. The schema is unchanged: the items are delivered as stored and the total is the MARS score |
| D38 | 2026-11-12 | Percentile bands. A new type, `band`, reads a percentile column that mixes plain numbers (`50`), bands (`25 - 50`, `50 - 25`, `[25-50]`) and one-sided classes (`>95`, `<5`, `>10`). The value is the lower limit of the band, on the list of limits the schema gives (TMT and fluency: 5, 10, 25, 50, 75, 90, 95; CVLT: 1, 5, 25, 50, 75, 95, 99). A plain number is the band that starts there. A cell that names less than one band keeps the band that starts at the limit written and gets `<variable>_cens`: +1 for `>10` (this band or a higher one), -1 for `<10` (the band under 10, or a lower one). This follows the proposal of the note taken from the EMR code (`norms/tmt-cvlt-percentile-bands.md`). The three TMT time percentiles and the two fluency percentiles are read this way, and almost all of their cells are full bands; the share of each band is the same in every period |
| D39 | 2026-11-12 | CVLT. The standardised columns hold a z-score or a percentile depending on the measure and the age group, exactly as the note says (percentile up to 69 years for trial 5, up to 39 for the four delayed recalls, from 40 to 69 for semantic clustering; z-score otherwise). A z-score is always written with two decimals and a percentile as a band or a whole number, so the cell itself tells what it holds: each of the six mixed columns feeds two variables that share it (`shared: true`), a band and a z-score. The z-scores are also turned into bands (D44). A z-score of a recall beyond 5 is out of range: the z-score of trials 1 to 5 is above 5 on 246 visits for ordinary raw totals, two thirds of them in 2009, 2013 and 2014, and that of semantic clustering on 100 visits, most in 2012 and 2013. On 43 visits the recency z-score was computed from an empty recency, as if it were 0 (-5.77); a custom check flags these (`check_failed`). The total of trials 1 to 5 is recomputed (54 mismatches) |
| D40 | 2026-11-12 | The other tests of NEUROPSYCHOLOGIE. Scores are recomputed where the formula could be read from the data: Stroop interference (colour-word minus A x B / (A + B) on the scores corrected for age; 29 mismatches), spatial span (item scores added, an empty item counting 0; 41 mismatches on the total), fluency rule breaks, COBRA total (none), errands total errors (9). Standard scores that come from norms (Stroop T-scores, spatial span and SCIP scaled scores, fluency z-scores) are delivered as stored; the z-scores written next to a T-score or a scaled score are that score brought to mean 0 and SD 1 in every row. CPT-II and CPT-3 are two instruments with their own columns and two schemas; their values, T-scores, percentiles and printed guidelines are delivered as stored, within wide limits. The trials and item scores of the WAIS digit span are added to the two digit-span schemas, with a check of each stored raw score against its item scores. The column `wais` repeats `wais_version` and is ignored |
| D41 | 2026-11-12 | Two changes to the generic reading. A number written without its leading zero (`.45`, `-.02`) is read (`format_repaired`); it was `unparsed`. A cell is empty when nothing is left of it after the text repairs: two cells hold only an escaped line break |
| D42 | 2026-11-12 | The four TMT error percentiles (`tmta02a_`, `tmtb02a_`, `tmtb05a_`, `tmtba02a_`) are not read as stored. Most patients make no error, several limits of the norms then fall on the same number of errors, and the EMR changed twice what it writes in that case. A patient with no error in part A has `>95` until 2015 (1,662 of 1,935 visits), `>5`, `>10` or `>25` from 2016 to 2021, and `<5` (426 visits) or `>10` from 2022. The share of the top band goes from 76% to 1% and 4% over the three periods, so the column holds three scales and a cell does not tell which. The numbers of errors and their z-scores are delivered, and the bands are recomputed (D43). Found on the report page of the variable (panel of the levels per year); all other band variables were then compared across the three periods and are stable |
| D43 | 2026-11-12 | The four TMT error bands are recomputed (was O26, answered by the project lead). They are read in the norm tables of the EMR note, from the number of errors (corrected plus uncorrected; the stored difference for B minus A), the age at the visit and the years of education entered on the neuropsychology form. The tables are four files of the `norms/` folder, written from the note by `norms/make_tmt_error_tables.py` (neither is in the repository). A number of errors on which several limits of the norms fall gets the lowest band it can be, with `<variable>_cens` = +1 (this band or a higher one): 5,290 of 5,836 visits for part A. With one rule for every year, the share of each band changes by 6 points at most between the periods (75 points before). Against the cells the EMR wrote from 2016 to 2021, the same band on 93% of the visits for part B, 98% for the perseverative errors, 95% for B minus A and 87% for part A; for part A no count of errors (corrected, uncorrected or both) reproduces the EMR's cells better than 89%. Schema features: a norm table can depend on a second variable (`by`, columns `by_min` and `by_max`) and can mark open bands (column `cens`); a variable with `keep: false` may read a column that another schema delivers |
| D44 | 2026-11-12 | CVLT: one band per measure for every age (was O25, answered by the project lead). Where the cell holds a z-score, the band is the one the z-score has under the normal law, as the EMR note proposes, and the cell gets the new info flag `band_from_z`; a z-score outside its range gives no band (`out_of_range`). The six measures that only have a z-score (trial 1, trials 1 to 5, list B, primacy, recency, bias) get a band variable too. The z-score variables are still delivered. Schema feature: `z_range` on a band. Result: `cvlt_trial5_band` on 5,820 visits (68 from a z-score), the four delayed recalls on about 5,810 each (about 2,920 from a z-score), `cvlt_semantic_band` on 5,029 (2,495). Limit found by comparing the two sources: for trial 5 and the delayed recalls, 18% to 28% of the bands read from a percentile are the top band (99), because the EMR writes the highest percentile when a perfect recall falls on several limits of the norms; of the bands computed from a z-score almost none is above 75. The two halves of a mixed band were therefore not on one scale at the top; the table half is recomputed in D45 |
| D45 | 2026-11-12 | CVLT: the bands that the EMR read in a table are read again from the raw scores (was O27, answered by the project lead). Where the cell holds a percentile, the band comes from the norm table of the measure, the raw score and the age at the visit; the cell only tells that the EMR used a table. Eleven measures: trial 5, the four delayed recalls, semantic clustering, perseverations, intrusions, correct and false recognitions, discriminability. The tables are files of `norms/`, written from the EMR note by `norms/make_cvlt_tables.py` (neither is in the repository). One rule for every test: a raw score on which several limits fall gets the lowest band it can be, with `<variable>_cens` = +1; the EMR wrote the highest (every cell written 99 for trial 5 and the delayed recalls is a perfect recall of 16 words). Where no limits coincide, the recomputed band is the EMR's on 98% to 100% of the visits. Serial clustering is left as the EMR wrote it: the note gives its table in whole numbers for a decimal index, and the bands read in it differ from the EMR's on 9% of the visits (O28). What remains between the two sources of a mixed band is no longer a difference of rule: 12% to 27% of the table bands are open bands at the top of the scale (the perfect recalls) against 1% to 4% of the bands computed from a z-score, where a perfect recall is most often one band lower. Schema feature: `lookup` and `from` on a band variable |
| D46 | 2026-11-12 | SUICIDE. The five questions on suicidal thoughts and acts (`isf01` to `isf05`, with "when did it last happen") are two forms in the same columns: about the whole life at the inclusion visit (38% have attempted suicide), about the time since the last visit at follow-up (3%; 93% of the patients who said yes at inclusion say no later; the "when" answers differ too). They are two schemas with their own output columns, `isf_lifetime` and `isf_since_visit`, split by a version read from the visit label (`isf_form`). The date of the first attempt holds 2011-11-11 in 1,133 cells: a placeholder, read as a missing code. The two Columbia sections (most violent and most serious attempt) are delivered as categories; each method has its own lethality scale and its own column, with short codes in the order of the scale. A drug type "Inconnu" is a missing code. C-SSRS: the items as stored, and the sum of the five intensity ratings is added. Yes/no answers are delivered as 1 and 0 |
| D47 | 2026-11-12 | ALS and WURS are split by form (was O23 for these two; the project lead asked the developers of the EMR: the ALS was replaced by the ALS-18 and the WURS by the WURS-25). Four schemas with their own output columns: `als54`, `als18`, `wurs61`, `wurs25`. The schema `als` and the output columns `als05` to `als46`, `als_total` and its three sub-scores, `wurs03` to `wurs59` and `wurs_total` are gone. The extraction stores both forms in the same columns (the 18 and the 25 questions that the reduced forms kept), so each long-form schema delivers those items, a bridge score from them (`als54_total18` and three sub-scores, `wurs61_sum25`) and, for the ALS, the three stored scores of the 54-item form. Which form a visit used: the long one (`als54`, `wurs61`) when the visit holds something that only the long questionnaires have, a score of the 54-item ALS (`als58`, `als60`) or one of the 22 items that only the BIS-10 has; `als18` when it holds ALS answers and none of those; `wurs25` when it holds ALS or BIS answers and none of those. The BIS is used because the reduced questionnaires arrived together: of the 6,085 visits that have an ALS and a BIS, 99.2% have the two in the same generation, and the 45 visits with ALS answers, a BIS-10 and no score of the 54-item ALS are long questionnaires with unanswered items (their `als57` is empty or differs from the 18-item score). The switch is sharp in each centre (with one date per centre, 7 of 513 visits are on the wrong side) but the dates go from September 2021 to May 2022, so one date for the cohort would misplace 72 visits; 22 visits before September 2021 hold an ALS-18 and a BIS-12. Result: `als_form` 4,695 `als54` and 1,442 `als18`; `wurs_form` 4,639 `wurs61` and 1,435 `wurs25`. For the WURS the rule is an assumption (O30): nothing in its own columns shows that it changed with the ALS and the BIS. 49 visits have a WURS and neither an ALS nor a BIS: `version_unknown`, answers not delivered. Where both forms were in use (July 2021 to June 2022) the common scores have the same mean in the two forms: 1.44 and 1.40 for the ALS, 35.5 and 35.5 for the WURS; the higher WURS sums of the later years (38 to 41, against 33 until 2020) are therefore a change over time, not an effect of the form. AIM stays one schema: the developers' message does not name it (O23). Schema feature: the columns of `filled` may belong to another instrument of the same visit; a visit where the instrument itself is empty has no version |
| D48 | 2026-11-12 | Suicide questions at follow-up, 2022 and 2023 (was the first half of O29, decided by the project lead after the COVID explanation was tested on the data and not supported; the evidence is in O29). Every "yes" to the five questions at a follow-up visit dated from 2022-01-01 to 2023-12-31, and the "when" answer that goes with it, keeps its value and gets the new discrepancy flag `period_doubt`. The "no" answers and the inclusion visits are not flagged. All centres are flagged alike: the schema does not name centres. Result: 1,445 "yes" answers (114 to "attempted suicide", 445 to the first question) and 1,243 "when" answers, on 467 visits of 402 patients. Many of them are true: before 2022 already 35% of the follow-up visits said yes to the first question and 2% to 4% to the last. The flag says that the answer cannot be told from an answer about the whole life, not that it is wrong. Schema feature: `doubt` on a variable (a period of visit dates, optionally the values concerned, a note) |
| D49 | 2026-11-12 | SUBSTANCES ET COMORBIDITE. Nine schemas. Tobacco is one schema (`tobacco`): the status of the day at every visit, with pack-years and the ages at which the patient started and stopped; "Statut inconnu" is a missing code and a value above 200 pack-years is out of range. The four comorbidity sections (anxiety disorders, substance use disorders, eating disorders, somatoform disorders) are filled at the inclusion visit and at the yearly visits, in the same columns, and the two do not answer the same question. At inclusion 48%, 37%, 20% and 3.6% of the patients have the disorder; at the yearly visits 35%, 23%, 14% and 1.7%. Of the patients answered "yes" at inclusion, 41%, 40%, 50% and 74% are answered "no" at a later visit. For the substances the question is about the whole life ("has or has had"), so a yes cannot become a no; it does in every centre (50% to 74% still "yes" in the eight centres with 40 answers or more) and in every period. The details given after a yes still describe the whole life at the yearly visits: the age at onset is the one given at inclusion on 62% of the visits and the cumulated durations have the same size. Each section is therefore two schemas with their own output columns, ending in `_v0` (inclusion) and `_fu` (yearly visits), split by `comorbidity_form`, which is read from the visit label, as for the suicide questions (D46). What the yearly form asks was O31, answered in D50. Other choices. Yes/no answers are 1 and 0 and "U" is a missing code. The first substance question is read in `rad_tb_subst_raw`; `rad_tb_subst`, a copy as 0 and 1 without the "unknown" answers, is ignored. The boxes of the anxiety disorders are filled only after a "yes" and stay missing after a "no" (was O32, changed in D50), whereas those of the substances are 0 after a "no" (the export writes them). Panic disorder: the form has an age at onset and a "symptoms in the past month" for each of its two boxes (with and without agoraphobia), but clinicians fill either one whatever the box, so the two columns are read as one detail of the panic disorder (5 `column_conflict`). Four columns that the dictionary does not list are read: the box "panic disorder" and the boxes of the three last anxiety disorders. Durations of the substance disorders are numbers in months, out of range above 840. Ages at onset are delivered as written. Three free-text columns are delivered as text |
| D50 | 2026-11-12 | Comorbidities, two answers of the project lead. (1) The yearly form asks the same questions as the inclusion form, about the time since the last visit (was O31). The two sets of columns of D49 stay (confirmed by the project lead): an answer about the time before the inclusion and an answer about the time since the last visit are two variables, as for the suicide questions (D46). The titles and notes of the eight schemas say it. (2) The boxes of the anxiety disorders are read as 0 where the patient has no anxiety disorder (was O32): a patient with no anxiety disorder has no panic disorder. They then behave like the boxes of the substances, which the export writes as 0 after a "no". 2,650 inclusion visits and about 2,950 yearly visits get these zeros for each of the twelve boxes: `panic_disorder_v0` goes from 2,476 to 5,126 visits and its mean from 32% (among the patients with an anxiety disorder) to 16% (among all patients). Where the first answer is unknown or empty the boxes stay missing, and so do the ages at onset and the "symptoms in the past month" after a "no". No flag: no cell is changed, and the first answer is delivered next to the boxes. One visit has a ticked box after a "no"; it is kept as written. Schema feature: `asked_if` on a yes/no variable (the question is asked only after a yes to another one) |
| D51 | 2026-11-12 | PERINATALITE. One schema, `perinatal`: the patient's own birth (age of each parent, term, gestational age, type of birth, stay in a neonatal unit, weight, length, head circumference, two Apgar scores). The eleven columns are in the extraction under the names of the dictionary's column "NOM VARIABLE EXTRACTION"; this sheet has a code-list column before the names, which the dictionary helper now skips. One value per patient (`level: patient`): the first visit that has it, the inclusion visit for 99% of the patients; where the form was filled again at a yearly visit, one answer in five differs, the first is kept and the patient gets `patient_value_varies` (197 flags). A 0 is a missing code in the five measures, the gestational age and the two ages: in 2009 and 2010 the form saved a 0 where nothing was known (57 of the 67 visits with a 0; an Apgar of 0 at one minute always comes with a 0 at five minutes). An age of 99 is a missing code. Gestational age: 6 to 9 are months and are converted to weeks (14 patients, `unit_inferred`); 22 values are out of range, 12 of them birth weights typed in this field. Hard limits: weight 400 to 6,500 g, length 25 to 60 cm, head circumference 20 to 42 cm, Apgar 1 to 10, mother's age 12 to 60, father's age 12 to 90. Values that may be another scale (a weight of 35) are not converted: the cell does not tell whether it is hectograms or weeks. The numbers were first winsorised like the others (was O33, changed in D52) |
| D52 | 2026-11-13 | Birth measures are not winsorised (was O33, decided by the project lead): `winsor: false` on the birth weight, the birth length, the head circumference and the gestational age. A very low birth weight or an extreme prematurity is the information these variables carry, and their hard limits already remove the impossible values. The default would have brought 49 weights to 1,620 g or 4,730 g and 11 gestational ages to 28 or 43 weeks |
| D53 | 2026-11-13 | EVALUATION MEDICALE, the sections left: 13 new schemas, 15 in the tab. (1) Five mood sections are split by DSM version like the follow-up form (D9, D12, D14, D15), because the two forms differ: first episode, whole life, year before inclusion, most recent episode at inclusion, current episode. Only the DSM-IV form has mixed episodes (counts, and a mixed type of episode); the specifiers of a depressive episode differ ("mixed" is DSM-5 only); three columns exist in the DSM-5 form only. `dsm_criteria` is filled on every inclusion visit that has a mood form (5,626 of 6,476). (2) The current episode is asked at every visit and describes the day of the visit, so inclusion and follow-up visits are in the same columns; the DSM version of a follow-up visit follows D12 and D14. (3) The psychotic disorder section offers the same disorders in both DSM forms and is not split by DSM version. It is split like the comorbidities (D49, D50) into `_v0` and `_fu` columns with `comorbidity_form`: of the 73 follow-up answers of patients with a psychotic disorder at inclusion, 69 are "no". (4) Yes/no answers are 1 and 0 in the whole tab; the two schemas of the follow-up form, written earlier with "yes" and "no", are changed. (5) A box or a count asked only after a yes is 0 after a no (`asked_if`, extended from yes/no boxes to counts; confirmed by the project lead): the boxes and counts of the year before inclusion where there was no mood episode that year (879 DSM-IV visits), those of the follow-up form where there was none since the last visit (3,972), and the numbers of episodes with psychotic features and of induced episodes where the answer to "at least one" is no. (6) Not loaded: the four lifetime columns `mhoccur_*_lt`, which the export writes on every row ("Y" where the count is 1 or more, "N" everywhere else, also where the count is unknown or empty), and three `_psy_spv` columns that are copies of the lifetime ones. The boxes of the year before inclusion are exact functions of the counts too, but are delivered because the follow-up form has the same pair. (7) The type of the most recent episode recorded at follow-up (`cetermepisode_recent_type`, filled where there was an episode since the last visit) is added to the two schemas of the follow-up form. (8) The three columns of the dictionary section "New Columns" have no label: `age_ehman` and `age_epman` are filled exactly where the patient has had a hypomanic or a manic episode and are read as the age at the first one; `rad_agethym` keeps its name (O34). (9) Counts are numbers; ">20" is right-censored at 20. Dates: 1000-01-01 is a placeholder. (10) DIVA: one schema, 50 patients; the number of criteria of each block is recomputed where the nine are answered (7 `score_mismatch`). 38 visits hold mood data and no DSM version (D15): `version_unknown`, not delivered |
| D54 | 2026-11-13 | SOIN SUIVI HOSP ARRET TRAVAIL: six schemas. (1) Hospitalisations. The number and the total duration are asked about the whole life at the inclusion visit and about the time since the last visit at every follow-up visit, in the same columns; the dictionary says so in the title of the section, and the data agree (2.5 hospitalisations on average at inclusion, 0.17 at follow-up). They are two schemas, `hospitalisations_v0` and `hospitalisations_fu`, with `_v0` and `_fu` columns. The age at the first hospitalisation and the 12 months before inclusion are in `hospitalisations_v0`. (2) Sick leave. The inclusion visit (the 12 months before, and the day of the visit) and the follow-up visits (since the last visit) already have columns of their own: `sick_leave_v0` and `sick_leave_fu`. "Non applicable" (no job) is a missing code. (3) The use of care and the following of the recommendations are follow-up forms: `care_use` and `recommendations`. (4) Asked only after a yes (`asked_if`): the number and the duration of the sick leaves are 0 after a "no"; the boxes of each part of the use of care are 0 after a "no" to the part, and each number after a "no" to its box. (5) Durations in months are a list with a quarter, half and three quarters of a month, read as 0.25, 0.5 and 0.75; ">20" is censored at 20 and the age "<5" at 5. (6) Hard limits: 52 weeks of hospitalisation and 53 weeks of sick leave in 12 months, 260 weeks of sick leave since the last visit, 52 sick leaves, 365 consultations. Cells with words ("2 semaines", "1 fois par mois") end unparsed (193). (7) One version column for the split by kind of visit: `visit_form` (inclusion, follow_up) replaces `isf_form` (D46) and `comorbidity_form` (D49), which were the same thing under two names. (8) Counts and durations of events are not winsorised (`winsor: false`), in this tab and in the episode counts of EVALUATION MEDICALE. Most of their values are 0, more so since a "no" gives a 0 (D50, D53), so their 99th percentile is 0 or 1 and the default brought every rarer value down to it. This corrects D53: `dsm4_fu_n_mixed_psychotic` had its 43 values above 0 turned to 0; in this tab three numbers of unscheduled consultations would have been. The durations of the substance disorders and the pack-years, which are not mostly 0, keep the default |

## Open questions

Each has a default that the schemas already follow. Answer when the
instrument is reached, or earlier.

| # | Question | Default used | Needed for |
|---|---|---|---|
| O1 | BIS reversed items: the extraction scores them `6 − value`, the usual rule on a 1 to 4 scale is `5 − value`. Which do we keep? | `5 − value`; stored scores are compared with a documented offset | BIS-10, BIS-12 |
| O2 | A left-censored result `<5`: is the value the limit (5) or half of it (2.5)? | The limit, with `<variable>_cens` = −1 | Biology |
| O3 | CRP has 389 results that are exactly 0. Real zeros, or "below the limit" with an unknown limit? | Kept as 0 | Biology |
| O7 | Family history (about 380 columns): summaries per patient, a long table, or left out? | Undecided | ANTECEDENTS |
| O8 | Current treatments are exported as Python lists in one cell (`med_psy_*`). What should a treatment variable look like for modelling? | Undecided | TRAITEMENTS |
| O12 | Norm tables. Received on 2026-11-12: WAIS-III vocabulary, 12 age bands, cited as "Wechsler, 1997"; it has not been checked against the French manual, which is not in the document folder. The TMT norm tables (times and errors, by age and education) and the CVLT percentile tables came on the same day in a note taken from the EMR code; the note says they were not checked against the publications. The four TMT error tables and eleven CVLT percentile tables are used (D43, D45). Still expected: the CVLT regressions for the z-scores, and the tables of the other tests | The tables are used as received (D19, D43) | WAIS-III vocabulary, TMT, CVLT |
| O15 | The generic code is 2,296 lines (blank lines and comments included), against a budget of about 1,300. The largest files are `harmonise.py`, `schema.py`, `plots.py` and `pipeline.py`. Trim, or raise the budget? | Left as it is | All |
| O16 | What do the codes of `formoppos` (1 for 610 patients, 2 for 3 patients; filled mostly from 2021) and `social_protec` (0, 1, 2) mean? The dictionary gives no label and no coding. If `formoppos` records an opposition to the use of the data, the 3 patients with code 2 may have to be excluded | Both delivered with their codes as written | PATIENT, Inclusion |
| O20 | Prolactin: 174 results cannot be given a unit (D31). 140 are between 100 and 500 at a time when their centre was not reporting in mUI/L: men are 16% of them, which suggests that roughly a quarter are in mUI/L and the others are truly high values in ng/mL. 34 are between 30 and 100 at a time when their centre was reporting in mUI/L. Twelve centres are concerned, and one has a third of them. Can the PI or the centres say which laboratories reported in mUI/L, and when? | Missing, with `unit_unknown` | BILAN BIOLOGIQUE |
| O23 | AIM: the dictionary lists it among the questionnaires reduced in 2021 (40 to 20 items), but the developers' message names only the ALS and the WURS (D47). Was the AIM-40 replaced by an AIM-20 too? If so it is split like the two others, with the same rule. Its score has the same mean in every year (3.8), and from July 2021 to June 2022 it is 3.86 on the visits of the long questionnaires and 3.74 on the others | One schema `aim` for all visits | AUTO-QUESTIONNAIRES |
| O24 | Three export defects lose answers: Epworth (answers 1 to 3 of every item), Fagerström item 3 ("any other cigarette"), CSM item 7 (one of five answers). Can the extraction be corrected? | D33 | AUTO-QUESTIONNAIRES |
| O28 | CVLT serial clustering: the EMR note gives the limits of its percentile table in whole numbers, but the index has decimals, so the table cannot be applied exactly (9% of the bands differ from the EMR's). Can the exact limits be taken from the EMR code (`CVLT_PERCENTILE_NORMS`)? Its band would then be recomputed like the eleven others. | The band as the EMR wrote it (its best scores are written 99) | NEUROPSYCHOLOGIE |
| O29 | Suicide questions at follow-up: 2% to 4% of the follow-up visits report an attempt since the last visit from 2012 to 2021, 16% in 2022, 9% in 2023, then 2% to 3% again. The four other questions rise too. Could it be COVID (asked by the project lead)? The data say no for most of it. (1) Dates: 3.4% in 2020 and 3.7% in 2021, against 1.5% to 2.5% before, which may be COVID; the jump starts in the first quarter of 2022 (14%), peaks in the third (22%) and stops in the first quarter of 2024 (1.6%). (2) Centres: of the eight centres with 30 answers or more in 2022-2023, five rise (12% to 31%) and three stay at 2% to 3%. (3) The MADRS item on suicidal thoughts, rated by the clinician at the same visits, has no peak in 2022-2023 in these five centres. (4) On the "yes" visits of 2022-2023 the lifetime history was typed again: the number of attempts is the number given at inclusion on 24 of 41 visits (17 of 85 from 2012 to 2019), and a date of first attempt before the inclusion is written on 32 visits (1 to 3 in each other period). (5) In the five centres, 34% of the patients who had ever attempted suicide at inclusion answer yes in 2022-2023 (4% before), and 7% of those who never had (0.7% before). It looks like answers about the whole life entered at part of the follow-up visits, starting when the reduced questionnaires arrived. The cell does not tell which answers, so the "yes" answers of these two years are flagged (D48). Still open, for the five centres or the developers: what changed in the follow-up form in early 2022 and again in early 2024? With the answer the flag could be narrowed to the visits concerned, or removed | Flagged `period_doubt` (D48) | SUICIDE |
| O30 | WURS: no column of the WURS tells the 61-item form from the 25-item one. The form of a visit is read from the ALS and the BIS of the same visit, assuming that the three reduced questionnaires were put in service together in each centre (D47). Can the developers confirm it? 49 visits have a WURS and neither an ALS nor a BIS, so no form: their answers are not delivered | As D47 | AUTO-QUESTIONNAIRES |
| O34 | `rad_agethym`, a column of the DSM-5 inclusion form with no label in the dictionary (915 ages, 60 "Ne sais pas", from 2020): what age is it? It is later than the age at the first episode for 511 of 625 patients (by a median of six years) and almost never before the age at the first psychotropic treatment (3 of 893; equal for 309), so it looks like the age at the first mood stabiliser | Delivered as `dsm5_agethym`, with that guess in its label | EVALUATION MEDICALE |

Answered on 2026-11-12: O4 became D16, O9 became D11 then D19, O10 became D12, O11 became D13, O13 became D14, O14 became D15, O5 became D27, O17 became D20, O18 became D24, O19 became D23, O21 became D30, O20 became D31 and the new O20, O22 became D37, O26 became D43, O25 became D44, O27 became D45.

## What the project lead told us about the EMR

Received on 2026-11-12. These describe the EMR application as it is now; the
extraction also holds data typed in its earlier versions.

| Subject | Fact | Consequence here |
|---|---|---|
| WAIS vocabulary | The psychologist enters the 33 item scores. The application computes the raw total and reads the scaled score in the norm table with the patient's age. The scaled score field is read-only | D19: the stored scaled score is trusted and checked against the table |
| TMT z-scores | One convention for every patient: z = (mean − raw) / SD, so a positive z-score is a better performance. The sign flip of 2012 to 2014 is in the historical data | D13 confirmed: `relation: negative` is the EMR's convention, and the old values are flipped to it |
| TMT percentiles | One numeric column for the z-score, one text column for the percentile band ("50 - 25", "> 95") | The percentile columns are ordered bands; the plain numbers of the years until 2015 are historical |
| CVLT | For several measures (trial 5, short- and long-delay recall, semantic clustering and others) the same `_std` column holds a z-score or a percentile band, depending on the patient's age group | With NEUROPSYCHOLOGIE: one raw column gives two outputs, a z-score and a band, chosen by what the cell holds |
| Percentile bands | A note taken from the application's code, kept in `norms/tmt-cvlt-percentile-bands.md` (outside the repository). TMT norms by age (under 40, 40 to 59, 60 and over) and years of education (under 6, 6 to 11, 12 and over), in eight bands from "P ≥ 95" to "P < 5". CVLT norms by age group (39 and under, 40 to 69, 70 and over), in eight bands from "P ≥ 99" to "P < 1", and the list of which CVLT measure gives a percentile or a z-score in each age group. For error counts a percentile band says little: no error can fall in a low band | With NEUROPSYCHOLOGIE: an ordered band type with these two lists of bands; the age at the visit tells which CVLT cells should hold a z-score. Recomputing a TMT band needs the years of education (SOCIAL tab). The z-score formula quoted in the note is not the one used (D23) |
| DSM version | The EMR stores no DSM version. The inclusion visit has DSM-5 forms only (mood, psychotic, comorbid). The six-month and yearly visits have a "current mood disorders" form that cites no DSM version. The "État du patient" form, filled at the visits, is a DSM-IV symptom checklist | `dsm_criteria` is therefore written by the export, not by the EMR. D12, D14 and D15 stand. The DSM-IV checklist is one instrument for all patients and needs no split |
| Prolactin unit | The application has a column next to the value that carries the unit | It is in the extraction (`prolctn_lborresu`; the choice itself is in `rad_prolactine`), but a unit was chosen for 28% of the results only. The others carry the form's default label, so the centre and the period are used (D31) |
| MARS | Items 1 to 10 are coded 1 = no and 0 = yes | D37: the dictionary's coding is wrong for these items; the stored total is the MARS score |

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
| Suicide questions, lifetime / since the last visit | `isf01` to `isf05` are lifetime questions at the inclusion visit and questions on the time since the last visit at follow-up, with different answers to "when" | Two schemas, split by the visit label (D46). The "yes" answers of the follow-up visits of 2022 and 2023 are flagged `period_doubt` (D48) | Done: `isf_lifetime`, `isf_since_visit` |
| Comorbidities, inclusion / yearly visits | The four comorbidity sections are filled at the inclusion visit and at the yearly visits in the same columns, but a "yes" at inclusion becomes a "no" later for 40% to 74% of the patients | Two schemas per section, split by the visit label (D49); the project lead confirmed that the yearly form is about the time since the last visit (D50) | Done: `anxiety_v0`, `anxiety_fu`, `substance_v0`, `substance_fu`, `eating_disorder_v0`, `eating_disorder_fu`, `somatoform_v0`, `somatoform_fu` |
| Mood sections, DSM-IV / DSM-5 forms | The inclusion forms of the mood evaluation differ: mixed episodes and a mixed type of episode in DSM-IV only, the specifier "mixed" and three age columns in DSM-5 only. DSM-5 inclusions start in 2020 and are the rule from 2022. The follow-up form of the current episode has no mixed type in any year | Five sections split by `dsm_version` (D53) | Done: `dsm4_*` and `dsm5_*` schemas of `premier_episode`, `vie_entiere`, `annee_ecoulee`, `episode_recent`, `episode_actuel` |
| Anxiety disorders, which ones | Among the patients with an anxiety disorder at inclusion, the box "panic disorder" is ticked for about 40% until 2017, 25% from 2019 to 2023 and 13% in 2025 and 2026; "not otherwise specified" goes from about 15% to 30%. A slow change of habits: no date at which a form changed | Delivered as written | Done: `anxiety_v0` |
| ALS-54 / ALS-18 | The ALS-18 replaced the 54-item ALS; each centre changed at its own date between September 2021 and May 2022. The extraction holds the same 18 items for both forms, their four scores, and three scores of the 54-item form (`als57`, `als58`, `als60`). On ALS-18 visits `als57` holds the 18-item anxiety-depression mean instead | Two schemas, split by what only the long questionnaires of the visit have (D47) | Done: `als54`, `als18` |
| WURS-61 / WURS-25 | The WURS-25 replaced the 61-item WURS. The extraction holds the same 25 items and their sum for both forms; no WURS column tells the forms apart | Two schemas; the form is read from the ALS and the BIS of the same visit (D47, O30) | Done: `wurs61`, `wurs25` |
| AIM-40 / AIM-20 | Reduced in 2021 according to the dictionary. The extraction holds only the reduced items and their score, identical in every year; no column tells the forms apart | One schema (O23) | Done: `aim` |

### Related cases that are not two editions in one column

| Case | What the data show | Handling | State |
|---|---|---|---|
| WAIS-IV similarities | Own columns, WAIS-IV only (802 visits from 2018). It replaced vocabulary in the WAIS-IV battery | One schema | Done: `wais4_similitudes` |
| CPT-II / CPT-3 | Separate columns: `cpt2xx` on 3,152 visits until 2021, `cpt3xx` on 509 visits from 2022; only 2 visits have both. `cpt_version` is filled on every row and mislabelled | Two schemas, nothing to split; `cpt_version` ignored | Done: `cpt2`, `cpt3` |
| TMT z-scores | Same test, but the sign of five of the six z-scores flipped centre by centre between 2012 and 2014: their rank correlation with the raw time is +0.8 before and −0.85 after. Eight centres changed; about 770 of 5,863 visits use the old sign | Old values flipped, one switch date per centre found from the data (D13) | Done: `tmt` |
| TMT percentile columns | Numbers (`95`) until 2015, classes (`>10`, `>25`) from 2016. In the EMR this is a text column holding a percentile band | Times read as bands (D38); errors recomputed from the norm tables, because the stored ones follow three rules (D42, D43) | Done: `tmt` |
| CVLT standardised columns | Bands, percentiles and z-scores mixed in the same column in every year; `cvlt20z_` held "Non applicable" until 2015. In the EMR the column holds a z-score or a band depending on the patient's age group | Two variables share the column, a z-score and a band (D39); the band also takes the z-scores, turned into bands (D44) | Done: `cvlt` |
| Unit labels in biology | MCH `%` to `pg`, MCHC and prolactin labels change over the years; the form has a unit choice for ten analytes (`rad_*`), copied into the unit column for nine of them | The unit rule (D28) | Done: the seven biology schemas |
| Prolactin unit | One centre reported in mUI/L during two periods (late 2014 to 2017, mid 2021 to mid 2022) under the default label; ng/mL elsewhere | The unit is read from the centre's results of the time (D31) | Done: `bhcg_prolactine`; 174 results without a unit (O20) |
| BDHI then AQ-12 | BDHI (75 items) until 2022, AQ-12 from 2021: two instruments for aggression, own columns | Two schemas, nothing to split | Done: `bdhi`, `aq12` |
| MAThyS sub-scores | The EMR changed their formula in 2022: plain sums before, reversed items after | Recomputed from the items (D34) | Done: `mathys` |
| Questionnaires added in 2021 | ASRS, AQ-12, STOP-BANG, and the MARS question `mars11` | Own schemas; no earlier data | Done: `asrs`, `aq12`, `stop_bang`, `mars` |

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
and LTSG (retired by 2021), the legacy `_n1` second ratings (ignored, D27),
`lost_to_follow_up_*_patient` (replaced by `*_stopsuivi`), and the
family-history date columns (from 2024).

## Findings to report to whoever produces the extraction

| Finding | Evidence |
|---|---|
| Epworth: only the answers equal to 0 are exported | `ess0101` to `ess0109`: 56,135 values, all `0`. An item is 0 or empty, and the total is filled only when the eight items are 0 |
| Fagerström item 3: the answer "any other cigarette" is not exported | Empty on 2,113 visits where the five other items are filled; the stored total is missing there |
| CSM item 7: one of its five answers is never exported | Empty on 450 visits where the twelve other items are filled; the stored total is missing there |
| PSQI, minutes to fall asleep | 277 values are the minutes multiplied by 60, and 83 are a bedtime. The stored latency component and the stored total are then too high (231 totals) |
| MAThyS | The decimal point is lost in 52 item cells (55 for 5.5), and the stored total is computed from them. The sub-scores `mathys29` to `mathys33` changed formula in 2022 |
| `als57` holds two scores | The anxiety-depression score of the 54-item form on the visits of the ALS-54, the mean of five of the 18 items on the visits of the ALS-18. `als55`, `als56` and `als59` are labelled with scales of the long form but are scores of the 18 items |
| Dictionary codings that are not those of the data | STAI-YA items are 1 to 4 (dictionary: 0 to 3). PSQI items are 0 to 3 (dictionary: 1 to 4). MARS items are 1 = no (dictionary: 1 = yes). CSM items are stored as points, not as the rank of the answer. The dictionary gives no scoring key for any questionnaire |
| Damaged characters | "d?AOS" in 12 STOP-BANG results, "N?gatif" in one ASRS result |
| CVLT z-scores that cannot be right | The z-score of trials 1 to 5 is above 5 on 246 visits whose raw totals are ordinary, two thirds of them in 2009, 2013 and 2014; the z-score of semantic clustering on 100 visits, most in 2012 and 2013. The recency z-score is "Non applicable" on 835 visits of patients aged 40 to 69, and on 43 visits it is computed from an empty recency (-5.77) |
| TMT error percentiles written with three rules | For a patient with no error in part A: `>95` until 2015, `>5` to `>25` from 2016 to 2021, `<5` on 426 visits from 2022. `<5` for the best possible result looks like an error of the 2022 version |
| CVLT norms: the table and the regression disagree on a perfect recall | In the age groups read in the percentile table, 12% to 27% of the patients are at the top of the scale with a perfect recall; in the age groups given a z-score, the same result is most often one band lower and 1% to 4% reach the top |
| The EMR writes the highest percentile for the CVLT and the lowest for the TMT | When several limits of the norms fall on one raw score: 99 for a perfect CVLT recall, `>10` for a TMT with no error |
| Date of the first suicide attempt | 2011-11-11 in 1,133 cells, on visits from 2012 to 2022 |
| Suicide attempts "since the last visit" in 2022 and 2023 | 16% and 9% of the follow-up visits, against 2% to 4% in every other year; five centres of eight, from the first quarter of 2022 to the last of 2023. The number of attempts and the date of the first attempt given at inclusion are often typed again on these visits (O29) |
| `rad_tb_subst` loses the "unknown" answers | It is `rad_tb_subst_raw` written as 0 and 1; the 94 "U" answers are empty in it |
| The boxes of the anxiety disorders are not exported after a "no" | The boxes of the substances are exported as 0 after a "no"; those of the anxiety disorders are empty. They are read as 0 here (D50) |
| Dictionary, anxiety disorders | Four columns are missing: `ceoccurtrouble_panique`, `ceoccurtrouble_anxieux_affection_medicale_generale`, `ce_occurtrouble_anxieux_induit_substance` and `ceoccur_trouble_anxieux_non_specifie` (written as a section title). The label of `abudep_autre` is that of a duration; the column is a yes/no |
| Panic disorder, two detail blocks | The age at onset and the "symptoms in the past month" exist once for "with agoraphobia" and once for "without"; clinicians fill either one whatever the box ticked (44% in the other block) |
| Pack-years are typed freely | 29 values above 200 (up to 51,050), 34 cells with words or a fraction, 101 "NA"; 115 values are above three packs a day for the years smoked |
| `abudep_sedatif` mixes two codings | "Oui" / "Non" on 153 visits from 2009 to 2022, "Y" / "N" on the others; the seven other substances only have "Y" / "N" |
| Perinatal measures hold zeros | In 2009 and 2010 the form saved a 0 in the weight, the length, the head circumference and the Apgar scores when they were not known (57 visits; 10 more later) |
| Birth weights typed as a gestational age | 12 cells of `gstabrth` hold 2,000 or more; 14 hold a number of months (6 to 9) |
| The PERINATALITE sheet of the dictionary has one more column | A code list before the names, so that every other column is one place to the right of the other sheets |
| Lifetime "at least one episode" columns are written on every row | `mhoccur_edm_lt`, `mhoccur_ehman_lt`, `mhoccur_epman_lt`, `mhoccur_epmixt_lt`: "Y" where the count of the row is 1 or more, "N" on all the other rows, including the rows where the count is "Ne sais pas" or empty and the 15,594 rows of the other visits |
| Three columns are copies | `mhoccur_edm_psy_spv`, `mhoccur_epman_psy_spv`, `mhoccur_epmixt_psy_spv` hold the lifetime answers of the `_lt` columns on every row; their dictionary section is the follow-up form |
| Placeholder dates in the mood forms | 1000-01-01 in 686 dates of onset of a psychotic disorder (611 in 2025 and 2026, next to a "no"), 313 start dates of the current episode and 137 dates of the most recent episode |
| Dictionary, EVALUATION MEDICALE | `age_ehman`, `age_epman` and `rad_agethym` have no label. `mhoccur_ehman_ly` (a hypomanic episode in the past year) carries the label of the depressive episode with psychotic features. `cedecodtrouble_humeur_actuel` is listed twice |
| Dictionary, SOIN SUIVI HOSP ARRET TRAVAIL | `hooccur_hospitalisation_ly` is listed and is not in the extraction. The three follow-up columns of the sick leave (`rad_arret_travail`, `arret_travail_nb`, `arret_travail_duree`) have no label |
| Numbers of consultations and durations of sick leave are typed freely | 193 cells hold words ("2 semaines", "1 fois par mois"); one duration of sick leave is 880,410 weeks; 44 durations of sick leave in the 12 months before inclusion are above 53 weeks |
| Columbia sections | On 17 visits the method of the attempt is empty although the lethality columns are filled; the date of the most violent attempt (`isf08_qsdtc`) is in the dictionary but not in the extraction |
| CPT-3 columns that do not hold a T-score | About 37 visits hold a value outside 20 to 90 in the T-score columns, probably the raw value. The dictionary names the CPT-3 columns with a final underscore that the extraction does not have |
| CPT-II typing errors | A few T-scores and percentiles of 1,000 or more (a lost decimal point), and counts above the number of targets; 57 cells in all |
| Errands test | The percentiles are typed by hand in many spellings ("20-50", "25<50", ">=75"); 37 times are written as a duration ("5'30") |
| The age entered on the neuropsychology form | Differs by more than a year from the age computed from the dates on 199 visits |
| BIS reversed items are scored `6 − value` on a 1 to 4 scale | Stored scores recovered exactly from the items on all complete rows |
| BIS-12 answers are stored in BIS-10 columns | 1,438 visits (a few from 2018, most from 2021 on) have only twelve of the 34 item columns filled |
| On BIS-12 visits the EMR still fills the BIS-10 subscales, the BIS-10 total and `bis11` | Computed from the 4, 4, 4, 12 and 9 items that happen to exist |
| Dictionary formula of the BIS planning subscale is incomplete | The stored score also uses items 14, 18 and 31 |
| WAIS-IV digit-span summary columns are shifted against their dictionary labels | `mcodemp_w` = raw total, `mcoiemp_w` = forward span, `empdid_w` = backward span, `nbrut_w` = span difference |
| WAIS-IV vocabulary is stored in columns named for WAIS-III | `vocab*_wais3` on 2,107 WAIS-IV visits |
| The WAIS-III vocabulary raw total is 3 points too low in the extraction | The stored total equals the sum of the 33 items minus 3 on 1,207 of 1,210 rows, and is never the sum itself. The scaled score was computed from the true total and is right, so only this column is wrong |
| TMT z-scores changed sign convention between 2012 and 2014 | Rank correlation with the raw time: +0.8 until 2011, −0.85 from 2014. Eight centres changed, each at its own date; the z-score of the B−A error difference never changed |
| `dsm_criteria` is empty at inclusion for 850 of 6,476 patients | 364 of them have follow-up mood evaluations (731 visits) whose DSM version is then unknown |
| Three lifetime answers are stored in columns named for the follow-up section | `mhoccur_edm_psy_spv`, `mhoccur_epman_psy_spv` and `mhoccur_epmixt_psy_spv` are filled at inclusion only |
| `cpt_version` is filled on every row with WAIS labels | Values `wais3` / `wais4` on all 22,077 rows |
| Unit columns are filled where the result is empty | 796 to 10,809 rows per analyte |
| Current treatments are exported as Python list literals | `med_psy_*`, 18,107 rows |
| Duplicated visit records | 7 exact duplicate rows |
| `nom_centre` is empty | 100% of rows |
| `formoppos` and `social_protec` have no label and no coding in the dictionary | 613 and 4,840 patients have a value |
| The EMR writes 1000-01-01 in date fields that do not apply | Date of death: 157 patients who are not recorded as deceased. Date of the change of diagnosis: 280 patients. Date of the referral letter: 51 patients |
| The date the information was collected (`dmdtc`) is impossible for 26 patients | 24 dates before 2008, 2 with a year below 100 |
| The inclusion visit is dated before the screening visit | 26 patients |
| The referral information is recorded less and less | `adresseur` is filled for 92% of the patients included in 2008 to 2012, 85% in 2013 to 2017, 66% in 2018 to 2021 and 43% in 2022 to 2026 |
| The dictionary lists three referral variables under "Fin de suivi" | `adresseur_date`, `connaissance_centre_expert` and its free-text detail |
| A column name is cut in the extraction | `connaissance_centre_expert_preci`, for `..._preciser` in the dictionary |
| The end-of-follow-up form exists in two sets of columns | `*_patient` (784 patients) and `*_stopsuivi` (71 patients); 5 patients have both, 2 with different reasons |
| The date of birth is exported with the day set to 15 | All 6,476 patients |
| The EGF holds a band instead of a number | 149 cells such as "60-51" |
| Stored FAST domain scores do not follow their items | 442 cells in all (0.2 to 0.8% of rows per domain), while the stored total always equals the sum of the 24 items |
| The stored CGI efficacy index does not follow its two components | 79 of 9,010 rows, each off by a multiple of 4 |
| The symptom counts of the DSM-IV checklist are not always stored | Absent on 1,946 visits where the nine depressive symptoms are answered, and on 678 for the manic symptoms; different from the count on 60 and 22 rows |
| Stored Alda scores do not follow their items | Criterion A on 9 rows, B score on 11 rows |
| Legacy columns are still in the extraction | The second ratings of MADRS and YMRS (`_n1`, 23 columns, 369 and 349 visits) come from data-management experiments |
| Decimal points are lost in some heights, weights and waists | 182 heights (1650 for 165.0), 3 weights, 1 waist. Half of the heights come from one centre, from 2018 on. The stored body mass index is right on those visits, so the loss happens after the EMR computed it |
| Blood pressure is typed in cmHg in six centres | 34 to 40 values per column |
| ECG intervals are typed in milliseconds, more and more often | QT: 387 values, 274 of them since 2023, in 14 centres; RR: 106; a few in hundredths of a second |
| The EMR computes the QTc from the numbers as typed | 164 stored QTc are impossible (0.013 or 13), where QT and RR were not on the same scale |
| The RR field holds values that look like heart rates | 25 values from 30 to 300 |
| A heart rate of 0 is stored when the ECG rate was not measured | 20 values |
| The unit columns of the biology are filled with a default label | Also on the 8,000 visits that have no result. Four default labels are wrong: "mg/L" for prolactin, "µUI/L" for TSH, "%" for MCH and for MCHC |
| The form offers "mmol/L" for bilirubin | 28 results; it can only mean µmol/L |
| The unit chosen for LDL cholesterol is not exported into its unit column | 246 results chosen as g/L are labelled mmol/L in `ldl_lborresu` |
| Results typed on another scale under the default label | Haematocrit as a fraction (477) or without its decimal point (58); MCHC in g/L (550); haemoglobin in g/L (473); iron in µg/dL (about 360); total cholesterol in g/L (about 250); glucose in g/L (124); free T4 in ng/dL (99); uric acid in mg/L, mg/dL or mmol/L (about 150); phosphate in mg/L (81); creatinine in mg/L (76); calcium in mg/L (51); urea in g/L (53); alkaline phosphatase in µkat/L (37); cell counts per mm3 (about 35 visits) |
| White-cell counts typed as percentages | About 850 results, almost none labelled "%": 40 visits with the five kinds in percent, and single cells, mostly basophils (461) |
| The five kinds of white cells do not add up to the leukocytes | 222 visits, beyond 10%, once the percentages are converted |
| No unit was chosen for 72% of the prolactin results | The unit column then holds the default label "mg/L". About 320 of these results are in mUI/L, most of them from one centre during two periods; 174 cannot be given a unit |
| The stored cholesterol ratio is computed from the numbers as typed | 364 visits differ from the ratio of the harmonised values |
| Prolactin is reported in ng/mL or in mUI/L without a reliable label | About 500 results of 100 and more under the default label; one centre accounts for 69% of them |
| Clozapine levels are on three scales at least | 65 results; 31 cannot be read |
| A creatinine clearance of 0 is stored when none was computed | 246 values |

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
| `wais3_vocabulaire` | `wais3_vocab_total` on 1,212 rows, range 8 to 64; 3 `score_mismatch` once the offset of −3 is applied. With the norm table in `norms/`: the check agrees with the stored scaled score on 1,191 of 1,210 rows; 19 `derived_doubt` on the scaled score and 19 on its z-score; no `norm_missing` |
| key columns | `age` valid on 22,065 of 22,070 visits (5 have no visit date), from 17.0 to 86.0 |
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
| coverage | 426 columns covered, 36 ignored, 1,774 not assigned yet |
| `data` | 22,070 rows and 497 columns |
| `parametres_physiques` | `unit_inferred`: 182 height (180 in mm), 3 weight, 1 waist. `out_of_range`: 3 height, 17 waist. `bmi` on 16,319 visits; 34 `score_mismatch`, 1 `out_of_range` |
| `pression_arterielle` | `unit_inferred` (cmHg): 34, 40, 38 and 38 (systolic and diastolic lying, then standing). 1 `out_of_range` on the standing systolic pressure and 1 on the lying heart rate |
| `biochimie`, other analytes | `unit_inferred` / `unit_doubt`: uric acid 92 / 61, creatinine 76 / 0, urea 55 / 0, phosphate 90 / 6, iron 391 / 50, calcium 67 / 0, albumin 13 / 0. Creatinine clearance: 246 missing codes, 177 `censored_right`, 46 `out_of_range`. HbA1c: 39 `out_of_range` |
| `bilan_lipidique` | HDL: 248 `unit_converted`, 19 `unit_doubt`, 8 `unit_inferred`, 47 `out_of_range`. LDL: 270 `unit_converted`, 50 `unit_doubt`. Total cholesterol: 222 `unit_doubt`, 28 `unit_inferred`. `cholesterol_hdl_ratio` on 13,129 visits; 364 `score_mismatch` |
| `bilan_hepatique` | Bilirubin: 182 `unit_converted`, 2 `unit_unknown`, 360 `censored_left`. Alkaline phosphatase: 37 `unit_inferred` |
| `bilan_thyroidien` | Free T4: 99 `unit_inferred`, 8 `unit_converted`. Free T3: 35 `out_of_range`. TSH: 2 `out_of_range`, 11 `censored_left` |
| `nfs`, other counts | `unit_inferred`: 637 haematocrit, 600 MCHC, 37 leukocytes, 31 MCV; white cells (percentages and counts per mm3): 475 basophils, 165 monocytes, 115 lymphocytes, 94 neutrophils, 60 eosinophils. `unit_doubt`: 90 eosinophils, 25 basophils. `unit_unknown` (a percentage without leukocytes): 2 to 4 per kind. `out_of_range`: 62 platelets, 4 basophils. 222 `check_failed` on leukocytes |
| `bhcg_prolactine` | hCG: 2,088 `censored_left`, no unit flag. Prolactin: 157 `unit_converted`, 330 `unit_inferred`, 10 `unit_doubt`, 174 `unit_unknown`, 67 `out_of_range` |
| `dosage_psychotropes` | `unit_inferred`: 37 lamotrigine, 12 carbamazepine, 5 valproate, 13 clozapine. Clozapine: 34 valid of 65. Lithium: 10 `out_of_range` |
| `ecg` | `unit_inferred`: 394 QT (387 ms, 7 cs), 106 RR, 220 stored QTc. Missing codes (0): 20, 63, 27 and 27 (heart rate, QT, RR, stored QTc). `out_of_range`: 10 heart rate, 23 QT, 75 RR, 164 stored QTc. `qtc_bazett` on 7,792 visits; 46 `score_mismatch`, 5 `out_of_range` |
| `cgi_egf` | Missing codes (0): 246 severity, 1,427 improvement, 1,615 therapeutic effect, 1,621 efficacy index. 79 `check_failed` on the efficacy index. `gaf`: 14,650 valid; 149 `band_middle`, one of which gives a value outside 1 to 100 and is `out_of_range`; 2 missing codes; none unparsed |
| `fast` | `fast_total` on 16,507 rows, no mismatch. `score_mismatch` on the domain scores: 49, 122, 68, 25, 89 and 89 (autonomy, occupational, cognitive, financial, interpersonal, leisure) |
| `ymrs` | `ymrs_total` on 17,154 rows, no mismatch |
| `etat_depressif` | `etatd_total` on 15,332 rows; 60 `score_mismatch`. Items hold 0 and 1 only |
| `etat_maniaque` | `etatm_total` on 15,207 rows; 22 `score_mismatch` |
| `alda` | `alda_total` on 1,638 rows; `score_mismatch`: 14 on the total, 11 on the B score, 9 on the criterion A check |
| `tmt` checks | 6 `score_mismatch` on `tmt_ba_time_check`, none on `tmt_ba_errors_check` |
| items of this tab | No `unparsed`, `unknown_code` or `out_of_range` on any of the 53 items |
| `patients` | 6,476 rows and 24 columns |
| `identite` | `sex`: 4,097 female, 2,377 male, 2 missing. `diagnosis`: 3,095 `bp2`, 2,714 `bp1`, 667 `bp_nos`. `age_at_inclusion` from 17 to 86. `birth_date` valid for every patient |
| `provenance` | `referred_by` valid for 4,639 patients. `information_date`: 24 `out_of_range`, 2 `unparsed`. `referral_letter_date`: 51 `date_placeholder` |
| `fin_de_suivi` | `followup_end_reason` filled for 850 patients: 791 valid, 59 missing codes, 2 `column_conflict`. `death_date`: 17 valid (1 `date_partial`), 157 `date_placeholder`. `diagnosis_change_date`: 55 valid, 280 `date_placeholder` |
| `visit_record` | `entry_date` valid on all 22,070 visits |
| patient-level flags | At most one line per patient, variable and flag |
| AUTO-QUESTIONNAIRES, scores | No `score_mismatch` on `prisem_total` (16,051 rows), `staya_total` (16,578), `mars_total` (15,987), `altman_total` (19,457), `qids_total` (19,235), `fagerstrom_total` (5,755), the six CTQ scores (`ctq_total` on 6,165), the four ALS scores of each form (`als54_total18` on 4,656, `als18_total` on 1,429), `aim_score` (6,063), `wurs61_sum25` (4,585), `wurs25_total` (1,426), `csm_total` (5,605). One to three mismatches on AQ-12 (2 in all), `bdhi_motor` (1), the two circadian scores (3 each) and `mdq_total` (3) |
| `mathys` | 52 `unit_inferred` on the items; 49 `score_mismatch` on `mathys_total` (15,587 rows) |
| `psqi` | `psqi_latency`: 277 `unit_inferred`, 83 `out_of_range`. 232 `score_mismatch` on `psqi_latency_component`, 231 on `psqi_total` (16,279 rows) |
| `als54`, `als18`, `wurs61`, `wurs25` | `als_form`: 4,695 `als54`, 1,442 `als18`, 3 `version_unknown` (a stored score and no answer). `wurs_form`: 4,639 `wurs61`, 1,435 `wurs25`, 49 `version_unknown`. `als54_anxiety` on 4,641 rows. No visit is in the columns of both forms; on the visits that have both, `als_form` and `bis_form` agree but for one |
| `bdhi`, `aq12`, `asrs` | `bdhi_total` on 4,472 rows, `aq12_total` on 1,367, `asrs_total` on 1,258 |
| items of this tab | No `unparsed`, `unknown_code` or `out_of_range` on any item of the 21 schemas |
| `tmt`, bands | `tmt_a_time_band` valid on 5,865 visits and `tmt_ba_time_band` on 5,869 (72 `censored_left`), none unparsed. Recomputed error bands: `tmt_a_errors_band` on 5,836 visits (5,290 `censored_right`, 8 `norm_missing`), `tmt_b_errors_band` on 5,792 (4,703), `tmt_b_perseverative_band` on 4,611 (4,464), `tmt_ba_errors_band` on 4,979 (3,596) |
| `cvlt` | One band per measure: `cvlt_trial5_band` on 5,817 visits (68 `band_from_z`, 1,602 `censored_right`, 3 `norm_missing`), `cvlt_short_free_band` on 5,801 (2,926 from z-scores, 526 `censored_right`), `cvlt_trial1_band` on 5,807 (all from z-scores), `cvlt_total_1_5_band` on 5,556 (246 `out_of_range`), `cvlt_hits_band` on 5,750 (3,945 `censored_right`), `cvlt_serial_band` on 4,951 as the EMR wrote it. No band of trial 5 is 99 any more. z-scores still delivered: `cvlt_trial5_z` on 69 cells, `cvlt_short_free_z` on 2,930. `cvlt_recency_z`: 995 missing codes, 43 `check_failed` (also on `cvlt_recency_band`). `cvlt_total_1_5` on 5,816 visits, 54 `score_mismatch` |
| `stroop`, `spatial_span`, `cobra`, `errands_test` | `stroop_interference` on 5,767 visits, 29 `score_mismatch`; `spatial_total` on 5,210, 41; `cobra_total` on 582, none; `errands_errors` on 789, 9 |
| `cpt2`, `cpt3` | `cpt3_omissions_t` valid on 471 visits, 37 `out_of_range`. CPT-II: 57 `out_of_range`, 23 `unparsed` |
| `neuropsy_conditions` | `handedness`: 5,440 right, 568 left, 121 both |
| SUICIDE | `visit_form`: 6,476 inclusion and 11,621 follow-up visits. `isf05_lifetime` on 5,897 visits (38% yes), `isf05_since_visit` on 9,181 (3% yes). 2,688 `period_doubt` on the follow-up answers of 2022 and 2023: 1,445 "yes" (114 on `isf05_since_visit`) and 1,243 "when"; none on `isf_lifetime`. `first_attempt_date`: 2,147 valid, 1,133 missing codes, 148 placeholders. `violent_method` on 336 visits, `serious_method` on 456. `css0101` on 3,543 visits, `cssrs_intensity` on 1,000. No `unknown_code` on any category of the tab |
| SUBSTANCES ET COMORBIDITE | `visit_form`: 6,476 inclusion and 11,621 follow-up visits. `anxiety_disorder_v0` on 5,151 visits (48% yes), `anxiety_disorder_fu` on 4,531 (35%); `substance_disorder_v0` on 5,232 (37%), `substance_disorder_fu` on 4,561 (23%); `eating_disorder_v0` on 5,201 (20%), `_fu` on 4,515 (14%); `somatoform_disorder_v0` on 5,167 (3.6%), `_fu` on 4,526 (1.7%). No visit is in both sets of columns. `panic_disorder_v0` on 5,126 visits (2,650 read as 0 after a "no"; 16% yes), `alcohol_disorder_v0` on 5,218 (26% yes). `panic_onset_age_v0` on 413; 5 `column_conflict` on the panic details. `tobacco_status` on 16,270 visits (83 missing codes). `pack_years`: 6,305 valid, 101 missing codes, 34 `unparsed`, 29 `out_of_range`. Durations: 26 `unparsed`, 2 `out_of_range`. No `unknown_code` on the tab |
| PERINATALITE | Patient level: `birth_term` for 4,743 patients (4,107 at term, 475 premature, 161 post-term), `birth_type` for 4,530 (444 caesarean), `mother_age_at_birth` for 4,539 (56 `patient_value_varies`), `birth_weight` for 2,429 (34 missing codes, 17 `out_of_range`, not winsorised), `gestational_age` for 1,193 (14 `unit_inferred`, 22 `out_of_range`), `apgar_1min` for 907 (53 missing codes, 2 `out_of_range`). No `unknown_code`, no `unparsed` |
| EVALUATION MEDICALE | 15 instruments. `dsm4_lt_n_mde` on 3,746 visits (236 `censored_right`), `dsm5_lt_n_mde` on 903 (55). `dsm4_ly_n_mde` on 4,034 (1,386 zeros; 1 visit keeps a count typed after a "no"), `dsm4_fu_n_mde` on 6,864 (4,603 zeros). `dsm4_current_episode` on 11,694 visits, `dsm5_current_episode` on 3,433. `psychotic_disorder_v0` on 5,370 (1.3% yes), `psychotic_disorder_fu` on 9,336 (0.4%); 686 `date_placeholder` on the date of onset. `dsm5_first_hypomania_age` 520, `dsm5_first_mania_age` 280, `dsm5_agethym` 915. DIVA totals on 41 to 45 visits, 7 `score_mismatch`. No visit in the columns of both DSM versions. 2 `unknown_code` (`dsm4_current_specifier`), 11 `unparsed`. `dsm_version`: 369 `version_inferred`, 38 `version_unknown` |
| SOIN SUIVI HOSP ARRET TRAVAIL | 6 instruments. `n_hospitalisations_v0` on 5,043 visits (mean 2.5; 25 `censored_right`), `n_hospitalisations_fu` on 8,374 (mean 0.17). `first_hospitalisation_age` on 3,889 (21 `censored_left`). `sick_leave_12m` on 4,042 (60% yes; 1,198 missing codes), `sick_leave_fu` on 6,287 (30%; 3,074). `sick_leave_weeks_12m`: 3,646 valid, 91 `unparsed`, 44 `out_of_range`. `care_usual` on 9,457 visits (91% yes), `care_urgent` on 9,295 (13%). `n_urgent_psychologist`: 37 values above 0, up to 24. `drug_advice_followed` on 9,443 visits (62% fully). No `unknown_code`, no `winsorised`. `visit_form`: 6,476 inclusion and 11,621 follow-up visits |

## Checklist

State: ☐ not started · ◐ schema written (draft) · ☑ reviewed · – ignored.
Numbers are variables in the dictionary section, item ranges expanded.

### 1. PATIENT (`patient/`)

| State | Section | Variables |
|---|---|---|
| ◐ | IDENTIFICATION PATIENT: `identite` (sex, diagnosis, date of birth, age at inclusion). `subjid` and `nom_centre` ignored | 10 |
| ◐ | Inclusion: `inclusion`. Codes not documented (O16) | 2 |
| ◐ | Provenance: `provenance`, with the three referral variables that the dictionary lists under Fin de suivi | 6 |
| ◐ | Fin de suivi and patient: `fin_de_suivi`, one schema for the two generations of columns (D17) | 12 + 8 |
| ◐ | visit: `visit_record` (the entry date). The other columns are keys; `id_fiche_clinique` ignored | 7 |

All 40 columns of the tab are covered (37) or ignored (3). The five schemas
meet the definition of done except for the review, so they stay `draft`.

### 2. HETERO-QUESTIONNAIRES (`hetero_questionnaires/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Questionnaire CGI-EGF: `cgi_egf` | 6 |
| ◐ | Questionnaire FAST: `fast` | 31 |
| ◐ | Questionnaire MADRS: `madrs` | 11 |
| – | Questionnaire MADRS_n1: legacy, ignored (D27) | 11 |
| ◐ | Questionnaire YMRS: `ymrs` | 12 |
| – | Questionnaire YMRS_n1: legacy, ignored (D27) | 12 |
| ◐ | Episode depressif majeur actuel: `etat_depressif` (DSM-IV checklist) | 15 |
| ◐ | Episode maniaque actuel: `etat_maniaque` (DSM-IV checklist) | 10 |
| ◐ | Questionnaire ALDA: `alda` | 10 |

All 118 columns of the tab are covered (95) or ignored (23). The seven
schemas meet the definition of done except for the review, so they stay
`draft`.

### 3. CONSTANTES et ECG (`constantes_et_ecg/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Paramètres physiques: `parametres_physiques` | 4 |
| ◐ | Pression artérielle / fréquence cardiaque: `pression_arterielle` | 6 |
| ◐ | ECG: `ecg` | 5 |

All 15 columns of the tab are covered. The three schemas meet the definition
of done except for the review, so they stay `draft`.

### 4. BILAN BIOLOGIQUE (`bilan_biologique/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Biochimie: `biochimie` (16 analytes) | 32 |
| ◐ | Bilan lipidique: `bilan_lipidique` | 9 |
| ◐ | Bilan hépatique: `bilan_hepatique` | 10 |
| ◐ | Bilan thyroidien: `bilan_thyroidien` | 6 |
| ◐ | NFS: `nfs` (13 counts and indices) | 26 |
| ◐ | bHCG and prolactin: `bhcg_prolactine`. 174 prolactin results without a unit (O20) | 4 |
| ◐ | Dosage des psychotropes: `dosage_psychotropes` | 8 |
| – | tests speciaux: nine unit choices ignored (already in the unit columns); `rad_chol_hll` is read by `ldl` | 10 |

All 105 columns of the tab are covered (96) or ignored (9). The seven schemas
meet the definition of done except for the review, so they stay `draft`.

### 5. AUTO-QUESTIONNAIRES (`auto_questionnaires/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Questionnaire PRISEM: `prisem` | 33 |
| ◐ | Questionnaire STAI Y_A: `stai_ya` | 21 |
| ◐ | Questionnaire MARS: `mars` | 12 |
| ◐ | Questionnaire MATHYS: `mathys` (20 scales) and `mathys_emotions` (7 items); five stored sub-scores ignored | 33 |
| ◐ | Questionnaire ALTMAN: `altman` | 6 |
| ◐ | Questionnaire QIDS-SR16: `qids_sr16` | 17 |
| ◐ | Questionnaire PSQI: `psqi`; two copies of items ignored | 27 |
| – | Questionnaire EPWORTH: ignored, only the zeros are exported (D33, O24) | 10 |
| ◐ | Questionnaire EQ5D: `eq5d` | 7 |
| ◐ | FAGERSTROM: `fagerstrom` | 7 |
| ◐ | APNEES DU SOMMEIL: `stop_bang`; one column ignored | 9 |
| ◐ | Questionnaire ASRS: `asrs` | 19 |
| ◐ | Questionnaire AQ12: `aq12` | 16 |
| ◐ | Questionnaire CTQ: `ctq`; one column ignored | 41 |
| ◐ | Questionnaire BIS10, split into `bis10` (34 items) and `bis12` (12 items) | 43 |
| ◐ | Questionnaire ALS: `als54` and `als18`, split by form (D47) | 25 |
| ◐ | Questionnaire AIM: `aim` (O23) | 21 |
| ◐ | Questionnaire WURS: `wurs61` and `wurs25`, split by form (D47, O30) | 26 |
| ◐ | Questionnaire BDHI: `bdhi` | 85 |
| ◐ | Questionnaire CSM: `csm` | 14 |
| ◐ | Inventaire du rythme circadien: `circadian` | 13 |
| ◐ | MDQ: `mdq` | 17 |

All 502 columns of the tab are covered (483) or ignored (19). The 23 schemas
meet the definition of done except for the review, so they stay `draft`.

### 6. NEUROPSYCHOLOGIE (`neuropsychologie/`)

| State | Section | Variables |
|---|---|---|
| ◐ | Clinical criteria (no header): `neuropsy_conditions`, with the hour of the testing | 12 |
| ◐ | Troubles des acquisitions et des apprentissages: `learning_disorders` | 10 |
| ◐ | CVLT: `cvlt` (raw scores, z-scores and percentile bands) | 40 |
| ◐ | TMT: `tmt` (times, errors, z-scores, percentile bands); the four stored error percentiles are ignored and recomputed | 22 |
| ◐ | Stroop (planches A, B, C, interférence): `stroop` | 21 |
| ◐ | Fluences verbales: `verbal_fluency` | 22 |
| ◐ | CPT II: `cpt2`; `cpt_version` ignored | 55 |
| ◐ | CPT III: `cpt3` | 18 |
| ◐ | Mémoire spatiale: `spatial_span` | 57 |
| ◐ | COBRA: `cobra` | 17 |
| ◐ | SCIP: `scip` | 12 |
| ◐ | Test des commissions: `errands_test` | 18 |
| ◐ | Similitudes: `wais4_similitudes` | 22 |
| ◐ | Vocabulaire, split into `wais3_vocabulaire` and `wais4_vocabulaire` | 37 |
| ◐ | Matrices, split into `wais3_matrices` and `wais4_matrices`; `wais` ignored | 30 |
| ◐ | Code, Symboles & IVT, split into `wais3_code_symboles_ivt` and `wais4_code_symboles_ivt` | 14 |
| ◐ | Mémoire des chiffres, split into `wais3_memoire_chiffres` and `wais4_memoire_chiffres` (scores, trials and item scores) | 85 |

All 489 columns of the tab are covered (483) or ignored (6). The 21 schemas
meet the definition of done except for the review, so they stay `draft`.
The norm tables that would let the pipeline recompute the standard scores
(O12) are still expected, apart from the WAIS-III vocabulary.

### 7. Mostly categorical tabs

| State | Tab (`folder/`) | Section | Variables |
|---|---|---|---|
| ◐ | SUICIDE (`suicide/`) | Intentionnalité suicidaire actuelle, split into `isf_lifetime` (inclusion) and `isf_since_visit` (follow-up); the "yes" answers of 2022 and 2023 at follow-up are flagged (D48) | 10 |
| ◐ | | Histoire des conduites suicidaires: `suicide_attempts` | 7 |
| ◐ | | Columbia TS la plus violente: `most_violent_attempt` | 10 |
| ◐ | | Columbia TS la plus grave: `most_serious_attempt` | 8 |
| ◐ | | C-SSRS Idéation suicidaire: `cssrs` | 11 |
| ◐ | SUBSTANCES ET COMORBIDITE (`substances_et_comorbidite/`) | Tabac: `tobacco` | 4 |
| ◐ | | Troubles anxieux, split into `anxiety_v0` (inclusion) and `anxiety_fu` (yearly visits, since the last visit); boxes read as 0 after a "no" (D49, D50) | 37 |
| ◐ | | Troubles liés à une substance au cours de la vie, split into `substance_v0` and `substance_fu`; `rad_tb_subst_raw` read, `rad_tb_subst` ignored | 43 |
| ◐ | | Trouble du comportement alimentaire, split into `eating_disorder_v0` and `eating_disorder_fu` | 4 |
| ◐ | | Trouble somatoforme, split into `somatoform_v0` and `somatoform_fu` | 4 |
| ◐ | PERINATALITE (`perinatalite/`) | (no header): `perinatal`, one value per patient, birth measures not winsorised (D51, D52) | 11 |
| ◐ | EVALUATION MEDICALE (`evaluation_medicale/`) | Premier épisode, split into `dsm4_premier_episode` and `dsm5_premier_episode` (D53) | 5 |
| ◐ | | Trouble vie entière, split into `dsm4_vie_entiere` and `dsm5_vie_entiere`; four export-written columns ignored | 20 |
| ◐ | | Depuis la dernière visite, split into `dsm4_depuis_derniere_visite` and `dsm5_depuis_derniere_visite`; yes/no as 1 and 0, counts 0 after a "no" (D53); three columns are copies of lifetime ones and are ignored | 15 |
| ◐ | | Année écoulée, split into `dsm4_annee_ecoulee` and `dsm5_annee_ecoulee` | 15 |
| ◐ | | Trouble psychotique, split into `trouble_psychotique_v0` and `trouble_psychotique_fu` | 4 |
| ◐ | | Episode le plus récent, split into `dsm4_episode_recent` and `dsm5_episode_recent`; the follow-up column is in the follow-up schemas | 8 |
| ◐ | | Trouble de l'humeur actuel, split into `dsm4_episode_actuel` and `dsm5_episode_actuel` (inclusion and follow-up visits) | 9 |
| ◐ | | DIVA (critères DSM-IV TR): `diva` | 40 |
| ◐ | | New Columns: in `dsm5_premier_episode` (O34) | 3 |
| ◐ | SOIN SUIVI HOSP ARRET TRAVAIL (`soin_suivi_hosp_arret_travail/`) | Hospitalisation, split into `hospitalisations_v0` and `hospitalisations_fu` (D54); one dictionary column is not in the extraction | 6 |
| ◐ | | Arrêt de travail: `sick_leave_v0` (inclusion) and `sick_leave_fu` (follow-up) | 8 |
| ◐ | | Recours aux soins: `care_use` | 24 |
| ◐ | | Suivi des recommandations: `recommendations` | 4 |
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
