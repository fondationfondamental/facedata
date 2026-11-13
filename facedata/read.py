"""Read an extraction and build the key columns of each visit."""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from facedata.flags import make_flags, stack_flags
from facedata.tokens import EMPTY_DATE, PLACEHOLDER_VISIT_DATES


def read_extraction(path):
    """Read the .tsv extraction. Every cell stays text, exactly as written."""
    return pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")


def read_norms(folder):
    """Read the norm tables of a folder: {file name without .csv: table}.

    A table has one line per cell: age_min, age_max, raw_min, raw_max, value.
    A folder that does not exist gives no table.
    """
    tables = {}
    for path in sorted(Path(folder).glob("*.csv")):
        tables[path.stem] = pd.read_csv(path)
    return tables


def visit_month(label):
    """Planned months since inclusion, read from the visit label.

    V0 -> 0, V6_mois -> 6, V1_an -> 12, V2_ans -> 24. Other labels -> missing.
    """
    if label == "V0":
        return 0
    found = re.fullmatch(r"V(\d+)_(mois|ans?)", label)
    if found is None:
        return np.nan
    number = int(found.group(1))
    return number if found.group(2) == "mois" else 12 * number


def prepare_visits(raw):
    """Drop duplicated visit records and build the key columns.

    Returns the extraction without duplicates (rows numbered from 0), the key
    columns, and the flags.
    """
    is_copy = raw.duplicated(subset="visitnum", keep="first")
    has_copy = raw.duplicated(subset="visitnum", keep=False) & ~is_copy
    raw = raw[~is_copy].reset_index(drop=True)
    has_copy = has_copy[~is_copy].reset_index(drop=True)

    keys = pd.DataFrame({"usubjid": raw["usubjid"], "visit": raw["visit"]})
    keys["visit_order"] = pd.to_numeric(raw["id_visit"], errors="coerce")
    keys["visit_month"] = raw["visit"].map(visit_month)
    is_placeholder = raw["svdtc"].isin(PLACEHOLDER_VISIT_DATES)
    date_text = raw["svdtc"].where(~is_placeholder & (raw["svdtc"] != EMPTY_DATE), "")
    keys["visit_date"] = pd.to_datetime(date_text, format="%Y-%m-%d", errors="coerce")
    keys["siteid"] = raw["siteid"]
    # Age at the visit, in years. The export gives the date of birth to the month only.
    keys["age"] = np.nan
    if "brthdtc" in raw.columns:
        birth = pd.to_datetime(raw["brthdtc"], format="%Y-%m-%d", errors="coerce")
        keys["age"] = (keys["visit_date"] - birth).dt.days / 365.25

    # A visit dated before the patient's previous visit is out of order.
    dated = keys.dropna(subset=["visit_date"]).sort_values(["usubjid", "visit_order"])
    previous = dated.groupby("usubjid")["visit_date"].shift()
    out_of_order = (dated["visit_date"] < previous).reindex(keys.index, fill_value=False)

    flags = stack_flags([
        make_flags(has_copy, "visit", "duplicate_row"),
        make_flags(is_placeholder, "visit_date", "date_placeholder"),
        make_flags(out_of_order, "visit_date", "visit_order", "dated before the previous visit"),
    ])
    return raw, keys, flags
