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

**Update of 2026-11-19.** The review of the history tab answered DM-3 (the boxes written
on every row: the application saves 0 for a box that is not ticked) and added DEV-10 to
DEV-12 and DM-8 to DM-14 (PROGRESS.md D31 to D47).

**Update of 2026-11-20.** The review of the medical evaluation (ASP, the comorbidity list, the DSM criteria and the ASDI)
split six schemas into `_v0` and `_fu` (D49), answered the code 3 of `dsmtype` (the MINI, D48) and the numbering of the
support levels (D52), and added DEV-13 and DM-15 to DM-17 (PROGRESS.md D48 to D53). The second part (the intellectual assessment, the Vineland, the suicide and substance
forms) closed O9 as to the wording and the levels of use of the substances (O8 (3); D56, D57), and added DEV-14 and DM-18 to DM-22 (D54 to D60); DM-2 is corrected.

**Update of 2026-11-20 (questionnaires, first part).** The review of the self-report questionnaires and the diagnostic instruments (PROGRESS.md D61 to D66) found where each wrong stored score comes from: the errors of the ADI-R, the ADOS, the SRS of a relative and the MARS are the export's, not the EMR's, so DEV-1 to DEV-3 and DEV-5 are rewritten; it recomputed the STAIC state and the BVAQ, split the ADHD-RS by age, answered parts of O2, O12, O13 and O17, and added DEV-15, DEV-16 and DM-23 to DM-24.

**Update of 2026-11-20 (questionnaires, second part).** The review of the old forms (PROGRESS.md D67 to D75) read the scripts of the PSQI, the CCC-2, the ABC and the AIM, recomputed the CCC-2 composite and the four LSAS sub-scores, renamed the three pilot forms like BP, and added DEV-17, DM-25, DM-26 and PI-5. The definition of done of the 30 schemas of the new forms (D76, D77) found nine steps of the years and centres with no known cause (DM-26).

**Update of 2026-11-20 (small tabs).** The review of the patient, clinical examination and social cognition tabs (PROGRESS.md D78 to D81) answered ASP-3 from the code of the export, the parts of ASP-1 (a) about the screening form (the forms keep the lists in comments), and added DEV-18 and DM-27.

**Update of 2026-11-20 (small tabs, medico-economic forms and definition of done).** The medico-economic forms (PROGRESS.md D82 to D86) split the adult and the child form written in one table (the 0 of the other form's boxes is 'never asked', DM-3), answered O15 (3) and (4), the `jobclas` and `hoocur` parts of O16 (9) and the cause of O17 (4) (two scales of the years of education by centre, M90). The definition of done of the 23 schemas (D87, D88) found the steps of the years and centres of DM-28. All 146 ASP schemas are reviewed.

## To send at once

These three answers change how every table is read. The work has started without them,
on careful defaults.

**ASP-1. What the thesaurus V2.13 leaves open, and where the extraction differs from
it.** The thesaurus names 4,063 of the 4,364 columns (230 more are in a range written
with a typo). (a) Not documented: `arm` and `siteid` (named with no label), `diag1s_1`
(codes 1 to 4, filled when an ASD is evoked at screening), `diag3s_1` and its eleven
boxes (filled when the conclusion is deferred), the kinds 1 to 5 of non-drug care (these three
answered: the forms 241 and 261 keep their lists in comments, D79; `arm` answered by the export, ASP-3), the
code 3 of `dsmtype` (98 visits: answered, the form 202 prints MINI, D48), `ados_tot` and `ados_diag`, the sub-scores
and T-scores of the SRS filled by a relative, the BIS scores. (b) The DSM-5 support
levels are numbered backwards (level 1 "very substantial support") in the dictionary; the boxes written
"level 3: support" are the most ticked (594 and 606 visits, against 127 and 115). Answered for the
form 198 (D52): it prints the levels in the wording, so the wording is right and the dictionary's number is wrong. (c) Twelve yes/no columns (`neuro_*`, `npsy_5`,
`npsy_6`) are written 1 yes, 2 no: the extraction holds 0, 1 and 9, never a 2. (d) The
labels of `brief_cona` and `brief_cone` are exchanged. (e) The CRP is written in mmol/L;
the values are mg/L. (f) The answer 9 of the question 19 of the ADHD-RS is written "child
under 7"; it is on 50 visits, none of a child under 7 (answered: the form prints NA, D63). (g) The SRS is written "screening
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
*Answered on 2026-11-20 by the code of the export (D78).* The export writes into `arm` the conclusion of
the DSM-5 criteria of autism of the inclusion visit (`cridsm26`, `face_asp_1_patients.sql` lines 25 and 122),
equal on 2,318 of 2,318 patients: 1 confirmed, 0 not confirmed. Whether the patients not diagnosed are
meant to stay is PI-2.
*Today:* both groups are delivered, with a `diagnosis` column. (O3, D3, D78)

