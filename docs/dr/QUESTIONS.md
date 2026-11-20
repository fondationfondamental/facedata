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
most recent visits), DM-1 (a dozen scales half empty since 2018: the simplified
visit explains it, the flag is still missing) and PI-1 (were the wrong stored
scores used). Each concerns a main variable of the
cohort.

## 1. For the EMR developers and whoever writes the export

### Priority A

**DEV-1. The three medication lists are crossed.** For a patient, the export
writes every product (substance, generic name, strength, unit) next to every
prescription line (form, daily dose, start, end): 2 products and 3 lines
give 6 items, the products ordered by class and the lines in cycles. This
holds for each of the 480 patients of the current psychotropic list, the 406
of the past list and the 273 of the somatic list. Which line belongs to which
product is not in the file, and the number of units a day is computed for
every pair. For the 194 patients who have several current psychotropic
products, no dose and no date can be delivered.
*Answered by the code of the export (2026-11-19, D50):* the export does it,
not the form. `face_dr_12_traitements.sql` keeps one arbitrary row per visit
of each list (`distinct on`, no order), builds the classes from those rows
and joins the rows to the patient by the patient alone; the forms are tables
of rows with an add button and no limit. That is why the past list holds one
product for 404 of 406 patients and half of the patients have one molecule in
the current list. The class and catalogue-code lists (`cmclas`, `cmclascd`)
hold the 8-digit catalogue code of each product of the table; 45 patients
have codes and no substance row (products with no ATC match).
*Request (R122):* can the export write one line per prescription, as for BP
and SZ (drop the `distinct on`, join on the row's own product code, one item
per row as for ASP, a left join, order by visit and row, give the visit of
the row)? The same `distinct on` hits the hospitalisations, the day
hospitalisations and the specialists of the care-use form. The reasons for
stopping a treatment (`psy_arret_1` to `psy_arret_3`, `psy_arret_som_1` to
`psy_arret_som_3`) are in the raw tables and the export does not select them
(to add to R122). Question M65 for the data managers: how many rows does the
lifetime table hold per patient?
*Today:* one item per product, without dates, for the patients with several
products; every line for the patients with one. (O27, D13, D50)

**DEV-2. Three scales are stored on another coding than in BP, and their
stored scores are computed with the BP formula.**
- CTQ: the seven "good childhood" items (2, 5, 7, 13, 19, 26, 28) are stored
  already reversed (the form keys them 5 to 1, and its own script adds the
  values as stored, which is right). In BP they fall when the abuse items
  rise (r = -0.30 to -0.57); here they rise with them (+0.17 to +0.56), in
  every period and centre. The stored emotional neglect, physical neglect and
  total reverse them a second time: the stored emotional neglect falls when
  emotional abuse rises (r = -0.61; +0.67 in BP). The cause is the export,
  not the EMR: the score definition of the export (`ctq.yaml` of the nucleus,
  lines 71 to 126) names the table of this cohort with the BP list of
  reversed items. The definitions of the BIS-10 and the MARS name it the same
  way.
- BIS-10: the same for the eleven reverse-keyed items and every stored
  score (the stored values hold together better as they are, alpha 0.76,
  than after the reversal of the key, 0.65; BP shows the opposite). The
  application's own sub-scores (`bis1035` to `bis1037`) are plain sums of the
  items as stored and equal ours on 530 of 530 visits; the export reverses
  the eleven items a second time and overwrites the application's total with
  its 12-item sum.
- MARS: 1 is "yes" here and "no" in BP (item 5: 14% of answers 1 against
  96%). The stored total counts poor adherence: its median is 3, against 8
  in BP. The script of the form (`220_score.js`) turns items 1 to 6, 9 and 10
  for this coding and is right; the export applies the BP key (items 7 and 8
  reversed) to this cohort's table: stored = 10 - right on 1,026 of 1,026
  visits.
