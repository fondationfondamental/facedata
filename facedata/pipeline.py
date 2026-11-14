"""The pipeline: the steps of docs/ARCHITECTURE.md (section 5), in order."""

from collections import namedtuple

import pandas as pd

from facedata import custom
from facedata.flags import finish_flags, make_flags, stack_flags
from facedata.harmonise import (band_from_table, censoring_from_units, check_range, collapse_patient_level,
                                compute_scores, convert_units, detect_version, doubt_period, first_rows,
                                fix_sign, winsorise)
from facedata.parse import clean_text, own_cells, parse_column, split_missing
from facedata.qc import qc_table
from facedata.read import prepare_visits, read_extraction, read_norms
from facedata.relatives import stack_relatives, summarise_relatives
from facedata.schema import check_cohort, check_schema, load_schemas, raw_columns
from facedata.tokens import EMPTY_DATE, KEY_COLUMNS
from facedata.treatments import at_visit, open_lists

Result = namedtuple("Result", ["data", "patients", "flags", "qc", "treatments", "relatives"])


def read_text(raw, version, name, variable):
    """Steps 3 and 5 for one variable: its cleaned text, without missing codes.

    A variable may list several raw columns, when the extraction moved it to
    a new column: the first column that holds a value is read. Returns the
    text, which visits are read, which cells were filled, and the flags.
    """
    is_read = pd.Series(True, index=raw.index)
    if "versions" in variable:
        is_read = version.isin(variable["versions"])     # read only on the visits of its edition
    text = pd.Series("", index=raw.index)
    filled = pd.Series(False, index=raw.index)
    flags = []
    for column in variable["columns"]:
        other = clean_text(raw[column]).where(is_read, "")
        if variable.get("shared"):                       # the column also holds the cells of another variable
            other = own_cells(other, variable)
        filled = filled | ((other != "") & (other != EMPTY_DATE))
        other, missing_flags = split_missing(other, name, variable)
        conflict = (text != "") & (other != "") & (text != other)
        flags.append(missing_flags)
        flags.append(make_flags(conflict, name, "column_conflict", "column " + column + " holds " + other))
        text = text.where(text != "", other)
    return text, is_read, filled, flags


def read_variable(raw, version, name, variable, keys=None, wholes=None, norms=None):
    """Steps 3, 5, 6 and 7 for one variable: from the raw column to clean values.

    keys and wholes (the values read so far, inside their range) are passed on
    to the unit conversion. A band that names a norm table is read there, with
    wholes and norms. Returns the values, the censoring, the flags, which
    visits are read and which cells were filled.
    """
    text, is_read, filled, flags = read_text(raw, version, name, variable)
    if "parse" in variable:                          # escape hatch: a function of custom.py
        values = getattr(custom, variable["parse"])(text)
        cens, parse_flags = pd.Series(0, index=text.index), stack_flags([])
    else:
        values, cens, parse_flags = parse_column(text, name, variable)
    if "lookup" in variable:                         # a band the EMR read in a table: read it again from the raw score
        values, cens, parse_flags = band_from_table(text, values, cens, parse_flags, name, variable,
                                                    keys["age"], wholes, norms)
    flags.append(parse_flags)
    labels = pd.Series("", index=text.index)
    if "unit_column" in variable:
        for column in variable["unit_columns"]:      # the first column that holds a label
            labels = labels.where(labels != "", clean_text(raw[column]))
        labels = labels.where(values.notna(), "")
        cens, censor_flags = censoring_from_units(cens, labels, name, variable)
        flags.append(censor_flags)
        # A censoring mark says nothing about the unit, and neither does a label the schema ignores.
        says_nothing = list(variable.get("censor_units", {})) + variable.get("ignore_units", [])
        labels = labels.where(~labels.str.lower().isin(says_nothing), "")
    if "units" in variable:
        values, unit_flags = convert_units(values, labels, name, variable, keys, wholes)
        flags.append(unit_flags)
    if variable.get("censored") == "half":
        values = values.where(cens != -1, values / 2)
    return values, cens, stack_flags(flags), is_read, filled