## 1. For the EMR developers and whoever writes the export

### Priority A: scores that are computed wrongly, by the EMR or by the export

Each was found by recomputing the stored score from its items; the corrected score is
delivered and the stored one is kept as a check. Since 2026-11-20 the scripts of the forms
and the definitions of the export were read for each one (PROGRESS.md D64): the cause is
named in the question.

**DEV-1. ADI-R: the domain totals A and C, the total D and the sub-score B3. The cause of the totals is the export** (`adir.yaml` of the export, lines 150-189; the script of the form, `200_score.js`, is right). The stored total A
adds the items 64 and 65 both, where the algorithm counts one of them by age (951 of
951 visits; it equals the sum of its own four sub-scores on 449 of 1,136 visits only).
The stored total C adds the two items of C3 and of C4 instead of the higher one (1,109
of 1,109). A stored total is up to 2 points (A) or 4 points (C) too high, and the
cut-offs are 10 and 3. The stored B3 leaves out the item 38 from 2016 to 2020 (99 of
the 117 visits where that item counts). The twelve sub-scores are otherwise right. The stored A is above the
published one on 659 of 1,089 visits and C on 424 of 1,109, and 8 of 679 complete visits of verbal subjects cross a cut-off on the stored totals and not on the published ones. The stored D is a partial sum
on 432 of 1,184 visits (a missing item counts 0 in the export; the form leaves D empty unless the five items are present), and 12 visits
of non-verbal subjects hold B2, B3 and the verbal B where the form leaves them empty.
*Questions:* can the formulas of `adir.yaml` be corrected (the items 64 and 65, the higher item of C3 and C4, a strict D), and the stored values recomputed?
Was the conclusion `adi_diag` read from the stored totals?
*Today:* the totals are the sums of the sub-scores, B3 the four-item sum. (D8, O12)

**DEV-2. SRS filled by a relative: no item is reversed. The cause is the export** (`recsoc.yaml`: it expects answers written 0 to 3 and receives 1 to 4, counts a missing answer as 0 and reads T-score tables made for a raw range of 0 to 24); the scripts of the forms compute the published total (`211_score.js`, `212_score.js`, `256_score.js`, `257_score.js`). The stored raw scores are
plain sums of the answers from 1 to 4 (1,722 of 1,722 visits); the publication counts 0
to 3 and reverses seventeen items. A stored total is 20 to 114 points too high (median
158 stored, 96 corrected). The T-scores are read from these sums, and the two total
T-scores are sums of sub-scale T-scores (values from 260 to 522).
*Questions:* can `recsoc.yaml` be corrected? The form is also picked from the age at the date of the form in the application and from the age at the visit here: 7 follow-up visits cross the age of 18.
(Answered on 2026-11-20: the adult self-report words the items 52 and 55 as problems, so its key of fifteen reversed items follows the wording.)
*Today:* the seven raw scores are computed with the published key; no T-score is
delivered. (D8, D64, O12)

**DEV-3. ADOS: a code 3 counted as 3. The cause is the export** (`ados.yaml` lines 100-101 and 123-124 and `easperger_aut_c1ados.sql` lines 248-250 sum the raw codes; the script of the form, `281_score.js`, counts a 3 as 2). The algorithm counts a code 3 as 2. The two
stored sub-scores of the module 4 (communication, social interaction) count it as 3 on
every visit (476 of 477 and 157 of 157 visits with a code 3; 40 and 14 stored values
above the maximum). The stored totals of the visits made with the first edition of the
ADOS count it as 3 too: every such visit of the module 3 (21 of 21), 41 of 80 of the
module 4 until 2017. And the module 4 total holds a 0 on 167 visits of 2013 to 2017
where no item is recorded, 104 of them visits of the module 3.
The zero totals (175, 167 with no item) come from the SQL, which computes the two sub-scores of the module 4 on every first-edition row without testing the module (`c1ados.sql` lines 248-251, `ados.yaml` line 81); the stereotyped-behaviours score of the module 4 holds the item C1 on 80 visits that the application dropped on 2018-12-11. `ados_diag` is the export's flag from the raw sums (6 'yes' that the published sums say no).
*Questions:* can the formulas be corrected? From which date did each centre use the
ADOS-2 (the item it added, B8 or B10, is empty until 2017 to 2019)? Was the
classification read from the stored totals?
*Today:* every score is recomputed with the published rule. (D8, D64, O12)

