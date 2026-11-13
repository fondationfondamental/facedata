# FACE BP — questions for the EMR developers, the data manager and the principal investigator

Written on 2026-11-13 from the extraction `BPALL_20261030.tsv` (22,070
visits of 6,476 patients) and the dictionary `FACEBP_thesaurus_V4.34.xlsx`.

Every column of the extraction is now read by the `facedata` package. Where
the data were ambiguous, the package took a careful default and wrote it
down. This document lists what only you can settle, so that the defaults can
be replaced by facts.

**How to read it**

- One section per recipient. Inside a section, the questions are sorted by
  priority.
- **A**: the answer changes the values delivered for many patients, or lifts
  a doubt on a whole period. Analyses are at risk today.
- **B**: the answer concerns one instrument or a group of patients.
- **C**: a confirmation or a correction that does not change an analysis.
- "Today" says what the package does while the question is open.
- The reference at the end of a question (O29, D47...) points to the full
  evidence in [PROGRESS.md](PROGRESS.md).

**How to answer.** Quote the number of the question (DEV-3, DM-1, PI-4). A
short answer is enough; "we do not know" is a useful answer too.

**What is not here.** Only counts are given, never a patient. The centres
are not named, because this repository is public: their codes can be given
on request. The schemas are still drafts: a clinician's review of each tab
is a separate task (PI-12).

| Recipient | A | B | C | Questions |
|---|---|---|---|---|
| EMR developers | 6 | 6 | 2 | DEV-1 to DEV-14 |
| Data manager | 3 | 4 | 2 | DM-1 to DM-9 |
| Principal investigator | 5 | 6 | 1 | PI-1 to PI-12 |

## 1. For the EMR developers

What the forms ask, what the application computes, and what the export
writes.

### Priority A

**DEV-1. Medical history from 2022: is there a first question per section
that the export does not hold?** (O37)
- What we see: until 2021 each section (neurological, cardiovascular,
  endocrine, skin, urinary, digestive, other) is answered at about 87% of
  the inclusion visits, mostly with "no". From 2022 a section is answered at
  14% to 39% of the inclusion visits. The number of "yes" per visit does not
  move; the number of "no" falls from about 26 to about 6. The two sections
  that keep being answered are the allergic one, whose first question
  (`somat_all`) is exported, and the gynaecological one.
- Questions: did the form change in 2022 so that a section opens only after
  a "yes" to a first question? Is an empty section a "no", or a section that
  was not asked? Can that first question be exported?
- Today: delivered as recorded. An empty section is missing, not "no".
- Your answer changes: the prevalence of every somatic disease from 2022
  (migraine goes from 20% to 43% of the answers only because the "no" are no
  longer written).

**DEV-2. Yearly forms: about which period do they ask?** (O38, O29, D50)
- What we see: the same columns are filled at inclusion and at the yearly
  visits. For the medical history, 1,520 of the 3,499 "yes" given at
  inclusion and answered again are "no" later (3% for diabetes, up to 60%
  for a drug eruption or a surgery). The project lead confirmed that the comorbidity
  sections ask about the time since the last visit; the medical history is
  not confirmed.
- Questions: for each yearly form (medical history, comorbidities,
  hospitalisations, sick leave, suicidal behaviour), is the question "ever"
  or "since the last visit"? Did the wording change at some date?
- Today: two sets of columns, `_v0` (inclusion) and `_fu` (yearly), never
  merged.
- Your answer changes: whether the two can be combined into a lifetime
  history, and how the `_fu` columns are labelled.

**DEV-3. Suicide questions at follow-up: what changed in early 2022 and in
early 2024?** (O29, D48)
- What we see: 2% to 4% of the follow-up visits report an attempt since the
  last visit from 2012 to 2021, then 16% in 2022 and 9% in 2023, then 2% to
  3% again. The rise starts in the first quarter of 2022 and stops in the
  first quarter of 2024, in five of the eight centres with enough answers.
  On these visits the lifetime number of attempts and the date of the first
  attempt are often typed again.
- Question: did the follow-up form show the lifetime questions for a time,
  or change its wording, when the reduced questionnaires were put in
  service?
- Today: the "yes" answers of the follow-up visits of 2022 and 2023 are kept
  and flagged `period_doubt`.
- Your answer changes: the flag can be narrowed to the visits concerned, or
  removed.

