# The FACE data dictionary

One page and one JSON file that describe every variable that `facedata`
delivers for the four cohorts (BP, SZ, DR, ASP): what it measures, what a
higher value means, how it is derived, where it lives in the data, which
cohorts and visits have it, how much is missing and how the values are spread.

| File | What it is |
|---|---|
| `facedata/dictionary/FACE-data-dictionary.html` | The page for people. Opens from the disk, with no network. Inside the package: every install has it |
| `facedata/dictionary/face_dictionary.json` | The same content for programs. One line per variable. Inside the package too |
| `dictionary/incomplete.csv` | The instruments and variables with a field that no source gives |
| `dictionary/stats/<cohort>.json` | The figures of each cohort, written by step 1 |
| `dictionary/annotations/*.yaml` | Written by hand: description, version, reference, construct, direction, cut-offs |
| `dictionary/constructs.yaml` | The list of constructs that an annotation may name |
| `dictionary/config.yaml` | The paths of the extractions and of the Excel dictionaries, the tabs of the view "all cohorts" |
| `build_stats.py`, `build_json.py`, `build_html.py`, `template.html` | The three steps |
| `check_numbers.py` | Checks the figures against the data by another road |

How to use the page and the JSON is in the [README](../README.md) of the
repository. This file says how they are built.

**The four generated files are committed**, so that whoever installs the
package knows what it delivers. They hold figures computed from patient data,
under these rules, which `tests/test_dictionary.py` checks on the committed
files:

- aggregates only: no row of a patient, and no centre (only how many centres
  have a value);
- a count from 1 to 4 is written `-1` ("fewer than 5"), and a percentage that
  would give such a count away is left out. This is the masking of the
  database reviews: one masked count beside a total can sometimes be worked
  out from the others;
- the values of a text column are never written, only how many there are;
- no label and no coding of the Excel dictionaries (`excel_labels: false` in
  `config.yaml`): the workbooks are not part of the repository, and their
  answer labels can hold the wording of a published questionnaire. Set it to
  `true` for a build that stays on your computer, and never commit that build;
- no value of a norm table: a score read in a table names the file only.

## Rebuild

```bash
.venv/bin/python dictionary/build_stats.py     # 1. loads the four cohorts and counts (a few minutes)
.venv/bin/python dictionary/build_json.py      # 2. schemas + annotations + figures -> facedata/dictionary/face_dictionary.json
.venv/bin/python dictionary/build_html.py      # 3. JSON + template -> facedata/dictionary/FACE-data-dictionary.html
.venv/bin/python dictionary/check_numbers.py   # the figures against the extractions
```

- A new extraction: change its path in `config.yaml`, then run the four lines.
- A schema changed: run the four lines. A test fails as long as the committed
  dictionary does not list exactly the variables that the schemas deliver.
- Only an annotation changed: steps 2 and 3 are enough.
- Commit the regenerated files with the change that caused them, so that the
  dictionary of a version of the package describes that version.
- `build_stats.py dr sz` computes some cohorts only. `--cached` keeps the
  loads in `local/cache/` and reuses them at the next run: use it while you
  work on the scripts, never after a schema or an extraction changed.

`tests/test_dictionary.py` runs the three steps on a made-up cohort, checks
that every annotation still names an instrument, a score and a construct that
exist, and checks the committed files against the rules above.

## Where each piece of information comes from

| Information | Source |
|---|---|
| Label, type, range, codes, unit, raw column, edition, score formula, reading rules, notes | The schemas, `facedata/<cohort>/schemas` |
| Description, version, reference, respondent, construct, period, direction, cut-offs, caveats | `annotations/*.yaml`, written from the notes of the schemas and from the literature notes, each with its source |
| Counts, missing values, visits, distributions, flags | The tables that `load(winsorise=False)` returns (`build_stats.py`) |
| Can the cohorts be stacked, what differs | `facedata/common_instruments.yaml`, `facedata/shared_names.yaml`, `facedata/<cohort>/differences.yaml`, and a comparison of the schemas |
| Tabs | The sheets of the Excel dictionaries of `thesauri/`, when they are on the computer (without them, the tab named in the schema) |
| French label, coding of the answers | The same workbooks, only in a build with `excel_labels: true`, which is never committed. Marked "not verified": the schemas are the reference |
| Meaning of the flag codes | `docs/ARCHITECTURE.md`, section 6 |

**Nothing is guessed.** A field that no source gives stays empty, and its
name goes into the list `incomplete` of the variable (and into
`incomplete.csv`). Three directions are derived, and say so in `basis`:
`formula` (an item takes the direction of the score that counts it, turned
when the item is reversed), `coding` (a yes/no answer: 1 is yes) and
`measurement` (a number with a unit: a larger measured value).

## The JSON file

```
meta          title, date, git commit, how ids are made, the description of every field (meta.fields)
cohorts       <cohort>: title, extraction, tabs, patients, visits (label, planned month, number), tables
constructs    <key>: area and label
flags         <code>: severity and meaning
instruments   <name>: one record per instrument
variables     <id>: one record per delivered column name
```

**The id of a variable is its column name** in the tables that
`facedata.<cohort>.load()` returns: `result.data`, `result.patients`,
`result.treatments` or `result.relatives` (the field `table` says which). A
name holds the same thing in every cohort that delivers it; the few
exceptions are in `harmonisation`. The raw column of the extraction is in
`cohorts.<cohort>.source.columns`.

The file has one line per instrument and per variable, each starting with its
id, so a search finds a whole record without reading the 18 MB:

```bash
grep -m1 '^"madrs_total":' facedata/dictionary/face_dictionary.json
```