def run_instrument(raw, keys, schema, limits=None, norms=None):
    """Run every step for one instrument.

    limits: winsor limits of an earlier load. norms: the norm tables.

    Returns a dict: values (one column per variable and score), cens, version,
    flags, limits (winsor limits used), n_rows (cells read), n_filled (cells
    that held something) and switch (the dates at which centres changed sign
    convention).
    """
    limits = limits or {}
    flags = []
    version = None
    if "version" in schema:
        version, version_flags = detect_version(raw, keys, schema)
        flags.append(version_flags)

    values = pd.DataFrame(index=raw.index)
    cens = pd.DataFrame(index=raw.index)
    wholes = pd.DataFrame(index=raw.index)           # the values inside their range, for a percentage or a norm table
    n_rows, n_filled = {}, {}
    per_patient = schema.get("level") == "patient"
    for name, variable in schema["variables"].items():
        values[name], cens[name], variable_flags, is_read, filled = read_variable(
            raw, version, name, variable, keys, wholes, norms)
        flags.append(variable_flags)
        if "asked_if" in variable:                   # a box shown only after a yes: a "no" there answers it too
            answered = ~filled & (values[variable["asked_if"]] == 0)
            values[name] = values[name].mask(answered, 0)
            filled = filled | answered
        if variable["type"] in ("number", "item") and "range" in variable:
            wholes[name], _ = check_range(values[name], name, variable)
        if per_patient:                              # count patients, not visit rows
            n_rows[name] = keys["usubjid"][is_read].nunique()
            n_filled[name] = keys["usubjid"][filled].nunique()
        else:
            n_rows[name], n_filled[name] = int(is_read.sum()), int(filled.sum())

    switch = {}
    if "sign" in schema:
        values, sign_flags, switch = fix_sign(values, keys, schema)
        flags.append(sign_flags)

    for name, variable in schema["variables"].items():
        if "range" in variable and variable["type"] in ("number", "item", "date"):
            values[name], range_flags = check_range(values[name], name, variable)
            flags.append(range_flags)
        if "doubt" in variable:                      # a period in which the column is not reliable
            flags.append(doubt_period(values[name], keys["visit_date"], name, variable["doubt"]))
    cens = cens.where(values[cens.columns].notna(), 0)

    values, score_flags = compute_scores(values, schema, version, keys["age"], norms, cens)
    flags.append(score_flags)

    for name, check in schema.get("checks", {}).items():     # custom checks: True where the row fails
        failed = getattr(custom, check)(values) & values[name].notna()     # an empty cell is never flagged
        flags.append(make_flags(failed, name, "check_failed", check))

    used_limits = {}
    for name, variable in schema["variables"].items():
        if variable["type"] == "number":
            values[name], winsor_flags, used_limits[name] = winsorise(
                values[name], name, variable, limits.get(name))
            flags.append(winsor_flags)
    for name, score in schema.get("scores", {}).items():
        if "winsor" in score:                        # a continuous score that asks for it (a body mass index)
            values[name], winsor_flags, used_limits[name] = winsorise(values[name], name, score, limits.get(name))
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


def once_per_patient(result, table, keys):
    """For a patient-level instrument: put values and flags on each patient's first visit.

    table is the one-row-per-patient table of the instrument. After this, the
    QC table and the flag log count patients, not visit rows.
    """
    first = first_rows(keys)
    is_first = keys.index.isin(first)
    lookup = table.set_index("usubjid")
    for name in lookup.columns:
        on_first_visit = keys["usubjid"].map(lookup[name]).where(is_first)
        if name in result["values"].columns:
            result["values"][name] = on_first_visit
        elif name.endswith("_cens"):
            result["cens"][name[:-5]] = on_first_visit.fillna(0)
    flags = result["flags"].copy()
    flags["row"] = first.loc[keys["usubjid"].loc[flags["row"]]].to_numpy()
    result["flags"] = flags.drop_duplicates(subset=["row", "variable", "flag"]).reset_index(drop=True)
    return result


