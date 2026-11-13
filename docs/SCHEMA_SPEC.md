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
| `level` | no | `visit` (default), `patient` (one value per patient), `list` (the cells hold lists: one row per item, section 15) or `relatives` (the same questions asked for each relative: one row per relative, section 16) |
| `notes` | no | Decisions, open questions, differences from the dictionary |
| `defaults` | no | Variable fields applied to every variable that does not set them. A field that does not apply to a variable's type is ignored |
| `version` | no | How to recognise the visits of this edition or form, when several share the same raw columns (section 7) |
| `variables` | yes | Output name → variable fields (section 4) |
| `scores` | no | Output name → score fields (section 8) |
| `sign` | no | Standard scores whose sign convention changed during the study, and how to recognise it (section 9) |
| `checks` | no | Names of functions in `facedata/custom.py` (section 10) |
| `names` | no | With `level: list`: the table in which the names of one list are looked up (section 15) |
| `at_visit` | no | With `level: list`: the yes/no columns of the visit table computed from the items and their dates (section 15) |
| `relatives` | no | With `level: relatives`, required: the prefix of the raw columns of each relative, and who the relative is (section 16) |
| `per_patient` | no | With `level: relatives`: the yes/no columns of the patients table computed from the rows of the relatives (section 16) |

## 4. Variable fields

The key is the **output name**: lower case, underscores, unique in the cohort.
Questionnaire items keep their extraction name (`madrs01`). Other variables
get a readable English name (`glucose`, `haemoglobin`).

| Field | Applies to | Meaning |
|---|---|---|
| `column` | all | Raw column. Default: the output name. A list of columns when the extraction moved the variable to another column (see below) |
| `label` | all | Short label for the report |
| `type` | all | `number`, `item`, `band`, `category`, `date`, `time` or `text`. Required (often through `defaults`) |
| `range` | number, item, date | `[min, max]`: hard limits, in the target unit. Outside is impossible. Required for `item`. For a date: `[earliest, latest]`, written `YYYY-MM-DD` |
| `codes` | category, item, number | For a category: `{raw: label}`, required. For an item or a number: `{raw: number}`, the raw text is replaced by the number before parsing, so that answers written as letters can be counted (`{Y: 1, N: 0}`). Matching ignores case and surrounding spaces |
| `missing` | all | `{token: reason}`: extra missing codes for this variable. Reasons: `unknown`, `not_applicable`, `not_recorded` |
| `unit` | number | Target unit of the output |
| `unit_column` | number | Raw column holding the unit label. A list when two columns hold it: the first one that is filled is read |
| `units` | number | `{unit: {factor, expect}}` (section 5) |
| `ignore_units` | number | Unit labels that say nothing, read as no label: a default label of the form that names the wrong unit (section 5) |
| `unit_rule` | number | Name of a function in `facedata/custom.py` that gives the unit of the values with no usable label (section 5) |
| `censor_units` | number | Unit-column values that really mean censoring: `{inf: left}` (section 6) |
| `censored` | number | `limit` (default) or `half`: the value given to a left-censored cell |
| `bands` | number | `middle`: a cell that holds a band of values (`60-51`) is read as the middle of the band and flagged `band_middle` (section 6) |
| `limits` | band | The percentiles that separate the bands, in rising order: `[5, 10, 25, 50, 75, 90, 95]` (section 6) |
| `shared` | band, number | `true`: the raw column holds bands and z-scores, read by two variables (section 6) |
| `lookup` and `from` | band | The band is read again in a norm table, from a raw score, where the cell holds a percentile (section 6) |
| `z_range` | band | `[low, high]`: the band also takes the z-scores of its column. A z-score inside the range is turned into its band under the normal law (section 6) |
| `versions` | all | The editions on whose visits the variable is read (section 7). Usually set once in `defaults`. Default: all visits |
| `winsor` | number | `[q_low, q_high]` percentiles (default `[0.01, 0.99]`), `{limits: [a, b]}` fixed limits, or `false`. Set `false` on a count of events that is 0 for most visits (episodes, consultations, hospitalisations): its 99th percentile is 0 or 1, and the default would bring every rarer value down to it |
| `keep` | all | `false`: read and checked, but not delivered (stored scores used for comparison). Such a variable may read a column that another schema delivers, when a score needs it (the years of education for a norm table) |
| `derived_from` | number, item | Name of a score that has `compare`. Says that the EMR computed this stored value from the stored score, so it is doubtful wherever that stored score is wrong (section 8) |
| `asked_if` | item, number | Name of a yes/no variable or of a count listed before. The question is asked only after a yes to it (or a count above 0): where that answer is 0 and the cell is empty, the value is 0 (section 4) |
| `separator` | item | The cell holds several boxes ticked in one list, written one after the other (`Alcool,Cannabis`). Each is read through `codes` and the largest number is kept (section 4) |
| `doubt` | all | `{period: [first day, last day], values: [...], note: ...}`: the cells of the visits dated in the period keep their value and get `period_doubt` (section 10) |
| `parse` | all | Name of a function in `facedata/custom.py` that parses this column (escape hatch) |
| `note` | all | Free text |

