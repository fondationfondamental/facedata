# facedata — architecture

`facedata` reads an extraction of a FACE cohort and returns data that are
ready for algorithms:

1. every value is parsed into one clean type,
2. units, censored values and instrument versions are harmonised,
3. whatever could not be harmonised is flagged, never silently kept or dropped,
4. continuous variables are winsorised,
5. every variable gets a quality-control (QC) summary and plots.

There is one module per cohort (`facedata.bp`, `facedata.sz`, `facedata.dr`, `facedata.asp`).
Everything specific to an instrument is written in a YAML schema
(see [SCHEMA_SPEC.md](SCHEMA_SPEC.md)). The Python code is generic and does not
change when an instrument is added.

Out of scope: imputation, scaling, one-hot encoding. Missing stays missing.

## 1. Source data

| Fact | Consequence |
|---|---|
| Each cohort has one extraction, one row per patient visit and one column per variable (BP: 22,178 × 2,236) | The pipeline works column by column |
| `.csv`, `.tsv` and `_sc.csv` hold the same content; the `.xlsx` has types already coerced by Excel | The source is the `.tsv`, read as text |
| The data dictionary (thesaurus) maps names and labels but has no types, units, ranges, missing codes or versions | Schemas carry that information; the thesaurus only seeds them |
| Key columns have the same names in all four cohorts | Keys and visits are handled once, in generic code |

Reading rule, used everywhere:

```python
pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")
```

Every cell arrives as a string, exactly as written. Nothing is guessed.

## 2. Package layout

```
facedata/
  schema.py       load_schema(), check_schema()
  tokens.py       constants only: missing tokens, placeholder dates, flag codes
  flags.py        make_flags(), stack_flags(), finish_flags(): the flag log
  read.py         read_extraction(), read_norms(), prepare_visits()
  parse.py        clean_text(), split_missing(), parse_number(), parse_item(), parse_boxes(),
                  parse_category(), parse_date(), parse_time(), parse_column()
  harmonise.py    detect_version(), convert_units(), fix_sign(), check_range(),
                  compute_scores(), collapse_patient_level(), winsorise()
  pipeline.py     read_variable(), run_instrument(), run_cohort(): the ordered steps, nothing else
  treatments.py   open_lists(), unpack(), look_up_names(), at_visit(): cells that hold lists (treatments) or several records
  relatives.py    stack_relatives(), summarise_relatives(): the same questions asked for each relative
  qc.py           qc_table(), coverage()
  plots.py        plot_variable(), plot_instrument()
  report.py       write_report()
  thesaurus.py    read_thesaurus(), draft_schema(): a helper, never used by load()
  custom.py       the rare named functions a schema refers to
  common.py       catalogue(), instruments_of(), baseline(): the cohorts together (never used by load())
  medications.csv the table of medication names (molecule, ATC code, group), shared by the cohorts
  shared_names.yaml        the variables that two cohorts cannot name or fill alike, each with the reason
  common_instruments.yaml  the instruments that two cohorts or more share: which stack, which variables, what differs
  bp/
    __init__.py   load(), report(), coverage()
    ignored.yaml  columns deliberately left out, each with a reason
    schemas/<tab>/<instrument>.yaml
  sz/             the same three functions and files for FACE SZ, and
    differences.yaml   the instruments whose schema is not the BP one, each with the reason
  dr/             the same for FACE DR (resistant depression); its differences.yaml compares with BP, or with SZ where BP has no such schema
  asp/            the same for FACE ASP (autism spectrum); the dictionary arrived after the module, so a schema folder is a source table of the export; differences.yaml compares with BP, then SZ, then DR
tests/            small hand-written tables only
```

## 3. Public API

```python
from facedata import bp

result = bp.load("data/bp/BPALL_20261113_2.tsv")              # every instrument that has a schema
result = bp.load(path, instruments=["madrs", "biochimie"])  # or only some
result = bp.load(path, norms="norms")                       # folder of the norm tables (the default)

result.data       # one row per patient visit
result.patients   # one row per patient
result.flags      # one row per flagged cell
result.qc         # one row per variable
result.treatments # one row per patient and medication
result.relatives  # one row per patient and relative

bp.report(result, "reports/bp")                              # HTML report and plots
bp.coverage(path, "thesauri/FACEBP_thesaurus_V4.34.xlsx")    # which columns have a schema
bp.load(new_path, winsor_limits=result.qc)                   # reuse winsor limits on new data
bp.load(path, winsorise=False)                               # leave the tails of the continuous variables as they are
```

`result` is a named tuple of six DataFrames.

Across cohorts:

```python
from facedata import bp, sz, common

table = common.catalogue()                                   # the instruments that two cohorts or more share
bp.load(path, instruments=common.instruments_of("bp", table), winsorise=False)
first, source = common.baseline(result)                      # one row per patient: inclusion, completed by screening
first, source = common.baseline(result, max_days=90)         # the screening visit only when it is at most 90 days away
```