*Question:* can you give this cohort its own score definitions (no reversed
item for the CTQ and the BIS-10, whose items the forms store already turned:
M20 is answered; items 1 to 6, 9 and 10 turned for the MARS), request R146?
*Today:* the items are read back to the BP coding and the scores are
recomputed (CTQ emotional neglect: mean 13.3, for 12.4 in BP; MARS median
7). The stored scores are reproduced exactly by "as stored" formulas and are
not delivered. (O17, D9, D67, D71, D72)

**DEV-3. QIDS-SR16: no total when one item of each pair is answered.** The
form asks for item 6 or 7 (appetite) and for item 8 or 9 (weight). Since
2022 most patients answer one of each pair (26% of the QIDS visits of 2022,
74% of those of 2026), and the EMR then stores no total: 227 visits.
*Answered by the source (D69):* the export takes the highest of each block in
strict mode (`qids.yaml` of the nucleus, lines 19 to 30 and 46 to 60), so a
blank partner blanks the total, whereas the application sets the unanswered
partner to 0 and computes it (`126_score.js`, lines 35 to 45).
*Question:* since when does the form show one item of each pair (the
selectors QIDS6A and QIDS8A are not exported)? Can the export take the
highest answered item of each pair, as the application does?
*Today:* the total is computed when the twelve other items are filled and
each pair has an answer (1,870 totals; 1,643 stored). The same rule now
applies in BP. Requests R147 (the export's strict maximum) and R155 (the
selectors), and A77 (the form's rule that clears the wrong block when QIDS8A
is 2: 2 visits). (O13, D9, D69)

**DEV-4. Other scores that the EMR computes wrongly.**
- SHAPS: the stored score counts "agree" on items 2, 4, 5, 7 and 9 and
  "disagree" on the nine others, while the fourteen stored items all point
  the same way (943 of 943 visits reproduced). The export reverses these five
  items (`shaps.yaml` of the nucleus, line 34); the script of the form counts
  the fourteen items the same way (`224_score.js`). Request R147. (O18, D69)
- Fagerström: item 3 is exported as the code of the answer (1 or 2) and the
  total adds the code: 2 points too high on 129 of 392 visits. The script of
  the form (`112_score.js`, line 49) and the export (`fagers.yaml`) both add
  the code, so one fix serves both. (O15, D72)
- MAThyS: on 68 visits of two centres (2013 to 2018) the stored sub-scores
  add the items with none reversed; the stored total is right. The script of
  the form was changed on 10 December 2018 to take the reversed values into
  account, and these are the visits saved before; the stored values stay
  wrong in the extraction. In BP the data managers recalculate these
  sub-scores since 10 November 2026 (DM-13). (O14, closed, D72)
- BFI: on 16 visits (four centres, 2014 to 2018) the stored
  conscientiousness and neuroticism are each other's value. (O19, D71)
- Age: the stored `age` is the age at inclusion for the patients with one
  visit and up to five years more for the others. (O5)
- SACHS (Bipolarity Index): the stored total is the sum of the five ratings
  each brought to its points, as the script of form 225 does, on 239 of 242
  visits; on the 3 others, the three earliest visits of one centre where the
  keys differ from the points (March, June and December 2016), it is the
  plain sum of the keys. Did the script of that centre change between
  December 2016 and March 2017? (D58)
