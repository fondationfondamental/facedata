# Requests to the export pipeline

This file lists changes we ask of the dataflow export pipeline, questions for the data managers and defects for the application developers. Counts are measured on BPALL_20261113_2.tsv (BPALL below), SZALL_20261117.tsv, DRALL_20261030.tsv and ASPALL_20261030.tsv (SZALL, DRALL, ASPALL). Earlier BP files are BPALL_20261030 and BPALL_20261113 (first run of 13 November). We read dataflow at commit a0e8a09e (2026-11-17) and the eBipolar/eSchizo source at commit 680ecad (2026-11-05). Line numbers refer to these commits.

Centres are named by letters. The letters are per cohort: the same letter names different centres in BP, SZ, DR and ASP. A letter without a cohort is a BP letter. The key of the letters is sent separately, one list per cohort.

Answer with one line per request: `R<n>: done (commit)`, `not done (reason)` or `question`.

## Batch 1 (2026-11-18)

### Summary

Counts, unless stated: BPALL read as text, one row per patient and visit (usubjid + visit: 22,171 visits in 22,178 rows), a cell counted when non-empty after strip. V0 = visit 'V0'; follow-up = any other visit except screening; periods are years of svdtc; centre letters come from siteid. "Package" means our reader's output on the same file. Paths are relative to the dataflow repository; `models/` means `reactor/dbt_project/models/`.

"Changes values" is yes when a value already in the extraction file changes or disappears, a removed column included. A new or renamed column alone is no.

| # | Title | Files (short) | Cohorts | Changes values | Priority | Answers |
|---|---|---|---|---|---|---|
| R1 | One record per patient code: the active record | face_bp_1_patients; trino_overrides | BP, SZ, DR, ASP | yes | high | FU-9 |
| R2 | Stop the run when the patient-removal step fails | face/pipeline.py | BP, SZ, DR, ASP | no | low | none |
| R3 | Count, then export, the patient status | ebipolar_patient; face_bp_1_patients | BP, SZ | no | medium | none |
| R4 | Placeholder or empty birth date: count, then keep | face_*_1_patients | BP, SZ, DR, ASP | yes | high | none |
| R5 | Count patient codes dropped silently | new dbt test | BP, SZ, DR | no | low | none |
| R6 | Say where ARM comes from | face_bp_1_patients; new ebipolar_arm_list | BP | no | medium | none |
| R7 | Document the hard-coded sex of 4 codes | ebipolar_patient | BP | no | low | none |
| R8 | Document day 15 of the birth date | thesaurus PATIENT | BP, SZ | no | low | DEV-13 |
| R9 | SZ record exclusions before the pick | face_sz_1_patients | SZ | no | low | none |
| R10 | DR: age at V0, and the active record | face_dr_1_patients | DR | yes | low | DR O5 |
| R11 | One stop_suivi row per patient | ebipolar_stop_suivi; eschizo_stop_suivi | BP, SZ | no | low | DM-5 |
| R12 | Export the application visit type | face_*_1_visites | BP, SZ, DR, ASP | no | medium | none |
| R13 | Give every follow-up the label of its window | *_visite.sql | BP, SZ, DR, ASP | yes | high | none |
| R14 | DR: fix which visit record DISTINCT ON keeps | edepression_visite | DR | yes | medium | none |
| R15 | ASP: V0 date from active records only | easperger_visite | ASP | no | low | none |
| R16 | Export the year chosen for an annual visit | face_bp/sz_1_visites | BP, SZ | no | low | none |
| R17 | Run the dbt tests as warnings; visit tests | face/pipeline.py; *_visite.yml | BP, SZ, DR, ASP | no | medium | none |
| R18 | Lowest form id when a visit has two rows of a form | 39 ebipolar clean models; face_bp_12; trino_overrides; DR, ASP models | BP, DR, ASP | yes | medium | FU-9, DM-6 |
| R19 | Blank the empty-date placeholders | new macro app_date; clean models | BP, SZ | yes | high | DEV-13 |
| R20 | Put centre C back in the DSM-5 staging union | stg_ebipolar_psy_diag_psychiatriquedsm5 | BP | yes | high | DEV-11, DM-6 |
| R21 | One row per visit in the two clean inputs of tab 6 | ebipolar_comorbide; ebipolar_psy_diag | BP | yes | high | DEV-14 |
| R22 | Blank 2011-11-11 in the follow-up first-attempt date | ebipolar_suicide_sem | BP | yes | high | DEV-13 |
| R23 | Keep the decimal point of the height | ebipolar_infirmier | BP | yes | high | DM-5 |
| R24 | Blank impossible ECG zeros | *_infirmier | BP, SZ, DR | yes | high | DEV-13 |
| R25 | DR nurse form: a decimal comma stops the build | edepression_infirmier | DR | no | low | none |
| R26 | BP LDL unit from the form's choice | ebipolar_lb | BP | yes | high | DM-1, DEV-13 |
| R27 | SZ LDL unit from the form's choice | eschizo_lb | SZ | yes | high | DM-1 |
| R28 | No unit label without a result | *_lb.sql | BP, SZ, DR, ASP | yes | low | DEV-13, DM-1 |
| R29 | Correct wrong default unit labels | ebipolar_lb; data_qa; edepression_lb; eschizo_lb | BP, SZ, DR | yes | medium | DEV-13 |
| R30 | Blank the clearance 0 written by the script | ebipolar_lb | BP | yes | high | DEV-13 |
| R31 | DR: read the TSH, free T3, free T4 unit choice | edepression_lb | DR | yes | high | DM-1 |
| R32 | Blank zeros of the 2009-2010 perinatal forms | *_mh.sql | BP, SZ, DR | yes | low | DEV-13 |
| R33 | Perinatal texts: stop wrong number readings | ebipolar_mh; eschizo_mh; face_bp_9 yml | BP, SZ | no | low | none |
| R34 | Write '>5' relatives as 6 | ebipolar_ap; eschizo_ap | BP, SZ | yes | high | DM-14 |
| R35 | BP empjob: export the form's class label | ebipolar_social | BP | yes | high | FU-8 |
| R36 | BP: export the class of the last job (empjob_last) | ebipolar_social; face_bp_15 | BP | no | medium | FU-8 |
| R37 | BP empjob_psytaitement: unescape; dictionary source | ebipolar_trt_sem; thesaurus | BP | yes | low | DM-7 |
| R38 | BP stprof: students as 3, unanswered empty | ebipolar_social | BP | yes | high | DM-13 |
| R39 | BP saltyp: dead branches, coding, migration map | ebipolar_social; migration config | BP | no | medium | DM-7 |
| R40 | 'Curatelle renforcée' gets its own code | ebipolar_social | BP | yes | low | DM-7 |
| R41 | BP age at first job: keep '<15' and '>60' | ebipolar_social | BP | yes | medium | none |
| R42 | BP household size and work durations: one number only | ebipolar_social | BP | yes | low | none |
| R43 | BP: export the date of the social assessment | face_bp_15 | BP | no | low | none |
| R44 | Follow-up work status (BP), job class (SZ) | ebipolar_trt_sem; face_bp_15; face_sz_12 | BP, SZ | no | medium | none |
| R45 | SZ empjob: old-form class labels | eschizo_social; face_sz_12 | SZ | yes | high | SZ O2 |
| R46 | SZ saltyp: export the ticked labels | eschizo_social | SZ | yes | high | SZ O22 |
| R47 | SZ maristat: match the SZ couple label | eschizo_social | SZ | yes | high | SZ O22 |
| R48 | SZ: export the socio_demog form | new eschizo_socio_demog; face_sz_12 | SZ | no | medium | SZ O23 |
| R49 | PSQI02: read 'H:MM' as meant | ebipolar_autoq_psqi; eschizo_autoq_psqi | BP, SZ | yes | high | DEV-14 |
| R50 | BP EQ-5D clean model: keep the minus sign | ebipolar_hetero_eq5d | BP | no | low | DM-13 |
| R51 | ASP EQ-5D: keep negative indices | easperger_aut_eq5d | ASP | yes | high | DM-13 |
| R52 | MAThyS slider table: count, then read | new staging; ebipolar_autoq_mathys | BP | yes | low | DM-12 |
| R53 | Two ATC codes; manual map only where the seed has none | ebipolar_medicament_psychotrope | BP | no | low | none |
| R54 | Medication strength from the product name | new ebipolar_cm_dose; face_bp_12 | BP, SZ | yes | medium | DM-14 |
| R55 | Stop exporting nom_centre | face_bp_1_patients; ebipolar_patient | BP | yes | low | DM-8 |
| R56 | Remove the copy social_protec | face_bp_1_patients | BP | yes | low | DEV-13 |
| R57 | Referral detail: dictionary name | face_bp_1_patients | BP | no | low | DEV-14 |
| R58 | Describe the 23 _n1 columns | face_bp_3 yml; thesaurus | BP | no | low | DEV-14 |
| R59 | WAIS-IV digit span: undo the alias shift | ebipolar_neuropsyw4; face_bp_4 | BP | yes | high | DEV-14, DM-7 |
| R60 | WAIS-III vocabulary total: stop subtracting 3 | face_bp_4 | BP | yes | high | DEV-14 |
| R61 | WAIS-IV vocabulary in its own columns | face_bp_4 | BP | yes | medium | DEV-14 |
| R62 | Fix the typo date_saise_neuropsychologie | face_bp_4 | BP | no | low | DEV-14 |
| R63 | Remove visit_neuropsychologie | face_bp_4 | BP | yes | low | DEV-13 |
| R64 | Suicide form chosen by visit type | face_bp_5 | BP | no | low | none |
| R65 | Export the comorbidity 'no change' question | face_bp_6 | BP | no | low | DM-10 |
| R66 | Export the pregnancy box | ebipolar_infirmier; face_bp_7 | BP | no | medium | DM-10 |
| R67 | SZ biology: units out of the duplicate ranking | face_sz_8 | SZ | no | low | none |
| R68 | Fix the two NULLIF slips; add the mixed-features answers | face_bp_10 | BP | yes | high | DEV-11 |
| R69 | dsm_criteria from the form that holds answers | face_bp_10 | BP | yes | medium | DEV-11 |
| R70 | One diagnosis form per inclusion row | new ebipolar_dsm_label; face_bp_6, 10, 11 | BP | yes | high | DEV-11 |
| R71 | Lifetime episode Y/N: empty when unanswered | face_bp_10 | BP | yes | high | DEV-13 |
| R72 | Follow-up psychotic flags from follow-up counts | face_bp_10 | BP | yes | high | DEV-13 |
| R73 | Ever hospitalised: SZ 'Ne sais pas', DR '00' | face_sz_10; face_dr_11 | SZ, DR | yes | high | none |
| R74 | Sick leaves: the social form's weeks are not a count | face_bp_11; ebipolar_social | BP | yes | medium | none |
| R75 | Units a day '1/2' read as 0.5 | face_bp_12 | BP | yes | high | none |
| R76 | Order the medication lists | face_bp_12 | BP | yes | low | DM-14 |
| R77 | Export the 7 BP medical-history shortcuts | ebipolar_mh; face_bp_14 | BP | no | high | DM-10 |
| R78 | Export the SZ shortcuts and 'no change?' | eschizo_mh; face_sz_13 | SZ | no | high | DM-10, SZ O26 |
| R79 | Export the BP medical-history change question | ebipolar_mh; face_bp_14 | BP | no | medium | DM-10 |
| R80 | Export the BP family-history change question | ebipolar_ap; face_bp_14 | BP | no | low | DM-10 |
| R81 | Allergic diseases: 0 only after an answered section | face_bp_14 | BP | yes | high | DEV-13 |
| R82 | Relatives' substances: read the list correctly | face_bp_14 | BP | yes | high | DEV-13 |
| R83 | BIS: scale keys, DR entries with no reversal, ASP total | bis10.yaml; test_bis10.py | BP, DR, ASP | yes | high | DM-13 |
| R84 | BIS in BP: each form's scores on its own visits | bis10.yaml | BP | yes | high | DM-13 |
| R85 | MAThyS in BP: the rule of each record's form | mathys.yaml | BP | yes | high | DM-12 |
| R86 | AIM and ALS in BP: short-form scores on long-form visits | aim.yaml; als.yaml | BP | yes | high | none |
| R87 | PRISE-M total by the application's rule | prisem.yaml | BP | yes | high | DM-13 |
| R88 | MDQ: empty when 14/15 unanswered could flip it | mdq.yaml | BP, DR | yes | high | none |
| R89 | PSQI efficiency: equal bed and rising times | psqi/efficiency.py | BP, SZ, DR | yes | high | none |
| R90 | PSQI efficiency: round to 0.1% | psqi/efficiency.py | BP, SZ | yes | low | none |
| R91 | Disable madrsn1_score | madrs.yaml | BP, DR | no | low | DM-13 |
| R92 | Score key names scale_min/scale_max | ctq, als, csm, epworth yaml | all | no | low | DM-13 |
| R93 | Reject unknown keys, invalid files, repeated names | registry; eq5d5l, recsoc, psqi yaml | all | no | low | DM-13 |
| R94 | Record the score run in the extraction summary | scores/api.py; extraction_summary.py | all | no | low | none |
| R95 | Correct the BP dictionary rows | FACEBP V4.34; 2 yml | BP | no | low | DM-7, DM-8 |
| R96 | Two stale BP mapping entries | BP_mapping.toml | BP | no | medium | DM-7 |
| R97 | New-diagnosis column: dictionary spelling | FACEBP V4.34 | BP | no | low | DEV-14 |
| R98 | CPT-3 names without final underscore | FACEBP V4.34 | BP | no | low | DEV-14, DM-7 |
| R99 | non_extract: say when it applies; act in ASP | config_loader.py; cli.py; EXTRACTION.md | all | no | low | none |
| R100 | Stop on a repeated (patient, visit) key | extraction.py; 4 TOMLs | all | no | low | DEV-14 |
| R101 | Quality pass: no visit removed over a perinatal value | reactor DAG; data_qa rules | BP, SZ, DR | no | medium | none |

### Before changing the code: questions

B items are ours: we answer them in this file before you start the request they block. M items are in the data-manager section below.

- **B1.** R22: blank only the placeholders of the follow-up first-attempt date (the request as written), or also empty the follow-up branch of ISF05_QSDTC in face_bp_5 (line 67 becomes `WHEN fiche_clinique.VISIT >= 'V0' THEN NULL`, or `WHEN fiche_clinique.VISIT_TMP IN (3, 4, 5) THEN NULL` after R64), since today's follow-up form does not ask the date? **Answer: the first.** The 2022-2023 form asked the date at some centres, and 60 real dates would be lost; our reader does not deliver a first-attempt date typed at follow-up anyway.
- **B2.** R83 and R84: every DR visit holds the 34-item BIS form. Should the gate of R84 also empty the 12-item scores (bis1038, bis1039, bis1040, bis10) on DR visits? **Answer: yes, the same rule as BP.** The 12-item scores belong on 12-item visits only. DR has none, so they are empty in DR; the 34-item scores stay.

Requests that wait for the data managers:

- R3 waits for M2. R4 waits for M3. Step 4 of R6 waits for M5. Step 2 of R7 waits for M4.
- Step 2 of R12 waits for M9. R14 waits for M44. R15 waits for M45. R16 waits for M46.
- R31 waits for M32. Step 3 of R42 waits for M48. Step 2 of R45 waits for M30. R52 waits for M21. R58 waits for M37.
- R70 waits for M13.
- R83 waits for M20 (please answer it first; the BP and DR parts ship together). Its ASP step waits for M49. R84 ships with R83.
- R85 waits for M47. Step 2 of R86 waits for M23 and M24. R99 waits for M10.

## Patients and records

### R1. Keep one record per patient code: the active record

- **Files:**
  - `models/thesaurus/face_bp/face_bp_1_patients.sql`: line 10 (DISTINCT ON), 808-809 (DSM fallback), 814 and 819 (the `'1900-01-15'` literals), 820 (AGE), 823-824 (FORMOPPOS, SOCIAL_PROTEC), 853-860 (joins and WHERE).
  - New `face_bp_1_patients.yml`.
  - `reactor/reactor/processing/trino_overrides.py`: `_patients` (lines 44-59) and its map entry (line 88).
  - Thesaurus path only: a PATIENT row N_RECORDS ticked in COCHER.
- **Today:**
  - The model runs `SELECT distinct on (patient.fondacode)` with no ORDER BY.
  - Its rows come from patient x DSM-IV x DSM-5 x V0 x non-opposition x social x stop_suivi, all LEFT JOINed on usubjid. The WHERE drops each joined row whose non-opposition form type is 3 or 4, or whose protection measure PROTEC is 3. It runs per row, before the pick. The age filter and 2 hard-coded codes run after the pick.
  - A patient transferred between centres has two raw records (A1). For these patients, usubjid, siteid, sex, end of follow-up and visits come from an arbitrary record. If that record has no V0 or no birth date, the patient is dropped silently.
  - The Trino port orders this pick by `SUBJID, USUBJID`, so Postgres and Trino can deliver different records.
- **Change:** The rule: among the records of a code that pass today's row filters and whose V0 gives an age in (2, 90), keep the one with the latest visit, then the most visits, then the record in the code's own centre, then the lowest id. Deliver the number of records of the code as N_RECORDS. The other record's visits are not re-attached. Everything stays in face_bp_1_patients, so the ranking reads the visits after the visit preprocessing.
  1. Add these CTEs. They use ROW_NUMBER, because the Trino port refuses ORDER BY on non-output columns. Each keeps one row per usubjid, and puts a row that passes today's filter first, so a record passes the filter exactly when one of its rows passes, as today.
  ```sql
  nonopp1 AS (SELECT * FROM (SELECT n.*, ROW_NUMBER() OVER (PARTITION BY n.usubjid
      ORDER BY CASE WHEN n.radhtml_formoppos IN ('3', '4') THEN 1 ELSE 0 END,
               CASE WHEN n.id_nonopposition ~ '^[0-9]+$' THEN CAST(n.id_nonopposition AS bigint) END NULLS LAST) AS rn_nonopp
    FROM nonopp n) t WHERE rn_nonopp = 1),
  social1 AS (SELECT * FROM (SELECT s.*, ROW_NUMBER() OVER (PARTITION BY s.usubjid
      ORDER BY CASE WHEN s.PROTEC = 3 THEN 1 ELSE 0 END, s.visitnum,
               CASE WHEN s.id_social_bilan_social ~ '^[0-9]+$' THEN CAST(s.id_social_bilan_social AS bigint) END NULLS LAST) AS rn_social
    FROM bilan_social s) t WHERE rn_social = 1),
  v0 AS (SELECT * FROM (SELECT f.usubjid, f.visitnum, f.svdtc, ROW_NUMBER() OVER (PARTITION BY f.usubjid
      ORDER BY f.svdtc NULLS LAST, f.visitnum) AS rn_v0
    FROM fiche_clinique f WHERE f.visit = 'V0') t WHERE rn_v0 = 1),
  visits AS (SELECT usubjid, MAX(svdtc) AS last_svdtc, COUNT(DISTINCT visitnum) AS n_visits
             FROM fiche_clinique GROUP BY usubjid),
  n_rec AS (SELECT fondacode, COUNT(*) AS n_records FROM patient GROUP BY fondacode),
  record AS (SELECT * FROM (SELECT patient.usubjid, ROW_NUMBER() OVER (PARTITION BY patient.fondacode
      ORDER BY visits.last_svdtc DESC NULLS LAST, visits.n_visits DESC NULLS LAST,
               CASE WHEN LPAD(CAST(patient.centre AS varchar), 2, '0') = SUBSTRING(patient.fondacode FROM 1 FOR 2) THEN 0 ELSE 1 END,
               CASE WHEN patient.usubjid ~ '^[0-9]+$' THEN CAST(patient.usubjid AS bigint) END NULLS LAST) AS record_rank
    FROM patient
    JOIN v0 ON v0.usubjid = patient.usubjid
    LEFT JOIN visits ON visits.usubjid = patient.usubjid
    LEFT JOIN nonopp1 ON nonopp1.usubjid = patient.usubjid
    LEFT JOIN social1 ON social1.usubjid = patient.usubjid
    WHERE (nonopp1.radhtml_formoppos NOT IN ('3', '4') OR nonopp1.radhtml_formoppos IS NULL)
      AND (social1.PROTEC != 3 OR social1.PROTEC IS NULL)
      AND patient.BRTHDTC <> DATE '1900-01-15'
      AND EXTRACT(YEAR FROM AGE(v0.svdtc, patient.BRTHDTC)) > 2
      AND EXTRACT(YEAR FROM AGE(v0.svdtc, patient.BRTHDTC)) < 90) t
    WHERE record_rank = 1),
  ```
  2. In the joined CTE:
     - Drop `distinct on`.
     - FROM: `patient JOIN record ON record.usubjid = patient.usubjid LEFT JOIN n_rec ON n_rec.fondacode = patient.fondacode LEFT JOIN v0 ON v0.usubjid = patient.usubjid`. Join psy_diag_psychiatrique and diagdsm5 on usubjid and `visitnum = v0.visitnum`, and nonopp1, social1 and stop_suivi on usubjid.
     - Keep today's WHERE (line 860) word for word.
     - Read FORMOPPOS from nonopp1, SOCIAL_PROTEC from social1 (until R56), and AGE from `v0.svdtc`.
     - Write `DATE '1900-01-15'` in both places.
     - Add `n_rec.n_records AS N_RECORDS`.
     - Keep the outer age filter and the 2 hard-coded codes.
  3. Delete `_patients` and its map entry. Run `reactor/tests/processing/test_trino_port.py::test_every_ebipolar_model_converts_to_valid_trino_sql`.
  4. In face_bp_1_patients.yml: subjid and usubjid unique and not_null; document n_records. R17 runs these tests.
- **Ships with:** after R11 (one stop_suivi row per patient), R18 and R21 (one diagnosis row per visit). R17 for the tests.
- **Effect on the current files:**
  - 18 of the 6,475 patients common to BPALL_20261030 and BPALL changed usubjid and siteid; 0 changed between the two 13 Nov runs. Measured with distinct (subjid, usubjid, siteid) per file, joined on subjid.
  - Simulated on these 18, each record's visits taken from the file where it was kept: the rule keeps the 13 Nov record for 14 and the 30 Oct record for 4, losing 0 (visit, date) pairs; today's file loses 1. So in BPALL, 4 patients change record once more and 1 visit comes back.
  - 57 BPALL patients switched or were delivered outside their code's centre in one run. Measured as subjid digits 1-2 against the modal digits of the siteid; these are equal for 17 of 17 centres.
  - Single-record patients: no change expected to ARM or AGE. dsm_criteria is filled on 5,649 rows, all V0, and no patient has two V0 rows.
  - All 6,498 delivered patients have an age, so patients lost today cannot be counted (M1).
  - N_RECORDS is added for 6,498 patients.
- **Other cohorts:** Apply the same rule with the same CTEs (v0, visits, n_rec, record), and deliver N_RECORDS under the same name.
  - SZ: face_sz_1_patients line 9 has the same pick, and eschizo_patient has no dedupe; 6 SZ patients are outside their code's centre. SZ's own row filter and the exclusions of R9 apply before the ranking. Add unique tests.
  - DR: face_dr_1_patients line 7; 0 patients outside their code's centre. R10 adds the V0 join.
  - ASP: face_asp_1_patients line 8 and easperger_patient; 0 outside.
- **Answers:** FU-9.

### R2. Stop the run when the patient-removal step fails

