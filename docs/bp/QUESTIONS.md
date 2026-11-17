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
on request. The schemas are still drafts: a clinician's review of each tab
is a separate task (PI-12).

| Section | Open | Who closes it |
|---|---|---|
| 1. To read in the application | 1 | The project, in the source code and on the development instance |
| 2. To check on the data or the publication | 0 | The project |
| 3. Choices of method | 3 | The project lead and the principal investigator |
| 4. For the data managers, the centres and the developers | 19 | The data managers; still to send |

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
| DEV-2, what the yearly forms ask | Medical history, family history, comorbidities and psychotic disorder: the inclusion form again, same wording, after "is there a change since the last visit?". Suicide, mood episodes, hospitalisations, care, sick leave: "since the last visit". A `_fu` answer of the first group is a yearly update | D84 |
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

## 1. To read in the application

What the forms ask and what the application computes. Each item is read in
the source code first, then checked on a form of the development instance.

### Priority A

### Priority B

- [ ] **DEV-8. Norms in the application's code.** (O28, O12, D43, D45)
  - Done: (2) the CVLT regressions that give the z-scores are read and
    used (D108).
  - To read: (1) the exact limits of the CVLT serial-clustering percentile
    table: the note gives whole numbers and the index has decimals, so 9% of
    our bands differ from the stored ones. The script holds the limits
    (whole numbers under 40 and from 70, decimals from 40 to 69) and the
    rule it applies between two limits: the band can be rebuilt from it.
    (3) The tables of the other tests (section 5). (4) When several limits
    of a table fall on the same raw score, the application writes the
    highest percentile for the CVLT (99) and the lowest for the TMT
    (`>10`): is that written on purpose?
  - Today: eleven CVLT bands and four TMT error bands are recomputed from
    the note, and the twelve CVLT z-scores from the regressions; the
    serial-clustering band and the z-scores of the other tests are as
    stored.
  - A table found in the code goes to `norms/`, outside the repository. It
    feeds PI-10 and DM-4.

### Priority C

## 2. To check on the data or the publication

Nothing open today. The screening pass of BP that follows this list will add
its findings here.

## 3. Choices of method

For the project lead and the principal investigator. Each has a default
that the package follows today. The three left are pieces of work that are
decided and still to do.

### Priority B

- [ ] **PI-8. Plausible limits and extreme values: a table to read.** (D52,
  D54, D79, D107)
  - Each measure has hard limits; a value outside is delivered as missing
    with a `danger` flag. Inside the limits, measures are brought back to
    their 1st and 99th percentiles (flag `winsorised`); counts of events and
    birth measures are not, and `load(..., winsorise=False)` keeps the
    tails.
  - The table is written: `reports/bp/limits.csv` (outside git), one line
    per variable that has limits: the limits, the values delivered, the
    values outside and three percentiles. 2,663 values are outside, on 191
    variables.
  - To do: read it, and say which limits to change.

- [ ] **PI-10. Standard scores of the neuropsychological tests: stored, or
  recomputed with one set of norms?** See section 5. Today a standard score
  is recomputed only where a table is available; the others are as the
  application stored them, with the norms it used at the time. Done for
  the CVLT on 2026-11-17 (D108): its z-scores are computed again from the
  regressions of the application's script. The other tests (TMT times,
  WAIS, Stroop, fluency, spans): still to choose; their scripts hold norm
  tables too.

### Priority C

- [ ] **PI-12. Review of the schemas.** Done: PATIENT, four schemas reviewed
  and one removed (D111). The 128 others are drafts. Each
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

- [ ] **DM-11. Which answer does the export use to remove the patients who
  object?** (D94, D68; new on 2026-11-17)
  - What we see: you told us that the export removes the patients with
    `formoppos` 3 or 4, "the oppositions". On the form of the application,
    `formoppos` is the kind of non-opposition form that was used: 1 adult
    patient, 2 patient under curatelle, 3 under tutelle, 4 minor. The
    opposition is another question of the same form: "does not object to the
    collection and use of the information" or "objects".
  - Questions: does the export read that second question? Are the patients
    who answered "objects" removed from the extraction? Are the patients
    under tutelle and the minors removed on purpose?
  - Today: every patient of the extraction is loaded.
  - It changes: whether some patients must be removed from every table
    already exported.

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