**DEV-4. PSQI: three components and the total.** The efficiency takes the hours in bed
as the difference between the two clock times without crossing midnight (191 of 192
visits): a night from 23:00 to 07:00 counts sixteen hours. The disturbance component is
3 as soon as one disturbance is reported (158 visits differ from the published rule).
The daytime dysfunction does not follow its two items (98 visits). The stored total has
a median of 9 where the corrected one has 7.
The script of the form shows the mechanism (`249_score.js`): the efficiency takes the absolute difference of the two clock times, and the components 5 and 7 join the
answers as text and compare the string (182 of 183 and 200 of 201 visits reproduced). The script also wants every answer 5b to 5j, so the component 5 is empty on the 17 visits
that have no 5j.
*Questions:* can the three formulas be corrected? The PSQI of BP, SZ and DR does
not have the error: recomputed with the published rules, components 4, 5 and 7 equal
the stored ones there (2 of 16,678 BP visits differ, none in SZ and DR; D22).
*Today:* the three components and the total are recomputed. (D9, D70, O13; A74 of EXPORT_REQUESTS.md)

**DEV-5. CTQ and MARS.** The stored CTQ physical abuse and emotional abuse leave out
an item each (items 12 and 14), and the total with them: **the script of the form** reads two radios, CTQ012 and CTQ014, that
do not exist (`334_score.js` lines 45 and 72). The stored emotional and physical neglect differ from the key on 83 and 26 visits
because the same script counts the answer 1 of a reversed item as 1 (line 15); the rule is found and reproduced on every visit. The MARS
is stored 1 = yes, the other way round from BP, and its stored total counts poor
adherence, as in DR: **the cause is the export** (`mars.yaml` reverses the items 7 and 8 on the DR and ASP columns; the script `332_score.js` is right).
*Questions:* can the script of the CTQ be corrected, and the export given a separate entry for DR and ASP with the items 1 to 6, 9 and 10 reversed?
*Today:* the BP keys are delivered. (D8, D62, D64, O12)

**DEV-5b. Sensory questionnaire (GSQ): the proprioceptive sub-score.** The thesaurus
names the 21 sub-scores: hyper-sensitivity, hypo-sensitivity and their sum, for seven
senses. For six senses the third is the sum of the two others. The proprioceptive one
is not: it counts the item 40, a gustatory item, where the item 41 belongs (447 of 449
complete visits).
The error is in the script of the form, which writes the item 40 for the item 41 in that sum (`338_score.js` line 46).
*Today:* the sub-score is delivered as the sum of its two parts; it differs from the
stored one on 381 of the 440 complete visits. (D14, D64)

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

**DEV-10. The lung history and the allergy.** The list of lung diseases of the history
form offers asthma, COPD, tuberculosis and other; a fifth code, "Allergie", is commented
out in the form and no code 5 is in the data. To 2020, 138 inclusion visits have a lung
yes and no lung list, 110 of them with the allergy question yes; the allergy question
itself holds only a yes or nothing until 2019. Was "Allergie" a lung code before the
allergy question existed, and are these lung yes allergies?
*Today:* delivered as recorded, the notes of the history say it. (D35, O18; A56 and M54 of EXPORT_REQUESTS.md)

**DEV-11. Hospitalisations at the follow-up visits.** The follow-up form writes the dates
of the start and of the end of a stay (DDEBHOSP, DFINHSOP); the export reads the year and
the length of the inclusion form (ANDEBHOSP, DURHOSP), so the year and the length are
blank on 8 of the 9 follow-up records. Can the export read the dates too?
*Today:* the reason alone is delivered at follow-up. (D36, O14; R109 of EXPORT_REQUESTS.md)

**DEV-12. The seizure questions and the shortcut of the history forms.** The forms of the
history (193 at inclusion, 347 at follow-up) write the seizure questions (CRISCONV, CRISAGE,
CRISACT, CRISFREQ) and the shortcut "no for all" (ATCDLTN) in the table `aut_atcdlt`, and the
export reads them in `aut_c1antmed`. The seizure question is answered on 75% to 86% of the
inclusion visits of each year 2012 to 2019, 45% in 2020, 4% in 2021 and on none from 2022.
Can the export read the right table, and the shortcut too?
*Today:* delivered as recorded; empty from 2021, the note says so. (D43, O21; R108 of EXPORT_REQUESTS.md)

**DEV-13. Form fields that the export leaves out.** The ADHD sub-type radio (TBATHT: combined, inattentive, hyperactive)
is in the clean model and not selected: the three old boxes stop in 2021, so 274 visits with ADHD yes from 2021 hold no
sub-type. The shortcut boxes 'Non pour tous les critères' of the DSM-5 criteria and of the ASDI (DSM5N, ASDIN) are not in the
extraction either: 90 inclusion visits have the nine criteria at 0 and a conclusion of 0, and a zero ticked by the shortcut
cannot be told from a typed zero. The DSM-IV criteria of the old form (CRIDSM1 to CRIDSM16, DSM4N) are in the clean model and
not selected. Can the export carry the three?
*Today:* the sub-type is missing, the shortcut zeros are delivered as typed. (D51, D52; R143 of EXPORT_REQUESTS.md)