- **Files:** `reactor/reactor/studies/face/pipeline.py` (`_apply_patient_operations`, lines 513-567); `nucleus/nucleus/data_qa/config/studies/face/rules/clinical/patient_removals.yaml`.
- **Today:** patient_removals.yaml is applied after the thesaurus layer, to the gold schema the extraction reads. It holds 1 SZ entry and 0 BP entries. A failure only logs a warning, and the extraction CLI does not apply the list, so a failed step delivers the patient.
- **Change:** When removals are configured and the step fails, fail the run, or write a marker that the extraction CLI checks.
- **Ships with:** none.
- **Effect on the current files:** None. The removed SZ patient is absent from SZALL.
- **Other cohorts:** The same step serves all four.
- **Answers:** none.

### R3. Count, then export, the patient status 'Patient exclu de la cohorte'

- **Files:** `clean/ebipolar/ebipolar_patient.sql` line 27; `face_bp_1_patients.sql`; SZ `eschizo_patient.sql` line 27 and `face_sz_1_patients.sql`.
- **Today:**
  - rad_statut_visite (answers include 'Refus de participation au suivi par le patient' and 'Patient exclu de la cohorte') is selected and never used or exported.
  - It is in the invisible group 999 of both applications, so only older versions could set it.
  - The eBipolar and eSchizo patient tables have no del or status column.
- **Change:** Wait for M2. If delivered patients hold a value, add `patient.rad_statut_visite AS STATUT_VISITE` (TOML path: nothing more; thesaurus path: tick a PATIENT row). This request removes no patient.
- **Ships with:** R1 (same model).
- **Effect on the current files:** Not measurable (M2).
- **Other cohorts:** SZ: same field and same change. DR and ASP filter their del and status flags.
- **Answers:** none.

### R4. Patients whose birth date is a placeholder or empty: count them, then keep them

- **Files:** `face_bp_1_patients.sql` lines 812-821 and 865; SZ lines 17, 22, 57; DR lines 30, 33, 54; ASP lines 28, 126.
- **Today:** '1900-01-15' (a placeholder month plus day 15) and unparsable dates give NULL BRTHDTC and AGE, and `WHERE age > 2 AND age < 90` drops the patient with no trace.
- **Change:** Wait for M3. If the count is not zero:
  1. Line 865 becomes `where (age > 2 and age < 90) or (age is null and BRTHDTC is null)`.
  2. In R1, a record without a usable birth date becomes a candidate, ranked after the records with an age in (2, 90).
  3. Same change in the other cohorts (SZ and ASP also have `age is not null`).
- **Ships with:** R1.
- **Effect on the current files:** Not measurable (M3); all 6,498 delivered patients have a birth date.
- **Other cohorts:** Same rule in SZ, DR, ASP.
- **Answers:** none.

### R5. Count, at each run, the patient codes dropped silently, by reason

- **Files:** new `reactor/dbt_project/tests/face_bp_dropped_patients.sql`.
- **Today:** The .fond export sends only the birth month (exportExcludedFields). ebipolar_patient adds day 15, the placeholder month becomes NULL, and the age filter drops the patient. Missing birth dates, records with no V0 and ages outside 2-90 are dropped the same way, and nothing counts them.
- **Change:** Add a warn test, run by R17. Log the counts, never the codes.
  ```sql
  SELECT reason, count(DISTINCT fondacode) AS patients FROM (
    SELECT p.fondacode, CASE WHEN p.brthdtc = DATE '1900-01-15' THEN 'placeholder birth date'
      WHEN p.brthdtc IS NULL THEN 'no birth date'
      WHEN NOT EXISTS (SELECT 1 FROM {{ ref('ebipolar_visite') }} v WHERE v.usubjid = p.usubjid AND v.visit = 'V0') THEN 'no V0'
      ELSE 'other: age outside 2-90, row filter, or record not kept' END AS reason
    FROM {{ ref('ebipolar_patient') }} p
    WHERE NOT EXISTS (SELECT 1 FROM {{ ref('face_bp_1_patients') }} g WHERE g.subjid = p.fondacode)) t
  GROUP BY reason
  ```
- **Ships with:** R17.
- **Effect on the current files:** None. In BPALL and BPALL_20261030, 0 delivered patients lack an age or a birth date. Today's number is M3.
- **Other cohorts:** Same test for SZ (lines 17, 22) and DR (30, 33). In ASP the rule is commented out on line 21 and active on line 28.
- **Answers:** none.

### R6. Say where ARM comes from: add ARM_SOURCE and ARM_DSM, and move the override list into its own model

- **Files:** `face_bp_1_patients.sql` lines 16-812; new `clean/ebipolar/ebipolar_arm_list.sql` and `.yml`.
- **Today:** A CASE on fondacode overrides the DSM answer.
  - 787 active WHEN lines for 780 codes. 7 codes appear twice, 3 of them with two labels (the first WHEN wins), and 1 code maps to ''.
  - The only conflict involving a kept label is on a code that is in no file.
  - 509 BPALL patients are listed (298 BP2, 165 BP1, 44 'Bipolaire non spécifié', 1 BPNOS, 1 TBNOS), and their arm always equals the list label. 494 of them have an empty dsm_criteria.
  - By centre: A 226, C 214, B 56, G 7, J 3, E 2, D 1.
  - Of the 271 listed codes absent from the file, 248 have a label outside the kept five, and 23 have a kept label.
  - The list has one commit, and nothing says where ARM came from.
- **Change:**
  1. `ebipolar_arm_list.sql` is `SELECT * FROM (VALUES ('<code>', '<label>'), ...) AS t(fondacode, arm_label)`, one row per code with its first label (780 rows, codes quoted). The yml declares fondacode unique and not_null (run by R17). Use VALUES rather than a seed: seeds are in git LFS and turn '' into NULL.
  2. LEFT JOIN arm_list on fondacode, then:
  ```sql
  CASE WHEN arm_list.fondacode IS NOT NULL THEN arm_list.arm_label
       ELSE COALESCE(NULLIF(diagdsm5.rad_tb_hum, ''), NULLIF(psy_diag_psychiatrique.rad_tb_hum, '')) END AS ARM,
  CASE WHEN arm_list.fondacode IS NOT NULL THEN 'list' WHEN NULLIF(diagdsm5.rad_tb_hum, '') IS NOT NULL THEN 'dsm5'
       WHEN NULLIF(psy_diag_psychiatrique.rad_tb_hum, '') IS NOT NULL THEN 'dsm4' END AS ARM_SOURCE,
  COALESCE(NULLIF(diagdsm5.rad_tb_hum, ''), NULLIF(psy_diag_psychiatrique.rad_tb_hum, '')) AS ARM_DSM
  ```
  3. Do not normalise labels: 14 codes carry spectrum, cyclothymia, induced or 'TB ?' labels.
  4. After M5, settle the conflicts and the '' entry, and add the test codes to the outer exclusion next to the 2 hard-coded codes.
  5. Thesaurus path: tick the two columns. Document them in the yml.
  6. Run test_trino_port.py (ebipolar_arm_list is a new clean model).
- **Ships with:** after R1: add the arm_list join to the FROM that R1 writes.
- **Effect on the current files:** ARM is unchanged for 6,498 patients, and ARM_SOURCE = 'list' for 509. The dsm4/dsm5 split cannot be measured, because rad_tb_hum is not exported.
- **Other cohorts:** SZ applies 2 ARM corrections after dbt, so its ARM_SOURCE needs a value 'correction'. DR and ASP take ARM from the form. Use the same column names in every cohort.
- **Answers:** none.

### R7. Document, or move, the hard-coded sex of 4 patient codes

- **Files:** `clean/ebipolar/ebipolar_patient.sql` line 16.
- **Today:** Line 16 forces 'Feminin' for 4 BP codes, with no comment. 3 are in BPALL (centres E, H, L), all delivered outside their code's centre, so they are transferred patients; none switched record. The 4th is on the ARM list and is absent.
- **Change:**
  1. Get the reason (M4).
  2. Keep the rule, with a comment giving the reason and date. Moving it to patient_corrections.yaml is riskier, because that step only warns on failure.
  3. Add a warn test, run by R17: `SELECT count(*) FROM (SELECT fondacode FROM {{ ref('ebipolar_patient') }} GROUP BY fondacode HAVING count(DISTINCT sex) > 1) t`.
- **Ships with:** none.
- **Effect on the current files:** none.
- **Other cohorts:** SZ and DR have no such override. ASP has commented per-code birth dates.
- **Answers:** none.

### R8. Document day 15 of the birth date and its effect on the age

- **Files:** thesaurus FACEBP V4.34 PATIENT rows BRTHDTC and AGE; the SZ thesaurus. Optional: `ebipolar_patient.sql` line 10, `eschizo_patient.sql` 13-14, `edepression_patient.sql` 7.
- **Today:** The application exports year and month only. Line 10 appends '-15', and AGE is computed from that date (face_bp_1_patients line 820).
- **Change:**
  1. BRTHDTC label: 'year and month of birth; the export sets the day to the 15th'.
  2. AGE label: 'completed years at inclusion, from the birth date with day 15; can be one year off when the inclusion falls in the birth month'.
  3. Same labels for SZ. Not for DR.
  4. Optional: add `!~ '^0000'` to the line-10 branch, as ASP does, because '0000-00-15' would stop the build.
- **Ships with:** none.
- **Effect on the current files:** No values change. 6,498 of 6,498 BP patients have day 15. 548 BP and 204 SZ patients have their V0 in their birth month.
- **Other cohorts:** In DR, 88 of 634 patients keep a real day (DR centres G 44, J 44).
- **Answers:** DEV-13.

### R9. Apply the SZ record exclusions before the pick, with a written reason for each

- **Files:** `face_sz_1_patients.sql` lines 50 and 55-58.
- **Today:** 1 fondacode is excluded before DISTINCT ON; 3 usubjid are excluded after it, so the unordered pick decides whether such a patient is in or out. None of the 4 is in SZALL; the ids belong to SZ centres A, A and J.
- **Change:**
  1. Move `AND patient.usubjid NOT IN (<the 3 ids>)` next to line 50.
  2. Comment each entry with its reason.
  3. Keep ids, not codes: each id carries 2 or more codes.
  4. Add unique tests on usubjid and subjid, run by R17.
- **Ships with:** none.
- **Effect on the current files:** 0, as far as the file shows.
- **Other cohorts:** BP and DR exclude on the pick key itself.
- **Answers:** none.

### R10. DR: compute the age at the V0 visit, and keep the active record

- **Files:** `face_dr_1_patients.sql` lines 7 and 48.
- **Today:** The visit join has no filter, so the unordered pick computes AGE at an arbitrary visit.
- **Change:**
  1. Line 48 adds `AND visite.visit = 'V0'`.
  2. Pick the record with R1's rule: the CTEs v0, visits, n_rec and record of R1, built on edepression_patient and edepression_visite, without the BP row filters (latest visit, then most visits, then the record in the code's own centre, then the lowest id, with the guarded cast). The V0 join of step 1 then feeds AGE only. Add N_RECORDS.
  3. Leave diag_psy (line 50) as it is until one patient of DR centre M with a screening diagnosis is checked.
- **Ships with:** none (R1 gives the rule).
- **Effect on the current files:** AGE changes for 184 of 634 DR patients (stored age against the calendar age from brthdtc and the V0 svdtc). 0 patients leave. Our delivered age is computed separately and does not change.
- **Other cohorts:** BP and SZ already join V0.
- **Answers:** DR O5.

### R11. Keep one stop_suivi row per patient with a fixed rule that the Trino port accepts

- **Files:** `clean/ebipolar/ebipolar_stop_suivi.sql`; SZ `clean/eschizo/eschizo_stop_suivi.sql`.
- **Today:**
  - The model is a plain SELECT of the staging union.
  - The application has no unique key on stop_suivi.ID_patient (A5). Its form opens and edits the first row (acces_formulaire.php lines 52-86), and the reminder lists treat any row with a reason as stopped.
  - face_bp_1_patients picks arbitrarily among such rows.
  - This model is the first of trino_slice.SLICE_MODELS.
- **Change:**
  1. Rename the columns in a CTE `renamed`, with the same output aliases as today.
  2. End with `SELECT DISTINCT ON (USUBJID) <the 12 columns> FROM renamed ORDER BY USUBJID, CASE WHEN id_stop_suivi ~ '^[0-9]+$' THEN CAST(id_stop_suivi AS BIGINT) END ASC NULLS LAST`. This keeps the lowest id, the row the form opens, as R18 does for the forms of a visit. It uses output names only, which `_eliminate_distinct_on` requires. Ids are text (varchar in the source ymls), hence the guarded cast.
  3. Run test_trino_port.py.
  4. After the change, the count of usubjid with more than one row must be 0 (a unique test, run by R17).
  5. Keep both column sets (*_stopsuivi and *_patient) in face_bp_1_patients.
- **Ships with:** before R1.
- **Effect on the current files:**
  - 71 of 6,498 patients have a stop_suivi row (dthdtc_stopsuivi filled), 70 of them with a reason.
  - The 8 columns are identical across BPALL_20261030, BPALL_20261113 and BPALL.
  - Expect 0 changes unless M7 finds differing duplicates.
- **Other cohorts:**
  - SZ has the same defect: 1,004 of 2,353 patients have a row, and 583 a reason. Wrap its final SELECT as CTE `renamed` and end with `SELECT DISTINCT ON (USUBJID) * FROM renamed ORDER BY USUBJID, <same id cast>`.
  - DR: the section is empty. ASP: not exported.
- **Answers:** DM-5.

## Visits

### R12. Export the application visit type in the visit table of the four cohorts

- **Files:** `face_bp_1_visites.sql` line 9; `face_sz_1_visites.sql` and `face_dr_1_visites.sql` line 8; `face_asp_1_visites.sql` line 9 (inside the select distinct); thesaurus PATIENT visit section; the base TOML of the ALL runs.
- **Today:** The clean models carry visit_tmp, but no visit table exports it. From the label: the 3,352 odd-labelled BP follow-ups are type 3 or 5; of the 8,334 even-labelled ones, 1,029 are certainly type 4, and 7,305 are undecidable.
- **Change:**
  1. Add `visit_tmp AS visit_type` after date_saisie in all four models. Use this name in every cohort.
  2. The visit table is appended from the base TOML (config_loader __append_untouched_base_tables). If that TOML lists columns, add "visit_type" (M9).
  3. Add a thesaurus row with COCHER empty, as for the 6 existing visit columns. CODAGE: '1=Screening; 2=Evaluation initiale; 3=Consultation semestrielle; 4=Evaluation annuelle; 5=Bilan hors visite'. SZ codes are 1, 2, 4; ASP codes are 1, 2, 4, 7; DR codes come from M44.
  4. Leave `wanted_visists` alone: both spellings are read (config_loader lines 1170-1172).
- **Ships with:** before R13. Tell us the first extraction that carries it.
- **Effect on the current files:** One new column on 22,178 rows: 1 on 3,987 screening rows, 2 on 6,498 V0 rows, 3/4/5 on 11,693 follow-up rows.
- **Other cohorts:** Same column name in all four.
- **Answers:** none.

### R13. Give every type-3 and type-4 visit the label of its window

- **Files:** `clean/ebipolar/ebipolar_visite.sql` lines 33-71 and 74-99; `eschizo_visite.sql` 23-61 and 64-78; `edepression_visite.sql` 29-67 and 70-82; `easperger_visite.sql` 33-71 and 74-87.
- **Today:**
  - The semester table (types 3 and 5, ids 3-23) has gaps at 2839-3017, 3204-3382 and 3569-3747 days, and stops at 3934. The annual table (ids 4-22) stops at 3844.
  - Outside a window, `ELSE visit_tmp` labels the visit V6_mois, V1_an or V18_mois. The preprocessor (visits.py) then merges such a visit into a real visit with that label (Case 2), or deletes both (tie, Case 3).
  - BPALL has 9 fallback follow-ups (7 V1_an, 1 V6_mois, 1 V18_mois) in 8 patients, 8.9 to 15.4 years after V0, centres C 5, E 2, A 1, L 1.
- **Change:**
  1. id_visit for type 3:
     - keep today's boundaries;
     - fill the gaps with ids 18 (<3018), 20 (<3383) and 22 (<3748); 23 is <3934;
     - then `ELSE 24 + CAST(FLOOR((VISITDY - 3934) / 182.625) AS INTEGER)`.
  2. Type 5 (off-visit assessments, 'Bilan hors visite'): keep today's branch in this release. We will ask for a rule once the first extraction with visit_type (R12) and M43 show how many there are.
  3. Types 4, 6, 8: keep the windows up to 22 (<3844), then `ELSE 24 + 2 * CAST(FLOOR((VISITDY - 3844) / 365.25) AS INTEGER)`.
  4. `WHEN VISITDY IS NULL THEN visit_tmp` stays first, so Case -1 still deletes those rows.
  5. Label:
  ```sql
  case when id_visit is null then null when id_visit = 1 then 'screening' when id_visit = 2 then 'V0'
       when visit_tmp not in (3, 4, 5, 6, 8) then null when id_visit = 4 then 'V1_an'
       when id_visit % 2 = 0 then 'V' || CAST((id_visit - 2) / 2 AS VARCHAR) || '_ans'
       else 'V' || CAST((id_visit - 2) * 6 AS VARCHAR) || '_mois' end as visit
  ```
  6. SZ, DR, ASP: the same, with one branch `VISIT_TMP IN (3, 5)`. Keep the eSchizo `CAST(visit_tmp AS integer)`. ASP type 7 stays unlabelled.
- **Ships with:** R12 first; R17. Tell us the first extraction that carries it.
- **Effect on the current files:** Simulated: dy from the V0 svdtc, type inferred from the fallback label.
  - 8 labels change: V1_an becomes V11_ans (3), V12_ans (2), V13_ans (1), V15_ans (1); V6_mois becomes V12_ans (1).
  - The formula gives today's label on all 22,171 visits. Repeated (usubjid, visit): 0 before and after. Out-of-order follow-ups: 5 become 2.
  - The 1 certain type-5 record (V18_mois at 8.9 years, in a gap) keeps its label. The same patient has an annual V9_ans on the same day.
  - Hidden merges and deletions need M42. 0 of the 9 patients followed 3,844 days or more have a non-fallback V1_an, against 74.3% of the 4,299 followed patients.
- **Other cohorts:** SZ: 3 labels change. DR: the empty id-14 label becomes V6_ans. ASP: 0 changes. The biobank models under thesaurus/prbbiofacepsycohigive inherit the labels.
- **Answers:** none.

### R14. DR: choose which record DISTINCT ON keeps

- **Files:** `clean/edepression/edepression_visite.sql` lines 1-21.
- **Today:** `DISTINCT ON (id_patient, centre, type_visit)` has no ORDER BY. A dropped record becomes orphaned, and the preprocessor (Case 4) deletes its forms.
- **Change:** Wait for M44. If (patient, centre, type) groups with 2 or more active records exist, keep the latest created record: add `ORDER BY id_patient, centre, type_visit, date_saisie DESC NULLS LAST, id_visite DESC` at the end of the CTE (in eBipolar, date_saisie is the day a record is created). This rule is provisional; M44 can change it.
- **Ships with:** none.
- **Effect on the current files:** Not measurable from DRALL (2,193 visits); see M44.
- **Other cohorts:** none.
- **Answers:** none.

### R15. ASP: compute the V0 date from active records only

- **Files:** `clean/easperger/easperger_visite.sql` lines 22-23.
- **Today:** v2 takes type-2 records before the `del = 0 and status = 1` filter (line 89), so an inactive V0 can duplicate rows.
- **Change:** Wait for M45.
  1. Add `and cast(del as integer) = 0 and cast(status as integer) = 1` to v2.
  2. Check that count(*) = count(distinct visitnum) in face_asp_1_visites before and after.
- **Ships with:** none.
- **Effect on the current files:** No sign in ASPALL: 4,500 rows, 4,500 visitnums, one V0 per patient.
- **Other cohorts:** DR filters already.
- **Answers:** none.

### R16. Export the year chosen for an annual visit (type_annuelle)

- **Files:** `face_bp_1_visites.sql`, `face_sz_1_visites.sql`; thesaurus.
- **Today:** ebipolar_visite (lines 10, 31) and eschizo_visite carry type_annuelle, but it is not exported. visite_nouvelle.php writes it for every disease (its schizo condition is commented out, lines 64-70).
- **Change:** Wait for M46. Add `type_annuelle AS visit_year_application` after the visit_type line, and a thesaurus row with COCHER empty.
- **Ships with:** R12.
- **Effect on the current files:** Not measurable.
- **Other cohorts:** DR and ASP have no such column.
- **Answers:** none.

### R17. Run the dbt tests as warnings, and test the four visit models after the visit preprocessing

- **Files:** `reactor/reactor/studies/face/pipeline.py` (around lines 141-152, and after the thesaurus layer); new `ebipolar_visite.yml`, `eschizo_visite.yml`, `edepression_visite.yml`; the existing `easperger_visite.yml`.
- **Today:** Each layer runs `dbt run` only (base/pipeline.py line 194), so no test ever runs. Fallback labels and NULL labels pass silently (DR id 14).
- **Change:**
  1. After `_process_visits(...)`, call `self.executor.test(select=VISIT_PREPROCESSING_CONFIG[pathology]["table_name"])`, and log failures as warnings.
  2. After the thesaurus layer, test the cohort's clean and thesaurus models the same way (for BP, the models under clean/ebipolar and thesaurus/face_bp), as warnings. R1, R5, R6, R7, R9, R11, R18 and R100 rely on this step.
  3. All tests `severity: warn`, under the `tests:` key (dbt-core ^1.7).
  4. Visit tests:
     - unique [usubjid, visit];
     - `visit is not null` where `visit_tmp is not null`;
     - `not (visit_tmp = 3 and id_visit = 3 and visitdy >= 276)`, the same for 4 (550) and 5 (642);
     - visitnum unique and not_null;
     - visit_tmp accepted_values: BP [1-5], SZ [1, 2, 4], ASP [1, 2, 4, 7], DR from M44.
  5. ASP: add the tests to the existing entry, not to a second file (a duplicate entry is a parse error).
- **Ships with:** R13.
- **Effect on the current files:** No values change. Visit warnings today: BP 9, SZ 3, DR 1; after R13, only the BP type-5 row is left.
- **Other cohorts:** included.
- **Answers:** none.

## Clean models (by form)

### R18. Keep the lowest form id when a visit has two rows of the same form

- **Files:**
  - New `reactor/dbt_project/analyses/bp_form_duplicates.sql`.
  - 39 models in `models/clean/ebipolar/`:
    - 36 with DISTINCT ON: ebipolar_autoq_{aim, als, altman, aq12, asrs, bdhi, bis, circadien, csm, ctq, epworth, mars, mathys, mdq, prisem, psqi, qids, stay_a, wurs}; ebipolar_cssrs; ebipolar_hetero_{alda, cgi_egf, eq5d, etatp, fast, madrs, madrs_n1, ymrs, ymrs_n1}; ebipolar_infirmier, _mh, _neuropsy, _neuropsyw4, _psy_diag_dsm5, _suicide, _suicide_sem;
    - ebipolar_autoq_als18, with no dedupe;
    - ebipolar_ap (lines 676-688) and ebipolar_lb (lines 424-432), with ROW_NUMBER.
  - `face_bp_12_traitements.sql` line 3; `trino_overrides.py` `_traitements` (lines 62-73).
  - New `models/staging/ebipolar/_stg_ebipolar_form_keys.yml`.
