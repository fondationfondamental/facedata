# FACE SZ — questions for the EMR developers, the data managers and the principal investigator

Written on 2026-11-13, updated on 2026-11-14 (DEV-14, DEV-15, the answers to
PI-2 and PI-4) and on 2026-11-19 (DEV-2, DEV-9, DEV-10, DEV-13, DEV-14, DEV-15, DEV-16, DM-8, DM-9, O32, O33, O34, O35, O36, O37, O38, O39, O40) and on 2026-11-20 (DEV-1, DEV-5, DEV-13, DEV-17, DM-7, PI-1, O31), from the
extraction `SZALL_20261113.tsv`, replaced on
2026-11-17 by `SZALL_20261117.tsv` (the same 6,616 rows:
4,941 visits and 1,675 screening rows of 2,353 patients) and the dictionary
`FACESZ_thesaurus_V4.20.xlsx`.

Every column of the extraction is now read by the `facedata` package
(`from facedata import sz`), or ignored with a written reason. Where the data
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
- The reference at the end of a question (O20, D12...) points to the full
  evidence in [PROGRESS.md](PROGRESS.md).

**How to answer.** Quote the number of the question (DEV-3, DM-1, PI-2). A
short answer is enough; "we do not know" is a useful answer too.

**What is not here.** Only counts are given, never a patient. The centres
are not named, because this repository is public: their codes can be given
on request. The questions already answered for FACE BP are not asked again;
the BP answers are in [the BP questions](../bp/QUESTIONS.md). Where a BP
answer may not hold for SZ, the question says so.

**Four questions to send first.** DEV-1 (Calgary items 8 and 9), DEV-3 (marital
status and source of income), DEV-4 (occupation of the Barona estimate) and
DEV-5 (scores computed wrongly). Each concerns a main variable of the cohort,
and each looks like an error of the export or of the EMR that a developer can
find quickly. Two others were answered: DM-10 (years of education), by the
extraction of 17 November 2026, and DEV-2 (substance use disorder at
inclusion), by the export model on 19 November 2026.

## 1. For the EMR developers and whoever writes the export

### Priority A

**DEV-1. Calgary depression scale: the export wires the wrong fields into the
last three items.** In the extraction `calgar07` is item 7 (early wakening),
`calgar08` is a copy of item 7 on every row, `calgar09` is item 8 (suicide), and
item 9 (observed depression, the observation of the interviewer) is in no
column. The model reads the early-wakening field twice and the suicide field
once (`eschizo_hetero_calgary.sql`, lines 35 to 43) and does not export the
observed-depression field, which the script of the form adds as item 9
(`hetero_calgary.js`, lines 20 to 22). The stored total `calgar` is the strict
sum of the nine exported columns, so it is the true total minus item 9 plus
item 7. The total of the scale, with its threshold of "above 6", is a main
outcome of the cohort: item 7 is above 0 on one visit in ten.
*Question:* can the export read `radhtml_calgary_suicide` for CALGAR08 and
`radhtml_calgary_depobservee` for CALGAR09, in the WHEN and in the CAST (request
R136)?
*Today:* items 1 to 8 (`calgary08` is the suicide item, read in `calgar09`) and
their sum (`calgary_sum8`); no total of the scale is delivered. (O4, D5, D76)

