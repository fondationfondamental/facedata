# facedata — schema specification

A schema is a YAML file that says everything the pipeline needs to know about
one instrument: which columns it reads, what type each one is, which values
are possible, which unit is wanted, how versions differ, and how scores are
computed.

The pipeline code knows nothing about MADRS, glucose or WAIS. If a special
case is not written in a schema, it does not exist.

## 1. Where schemas live

```
facedata/<cohort>/schemas/<tab>/<instrument>.yaml
```

- One file per section of the data dictionary (one questionnaire, one lab
  panel, one test).
- `<tab>` is the dictionary tab in lower case with underscores:
  `hetero_questionnaires`, `bilan_biologique`, `neuropsychologie`, ...
- The file name is the instrument name.

## 2. How the YAML is read

Schemas are read with `yaml.BaseLoader`: **every value arrives as text**, and
`check_schema` converts the fields that must be numbers. So write values
exactly as they appear in the data, with no quoting tricks:

```yaml
codes: {Oui: yes, Non: no, 0: no, 1: yes}      # keys stay "Oui", "Non", "0", "1"
missing: {1000-01-01: not_recorded}            # stays text, not a date
```

Quote a value only if it contains `: `, ` #`, or starts with one of
`[ ] { } > | * & ! % @`. Example: `">= baccalaureat"`.

## 3. Instrument fields

| Field | Required | Meaning |
|---|---|---|
| `instrument` | yes | Name, same as the file name. Used in `load(instruments=[...])` and in the report |
| `title` | yes | Name a person would recognise |
| `tab` | yes | Dictionary tab, as written there |
| `section` | yes | Dictionary section header, as written there |
| `status` | yes | `draft` or `reviewed` |
| `level` | no | `visit` (default) or `patient` (one value per patient) |
| `notes` | no | Decisions, open questions, differences from the dictionary |
| `defaults` | no | Variable fields applied to every variable that does not set them. A field that does not apply to a variable's type is ignored |
| `version` | no | How to recognise the visits of this edition or form, when several share the same raw columns (section 7) |
| `variables` | yes | Output name → variable fields (section 4) |
| `scores` | no | Output name → score fields (section 8) |
| `sign` | no | Standard scores whose sign convention changed during the study, and how to recognise it (section 9) |
| `checks` | no | Names of functions in `facedata/custom.py` (section 10) |

## 4. Variable fields

The key is the **output name**: lower case, underscores, unique in the cohort.
Questionnaire items keep their extraction name (`madrs01`). Other variables
get a readable English name (`glucose`, `haemoglobin`).

| Field | Applies to | Meaning |
|---|---|---|
| `column` | all | Raw column. Default: the output name |
| `label` | all | Short label for the report |
| `type` | all | `number`, `item`, `category`, `date`, `time` or `text`. Required (often through `defaults`) |
| `range` | number, item | `[min, max]`: hard limits, in the target unit. Outside is impossible. Required for `item` |
| `codes` | category | `{raw: label}`. Required. Matching ignores case and surrounding spaces |
| `missing` | all | `{token: reason}`: extra missing codes for this variable. Reasons: `unknown`, `not_applicable`, `not_recorded` |
| `unit` | number | Target unit of the output |
| `unit_column` | number | Raw column holding the unit label |
| `units` | number | `{unit: {factor, expect}}` (section 5) |
| `censor_units` | number | Unit-column values that really mean censoring: `{inf: left}` (section 6) |
| `censored` | number | `limit` (default) or `half`: the value given to a left-censored cell |
| `versions` | all | The editions on whose visits the variable is read (section 7). Usually set once in `defaults`. Default: all visits |
| `winsor` | number | `[q_low, q_high]` percentiles (default `[0.01, 0.99]`), `{limits: [a, b]}` fixed limits, or `false` |
| `keep` | all | `false`: read and checked, but not delivered (stored scores used for comparison) |
| `derived_from` | number, item | Name of a score that has `compare`. Says that the EMR computed this stored value from the stored score, so it is doubtful wherever that stored score is wrong (section 8) |
| `parse` | all | Name of a function in `facedata/custom.py` that parses this column (escape hatch) |
| `note` | all | Free text |

### Types

| Type | Use for | Output | Winsorised |
|---|---|---|---|
| `number` | Measurements: lab results, weight, reaction times, z-scores | float | yes, unless `winsor: false` |
| `item` | Questionnaire items and bounded whole-number scores | float holding whole numbers | never |
| `category` | Coded answers | harmonised label | never |
| `date` | Dates | date | never |
| `time` | Clock times and durations written `HH:MM` | hours as float | never |
| `text` | Free text | cleaned string | never |