**DEV-4. Three questionnaires lose answers in the export. Can it be
corrected?** (O24, D33)
- Epworth: only the answers equal to 0 are exported (56,135 values, all 0),
  so no score can be computed.
- Fagerström item 3: the answer "any other cigarette" is never exported
  (empty on 2,113 visits where the five other items are filled).
- CSM item 7: one of its five answers is never exported (450 visits).
- Today: the Epworth is not delivered as a score; the two other totals are
  missing on these visits.
- Your answer changes: three scores become usable.

**DEV-5. Reduced questionnaires of 2021-2022: which form was used at each
visit?** (O30, O23, D47)
- What we see: the BIS-12 replaced the BIS-10, the ALS-18 the 54-item ALS
  and the WURS-25 the 61-item WURS, each centre at its own date between
  September 2021 and May 2022. They are stored in the same columns. Only
  the BIS and the ALS can be told apart from the data. For the WURS the form
  is guessed from the ALS and the BIS of the same visit; 49 visits have a
  WURS alone and are not delivered. For the AIM the extraction holds 20
  items in every year, with the same mean score.
- Questions: (1) were the three reduced questionnaires put in service
  together in each centre, and at which date per centre? (2) Was the AIM-40
  replaced by an AIM-20, and when? (3) Can the export hold a column that
  names the form? (4) What is the order of the questions on the ALS-18 and
  the WURS-25?
- Today: one schema per form; one schema `aim` for all visits.
- Your answer changes: the 49 WURS visits, the split of the AIM, and the
  proof that the long and short forms are never mixed.

**DEV-6. Computed scores whose rule changed over the years: is there a list
of the changes with their dates?** (D13, D34, D42, D43)
- TMT error percentiles follow three rules for a patient with no error:
  `>95` until 2015, `>5` to `>25` from 2016 to 2021, and `<5` on 426 visits
  from 2022. `<5` for the best result looks like an error of the 2022
  version.
- MAThyS sub-scores (`mathys29` to `mathys33`) changed formula in 2022:
  plain sums before, reversed items after.
- CVLT: the z-score of trials 1 to 5 is above 5 on 246 visits with ordinary
  raw totals, two thirds of them in 2009, 2013 and 2014; the recency
  z-score is computed from an empty recency on 43 visits (-5.77).
- TMT z-scores changed sign between 2012 and 2014, centre by centre (about
  770 visits use the old sign). You confirmed that this is historical.
- Today: recomputed from the raw values where we have the rule or the table;
  otherwise delivered as stored, with a flag.
- Your answer changes: every stored standard score could be given its
  period of validity instead of being checked one by one.

### Priority B

**DEV-7. BIS: reversed items are scored `6 − value` on a 1 to 4 scale.**
(O1)
- What we see: the stored scores are recovered exactly with `6 − value`. The
  usual rule is `5 − value`. On BIS-12 visits the application still fills
  the BIS-10 subscales, the BIS-10 total and `bis11` from the items that
  happen to exist.
- Question: is `6 − value` intended? Can the BIS-10 scores be left empty on
  BIS-12 visits?
- Today: `5 − value`; the stored scores are compared with a known offset.

**DEV-8. Norms in the application's code.** (O28, O12, D43, D45)
- Questions: (1) the exact limits of the CVLT serial-clustering percentile
  table (`CVLT_PERCENTILE_NORMS`): the note gives whole numbers and the
  index has decimals, so 9% of our bands differ from yours. (2) The CVLT
  regressions that give the z-scores. (3) The tables of the other tests
  (section 4). (4) When several limits of a table fall on the same raw
  score, the application writes the highest percentile for the CVLT (99) and
  the lowest for the TMT (`>10`): is that intended?
- Today: eleven CVLT bands and four TMT error bands are recomputed from the
  note; the serial-clustering band and every z-score are as stored.

**DEV-9. Family history form.** (O39, D58)
- Questions: (1) is `soeur1` the eldest sister, or the first sister with
  something to describe? The disorders are filled for as many relatives as
  the patient counted as affected, but a birth date is also filled for
  sister 1 of 212 of the 1,332 patients with one sister and none affected.
  (2) The numbers of relatives stop at 5: does 5 mean "5 or more"? (3) The
  death of the mother is almost never exported (115 patients, against 4,142
  for the father). (4) From 2022 the birth dates and dates of death of the
  relatives are almost never typed (70% to 9%, and 51% to 1%): was the field
  removed?
- Today: delivered as recorded.

