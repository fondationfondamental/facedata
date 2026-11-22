# Hand-off of export requests, batches 2 to 8

This file hands over the requests of batches 2 to 8 of `EXPORT_REQUESTS.md`. We wrote them on 19 and 20 November 2026 and have not sent them yet. Batch 1 (2026-11-18) was handed over before and is not repeated here. This file is an index: each row has a short title and a link to the full text in `EXPORT_REQUESTS.md`. Please read the full text before you act on an item.

## Extractions and source versions

Counts are measured on BPALL_20261113_2.tsv (BPALL below), SZALL_20261117.tsv, DRALL_20261030.tsv and ASPALL_20261030.tsv (SZALL, DRALL, ASPALL). Earlier BP files are BPALL_20261030 and BPALL_20261113 (first run of 13 November). We read dataflow at commit a0e8a09e (2026-11-17) and the application source at commit 680ecad (2026-11-05): eBipolar, eSchizo, eCEDR and eAsperger are in that one repository. Line numbers refer to these commits.

## Words used

- Cohorts: BP (bipolar, application eBipolar), SZ (schizophrenia, eSchizo), DR (depression, eCEDR), ASP (autism spectrum disorders, children and adults, eAsperger).
- Centres are named by letters. The letters are per cohort: the same letter names different centres in BP, SZ, DR and ASP. The key of the letters is sent separately, one list per cohort.
- R items are requests to the dataflow export pipeline. A items are defects for the application developers. M items are questions for the data managers.
- Priority (high, medium, low) is the one the source gives. The source gives a priority for R items only.

## How to answer

Answer with one line per item, in the empty block at the end of your part:

- `R<n>: done (commit)`, `R<n>: not done (reason)` or `R<n>: question`;
- the same format for A items: `A<n>: done (commit)`, `not done (reason)` or `question`;
- the same format for M items: `M<n>: done (your answer, or where it is)`, `not done (reason)` or `question`.

## Counts

171 new items: 70 R, 55 A and 46 M. Each number appears once in this file. The numbers run without a gap: R102 to R171, A45 to A99, M50 to M95.

| Batch | Date | Tabs reviewed | R | A | M | Total |
|---|---|---|---|---|---|---|
| 2 | 2026-11-19 | Biology | 5 | 0 | 3 | 8 |
| 3 | 2026-11-19 | Antecedents | 6 | 12 | 8 | 26 |
| 4 | 2026-11-19 | Substances and comorbidities | 9 | 1 | 3 | 13 |
| 5 | 2026-11-19 | Suicide, care use, treatments | 13 | 4 | 4 | 21 |
| 6 | 2026-11-19 | Medical evaluation, hetero-questionnaires | 11 | 10 | 5 | 26 |
| 7 | 2026-11-20 | Self-questionnaires | 12 | 12 | 7 | 31 |
| 8 | 2026-11-20 | Patient, vital signs and ECG, perinatal, social, DR MINI, ASP socio-demographic and clinical | 14 | 16 | 16 | 46 |
| **Total** | | | **70** | **55** | **46** | **171** |

Batches 3, 5 and 8 also add new evidence to 13 items of batch 1 (10 R, 2 A, 1 M; batch 3: 1, batch 5: 3, batch 8: 9). They keep their batch 1 number. They are listed once, in the new-evidence table of part 1.

The source does not say in which batch each A item was written, except A84 to A99 (batch 8). For A45 to A83, the batch is that of the commit that added the item to `EXPORT_REQUESTS.md`.

---

## Part 1. Export pipeline (R items)

70 requests. The full text of each is its row in the table of its batch section.