## 4. What `load()` returns

### `data`: one row per patient visit

Key columns first, then the harmonised variables of every instrument.

| Column | Content |
|---|---|
| `cohort` | `bp`, `sz`, `dr` or `asp`. First column of `data`, `patients`, `flags`, `treatments` and `relatives` |
| `usubjid` | Patient identifier (text), unique inside a cohort only |
| `visit` | Visit label as extracted (`V0`, `V6_mois`, `V1_an`, ...). The export writes it: the planned time point, from windows of six months on the days since the inclusion record, chosen by the visit type; not the visit type itself (requests R12 and R13 of [EXPORT_REQUESTS.md](EXPORT_REQUESTS.md)) |
| `visit_order` | Rank of the visit (from `id_visit`) |
| `visit_month` | Planned months since inclusion, read from the label (`V0` = 0, `V6_mois` = 6, `V1_an` = 12) |
| `visit_date` | Visit date (from `svdtc`) |
| `siteid` | Centre (text, leading zeros kept) |
| `age` | Age at the visit, in years with decimals (from `brthdtc` and the visit date). The BP, SZ and ASP exports give the date of birth to the month only, so it is exact to about two weeks; the DR export keeps the day for 88 patients, which the DR schema sets to the 15th |
| harmonised variables | Numbers are floats in the schema's unit, categories are harmonised labels, dates are dates |

(`usubjid`, `visit`) is unique inside a cohort: the export's visit preprocessing merges or deletes the records that share a label, and the real-data tests check it.

**Putting two cohorts together.** The tables of two cohorts have the same key
columns and the same names for the instruments they share, so they can be
stacked (`pd.concat`). A name holds the same thing in every cohort (the same
kind of value, unit, table and labels), and a raw column that the cohorts
share has one name; the few exceptions are written, each with its reason, in
`facedata/shared_names.yaml`, and `tests/test_cohorts.py` fails on any other. The key is then (`cohort`, `usubjid`, `visit`): a
`usubjid` is a number given inside a cohort, and 824 numbers are used in both
FACE BP and FACE SZ for different patients (199 FACE DR numbers are also BP
numbers, and 209 are SZ numbers). Never join two cohorts on
`usubjid` alone. `patients` also holds `fondacode`, the patient code of the
foundation: it is unique across the cohorts, and it stays the same from one
extraction to the next, while `usubjid` can change for a patient registered
in two centres.

**The common instruments.** `facedata/common_instruments.yaml` lists the
instruments that two cohorts or more deliver, one entry each: the name of its
schema in each cohort (the errands test is in `executive_functions` in FACE
ASP), a verdict `stack` (`yes`: the same form, coding and scoring; `with
care`: read the note first; `no`: the same name or subject, not the same
thing), the variables to `use` across cohorts and a `note` on what differs.
It is written by hand, after the schemas were compared variable by variable
and the values compared on the extractions: the answers of each item, the
range of each score, the direction of each item against its score, the sign
of each z-score, the unit of each measurement. `common.catalogue()` reads it
as a table, `common.instruments_of(cohort, table)` gives the names to load,
and `tests/test_common.py` fails when two cohorts share an instrument that
the file does not list, when it names a schema that does not exist, or when a
variable to use is not delivered by two cohorts of the entry. Across cohorts
the tables are loaded with `winsorise=False`: the winsor limits are computed
inside a cohort, so the same value could be clipped in one cohort and not in
another.

**One baseline row per patient.** The screening visit and the inclusion visit
are two rows of `data`, and an instrument may be filled at the one or at the
other (the MDQ of FACE BP at screening only; the MINI of FACE DR at
screening). `common.baseline(result)` returns one row per patient, named
`baseline`: each instrument is taken from the inclusion visit, and when the
inclusion visit holds nothing of an instrument, the instrument is taken whole
from the screening visit, so that its items and its scores always come from
the same visit. The instrument of a column is read in `qc`; a censoring
column goes with its variable; the first columns (date, centre, age) are
those of the inclusion visit, and `screening_date` and `days_from_screening`
are added. A second table gives, per patient and instrument, the visit the
values come from. The two visits can be far apart (a median of 70 days in
FACE BP, 34 in SZ, 10 in DR, 25 in ASP, and more than a year for 6%, 1%, 1%
and 10% of the patients who have both): `max_days` leaves out a screening
visit that is further than that from the inclusion. The flags keep the name
of the real visit.

Two kinds of companion column travel with the variables, because a model
needs them:

| Column | Meaning |
|---|---|
| `<variable>_cens` | −1 left-censored (true value is below the stored one), 0 observed, +1 right-censored. Present only for variables that have censored values |
| a version column | Which edition or form of an instrument was used at that visit, e.g. `wais_version` = `wais3` or `wais4`, `bis_form` = `bis10` or `bis12` |