**DEV-2. Substance use disorder at the inclusion visit: the first question
is built by the export.** `rad_tb_subst` holds "Ne sais pas" on 975 of the
1,583 inclusion visits that answer (45% to 75% in every year), "Non" on 18
and "Oui" on 590. At follow-up "Ne sais pas" is 2%.
*Question:* **answered on 2026-11-19: read in the export model** (D65). The
model (`face_sz_6_substances_comorbidites.sql`) writes "Oui" when one of the
eight boxes is yes, "Non" when the six are no and "Ne sais pas" otherwise.
After a "no" to `rad_add_4` ("more than ten times in your life: illicit
drugs or medicines taken without a prescription") the form shows no drug
question and the export leaves the drug boxes blank, so "all six no" is not
reached: 925 of the 975 visits have that "no". There is no question to send;
the export could read that "no" as "N" and keep the clinician's own answer
(`rad_tb_subst_raw`, request R116).
*Today:* "Ne sais pas" is a missing code, so the first question is missing on
these visits (97% of the 608 valid answers are yes: it does not measure the
disorder). The drug boxes are 0 after the "no" to `rad_add_4` (D63), and the
box of each substance is delivered. (O20 closed, D63, D65)

**DEV-3. Social module: answers that never appear.** `maristat` never holds
code 2 (married or living as a couple): it is 1 on 1,652 visits, 3 or 4 on
72, and empty on 12% to 20% of the visits of every year, among them patients
who live in their own family home and have children. `saltyp` never holds
code 1 (salary) or code 4 (disability pension): most employed patients have
no source of income.
*Question:* does the export lose these three answers? Their labels hold a
slash ("Marié/concubin/Pacsé") or an apostrophe ("Pension d'invalidité"); the
apostrophe was the cause of the losses corrected on 13 November.
*Today:* delivered as extracted; an empty cell is often a lost answer. (O22,
D18)

**DEV-4. Barona estimate: the occupation follows the diploma.** The form
lists seven occupations and seven diplomas. On 1,111 of the 1,546 visits
that have both (72%; 15% would be expected by chance), the occupation holds
the same place in its list as the diploma in its own: 221 of 225 "farmers"
have a CAP or BEP, 218 of 237 "retired" patients a general baccalauréat, in
a cohort whose median age is about 30. Every year, every centre. The expected
IQs are computed with this occupation.
*Question:* does the form fill the occupation from the diploma, or does the
export read the wrong field? Which equation computes the expected IQs?
*Today:* the values are kept and flagged on these visits (the occupation,
three expected IQs, three differences). (O17, D13)

**DEV-5. Scores that are computed wrongly.** Two groups, found by comparing
the stored scores with their items and with the publications.

- PANSS: three of the fifteen five-factor scores sum a wrong item. Wallwork
  positive counts N2 where the paper and the script of the form have G9 (it
  differs on 3,276 of 4,661 visits); Wallwork negative counts N5 for N6 (2,973
  of 4,656); Lançon negative counts N7 for G7 (2,830 of 4,660). The wrong items
  are in the score step of the export (`panss.yaml`, lines 88, 99 and 156; the
  script of the form has the right ones, `hetero_panss.js` lines 70, 74 and
  75), which overwrites the columns (request R137).
- WAIS-IV: the stored working memory index (`imt02_wais4`) always ends in .3
  and the stored full-scale IQ (`ei23_wais4`) in .1. Their percentile ranks,
  and the Barona difference of the same visit, are those of the stored value
  plus 0.7 and plus 2.9. At the centre of the sum of scaled scores, where
  every index is 100, they are 99.3 and 97.1.

*Answered on 2026-11-20 for the PANSS (D77):* both programs compute the factors,
the form on a button with the right items and the score step of the export with
three wrong item references; the stored columns are the export's.
*Question:* can the three item references of the export be corrected, and which
program computes the WAIS-IV indices, the EMR or the export?
*Today:* the package delivers the corrected values (the items of the form for
the PANSS; the stored index plus 0.7 and plus 2.9 for the WAIS-IV) and keeps
the stored ones as checks. (O5, O15, D10, D12, D77)

**DEV-6. CVLT: the z-score of trials 1 to 5 is wrong on 291 visits, from
October 2021 to June 2026.** The median of `cvlt01z_` is about -1.5 in
every year until 2021, then 0.8 in 2022, 4.0 in 2023 and 5.3 in 2024, while
the raw total does not move.
*Answered on 2026-11-17 by the code of the application (D32).* Until a
correction dated 2024-08-02 the script of the SZ form computed this z-score
with the coefficients of the age and of the sex exchanged, for the patients
under 70. Each centre runs its own copy, so the wrong formula was still in
use in June 2026: 291 stored z-scores in eleven centres, each 4 to 9 points
too high. FACE BP has the same defect in 2013 and 2014 and for its patients
of 70 and over, and computes its z-scores again (BP D108).
*Question left:* (1) which centres still run a copy older than the
correction of 2024-08-02? The 13 wrong values of 2026 come from them. (2)
Can the stored values be computed again in the database?
*Today:* the package computes the CVLT z-scores again since the years of
education are exported (D35); the stored ones are only compared with them.

**DEV-14. Medical history: three sections are mostly empty since 2022.**
(Added on 2026-11-14, reworded on 2026-11-19.) Until 2021 each section of
somatic diseases is answered at 81% to 100% of the inclusion visits, mostly
with "no". Since 2022 the digestive section is answered at 42% of them, the
other diseases at 46% and the autoimmune diseases at 32%; the neurological,
cardiovascular, endocrine, skin and allergic sections do not move. The share
of all included patients with a digestive disease is the same before and
after (17%), but among the answered sections it goes from 21% to 40%: the
"no" are no longer written. 283 of the 609 inclusions since 2022 hold none of
the three sections. Between centres, the autoimmune section is answered at 3%
to 83% of the inclusions since 2022. The same happened to every section of
FACE BP in 2022 (DEV-1 of the BP questions).
*Read in the application:* no change of the form in 2022 is known. The script
of the shortcut "Non pour tous" copies the "no" to each disease in four
sections (neurological, cardiovascular, endocrine, skin) and stops at line 29
(the field `rad_urin_non` has no row in the SZ form), so it copies nothing in
these three sections (A31 of the requests).
*Question:* can the script be repaired and the shortcut exported (R78)? Until
then, is an empty section a "no"?
*Today:* delivered as extracted, missing where the section is empty. No
prevalence of these diseases should be computed on the inclusions from 2022.
(O26, D23, D51)

### Priority B

**DEV-7. S-QoL, items 17 and 18.** The answers 1 and 3 are not in the
extraction, in any year: the two items hold only 2, 4 and 5, while item 16 of
the same dimension holds 1 to 5. 1,549 visits have item 16 and no item 17,
and the stored dimension exists on 782 of them: the patients did answer.
*Question:* can the lookup of these two items be corrected, as it was for
the Epworth scale in BP?
*Today:* the items as extracted (missing where the answer was 1 or 3); the
dimension that uses them is delivered as stored. (O8)

**DEV-8. Items that are a copy of another item.** On every WAIS-IV visit,
`mat25_w` and `mat26_w` hold the value of `mat24_w`, and `simil10_w` and
`simil11_w` hold the same value, while the stored totals count the true
items.
*Question:* can the export read the right fields?
*Today:* the copied items are not delivered; the totals are delivered as
stored. (O12, D11, D14)

**DEV-9. Columns filled from another field.** (1) Five columns of the anxiety
section hold other fields of the form than their names say (`eschizo_psy_diag.sql`,
lines 304-352 and 385-390; R114). `ceoccurtroubpansago`, "panic disorder
without agoraphobia", holds `rad_trouble_panique`, the panic disorder with or
without agoraphobia; `ceoccurtoc`, "obsessive-compulsive disorder", holds
`rad_trouble_obsessionnel`, the obsessional disorder (the obsessive-compulsive
disorder is `rad_trouble_compulsif`); `ceoccuranxietegeneral`, "generalised
anxiety", holds `rad_anxieux`, a screening question ("in the last ten months");
`ceoccurtroubanxaffmed`, "anxiety due to a medical condition", holds
`rad_anxieux_generalise_titre`, the generalised anxiety; and
`ceoccurtroubpanago`, "panic disorder with agoraphobia", holds, on all its 634
rows, `rad_peur_agoraphobie`, the screening question on agoraphobic fear. No
answer is lost, but the names mislead anyone who reads the extraction without
the package. (2) The export swaps
the two migraine columns: `eschizo_mh.sql` (lines 79-90) writes
`rad_somatique_migraine` to `migraine_MHDECOD` and `rad_somat_mig_tt` to
`migraine_MHOCCUR`, where the eBipolar script is right. `migraine_mhdecod`
holds the disease of every patient and `migraine_mhoccur` is "treated", filled
only after a yes (the form and the dictionary have the disease in `_mhoccur`).
*Question:* can both be corrected in the export (R114 for the anxiety columns,
R107 for the migraine)?
*Today:* (1) each column is delivered under the name of what it holds (the
panic disorder, the obsessional disorder, the screening question and the
generalised anxiety, the screening question on agoraphobic fear), and the box
named for the panic disorder with agoraphobia is ignored; (2) the two columns
are read the other way round. (O19 answered, O24, D50, D60)

**DEV-10. Values written where nothing was measured, or not for the visit.**
(1) The percentile of part B of the doors test is "<1" on 172 visits where
part B is empty: computed from an empty cell, as if the score were 0 (the
same error as for the CVLT recency in FACE BP). (2) *Answered by the
export model on 2026-11-19 (D72).* The twelve columns "psychotropic
treatments at the time of the visit" (`psychotic`, `psychotic_nb` and the
others) are the same on every row of a patient because the export computes
them from the whole medication list: the six counts are `COUNT(DISTINCT name)`
of the product names, as typed, that match fixed name patterns
(`face_sz_11_traitements.sql`, 29 patterns for the antipsychotics, 25, 13, 4,
10 and 9 for the other classes), and the six yes/no columns are derived from
the counts. The patterns miss 480 of the 10,188 psychotropic rows of the list
(356 patients), and a count is of names, not of molecules or of treatments of
the visit. (3) The lifetime hospitalisation yes/no (`hooccur_hospitalisation_lt`)
is derived by the export from the number of hospitalisations: empty if the
number is empty, "N" if 0, else "Y", so "Ne sais pas" in the number becomes "Y"
on 44 inclusion visits (37 of them give an age at the first hospitalisation).
*Question:* can (1) be left empty, and can (3) leave an unknown number as an
unknown (R73 and R134 of the requests: map "Pas d'hospitalisations" to "N" and
a "Ne sais pas" to empty)?
*Today:* (1) the 172 bands are kept and flagged; (2) the six counts are
delivered once per patient with a label that says what they count, and what a
patient takes at a visit is computed from the dates of the list; (3) the 44
cells are flagged `derived_doubt` and delivered as extracted. (D14, D19, D70,
D72)

