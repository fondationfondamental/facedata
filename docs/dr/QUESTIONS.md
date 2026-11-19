# FACE DR — questions for the EMR developers, the data managers and the principal investigator

Written on 2026-11-14, from the extraction `DRALL_20261030.tsv` (2,193 rows:
1,559 visits and 634 screening rows of 634 patients) and the dictionary
`FACEDR_thesaurus_V4.16.xlsx`.

Every column of the extraction is now read by the `facedata` package
(`from facedata import dr`), or ignored with a written reason. Where the data
were ambiguous, the package took a careful default and wrote it down. This
document lists what only you can settle, so that the defaults can be replaced
by facts.

**How to read it**

- One section per recipient. Inside a section, the questions are sorted by
  priority.
- **A**: the answer changes the values delivered for many patients, or lifts
  a doubt on a whole period. Analyses are at risk today.
- **B**: the answer concerns one instrument or a group of patients.
- **C**: a confirmation or a correction that does not change an analysis.
- "Today" says what the package does while the question is open.
- The reference at the end of a question (O17, D9...) points to the full
  evidence in [PROGRESS.md](PROGRESS.md).

**How to answer.** Quote the number of the question (DEV-3, DM-1, PI-2). A
short answer is enough; "we do not know" is a useful answer too.

**What is not here.** Only counts are given, never a patient. The centres
are not named, because this repository is public: their codes can be given
on request. The questions already answered for FACE BP and FACE SZ are not
asked again ([BP questions](../bp/QUESTIONS.md), [SZ questions](../sz/QUESTIONS.md)).

**Five questions to send first.** DEV-1 (the medication lists are crossed),
DEV-2 (three scales scored on the wrong coding), DEV-3 (no QIDS total on
most recent visits), DM-1 (a dozen scales half empty since 2018) and PI-1
(were the wrong stored scores used). Each concerns a main variable of the
cohort.

## 1. For the EMR developers and whoever writes the export

### Priority A

**DEV-1. The three medication lists are crossed.** For a patient, the export
writes every product (substance, generic name, strength, unit) next to every
prescription line (form, daily dose, start, end): 2 products and 3 lines
give 6 items, the products in alphabetical blocks and the lines in cycles.
This holds for each of the 480 patients of the current psychotropic list,
the 406 of the past list and the 273 of the somatic list. Which line belongs
to which product is not in the file, and the number of units a day is
computed for every pair. For the 194 patients who have several current
psychotropic products, no dose and no date can be delivered.
*Questions:* can the export write one line per prescription, as for BP and
SZ? The past list holds one product for 404 of 406 patients, and half of the
patients have one molecule in the current list: does the form, or the
export, keep one line only? The class and catalogue-code lists (`cmclas`,
`cmclascd`) do not have the length of the others.
*Today:* one item per product, without dates, for the patients with several
products; every line for the patients with one. (O27, D13)

**DEV-2. Three scales are stored on another coding than in BP, and their
stored scores are computed with the BP formula.**
- CTQ: the seven "good childhood" items (2, 5, 7, 13, 19, 26, 28) are stored
  already reversed. In BP they fall when the abuse items rise (r = -0.30 to
  -0.57); here they rise with them (+0.17 to +0.56), in every period and
  centre. The stored emotional neglect, physical neglect and total reverse
  them a second time: the stored emotional neglect falls when emotional
  abuse rises (r = -0.61; +0.67 in BP).
- BIS-10: the same for the eleven reverse-keyed items and every stored
  score (the stored values hold together better as they are, alpha 0.76,
  than after the reversal of the key, 0.65; BP shows the opposite).
- MARS: 1 is "yes" here and "no" in BP (item 5: 14% of answers 1 against
  96%). The stored total counts poor adherence: its median is 3, against 8
  in BP.
*Question:* can you confirm it on the forms (the points attached to each
answer), and correct the stored scores?
*Today:* the items are read back to the BP coding and the scores are
recomputed (CTQ emotional neglect: mean 13.3, for 12.4 in BP; MARS median
7). The stored scores are reproduced exactly by "as stored" formulas and are
not delivered. (O17, D9)

**DEV-3. QIDS-SR16: no total when one item of each pair is answered.** The
form asks for item 6 or 7 (appetite) and for item 8 or 9 (weight). Since
2022 most patients answer one of each pair (26% of the QIDS visits of 2022,
74% of those of 2026), and the EMR then stores no total: 227 visits.
*Question:* did the form change in 2022? Can the total be computed with one
answer per pair?
*Today:* the total is computed when the twelve other items are filled and
each pair has an answer (1,870 totals; 1,643 stored). The same rule now
applies in BP. (O13, D9)

