"""Read instrument schemas (YAML files) and check them.

The rules are in docs/SCHEMA_SPEC.md. A schema is a plain dict.
"""

from pathlib import Path

import pandas as pd
import yaml

from facedata import custom
from facedata.tokens import KEY_COLUMNS

INSTRUMENT_FIELDS = {"instrument", "title", "tab", "section", "status", "level", "notes",
                     "defaults", "version", "variables", "scores", "sign", "checks", "names", "at_visit",
                     "relatives", "per_patient", "crossed", "per_visit", "packed", "uses", "implausible_visits", "implausible_pool"}
REQUIRED_FIELDS = ["instrument", "title", "tab", "section", "status", "variables"]
VARIABLE_FIELDS = {"column", "label", "type", "range", "codes", "missing", "unit", "unit_column",
                   "units", "ignore_units", "unit_rule", "censor_units", "censored", "bands", "limits",
                   "shared", "z_range", "lookup", "from", "versions", "winsor", "keep", "derived_from",
                   "doubt", "asked_if", "box_list", "shown_if", "before_visit", "separator", "parse", "note", "day"}
SCORE_FIELDS = {"sum", "mean", "max", "min", "lookup", "profile", "distance", "from", "by", "regression", "with", "band_of", "limits", "custom", "minus", "floor", "scale", "reverse", "min_items",
                "points", "otherwise", "versions", "compare", "compare_offset", "compare_tolerance", "winsor", "label",
                "range", "keep", "age", "stop_at_zero", "compare_turned", "age_date", "age_date_since"}
VERSION_FIELDS = {"name", "column", "codes", "filled", "age", "level", "follow_up", "by_inclusion_date", "since", "override"}
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
        if "day" in variable:
            variable["day"] = to_numbers([variable["day"]])[0]
        if "range" in variable and variable.get("type") == "date":
            variable["range"] = to_dates(variable["range"])
        elif "range" in variable:
            variable["range"] = to_numbers(variable["range"])
        for unit in variable.get("units", {}).values():
            unit["factor"] = to_number(unit.get("factor"))
            unit["offset"] = to_number(unit.get("offset", "0"))
            unit["expect"] = to_numbers(unit.get("expect", []))
        if isinstance(variable.get("doubt"), dict):  # a period of dates, and the values that are doubted
            doubt = dict(variable["doubt"])
            doubt["period"] = to_dates(doubt.get("period", []))
            if "values" in doubt:
                doubt["values"] = to_numbers(doubt["values"])
            doubt["remove"] = doubt.get("remove") == "true"
            variable["doubt"] = doubt
        if isinstance(variable.get("shown_if"), dict):   # {variable: the answers that show the question}
            variable["shown_if"] = {gate: to_numbers(shown if isinstance(shown, list) else [shown])
                                    for gate, shown in variable["shown_if"].items()}
        if "before_visit" in variable:
            variable["before_visit"] = variable["before_visit"] == "true"
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
    if "before" in schema.get("sign", {}):               # a change of direction at a known date
        schema["sign"]["before"] = to_dates([schema["sign"]["before"]])[0]
    for score in schema.get("scores", {}).values():
        score["keep"] = score.get("keep") != "false"
        for field in ["stop_at_zero", "compare_turned"]:
            score[field] = score.get(field) == "true"
        score["compare_offset"] = to_number(score.get("compare_offset", "0"))
        for field in ["min_items", "floor", "compare_tolerance"]:
            if field in score:
                score[field] = to_number(score[field])
        if isinstance(score.get("winsor"), list):
            score["winsor"] = to_numbers(score["winsor"])
        if isinstance(score.get("points"), dict):        # {answer: points}, both numbers
            score["points"] = {to_number(answer): to_number(points) for answer, points in score["points"].items()}
        if isinstance(score.get("scale"), list):
            score["scale"] = to_numbers(score["scale"])
        if isinstance(score.get("limits"), list):        # the bands of a z-score
            score["limits"] = to_numbers(score["limits"])
        if "range" in score:
            score["range"] = to_numbers(score["range"])
    if "per_visit" in schema:                        # a list of the visit, not of the patient
        schema["per_visit"] = schema["per_visit"] == "true"
    if isinstance(schema.get("names"), dict):        # the names table: in the cohort folder, or shared in the package folder
        cohort_folder = Path(path).parents[2]
        table = schema["names"].get("table", "")
        in_cohort = cohort_folder / table
        schema["names"]["path"] = in_cohort if in_cohort.exists() else cohort_folder.parent / table
    block = schema.get("per_patient")
    if isinstance(block, dict) and isinstance(block.get("columns"), dict):
        for column in block["columns"].values():     # where: each variable with the list of values that fit
            if isinstance(column, dict) and isinstance(column.get("where"), dict):
                for variable, wanted in column["where"].items():
                    column["where"][variable] = to_numbers(wanted if isinstance(wanted, list) else [wanted])
    return schema