**DEV-11. `empjob`, the class of the job.** One code, 5, on 41 rows: the
defect found in FACE BP, where the list of the form is looked up in the
classes of the dictionary.
*Today:* ignored. (O2)

**DEV-12. Columns that are missing from the extraction.** The estimated
full-scale IQ of the WAIS-III (`ei06_wais3`) and `ei08_wais3`, although its
percentile rank and its confidence interval are extracted. The years of
education after 2015: see DM-10, the application has them. The sheet TAP of
the dictionary.
*Question:* can they be added?
*Today:* not delivered. (O14, O11)

**DEV-15. Two values that change at a date.** (Added on 2026-11-14.) (1)
Migraine at inclusion is "yes" for 11.6% of the answers of 2011 to 2017 and
for 4.6% of those of 2018 to 2026 (the step falls between the second half of
2017, 15.5%, and the first half of 2018, 3.8%, at four of the centres), while
head injury, epilepsy and hypertension do not move. (2) The IQ estimated from two subtests of the WAIS-IV is
stored for 41% to 68% of the inclusions of 2019 to 2021 and for 10% to 28%
of those of 2022 to 2026, while the two subtests are still done at about
three inclusions in four.
*Question:* did the migraine question change in 2018 (M55 of the requests)? Is the two-subtest IQ
no longer computed, or no longer exported?
*Today:* both delivered as extracted. (O27, O28, D23)