| # | Batch | Cohorts | Title | Priority | Full text |
|---|---|---|---|---|---|
| R102 | 2 | BP, SZ | Export the sampling date and place, ferritin and corrected calcium of the biology form | medium | [batch 2][b2] |
| R103 | 2 | BP, DR | Check the column order of the biology tables at one BP centre and one DR centre: values sit in the wrong fields | medium | [batch 2][b2] |
| R104 | 2 | DR | Export the unit choices of the DR drug levels | low | [batch 2][b2] |
| R105 | 2 | DR | DR prolactin: export the unit only when it was chosen, or mark the back-filled unit | medium | [batch 2][b2] |
| R106 | 2 | SZ | SZ vitamin D: give the unit by centre | low | [batch 2][b2] |
| R107 | 3 | SZ | Swap back the two SZ migraine columns (disease and treated) | high | [batch 3][b3] |
| R108 | 3 | ASP | ASP: read five history fields from the table the forms write (aut_atcdlt) | medium | [batch 3][b3] |
| R109 | 3 | ASP | ASP: read the year and length of a hospitalisation from the fields the forms fill | medium | [batch 3][b3] |
| R110 | 3 | DR | DR children and siblings: export every row, with sex and row gate, in a fixed order | medium | [batch 3][b3] |
| R111 | 3 | DR | DR: export the onset date of another cardiovascular disease (follow-up form) | low | [batch 3][b3] |
| R112 | 3 | BP | Correct the BP dictionary, antecedents sheet | low | [batch 3][b3] |
| R113 | 4 | BP | BP panic columns: build them from the form's type list, matching list elements, not substrings | high | [batch 4][b4] |
| R114 | 4 | SZ | SZ anxiety columns that hold another form field: fix them; export the panic type list | high | [batch 4][b4] |
| R115 | 4 | SZ | Export the anxiety and eating questions of the yearly SZ comorbidity form | medium | [batch 4][b4] |
| R116 | 4 | SZ | SZ substances at inclusion: read 'no' to the drug question as N; export the raw gate and the yearly details | medium | [batch 4][b4] |
| R117 | 4 | BP | BP comorbidities: keep non-numeric onset ages as tokens; export the substance-induced disorder block | medium | [batch 4][b4] |
| R118 | 4 | SZ | SZ tea and coffee: export the 12-month frequency category | low | [batch 4][b4] |
| R119 | 4 | BP | Correct the substance rows of the BP dictionary | low | [batch 4][b4] |
| R120 | 4 | BP, SZ | Export the SZ substance treatment and withdrawal fields and the BP nicotine substitution | low | [batch 4][b4] |
| R121 | 4 | DR | Correct the DR dictionary rows of the substances sheet | low | [batch 4][b4] |
| R122 | 5 | DR | DR medication lists: stop crossing rows between lists and visits; same fix for the care-use tables; export stop reasons | high | [batch 5][b5] |
| R123 | 5 | BP, SZ | Export the injectable dose and the entry date (the date only after A39 is fixed) | low | [batch 5][b5] |
| R124 | 5 | SZ | Export the SZ care-use block | medium | [batch 5][b5] |
| R125 | 5 | BP, SZ | Export the non-drug follow-up columns (sessions, dates) that the clean models already read | medium | [batch 5][b5] |
| R126 | 5 | BP | Export the BP C-SSRS behaviour block and the SIS; first say whether they hold data | medium | [batch 5][b5] |
| R127 | 5 | DR | Export the DR simplified-visit flag | medium | [batch 5][b5] |
| R128 | 5 | BP, SZ | Keep the follow-up sick-leave weeks as typed | low | [batch 5][b5] |
| R129 | 5 | DR | DR numbers written '00': read them as zero (extends R73 to DR) | low | [batch 5][b5] |
| R130 | 5 | BP, SZ, DR | Correct the dictionary rows of the suicide, care-use and treatment tabs | low | [batch 5][b5] |
| R131 | 5 | SZ | Export the SZ count of suicide attempts in the last 12 months | low | [batch 5][b5] |
| R132 | 5 | SZ | Export the parent gates of the SZ care changes | low | [batch 5][b5] |
| R133 | 5 | DR | Export the DR psychotherapy kinds and the reasons for ending them | low | [batch 5][b5] |
| R134 | 5 | SZ | SZ 'ever hospitalised': 'Ne sais pas' must not become Y (extends R73) | medium | [batch 5][b5] |
| R135 | 6 | SZ | SZ YMRS: score items 5, 8 and 9 on 0 to 8 | high | [batch 6][b6] |
| R136 | 6 | SZ | SZ Calgary: read items 8 and 9 from the right form fields | high | [batch 6][b6] |
| R137 | 6 | SZ, BP, DR | Score definitions: fix the item lists of three PANSS factors and the MADRS maximum | medium | [batch 6][b6] |
| R138 | 6 | SZ | SZ EGF: keep the band answers as typed | medium | [batch 6][b6] |
| R139 | 6 | DR | DR: export which forms each visit offered | medium | [batch 6][b6] |
| R140 | 6 | BP | Export the BP diagnosis columns the clean models hold and the export drops (extends R68) | medium | [batch 6][b6] |
| R141 | 6 | SZ | Export the SZ follow-up diagnostic form and two done / not-done flags | medium | [batch 6][b6] |
| R142 | 6 | DR | DR mood history: export every episode row, the first-episode type and the follow-up form fields | medium | [batch 6][b6] |
| R143 | 6 | ASP | ASP disorders: export the ADHD sub-type, anorexia remission, shortcut flags, DSM-IV criteria; explain four empty columns | medium | [batch 6][b6] |
| R144 | 6 | BP, SZ, DR, ASP | Correct the dictionary rows of the evaluation and hetero-questionnaire tabs | low | [batch 6][b6] |
| R145 | 6 | DR | Export the DR CGI-I | low | [batch 6][b6] |
| R146 | 7 | DR, ASP | CTQ, BIS-10 and MARS score definitions: give DR and ASP their own entries, without the BP reversals | high | [batch 7][b7] |
| R147 | 7 | DR | Fix the DR QIDS, SHAPS and Fagerstrom score definitions | high | [batch 7][b7] |
| R148 | 7 | ASP | Score the SRS of a relative as the application does | high | [batch 7][b7] |
| R149 | 7 | ASP | Fix the ADOS and ADI-R score definitions | high | [batch 7][b7] |
| R150 | 7 | SZ | SZ S-QoL items 17 and 18: read them with the form's labels; export the 'not concerned' boxes | high | [batch 7][b7] |
| R151 | 7 | SZ | SZ SOGS item 6 and Birchwood: map the missed answers | medium | [batch 7][b7] |
| R152 | 7 | SZ | Export the SZ questionnaire done / not-done flags, the food form and the EPHP flags | medium | [batch 7][b7] |
| R153 | 7 | ASP | ASP: keep negative CCC-2 values; export the RBS-R factors and HAM-D items 18a to 21 | medium | [batch 7][b7] |
| R154 | 7 | ASP | ASP: export the respondent (form id) and the automatic / manual score flag | medium | [batch 7][b7] |
| R155 | 7 | DR | DR simplified visit: complete the list of forms not offered; export the QIDS selectors (extends R127, R139) | medium | [batch 7][b7] |
| R156 | 7 | ASP | Correct the dictionary rows of the ASP questionnaires sheet | low | [batch 7][b7] |
| R157 | 7 | SZ, DR | Correct the dictionary rows of the SZ and DR self-questionnaire sheets | low | [batch 7][b7] |
| R158 | 8 | BP, DR, ASP | Export the 'ECG done' answer and the cardiologist boxes | medium | [batch 8][b8] |
| R159 | 8 | SZ | SZ: export the QT and RR of the nurse form | medium | [batch 8][b8] |
| R160 | 8 | DR | DR work durations: keep the decimals | low | [batch 8][b8] |
| R161 | 8 | DR | DR referrer codes 2 and 3 are written the wrong way round | medium | [batch 8][b8] |
| R162 | 8 | DR | DR: write day 15 in the birth date, as the other cohorts do | low | [batch 8][b8] |
| R163 | 8 | SZ | SZ end of follow-up: the date of death is written as the cause; export cause, date and the other fields | medium | [batch 8][b8] |
| R164 | 8 | ASP | ASP: export the referral and end-of-follow-up fields | medium | [batch 8][b8] |
| R165 | 8 | ASP | ASP other diagnosis before the referral: export the 18 boxes | low | [batch 8][b8] |
| R166 | 8 | DR | DR: export how the patient heard of the expert centre | low | [batch 8][b8] |
| R167 | 8 | ASP | ASP: export ULIS, the follow-up schooling fields and one parents' field | low | [batch 8][b8] |
| R168 | 8 | SZ | SZ neuropsychology: export the age and years of education of each form in their own columns | low | [batch 8][b8] |
| R169 | 8 | DR | DR MINI: keep the decimals of height and weight; leave the boxes of an unanswered module empty | low | [batch 8][b8] |
| R170 | 8 | BP, SZ | Blood pressure typed 'a/b': split it into systolic and diastolic; BP heart rate: keep the decimal point | low | [batch 8][b8] |
| R171 | 8 | SZ, DR, ASP | Correct the dictionary rows of the small tabs | low | [batch 8][b8] |