- FAST: the script of form 130 empties all six domain scores and the total
  when one item is blank, where the BP domain scripts sum each domain alone;
  and 95 of the 527 domains whose items are all 0 are left empty on complete
  visits (A66, M68). (D61)
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
The export keeps one arbitrary row of the episode table per visit (`select
distinct on` with no order: the number typed on the row kept is 1 on 102 of 220
rows), and neither the resistance of the first episode (`TYPE_PREM_EPIR` of
form 116) nor the fields of form 183 that give, since the last visit, the
mixed psychotic episodes, the complete and incomplete remission and the
seasonal pattern (R142, D65). The dates of birth of the relatives are empty. Four columns
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
counted a relative and have no row (R110). The psychotherapy form (155) has
sixteen kinds and a reason for the end of each therapy; the extraction holds
fourteen kinds and no reason (R133, O33). The clean model of the export reads
the CGI improvement of the TRD application (form 184, table `autoq_cgi_i`,
`CGII1`, offered at the follow-up visits) and `face_dr_3_heteroquestionnaires`
selects the CGI severity only, so the extraction has no CGI-I (R145, D61). The same `select distinct on` with
no order keeps one arbitrary row per visit of the hospitalisations, the day
hospitalisations and the specialists of the care-use form (R122). The
Columbia scale has two forms in the table `cssrs` (the full one, 39 yes/no
questions, and the simplified one of 10, chosen by `visite.SVUPDES`): 26% of
the answered visits hold none of the 20 full-form-only fields and the
extraction does not say which form was used (R127). A number typed "00"
leaves the yes/no that the export computes from it empty: 47 sick-leave
numbers (46 from 2024) and 6 numbers of general practitioner visits (R129).
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
neuropsychology form; the two forms of the verbal fluency; the closest
person. The lists of the settings of ECT and TMS, of the expertise of the
therapist and of the result of a psychotherapy (forms 203 and 155, D51), of the
method, drug, consequences and
trigger of the most violent and the most serious suicide attempt and the
place of a hospitalisation or consultation are not in the dictionary either,
but forms 151, 152, 194, 203 and 155 give them (D46, D48, D51): please add them. The
dictionary rows of the sick leave and of the care use say Y/N/NA for answers
stored 1/0/2, and its ISF rows list the visit "v0" only while the form is
shown at 24 and 48 months too (R130). The lists of the medical history and the
two lists of the family (the kind of mood disorder and the suicide of a
relative) are not in the dictionary either, but the forms give them (D34,
D37): please add them. The dictionary lists the visits of `MHOCCUR_EMAN_PSY`,
`MHOCCUR_EIND` and `EVNUM_SUICID` as 6 months and 1 year only, and those of
the YMRS as inclusion, 6 months and 1 year, while later visits hold them
(R144, D65); it maps `EGF_` to `EGD_SCORE`, a column that the export does not
read (R144, D61). The dictionary names the field of the type of diabetes
of the siblings `ATCDFAMCV_FRATRIE_TYPDIAB` and the application
`ATCDFAMCV_ENFANT_TYPDIAB` (form 165 line 133): the export maps it correctly.
Wordings that are missing: the 64 Paykel events (the dictionary announces 61),
the 17 traumatic events, the items of the SHAPS, the SPIN and the MDQ. The 53
Amiel-Lebigre events and the options of their second column (forms 209 and
210, D60), the ATHF columns called bupropion twice and antipsychotics twice and
the keys of its lithium, carbamazepine and bilateral ECT lines (form 154, D59)
and the options of the SACHS (form 225, D58) are in the forms: please add
them to the dictionary.
*Today:* the lists that BP has are read in the order of the BP list where
the shares agree (handedness, type of diabetes); the lists that a form gives
are read from the form; every other list is delivered as `code_N`. (O4, O8,
O9, O20, O23, O25, O26, O28, O29)

**DEV-12. Two defects of the mood forms.** The form of the depressive
symptoms in boxes (182) is in no menu and in no list of simplified visits, and
its "Score total" is never filled; the list forms 128 (inclusion) and 183
(follow-up) are the ones in use (A70). In forms 116 and 183 the psychotic count
of the manic episodes since the last visit is shown only when the hypomanic
count is above 0 (`js/formulaires.js` line 4617, and line 4618 for the mixed
count): the yes/no beside it is filled on 17 follow-up visits and the count on
791 (A71).
*Question:* is line 4617 meant to read a manic count, and is form 182 to be
removed?
*Today:* the count is delivered and the yes/no is not gated; the depressive
symptoms are read from the list forms and, for visits to 2016, from the boxes
of form 182. (D56, D64)