### Priority C

**DEV-13. The dictionary.** 201 columns of the extraction are not in it. For
most the instrument makes the meaning clear; for these the question itself is
unknown: the "level" columns of the Yale-Brown scale
(`ybobse1`...), and four z-scores of the six elements test (`elem616_`,
`elem620_`, `elem623_`, `elem625_`). Four others were read in the field
tables of the application on 2026-11-19 and 2026-11-20: `rad_ecv_vp5` (the question
"Homicide" of the physical violence: D80), `rad_add_4` (question 4 of the
addiction form, "more than ten times in your life": D63), `rad_add_heroin7a`
(the heroin question 7a, "a symptom of a use disorder over the whole life":
D66; not delivered yet, O21) and the screening questions of the anxiety
section (`rad_attaq_paniq`, `rad_peur_*`, `rad_trouble_compulsif`: D60). Other points: `causedec_stopsuivi`,
named for the cause of death, holds the date of death; "Arme à feu" is
written "Arme ? feu"; the sisters, brothers and children of the family
history hold the same lists of disorders as the parents, not "yes, no,
unknown". (O21, O10, D4, D18, D20, D60, D63, D66, D80)

## 2. For the data managers

### Priority A

**DM-10. Years of education: a field of the application that the export
does not read.** (Added on 2026-11-17, and answered the same day: the extraction
of 17 November 2026 reads it at every assessment, D35.) `cclin08_` holds the years of
education until 2016 only: 569 of the 2,298 visits with a CVLT. In the
application the later visits have them: the WAIS-IV form of the
neuropsychological assessment has the same field (`annees_etudes`), and the
form of the CVLT and of the TMT reads it there to compute its z-scores. The
export reads the field of the older form only.
*Question:* can `cclin08_` be filled from the WAIS-IV form too, at every
visit?
*What it unlocks:* the percentile bands of the TMT errors on about 2,300
visits per band, and the CVLT z-scores computed again as in BP, which
corrects 291 z-scores of trials 1 to 5 (DEV-6).
*Today:* done. The TMT error bands exist on about 3,100 visits and the CVLT
z-scores are computed again. (D35)

