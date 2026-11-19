# FACE BP — open questions, as a list to close

Extraction: `BPALL_20261113_2.tsv` (22,171 visits of 6,498 patients).
Dictionary: `FACEBP_thesaurus_V4.34.xlsx`.

First written on 2026-11-13 as 35 questions for the EMR developers, the data
manager and the principal investigator (D62). Rewritten on 2026-11-17 as a
list of things to close: the questions answered since then are removed, and
the others are sorted by who can close them. The counts inside the items are
those of the extraction of 30 October 2026, unless a decision says otherwise.

Every column of the extraction is read by the `facedata` package. Where the
data were ambiguous, the package took a careful default and wrote it down.
This list holds what is still open, so that the defaults can be replaced by
facts.

**How to read it**

- One box per item: `[ ]` open, `[x]` closed, with the decision that closed
  it.
- The numbers are those of the document of 13 November and do not change:
  DEV- (what the forms ask, what the application computes, what the export
  writes), DM- (dictionary, units, values, norm tables), PI- (choices of
  method), FU- (follow-up questions). An O-number is an open question of
  [PROGRESS.md](PROGRESS.md) that had no number here.
- **A**: the answer changes the values delivered for many patients, or lifts
  a doubt on a whole period. **B**: it concerns one instrument or a group of
  patients. **C**: a confirmation or a correction that changes no analysis.
- "Today" says what the package does while the item is open.
- The reference at the end of a title (O29, D47...) points to the full
  evidence in [PROGRESS.md](PROGRESS.md).

**Two new sources (2026-11-17).** The project can now read the source code
of the application (eBipolar v3) and use its development instance, which
holds test records only. Most questions written for the EMR developers no
longer wait for an answer: they are in section 1. Two limits: the history of
the code starts in January 2024, and the development instance runs the forms
of today. Neither says how a form looked in 2012 or in early 2022.

**What is not here.** Only counts are given, never a patient. The centres
are not named, because this repository is public: their codes can be given
on request. 134 of the 135 schemas are reviewed; the other one is a draft until
its review (PI-12).

| Section | Open | Who closes it |
|---|---|---|
| 1. To read in the application | 0 | The project, in the source code and on the development instance |
| 2. To check on the data or the publication | 0 | The project |
| 3. Choices of method | 3 | The project lead and the principal investigator |
| 4. For the data managers, the centres and the developers | 18 | The data managers; still to send. The requests to the export are in [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md) |

## Answered and removed

The answers are decisions of [PROGRESS.md](PROGRESS.md). The questions below
are closed and are no longer in the list. Those of 2026-11-17 were read in
the application (its source code and its development instance) and decided
with the project lead.