**DEV-14. The Vineland sum and composite are typed.** The script of the form (`119_score.js`) would write the sums of the raw
scores of the sub-domains into the fields that the form labels standard scores of the domains, and it never runs: the call is
commented out (`eASPERGER.js` line 3951), the global field is commented out of the form (`119.php` line 110) and the script
of the follow-up form (`349_score.js`) does not exist. The domain scores, the sum and the composite are therefore typed: 41 of the
943 stored sums differ from the sum of the three domain scores (7 include the motor domain, 7 have the sum and the composite
swapped, 4 hold a domain below 20). Can the EMR compute the sum and the composite from the domain scores?
*Today:* the stored sum is delivered as typed and checked against the sum of the domains (23 visits flagged). (D54, O31; A67 of EXPORT_REQUESTS.md)

**DEV-15. Defects of the scripts of the forms found by the review of the questionnaires.** (a) The STAIC state total reverses the ten
positive adjectives (items 1, 3, 6, 8, 10, 12, 13, 14, 17, 20) instead of the ten negative ones, and its reversal map sends 1 to 3, 2 to 1 and 3 to 1 (`342_score.js` lines 8-15). (b) The ADOS-2 classification has an operator-precedence
defect (`281_score.js` line 126): a stale or empty class on 28 of 1,349 visits of the module 4 and 2 of 795 of the module 3; the arrays of cut-offs of the module 2 look
transposed (line 305, to verify). (c) The BVAQ script gave the factors inverted (24 minus the right sum) until a date that differs by centre, from 2021 to 2026: 289 of 441 complete visits. (d) The EQ-5D script
needs the visual scale before it writes the index (34 visits with the five answers have none) and the BP and SZ script never tests it (`hetero_eq5d.js` lines 31 and 35, A18).
*Questions:* can the scripts be corrected, and the stored values written again (the ASP form 342, 281, the BVAQ form 336)?
*Today:* the STAIC state and the BVAQ are recomputed; the other values are delivered as stored. (D62, D64)

**DEV-16. What the export does not carry.** (a) The Manual mode of the forms (radio 'Automatique / Manuel', `manuel_score.js`; the flag `score_manuell`, saved by `save_data.php`) is in no export model: the scores typed without their items cannot be told from scores written by the script. (b) The BRIEF
of adults and the DCDQ hold two forms in the same columns (the informant form 264 and the self-report form 344; the parent form 224 and the adult form 223) and no column names the form or the respondent. (c) The
export casts some ages and years with `~ '^[0-9]+$'`, which drops decimals and tokens (the years the BRIEF rater has known the patient, the ages of the tics). (d) The field of the CCC-2 composite is a `char(2)`, so the negative values are not in the extraction (`easperger.sql` line 3377); why the values from -9 to -1, which fit in two characters, are lost too is not established (R153).
*Today:* delivered as extracted, the notes say which form a visit most probably holds. (D64; the requests are numbered in EXPORT_REQUESTS.md)

**DEV-17. Defects of the scripts and of the export in the old forms.** (a) The CCC-2 script scores only below the age of 17 (`214_score.js` line 30) while the children's form is given to patients of 17 to 24 (17 visits with items and no score), and it tests the interests with `!=`, which would drop a scaled score of 0 (line 268; none present). (b) The ABC script counts a blank item as 0 (`255_score.js`): 36 visits with a blank item hold 61 stored scores, 55 equal the blank-as-0 sum and 6 scores of 5 visits another value (an item edited after the score). (c) The AIM script reverses the item 36 where the key says 37 (`230_score.js` line 35; no stored value is affected). (d) The Time box saves 00:00:00 when it is not touched: the CSHQ waking time on 18 of 119 visits and the PSQI rising time on 8 visits (A75; the 24-hour warning of the BP PSQI form is missing here). (e) The export computes the ALS depression with 10 items, without the item 1, where the application counts 11 (`229_score.js` line 170; M25), so the 4 visits of the pilot differ. (f) The HAM-D items 18a to 21 of the form and the five RBS-R factor columns of the script (`215_score.js` lines 183 to 310) are not in the extraction (R153). (g) The options of `TICVIE3` and `TICVIE4` in form 216 are those of the tic-free-period question (A82).
*Questions:* can the scripts be corrected, and the fields exported?
*Today:* the CCC-2 composite and the PSQI components are recomputed, 00:00:00 is read as not recorded, the others are delivered as stored. (D68 to D74; R153, A74, A75, A81, A82)