### Types

| Type | Use for | Output | Winsorised |
|---|---|---|---|
| `number` | Measurements: lab results, weight, reaction times, z-scores | float | yes, unless `winsor: false` |
| `item` | Questionnaire items and bounded whole-number scores | float holding whole numbers | never |
| `band` | Percentile bands (`25 - 50`, `>95`) | lower limit of the band, as a float | never |
| `category` | Coded answers | harmonised label | never |
| `date` | Dates | date | never |
| `time` | Clock times and durations written `HH:MM` | hours as float | never |
| `text` | Free text | cleaned string | never |

More types are added only when an instrument needs one (lists for
treatments).

### A variable that moved to another column

The EMR sometimes replaced a form by a new one that asks the same question
with the same answers, and the extraction keeps both columns. List them, the
current one first:

```yaml
followup_end_reason:
  column: [lost_to_followup_stopsuivi, lost_to_follow_up_patient]
  type: category
  codes: {Refus du patient: patient_refused, Déménagement: moved}
```

On each row, the first column that holds a value is read. When two columns
hold different values on the same row, the first one is kept and the cell
gets `column_conflict`.

This is for one question stored in two places. Two editions of an instrument
are never merged this way (section 7).

### A question asked only after a yes

Some forms show a question only when the answer to an earlier one is yes: the
box of each anxiety disorder is shown only if the patient has an anxiety
disorder. After a "no" the cell is empty in the extraction, although the
answer is known: none.

```yaml
anxiety_disorder: {column: rad_tb_anx, type: item, range: [0, 1], codes: {Y: 1, N: 0}}
panic_disorder:   {column: ceoccurtrouble_panique, type: item, range: [0, 1], asked_if: anxiety_disorder}
```

- `asked_if` names a variable of the same schema, listed before: a yes/no
  item with `range: [0, 1]`, or a count (an item whose range starts at 0:
  "how many of them..." is asked only when the number of sisters is not 0).
  The variable itself is a yes/no box or a count: an item or a number whose
  range starts at 0.
- Where the named answer is 0 and the cell is empty, the value is 0.
- Where the named answer is missing (unknown, or the form was not filled),
  the value stays missing. Where it is 1, the cell is read as usual.
- These values get no flag: no cell is changed, and the answer they come
  from is delivered next to them. In the QC table they count as filled
  cells.

Use it for yes/no boxes and for counts: with no mood episode in the past
year, the number of depressive episodes in the past year is 0.

```yaml
any_episode: {column: rad_tb_hum_epthyman, type: item, range: [0, 1], codes: {Oui: 1, Non: 0}}
n_mde:       {column: evnum_edm_ly, type: number, range: [0, 50], asked_if: any_episode}
```

Never use it for a detail of the thing asked about, such as an age at onset
or a severity: after a "no" it has no value and stays missing. The schema
check cannot tell a count from an age; that is for the author to see.

### Several boxes in one cell

Some questions let the rater tick several boxes of a list, and the
extraction writes the ticked boxes in one cell, one after the other:
`Alcool,Cannabis`. Such a cell is not one category. It is read as one yes/no
variable per box, or per group of boxes:

```yaml
relative_alcohol:
  column: substance
  type: item
  range: [0, 1]
  separator: ","
  codes: {Alcool: 1, Cannabis: 0, Autre substance: 0, Aucun: 0}
relative_substance:
  column: substance
  type: item
  range: [0, 1]
  separator: ","
  codes: {Alcool: 1, Cannabis: 1, Autre substance: 1, Aucun: 0}
```

- The cell is cut at the `separator`. Each box is read through `codes`, and
  the largest number is the value: 1 as soon as one wanted box is ticked.
- `codes` lists every box of the list. A box that is not listed makes the
  cell `unknown_code`.
- A missing code among the boxes (`Aucun,Ne sais pas`) is not a box. Where
  the value would be 0 next to it, the value is missing and the cell gets
  `missing_code`: "none, and I do not know" cannot be read as a no. A wanted
  box next to it still gives 1.
