"""Cells that hold lists: one row per patient and item (docs/SCHEMA_SPEC.md, section 15)."""

import ast

import numpy as np
import pandas as pd

from facedata import custom
from facedata.flags import make_flags, stack_flags
from facedata.tokens import KEY_COLUMNS


def list_columns(schema):
    """The raw columns of a list instrument: those of its variables, less the columns of the names table."""
    given = schema.get("names", {}).get("gives", [])
    columns = [column for variable in schema["variables"].values() for column in variable["columns"]]
    return sorted(set(columns) - set(given))


def open_lists(raw, keys, schema):
    """Open the list cells of an instrument: one row per patient and item.

    Returns the items as a table of text (like an extraction, with one row per
    item), the key columns of the items, and the flags.
    """
    columns = list_columns(schema)
    has_list = (raw[columns] != "").any(axis=1)
    # Every row of a patient holds the same lists: the first row is read.
    first = keys[has_list].sort_values("visit_order").groupby("usubjid").head(1).index
    whole = raw.loc[has_list, columns].agg("|".join, axis=1)
    n_versions = whole.groupby(keys["usubjid"][has_list]).nunique()
    lists = raw.loc[first, columns].map(lambda cell: ast.literal_eval(cell) if cell else [])
    longest = lists.map(len).max(axis=1)
    lists, longest = lists[longest > 0], longest[longest > 0]
    for column in columns:                           # a list shorter than the others gets empty items
        lists[column] = [cell + [None] * (n - len(cell)) for cell, n in zip(lists[column], longest)]
    opened = lists.explode(columns)
    items = opened.map(lambda value: "" if pd.isna(value) else str(value)).reset_index(drop=True)

    item_keys = keys.loc[opened.index, KEY_COLUMNS].reset_index(drop=True)
    item_keys["visit_order"] = item_keys.groupby("usubjid").cumcount() + 1
    item_keys["visit"] = "item " + item_keys["visit_order"].astype(str)
    item_keys["visit_month"] = np.nan
    varying = item_keys["usubjid"].isin(n_versions.index[n_versions > 1]) & (item_keys["visit_order"] == 1)
    flags = stack_flags([make_flags(varying, name, "patient_value_varies") for name in schema["variables"]])
    if "names" in schema:
        block = schema["names"]
        found = look_up_names(items[block["column"]], block)
        items = pd.concat([items, found], axis=1)
        unknown = (items[block["column"]] != "") & (found[block["gives"][0]] == "")
        name = [name for name, variable in schema["variables"].items() if variable["columns"] == [block["gives"][0]]]
        detail = "name not in the table: " + getattr(custom, block["clean"])(items[block["column"]])
        flags = stack_flags([flags] + [make_flags(unknown, one, "unknown_code", detail) for one in name])
    return items, item_keys, flags


def look_up_names(names, block):
    """The columns of the names table for each name.

    The stem of the name is looked up whole, then by its first two words,
    then by its first word. A name that is not found gets empty cells.
    """
    table = pd.read_csv(block["path"], dtype=str, keep_default_na=False).set_index("name")
    stems = getattr(custom, block["clean"])(names)
    words = stems.str.split()
    found = pd.DataFrame("", index=names.index, columns=block["gives"])
    for candidate in [words.str[:1].str.join(" "), words.str[:2].str.join(" "), stems]:     # the longest match wins
        known = candidate.isin(table.index)
        found[known] = table.loc[candidate[known], block["gives"]].to_numpy()
    return found


def at_visit(values, item_keys, keys, block):
    """Yes/no columns of the visit table: on a treatment on the day of the visit.

    values: the harmonised items. 1 when an item that fits started on or
    before the visit and has not ended; 0 when the patient has items and none
    fits; missing when it cannot be told.
    """
    table = pd.DataFrame(index=keys.index)
    can_tell = keys["usubjid"].isin(item_keys["usubjid"]) & keys["visit_date"].notna()
    visits = keys[["usubjid", "visit_date"]].reset_index(names="row")
    for name, column in block["columns"].items():
        fits = pd.Series(True, index=values.index)
        for variable, value in column["where"].items():
            fits = fits & (values[variable] == value)
        periods = pd.DataFrame({"usubjid": item_keys["usubjid"], "start": values[block["start"]], "end": values[block["end"]]})
        pairs = visits.merge(periods[fits], on="usubjid")              # each visit with each fitting item of the patient
        running = pairs["end"].isna() | (pairs["end"] >= pairs["visit_date"])
        started = pairs["start"] <= pairs["visit_date"]
        on = pd.Series(0.0, index=keys.index)
        on[pairs.loc[running & pairs["start"].isna(), "row"].unique()] = np.nan
        on[pairs.loc[running & started, "row"].unique()] = 1.0
        table[name] = on.where(can_tell)
    return table