**DEV-18. The clinical examination and the screening form in the export and the forms.** (a) The box 'ECG done' (`egyn`), which gates the intervals in form 194, and the second cardiologist box (`cardyn`) are in the clean model and not in the extraction (R158). (b) The help text of the RR field says to divide the heart rate by 60, the inverse of the right 60 / rate (`194.php` lines 31-32; A84); in this cohort the typed RR follows 60 / rate. (c) The form checks the six emotion scores of the facial emotion test against 100 but not its total (`TREF01`) nor the faux pas score (`FAUPA01`) (`eASPERGER.js` lines 3024-3090; A94): 6 values in the 700s. (d) The referral fields of the patient form (sector, how the centre was known, who referred the patient and why, the dates of the letter and of the collection) and the end of follow-up (`fin_suivi`, `datedc`, `causdc`) are not exported (R164). (e) The 'other earlier diagnosis' is an 18-box multiple choice and the export keeps the lowest box ticked, labels the box 4 '4', gives the boxes 10 and 12 the same label, and writes the free text when no box is ticked (`easperger_screening.sql` lines 29-50; R165).
*Questions:* can these fields be exported and the check be added?
*Today:* the QTc is computed from the typed QT and RR; the 700s are out of range; the earlier diagnosis is delivered as the lowest box. (D79, D80, D81; R158, R164, R165, A84, A94)

## 2. For the data managers

### Priority A

**DM-1. What the thesaurus does not say, form by form.** The thesaurus gave the wording
of almost every question and list (applied on 2026-11-14). It leaves out: the code 0 of the occupation and
the code 8 of the level of education of the Barona estimate, the code 8 of the vaccine
lines, and the blocks named in ASP-1. Four lists hold other codes than the thesaurus
writes: `jobclas1` and `jobclas2` (0 and 1, for "1 full time, 2 part time"),
`hoocur_arret_travail` (1 and 2, for "1 yes, 0 no"), and the item before the last of
each A-TAC module, which holds a number above 2 (an age?). Which is right? (ASP-1; O16)

**DM-2. Two editions and two forms found in the data.** The ADOS first edition and the
ADOS-2 (the added item is empty on 96 and 254 visits); the BRIEF of children (86 items,
581 visits) and the BRIEF-A (75 items, 591); the CCC-2 and the CC-A in the same seventy
columns; the WISC-IV mostly until 2017 (and on 67 visits from 2018: DM-20) and the WISC-V from 2017. Can each be confirmed, with
its date? The summary sheet of the thesaurus also lists two forms of the SRS filled by
a relative, for a child and for an adult, in the same columns: we tell them apart by
the age at the visit, under 18 or not. Is that how the form is chosen? (D5, D8, D9, D14)

**DM-3. Boxes written on every row.** The trimester boxes, the drug classes of the
pregnancy, the gynaecology boxes and most boxes of the medico-economic form hold a 0
on every visit that has the form: is a 0 "no" or "not answered"? (O14, O15)
*Answered on 2026-11-19 by the code of the application (D33).* A box that is not ticked
is saved 0 on every save (`class.update.php`): the 0 is "not ticked", never an explicit no.
The boxes are delivered as recorded and flagged where the question above them is empty (gynaecology D33, pregnancy D39).
*Medico-economic forms (2026-11-20, D82).* The adult form 350 and the child form 351 write one table and the save writes 0 into the boxes of the form not shown (14,471 and 4,039 cells, never a 1): those zeros are 'never asked' and are delivered missing; the form of a visit is read from the questions only one form asks. The same for the time at school of the 2019 inclusion form.

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

**DM-8. Empty rows in the lists of somatic diseases.** 19 rows of the eight lists have no
code (in six lists), 14 of them with all four fields empty: a record opened and nothing
typed, or a defect of the export? *Today:* delivered as rows with no value. (D35, O19; M59 of EXPORT_REQUESTS.md)

**DM-9. Family history of neurodevelopmental disorders.** (a) Is a summary per patient
wanted (a relative with an ASD, a first-degree relative with one of the nine disorders)?
It cannot be built safely today: 191 of the 562 relatives have no relative code, and the
question "is there a family history?" does not hide the table of the relatives (62 of the
305 visits with a relative with a yes answer it yes, 233 leave it blank). (b) 171 of the
387 relatives with a yes leave other answers blank (the form has radios, not boxes): is
a blank a no or not answered? *Today:* no summary; the blanks stay missing. (D36, O20; A50 of EXPORT_REQUESTS.md)

**DM-10. The ages of the milestones.** The four ages (sitting, walking, first words, first
sentences) hang on no question of the form, and the form prints the normal age: are they meant
to be typed for every child? 532 of the 1,588 inclusion visits with no psychomotor delay hold an
age of sitting, and 709 of the 1,389 with no language delay an age of the first words.
*Today:* delivered as typed. (D43, O22)

**DM-11. An empty radio.** A radio left unticked is saved empty: 23 of the 98 inclusion visits
with an infection of the pregnancy at yes and 27 of the 196 with a substance at yes have a yes
next to an empty radio. Is an empty radio a no or not answered? (Same question as DM-9 (b).)
*Today:* missing. (D40, O23)