- Several variables may read the same column this way: this is the one case,
  with `shared`, where a raw column feeds several delivered variables.

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
| `aliases` | Other spellings of the unit label. Case and spaces are already ignored, so `g/l` needs no alias. Also for a label that the form prints wrongly and that can only mean this unit (`mmol/L` for a bilirubin in µmol/L) |

How the pipeline uses them is in ARCHITECTURE.md, step 7. In short:

- the label is believed when the value fits it;
- when the value does not fit the label and fits exactly one other unit, that
  unit is used and the cell is flagged (`unit_inferred` or `unit_doubt`);
- unit labels not listed (`erreur`, `cdk`, `NC`) count as unknown, so the
  magnitude decides.

Choose `expect` ranges that do not overlap whenever the units can be told
apart by magnitude. When they cannot (two units on almost the same scale),
let them overlap: a cell with an unknown label then gets `unit_unknown`.

### A percentage of another variable

Some results are written as a percentage of another result of the same
visit: a kind of white cells as a percentage of the leukocytes. Such a unit
has `percent_of` in place of `factor`:

```yaml
neutrophils:
  unit: G/L
  units:
    G/L:    {factor: 1, expect: [0, 25]}
    "/mm3": {factor: 0.001, expect: [100, 25000], aliases: ["/mm"]}
    "%":    {percent_of: leukocytes, expect: [0, 100], aliases: [pour]}
  range: [0, 25]
```

The value is multiplied by the other variable and divided by 100. The other
variable is taken in its own target unit, and only where it is inside its
hard range. It must be a number listed **before** this variable in the same
schema. Where it is missing, the percentage cannot be converted: the cell
becomes missing and gets `unit_unknown`.

The `expect` range of the percentage may overlap the others. The rule of
step 7 still works: a value that fits its label keeps it, and a value too
large for its label that fits only the percentage is read as one.

### A label that says nothing

The form may print a default unit label that names the wrong unit, on every
result for which nobody chose a unit. List it in `ignore_units`: it is then
read as no label at all, so that the magnitude decides without a flag on
every cell.

```yaml
ignore_units: [mg/L]        # the default label of the form; no prolactin is in mg/L
```

Do not use it for a default label that names the usual unit: that label is
believed whenever the value fits it, which is what one wants.

### Two units on the same scale

When the `expect` ranges of two units overlap widely and most results have
no usable label, the magnitude cannot decide, and every such result would be
`unit_unknown`. A `unit_rule` names a function of `facedata/custom.py` that
decides from other evidence, such as the unit a centre used at the time
(section 10). It is asked only about the values with no usable label. Where
it names a unit, that unit is used (`unit_inferred` when it is not the
target unit). Where it cannot tell, the value is treated as before:
`unit_unknown` if several units fit.

```yaml
prolactin:
  unit_column: prolctn_lborresu
  ignore_units: [mg/L]
  unit: ng/mL
  units:
    ng/mL: {factor: 1,      expect: [0.5, 500], aliases: [µg/L]}
    mUI/L: {factor: 0.0472, expect: [30, 20000], aliases: [µIU/ml]}
  unit_rule: prolactin_unit
```

A variable with no unit column can still list several units; the magnitude
alone decides (ECG intervals in s or ms, a height in cm or mm). Only the
values that are converted get `unit_inferred`. The units can also describe a
lost decimal point: `0.1 kg` with factor 0.1 for a weight written 655.

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

Not everything written with `<` or `>` is censoring. A label such as
`>= baccalaureat` is a category: give it `type: category` and list it in
`codes`. Percentile classes (`>95`) are bands, described below.

A rater sometimes writes a band instead of a number: `60-51` for a
functioning score between 51 and 60. With `bands: middle` the cell is read as
the middle of the band (55.5) and gets `band_middle`. The value is kept, but
it is only known to within the band. Without the field, such a cell is
`unparsed`.

### Percentile bands

Some tests give a result as a percentile band: "between the 25th and the
50th percentile". The column then holds bands in several spellings
(`25 - 50`, `50 - 25`), one-sided classes (`>95`, `<5`, `>10`) and plain
numbers (`50`). `type: band` puts them all on one ordered scale.

```yaml
tmt_a_time_band:
  column: tmta01a_
  type: band
  limits: [5, 10, 25, 50, 75, 90, 95]     # the percentiles that separate the bands
```

The value is the **lower limit of the band**: 0 for the band under the first
limit, then 5, 10, 25 and so on, up to 95 for the band of 95 and more.