**DM-1. `formoppos`: what is code 2?** *(No longer delivered since 2026-11-17, D34: the column is administrative. The answer below stays for the record.)* Filled for 1,099 of the 2,353
patients: code 1 for 1,012 and code 2 for 87, in nine centres and in every
year from 2012. In FACE BP code 2 is given to 3 patients of 619, and you told
us that codes 1 and 2 have no documented definition.
*Question:* what does code 2 mean, and why is it so much more frequent here?
*Today:* delivered with its codes as written. (O1)
**Answered on 2026-11-17, read on the form of the application (D29):** code 1
is the form of an adult patient, code 2 that of a patient under curatelle.
The opposition itself is another question of the form: see DM-11 of the BP
list.

**DM-2. 33 visits labelled WAIS-III that were given the WAIS-IV.** In 2013,
2015 and 2016 (every visit labelled WAIS3 in 2016): their digit-span total
counts the sequencing task, all have cells in the WAIS-IV index columns, none
has the letter-number sequencing.
*Question:* can `wais_version` be corrected for these visits?
*Today:* answered by the project lead (D47): a visit that holds the sequencing
task is read as WAIS-IV whatever its label (`version.override`, flag
`version_overridden`); 33 visits move. (O16)

**DM-3. Work status and source of income, 2015 to 2018.** `stprof` and
`saltyp` are empty on almost every inclusion visit from mid-2015 to 2018
(137 of 148 visits in 2016, 149 of 153 in 2017), and filled before and after,
while the housing and the income level are filled all along.
*Question:* was another form in use, and are the answers in the source
database?
*Today:* missing in that period. (O23)

### Priority B

**DM-4. Vitamin D: which unit?** The dictionary gives none and the unit
column is empty. Most centres have a median of 38 to 65, the size of nmol/L;
one centre has a median of 24 and a third of its results under 30, the size
of ng/mL (1 ng/mL is 2.5 nmol/L).
*Question:* did that centre report in ng/mL, always or for a period?
*Today:* delivered as written, with no unit. (O7)

**DM-5. WURS: which form?** In BP the 61-item questionnaire was replaced by
the 25-item one in 2021, in the same columns. Here 305 visits from 2012 to
2026 hold the 25 items, 127 of them before 2021, and SZ has no other
questionnaire to tell the form from.
*Question:* which form did the SZ centres use, and when did it change?
*Today:* the 25 items and their sum, not called WURS-25 or WURS-61. (O9)

**DM-6. Six films (LIS).** The score is the distance to the ratings of a
reference group; one set of 30 reference ratings gives the stored score on
983 of 1,011 visits. 28 visits of 2022 to 2024 hold a score that their
ratings do not give, and 137 visits with the 30 ratings have no score.
*Question:* which reference ratings does the EMR use? With them the score
could be computed for every visit.
*Today:* recomputed from the 30 ratings with the reference ratings found in the
script of the application (D48): 28 visits differ from the stored score. (O18)

**DM-7. AIMS, items 11 and 12.** *Answered on 2026-11-20 by the field table of
the application and the export model (D78).* Item 11 is "current problems with
teeth or dentures" (`rad_pbactu`) and item 12 "usually wears dentures"
(`rad_portprothese`) in the form and in the export (`eschizo_hetero_aims.sql`,
lines 84 to 91); the dictionary names them in the order of the columns of the
table. The schema had the right order.
*Question left:* correct the dictionary row, and the Barnes global item, which
has six options (0 to 5) where the dictionary says 0 to 4 (request R144).

**DM-8. Medical history at the follow-up visits.** A disease answered yes at
inclusion is most often answered no later (39 of 47 follow-up answers for a
head injury, 43 of 54 for acne).
*Question:* what period does the follow-up form ask about?
**Answered on 2026-11-19: read in the application** (D56, BP D84). The yearly
form is the inclusion form again, with no period in the wording of its
questions, after one more question, "no change since the last visit?", shown
at the yearly visit only and not exported (R78): an empty follow-up section
may mean "no change". A follow-up answer is a yearly update, neither a history
of the whole life nor strictly an answer about the time since the last visit.
*Today:* two columns per question, `_v0` and `_fu`. (D20, D56; BP D84)

### Priority C