**DM-12. The follow-up form 244.** Its three "change since the last visit" boxes (pregnancy,
first acquisitions, epilepsy) are filled on 147, 111 and 116 follow-up visits, from 2014 to 2020
(2019 for the last two), and the form is out of the menu of the application. When was it
retired? *Today:* delivered as recorded; they gate nothing. (D38, O24)

**DM-13. The folic acid of the pregnancy.** Among the answers yes and no the share of yes is
32% to 36% in 2013 and 2014, 13% to 20% from 2016 to 2020 and 42% to 44% in 2021 and 2022, and
8% to 54% by centre; in one centre it goes from 48% to 3% and then 0%, in another from 33% to
69%, among the children and among the adults. Was the question reworded, or did a centre change
how the answer is entered? *Today:* delivered as recorded and stated in the note; `pregnancy` is
`reviewed` all the same (a documented step with no known cause does not block). (D47, O25)

**DM-14. The allergy question of the history.** Yes for 14% to 16% of the inclusion visits of
2021 to 2023 and 28% to 34% from 2024, in each of the five centres with 20 answers in both
periods, where the other questions change little. Was the allergy question or the way it is
shown changed at the end of 2023? *Today:* delivered as recorded and stated in the note; `somatic_history_v0`
is `reviewed` all the same (a documented step with no known cause does not block). (D47, O26)

**DM-15. The conclusion of the DSM-5 criteria of autism.** `cridsm26` is typed, with no script, and the instruction at the top
of form 198 is the DSM-IV count ('6 items or more'). On the 1,831 inclusion visits with the nine criteria the conclusion differs
from the DSM-5 rule (all three A, at least two of four B, C and D) on 138 (133 yes with the criteria not met, 5 no with all
met). Is it the clinician's diagnosis, and will the instruction be corrected?
*Today:* delivered as typed; the note says so. (D52, O27)

**DM-16. The ASDI: the rule of the box and the answer 'a little'.** The form requires both items of the routines domain (the
published rule in the secondary sources found is at least one of two), and `asdicrit` is typed. Recomputed with the form's own
thresholds the box is reproduced on 199 of the 290 inclusion visits (214 with one item for routines; 161 and 176 counting only
'yes'). On what rule is it ticked, and how does 'a little' count?
*Today:* delivered as typed, no total. (D52, O28)

**DM-17. The comorbidity list at the yearly visits.** The summary form 348 has a change question and the sleep and
self-injury form 203 has one; the learning form 120 has none. An empty yearly section is read as 'no change'. The change box
is yes on 50 visits and all hold the section, no on 162 of which 26 hold it (sleep: yes 34 of 34, no 26 of 150). Is the yearly
list an update filled for what changed?
*Today:* two sets of columns (`_v0`, `_fu`), an empty yearly section stays missing. (D49, O29)

**DM-18. What is `TS`?** The first question of the suicide form is labelled 'Conduites suicidaires' (suicidal behaviour) and its
details are 'age of the first TS', 'number of TS' and 'serious attempt'. Is it a suicide attempt, as the fifth question of the ISF of
the other cohorts, or any suicidal behaviour? The yes rate is 11.5% (15.0% in adults, 5.1% in children) against 38% of the BP
inclusions.
*Today:* delivered as `isf05_lifetime`, the note gives the label of the form. (D56, O30)

**DM-19. The Vineland: typed numbers.** 23 visits have a stored sum that differs from the sum of the domain scores (on 19 the
composite follows the stored sum, so a domain score is probably mistyped), 7 have the sum and the composite swapped (one centre,
2019-2020; 6 of the swapped composites lie inside the range), and 32 sums have no socialisation score. Can the centres check
them (the visit counts can be sent)? And the standard scores of the children fall in 2018-2021 and return from 2022 (socialisation
76, 45, 63) in the two centres that hold them while the raw scores do not move: was the table or the rule of conversion changed?
15% of the socialisation scores are 20, the lowest of the scale: typed as the floor, or in place of a value below 20?
*Today:* delivered as typed; the notes say it. (D54, D60, O31; M72 of EXPORT_REQUESTS.md)

**DM-20. The general ability index and the editions of the Wechsler scales.** The general ability index (`iag`) is one text field
for the three editions (301 of the 675 are children). In one centre (81 values, all children, 75 from 2023) its median is 66, 46
points below the WISC-V full-scale IQ of the same visit (r 0.43; +2 points and r 0.97 in the other centres): a sum of scaled scores?
The WISC-IV box is ticked on 37 visits of patients aged 18 or more at the visit (5 of the 34 with a date were 18 or more at the
assessment), the WISC-V box on 19, the WISC-IV indices exist to 2026 (67 visits from 2018), 10 WAIS-IV assessments are dated under
16 and 5 visits tick two editions: old forms kept, a wrong tick, or the wrong edition for the age?
*Today:* delivered per edition as ticked; the notes say that the indices belong to the date of the assessment. (D55, D60, O32, O33)