| Cell | Value | `<variable>_cens` | Flag |
|---|---|---|---|
| `25 - 50` or `50 - 25` | 25 | 0 | none |
| `50`, a limit | 50, the band that starts there | 0 | none |
| `>95`, the last limit | 95 | 0 | none |
| `<5`, the first limit | 0 | 0 | none |
| `>10` | 10: this band or a higher one | +1 | `censored_right` |
| `10 - 50`, wider than one band | 10: this band or a higher one | +1 | `censored_right` |
| `<10` | 5: this band or a lower one | −1 | `censored_left` |
| anything else (`12`, `30 - 40`) | missing | 0 | `unparsed` |

The two ends of a band must be limits (0 and 100 are accepted as ends). The
value says where the patient stands among the norms at the least; a cell
with `_cens` = −1 may stand lower than its value.

Before delivering a band, compare the share of each band from one period to
the next (the report draws it per year). The EMR changed more than once
what it writes when several limits of the norms fall on the same raw score,
as for the TMT errors; such a column holds several scales and is not
delivered (decision D42 in `docs/bp/PROGRESS.md`).

### A column shared by a z-score and a band

For some measures the EMR writes a percentile for one age group and a
z-score for another, in the same column. Two variables then read the
column, and both say `shared: true`:

```yaml
cvlt_trial5_band: {column: cvlt05z_, type: band, limits: [1, 5, 25, 50, 75, 95, 99], shared: true}
cvlt_trial5_z:    {column: cvlt05z_, type: number, range: [-10, 10], shared: true}
```

The band takes the cells that hold a band or a whole number. The number
takes all the others: a z-score is written with a decimal point (`1.00`).
Neither variable sees, counts or flags the cells of the other.

### A band from a z-score

Two variables that are each filled for part of the patients are hard to
use. To put every patient on one scale, the band can also take the z-scores
of the column: give it `z_range`.

```yaml
cvlt_trial5_band: {column: cvlt05z_, type: band, limits: [1, 5, 25, 50, 75, 95, 99], shared: true, z_range: [-5, 5]}
cvlt_trial5_z:    {column: cvlt05z_, type: number, range: [-5, 5], shared: true}
```

A z-score inside `z_range` is turned into the band it has under the normal
law: the share of the law that lies under the z-score, in percent, is put
between the limits. A z-score of 0 is the 50th percentile (band 50), 0.80
the 79th (band 75) and -1.70 the 4th (band 1). The cell gets `band_from_z`.
A z-score outside `z_range` is an error: the band is missing and the cell
gets `out_of_range`. The number variable still delivers the z-score itself.

This assumes that the scores of the norm group follow a normal law, which a
norm table does not. `band_from_z` tells which bands rest on that
assumption. A higher band is a higher z-score; whether that is a better
performance depends on the measure.

### A band read again in a norm table

When several limits of the norms fall on the same raw score (a perfect
recall, no error), the EMR has written the highest percentile for some
tests and the lowest for others, and has changed its mind over the years.
A band read from such cells is not on one scale. With `lookup` and `from`,
the band is read again in the norm table:

```yaml
cvlt_trial5_band:
  column: cvlt05z_
  type: band
  limits: [1, 5, 25, 50, 75, 95, 99]
  lookup: cvlt_trial5          # the file norms/cvlt_trial5.csv
  from: cvlt_trial5            # the raw score: a number or an item listed before
  shared: true
  z_range: [-5, 5]
```

A cell that holds a percentile is then not read for its content: it only
tells that the EMR used a table for this patient. The band comes from the
table, the raw score and the age at the visit, exactly as for a score
(section 8): the lowest band the raw score can be, with
`<variable>_cens` = +1 and `censored_right` where the table says "this band
or a higher one". If nothing can be read (no table, no raw score, no age),
the band is missing and the cell gets `norm_missing`. A cell that holds a
z-score is still turned into a band through `z_range`.

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

The columns listed may belong to another instrument filled at the same
visit, when the instrument's own columns do not tell its form. The 25 WURS
items are the same columns in the 61-item and in the 25-item questionnaire,
and nothing else in the WURS tells them apart. The reduced questionnaires
replaced the long ones together (decision D47 in PROGRESS.md), so the form
of the WURS is read from the ALS and the BIS of the same visit:

```yaml
version:
  name: wurs_form
  filled:
    wurs61: [als58, bis1002]         # a score or an item that only the long questionnaires have
    wurs25: [als05, bis1001]         # an ALS or BIS answer, and none of the above
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
  instrument was not administered. "Nothing" means the columns that the
  schema's own variables read: a column of another instrument listed under
  `filled` does not give a version to a visit where the instrument is empty.
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
| `lookup` and `from` | Instead of `sum` or `mean`: the score is read in a norm table. `lookup` names the table, `from` the raw score to look up, and `by` a second variable the table depends on (see below) |
| `custom` | Instead of `sum` or `mean`: the name of a function of `facedata/custom.py` that computes the score from the instrument's values, when it is a formula (a body mass index, a corrected QT interval) |
| `reverse` | Items reversed first: `min + max − value`, using the item's own `range` |
| `minus` | With `sum`: variables or earlier scores subtracted from the sum. All of them must be present |
| `floor` | The lowest value the score can take; a lower result is raised to it (the Alda total is A minus B, not below 0) |
| `min_items` | How many items must be present. Default: all of them. Otherwise the score is missing |
| `versions` | Versions in which the score is computed. Missing elsewhere |
| `compare` | Variable holding the score as stored in the extraction. A difference above 0.01 gives `score_mismatch`; the recomputed score is kept |
| `compare_offset` | Known, documented offset of the stored score: stored = recomputed + offset. Explain it in `notes` |
| `compare_tolerance` | Largest difference accepted between the stored and the recomputed score. Default 0.01. Use it when the stored score is rounded: 0.051 for one decimal |
| `winsor` | `[q_low, q_high]`: winsorise this score like a number. Only for a continuous score (a body mass index) |
| `label`, `range`, `keep` | As for variables. `keep: false` makes a score a pure consistency check |

A score is not winsorised unless it sets `winsor`.

### Scores read in a norm table

A scaled score depends on the raw score and on the age of the patient,
through a table of the test manual. The tables are copyrighted, so they are
not in the repository: they are CSV files in a folder that `load()` is given
(`norms/` by default), one file per table, one line per cell:

```
age_min,age_max,raw_min,raw_max,value
16,17,0,3,1
```

A line says: at an age from `age_min` to `age_max` (completed years, at the
visit) and a raw score from `raw_min` to `raw_max`, the standard score is
`value`.

```yaml
scores:
  wais3_vocab_scaled_check:
    lookup: wais3_vocabulary          # the file norms/wais3_vocabulary.csv
    from: wais3_vocab_total           # the raw score: a variable or an earlier score
    compare: wais3_vocab_scaled       # the scaled score stored by the EMR
    keep: false
```

A raw score for which nothing can be read gets `norm_missing`: the table was
not found, the visit has no date (so no age), or the age or the raw score is
outside the table.

A table can depend on a second variable besides the age, such as the years
of education. It then has two more columns, `by_min` and `by_max`, and the
score names the variable with `by`. Like the age, the variable is taken in
completed units (rounded down).

A table of percentile bands gives the lower limit of the band as `value`
(section 6). It can have a column `cens`: 1 on the lines where the raw score
only says "this band or a higher one", because several limits of the norms
fall on that raw score (most patients make no error). The score then gets
`<score>_cens` = +1 and `censored_right` on those rows, like a band read
from a cell.

```
age_min,age_max,by_min,by_max,raw_min,raw_max,value,cens
0,49,10,99,0,0,25,1
```

```yaml
scores:
  tmt_a_errors_band:
    lookup: tmt_a_errors              # the file norms/tmt_a_errors.csv
    from: tmt_a_errors                # the number of errors
    by: tmt_education                 # the table also depends on the years of education
```

(The numbers of this example are made up.)

Use it in one of two ways. As a check (`keep: false` and `compare`), when the
EMR already stores the standard score: the stored one is delivered, and the
rows where the table disagrees are flagged. Or as the delivered score, when
the extraction has none.

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

Check first that the value really was derived from the stored score. The
WAIS-III vocabulary scaled score looked like it; the norm table showed that
the EMR had used the true total, and that only the total column of the
extraction was wrong. Its schema now names the norm-table check instead:
`derived_from: wais3_vocab_scaled_check` flags the scaled score where the
table gives another value.

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
- `checks: {variable: name}` on an instrument: `name(values)` takes the
  table of the instrument's values and returns True for the rows where the
  variable fails the check. Those cells keep their value and get
  `check_failed`, with the function name in `detail`.
- `custom: name` on a score: `name(values)` takes the same table and returns
  the score.
- `unit_rule: name` on a variable: `name(values, keys)` takes the values
  that have no usable unit label (the others are missing) and the key
  columns. It returns, for each value, the name of a unit listed in `units`,
  or missing where it cannot tell (section 5).

```yaml
checks:
  cgi_efficacy_index: cgi_index_differs     # (therapeutic effect - 1) x 4 + side effects