### New evidence for batch 1 items

These items were handed over in batch 1. Batches 3, 5 and 8 add evidence; the request or question itself is unchanged. No new answer is needed unless the evidence changes your batch 1 answer. Two A items and one M item are listed here too, so that each number appears once in this file; they are for the developers and the data managers.

| # | Batch of the new evidence | For | What is new | Full text |
|---|---|---|---|---|
| R10 | 8 | export pipeline | The DR age join has no V0 filter; the stored age is the age at V0 for only part of the patients | [R10][r10], [batch 8][b8] |
| R23 | 8 | export pipeline | Heights: unchanged in the new review | [R23][r23], [batch 8][b8] |
| R24 | 8 | export pipeline | ECG zeros: unchanged in the new review | [R24][r24], [batch 8][b8] |
| R33 | 8 | export pipeline | BP Apgar answers 'a/b' are averaged; the gestational age keeps only the first integer | [R33][r33], [batch 8][b8] |
| R34 | 3 | export pipeline | SZ counts corrected; neither cohort holds a '>5' token, so these counts are lost | [R34][r34] |
| R41 | 8 | export pipeline | Line given; excess of answers at age 15 against 16 | [R41][r41], [batch 8][b8] |
| R42 | 8 | export pipeline | Line given; household sizes above 20 | [R42][r42], [batch 8][b8] |
| R46 | 8 | export pipeline | The SZ income CASE keeps the first match and misses two labels, so two codes are never written | [R46][r46], [batch 8][b8] |
| R47 | 8 | export pipeline | The SZ marital-status pattern never matches the SZ label | [R47][r47], [batch 8][b8] |
| R48 | 8 | export pipeline | Date the work status moved to the socio_demog form; other fields the form holds | [R48][r48], [batch 8][b8] |
| A30 | 5 | application developers | Count updated, with counts by year; the script also overwrites a typed 0 and joins by patient, not by visit | [A30][adef] |
| A38 | 5 | application developers | Text corrected: the empty strength id is stored as 0; the strength text field is varchar(255) | [A38][adef] |
| M14 | 5 | data managers | Count updated; the data date the last run of the script; the per-database count is still needed | [M14][mdm] |