Each edition or form of an instrument has its own columns (`wais3_...`,
`wais4_...`, `bis10_...`, `bis12_...`). One output column never holds two
editions.

### `patients`: one row per patient

Variables whose schema says `level: patient` (demographics, lifetime
history), with `cohort`, `usubjid` and `fondacode` first. They are repeated on every visit row in the extraction; here they
appear once. The table also holds the yes/no columns that sum up the
relatives of the patient (below).

### `treatments`: one row per patient and treatment

The extraction stores the treatments of a patient as lists in one cell, the
same on every row of the patient. An instrument whose schema says `level:
list` opens them: one row per patient and item, with `usubjid`, `item` (1,
2, 3...) and the variables of the schema (the name as written, the molecule
and the group it belongs to, the dose, the start and end dates). The table
is empty when no such instrument is loaded.

A cohort can have several such instruments (FACE DR has three: the current
psychotropic treatments, the past ones and the somatic ones). Their rows are
stacked, and a column `list` after `usubjid` names the instrument of each
row. Where the export crossed the products of a patient with the
prescription lines, the schema says so (`crossed`), and the items are put
back as far as the file allows (SCHEMA_SPEC, section 15).

What a visit needs, whether the patient was on a treatment that day, is
computed from the dates of the items and delivered in `data` as yes/no
columns (SCHEMA_SPEC, section 15).

Two other shapes go through the same machinery (SCHEMA_SPEC, section 15).
In FACE ASP the treatment list belongs to a visit, not to the patient
(`per_visit`): every row that holds a list is opened, and the table has a
column `visit`. And one export packs several records in a cell,
`(a - b - c) | (a - b - c)`: the diseases of a body system, the relatives,
the hospitalisations. `packed` opens them into one row per record, in lists
of their own (FACE ASP has eleven lists).

### `relatives`: one row per patient and relative

The family history asks the same questions for the mother, the father, each
sister and so on, in one set of columns per relative. An instrument whose
schema says `level: relatives` puts them under one another: one row per
patient and relative about whom something is known, with `usubjid`,
`relative` (`mother`, `sister_1`...) and the variables of the schema. A
family is described once: for each relative and question the first visit
that holds an answer is read. The table is empty when no such instrument is
loaded.

What an analysis most often needs, whether a relative of the patient has a
given disorder, is computed from these rows and delivered in `patients` as
columns that are 1, 0 or missing: missing when it cannot be told
(SCHEMA_SPEC, section 16).

### `flags`: one row per flagged cell

| Column | Content |
|---|---|
| `usubjid`, `visit` | Where. For a row of `treatments`, `visit` holds `item 3` (`medications item 3` in a cohort that has several lists); for a row of `relatives`, the name of the relative |
| `variable` | Output variable name |
| `raw` | The original string, untouched |
| `value` | The value now in `data` (empty if removed). For a variable that is read but not delivered (`keep: false`), the value used for the checks |
| `flag` | Flag code, see section 6 |
| `severity` | `info`, `discrepancy` or `danger` |
| `detail` | Short explanation, e.g. `g/L -> mmol/L`, `limit 5`, `stored 32, computed 27` |

A cell with several flags has several rows.

### `qc`: one row per variable

See section 7.

### The invariant

> Every non-empty raw cell of a schema variable ends either as a value in
> `data` / `patients`, or as a row in `flags`.

