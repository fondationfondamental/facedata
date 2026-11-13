"""Quality control: one line of figures per variable, and schema coverage."""

import numpy as np
import pandas as pd

from facedata.harmonise import detect_version
from facedata.schema import raw_columns
from facedata.tokens import EMPTY_DATE, SEVERITY


def largest_shift(values, groups):
    """Largest distance between a group's median and the overall median.

    Measured in units of the overall interquartile range. Groups with fewer
    than 20 values are left out. A large result points to a hidden unit
    mixture, a version change or a site habit.
    """
    spread = values.quantile(0.75) - values.quantile(0.25)
    if not spread > 0:
        return np.nan
    medians = values.groupby(groups).median()
    sizes = values.groupby(groups).count()
    medians = medians[sizes >= 20]
    if len(medians) == 0:
        return np.nan
    return ((medians - values.median()).abs() / spread).max()


def qc_row(name, spec, values, cens, keys, flag_counts):
    """The QC figures of one variable, as a dict. `values` is the final column."""
    row = {"variable": name, "label": spec.get("label", ""), "column": ", ".join(spec.get("columns", [])),
           "type": spec.get("type", "score"), "unit": spec.get("unit", "")}
    valid = values.notna()
    row["n_valid"] = int(valid.sum())
    row["n_missing_code"] = int(flag_counts.get("missing_code", 0))
    for severity in ["info", "discrepancy", "danger"]:
        codes = [flag for flag in flag_counts.index if SEVERITY[flag] == severity]
        row["n_" + severity] = int(flag_counts[codes].sum())
    for flag in SEVERITY:
        row[flag] = int(flag_counts.get(flag, 0))
    row["n_cens_left"] = int((valid & (cens == -1)).sum())
    row["n_cens_right"] = int((valid & (cens == 1)).sum())
    row["n_limits"] = int(values[valid & (cens != 0)].nunique())
    row["n_distinct"] = int(values.nunique())
    years = keys["visit_date"].dt.year[valid]
    row["first_year"], row["last_year"] = years.min(), years.max()
    row["n_sites"] = int(keys["siteid"][valid].nunique())
    if row["type"] in ("number", "item", "band", "time", "score") and valid.any():
        numbers = values.astype(float)
        row["min"], row["max"] = numbers.min(), numbers.max()
        for label, share in [("p01", 0.01), ("p25", 0.25), ("median", 0.5), ("p75", 0.75), ("p99", 0.99)]:
            row[label] = numbers.quantile(share)
        row["site_shift"] = largest_shift(numbers, keys["siteid"])
        row["year_shift"] = largest_shift(numbers, keys["visit_date"].dt.year)
    return row


def qc_table(schema, result, keys):
    """One QC line per delivered variable and score of an instrument.

    result is what run_instrument() returns.
    """
    counts = result["flags"].groupby(["variable", "flag"]).size()
    no_flags = pd.Series(dtype=int)
    specs = {**schema["variables"], **schema.get("scores", {})}
    rows = []
    for name, spec in specs.items():
        if not spec["keep"]:
            continue
        flag_counts = counts[name] if name in counts.index.get_level_values(0) else no_flags
        cens = result["cens"].get(name, pd.Series(0, index=keys.index))
        row = qc_row(name, spec, result["values"][name], cens, keys, flag_counts)
        row["instrument"] = schema["instrument"]
        row["tab"] = schema["tab"]
        row["level"] = schema.get("level", "visit")
        first_item = (spec.get("sum") or spec.get("mean") or [name])[0]     # a score is read where its items are
        row["n_rows"] = int(result["n_rows"].get(first_item, len(keys)))
        row["n_filled"] = int(result["n_filled"].get(name, row["n_valid"]))
        row["pct_valid"] = round(100 * row["n_valid"] / row["n_filled"], 1) if row["n_filled"] else np.nan
        low, high = result["limits"].get(name, (np.nan, np.nan))
        row["winsor_low"], row["winsor_high"] = low, high
        row["n_winsorised"] = row["winsorised"]
        rows.append(row)
    first = ["variable", "instrument", "tab", "label", "column", "type", "unit", "level",
             "n_rows", "n_filled", "n_valid", "pct_valid", "n_missing_code"]
    table = pd.DataFrame(rows)
    return table[first + [column for column in table.columns if column not in first]]


def coverage(raw, keys, schemas, thesaurus_names, ignored):
    """Which columns have a schema yet. One line per column name.

    status: covered, ignored, not_assigned (in the extraction, no schema yet),
    missing_in_extraction (a schema or the list of ignored columns names it),
    thesaurus_only. n_unread counts the cells that hold a value on a visit
    where no schema reads the column (another edition's visit).
    """
    always = pd.Series(True, index=raw.index)
    read_on = {}                          # column -> True/False per row: something reads it there
    for column in ["usubjid", "visit", "id_visit", "visitnum", "svdtc", "siteid"]:
        read_on[column] = always          # the key columns, read for every instrument
    for schema in schemas.values():
        version = None
        if "version" in schema:
            version, version_flags = detect_version(raw, keys, schema)
            block = schema["version"]
            for column in [block["column"]] if "column" in block else []:
                read_on[column] = always
        for variable in schema["variables"].values():
            rows = version.isin(variable["versions"]) if "versions" in variable else always
            for column in raw_columns(schema, variable):
                read_on[column] = read_on.get(column, ~always) | rows
            for column in variable.get("unit_columns", []):
                read_on[column] = always
    names = sorted(set(raw.columns) | set(read_on) | set(thesaurus_names) | set(ignored))
    lines = []
    for name in names:
        in_extraction = name in raw.columns
        line = {"column": name, "in_thesaurus": name in thesaurus_names, "n_filled": 0, "n_unread": 0}
        if in_extraction:
            filled = (raw[name] != "") & (raw[name] != EMPTY_DATE)
            line["n_filled"] = int(filled.sum())
        if name in read_on and in_extraction:
            line["status"] = "covered"
            line["n_unread"] = int((filled & ~read_on[name]).sum())
        elif name in ignored and in_extraction:
            line["status"] = "ignored"
        elif in_extraction:
            line["status"] = "not_assigned"
        elif name in read_on or name in ignored:
            line["status"] = "missing_in_extraction"
        else:
            line["status"] = "thesaurus_only"
        lines.append(line)
    return pd.DataFrame(lines)[["column", "status", "in_thesaurus", "n_filled", "n_unread"]]