```

Use them rarely. A second instrument needing the same rule is a sign that the
spec should gain a field instead.

### A period in which a column is not reliable

Sometimes the data show that a column was filled wrongly during some months,
and the cell itself does not tell which answers are wrong. The schema then
names the period, and the cells of the visits dated in it keep their value
and get the flag `period_doubt` (discrepancy):

```yaml
defaults:
  doubt:
    period: [2022-01-01, 2023-12-31]     # visit dates, both days included
    values: [1]                          # optional: only the cells that hold one of these values
    note: answers about the whole life entered at follow-up visits
```

- `period` is required: two dates written `YYYY-MM-DD`.
- `values` lists delivered values (numbers, or labels of a category).
  Without it every filled cell of the period is flagged.
- `note` is the text written in the `detail` column of the flag log.
- A cell that is missing, or that another step removed (`out_of_range`,
  `unknown_code`), is not flagged.

Like every field, `doubt` can be set once in `defaults`. Write in the schema
`notes` what the data show, and log the decision in PROGRESS.md: a period is
never doubted without evidence.

## 11. What needs no schema entry

Done for every variable (details in ARCHITECTURE.md, section 5):

- text repairs: spaces, HTML entities, escaped apostrophes, literal `\n`;
- global missing codes: `Ne sais pas`, `NSP`, `Non applicable`, `NA`, `NaN`, ...;
- empty dates `0000-00-00` and placeholder dates `1000-01-01`, `1850-01-01`,
  `1900-01-01`;
- number repairs: decimal comma, missing leading zero, trailing dot, trailing `%`;
- censoring marks in front of a number.

## 12. What `check_schema` verifies

`check_schema(schema, columns)` returns a list of problems; `load()` stops if
the list is not empty.

- Only the fields listed in this document are used, and required ones are present.
- `type` is known; `item` has a `range`; `category` has `codes`; `band` has
  `limits`, numbers in rising order. `z_range` is `[low, high]`, on a band.
  On a variable, `lookup` and `from` go together, on a band, and `from` names
  a number or an item with a range, listed before.
- Fields that must be numbers are numbers; `range` and `expect` have low ≤ high.
- A variable with `units` has a `unit`, that unit is listed, and its factor is 1.
  Every unit has an `expect` range and either a `factor` or `percent_of`.
  `percent_of` names a number listed before the variable in the same schema.
- `unit_rule` names a function that exists in `facedata/custom.py`.
- `doubt` has a `period` of two dates, first day ≤ last day, and no field
  other than `period`, `values` and `note`.
- `asked_if` names an item whose range starts at 0 (a yes/no item or a
  count), listed before in the same schema, on an item or a number whose
  range starts at 0.
- `separator` is on an item that has `codes`.
- Versions named in `versions` exist in `version`.
- Schemas that use the same version `name` have identical `version` blocks.
- A raw column feeds at most one variable per version, across all schemas of
  the cohort. Three exceptions: a variable with `keep: false` may read a
  column that a delivered variable reads, a `band` and a `number` may both
  say `shared: true`, and several items with `separator` may each read one
  box of the same list.
- Scores refer to variables or earlier scores that exist; reversed items have a `range`.
- `derived_from` names a score that has `compare`.
- `checks` names variables or scores of the schema and functions that exist
  in `facedata/custom.py`.
- A score has exactly one of `sum`, `mean`, `lookup` and `custom`; `lookup`
  comes with `from`, `by` with `lookup`, `minus` with `sum`, and `custom` names a function that
  exists in `facedata/custom.py`. Whether the norm table exists is not checked here: a missing table
  gives `norm_missing` flags, not an error.
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
| `hetero_questionnaires/etat_depressif.yaml` | Answers written Y and N, delivered as 1 and 0 and counted (`codes` on items) |
| `hetero_questionnaires/alda.yaml` | A score that is a difference with a floor (`minus`, `floor`) |
| `hetero_questionnaires/cgi_egf.yaml` | A code that means "not assessed" (`missing`), a custom check (`checks`) |
| `constantes_et_ecg/parametres_physiques.yaml` | Units recognised with no unit column, lost decimal points, a score computed by a custom function and compared with a rounded stored value |
| `constantes_et_ecg/ecg.yaml` | Intervals in seconds, milliseconds or hundredths of a second; a stored score delivered next to the recomputed one |
| `patient/fin_de_suivi.yaml` | A patient-level instrument, variables read from two generations of columns, dates with a range |
| `bilan_biologique/biochimie.yaml` | Censoring with many detection limits (CRP), two units with an unreliable label (glucose) |
| `bilan_biologique/nfs.yaml` | A hidden unit mixture under one label (haemoglobin) |
| `auto_questionnaires/bis10.yaml`, `auto_questionnaires/bis12.yaml` | Two instruments stored in the same columns and split by form, the form found from which items are filled, a documented offset of the stored scores |
| `auto_questionnaires/als54.yaml`, `auto_questionnaires/als18.yaml`, `auto_questionnaires/wurs61.yaml`, `auto_questionnaires/wurs25.yaml` | A long questionnaire and the reduced one that replaced it, stored in the same columns; the form found from what only the long questionnaires of the same visit have, a bridge score from the common items |
| `neuropsychologie/wais3_*.yaml`, `neuropsychologie/wais4_*.yaml` | Two editions stored in the same columns and split by a version column: digit span, vocabulary, matrices, coding and symbol search (two schemas each), and similarities (WAIS-IV only). Scaled scores marked `derived_from` their raw total |
| `neuropsychologie/tmt.yaml` | Z-scores whose sign convention changed centre by centre (`sign`), missing codes of one variable |
| `evaluation_medicale/dsm4_depuis_derniere_visite.yaml`, `evaluation_medicale/dsm5_depuis_derniere_visite.yaml` | Two editions split by a version recorded once per patient (`level: patient`), yes/no codes, counts with a cap (`>20`) |
| `traitements/medications.yaml` | Cells that hold lists (`level: list`), names looked up in a table, yes/no columns of a visit computed from dates |
| `antecedents/family_structure.yaml`, `antecedents/family_history.yaml` | A count asked only after another count (`asked_if`), the same questions for each relative (`level: relatives`), boxes ticked in one cell (`separator`), yes/no columns per patient computed from the relatives |
| `antecedents/allergic_history_v0.yaml`, `antecedents/allergic_history_fu.yaml` | A list of boxes shown only after a yes (`separator` with `asked_if`), in an inclusion form and a yearly form |

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

## 15. Lists: one row per item

The current treatments are exported as lists in one cell: `['TERALITHE',
'LAMICTAL']` in the column of the names, `['2015-03-15', '2018-06-15']` in
the column of the start dates, and so on. The lists of a row have the same
length (item 1 of each list describes the same treatment), and every row of
a patient holds the same lists: the cell is the patient's whole history, not
the treatment of the visit.

```yaml
instrument: medications
level: list
names:
  column: med_psy_cmtrt            # the list that holds the names
  clean: medication_name           # function of custom.py: "TERALITHE LP 400 mg, comprimé" -> "TERALITHE LP"
  table: medications.csv           # in the cohort folder: name, molecule, atc, treatment_group
  gives: [molecule, atc, treatment_group]