Nothing disappears silently. A test checks this for each instrument. A
stored score that is read only to be compared (`keep: false`) follows the
same rule: where the score cannot be recomputed, the row is flagged
`score_not_recomputed` and the flag log holds what was stored.
"Empty" means the empty string and `0000-00-00` (the export's empty date),
once the text repairs of step 3 are done: a cell that holds only an escaped
line break is empty (two cells of the BP extraction).

An empty cell gets a value in one case only: a yes/no question or a count
that the form asks only after a yes to another question (`asked_if` in the
schema) is 0 where that other answer is no. A patient with no anxiety
disorder has no panic disorder; with no mood episode in the past year, the
number of depressive episodes of that year is 0. These values get no flag.

## 5. The pipeline

All steps are generic. They run once per instrument, in this order.

| # | Function | What it does |
|---|---|---|
| 1 | `read_extraction(path)` | Reads the TSV as text |
| 2 | `prepare_visits(raw)` | Drops duplicated visit records, builds the key columns |
| 3 | `clean_text(column)` | Repairs text damage without changing meaning |
| 4 | `detect_version(raw, schema)` | Works out the instrument version of each row |
| 5 | `split_missing(column, variable)` | Turns missing codes into missing values |
| 6 | `parse_<type>(column, variable)` | Turns strings into numbers, categories, dates; separates censoring marks |
| 7 | `convert_units(values, labels, variable)` | Brings numbers to the schema's unit |
| 8 | `fix_sign(data, schema)` | Brings standard scores to one sign convention |
| 9 | `check_range(values, variable)` | Removes impossible values |
| 10 | `compute_scores(data, schema)` | Recomputes scores from items, compares with stored scores |
| 11 | `collapse_patient_level(data, schema)` | One value per patient for patient-level variables |
| 12 | `winsorise(values, limits)` | Clips the tails of continuous variables |
| 13 | `qc_table(...)` | One QC row per variable |

Steps 3, 5 to 7 and 9 run once per variable. Each returns the cleaned values
and a small table of flags. `run_instrument()` only calls them in order and
stacks the flags.

### Step 1: reading

Every cell is read as text. One export (FACE ASP) wrote its accents twice
over: "dÃ©pression" is "dépression" read as Latin-1 and encoded again. The
loader of that cohort asks the reader to put these cells back
(`repair_accents`); a cell that the way back cannot decode stays as written.
The SZ and DR extractions hold the same defect in a few hundred cells of
free text, which are not repaired.

### Step 2: visits

- Rows with the same `visitnum` are exact duplicates; one is kept
  (`duplicate_row`).
- `visit_month` comes from the label: `V<n>_mois` is n months, `V<n>_an(s)` is
  12 × n months, `V0` is 0.
- `screening` is a visit of its own, before `V0`. It has no `visit_month`:
  it took place a median of 70 days before the inclusion, with a wide spread.
  In BP it is dated after `V0` for 26 patients (`visit_order`).
- Placeholder visit dates (`1950-01-01`) become missing (`date_placeholder`).
- A visit dated before the cohort opened (each cohort module gives the day)
  or after today has an impossible date: it becomes missing (`out_of_range`
  on `visit_date`), and so does the age at that visit. An age below 0 or
  above 110 years is missing too (`out_of_range` on `age`).
- `siteid` is written with two digits (`4` becomes `04`): one extraction
  writes the centre codes as numbers, the others as two characters.
- A patient whose visit dates do not increase with the visit order gets
  `visit_order` on the visits concerned.

### Step 3: text repairs

Applied to every cell; none changes meaning, so none is flagged.

| Damage | Repair |
|---|---|
| Leading or trailing spaces | Stripped |
| HTML entities (`&gt;`, `&#8805;`) | Decoded |
| Backslash before an apostrophe (`d\'une`) | Removed |
| Literal `\n` or `\r\n` written as text | Replaced by a space |

### Step 5: missing codes

Tokens that mean "no value" become missing and get `missing_code`, with the
reason in `detail`. Matching ignores case.

| Reason | Tokens |
|---|---|
| `unknown` | `Ne sais pas`, `ne sait pas`, `NSP`, `?`, `inconnu` |
| `not_applicable` | `Non applicable`, `NA`, `N/A` |
| `not_recorded` | `Non renseigné`, `NR`, `NC`, `.` |
| `not_a_number` | `NaN`, `None`, `null`, `Infinity`, `-Infinity` |

Placeholder dates (`1000-01-01`, `1850-01-01`, `1900-01-01`) get
`date_placeholder`. A schema can add tokens for one variable (for example `0`
meaning "not done"). A token that the variable's own `codes` lists is a value,
not a missing code.

### Variables in several columns

When the extraction moved a variable to a new column, the schema lists both.
Steps 3 and 5 run on each column, then the first column that holds a value is
kept. Two columns with different values on the same row give
`column_conflict`.

### Step 6: parsing

| Type | Accepted | Repairs flagged `format_repaired` |
|---|---|---|
| `number` | Integer or decimal, optional sign, optional `<`, `>`, `<=`, `>=` in front | Decimal comma (`27,90`), missing leading zero (`.45`), trailing dot (`28.2.`), trailing `%`, space after the sign |
| `item` | Whole number | Same |
| `band` | A percentile band (`25 - 50`), a one-sided class (`>95`) or a limit (`50`); the value is the lower limit of the band | none; a one-sided or wide band gives `censored_right` or `censored_left` (SCHEMA_SPEC.md, section 6) |
| `category` | A key of the variable's `codes`, ignoring case and spaces | none |
| `date` | `YYYY-MM-DD`, or `DD/MM/YYYY` | Partial dates `YYYY-00-00` and `YYYY-MM-00` (or `MM/YYYY` and `YYYY`) become the middle of the period (`date_partial`). With `day`, a date that kept its real day gets the day that the export writes for the others (`date_partial`) |
| `time` | `HH:MM` or `HH:MM:SS`, returned as hours | none |
| `text` | Anything | none |

An item, a number or a band can list `codes`: the raw text is replaced by the code's
number first, so that answers written `Y` and `N` become 1 and 0.

A censoring mark gives the value (the limit) and `<variable>_cens`, with
`censored_left` or `censored_right`. Whatever is still not understood becomes
missing with `unparsed` (or `unknown_code` for a category).

### Step 7: units

Each unit named in a schema has a conversion factor (and an offset for a
scale with another zero, such as an HbA1c in mmol/mol) and an expected range
of values in its own scale. The rule is the same for every variable.

| Unit label | The value fits | Result | Flag |
|---|---|---|---|
| Known | The labelled unit's expected range | Converted from the labelled unit | none, or `unit_converted` if it is not the target unit |
| Known | Not the labelled unit's range, exactly one other unit's | Converted from the other unit | `unit_inferred` if the value is impossible under the label, otherwise `unit_doubt` |
| Unknown or empty | Exactly one unit's range | Converted from that unit | `unit_inferred`; none when there is no label at all and the unit is the schema's own |
| Unknown or empty | Several units' ranges | Missing | `unit_unknown` |
| Any | No unit's range | Converted from the labelled unit (target unit if unknown) | none here; step 9 decides |

Censoring limits go through the same rule. A label that is a censoring
mark (`inf`) is not a unit label: it counts as no label at all, and so does
a label listed in `ignore_units`. Variables without a unit column
(ECG intervals in seconds or milliseconds, height with a lost decimal point)
use the same rule with an empty label.

Two additions, both written in the schema (SCHEMA_SPEC.md, section 5):

- A unit can be a **percentage of another variable** of the same visit (a
  kind of white cells as a percentage of the leukocytes). Its factor is that
  other value divided by 100, row by row. Where the other value is missing
  or out of range, the cell becomes missing and gets `unit_unknown`.
- A variable can name a **unit rule**, a function of `custom.py`, for the
  values with no usable label. Where the rule names a unit, it replaces the
  two "unknown or empty" lines of the table. Where it cannot tell, the table
  applies.

### Step 4 and versions

The extraction sometimes stores two editions or forms of an instrument in the
same raw columns: BIS-10 and BIS-12, WAIS-III and WAIS-IV. The rule is that
**a change of instrument is never hidden inside an output column**. Each
edition has its own schema and its own output columns, and reads only its own
visits.

A schema says how to recognise its visits: from a version column
(`wais_version`), from which items are filled (BIS), or from a column that is
filled once per patient (the DSM criteria, recorded at inclusion). The items
may be those of another questionnaire of the same visit, when the
instrument's own columns do not tell its form (ALS, WURS, AIM). A child form
and an adult form with the same items are told apart by the age at the visit
(the SRS filled by a relative, in ASP).
`detect_version` gives every visit its edition; each variable is then read
only on the visits of its schema's edition and is missing elsewhere, without
a flag.

When the version is recorded once per patient, a visit takes, in this order:
its own value; the version that the schema gives to follow-up visits from a
certain date (from 2022 every follow-up used the DSM-5 form); the value of
the patient's earliest visit that has one; and, for a patient with no value
at all, the version that the schema attaches to the patient's inclusion date
(`version_inferred`).

A visit with data but no recognisable edition gets `version_unknown`, and the
variables that depend on the edition are missing. The same holds for a visit
dated before the day its edition came into use, when the schema gives that
day (`since`).

### Step 8: sign conventions

Only for instruments whose schema has a `sign` block. Some z-scores were
written with one sign in the early years and the opposite sign later, and
each centre changed at its own date. `fix_sign` finds that date in each
centre and brings every value to the convention the schema asks for.

For one centre:

1. Take the visits that have a date. For each pair of the schema (a standard
   score and its raw value), compute the rank correlation between the two,
   and average over the pairs.
2. Try each month as the switch date: multiply the standard scores dated
   before it by −1 and compute the same average. Keep the month that brings
   the average closest to the wanted relation.
3. Accept the switch only if at least 10 visits lie before it and, before
   it, the scores as written clearly move the wrong way: a mean rank
   correlation of 0.5 or more in the wrong direction. Where they move the
   wrong way less clearly, the early scores of the centre are a mixture of
   the two conventions: nothing is flipped, and they get `sign_doubt`.
   Otherwise nothing is changed in that centre.
4. Standard scores dated before the switch are multiplied by −1 and get
   `sign_flipped`. Those dated within 90 days of it, before or after, also
   get `sign_doubt`, because a centre does not change on a single day. A
   standard score on a visit without a date is kept as written and gets
   `sign_doubt`.

The switch dates are found again at each load, from the data. They are listed
on the instrument's report page. An extraction with few visits per centre
gives no switch date, and nothing is flipped.

A schema can also give the date itself (`before`) with the variables to turn
(`turn`), when a form changed the direction in which it stores some answers.
Nothing is searched then: the values of the visits dated before that day are
turned around the middle of their range (or multiplied by −1 when they have
no range) and get `sign_flipped`; those within 90 days of the day, and those
of a visit without a date, get `sign_doubt`.

### Step 9: range

A value outside the schema's hard `range` is impossible. It becomes missing
with `out_of_range`. It is never clipped into range. Times (hours) and dates have a range too:
a date before the cohort existed, or far in the future, is impossible.

A schema can also name a period in which a column is not reliable (`doubt`).
The values of the visits dated in that period are possible, so they are
kept, but they get `period_doubt`: the analyst decides. Where most of the
doubted values are known to be wrong, the schema asks for them not to be
delivered (`remove: true`): they become missing and get `period_removed`.
They are removed as soon as they are read, so that no answer is inferred
from them (a count set to 0 after a removed "no").

### Step 10: scores

Scores are recomputed from the harmonised items (sum, mean or highest item,
with reverse items; an answer can count other points than its code; a sum
can subtract other values and have a floor). A score that is a
formula, such as a body mass index, is a small function in `custom.py`. When the extraction also stores the score, the two are compared; a
difference above 0.01 gives `score_mismatch` and the recomputed value is kept.
Where the stored score exists and the score cannot be recomputed (an item is
missing), neither is delivered and the row gets `score_not_recomputed`, with
the stored value in `detail`. A check that is not delivered (`keep: false`)
files its `score_mismatch` under the stored value it checks, which is the
column the analyst sees.

A form can let the clinician type a total without its items. Where the schema
says so (`otherwise`), a score with no item recorded is delivered as stored
and gets `score_as_stored`. So does every total built on such a score: the
rule that produced a typed value cannot be checked.

A score can also be read in a norm table, from a raw score and the age at
the visit (a scaled score), and if the table says so from a second variable
such as the years of education (the percentile bands of the TMT errors). The
tables are copyrighted and are not in the repository; `load()` reads them
from a folder. A raw score for which nothing can be read gets `norm_missing`.

Where the norms give a regression and not a table (the CVLT), a z-score is
computed from the raw score, the age at the visit and the other variables of
the regression (years of education, sex); the coefficients are a file of the
same folder. A band can then be read in a table for the ages that have one
and be the band of the z-score for the others (SCHEMA_SPEC, section 8).

Some stored values were computed by the EMR from another value (a scaled
score from a raw total). Where the check of that other value fails, such a
value is kept and gets `derived_doubt`.

### Step 11: patient level

For `level: patient` variables the first non-missing value in visit order is
kept. If visits disagree, the patient gets `patient_value_varies`, on a
visit whose value differs from the kept one.

The extraction repeats a patient-level value on every visit row, so a bad
cell would be flagged once per visit. The flags of a patient-level variable
are therefore given once per patient and kind of flag: each stays on the
visit of the cell that raised it, with that cell's text in `raw` (the
earliest visit when several raise it). The QC table counts patients, not
visit rows. The report draws these flags with the value, on the patient's
first visit.

