"""Read instrument schemas (YAML files) and check them.

The rules are in docs/SCHEMA_SPEC.md. A schema is a plain dict.
"""

from pathlib import Path

import pandas as pd
import yaml

from facedata import custom
from facedata.tokens import KEY_COLUMNS

INSTRUMENT_FIELDS = {"instrument", "title", "tab", "section", "status", "level", "notes",
                     "defaults", "version", "variables", "scores", "sign", "checks"}
REQUIRED_FIELDS = ["instrument", "title", "tab", "section", "status", "variables"]
VARIABLE_FIELDS = {"column", "label", "type", "range", "codes", "missing", "unit", "unit_column",
                   "units", "ignore_units", "unit_rule", "censor_units", "censored", "bands", "limits",
                   "shared", "z_range", "lookup", "from", "versions", "winsor", "keep", "derived_from",
                   "doubt", "asked_if", "parse", "note"}
SCORE_FIELDS = {"sum", "mean", "lookup", "from", "by", "custom", "minus", "floor", "reverse", "min_items",
                "versions", "compare", "compare_offset", "compare_tolerance", "winsor", "label",
                "range", "keep"}
VERSION_FIELDS = {"name", "column", "codes", "filled", "level", "follow_up", "by_inclusion_date"}
TYPES = {"number", "item", "band", "category", "date", "time", "text"}


def to_number(text):
    """Text to a number. Text that is not a number is returned unchanged."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return text


def to_numbers(texts):
    return [to_number(text) for text in texts]


def to_dates(texts):
    """Texts written YYYY-MM-DD to dates. A text that is not a date is returned unchanged."""
    dates = []
    for text in texts:
        try:
            dates.append(pd.Timestamp(text))
        except (TypeError, ValueError):
            dates.append(text)
    return dates


def load_schema(path):
    """Read one schema file and prepare it for the pipeline."""
    with open(path, encoding="utf-8") as file:
        schema = yaml.load(file, Loader=yaml.BaseLoader)   # every value arrives as text
    defaults = schema.get("defaults") or {}
    for name, variable in schema["variables"].items():
        variable = {**defaults, **(variable or {})}
        variable.setdefault("column", name)
        # A variable may list several raw columns; "columns" is always a list.
        variable["columns"] = variable["column"] if isinstance(variable["column"], list) else [variable["column"]]
        if "unit_column" in variable:                # the unit label can also sit in several columns
            unit_column = variable["unit_column"]
            variable["unit_columns"] = unit_column if isinstance(unit_column, list) else [unit_column]
        variable["keep"] = variable.get("keep") != "false"
        if "shared" in variable:
            variable["shared"] = variable["shared"] == "true"
        if "limits" in variable:
            variable["limits"] = to_numbers(variable["limits"])
        if "z_range" in variable:
            variable["z_range"] = to_numbers(variable["z_range"])
        if "range" in variable and variable.get("type") == "date":
            variable["range"] = to_dates(variable["range"])
        elif "range" in variable:
            variable["range"] = to_numbers(variable["range"])
        for unit in variable.get("units", {}).values():
            unit["factor"] = to_number(unit.get("factor"))
            unit["expect"] = to_numbers(unit.get("expect", []))
        if isinstance(variable.get("doubt"), dict):  # a period of dates, and the values that are doubted
            doubt = dict(variable["doubt"])
            doubt["period"] = to_dates(doubt.get("period", []))
            if "values" in doubt:
                doubt["values"] = to_numbers(doubt["values"])
            variable["doubt"] = doubt
        if "ignore_units" in variable:               # unit labels are compared in lower case
            variable["ignore_units"] = [label.lower() for label in variable["ignore_units"]]
        winsor = variable.get("winsor")
        if winsor == "false":
            variable["winsor"] = False
        elif isinstance(winsor, list):
            variable["winsor"] = to_numbers(winsor)
        elif isinstance(winsor, dict):
            variable["winsor"] = {"limits": to_numbers(winsor.get("limits", []))}
        schema["variables"][name] = variable
    for score in schema.get("scores", {}).values():
        score["keep"] = score.get("keep") != "false"
        score["compare_offset"] = to_number(score.get("compare_offset", "0"))
        for field in ["min_items", "floor", "compare_tolerance"]:
            if field in score:
                score[field] = to_number(score[field])
        if isinstance(score.get("winsor"), list):
            score["winsor"] = to_numbers(score["winsor"])
        if "range" in score:
            score["range"] = to_numbers(score["range"])
    return schema


def load_schemas(folder):
    """Read every schema of a cohort: {instrument name: schema}."""
    schemas = {}
    for path in sorted(Path(folder).glob("*/*.yaml")):
        schema = load_schema(path)
        schema["file"] = path.stem
        schemas[schema.get("instrument", path.stem)] = schema
    return schemas


def is_range(value):
    """True for [low, high] with two numbers (or two dates) and low <= high."""
    if not isinstance(value, list) or len(value) != 2:
        return False
    if not all(isinstance(limit, (float, pd.Timestamp)) for limit in value):
        return False
    return type(value[0]) == type(value[1]) and value[0] <= value[1]


def version_names(schema):
    """The edition names that the schema's version block can give."""
    version = schema.get("version", {})
    return set(version.get("codes", {}).values()) | set(version.get("filled", {}))