def computed_schema(schema, field):
    """The yes/no columns computed from the rows of an instrument, described as an instrument of their own.

    field: at_visit (columns of the visit table, from a list) or per_patient
    (columns of the patients table, from the relatives).
    """
    block = schema[field]
    name = schema["instrument"] + "_" + field
    variables = {}
    for column, fields in block.get("columns", {}).items():
        variables[column] = {"label": fields.get("label", ""), "type": "item", "range": [0.0, 1.0], "columns": [], "keep": True}
    computed = {"instrument": name, "file": name, "title": block.get("title", name), "tab": schema["tab"],
                "section": schema["section"], "status": schema["status"], "notes": block.get("notes", ""),
                "variables": variables, "derived_from": schema["instrument"]}
    if field == "per_patient":
        computed["level"] = "patient"
    return computed


def load_schemas(folder):
    """Read every schema of a cohort: {instrument name: schema}."""
    schemas = {}
    for path in sorted(Path(folder).glob("*/*.yaml")):
        schema = load_schema(path)
        schema["file"] = path.stem
        schemas[schema.get("instrument", path.stem)] = schema
        for field in ["at_visit", "per_patient"]:
            if isinstance(schema.get(field), dict):
                derived = computed_schema(schema, field)
                schemas[derived["instrument"]] = derived
    return schemas


def given_columns(schema):
    """The columns that variables read and that are not in the extraction.

    A names table gives columns to the items of a list, and the list of
    relatives gives columns to the rows of each relative.
    """
    given = set()
    if isinstance(schema.get("names"), dict):
        given = given | set(schema["names"].get("gives", []))
    if isinstance(schema.get("relatives"), dict):
        for who in schema["relatives"].values():
            given = given | set(who if isinstance(who, dict) else [])
    if isinstance(schema.get("packed"), dict):       # the fields of the records packed in a cell
        for block in schema["packed"].values():
            given = given | set(block.get("fields", []) if isinstance(block, dict) else [])
    return given


