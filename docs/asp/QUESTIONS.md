# FACE ASP — questions for the EMR developers, the data managers and the principal investigator

Written on 2026-11-14 from the extraction `ASPALL_20261030.tsv` (4,500 rows: 2,318
inclusion visits, 1,809 screening visits and 373 follow-up visits of 2,318 patients),
once every one of its 4,364 columns was read. The reference at the end of a question
(O12, D8...) points to the evidence in [PROGRESS.md](PROGRESS.md).

Only counts are given, never a patient. The centres are not named, because this
repository is public: their codes can be given on request. The questions already
answered for the other cohorts are not asked again
([BP](../bp/QUESTIONS.md), [SZ](../sz/QUESTIONS.md), [DR](../dr/QUESTIONS.md)).

**Six questions to send first.** ASP-1 (what the thesaurus leaves open), ASP-2 (the
date of the new forms), ASP-3 (the meaning of `arm`), DEV-1 (the ADI-R totals), DEV-2
(the SRS of a relative) and PI-1 (were the wrong stored scores used). Each concerns a
main variable of the cohort.

**Update of 2026-11-14.** The thesaurus `FACETSASDI_thesaurus_V2.13.xlsx` arrived after
these questions were written, was compared with the schemas and applied to them
(PROGRESS.md D13 and D14). ASP-1, DEV-5b, DM-1 and DM-2 are rewritten for it. The
questions about the scores (DEV) stand: the thesaurus names the scores and gives no rule
to compute them. One wrong score was found through it (DEV-5b).

## To send at once

These three answers change how every table is read. The work has started without them,
on careful defaults.

**ASP-1. What the thesaurus V2.13 leaves open, and where the extraction differs from
it.** The thesaurus names 4,063 of the 4,364 columns (230 more are in a range written
with a typo). (a) Not documented: `arm` and `siteid` (named with no label), `diag1s_1`
(codes 1 to 4, filled when an ASD is evoked at screening), `diag3s_1` and its eleven
boxes (filled when the conclusion is deferred), the kinds 1 to 5 of non-drug care, the
code 3 of `dsmtype` (98 visits: the MINI?), `ados_tot` and `ados_diag`, the sub-scores
and T-scores of the SRS filled by a relative, the BIS scores. (b) The DSM-5 support
levels are numbered backwards (level 1 "very substantial support"); the boxes written
"level 3: support" are the most ticked (594 and 606 visits, against 127 and 115). Is
the wording right and the number wrong? (c) Twelve yes/no columns (`neuro_*`, `npsy_5`,
`npsy_6`) are written 1 yes, 2 no: the extraction holds 0, 1 and 9, never a 2. (d) The
labels of `brief_cona` and `brief_cone` are exchanged. (e) The CRP is written in mmol/L;
the values are mg/L. (f) The answer 9 of the question 19 of the ADHD-RS is written "child
under 7"; it is on 50 visits, none of a child under 7. (g) The SRS is written "screening
only"; the form of a relative is also on 527 inclusion and 121 follow-up visits. (h) Can
the scoring rules be given: reversed items, the key of the BVAQ, of the Par-DD-QoL and of
the EQ-5D index, how a T-score is read?
*Today:* the data decide where they contradict the thesaurus; a list with no wording is
delivered as numbered codes. (O1, O16, D13)

**ASP-2. The date of the new forms.** The questionnaires are in three source tables:
`autoquestionnaires`, `autoquestionnaires_old_part1` and `autoquestionnaires_old_part2`.
The old ones (AQ, empathy and systemizing quotients, LSAS, ABC, RBS-R, the Hamilton
scales, SPQ, PSQI...) are filled until 2013 to 2021 depending on the scale; the new ones
(RAADS, SRS-A, ASRS, BDI, CDI, STAI, BVAQ, CTQ...) start in 2019 to 2021. On which date
did each centre move to the new forms, and which instruments were dropped, kept or
replaced?
*Today:* an old scale after the change and a new one before it count as "not asked"; the
period of use of each scale is read from the data. (O2, D3)

**ASP-3. The meaning of `arm`.** It is 1 for 2,008 patients and 0 for 310. We read 1 as
an autism spectrum diagnosis confirmed at the expert centre and 0 as a patient assessed
and not diagnosed. Is that right, and were the patients not diagnosed meant to be in the
extraction?
*Today:* both groups are delivered, with a `diagnosis` column. (O3, D3)

## 1. For the EMR developers and whoever writes the export

### Priority A: scores that the EMR computes wrongly