**DEV-4. Other scores that the EMR computes wrongly.**
- SHAPS: the stored score counts "agree" on items 2, 4, 5, 7 and 9 and
  "disagree" on the nine others, while the fourteen stored items all point
  the same way (943 of 943 visits reproduced). (O18)
- Fagerström: item 3 is exported as the code of the answer (1 or 2) and the
  total adds the code: 2 points too high on 129 of 392 visits. (O15)
- MAThyS: on 68 visits of two centres (2013 to 2018) the stored sub-scores
  add the items with none reversed; the stored total is right. In BP the
  data managers recalculate these sub-scores since 10 November 2026. (O14)
- BFI: on 16 visits (four centres, 2014 to 2018) the stored
  conscientiousness and neuroticism are each other's value. (O19)
- Age: the stored `age` is the age at inclusion for the patients with one
  visit and up to five years more for the others. (O5)
*Today:* each score is recomputed from its items; the stored values that
differ are flagged.

### Priority B

**DEV-5. Boxes that the form sets to 0 as soon as it is opened.** In the
MINI (the boxes "current, past, recurrent" of the depressive episode, the
conclusion on the mood disorders, the 39 substances), in the traumatic
events (the impact of each event), in the medical history (causes of a drug
eruption, causes of a urinary retention, cancers, allergic diseases) and in
the family form (substances and cardiovascular risk factors of the parents and
the grandparents: six rows per patient, on all 577 forms), a column holds 0 on
every row where the form exists, also where the question was not asked. The
children and the siblings of the family form do not have it: their unticked
boxes are empty. For the MINI
this hides the answer: 158 visits meet the criteria of a current depressive
episode with the box "current" at 0.
*Question:* can the export leave these cells empty where the question has
no answer, or can the conclusion be computed from the symptoms?
*Today:* the boxes are delivered and flagged where their question is empty;
counts of symptoms are delivered next to the MINI conclusions. (O24, O20,
O29)

**DEV-6. STAI: three codings of the answers.** The twenty answers are
stored from 0 to 3 (655 visits), from 1 to 4 (184) or from 2 to 5 (100, one
centre), one coding per centre and year. No visit is coded 2 to 5 after 2021, and
every visit of 2025 and 2026 is coded 1 to 4.
*Question:* is there a version of the form per period?
*Today:* the coding is read from the answers of the visit, or of the centre
in the same year, and the items are delivered from 1 to 4. The total does
not depend on the coding. (O16)

**DEV-7. Neuropsychology: labels cut and signs.** The percentile band of the
TMT B minus A time (394 cells) and of the letter fluency (257) is cut after
four characters ("25-5" for "25-50"): more than nine labels in ten until
2019, 6% and 14% in 2025 and 2026. The
z-scores of the TMT errors and of the B minus A time have the opposite sign
of the two time z-scores, in every centre and year.
*Question:* can the export give the whole label? Is the sign intended?
*Today:* a cut label is read as its band; the three z-scores are turned so
that a higher value is a better performance, as in BP. (O23)

**DEV-8. Units and fields of the biology.** Unit lists offer units that no
result can be in ("mmol/L" for vitamin D, folates and cortisol; "ng/L" for
folates); vitamin D "ng/L" (121 results) and vitamin B12 "pg/L" (27) cannot
be read with certainty. The urine fields for psychostimulants and opiates
and "MRI done" hold numbers that are not 0 or 1 on 17 to 22 visits. No box
is ticked for oxcarbazepine although 13 levels exist.
*Today:* the size of the value decides the unit where it is clear; the
other cells are removed and flagged. (O10, O12)

**DEV-9. What does not reach the extraction.** The end of follow-up (six
columns) is empty on every row, while 284 of 634 patients never came back.
One depressive episode per visit is exported, although the form numbers the
episodes. The dates of birth of the relatives are empty. Four columns
(`etat_epi_maj`, `fetat_epi_edm`, `etat_epi_depress`, `etat_sui_nb`) are
copies of other columns at follow-up. The follow-up form of the medical
history (191) has a date for another cardiovascular disease that the inclusion
form lacks, and the extraction has no column for it (about 4 cells; R111).
The text of another autoimmune disease is empty on all 7 yes at inclusion (the
form declares its box digits-only, like a count: is it typed there? A49,
M57). The tables of the children and of the siblings of the family form reach
the extraction as one record per patient and visit (`select distinct on` with
no order, so one affected child and one affected sibling, chosen by chance):
13 patients counted 2 or more affected children and 54 siblings, and 6 and 25
counted a relative and have no row (R110).
*Question:* are these fields filled in the EMR, and can they be exported?
Can the export give every record of the children and of the siblings, as BP
gives five sisters, five brothers, five daughters and five sons?
*Today:* one arbitrary row per group; the per-patient columns of the family
are 1 or missing when a patient counted 2 or more. (O2, O26, O29)