More types are added only when an instrument needs one (percentile bands for
CVLT, lists for treatments).

## 5. Units

```yaml
glucose:
  column: gluc_lbstresc
  unit_column: gluc_lborresu
  type: number
  unit: mmol/L                                  # target unit
  units:
    mmol/L: {factor: 1,     expect: [2.5, 40]}
    g/L:    {factor: 5.551, expect: [0.3, 2.5]}
  range: [1.5, 40]
```

| Field | Meaning |
|---|---|
| `factor` | Multiply a value in this unit by `factor` to get the target unit. The target unit has factor 1 |
| `expect` | `[low, high)`: the values one expects to see **in this unit's own scale**. Used to recognise the unit from the magnitude |
| `aliases` | Other spellings of the unit label. Case and spaces are already ignored, so `g/l` needs no alias |

How the pipeline uses them is in ARCHITECTURE.md, step 7. In short:

- the label is believed when the value fits it;
- when the value does not fit the label and fits exactly one other unit, that
  unit is used and the cell is flagged (`unit_inferred` or `unit_doubt`);
- unit labels not listed (`erreur`, `cdk`, `NC`) count as unknown, so the
  magnitude decides.

Choose `expect` ranges that do not overlap whenever the units can be told
apart by magnitude. When they cannot (two units on almost the same scale),
let them overlap: a cell with an unknown label then gets `unit_unknown`.

A variable with no unit column can still list several units; the magnitude
alone decides (ECG intervals in s or ms).

## 6. Censoring

Any `number` may hold `<limit` or `>limit`. The pipeline always:

- stores the limit as the value (or half of it for left-censored cells when
  `censored: half`),
- writes −1 or +1 in `<variable>_cens`,
- flags the cell `censored_left` or `censored_right`.

`censor_units` handles extractions where the mark sits in the unit column:

```yaml
crp:
  column: crp_lbstresc
  unit_column: crp_lborresu
  censor_units: {inf: left, inferieur: left}   # unit "inf" means "< value"
```

Not everything written with `<` or `>` is censoring. Percentile classes
(`>95`) and labels (`>= baccalaureat`) are categories: give them
`type: category` and list them in `codes`.

## 7. Editions and forms

**One schema describes one edition or form of an instrument.** A change of
instrument is never hidden inside an output column. BIS-10 and BIS-12, or
WAIS-III and WAIS-IV, are separate instruments with separate schemas and
separate output columns, even where the extraction stores them in the same
raw columns.

When several editions share raw columns, each schema says how to recognise
its own visits. There are three ways.

From a column filled at every visit:

```yaml
version:
  name: wais_version                 # output column
  column: wais_version               # raw column
  codes: {WAIS3: wais3, WAIS4: wais4}
```

From a column filled once per patient:

```yaml
version:
  name: dsm_version
  column: dsm_criteria               # recorded at the inclusion visit only
  codes: {DSM4: dsm4, DSM5: dsm5}
  level: patient                     # the patient's other visits take the value
  follow_up: {dsm5: 2022-01-01}      # from that date, every follow-up visit is dsm5
  by_inclusion_date:                 # patients with no value: decided by their inclusion date
    dsm4: [1900-01-01, 2019-12-31]
    dsm5: [2023-01-01, 2100-12-31]
```

With `level: patient`, the version of a visit is the first of these that
gives one:

1. the value written on the visit itself;
2. `follow_up` (optional): a follow-up visit (`visit_month` above 0) dated on
   or after the date given has that version, whatever the patient's
   inclusion. From 2022 the follow-up form was the DSM-5 form for everyone
   (decision D14 in PROGRESS.md);
3. the value of the patient's earliest visit that has one. Before 2022 a
   follow-up visit was evaluated with the criteria of the patient's
   inclusion (decision D12);
4. `by_inclusion_date` (optional): for a patient with no value at all, the
   version whose date range holds the patient's earliest visit date
   (decision D15). The visits concerned get `version_inferred`.

From which items are filled:

```yaml
version:
  name: bis_form
  filled:                            # tested top to bottom, first match wins
    bis10: [bis1002, bis1003]        # at least one of these columns is filled
    bis12: [bis1001, bis1006]
```

Then each schema:

- carries that `version` block, word for word the same in every schema that
  uses the same `name`;
- sets `defaults: {versions: [<its own edition>]}`, so that it reads only its
  own visits;