def run_list_instrument(raw, keys, schema, schemas, limits=None, norms=None):
    """An instrument whose cells hold lists: one row per patient and item (SCHEMA_SPEC, section 15).

    Returns the table of items, the yes/no columns of the visit table, the
    flags and the QC tables.
    """
    items, item_keys, list_flags = open_lists(raw, keys, schema)
    result = run_instrument(items, item_keys, schema, limits, norms)
    result["flags"] = stack_flags([result["flags"], list_flags])
    front = pd.DataFrame({"usubjid": item_keys["usubjid"], "item": item_keys["visit_order"]})
    table = pd.concat([front, delivered_columns(schema, result)], axis=1)
    flags = finish_flags(result["flags"], item_keys, raw_strings(items, schema), result["values"])
    qc = [qc_table(schema, result, item_keys)]
    visit_columns = pd.DataFrame(index=keys.index)
    if "at_visit" in schema:
        visit_columns = at_visit(result["values"], item_keys, keys, schema["at_visit"])
        qc.append(qc_table(schemas[schema["instrument"] + "_at_visit"], computed(visit_columns), keys))
    return table, visit_columns, flags, qc


def computed(values, n_rows=None):
    """Columns computed from other values, in the shape of what run_instrument() returns."""
    return {"values": values, "cens": pd.DataFrame(index=values.index), "flags": stack_flags([]),
            "limits": {}, "n_rows": n_rows or {}, "n_filled": {}, "version": None}


def run_relatives_instrument(raw, keys, schema, limits=None, norms=None):
    """The same questions asked for each relative: one row per patient and relative (SCHEMA_SPEC, section 16).

    Returns the table of relatives, the flags and the QC table.
    """
    rows, row_keys, varying_flags = stack_relatives(raw, keys, schema)
    result = run_instrument(rows, row_keys, schema, limits, norms)
    result["flags"] = stack_flags([result["flags"], varying_flags])
    flags = finish_flags(result["flags"], row_keys, raw_strings(rows, schema), result["values"])
    asked = [name for name, variable in schema["variables"].items() if raw_columns(schema, variable)]
    described = result["values"][asked].notna().any(axis=1)      # something is known about the relative
    front = pd.DataFrame({"usubjid": row_keys["usubjid"], "relative": row_keys["visit"]})
    table = pd.concat([front, delivered_columns(schema, result)], axis=1)[described].reset_index(drop=True)
    result["values"], result["cens"] = result["values"][described], result["cens"][described]
    return table, flags, qc_table(schema, result, row_keys[described])


def run_per_patient(relatives, patients, keys, schema, computed_schema):
    """The yes/no columns of the patients table that sum up the relatives (SCHEMA_SPEC, section 16).

    Returns the patients table with these columns, and their QC table. For
    the QC table the values sit on the first visit of each patient.
    """
    summary = summarise_relatives(relatives, patients, schema["per_patient"])
    values = keys[["usubjid"]].merge(summary, on="usubjid", how="left").set_index(keys.index).drop(columns="usubjid")
    values.loc[~keys.index.isin(first_rows(keys))] = float("nan")
    n_rows = {name: len(patients) for name in values.columns}
    return patients.merge(summary, on="usubjid", how="left"), qc_table(computed_schema, computed(values, n_rows), keys)


def raw_strings(raw, schema):
    """The original text of each variable, untouched, for the flag log."""
    table = pd.DataFrame(index=raw.index)
    for name, variable in schema["variables"].items():
        text = raw[variable["columns"][0]]
        for column in variable["columns"][1:]:       # the first column that holds something
            text = text.where((text.str.strip() != "") & (text != EMPTY_DATE), raw[column])
        table[name] = text
    if "column" in schema.get("version", {}):
        table[schema["version"]["name"]] = raw[schema["version"]["column"]]
    return table