- [ ] **DM-14. Three answers that the export does not carry.** (D95, D96;
  new on 2026-11-17)
  - The strength of the medications: 2 of the 8,654 medications started from
    2018 have a strength (`med_psy_cmdose`), against 5,374 of the 7,922
    started until 2013. The form still records it, and the units a day are
    exported, so only the strength is missing to compute a daily dose.
  - "More than 5" daughters, sons, sisters or brothers: the form offers it;
    the extraction stops at 5. Is it written 5, or lost?
  - Still wished: one row per medication, in place of lists in one cell
    repeated on every row of the patient.
  - Today: no daily dose from 2018; a count of relatives of 5 is read as 5.

- [ ] **DEV-11. `dsm_criteria`: how does the export decide between DSM-IV
  and DSM-5?** (D12, D15)
  - What we see: the application stores no DSM version, so the export
    writes this column. It is empty at inclusion for 850 of 6,476 patients;
    364 of them have follow-up mood evaluations (731 visits) whose version
    is then unknown.
  - Today: the version is read once per patient, or taken from the year of
    inclusion; visits without one are not delivered in the mood sections.

- [ ] **DM-5. Values to query with the centres.** Each is already
  neutralised in the package (missing with a flag, or repaired with a flag).
  The centre codes can be given on request.

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

- [ ] **DM-6. Centres that fill a form differently from the others.** Can
  each be asked?
  - Whole tabs that four centres no longer hold since 2022 (O40, D110).
    Share of the visits that hold something of the tab, 2016-2021 then from
    2022. Did these centres stop filling these forms, or do their copies of
    the application store them elsewhere?

    | Centre (inclusions from 2022) | At inclusion | At follow-up |
    |---|---|---|
    | A (210) | Medical evaluation 79% then 20%; neuropsychology 59% then 27%; social 62% then 16%; care and hospitalisations 80% then 26%; treatments 50% then 10% | Medical evaluation 73% then 27%; care 73% then 30%; suicide 77% then 32%; treatments 94% then 52% |
    | C (178) | Medical evaluation 79% then 0%; biology 53% then 24%; neuropsychology 61% then 32% | Biology 64% then 30% |
    | H (128) | Biology 85% then 16%, and none of the 71 inclusions from 2024; social 40% then 2%; neuropsychology 95% then 54% | Biology 92% then 6% |
    | B (197) | Neuropsychology 91% then 46% | Medical history 54% then 10% |

    The seven other centres of 40 inclusions or more are stable. Over the
    whole cohort each neuropsychological test is held by 37% to 42% of the
    inclusions since 2022, against 73% to 83% before.
  - Suicide questions at follow-up in 2022-2023: five centres of eight. Each
    centre runs its own copy of the application: which copies showed the
    questions about the whole life at follow-up, and from when to when?
    With the answer, the removal of D88 could be narrowed (O29).
  - Prolactin in mUI/L: one centre holds 69% of the high results.
  - The referral information (`adresseur`) is recorded for 92% of the
    patients included in 2008-2012 and 43% in 2022-2026.
  - Among patients with an anxiety disorder, "panic disorder" is ticked for
    about 40% until 2017 and 13% in 2025-2026, while "not otherwise
    specified" doubles: a slow change of habits, with no date.