**DM-21. The full-scale IQ and `qirea`.** The WISC-IV full-scale IQ is missing on 60% of the visits with the four indices (WAIS-IV 20%,
WISC-V 15%) and the spread of the indices is larger where it is missing, while form 119 says in red to fill it even if the profile is
heterogeneous: is the instruction not followed for this edition? And `qirea` ('IQ already done') left the form around 2021: on 268 visits it
says no and 205 of them hold an index: was it replaced by the boxes of the editions?
*Today:* delivered as typed, never computed. (D55, O34, O35)

**DM-22. The comorbidity list by centre and year.** The share of inclusions that answer the axis I list runs from 14% to 87% among the
five centres with 100 or more inclusions, with clear shifts at three (M71 of EXPORT_REQUESTS.md), and three yes rates step with no setting that
explains it: insomnia (in the centre that answers alone to 2017 the adults fall from 52% to 85% in 2014-2017 to 19% to 45% in 2018-2022), ADHD
in adults (8% to 14% in 2016-2020, 44% in 2026 in the main later centre) and the depressive episode in adults (44% to 67% to 2022, 30% to 40% in
2023-2025). Is the list filled for all the patients, or chosen by the centre and the rater?
*Today:* delivered as recorded; the notes carry the steps and the schemas are `reviewed` all the same (a documented step with no known cause does not block). (D60, O36)

**DM-23. The first edition of the ADOS in the ADOS-2 columns.** The export maps the items of the first edition into the columns of the ADOS-2 (`easperger_aut_c1ados.sql` lines 26-145): 36 item cells of the three modules
lie outside the answer list of the ADOS-2 (the item B5 of the module 3 and the item B6 of the module 4 coded 3), 12 visits hold the items of another module than the one entered, and the column A22 of the staging is mapped to
the items B9a and B9b of the module 2. How were these two items coded in the first edition, and is the A22 mapping a slip?
*Today:* delivered as recorded (the codes 7 and 8 and the answers outside the list are flagged where the range says so). (D64)

**DM-24. The BVAQ and the typed scores.** (a) The form of this cohort is a 20-item, 5-factor questionnaire where the published Bermond-Vorst questionnaire has 40 items: which version and which key was used, and on
which date did each centre correct its script (the stored factors were inverted until 2021 to 2026, by centre)? (b) What rule does the centre that types its scores in the Manual mode apply on paper (the typed means of
the STAIC, the CDI and the EQ differ from those of the computed scores)?
*Today:* (a) the key of the script is delivered and the 20-item form is to verify; (b) the typed scores are kept as stored. (D62, D65, O17)

**DM-25. Old questionnaires: who answers and what the boxes mean.** (a) The items of the CC-A (form 213) are in the first person ("I mix up ...", "people tell me ..."): is it answered by the patient, as the notes now say, and not by a relative? (b) `rep3syma` (0 to 13) is the number of what: the most severe of the 13 boxes of the form 218? (c) On the 8 PSQI visits whose rising time is the 00:00:00 default (a Time box left untouched) the bedtime is 00:00:00 too (41 bedtimes of 00:00:00 in all): is that bedtime the default as well (then 8 cells would become missing), or midnight? (d) What does the rater mean by `tourtt` ('tics and/or Tourette') when `tourdiag` is no (1 answer on 257 visits)? (e) Which form (223, adult retrospective, or 224, child) filled each DCDQ visit, and who answered the adult form (the export holds no form number and no respondent for it; R154)?
*Today:* (a) the schema says the patient answers (to verify); (b) a number; (c) the bedtime as written; (d) as written; (e) one schema, the respondent in the label. (D69, D70, D74, O38)

**DM-26. Steps of the years and centres of the new questionnaires.** Nine steps remain with no known cause (D77): the ADI-R totals fall from a median of 21 (2011 to 2013) to 10 to 12 from 2018 in children and adults alike, while the edition of the interview does not change; the ADOS module 3 of the main centre (total 16 in 2017, 8 in 2018, 13 in 2019); the Short Sensory Profile of 2018 to 2020 in both age groups; the median EQ-5D index of adults (0.80 to 0.91 in 2014 and 2015, 0.62 to 0.70 from 2019); the GAF of adults (52 in 2020 to 2022, 60 from 2024); the SRS of children (78 in 2014, 77 to 93 from 2022); the ASRS and the GSQ of centre D (median total 35 against 40 to 45, 63 against 74 to 81); the PRISE-M (median total 2 in centre B, 13 in C); and the BRIEF, the ADHD-RS and the SRS of children in centre C, which holds the years to 2015 and reads lower than centre A (140 against 160, 19 against 26, 85 against 92). Is each the case mix, the rater, or a change of setting (a form, a script, a way of filling) that the centres know?
*Today:* delivered as recorded; the notes of the schemas carry the steps and the schemas are `reviewed` all the same (a documented step with no known cause does not block). (D77, O37)