**DEV-13. Defects of the sleep, trauma, QIDS and MDQ forms.**
- PSQI: the script of the form (`192_score.js`, lines 165 to 196) takes the
  absolute difference of the bedtime and the rising time for the efficiency,
  which is wrong across midnight (16 hours in bed from 23:00 to 07:00); the
  extraction is right only because the export computes the efficiency again
  (A74). The Time widget saves its default 00:00:00 untouched (the rising time
  of 39 visits). A bedtime typed 24:xx is exported as it is (7 visits), where
  the BP export converts it to 0, and the warning for the 24-hour clock that
  BP shows is missing (A75).
- CTQ: the script counts an unanswered denial item as 0 (`eval_deni`), and the
  stored denial score is empty on 93 visits that have the three items (A73).
- QIDS: the selectors QIDS6A and QIDS8A are not exported (R155), and
  `js/formulaires.js`, line 3965, clears the wrong block when QIDS8A is 2 (2
  visits show an answer that the form hides: A77).
- MDQ: questions 14 and 15 are hidden since January 2018 when no symptom is
  ticked (`js/formulaires.js`, lines 5157 to 5170); the export cannot tell the
  hidden questions from blanks.
*Question:* can these be corrected or exported?
*Today:* the delivered scores follow the application, not the stored values;
the notes of the schemas say it. (O35, D68, D69, D70)

**DEV-14. Old forms keyed differently.** The BIS form 138 (the form before
215) keys items 33 and 34 as 4, 2, 3, 1 where form 215 keys them 4, 3, 2, 1
(the answers "occasionally" and "often" swap); the BFI form 135 (the form
before 214) keys item 29 from 5 to 1 where form 214 keys it 1 to 5 (found in
two centres, on visits dated 2014 or earlier). Which visits used these forms
is not in the extraction.
*Question:* which visits used the forms 138 and 135, and can the keys be
corrected (A82; the data managers, M75: until when and in which centres)?
*Today:* the BIS items are read as form 215; the BFI item 29 is delivered as
stored. (O37, D71)

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
*Answered by the application (2026-11-19, D55):* the simplified visit
(`visite.SVUPDES = 1`; `DESTVISIMP` in `config/globale2.php`) offers a short
list of forms, and the fourteen scales are exactly the ones that no list
holds (the QIDS, the MADRS, the EQ-5D and the MDQ are on it): an empty scale
since 2018 is "not asked" on a simplified visit. The SACHS and the ERD are
left out too. The YMRS is filled on 90% of the V0 visits to 2017 and 50% since
2018; since 2018 three of the 12 centres with 10 V0 visits or more fill it on
89% to 97% and five on 4% to 17%.
*Question:* since when is the simplified visit used, and by which centres (M69)?
Can the export carry the flag `svupdes` and the list of forms that the visit
offered (R127, R139, R155)?
*Today:* an empty scale since 2018 is missing data: without the flag it cannot
be told from a form left blank; the notes of the scales say that the
simplified visit omits them. (O1)

