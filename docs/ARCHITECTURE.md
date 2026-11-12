# facedata — architecture

`facedata` reads an extraction of a FACE cohort and returns data that are
ready for algorithms:

1. every value is parsed into one clean type,
2. units, censored values and instrument versions are harmonised,
3. whatever could not be harmonised is flagged, never silently kept or dropped,
4. continuous variables are winsorised,
5. every variable gets a quality-control (QC) summary and plots.

There is one module per cohort (`facedata.bp`, later `sz`, `dr`, `asp`).
Everything specific to an instrument is written in a YAML schema
(see [SCHEMA_SPEC.md](SCHEMA_SPEC.md)). The Python code is generic and does not
change when an instrument is added.

Out of scope: imputation, scaling, one-hot encoding. Missing stays missing.

## 1. Source data

| Fact | Consequence |
|---|---|
| Each cohort has one extraction, one row per patient visit and one column per variable (BP: 22,077 × 2,236) | The pipeline works column by column |
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
  read.py         read_extraction(), prepare_visits()
  parse.py        clean_text(), split_missing(), parse_number(), parse_item(),
                  parse_category(), parse_date(), parse_time(), parse_column()
  harmonise.py    detect_version(), convert_units(), fix_sign(), check_range(),
                  compute_scores(), collapse_patient_level(), winsorise()
  pipeline.py     read_variable(), run_instrument(), run_cohort(): the ordered steps, nothing else
  qc.py           qc_table(), coverage()
  plots.py        plot_variable(), plot_instrument()
  report.py       write_report()
  thesaurus.py    read_thesaurus(), draft_schema(): a helper, never used by load()
  custom.py       the rare named functions a schema refers to
  bp/
    __init__.py   load(), report(), coverage()
    ignored.yaml  columns deliberately left out, each with a reason
    schemas/<tab>/<instrument>.yaml
tests/            small hand-written tables only
```

## 3. Public API

```python
from facedata import bp

result = bp.load("data/bp/BPALL_20261030.tsv")              # every instrument that has a schema
result = bp.load(path, instruments=["madrs", "biochimie"])  # or only some

result.data       # one row per patient visit
result.patients   # one row per patient
result.flags      # one row per flagged cell
result.qc         # one row per variable