### Step 12: winsorising

- Only variables of type `number`, and the continuous scores that ask for it
  (a body mass index). Never items, bounded scores, categories, dates or
  times.
- Runs last, so scores are computed from unclipped inputs.
- Default limits: the 1st and 99th percentile of the valid values, pooled over
  sites and visits. Each limit is a value that was really observed (the
  nearest one to the percentile). A schema can give other percentiles, fixed
  limits, or switch it off.
- Each clipped cell gets `winsorised`; `raw` keeps the original.
- `load(..., winsorise=False)` skips the step: the values are delivered as
  harmonised, with their true tails. Use it when the tails are the subject
  (a glucose above the 99th percentile, a very low z-score), or when two
  cohorts are compared: each cohort has its own limits.
- The limits used are stored in `qc` (`winsor_low`, `winsor_high`). Passing a
  previous `qc` table to `load(..., winsor_limits=...)` applies those limits
  instead of computing new ones. Do this when a model is validated on data
  that were not used to fit it.

## 6. Flag codes

| Severity | Meaning | In `data` |
|---|---|---|
| `info` | Harmonised. The value is trusted | The harmonised value |
| `discrepancy` | The value conflicts with other information | The value is kept; use with care |
| `danger` | Could not be harmonised | Missing; the raw string is in `flags` |