Each was found by recomputing the stored score from its items; the corrected score is
delivered and the stored one is kept as a check.

**DEV-1. ADI-R: the domain totals A and C, and the sub-score B3.** The stored total A
adds the items 64 and 65 both, where the algorithm counts one of them by age (951 of
951 visits; it equals the sum of its own four sub-scores on 449 of 1,136 visits only).
The stored total C adds the two items of C3 and of C4 instead of the higher one (1,109
of 1,109). A stored total is up to 2 points (A) or 4 points (C) too high, and the
cut-offs are 10 and 3. The stored B3 leaves out the item 38 from 2016 to 2020 (99 of
the 117 visits where that item counts). The twelve sub-scores are otherwise right.
*Questions:* can the three formulas be corrected, and the stored values recomputed?
Was the conclusion `adi_diag` read from the stored totals?
*Today:* the totals are the sums of the sub-scores, B3 the four-item sum. (D8, O12)

**DEV-2. SRS filled by a relative: no item is reversed.** The stored raw scores are
plain sums of the answers from 1 to 4 (1,722 of 1,722 visits); the publication counts 0
to 3 and reverses seventeen items. A stored total is 20 to 114 points too high (median
158 stored, 96 corrected). The T-scores are read from these sums, and the two total
T-scores are sums of sub-scale T-scores (values from 260 to 522).
*Questions:* can the formula be corrected? Which forms were given (school-age,
adult relative)? Why does the adult self-report reverse fifteen items and not the
items 52 and 55?
*Today:* the seven raw scores are computed with the published key; no T-score is
delivered. (D8, O12)

**DEV-3. ADOS: a code 3 counted as 3.** The algorithm counts a code 3 as 2. The two
stored sub-scores of the module 4 (communication, social interaction) count it as 3 on
every visit (476 of 477 and 157 of 157 visits with a code 3; 40 and 14 stored values
above the maximum). The stored totals of the visits made with the first edition of the
ADOS count it as 3 too: every such visit of the module 3 (21 of 21), 41 of 80 of the
module 4 until 2017. And the module 4 total holds a 0 on 167 visits of 2013 to 2017
where no item is recorded, 104 of them visits of the module 3.
*Questions:* can the formulas be corrected? From which date did each centre use the
ADOS-2 (the item it added, B8 or B10, is empty until 2017 to 2019)? Was the
classification read from the stored totals?
*Today:* every score is recomputed with the published rule. (D8, O12)

**DEV-4. PSQI: three components and the total.** The efficiency takes the hours in bed
as the difference between the two clock times without crossing midnight (191 of 192
visits): a night from 23:00 to 07:00 counts sixteen hours. The disturbance component is
3 as soon as one disturbance is reported (158 visits differ from the published rule).
The daytime dysfunction does not follow its two items (98 visits). The stored total has
a median of 9 where the corrected one has 7.
*Questions:* can the three formulas be corrected? **Does the PSQI of BP, SZ and DR
compute its components the same way?** They are delivered as stored there.
*Today:* the three components and the total are recomputed. (D9, O13)

**DEV-5. CTQ and MARS.** The stored CTQ physical abuse and emotional abuse leave out
an item each (items 12 and 14), and the total with them; the stored emotional and
physical neglect differ from the key on 83 and 26 visits with no rule found. The MARS
is stored 1 = yes, the other way round from BP, and its stored total counts poor
adherence, as in DR.
*Today:* the BP keys are delivered. (D8, O12)

**DEV-5b. Sensory questionnaire (GSQ): the proprioceptive sub-score.** The thesaurus
names the 21 sub-scores: hyper-sensitivity, hypo-sensitivity and their sum, for seven
senses. For six senses the third is the sum of the two others. The proprioceptive one
is not: it counts the item 40, a gustatory item, where the item 41 belongs (447 of 449
complete visits).
*Today:* the sub-score is delivered as the sum of its two parts; it differs from the
stored one on 387 of 603 visits. (D14)

### Priority B: the export

**DEV-6. The accents are written two or three times over.** "dÃ©pression" for
"dépression": 7,444 broken "é" in 117 columns of the ASP file, 835 in SZ and 1,021 in
DR. *Today:* put back by the reader for ASP only. (D10, O14)

**DEV-7. Scores typed without their items.** A third of the RAADS-R sub-scales, a
quarter of the ADI-R sub-scores, of the GSQ and of the BRIEF scales and a fifth of the
ADHD-RS scores have no item. Are they computed on paper and typed? *Today:* kept as
stored where no item is recorded, flagged `score_as_stored`. (D8)