def read_limits(qc):
    """Winsor limits of an earlier load: {variable: (low, high)}."""
    if qc is None:
        return {}
    with_limits = qc.dropna(subset=["winsor_low", "winsor_high"])
    return {row["variable"]: (row["winsor_low"], row["winsor_high"]) for index, row in with_limits.iterrows()}


def with_cohort(table, cohort):
    """The table with the cohort as its first column, so that the tables of two cohorts can be stacked."""
    table = table.copy()
    table.insert(0, "cohort", cohort)
    return table


def run_cohort(path, schema_folder, instruments=None, winsor_limits=None, norms_folder="norms", cohort=None):
    """Load an extraction with every schema of the folder (or only some instruments).

    cohort: the name written in the column `cohort` of the tables ("bp", "sz"). A usubjid is
    unique inside a cohort only.
    """
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
        schemas = {name: schema for name, schema in schemas.items()
                   if name in instruments or schema.get("derived_from") in instruments}
    limits = read_limits(winsor_limits)
    norms = read_norms(norms_folder)

    data = keys[KEY_COLUMNS].copy()
    patients = pd.DataFrame({"usubjid": sorted(keys["usubjid"].unique())})
    visit_text = pd.DataFrame({"visit_date": raw["svdtc"]})
    all_flags = [finish_flags(visit_flags, keys, visit_text, keys)]
    all_qc = []
    treatments = pd.DataFrame(columns=["usubjid", "item"])
    relatives = pd.DataFrame(columns=["usubjid", "relative"])
    for schema in schemas.values():
        if "derived_from" in schema:                     # computed with the instrument it comes from
            continue
        if schema.get("level") == "relatives":
            relatives, flags, qc = run_relatives_instrument(raw, keys, schema, limits, norms)
            all_flags.append(flags)
            all_qc.append(qc)
            continue
        if schema.get("level") == "list":
            treatments, visit_columns, flags, qc = run_list_instrument(raw, keys, schema, schemas, limits, norms)
            data = pd.concat([data, visit_columns], axis=1)
            all_flags.append(flags)
            all_qc.extend(qc)
            continue
        result = run_instrument(raw, keys, schema, limits, norms)
        table = delivered_columns(schema, result)
        for column in table.columns.intersection(data.columns):     # a version column that another schema also gives
            data[column] = data[column].fillna(table[column])
        table = table[[column for column in table.columns if column not in data.columns]]
        if schema.get("level") == "patient":
            table, patient_flags = collapse_patient_level(table, keys)
            patients = patients.merge(table, on="usubjid", how="left")
            result["flags"] = stack_flags([result["flags"], patient_flags])
            result = once_per_patient(result, table, keys)
        else:
            data = pd.concat([data, table], axis=1)
        final = result["values"].copy()
        if result["version"] is not None:
            final[schema["version"]["name"]] = result["version"]
        all_flags.append(finish_flags(result["flags"], keys, raw_strings(raw, schema), final))
        all_qc.append(qc_table(schema, result, keys))
    for name, schema in schemas.items():                 # the relatives summed up per patient, once patients is whole
        if "per_patient" in schema:
            patients, qc = run_per_patient(relatives, patients, keys, schema, schemas[name + "_per_patient"])
            all_qc.append(qc)
    flags = pd.concat(all_flags, ignore_index=True)
    flags = flags.drop_duplicates(subset=["usubjid", "visit", "variable", "flag"]).reset_index(drop=True)
    data = data.copy()                                   # built column by column: a copy puts it back in one piece
    qc = pd.concat(all_qc, ignore_index=True)
    if cohort is not None:
        data, patients, flags = with_cohort(data, cohort), with_cohort(patients, cohort), with_cohort(flags, cohort)
        treatments, relatives = with_cohort(treatments, cohort), with_cohort(relatives, cohort)
    return Result(data, patients, flags, qc, treatments, relatives)