def raw_columns(schema, variable):
    """The columns of the extraction that a variable reads.

    With level: relatives, a column of the schema is an ending, read once
    per relative: "trouble" is mere_trouble, pere_trouble and so on.
    """
    columns = [column for column in variable["columns"] if column not in given_columns(schema)]
    if isinstance(schema.get("relatives"), dict):
        columns = [prefix + "_" + column for prefix in schema["relatives"] for column in columns]
    return columns


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
    return set(version.get("codes", {}).values()) | set(version.get("filled", {})) | set(version.get("age", {}))


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
    if "day" in variable and (kind != "date" or variable["day"] not in range(1, 29)):
        problems.append(f"{name}: day must be a whole number from 1 to 28, on a date")
    if variable.get("shared") and kind not in ("band", "number"):
        problems.append(f"{name}: only a band and a number can share a column")
    if "bands" in variable and (variable["bands"] != "middle" or kind != "number"):
        problems.append(f"{name}: bands can only be 'middle', on a number")
    if "range" in variable and not is_range(variable["range"]):
        problems.append(f"{name}: range must be [low, high]")
    if "units" in variable:
        target = variable["units"].get(variable.get("unit"), {})
        if target.get("factor") != 1.0 or target.get("offset") != 0.0:
            problems.append(f"{name}: the target unit must be listed in units with factor 1 and no offset")
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
            if not isinstance(unit["offset"], float) or ("percent_of" in unit and unit["offset"] != 0.0):
                problems.append(f"{name}: unit {unit_name}: offset must be a number, and not on a percent_of")
    if "asked_if" in variable:
        names = list(schema["variables"])
        gate = schema["variables"].get(variable["asked_if"], {})
        gate_takes_zero = gate.get("type") in ("item", "number") and gate.get("range", [None])[0] == 0.0
        takes_zero = kind in ("item", "number") and variable.get("range", [None])[0] == 0.0
        if variable["asked_if"] not in names[:names.index(name)] or not gate_takes_zero or not takes_zero:
            problems.append(f"{name}: asked_if must name a yes/no item or a count (an item or a number whose range starts at 0) "
                            "listed before, on an item or a number whose range starts at 0")
    if "box_list" in variable:
        boxes = [other for other, spec in schema["variables"].items() if spec.get("box_list") == variable["box_list"]]
        if kind != "item" or variable.get("range") != [0.0, 1.0] or len(boxes) < 2:
            problems.append(f"{name}: box_list goes on a yes/no item, and names a list of two boxes or more")
    if "shown_if" in variable:
        gates = list(variable["shown_if"]) if isinstance(variable["shown_if"], dict) else []
        if len(gates) != 1 or gates[0] not in list(schema["variables"])[:list(schema["variables"]).index(name)]:
            problems.append(f"{name}: shown_if names one variable listed before, with the answers that show the question")
    if "before_visit" in variable and kind != "date":
        problems.append(f"{name}: before_visit goes on a date")
    if "separator" in variable and (kind != "item" or "codes" not in variable):
        problems.append(f"{name}: separator goes on an item that has codes")
    if "doubt" in variable:
        doubt = variable["doubt"]
        is_block = isinstance(doubt, dict) and set(doubt) <= {"period", "values", "note", "remove"}
        if not is_block or not is_range(doubt.get("period")) or not isinstance(doubt["period"][0], pd.Timestamp):
            problems.append(f"{name}: doubt needs a period [first day, last day], and may have values, a note and remove")
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
        source = variable["derived_from"]
        is_checked_score = "compare" in schema.get("scores", {}).get(source, {})
        is_other_variable = source in schema["variables"] and source != name
        if not is_checked_score and not is_other_variable:
            problems.append(f"{name}: derived_from must name a score that has compare, or another variable")
    if columns is not None:
        for column in raw_columns(schema, variable) + variable.get("unit_columns", []):
            if column not in columns:
                problems.append(f"{name}: column '{column}' is not in the extraction")
    return problems


def check_z_score(name, score):
    """The fields of a z-score computed with a regression, and of the band of a z-score."""
    problems = []
    if ("with" in score and "regression" not in score) or not isinstance(score.get("with", {}), dict):
        problems.append(f"{name}: with goes with regression: a mapping {{term of the table: variable}}")
    if "band_of" in score:
        alone_or_lookup = [kind for kind in ["sum", "mean", "max", "min", "regression", "custom"] if kind in score] == []
        limits = score.get("limits")
        rising = isinstance(limits, list) and all(isinstance(limit, float) for limit in limits) and limits == sorted(limits)
        if not alone_or_lookup or not rising or len(limits) == 0:
            problems.append(f"{name}: band_of goes alone or with lookup, and needs limits, numbers in rising order")
    elif "limits" in score:
        problems.append(f"{name}: limits goes with band_of")
    return problems