variables:
  medication: {column: med_psy_cmtrt, type: text}
  molecule: {column: molecule, type: text}
  treatment_group: {column: treatment_group, type: category, codes: {lithium: lithium, antidepressant: antidepressant}}
  start_date: {column: med_psy_cmstdtc, type: date, range: [1950-01-01, 2026-12-31]}
  end_date: {column: med_psy_cmendtc, type: date, range: [1950-01-01, 2026-12-31]}
at_visit:
  title: Treatments on the day of the visit
  start: start_date
  end: end_date
  columns:
    on_lithium: {where: {treatment_group: lithium}, label: On lithium at the visit}
    on_lamotrigine: {where: {molecule: lamotrigine}, label: On lamotrigine at the visit}
```

**`level: list`.** The lists are opened into one row per patient and item,
and these rows go through the same steps as visit rows: every variable field
of section 4 applies to an item. The rows are delivered in the table
`treatments` of the result, with `usubjid` and `item` (1, 2, 3...) in front.
In the flag log the column `visit` holds `item 3`. Where the rows of a
patient hold different lists, the first is kept and the patient gets
`patient_value_varies`.

**`names`.** One list holds names typed or picked in a catalogue, and many
names mean the same thing (a brand, the same brand with its dose, a generic
with the maker's name). `clean` names a function of `custom.py` that cuts a
name to its stem. The stem is looked up in the `name` column of the table:
first whole, then its first two words, then its first word, so that
`LAMOTRIGINE ARROW` is found under `LAMOTRIGINE`. The columns listed in
`gives` are then columns that variables can read, like raw columns. A name
that is not in the table keeps what was written, leaves the columns of
`gives` empty and gets `unknown_code`: a name is never guessed.

The table is data of the package, not patient data: it holds what the
pharmacopoeia says (TERALITHE is lithium, group lithium, ATC N05AN01). It is
written by hand and must be read by someone who knows the drugs.

**`at_visit`.** A list has no visit: what a visit needs is whether the
patient was on a treatment that day. Each column of `columns` is 1 on a
visit when at least one item that fits `where` (a variable and the value it
must have) has `start` on or before the visit date and `end` on or after it,
or no `end`: an item without an end date is taken as still running. It is 0
when the patient has items and none fits. It is missing when the patient has
no list at all, when the visit has no date, and when the only items that fit
have no start date. These columns are delivered in `data` and described as
an instrument of their own, named `<instrument>_at_visit`, with a page in
the report.

`check_schema` verifies that `names` and `at_visit` come with `level: list`,
that `clean` is a function of `custom.py`, that `start`, `end` and the
variables named in `where` are variables of the schema, and that every
column has a `where` and a `label`.

## 16. Relatives: one row per relative

The family history asks the same questions for the mother, the father, each
sister, each brother and so on. The extraction has one set of columns per
relative, with the same endings: `mere_trouble`, `pere_trouble`,
`soeur1_trouble`... A schema with `level: relatives` describes the questions
once and lists the relatives.

```yaml
instrument: family_history
level: relatives
relatives:                 # prefix of the raw columns: what the rows of this relative get
  mere:   {relative: mother,   kinship: mother, degree: 1}
  pere:   {relative: father,   kinship: father, degree: 1}
  soeur1: {relative: sister_1, kinship: sister, degree: 1}
  soeur2: {relative: sister_2, kinship: sister, degree: 1}