- gives its variables output names of its own (`wais3_...`, `wais4_...`).

`data` gets the version column once (`wais_version`, `bis_form`) and separate
columns for each edition. Nothing is mixed unless the analyst mixes it,
knowingly.

Rules:

- A visit where nothing is filled has no version and is not flagged: the
  instrument was not administered.
- A visit with data but a version code that is not listed gets
  `version_unknown`.
- With `level: patient`, a patient whose visits hold two different values
  keeps the earliest one and gets `patient_value_varies`. A visit that none
  of the four rules reaches has no version: if it holds data it gets
  `version_unknown`.
- One raw column may be read by several variables only if their `versions` do
  not overlap, across all schemas of the cohort.
- A cell that holds a value on a visit whose edition has no variable for that
  column is not read. `coverage()` counts those cells per column, and the
  schema `notes` say why. Examples: the BIS-10 subscale columns that the EMR
  also fills on BIS-12 visits; WAIS-III vocabulary items 31 to 33 on a few
  WAIS-IV visits.

Scores can still be compared across editions when that is scientifically
justified (the twelve items common to BIS-10 and BIS-12, the age-scaled WAIS
scores). That is a decision for the analysis, taken by combining two named
columns.

## 8. Scores

```yaml
scores:
  bis10_sum12:
    label: Total of the 12 items that the BIS-12 also has
    sum: [bis1001, bis1006, bis1008, bis1009, bis1012, bis1014,
          bis1017, bis1020, bis1021, bis1023, bis1025, bis1028]
    reverse: [bis1001, bis1008, bis1009, bis1012, bis1021]
    compare: bis10_sum12_stored
    compare_offset: 5
```

| Field | Meaning |
|---|---|
| `sum` or `mean` | The variables to combine. Scores defined higher up in the file may be used too |
| `reverse` | Items reversed first: `min + max − value`, using the item's own `range` |
| `min_items` | How many items must be present. Default: all of them. Otherwise the score is missing |
| `versions` | Versions in which the score is computed. Missing elsewhere |
| `compare` | Variable holding the score as stored in the extraction. A difference above 0.01 gives `score_mismatch`; the recomputed score is kept |
| `compare_offset` | Known, documented offset of the stored score: stored = recomputed + offset. Explain it in `notes` |
| `label`, `range`, `keep` | As for variables. `keep: false` makes a score a pure consistency check |

Scores are never winsorised.

### Stored values derived from a stored score

Next to a raw total, the extraction often stores values that the EMR computed
from it: an age-scaled score, a z-score, a percentile. They cannot be
recomputed without the norm tables, so they are delivered as stored. But when
the stored total is wrong, they are wrong too. `derived_from` says so:

```yaml
variables:
  wais3_vocab_total_stored: {column: vocabtot_wais3, range: [0, 66], keep: false}
  wais3_vocab_scaled:       {column: vocabstd_wais3, range: [1, 19], derived_from: wais3_vocab_total}

scores:
  wais3_vocab_total:
    sum: [wais3_vocab01, wais3_vocab02]          # ... all 33 items
    compare: wais3_vocab_total_stored
    compare_offset: -3
```

On every row where the stored score differs from the recomputed one, the
derived value is kept and flagged `derived_doubt`. A documented
`compare_offset` does not excuse it: the offset says that the stored score is
wrong in a known way, and what was derived from it carries the error.

## 9. Sign conventions

A z-score can be written with either sign. A slow Trail Making time is `+1.5`
in one convention (above the mean time) and `-1.5` in the other (worse than
the mean). Some centres changed convention during the study, so one column
holds both, and nothing in the cell says which.

```yaml
sign:
  relation: negative       # when the raw value goes up, the standard score must go down
  by: siteid               # each centre changed once, at its own date
  pairs:                   # standard score: the raw variable it was computed from
    tmt_a_time_z: tmt_a_time
    tmt_a_errors_z: [tmt_a_errors_corrected, tmt_a_errors_uncorrected]
```

| Field | Meaning |
|---|---|
| `relation` | `negative` or `positive`: how the standard score must move when the raw value goes up. This is the convention of the output |
| `by` | Key column inside which the convention changed at most once, from the opposite convention to the wanted one. Normally `siteid` |
| `pairs` | Each standard score with its raw variable. A list of raw variables is added up first |

How the switch date is found is in ARCHITECTURE.md, step 8. In short: in each
centre the pipeline looks for the month before which the standard scores move
the wrong way. The values before that month are multiplied by −1 and flagged
`sign_flipped`. The values within 90 days of it are also flagged `sign_doubt`.