def check_scores(schema):
    problems = []
    known = set(schema["variables"]) | set(schema.get("uses", []))      # uses: scores that other schemas deliver
    for name, score in schema.get("scores", {}).items():
        for field in score:
            if field not in SCORE_FIELDS:
                problems.append(f"{name}: unknown field '{field}'")
        kinds = [kind for kind in ["sum", "mean", "max", "min", "lookup", "profile", "regression", "distance", "custom"] if kind in score]
        if len(kinds) != 1 and not (kinds == [] and "band_of" in score):
            problems.append(f"{name}: a score has exactly one of sum, mean, max, min, lookup, regression and custom, or band_of alone")
        combines = "sum" in score or "mean" in score or "max" in score or "min" in score
        if ("points" in score or "otherwise" in score) and not combines:
            problems.append(f"{name}: points and otherwise go with sum, mean, max or min")
        points = score.get("points", {})
        if not isinstance(points, dict) or not all(isinstance(number, float) for pair in points.items() for number in pair):
            problems.append(f"{name}: points is a mapping {{answer: points}} of numbers")
        if "custom" in score and not hasattr(custom, score["custom"]):
            problems.append(f"{name}: there is no function '{score['custom']}' in facedata/custom.py")
        if "winsor" in score and not is_range(score["winsor"]):
            problems.append(f"{name}: winsor on a score must be [q_low, q_high]")
        if ("lookup" in score or "regression" in score or "profile" in score or "distance" in score) != ("from" in score):
            problems.append(f"{name}: lookup, regression and profile need from, the raw score; from goes with one of them")
        if ("profile" in score or "distance" in score) != isinstance(score.get("from"), list) and "regression" not in score:
            problems.append(f"{name}: a profile and a distance read a list in from, and only they do (a regression may)")
        problems.extend(check_z_score(name, score))
        if "minus" in score and "sum" not in score:
            problems.append(f"{name}: minus goes with sum")
        if "scale" in score:
            scale = score["scale"]
            two_numbers = isinstance(scale, list) and len(scale) == 2 and all(isinstance(number, float) for number in scale)
            if not two_numbers or ("sum" not in score and "mean" not in score):
                problems.append(f"{name}: scale is [factor, offset], on a score that has sum or mean")
        if "by" in score and "lookup" not in score and "regression" not in score:
            problems.append(f"{name}: by goes with lookup or regression")
        if ("age" in score or "age_date" in score) and "lookup" not in score and "regression" not in score:
            problems.append(f"{name}: age and age_date go with lookup or regression")
        if score["stop_at_zero"] and "sum" not in score:
            problems.append(f"{name}: stop_at_zero goes with sum")
        if score["compare_turned"] and "compare" not in score:
            problems.append(f"{name}: compare_turned goes with compare")
        used = (score.get("sum", []) + score.get("mean", []) + score.get("max", []) + score.get("min", [])
                + score.get("reverse", []) + score.get("minus", []))
        for field in ["compare", "by", "otherwise", "band_of", "age", "age_date"]:
            if field in score:
                used = used + [score[field]]
        if "from" in score:                          # one variable, or the list of a profile
            used = used + (score["from"] if isinstance(score["from"], list) else [score["from"]])
        if isinstance(score.get("with"), dict):
            used = used + list(score["with"].values())
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
    ways = [way for way in ("column", "filled", "age") if way in version]
    if "name" not in version or len(ways) != 1:
        problems.append("version: needs a name, and one of column with codes, filled and age")
    for name, band in version.get("age", {}).items():
        numbers = pd.to_numeric(pd.Series(band if isinstance(band, list) else []), errors="coerce")
        if len(numbers) != 2 or numbers.isna().any() or not numbers[0] < numbers[1]:
            problems.append(f"version: age '{name}' needs two numbers, the first below the second")
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
    since = version.get("since", {})
    if not isinstance(since, dict):
        problems.append("version: since is written {version: YYYY-MM-DD}")
        since = {}
    for name, first_day in since.items():
        if name not in version_names(schema):
            problems.append(f"version: since names '{name}', which is not a version of the block")
        if pd.isna(pd.to_datetime(first_day, format="%Y-%m-%d", errors="coerce")):
            problems.append(f"version: since '{name}' needs a date written YYYY-MM-DD")
    for name in version.get("override", {}):
        if name not in version_names(schema):
            problems.append(f"version: override names '{name}', which is not a version of the block")
    if columns is not None:
        used = [version["column"]] if "column" in version else []
        for group in list(version.get("filled", {}).values()) + list(version.get("override", {}).values()):
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
    if set(sign) == {"before", "turn"}:
        if not isinstance(sign["before"], pd.Timestamp):
            problems.append("sign: before is a date written YYYY-MM-DD")
        for name in sign["turn"]:
            if name not in schema["variables"]:
                problems.append(f"sign: '{name}' is not a variable")
        return problems
    if set(sign) != {"relation", "by", "pairs"}:
        problems.append("sign: needs relation, by and pairs, or before and turn, and nothing else")
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