### Answers of the export pipeline

```text
R102: 
R103: 
R104: 
R105: 
R106: 
R107: 
R108: 
R109: 
R110: 
R111: 
R112: 
R113: 
R114: 
R115: 
R116: 
R117: 
R118: 
R119: 
R120: 
R121: 
R122: 
R123: 
R124: 
R125: 
R126: 
R127: 
R128: 
R129: 
R130: 
R131: 
R132: 
R133: 
R134: 
R135: 
R136: 
R137: 
R138: 
R139: 
R140: 
R141: 
R142: 
R143: 
R144: 
R145: 
R146: 
R147: 
R148: 
R149: 
R150: done (dataflow fcbdfb31; extraction SZALL_20261121, SZ D104)
R151: 
R152: 
R153: 
R154: 
R155: 
R156: 
R157: 
R158: 
R159: 
R160: 
R161: 
R162: 
R163: 
R164: 
R165: 
R166: 
R167: 
R168: 
R169: 
R170: 
R171: 
```

---

## Part 2. Application developers (A items)

55 defects of eBipolar (BP), eSchizo (SZ), eCEDR (DR) and eAsperger (ASP). The full text of each is its bullet in the list of application defects. Each bullet gives where the defect is and how many records it touches.

| # | Batch | Cohorts | Title | Full text |
|---|---|---|---|---|
| A45 | 3 | DR, ASP | History forms hide a gate's children one level only: a grandchild stays filled when its grandparent is cleared | [A45][adef] |
| A46 | 3 | DR | eCEDR evaluates the lithium, valproate and allergy sub-gates before their gate when the form loads | [A46][adef] |
| A47 | 3 | DR | eCEDR: a double click unticks a radio without a change event, so children stay filled under an empty gate | [A47][adef] |
| A48 | 3 | DR | eCEDR keeps children and siblings rows after the count is set to none; nothing checks the row count | [A48][adef] |
| A49 | 3 | DR | eCEDR: the 'which other autoimmune disease' textbox accepts digits only | [A49][adef] |
| A50 | 3 | ASP | eAsperger family gate script binds the wrong field name, so the gate has no effect | [A50][adef] |
| A51 | 3 | ASP | eAsperger follow-up family form has no relatives table; retired follow-up forms leave their columns | [A51][adef] |
| A52 | 3 | ASP | eAsperger history list tables keep their rows after the section gate is set to no or unknown | [A52][adef] |
| A53 | 3 | ASP | eAsperger boxes default to 0 and are written 0 on every save, so a 0 is not an answer | [A53][adef] |
| A54 | 3 | BP, SZ | The gynaecological section is shown to men and the answers are kept | [A54][adef] |
| A55 | 3 | SZ | The eSchizo copy script (A31) names three fields absent from the SZ form | [A55][adef] |
| A56 | 3 | ASP | eAsperger form 193: the pulmonary code 'Allergie' is commented out; the allergy gate holds only 1 or empty until 2019 | [A56][adef] |
| A57 | 4 | BP, SZ | DSM-5 diagnosis forms have no onset age of the eating disorder; the DSM-5 form adds night eating syndrome | [A57][adef] |
| A58 | 5 | BP, SZ | Medication list: the end-before-start check is wrong on the add form and missing on the correction page | [A58][adef] |
| A59 | 5 | BP | BP C-SSRS deterrents item shows the text of the controllability question | [A59][adef] |
| A60 | 5 | BP | BP suicide group tables lack groups 4 and 6, so the violent and serious attempt blocks are no longer shown | [A60][adef] |
| A61 | 5 | DR | eCEDR C-SSRS and suicide forms: handlers clear the wrong fields, a menu flag is never set, rows are not deleted | [A61][adef] |
| A62 | 6 | SZ | eSchizo SUMD script stops with an error before it applies the attribution rule | [A62][adef] |
| A63 | 6 | BP, SZ | The CGI efficacy index is computed only on a label click, so it goes stale (extends A7) | [A63][adef] |
| A64 | 6 | BP, SZ | The patient-state checklist script gives -999 to 'Ne sais pas' and stops on a blank item | [A64][adef] |
| A65 | 6 | SZ | eSchizo BARS: item 1 has no upper bound; the percentage is never exported | [A65][adef] |
| A66 | 6 | DR | eCEDR FAST script empties all domains when one item is blank and leaves zero-sum domains empty | [A66][adef] |
| A67 | 6 | ASP | eAsperger Vineland score script never runs, so all sums and composites are typed | [A67][adef] |
| A68 | 6 | BP | BP DIVA sums load for the DSM-IV table only | [A68][adef] |
| A69 | 6 | BP | BP follow-up diagnosis: the episode total omits mixed episodes and is never saved by the script | [A69][adef] |
| A70 | 6 | DR | eCEDR form 182 is in no menu and its total is never filled | [A70][adef] |
| A71 | 6 | DR | eCEDR forms 116 and 183: the psychotic count of manic episodes shows only when the hypomanic count is above 0 | [A71][adef] |
| A72 | 7 | ASP | eAsperger CTQ script: wrong value for reversed items and two items read from radios that do not exist | [A72][adef] |
| A73 | 7 | BP, SZ, DR | The CTQ denial score counts an unanswered item as 0 | [A73][adef] |
| A74 | 7 | DR, ASP | PSQI scripts: efficiency wrong before midnight; two eAsperger components add answers as text | [A74][adef] |
| A75 | 7 | SZ, DR, ASP | An untouched time field saves 00:00:00; the 24-hour warning exists on the BP PSQI form only | [A75][adef] |
| A76 | 7 | ASP | eAsperger STAIC state script reverses the wrong adjectives and maps the answers wrongly | [A76][adef] |
| A77 | 7 | DR | eCEDR QIDS: the weight-gain answer clears the wrong item (see R155) | [A77][adef] |
| A78 | 7 | BP, ASP | eBipolar ASRS script tests the wrong variable; the eAsperger ASRS form has no score field | [A78][adef] |
| A79 | 7 | ASP | eAsperger ADOS-2 script: module-4 class precedence defect, module-2 cut-offs to check, old values not recomputed | [A79][adef] |
| A80 | 7 | SZ | eSchizo SOGS item 4 always scores 1; EPHP 'cannot be assessed' counted as 7 points, old values not recomputed | [A80][adef] |
| A81 | 7 | ASP | eAsperger scripts of smaller scales (GSQ, CCC-2, AIM, BVAQ, ABC): six scoring defects | [A81][adef] |
| A82 | 7 | DR, ASP | Old forms keyed differently from their current versions (BIS, BFI); one form offers the wrong tic answers | [A82][adef] |
| A83 | 7 | ASP | eAsperger EQ-5D: indices typed without decimal separator; the script needs the VAS | [A83][adef] |
| A84 | 8 | BP, SZ, DR, ASP | The RR help text of the nurse file gives the inverse formula, in all four applications | [A84][adef] |
| A85 | 8 | DR | eCEDR MINI suicide-risk level: the scores 1, 9 and 17 get no level | [A85][adef] |
| A86 | 8 | DR | eCEDR MINI OCD: handlers reset the conclusion after G6 is answered | [A86][adef] |
| A87 | 8 | DR | eCEDR MINI panic: D6 is cleared on reload when no symptom is ticked | [A87][adef] |
| A88 | 8 | DR | eCEDR MINI: the text of option 1 of C4 says the opposite of the MINI | [A88][adef] |
| A89 | 8 | DR | eCEDR MINI alcohol dependence counts five of the seven criteria | [A89][adef] |
| A90 | 8 | DR | eCEDR MINI GAD: N4 is hidden and unticked on load; the 'no' of N2 cannot be saved | [A90][adef] |
| A91 | 8 | DR | eCEDR MINI antisocial personality: inverted load condition; the conclusion ignores P1 | [A91][adef] |
| A92 | 8 | DR | eCEDR MINI mood summary: a typo makes the psychotic-feature boxes ignore two items | [A92][adef] |
| A93 | 8 | SZ | eSchizo Barona scripts: an unknown label counts 0 without warning; a change of age does not recompute | [A93][adef] |
| A94 | 8 | ASP | eAsperger social cognition: the total and faux pas scores have no range check | [A94][adef] |
| A95 | 8 | ASP | eAsperger parents' form: the parent 2 block says 'parent 1' for two fields | [A95][adef] |
| A96 | 8 | ASP | eAsperger schooling block is cleared on load when its gate is empty, so re-saving erases the answers | [A96][adef] |
| A97 | 8 | DR | eCEDR MINI psychotic module: a reused list variable hides the wrong items | [A97][adef] |
| A98 | 8 | DR | eCEDR MINI PTSD: H5 opens at different thresholds on load and on change | [A98][adef] |
| A99 | 8 | ASP, DR | eAsperger hide statements point to divs that do not exist; eCEDR nurse file hides a missing div | [A99][adef] |