**DEV-10. Date of birth.** The real day is exported for 88 patients of two
centres; for the others the day is the 15th, as in BP and SZ.
*Today:* the day is set to the 15th for every patient. (O3)

### Priority C

**DEV-11. What the dictionary does not give.** Codes exported as numbers
with no list: the purpose of the visit; handedness, the time since the last
rating, the psychotropic treatment and "how long before" in the
neuropsychology form; the two forms of the verbal fluency; the method,
drug, consequences and trigger of the most violent and the most serious
suicide attempt; the closest person; the place of a hospitalisation or
consultation; the settings of ECT and TMS, the expertise of the therapist
and the result of a psychotherapy. The lists of the medical history and the
two lists of the family (the kind of mood disorder and the suicide of a
relative) are not in the dictionary either, but the forms give them (D34,
D37): please add them. The dictionary names the field of the type of diabetes
of the siblings `ATCDFAMCV_FRATRIE_TYPDIAB` and the application
`ATCDFAMCV_ENFANT_TYPDIAB` (form 165 line 133): the export maps it correctly.
Wordings that are missing: the 53 Amiel-Lebigre events and the four codes of their second
column, the 64 Paykel events (the dictionary announces 61), the 17
traumatic events, the items of the SHAPS, the SPIN and the MDQ, the two
columns called bupropion and the two called antipsychotics in the ATHF.
*Today:* the lists that BP has are read in the order of the BP list where
the shares agree (handedness, type of diabetes); every other list is
delivered as `code_N`. (O4, O8, O9, O20, O23, O25, O26, O28, O29)

## 2. For the data managers

### Priority A

**DM-1. A dozen scales are half empty since 2018.** Altman, Rosenberg,
MAThyS, STAI, BIS-10, BFI, CSM, PSQI, Epworth, MARS, PRISE-M, and the
clinician scales BAS, FAST and YMRS, are filled at 83% to 96% of the
inclusion visits until 2017 and at 39% to 52% since 2018; the Paykel list
goes from about 80% to 19% to 34%. The QIDS, the MADRS, the EQ-5D, the MDQ
and the CTQ stay high. For the STAI, 10 of the 12 centres that included
before 2018 were at 80% or more; since 2018, 2 centres of 14 are at 80% or
more and 4 at 10% or less.
*Question:* was a shorter set of questionnaires allowed from 2018, and in
which centres?
*Today:* an empty scale after 2018 is missing data, not "not asked". (O1)

**DM-2. Other forms that thin out.** The neuropsychological assessment (three
inclusions in four until 2020, one in two since) and the MINI (82% to 89%
of the screening visits until 2020, 57% to 66% since); the ISF at inclusion
(92% to 96% until 2017, about half since 2018, while the Columbia scale
stays at 75% to 98%); three tests that stop (memory for designs, Baddeley dual task,
auditory span, between 2018 and 2021); SPIN, DETC-CAGE and PCL-S, filled by
a few percent of the patients since 2024; and the list of current psychotropic
treatments (79% to 94% of the patients included until 2019 have one, 50% to
68% of those included since 2021).
*Question:* which of these are changes of the protocol, and from when? (O22,
O24, O25, O21, O30)

### Priority B

**DM-3. Visits.** One row of 2026 has no visit label. One screening visit
is dated in 2000. 14 screening visits are dated after the inclusion visit.
Eight rows carry the labels of three years, five years and thirty months.
(O6)

**DM-4. Fields filled for part of the patients.** The referrer is filled
for 111 patients, 63 of them included in 2025 and 2026. The history of
hospitalisations at inclusion is on about half of the patients (8% to 83%
by centre). (O4)

**DM-5. Typing.** HbA1c of 20 to 60 on 22 visits (mmol/mol?); 0 typed where
a blood count was not measured (91 cells, one centre); sick leave above 53
weeks in a year on 32 answers; time spent sitting above 24 hours a day on
103 answers (the week?). (O11, O26, O21)

**DM-6. Forms saved blank.** At inclusion 17 to 19 forms of the medical
history hold only the boxes at 0 (the gate of the section and every question
empty), and 19 forms of the family hold nothing but the boxes of the
relatives at 0. Were these forms opened and saved without being filled?
*Today:* delivered as recorded; the boxes are flagged `derived_doubt`, and a
family form that holds only boxes at 0 counts as no answer in the per-patient
columns. (O29)