| Question | Answer | Decision |
|---|---|---|
| DEV-4, three questionnaires lost answers in the export | Corrected in the extraction of 13 November: the Epworth is loaded, the Fagerström and CSM totals are complete | D64 |
| DEV-5, parts 1 to 3, reduced questionnaires | The long forms were filled until 2021 (2022 in two centres); the AIM-40 was replaced by the AIM-20 too; no field records the form | D66, D67, D75 |
| DEV-6, MAThyS sub-scores | The data managers recalculate them from the items with one formula for every year | D65, D75 |
| DEV-6, sign of the TMT z-scores | Historical; the old values are flipped to one convention | D13, D23 |
| DEV-9, part 3, death of the mother | A mapping error of the export, corrected | D70 |
| DEV-13, `rad_tb_subst` | "Unknown" is left empty on purpose; the full answer is in `rad_tb_subst_raw` | D74 |
| DEV-14, `als57` holds two scores | Confirmed; it is what the schemas read | D67 |
| DM-3, `formoppos` as an opposition | The data managers answered that the export removes the oppositions, codes 3 and 4. The form shows that `formoppos` is not the opposition: asked again as DM-11 | D68, D94 |
| DM-7, coding of `social_protec` | 0 none, 1 curatelle, 2 tutelle, 3 sauvegarde de justice | D68 |
| DM-8, `isf08_qsdtc` | The question was removed from the BP form | D69 |
| FU-1, a column that names the form | There is none; the rule stays | D75 |
| FU-2, `als55` | Written by the score step of the data managers, on every visit where its five items are answered | D72 |
| FU-3, reduced forms before 2021 | Not delivered (FU-10 stays) | D71 |
| FU-4, patients who left the extraction | Registered in two centres; no opposition (FU-9 stays) | D73 |
| FU-5, `formoppos` codes 1 and 2 | Not documented by the data managers; read on the form: 1 adult patient, 2 under curatelle | D75, D94 |
| FU-6, other lookup tables | All checked; no other answer is lost | D74 |
| FU-7, MAThyS recomputation | Intended | D75 |
| DEV-1, medical history from 2022 (2026-11-17) | Seven sections of the form start with a shortcut, "Non pour tous" or "Ne sais pas pour tous". In eBipolar it leaves each disease unanswered, and the extraction does not hold it. The seven fields are asked for (DM-10) | D83 |
| PI-2, how to use the medical history from 2022 | As recorded until the shortcuts are exported; then a "Non pour tous" gives 0 to each disease of its section | D83 |
| DEV-2, what the yearly forms ask | Medical history, family history, comorbidities and psychotic disorder: the inclusion form again, same wording, after "is there a change since the last visit?". Suicide, mood episodes, hospitalisations, care, sick leave: "since the last visit". A `_fu` answer of the first group is a yearly update. The family form has no `_fu` twin: a later answer is ignored by the first-answer rule (378 patients answer the counts at two or more visits; among the parents and grandparents 190 "yes" become "no" and 55 "no" become "yes"; 60 parents or grandparents pass from alive to deceased; PI-15) | D84, D148 |
| DEV-3, suicide questions at follow-up | Two forms; the follow-up form of today says "since the last visit". The one of 2022 and 2023 also asked about the whole life in part of the centres: each centre runs its own copy of the application | D85 |
| PI-3, follow-up suicide answers of 2022 and 2023 | Not delivered, the "yes" and the "no" alike | D88 |
| O47, history of suicide attempts at follow-up | Split: the whole life at inclusion, since the last visit at follow-up; a date of the first attempt typed at follow-up is not delivered | D86 |
| PI-11 and DEV-10, `rad_agethym`, `age_ehman`, `age_epman` | Age at the first mood stabiliser; ages at the first hypomanic and manic episodes | D87 |
| DM-9, screening rows | The screening visit has its own forms (Altman, QIDS, MDQ, a screening form); the rows are read | D90 |
| Found on the way: the age at the first episode of the DSM-5 form | It is the age at the first depressive episode; the first episode is now the earliest of the three ages of the form | D89 |
| O45, MAThyS key | The application's key is the published one for the reversed items, and its five sub-scores are the factors of the validation study (to confirm on the paper). Item 17 went against the scale because of the form, not of the key | D91 |
| Found on the way: the MAThyS has two forms | The old form stored eight scales already turned towards the score. They are turned before September 2021 and not delivered until the end of 2022, while the centres changed form | D91 |
| O45, BIS-10 key | The script of the application names the three sub-scales that the schema found (8, 11 and 11 items); the French publication is not checked | D92 |
| DEV-7, PI-6 and O1, BIS reversed items | `5 − value`, as the application's script does. The `6 − value` is in the score step of the data managers (DM-13) | D92 |
| O44, PSQI at exactly 7 hours | Kept as stored (0): the application tests "7 hours or more", and the published sheet does not settle 7 hours | D93 |
| DEV-10 and O35, source of income and work status | On the form, income 7 is "other"; the students are exported with "other" in the work status (DM-13) | D94 |
| DEV-10 and O16, `formoppos` | The form that was used: 1 adult patient, 2 under curatelle, 3 under tutelle, 4 minor. The opposition is another question (DM-11) | D94 |
| DEV-10, sick-leave columns at follow-up | On sick leave since the last visit for a psychiatric disorder; number; total duration in weeks | D94 |
| DEV-9 and O39, family history form | The siblings and children described are the affected ones, in order, up to five. The form offers "more than 5" relatives, never exported (DM-14). The dates of the parents and grandparents are hidden on the form of today | D95 |
| DEV-12, treatments | No end date means running: it is the application's rule (box "Traitement en cours", written 0000-00-15). The daily dose is the strength times the units a day; the strength is not exported from 2018 (DM-14) | D96 |
| DEV-5, part 4, order of the questions on the reduced forms | ALS-18 and AIM-20: numbered in the rising order of the numbers of the long forms; WURS-25: the numbers of the long form are printed | D97 |
| PI-1, a cumulated lifetime column | No: `_v0` and `_fu` stay two sets of columns | D100 |
| PI-7, O2 and O3, results below a limit | "<5" stays 5 with its censoring column; a CRP of exactly 0 is delivered as missing, in the four cohorts | D101 |
| PI-5 and O36, the medication table | Checked against the application's own drug list (129 of 131 groups, 128 of 135 ATC codes). Gabapentin and pregabalin go with the anticonvulsants, as there | D102 |
| PI-9, family summaries | The strict rule stays | D103 |
| O30, items of the long forms | Not asked for; the form stays read from the ALS and the BIS of the visit | D104 |
| O46, screening visit in the baseline row | No default limit; `max_days` sets one | D105 |
| PI-4, bridges between forms | The existing bridge scores are enough | D107 |
| DM-2, scoring keys | The scripts of the application are the scoring rules; the keys of the schemas are the same for the twenty scales compared. Scores are computed on a button and not on saving, which explains most stored scores that do not follow their items | D106 |
| PI-10 and DEV-8 (2), CVLT z-scores (2026-11-17) | The z-scores are computed again with the regressions of the application's script, from the raw score, the age at the visit, the years of education and the sex. The script gives back 95% to 99% of the stored z-scores; of those of trials 1 to 5, 232 were computed with the coefficients of the age and of the sex exchanged (2013 and 2014; the patients of 70 and over until August 2024) and 105 with no sex. The stored z-scores are kept as a check. Two lines of the recency norm are corrected (the mean from 40 to 69, the sign of the age term from 70): see DM-16 | D108, D109 |
| DEV-6, dated list of the changes of rule | What the code can tell (its history starts in 2024): 2024-07-25, 1000-01-01 written in every empty date; 2024-08-02, CVLT regression of the patients of 70 and over corrected; the TMT "<5" is a defect of today's script | D98 |
| DM-11, does the export remove the patients who object? (2026-11-18) | No step of the export reads the answer "objects"; it removes the records with a tutelle or minor form (`formoppos` 3 or 4) or under sauvegarde de justice (PROTEC 3), row by row. The project lead decided not to use the opposition answer: nothing is asked of the export | D119 |
| DEV-11, how the export decides between DSM-IV and DSM-5 (2026-11-18) | From the content of the two inclusion records: DSM5 when the DSM-5 record holds one of five lifetime answers, else DSM4; follow-ups never get one. Of the 849 empty inclusions, 202 are centre C's, whose DSM-5 table is missing from the export. Asked of the export: R20, R68 to R70. In the package, a placeholder date no longer counts as a filled form, and the follow-ups keep the switch date of 2022 | D119, D122 |
| DEV-8 and O28, the CVLT serial-clustering table and the tie rule (2026-11-18) | The script of the application holds the exact limits (decimals from 40 to 69 years), the same in the BP and the eSchizo forms. The band is recomputed from the raw index like the eleven others; 784 BP bands change (692 written 99 become "95 or higher"). The tie rule is an accident of the loop: the CVLT script advances while the score is above a limit (so it stops at the highest percentile), the TMT script while it is at or above (the lowest); nothing says it is meant. The package keeps one rule | D129 |
| PI-8, plausible limits (2026-11-18) | Read with the limits table and the cross-cohort screen: one hard range per variable shared by two cohorts (a test fails on a new difference); the hard range is applied to times (a night of 90 hours was delivered); an index of semantic clustering of 8 or more is a typed count; platelets in hundreds of G/L are recovered; a prolactin of 0 is "nothing measured"; HbA1c in mmol/mol is converted (D127) | D130 |
| PI-13 and O51, empty boxes of the use of care (2026-11-18) | Read as no beside a ticked box, as for the non-drug treatments: 2,106 boxes and 2,106 numbers become 0, no written value changes; a box whose number was typed is left as written | D131 |
| PI-10, standard scores of the neuropsychological tests (2026-11-18) | Computed again from the raw scores with the tables of the application's scripts for the TMT, the WAIS-III and WAIS-IV subtests and indices, the Stroop, the fluency, the spatial span, the SCIP and the errands; the stored scores are checks and their differences are flagged. Not done: LIS, Barona, fNART. The tables are the application's and are not checked against the manuals (DM-4) | D135 |
| NEUROPSYCHOLOGIE tab review, four cohorts (2026-11-19, D138 to D143) | Every neuropsychological test of BP, SZ, DR and ASP was read against the form, the application script and the data, and recomputed where its rule is known: the WAIS family with one similarities, total and table rule (SZ edition O16 closed; BP vocabulary row 25-29 from ASP; ASP age at the form date and shared index names), TMT, errands (years of education), CPT checks, CVLT discriminability, the DR tests (D2, Baddeley, RL/RI-16, auditory span, designs) from the DR script tables, Barona, fNART, LIS and SSTICS (new expected-value and distance scores). The tables are compared across the four applications and not checked against the manuals (DM-4 stays open). 79 of the 83 schemas of the tab are `reviewed` |
| BILAN BIOLOGIQUE tab review, four cohorts (2026-11-19, D144) | The 35 schemas were read against the forms, the application scripts and the data. No unit mismatch between cohorts. A shifted block of lab results (one BP centre to 2023, one DR centre to 2022) is removed by a pooled data rule (`implausible_pool`: BP 29 visits, DR 35); the clipping of lab tails is kept (the project lead's choice); prolactin typed in mg/L, glucose in mg/dL, DR vitamin D code 2 and ASP code 64387 are read; zeros that mean not measured are missing codes; the notes carry the causes of the lipid ratio mismatches, the clearance, the unmarked CRP limits and the form caps. All 35 schemas are `reviewed`; open points (iron in micrograms per decilitre at one centre, DR prolactin of two centres, SZ vitamin D of one centre, the ASP CRP, clozapine of 1 to 19) wait on the centres (requests R102 to R106) |
| ANTECEDENTS tab review, BP (2026-11-19, D145 to D149) | The 20 schemas were read against the forms of the application, the graph of their dependencies and the data. The three retention boxes hang on the retention itself, the hormone therapy is a detail of the menopause (missing after a "no"), `nephropathy_treatment_related` is `nephropathy_lithium`, hepatitis D has its code, and the type of diabetes of a relative is shown after its box only (3 cells `not_shown`). The notes carry the yearly-update wording (D84), the shortcut "Non pour tous" and the change question that is not exported (DM-10), the placeholders by year (DEV-13), the counts measured again and, for each year or centre shift of the QC table, its cause. "More than 5" relatives is lost, not written 5 (DM-14). All 20 schemas are `reviewed`; open: PI-15 (later family answers), `frere2_suicide` (M53, DM-5), the skin Oui/Non pattern (DM-5) | D145 to D149 |
| SUBSTANCES ET COMORBIDITE tab review, BP (2026-11-19, D150 to D157) | The 9 schemas were read against the forms and the export model of the application and the data. The two panic type columns hold social phobia (they are ignored, R113) and the panic box, which the export builds with a substring match, becomes a score missing where only the agoraphobia box can have ticked it (362 cells); the eight substance boxes hang on the first question (no cell changes); six box labels carry the form's option texts. The notes carry the three tables of the application, the yearly-update wording (R4), the export losses (the age tokens and the substance-induced block, R117; the dictionary rows, R119; the nicotine substitution, R120; the eating age missing from the DSM-5 form, A57), the details left empty under a ticked box, the whole-tab-empty steps from 2022 (O40), the tobacco status that is not "never smoked", the counts measured again and, for each year or centre shift of the QC table, its cause. All 9 schemas are `reviewed`; open: DM-6 (centres, M62), DM-7 (dictionary rows), DM-17 (gate correction, M63), PI-16 (an "ever smoked" column) | D150 to D157 |
| PI-14 and O53, dates of the most recent episode after the inclusion visit (2026-11-18) | Kept as written (the project lead's choice): 114 starts and 212 ends later than the visit are full typed dates that the data cannot tell from an expected end | D131 |

## 1. To read in the application

What the forms ask and what the application computes. Each item is read in
the source code first, then checked on a form of the development instance.

### Priority A

### Priority B

Nothing open today. The norms of the other tests (PI-10, DM-4) wait on their tables and on the manuals.

### Priority C

## 2. To check on the data or the publication

Nothing open today. The screening pass of BP that follows this list will add
its findings here.

## 3. Choices of method

For the project lead and the principal investigator. Each has a default
that the package follows today. PI-12 is a piece of work that is decided and
still to do.

### Priority B

- [ ] **PI-15. Later family answers are not delivered.** (D148, DEV-2; new on
  2026-11-19) The family is described at the inclusion visit and sometimes
  again at the yearly visits: 378 patients answer the counts of relatives at
  two or more visits, and 231 of them change at least one answer (among the
  parents and grandparents 190 "yes" become "no" and 55 "no" become "yes";
  60 parents or grandparents pass from alive to deceased). `family_structure`
  and `family_history` keep the first answer and flag the others
  `patient_value_varies`. Should they get a yearly twin, as the medical
  history has (D84, D100), or stay first answer? The default is the first
  answer; the notes say that a later answer is ignored.
  - Today: the first answer of each relative and question is delivered.

### Priority C

- [ ] **PI-16. Tobacco: a per-patient "ever smoked"?** (D156; new on
  2026-11-19) "Non fumeur" is the status of the day, not "never smoked": a
  patient who is a non-smoker at a visit was a current or ex-smoker at an
  earlier visit in 957 of 7,876 non-smoker visits (12%); ex-smoker to
  non-smoker happens in 349 of 1,194 pairs of consecutive visits, and 194
  patients are ex-smokers at a visit and current smokers at a later one.
  Should the package deliver an analyst-facing per-patient column (ever a
  current or ex-smoker, the first start age, the latest pack-years), as it
  does for the family history (D103)? The default is no such column: the
  note of `tobacco` forbids deriving 0 pack-years from "Non fumeur".
  - Today: one value per visit, as recorded.

- [ ] **PI-12. Review of the schemas.** Done: PATIENT, four schemas reviewed
  and one removed (D111); HETERO-QUESTIONNAIRES, seven reviewed (D113);
  CONSTANTES et ECG, three reviewed (D114); SOCIAL, one reviewed (D116);
  PERINATALITE, one reviewed (D117); EVALUATION MEDICALE, fifteen reviewed
  (D122); SOIN SUIVI HOSP ARRET TRAVAIL, six reviewed (D123); TRAITEMENTS,
  four reviewed (D124); SUICIDE, ten reviewed after the splits by form
  (D125); with the audit of the four cohorts, `errands_test` (D126) and
  `biochimie` (D127); AUTO-QUESTIONNAIRES, 26 of 27 (D134); NEUROPSYCHOLOGIE, the 20 drafts of the
  tab (D138 to D143, with 58 of the 62 schemas of the same tab in SZ, DR and
  ASP; the 4 left as drafts are SZ barona, lis and WAIS-III digit span and
  ASP social cognition, for gaps with no known cause). BILAN BIOLOGIQUE, the 6 drafts of the tab (D144, with the 28 schemas of the
  same tab in SZ, DR and ASP). ANTECEDENTS, the 20 drafts of the tab (D145 to
  D149). SUBSTANCES ET COMORBIDITE, the 9 drafts of the tab (D150 to D157). 134 of 135 are
  reviewed; the other one is a draft (MAThyS). Each
  has notes that state what was asked, how the score is computed and what
  remains doubtful. Decided on 2026-11-17 (D107): the project lead reviews
  them tab by tab, in working sessions that follow this list; a schema read
  and agreed becomes `reviewed`.

## 4. For the data managers, the centres and the developers

What reading the application cannot settle: the export, the dictionary, the
laboratories, the habits of the centres, and the defects to correct at the
source, in the export or in the application. Still to send.

### Priority A

- [ ] **DM-1. Lab results typed on another scale under the default unit
  label.** (D28, D31, O20)
  - What we see: the unit column carries a default label, so the unit must
    be read from the size of the value. About 2,900 results are concerned:
    haematocrit as a fraction (477), MCHC in g/L (550), haemoglobin in g/L
    (473), iron in µg/dL (about 360), total cholesterol in g/L (about 250),
    glucose in g/L (124), free T4 in ng/dL (99), uric acid on three scales
    (about 150), and smaller numbers for phosphate, creatinine, calcium,
    urea and alkaline phosphatase. About 850 white-cell counts are
    percentages.
  - Prolactin is the hard case: no unit was chosen for 72% of the results.
    About 320 are in mUI/L, most from one centre during two periods. **174
    results cannot be given a unit.** Clozapine levels are on at least three
    scales; 31 of 65 cannot be read.
  - Questions: can the centres or their laboratories say in which unit they
    reported prolactin, and when? Is there a list of the units used by each
    laboratory?
  - Today: the unit is inferred where only one fits (flag `unit_inferred`);
    the 174 prolactin results and the 31 clozapine levels are missing.
  - It changes: 205 results recovered, and the inferred units confirmed.
  - Export side, read on 2026-11-18 (batch 1 of the requests, [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)): the
    unit chosen on the form is not exported for LDL (246 results chosen as
    g/L are labelled mmol/L), and a default label is written also where there
    is no result or no choice. Asked: R26 to R31. The question of the units of
    each laboratory stays for the centres.

- [ ] **DM-10. Eight fields of the application to add to the export.**
  (D83, D84; new on 2026-11-17)
  - Seven shortcuts of the medical history, one per section, in the
    application's table `psy_histoire_medicale`: `rad_neuro_non`,
    `rad_cv_non`, `rad_endoc_non`, `rad_dermato_non`, `rad_urin_non`,
    `rad_hepato_non`, `rad_pathoa_non`. Their answers are "Non pour tous"
    and "Ne sais pas pour tous". In eBipolar the diseases of the section
    stay unanswered when the shortcut is ticked, so the extraction shows an
    empty section: at 14% to 39% of the inclusion visits from 2022, a section
    holds an answer, against about 87% before.
  - `rad_pas_dechangement`, the first question of the medical history and of
    the comorbidities at the annual visit ("is there a change since the last
    visit?"), in `psy_histoire_medicale` and `psy_troubles_comorbides`.
  - Today: an empty section is missing, not "no".
  - It changes: with the shortcuts, a "Non pour tous" gives 0 to each
    disease of its section, and the prevalence of every somatic disease from
    2022 can be computed again. FACE SZ has the same fields.
  - A ninth field, of lower priority (D114): the box "pregnant woman" of the
    nurse form (`rad_femmenceinte`, table `inf_dossier_infirmier`), next to
    the weight and the waist. Without it the weight, the body mass index and
    the waist of a pregnant woman cannot be told apart.
  - Asked of the export on 2026-11-18 (batch 1, [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)): the seven shortcuts
    (R77), the change questions of the medical history (R79), of the
    comorbidities (R65) and of the family history (R80), the pregnancy box
    (R66); the same fields in SZ (R78). Found on the way: "is there a
    change?" reads "changed" in two BP forms and "unchanged" in the
    comorbidity form and in eSchizo (A33): the export exports the answer as
    typed, and the schemas will say what it means.

- [ ] **DM-12. MAThyS: the old form stored eight scales the other way
  round.** (D91; new on 2026-11-17)
  - What we see: until the new form arrived (September 2021 to May 2022,
    centre by centre) the eight reversed scales (5 to 10, 17, 18) were
    stored already turned towards the score, and the application rightly
    added them without reversing. The new form stores them as written. Your
    recalculation of 10 November applies one formula to every year: the
    sub-scores `mathys29` to `mathys33` and the total are now wrong for the
    visits of the old form (about 11,300), where the application's own
    sub-scores were right. The total of the extraction (`mathys_`) already
    applied the key to every year in the file of October: it has been wrong
    for the old form in each extraction.
  - Requests: (1) export the sub-scores as the application stored them, or
    the form of each record (the application has two forms, the typed one
    and the slider); (2) two centres still enter the old direction on the
    new form (their codes on request): can they be asked how they fill the
    scale? (3) about 80 visits dated before September 2021 were scored with
    the new formula: were they typed or saved again later?
  - Today: the eight items are turned before 2021-09-01, and they are not
    delivered, with the total and four sub-scores, from 2021-09-01 to
    2022-12-31 (1,435 visits).
  - It changes: with the form of each record, the 1,435 visits come back
    and the two centres can be corrected.
  - Export side, 2026-11-18: the score step keeps writing its own MAThyS
    scores (decided by the project lead, D119), so request (1) becomes: say
    whether the form of each record can be told (M47 of [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)), and score
    each record with the rule of its form (R85); the slider table is read by
    no model (R52, M21). Our package computes the MAThyS from the items.

### Priority B

- [ ] **DM-13. Two defects of the score step and of the lookup tables.**
  (D92, D94; new on 2026-11-17)
  - BIS: the scores of the extraction reverse an item as `6 − value` on
    answers of 1 to 4, where the application's script reverses 4, 3, 2, 1
    (`5 − value`). Every stored score is one point too high per reversed
    item (the cognitive mean by 1, the 12-item total by 5, the BIS-10 total
    by 11). The scores of the 12-item form are also written on the visits of
    the 34-item form.
  - Work status (`stprof`): the answer "Etudiant" is never exported (code
    3); the students are in code 6, "other" (1,150 patients, 39% of them
    under 25). The same kind of defect as the apostrophe one (D63)?
  - Today: `5 − value`; code 6 is delivered as `student_or_other`.
  - Read on 2026-11-18: the BIS keys of the score step use names that its
    reader ignores, so the default scale 1 to 5 reverses as `6 − value`; the
    12-item scores are written on every visit. The work status: the export
    tests "Étudiant" with an accent, the form stores "Etudiant", and every
    other answer, an empty one included, becomes 6. Asked: R83 and R84 (BIS),
    R38 (work status), in [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md).

- [ ] **FU-8. `empjob`: export the answer of the form as it is.** (O43,
  D74, D94, D99)
  - What we see: two of the nine codes of the dictionary are exported (122
    of 2,300 employed patients), because the export looks the answers of the
    form up in the nine classes of the dictionary. The form offers 18
    classes, the second level of the INSEE nomenclature of occupations.
    FACE SZ has the same defect.
  - Request, agreed by the project lead: export the label of the form as it
    is, as `empjob_psytaitement` already is. The package will deliver the 18
    classes and derive the groups of the nomenclature:

    | Class on the form | Class of the dictionary |
    |---|---|
    | Agriculteur exploitant | 1 agriculteurs exploitants |
    | Artisan; Commerçant et assimilé; Chef d'entreprise de 10 salariés ou plus | 2 artisans, commerçants, chefs d'entreprise |
    | Profession libérale et assimilé; Cadre de la fonction publique, profession intellectuelle et artistique; Cadre d'entreprise | 3 cadres et professions intellectuelles supérieures |
    | Profession intermédiaire de l'enseignement, de la santé, de la fonction publique et assimilés; Profession intermédiaire administrative et commerciale des entreprises; Technicien; Contremaître, agent de maîtrise | 4 professions intermédiaires |
    | Employé de la fonction publique; Employé administratif d'entreprise; Employé de commerce; Personnel de service direct aux particuliers | 5 employés |
    | Ouvrier qualifié; Ouvrier non qualifié; Ouvrier agricole | 6 ouvriers |
    | No class of the form | 7 retraités; 8 autres personnes sans activité professionnelle; 0 autres |

  - The same list is asked for the last job of a patient without a job: can
    it be exported too?
  - Today: `empjob` is not loaded.
  - Asked of the export on 2026-11-18 (batch 1, [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)): the label of the
    form (R35), the class of the last job as `empjob_last` (R36), the
    follow-up work status (R44); the same in SZ (R45).

- [ ] **DM-14. Three answers that the export does not carry.** (D95, D96;
  new on 2026-11-17)
  - The strength of the medications: 2 of the 8,654 medications started from
    2018 have a strength (`med_psy_cmdose`), against 5,374 of the 7,922
    started until 2013. Read on 2026-11-18: since the public drug list the
    form stores no strength (A38 of [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)); the strength is in the product
    name. Asked: the export reads it there, with a source column (R54).
  - "More than 5" daughters, sons, sisters or brothers: the form offers it;
    the extraction stops at 5. Answered on 2026-11-19 (D147): it is lost, not
    written 5. The count of relatives is empty and the number of affected
    relatives is filled beside it (55 visits of 49 patients: 19 patients for
    the sisters, 31 for the brothers, 1 for the sons); a 5 is exactly five.
  - Still wished: one row per medication, in place of lists in one cell
    repeated on every row of the patient.
  - "More than 5" relatives: the export loses the answer (the count is
    empty). Asked: write it 6 (R34); the package will read 6 as "more than
    5". One row per medication: not asked; the lists stay.
  - Package side, 2026-11-18 (D124): until R54 ships, the package reads the
    strength from the name with the rule of R54 (one amount of a mass, not
    per volume) and delivers the daily dose in mg with a column that says
    where the strength comes from. The export reads '1/2' units as 1, which
    doubles 2 stored doses (R75); the package's dose is right there. The
    item number changes between extractions until R76 ships.
  - Today: the daily dose is the package's (strength stored, else read from
    the name); a count of relatives of 5 is read as 5.

- [ ] **DM-5. Values to query with the centres.** Each is already
  neutralised in the package (missing with a flag, or repaired with a flag).
  The centre codes can be given on request.

  | Finding | Count |
  |---|---|
  | Heights with a lost decimal point (1650 for 165.0): the export removes the point, the centres typed it (R23 of [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)) | 182 |
  | Blood pressure typed in cmHg, in six centres | 34 to 40 values per column |
  | ECG intervals typed in milliseconds, more and more often | QT 387 (274 since 2023), RR 106 |
  | RR values that look like heart rates | 25 |
  | The five kinds of white cells do not add up to the leukocytes | 222 visits |
  | Pack-years typed freely: above 200, words, fractions | 29 + 34, and 101 "NA" |
  | CVLT semantic clustering: a count typed in place of the index, mostly one centre in 2012-2013 (D130, DM-15) | 216 above 8; about 50 whole numbers between 4 and 8 stay |
  | Platelets typed in hundreds of G/L (2.47 for 247), four centres, 2011-2013 (read, D130) | 58 |
  | Prolactin of 0 where nothing was measured (a missing code, D130) | 19 |
  | HbA1c typed in mmol/mol under the label % (converted, D127) | 8 |
  | PSQI hours of sleep above 24 or an impossible time of day (removed, D130) | 3 + 2 |
  | PSQI bedtime typed on a 12-hour clock, 11:00 for 23:00 (efficiency corrected, D132) | 554 |
  | Numbers of consultations typed as words (the follow-up sick-leave number and duration lose their words in the export, which runs the digits together: 880,410 weeks is the export's, D123) | 193 cells |
  | Birth weights typed as a gestational age, or months instead of weeks | 12 and 14 |
  | CPT-II values of 1,000 or more, counts above the number of targets | 57 cells |
  | CPT-3 columns that hold a raw value instead of a T-score | About 37 visits |
  | Errands test: percentiles typed by hand in many spellings; times as "5'30" | 37 times |
  | EGF written as a band ("60-51") | 149 cells |
  | Age entered on the neuropsychology form differs from the dates by more than a year | 199 visits |
  | The inclusion visit is dated before the screening visit | 26 patients |
  | Date the information was collected is impossible (before 2008, or a year below 100) | 26 patients |
  | The gynaecological section is filled for men (kept as recorded: filter on sex) | 203 inclusion rows, 60 yearly rows |
  | Skin diseases: after a "yes" to "triggered or worsened by lithium" (valproic acid for hair loss), only one of the two answers "triggered" and "worsened" is typed, always a "yes", and the other is left empty (Oui/Non questions: an empty one is not read as a "no", D145) | 23 of 49 psoriasis, 30 of 93 acne, 95 of 246 hair loss at inclusion |
  | The suicide answer of the second brother (`frere2_suicide`) is filled in 42% of the visits that hold an answer for him, against 90% to 100% for each of the 15 other blocks with 30 answers or more: does the application store it? (asked in M53 of [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md), D148) | 74 of 178 visits |
  | The end-of-follow-up reason exists in two sets of columns with different answers | 2 of 5 patients who have both |

- [ ] **DM-6. Centres that fill a form differently from the others.** Can
  each be asked?
  - Whole tabs that four centres no longer hold since 2022 (O40, D110).
    Share of the visits that hold something of the tab, 2016-2021 then from
    2022. Did these centres stop filling these forms, or do their copies of
    the application store them elsewhere?

    | Centre (inclusions from 2022) | At inclusion | At follow-up |
    |---|---|---|
    | A (210) | Medical evaluation 79% then 20%; neuropsychology 59% then 27%; social 62% then 16%; care and hospitalisations 80% then 26%; treatments 50% then 10% | Medical evaluation 73% then 27%; care 73% then 30%; suicide 77% then 32%; treatments 94% then 52% |
    | C (178) | Medical evaluation 79% then 0% (the DSM-5 table of this centre is missing from the export, R20); biology 53% then 24%; neuropsychology 61% then 32% | Biology 64% then 30% |
    | H (128) | Biology 85% then 16%, and none of the 71 inclusions from 2024; social 40% then 2%; neuropsychology 95% then 54% | Biology 92% then 6% |
    | B (197) | Neuropsychology 91% then 46% | Medical history 60% then 10% of the yearly visits (the six-monthly visits never hold the form: 54% of all the follow-up visits) |

    The seven other centres of 40 inclusions or more are stable. Over the
    whole cohort each neuropsychological test is held by 37% to 42% of the
    inclusions since 2022, against 73% to 83% before.
  - Suicide questions at follow-up in 2022-2023: five centres of eight. Each
    centre runs its own copy of the application: which copies showed the
    questions about the whole life at follow-up, and from when to when?
    With the answer, the removal of D88 could be narrowed (O29). The form
    already shows in November 2021, where D88 now starts (D125). Centre A's
    copy wrote 2011-11-11 in the first-attempt date of every follow-up form
    it saved until May 2022, and its "yes" to "attempted" rose from June
    2022; D88 is kept for every centre (D125).
  - C-SSRS at inclusion (D125): centres G and H, and partly B and D, answer
    "yes" far more often than the other centres (wish to be dead 65% to 71%
    of their inclusions, 31% elsewhere) and rate a higher intensity (median
    sum 17, against 12 to 13), while their patients report a wish to die in
    the past week as often as elsewhere (12% against 15%). The form asks
    about the past week: do their raters ask about the whole life, as the
    paper version does?
  - The social tab is held by 29% and 39% of the inclusions of centre C in
    2016-18 and 2019-21 (71% to 89% before and after) and by 23% of those
    of centre F in 2019-21 (D116). Centre I left the perinatal section of
    the medical history empty from 2019 (1 of its 74 inclusions of
    2019-21) while filling the rest of the form (D117).
  - Prolactin in mUI/L: one centre holds 69% of the high results.
  - ECG: in two centres the RR interval typed in the form does not fit the
    heart rate of the same ECG (it agrees within 10% on 22% of their visits,
    80% to 97% elsewhere; median RR 1.1 s for a rate of 70). What do they
    type in that field? The QTc that the application computes from it is too
    low; the package computes it from the heart rate (D114).
  - The referral information (`adresseur`) is recorded for 92% of the
    patients included in 2008-2012 and 43% in 2022-2026.
  - Medical evaluation (D122). From 2022 centre B fills the DSM-5 mood form
    for about 70% of its inclusions, against 94% to 100% before, while its
    MADRS stays at 98%: is the mood evaluation of the inclusion filled
    elsewhere? Centre A has the first-episode section (and the other
    sections of the DSM-5 form) for 2 of its 141 inclusions since 2023,
    against 838 of 911 in the other centres: do these records exist in the
    application? Centre A also leaves the follow-up diagnosis form almost
    empty from 2022Q4 to 2024Q1 and from 2025Q3 while it rates the MADRS.
    Centre F answers "yes, an episode since the last visit" at 73% of its
    follow-ups from 2022 against 46% before: does it count the current
    episode? Centre F also has 12 "yes" to a psychotic disorder at
    inclusion in 2016-18 against 0 before and 5 after: real diagnoses, or
    the psychotic features of mood episodes?
  - Use of care (D123): four centres leave the number of consultations
    empty after a yes more and more often. Psychiatrist: centre A 8% until
    2018, 37% in 2019-2021, 66% from 2022; C 14%, 24%, 55%; F 4%, 46%, 57%;
    I 1%, 4%, 54%; B, D and G stay at 15% or less. Do they no longer ask
    the number?
  - Among the inclusion visits with an anxiety disorder, the stored box
    "panic disorder" is ticked on 39% until 2017 and 14% in 2025-2026 (33%
    and 13% once the visits with only the agoraphobia box are taken out:
    the export's panic box also matches "Agoraphobie sans trouble panique",
    D151, R113), while "not otherwise specified" goes from 19% to 27%-29%
    in 2024-2026: a slow change of habits, with no date.
  - The comorbidity tab (O40, D153): the four gates (anxiety, substances,
    eating disorders, somatoform disorders) are all empty on 17% of the
    inclusions and 43% of the yearly visits. Share of the inclusions with
    the four gates empty, up to 2018, in 2019-2021 and in 2022-2024:
    centre A 9%, 33%, 87%; centre C 17%, 27%, 100% (R20); centre B 1%, 8%,
    35%; centre I 2%, 20%, 58%. Did these centres stop filling the tab, or
    do their copies store it elsewhere?
  - Substance use disorders (D154, D155; M62 of
    [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)). A ticked box has all four
    details (type, past month, age, duration) empty on 18% of the boxes at
    inclusion and 17% at the yearly visits: 5% to 9% of the boxes of each
    year 2011-2016, 32% to 40% in 2018-2021 and 9% in 2022 at inclusion; the
    type alone is empty on 4% to 67% of the ticked boxes by centre at
    inclusion (centres with 25 boxes or more) and 6% to 53% at the yearly
    visits. Did the centres leave the details blank, or were they lost
    between the application and the export (the age tokens of R117 are one
    loss)? The share of "yes" to the first question is 26% to 52% by centre
    at inclusion (14 centres) and 13% to 42% at the yearly visits (11
    centres), and the alcohol "symptoms in the past month" 11% to 41% and 30%
    to 64% of the answers: another case mix, or another reading of the
    question? The first question is empty on 14% of the inclusion visits up
    to 2021 and 35% from 2022 (yearly 37% then 58%): three centres at
    inclusion (C 100% from 2022 against 21% before, A 89% against 20%, B 32%
    against 3%) and five at the yearly visits (O40).
  - Tobacco (D156). The pack-years of the smokers and ex-smokers are filled
    on 16% of the visits of one centre from 2022 (73% before) and 45% of
    another (70% before), and the status is empty on 32% of the first one's
    visits (13% before); a centre with 22 typed values has a median of 32.5
    pack-years against 7.5 to 15.3 in the centres with 100 values or more;
    42 visits give less than 1 pack-year for a patient who smoked 10 years or
    more (packs a day typed in the field?). The status is filled on 76% of
    the yearly visits of 2020 (63% in the second quarter) against 86% to 94%
    in the other years from 2014. What changed in these centres, and in
    2020? No request: nothing to change in the export.

- [ ] **DM-7. Corrections to the dictionary.**

  | Tab | Correction |
  |---|---|
  | PATIENT | `formoppos` and `social_protec` have no label and no coding. They are no longer delivered (D111), so their coding is no longer asked. `arm`, the type of disorder: the dictionary should say that it is the type of mood disorder of the DSM-5 inclusion form, else of the DSM-IV one, replaced by the export's own list for 509 patients (read in the export, D119; R6). Three referral variables are listed under "Fin de suivi" |
  | AUTO-QUESTIONNAIRES | Codings of STAI-YA, PSQI, MARS and CSM (DM-2). `als55`, `als56`, `als59` carry labels of the long form but are scores of the 18 items: `als55`, labelled "Depression", is the anxiety-depression score (D72); `als56` is depression-elation and `als59` is anger (D67) |
  | NEUROPSYCHOLOGIE | The WAIS-IV digit-span summary columns have the labels of other columns. The CPT-3 names end with an underscore that the extraction does not have |
  | SUBSTANCES ET COMORBIDITE | Four anxiety columns have a row with a name only, no label, code, field or visit (rows 25 to 28: `ceoccurtrouble_panique` and three others). `ceoccurtroubpanago` and `ceoccurtroubpansago` are described as panic disorder with and without agoraphobia but hold "panic and social phobia ticked" and "panic ticked, social phobia not" (D150, R113). The label of `abudep_autre` is that of a duration; it is a yes/no. The eight `SUOCCUR_` rows of the substances say Y/N/U for values that are 0 and 1 (empty for unknown), and `rad_tb_subst_raw` has no row (D155, R119). The substance-induced disorder block of the form is in neither the dictionary nor the extraction (R117) |
  | EVALUATION MEDICALE | `age_ehman`, `age_epman`, `rad_agethym` have no label: age at the first hypomanic episode, at the first manic episode, at the first mood stabiliser (D87). `agedebutpremier_episode` is the age at the first depressive episode on the DSM-5 form (D89). `mhoccur_ehman_ly` carries the label of another variable. `cedecodtrouble_humeur_actuel` is listed twice |
  | SOIN SUIVI HOSP ARRET TRAVAIL | Three follow-up columns of the sick leave have no label |
  | TRAITEMENTS | The first question of the lifetime non-drug form carries the wording of the follow-up form ("depuis la dernière visite") in the application itself, and the dictionary copies it (D124). The six `CMOCCUR_*` columns and the boxes of the lifetime non-drug form hold "Oui; Non; Ne sais pas", not Y/N/U, and the 27 `_lt` rows are the patient's lifetime form, not follow-up visits. `CMDOSE` is the strength as text, empty since 2015; `CMDOSTOT` is computed by the export; an end date 0000-00-15 or 0000-00-00 is the box "Traitement en cours". The follow-up form also asks the number of CBT sessions and the start of the psychoeducation groups, which are not exported |
  | SUICIDE | At the follow-up visits ISF01 to ISF09A hold the follow-up form, asked "since the last visit", with its own answers to "when"; the labels give the inclusion wording only. ISF08 and ISF09 hold Oui / Non / Ne sais pas, not Y / N. LTSV09 is Oui / Non. The export's descriptions of CSS0108 to CSS0112 are one row off, and code 3 of CSS0108 is "par semaine" (D125) |
  | PERINATALITE | The sheet has one more column than the others, so every column is one place to the right |
  | SOCIAL | `saltyp`: the form has seven answers and 7 is "other"; the dictionary says 7 = no income and 8 = other. `stprof`: see DM-13 (D94) |
  | ANTECEDENTS | `dyslipid_mhdecod_eq` has `mere_structure` as its coding. The answer for the thyroid disorder is in `dysthyro_mhoccur_tt` |
  | YMRS | The items have no label |
  | Whole dictionary | Three columns of the extraction are in no tab (DEV-14). 2,117 names of the dictionary are not in the extraction |

- [ ] **FU-9. Patients registered in two centres.** (O41, D73, D76)
  - What it means: for these patients the identifier (`usubjid`) and the
    centre (`siteid`) can change at each run. Two extractions cannot be
    joined on `usubjid` for them, and their visits move from one centre to
    another in the comparisons between centres.
  - Can the export always keep the same record (the first registration, or
    the centre of each visit)?
  - `subjid` does not change: it is the same in the two BP files for the 18
    patients who changed `usubjid`, and the package delivers it as
    `fondacode` (D76). Can you confirm that it is the patient code of the
    foundation, and that two extractions can be joined on it?
  - How many patients are registered in two centres? Are the visits made in
    both centres exported under the record that is kept?
  - 19 patients left and, by your count, 18 came back under another
    identifier. What about the last one?
  - Between the two runs of 13 November, one questionnaire of one visit of
    2024 changed (six cells of the PRISE-M). An edit in the EMR in between,
    or two records of the same form?
  - Read on 2026-11-18: a transfer between centres creates a second record
    with the same patient code, and the export keeps one record at random
    (A1). Asked: keep the active record and deliver the number of records
    (R1, decided by the project lead); count the codes with two records
    (M1). The PRISE-M cells changed because a visit holds two rows of the
    form and the export picks one at random (R18: the lowest form id). The
    patient who left: M8.
  - Today: loaded as extracted.

- [ ] **DM-15. CVLT semantic clustering: counts typed in place of the
  index.** (O49, D108, D130) A clustering index has decimals and stays low
  (median 2.3). In 2012 and 2013, 23% of the values are above 4 and 24% are
  whole numbers, against 2% to 7% and 2% to 6% in the other periods; 96% of
  the 2012-2013 visits of one centre hold such a value (median 12, a
  correlation of 0.36 with the total recall), and the habit goes on at a
  lower rate in other years (83 values above 7 outside 2012-2013) and in
  SZ (18). By band of the index, the share of whole numbers is 2% to 3% up
  to 4, 17% to 37% from 4 to 6 and above 50% from 6 on: a number of
  clusters is typed. Which quantity is it, and can the index be rebuilt
  (it needs the words recalled in each category)? Their identifiers can be
  given on request.
  - Today: an index of 8 or more is `out_of_range` (216 BP, 17 SZ values);
    its z-score and band are missing; between 4 and 8 a few counts remain
    that cannot be told from an index (D130).
  - It changes: with the answer, the 233 values come back as indices.

- [ ] **DM-16. CVLT recency: two lines of the norm to confirm with the
  manual, and to correct in the application.** (O50, D109) The raw recency
  is the same at every age, and the patients under 40 have a mean z-score
  of 0.05. As the application computes it, the patients of 40 to 69 are at
  -0.82 and those of 70 and over at -3.71.
  - From 40 to 69 the application has two means for the recency, 0.78
    standard deviation apart: one in the BP form, one in the SZ form. Which
    is the one of the manual (Deweer et al., 2008)?
  - From 70 the age term looks typed with the wrong sign: turned, the mean
    z-score is -0.25.
  - The response bias from 40 years drifts with the age (-0.5 to -1.0, then
    +1.0 from 70) while the raw bias hardly moves: are its coefficients
    those of the manual?
  - Today: the package uses the SZ form's mean from 40 to 69 and turns the
    sign from 70, for both cohorts; the bias is as the application computes
    it. The clinicians still read the application's values.

- [ ] **DM-17. Does the gate correction of the dataflow run on BPALL?**
  (M63, D153; new on 2026-11-19) The dataflow corrects the first question of
  the anxiety section (`rad_tb_anx`) from "Non" to "Oui" when the section
  holds evidence of a yes (`gate_correction_config` of
  `pathologies.yaml`: one of 23 flag columns, the boxes and the past-month
  answers, positive, or one of 11 age columns filled). In the extraction
  the question is still "no" on 14 inclusion visits and 7 yearly visits
  under that same rule (8 and 5 by a flag, 9 and 2 by an age; a box is
  ticked after a "no" on 5 and 1 of them). Does the correction run on
  BPALL, with a narrower rule, or only on another extract? Two of its flag
  columns are the panic type columns that hold social phobia (D150, R113).
  - Today: the answer is delivered as recorded; the boxes under a "no" are
    read as 0 (D50), the five inclusion visits and the one yearly visit
    that have a box after a "no" are kept as written (D153).
  - It changes: with a correction, about 21 gates would become "yes" and
    their details would no longer sit under a "no".

### Priority C

- [ ] **FU-10. The reduced questionnaires dated before 2021 look
  complete.** (D71) A remark more than a question. The visits that are no
  longer delivered do not look like long forms with unanswered items: seven
  of the eight hold the 18 ALS answers, all hold the 25 WURS and the 20 AIM
  answers, and their BIS holds the twelve items of the BIS-12 and none of
  the 22 others. They look like reduced questionnaires typed under an early
  visit date. Can the visit dates of these visits be checked in the EMR?
  Their identifiers can be given on request. If the date is wrong and is
  corrected, the questionnaires come back by themselves.
  - Today: not delivered, flagged `version_unknown`.

### To correct at the source, and smaller questions

- [ ] **DM-4. Norm tables: where does each one come from?** (O12) See
  section 5.
  - The WAIS-III vocabulary table is cited as "Wechsler, 1997" and has not
    been checked against the French manual. The TMT and CVLT tables come
    from a note taken from the application's code, which says they were not
    checked against the publications.
  - The code of the application cites no source for its tables (read in
    November 2026). Questions: which edition and which country for each
    test? Can the manuals or the published tables be consulted to check
    them?

- [ ] **DEV-13. Values that the application or the export writes by
  itself.** Each is already neutralised in the package. The first two rows are
  the application's (D85, D98); the others are written by the export.

  | What is written | Where | Count |
  |---|---|---|
  | `1000-01-01` in a date that was not typed | Medical history (every empty date of a form saved from 2025), relatives' birth and death dates (28,582 cells in the 52 date columns of the extraction; 23,765 first answers flagged in `relatives`), mood forms, death, change of diagnosis, referral. Written by the application since its version of 2024-07-25, in every empty date of a form that is saved (D98, D148) | 23,831 (the figure the test pins) + 28,582 + 1,136 + 488 |
  | `2011-11-11` as the date of the first suicide attempt | Follow-up visits of one centre from 2011 to 2023 (every form it saved until May 2022); written by its copy of the follow-up form, which has no such field today (D85, D125) | 1,142 cells |
  | "Y" or "N" on every row, whatever was answered | `mhoccur_edm_lt`, `mhoccur_ehman_lt`, `mhoccur_epman_lt`, `mhoccur_epmixt_lt` | All rows |
  | 0 or 1 on every row | Five allergic diseases; `<relative>_alcool`, `_cannabis`, `_autre_substance` (the last one is 1 on 2,709 rows where the list does not hold it) | All rows |
  | A copy of another column | `mhoccur_*_psy_spv` (three), `protec`, `visit_neuropsychologie`, `cpt_version` (WAIS labels) | All rows |
  | A default unit label, also where there is no result | Biology; four defaults are wrong: "mg/L" for prolactin, "µUI/L" for TSH, "%" for MCH and MCHC | 796 to 10,809 rows per analyte |
  | 0 when nothing was measured | Heart rate (20), creatinine clearance (246). The perinatal measures of 2009-2010 (57 visits) are zeros saved by the application's forms of those years, which the export passes on (D117) | |
  | The day of birth set to 15 | All patients | 6,476 |
  | The unit chosen on the form is not exported | LDL cholesterol chosen as g/L, labelled mmol/L | 246 results |

  Asked of the export on 2026-11-18 ([EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)): R19 (the empty-date placeholders), R22 (2011-11-11), R71 and R72 (the Y/N and the copies of the mood forms), R81 and R82 (allergic diseases, relatives' substances), R24 and R30 (zeros), R26 and R28 (units), R56 and R63 (copies), R8 (day 15, documented). The 1000-01-01 and 2011-11-11 dates are written by the application (A19, A20).

- [ ] **DEV-14. Stored scores that do not follow their items, and names.**
  The formulas of the application are read (D106): it computes a score on a
  button and not on saving, so a stored score can be older than its items.

  | Finding | Count |
  |---|---|
  | FAST domain scores differ from their items (the total is written again by the export's score step, so it always fits) | 442 cells |
  | CGI efficacy index differs from its two components, by a multiple of 4 | 79 of 9,010 rows |
  | DSM-IV checklist: the symptom counts are not stored | 1,946 visits (depressive), 678 (manic) |
  | WAIS-III vocabulary raw total is the sum of the items minus 3 | 1,207 of 1,210 rows |
  | QTc computed from QT and RR typed on different scales | 164 impossible values |
  | Cholesterol ratio computed from the numbers as typed | 364 visits |
  | Alda criterion A and B score differ from their items | 9 and 11 rows |
  | MAThyS: the decimal point is lost in 52 item cells (55 for 5.5) | 52 cells |
  | PSQI: minutes to fall asleep multiplied by 60, or a bedtime | 277 and 83 values |
  | WAIS-IV digit-span summary columns are shifted against their labels | 4 columns |
  | WAIS-IV vocabulary is stored in columns named `vocab*_wais3` | 2,107 visits |
  | A column name is cut: `connaissance_centre_expert_preci` | |
  | Names that differ from the dictionary: `lost_to_follow_up_chgdiag_stopsuivi`, `date_saise_neuropsychologie`, the CPT-3 columns | |
  | Legacy columns still exported: second ratings `_n1` of MADRS and YMRS | 23 columns |
  | Duplicated visit records | 7 rows |
  | Damaged characters ("d?AOS", "N?gatif") | 13 cells |
  | Read in the code: the medical-history shortcuts "Non pour tous" no longer fill the diseases in eBipolar (the script is switched off; it is active in eSchizo) (D83) | 7 sections |
  | Read in the code: TMT error percentile "<5" for a test with no error, where every limit of the norm equals the number of errors (D98) | 426 visits |
  | Read in the code: CVLT z-score of trials 1 to 5 computed with the coefficients of the age and of the sex exchanged: the patients of 70 and over until the correction of 2024-08-02, and visits of 2013 and 2014. The values stay wrong in the database; the package computes them again (D98, D108) | 232 values |
  | CVLT z-scores computed with no sex, most in 2012 and 2015 (D108) | 105 values of trials 1 to 5, about 50 for five other measures |
  | Read in the code: the ALS-18 form prints "19" for its last question; a WURS form of 28 questions exists beside the one of 25 (D97) | |
  | Two centres still enter the MAThyS in the direction of the old form (DM-12; 215 visits from 2023, measured again on 2026-11-18) | About 215 visits |

  Asked of the export on 2026-11-18 ([EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md)): the names (R57, R62, R97, R98), the WAIS-IV digit span and vocabulary columns (R59 to R61), the WAIS-III vocabulary total (R60), the PSQI minutes (R49), one row per visit and form (R18, R21, R100). The damaged characters come from the transfer of a patient between centres (A2). The `_n1` MADRS and YMRS are, by the forms, the mood rated at the neuropsychological testing when the last rating is more than a week old: kept in the export (R58, M37); D27 is to be read again with the tab NEUROPSYCHOLOGIE.

- [ ] **DM-8. Columns that the dictionary lists and the extraction does not
  hold.** `hooccur_hospitalisation_ly`, `nom_centre_expert`, `armcd`, `ageu`.
  `nom_centre` is in the extraction and empty on every row. The form
  does ask the number of hospitalisations of the past 12 months at inclusion:
  was the column dropped on purpose? The three other names are the export's.
  - Read on 2026-11-18: no model ever produced `hooccur_hospitalisation_ly`;
    `nom_centre` is empty by construction. Asked: R55 and R95 of [EXPORT_REQUESTS.md](../EXPORT_REQUESTS.md).

## 5. Norms: what the data hold and what could be checked

A standard score is only as good as the norm behind it. This table says, for
each test, where the standard scores come from and what is missing to check
them (DM-4). Since D135 (2026-11-18) the standard scores of the TMT, the
WAIS-III and WAIS-IV subtests and indices, the Stroop, the fluency, the spatial
span, the SCIP and the errands are not "stored" any more: they are computed
again from the raw scores with the tables of the application's scripts, and the
column "What was checked" below is what the stored values were found to follow
(the figures of D135 replace the earlier ones). The CPT, the COBRA, the LIS, the
Barona and the fNART are as stored. The tables themselves are the application's
and have not been checked against the manuals.

| Test | Standard scores delivered | Where they come from | What was checked | What is needed |
|---|---|---|---|---|
| WAIS-III vocabulary | Scaled score, z-score | Stored; a table of 12 age bands was received ("Wechsler, 1997") | The stored scaled score against the table: 19 visits differ, 12 of them by an age one year off | The French manual, to check the table |
| WAIS-III digit span, matrices, coding, symbol search | Scaled scores, z-scores | Stored | The z-score is the scaled score brought to mean 0 and SD 1 | The norm tables |
| WAIS-IV digit span, matrices, coding, symbol search, similarities, vocabulary | Scaled scores, z-scores; z-scores of the longest spans | Stored | Same; the span z-scores follow the spans (rank correlation 0.95 to 0.97); 13 digit-span visits have a doubtful raw total | The norm tables, and the norms of the spans |
| TMT, times | z-scores, percentile bands | Stored | Sign brought to one convention on 3,847 values | The published norms (the formula quoted in the note is not the one used) |
| TMT, errors | Percentile bands | Recomputed from four tables by age and education (note from the code) | The stored bands follow three rules over the years; 6 to 8 visits per measure lack the age or the education | A check of the tables against the publication |
| CVLT, eleven measures | Percentile bands | Recomputed from eleven tables by age group (note from the code); for the ages that have a regression, the band of the computed z-score | 0 to 9 visits per measure cannot be read (106 for the semantic clustering, DM-15) | A check against the publication |
| CVLT, serial clustering | Percentile band | Stored | The table cannot be applied exactly (DEV-8) | The exact limits |
| CVLT, twelve measures | z-scores | Computed again from the regressions of the application's script (D108) | The script gives back 95% to 99% of the stored z-scores (91.5% for trials 1 to 5, where 337 stored values follow a wrong formula) | A check of the regressions against the manual; two lines of the recency are corrected on the evidence of the data (DM-16) |
| Stroop | T-scores, z-scores | Stored; T-scores from the manual | z = (T − 50) / 10 in all but a few rows; the stored interference differs from the recomputed one on 29 visits | The norm tables |
| Verbal fluency | z-scores, percentile bands | Stored | Nothing | The norms used |
| Spatial span | Scaled scores, z-scores | Stored; scaled scores from the manual | z = (scaled − 10) / 3; on 41 visits the raw total does not follow its parts, so its scaled score is doubtful | The norm tables |
| CPT-II, CPT-3 | T-scores, percentiles | Printed by the test software | Limits only | Nothing can be recomputed |
| Errands test | Percentiles, z-scores from 2022 | Typed by hand from the norms | Nothing | The norms used |
| SCIP | z-scores | Stored | Nothing | The norms used |
| COBRA | None | | | |

Three things would improve the standard scores more than anything else:

1. the reference of the norms used for each test (edition, country,
   publication);
2. the tables or regressions themselves, kept outside the repository like
   the ones already received;
3. the list of the dates at which the application changed a norm or a
   formula (DEV-6).