**DEV-10. Columns and codes with no documented meaning.** (O16, O34, O35)
- `formoppos`: 1 for 610 patients, 2 for 3 patients, mostly from 2021. Is it
  an opposition to the use of the data? See DM-3.
- `rad_agethym` (915 ages, from 2020): which age is it? It looks like the
  age at the first mood stabiliser.
- `saltyp` (main source of income): code 8 "other" never appears, and code 7
  "no income" is given to three quarters of the retired. Does 7 hold both?
- `stprof` (work status): code 3 "student" never appears, and 6 "other" is
  given to 23% of the patients, who are young. Are students exported as 6?
- `age_ehman`, `age_epman`, and the three follow-up columns of the sick
  leave (`rad_arret_travail`, `arret_travail_nb`, `arret_travail_duree`)
  have no label.
- `empjob` (class of the current job): two of its nine codes are exported
  (122 of 2,300 employed patients).

**DEV-11. `dsm_criteria`: how does the export decide between DSM-IV and
DSM-5?** (D12)
- What we see: the application stores no DSM version, so the export writes
  this column. It is empty at inclusion for 850 of 6,476 patients; 364 of
  them have follow-up mood evaluations (731 visits) whose version is then
  unknown.
- Today: the version is read once per patient; visits without one are not
  delivered in the mood sections.

**DEV-12. Treatments.** (D56)
- Questions: (1) an empty end date is written `0000-00-00` or, from 2014,
  `0000-00-15`: does it always mean that the treatment is still running?
  (2) The total daily dose is filled for 80% of the medications until 2013
  and 5% from 2018: was the field removed? (3) The current treatments are
  exported as lists in one cell, the same on every row of the patient: can
  the export give one row per medication?
- Today: a medication without an end date counts as still running at every
  later visit.

### Priority C

**DEV-13. Values that the application or the export writes by itself.** A
list to correct at the source; each is already neutralised in the package.

| What is written | Where | Count |
|---|---|---|
| `1000-01-01` in a date that was not typed | Medical history (every date from 2025), relatives' birth and death dates, mood forms, death, change of diagnosis, referral | 21,903 + 22,172 + 1,136 + 488 |
| `2011-11-11` as the date of the first suicide attempt | Visits from 2012 to 2022 | 1,133 cells |
| "Y" or "N" on every row, whatever was answered | `mhoccur_edm_lt`, `mhoccur_ehman_lt`, `mhoccur_epman_lt`, `mhoccur_epmixt_lt` | All rows |
| 0 or 1 on every row | Five allergic diseases; `<relative>_alcool`, `_cannabis`, `_autre_substance` (the last one is 1 on 2,709 rows where the list does not hold it) | All rows |
| A copy of another column | `mhoccur_*_psy_spv` (three), `protec`, `visit_neuropsychologie`, `cpt_version` (WAIS labels) | All rows |
| A default unit label, also where there is no result | Biology; four defaults are wrong: "mg/L" for prolactin, "µUI/L" for TSH, "%" for MCH and MCHC | 796 to 10,809 rows per analyte |
| 0 when nothing was measured | Heart rate (20), creatinine clearance (246), perinatal measures in 2009-2010 (57 visits) | |
| The day of birth set to 15 | All patients | 6,476 |
| The unit chosen on the form is not exported | LDL cholesterol chosen as g/L, labelled mmol/L | 246 results |
| `rad_tb_subst` loses the "unknown" answers | 94 "U" are empty in it | |

**DEV-14. Stored scores that do not follow their items, and names.**

| Finding | Count |
|---|---|
| FAST domain scores differ from their items (the total is always right) | 442 cells |
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
| `als57` holds two different scores depending on the form | All ALS-18 visits |
| A column name is cut: `connaissance_centre_expert_preci` | |
| Names that differ from the dictionary: `lost_to_follow_up_chgdiag_stopsuivi`, `date_saise_neuropsychologie`, the CPT-3 columns | |
| Legacy columns still exported: second ratings `_n1` of MADRS and YMRS | 23 columns |
| Duplicated visit records | 7 rows |
| Damaged characters ("d?AOS", "N?gatif") | 13 cells |

## 2. For the data manager

The dictionary, the units, the values to query with the centres, and the
norm tables.

### Priority A