**DM-9. The table of medication names.** `facedata/medications.csv` gives the
molecule, the ATC code and a group for 250 names. It was written by hand and
has still to be read by a pharmacist. The ATC code that the EMR gives for
3,322 medications of this extraction agrees with it on 3,314; of the 8
others, 7 are rows of Valdoxan (2011 to 2014) whose product in the EMR list is
a nicotine patch (the product chosen and the name typed disagree; the table
follows the name), and 1 is a gabapentin row with an old code. 149
medications of 11,038 keep an unknown name. (D19, D73; BP O36)

## 3. For the principal investigator

### Priority A

**PI-1. PANSS five-factor scores.** (1) Lançon 1998: the corrected negative
factor (G7 in place of N7) rests on the abstract of the paper and on the
number of items per factor; the five lists of items could not be read in the
paper itself, but the script of the form itself uses G7 as the corrected factor
does (D77). Can the lists be confirmed in the paper? (2) van der Gaag 2006: the
stored scores keep 29 terms of 28 items of the 45 terms of the published
formula, and neither of its two subtractions. Which version is wanted?
*Today:* Wallwork (two factors) and Lançon (one factor) corrected; van der
Gaag as stored, labelled with its items. (O5, D10)

**PI-2. Four corrections that the package makes.** Each rests on the data
and is written in the notes of its schema; each needs your agreement.
**Answered on 2026-11-14: agreed** (D22). The four corrections stay, and
each is listed with its evidence in PROGRESS.md, section "Instrument changes
found in the extraction".

- The three PANSS factor scores (DEV-5).
- The WAIS-IV working memory index and full-scale IQ, plus 0.7 and plus 2.9
  (DEV-5).
- The two migraine columns, read the other way round (DEV-9).
- The laterality quotient, recomputed on the ten activities of the
  Edinburgh inventory: one centre computed it on 12 lines (41 visits).

### Priority B

**PI-3. Joining the two cohorts.** The tables of BP and SZ have a first
column `cohort`, the same columns for the patients and the same names for the
instruments they share, so that they can be stacked. The patient number
(`usubjid`) is given inside a cohort: 824 numbers are used in both for
different patients, and `fondacode` is the code to join on. Two SZ forms
differ from BP under the same instrument name (the anxiety disorders, where
each disorder follows a screening question, and the medical history, which
is shorter); `facedata/sz/differences.yaml` lists every difference.
*Question:* are there instruments whose names should be brought closer, or
kept apart?

**PI-4. A "no" that the form did not ask.** In the anxiety section and in
the drug-use section a question is shown only after a yes. The package
delivers 0 where the form did not show it after a "no" (no anxiety disorder,
so no panic disorder; never used illicit drugs, so never used heroin).
*Question:* is that the reading you want, or should these cells stay
missing?
**Answered on 2026-11-14: agreed** (D22): the 0 is delivered.

**PI-5. The class of the job.** As for BP: the mapping between the list of
the form and the INSEE classes has to be confirmed before `empjob` can be
delivered. (O2)

## Added by the audit of 2026-11-14

**S-QoL index with a missing dimension (O29).** The EMR averages the dimensions it has; 1,194 of 4,227 indices are concerned. Is that the rule to follow, and from how many dimensions?

**Unit of vitamin D by centre (O30).**

**YMRS, three items stored as levels (O31, answered on 2026-11-20).** Items 5
(irritability), 8 (content) and 9 (disruptive and aggressive behaviour) are
stored 0 to 4 where the scale scores them 0, 2, 4, 6 or 8, in every year and
nearly every centre, and the stored total adds them once; item 6 is stored in
points. The form is the one of FACE BP and the script of the form doubles the
four items: the export maps the letters of items 5, 8 and 9 to the levels
(`eschizo_hetero_ymrs.sql`, lines 47 to 86), a slip of the export and not another
form (D75, request R135). The loader reads the levels as points (0, 2, 4, 6, 8)
and delivers the published total, higher than the stored one on 776 of 4,538
visits. *Question left:* when the export is corrected the cells hold the
points, and the package must then stop reading them through the codes.

## Added by the ANTECEDENTS review of 2026-11-19

**Hormonal treatment of the menopause (O32, for the EMR developers).** The
question is "no" on all 39 answers (BP: 98 yes of 783, DR: 36 of 412) and empty
on 13 of the 52 menopause "yes". Does the SZ form show the question, and is
its field (`hormonal_rporres`) written when the menopause is "yes"? (M56 of the
requests.) Today it is delivered as extracted and asked of every woman (D55).

