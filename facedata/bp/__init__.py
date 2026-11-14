"""FACE BP (bipolar disorder).

The instrument schemas are in facedata/bp/schemas/<tab>/<instrument>.yaml.
"""

from pathlib import Path

import yaml

from facedata import qc
from facedata.pipeline import run_cohort
from facedata.read import prepare_visits, read_extraction
from facedata.report import write_report
from facedata.schema import load_schemas
from facedata.thesaurus import read_thesaurus

FOLDER = Path(__file__).parent
SCHEMAS = FOLDER / "schemas"


def load(path, instruments=None, winsor_limits=None, norms="norms"):
    """Load a FACE BP extraction (.tsv).

    instruments: names of the instruments to load. Default: all that have a schema.
    winsor_limits: the qc table of an earlier load, to reuse its winsor limits.
    norms: the folder that holds the norm tables (they are not part of the repository).
    Returns a Result with six tables: data, patients, flags, qc, treatments and relatives.
    """
    return run_cohort(path, SCHEMAS, instruments, winsor_limits, norms, cohort="bp")


def report(result, folder):
    """Write the HTML quality-control report of a load into `folder`. Returns the index page."""
    return write_report(result, load_schemas(SCHEMAS), folder)


def coverage(path, thesaurus_path=None):
    """Which columns of the extraction have a schema yet: one line per column name."""
    raw, keys, flags = prepare_visits(read_extraction(path))
    names = set(read_thesaurus(thesaurus_path)["name"]) if thesaurus_path else set()
    with open(FOLDER / "ignored.yaml", encoding="utf-8") as file:
        ignored = yaml.load(file, Loader=yaml.BaseLoader)
    return qc.coverage(raw, keys, load_schemas(SCHEMAS), names, ignored)