- **Today:**
  - The 36 models use DISTINCT ON (USUBJID, VISITNUM) with no ORDER BY, so a visit with two raw rows gets either row.
  - ebipolar_autoq_als18 keeps every row, and face_bp_2 LEFT JOINs it (line 565), so two rows would double the visit.
  - ebipolar_ap and ebipolar_lb keep one row per visit with ROW_NUMBER: a row with data first, then the highest id (`id_psy_antecedant_familiaux_psy DESC`, `id_inf_bilan_biologique DESC`).
  - BPALL_20261113 and BPALL differ, across all 2,236 columns, in mere_dthfl (code fix 30586bc2) and in 6 PRISE-M cells of 1 V0 visit of centre N (prism, prism04a, prism09b/c/d/f). Same raw schemas, PRISE-M model unchanged since 2026-06-16. So the raw table holds two rows for that visit, despite the UNIQUE KEY on ID_fiche_clinique (A4).
  - The application opens the lowest id (acces_formulaire.php lines 52-55, 84-86).
  - face_bp_12 line 3 picks one medicament_lifetime row per patient arbitrarily (no key on ID_patient). Its 45 columns repeat on every visit, and Trino orders the same pick by the id as text.
  - Ids are text. date_saisie is the creation day, so 'last saved' is not available.
- **Change:** Keep the lowest form id, the row the application opens, with one ORDER BY per model.
  1. The analysis counts, per staging model and centre, the visits with 2+ rows, those whose rows differ, and those whose copies share an id. Run it on Postgres.
  ```sql
  SELECT '<stg model>' AS form_table, centre, COUNT(*) AS visits_with_2_rows_or_more,
         SUM(CASE WHEN n_versions > 1 THEN 1 ELSE 0 END) AS visits_whose_rows_differ,
         SUM(CASE WHEN n_ids < n_rows THEN 1 ELSE 0 END) AS copies_sharing_an_id
  FROM (SELECT centre, id_fiche_clinique, COUNT(*) AS n_rows, COUNT(DISTINCT <id column>) AS n_ids,
               COUNT(DISTINCT md5((to_jsonb(t) - '<id column>' - 'date_saisie')::text)) AS n_versions
        FROM {{ ref('<stg model>') }} AS t GROUP BY centre, id_fiche_clinique HAVING COUNT(*) > 1) d
  GROUP BY centre
  ```
     - Run it on the staging model of each of the 39 models, on medicament_lifetime (grouped by id_patient), and on the tables that no model deduplicates: social_bilan_social, psy_diag_psychiatrique, _semestriel, psy_traitement_semestriel, psy_troubles_comorbides.
  2. In the 36 models, append `ORDER BY USUBJID, VISITNUM, CASE WHEN <id> ~ '^[0-9]+$' THEN CAST(<id> AS bigint) END`, where `<id>` is the model's raw id: id_autoq_<name>, id_autoq_type_circadien, id_hetero_<name>, id_hetero_etat_patient, id_cssrs, id_inf_dossier_infirmier, id_psy_histoire_medicale, id_psy_neuropsychologie(_wais4), id_psy_diag_psychiatriquedsm5, id_psy_suicide(_semestriel).
     - In ebipolar_autoq_qids, add `id_autoq_ids,` to the SELECT.
     - In ebipolar_autoq_wurs, add `id_autoq_wurs,` (the Trino port needs output names).
     - ebipolar_infirmier uses lowercase names.
     - ebipolar_autoq_als18: start the SELECT with `DISTINCT ON (USUBJID, VISITNUM)` and append the same ORDER BY on id_autoq_als18.
     - ebipolar_ap (lines 678-682) and ebipolar_lb (lines 426-428): replace the ORDER BY of the ROW_NUMBER with `CASE WHEN <id> ~ '^[0-9]+$' THEN CAST(<id> AS bigint) END`, on id_psy_antecedant_familiaux_psy and id_inf_bilan_biologique.
  3. face_bp_12 line 3 becomes `SELECT DISTINCT ON (usubjid) * FROM {{ref('ebipolar_medicament_lt')}} AS medicament_lifetime ORDER BY usubjid, CASE WHEN id_medicament_lifetime ~ '^[0-9]+$' THEN CAST(id_medicament_lifetime AS bigint) END`. In `_traitements`, the old string becomes this new line-3 text (with `*`), and the new string is the same text with `{columns}` in place of `*` and no ORDER BY added. Otherwise the port writes two ORDER BY clauses.
  4. Add warn tests `unique_combination_of_columns` [centre, id_fiche_clinique] ([centre, id_patient] for lifetime). R17 runs them.
  5. test_trino_port.py must pass.
- **Ships with:** R21 (same rule).
- **Effect on the current files:**
  - Rows unchanged.
  - The 1 known PRISE-M visit gets a fixed version (6 prism* cells differ; 31 against 32 filled). Other visits, including those where ebipolar_ap and ebipolar_lb now keep another row: M6.
  - Lifetime: of 2,817 patients with answers, 0 have differing rows. 2 patients changed between BPALL_20261030 and BPALL, and the medication lists of 3,429 of 4,750 patients changed order, so physical order does move.
- **Other cohorts:** DR: 9 edepression_autoq models and 18 DISTINCT ON in face_dr_10, 11, 12 and 13 (face_dr_12 lines 4-9 include psy_lifetime, the lifetime treatments). ASP: 10 face_asp tab models. Apply the same rule there (lowest raw id, guarded cast, one ORDER BY per model). SZ keeps its own rule for now.
- **Answers:** FU-9, DM-6.

### R19. Blank the empty-date placeholders 1000-01-01 and 0000-00-00

- **Files:**
  - New `reactor/dbt_project/macros/app_date.sql`.
  - ebipolar_mh (43 CASEs), _social (lines 7, 73), _ap (lines 258-575), _psy_diag (263, 264, 277), _psy_diag_dsm5 (268, 269, 282), _psy_diag_sem (20-37), _patient (20, 31, 32, 42), _stop_suivi (8, 12), _trt_sem (32-48), _medicament_lt (9-52), _suicide (18), _suicide_sem (19).
  - SZ: eschizo_suicide (23), eschizo_patient (28), eschizo_stop_suivi (15).
- **Today:** The application stores 0000-00-00, or 1000-01-01 since its version of 2024-07-25 (A19). ebipolar_mh and _social drop only '^0000-'; the other models pass both. In face_bp_10, a placeholder in one form hides the date of the next form.
- **Change:**
  1. Macro: `CASE WHEN CAST({{ column_name }} AS VARCHAR) IN ('0000-00-00', '1000-01-01') THEN NULL ELSE {{ column_name }} END`.
  2. ebipolar_mh and _social: add `AND <col> <> '1000-01-01'` to each condition.
  3. Wrap each listed date with an explicit alias, for example `{{ app_date('date_atcdfampsy_mereddn') }} AS mere_BRTHDTC`. `_traitements` reads these output names.
  4. Not in ebipolar_medicament_psychotrope, where 0000-00-15 means 'running'.
- **Ships with:** none (R22 uses the macro).
- **Effect on the current files:** Full cell scan of BPALL, exact match.
  - 1000-01-01 is emptied on 63,181 cells in 134 columns: face_bp_14 52,411, face_bp_12 7,980, face_bp_10 1,240, face_bp_1 1,212, stprof_scdtc 176, isf05_qsdtc 162.
  - 0000-00-00 is emptied on 667,131 cells in 92 columns.
  - We already read both as missing.
- **Other cohorts:** SZALL: 136 and 7,561 cells. DR and ASP: none found.
- **Answers:** DEV-13.

### R20. Put centre C back in the DSM-5 diagnosis staging union

- **Files:** `models/staging/ebipolar/stg_ebipolar_psy_diag_psychiatriquedsm5.sql` lines 2-3 and 6-25. This rebuilds ebipolar_psy_diag_dsm5, face_bp_1 (ARM), face_bp_6, 10 and 11.
- **Today:** Centre C's source sits in a Jinja comment ('add after debug') since the first commit (2025-11-19). The other 58 staging models list 17 centres, and centre C's yml declares the table (213 columns).
- **Change:**
  1. Move the source into the relations list.
  2. Build the model alone. If the union fails on a type, add `column_override={'<column>': 'text'}`, as stg_edepression_autoq_psqi does.
  3. Check the counts: raw rows; rows per centre (17); centre C rows at V0.
  4. Before release, count the centre C patients not on the ARM list whose ARM changes or who enter BPALL through the wanted_diagnosis filter (extraction_bp.toml lines 43-44).
  5. Rebuild downstream.
- **Ships with:** none. Run M13 again afterwards.
- **Effect on the current files:**
  - Centre C V0 rows have 0 DSM5 labels. From 2022, 178 of 178 are unlabelled; 202 V0 visits have no tab-10 inclusion value.
  - From 2022, filled cells for centre C against the others: rad_tb_anx 0/178 against 995/1,341; nboccur_hospitalisation 0/178 against 967/1,341.
  - All 178 centre C patients from 2022 are on the ARM list.
  - Raw content: M12.
- **Other cohorts:** None; all other staging unions are complete.
- **Answers:** DEV-11, DM-6.

### R21. Deduplicate the two clean inputs of tab 6

- **Files:** `clean/ebipolar/ebipolar_comorbide.sql` (line 1, FROM at 310-311); `ebipolar_psy_diag.sql` (line 1, FROM at 337-338); optional `ebipolar_psy_diag_sem.sql`.
- **Today:** Neither model deduplicates, and face_bp_6 ends with `SELECT *`. So BPALL has 7 extra rows on 3 visits of centre C (2, 3 and 5 copies), identical on all 2,236 columns (md5 of each line).
- **Change:**
  1. `SELECT DISTINCT ON (USUBJID, VISITNUM)`, with `ORDER BY USUBJID, VISITNUM, <regex-guarded bigint cast of id_psy_troubles_comorbides or id_psy_diag_psychiatrique>` (the rule of R18).
  2. Optionally the same in _psy_diag_sem.
- **Ships with:** R100 (the guard must not ship first).
- **Effect on the current files:** 22,178 rows become 22,171. No other value changes.
- **Other cohorts:** 0 repeated keys in SZALL, DRALL and ASPALL.
- **Answers:** DEV-14.

### R22. Blank 2011-11-11 in the follow-up date of the first suicide attempt

- **Files:** `clean/ebipolar/ebipolar_suicide_sem.sql` line 19.
- **Today:** date_histts_date is not on the follow-up form (A20). It holds 2011-11-11 in centre A and 0000-00-00 elsewhere, and reaches ISF05_QSDTC on every follow-up.
- **Change:** `NULLIF({{ app_date('date_histts_date') }}, '2011-11-11') AS date_histts_date,`. Apply this to this column only: 13 cells of 5 other columns hold that date as a real date. B1 asks whether the follow-up branch of ISF05_QSDTC should also be emptied.
- **Ships with:** R19.
- **Effect on the current files:** Follow-up visits: 2011-11-11 is emptied on 1,142 (all centre A, 2011-2023); 0000-00-00 on 8,073; 60 real dates stay.
- **Other cohorts:** SZ has no 2011-11-11.
- **Answers:** DEV-13.

### R23. Height: keep the decimal point that the export removes

- **Files:** `clean/ebipolar/ebipolar_infirmier.sql` lines 82-83 and 114-130; optional data_qa column.yaml lines 90-96.
- **Today:** The plain-number branch runs `REGEXP_REPLACE(taille, '[^0-9]', '', 'g')`, so 172.5 becomes 1725. The form accepts decimals (help text example 170.5).
- **Change:**
  1. In CTE norm, add `REGEXP_REPLACE(REPLACE(REPLACE(LOWER(COALESCE(taille,'')), ',', '.'), ';', '.'), '[^0-9.]', '', 'g') AS height_clean`.
  2. After the '1m80' branch, add `WHEN height_clean ~ '^[0-9]+[.][0-9]+$' THEN CAST(height_clean AS DOUBLE PRECISION)`. Keep the other branches.
  3. Run test_trino_port.py and test_bp_label_mappings.py.
  4. Optional: the data_qa rule for height >= 1000 becomes obsolete for BP.
- **Ships with:** Nothing in dataflow. Tell us the first extraction that carries it: a height typed in metres would arrive as 1.72, and our reader needs a metre unit first.
- **Effect on the current files:**
  - 182 of 16,496 heights change: 180 four-digit values become value/10 (178 end in 5), and 2 five-digit values become value/100. The range becomes 148.5-185.5.
  - Centres: E 89, D 42, B 11, C 10, others 30.
  - The stored BMI matches the decimal reading on 180 of the 182 (weight/(h/1000)^2 within 0.051), and the delivered value on none.
  - Of 15,982 checkable heights, 0 fit metres. 332 heights without a BMI cannot be checked (M36).
- **Other cohorts:** SZ keeps a point but loses a comma; no SZ height is 1000 or more. DR: R25. ASP: correct.
- **Answers:** DM-5.

### R24. ECG heart rate, RR, QT and QTc: blank the impossible zeros

- **Files:** `ebipolar_infirmier.sql` lines 190-226; DR `edepression_infirmier.sql` 78-92; SZ `eschizo_infirmier.sql` 113-121.
- **Today:** A raw 0 passes the regex. The zeros come from the 2009-2011 forms (A22).
- **Change:** Wrap each cast once: `NULLIF(CAST(CASE ... END AS DOUBLE PRECISION), 0) AS EGHRMN`, and the same for RR, QTC and QT, the 4 DR columns and the SZ QTC.
- **Ships with:** none.
- **Effect on the current files:** 137 cells on 90 visits: eghrmn 20, rr 27, qtc 27, qt 63, almost all up to 2012. We already treat 0 as not recorded.
- **Other cohorts:** DR: rr 23 and qtc 23 at DR centre M. SZ and ASP: 0.
- **Answers:** DEV-13.

### R25. DR nurse form: a decimal comma would stop the build

- **Files:** `edepression_infirmier.sql` lines 45, 48, 51, 54, 57, 60, 63, 66, 69, 75, 79.
- **Today:** 11 branches accept '[,.]' and then `CAST(x AS double precision)` fails on a comma.
- **Change:** Use `CAST(REPLACE(x, ',', '.') AS double precision)` in the 11 branches.
- **Ships with:** none.
- **Effect on the current files:** none (0 commas today).
- **Other cohorts:** ASP already replaces the comma.
- **Answers:** none.

**Biology**

### R26. BP: build the LDL unit label from the unit chosen on the form

- **Files:** `clean/ebipolar/ebipolar_lb.sql` lines 94-104.
- **Today:** LDL_LBORRESU never reads rad_chol_hll and defaults to 'mmol/L'. HDL and 8 other analytes do read their choice.
- **Change:** Before `ELSE 'mmol/L'` (line 103), add the HDL branch: `WHEN rad_chol_hll IS NOT NULL AND LENGTH(TRIM(rad_chol_hll)) > 0 THEN CASE WHEN LOWER(TRIM(rad_chol_hll)) IN ('g/l', 'g') THEN 'g/L' ELSE TRIM(rad_chol_hll) END`.
- **Ships with:** one commit with R28, R29 and R30 (the same unit CASEs), applied in the order R29, R26, R28, R30.
- **Effect on the current files:** 245 results chosen as g/L change from 'mmol/L' to 'g/L' (230 of them from 2022; most in F 69 and A 47). 3,037, 9,543 and 32 others are unchanged. 18 visits have a choice but no value. We read rad_chol_hll first, so nothing we deliver changes.
- **Other cohorts:** SZ: R27. DR copies its choice.
- **Answers:** DM-1, DEV-13.

### R27. SZ: build the LDL unit label from the unit chosen on the form

- **Files:** `clean/eschizo/eschizo_lb.sql` lines 37-41.
- **Today:** rad_chol_ldl is selected (line 149) but ignored. LDL is the only eSchizo choice that is not read.
- **Change:** Before line 40, add `WHEN staging.rad_chol_ldl IS NOT NULL AND LENGTH(TRIM(staging.rad_chol_ldl)) > 0 THEN TRIM(staging.rad_chol_ldl)`.
- **Ships with:** none.
- **Effect on the current files:** 3,528 of 3,530 LDL results are labelled mmol/L. A g/L choice changes a delivered value only between 0.8 and 2.6: at most 1,201 results (M31).
- **Other cohorts:** BP: R26.
- **Answers:** DM-1.

### R28. Write no unit label where there is no result