**DM-2. Other forms that thin out.** The neuropsychological assessment (three
inclusions in four until 2020, one in two since) and the MINI (82% to 89%
of the screening visits until 2020, 57% to 66% since); the ISF at inclusion
(96% to 99% in 2013-2016, 73% in 2017 and 45% to 72% a year since: about 14%
of the inclusions of seven centres since 2018 against 84% at seven others,
while the Columbia scale stays at 75% to 98%); three tests that stop (memory for designs, Baddeley dual task,
auditory span, between 2018 and 2021); SPIN, DETC-CAGE and PCL-S, filled by
a few percent of the patients since 2024; and the list of current psychotropic
treatments (79% to 94% of the patients included until 2019 have one, 50% to
68% of those included since 2021).
*Answered in part by the application (2026-11-19, D55):* the lists of the
simplified visit do not hold the ISF (form 145; the short Columbia form 230 is
offered instead), the MINI (142 and 229), the Paykel list (166), the traumatic
events (208), the SPIN (197) or the PTSD scale (216), and the thinning of these
forms since 2018 may have the same cause (to confirm by the owners of those
tabs; the neuropsychology form 199 is on the lists).
The LEAPS (form 190) is in none of the four lists either, yet it is filled on
64% to 69% of the V0 visits since 2018 (58% in 2012 to 2014): the lists do not
explain every form (O38).
*Question:* which of these are changes of the protocol, and from when? Is the ISF
chosen per centre (M66)? Do the lists cover every form offered on a simplified
visit (M69, R155)? (O22,
O24, O25, O21, O30, O38)

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
103 answers (the week? 60 of the 75 weekday values are multiples of 5: M79).
(O11, O26, O21)

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
on 79 of the 100 CAGE forms whose opening question is empty (78 in 2012 to
2015 and one in 2016; 78 of the 79 have a total of 0), and they ask "have you
ever..." under a question about the present. The fall of the fill rate of the
CAGE (45% of the inclusions of 2012 to 2014, 19% in 2015 to 2017, 2% to 5%
since) follows this change of form.
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

**DM-9. Psychotherapy.** The question "psychotherapy" and the fourteen kinds
of the psychotherapy form disagree: at inclusion 85 of the 211 visits that
answer no hold a kind yes and 12 of the 228 that answer yes hold every kind
no; at follow-up 111 of 451 and 16 of 260. The form has sixteen kinds and a
reason for the end of each therapy, which the extraction does not hold
(R133).
*Questions:* which of the two do the raters fill, and which is right? Can
the two missing kinds and the reasons be exported?
*Today:* the question is delivered as stored, the kinds as answered, and no
"any psychotherapy" is derived. (O33, D51)

**DM-10. FAST domains left empty.** On the 513 visits that have the 24 items,
95 of the 527 domains whose items are all 0 have no stored score (7, 10, 3,
59, 5 and 11 per domain), where the 432 others hold 0. The script of form 130
(A66) explains the visits with a blank item, not these.
*Question:* what leaves a domain empty when its items are all 0 (M68)?
*Today:* the domain score is recomputed from its items, 0 included; the stored
one is a check. (D61)

**DM-11. Two steps in time.** The Amiel-Lebigre list at inclusion has a median
of 4 or 5 events a visit from 2015 to 2018 and 11 to 16 from 2019, inside the
centres (7 of the 8 centres with 6 visits or more in each period rise): the
events ticked "whole life" go from a median of 0 to 6 a visit, and the form and
its four options are the same since 2014. The ERD total has a median of 7 and 9
in 2020 and 2021 against 13 in the other years, in the same centres, and all
fourteen items are lower.
*Question:* did the instructions, the raters or the way the forms are filled
change in these years?
*Today:* delivered as typed; the schema notes say it. (D66)

