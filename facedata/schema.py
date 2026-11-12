"""Read instrument schemas (YAML files) and check them.

The rules are in docs/SCHEMA_SPEC.md. A schema is a plain dict.
"""

from pathlib import Path

import yaml

from facedata.tokens import KEY_COLUMNS

INSTRUMENT_FIELDS = {"instrument", "title", "tab", "section", "status", "level", "notes",
                     "defaults", "version", "variables", "scores", "sign", "checks"}
REQUIRED_FIELDS = ["instrument", "title", "tab", "section", "status", "variables"]
VARIABLE_FIELDS = {"column", "label", "type", "range", "codes", "missing", "unit", "unit_column",
                   "units", "censor_units", "censored", "versions", "winsor", "keep",
                   "derived_from", "parse", "note"}
SCORE_FIELDS = {"sum", "mean", "reverse", "min_items", "versions", "compare", "compare_offset",
                "label", "range", "keep"}
VERSION_FIELDS = {"name", "column", "codes", "filled", "level", "follow_up", "by_inclusion_date"}
TYPES = {"number", "item", "category", "date", "time", "text"}


def to_number(text):
    """Text to a number. Text that is not a number is returned unchanged."""
    try:
        return float(text)
    except (TypeError, ValueError):
        return text


def to_numbers(texts):
    return [to_number(text) for text in texts]


def load_schema(path):
    """Read one schema file and prepare it for the pipeline."""
    with open(path, encoding="utf-8") as file:
        schema = yaml.load(file, Loader=yaml.BaseLoader)   # every value arrives as text
    defaults = schema.get("defaults") or {}
    for name, variable in schema["variables"].items():
        variable = {**defaults, **(variable or {})}
        variable.setdefault("column", name)
        variable["keep"] = variable.get("keep") != "false"
        if "range" in variable:
            variable["range"] = to_numbers(variable["range"])
        for unit in variable.get("units", {}).values():
            unit["factor"] = to_number(unit.get("factor"))
            unit["expect"] = to_numbers(unit.get("expect", []))
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
        if "min_items" in score:
            score["min_items"] = to_number(score["min_items"])
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
    """True for [low, high] with two numbers and low <= high."""
    if not isinstance(value, list) or len(value) != 2:
        return False
    if not all(isinstance(number, float) for number in value):
        return False
    return value[0] <= value[1]


def version_names(schema):
    """The edition names that the schema's version block can give."""
    version = schema.get("version", {})
    return set(version.get("codes", {}).values()) | set(version.get("filled", {}))


def check_variable(name, variable, schema, columns):
    """Problems of one variable, as a list of sentences."""
    problems = []
    for field in variable:
        if field not in VARIABLE_FIELDS:
            problems.append(f"{name}: unknown field '{field}'")
    kind = variable.get("type")
    if kind not in TYPES:
        problems.append(f"{name}: type must be one of {sorted(TYPES)}")
    if kind == "item" and "range" not in variable:
        problems.append(f"{name}: an item needs a range")
    if kind == "category" and "codes" not in variable:
        problems.append(f"{name}: a category needs codes")
    if "range" in variable and not is_range(variable["range"]):
        problems.append(f"{name}: range must be [low, high]")
    if "units" in variable:
        target = variable["units"].get(variable.get("unit"), {})
        if target.get("factor") != 1.0:
            problems.append(f"{name}: the target unit must be listed in units with factor 1")
        for unit_name, unit in variable["units"].items():
            if not isinstance(unit["factor"], float) or not is_range(unit["expect"]):
                problems.append(f"{name}: unit {unit_name} needs a factor and an expect range")
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
        for field in ["column", "unit_column"]:
            if field in variable and variable[field] not in columns:
                problems.append(f"{name}: column '{variable[field]}' is not in the extraction")
    return problems


def check_scores(schema):
    problems = []
    known = set(schema["variables"])
    for name, score in schema.get("scores", {}).items():
        for field in score:
            if field not in SCORE_FIELDS:
                problems.append(f"{name}: unknown field '{field}'")
        if ("sum" in score) == ("mean" in score):
            problems.append(f"{name}: a score has either sum or mean")
        used = score.get("sum", []) + score.get("mean", []) + score.get("reverse", [])
        if "compare" in score:
            used = used + [score["compare"]]
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
    return [f"{schema.get('instrument')}: {problem}" for problem in problems]


def check_cohort(schemas):
    """Problems that only show when the schemas of a cohort are put side by side."""
    problems = []
    seen_outputs = {}
    seen_versions = {}
    readers = {}                 # raw column -> list of (edition, variable)
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
                readers.setdefault(variable["column"], []).append((edition, name))
    for column, uses in readers.items():
        editions = [edition for edition, name in uses]
        if len(editions) != len(set(editions)) or ("every visit" in editions and len(editions) > 1):
            names = [name for edition, name in uses]
            problems.append(f"raw column '{column}' feeds several variables on the same visits: {names}")
    return problems