def check_variable(name, variable, schema, columns):
    """Problems of one variable, as a list of sentences."""
    problems = []
    for field in variable:
        if field not in VARIABLE_FIELDS and field not in ("columns", "unit_columns"):
            problems.append(f"{name}: unknown field '{field}'")
    kind = variable.get("type")
    if kind not in TYPES:
        problems.append(f"{name}: type must be one of {sorted(TYPES)}")
    if kind == "item" and "range" not in variable:
        problems.append(f"{name}: an item needs a range")
    if kind == "category" and "codes" not in variable:
        problems.append(f"{name}: a category needs codes")
    limits = variable.get("limits", [])
    if kind == "band" and (limits == [] or not all(isinstance(limit, float) for limit in limits)
                           or limits != sorted(set(limits))):
        problems.append(f"{name}: a band needs limits, numbers in rising order")
    if "lookup" in variable or "from" in variable:
        names = list(schema["variables"])
        source = schema["variables"].get(variable.get("from"), {})
        listed_before = variable.get("from") in names[:names.index(name)]
        if kind != "band" or "lookup" not in variable or not listed_before or "range" not in source:
            problems.append(f"{name}: lookup and from go together, on a band; from names a variable with a range, listed before")
    if "z_range" in variable and (kind != "band" or not is_range(variable["z_range"])):
        problems.append(f"{name}: z_range must be [low, high], on a band")
    if variable.get("shared") and kind not in ("band", "number"):
        problems.append(f"{name}: only a band and a number can share a column")
    if "bands" in variable and (variable["bands"] != "middle" or kind != "number"):
        problems.append(f"{name}: bands can only be 'middle', on a number")
    if "range" in variable and not is_range(variable["range"]):
        problems.append(f"{name}: range must be [low, high]")
    if "units" in variable:
        target = variable["units"].get(variable.get("unit"), {})
        if target.get("factor") != 1.0:
            problems.append(f"{name}: the target unit must be listed in units with factor 1")
        names = list(schema["variables"])
        earlier = names[:names.index(name)]          # the variables listed before this one
        for unit_name, unit in variable["units"].items():
            if not is_range(unit["expect"]):
                problems.append(f"{name}: unit {unit_name} needs an expect range")
            if "percent_of" in unit:
                whole = schema["variables"].get(unit["percent_of"], {})
                if unit["percent_of"] not in earlier or whole.get("type") != "number" or "range" not in whole:
                    problems.append(f"{name}: percent_of must name a number with a range, listed before {name}")
            elif not isinstance(unit["factor"], float):
                problems.append(f"{name}: unit {unit_name} needs a factor or percent_of")
    if "asked_if" in variable:
        names = list(schema["variables"])
        gate = schema["variables"].get(variable["asked_if"], {})
        gate_is_yes_no = gate.get("type") == "item" and gate.get("range") == [0.0, 1.0]
        takes_zero = kind in ("item", "number") and variable.get("range", [None])[0] == 0.0
        if variable["asked_if"] not in names[:names.index(name)] or not gate_is_yes_no or not takes_zero:
            problems.append(f"{name}: asked_if must name a yes/no item listed before, on an item or a number whose range starts at 0")
    if "doubt" in variable:
        doubt = variable["doubt"]
        is_block = isinstance(doubt, dict) and set(doubt) <= {"period", "values", "note"}
        if not is_block or not is_range(doubt.get("period")) or not isinstance(doubt["period"][0], pd.Timestamp):
            problems.append(f"{name}: doubt needs a period [first day, last day], and may have values and a note")
    if "unit_rule" in variable and not hasattr(custom, variable["unit_rule"]):
        problems.append(f"{name}: there is no function '{variable['unit_rule']}' in facedata/custom.py")
    winsor = variable.get("winsor")
    limits = winsor["limits"] if isinstance(winsor, dict) else winsor
    if winsor not in (None, False) and not is_range(limits):
        problems.append(f"{name}: winsor must be [q_low, q_high], {{limits: [a, b]}} or false")
    for version in variable.get("versions", []):
        if version not in version_names(schema):
            problems.append(f"{name}: version '{version}' is not in the version block")
    if "derived_from" in variable:
        score = schema.get("scores", {}).get(variable["derived_from"], {})
        if "compare" not in score:
            problems.append(f"{name}: derived_from must name a score that has compare")
    if columns is not None:
        for column in variable["columns"] + variable.get("unit_columns", []):
            if column not in columns:
                problems.append(f"{name}: column '{column}' is not in the extraction")
    return problems


