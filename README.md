# facedata

Load the FACE psychiatric cohorts in Python:

- FACE BP (bipolar disorder);
- FACE SZ (schizophrenia);
- FACE DR (treatment-resistant depression);
- FACE ASP (autism spectrum, children and adults).

facedata reads the extraction file of a cohort, checks every cell and returns
harmonised tables. A guide and a data dictionary come with the package and
describe every variable it delivers.

- Every column of the four extractions is either read or left out for a
  stated reason.
- Scores are recomputed from their items. Where the database stored a score,
  facedata compares the two, and corrects a stored score that is known to be
  wrong.
- An instrument shared by several cohorts has the same column names in each,
  so the tables of several cohorts can be stacked.
- Every value that is changed or doubtful is listed in `result.flags`, next to
  its raw value.

## Install

The repository is private: you need access to it on GitHub. The extractions
and the norm tables are not part of the package (see
[Patient data](#patient-data)).

With uv:

```bash
uv add "facedata @ git+https://github.com/fondationfondamental/facedata@v0.3.0"
```

With pip:

```bash
pip install "facedata @ git+https://github.com/fondationfondamental/facedata@v0.3.0"
```

`@v0.3.0` pins a release, so an analysis keeps giving the same results when
the package changes.

## Set up your research project

Run this once, in the folder of your project:

```bash
facedata init
```

It writes a short block into `AGENTS.md`, which Codex, Cursor, Copilot and
other coding agents read, and makes `CLAUDE.md` read it, for Claude Code. The
block tells an agent:

- what the cohorts are;
- where the guide and the data dictionary are, and how to search them;
- the rules for patient data.

The rest of both files is kept. Run it again after an upgrade to refresh the
block.

You and your agents can then use these commands. In a uv project, run them as
`uv run facedata ...`; anywhere, as `python -m facedata ...`.

| Command | What it gives |
|---|---|
| `facedata guide` | The guide to the four cohorts; `--section 4` prints one section |
| `facedata find depression --cohort dr --level score` | The variables whose id, label or meaning holds every word |
| `facedata show madrs_total madrs` | The records of variables or instruments, as JSON; `--full` keeps the distributions |
| `facedata instruments --cohort sz` | The instruments of a cohort; `--shared` lists those of two cohorts or more |
| `facedata page` | Opens the data dictionary page in your browser |
| `facedata files` | Prints where the guide, the dictionary and the page are |

The same from Python: `from facedata import guide`, then
`guide.find("depression", cohort="dr")`, `guide.variable("madrs_total")` or
`guide.instruments(shared=True)`.

**Start with the guide.** It covers:

- loading, and the checks to make before an analysis;
- each cohort, with its visits and its traps;
- the instruments the cohorts share;
- the same subject measured with other instruments;
- the editions that must never share a column;
- every instrument.

Read it on GitHub:
[FACE-guide.md](https://github.com/fondationfondamental/facedata/blob/main/facedata/dictionary/FACE-guide.md).

## Load a cohort

```python
from facedata import bp          # or sz, dr, asp

result = bp.load("/path/to/BPALL_20261113_2.tsv", norms="/path/to/norms")

result.data        # one row per patient visit
result.patients    # one row per patient
result.flags       # one row per changed or doubtful cell, with its raw value
result.qc          # one row per variable: counts, range, flags
result.treatments  # one row per patient (or visit) and medication
result.relatives   # one row per patient and relative: the family history
```

- **To load only what you need**, name the instruments with
  `bp.load(path, instruments=["madrs", "ymrs"])`. This takes seconds. Loading
  all of FACE BP takes about a minute and a half.
- **Each variable has a name** in the data dictionary, and that name is its
  column in one of these tables. The field `instrument` of a variable is what
  you pass to `instruments=`.
- **The key of a patient is `cohort` with `usubjid`.** A `usubjid` is unique
  only inside its cohort. `patients` also holds `fondacode`, the patient code
  that is unique across cohorts and stays the same from one extraction to the
  next.
- **Extreme values of measures are clipped** to the 1st and 99th percentile,
  with the flag `winsorised`. Vital signs and ECG intervals are not clipped.
  `winsorise=False` keeps every value as it was typed.
- **The norm tables** turn raw test scores into T-scores, percentiles and
  z-scores; `norms` defaults to a folder named `norms` in the current
  directory. Without the tables, the package still loads: those standard
  scores are missing, and `result.flags` says so. Sums and means of items do
  not need the tables.
- **A quality report:** `bp.report(result, "reports/bp")` writes an HTML report
  with plots. Open `reports/bp/index.html`. It takes about ten minutes.

[ARCHITECTURE.md](https://github.com/fondationfondamental/facedata/blob/main/docs/ARCHITECTURE.md#4-what-load-returns)
describes every column of the six tables. The flag codes are in section 7 of
the guide.

| Module | Patients | Worth knowing |
|---|---|---|
| `bp` | Adults with a bipolar disorder | A `_v0` column (inclusion, the whole life) and a `_fu` column (follow-up, since the last visit) are two different questions. Sex, diagnosis and family history are in `patients` |
| `sz` | Adults with schizophrenia, a schizoaffective or a schizophreniform disorder | `_v0` and `_fu` as in BP. Some scores that the database stored wrong are delivered corrected. Read an extraction of 2026-11-23 or later: in the earlier files two Calgary items are in the wrong columns |
| `dr` | Adults with a treatment-resistant major depressive disorder | The screening visit is a row of its own (`visit == "screening"`), with the MINI and the inclusion criteria. `treatments` holds three lists, named in the column `list` |
| `asp` | Children from 5 years and adults assessed for an autism spectrum disorder | `diagnosis` says whether the centre confirmed the disorder; both groups are delivered. Children and adults answer different forms, in different columns. `treatments` holds eleven lists |

For each cohort's visits and traps, run `facedata guide --section 4`.

## Work across cohorts

All four modules deliver the same patient columns. An instrument that several
cohorts share has the same column names in each. So the tables of several
cohorts can be stacked:

```python
import pandas as pd
from facedata import bp, sz

one = bp.load("/path/to/BPALL_20261113_2.tsv", instruments=["identite", "ymrs"])
two = sz.load("/path/to/SZALL_20261123.tsv", instruments=["identite", "ymrs"])
visits = pd.concat([one.data, two.data], ignore_index=True)
patients = pd.concat([one.patients, two.patients], ignore_index=True)
```

Before you stack, check the verdict for each instrument. `facedata.common` has
them:

- `common.catalogue()` lists the instruments that two cohorts or more share.
  For each one, it says whether it stacks as it is ("yes", "with care" or
  "no") and names the variables to use.
- `common.baseline()` returns one row per patient: the inclusion visit,
  completed by the screening visit.

```python
from facedata import bp, common

table = common.catalogue()                     # instrument, cohorts, stack, use, note
wanted = table[table["stack"] != "no"]

bipolar = bp.load("/path/to/BPALL_20261113_2.tsv", instruments=common.instruments_of("bp", wanted), winsorise=False)
first, source = common.baseline(bipolar)       # one row per patient, and the visit each instrument comes from
```

Some instruments are not on one scale: the same subject can be measured with
different instruments in different cohorts (depression is rated with the MADRS
in BP and DR, the Calgary scale in SZ and the HAM-D in ASP). Section 5 of the
guide lists these instruments, and the editions that must stay in separate
columns.

## The data dictionary

Three files in the package describe every variable that `load()` delivers in
the four cohorts. Every install has them; `facedata files` prints where they
are.

| File | For whom |
|---|---|
| `FACE-guide.md` | Everyone, first: the guide described above (`facedata guide`) |
| `FACE-data-dictionary.html` | People: a page to browse, search and filter. It opens from the disk and needs no network (`facedata page`) |
| `face_dictionary.json` | Programs and coding agents: one record per variable, one line each (`facedata find`, `facedata show`) |

For each variable, the dictionary gives:

- its meaning, and what a higher value means;
- how it is derived;
- the cohorts and visits that have it;
- its missing values and its distribution;
- what differs between the cohorts.

The figures describe the extractions named in the page, under "How to read".
They are aggregates only: no row of a patient, no free text, no centre, and no
count from 1 to 4 (the page shows "<5", the JSON -1).

### The page

1. **Choose a cohort**, or "All cohorts", at the top.
2. **Search** any word: a variable name, a label, an instrument, or a raw
   column of the extraction.
3. **Filter** on the left: level, type, instrument, construct, the cohorts
   that deliver it, the timepoint, the share missing at baseline, whether the
   cohorts can be stacked.
4. **Click a row** to open its card. It shows what the variable measures and
   which way it runs, how it is derived, its figures in each cohort, and
   whether the cohorts can be stacked.
5. **Tick** the variables you want. The basket exports a CSV or JSON of their
   metadata, a Python list, an R vector, and the `load()` code for each
   cohort.

| I want | In the page |
|---|---|
| Scores that two cohorts share | "All cohorts", tick the two cohorts under *Delivered in*, Level *score*, Across cohorts *Instrument stacks* |
| Variables with enough follow-up for a longitudinal model | A cohort, Timepoint *1 year*, tick *Repeated*, Missing *Less than 25%* |
| Everything that measures one thing | Construct, for example *Depressive symptoms* |
| To put several scores on one scale | The card of each: *Higher = ...* says which way it runs |
| What is not documented | Metadata *A field is not documented* |

"Baseline" means one row per patient: the inclusion visit, completed by the
screening visit when the inclusion visit has nothing of the instrument.

### The JSON

`facedata show <id>` prints one record, and `facedata find <words>` searches
them. From Python:

```python
from facedata import guide

dictionary = guide.read_dictionary()

# the depression scores that FACE BP and FACE DR both deliver, with what a higher value means
for name, record in dictionary["variables"].items():
    if record["level"] == "score" and record.get("construct") == "depression" and {"bp", "dr"} <= set(record["cohorts"]):
        print(name, "|", record["direction"].get("higher_means"))
```

`dictionary["meta"]["fields"]` describes every field of a record.

Check these fields before you compute:

- `direction`, before you put variables on one scale;
- `harmonisation`, before you stack cohorts;
- `missing` and `timepoints`, before a longitudinal model;
- `edition`;
- the `flags` of the instrument.

An empty field means "not documented"; the names of those fields are listed in
`incomplete`. A count of -1 means "fewer than 5".

## Tutorials

These notebooks are on GitHub. To use one, download it into your project,
set the path of the extraction in its first cell, and open it with Jupyter, for
example `uv run --with jupyterlab jupyter lab bipolar-tutorial.ipynb`.

| Notebook | What it shows |
|---|---|
| [bipolar-tutorial.ipynb](https://github.com/fondationfondamental/facedata/blob/main/bipolar-tutorial.ipynb) | A first tour of FACE BP for people who do not code much: load, find a variable, plot, follow patients, avoid the traps |
| [schizophrenia-tutorial.ipynb](https://github.com/fondationfondamental/facedata/blob/main/schizophrenia-tutorial.ipynb) | The same tour for FACE SZ, ending with BP and SZ in one table |
| [depression-tutorial.ipynb](https://github.com/fondationfondamental/facedata/blob/main/depression-tutorial.ipynb) | FACE DR, with four use cases: response and remission, resistance and treatments, MINI diagnoses, life events |
| [autism-tutorial.ipynb](https://github.com/fondationfondamental/facedata/blob/main/autism-tutorial.ipynb) | FACE ASP, with four use cases: diagnostic profile, children and adults, comorbidities and treatments, self-reported traits |
| [common-instruments.ipynb](https://github.com/fondationfondamental/facedata/blob/main/common-instruments.ipynb) | The four cohorts together: the shared instruments, one baseline row per patient, the stacked table, what to check before comparing |

Run the cells from top to bottom with `Shift` + `Enter`. The output under a
cell is patient data. Before you save a notebook that will be shared, clear it
(*Edit*, *Clear Outputs of All Cells*).

## Patient data

- **The extractions** (`.tsv` files) are pseudonymised patient records. Keep
  them out of git, for example in a `data/` folder listed in `.gitignore`.
- **Report aggregates only.** Never copy rows, identifiers (`usubjid`,
  `fondacode`), the dates of a patient or free text into code, documents or
  commits. Write a count from 1 to 4 as "fewer than 5". Do not name centres.
- **The norm tables** come from the test manuals and are copyrighted. Keep
  them out of git too, and never copy a value of them into code or notes.

## Working on facedata itself

How the package works, how to add an instrument and how to rebuild the data
dictionary are explained in
[docs/ARCHITECTURE.md](https://github.com/fondationfondamental/facedata/blob/main/docs/ARCHITECTURE.md),
[docs/SCHEMA_SPEC.md](https://github.com/fondationfondamental/facedata/blob/main/docs/SCHEMA_SPEC.md)
and [dictionary/README.md](https://github.com/fondationfondamental/facedata/blob/main/dictionary/README.md).