**Parents with a disorder or a risk factor, fewer since 2018 (O33, for the data
managers).** In `family_structure` the share of mothers and of fathers "with a
psychiatric disorder, an abuse of or dependence on a substance, a history of
suicide attempt or a cardiovascular risk factor" falls with the year of
inclusion: mothers 43% of 896 patients included in 2010-2017 and 30% of 1,127
included in 2018-2026 (48% in 2017, 31% in 2018), fathers 43% of 860 and 32% of
1,096. Six of the nine centres with 40 patients in each period fall by 4 to 41
points (one goes from 67% to 26%). The affected sisters and brothers (12% and
14% of the patients) and the psychiatric first-degree columns (`fdr_depression`
33% and 31%, `fdr_bipolar` 7% and 8%) do not move, and FACE BP shows no step.
Did the wording of the question, the form or the way the centres answer it
change around 2018, the date of the migraine step (DEV-15)? Today it is
delivered as extracted (D59).

## Added by the SUBSTANCES ET COMORBIDITE review of 2026-11-19

**Anxiety and eating disorders at the yearly visits (O34, for the EMR
developers).** The yearly comorbidity form (`psy_troubles_comorbides`) asks the
list of the ten anxiety disorders with the past-month question of each, the type
of the panic disorder, and the eating disorder (first question, type, past
month). The export reads only `rad_tb_anx` of it (the model comments out the list
and the panic type, lines 62-63 of `face_sz_6_substances_comorbidites.sql`): 2,588
yearly visits hold no cell of anxiety or eating detail, so there is no eating
disorder at follow-up, and the anxiety is one yes/no question (2,265 answers, 716
yes). Can the export read them (R115)? The BP form has a "no change" gate
(`rad_pas_dechangement`); the SZ form has none: is that on purpose? Today only
the first question is delivered (`anxiety_fu`), as a yearly update (BP D84).

**The screening question of the generalised anxiety says "ten months" (O35, for
the data managers).** The form asks "in the last ten months, have you been
particularly nervous or anxious?" where the other screening questions of the
anxiety section ask "ever". Is "ten months" a typing error (M61 of the
requests)? Today it is delivered as `gad_screening_v0` (353 yes of 634 answers,
at inclusion only), labelled with the form's words (D60).

**The substance module of SZ (O36, for the data managers).** The opening
questions of the addiction form (more than ten times in your life: alcohol,
cannabis, drugs) are answered on 6% of the inclusion and yearly visits of 2012,
17% of 2014, 52% of 2015 and 84% from 2016. Was the module introduced centre by
centre from 2015, as the anxiety tree was? One centre goes from 77% to 31% to
34% of its inclusion visits (2016-18, 2019-21, 2022-26) and from 53% to 23% to
11% at follow-up, another from 79% to 33% of its yearly visits from 2022. Today
it is delivered as extracted: an empty cell is not "no" (D65; compare BP O40).

**Alcohol amounts above 40 glasses a day (O37, for the data managers).** 49
whole-life values (22 from 41 to 60, 22 from 61 to 100, 5 above 100) and 5 of
the last 12 months. Is the unit a glass per day, or per week? Today they are out
of range and delivered as missing (range 0 to 40; D66).

## Added by the CARE AND TREATMENTS review of 2026-11-19

**DEV-16. Columns that the application and the clean models hold and the
export drops (for the EMR developers and whoever writes the export).** (1)
The care-use block of the follow-up form (general practitioner, psychiatrist,
psychologist, nurse interviews, specialists, others, psychiatric and somatic
emergencies without admission, non-psychiatric care, examinations): 36 columns
are read by `eschizo_trt_sem.sql`, none is selected by `face_sz_10` (R124).
(2) The non-drug treatments of the follow-up form: the sessions of the
electroconvulsive therapy, the magnetic stimulation, "other" and the cognitive
remediation, the start and end dates of 12 kinds, the group or individual sets
and the tool of the remediation are in the table and in the clean model, and
`face_sz_11` selects only the `PROCCUR_*` answers (R125). (3) The number of
attempts in the last 12 months of the inclusion form (`histts_nb12mois`) is
staged in `eschizo_suicide.sql` and not selected by `face_sz_5` (R131). (4) The
parent question of the care changes (`rad_tbpsychoan_modpec`, `_med`) has no row
in the field table and is not exported (R132, see O39). (5) The follow-up
number and weeks of psychiatric sick leave are stripped of every non-digit by
`eschizo_trt_sem.sql` (lines 45-55): "2-3" becomes 23, and 5 weeks are above 99
(R128).
*Question:* can they be exported, and is (5) intended?
*Today:* none of them is delivered; the notes of `hospitalisations_12m`,
`non_drug_fu`, `suicide_attempts` and `care_changes` say so. (D70, D73, D69,
D72, D71)