def check_scores(schema):
    problems = []
    known = set(schema["variables"])
    for name, score in schema.get("scores", {}).items():
        for field in score:
            if field not in SCORE_FIELDS:
                problems.append(f"{name}: unknown field '{field}'")
        if len([kind for kind in ["sum", "mean", "lookup", "custom"] if kind in score]) != 1:
            problems.append(f"{name}: a score has exactly one of sum, mean, lookup and custom")
        if "custom" in score and not hasattr(custom, score["custom"]):
            problems.append(f"{name}: there is no function '{score['custom']}' in facedata/custom.py")
        if "winsor" in score and not is_range(score["winsor"]):
            problems.append(f"{name}: winsor on a score must be [q_low, q_high]")
        if ("lookup" in score) != ("from" in score):
            problems.append(f"{name}: lookup needs from, the raw score to look up")
        if "minus" in score and "sum" not in score:
            problems.append(f"{name}: minus goes with sum")
        if "by" in score and "lookup" not in score:
            problems.append(f"{name}: by goes with lookup")
        used = score.get("sum", []) + score.get("mean", []) + score.get("reverse", []) + score.get("minus", [])
        for field in ["compare", "from", "by"]:
            if field in score:
                used = used + [score[field]]
        for item in used:
            if item not in known:
                problems.append(f"{name}: '{item}' is not a variable or an earlier score")
        for item in score.get("reverse", []):
            if "range" not in schema["variables"].get(item, {}):
                problems.append(f"{name}: reversed item '{item}' needs a range")
        if not isinstance(score["compare_offset"], float):
            problems.append(f"{name}: compare_offset must be a number")
        known.add(name)
    return problems


def check_version(schema, columns):
    problems = []
    version = schema.get("version")
    if version is None:
        return problems
    for field in version:
        if field not in VERSION_FIELDS:
            problems.append(f"version: unknown field '{field}'")
    if "name" not in version or ("column" in version) == ("filled" in version):
        problems.append("version: needs a name, and either column with codes or filled")
    if "column" in version and "codes" not in version:
        problems.append("version: column needs codes")
    if version.get("level", "patient") != "patient" or ("level" in version and "column" not in version):
        problems.append("version: level can only be patient, with a column")
    names = list(version.get("follow_up", {})) + list(version.get("by_inclusion_date", {}))
    if names and "level" not in version:
        problems.append("version: follow_up and by_inclusion_date need level: patient")
    for name in names:
        if name not in version_names(schema):
            problems.append(f"version: '{name}' is not listed in codes")
    if columns is not None:
        used = [version["column"]] if "column" in version else []
        for group in version.get("filled", {}).values():
            used = used + group
        for column in used:
            if column not in columns:
                problems.append(f"version: column '{column}' is not in the extraction")
    return problems