- [ ] **DM-7. Corrections to the dictionary.**

  | Tab | Correction |
  |---|---|
  | PATIENT | `formoppos` and `social_protec` have no label and no coding. They are no longer delivered (D111), so their coding is no longer asked. `arm`, the type of disorder: it is the mood-disorder diagnosis of the DSM form, which is filled at every visit; which visit gives the exported value, the inclusion or the last one? (D111) Three referral variables are listed under "Fin de suivi" |
  | AUTO-QUESTIONNAIRES | Codings of STAI-YA, PSQI, MARS and CSM (DM-2). `als55`, `als56`, `als59` carry labels of the long form but are scores of the 18 items: `als55`, labelled "Depression", is the anxiety-depression score (D72); `als56` is depression-elation and `als59` is anger (D67) |
  | NEUROPSYCHOLOGIE | The WAIS-IV digit-span summary columns have the labels of other columns. The CPT-3 names end with an underscore that the extraction does not have |
  | SUBSTANCES ET COMORBIDITE | Four anxiety columns are missing (`ceoccurtrouble_panique` and three others). The label of `abudep_autre` is that of a duration; it is a yes/no |
  | EVALUATION MEDICALE | `age_ehman`, `age_epman`, `rad_agethym` have no label: age at the first hypomanic episode, at the first manic episode, at the first mood stabiliser (D87). `agedebutpremier_episode` is the age at the first depressive episode on the DSM-5 form (D89). `mhoccur_ehman_ly` carries the label of another variable. `cedecodtrouble_humeur_actuel` is listed twice |
  | SOIN SUIVI HOSP ARRET TRAVAIL | Three follow-up columns of the sick leave have no label |
  | TRAITEMENTS | The first question of the lifetime non-drug form carries the label of the follow-up form |
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
  - Today: loaded as extracted.

- [ ] **DM-15. CVLT semantic clustering: another quantity typed in 2012
  and 2013.** (O49, D108) In 2012 and 2013, 23% of the indices are above 4
  and 24% are whole numbers, against 2% to 7% and 2% to 6% in the other
  periods, in eight centres. A clustering index has decimals and stays
  low; these values look like a number of clusters. Which quantity was
  typed, and can the index be rebuilt from it? Their identifiers can be
  given on request.
  - Today: the index is delivered as recorded; its z-score and its band
    are missing on 104 visits (`out_of_range`).

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
  | `1000-01-01` in a date that was not typed | Medical history (every date from 2025), relatives' birth and death dates, mood forms, death, change of diagnosis, referral. Written by the application since its version of 2024-07-25, in every empty date of a form that is saved (D98) | 21,903 + 22,172 + 1,136 + 488 |
  | `2011-11-11` as the date of the first suicide attempt | Follow-up visits from 2012 to 2023; written by the follow-up form, which has no such field today (D85) | 1,142 cells |
  | "Y" or "N" on every row, whatever was answered | `mhoccur_edm_lt`, `mhoccur_ehman_lt`, `mhoccur_epman_lt`, `mhoccur_epmixt_lt` | All rows |
  | 0 or 1 on every row | Five allergic diseases; `<relative>_alcool`, `_cannabis`, `_autre_substance` (the last one is 1 on 2,709 rows where the list does not hold it) | All rows |
  | A copy of another column | `mhoccur_*_psy_spv` (three), `protec`, `visit_neuropsychologie`, `cpt_version` (WAIS labels) | All rows |
  | A default unit label, also where there is no result | Biology; four defaults are wrong: "mg/L" for prolactin, "µUI/L" for TSH, "%" for MCH and MCHC | 796 to 10,809 rows per analyte |
  | 0 when nothing was measured | Heart rate (20), creatinine clearance (246), perinatal measures in 2009-2010 (57 visits) | |
  | The day of birth set to 15 | All patients | 6,476 |
  | The unit chosen on the form is not exported | LDL cholesterol chosen as g/L, labelled mmol/L | 246 results |

- [ ] **DEV-14. Stored scores that do not follow their items, and names.**
  The formulas of the application are read (D106): it computes a score on a
  button and not on saving, so a stored score can be older than its items.

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
  | Two centres still enter the MAThyS in the direction of the old form (DM-12) | About 175 visits |

- [ ] **DM-8. Columns that the dictionary lists and the extraction does not
  hold.** `hooccur_hospitalisation_ly`, `nom_centre_expert`, `armcd`, `ageu`.
  `nom_centre` is in the extraction and empty on every row. The form
  does ask the number of hospitalisations of the past 12 months at inclusion:
  was the column dropped on purpose? The three other names are the export's.

## 5. Norms: what the data hold and what could be checked

A standard score is only as good as the norm behind it. This table says, for
each test, where the standard scores come from and what is missing to check
or recompute them (DEV-8, DM-4, PI-10).

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