| Flag | Severity | Raised when |
|---|---|---|
| `missing_code` | info | The cell held a missing code |
| `date_placeholder` | info | The date was a placeholder |
| `date_partial` | info | Day or month was unknown, or the day was replaced by the day that the export writes (`day`) |
| `format_repaired` | info | A number was written unusually but unambiguously |
| `censored_left` | info | The cell was `<limit`. For a band: this band or a lower one |
| `censored_right` | info | The cell was `>limit`. For a band: this band or a higher one |
| `band_from_z` | info | The band is the one a z-score has under the normal law: the z-score of the cell, or one computed with the regression of the norms |
| `unit_converted` | info | Converted from a labelled unit |
| `unit_inferred` | info | Unit taken from the magnitude; the label was missing, unknown or impossible |
| `sign_flipped` | info | A standard score written in the old sign convention was multiplied by −1 |
| `version_inferred` | info | No version was recorded for the patient; it was taken from the inclusion date |
| `version_overridden` | info | The form labels the visit with one edition, a column that only another edition has is filled: the visit has the other edition |
| `visit_removed` | discrepancy | The visit has several impossible values in the instrument (`implausible_visits`): its block is shifted, so its other values are not delivered |
| `duplicate_row` | info | A duplicated visit record was dropped |
| `winsorised` | info | The value was clipped |
| `unit_doubt` | discrepancy | The value was possible under its label but fits another unit better |
| `sign_doubt` | discrepancy | The standard score is dated within 90 days of the centre's change of sign convention, or has no date; or the early scores of the centre mix the two conventions and were not flipped |
| `band_middle` | discrepancy | The cell held a band of values (`60-51`); the value is the middle of the band |
| `column_conflict` | discrepancy | Two raw columns of one variable hold different values; the first one listed is kept |
| `score_mismatch` | discrepancy | Stored and recomputed scores differ |
| `score_as_stored` | discrepancy | None of the items of the score is recorded: the score typed in the extraction is delivered, unchecked. Also a total built on such a score |
| `derived_doubt` | discrepancy | The value was computed by the EMR from a stored score that differs from the recomputed one |
| `patient_value_varies` | discrepancy | A patient-level variable, or an answer about a relative, changes between visits |
| `list_crossed` | discrepancy | An item of a list that the export crossed: the patient has several products, and the file does not say which dose or date belongs to which (SCHEMA_SPEC, section 15) |
| `visit_order` | discrepancy | Visit dates are not in visit order |
| `check_failed` | discrepancy | A custom check named in the schema failed |
| `period_doubt` | discrepancy | The visit is dated in a period in which the schema says the column is not reliable |
| `period_removed` | danger | The visit is dated in a period in which the schema says the column is not reliable and asks for the value not to be delivered; `raw` holds what was written |
| `unparsed` | danger | The cell could not be read as its type |
| `unknown_code` | danger | A category value is not in the code list |
| `out_of_range` | danger | The value is outside the hard range. Also a visit date before the cohort opened or after today, an impossible age, and a date that must come before its visit on the day of the visit or later (`before_visit`) |
| `not_shown` | danger | The cell answers a question that the form did not show for the answer given (`shown_if`): a value the form wrote by itself; `raw` holds it |
| `unit_unknown` | danger | No usable unit label and the magnitude fits several units; or a percentage of a value that is missing |
| `version_unknown` | danger | Data present but version not recognisable |
| `norm_missing` | danger | No standard score could be read: the norm table was not found, or it has nothing for this age, raw score and second variable. For a z-score computed with a regression: the table was not found, or a variable of the regression is missing |
| `score_not_recomputed` | danger | The extraction stores the score but an item is missing: the score is not delivered; `detail` holds the stored value |