def check_sign(schema):
    problems = []
    sign = schema.get("sign")
    if sign is None:
        return problems
    if set(sign) != {"relation", "by", "pairs"}:
        problems.append("sign: needs relation, by and pairs, and nothing else")
        return problems
    if sign["relation"] not in ("negative", "positive"):
        problems.append("sign: relation is negative or positive")
    if sign["by"] not in KEY_COLUMNS:
        problems.append("sign: by must be a key column")
    for score, raw_names in sign["pairs"].items():
        if schema["variables"].get(score, {}).get("type") != "number":
            problems.append(f"sign: '{score}' must be a variable of type number")
        raw_names = [raw_names] if isinstance(raw_names, str) else raw_names
        for name in raw_names:
            if name not in schema["variables"]:
                problems.append(f"sign: '{name}' is not a variable")
    return problems


def check_schema(schema, columns=None):
    """Problems found in one schema. An empty list means the schema is correct.

    columns: the column names of the extraction. Without them, the test that
    every raw column exists is left out.
    """
    problems = []
    for field in schema:
        if field not in INSTRUMENT_FIELDS and field != "file":
            problems.append(f"unknown field '{field}'")
    for field in REQUIRED_FIELDS:
        if field not in schema:
            problems.append(f"missing field '{field}'")
    if schema.get("instrument") != schema.get("file", schema.get("instrument")):
        problems.append("the instrument name must be the file name")
    if schema.get("status") not in ("draft", "reviewed"):
        problems.append("status is draft or reviewed")
    if schema.get("level", "visit") not in ("visit", "patient"):
        problems.append("level is visit or patient")
    for name, variable in schema.get("variables", {}).items():
        problems = problems + check_variable(name, variable, schema, columns)
    problems = problems + check_scores(schema) + check_version(schema, columns) + check_sign(schema)
    outputs = set(schema.get("variables", {})) | set(schema.get("scores", {}))
    for name, function in (schema.get("checks") or {}).items():
        if name not in outputs:
            problems.append(f"checks: '{name}' is not a variable or a score")
        if not hasattr(custom, function):
            problems.append(f"checks: there is no function '{function}' in facedata/custom.py")
    return [f"{schema.get('instrument')}: {problem}" for problem in problems]


def check_cohort(schemas):
    """Problems that only show when the schemas of a cohort are put side by side."""
    problems = []
    seen_outputs = {}
    seen_versions = {}
    readers = {}                 # raw column -> list of (edition, variable, is it delivered)
    sharing = {}                 # raw column -> types of the variables that share it
    for instrument, schema in schemas.items():
        for name in list(schema["variables"]) + list(schema.get("scores", {})):
            if name in seen_outputs:
                problems.append(f"output '{name}' is in {seen_outputs[name]} and in {instrument}")
            seen_outputs[name] = instrument
        if "version" in schema:
            block = schema["version"]
            first = seen_versions.setdefault(block.get("name"), block)
            if block != first:
                problems.append(f"{instrument}: version block '{block.get('name')}' differs from another schema's")
        for name, variable in schema["variables"].items():
            for edition in variable.get("versions", ["every visit"]):
                for column in variable["columns"]:
                    if variable.get("shared"):           # a band and a number may read the same column
                        sharing.setdefault(column, []).append(variable["type"])
                    else:
                        readers.setdefault(column, []).append((edition, name, variable["keep"]))
    for column, types in sharing.items():
        if sorted(types) != ["band", "number"] or column in readers:
            problems.append(f"raw column '{column}' must be shared by one band and one number, and by nothing else")
    for column, uses in readers.items():
        delivered = [use for use in uses if use[2]]
        if delivered:                                    # a variable that is not delivered may read a delivered column
            uses = delivered
        editions = [edition for edition, name, keep in uses]
        if len(editions) != len(set(editions)) or ("every visit" in editions and len(editions) > 1):
            names = [name for edition, name, keep in uses]
            problems.append(f"raw column '{column}' feeds several variables on the same visits: {names}")
    return problems