Two batch 1 defects got new evidence; see the new-evidence table in part 1.

### Answers of the application developers

```text
A45: 
A46: 
A47: 
A48: 
A49: 
A50: 
A51: 
A52: 
A53: 
A54: 
A55: 
A56: 
A57: 
A58: 
A59: 
A60: 
A61: 
A62: 
A63: 
A64: 
A65: 
A66: 
A67: 
A68: 
A69: 
A70: 
A71: 
A72: 
A73: 
A74: 
A75: 
A76: 
A77: 
A78: 
A79: 
A80: 
A81: 
A82: 
A83: 
A84: 
A85: 
A86: 
A87: 
A88: 
A89: 
A90: 
A91: 
A92: 
A93: 
A94: 
A95: 
A96: 
A97: 
A98: 
A99: 
```

---

## Part 3. Data managers (M items)

46 questions. The full text of each is in the paragraph 'Questions for the data managers' at the end of its batch section. Please answer with counts only, never patient codes.

| # | Batch | Cohorts | Title | Full text |
|---|---|---|---|---|
| M50 | 2 | DR | DR prolactin: are the many results of 100 or more at some centres mUI/L typed under the first unit? | [batch 2][b2] |
| M51 | 2 | ASP | ASP CRP: is it high-sensitivity, and in mg/L or mg/dL? | [batch 2][b2] |
| M52 | 2 | DR | Why do DR lithium, valproate or oxcarbazepine levels appear without their box ticked? | [batch 2][b2] |
| M53 | 3 | BP | BP: does the application store the suicide answer of the second sibling (filled far less often)? | [batch 3][b3] |
| M54 | 3 | ASP | ASP: was the pulmonary code 'Allergie' moved to the allergy gate in 2020 and its rows deleted? (see A56) | [batch 3][b3] |
| M55 | 3 | SZ | Did the SZ migraine question, its practice or the form change in 2018? | [batch 3][b3] |
| M56 | 3 | SZ | Is the SZ menopause hormone therapy never 'yes' because answers are lost? | [batch 3][b3] |
| M57 | 3 | DR | Can the DR 'which other autoimmune disease' textbox take letters? (see A49) | [batch 3][b3] |
| M58 | 3 | BP, DR | Are onset dates after the visit date typing errors worth sending back to the centres? | [batch 3][b3] |
| M59 | 3 | ASP | Can the eAsperger list tables save a row with no disease code? | [batch 3][b3] |
| M60 | 3 | SZ | Did the SZ family form or its practice change around 2018? | [batch 3][b3] |
| M61 | 4 | SZ | The SZ anxiety screening says 'ten months': is it a typo for six? | [batch 4][b4] |
| M62 | 4 | BP | Why are the details of a ticked BP substance box often empty, with large differences between centres? | [batch 4][b4] |
| M63 | 4 | BP | Does the dataflow correction of the anxiety gate run on BPALL? | [batch 4][b4] |
| M64 | 5 | BP | Is the BP SIS and behaviour block filled in the database, and which attempt does the SIS rate? (informs R126) | [batch 5][b5] |
| M65 | 5 | DR | How many rows per patient does the DR lifetime medication table hold? (informs R122) | [batch 5][b5] |
| M66 | 5 | DR | Is the DR suicidal-ideation form chosen per centre? | [batch 5][b5] |
| M67 | 5 | SZ | Was the top gate of the SZ care changes removed in mid-2019? (informs R132) | [batch 5][b5] |
| M68 | 6 | DR | Why are DR FAST domains with all items at 0 empty on complete visits? (see A66) | [batch 6][b6] |
| M69 | 6 | DR | Is the DR YMRS switched off per centre, beyond the simplified visit? (informs R139) | [batch 6][b6] |
| M70 | 6 | BP | Was the BP depressive-symptoms checklist taken off its menu? | [batch 6][b6] |
| M71 | 6 | ASP | Is the ASP axis I list form chosen per centre? | [batch 6][b6] |
| M72 | 6 | ASP | Can one ASP centre check its swapped or inconsistent Vineland scores? (see A67) | [batch 6][b6] |
| M73 | 7 | DR | What does the DR follow-up MDQ ask? | [batch 7][b7] |
| M74 | 7 | DR | Why is the DR SPIN filled at follow-up and in patients without social phobia? | [batch 7][b7] |
| M75 | 7 | DR | Until when, and in which centres, were the old DR BIS and BFI forms used? (see A82) | [batch 7][b7] |
| M76 | 7 | ASP | What rule does the ASP centre that types scores without items apply? (informs R154) | [batch 7][b7] |
| M77 | 7 | BP, DR | Which MAThyS direction did centres still on the old direction use on the new form? Is the overlay still given? (extends M47) | [batch 7][b7] |
| M78 | 7 | DR | DR Paykel: what does the month of an event mean, and what period do follow-up event lists cover? | [batch 7][b7] |
| M79 | 7 | DR | DR physical activity: are sitting hours above 24 a day weekly figures? | [batch 7][b7] |
| M80 | 8 | SZ | Which nurse script runs in the SZ centres? (informs R159) | [batch 8][b8] |
| M81 | 8 | BP, SZ | How many raw BP and SZ blood pressures contain '/'? (informs R170) | [batch 8][b8] |
| M82 | 8 | DR | How was the DR QTc computed in 2012-2016? | [batch 8][b8] |
| M83 | 8 | ASP | What is the unit of the ASP cigarettes field at one centre? | [batch 8][b8] |
| M84 | 8 | ASP | Which block does the ASP follow-up change box FNMCHANG cover? | [batch 8][b8] |
| M85 | 8 | SZ | How were the 28 SZ LIS scores of 2022-2024 written? | [batch 8][b8] |
| M86 | 8 | SZ | Which answer labels did the Barona scripts of two SZ centres know? (see A93) | [batch 8][b8] |
| M87 | 8 | DR | DR MINI: which version, which suicidality points and bands, lifetime or since the last MINI, and why rows at V3 and V5? (see A85) | [batch 8][b8] |
| M88 | 8 | DR | Which rule showed the MDD box of the DR MINI mood summary? | [batch 8][b8] |
| M89 | 8 | DR | What does a DR MINI O2 'no' mean for a patient with no medicine and no illness? | [batch 8][b8] |
| M90 | 8 | ASP | ASP: are hospital counts stays or days, and what does each centre count as years of education? | [batch 8][b8] |
| M91 | 8 | ASP | Does the old ASP social module hold records? | [batch 8][b8] |
| M92 | 8 | DR | DR end of follow-up: do saved forms exist, and can the cause be exported? | [batch 8][b8] |
| M93 | 8 | all | Will future extractions turn four social codes into words, as the nucleus data_qa rules would? | [batch 8][b8] |
| M94 | 8 | SZ | Why did the SZ referral form stop being filled from 2019-2020 at some centres? | [batch 8][b8] |
| M95 | 8 | SZ | Why does one SZ centre store a QTc on so few of its nurse visits? | [batch 8][b8] |