## 7. QC and report

### `qc` columns

| Group | Columns |
|---|---|
| Identity | `variable`, `instrument`, `tab`, `label`, `column`, `type`, `unit`, `level` |
| Completeness | `n_rows` (visits on which the variable is read), `n_filled` (raw non-empty), `n_valid`, `pct_valid` (valid among filled), `n_missing_code` |
| Flags | `n_info`, `n_discrepancy`, `n_danger`, and one count per flag code |
| Censoring | `n_cens_left`, `n_cens_right`, `n_limits` (distinct limits) |
| Distribution | `n_distinct`, `min`, `p01`, `p25`, `median`, `p75`, `p99`, `max` |
| Winsorising | `winsor_low`, `winsor_high`, `n_winsorised` |
| Time and place | `first_year`, `last_year`, `n_sites`, `site_shift`, `year_shift` |

`site_shift` and `year_shift` are the largest distance between a site's (or a
year's) median and the overall median, in units of the overall interquartile
range. Sites or years with fewer than 20 values are left out. A large value
points to a hidden unit mixture, a version change or a site habit.

The table has one line per delivered variable and score. Variables that are
read only for checks (`keep: false`) have no line; their flags are in `flags`.

### Plots

One figure per variable, four panels:

| Panel | Shows | Reveals |
|---|---|---|
| 1 | Distribution as written (grey) and harmonised (blue), with range and winsor lines | Outliers, scale mixtures, what the pipeline changed |
| 2 | Share of raw cells per year: value, censored, missing code, unparsed, empty | Format changes, missingness over time |
| 3 | Per year: median and quartiles of the harmonised value, and the median as written | Version and unit changes |
| 4 | Per site: the same | Site effects, hidden unit mixtures |

For categories, and for scales with 10 levels or fewer, panels 1, 3 and 4
show the levels instead: how many values at each level, then the share of
each level per year and per site. An ordered scale is drawn in one hue, from
light to dark. The levels of a category get one colour each, at most seven;
the rarer ones are drawn together.

Text and date variables get no figure, and neither does a variable with
fewer than 20 values: a figure of so few patients would show individuals.
For the same reason a site or a year with fewer than 20 values is left out
of the per-site and per-year panels.
Patient-level variables are drawn with the year and the site of the
patient's first visit.

