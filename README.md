# facedata

Load, harmonise and quality-check data from the FACE psychiatric cohorts
(bipolar disorder, schizophrenia, resistant depression, Asperger).

One module per cohort. Everything specific to an instrument is written in a
small YAML schema; the Python code is generic and stays small.

**Status:** every column of the four extractions (BP, SZ, DR, ASP) is read or
deliberately ignored. All the schemas are reviewed, tab by tab (BP 135, SZ 125, DR 139, ASP 146):
each cohort's progress file
lists the decisions taken and the questions still open
([BP](docs/bp/PROGRESS.md), [SZ](docs/sz/PROGRESS.md), [DR](docs/dr/PROGRESS.md),
[ASP](docs/asp/PROGRESS.md)).

## Read first

| Document | What it tells you |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | What the package returns, the pipeline steps, the flag codes, the QC report |
| [docs/SCHEMA_SPEC.md](docs/SCHEMA_SPEC.md) | Every field a schema may contain, and how to add an instrument |
| [docs/bp/PROGRESS.md](docs/bp/PROGRESS.md) | FACE BP checklist, decisions taken, decisions still open |
| [docs/bp/QUESTIONS.md](docs/bp/QUESTIONS.md) | The open questions of FACE BP as a list to close, sorted by who can close them (the application, the data, a choice of method, the data managers) and by priority, and the state of the norms |
| [docs/sz/PROGRESS.md](docs/sz/PROGRESS.md) | FACE SZ checklist, decisions taken, decisions still open, and what was corrected, separated or flagged |
| [docs/sz/QUESTIONS.md](docs/sz/QUESTIONS.md) | The same questions for FACE SZ |
| [docs/dr/PROGRESS.md](docs/dr/PROGRESS.md) | FACE DR (resistant depression) checklist, decisions taken, decisions still open, and what was corrected, separated or flagged |
| [docs/dr/QUESTIONS.md](docs/dr/QUESTIONS.md) | The same questions for FACE DR |
| [docs/asp/PROGRESS.md](docs/asp/PROGRESS.md) | FACE ASP (autism spectrum, children and adults) checklist, decisions taken, decisions still open. The dictionary arrived after the module was written: every instrument was identified from the data, then checked against it |
| [docs/asp/QUESTIONS.md](docs/asp/QUESTIONS.md) | The same questions for FACE ASP |
| [bipolar-tutorial.ipynb](bipolar-tutorial.ipynb) | A first tour of the FACE BP data for people who do not code much: load, find a variable, plot, follow patients, avoid the traps |
| [schizophrenia-tutorial.ipynb](schizophrenia-tutorial.ipynb) | The same tour for FACE SZ, with a last section that puts the two cohorts in one table |
| [depression-tutorial.ipynb](depression-tutorial.ipynb) | The same tour for FACE DR, with four use cases (response and remission, resistance and treatments, MINI diagnoses, life events) and a last section that puts the three cohorts in one table |
| [autism-tutorial.ipynb](autism-tutorial.ipynb) | The same tour for FACE ASP: children and adults, a dictionary that arrived after the work, four use cases (diagnostic profile, children and adults, comorbidities and treatments, self-reported traits) and a last section that puts the four cohorts in one table |
| [common-instruments.ipynb](common-instruments.ipynb) | The four cohorts together, for transdiagnostic work: the catalogue of the instruments they share, the screening and the inclusion visits in one row per patient, the stacked table, what to check before comparing |
| [The data dictionary](#data-dictionary-what-the-package-delivers-and-what-to-pick) | Every delivered variable in one page for people and one JSON file for coding agents: meaning, direction, derivation, cohorts and visits, missing values, distribution. How it is built: [dictionary/README.md](dictionary/README.md) |

## Install

The repository is private: you need access to it on GitHub. The data, the
norms and the dictionaries are not part of the package (see [Data](#data)).

**In another project, with uv:**

```bash
uv add "facedata @ git+https://github.com/fondationfondamental/facedata@v0.2.0"
```

**In another project, with pip:**

```bash
pip install "facedata @ git+https://github.com/fondationfondamental/facedata@v0.2.0"
```

`@v0.2.0` pins a released version, so an analysis keeps giving the same
results when the package changes. Leave it out to take the latest `main`.

`coverage()` reads the thesaurus workbooks and needs the extra `thesaurus`
(openpyxl). With uv:

```bash
uv add "facedata[thesaurus] @ git+https://github.com/fondationfondamental/facedata@v0.2.0"
```

The same with pip:

```bash
pip install "facedata[thesaurus] @ git+https://github.com/fondationfondamental/facedata@v0.2.0"
```

**From a local copy that you are changing:** an editable install sees your
edits at once. With uv, run this from the other project:

```bash
uv add --editable /path/to/facedata
```

With pip:

```bash
pip install -e /path/to/facedata
```

**To work on this repository itself** (tests, notebooks):

```bash
uv sync
```

Outside this folder, give the full path of the extraction and of the norm
tables: `bp.load("/path/to/BPALL_20261113_2.tsv", norms="/path/to/norms")`.
By default `norms` is the folder `norms` of the current directory.

## Data dictionary: what the package delivers, and what to pick

Two files inside the package describe every variable that `load()` delivers
for the four cohorts: 9,600 columns in 362 instruments. They hold the same
content, and every install has them.

| File | For whom |
|---|---|
| `facedata/dictionary/FACE-data-dictionary.html` | People: a page to browse, search and filter. It opens from the disk, with no network |
| `facedata/dictionary/face_dictionary.json` | Programs and coding agents: one record per variable, one line each |

Where they are on your computer, and the page opened in your browser:

```python
from pathlib import Path
import webbrowser

import facedata

folder = Path(facedata.__file__).parent / "dictionary"
print(folder)
webbrowser.open((folder / "FACE-data-dictionary.html").as_uri())
```

In a copy of this repository, double-click
`facedata/dictionary/FACE-data-dictionary.html`.

The name of a variable in the dictionary is the name of its column in the
tables that `load()` returns, so what you pick is what you ask for. The
figures were computed on the extractions named in the page ("How to read"):
they describe those files, and are rebuilt when a new extraction arrives
([dictionary/README.md](dictionary/README.md)). They are aggregates only: no
row of a patient, no value of a free-text column, no centre, and no count
from 1 to 4 (shown "<5").

### The page, for people

1. **Choose a cohort**, or "All cohorts", at the top. Each cohort shows the
   tabs of its own Excel dictionary.
2. **Search** any word: a variable name, a label, an instrument, a raw column
   of the extraction. The search looks in every tab, and each tab shows how
   many variables match.
3. **Filter** on the left: level (score, sub-score, item, single), type
   (continuous, ordinal, binary, nominal, date, text), instrument, construct,
   the cohorts that deliver the variable, the timepoint, the share of missing
   values at baseline, whether the cohorts can be stacked, and whether a
   field is not documented.
4. **Read a row**: the name, the label, the level and type, a dot per cohort
   that delivers it, a small distribution and the share missing at baseline.
   Open an instrument to see its rows; "About this instrument" gives its
   description, version, reference and the notes of its schema.
5. **Click a row** for its card. Before you use a variable, read on the card:
   - *What it measures*: the construct, and what a higher value means, with
     the source of that statement;
   - *Hierarchy and derivation*: the score it is counted in or the items it
     counts, the formula, the reversed items;
   - *In each cohort*: the table and column, the raw column of the
     extraction, the range or the categories, the number of values and of
     patients, the missing values, the distribution, the values at each
     visit, and the flags that facedata raised;
   - *Across cohorts*: whether the cohorts can be put under one another, and
     what differs.
6. **Tick** the variables you want. The basket keeps them when you change tab
   or cohort. It exports a CSV and a JSON with their metadata, a Python list,
   an R vector, and the `load()` code for each cohort.

| I want | In the page |
|---|---|
| Scores that two cohorts share, for a transdiagnostic analysis | "All cohorts", tick the two cohorts under *Delivered in*, Level *score*, Across cohorts *Instrument stacks* |
| Variables with enough follow-up for a longitudinal model | A cohort, Timepoint *1 year*, tick *Repeated*, Missing *Less than 25%* |
| Everything that measures one thing | Construct, for example *Depressive symptoms* |
| To put several scores on one scale | The card of each: *Higher = ...* says which way it runs |
| What is not documented | Metadata *A field is not documented*; the amber mark on a row lists the fields |

"Baseline" is one row per patient: the inclusion visit, completed by the
screening visit when the inclusion visit holds nothing of the instrument.
The figures are those of `load(winsorise=False)`: the tails are not clipped.

### The JSON, for coding agents

Read one record without loading the 18 MB: each variable is one line that
starts with its name.

```bash
grep -m1 '^"madrs_total":' facedata/dictionary/face_dictionary.json
```

Or load it and filter:

```python
import json
from pathlib import Path

import facedata

path = Path(facedata.__file__).parent / "dictionary" / "face_dictionary.json"
dictionary = json.loads(path.read_text(encoding="utf-8"))
variables = dictionary["variables"]

# the depression scores that FACE BP and FACE DR both deliver, with what a higher value means
for name, record in variables.items():
    if record["level"] == "score" and record.get("construct") == "depression" and {"bp", "dr"} <= set(record["cohorts"]):
        print(name, "|", record["direction"].get("higher_means"), "|", record["cohorts"]["bp"]["missing"])
```

A record gives, for a variable: `label`, `meaning`, `level`, `kind`,
`construct`, `direction` (what a higher value means, and how it is known),
`cutoffs`, `parents` and `children`, `harmonisation` (can the cohorts be
stacked, what differs), `incomplete`, and one block per cohort with the
table, the raw columns, the range or categories, the derivation, the counts,
the missing values, the values at each visit, the statistics and the
distribution. `dictionary["instruments"]` gives the description, version,
reference and schema notes of each instrument, and `dictionary["meta"]["fields"]`
describes every field.

Rules for an agent:

- **Pick by name.** A variable id is a column of `result.data`,
  `result.patients`, `result.treatments` or `result.relatives`; the field
  `table` of the cohort block says which. The instrument to give to
  `load(instruments=[...])` is the field `instrument`.
- **Check before you compute.** `direction` before putting variables on one
  scale or reversing one; `harmonisation` before stacking cohorts; `missing`,
  `timepoints` and `n.patients_2plus` before a longitudinal model; `edition`
  for a variable that exists on some visits only; the `flags` of the
  instrument for its caveats.
- **An empty field means "not documented".** Its name is in `incomplete`. Do
  not fill it from memory: say that it is not documented.
- **A count of -1 means "fewer than 5"**, and a percentage that would give
  such a count away is absent.
- Do not print the whole file, and do not edit it: it is generated
  ([dictionary/README.md](dictionary/README.md)).

## Use

```python
from facedata import bp

result = bp.load("data/bp/BPALL_20261113_2.tsv")

result.data       # one row per patient visit, harmonised
result.patients   # one row per patient
result.flags      # one row per flagged cell, with the raw value
result.qc         # one row per variable
result.treatments # one row per patient and medication, with its dates
result.relatives  # one row per patient and relative: the family history

bp.report(result, "reports/bp")          # open reports/bp/index.html
bp.coverage("data/bp/BPALL_20261113_2.tsv", "thesauri/FACEBP_thesaurus_V4.34.xlsx")
```

Loading everything takes about a minute and a half (a few seconds when you
name the instruments you need), the report about ten minutes.

FACE SZ is read the same way (`from facedata import sz`): every column of its
extraction is read by a schema or ignored with a reason, in 127 instruments.
Its 125 schemas are reviewed, tab by tab, and
the questions of `docs/sz/QUESTIONS.md` stay open until answered;
`docs/sz/PROGRESS.md` logs each decision. The tables of the two
cohorts have the same key columns and the same names for the instruments
they share, so they can be stacked:

```python
import pandas as pd
from facedata import bp, sz

one = bp.load("data/bp/BPALL_20261113_2.tsv", instruments=["identite", "ymrs"])
two = sz.load("data/sz/SZALL_20261117.tsv", instruments=["identite", "ymrs"])
patients = pd.concat([one.patients, two.patients], ignore_index=True)
visits = pd.concat([one.data, two.data], ignore_index=True)
```

FACE DR, the cohort of resistant depression, is read the same way too
(`from facedata import dr`): every one of the 2,375 columns of its extraction
is read by one of 138 schemas or ignored with a reason, and
`docs/dr/PROGRESS.md` logs each decision. Its screening visit is a visit of
its own (`visit == "screening"`), where the MINI is given. Its table
`treatments` holds three lists, named in the column `list`.

FACE ASP, the cohort of autism spectrum disorders, has children and adults
(`from facedata import asp`). Its extraction came without a dictionary: each
of its 4,364 columns is read by one of 138 schemas or ignored with a reason,
and every instrument was identified from its column names, its items and its
stored scores. The thesaurus arrived afterwards: it confirmed the instruments,
corrected eight readings and gave the wording of the lists and the labels; a
code that it does not document is delivered as a numbered code. Its table `treatments` holds eleven lists (the treatments of each
visit, the diseases of each body system, the relatives, the
hospitalisations). `docs/asp/PROGRESS.md` logs each decision.

The first column of every table is `cohort`. A `usubjid` is unique inside a
cohort only (the same number can be another patient in the other cohort), so
the key is `cohort` with `usubjid`. `patients` also holds `fondacode`, the
patient code that is unique across cohorts and does not change from one
extraction to the next.

`facedata.common` is for work across cohorts. Its catalogue lists the
instruments that two cohorts or more share, says which can be stacked as they
are, and names the variables to use; `baseline()` puts the screening visit and
the inclusion visit of a patient in one row:

```python
from facedata import bp, sz, common

table = common.catalogue()                                  # instrument, cohorts, stack (yes / with care / no), use, note
wanted = table[table["stack"] != "no"]

bipolar = bp.load("data/bp/BPALL_20261113_2.tsv", instruments=common.instruments_of("bp", wanted), winsorise=False)
first, source = common.baseline(bipolar)                    # one row per patient, and the visit each instrument comes from
```

## Tutorial

```bash
uv run jupyter lab bipolar-tutorial.ipynb
```

```bash
uv run jupyter lab schizophrenia-tutorial.ipynb
```

```bash
uv run jupyter lab depression-tutorial.ipynb
```

```bash
uv run jupyter lab autism-tutorial.ipynb
```

```bash
uv run jupyter lab common-instruments.ipynb
```

One notebook per cohort. The second one ends with a section that loads the
instruments shared by FACE BP and FACE SZ and stacks the two cohorts; the
third one stacks the three, and the fourth one the four. The fifth notebook
is about the four cohorts together: the catalogue of the common instruments,
one baseline row per patient, and the stacked table.

A notebook opens in the web browser. Run its cells from top to bottom with
`Shift` + `Enter`. What appears under a cell is patient data: clear it
(*Edit*, *Clear Outputs of All Cells*) before you save a notebook that will
be shared or sent to GitHub.

## Tests

```bash
uv run pytest
```

The tests use small hand-written tables. One test file per cohort also checks
the real extraction when it is on the computer, and is skipped otherwise.

## Data

The extractions (`data/`) and the data dictionaries (`thesauri/`) are not part
of the repository. Put them next to the code:

```
data/bp/BPALL_20261113_2.tsv
thesauri/FACEBP_thesaurus_V4.34.xlsx
norms/wais3_vocabulary.csv
```

`norms/` holds the norm tables of the tests (age band and raw score to
scaled score or percentile band). They are copyrighted, so they stay out of the repository
too. Without them the package still loads; the checks that need a table say
so in `result.flags`.

They hold pseudonymised patient records. Never copy rows or identifiers into
code, tests, documents or commits.