**DM-1. Lab results typed on another scale under the default unit label.**
(D28, D31, O20)
- What we see: the unit column carries a default label, so the unit must be
  read from the size of the value. About 2,900 results are concerned:
  haematocrit as a fraction (477), MCHC in g/L (550), haemoglobin in g/L
  (473), iron in µg/dL (about 360), total cholesterol in g/L (about 250),
  glucose in g/L (124), free T4 in ng/dL (99), uric acid on three scales
  (about 150), and smaller numbers for phosphate, creatinine, calcium, urea
  and alkaline phosphatase. About 850 white-cell counts are percentages.
- Prolactin is the hard case: no unit was chosen for 72% of the results.
  About 320 are in mUI/L, most from one centre during two periods. **174
  results cannot be given a unit.** Clozapine levels are on at least three
  scales; 31 of 65 cannot be read.
- Questions: can the centres or their laboratories say in which unit they
  reported prolactin, and when? Is there a list of the units used by each
  laboratory?
- Today: the unit is inferred where only one fits (flag `unit_inferred`);
  the 174 prolactin results and the 31 clozapine levels are missing.
- Your answer changes: 205 results recovered, and the inferred units
  confirmed.

**DM-2. The dictionary gives no scoring key.** (D37)
- What we see: no questionnaire has a scoring rule in the dictionary, and
  four codings are not those of the data: STAI-YA items are 1 to 4
  (dictionary: 0 to 3), PSQI items are 0 to 3 (dictionary: 1 to 4), MARS
  items 1 to 10 are 1 = no (dictionary: 1 = yes), CSM items are stored as
  points. The formula of the BIS planning subscale is incomplete (the stored
  score also uses items 14, 18 and 31).
- Question: can you send the scoring rules that the cohort considers
  official (reversed items, subscales, number of items needed), and the
  paper forms of the ALS-18, the WURS-25 and the AIM?
- Today: every formula was rebuilt from the stored totals and checked
  against them.
- Your answer changes: the scores can be reviewed against a reference
  instead of against the application.

**DM-3. `formoppos`: does it record an opposition to the use of the data?**
(O16)
- What we see: 1 for 610 patients, 2 for 3 patients; no label and no coding.
- Question: what do the codes mean? If 2 is an opposition, these 3 patients
  may have to be removed from every extraction.
- Today: delivered with its codes as written.

### Priority B

**DM-4. Norm tables: where does each one come from?** (O12) See section 4.
- The WAIS-III vocabulary table is cited as "Wechsler, 1997" and has not
  been checked against the French manual. The TMT and CVLT tables come from
  a note taken from the application's code, which says they were not checked
  against the publications.
- Questions: which edition and which country for each test? Can the manuals
  or the published tables be consulted to check them?

**DM-5. Values to query with the centres.** Each is already neutralised in
the package (missing with a flag, or repaired with a flag). The centre codes
can be given on request.

| Finding | Count |
|---|---|
| Heights with a lost decimal point (1650 for 165.0); half from one centre, from 2018 | 182 |
| Blood pressure typed in cmHg, in six centres | 34 to 40 values per column |
| ECG intervals typed in milliseconds, more and more often | QT 387 (274 since 2023), RR 106 |
| RR values that look like heart rates | 25 |
| The five kinds of white cells do not add up to the leukocytes | 222 visits |
| Pack-years typed freely: above 200, words, fractions | 29 + 34, and 101 "NA" |
| Numbers of consultations and sick-leave durations typed as words; one duration of 880,410 weeks | 193 cells |
| Birth weights typed as a gestational age, or months instead of weeks | 12 and 14 |
| CPT-II values of 1,000 or more, counts above the number of targets | 57 cells |
| CPT-3 columns that hold a raw value instead of a T-score | About 37 visits |
| Errands test: percentiles typed by hand in many spellings; times as "5'30" | 37 times |
| EGF written as a band ("60-51") | 149 cells |
| Age entered on the neuropsychology form differs from the dates by more than a year | 199 visits |
| The inclusion visit is dated before the screening visit | 26 patients |
| Date the information was collected is impossible (before 2008, or a year below 100) | 26 patients |
| Method of the attempt empty although the lethality is filled | 17 visits |
| The gynaecological section is filled for men | 200 |
| The end-of-follow-up reason exists in two sets of columns with different answers | 2 of 5 patients who have both |

**DM-6. Centres that fill a form differently from the others.** Can each be
asked?
- History sections at inclusion since 2022: two large centres hold almost
  none of the comorbidities, the lifetime mood history and the
  hospitalisations (388 inclusions; they were at about two thirds before).
  Did they stop filling these sections, or are they stored elsewhere? (O40)