One batch 1 question got new evidence; see the new-evidence table in part 1.

### Answers of the data managers

```text
M50: 
M51: 
M52: 
M53: 
M54: 
M55: 
M56: 
M57: 
M58: 
M59: 
M60: 
M61: 
M62: 
M63: 
M64: 
M65: 
M66: 
M67: 
M68: 
M69: 
M70: 
M71: 
M72: 
M73: 
M74: 
M75: 
M76: 
M77: 
M78: 
M79: 
M80: 
M81: 
M82: 
M83: 
M84: 
M85: 
M86: 
M87: 
M88: 
M89: 
M90: 
M91: 
M92: 
M93: 
M94: 
M95: 
```

[b2]: EXPORT_REQUESTS.md#batch-2-2026-11-19-biology-tab
[b3]: EXPORT_REQUESTS.md#batch-3-2026-11-19-antecedents-tab
[b4]: EXPORT_REQUESTS.md#batch-4-2026-11-19-substances-and-comorbidities-tab
[b5]: EXPORT_REQUESTS.md#batch-5-2026-11-19-suicide-care-use-and-treatments-tabs
[b6]: EXPORT_REQUESTS.md#batch-6-2026-11-19-evaluation-and-hetero-questionnaire-tabs
[b7]: EXPORT_REQUESTS.md#batch-7-2026-11-20-auto-questionnaire-tabs
[b8]: EXPORT_REQUESTS.md#batch-8-2026-11-20-patient-vital-signs-and-ecg-perinatal-and-social-tabs-dr-mini-asp-socio-demographic-and-clinical-sections
[adef]: EXPORT_REQUESTS.md#application-defects-for-the-developers-of-ebipolar-eschizo-ecedr-and-easperger
[mdm]: EXPORT_REQUESTS.md#questions-for-the-data-managers-counts-only-the-database-can-give
[r10]: EXPORT_REQUESTS.md#r10-dr-compute-the-age-at-the-v0-visit-and-keep-the-active-record
[r23]: EXPORT_REQUESTS.md#r23-height-keep-the-decimal-point-that-the-export-removes
[r24]: EXPORT_REQUESTS.md#r24-ecg-heart-rate-rr-qt-and-qtc-blank-the-impossible-zeros
[r33]: EXPORT_REQUESTS.md#r33-perinatal-texts-stop-turning-some-typed-answers-into-wrong-numbers
[r34]: EXPORT_REQUESTS.md#r34-write-5-daughters-sons-sisters-or-brothers-as-6
[r41]: EXPORT_REQUESTS.md#r41-bp-age-at-first-job-keep-the-answers-15-and-60
[r42]: EXPORT_REQUESTS.md#r42-bp-household-size-and-work-durations-do-not-run-two-numbers-together
[r46]: EXPORT_REQUESTS.md#r46-sz-saltyp-export-the-ticked-income-labels
[r47]: EXPORT_REQUESTS.md#r47-sz-maristat-match-the-sz-label-of-married-or-living-as-a-couple
[r48]: EXPORT_REQUESTS.md#r48-sz-export-the-socio_demog-form-in-its-own-columns