- **Files:** `ebipolar_lb.sql` (43 CASEs, lines 15-387); `eschizo_lb.sql` (16 CASEs); `edepression_lb.sql` (39 CASEs and 9 copied units at lines 98, 113, 115, 117, 119, 127, 129, 214, 274); optional `easperger_lb.sql` (31, 36, 38, 45, 57).
- **Today:** 96,110 BP label cells sit next to an empty value: 95,145 defaults, 598 chosen units, 367 words (252 'NaN', 28 'Unknown', 87 others).
- **Change:** A result that has a value but no chosen unit keeps its default label (with R29's corrections). Only labels with no value go:
  1. Add a first branch `WHEN SUBSTRING(<raw> FROM '[0-9]') IS NULL THEN NULL` to each BP unit CASE. This is exactly the condition under which the value is NULL.
  2. hCG: also require `SUBSTRING(bhcg FROM '[a-zA-Zµ/%]') IS NULL`, to keep qualitative words.
  3. Clearance with R30: test the R30 extraction with NULLIF '0'.
  4. SZ: the same branch in the 16 defaulted CASEs (not VITD, TGNIGMAB, HCG), only with R67.
  5. DR: the same in the 39 CASEs, and wrap the 9 copied units in `CASE WHEN SUBSTRING(<raw> FROM '[0-9]') IS NULL THEN NULL ELSE <unit> END`.
  6. ASP: optional wrapper.
- **Ships with:** BP: one commit with R26, R29 and R30, applied in the order R29, R26, R28, R30. SZ step: R67.
- **Effect on the current files:** BP: 96,085 labels are emptied, 25 hCG words stay, 0 result labels change. SZ: 10,068 cells. DR: up to 7,159. ASP: 7. We already blank labels without values.
- **Other cohorts:** included.
- **Answers:** DEV-13, DM-1.

### R29. Correct the wrong default labels of TSH, MCH and prolactin, and the haemoglobin 'g/l' mapping

- **Files:** `ebipolar_lb.sql` lines 169, 176, 180, 201, 206, 233-234, 364, 386; data_qa `units.yaml` 122-133, `values.yaml` line 2217, `DATA-QA.md` 673-680; `edepression_lb.sql` 177, 258; `eschizo_lb.sql` 126.
- **Today:**
  - The TSH default 'µUI/L' is 1,000 times off: the form offers microUI/ml and mUI/L.
  - The MCH default '%' should be pg.
  - The prolactin default 'mg/L' is impossible.
  - A typed haemoglobin 'g/l' is relabelled 'g/dL'.
  - The optional data_qa pass makes µUI/L canonical.
- **Change:** Default labels stay; the wrong ones are corrected.
  1. TSH: line 180 becomes `ELSE 'mUI/L'`; lines 169 and 176 become 'microUI/ml'; data_qa canonical `mUI/L`, with `{"µUI/L": 1.0, "microUI/ml": 1.0}`.
  2. MCH: line 234 becomes `ELSE 'pg'`; line 233 normalises 'Pg' to 'pg'.
  3. Prolactin: line 386 becomes `ELSE NULL`.
  4. Haemoglobin: line 201 splits 'g/%' (g/dL) from 'g/l' (g/L), and the same at line 206. values.yaml gets a new G_PER_L cluster.
  5. Optional: normalise the MCHC choice spelling at line 364.
  6. DR: line 177 becomes 'mUI/L' and line 258 'pg'.
  7. SZ: line 126 becomes NULL, only with R67.
- **Ships with:** BP: one commit with R26, R28 and R30, applied in the order R29, R26, R28, R30. SZ step: R67.
- **Effect on the current files:**
  - TSH: up to 8,706 labels change (8,656 values under 10).
  - MCH: 7,329 change, plus 3,199 'Pg'.
  - Prolactin: up to 4,387.
  - Haemoglobin: at most 476.
  - DR: 1,162 TSH, 1,076 MCH. SZ: up to 1,818 prolactin.
  - Nothing we deliver changes.
- **Other cohorts:** included.
- **Answers:** DEV-13.

### R30. Creatinine clearance: blank the 0 written by the script

- **Files:** `ebipolar_lb.sql` line 273.
- **Today:** The script writes 0 when the weight is not yet saved (A21), and the export keeps it.
- **Change:** Wrap the extracted value: `CASE WHEN <extraction> ~ '^0+(\.0+)?$' THEN NULL ELSE <extraction> END AS CREATCLR_LBSTRESC`. The extraction is today's `REPLACE(REPLACE(TRIM(SUBSTRING(creatinine_clairance FROM '([<>]?[0-9]+(?:\s*[.,]\s*[0-9]+)?)')), ' ', ''), ',', '.')`.
- **Ships with:** one commit with R26, R28 and R29, applied in the order R29, R26, R28, R30.
- **Effect on the current files:** 246 cells, 2021-2026. We already read 0 as not recorded.
- **Other cohorts:** none.
- **Answers:** DEV-13.

### R31. DR: read the unit chosen for TSH, free T3 and free T4

- **Files:** `edepression_lb.sql` lines 173-191 (choices at 99 and 309-310).
- **Today:** All DR thyroid labels are defaults (1,162 TSH, 1,124 T3, 1,131 T4). A result chosen as pg/mL is delivered as pmol/L: 1.536 times (T3) and 1.287 times (T4) too low.
- **Change:** Wait for M32 (the option codes).
  1. Before each ELSE, add `WHEN NULLIF(TRIM(t3libre_unit), '') IS NOT NULL THEN CASE TRIM(t3libre_unit) WHEN '<code>' THEN '<label>' ... ELSE TRIM(t3libre_unit) END`, and the same for t4libre_unit and tsh_unit.
  2. If the codes cannot be mapped, export the three fields instead (face_dr_9 SELECT and yml, plus the thesaurus tick or the TOML).
- **Ships with:** R29.
- **Effect on the current files:** Not measurable (M32).
- **Other cohorts:** none.
- **Answers:** DM-1.

**Perinatal and family**

### R32. Perinatal measures and parental ages: blank the zeros of the 2009-2010 forms

- **Files:** `ebipolar_mh.sql` lines 10-133; DR `edepression_mh.sql` 13-40; SZ `eschizo_mh.sql` 15-16 and 27-75.
- **Today:** The application's 2009-2010 forms stored 0 for an unknown measure (A22). The export passes it: a raw 0 is kept, and a weight of 0 becomes 0 g. The export's data-QA config already lists agemere, agepere, brthwt, brthht, brthcirc and gstabrth as columns where 0 means unknown, but that pass did not run for BPALL (see R101). This is hardening, low priority.
- **Change:** Wrap the final expression of AGEMERE, AGEPERE, GSTABRTH, BRTHWT, BRTHHT, BRTHCIRC, APGR0106_1min and APGR0106_5min in `NULLIF(..., 0)`. Do the same in eschizo_mh (AGEMERE, AGEPERE, POIDSNA) and edepression_mh (the same 8 columns). R33 rewrites the texts that the Trino override `_mh` matches (`'kg', ''` with its newline, and the `REGEXP_REPLACE(REPLACE(LOWER(peri_naisstaille)...` pair): update `_mh` as R33 step 7 says, and run test_trino_port.py.
- **Ships with:** R33 (same lines, one commit).
- **Effect on the current files:** BP 289 cells: 272 birth-measure cells on 67 visits (weight 35, length 54, head 66, Apgar 1 min 58, Apgar 5 min 59), 61 of the visits up to 2012; agemere 7, agepere 9, gstabrth 1. 58 of the 59 five-minute Apgar zeros come with a one-minute zero. We already read 0 as not recorded.
- **Other cohorts:** DR 43 cells on 8 visits (2014-2021); SZ 4 (agemere 2, agepere 2); ASP 0.
- **Answers:** DEV-13.

### R33. Perinatal texts: stop turning some typed answers into wrong numbers

- **Files:** `ebipolar_mh.sql` lines 10-11 (ages), 18 (GSTABRTH), 31-47 and 69-73 (weight), 84-85 and 96-97 (length, head), 107-114 and 124-131 (Apgar); `eschizo_mh.sql` 15-16 (ages) and 27-75 (weight); `face_bp_9_perinatalite.yml` line 47; `trino_overrides.py` `_mh`.
- **Today:**
  - Apgar: 'a/b' gives (a+b)/2, so '8/10' becomes 9. '<7' becomes 7.
  - Weight: 'a kg b' gives a x 1000 + b, so '3kg5' becomes 3005. A decimal with no unit is read as kilograms, so '3250.5' would become 3,250,500. The kg branch (lines 43-47) does not strip a leading '<' or '>' before its cast, so '<3kg' would stop the build.
  - Ages keep every digit: '30-35' would become 3035.
  - GSTABRTH keeps the first number of any text: '8 mois 1/2' gives 8.
  - Length and head: '49,5cm' gives NULL.
  - The yml labels prembrth 'Nombre de naissance'; the form and the dictionary say 'Naissance' (the term of birth).
  - The application's form checks block units in all these fields except the Apgar scores (A44), since at least 2024-01. So new entries reach only the Apgar rule. This is low priority.
- **Change:**
  1. Length and head: with `n = REPLACE(REPLACE(LOWER(x), ' ', ''), ',', '.')`, use `WHEN n ~ '^\d+(\.\d+)?\D*$' THEN SUBSTRING(n FROM '^\d+(?:\.\d+)?')::double precision`. Do not combine the wider pattern with today's '[^0-9]' stripping: '49,5cm' would become 495.
  2. Apgar: read 'a/b' only as a score out of 10: `WHEN x ~ '^\s*\d{1,2}\s*/\s*10\s*$' THEN SPLIT_PART(x, '/', 1)::double precision`, when that part is 10 or less. Any other fraction gives NULL, because in the 5-minute field 'a/b' can be the pair of scores at 1 and 5 minutes. '<n' gives NULL.
  3. Ages: return NULL when `LOWER(x) ~ '\d\D+\d'` (two numbers, or a decimal); otherwise keep today's expression. A stricter pattern would drop answers read correctly today, such as '30 Ans', and the SZ code 999.
  4. GSTABRTH: return NULL when the text holds two numbers that are not one decimal (`x ~ '\d[^0-9.,]+\d'`); otherwise keep today's expression.
  5. Weight: in the kg-g branch use `\1 * 1000 + RPAD(\2, 3, '0')::int`; limit the decimal-without-unit branch to one-digit kilograms (`'^\d\.\d+$'`), anything else NULL; strip `'^[<>]+'` in the kg branch's value, as its test already does. Apply the same weight and age changes to eschizo_mh.
  6. yml: prembrth 'Terme de la naissance'.
  7. Update `_mh` if the texts it rewrites change, and run test_trino_port.py.
- **Ships with:** R32 (same lines, one commit).
- **Effect on the current files:** No change can be shown in BPALL. Possible: 1 weight of the form x00y (2016-18), and 3 weights between 20,000 and 60,000 g that are exact multiples of 1,000 (up to 2015), which fit a two-digit entry read as kilograms. Those 3 are out of range and we already read them as missing.
- **Other cohorts:** SZ: same age and weight rules. DR and ASP accept plain digits only.
- **Answers:** none.

### R34. Write '>5' daughters, sons, sisters or brothers as 6

- **Files:** `ebipolar_ap.sql` lines 44-47, 52-55, 60-63, 68-71; `face_bp_14_antecedents.yml` lines 1255, 1409, 1563, 1717; SZ `eschizo_ap.sql` 25-52 and `face_sz_13_antecedents.yml`.
- **Today:** The count CASE has no ELSE, so '>5' becomes NULL.
- **Change:** Add `WHEN rad_structure_<x> = '>5' THEN 6` to the four count CASEs (not the _atteint ones). Document '6 = plus de 5'. The same in SZ. The form offers 0 to 5 and '>5', so 6 can be told from 5.
- **Ships with:** Nothing in dataflow. Tell us the first extraction that carries it: our reader must read 6 as 'more than 5', not as six.
- **Effect on the current files:** At least 49 BP patients on 55 visits (count empty, affected count filled; visits: sisters 21, brothers 33, sons 1; patients: 19, 31, 1). SZ: 18 patients on 23 visit-by-type rows (19 distinct visits; sisters 12 patients, brothers 10, daughters and sons 0): the extraction holds no '>5' token in either cohort, so 5 is exactly five and these counts are lost.
- **Other cohorts:** DR and ASP: none.
- **Answers:** DM-14.

**Social**

### R35. BP empjob: export the job class label of the form

- **Files:** `ebipolar_social.sql` lines 62-72; `face_bp_15_social.sql` line 39 (comment); `face_bp_15_social.yml` lines 86-91; thesaurus SOCIAL EMPJOB.
- **Today:**
  - A '=' CASE over 9 dictionary labels reads a field that stores 18 INSEE level-2 labels.
  - Only 'Agriculteur exploitant' and 'Employé de commerce' match. The 'Profession intermédiaire de l'enseignement...' label fails on its backslash.
  - The yml names the column empjob_bilansocial.
- **Change:**
  1. Replace the CASE with `NULLIF({{ unescape_apostrophe('rad_social_stprof_class') }}, '') AS EMPJOB,`.
  2. Comment line 39 with what EMPJOB and EMPJOB_Psytaitement hold.
  3. Rename the yml entry to empjob, and list the 18 labels (as on the form, including 'Ouvrier non qualifiés').
  4. Set the thesaurus CODAGE the same way.
  5. After the run, check rows per (usubjid, visitnum).
- **Ships with:** one commit with the other ebipolar_social requests (R36, R38-R42, R74); R45 (SZ, same labels).
- **Effect on the current files:** 122 V0 cells move from codes to labels (12 '1', 110 '5'). Other classes come back, at most 2,308 employed V0 visits; jobclas is filled on 2,177 of them.
- **Other cohorts:** SZ: R45. DR and ASP use codes.
- **Answers:** FU-8.

### R36. BP: export the class of the last job

- **Files:** `ebipolar_social.sql` after line 73; `face_bp_15_social.sql` after line 21; yml lines 104-109; thesaurus SOCIAL.
- **Today:** rad_social_stprof_classlast (asked when stprof = Sans emploi, 18 labels) is not selected. The yml documents a column that does not exist.
- **Change:**
  1. Add `NULLIF({{ unescape_apostrophe('rad_social_stprof_classlast') }}, '') AS EMPJOB_LAST,` and select it in face_bp_15.
  2. Name the yml entry empjob_last.
  3. Add a thesaurus row (SC, visite initiale; tick on the thesaurus path).
- **Ships with:** one commit with R35, R38-R42 and R74 (same model). Same name as SZ in R45.
- **Effect on the current files:** A new column, asked of 1,049 V0 visits with stprof 0.
- **Other cohorts:** SZ in R45.
- **Answers:** FU-8.

### R37. BP empjob_psytaitement: remove the backslash and correct the dictionary source

- **Files:** `ebipolar_trt_sem.sql` line 78; yml lines 93-95; thesaurus SOCIAL EMPJOB_Psytaitement.
- **Today:** The value is exported with backslashes. The dictionary gives rad_social_stprof_classlast (the inclusion question on the last job) as its source, but the export reads rad_social_stprof_class of the follow-up form (face_bp_15_social.sql line 20). That follow-up question is asked only after a change of work status, when the new status is 'Actif'.
- **Change:**
  1. `NULLIF({{ unescape_apostrophe('rad_social_stprof_class') }}, '') AS EMPJOB_Psytaitement`.
  2. Thesaurus source: psy_traitement_semestriel.rad_social_stprof_class, with a label, the 18 labels, follow-up visits.
  3. Add the same yml description.
  4. Optional: drop the unused migration map.
- **Ships with:** R44 (the status that says when the class is asked).
- **Effect on the current files:** 72 of 219 cells lose the backslash. We already handle it.
- **Other cohorts:** SZ: R44.
- **Answers:** DM-7.

### R38. BP stprof: code the students as 3 and leave unanswered statuses empty

- **Files:** `ebipolar_social.sql` lines 42 and 46; yml; thesaurus STPROF.
- **Today:** The CASE tests 'Étudiant', but the form stores 'Etudiant'. `ELSE 6` sends students and blanks to 'Autres'.
- **Change:**
  1. Line 42: `IN ('Etudiant', 'Étudiant') THEN 3`.
  2. Line 46: `ELSE NULL`. The enum is fully listed above.
  3. Document 'vide = non renseigné'.
  4. Optional: an accepted_values test on rad_social_stprof.
- **Ships with:** one commit with R35, R36, R39-R42 and R74 (same model). The migration map already has 3 = Étudiant. Tell us the first extraction that carries it: our reader maps the stprof codes.
- **Effect on the current files:** The 1,150 V0 cells in code 6 split into 3, 6 and empty; at least 7 become empty (every other social answer empty). Code 6 has a median age of 30.3 and 39% under 25.
- **Other cohorts:** SZ is correct.
- **Answers:** DM-13.

### R39. BP saltyp: remove the dead label branches, correct the coding, give the migration a BP map

- **Files:** `ebipolar_social.sql` lines 109-119; yml line 151; thesaurus SALTYP; `nucleus/nucleus/migration/config/encoding_casting_rules.yaml` 99-107, `migration/cli.py` 294, `config/pathologies.yaml`.
- **Today:**
  - The field is enum('1'..'7'), so the label branches never run.
  - The yml, the dictionary and the shared migration map say 7 = Absence de revenus; on the BP form, 7 = Autres and 5 = Allocations de chômage.
  - The dictionary misnames the field.
- **Change:**
  1. `CASE WHEN radhtml_social_stprof_revenus ~ '^[1-7]$' THEN radhtml_social_stprof_revenus::integer END AS SALTYP`.
  2. Coding: 1 Salaire, 2 RMI/RSA, 3 AAH, 4 Pension d'invalidité, 5 Allocations de chômage, 6 APL, 7 Autres. Thesaurus name: radhtml_social_stprof_revenus.
  3. Add a BP override map, merged by cli.py over the shared one (SZ keeps its map).
- **Ships with:** one commit with R35, R36, R38, R40-R42 and R74 (same model).
- **Effect on the current files:** BPALL is unchanged. Up to 1,071 migration rows change from 'Absence de revenus' to 'Autres'.
- **Other cohorts:** SZ: R46.
- **Answers:** DM-7.

### R40. Give 'Curatelle renforcée' its own protection code

- **Files:** `ebipolar_social.sql` lines 50-56; `face_bp_15_social.yml`.
- **Today:** The third answer falls to `ELSE NULL`, so it is empty in social_protec and protec.
- **Change:**
  1. Add `WHEN rad_social_protec = 'Curatelle renforcée' THEN 4`.
  2. Document '4 = curatelle renforcée'.
  3. The PROTEC 3 filter of face_bp_1_patients is unchanged: code 4 passes it, as NULL does today.
- **Ships with:** one commit with R35, R36, R38, R39, R41, R42 and R74 (same model). Tell us the first extraction that carries it: our reader maps the protec codes.
- **Effect on the current files:** At most 187 patients go from empty to 4 (empty social_protec but stprof filled; C 85, A 21, E 17).
- **Other cohorts:** SZ, DR and ASP: not exported, or no such answer (not checked again).
- **Answers:** DM-7.

### R41. BP age at first job: keep the answers '<15' and '>60'

- **Files:** `ebipolar_social.sql` line 74; `face_bp_15_social.yml` (profage); thesaurus SOCIAL PROFAGE.
- **Today:** The form offers 'Ne sais pas', '<15', 15 to 60 and '>60'. Line 74 keeps only the digits and casts to integer, so '<15' becomes 15, '>60' becomes 60 and 'Ne sais pas' becomes empty. The SZ export keeps the text (eschizo_social.sql lines 81-84).
- **Change:** `NULLIF(NULLIF(rad_social_prof_age, ''), 'Ne sais pas') AS PROFAGE,` (text: '<15', '15' to '60', '>60'). The yml already declares character varying, and the data-QA cast rules already list profage as a string. Describe the coding in the yml and the dictionary.
- **Ships with:** one commit with R35, R36, R38-R40, R42 and R74 (same model). Tell us the first extraction that carries it: our reader must read the column as a censored number.
- **Effect on the current files:** Up to 182 inclusions now at 15 can become '<15'. 3 inclusions read 60; they belong to patients aged 30 to 45 at inclusion, so they are entry errors whatever was stored. No other model reads PROFAGE.
- **Other cohorts:** SZ already keeps the text.
- **Answers:** none.

### R42. BP household size and work durations: do not run two numbers together

- **Files:** `ebipolar_social.sql` lines 76-104 (PROFDUR, DURTOT) and 108 (NBPERS); yml; thesaurus SOCIAL.
- **Today:**
  - NBPERS keeps every digit of a free-text answer (varchar(50), no check on the form), so '2 ou 3' gives 23.
  - PROFDUR and DURTOT: the ELSE branch (lines 88 and 103) keeps only digits and points. It drops the '<' or '>' that the form's check allows, and runs two numbers together ('5 à 10' gives 510). The 'mois' branch (lines 84-85) divides all the digits by 12, so '2 ans 3 mois' gives 23/12.
  - The form's checks run in the browser only; the check at submit is commented out (verifications.php line 280).
- **Change:**
  1. NBPERS: `CASE WHEN social_vie_nbpers ~ '^\D*\d{1,2}\D*$' THEN SUBSTRING(social_vie_nbpers FROM '\d+')::int END`. An answer like '3 personnes' stays 3; an answer with two numbers becomes empty.
  2. PROFDUR and DURTOT: apply the same one-number rule in the ELSE branch; read 'N an(s) M mois' as N + M/12 before the 'mois' branch; keep a leading '<' or '>' (the columns then become text, as PROFAGE in R41).
  3. If M48 shows many texts that fail the rule, add the raw texts as companion columns.
- **Ships with:** one commit with R35, R36, R38-R41 and R74 (same model). Tell us the first extraction that carries it.
- **Effect on the current files:** Out of range today: 5 household sizes (23 to 100; 1 is a patient living in an institution, where a large count may be true) and 5 durations (longest job 78; total 61, 67, 510 and 2,223). 510 and 2,223 fit two numbers run together. Other cases cannot be counted from the file (M48).
- **Other cohorts:** SZ has none of these three columns. DR (edepression_bilan_social.sql lines 29-41) keeps plain digits only, so its decimals and '<' become empty.
- **Answers:** none.

### R43. BP: export the date of the social assessment

- **Files:** `face_bp_15_social.sql` after line 10; `face_bp_15_social.yml`; thesaurus SOCIAL.
- **Today:** ebipolar_social selects date_bilan_social ('Date de recueil des informations', a required field; line 7), but face_bp_15 does not export it. The tab carries the visit date only.
- **Change:** Add `social_bilan_social.date_bilan_social AS DATE_BILAN_SOCIAL,`, a yml entry and a dictionary row. Line 7 already blanks '0000-' dates; R19 blanks '1000-01-01'.
- **Ships with:** R19.
- **Effect on the current files:** A new column on visits with a social form.
- **Other cohorts:** not checked.
- **Answers:** none.

### R44. Follow-up work status (BP) and follow-up job class (SZ)

- **Files:** `ebipolar_trt_sem.sql` lines 75-77; `face_bp_15_social.sql` after line 20; yml; thesaurus; `face_sz_12_social_perinatalite.sql`; SZ yml and thesaurus.
- **Today:** ebipolar_trt_sem selects rad_changement_statut, rad_statut_actuel and statut_actuel_autre (lines 75-77), and face_bp_15 exports none of them. The follow-up job class (R37) is asked only after a change of status and a current status 'Actif', so its 219 cells have no denominator: an empty cell does not say that the patient does not work. The SZ follow-up fields of eschizo_trt_sem are not exported.
- **Change:**
  1. BP: add `NULLIF(rad_changement_statut, '') AS STPROF_CHANGE_Psytaitement` (exported as stored), and `CASE WHEN rad_statut_actuel = 'Sans emploi' THEN 0 WHEN rad_statut_actuel = 'Actif' THEN 1 WHEN rad_statut_actuel = 'Retraité' THEN 2 WHEN rad_statut_actuel IN ('Etudiant', 'Étudiant') THEN 3 WHEN rad_statut_actuel = 'Pension' THEN 4 WHEN rad_statut_actuel = 'Au foyer' THEN 5 WHEN rad_statut_actuel = 'Autres' THEN 6 END AS STPROF_Psytaitement`. Select both in face_bp_15. Add yml entries and thesaurus rows. Do not export the free text statut_actuel_autre.
  2. SZ: join eschizo_trt_sem in face_sz_12 and select `NULLIF({{ unescape_apostrophe('psy_traitement_semestriel_sz.rad_social_stprof_actifclasse') }}, '') AS EMPJOB_Psytaitement`, with the status fields under the BP names, coded like SZ STPROF.
- **Ships with:** none.
- **Effect on the current files:** BP: 2 new follow-up columns (2,453 follow-up visits with the form from 2022; 219 with a job class).
- **Other cohorts:** SZ socio_demog_semestriel is not exported either.
- **Answers:** none.

### R45. SZ empjob: export the job class labels of the old social form

- **Files:** `eschizo_social.sql` lines 69-80; `face_sz_12_social_perinatalite.sql` after line 20; yml lines 48-51; FACESZ thesaurus.
- **Today:** The same 9-label lookup, with LIKE. Only '%Employé de commerce%' occurs in the data. '%Ouvriers%' and '%Retraités%' belong to rad_social_classe. The last-job field is not selected, and the dictionary names a socio_demog code as the source.
- **Change:** EMPJOB holds the 18 labels of the old form, as in BP; the socio_demog INSEE code gets its own column (R48).
  1. `NULLIF({{ unescape_apostrophe('staging.rad_social_stprof_actifclasse') }}, '') AS EMPJOB` and `NULLIF({{ unescape_apostrophe('staging.rad_social_stprof_inactif_dernclasse') }}, '') AS EMPJOB_LAST`. Select them in face_sz_12.
  2. Add `NULLIF(staging.rad_social_classe, '') AS EMPJOB_GROUP` only if M30 shows that it is filled.
  3. Add yml entries and thesaurus rows (tick, or companion_columns, on the thesaurus path).
  4. More filled columns can change which duplicate face_sz_12's DISTINCT ON keeps (lines 46-61).
- **Ships with:** R35, R36, R48.
- **Effect on the current files:** 41 V0 cells hold '5' (21 employed). They become labels, and other labels come back, at most 236 employed plus answering non-employed patients.
- **Other cohorts:** BP: R35.
- **Answers:** SZ O2.

### R46. SZ saltyp: export the ticked income labels

- **Files:** `eschizo_social.sql` lines 85-95; yml lines 57-61; FACESZ thesaurus SALTYP.
- **Today:** The field is a multi-answer SET. Line 87 tests 'Salarié'. Line 90 tests an unescaped apostrophe. A multi-answer cell keeps one code, chosen by the CASE order.
- **Change:** `NULLIF({{ unescape_apostrophe('staging.chk_social_revenus_type') }}, '') AS SALTYP` (the ticked labels as stored; the type becomes text). Document it.
- **Ships with:** R48. Tell us the first extraction that carries it: our reader maps the SALTYP codes.
- **Effect on the current files:** V0: codes 1 and 4 are absent today; 1,253 empty. 162 of 236 employed visits are empty.
- **Other cohorts:** BP: R39.
- **Answers:** SZ O22.

### R47. SZ maristat: match the SZ label of 'married or living as a couple'

- **Files:** `eschizo_social.sql` line 15.
- **Today:** `LIKE '%Marié / Concubin / Pacsé%'` misses the SZ label, so code 2 never appears.
- **Change:** `WHEN staging.rad_social_marital LIKE 'Marié%' THEN 2`.
- **Ships with:** none.
- **Effect on the current files:** Code 2 goes from 0 to at most 253 V0 visits (housing filled and maristat empty).
- **Other cohorts:** BP is correct (2,413).
- **Answers:** SZ O22.

### R48. SZ: export the socio_demog form in its own columns

- **Files:** new `clean/eschizo/eschizo_socio_demog.sql`; `face_sz_12_social_perinatalite.sql`; yml; thesaurus.
- **Today:** stg_eschizo_socio_demog exists but is not read. The dictionary sources STPROF, EMPJOB and SALTYP from it, and the form script hides the old fields in its favour.
- **Change:**
  1. The clean model selects id, USUBJID, VISITNUM, date_saisie, fondacode, `rad_sociodemog_nf`, `NULLIF(radhtml_social_stprof,'') AS STPROF_SD`, `NULLIF(social_stprof_actifclasse,'') AS EMPJOB_INSEE`, `NULLIF(chkhtml_social_revenus_type,'') AS SALTYP_SD` and centre.
  2. LEFT JOIN it in face_sz_12 on visitnum and USUBJID.
  3. Document the code lists, one thesaurus row per column.
- **Ships with:** R45, R46.
- **Effect on the current files:** New columns. 626 of 1,972 SZ V0 visits with housing filled have no old-form status (445 of 505 in 2016-18).
- **Other cohorts:** SZ only.
- **Answers:** SZ O23.

**Self-questionnaires and treatments**

### R49. PSQI02: read 'H:MM' as minutes:seconds above 4 hours, and as empty at hours 21 to 24

- **Files:** `ebipolar_autoq_psqi.sql` lines 43-98; SZ `eschizo_autoq_psqi.sql` lines 30-50.
- **Today:**
  - Any 'H:MM' becomes H x 60 + M: '30:00' gives 1800, and the bedtime '22:30' gives 1350.
  - The '00:30' and '24:xx' branches can never run.
  - 'XhYY' is read the same way.
  - An unanchored 'mn' branch turns '5-15m' into 515.
  - psqi14 and psqi_ follow from this value.
- **Change:**
  1. Replace lines 44-53, in this order:
     - 'H:MM' with H from 21 to 24 gives NULL;
     - H x 60 + M <= 240 gives that value;
     - `'^[0-9]{1,2}:00$'` gives H;
     - other 'H:MM' gives `ROUND(H + M/60, 1)`.
  2. Before line 56, add 'Nh' with N from 21 to 24 gives NULL.
  3. Move the range branch above 'mn', with the pattern `'^[0-9]+\s*[/-]\s*[0-9]+\s*[a-zA-Z]*$'`, giving the mean of the two numbers.
  4. The same rules in SZ.
- **Ships with:** none.
- **Effect on the current files:** Upper bounds: psqi02 changes on 362 visits (273 read as minutes, 89 emptied), psqi14 on 258 (89 emptied), psqi_ on 256 (88 emptied). M22 gives the raw split.
- **Other cohorts:** SZ: 16 values above 240. DR: 1. ASP: 0.
- **Answers:** DEV-14.

### R50. BP EQ-5D clean model: keep the minus sign of the index

- **Files:** `ebipolar_hetero_eq5d.sql` line 30.
- **Today:** The regex captures from the first digit, so it drops the minus sign. The score step hides this by rewriting eq5d_.
- **Change:** Use the pattern `'^.*?(-?[0-9]+([,\.][0-9]+)?).*$'`. Optional: cast only text that matches `'^-?[0-9]+(\.[0-9]+)?$'`, because a value with no digit would fail the CAST.
- **Ships with:** R51.
- **Effect on the current files:** None while the step runs. Up to 153 negative profiles. hubdashboard face_bp_all reads this model directly.
- **Other cohorts:** ASP: R51.
- **Answers:** DM-13.

### R51. ASP EQ-5D: keep negative indices instead of NULL

- **Files:** `easperger_aut_eq5d.sql` line 43.
- **Today:** `'^[0-9]+(\.[0-9]+)?$'` sends negative indices to NULL, and no step restores them.
- **Change:** Use `'^-?[0-9]+(\.[0-9]+)?$'`.
- **Ships with:** R50.
- **Effect on the current files:** Up to 11 V0 visits gain a negative index (the profile is negative and the index empty). 0 negative indices are stored today.
- **Other cohorts:** SZ keeps the sign. DR has no index.
- **Answers:** DM-13.

### R52. MAThyS slider table: count its rows before any model is built

- **Files:** source ymls `raw_ebipolar_<centre>.yml` (autoq_mathys_slide); if rows exist: new `stg_ebipolar_autoq_mathys_slide.sql`, `ebipolar_autoq_mathys.sql`, face_bp_2 and its yml, thesaurus.
- **Today:** The table is declared in every centre and read by no model (A13). MAThyS cover is 80% of visits with ASRM answers, against 59% in centre C from 2021 and 50% in centre J in 2016-2020.
- **Change:** Wait for M21.
  1. If empty everywhere, close.
  2. Otherwise:
     - union the 17 centres in staging;
     - in the clean model, union typed and slider rows before the DISTINCT ON, with `ORDER BY USUBJID, VISITNUM, CASE WHEN mathys_form = 'typed' THEN 0 ELSE 1 END, CASE WHEN <id> ~ '^[0-9]+$' THEN CAST(<id> AS bigint) END` (typed first, then the lowest id, as in R18; `<id>` holds each row's raw id);
     - map slider items to MATHYS01-20 with an explicit rule for '' (an unmoved slider is stored empty);
     - add mathys_form ('typed' or 'slider'), exported and ticked ('typed' for DR);
     - the score step then scores slider rows as it scores typed rows; R85 sets the rule per form.
- **Ships with:** after R18 (same model).
- **Effect on the current files:** Unknown until M21.
- **Other cohorts:** DR has no slider table.
- **Answers:** DM-12.

### R53. Correct two manual ATC codes and apply the manual map only where the seed gave none

- **Files:** `ebipolar_medicament_psychotrope.sql` lines 29-174 (52, 124).
- **Today:** The manual map overrides the seed on every row. It gives CITALOPRAM N06AB10 and PAROXETINE N06AB03.
- **Change:**
  1. Line 52 becomes 'N06AB04'; line 124 becomes 'N06AB05'.
  2. Start the CASE with `WHEN code_atc IS NOT NULL THEN code_atc`.
- **Ships with:** none.
- **Effect on the current files:** None on BPALL (it feeds face_bp_13 and the hubdashboard). 225 paroxetine and 40 citalopram medications get the right code.
- **Other cohorts:** not checked.
- **Answers:** none.

### R54. Read the medication strength from the product name when the form stored none, with a source column

- **Files:** new `clean/ebipolar/ebipolar_cm_dose.sql`; `face_bp_12_traitements.sql` lines 5, 10-42, 126-133; yml; thesaurus TRAITEMENTS; BP_mapping.toml [list_expand].
- **Today:** Since the public drug list, the form stores no strength (A38), and dose, unit and daily dose stay empty. ebipolar_cm is in the Trino slice, so the parsing goes in a new model.
- **Change:** The export fills the existing columns, and a source column says where each strength comes from.
  1. ebipolar_cm_dose counts the amounts in med_psy_cmtrt with the regex `(?<![0-9] )(?<![0-9.,])([0-9]+(?:[.,][0-9]+)?[[:space:]]*(?:mg|g|µg|mcg|microgrammes?|ui|%)(?:[[:space:]]*/[[:space:]]*(?:[0-9]+(?:[.,][0-9]+)?[[:space:]]*)?(?:ml|g|dose))?)(?![[:alpha:]À-ÿ])` (Postgres 9.6 or later):
     - med_psy_cmdose = the stored posologie, else the single amount (µg/mcg written as 'microgrammes');
     - med_psy_cmdose_source = 'posologie', 'nom', or 'nom_multiple' (no strength).
  2. face_bp_12 reads ebipolar_cm_dose, aggregates the source (same ORDER BY as R76) and selects it as med_psy_cmdose_source.
  3. Document it. Tick it on the thesaurus path. Add it and med_psy_cmdostot to list_expand.
  4. Run test_trino_port.py. The lookbehinds and the `regexp_matches` count may need a Trino override.
- **Ships with:** R75 (otherwise 8 new doses are doubled); R76.
- **Effect on the current files:** Emulated on 22,758 medications. 14,471 get a strength from the name. Daily doses go from 6,418 to 19,372 (from 2 to 7,665 among starts from 2018). Expect 3 new doses above 5,000. face_bp_all and MinimumDataset read med_psy_cmdose. Tell us the first extraction that carries it.
- **Other cohorts:** SZ: same defect; twin model eschizo_cm_dose and face_sz_11 changes (7,489 strengths). DR and ASP: none.
- **Answers:** DM-14.

## Tab models (by tab)

**Tab 1, PATIENT**

### R55. Stop exporting nom_centre, a column that is always empty

- **Files:** `face_bp_1_patients.sql` line 15; `ebipolar_patient.sql` line 38; `nucleus/_standards/data/extraction/BP_rename_mapping.toml` lines 19, 30 (LFS); dictionary PATIENT rows 12, 35.
- **Today:** `NULL::text AS NOM_CENTRE_EXPERT` since a81f760b, because the application export strips nom_centre.
- **Change:** Delete the two SQL lines and the two rename lines. R95 deletes the dictionary rows.
- **Ships with:** R95; with or after R1 (same model).
- **Effect on the current files:** 2,236 columns become 2,235. 0 of 22,171 cells are non-blank.
- **Other cohorts:** SZ has already dropped it; delete its dictionary row too.
- **Answers:** DM-8.

### R56. Remove the patient-level copy social_protec and keep protec

- **Files:** `face_bp_1_patients.sql` line 824; `encoding_casting_rules.yaml` line 70.
- **Today:** protec (V0, tab 15) is copied as SOCIAL_PROTEC onto every row, through an unordered pick.
- **Change:** Delete line 824 only. The social join and the WHERE at line 860 stay, because the PROTEC filter uses them (with R1, through social1). Remove the migration map. On the thesaurus path, delete the PATIENT row.
- **Ships with:** none; with R1 or after it.
- **Effect on the current files:** social_protec disappears (17,667 cells, all copies of the 4,858 V0 protec values).
- **Other cohorts:** BP only.
- **Answers:** DEV-13.

### R57. Give the referral detail its dictionary name

- **Files:** `face_bp_1_patients.sql` line 843; BP_rename_mapping.toml lines 15, 26.
- **Today:** The column is aliased CONNAISSANCE_CENTRE_EXPERT_PRECI (a97eb7e3), while the dictionary says ..._PRECISER.
- **Change:** Alias it `CONNAISSANCE_CENTRE_EXPERT_PRECISER`, and delete the two rename lines in the same commit.
- **Ships with:** with or after R1 (same model).
- **Effect on the current files:** The name changes (386 patients have a value; free text, not read).
- **Other cohorts:** SZ uses connaissance_autre.
- **Answers:** DEV-14.

**Tab 3, HETERO-QUESTIONNAIRES**

### R58. Describe the 23 _n1 columns as the MADRS and YMRS rated at the neuropsychological testing

- **Files:** `face_bp_3_heteroquestionnaires.yml`; thesaurus rows 54-71; optional `face_bp_3_heteroquestionnaires.sql` after lines 68 and 93.
- **Today:** Both neuropsychology forms open 'le nouvel MADRS/YMRS' (hetero_*_n1) when the last rating is over a week old (cclin04_). The dictionary does not say so. The columns stay in the export.
- **Change:** Wait for M37.
  1. Relabel the dictionary blocks and the yml entries.
  2. Optional: export `hetero_madrs_n1.date_madrs AS DATE_MADRS_n1` and `hetero_ymrs_n1.date_ymrs AS DATE_YMRS_n1`, with rows and yml entries.
- **Ships with:** R95.
- **Effect on the current files:** No value changes. 368 MADRS_n1 and 348 YMRS_n1 visits; cclin04_ says 'Plus d'une semaine' on 349 and 333 of them; 21 and 22 visits have no other rating.
- **Other cohorts:** SZ has hetero_ymrs_n1, which is not exported.
- **Answers:** DEV-14.

**Tab 4, NEUROPSYCHOLOGIE**

### R59. WAIS-IV digit span: undo the alias shift, and take the WAIS-IV form first in the six summary columns

- **Files:** `ebipolar_neuropsyw4.sql` lines 235-238; `face_bp_4_neuropsychologie.sql` lines 523-574.
- **Today:**
  - The aliases are shifted by one: wais_mc_tot AS MCODEMP, ..., wais_mc_emp AS NBRUT.
  - MCODEMP_w, NBRUT_w, NSTAND_w and VSTAND_w take WAIS-III first, while the other columns take WAIS-IV first.
- **Change:**
  1. `wais_mc_end AS MCODEMP, wais_mc_env AS MCOIEMP, wais_mc_emp AS EMPDID, wais_mc_tot AS NBRUT`.
  2. Swap the CASE arms of the four COALESCEs so that WAIS-IV comes first, keeping the '' and '%Questionna%' filters.
  3. Release note: on WAIS-IV visits these four columns change meaning.
- **Ships with:** none.
- **Effect on the current files:** 4,689 WAIS4 visits move their values (4,654 of 4,675 complete ones fit the shifted layout today). 15 mixed visits change. 1,302 WAIS3 visits are unchanged.
- **Other cohorts:** SZ, DR and ASP are correct.
- **Answers:** DEV-14, DM-7.

### R60. Stop subtracting 3 from the WAIS-III vocabulary total

- **Files:** `face_bp_4_neuropsychologie.sql` line 405.
- **Today:** `VOCABTOT::bigint - 3`, while the application stores the 33-item sum.
- **Change:** Remove `- 3`. Keep the regex guard.
- **Ships with:** R61 must not bring the offset back.
- **Effect on the current files:** +3 on 1,210 WAIS3 visits (1,207 then equal the item sum) and on 9 WAIS4 visits.
- **Other cohorts:** none.
- **Answers:** DEV-14.

### R61. Export the WAIS-IV vocabulary in its own _wais4 columns

- **Files:** `face_bp_4_neuropsychologie.sql` lines 364-410; yml lines 319-564; thesaurus rows 306-312.
- **Today:** WAIS-IV items 1-30 are coalesced into VOCABnn_wais3 cell by cell.
- **Change:**
  1. Replace lines 364-410 with two blocks: psy_neuropsychologie.VOCAB01-33 AS VOCABnn_wais3, and psy_neuropsychologie_wais4.VOCAB01_wais4-30 AS VOCABnn_wais4.
  2. Totals: `CASE WHEN x ~ '^[0-9]+$' THEN x::bigint END`. STD and CR: `NULLIF(x,'')`.
  3. Add dictionary rows, one per item (ranges do not expand).
  4. Rename the yml entries to _wais3.
- **Ships with:** R60.
- **Effect on the current files:** 2,106 WAIS4 visits move to _wais4. 9 stay in _wais3, where they belong. 2 mixed visits split. 33 columns are added.
- **Other cohorts:** ASP already uses wais_voc*.
- **Answers:** DEV-14.

### R62. Fix the typo date_saise_neuropsychologie and document the column

- **Files:** `face_bp_4_neuropsychologie.sql` line 12; yml; thesaurus.
- **Today:** The name has a typo, and the column is in no dictionary tab.
- **Change:** Alias it DATE_SAISIE_NEUROPSYCHOLOGIE, and add a yml entry and a dictionary row ('Date de dernière saisie du formulaire de neuropsychologie').
- **Ships with:** none.
- **Effect on the current files:** Name only (6,313 values).
- **Other cohorts:** none.
- **Answers:** DEV-14.

### R63. Remove visit_neuropsychologie, a copy of visit

- **Files:** `face_bp_4_neuropsychologie.sql` line 11.
- **Today:** It equals visit on 22,171 of 22,171 rows, and nothing reads it.
- **Change:** Delete line 11.
- **Ships with:** none.
- **Effect on the current files:** One column fewer.
- **Other cohorts:** none.
- **Answers:** DEV-13.

**Tab 5, SUICIDE**

### R64. Choose the suicide form by the visit type, not by a text comparison of labels

- **Files:** `face_bp_5_suicide.sql` (35 lines with `VISIT >= 'V0'`, 34 with `VISIT = 'V0'`).
- **Today:** `>= 'V0'` is a text comparison, which depends on the collation for 'screening'.
- **Change:** Replace it with `VISIT_TMP IN (3, 4, 5)`; optionally `= 'V0'` with `VISIT_TMP = 2`.
- **Ships with:** none.
- **Effect on the current files:** none.
- **Other cohorts:** Only this model uses `>=`.
- **Answers:** none.

**Tab 6, SUBSTANCES ET COMORBIDITE**

### R65. Export the comorbidity question 'Pas de changement de l'histoire somatique?'

- **Files:** `face_bp_6_substances_comorbidites.sql` after line 18; yml; thesaurus.
- **Today:** psy_troubles_comorbides.rad_pas_dechangement (Oui = unchanged) is passed by the clean model and not exported. The column is NOT NULL with no default, so old rows may read 'Oui' (M18).
- **Change:** Add `NULLIF(psy_troubles_comorbides.rad_pas_dechangement, '') AS comorb_nochange_lastvisit`, exported as stored ('Oui', 'Non'). Quote the full label in the yml and the dictionary. The change questions keep the polarity of their form, and the name says it: R65 and R78 ask 'no change?' (Oui = unchanged), R79 and R80 ask 'change?' (Oui = changed).
- **Ships with:** none.
- **Effect on the current files:** One column on annual rows. From 2022, 1,603 of 2,835 annual visits have the four gates empty.
- **Other cohorts:** none.
- **Answers:** DM-10.

**Tab 7, CONSTANTES et ECG**

### R66. Export the pregnancy box of the nurse form

- **Files:** `ebipolar_infirmier.sql` (base CTE after line 21; final SELECT before line 252); `face_bp_7_constantes_et_ecg.sql` after line 14; yml; thesaurus.
- **Today:** rad_femmenceinte (Oui/Non) is not selected. The box is hidden, not cleared, for men (A34).
- **Change:**
  1. Add `rad_femmenceinte,` to the base CTE, and `CASE WHEN rad_femmenceinte = 'Oui' THEN 'Y' WHEN rad_femmenceinte = 'Non' THEN 'N' ELSE rad_femmenceinte END AS PREGST_RPORRES` to the final SELECT.
  2. Select it in face_bp_7. Document 'empty = not answered'.
  3. Thesaurus row after WSTCIR (and `"pregst" = "pregst_rporres"` if needed).
- **Ships with:** none.
- **Effect on the current files:** A new column. Upper bound: women with a weight, V0 3,826, six-monthly 1,905, annual 4,663.
- **Other cohorts:** none.
- **Answers:** DM-10.

**Tab 8, BILAN BIOLOGIQUE**

### R67. SZ: leave the unit labels out of the count that picks one biology row per visit

- **Files:** `face_sz_8_bilan_biologique.sql` lines 68-87.
- **Today:** DISTINCT ON orders by the count of filled fields, and that count includes 16 default labels. They are constant today, so they do not matter yet.
- **Change:** At line 86, add `AND k NOT IN ('urate_lborresu','crp_lborresu','gluc_lborresu','hba1c_lborresu','hdl_lborresu','ldl_lborresu','chol_lborresu','trig_lborresu','wbc_lborresu','rbc_lborresu','hgb_lborresu','neut_lborresu','eos_lborresu','mcv_lborresu','plat_lborresu','prolctn_lborresu')`, and update the comment.
- **Ships with:** R28, R29 (SZ steps).
- **Effect on the current files:** No change; the order stays the same (M33).
- **Other cohorts:** not needed.
- **Answers:** none.

**Tab 10, EVALUATION MEDICALE**

### R68. Fix the two NULLIF slips, and add the mixed-features answers of the current episode

- **Files:** `face_bp_10_evaluation_medicale.sql` lines 58 and 163; yml; thesaurus EVALUATION MEDICALE.
- **Today:**
  - `COALESCE(NULLIF(a, b))`, so the DSM-5 count (line 58) and the follow-up catatonic answer (line 163) are never delivered. The DSM-5 inclusion form asks the catatonic question in rad_epactuel_catyp (clean ebipolar_psy_diag_dsm5.sql line 277), which no model exports.
  - The follow-up 'Episode Mixte?' (rad_epactuel_mixttyp2, ebipolar_psy_diag_sem line 45) and the DSM-5 'Type d'épisode Mixte' (rad_epactuel_mixtyp, ebipolar_psy_diag_dsm5 line 554) are asked under the same rule and exported nowhere.
- **Change:**
  1. Line 58: `COALESCE(NULLIF(psy_diag_psychiatrique.rad_tb_hum_nbepmanpsy, ''), NULLIF(psy_diag_psychiatriquedsm5.rad_tb_hum_nbepmanpsy, '')) AS EVNUM_EPMAN_PSY_LT,`.
  2. Line 163: `COALESCE(NULLIF(psy_diag_psychiatrique.rad_epactuel_mixttyp, ''), NULLIF(psy_diag_psychiatrique_semestriel.rad_epactuel_mixttyp, ''), NULLIF(psy_diag_psychiatriquedsm5.rad_epactuel_catyp, '')) AS CEDECODTrouble_humeur_actuel,`. All three fields are the catatonic yes/no.
  3. After line 163, add two columns, with yml entries and thesaurus rows ticked in COCHER:
     - `NULLIF(psy_diag_psychiatrique_semestriel.rad_epactuel_mixttyp2, '') AS CEMIXTTrouble_humeur_actuel_fu,` (follow-up form, asked when the current episode is manic or unspecified);
     - `NULLIF(psy_diag_psychiatriquedsm5.rad_epactuel_mixtyp, '') AS CEMIXTTrouble_humeur_actuel_v0,` (DSM-5 inclusion form, asked when the current episode is manic).
- **Ships with:** R70 wraps these lines.
- **Effect on the current files:**
  - Up to 251 manic-psychotic counts are gained (DSM5 V0 visits answering Oui: 252, with 1 count today).
  - The catatonic answer is filled on 0 of 11,686 follow-ups today, and up to 83 gain one. Up to 11 DSM-5 inclusions also gain one.
  - The two new columns: at most 83 follow-up visits and 1 DSM-5 inclusion.
- **Other cohorts:** None found by grep.
- **Answers:** DEV-11.

### R69. Label an unlabelled inclusion by the form that alone holds its mood or psychosis answers

- **Files:** `face_bp_10_evaluation_medicale.sql` lines 12-28; yml; thesaurus EVALUATION MEDICALE row dsm_criteria.
- **Today:** DSM5 or DSM4 is decided on 5 lifetime fields. 849 of 6,498 V0 rows have no label; 85 of them hold mood or psychosis answers.
- **Change:**
  1. At the top of the model, a Jinja list `dsm_answer_fields` of these 44 fields, which exist in both clean models: rad_tb_hum_type1er, rad_tb_hum_aao, rad_tb_hum_1erpostpartum, rad_tb_hum_1ercyclo, rad_tb_hum_nbepdep, rad_tb_hum_epdeppsy, rad_tb_hum_nbepdeppsy, rad_tb_hum_nbephypoman, rad_tb_hum_nbepman, rad_tb_hum_epmanpsy, rad_tb_hum_nbepmanpsy, rad_tb_hum_epmixtpsy, rad_tb_hum_nbepmixtpsy, rad_tb_hum_ind, rad_tb_hum_nbind, rad_rapidcycling, rad_remisintercycl, rad_saisonalite, rad_tb_hum_aao_tt, rad_tb_hum_epthyman, rad_tb_hum_nbepdepan, rad_tb_hum_epdeppsyan, rad_tb_hum_nbepdeppsy_an, rad_tb_hum_nbephypomanan, rad_tb_hum_nbepmanan, rad_tb_hum_nbepmixtan, rad_tb_hum_epmanpsyan, rad_tb_hum_nbepmanpsyan, rad_tb_hum_epmixtpsyan, rad_tb_hum_nbepmixtpsyan, rad_tb_psychos, rad_tb_psychos_type, rad_tb_psychos_lastmonth, rad_eprecent_type, rad_eprecent_edmtype, rad_eprecent_chron, rad_eprecent_sever, rad_eprecent_postpartum, rad_epactuel, rad_epactuel_type, rad_epactuel_edmtype, rad_epactuel_sever, rad_epactuel_chron, rad_postpartum_actuel.
  2. Keep the two current WHENs, and add before ELSE NULL: 'DSM5' when the CONCAT of the DSM-5 fields <> '' and the CONCAT of the DSM-IV fields = ''; 'DSM4' the other way round. Build each CONCAT with a Jinja loop over the list. CONCAT skips NULLs, so a missing record counts as ''. Dates, DIVA, the migration ages and the sick-leave fields are left out on purpose, so a record holding only defaults gets no label.
  3. Add a yml entry and a thesaurus description.
- **Ships with:** none.
- **Effect on the current files:** Up to 85 V0 rows gain a label (38 up to 2019, 21 in 2020-21, 26 from 2022). No existing label changes.
- **Other cohorts:** none.
- **Answers:** DEV-11.

### R70. Read every inclusion value of tabs 6, 10 and 11 from the form named by the label

- **Files:** new `clean/ebipolar/ebipolar_dsm_label.sql` (ephemeral); new `macros/dsm_keep_unless.sql`; face_bp_10 lines 12-163; face_bp_6 (106 COALESCEs); face_bp_11 lines 15-22.
- **Today:** The label prefers DSM-5, but every cell takes DSM-IV first, so a visit with both forms mixes them (A28).
- **Change:** Wait for M13. Deliver the labelled form only:
  1. ebipolar_dsm_label computes R69's label per visit.
  2. Join it in tabs 6, 10 and 11.
  3. Macro: `CASE WHEN dsm_label.dsm_criteria = '{{ label }}' THEN NULL ELSE {{ expr }} END`.
  4. Wrap each DSM-IV term in `dsm_keep_unless('DSM5', ...)` and each DSM-5 term in `dsm_keep_unless('DSM4', ...)`, the DSM-5 mixed-features column of R68 included. Keep the follow-up terms and the order. Do not wrap lines 79, 97 and 100 (R72 makes them read the follow-up form only), nor the DIVA and migration columns (lines 166-209).
  5. Run test_trino_port.py (ebipolar_dsm_label is a new clean model).
- **Ships with:** after R68, R69, R71 and R72 (they rewrite the lines this request wraps).
- **Effect on the current files:** At least 25 V0 visits mix forms (16 labelled DSM4 with DSM-5-only cells, 9 labelled DSM5 with evnum_epmixt_lt). Single-form visits do not change.
- **Other cohorts:** none.
- **Answers:** DEV-11.

### R71. Lifetime mood-episode Y/N: empty where the count was not answered, U for 'Ne sais pas'

- **Files:** `face_bp_10_evaluation_medicale.sql` lines 35-51.
- **Today:** `NOT IN ('0','Ne sais pas','') THEN 'Y' ELSE 'N'` writes N on every non-V0 row, and for 'Ne sais pas'.
- **Change:** On `c = COALESCE(NULLIF(dsm4,''), NULLIF(dsm5,''))`: `WHEN c IS NULL THEN NULL WHEN c = 'Ne sais pas' THEN 'U' WHEN c = '0' THEN 'N' ELSE 'Y'`, for EDM, EHMAN and EPMAN. EPMIXT uses the DSM-IV count only.
- **Ships with:** before R70. Tell us the first extraction that carries it: our reader maps Y and N.
- **Effect on the current files:** N becomes empty on 68,065 cells, and U on 2,889; Y is unchanged.
- **Other cohorts:** none.
- **Answers:** DEV-13.

### R72. Compute the three follow-up psychotic flags from the follow-up counts

- **Files:** `face_bp_10_evaluation_medicale.sql` lines 79, 97, 100; yml lines 169, 197, 218; `encoding_casting_rules.yaml` line 933.
- **Today:** The *_psy_spv columns copy the lifetime answer at V0.
- **Change:**
  1. Line 79: `CASE WHEN psy_diag_psychiatrique_semestriel.rad_tb_hum_nbepdep = '0' THEN 'N' WHEN psy_diag_psychiatrique_semestriel.rad_tb_hum_nbepdeppsy = '0' THEN 'N' WHEN psy_diag_psychiatrique_semestriel.rad_tb_hum_nbepdeppsy = 'Ne sais pas' THEN 'U' WHEN COALESCE(psy_diag_psychiatrique_semestriel.rad_tb_hum_nbepdeppsy,'') = '' THEN NULL ELSE 'Y' END` (the model's CTE and join keep the full name; it has no short alias).
  2. The same at line 97 (nbepman, nbepmanpsy) and line 100 (nbepmixt, nbepmixtpsy).
  3. Update the yml and map Y/N/U in the migration.
- **Ships with:** before R70. Tell us the first extraction that carries it: our reader maps Y and N.
- **Effect on the current files:** V0 cells are emptied (5,056, 4,425, 4,022). Follow-ups: depressive N 3,501, Y 110, U 37; manic 3,629, 181, 10; mixed 2,689, 37, 5.
- **Other cohorts:** none.
- **Answers:** DEV-13.

**Tab 11, SOIN SUIVI HOSP ARRET TRAVAIL**

### R73. Lifetime hospitalisation Y/N: 'Ne sais pas' becomes Y in SZ, '00' stays empty in DR

- **Files:** `face_sz_10_soin_suivi_hosp_arret_travail.sql` lines 17-21; `face_dr_11_soin_suivi_hosp_arret_travail.sql` lines 33-37 and its yml lines 44-47.
- **Today:** SZ's `ELSE 'Y'` catches 'Ne sais pas'. DR's bigint cast leaves '00' NULL, and would fail on text.
- **Change:** Both become, on text: NULL or blank gives NULL; 'Ne sais pas' gives 'U'; `~ '^0+$'` gives 'N'; `~ '^([0-9]+|>[0-9]+)$'` gives 'Y'; else NULL. Update the DR yml.
- **Ships with:** none. Tell us the first extraction that carries it: our reader maps Y and N.
- **Effect on the current files:** SZ: 44 visits go from Y to U. DR: 19 V0 visits go from empty to N.
- **Other cohorts:** BP and ASP: none.
- **Answers:** none.

### R74. Sick leaves in the past year: the social form's weeks are not a count

- **Files:** `face_bp_11_soin_suivi_hosp_arret_travail.sql` lines 23-25; `ebipolar_social.sql` lines 133 and 135; yml; thesaurus.
- **Today:**
  - NBOCCUR_arret_travail (line 24), the number of sick leaves, takes as its last fallback the social form's social_travan_nb, 'Nombre de semaines cumulées sur l'année', a number of weeks. The clean model names it NBOCCUR_arret_travail_LY_SocialBilan (line 133).
  - The social form's yes/no 'Arrêt de travail au cours de l'année passée' (rad_social_travan, selected as HOOCCUR_arret_travail_LY_SocialBilan, line 135) is not exported. HOOCCUR_arret_travail (line 23) reads the diagnosis forms only.
  - At V0, 40 values of NBOCCUR_arret_travail are numbers above 20, although the diagnosis forms stop at '>20'. 22 of them are on visits where HOOCCUR_arret_travail is empty, which fits the social fallback.
- **Change:**
  1. Line 24: remove the social term.
  2. Line 25: add `NULLIF(social_bilan_social.NBOCCUR_arret_travail_LY_SocialBilan, '')` as the last term of HODUR_arret_travail, which holds weeks (tb_hum_duree_arretan, 'en semaines').
  3. Line 23: add `NULLIF(social_bilan_social.HOOCCUR_arret_travail_LY_SocialBilan, '')` as the last term of HOOCCUR_arret_travail.
  4. In ebipolar_social line 133, rename the alias to a weeks name, for example HODUR_arret_travail_LY_SocialBilan, and update the two references.
  5. Update the yml and the dictionary.
- **Ships with:** one commit with the ebipolar_social requests R35, R36 and R38-R42.
- **Effect on the current files:** The cells filled by the fallback move from the count to the duration. Their number cannot be read from the file, because the COALESCE hides the source; the 40 values above 20 are the part that shows.
- **Other cohorts:** not checked.
- **Answers:** none.

**Tab 12, TRAITEMENTS**

### R75. Read units a day written '1/2' as 0.5 in the daily dose

- **Files:** `face_bp_12_traitements.sql` lines 33-35.
- **Today:** The first number of med_psy_cmdosfrq is taken, so '1/2' counts as 1.
- **Change:** Replace the second factor with:
  ```sql
  CASE WHEN med_psy_cmdosfrq::text ~ '^[[:space:]]*[0-9]+[[:space:]]*/[[:space:]]*[1-9][0-9]*'
       THEN SUBSTRING(med_psy_cmdosfrq::text FROM '^[[:space:]]*([0-9]+)')::numeric
          / SUBSTRING(med_psy_cmdosfrq::text FROM '/[[:space:]]*([1-9][0-9]*)')::numeric
       ELSE ( (regexp_match(replace(med_psy_cmdosfrq::text, ',', '.'), '([0-9]+(?:\.[0-9]+)?)'))[1] )::numeric END
  ```
- **Ships with:** before or with R54.
- **Effect on the current files:** 2 delivered doses are halved, and they then match strength x units. No other dose changes.
- **Other cohorts:** none.
- **Answers:** none.

### R76. Order the medication lists so that their order stays the same between builds

- **Files:** `face_bp_12_traitements.sql` lines 10-42.
- **Today:** array_agg has no ORDER BY, so the item order follows the physical order of the table. The lists stay the delivery format of the medications.
- **Change:** Give every array_agg the same `ORDER BY med_psy_cmstdtc NULLS LAST, id_medicament_psychotrope` (never date_saisie).
- **Ships with:** before or with R54.
- **Effect on the current files:** The order changes once. Between BPALL_20261030 and BPALL, 3,429 of 4,750 lists changed order; between the two 13 Nov runs, 0.
- **Other cohorts:** SZ and DR already order theirs.
- **Answers:** DM-14.

**Tab 14, ANTECEDENTS**

### R77. Export the seven section shortcuts of the BP medical history

- **Files:** `ebipolar_mh.sql` before line 839; `face_bp_14_antecedents.sql` after lines 172, 128, 102, 72, 51, 33, 11; yml; thesaurus ANTECEDENTS.
- **Today:** rad_neuro_non, _cv_non, _endoc_non, _dermato_non, _urin_non, _hepato_non and _pathoa_non are in staging but not exported. The eBipolar copy script is off (A32), so a shortcut is the only record of the answer.
- **Change:**
  1. In ebipolar_mh, add for each field `CASE WHEN x = 'Non pour tous' THEN 'N' WHEN x = 'Ne sais pas pour tous' THEN 'U' ELSE x END AS x`.
  2. In face_bp_14, add `psy_histoire_medicale.<x>,` after each section header, working from the bottom up. Ship both steps together, or face_bp_14 and the extraction fail.
  3. Add yml entries and 7 thesaurus rows (COCHER empty in the template).
- **Ships with:** R79 (same files, one commit).
- **Effect on the current files:** 7 columns, no value changes. Upper bound: from 2022, 1,287 V0 visits with a history have 30,094 empty section cells; 257 have all seven empty.
- **Other cohorts:** SZ: R78.
- **Answers:** DM-10.

### R78. Export the seven SZ section shortcuts and the SZ 'no change?' question

- **Files:** `eschizo_mh.sql` before line 617; `face_sz_13_antecedents.sql` after line 209 and after lines 97, 88, 62, 46, 35, 25, 13, 12; yml; thesaurus.
- **Today:** Six shortcuts, rad_patho_non (U = 'Non connu pour tous') and rad_pas_dechangement (Oui = unchanged) are not exported. The copy script crashes at line 29 (A31).
- **Change:**
  1. Add the CASEs for the 7 shortcuts on `staging.<field>`, as in R77, and `NULLIF(staging.rad_pas_dechangement, '') AS mh_nochange_lastvisit`, exported as stored. Do not export rad_urin_non.
  2. In face_sz_13, subtract the 8 new keys in the ORDER BY count after line 209, so that the same duplicate stays kept, then add the columns after the headers.
  3. Add yml entries and thesaurus rows.
- **Ships with:** none.
- **Effect on the current files:** 8 columns, no value changes. From 2022, 545 V0 visits have a section head answered; the digestive, other and autoimmune sections are empty on 287, 259 and 349 of them, against fewer than 10 for the four other sections.
- **Other cohorts:** BP: R77, R79.
- **Answers:** DM-10, SZ O26.

### R79. Export the BP medical-history change question of the annual visit

- **Files:** `ebipolar_mh.sql` before line 839; `face_bp_14_antecedents.sql` after line 10; yml; thesaurus.
- **Today:** rad_pas_dechangement ('y a-t'il une modification...', Oui = changed) is shown at annual visits only, and not exported.
- **Change:** Add `NULLIF(rad_pas_dechangement, '') AS mh_change_lastvisit` (exported as stored), select it after line 10, and quote the label in the yml, noting the 2024 wording (M17).
- **Ships with:** R77 (same commit).
- **Effect on the current files:** 1 column. Annual visits with an empty history: 1,035/1,754, 1,268/2,051, 1,019/1,354, 1,087/1,481 by period from 2016.
- **Other cohorts:** SZ uses the opposite wording (R78).
- **Answers:** DM-10.

### R80. Export the BP family-history change question

- **Files:** `ebipolar_ap.sql` before line 672; `face_bp_14_antecedents.sql` after line 206; yml; thesaurus.
- **Today:** psy_antecedant_familiaux_psy.rad_pas_dechangement (Oui = changed) is not exported. Without it, an unchanged family history cannot be told from one not filled at the annual visit.
- **Change:** Add `NULLIF(rad_pas_dechangement, '') AS fh_change_lastvisit` (exported as stored) in both models, a yml entry and a dictionary row.
- **Ships with:** none.
- **Effect on the current files:** 1 column. Annual visits with all family columns empty: 1,670/1,754, 1,861/2,051, 771/1,354, 595/1,481.
- **Other cohorts:** none.
- **Answers:** DM-10.

### R81. Five allergic and inflammatory diseases: 0 only after an answered section

- **Files:** `face_bp_14_antecedents.sql` lines 148-169; optional `ebipolar_mh.sql` 617-683; thesaurus CODAGE.
- **Today:** `LIKE ... THEN 1 ELSE 0` writes 0 where nothing was answered.
- **Change:** `CASE WHEN chk_somat_all_specifier LIKE '%<option>%' THEN 1 WHEN somat_all = 'N' THEN 0 WHEN somat_all = 'Y' AND COALESCE(chk_somat_all_specifier,'') <> '' THEN 0 END`, for the asthma, allergy, lupus, rheumatoid arthritis and other autoimmune options. CODAGE: '1 coché, 0 non coché dans une section remplie, vide non renseigné'.
- **Ships with:** none.
- **Effect on the current files:** 72,235 cells go from 0 to empty (14,447 visits). The face_bp_all, biobank and FHIR outputs change.
- **Other cohorts:** none.
- **Answers:** DEV-13.

### R82. Relatives' alcohol, cannabis and other-substance columns: read the multi-choice list

- **Files:** `face_bp_14_antecedents.sql` lines 331-715; thesaurus CODAGE.
- **Today:** '=' and NOT IN on a multi-choice list: 'Aucun' and 'Ne sais pas' give 'other substance' = 1, and a combination gives 0.
- **Change:** `CASE WHEN R_substance LIKE '%B%' THEN 1 WHEN R_structure = 'N' THEN 0 WHEN COALESCE(R_substance,'') = '' OR R_substance LIKE '%Ne sais pas%' THEN NULL ELSE 0 END`. The structure branch applies to parents and grandparents only.
- **Ships with:** none.
- **Effect on the current files:** Of 1,729,338 cells (78 columns on 22,171 visits): 742 go from 0 to 1, 9,833 from 1 to 0, and 1,644,458 become empty.
- **Other cohorts:** DR already leaves unanswered cells empty.
- **Answers:** DEV-13.

## Score step

Definitions are in `nucleus/nucleus/processing/scores/definitions/`. The step keeps writing the columns it writes today. The requests below fix its formulas and keys.

### R83. BIS: declare the 1 to 4 range with the keys the step reads, give DR its own entries with no item reversed, and give the ASP total its formula

- **Files:** `bis10.yaml` (15 entries with min_value/max_value; 12 sum entries with round_decimals; table_glob of the 9 shared entries at lines 20-21, 35-36, 58-59, 72-73, 86-87, 100-101, 114-115, 128-129, 143-144; a new DR block); `nucleus/tests/processing/scores/calculator/score/test_bis10.py`; a new test beside test_ados.py.
- **Today:**
  - pydantic drops min_value/max_value, so reversed items are scored 6 - value instead of 5 - value. The tests assert the wrong values.
  - The 9 BP entries also run on face_dr_2_autoquestionnaires and reverse 11 items. eDepression seems to store those items already turned: the application's own DR sub-scores BIS1035-1037 equal the plain sums of the stored items on 530 of 530 complete visits (M20).
- **Change:** Ask M20 now. Ship the BP and DR parts together once it is answered.
  1. In the 15 entries, replace `min_value: 1` by `scale_min: 1` and `max_value: 4` by `scale_max: 4`.
  2. Delete `round_decimals` from the 12 sum entries.
  3. Fix the 14 test calls (`scale_min=1, scale_max=4`), with expected values on 5 - value.
  4. Add a test that loads definitions/ (as test_ados.py does), with every item at 1: bis10_cognitive 4.0 and bis10_imp_motrice 14.
  5. DR: remove face_dr_2_autoquestionnaires from the table_glob of the 9 shared entries. Add DR entries with new entry names (the loader keys entries by name), writing the same columns as today: bis10_cognitive_dr to bis1038, bis10_behavioral_dr to bis1039, bis10_general_dr to bis1040 (mean of bis1038 and bis1039), bis10_imp_motrice_dr to bis10_imp_mot, bis10_imp_attentionnelle_dr to bis10_imp_att, bis10_diff_planification_dr to bis10_imp_pla, bis10_score_total_dr to bis10_score_total, bis11_dr to bis11 and bis10_dr to bis10 (the 12 items). Each takes today's items, `table_glob: ["face_dr_2_autoquestionnaires"]`, `reverse_items: []`, scale 1-4 and `missing_mode: ignore`, with `round_decimals: 1` on the three means only. Example:
  ```yaml
    - type: mean
      name: bis10_cognitive_dr
      output: bis1038
      table_glob: ["face_dr_2_autoquestionnaires"]
      items: ["BIS1001", "BIS1008", "BIS1009", "BIS1012", "BIS1021"]
      reverse_items: []   # stored already turned by the eDepression form
      scale_min: 1
      scale_max: 4
      missing_mode: ignore
      round_decimals: 1
      export: true
  ```
  6. Add a check: the DR bis10_imp_mot, bis10_imp_att and bis10_imp_pla equal BIS1035, BIS1036 and BIS1037 where all items are filled.
  7. ASP: the entry bis10_general_asp (lines 192-203) writes the mean of bis1038 and bis1039 into bis_score, the eAsperger BIS total. Keep the output bis_score, and give the entry the eAsperger total formula once M49 gives it.
- **Ships with:** R84. See B2. Step 7 waits for M49.
- **Effect on the current files:**
  - BP, keys alone: bis1038 -1.0 on 6,148; bis10 -5 on 6,132; bis11 -4 on 6,136; similar shifts on the sub-scores. R84 changes the BP columns further.
  - ASP: its 6 sum entries have the same key defect; 4 visits change. bis_score equals the mean of bis1038 and bis1039 on 4 of 4 ASPALL visits today; step 7 changes it on those visits.
  - DR: bis1039 unchanged; bis1038 and bis1040 change on 500 visits, bis10_imp_mot 393, bis10_imp_att 420, bis10_imp_pla 508, bis11 485, bis10_score_total 523, bis10 500.
- **Other cohorts:** SZ has no BIS.
- **Answers:** DM-13.

### R84. BIS in BP: write each form's scores only on the visits of that form

- **Files:** `bis10.yaml`, BP part (lines 14-151); `face_bp_2_autoquestionnaires.yml` lines 1822-1840.
- **Today:** The step writes the 12-item scores (bis1038, bis1039, bis1040, bis10) on all 4,689 34-item visits, and the 34-item sub-scores, total and bis11 on the 1,459 12-item visits, as sums of the shared items. No column records the form.
- **Change:** Keep the recalculation in the nine columns, with 5 - value (R83):
  1. Write each BP score first into a helper (export false), with missing_mode strict, then into its column. The 34-item scores (bis10_imp_mot, bis10_imp_att, bis10_imp_pla, bis10_score_total, bis11) need no mask: strict empties them on 12-item visits, since each needs an item only the 34-item form asks.
  2. The 12-item scores need a form marker built in the step, not in dbt: a `sum` (missing_mode ignore, export false) over the 22 items only the 34-item form asks (BIS1002, 1003, 1004, 1005, 1007, 1010, 1011, 1013, 1015, 1016, 1018, 1019, 1022, 1024, 1026, 1027, 1029, 1030, 1031, 1032, 1033, 1034); then `gte` with threshold 1; then `eq` with value 1.0 (1 on 34-item visits, 0 elsewhere); then a `mask` with condition_value 0 on each of the four 12-item scores. This relies on `eq` returning 0 for an empty input (comparison.py line 59): on 12-item visits the `sum` is empty and `gte` keeps it empty. Do not change EqComputer.
  3. Do not use case_when with op isna: CaseWhenComputer sets an empty input to empty after its rules.
  4. bis1040 reads the unmasked helpers.
  5. bis10 stays the 12-item sum, as dictionary V4.34 says. Describe the nine columns in the yml.
- **Ships with:** R83.
- **Effect on the current files:** Measured with the 5 - value recalculation, strict, by form:
  - bis1038, bis1039, bis1040 and bis10 are emptied on the 4,689 34-item visits.
  - 12-item visits: bis1038 -1.0 on 1,455 (4 emptied); bis1039 unchanged on 1,451 (8 emptied); bis1040 -0.4/-0.5/-0.6 on 336/761/352 (10 emptied); bis10 -5 on 1,449 (10 emptied).
  - 34-item visits: bis10_imp_mot -1 on 4,653 (36 emptied), bis10_imp_att -2 on 4,668 (21 emptied), bis10_imp_pla -8 on 4,654 (35 emptied); bis10_score_total -11 on 4,638 (51 emptied); bis11 -4 on 4,650 (39 emptied).
  - The three sub-scores, the total and bis11 are emptied on the 1,459 12-item visits.
  - Our package computes BIS from the items, so no delivered value changes.
- **Other cohorts:** DR: R83 and B2. ASP: its own entries. SZ: no BIS.
- **Answers:** DM-13.

### R85. MAThyS in BP: score each record with the rule of its form

- **Files:** `mathys.yaml`, the six entries (table_glob at lines 13-17, 30-34, 47-51, 64-68, 81-85, 101-105).
- **Today:** Six entries write mathys29-33 and mathys_ on every BP and DR visit with the key: 10 - value on items 5-10, 17 and 18, strict. The old BP form stored these eight items already turned, so on old-form records the key turns them back the wrong way. A correct score needs the form of each record, and the export does not have it: MAThyS stores no form or version (A10). Our package places records by date and leaves 1,435 records of 2021-09 to 2022-12 undelivered.
- **Change:** Wait for M47. If the form of each record can be told (a stored version, or the date each centre switched), carry it in the clean model and gate the six BP entries: the plain sum of the stored items on old-form records, the key on new-form records. DR keeps the key, which holds in every DR year.
- **Ships with:** R52 (the slider form, if its table holds rows).
- **Effect on the current files:** About 10,184 BP visits dated before 2023 would get the plain sum, the right score for the old form (measured against BPALL_20261030, which still held the application's sub-scores). Our package computes MAThyS from the items, so no delivered value changes.
- **Other cohorts:** DR: unchanged. SZ and ASP: no MAThyS.
- **Answers:** DM-12.

### R86. AIM and ALS in BP: the step writes short-form scores on long-form visits

- **Files:** `aim.yaml` (aim_score, line 6); `als.yaml` (lines 5, 40, 53, 67); `face_bp_2_autoquestionnaires.yml` lines 1969-1995 and 2137-2142.
- **Today:**
  - aim_score writes the 20-item mean over aim_ on every row, also on the 4,647 AIM-40 visits where aim_ is filled. There the application stored a 40-item mean (11 items reversed, rounded to 2, in the shared application code of May 2023).
  - The four ALS entries write the ALS-18 formulas over als55, als56, als59 and als_ on the 4,696 visits of the 54-item form. There the application stored long-form scores: depression (11 items), elation (12) and anger (7), each rounded to 2, and a total equal to the mean of the six sub-scores, rounded to 1.
  - On ALS-18 visits the application rounds the sub-scores to 2 decimals and the total to 1. The step does not round als56 and rounds als_ to 3.
  - Tab 2 carries only the 20 AIM and 18 ALS items of the short forms, and no column records the form (A9). So the step cannot apply the long-form rules today.
- **Change:**
  1. Now: round als56 to 2 decimals and als_ to 1, as the application does. als55 and als59 are means of 5 items and need no rounding.
  2. Wait for M23 and M24. If they confirm the long-form rules, carry the form of each record into the clean models (from the staging items rad_aim1-40 and rad_als_1-54) and the long-form items into tab 2. Then gate the entries: short-form formulas on short-form records, long-form formulas on long-form records. Never disable an entry with `table_glob: []` (calculator/base.py line 27 turns it into all tables).
- **Ships with:** none.
- **Effect on the current files:**
  - Step 1: als56 moves by 0.005 on 719 of 1,452 ALS-18 values; als_ moves by up to 0.044 on 1,181 of 1,378.
  - Step 2: up to 4,647 aim_ values, and up to 4,679 values of each ALS column on 54-item visits.
- **Other cohorts:** ASP's long ALS entries may differ from the eAsperger script (M25).
- **Answers:** none.

### R87. PRISE-M: score the total with the application's rule

- **Files:** `prisem.yaml`; new test `test_prisem.py`.
- **Today:** A sum of the filled items. The application needs all 30 common items plus exactly one of 6d and 8c.
- **Change:**
  1. BP entries: a strict sum of the 30 items; binary_sum on PRISM06D and PRISM08C; coalesce; mask where the count is 1; a strict compose into prism. All helpers export false.
  2. Keep today's sum for DR and ASP, under the entry name prisem_score_dr_asp and the same output prism.
  3. Tests on 7 made-up rows.
- **Ships with:** none.
- **Effect on the current files:** prism goes from 16,227 to 15,864 (35 with both sex items, 9 with neither, 319 incomplete).
- **Other cohorts:** DR and ASP are unchanged until M26.
- **Answers:** DM-13.

### R88. MDQ screen: empty when an unanswered question 14 or 15 could still make it positive

- **Files:** `mdq.yaml` lines 31-99; new `test_mdq_definition.py`.
- **Today:** EqComputer turns an empty mdq14 or mdq15 into 0, so the screen becomes 'Négatif'.
- **Change:** Replace the chain, with all helpers export false:
  1. case_when entries give one fail flag per criterion: mdqcal >= 7, mdq14 = 1, mdq15 in [2, 3] (0 when met, 1 otherwise; a missing input stays missing).
  2. max (ignore) gives the known fails; case_when eq 1 gives the certain fail.
  3. max (strict) of the three flags; coalesce of the certain fail and the strict max.
  4. mask on complete items 1-13.
  5. map to mdq_: 1 'Négatif', 0 'Positif'.
  6. Seven test rows. Leave EqComputer as it is: R84 relies on it.
- **Ships with:** none.
- **Effect on the current files:** BP: 17 visits go from 'Négatif' to empty (engine replay). DR: 1.
- **Other cohorts:** included.
- **Answers:** none.

### R89. PSQI efficiency: no time in bed when the bedtime equals the rising time

- **Files:** `calculator/psqi/efficiency.py` lines 176-178; `test_efficiency.py`.
- **Today:** Equal times give 24 h in bed, so psqi11 = 3.
- **Change:** `if wake_time == bed_time: return np.nan`, then `if wake_time < bed_time:` add a day. Add a test (08:00, 08:00 gives NaN).
- **Ships with:** R90 (same file).
- **Effect on the current files:** BP: 20 visits, psqi11 and psqi_ become empty. SZ 11, DR 7.
- **Other cohorts:** included.
- **Answers:** none.

### R90. PSQI efficiency: round to 0.1% before banding

- **Files:** `efficiency.py` line 119; `test_efficiency.py`.
- **Today:** There is no rounding, so 84.98% scores 1; the application rounds it and scores 0.
- **Change:** `efficiency_pct = np.floor((sleep_hours / hours_in_bed) * 1000 + 0.5) / 10`. Test: 23:00, 06:06, 06:02 gives 0.
- **Ships with:** R89.
- **Effect on the current files:** BP 1 visit, SZ 1.
- **Other cohorts:** included.
- **Answers:** none.

### R91. Disable madrsn1_score, which never runs

- **Files:** `madrs.yaml` lines 15-24.
- **Today:** It needs MADRSN01-10, which do not exist, so it is skipped on every run.
- **Change:** `enabled: false`; the same for ymrsn1_new_score.
- **Ships with:** none.
- **Effect on the current files:** none.
- **Other cohorts:** DR: same.
- **Answers:** DM-13.

### R92. Use the key names the score step reads (scale_min/scale_max) in ctq, als, csm and epworth

- **Files:** `ctq.yaml` (10 line pairs, from 30-31 to 207-208); `als.yaml` 45-46, 59-60, 72-73; `csm.yaml` 26-27; `epworth.yaml` 21-22, 42-43.
- **Today:** ctq and als use min_value/max_value, which the step drops, so the defaults 1/5 apply. csm and epworth use the read keys but give the range of the total (13-55, 0-24), not of an item. The values are right by chance: the CTQ items are on 1-5, and the ALS, csm and epworth entries reverse no item.
- **Change:** Rename the keys in CTQ (1/5) and ALS (0/3). In csm, remove the keys and comment that no item is reversed. In epworth, 0/3. Do not add extra='forbid' yet.
- **Ships with:** none.
- **Effect on the current files:** none.
- **Other cohorts:** included: the CTQ entries run on BP, SZ, DR and ASP; csm on BP and DR; the second epworth entry on DR and ASP; the ALS entries named here on BP.
- **Answers:** DM-13.

### R93. Reject unknown keys, invalid files and repeated names instead of ignoring them

- **Files:** `registry/models.py`; `registry/loader.py` lines 38-72 and 80-83; `eq5d5l.yaml`; `recsoc.yaml`; `psqi.yaml`; a new test.
- **Today:** Typos fall back to defaults, an invalid file is skipped with a log line, and a repeated name replaces silently (psqi.yaml defines its 8 entries twice).
- **Change:**
  1. eq5d5l: `separator` becomes `sep`; delete `na_rep`.
  2. recsoc: delete the 6 unread keys (25 occurrences).
  3. psqi.yaml: delete lines 177-334.
  4. Add `ConfigDict(extra="forbid")` to the models.
  5. Make the loader raise on invalid files and repeated names, or add a test that does.
- **Ships with:** after R83 and R92.
- **Effect on the current files:** none.
- **Other cohorts:** all.
- **Answers:** DM-13.

### R94. Extraction summary: say whether the score step ran and which columns it rewrote

- **Files:** `scores/api.py` (run_scores_on_schema, from line 345); `extraction/extraction_summary.py`.
- **Today:** Only reactor/CHANGELOG.md records the runs. With --no-scores, or after a failed layer, 46 BP columns change meaning silently.
- **Change:**
  1. Write `<gold>._score_runs` (time, commit, outputs per table).
  2. Print a section 'Scores recomputed by the export', or 'no run recorded'.
- **Ships with:** none.
- **Effect on the current files:** none.
- **Other cohorts:** all.
- **Answers:** none.

## Dictionary and configuration

Row numbers are those of FACEBP_thesaurus_V4.34.xlsx before any edit. Apply the row edits from the bottom of each sheet up, so that a deletion does not move the rows named below it.

### R95. Correct the BP dictionary so that every name it lists exists and every delivered column can be ticked

- **Files:** FACEBP_thesaurus_V4.34.xlsx; `nucleus/_standards/data/extraction/range_overrides.json` (LFS); `face_bp_5_suicide.yml` lines 124-127; `face_bp_11_soin_suivi_hosp_arret_travail.yml` lines 38-46.
- **Today:** Read with the pipeline's expander and BP_mapping.toml, 2,121 dictionary names match no column (2,058 from sparse digit-span ranges), and 119 of 2,236 columns cannot be ticked.
- **Change:**
  1. Read range_overrides.json first (M11).
  2. PATIENT: delete rows 8, 11, 35, 49, 52, and row 12 with R55. Label rows 45-48, 50, 51.
  3. SOINS: delete row 8; rows 9-10 'visite initiale'.
  4. SUICIDE: delete row 19.
  5. NEUROPSYCHOLOGIE: one row per item for rows 337, 340 (14 items), 352, 355, 358, 215, 218, 302; rows 309 and 70 follow R61 and R58. Label row 150 cpt_version.
  6. AUTO-QUESTIONNAIRES: replace row 229 with the 25 WURS items; label ALS55, ALS56, ALS59.
  7. SUBSTANCES: rad_tb_subst coding; add a rad_tb_subst_raw row; label rows 26-29.
  8. yml: delete isf08_qsdtc, and set the 12-month wording.
- **Ships with:** R55, R96, R97, R98, R57, R62, R63, R61, R58.
- **Effect on the current files:** BPALL is unchanged. Simulated: 0 unmatched names and 0 unticked columns.
- **Other cohorts:** SZ: 63 and 152; DR: 12 and 322. Each needs its own pass.
- **Answers:** DM-7, DM-8.

### R96. Two BP mapping entries make a ticked Epworth total and dysthyroidism type return other columns

- **Files:** `BP_mapping.toml` [variables_mapping] lines 150, 152, 587 (LFS).
- **Today:** `"ess0109" = "essdorm"` and `"dysthyro_mhmodify" = "dysthyro_mhmodify_tt"` swap ticked variables.
- **Change:** Delete lines 152 and 587, and line 150 if no older dictionary uses ESS. Optional: a pytest that flags a key mapped to another column of the same model.
- **Ships with:** R95.
- **Effect on the current files:** None on BPALL; 2 more columns become tickable.
- **Other cohorts:** None in SZ, DR or ASP.
- **Answers:** DM-7.

### R97. Rename the new-diagnosis dictionary row to the CHGDIAG spelling the export uses

- **Files:** FACEBP V4.34 PATIENT row 30.
- **Today:** The export uses CHGDIAG (as DR does), while the row says CHDIAG.
- **Change:** Rename the row. Keep rename-mapping lines 17 and 28 for older copies. Leave the _patient twin unchanged.
- **Ships with:** none.
- **Effect on the current files:** none (9 patients have a value).
- **Other cohorts:** DR already uses CHGDIAG.
- **Answers:** DEV-14.

### R98. Drop the final underscore from the 18 CPT-3 dictionary names

- **Files:** FACEBP V4.34 NEUROPSYCHOLOGIE rows 249-266; optional BP_mapping.toml.
- **Today:** CPT306A_ to CPT311D_ do not match the model, so a ticked request loses all 18 columns.
- **Change:** Rename the rows. Optionally add 18 mapping entries `"cpt306a_" = "cpt306a"`.
- **Ships with:** none.
- **Effect on the current files:** None on BPALL; 526 visits hold CPT-3 values.
- **Other cohorts:** none.
- **Answers:** DEV-14, DM-7.

### R99. Say when non_extract applies, and make it act in ASP dictionary runs too

- **Files:** `extraction/EXTRACTION.md` lines 164-185; `config_loader.py` lines 298-321; `nucleus/nucleus/cli.py` lines 381-384; a new test.
- **Today:** Without --thesaurus-file, the whole --mapping-file is ignored, which is how brthdtc is delivered. The non_extract filter sits under `if mappings.variables_mapping:`, which is empty for ASP.
- **Change:**
  1. Move the non_extract block out of that condition.
  2. Warn when --mapping-file is given without --thesaurus-file.
  3. Correct the docs.
  4. Add a pytest.
- **Ships with:** after M10. If dates of birth are allowed, brthdtc leaves the four lists.
- **Effect on the current files:** None on the four files. ASP dictionary runs start removing listed names.
- **Other cohorts:** list sizes BP 28, SZ 29, DR 19, ASP 19.
- **Answers:** none.

### R100. Stop the extraction when a (patient, visit) key repeats

- **Files:** `extraction/extraction.py` (merge_tables line 435, _join_table line 1083); `definitions.py`; `config_loader.py` (line 1056); the 4 FACE base TOMLs.
- **Today:** Left merges never check the keys, so a repeated right-hand key adds rows silently. `dbt run` never runs tests.
- **Change:**
  1. Add a switch fail_on_repeated_keys, true in the FACE TOMLs only.
  2. After each merge, raise if rows grew, naming the table and the count, never the keys.
  3. After the filters, check (patient, visit) duplicates.
  4. Add pytests.
  5. Optional: dbt unique tests, run by R17.
- **Ships with:** R21.
- **Effect on the current files:** None once R21 is applied (0 repeated keys in the four files). Without R21, BP stops on 3 keys.
- **Other cohorts:** all.
- **Answers:** DEV-14.

### R101. Keep the gold quality pass from removing FACE visits over a perinatal value

- **Files:** `floworchestra/floworchestra/core/dags/reactor.py` (param run_quality_pass, around lines 86-89); `reactor/reactor/cli.py` (--run-quality-pass); `nucleus/nucleus/data_qa/config/studies/face/rules/clinical/ranges.yaml` and `column.yaml` (range_nullify_columns, lines 719-725); `nucleus/_standards/data/variables/bp_id_cols.yaml` (LFS).
- **Today:**
  - The quality pass is off by default in the reactor command line, but on by default in the Airflow DAG (since 0ba6402c, 2026-06-10). BPALL did not go through it: its out-of-range cells are present.
  - When it runs, a value outside the perinatal ranges (parental age 12-120, gestational age 22-44 weeks, weight 200-6000 g, length 25-70 cm, head 22-50 cm) removes that (patient, visit) from every visit-level gold table, and so from the extraction. The patient table keeps the patient, flagged is_quarantined. Zeros are turned into missing first. The two Apgar scores are already under range_nullify_columns.
  - Its TSH, LDL and haemoglobin rules also conflict with R26 and R29.
- **Change:**
  1. Keep the quality pass off for the FACE extractions, or leave the perinatal columns out of it.
  2. If the pass must run on FACE, put agemere, agepere, brthwt, brthht and brthcirc under range_nullify_columns, as the Apgar scores are. Leave gstabrth out, or put a scale_corrections rule before it (gstabrth < 11, factor 4.345): 14 gestational ages are typed in months (6 to 9), and our reader converts them to weeks.
  3. Confirm that face_bp_9_perinatalite is listed in bp_id_cols.yaml (a table without id_cols is never scanned).
- **Ships with:** none. See M34.
- **Effect on the current files:** None on BPALL. If the pass runs as configured: 56 BP visits (50 inclusions, 55 patients) leave every visit table; the cells are agepere 1, gstabrth 37, brthwt 15, brthht 2 and brthcirc 5.
- **Other cohorts:** The face config is shared: 5 SZ inclusion visits and 1 DR inclusion visit; ASP 0.
- **Answers:** none.

## Questions for the data managers (counts only the database can give)

Counts only, never codes. Each item says which requests it informs.

- **M1.** How many fondacodes have 2+ records, per cohort? Informs R1. On file: at least 18 BP patients switched record between runs; 57 BP patients switched or are delivered outside their code's centre; SZ 6, DR 0, ASP 0.
- **M2.** What values does rad_statut_visite hold, how many records, and how many in gold (BP and SZ)? Does 'Patient exclu' mean that the patient must leave the cohort? Informs R3. Not exported.
- **M3.** How many codes does the age filter drop, by reason (placeholder 1900-01, no birth date, no V0, age out of range), per cohort? Is 1900-01 typed when the date is unknown? Informs R4 and R5. On file: 0 delivered patients lack an age.
- **M4.** Why does ebipolar_patient line 16 force Feminin for 4 codes? Do the records disagree on rad_sexe? Informs R7. On file: 3 in BP (centres E, H, L), all transferred.
- **M5.** ARM list: who keeps it; the reason and date per code; the 3 conflicting codes; the '' code; the test codes; why 23 listed bipolar codes are absent. Do centres A, B and C keep their inclusion forms outside the application since 2022? After R20, how many centre C patients differ or are absent? Informs R6 and R20. On file: 509 listed patients; from 2022 listed V0 patients: A 167/210, B 55/197, C 178/178, H 0/128.
- **M6.** Per form table and centre: visits with 2+ rows, whether they differ, and whether they share an id. Patients with 2+ medicament_lifetime rows. Which centre C table holds the tab-6 copies? Does every centre copy keep the UNIQUE key on ID_fiche_clinique? Use the analysis in R18. Informs R18 and R21. On file: 1 PRISE-M visit (centre N); 7 extra rows on 3 centre C visits.
- **M7.** stop_suivi patients with 2+ rows, and with differing fields (BP and SZ). Query in R11. Informs R11. On file: one row per patient.
- **M8.** Why did 1 BP patient of BPALL_20261030 leave BPALL_20261113? The patient had a V0, an age and a birth date. Comparing the two runs finds the patient.
- **M9.** Please send the exact command, options and base TOML of BPALL_20261113_2 and SZALL_20261117. Was a thesaurus filter applied? Informs R1, R12, R36 and R54. On file: brthdtc on all rows, although it is on non_extract; dysthyro_mhmodify present although remapped; rad_tb_subst_raw present; the summary says reactor_gold_bp, 15 tables, 0 non_extract.
- **M10.** Data protection: may brthdtc be delivered (a) in full, (b) to the month, or (c) not at all? Informs R99. On file: BP, SZ and ASP are all day 15. DR: 88 of 634 patients have a real day. BP relatives' birth dates: 12,567 cells with a day other than 1 or 15.
- **M11.** Which tokens does range_overrides.json hold? For the ranges, do you prefer one row per item, or overrides? Informs R95. On file: these rows account for 2,090 unmatched names.
- **M12.** Does centre C's raw psy_diag_psychiatriquedsm5 hold rows, by year? What error led to the comment? Informs R20. On file: 0 DSM5 labels for centre C.
- **M13.** How many inclusion visits hold both a DSM-IV and a DSM-5 record, by year, centre and content? Count again after R20. Informs R70. On file: at least 25.
- **M14.** When, and on which databases, was social_diag.php run? Count the DSM-IV records holding only its 3 fields, by date_saisie. Informs R69. On file: 145 V0 records match its pairs.
- **M15.** 407 inclusion records hold only default dates without the script pattern (221 in centre A). Where is their diagnosis? Informs R69.
- **M16.** Is there a release date for the follow-up form switching to DSM-5 criteria in early 2022? On file: 11,686 follow-ups carry no edition.
- **M17.** Before 2024-01-09, did rad_pas_dechangement (fields 445 and 714) read 'Pas de changement ... ?' If so, from which date does it read 'y a-t'il une modification ...?' Informs R79 and R80.
- **M18.** psy_troubles_comorbides.rad_pas_dechangement: counts of Oui, Non, '' and NULL by year, against the four gates. When was it added? Informs R65. On file: from 2022, 1,603 of 2,835 annual visits have empty gates.
- **M19.** Please forward A31 to the eSchizo team. When did the urinary section leave the form? On file: digestive answered at 92.2% in 2019-21 against 45.8% in 2022-23.
- **M20.** Does eDepression store BIS items 1, 7, 8, 9, 10, 12, 13, 15, 21, 33 and 34 already turned? Please answer first: R83 waits for it. On file: plain sums match the stored sub-scores on 530 of 530.
- **M21.** autoq_mathys_slide: rows per centre, share of '' and '5.0', range of date_mathys (centre C first). Informs R52.
- **M22.** autoq_psqi.psqi_2: counts by pattern ('H:MM' with hours 0-4, 5-20, 21-24, 25+; 'Nh'; 'heu'; ranges; 'mn'). Informs R49. On file: 362 values above 240.
- **M23.** AIM_ against rad_aim1-40: on long-form and short-form rows, how many are null, equal the 40-item mean, equal the 20-item mean, or something else? Was aim_score meant for the 20-item form only? Informs R86. On file: 6,084 filled, all equal to the 20-item mean.
- **M24.** ALS55-60 and ALS_ against rad_als_1-54: on long-form rows, how many equal the long formulas? On the 74 ALS-18 visits without als57, is each row from autoq_als or autoq_als18? Informs R86.
- **M25.** Does the eAsperger ALS script use 11 depression items and a 6-score mean? The step's ASP entries use 10 items and the mean of the 54 items. On file: the 4 ASP values equal the step's formula.
- **M26.** Do the eDepression and eAsperger PRISE-M scripts use the eBipolar rule? Informs R87. On file: DR would lose 32 of 1,050 values, ASP 1 of 211.
- **M27.** How many EQ-5D indices start with a minus sign (BP hetero_eq5d, ASP aut_eq5d)? Any values with no digit? Informs R50 and R51. On file: 153 BP negatives (all from the step); ASP 0.
- **M28.** Is mars_score meant to run on SZ? The SZ model names item 10 MARS010, so it never runs. If it is, the item name needs a fix. On file: 62 SZ visits with no total, 2 different.
- **M29.** BP inclusions: records per raw rad_social_stprof value (Etudiant, Autres, '', NULL). Informs R38. On file: 1,150 in code 6.
- **M30.** SZ, by inclusion year: visits with a socio_demog record, answers in each old-form field (rad_social_classe included), and multi-answer income cells. Informs R45, R46 and R48. On file: 626 of 1,972 visits have no old-form status.
- **M31.** eSchizo: records with rad_chol_ldl = 'g/L' and rad_prolacti = 'mg/L', with a value, by year. Informs R27 and R29. On file: up to 1,201 and 1,818.
- **M32.** eDepression tsh_unit, t3libre_unit, t4libre_unit: options and counts. Informs R31. On file: all labels are defaults.
- **M33.** eSchizo inf_bilan_biologique: visits with 2+ records. Can you compare the rows before and after R67? Informs R67.
- **M34.** Which FACE extractions went through the gold quality pass, and is it meant to run on them? The Airflow DAG runs it by default. Informs R101. On file: BPALL did not go through it.
- **M35.** Does centre A's database have DEFAULT '2011-11-11' on date_histts_date, or on other columns? Informs R22. On file: 1,142 follow-ups, all centre A.
- **M36.** Raw BP taille texts: split into decimal, decimal under 3 and unchanged (query in the same form as R23). Informs R23. On file: 182 heights of 1000 or more; 332 not checkable.
- **M37.** Are hetero_madrs_n1 and hetero_ymrs_n1 the mood rated at testing? Are they still used, and should their dates be exported? Informs R58.
- **M38.** 21 WAIS4-labelled visits also hold a WAIS-III form. Which edition was given, and can the extra form be removed? Informs R59 and R61. On file: centres H 5, E 4, D 4, others 8; 2011-2023.
- **M39.** For our open question O40, an aggregate count on the raw uploads of the 17 centres, by centre and year: linked rows, empty rows and orphans for the main forms; medications per patient; section-date rows; the wais4_save table (C, F, K). Build it in analyses/.
- **M40.** fiche_clinique22 bypasses the export's exclusion list. Should the ingestion skip it? On file: declared in 18 of 18 BP and 16 of 16 SZ upload ymls.
- **M41.** SZ and DR each declare one upload that no staging model reads, and ASP excludes one. Is this deliberate? On file: SZ 16 uploads, 12 unioned; DR 16 and 14; ASP 10 and 9.
- **M42.** Preprocessing logs (ebipolar_ and eschizo_visit_log.csv): Case 2 and 3 entries on V1_an, V6_mois and V18_mois, with VISIT_TMP and VISITDY. How many fall outside the windows? Totals per case. Informs R13.
- **M43.** eBipolar type-5 records by year, and how many survive the preprocessing. Informs R13.
- **M44.** eDepression type_visit codes. How many (patient, centre, type) groups have 2+ active records? Informs R12, R14 and R17.
- **M45.** ASP patients with an inactive type-2 record next to an active one. Informs R15.
- **M46.** type_annuelle fill rate by type and year (BP and SZ). Informs R16.
- **M47.** MAThyS: can the form of each record (old typed form, new form) be told, by a stored version or by the date each centre switched? Informs R85. On file: 1,435 records of 2021-09 to 2022-12 cannot be placed by date.
- **M48.** BP social_bilan_social: per field (social_vie_nbpers, social_prof_dur, social_prof_durtot), how many stored texts are not one plain number: two numbers, years and months, a unit other than years, a '<' or '>'? Informs R42. On file: 5 household sizes and 5 durations out of range.
- **M49.** Which formula does eAsperger use for the BIS total bis_score: items, reversals, sum or mean, rounding? Informs R83 (step 7). On file: bis_score equals the score step's mean of bis1038 and bis1039 on 4 of 4 ASP visits, so the application's value is in no file.

## Application defects (for the developers of eBipolar and eSchizo)

- **A1.** A transfer creates a second live record with the same fondacode; the sender's record stays and is not linked. Where: admin/transfertPatient.php; gestion_site/import_patient.php line 262. Count: at least 18 BP patients; 57 switched or outside their centre; SZ 6.
- **A2.** Transfers damage characters: utf8_decode runs before the INSERT. Where: import_patient.php lines 261, 364. Count: 5 cells (centre E) plus 1 text cell; 24 cells in BPALL_20261030.
- **A3.** The .fond export writes fiche_clinique22 without the exclusion list. Where: class.tools.php lines 756-759, 888-891, 1265.
- **A4.** A visit can hold two rows of a form despite UNIQUE ID_fiche_clinique. Only the first row is shown; supprime_doublons.php deletes only identical copies. medicament_lifetime has no key on ID_patient, and its check-then-insert is not atomic (acces_formulaire.php lines 52-90). Count: 1 PRISE-M visit (centre N); 3 centre C visits.
- **A5.** stop_suivi has no unique key on ID_patient. Where: ebipolar.sql lines 9693-9694; acces_formulaire.php. Count: database only (M7).
- **A6.** End of follow-up exists in two forms: the patient form section and stop_suivi. Only stop_suivi is read by the reminders. Count: 5 patients have both (2 differ); 778 have the patient form only.
- **A7.** Scores are computed only on 'Calculer', so they go missing or stale: CTQ classes empty with complete items 67-71 per sub-score; bdhi84/85 26/37; als57 stale 11/1,382; FAST domains missing on 622 and different on 359; madrs__n1 35 missing and 5 different; SZ mars_ 62 missing; CGI index off by multiples of 4 on 81 of 9,060; DSM-IV checklist counts missing 1,952/677; Alda stale on 9/11. Where: formspecial scripts (hetero_cgi_egf.js lines 11-21, hetero_etat_patient.js lines 19-60, hetero_alda.js lines 22-41 and others).
- **A8.** QTc and the total/HDL ratio are computed live from the typed numbers, with no unit. Where: inf_dossier_infirmier_bp.js lines 139-158; inf_bilan_biologique.js lines 77-88. Count: the QTc formula holds on 7,819/7,956, the ratio on 12,626/12,648.
- **A9.** The same fields hold different scores per form, with no form recorded: aim_score (40 or 20 items) and the ALS fields. Count: 4,673 AIM-40 and 4,696 ALS-54 visits.
- **A10.** MAThyS stores no form or version, and the scale direction did not follow the form switch. Count: 1,435 visits of 2021-09 to 2022-12 not delivered; about 175 from 2023 in two centres.
- **A11.** Two ALS-18 totals exist: autoq_als.js line 96 against autoq_als18.js. Count: 74 against 1,382 visits.
- **A12.** The CTQ denial score counts a missing answer as 0 (autoq_ctq.js). Count: 36 of 42.
- **A13.** The MAThyS slider script reverses no item, its emotion score omits item 18, it is not loaded or registered, and an unmoved slider is stored empty. Count: 21 stored emotion scores equal items 3+7+10.
- **A14.** MAThyS items accept values above 10 (varchar(10)). Count: 52 cells.
- **A15.** The PSQI minutes field is free text read with parseFloat (autoq_psqi.js line 50). Count: 362 values above 240.
- **A16.** PSQI efficiency with equal times divides by zero (autoq_psqi.js lines 83-116). Count: 20 BP visits.
- **A17.** PRISE-M shows both sex items to everyone; the .php variant that hides them is not loaded. Count: 35 with both, 9 with neither.
- **A18.** The EQ-5D missing-scale check compares a NodeList with '' (hetero_eq5d.js). No effect on the index.
- **A19.** 1000-01-01 is written into every empty date on save, and 188 columns default to it. Where: recupere_formulaire.inc.php lines 428, 521. Count: 63,181 BP cells; 136 SZ.
- **A20.** psy_suicide_semestriel keeps date_histts_date (NOT NULL, no default), which the form does not show: 0000-00-00 is stored, or 2011-11-11 in centre A until 2023. Where: ebipolar.sql line 7235. Count: 8,073 and 1,142 follow-ups.
- **A21.** The Cockcroft script writes 0 when the weight is not saved (naissance.php emits a leading newline), and 'NAN' otherwise. It uses the age on the day of typing. Where: inf_bilan_biologique.js lines 28-60. Count: 246 zeros; 252 'NaN'.
- **A22.** The forms of 2009-2010 saved 0 for unknown ECG and perinatal measures. Count: 137 and 289 cells.
- **A23.** The prolactin unit choice offers mg/L (BP and SZ). Count: 295 BP results, median 12.7.
- **A24.** The bilirubin choice offers mmol/L. Count: 29 results, median 7.0.
- **A25.** The MCH choice offers ' %'. Count: 17 results.
- **A26.** The ten unit choices are optional with no default. Count: 86,805 results without a choice. The LDL choice rate was 6.5% in 2019-21 and 94.7% from 2024.
- **A27.** The TSH field rejects values above 10. Count: 44 of 8,598 before 2022, 0 of 3,442 after.
- **A28.** One inclusion visit can hold both diagnosis forms (visite.php lines 362-377). Count: at least 25.
- **A29.** No DSM edition is stored. Count: 11,686 follow-ups and 849 inclusions without one.
- **A30.** social_diag.php inserts DSM-IV records holding only the sick-leave fields and rewrites rad_social_travan. Count: 145 V0 records.
- **A31.** The eSchizo copy script stops at line 29 (urin_non is null), so the digestive, other and autoimmune shortcuts copy nothing. Where: psy_histoire_medicale.js line 29. Count: from 2022, of 545 inclusion visits with a section head answered, these sections are empty on 287, 259 and 349, against fewer than 10 for the others.
- **A32.** The eBipolar shortcut script is off (lines 6-140). Its skin list omits psoriasis, and its digestive list names absent fields. Count: 257 V0 and 193 annual visits from 2022 with all seven sections empty.
- **A33.** rad_pas_dechangement means 'changed' in two BP forms and 'unchanged' in the comorbidity form and in eSchizo. The comorbidity column is NOT NULL with no default. Where: ebipolar_data.sql lines 90668, 91458, 92897; ebipolar.sql lines 5100, 5988, 7544.
- **A34.** The pregnancy box is hidden but not cleared for men, and is shown when the sex is empty. Where: inf_dossier_infirmier_bp.js line 23. Count: 4 weighed visits with an empty sex.
- **A35.** The label 'Ouvrier non qualifiés' has a stray s. Count: 7 of 219 cells.
- **A36.** The SZ old-form job class has no display condition. Count: 20 of 41 cells on non-employed visits.
- **A37.** Apostrophes are stored with a backslash. Count: 72 of 219 cells.
- **A38.** The medication form stores no strength: posologie '' and ID '' are written into an int column. Where: medicament_psychotrope_ajout_validation.php lines 39-55, 76-77; modifier_validation.php lines 38-57, 79-87. Count: 11,589 of 11,593 BP medications from 2016; SZ 5,133 of 5,140.
- **A39.** Correcting a medication sets date_saisie to '2011-06-21 16:02:57' (modifier_validation.php line 86).
- **A40.** A screening can be dated after V0. Count: BP 26 patients (13 more than 90 days after); SZ 18, DR 14, ASP 42.
- **A41.** The visit type can be edited, and duplicate type-1/2 records exist, which shifts every label. Count: 18 follow-ups in 13 patients have a lower visitnum than their V0.
- **A42.** Type 5 has no form list but holds forms, and gets scheduled labels. Count: at least 1 certain; up to 3,352 candidates.
- **A43.** The social form's numeric checks (durations, household size) run in the browser only; the check at submit is commented out. Where: verifications.php line 280; affiche_formulaire.inc.php (compare2). Count: 5 household sizes and 5 durations out of range.
- **A44.** The two Apgar fields accept any text: peri_naissapgar1 and peri_naissapgar5 are varchar(50) with no minimum, maximum or check. Make them an integer 0-10. Where: ebipolar_data.sql, psy_histoire_medicale_nom_champ ids 188 and 189. Count: 3 cells above 10 (2009, 2014).
- **A45.** The history forms hide the children of a gate one level only: a grandchild stays filled and posted when its grandparent is cleared. Where: eCEDR formulaires.js `s_masquer` (about 20 history and 40 family fields in chains); eAsperger eASPERGER.js `masquer` (an age at menarche under a gynaecology box that is not ticked). Count: DR 2 zero cells; ASP 1 value.
- **A46.** eCEDR evaluates the lithium and valproate sub-gates before their disease gate at load, and the allergic boxes before the allergy gate, so six sub-gate fields show for a disease at yes. Where: formulaires.js, `f_psy_histoire_medical` (about line 4667). Count: no cell affected.
- **A47.** eCEDR unticks a radio by a double click without a change event, so a form can be saved with the gate empty and the children filled. Where: class.qcm.php. Count: 1 DR inclusion visit (hypertension treated and controlled).
- **A48.** eCEDR keeps the saved rows of the children and siblings tables after the count is set to none, and nothing checks the number of rows against the count. Where: tab_enfant and tab_fratrie (class.update.php). Count: 1 sibling row under counts 0 and 0 (DR).
- **A49.** The textbox 'which other autoimmune disease' of the eCEDR history forms uses the digits-only style. Where: 164.php line 189; 191.php line 179; class.javascript.js line 934. Count: text filled on 0 of 7 yes at inclusion (static reading, to confirm on the dev instance).
- **A50.** The eAsperger family gate script binds ANTFAM* while the field is ATCDFAM, so the relatives table is always shown and the gate means nothing. Where: eASPERGER.js about line 4833. Count: 305 V0 visits with a relative holding a yes; 62 have the gate at yes, 233 empty.
- **A51.** The eAsperger follow-up family form (247) holds only the change gate and no relatives table, and the follow-up forms 244 (groschang, acqchang, esichang) are retired from the menu while the columns remain. Where: global.php lines 140, 423. Count: 23 follow-ups with the family change at yes and nothing to enter.
- **A52.** The eAsperger tables atcd_* keep their rows after the section gate is set to no or unknown; only the bin icon deletes a row. Where: class.update.php line 124; class.tableau.php lines 167-178. Count: 17 V0 lists under 12,678 gates at 0 or 9.
- **A53.** The eAsperger boxes GYNCO_1..6, ANTFCT_1..3, MORUTE_1..3 and MEDNPSY_1..6 are tinyint NOT NULL DEFAULT 0 and written 0 on every save, so a 0 is not an answer. Where: easperger.sql; class.update.php lines 346-349. Count: 0 or 1 on 2,139 V0 and 149 follow-up visits; 88 V0 and 148 follow-up visits hold these boxes and no other pregnancy answer.
- **A54.** The gynaecological section is shown to men in eBipolar and eSchizo and the answers are kept. Where: the history form definitions (no sex rule). Count: BP 203 of 2,389 men's inclusion visits and 60 yearly visits; SZ 127 of 1,706 men's inclusion visits.
- **A55.** The eSchizo copy script (A31) also names three fields absent from the SZ form in its 'other diseases' handler: rad_somat_opht, rad_somatique_chirurgie, rad_somatique_pathologieautre. A null guard at line 29 would not be enough for that section.
- **A56.** The eAsperger form 193 has the pulmonary code 5 'Allergie' commented out, and the allergy gate ANTALRGI holds only 1 or empty until 2019. Where: 193.php; eASPERGER.js. Count: to 2020, 138 V0 visits with a pulmonary gate at yes and no pulmonary list, 110 of them with ANTALRGI at yes (see M54).
- **A57.** The DSM-5 diagnosis forms have no onset age of the eating disorder, and the DSM-5 form also offers 'Night eating syndrome' that the DSM-IV form does not. Where: psy_diag_psychiatriquedsm5 (BP); the SZ diagnosis form. Count: BP inclusion yes visits: the age is filled on 84% of 787 DSM-4 visits and on 2 of 232 DSM-5 visits (3 of 231 from 2022, none after); SZ 84-91% to 2018, 17% in 2019-21, 0-4% since.

## Batch 2 (2026-11-19): biology tab

Requests found by the review of the BILAN BIOLOGIQUE tab (BP D144, SZ D49, DR D33, ASP D30). Same conventions as batch 1; the numbers continue it.

| # | Title | Files (short) | Cohorts | Changes values | Priority | Answers |
|---|---|---|---|---|---|---|
| R102 | Export the sampling date and place, ferritin and corrected calcium of the biology form | ebipolar and eschizo biology tables; the BILAN BIOLOGIQUE dictionary | BP, SZ | no | medium | none |
| R103 | Check the column order of the biology tables of one centre in BP (to 2023) and one centre in DR (to 2022): blood-count values sit in the iron, HbA1c, AST, ALT, TSH and glucose fields (DR: shifted by 7 fields) | face_bp biology models; the eCEDR biology table | BP, DR | yes | medium | D144 |
| R104 | Export the unit choices of the DR drug levels (fluoxetine, venlafaxine, clomipramine) | ecedr psychotropes table | DR | no | low | none |
| R105 | The DR application writes unit code 1 (ng/mL) on every prolactin result with no unit chosen (script_unit.php): export the unit only when it was chosen, or tell us which results carry the back-fill | ecedr prolactin fields | DR | no | medium | D144 |
| R106 | The vitamin D unit by centre in SZ (one centre writes ng/mL, the form has no unit) | eschizo vitamin D field | SZ | no | low | SZ O7 |

Questions for the data managers: M50, does the DR prolactin of centres with many results of 100 or more come from mUI/L typed under the first option? M51, is the ASP CRP a high-sensitivity CRP, in mg/L or mg/dL (the form label reads mmol/L)? M52, why does a lithium, valproate or oxcarbazepine level appear without its box ticked in the shifted visits of DR?

## Batch 3 (2026-11-19): antecedents tab

Requests found by the review of the ANTECEDENTS tab (BP, SZ, DR and ASP: 77 schemas; decisions in the PROGRESS file of each cohort). Same conventions as batch 1; the numbers continue batch 2.

| # | Title | Files (short) | Cohorts | Changes values | Priority | Answers |
|---|---|---|---|---|---|---|
| R107 | Swap back the two SZ migraine columns: `rad_somatique_migraine` is the disease and `rad_somat_mig_tt` is 'treated', and eschizo_mh.sql writes them the other way round (ebipolar_mh.sql line 138 is right). The schema and its pins change in the same commit as the first extraction after the fix | dataflow clean/eschizo/eschizo_mh.sql lines 79-90 | SZ | yes | high | SZ O24, DEV-9 |
| R108 | Export CRISCONV, CRISAGE, CRISACT, CRISFREQ and ATCDLTN from aut_atcdlt: forms 193 and 347 write them there and the export reads aut_c1antmed (V0 fill 0.84 to 2019, 0.45 in 2020, 0.04 in 2021, 0 from 2022) | face_asp_6_antecedents.sql lines 172-175 | ASP | no | medium | ASP O14 |
| R109 | Read DDEBHOSP and DFINHSOP for the year and length of a hospitalisation (the export reads ANDEBHOSP and DURHOSP: the year is filled on 3 of 185 records to 2019 and the length only from 2020; follow-up form 248 writes DDEBHOSP and DFINHSOP too) | easperger_hospitalisation_agg.sql | ASP | no | medium | ASP O14 |
| R110 | Export every row of the DR children and siblings tables with the sex and the row gate, in a fixed order: `select distinct on (usubjid, visitnum)` without ORDER BY keeps one arbitrary affected relative per group | face_dr_13_antecedents.sql | DR | yes | medium | DR O29, PI-2 |
| R111 | Export the onset date of another cardiovascular disease of the DR follow-up form (C44 of form 191), absent from the dictionary and the extraction | ecedr 191.php line 54 | DR | no | low | none |
| R112 | Correct the BP dictionary: the CODAGE of dyslipid_MHDECOD_eq holds a stray 'mere_structure'; traumacra_MHOCCUR has no CODAGE; the 52 family `trouble` and `suicide` columns say Y/N/U for labels; alcool, cannabis and autre_substance say Y=Yes for 0/1 values | thesaurus FACEBP ANTECEDENTS | BP | no | low | none |

Questions for the data managers: M53, BP `frere2_suicide` is filled in 42% of the sibling blocks (74 of 178) while the other siblings, children and parents are at 90% to 100%, in all 15 centres and every year: does the application store the answer? M54, was the pulmonary code 'Allergie' (code 5 of the eAsperger form 193) migrated to the allergy gate in 2020 and its rows deleted, as the pulmonary gate at yes without a list (138 visits to 2020, 110 with the allergy gate at yes) suggests? M55, did the SZ migraine question, its practice or the form change in 2018 (the yes share at inclusion falls from 11.6% in 2011-2017 to 4.6% in 2018-2026, at four of the centres only)? M56, is the SZ hormone therapy of the menopause never at yes by loss (0 yes of 39 answers; BP 98 of 783, DR 36 of 412)? M57, can the DR textbox 'which other autoimmune disease' take letters (filled on 0 of 7 yes)? M58, are the onset dates after the visit date (BP 61 of 9,966 delivered dates, DR 4 of 866 at inclusion; 11 before the birth year in BP) typed errors worth sending back to the centres? M59, can the eAsperger list tables save a row with no disease code (19 rows, 14 of them empty)? M60, did the SZ family form or its practice change around 2018 (the mother is 'affected' for 43% of the inclusion visits to 2017 and 30% since, the father 43% and 32%, while the siblings, the psychiatric first-degree columns and BP do not move)?

## Batch 4 (2026-11-19): substances and comorbidities tab

Requests found by the review of the SUBSTANCES ET COMORBIDITE tab (BP, SZ and DR: 22 schemas; decisions in the PROGRESS file of each cohort). Same conventions as batch 1; the numbers continue batch 3.

| # | Title | Files (short) | Cohorts | Changes values | Priority | Answers |
|---|---|---|---|---|---|---|
| R113 | Build the BP panic columns from the form's type list: `ceoccurtroubpanago` is 1 when the choice list holds 'Trouble panique' and 'Phobie sociale' and `ceoccurtroubpansago` when it holds panic and not social phobia (the type list `chk_anxieux_trouble_panique_type` is not exported); the 'panic disorder' column uses `ILIKE '%Trouble panique%'`, which also matches 'Agoraphobie sans trouble panique' (395 visits: agoraphobia ticked, panic ticked; 361 of them with no panic detail). Match the elements of the set, not substrings (the same pattern builds the 20 sets of the tab) | face_bp_6_substances_comorbidites.sql lines 21-22, 30 | BP | yes | high | BP DM-6, DM-7 |
| R114 | Fix the SZ anxiety columns that hold another form field: `CEOCCURtroubpansago` holds `rad_trouble_panique` (panic disorder, with or without agoraphobia), `CEOCCURtoc` holds `rad_trouble_obsessionnel` instead of `rad_trouble_compulsif`, `CEOCCURanxietegeneral` holds `rad_anxieux` (a screening question), `CEOCCURtroubanxaffmed` holds `rad_anxieux_generalise_titre`, `CEOCCURtroubpanago` holds `rad_peur_agoraphobie`; export the panic type list `chk_anxieux_trouble_panique_type`. The schema names the variables for what the columns hold; it changes in the same commit as the first extraction after the fix | eschizo_psy_diag.sql; face_sz_6_substances_comorbidites.sql | SZ | yes | high | SZ O19 |
| R115 | Export the questions of the yearly SZ comorbidity form: `chk_troubles_anxieux_choix`, the past month of each disorder, `rad_tb_alim` with its type and past month (the model reads only `rad_tb_anx` and the substance columns; lines 62-63 are commented out: 2,588 yearly visits hold no cell of eating or anxiety detail) | face_sz_6_substances_comorbidites.sql | SZ | no | medium | SZ DM-8 |
| R116 | SZ substances at inclusion: `rad_tb_subst` is built from the addicto flags ('Oui' any box Y: 590; 'Non' all six N: 18; 'Ne sais pas' 975, of which 925 have `rad_add_4` = Non and the five drug columns blank): read `rad_add_4` = Non as N for the five drug groups (then 'Non' 826 and 'Ne sais pas' 167); export `rad_tb_subst_raw`, the per-substance type, month, age and duration of the yearly form, `rad_add_autre4e2` and the other-product details (a dose on 71 of 186 yes visits) | addicto_flags in the SZ model; eschizo addicto form | SZ | yes | medium | SZ O20, O21 |
| R117 | BP comorbidities: keep the non-numeric onset ages ('Ne sais pas', '<5', '>89') as tokens instead of NULL (the cast `^[0-9]+$` drops them: the empty age under a ticked box, 26-70%, mixes unknown and unanswered); export the substance-induced disorder block `rad_tb_substind`, `chk_tb_substind_sub`, `chk_tb_substind_typ`, `rad_tb_substindpres` (in the clean model, in neither the dictionary nor the extraction) | ebipolar_comorbide.sql lines 10-135; ebipolar_psy_diag.sql line 25; face_bp_6 | BP | yes | medium | BP DM-7 |
| R118 | SZ tea and coffee: export the 12-month frequency category (the dictionary maps two form fields to the same name `SUDOSFRQ_theLY` / `SUDOSFRQ_cafeLY`; only the numbers 1-7 are exported: 841 and 1,965 cells; 'weekly or less' is lost) | SZ addicto model; dictionary SUBSTANCES ET COMORBIDITE | SZ | no | low | none |
| R119 | Correct the substance rows of the BP dictionary: the 8 `SUOCCUR_*` rows say Y/N/U for 0/1 values (empty for unknown); `rad_tb_subst_raw` has no row; the `ABUDEP_autre` label is wrong | thesaurus FACEBP SUBSTANCES ET COMORBIDITE | BP | no | low | none |
| R120 | Export form fields that the SZ and BP forms hold and the extraction does not: SZ tobacco (age of the strongest dependence, treatment for tobacco use), SZ cannabis, alcohol, sedatives, heroin, cocaine, opiates and other products (treatment for the use; hospitalisation for withdrawal: yes, number, age), BP nicotine substitution and its type | eschizo addicto form; ebipolar nursing file | BP, SZ | no | low | none |
| R121 | Correct the DR dictionary rows of the SUBSTANCES sheet: SUOCCUR_CANNABIS_LT (DCCAN, 'Consommez-vous du cannabis ?') is listed for v0 with Y, N and U, but the extraction holds 1 and 0 (never unknown) at inclusion (429 visits), 2 years (92), 4 years (57) and 4 other visits, and none at 6, 12, 18 and 30 months; the name copies the lifetime question of SZ, while the question is about the present. The four tobacco rows list v0, 6 months and 1 year and are filled at 18 months, 2 and 4 years too | thesaurus FACEDR V4.16 SUBSTANCES | DR | no | low | DR DM-7, DM-8 |

Questions for the data managers: M61, the SZ form says 'ten months' for the generalised-anxiety screening (nervous or anxious in the last ten months): is it a typo for six? M62, why are the details of a ticked BP substance box left empty on 17 to 18% of the ticked boxes (all four details empty), 4% to 67% by centre at inclusion (6% to 53% at the yearly visits) for the type, and why is the yes share of the substance gate highest in one centre? M63, does the dataflow gate correction (`rad_tb_anx` to 'Oui' on evidence) run on BPALL? 14 inclusion and 7 follow-up visits show a 'no' with evidence.
