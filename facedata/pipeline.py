"""The pipeline: the steps of docs/ARCHITECTURE.md (section 5), in order."""

from collections import namedtuple

import pandas as pd

from facedata import custom
from facedata.flags import finish_flags, make_flags, stack_flags
from facedata.harmonise import (censoring_from_units, check_range, collapse_patient_level,
                                compute_scores, convert_units, detect_version, fix_sign, winsorise)
from facedata.parse import clean_text, parse_column, split_missing
from facedata.qc import qc_table
from facedata.read import prepare_visits, read_extraction
from facedata.schema import check_cohort, check_schema, load_schemas
from facedata.tokens import EMPTY_DATE, KEY_COLUMNS

Result = namedtuple("Result", ["data", "patients", "flags", "qc"])


def read_variable(raw, version, name, variable):
    """Steps 3, 5, 6 and 7 for one variable: from the raw column to clean values.

    Returns the values, the censoring, the flags, and how many cells were
    read and how many of them were filled.
    """
    text = clean_text(raw[variable["column"]])
    n_rows = len(text)
    if "versions" in variable:
        of_edition = version.isin(variable["versions"])
        text = text.where(of_edition, "")            # read only on the visits of its edition
        n_rows = int(of_edition.sum())
    n_filled = int(((text != "") & (text != EMPTY_DATE)).sum())
    text, missing_flags = split_missing(text, name, variable)
    if "parse" in variable:                          # escape hatch: a function of custom.py
        values = getattr(custom, variable["parse"])(text)
        cens, parse_flags = pd.Series(0, index=text.index), stack_flags([])
    else:
        values, cens, parse_flags = parse_column(text, name, variable)
    flags = [missing_flags, parse_flags]
    labels = pd.Series("", index=text.index)
    if "unit_column" in variable:
        labels = clean_text(raw[variable["unit_column"]]).where(values.notna(), "")
        cens, censor_flags = censoring_from_units(cens, labels, name, variable)
        flags.append(censor_flags)
    if "units" in variable:
        values, unit_flags = convert_units(values, labels, name, variable)
        flags.append(unit_flags)
    if variable.get("censored") == "half":
        values = values.where(cens != -1, values / 2)
    return values, cens, stack_flags(flags), n_rows, n_filled


def run_instrument(raw, keys, schema, limits=None):
    """Run every step for one instrument.

    Returns a dict: values (one column per variable and score), cens, version,
    flags, limits (winsor limits used), n_rows, n_filled and switch (the
    dates at which centres changed sign convention).
    """
    limits = limits or {}
    flags = []
    version = None
    if "version" in schema:
        version, version_flags = detect_version(raw, keys, schema)
        flags.append(version_flags)

    values = pd.DataFrame(index=raw.index)
    cens = pd.DataFrame(index=raw.index)
    n_rows, n_filled = {}, {}
    for name, variable in schema["variables"].items():
        values[name], cens[name], variable_flags, n_rows[name], n_filled[name] = read_variable(
            raw, version, name, variable)
        flags.append(variable_flags)

    switch = {}
    if "sign" in schema:
        values, sign_flags, switch = fix_sign(values, keys, schema)
        flags.append(sign_flags)

    for name, variable in schema["variables"].items():
        if "range" in variable and variable["type"] in ("number", "item"):
            values[name], range_flags = check_range(values[name], name, variable)
            flags.append(range_flags)
    cens = cens.where(values[cens.columns].notna(), 0)

    values, score_flags = compute_scores(values, schema, version)
    flags.append(score_flags)

    for check in schema.get("checks", []):           # custom checks: True where the row fails
        failed = getattr(custom, check)(values)
        flags.append(make_flags(failed, schema["instrument"], "check_failed", check))

    used_limits = {}
    for name, variable in schema["variables"].items():
        if variable["type"] == "number":
            values[name], winsor_flags, used_limits[name] = winsorise(
                values[name], name, variable, limits.get(name))
            flags.append(winsor_flags)

    return {"values": values, "cens": cens, "version": version, "flags": stack_flags(flags),
            "limits": used_limits, "n_rows": n_rows, "n_filled": n_filled, "switch": switch}


def delivered_columns(schema, result):
    """The output columns of an instrument: kept variables, scores, censoring and version."""
    specs = {**schema["variables"], **schema.get("scores", {})}
    table = pd.DataFrame(index=result["values"].index)
    for name, spec in specs.items():
        if not spec["keep"]:
            continue
        table[name] = result["values"][name]
        if name in result["cens"].columns and (result["cens"][name] != 0).any():
            table[name + "_cens"] = result["cens"][name]
    if result["version"] is not None:
        table[schema["version"]["name"]] = result["version"]
    return table


def raw_strings(raw, schema):
    """The original text of each variable, untouched, for the flag log."""
    table = pd.DataFrame(index=raw.index)
    for name, variable in schema["variables"].items():
        table[name] = raw[variable["column"]]
    if "column" in schema.get("version", {}):
        table[schema["version"]["name"]] = raw[schema["version"]["column"]]
    return table


def read_limits(qc):
    """Winsor limits of an earlier load: {variable: (low, high)}."""
    if qc is None:
        return {}
    with_limits = qc.dropna(subset=["winsor_low", "winsor_high"])
    return {row["variable"]: (row["winsor_low"], row["winsor_high"]) for index, row in with_limits.iterrows()}


def run_cohort(path, schema_folder, instruments=None, winsor_limits=None):
    """Load an extraction with every schema of the folder (or only some instruments)."""
    raw, keys, visit_flags = prepare_visits(read_extraction(path))
    schemas = load_schemas(schema_folder)
    problems = check_cohort(schemas)
    for schema in schemas.values():
        problems = problems + check_schema(schema, set(raw.columns))
    if problems:
        raise ValueError("The schemas have problems:\n" + "\n".join(problems))
    if instruments is not None:
        unknown = [name for name in instruments if name not in schemas]
        if unknown:
            raise ValueError(f"No schema for {unknown}. Known instruments: {sorted(schemas)}")
        schemas = {name: schemas[name] for name in instruments}
    limits = read_limits(winsor_limits)

    data = keys[KEY_COLUMNS].copy()
    patients = pd.DataFrame({"usubjid": sorted(keys["usubjid"].unique())})
    visit_text = pd.DataFrame({"visit_date": raw["svdtc"]})
    all_flags = [finish_flags(visit_flags, keys, visit_text, keys)]
    all_qc = []
    for schema in schemas.values():
        result = run_instrument(raw, keys, schema, limits)
        table = delivered_columns(schema, result)
        table = table[[column for column in table.columns if column not in data.columns]]
        if schema.get("level") == "patient":
            table, patient_flags = collapse_patient_level(table, keys)
            patients = patients.merge(table, on="usubjid", how="left")
            result["flags"] = stack_flags([result["flags"], patient_flags])
        else:
            data = pd.concat([data, table], axis=1)
        final = result["values"].copy()
        if result["version"] is not None:
            final[schema["version"]["name"]] = result["version"]
        all_flags.append(finish_flags(result["flags"], keys, raw_strings(raw, schema), final))
        all_qc.append(qc_table(schema, result, keys))
    flags = pd.concat(all_flags, ignore_index=True)
    flags = flags.drop_duplicates(subset=["usubjid", "visit", "variable", "flag"]).reset_index(drop=True)
    return Result(data, patients, flags, pd.concat(all_qc, ignore_index=True))