**DM-7. Cannabis and the DETC-CAGE.** "Consommez-vous du cannabis ?" asks
about the present. It is answered at inclusion (429 of 634 visits), at 2
years (92 of 146) and at 4 years (57 of 69), and at none of the 702 visits
of 6, 12, 18 and 30 months, although the tobacco status of the same nurse's
record is filled on 84% of them. The dictionary lists visit v0 only and the
codes Y, N and U (the data are 1 and 0). The question is empty on 11% to 33%
of the inclusions a year since 2016. The four DETC-CAGE items are shown only
after a yes (21 of the 24 yes, none of the 558 no), but they are also filled
on 79 of the 100 CAGE forms whose opening question is empty (all 2012 to
2016), and they ask "have you ever..." under a question about the present.
*Questions:* is the question asked at those three visits only, and is it
still part of the protocol? Do the forms 103 and 119 (the items with no
opening question) explain the 79 forms? Does a patient who stopped cannabis
skip the CAGE by design?
*Today:* 1 yes, 0 no, an empty answer is missing data; the CAGE items are
delivered as recorded. (O31, D42)

**DM-8. Tobacco of the nurse's record.** Since 2021 the non-smokers are 64%
of the visits against 50% until 2020 (the same at inclusion and at follow-up,
9 of 12 centres up), and the details are given less often: pack-years valid
for 76% of the smokers against 93%, the status filled on 76% of the inclusions
against 90%. One centre holds no tobacco status and no cannabis answer at any
of its 70 visits since 2017. The dictionary lists the four tobacco items for
the inclusion, 6 months and 1 year; they are filled at 18 months, 2 and 4
years too.
*Questions:* is the fall of the smokers real, or is the status answered with
less care as the record is filled less? Is the nurse's record hidden or not
used in that centre? Does the form hold the tobacco items at every visit?
*Today:* delivered as recorded; "non-smoker" is not read as "never smoked", an
empty detail is missing data. (O32, D43)

## 3. For the principal investigator

### Priority A

**PI-1. Were the stored scores of the CTQ, the BIS-10, the MARS and the
SHAPS used in published work on FACE DR?** They are wrong in the extraction
(DEV-2, DEV-4): the CTQ neglect scores and total, every BIS-10 score, the
MARS total (which counts poor adherence) and the SHAPS score. (O17, O18)

**PI-2. Questions asked again at follow-up.** The five ISF questions are asked
again at 2 and 4 years in the same columns. About the whole life, as at
inclusion, or since the last visit? The answers show both: 26 of 44 follow-up
visits of patients with a suicide attempt at inclusion answer "no", and 29 of
91 "yes" are dated "more than a year ago".
*Answered by the forms (2026-11-19, D36):* the nine medical histories use the
inclusion form again (form 191), with no period in the questions and no
"change since the last visit" question: a yearly update, as in BP (D84). The
answers still differ from the inclusion ones (migraine 16 of 25 follow-up
visits answer "no" after a "yes" at inclusion, hypertension 4 of 20, counted
by visit). The family form has no follow-up twin: it is on the inclusion visit
only (577 patients, one also at screening, none at 2 or 4 years).
*Today:* the follow-up answers are delivered in columns of their own. (O25,
O29)

**PI-3. MINI.** It is given again at 2 and 4 years to 89 visits: by
protocol? Antisocial personality disorder is concluded on 6 visits, none of
which has the criteria in its items. Which version of the MINI is the form
(the modules and the suicidality points are those of version 6)? (O24)

### Priority B

**PI-4. Instruments to name.** Is the "SACHS" the Bipolarity Index (Sachs
2004), and does the form let the rater tick several statements of a
dimension (104 of 242 visits hold a value between two points of the scale)?
Is the word-list test of the neuropsychology the RL/RI-16, and the test for
designs the Designs subtest of the WMS-IV? Which letter and category does
each of the two forms of the verbal fluency use? (O7, O23)
*Answered by the eCEDR form (2026-11-19, D32):* the word-list test is the
RL/RI-16 (16 items), the test for designs is the Designs subtest of the WMS-IV
(MEM IV), and the fluency forms are letter P with animals and letter R with
fruits.

**PI-5. Mood history.** The type of the first episode has the answers
"resistant" and "not resistant" next to the kinds of episode (21 visits).
"Délai (semaines)": a delay between what and what? Is a resistance score
computed from the ATHF somewhere? None is in the extraction. (O26, O8)
