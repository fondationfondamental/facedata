<!-- facedata:start (facedata {version}; written by `facedata init`: run it again after an upgrade) -->
## FACE cohort data (facedata)

This project analyses the FACE cohorts with the Python package `facedata`:
BP (bipolar disorder), SZ (schizophrenia), DR (treatment-resistant depression)
and ASP (autism spectrum, children and adults).
`from facedata import bp; result = bp.load("/path/to/<extraction>.tsv", norms="/path/to/norms")`
returns six tables: `result.data` (one row per visit), `result.patients`,
`result.flags`, `result.qc`, `result.treatments` and `result.relatives`.

Before choosing or using a variable:

- Read the guide that ships with the package: `facedata guide`, or one section
  at a time with `facedata guide --section 4`. Sections 1 to 4 first (loading,
  the rules, the cohorts, their visits and their traps); section 5 before
  comparing or stacking cohorts (5.1 shared instruments, 5.2 the same subject
  under other instruments, 5.3 editions, 5.4 constructs).
- Find variables with `facedata find <words> [--cohort bp] [--level score]`,
  and read records with `facedata show <variable or instrument> ...` (JSON).
  A variable id is the column name that `load()` delivers. Do not print the
  whole dictionary JSON (18 MB). For people, `facedata page` opens the
  searchable page.
- In a record, check `direction` before putting variables on one scale,
  `harmonisation` before stacking cohorts, `missing` and `timepoints` before a
  longitudinal model, `edition`, and the `flags` of the instrument. An empty
  field means "not documented" (its name is in `incomplete`): say so, never
  fill it from memory. A count of -1 means "fewer than 5".
- Two editions or forms of an instrument (WAIS-III and WAIS-IV, BIS-10 and
  BIS-12, child and adult forms, the inclusion `_v0` and follow-up `_fu`
  questions) are separate columns: never merge them. Instruments that measure
  one subject in different cohorts (MADRS, Calgary, HAM-D) are not on one scale.
- If the command `facedata` is not found, run `python -m facedata ...` (or
  `uv run facedata ...` in a uv project).

Patient data:

- The tables are pseudonymised patient records. Report aggregates only. Never
  print, paste or commit patient rows, identifiers (`usubjid`, `fondacode`),
  the dates of a patient, or the values of a text column. Write a count from 1
  to 4 as "fewer than 5", and do not name centres.
- Keep the extractions and the norm tables out of git. The norm tables are
  copyrighted: never copy a value of them into code or notes. Save notebooks
  without their outputs.
<!-- facedata:end -->