def check_lists(schema):
    """Problems of the fields of a list instrument (SCHEMA_SPEC, section 15)."""
    problems = []
    names, block = schema.get("names"), schema.get("at_visit")
    if (names is not None or block is not None) and schema.get("level") != "list":
        problems.append("names and at_visit need level: list")
    if "crossed" in schema:
        read = {column for variable in schema["variables"].values() for column in variable.get("columns", [])}
        if schema.get("level") != "list" or not isinstance(schema["crossed"], list) or not set(schema["crossed"]) <= read:
            problems.append("crossed needs level: list, and lists raw columns that variables of the schema read")
    if "per_visit" in schema and (schema.get("level") != "list" or block is not None or "crossed" in schema):
        problems.append("per_visit needs level: list, and goes with neither at_visit nor crossed")
    if "packed" in schema:
        packed = schema["packed"]
        well_formed = isinstance(packed, dict) and all(isinstance(fields, dict) and isinstance(fields.get("fields"), list)
                                                       and fields.get("text", fields["fields"][0]) in fields["fields"] for fields in packed.values())
        if schema.get("level") != "list" or not well_formed:
            problems.append("packed needs level: list, and for each raw column its fields (and text, one of the fields)")
    if names is not None:
        if not isinstance(names, dict) or set(names) - {"path", "otherwise"} != {"column", "clean", "table", "gives"}:
            problems.append("names needs column, clean, table and gives, and nothing else but otherwise")
        elif not hasattr(custom, names["clean"]):
            problems.append(f"names: there is no function '{names['clean']}' in facedata/custom.py")
        elif not Path(names["path"]).exists():
            problems.append(f"names: there is no table '{names['table']}' in the cohort folder")
    if block is not None:
        known = set(schema.get("variables", {}))
        if not isinstance(block, dict) or not {"start", "end", "columns"} <= set(block) or not {block.get("start"), block.get("end")} <= known:
            problems.append("at_visit needs start and end, two variables of the schema, and columns")
            return problems
        for name, column in block["columns"].items():
            if not isinstance(column, dict) or not {"where", "label"} <= set(column) or not set(column["where"]) <= known:
                problems.append(f"at_visit: column '{name}' needs a label and a where that names variables of the schema")
    return problems


def check_relatives(schema):
    """Problems of the fields of an instrument asked for each relative (SCHEMA_SPEC, section 16)."""
    problems = []
    relatives, block = schema.get("relatives"), schema.get("per_patient")
    is_level = schema.get("level") == "relatives"
    if is_level != isinstance(relatives, dict) or (block is not None and not is_level):
        problems.append("level: relatives and relatives go together, and per_patient needs them")
        return problems
    if not is_level:
        return problems
    for prefix, who in relatives.items():
        if not isinstance(who, dict) or "relative" not in who:
            problems.append(f"relatives: '{prefix}' needs a relative, the name of its rows")
    if block is not None:
        known = set(schema.get("variables", {}))
        if not isinstance(block, dict) or not {"by", "counts", "columns"} <= set(block) or block.get("by") not in known:
            problems.append("per_patient needs by, a variable of the schema, counts and columns")
            return problems
        for name, column in block["columns"].items():
            complete = isinstance(column, dict) and {"among", "where", "label"} <= set(column)
            if not complete or not set(column["where"]) <= known or not set(column["among"]) <= set(block["counts"]):
                problems.append(f"per_patient: column '{name}' needs a label, an among that lists groups of counts "
                                "and a where that names variables of the schema")
    return problems