**DM-12. The period of the questions asked again at follow-up.** The traumatic
events (form 208, no period printed) and the Paykel list (form 166, "in the
preceding year") are asked again at 1, 2 and 4 years; of the traumatic events
answered yes at inclusion, 21%, 17% and 14% are yes again at the three visits
(105, 61 and 27 patients with both forms complete). The MDQ asks whether there
"ever" was a period of elation, yet 47%, 47% and 39% of the yes answers of the
inclusion are yes again. The Paykel month ("from 01 to 12") peaks at 1, 6 and
12. The SPIN is offered at the initial visit only by the application, and 46
of its 147 visits are follow-ups.
*Question:* does a follow-up visit ask about the time since the previous
visit? Is the Paykel month a calendar month or a number of months before the
visit? Why does the SPIN reach follow-up visits?
*Today:* delivered as recorded; the notes say that the follow-up answers are
not cumulative, and the MDQ title says "lifetime at inclusion". (O34, D67,
D70; M73 the follow-up MDQ, M74 the SPIN, M78 the Paykel month and the
follow-up period)

**DM-13. MAThyS: the direction of the scales by centre, and the stored
sub-scores.** In three centres the eight reversed items go with the twelve
others instead of against them in some periods (70 visits of one centre in
2013 to 2015, 30 of another from 2019, 15 of a third in 2022 to 2023: about
115 of the 937 complete visits, 12%; two more centre-periods of 41 and 9 visits
are doubtful, so up to 165 and 18%). The same centre that is wrong in 2013 to
2015 is right in 2016 to 2018. The 68 visits whose stored sub-scores are plain
sums (2013 to 2018) are those saved before the script of the form was changed
on 10 December 2018.
*Question:* does the centre enter the scales in the old direction, or is a form
version missing (BP has the same problem in two centres: BP D91, M47, M77)?
Will the DR extraction be recalculated for the 68 visits, as BP's has been
since 10 November 2026?
*Today:* the key is applied to every visit: the total and the sub-scores of
the visits in the wrong direction are wrong; the note of `mathys` states the
limit. (O36, O14, D72)

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
*Answered by the form (2026-11-19, D44):* form 145 says "ever" and prints no
period, at inclusion and at 2 and 4 years alike: the answers are a yearly
update that the raters read both ways, delivered as `isf_lifetime_fu` (no
longer flagged, and not joined with the BP and SZ questions "since the last
visit"). The Columbia scale (forms 150 and 230) prints no period either.
*Answered by the forms (2026-11-19, D36):* the nine medical histories use the
inclusion form again (form 191), with no period in the questions and no
"change since the last visit" question: a yearly update, as in BP (D84). The
answers still differ from the inclusion ones (migraine 16 of 25 follow-up
visits answer "no" after a "yes" at inclusion, hypertension 4 of 20, counted
by visit). The family form has no follow-up twin: it is on the inclusion visit
only (577 patients, one also at screening, none at 2 or 4 years).
*Today:* the follow-up answers are delivered in columns of their own, with
no flag. (O25, O29)

**PI-3. MINI.** It is given again at 2 and 4 years to 89 visits: by
protocol? Antisocial personality disorder is concluded on 6 visits, none of
which has the criteria in its items. Which version of the MINI is the form
(the modules and the suicidality points are those of version 6)? (O24)

### Priority B

**PI-4. Instruments to name.** Is the word-list test of the neuropsychology the RL/RI-16, and the test for
designs the Designs subtest of the WMS-IV? Which letter and category does
each of the two forms of the verbal fluency use? (O23)
*Answered by form 225 and its script (2026-11-19, D58; O7 closed):* the
"SACHS" is the Bipolarity Index (Aiken, Weisler and Sachs 2015); the form lets
the rater tick one statement per dimension, and the 104 of 242 visits that hold
a value between two points hold a key of a further statement of the same points
(the label of each statement starts with its points).
*Answered by the eCEDR form (2026-11-19, D32):* the word-list test is the
RL/RI-16 (16 items), the test for designs is the Designs subtest of the WMS-IV
(MEM IV), and the fluency forms are letter P with animals and letter R with
fruits.

**PI-5. Mood history.** The type of the first episode has the answers
"resistant" and "not resistant" next to the kinds of episode (21 visits).
"Délai (semaines)": a delay between what and what? Is a resistance score
computed from the ATHF somewhere? None is in the extraction.
*Answered by form 116 (2026-11-20, D65; O26(2)):* the list of the form stops at
"Ne sais pas"; the resistance of the first episode is a separate radio
(`TYPE_PREM_EPIR`) that the export does not select (R142), and the 21 answers
are delivered as missing. The delay is `DELAI_CHRONO_EPI` (weeks, "Max 52"),
and the form does not say a delay of what: still open (equal to the untreated
weeks of the current episode on 52 of 130 rows).
*Answered by form 154 (2026-11-19, D59; O8 closed):* the application has no
script and no total for the ATHF; the published form has none either (number
of trials, number of failed adequate trials, most potent rating, total potency).
(O26)