"As written" is read again from the raw text kept in `flags`, so the report
needs nothing but the result of `load()`.

One figure per instrument: the share of visits with a value, per variable and
year; the visits per year, by version when there is one; and, for an
instrument with a `sign` block, the rank correlation between raw value and
standard score per year, as written and harmonised.

### Report

```
reports/bp/
  index.html            summary, contents, flag counts, the QC table
  <instrument>.html     schema notes, QC rows, flag counts, figures
  plots/<instrument>/<variable>.png
  plots/<instrument>/_instrument.png
```

Plain HTML written with f-strings and `DataFrame.to_html`. The report shows
aggregates only; patient-level rows stay in `result.flags`. `reports/` is
git-ignored.

## 8. Thesaurus and coverage

- The thesaurus is not read by `load()`. Its labels and formulas are sometimes
  wrong, so it must not sit on the critical path.
- `draft_schema()` prints a YAML skeleton for one thesaurus section: column
  names (item ranges expanded), labels, codings when they can be parsed, and
  the value classes seen in the data as comments. A person then completes it.
- `coverage()` lists every name found in the extraction, the schemas or the
  thesaurus, with a status: `covered`, `ignored`, `not_assigned` (in the
  extraction, no schema yet), `missing_in_extraction`, `thesaurus_only`. For
  each column it also counts the cells that hold a value but are not read,
  because no schema covers that column for the visit's edition.
- Columns left out on purpose are listed with a reason in
  `facedata/bp/ignored.yaml` (fully empty columns, duplicated keys, columns
  the export filled with defaults).

## 9. Other cohorts

Each cohort has its own schema folder. BP, SZ and DR share item codes for the
instruments they have in common, so their schemas start as copies of the BP
ones and keep their instrument name, their output columns and their scoring
key. `tests/test_cohorts.py` compares the schemas of the same name in two
cohorts (`defaults`, `variables`, `scores`, `version`); a difference must be
listed with its reason in the cohort's `differences.yaml`. A copy is only a
starting point: it is checked on the cohort's own data like any other schema
(the same column can hold another question, and the same score another
formula). FACE SZ is written this way: all its columns are read or ignored
(`docs/sz/PROGRESS.md`, `docs/sz/QUESTIONS.md`). 67 of its 125 schemas have the name
of a BP schema: 9 are the same and 58 are listed in `differences.yaml`. FACE DR
too (`docs/dr/PROGRESS.md`, `docs/dr/QUESTIONS.md`): 79 of its 137 schemas have the
name of a BP schema (75) or of an SZ schema (4); 11 are the same and 68 are listed.
FACE ASP was written before its dictionary arrived, then checked against it, and has few shared instruments (`docs/asp/PROGRESS.md`, `docs/asp/QUESTIONS.md`): 37 of its 138
schemas have the name of a schema of another cohort; 2 are the same and 35 are listed in its `differences.yaml`.
A stored score that follows the formula of the other cohort does not prove a copied
schema right, because the EMR applies the same formula to the answers of another
form: compare the answers themselves between the cohorts (the mean of each item,
and whether each item rises with the rest of its scale) before trusting a copy. A table that the cohorts share, such as the
medication names, sits in the package folder: a schema names its file, and
the loader looks in the cohort folder first. ASP has other column names, and
its thesaurus arrived after the module: its schemas were written from the data
and then checked against it.

`tests/test_cohorts.py` also compares the cohorts variable by variable, in
every pair: a raw column that two cohorts read has the same output name, and
an output name is the same kind of value, in the same unit, in the same table
and with the same labels (one list of labels may hold more boxes than the
other). What cannot be so is listed in `facedata/shared_names.yaml` with its
reason, and a line that is no longer true makes the test fail.

## 10. Tests and definition of done

- No real data in the repository. Tests use small hand-written tables with the
  token shapes found in the extractions (`<5`, `27,90`, `25 - 50`,
  `0000-00-00`, `Ne sais pas`).
- One test per pipeline step, one expected-values table per instrument, one
  test that every schema passes `check_schema`.
- A real-data test runs only when `data/bp/*.tsv` is present, and checks
  aggregates only.
- `tests/test_common.py` checks the baseline row on a hand-written table and
  the catalogue of the common instruments against the schemas.

An instrument is done when:

1. its schema passes `check_schema` against the extraction's columns;
2. every column of its thesaurus section is in the schema or in `ignored.yaml`;
3. the invariant of section 4 holds;
4. no `unparsed` or `unknown_code` value is left unexplained;
5. stored and recomputed scores agree, or the gap is explained in the schema's `notes`;
6. its report page has been read, and the year and site panels show no unexplained step;
7. decisions are logged in `docs/bp/PROGRESS.md` and the schema says `status: reviewed`.