- Suicide questions at follow-up in 2022-2023: five centres of eight
  (DEV-3).
- Prolactin in mUI/L: one centre holds 69% of the high results.
- The referral information (`adresseur`) is recorded for 92% of the patients
  included in 2008-2012 and 43% in 2022-2026.
- Among patients with an anxiety disorder, "panic disorder" is ticked for
  about 40% until 2017 and 13% in 2025-2026, while "not otherwise specified"
  doubles: a slow change of habits, with no date.

**DM-7. Corrections to the dictionary.**

| Tab | Correction |
|---|---|
| PATIENT | `formoppos` and `social_protec` have no label and no coding. Three referral variables are listed under "Fin de suivi" |
| AUTO-QUESTIONNAIRES | Codings of STAI-YA, PSQI, MARS and CSM (DM-2). `als55`, `als56`, `als59` carry labels of the long form but are scores of the 18 items |
| NEUROPSYCHOLOGIE | The WAIS-IV digit-span summary columns have the labels of other columns. The CPT-3 names end with an underscore that the extraction does not have |
| SUBSTANCES ET COMORBIDITE | Four anxiety columns are missing (`ceoccurtrouble_panique` and three others). The label of `abudep_autre` is that of a duration; it is a yes/no |
| EVALUATION MEDICALE | `age_ehman`, `age_epman`, `rad_agethym` have no label. `mhoccur_ehman_ly` carries the label of another variable. `cedecodtrouble_humeur_actuel` is listed twice |
| SOIN SUIVI HOSP ARRET TRAVAIL | Three follow-up columns of the sick leave have no label |
| TRAITEMENTS | The first question of the lifetime non-drug form carries the label of the follow-up form |
| PERINATALITE | The sheet has one more column than the others, so every column is one place to the right |
| ANTECEDENTS | `dyslipid_mhdecod_eq` has `mere_structure` as its coding. The answer for the thyroid disorder is in `dysthyro_mhoccur_tt` |
| YMRS | The items have no label |
| Whole dictionary | Three columns of the extraction are in no tab (DEV-14). 2,117 names of the dictionary are not in the extraction |

### Priority C

**DM-8. Columns that the dictionary lists and the extraction does not
hold.** Were they dropped on purpose? `isf08_qsdtc` (date of the most
violent attempt), `hooccur_hospitalisation_ly`, `nom_centre_expert`,
`armcd`, `ageu`. `nom_centre` is in the extraction and empty on every row.

**DM-9. Screening rows.** The extraction holds 3,973 screening rows that
carry almost no measure. Are they needed, and should anything be read from
them?

## 3. For the principal investigator

Choices of method. Each has a default that the package follows today.

### Priority A

**PI-1. Inclusion and yearly answers are delivered separately. Do you
agree?** (D46, D49, D59)
- For suicidal behaviour, comorbidities, hospitalisations, sick leave and
  the medical history, the inclusion visit is about the whole life and the
  yearly visits are (or seem to be) about the time since the last visit.
- Today: two sets of columns, `_v0` or `_lifetime`, and `_fu` or
  `_since_visit`. No "ever, up to this visit" column is built.
- Question: is that what analyses need, or do you want a cumulated lifetime
  column as well? It can only be built once DEV-2 is answered.

**PI-2. Medical history from 2022: how should it be used?** (O37)
- Until DEV-1 is answered, the share of "yes" among the answers from 2022 is
  not a prevalence.
- Question: should the package (a) keep the values as recorded, as today;
  (b) flag every answer from 2022; or (c) read an empty section as "no" from
  2022, if the developers confirm the first question?

**PI-3. Suicide answers of the follow-up visits of 2022 and 2023.** (O29,
D48)
- Today they are kept and flagged. In the five centres concerned, 34% of the
  patients with a lifetime attempt answer "yes, since the last visit" in
  these two years, against 4% before.
- Question: keep them with the flag, or deliver them as missing until DEV-3
  is answered?

**PI-4. Editions and forms are never merged. Which bridges do you want?**
(D9)
- Separate columns today: WAIS-III and WAIS-IV, BIS-10 and BIS-12, ALS-54
  and ALS-18, WURS-61 and WURS-25, DSM-IV and DSM-5 mood sections, CPT-II
  and CPT-3.
- Bridges already delivered: `bis10_sum12` (the 12 items that both BIS
  have), `als54_total18`, `wurs61_sum25`, and the z-scores of the WAIS
  subtests.