```python
import json
dictionary = json.load(open("facedata/dictionary/face_dictionary.json", encoding="utf-8"))
record = dictionary["variables"]["madrs_total"]
record["direction"]                     # higher_means, polarity, basis, source
record["cohorts"]["bp"]["missing"]      # all, baseline, in_instrument (percentages)
scores = [name for name, one in dictionary["variables"].items()
          if one["level"] == "score" and one.get("construct") == "depression" and {"bp", "dr"} <= set(one["cohorts"])]
```

### A variable

| Field | Content |
|---|---|
| `id`, `label`, `meaning` | The column name, the label of the schema, and a plain sentence when one was written |
| `level` | `item` (counted in a score), `subscore`, `score`, `standalone` (belongs to no score), `companion` (censoring column or column that names an edition), `key` |
| `kind`, `type`, `unit` | `kind`: continuous, ordinal, binary, nominal, date or text. `type`: the type of the schema (number, item, band, category, date, time, text, score) |
| `instrument`, `tab` | The instrument and its tab in the view "all cohorts" |
| `construct` | A key of `constructs`: of the variable when its annotation names one, else of its instrument |
| `direction` | `higher_means`, `polarity` (worse, better, neutral, not_applicable), `basis`, `source`, and for an item `in_score` (the score and `keyed`: same, reversed or recoded) |
| `cutoffs` | `value`, `meaning`, `source`, `confidence`. Only cut-offs that a project document gives |
| `parents`, `children`, `computed_from`, `companion_of` | The hierarchy |
| `harmonisation` | `stack` (yes, with care, no), `recommended`, `exception`, `raw_column_note`, `differences` |
| `incomplete` | The fields that no source gives: meaning, construct, direction, range, answer_labels |
| `cohorts.<cohort>` | See below |

### A variable in one cohort

`label`, `level`, `kind`, `type`, `unit`, `instrument` and `tab` are written in
the cohort block only when they differ from the record.

| Field | Content |
|---|---|
| `table`, `source` | Where the value is delivered, and the raw columns read (`stored_score`: the column of the score as stored). The extraction file is `cohorts.<cohort>.extraction` |
| `range`, `categories`, `raw_codes`, `answer_labels`, `missing_codes` | The values it can take. `range_from` says when the range of a score was computed from the ranges of its items |
| `edition` | The column that names the edition and the values on which the variable is read |
| `derivation` | `method`, `formula` in words, `items`, `reverse`, `points`, `scale`, `min_items`, `norm_table`, `function`, `stored_in` |
| `reading`, `rules` | The rules of the schema that change how a value is understood, as fields and as sentences |
| `n` | `rows`, `valid`, `patients`, `patients_2plus` (a value at two visits or more), `baseline` |
| `missing` | Percentages. `all`: rows without a value. `baseline`: patients without a value in the baseline row. `in_instrument`: visits without a value among those that hold a value of the instrument |
| `timepoints` | Number of values at each visit label |
| `stats` | `all` and `baseline`: n, mean, sd, min, max, percentiles; for a date the first and last year; for a text n and n_distinct only |
| `dist` | `all` and `baseline`. `bins`: `x` holds the edges between the 1st and 99th percentile and the end bins hold the tails. `levels`: one count per answer. `years`: one count per year |
| `flags`, `censored`, `years`, `n_sites` | The flags raised by facedata, the censored cells, the first and last year, the number of centres |

**Baseline** is one row per patient: the inclusion visit, completed by the
screening visit when the inclusion visit holds nothing of the instrument
(`facedata.common.baseline`). **The figures are not winsorised.** A count from
1 to 4 is written `-1`, and a percentage that would give it away is left
out. A variable with fewer than 5 values has no figures,
and one with fewer than 20 no distribution.

## Annotations

One YAML file per group of instruments, a mapping from the name of an
instrument to its annotation. An instrument that several cohorts have is
annotated once.

```yaml
madrs:
  description: Ten items rated by the clinician, each from 0 to 6.
  version: 10 items
  reference: "Montgomery SA, Asberg M. Br J Psychiatry 1979;134:382-389"   # or not_applicable for a form of the application
  reference_confidence: confirmed in source (abstract)
  respondent: clinician          # patient, clinician, relative, test, laboratory, measurement, computed
  construct: depression          # a key of constructs.yaml
  period: past week
  sources: [schema notes (bp madrs), scale_reference.md section 1]
  items: {higher_means: more severe symptom, polarity: worse, basis: literature, source: ...}
  scores:
    madrs_total:
      meaning: Severity of depression, the sum of the ten items.
      higher_means: more severe depression
      polarity: worse            # worse, better, neutral, not_applicable
      basis: literature          # stated, anchors, literature
      source: scale_reference.md section 1
      cutoffs:
        - {value: "7 to 19", meaning: mild depression, source: ..., confidence: secondary}
  variables:
    "tmt_*_z": {higher_means: better performance, polarity: better, basis: stated, source: "schema notes (bp tmt)"}
  flags:
    - What a user must know, and what stays to verify.
```

Rules:

- Write only what a document states, and name the document in `source`.
  `stated`: a note or a label says it in words. `anchors`: it follows from the
  answer labels or from what is counted. `literature`: the literature notes
  say it; copy their confidence tag. No source: leave the field out.
- A key of `scores` or `variables` may hold `*` to cover several names; an
  exact name wins.
- No wording of a questionnaire item beyond the short labels of the schemas,
  no value of a norm table, no name of a centre.
- A new construct gets a line in `constructs.yaml` first.

The first version of the annotations was drafted on 2026-11-21 from the
schema notes and from the literature notes of `local/out/scale_reference*.md`.
What a reviewer was unsure about is in the `flags` of the instrument.