variables:
  kinship: {column: kinship, type: category, codes: {mother: mother, father: father, sister: sister}}
  relative_disorder: {column: trouble, type: category, codes: {Bipolaire: bipolar, Aucun: none}}
  relative_birth_date: {column: brthdtc, type: date, range: [1840-01-01, 2026-12-31]}
per_patient:
  title: Family history, per patient
  by: kinship
  counts: {mother: mother_affected, father: father_affected, sister: n_sisters_affected}
  columns:
    fdr_bipolar:
      label: A first-degree relative with bipolar disorder
      among: [mother, father, sister]
      where: {relative_disorder: bipolar}
```

**`relatives`.** Each key is the prefix of the raw columns of one relative:
the variable that says `column: trouble` reads `mere_trouble` for the
mother and `soeur1_trouble` for the first sister. Every column must exist
for every relative. The fields of a relative are free, except `relative`,
which is required and names the row: they become columns that variables can
read like raw columns (`kinship`, `degree`).

**`level: relatives`.** The columns of every relative are put under one
another, and these rows go through the same steps as visit rows: every
variable field of section 4 applies. They are delivered in the table
`relatives` of the result, with `usubjid` and `relative` in front. In the
flag log the column `visit` holds the name of the relative.

- A family is described once, most often at inclusion, sometimes completed
  at a later visit. For each relative and column, the first cell of the
  patient that is not empty is read, in visit order. Where a later visit
  holds another text, the first is kept and the cell gets
  `patient_value_varies`.
- A relative has a row when at least one of the variables read from the raw
  columns has a value. A relative for whom the cells hold only missing codes
  or placeholder dates has no row; the flags of these cells stay in the log.

**`per_patient`.** What an analysis most often needs is one answer per
patient: is there a relative with bipolar disorder among the parents, the
siblings and the children? Each column of `columns` is computed from the
rows of the relatives:

- `by` names the variable that says to which group of relatives a row
  belongs, and `among` lists the groups that the column looks at.
- `where` gives variables and the value they must have. A list of values
  means any of them: `{relative_suicide: [attempt, completed]}`.
- `counts` names, for each group, a variable of a patient-level schema of
  the cohort that says how many relatives of the group have something to
  describe: 1 or 0 for the mother, a number for the sisters. The form asks
  for the details of these relatives only.

A group answers **yes** when one of its rows fits `where`. It answers **no**
when its count is known and at least that many of its rows have a value for
every variable of `where`: all the relatives that had to be described are
described, and none fits. With a count of 0 this is a no without any row.
Otherwise the group is **unknown**. The column is 1 when one group of
`among` answers yes, 0 when all of them answer no, and missing otherwise:
one "do not know" is enough to leave it missing, unless another relative
says yes.

These columns are delivered in `patients` and described as an instrument of
their own, named `<instrument>_per_patient`, with a page in the report. The
schema that holds the counts must be loaded with the relatives: `load()`
stops with a message if it is not.

`check_schema` verifies that `relatives` and `per_patient` come with `level:
relatives`, that every relative has a `relative`, that `by` and the
variables named in `where` are variables of the schema, that the groups of
`among` are listed in `counts`, and that every column has a `label`. Put
side by side, the schemas of the cohort must give the variables named in
`counts`, in patient-level schemas.