Rules:

- All the pairs of an instrument share one switch date per centre, because
  the convention belongs to the form, not to one score.
- List only standard scores that changed. One that has the wanted sign in
  every year would be flipped by mistake (look at the instrument figure of
  the report first).
- The standard scores listed are of type `number`. Their `range` is checked
  after the flip, so write it in the convention of the output.

## 10. Checks and custom functions

`facedata/custom.py` holds the few rules that cannot be written as data.

- `parse: name` on a variable: `name(column) -> values` replaces step 6.
- `checks: [name]` on an instrument: `name(data) -> True/False per row`; rows
  that return True get `check_failed` with the function name in `detail`.

Use them rarely. A second instrument needing the same rule is a sign that the
spec should gain a field instead.

## 11. What needs no schema entry

Done for every variable (details in ARCHITECTURE.md, section 5):

- text repairs: spaces, HTML entities, escaped apostrophes, literal `\n`;
- global missing codes: `Ne sais pas`, `NSP`, `Non applicable`, `NA`, `NaN`, ...;
- empty dates `0000-00-00` and placeholder dates `1000-01-01`, `1850-01-01`,
  `1900-01-01`;
- number repairs: decimal comma, trailing dot, trailing `%`;
- censoring marks in front of a number.

## 12. What `check_schema` verifies

`check_schema(schema, columns)` returns a list of problems; `load()` stops if
the list is not empty.

- Only the fields listed in this document are used, and required ones are present.
- `type` is known; `item` has a `range`; `category` has `codes`.
- Fields that must be numbers are numbers; `range` and `expect` have low ≤ high.
- A variable with `units` has a `unit`, that unit is listed, and its factor is 1.
- Versions named in `versions` exist in `version`.
- Schemas that use the same version `name` have identical `version` blocks.
- A raw column feeds at most one variable per version, across all schemas of
  the cohort.
- Scores refer to variables or earlier scores that exist; reversed items have a `range`.
- `derived_from` names a score that has `compare`.
- A `version` block with `level` says `patient` and reads a `column`.
  `follow_up` and `by_inclusion_date` need `level: patient`; they name
  versions listed in `codes` and their dates are written `YYYY-MM-DD`.
- A `sign` block has `relation`, `by` and `pairs`; `by` is a key column; every
  name in `pairs` is a variable of the schema, and the standard scores are of
  type `number`.
- Every raw column named exists in the extraction.
- Output names are unique within the cohort.

## 13. The first schemas

These schemas were written first because together they exercise every
mechanism. Read them as examples.

| File | Shows |
|---|---|
| `hetero_questionnaires/madrs.yaml` | `defaults`, items, a score compared with the stored total |
| `bilan_biologique/biochimie.yaml` | Censoring with many detection limits (CRP), two units with an unreliable label (glucose) |
| `bilan_biologique/nfs.yaml` | A hidden unit mixture under one label (haemoglobin) |
| `auto_questionnaires/bis10.yaml`, `auto_questionnaires/bis12.yaml` | Two instruments stored in the same columns and split by form, the form found from which items are filled, a documented offset of the stored scores |
| `neuropsychologie/wais3_*.yaml`, `neuropsychologie/wais4_*.yaml` | Two editions stored in the same columns and split by a version column: digit span, vocabulary, matrices, coding and symbol search (two schemas each), and similarities (WAIS-IV only). Scaled scores marked `derived_from` their raw total |
| `neuropsychologie/tmt.yaml` | Z-scores whose sign convention changed centre by centre (`sign`), missing codes of one variable |
| `evaluation_medicale/dsm4_depuis_derniere_visite.yaml`, `evaluation_medicale/dsm5_depuis_derniere_visite.yaml` | Two editions split by a version recorded once per patient (`level: patient`), yes/no codes, counts with a cap (`>20`) |

## 14. Adding an instrument

1. Run `draft_schema()` for the dictionary section. It prints a skeleton with
   the column names, the labels and what the data contain.
2. Save it as `facedata/<cohort>/schemas/<tab>/<instrument>.yaml` and complete
   it: types, ranges, codes, units, versions, scores.
3. Check every formula and every column meaning against the data. The
   dictionary is sometimes wrong.
4. Run `load(path, instruments=["<instrument>"])` and read `result.flags` and
   the report page.
5. Explain what remains flagged in `notes`, log decisions in
   `docs/<cohort>/PROGRESS.md`, and set `status: reviewed`.
