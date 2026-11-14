"""FACE ASP (Asperger syndrome and autism spectrum disorders).

The instrument schemas are in facedata/asp/schemas/<table>/<instrument>.yaml.
The folder of a schema is the source table of its columns. The dictionary arrived after the
module: the notes of each schema say how its instrument was identified and what the dictionary confirms. An instrument
that FACE BP, SZ or DR also has starts as a copy of that schema and keeps its names;
facedata/asp/differences.yaml lists the copies that had to change.
"""

from pathlib import Path

import yaml

from facedata import qc
from facedata.pipeline import run_cohort
from facedata.read import prepare_visits, read_extraction
from facedata.report import write_report
from facedata.schema import load_schemas

FOLDER = Path(__file__).parent
SCHEMAS = FOLDER / "schemas"
FIRST_VISIT = "2009-01-01"       # the cohort opened that year: an earlier visit date is impossible
FIRST_TABLE = "patient"          # the columns before the first marker: the patient and the visit


def load(path, instruments=None, winsor_limits=None, norms="norms", winsorise=True):
    """Load a FACE ASP extraction (.tsv).

    instruments: names of the instruments to load. Default: all that have a schema.
    winsor_limits: the qc table of an earlier load, to reuse its winsor limits.
    norms: the folder that holds the norm tables (they are not part of the repository).
    winsorise: False leaves the tails of the continuous variables as they are (no clipping, no limits in qc).
    Returns a Result with six tables: data, patients, flags, qc, treatments and relatives.
    """
    return run_cohort(path, SCHEMAS, instruments, winsor_limits, norms, cohort="asp", repair_accents=True, first_visit=FIRST_VISIT, winsorise_values=winsorise)


def report(result, folder):
    """Write the HTML quality-control report of a load into `folder`. Returns the index page."""
    return write_report(result, load_schemas(SCHEMAS), folder)


def source_tables(columns):
    """The source table of each column of the extraction: {column: table}.

    The export writes its tables one after the other. Each table but the first
    starts with a copy of the patient identifier, named subjid_<table>.
    """
    tables, table = {}, FIRST_TABLE
    for column in columns:
        if column.startswith("subjid_"):
            table = column[len("subjid_"):]
        tables[column] = table
    return tables


def coverage(path):
    """Which columns of the extraction have a schema yet: one line per column name, with its source table."""
    raw, keys, flags = prepare_visits(read_extraction(path, repair_accents=True), FIRST_VISIT)
    with open(FOLDER / "ignored.yaml", encoding="utf-8") as file:
        ignored = yaml.load(file, Loader=yaml.BaseLoader) or {}      # an empty list of ignored columns
    lines = qc.coverage(raw, keys, load_schemas(SCHEMAS), set(), ignored)
    tables = source_tables(raw.columns)
    lines.insert(1, "table", lines["column"].map(tables).fillna(""))
    return lines