bp.report(result, "reports/bp")                              # HTML report and plots
bp.coverage(path, "thesauri/FACEBP_thesaurus_V4.34.xlsx")    # which columns have a schema
bp.load(new_path, winsor_limits=result.qc)                   # reuse winsor limits on new data
```

`result` is a named tuple of four DataFrames.

## 4. What `load()` returns

### `data`: one row per patient visit

Key columns first, then the harmonised variables of every instrument.

| Column | Content |
|---|---|
| `usubjid` | Patient identifier (text) |
| `visit` | Visit label as extracted (`V0`, `V6_mois`, `V1_an`, ...) |
| `visit_order` | Rank of the visit (from `id_visit`) |
| `visit_month` | Planned months since inclusion, read from the label (`V0` = 0, `V6_mois` = 6, `V1_an` = 12) |
| `visit_date` | Visit date (from `svdtc`) |
| `siteid` | Centre (text, leading zeros kept) |
| harmonised variables | Numbers are floats in the schema's unit, categories are harmonised labels, dates are dates |

(`usubjid`, `visit`) is unique.

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

Variables whose schema says `level: patient` (demographics, lifetime history,
family history). They are repeated on every visit row in the extraction; here
they appear once.

### `flags`: one row per flagged cell

| Column | Content |
|---|---|
| `usubjid`, `visit` | Where |
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

Nothing disappears silently. A test checks this for each instrument.
"Empty" means the empty string and `0000-00-00` (the export's empty date).

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

### Step 2: visits

- Rows with the same `visitnum` are exact duplicates; one is kept
  (`duplicate_row`).
- `visit_month` comes from the label: `V<n>_mois` is n months, `V<n>_an(s)` is
  12 × n months, `V0` is 0.
- Placeholder visit dates (`1950-01-01`) become missing (`date_placeholder`).
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

### Step 6: parsing

| Type | Accepted | Repairs flagged `format_repaired` |
|---|---|---|
| `number` | Integer or decimal, optional sign, optional `<`, `>`, `<=`, `>=` in front | Decimal comma (`27,90`), trailing dot (`28.2.`), trailing `%`, space after the sign |
| `item` | Whole number | Same |
| `category` | A key of the variable's `codes`, ignoring case and spaces | none |
| `date` | `YYYY-MM-DD` | Partial dates `YYYY-00-00` and `YYYY-MM-00` become the middle of the period (`date_partial`) |
| `time` | `HH:MM`, returned as hours | none |
| `text` | Anything | none |

A censoring mark gives the value (the limit) and `<variable>_cens`, with
`censored_left` or `censored_right`. Whatever is still not understood becomes
missing with `unparsed` (or `unknown_code` for a category).

### Step 7: units

Each unit named in a schema has a conversion factor and an expected range of
values in its own scale. The rule is the same for every variable.

| Unit label | The value fits | Result | Flag |
|---|---|---|---|
| Known | The labelled unit's expected range | Converted from the labelled unit | none, or `unit_converted` if it is not the target unit |
| Known | Not the labelled unit's range, exactly one other unit's | Converted from the other unit | `unit_inferred` if the value is impossible under the label, otherwise `unit_doubt` |
| Unknown or empty | Exactly one unit's range | Converted from that unit | `unit_inferred` |
| Unknown or empty | Several units' ranges | Missing | `unit_unknown` |
| Any | No unit's range | Converted from the labelled unit (target unit if unknown) | none here; step 9 decides |

Censoring limits go through the same rule. Variables without a unit column
(ECG intervals in seconds or milliseconds, height with a lost decimal point)
use the same rule with an empty label.

### Step 4 and versions

The extraction sometimes stores two editions or forms of an instrument in the
same raw columns: BIS-10 and BIS-12, WAIS-III and WAIS-IV. The rule is that
**a change of instrument is never hidden inside an output column**. Each
edition has its own schema and its own output columns, and reads only its own
visits.

A schema says how to recognise its visits: from a version column
(`wais_version`), from which items are filled (BIS), or from a column that is
filled once per patient (the DSM criteria, recorded at inclusion).
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
variables that depend on the edition are missing.

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
   it, the scores as written really move the wrong way. Otherwise nothing is
   changed in that centre.
4. Standard scores dated before the switch are multiplied by −1 and get
   `sign_flipped`. Those dated within 90 days of it, before or after, also
   get `sign_doubt`, because a centre does not change on a single day. A
   standard score on a visit without a date is kept as written and gets
   `sign_doubt`.

The switch dates are found again at each load, from the data. They are listed
on the instrument's report page. An extraction with few visits per centre
gives no switch date, and nothing is flipped.

### Step 9: range

A value outside the schema's hard `range` is impossible. It becomes missing
with `out_of_range`. It is never clipped into range.

### Step 10: scores

Scores are recomputed from the harmonised items (sum or mean, with reverse
items). When the extraction also stores the score, the two are compared; a
difference above 0.01 gives `score_mismatch` and the recomputed value is kept.

Some stored values were computed by the EMR from a stored score (a scaled
score from a raw total). They cannot be recomputed without the norm tables.
Where the stored score differs from the recomputed one, such a value is kept
and gets `derived_doubt`.

### Step 11: patient level

For `level: patient` variables the first non-missing value by visit date is
kept. If visits disagree, the patient gets `patient_value_varies`.

### Step 12: winsorising

- Only variables of type `number`. Never items, bounded scores, categories,
  dates or times.
- Runs last, so scores are computed from unclipped inputs.
- Default limits: the 1st and 99th percentile of the valid values, pooled over
  sites and visits. Each limit is a value that was really observed (the
  nearest one to the percentile). A schema can give other percentiles, fixed
  limits, or switch it off.
- Each clipped cell gets `winsorised`; `raw` keeps the original.
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
| `date_partial` | info | Day or month was unknown |
| `format_repaired` | info | A number was written unusually but unambiguously |
| `censored_left` | info | The cell was `<limit` |
| `censored_right` | info | The cell was `>limit` |
| `unit_converted` | info | Converted from a labelled unit |
| `unit_inferred` | info | Unit taken from the magnitude; the label was missing, unknown or impossible |
| `sign_flipped` | info | A standard score written in the old sign convention was multiplied by −1 |
| `version_inferred` | info | No version was recorded for the patient; it was taken from the inclusion date |
| `duplicate_row` | info | A duplicated visit record was dropped |
| `winsorised` | info | The value was clipped |
| `unit_doubt` | discrepancy | The value was possible under its label but fits another unit better |
| `sign_doubt` | discrepancy | The standard score is dated within 90 days of the centre's change of sign convention, or has no date |
| `score_mismatch` | discrepancy | Stored and recomputed scores differ |
| `derived_doubt` | discrepancy | The value was computed by the EMR from a stored score that differs from the recomputed one |
| `patient_value_varies` | discrepancy | A patient-level variable changes between visits |
| `visit_order` | discrepancy | Visit dates are not in visit order |
| `check_failed` | discrepancy | A custom check named in the schema failed |
| `unparsed` | danger | The cell could not be read as its type |
| `unknown_code` | danger | A category value is not in the code list |
| `out_of_range` | danger | The value is outside the hard range |
| `unit_unknown` | danger | No usable unit label and the magnitude fits several units |
| `version_unknown` | danger | Data present but version not recognisable |

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
each level per year and per site. Text and date variables get no figure.

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
ones; a test reports any difference between same-named schemas. ASP has no
thesaurus and different names, so its schemas are written from the data.

## 10. Tests and definition of done

- No real data in the repository. Tests use small hand-written tables with the
  token shapes found in the extractions (`<5`, `27,90`, `25 - 50`,
  `0000-00-00`, `Ne sais pas`).
- One test per pipeline step, one expected-values table per instrument, one
  test that every schema passes `check_schema`.
- A real-data test runs only when `data/bp/*.tsv` is present, and checks
  aggregates only.

An instrument is done when:

1. its schema passes `check_schema` against the extraction's columns;
2. every column of its thesaurus section is in the schema or in `ignored.yaml`;
3. the invariant of section 4 holds;
4. no `unparsed` or `unknown_code` value is left unexplained;
5. stored and recomputed scores agree, or the gap is explained in the schema's `notes`;
6. its report page has been read, and the year and site panels show no unexplained step;
7. decisions are logged in `docs/bp/PROGRESS.md` and the schema says `status: reviewed`.