**DEV-8. Columns that are copies or empty.** 42 columns of the questionnaire table
repeat the medical evaluation on every row; 122 columns in all are ignored, each with
its reason (`facedata/asp/ignored.yaml`). The BVAQ scores are not functions of its
twenty exported items: are the items exported in the order of the form? (O12)

**DEV-9. Units.** No unit column for most analytes, and catalogue numbers in the five
that exist; the dose of a treatment has no unit; the amounts of the medico-economic
form have none. 29 vitamin D results cannot be read. (D6, O10, O14, O15)

## 2. For the data managers

### Priority A

**DM-1. What the thesaurus does not say, form by form.** The thesaurus gave the wording
of almost every question and list (applied on 2026-11-14). It leaves out: the code 3 of
the interview used for the DSM summary (98 visits), the code 0 of the occupation and
the code 8 of the level of education of the Barona estimate, the code 8 of the vaccine
lines, and the blocks named in ASP-1. Four lists hold other codes than the thesaurus
writes: `jobclas1` and `jobclas2` (0 and 1, for "1 full time, 2 part time"),
`hoocur_arret_travail` (1 and 2, for "1 yes, 0 no"), and the item before the last of
each A-TAC module, which holds a number above 2 (an age?). Which is right? (ASP-1; O16)

**DM-2. Two editions and two forms found in the data.** The ADOS first edition and the
ADOS-2 (the added item is empty on 96 and 254 visits); the BRIEF of children (86 items,
581 visits) and the BRIEF-A (75 items, 591); the CCC-2 and the CC-A in the same seventy
columns; the WISC-IV until 2016 and the WISC-V from 2017. Can each be confirmed, with
its date? The summary sheet of the thesaurus also lists two forms of the SRS filled by
a relative, for a child and for an adult, in the same columns: we tell them apart by
the age at the visit, under 18 or not. Is that how the form is chosen? (D5, D8, D9, D14)

**DM-3. Boxes written on every row.** The trimester boxes, the drug classes of the
pregnancy, the gynaecology boxes and most boxes of the medico-economic form hold a 0
on every visit that has the form: is a 0 "no" or "not answered"? (O14, O15)

**DM-4. The treatments.** Is the list the treatment on the day of the visit? 259
inclusion visits declare a current treatment and hold no list. 203 names are not in
the table of medications, and 31 names were added to it and are to be checked by
someone who knows the drugs. (D10, O14)

### Priority B

**DM-5. Follow-up.** 8% of the patients have a visit at one year and 2% at three; two
centres have none. Is the follow-up of this cohort meant to be annual? (D1)

**DM-6. Completion by centre.** The ADI-R is recorded for 0% to 92% of the patients by
centre, the ADOS for 19% to 97%, the adult questionnaires of the new set for 0% to 94%. Which
instruments does each centre give? (D8)

**DM-7. Values out of range**, listed with their counts in the progress file: a few
birth weights, fifteen head circumferences at birth, 28 EQ-5D indices above 1, a few
T-scores typed in place of raw scores of the BRIEF. (O12, O14)

## 3. For the principal investigator

**PI-1. Were the wrong stored scores used?** The ADI-R totals, the SRS of a relative,
the ADOS module 4 sub-scores, the PSQI and the CTQ have been stored with a wrong
formula for years. Have they been used in a publication or in a clinical report? The
corrected values are in `data`; the stored ones can be delivered next to them on
request.

**PI-2. Patients not diagnosed.** 310 of the 2,318 patients have no confirmed diagnosis
(`arm` 0). Are they a comparison group, or patients to leave out? (ASP-3)

**PI-3. Children and adults.** 956 patients are under 18 at inclusion. The child and
adult forms of an instrument are delivered as separate instruments (STAIC and STAI,
CDI and BDI-II, BRIEF and BRIEF-A, WISC and WAIS). Is that the wanted reading?

**PI-4. Standard scores.** The Wechsler indices, the Vineland standard scores, the
CCC-2 scaled scores and the ADOS comparison score are delivered as stored: they need
norm tables that the project does not hold. Should the tables be obtained?

## Added by the audit of 2026-11-14

Eight questions, in PROGRESS O17: the rule behind the scores typed without their items (one centre per instrument), the SRS adult key, the EQ item 57, the years of education, the relative codes of the family history, the two copies of the WAIS-IV indices, the opening year of the first centre, and the column `cmdosu`.