def check_schema(schema, columns=None):
    """Problems found in one schema. An empty list means the schema is correct.

    columns: the column names of the extraction. Without them, the test that
    every raw column exists is left out.
    """
    problems = check_lists(schema) + check_relatives(schema)
    for field in schema:
        if field not in INSTRUMENT_FIELDS and field not in ("file", "derived_from"):
            problems.append(f"unknown field '{field}'")
    for field in REQUIRED_FIELDS:
        if field not in schema:
            problems.append(f"missing field '{field}'")
    if schema.get("instrument") != schema.get("file", schema.get("instrument")):
        problems.append("the instrument name must be the file name")
    if schema.get("status") not in ("draft", "reviewed"):
        problems.append("status is draft or reviewed")
    if schema.get("level", "visit") not in ("visit", "patient", "list", "relatives"):
        problems.append("level is visit, patient, list or relatives")
    if "implausible_visits" in schema and not str(schema["implausible_visits"]).isdigit() or str(schema.get("implausible_visits", "2")) in ("0", "1"):
        problems.append("implausible_visits is a whole number, 2 or more")
    if "implausible_pool" in schema and "implausible_visits" not in schema:
        problems.append("implausible_pool goes with implausible_visits")
    for name, variable in schema.get("variables", {}).items():
        problems = problems + check_variable(name, variable, schema, columns)
    if columns is not None and isinstance(schema.get("packed"), dict):
        for column in schema["packed"]:
            if column not in columns:
                problems.append(f"packed: column '{column}' is not in the extraction")
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
    per_patient = set()          # the variables that patient-level schemas give
    for schema in schemas.values():
        if schema.get("level") == "patient":
            per_patient = per_patient | set(schema["variables"])
    for instrument, schema in schemas.items():
        block = schema.get("per_patient")
        for name in block.get("counts", {}).values() if isinstance(block, dict) else []:
            if name not in per_patient:
                problems.append(f"{instrument}: per_patient counts with '{name}', which no patient-level schema gives")
        for name in list(schema["variables"]) + list(schema.get("scores", {})):
            both_lists = schema.get("level") == "list" and schemas.get(seen_outputs.get(name), {}).get("level") == "list"
            if name in seen_outputs and not both_lists:          # list instruments fill one table: they may share names
                problems.append(f"output '{name}' is in {seen_outputs[name]} and in {instrument}")
            seen_outputs[name] = instrument
        if "version" in schema:
            block = schema["version"]
            first = seen_versions.setdefault(block.get("name"), block)
            if block != first:
                problems.append(f"{instrument}: version block '{block.get('name')}' differs from another schema's")
        for name, variable in schema["variables"].items():
            for edition in variable.get("versions", ["every visit"]):
                for column in raw_columns(schema, variable):
                    if variable.get("shared"):           # a band and a number may read the same column
                        sharing.setdefault(column, []).append(variable["type"])
                    elif "separator" not in variable:    # each box of a list may have its variable
                        readers.setdefault(column, []).append((edition, name, variable["keep"]))
    for instrument, schema in schemas.items():
        for name in schema.get("uses", []):
            if name not in seen_outputs or seen_outputs[name] == instrument:
                problems.append(f"{instrument}: uses '{name}', which no other schema delivers")
    for column, types in sharing.items():
        if sorted(types) not in (["band", "number"], ["number"]) or column in readers:        # or one number, with nothing for the bands
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