**DM-27. The clinical examination and the social cognition tests.** (a) The tobacco dose `sudose_cig` is labelled pack-years: all 11 values above 60 come from one centre (B), whose 20 values have a median of 73 against 3.8 to 10 elsewhere, and 13 of its 16 values with known years of smoking mean more than a pack a day for every year smoked. What did that centre type (M83; O10)? (b) The box `fnmchang` of the follow-up form 245 sits between the Tanner stages and the neurological examination: which block does its 'change since the last visit' cover (M84)? (c) The non-drug care kinds 1 to 5 (CMP, CMPP, day hospital, IME, IMPRO) left the forms: on which date in each centre? The last ticks are on patients first seen in 2018 to 2020. (d) At centre D the facial emotion scores for anger, sadness, disgust and fear are one photo of nine lower than at B and C (adults), with no date and no scoring cause: is the test given or scored differently there?
*Today:* (a) delivered as typed up to 200; (b) the label says the block is not stated; (c) the 0 from 2022 is missing; (d) delivered as recorded, the note documents the step. (D79, D81)

**DM-28. The medico-economic forms and the steps of the small tabs.** (a) The day-hospital and full-time hospital counts are printed 'number of consultations in the last 12 months' and the day-hospital count is bimodal (median 1 in one centre, 10 in another): stays or days (M90)? (b) The years of education (EDULEVEL) are on two scales by centre (median 3 years in one centre, 13.5 to 14 in three others): which rule does each centre follow (M90; O17 (4))? (c) Do the records of the old 'Module social' (forms 263 and 265, commented out, global.php line 185) hold answers (M91)? (d) The distance `pec031` is asked in metres, and 18 of 303 values are under 100: kilometres typed in the box of metres? (e) One visit gives more than 7 days a week in the employment structures. (f) A parent who saw a general practitioner in the last 12 months (form 353) is 61% to 67% in 2021 and 7% to 25% from 2023 in both centres that fill the form, while the psychiatrist and the psychologist do not move: was the question, its default or its display changed in 2022? (g) The support at school of children falls from 43% to 46% (2016 to 2020) to 26% (from 2021) in the two children's centres; the garden of the home in one centre moves from 17% to 56% and back to 22%; centre D gave the information note to 45% to 75% of its patients until 2020; the change boxes of the follow-up forms are yes on 64% to 98% of the visits of one centre and 11% to 45% elsewhere. Is any of these a change of the forms or of the practice? (O39)
*Today:* (a) labelled 'stays or days'; (b) read and not delivered (`education_years_as_stored`); (d) (e) delivered as typed; (f) (g) delivered as recorded, the notes carry the steps and the schemas are `reviewed` (a documented step with no known cause does not block). (D82 to D88)

## 3. For the principal investigator

**PI-1. Were the wrong stored scores used?** The ADI-R totals, the SRS of a relative,
the ADOS module 4 sub-scores, the MARS total (all four written by the export), the PSQI, the CTQ, the STAIC state and the BVAQ factors before 2025 (written by the scripts of the forms)
have been stored with a wrong
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

**PI-5. Published sources and keys of the old forms.** The forms of the old set were identified from their wording, and the published source is not read for several: the criteria of the MCDD, the tic and obsessive-compulsive checklists (Yale-style), the THADA, the DCDQ'07 (sub-scales, age range of 5 to 15 years), the TCI edition with 125 items, the Attachment Style Questionnaire (Feeney and others, 1994, 40 items, or another), the key of the Social Anhedonia Scale (`anh_score` is not the plain sum of its 40 items on any of 4 visits), the grouping of the 24 LSAS situations (12 and 12 on the form and in the French validation; 13 and 11 in some English literature?). The pilot BIS is delivered with the four scores of BP: should ASP deliver the cognitive, behavioural and general scores too (they follow 5 - value, where the BP ones are 1 higher)?
*Today:* the wording of the forms, no source asserted; the LSAS follows the form. (D67, D71, D74, O38)

## Added by the audit of 2026-11-14

Eight questions, in PROGRESS O17: the rule behind the scores typed without their items (one centre per instrument; answered in part on 2026-11-20: they are typed in the Manual mode of the forms, DM-24), the SRS adult key (answered: it follows the wording), the EQ item 57 (answered: a translation effect, the key is kept), the years of education, the relative codes of the family history, the two copies of the WAIS-IV indices, the opening year of the first centre, and the column `cmdosu`.