- Question: are these bridges acceptable for pooled analyses, and is another
  one needed?

**PI-5. The table of medications needs a clinical review.** (O36, D56)
- `facedata/bp/medications.csv` gives, for 223 names, the molecule, its ATC
  code and one of ten groups. It was written from general knowledge of the
  pharmacopoeia. 229 medications of 159 patients have a name that is not in
  it.
- Questions: who can read it (a pharmacist or a psychiatrist)? In which
  group do the gabapentinoids, clonazepam, amisulpride, sulpiride and
  alimemazine go? Is "no end date means still on the treatment" acceptable?

### Priority B

**PI-6. BIS reversed items: `5 − value` or the application's `6 − value`?**
(O1) Today `5 − value`, so the delivered totals are lower than the stored
ones by a constant.

**PI-7. Lab results below the detection limit.** (O2, O3) Today a "<5" is
delivered as 5 with `_cens` = −1. Would you rather have half the limit? CRP
has 389 results that are exactly 0: real zeros, or below an unknown limit?
They are kept as 0.

**PI-8. Plausible limits and extreme values.** (D52, D54)
- Each measure has hard limits; a value outside is delivered as missing with
  a `danger` flag (4,036 cells carry such a flag, the unreadable ones
  included). Inside the limits, measures are brought back to their 1st and
  99th percentiles (flag `winsorised`). Counts of events and birth measures
  are not, because the rare values are the information.
- Question: do you want to review the list of limits? It can be exported as
  one table.

**PI-9. Family history summaries.** (D58)
- The form's question covers a psychiatric disorder, a substance, a suicide
  attempt or a cardiovascular risk factor. The columns `fdr_` are 1 when a
  first-degree relative has the disorder, 0 when every part of the family is
  answered and nobody has it, and missing otherwise: `fdr_bipolar` is
  missing for 2,118 of the 5,712 patients who have a family answer.
- Question: is this strict rule what you want, or should "nothing reported"
  count as 0?

**PI-10. Standard scores of the neuropsychological tests: stored, or
recomputed with one set of norms?** See section 4. Today a standard score is
recomputed only where a table is available; the others are as the
application stored them, with the norms it used at the time.

**PI-11. `rad_agethym`.** (O34) An age recorded on the DSM-5 inclusion form
from 2020, with no label. It looks like the age at the first mood
stabiliser. Do you know the form?

### Priority C

**PI-12. Review of the schemas.** The 130 schemas are drafts. Each has notes
that state what was asked, how the score is computed and what remains
doubtful. Who can review them, tab by tab, and in which order?

## 4. Norms: what the data hold and what could be checked

A standard score is only as good as the norm behind it. This table says, for
each test, where the standard scores come from and what is missing to check
or recompute them.

| Test | Standard scores delivered | Where they come from | What was checked | What is needed |
|---|---|---|---|---|
| WAIS-III vocabulary | Scaled score, z-score | Stored; a table of 12 age bands was received ("Wechsler, 1997") | The stored scaled score against the table: 19 visits differ, 12 of them by an age one year off | The French manual, to check the table |
| WAIS-III digit span, matrices, coding, symbol search | Scaled scores, z-scores | Stored | The z-score is the scaled score brought to mean 0 and SD 1 | The norm tables |
| WAIS-IV digit span, matrices, coding, symbol search, similarities, vocabulary | Scaled scores, z-scores; z-scores of the longest spans | Stored | Same; the span z-scores follow the spans (rank correlation 0.95 to 0.97); 13 digit-span visits have a doubtful raw total | The norm tables, and the norms of the spans |
| TMT, times | z-scores, percentile bands | Stored | Sign brought to one convention on 3,847 values | The published norms (the formula quoted in the note is not the one used) |
| TMT, errors | Percentile bands | Recomputed from four tables by age and education (note from the code) | The stored bands follow three rules over the years; 6 to 8 visits per measure lack the age or the education | A check of the tables against the publication |
| CVLT, eleven measures | Percentile bands | Recomputed from eleven tables by age group (note from the code) | 1 to 44 visits per measure cannot be read in the table | A check against the publication |
| CVLT, serial clustering | Percentile band | Stored | The table cannot be applied exactly (DEV-8) | The exact limits |
| CVLT, twelve measures | z-scores | Stored | 246 visits have an impossible z-score for trials 1 to 5 | The regressions (DEV-8) |
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
