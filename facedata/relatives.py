"""The same questions asked for each relative: one row per patient and relative (docs/SCHEMA_SPEC.md, section 16)."""

import numpy as np
import pandas as pd

from facedata.flags import make_flags, stack_flags
from facedata.harmonise import first_rows
from facedata.schema import given_columns
from facedata.tokens import EMPTY_DATE, KEY_COLUMNS


def stack_relatives(raw, keys, schema):
    """Put the columns of every relative under one another: one row per patient and relative.

    For each relative and column, the first cell of the patient that is not
    empty is read, in visit order. Returns the rows as a table of text (like
    an extraction, with one row per relative), their key columns, and the
    flags of the cells that a later visit writes differently.
    """
    endings = {column for variable in schema["variables"].values() for column in variable["columns"]}
    endings = sorted(endings - given_columns(schema))
    used = [prefix + "_" + ending for prefix in schema["relatives"] for ending in endings]
    text = raw[used].where((raw[used] != "") & (raw[used] != EMPTY_DATE))
    in_order = text.assign(usubjid=keys["usubjid"], order=keys["visit_order"]).sort_values("order")
    per_patient = in_order.drop(columns="order").groupby("usubjid")
    first, n_texts = per_patient.first(), per_patient.nunique()

    rows, varies, orders = [], [], []
    for order, (prefix, who) in enumerate(schema["relatives"].items(), start=1):
        columns = [prefix + "_" + ending for ending in endings]
        described = first[columns].notna().any(axis=1)
        one = first.loc[described, columns].fillna("").set_axis(endings, axis=1)
        for name, value in who.items():              # who the relative is: columns that variables can read
            one[name] = value
        rows.append(one.reset_index())
        varies.append(n_texts.loc[described, columns].set_axis(endings, axis=1) > 1)
        orders = orders + [order] * len(one)
    rows = pd.concat(rows, ignore_index=True)
    varies = pd.concat(varies, ignore_index=True)

    row_keys = keys.loc[first_rows(keys).loc[rows["usubjid"]], KEY_COLUMNS].reset_index(drop=True)
    row_keys["visit"] = rows["relative"]             # the flag log names the relative where it names the visit
    row_keys["visit_order"] = orders
    row_keys["visit_month"] = np.nan
    flags = []
    for name, variable in schema["variables"].items():
        for column in variable["columns"]:
            if column in endings:
                flags.append(make_flags(varies[column], name, "patient_value_varies"))
    return rows, row_keys, stack_flags(flags)


def summarise_relatives(table, patients, block):
    """Yes/no columns of the patients table: does a relative of some groups have something?

    table: the rows of the relatives. A group of relatives says yes when one
    of its rows fits; no when its count is known and that many rows have a
    value; nothing otherwise. The column is 1 when a group says yes, 0 when
    every group says no, and missing otherwise.
    """
    not_loaded = [name for name in block["counts"].values() if name not in patients.columns]
    if not_loaded:
        raise ValueError(f"per_patient needs {not_loaded}: load the instrument that gives them too")
    counts = patients.set_index("usubjid")
    summary = pd.DataFrame(index=counts.index)
    for name, column in block["columns"].items():
        fits = pd.Series(True, index=table.index)
        known = pd.Series(True, index=table.index)
        for variable, wanted in column["where"].items():
            fits = fits & table[variable].isin(wanted)
            known = known & table[variable].notna()
        any_yes = pd.Series(False, index=counts.index)
        all_no = pd.Series(True, index=counts.index)
        for group in column["among"]:
            of_group = table.loc[table[block["by"]] == group, "usubjid"]
            n_fit = fits[of_group.index].groupby(of_group).sum().reindex(counts.index, fill_value=0)
            n_known = known[of_group.index].groupby(of_group).sum().reindex(counts.index, fill_value=0)
            any_yes = any_yes | (n_fit > 0)
            all_no = all_no & (n_known >= counts[block["counts"][group]])      # False where the count is unknown
        summary[name] = np.where(any_yes, 1.0, np.where(all_no, 0.0, np.nan))
    return summary.reset_index()