**The 12-month block of the follow-up form (O38, for the data managers).** The
hospitalisations of the follow-up form (hospitalised full time, number, weeks,
reason) are worded "au cours de l'année écoulée" at every visit, but the
answers follow the time since the previous visit: the share of yes is 17% of
1,469 answered visits up to 420 days after the previous one and 23% of 868
later ones, where the somatic sick leave of the same form, worded 12 months, is
7% in both. Is the block meant to cover the time since the last visit, as in
FACE BP? Today it is read as "since the last visit" at follow-up (D70).

**The parent of the care changes (O39, for the data managers).** The question
"change of the non-drug care" (`care_changes`) depends in the field table on
`rad_tbpsychoan_modpec`, which has no row and is not exported (R132). It is
answered on 38% of the visits to 2017 and on 82% to 94% from the second half of
2019, and the share of yes among the answered visits falls from 38% to 14%. Was
the parent question removed in mid-2019, and what does an empty answer before
that mean (M67 of the requests)? Today an empty cell before mid-2019 is "no
change, or not shown" and the section is delivered as a yearly update (D72).

**The history of treatments of the medication lists (O40, for the data managers).**
The medication list of a patient is the whole history typed at the inclusion
visit and added to afterwards. For the patients included from 2018 it holds
fewer past treatments: per patient with a list, the rows started before the
inclusion visit are 5.0 to 5.9 for the inclusions of 2011 to 2017 and 2.5 to
4.0 from 2018, and the rows already ended at the inclusion are 2.6 to 3.5 and
0.4 to 1.4; the share of patients with a list moves little. The six counts of
`medication_classes` fall with the lists (2.8 to 3.5 antipsychotic names per
patient with a list for the inclusions of 2011 to 2017, 1.6 to 2.5 from 2018).
Did the form or the practice stop asking for the history of treatments in
2018? Today the lists are delivered as typed (D74).

## Added by the CLINICAL SCALES review of 2026-11-20

**DEV-17. The clinical scales: what the forms and the export do wrongly (for the
EMR developers and whoever writes the export).** (1) YMRS: the export gives the
letters of items 5, 8 and 9 the levels 0 to 4 where the form, FACE BP and FACE DR
give 0, 2, 4, 6, 8 (R135, D75). (2) Calgary: items 8 and 9 (DEV-1, R136). (3)
SUMD: the script of the form ticks attribution radios for the three general items
(`labelfieldsradhtml_attribu10`, 20, 30) that the form does not have, and stops
with an error before it sets the attribution of a symptom to 0 where its
awareness is 0 or 3: 530 attributions of 1 to 3 remain under such an awareness,
12.1% of the cells concerned on the visits where a general item is 0 or 3
against 0.2% elsewhere (A62, D78). (4) BARS: the first question (doses per day)
has no upper limit where the two others are limited to 0 to 31: 250 values above
20, 193 of them exactly 100 and 146 of those with a percentage of 100, so a
percentage was typed in the dose field; 271 visits have 0 doses (A65, D78). (5)
Scores computed on a button are stale after an edit of an item: the CGI
efficacy index differs from its items on 23 visits, the Barnes sum on 3, the
extrapyramidal mean on 10, always lower than the items for the last two. (6) The
export drops the EGF texts that are not a whole number although the field is
varchar(25) (R138), the done / not-done flags of the CGI-EGF and PSP forms and
the follow-up diagnostic form with its course, violence and substances (R141),
and the dictionary swaps the AIMS items 11 and 12 and gives the Barnes global
item 0 to 4 (R144).
*Question:* can they be corrected, and can the scores be computed when the form
is saved?
*Today:* the package reads the YMRS levels as points, delivers items 1 to 8 of the
Calgary scale, recomputes the CGI index, and keeps the other cells as typed.
(D75, D76, D78, D79)

**Duplicates of the evaluation row (DM-11, for the data managers).** The model of
the evaluation tab (`face_sz_9_evaluation_medicale.sql`, lines 118 to 133) keeps
one row per visit, the one with the most filled fields, and breaks ties
arbitrarily. No visit of the extraction has a duplicate. Does the application
ever hold two rows of a visit in this tab, and what are they (R141, D80)?
