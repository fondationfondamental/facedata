"""The data dictionary as one JSON file.

Step 2 of 3 (dictionary/README.md). Puts together, for every delivered
variable of the four cohorts:

- what the schemas say (facedata/<cohort>/schemas): type, range, codes, unit,
  raw column, score formula, edition, reading rules;
- what was written by hand (dictionary/annotations): description, version,
  reference, construct, direction, cut-offs, each with its source;
- what the data say (dictionary/stats, written by build_stats.py);
- what differs between cohorts (common_instruments.yaml, shared_names.yaml,
  differences.yaml, and a comparison of the schemas);
- the label and the coding of the Excel dictionaries, when they are on the computer.

Nothing is guessed: a field that no source gives is left empty and its name
goes into `incomplete`.

    .venv/bin/python dictionary/build_json.py       # writes dictionary/face_dictionary.json
"""

import datetime
import fnmatch
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import facedata.asp  # noqa: E402
import facedata.bp  # noqa: E402
import facedata.dr  # noqa: E402
import facedata.sz  # noqa: E402
from facedata import custom  # noqa: E402
from facedata.schema import load_schemas, raw_columns  # noqa: E402
from facedata.thesaurus import expand_range  # noqa: E402

FOLDER = Path(__file__).resolve().parent
MODULES = {"bp": facedata.bp, "sz": facedata.sz, "dr": facedata.dr, "asp": facedata.asp}
COHORTS = list(MODULES)
TABLE_OF_LEVEL = {"visit": "data", "patient": "patients", "list": "treatments", "relatives": "relatives"}
COMBINE = ["sum", "mean", "max", "min"]
FROM_A_TABLE = ["lookup", "regression", "profile", "distance", "band_of", "custom"]
READING_FIELDS = ["asked_if", "box_list", "shown_if", "separator", "unit_column", "units", "ignore_units", "unit_rule",
                  "censor_units", "censored", "bands", "limits", "shared", "z_range", "lookup", "from", "winsor",
                  "derived_from", "doubt", "before_visit", "not_above", "day", "parse", "note"]
KEY_TEXT = {
    "cohort": "The cohort of the row: bp, sz, dr or asp. First column of every table.",
    "usubjid": "Patient identifier, unique inside a cohort only. Join two cohorts on cohort and usubjid, never on usubjid alone.",
    "visit": "Visit label as extracted (screening, V0, V6_mois, V1_an...): the planned time point.",
    "visit_order": "Rank of the visit of the patient.",
    "visit_month": "Planned months since inclusion, read from the visit label (V0 = 0, V1_an = 12). Empty for the screening visit.",
    "visit_date": "Date of the visit.",
    "siteid": "Code of the centre, as text with two digits.",
    "age": "Age at the visit in years with decimals, from the date of birth and the visit date.",
    "list": "Which list the row belongs to, in a cohort whose table of treatments holds several lists.",
    "item": "Rank of the item in its list (1, 2, 3...).",
    "relative": "Which relative the row describes (mother, father, sister_1...).",
}
GENERIC_LABEL = re.compile(r"(\bitem \d+\w?$)|(^box \d+$)|(^column \w+$)|(^code_\d+$)", re.IGNORECASE)
YES_WORDS = {"oui", "yes", "y", "o", "coché", "coche", "vrai", "true"}


def read_yaml(path, as_text=False):
    """A YAML file as a dict. as_text: every value stays text, as the schemas are read."""
    with open(path, encoding="utf-8") as file:
        return yaml.load(file, Loader=yaml.BaseLoader if as_text else yaml.SafeLoader) or {}


def plain(value):
    """A value that JSON can hold: dates as text, whole floats as whole numbers, containers walked through."""
    if isinstance(value, dict):
        return {str(key if not isinstance(key, float) else plain(key)): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [plain(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        if pd.isna(value):
            return None
        return int(value) if value == int(value) and abs(value) < 1e15 else value
    return value


# ---------------------------------------------------------------- hand-written and reference inputs

def read_annotations():
    """Every file of dictionary/annotations as one dict: instrument -> annotation."""
    annotations = {}
    for path in sorted((FOLDER / "annotations").glob("*.yaml")):
        for name, entry in read_yaml(path).items():
            annotations[name] = {**(entry or {}), "file": "dictionary/annotations/" + path.name}
    return annotations


def annotation_of(annotation, name):
    """The entry of a score or a variable in an instrument's annotation: its own name first, then a pattern with *."""
    entries = {**(annotation.get("variables") or {}), **(annotation.get("scores") or {})}
    if name in entries:
        return entries[name] or {}
    for pattern, entry in entries.items():
        if "*" in pattern and fnmatch.fnmatchcase(name, pattern):
            return entry or {}
    return {}


def flag_meanings():
    """The flag codes with their severity and meaning, read in docs/ARCHITECTURE.md (section 6)."""
    text = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    found = re.findall(r"^\| `(\w+)` \| (info|discrepancy|danger) \| (.+?) \|$", text, flags=re.MULTILINE)
    return {code: {"severity": severity, "meaning": meaning} for code, severity, meaning in found}


def read_workbook(path):
    """An Excel dictionary as {"sheets": [names], "names": {extraction name: sheet, section, label, coding}}.

    The sheets do not all have the same columns: the header row says where the
    label and the coding are. Names are in lower case and ranges are expanded
    ("STAYA01 à STAYA20"). Returns None when the workbook is not on the computer.
    """
    if not Path(path).exists():
        return None
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    names, kept = {}, []
    for sheet_name, sheet in sheets.items():
        sheet = sheet.fillna("")
        header, first = None, 0
        for position, row in enumerate(sheet.itertuples(index=False)):
            starts = [str(cell).strip().lower().startswith(("nom variable", "nom de variable")) for cell in row[:3]]
            if any(starts):                          # one sheet has a code-list column before the names
                header, first = position, starts.index(True)
                break
        if header is None:                           # the contents and the instructions
            continue
        sheet = sheet.iloc[:, first:]
        titles = [str(cell).strip().lower() for cell in sheet.iloc[header]]
        label_at = next((index for index, title in enumerate(titles) if title == "label"), None)
        coding_at = next((index for index, title in enumerate(titles) if title in ("codage", "code")), None)
        kept.append(sheet_name)
        section = ""
        for row in sheet.iloc[header + 1:].itertuples(index=False):
            name = str(row[0]).strip()
            if name == "":
                continue
            if "".join(str(cell) for cell in row[1:]).strip() == "":      # a line with a name only is a section header
                section = name
                continue
            for one in expand_range(name):
                names.setdefault(one.lower(), {"sheet": sheet_name, "section": section,
                                               "label": str(row[label_at]).strip() if label_at is not None else "",
                                               "coding": str(row[coding_at]).strip() if coding_at is not None else ""})
    return {"sheets": kept, "names": names}


# ---------------------------------------------------------------- what a schema says about a score

def items_of(score):
    """The names that a score adds up, averages or takes the highest or the lowest of."""
    for field in COMBINE:
        if field in score:
            return list(score[field])
    return []


def method_of(score):
    for field in COMBINE + FROM_A_TABLE:
        if field in score:
            return field
    return "unknown"


def signed_leaves(name, schema, sign=1, seen=()):
    """The delivered variables and scores under a score, each with +1 or -1.

    -1: a higher answer lowers the score (a reversed item, a value taken off).
    A hidden score (keep: false) used as an item is opened; a delivered one is
    a child of its own. Returns {name: sign} for the direct delivered children,
    and {leaf variable: sign} for all the variables below.
    """
    scores = schema.get("scores", {})
    score = scores[name]
    children, leaves = {}, {}
    parts = [(item, -1 if item in score.get("reverse", []) else 1) for item in items_of(score)]
    parts += [(item, -1) for item in score.get("minus", [])]
    for item, item_sign in parts:
        total = sign * item_sign
        if item in scores and item not in seen:
            below_children, below_leaves = signed_leaves(item, schema, total, seen + (name,))
            if scores[item].get("keep", True):
                children[item] = total
            else:
                children.update(below_children)
            leaves.update(below_leaves)
        else:
            leaves[item] = total
            if schema["variables"].get(item, {}).get("keep", True):
                children[item] = total
    return children, leaves


def words_for_score(name, score, schema):
    """The formula of a score in one or two sentences."""
    method = method_of(score)
    items = items_of(score)
    shown = ", ".join(items) if len(items) <= 12 else ", ".join(items[:3]) + ", ..., " + items[-1]
    if method in COMBINE:
        verb = {"sum": "Sum", "mean": "Mean", "max": "Highest", "min": "Lowest"}[method]
        text = "%s of %d %s (%s)" % (verb, len(items), "value" if len(items) == 1 else "values", shown)
        if score.get("reverse"):
            text += "; reversed first (minimum + maximum - answer): " + ", ".join(score["reverse"])
        if score.get("points"):
            text += "; answers that count other points than their code: " + ", ".join(
                "%s counts %s" % (plain(answer), plain(points)) for answer, points in score["points"].items())
        if score.get("stop_at_zero"):
            text += "; the items after the first one scored 0 are not counted"
        if score.get("minus"):
            text += "; minus " + ", ".join(score["minus"])
        if score.get("scale"):
            text += "; then multiplied by %s and %s added" % (plain(score["scale"][0]), plain(score["scale"][1]))
        if "floor" in score:
            text += "; not below %s" % plain(score["floor"])
        needed = score.get("min_items")
        text += "; all the values are needed" if needed is None else "; at least %s of them are needed" % plain(needed)
        if "otherwise" in score:
            text += "; where no item is recorded the score typed in the form is delivered (flag score_as_stored)"
    elif method == "lookup":
        text = "Read in the norm table norms/%s.csv from %s and the age at the visit" % (score["lookup"], score.get("from"))
        if "by" in score:
            text += ", by %s" % score["by"]
        if "band_of" in score:
            text += "; where the table gives nothing, the band of the z-score %s under the normal law" % score["band_of"]
    elif method == "regression":
        others = ", ".join("%s (%s)" % (variable, term) for term, variable in (score.get("with") or {}).items())
        text = "Computed with the regression of norms/%s.csv from %s and the age at the visit" % (score["regression"], plain(score.get("from")))
        text += (", with " + others) if others else ""
        text += ": a z-score, (raw - expected) / standard deviation, or the expected value when the table has no standard deviation"
    elif method == "profile":
        text = "Read in the table norms/%s.csv from the answers to %s, written one after another" % (score["profile"], ", ".join(score.get("from", [])))
    elif method == "distance":
        text = "Sum of the absolute differences between %d answers and the reference answers of norms/%s.csv" % (len(score.get("from", [])), score["distance"])
    elif method == "band_of":
        text = "Percentile band of the z-score %s under the normal law, with the limits %s" % (score["band_of"], plain(score.get("limits")))
    elif method == "custom":
        function = getattr(custom, score["custom"], None)
        told = " ".join((inspect.getdoc(function) or "").split("\n\n")[0].split()).rstrip(".") if function else ""
        text = "Computed by the function facedata.custom.%s: %s" % (score["custom"], told[:1].lower() + told[1:])
    else:
        text = ""
    if "age" in score or "age_date" in score:
        text += "; the table is read with the age typed in the form when it is within one year of the age at the visit" if "age" in score else \
                "; the table is read with the age at the date of the assessment"
    if "compare" in score:
        stored = schema["variables"].get(score["compare"], {}).get("columns", [score["compare"]])
        text += ". Compared with the score stored in the column %s" % ", ".join(stored)
        if score.get("compare_offset"):
            text += " (the stored one is higher by %s, a known offset)" % plain(score["compare_offset"])
        text += ": a difference is flagged score_mismatch and this recomputed value is the one delivered"
    return text.strip() + "."


def possible_range(name, schema, seen=()):
    """The lowest and highest value that a sum, a mean, a highest or a lowest of items can take, from the ranges of its items.

    None when the schema does not give the range of every item, or when some
    answers count other points than their code. A range written in the schema wins.
    """
    scores, variables = schema.get("scores", {}), schema["variables"]
    if name in variables:
        limits = variables[name].get("range")
        return plain(limits) if variables[name].get("type") in ("item", "number") and limits else None
    score = scores.get(name)
    if score is None or name in seen:
        return None
    if "range" in score:
        return plain(score["range"])
    if method_of(score) not in COMBINE or "points" in score or score.get("stop_at_zero"):
        return None
    parts = [possible_range(item, schema, seen + (name,)) for item in items_of(score)]
    taken = [possible_range(item, schema, seen + (name,)) for item in score.get("minus", [])]
    if not parts or any(part is None for part in parts + taken):
        return None
    lows, highs = [part[0] for part in parts], [part[1] for part in parts]
    method = method_of(score)
    needed = int(score.get("min_items", len(parts)))
    if method == "sum":                              # with fewer items than all, the lowest sum counts the smallest ones only
        low = sum(sorted(lows)[:needed]) if all(value >= 0 for value in lows) else sum(lows)
        high = sum(highs)
    elif method == "mean":
        low, high = min(lows), max(highs)
    else:
        low, high = (min(lows), max(highs)) if needed < len(parts) else ((max(lows), max(highs)) if method == "max" else (min(lows), min(highs)))
    low, high = low - sum(part[1] for part in taken), high - sum(part[0] for part in taken)
    if "scale" in score:
        factor, offset = score["scale"]
        low, high = sorted([low * factor + offset, high * factor + offset])
    if "floor" in score:
        low, high = max(low, score["floor"]), max(high, score["floor"])
    return [plain(float(low)), plain(float(high))]


def derivation_of_score(name, score, schema):
    """How a score is computed, as fields and as words."""
    derivation = {"method": method_of(score), "formula": words_for_score(name, score, schema)}
    for field in COMBINE:
        if field in score:
            derivation["items"] = list(score[field])
    for field in ["reverse", "points", "minus", "scale", "floor", "min_items", "from", "by", "with", "band_of", "limits", "versions"]:
        if field in score:
            derivation[field] = plain(score[field])
    if score.get("stop_at_zero"):
        derivation["stop_at_zero"] = True
    for field in ["lookup", "regression", "profile", "distance"]:
        if field in score:
            derivation["norm_table"] = "norms/%s.csv" % score[field]
    if "custom" in score:
        derivation["function"] = "facedata.custom." + score["custom"]
    for field, key in [("compare", "stored_in"), ("otherwise", "typed_total_in")]:
        if field in score:
            derivation[key] = schema["variables"].get(score[field], {}).get("columns", [score[field]])
    if score.get("compare_offset"):
        derivation["stored_offset"] = plain(score["compare_offset"])
    return derivation


# ---------------------------------------------------------------- what a schema says about a variable

def words_for_reading(variable, schema):
    """The rules of the schema that change how a value must be understood, as sentences."""
    told = []
    if "asked_if" in variable:
        told.append("Asked only after a yes to %s (or a count above 0): an empty cell after a no is delivered as 0." % variable["asked_if"])
    if "box_list" in variable:
        told.append("One box of the list %s: an empty box beside a ticked box of the same list is delivered as 0." % variable["box_list"])
    if "shown_if" in variable:
        for gate, answers in variable["shown_if"].items():
            told.append("Shown by the form only when %s is %s: a value written elsewhere is removed (flag not_shown)." % (gate, " or ".join(str(plain(a)) for a in answers)))
    if "separator" in variable:
        told.append("The raw cell holds several ticked boxes; this variable is 1 when one of its boxes is ticked.")
    if "units" in variable:
        told.append("Brought to %s from: %s." % (variable.get("unit"), ", ".join(variable["units"])))
    if variable.get("type") == "band":
        told.append("Percentile band: the value is the lower limit of the band (limits %s)." % plain(variable.get("limits")))
    if variable.get("shared"):
        told.append("The raw column holds bands and z-scores, read by two variables.")
    if "derived_from" in variable:
        told.append("Stored by the application, which computed it from %s: doubtful where that value is wrong or empty (flag derived_doubt)." % variable["derived_from"])
    if variable.get("before_visit"):
        told.append("A date of an event before the visit: a date on the day of the visit or later is removed.")
    if "not_above" in variable:
        told.append("A value above %s on the same row is kept and flagged check_failed." % variable["not_above"])
    if isinstance(variable.get("doubt"), dict):
        doubt = variable["doubt"]
        period = " to ".join(str(plain(day)) for day in doubt.get("period", []))
        action = "not delivered (flag period_removed)" if doubt.get("remove") else "kept and flagged period_doubt"
        told.append("Visits dated %s: values %s. %s" % (period, action, doubt.get("note", "")))
    if "versions" in variable:
        told.append("Read only on the visits of the edition %s (column %s)." % (" or ".join(variable["versions"]), schema.get("version", {}).get("name", "")))
    if variable.get("winsor") not in (None, False) or (variable.get("type") == "number" and variable.get("winsor") is None):
        told.append("Clipped to the 1st and 99th percentile by load() unless winsorise=False; the figures here are not clipped.")
    if "note" in variable:
        told.append(str(variable["note"]))
    return [" ".join(text.split()) for text in told]


def kind_of(spec_type, spec, stats):
    """The kind of value for an analysis: continuous, ordinal, binary, nominal, date or text."""
    if spec_type == "category":
        labels = set((spec.get("codes") or {}).values())
        return "binary" if len(labels) == 2 else "nominal"
    if spec_type in ("date", "text"):
        return spec_type
    if spec_type in ("number", "time"):
        return "continuous"
    if spec_type == "band":
        return "ordinal"
    if spec_type == "item":
        return "binary" if plain(spec.get("range")) == [0, 1] else "ordinal"
    distinct = ((stats or {}).get("stats", {}).get("all") or {}).get("n_distinct")       # a score: the data say how many levels
    limits = plain(spec.get("range"))
    if limits == [0, 1] or (distinct is not None and distinct <= 2 and limits is None and method_of(spec) == "custom"):
        return "binary"
    if method_of(spec) == "band_of" or (method_of(spec) == "lookup" and "limits" in spec):
        return "ordinal"
    if distinct is not None and distinct <= 7:
        return "ordinal"
    return "continuous"


def anchors_from(coding):
    """A coding written '0:Absent; 1:Tolérable' or 'Oui=1,Non=0' as {code: label}; {} when it cannot be read."""
    found = {}
    for part in re.split(r"[;\n]|,(?=\s*[^,=:]+[=:])", coding or ""):
        match = re.fullmatch(r"\s*(-?\d+)\s*[:=]\s*(.+?)\s*", part) or re.fullmatch(r"\s*(.+?)\s*[:=]\s*(-?\d+)\s*", part)
        if not match:
            continue
        first, second = match.groups()
        code, label = (first, second) if re.fullmatch(r"-?\d+", first) else (second, first)
        found[code] = label
    return found


def variable_block(cohort, name, spec, schema, is_score, context):
    """What one cohort says about one delivered variable or score, before the statistics."""
    stats = context["stats"].get(name)
    spec_type = spec.get("type", "score") if not is_score else "score"
    level = schema.get("level", "visit")
    block = {"instrument": schema["instrument"], "tab": context["tab_of"][schema["instrument"]], "section": schema.get("section", ""),
             "table": TABLE_OF_LEVEL[level], "label": spec.get("label", ""), "type": spec_type,
             "kind": kind_of(spec_type, spec, stats)}
    if is_score:
        block["source"] = {"columns": []}
        block["derivation"] = derivation_of_score(name, spec, schema)
        if "stored_in" in block["derivation"]:
            block["source"]["stored_score"] = block["derivation"]["stored_in"]
    else:
        block["source"] = {"columns": raw_columns(schema, spec)}
        reading = {field: plain(spec[field]) for field in READING_FIELDS if field in spec}
        if reading:
            block["reading"] = reading
        if "derived_from" in spec and block["kind"] in ("continuous", "ordinal"):       # a standard score next to its raw score
            block["derivation"] = {"method": "stored", "from": spec["derived_from"],
                                   "formula": "Stored by the application, which computed it from %s." % spec["derived_from"]}
        if "columns" in spec and not spec["columns"] and "derived_from" in schema:       # a yes/no column computed from rows
            block["derivation"] = {"method": "computed", "from": schema["derived_from"],
                                   "formula": "Computed by facedata from the rows of the instrument %s." % schema["derived_from"]}
    rules = words_for_reading(spec, schema) if not is_score else (
        ["Computed only on the visits of the edition %s." % " or ".join(spec["versions"])] if "versions" in spec else [])
    if rules:
        block["rules"] = rules
    for field in ["unit", "range"]:
        if spec.get(field) not in (None, ""):
            block[field] = plain(spec[field])
    if is_score and "range" not in block:
        limits = possible_range(name, schema)
        if limits:
            block["range"], block["range_from"] = limits, "the ranges of the items"
    if isinstance(spec.get("codes"), dict):
        if spec_type == "category":
            block["categories"] = list(dict.fromkeys(spec["codes"].values()))
        block["raw_codes"] = dict(spec["codes"])
    if isinstance(spec.get("missing"), dict):
        block["missing_codes"] = dict(spec["missing"])
    editions = spec.get("versions") or (schema.get("defaults") or {}).get("versions")
    if editions:
        block["edition"] = {"column": schema.get("version", {}).get("name"), "values": list(editions)}
    workbook = context["workbook"]
    if workbook and not is_score:
        for column in block["source"]["columns"]:
            line = workbook["names"].get(column.lower())
            if line:
                anchors = anchors_from(line["coding"]) if spec_type != "category" else {}
                if anchors:                          # the coding of the Excel dictionary, read as code -> label
                    block["answer_labels"] = anchors
                excel = {key: line[key] for key in ["label", "coding"] if line[key] and not (key == "coding" and anchors)}
                if excel.get("label", "").strip().lower() == block["label"].strip().lower():
                    del excel["label"]
                if excel:
                    block["excel"] = excel
                break
    return block


# ---------------------------------------------------------------- one cohort

def tabs_of_cohort(schemas, workbook):
    """The tab of each instrument: the sheet of the Excel dictionary that lists its columns.

    The schemas of BP, SZ and DR name their sheet. The ASP schemas name a table
    of the export: the sheet is the one that holds most of their columns, and
    for an instrument with no column in the workbook, the sheet of most
    instruments of its folder.
    """
    sheets = set(workbook["sheets"]) if workbook else set()
    tab_of, by_folder = {}, {}
    for name, schema in schemas.items():
        if schema["tab"] in sheets or not workbook:
            tab_of[name] = schema["tab"]
            continue
        counts = {}
        for variable in schema["variables"].values():
            for column in variable.get("columns", []):
                line = workbook["names"].get(column.lower())
                if line:
                    counts[line["sheet"]] = counts.get(line["sheet"], 0) + 1
        if counts:
            tab_of[name] = max(counts, key=counts.get)
            folder = by_folder.setdefault(schema["tab"], {})
            folder[tab_of[name]] = folder.get(tab_of[name], 0) + 1
    for name, schema in schemas.items():
        if name not in tab_of:
            folder = by_folder.get(schema["tab"], {})
            tab_of[name] = max(folder, key=folder.get) if folder else schema["tab"]
    return tab_of


def cohort_blocks(cohort, context):
    """Every delivered variable and score of a cohort: {name: block}, and the tree of the scores."""
    schemas = context["schemas"]
    blocks, parents, children, leaves = {}, {}, {}, {}
    for schema in schemas.values():
        for name, spec in schema["variables"].items():
            if spec.get("keep", True) and name not in blocks:
                blocks[name] = variable_block(cohort, name, spec, schema, False, context)
            elif spec.get("keep", True):
                blocks[name].setdefault("also_in", []).append(schema["instrument"])
        for name, spec in schema.get("scores", {}).items():
            if not spec.get("keep", True):
                continue
            blocks[name] = variable_block(cohort, name, spec, schema, True, context)
            if method_of(spec) in COMBINE and len(items_of(spec)) + len(spec.get("minus", [])) == 1:
                blocks[name]["computed_from"] = items_of(spec)       # one value rescaled: no hierarchy
            elif method_of(spec) in COMBINE:
                below, all_leaves = signed_leaves(name, schema)
                children[name] = below
                leaves[name] = set(all_leaves)
                for child, sign in below.items():
                    parents.setdefault(child, {})[name] = sign
    for name, block in blocks.items():               # the level in the hierarchy
        is_score = block["type"] == "score"
        inside = any(name != other and leaves.get(name) and leaves[name] < leaves[other]
                     and blocks[other]["instrument"] == block["instrument"] for other in leaves)
        if is_score:
            block["level"] = "subscore" if name in parents or inside else "score"
        elif block.get("derivation", {}).get("method") == "stored":
            block["level"] = "score"
        else:
            block["level"] = "item" if name in parents else "standalone"
        if name in parents:
            widest_first = sorted(parents[name], key=lambda parent: -len(leaves.get(parent, ())))
            block["parents"] = {parent: parents[name][parent] for parent in widest_first}
        if name in children:
            block["children"] = list(children[name])
        source = block.get("derivation", {}).get("from")
        if source and block.get("derivation", {}).get("method") not in COMBINE and "computed_from" not in block:
            block["computed_from"] = [one for one in (source if isinstance(source, list) else [source]) if isinstance(one, str)]
    return blocks


def short_figures(figures, block):
    """The figures worth keeping for the kind of value: the percentiles say nothing more than the counts of a yes/no box."""
    wanted = {"n", "mean", "sd", "min", "max", "median", "first_year", "last_year"}
    if block["kind"] in ("continuous", "text"):
        wanted |= {"p01", "p05", "p25", "p75", "p95", "p99", "n_distinct"}
    if block["kind"] == "ordinal":
        wanted |= {"p25", "p75"}
    if block["type"] in ("item", "score") and block["kind"] != "binary":
        wanted |= {"at_minimum_pct", "at_maximum_pct"}
    return {name: value for name, value in figures.items() if name in wanted}


def add_statistics(blocks, context):
    """The figures of build_stats.py into each block, and the keys and companion columns that facedata adds."""
    stats, order = context["stats"], [visit["visit"] for visit in context["visits"]]
    for name, figures in stats.items():
        if name not in blocks and figures["role"] != "variable":
            owner = name[:-5] if figures["role"] == "censoring" else None
            users = figures.get("instruments") or []
            blocks[name] = {
                "instrument": users[0] if users else None, "table": figures["table"],
                "level": "key" if figures["role"] == "key" else "companion", "type": "category" if figures["role"] == "edition" else "item",
                "kind": {"key": "key", "censoring": "ordinal", "edition": "nominal"}[figures["role"]],
                "label": KEY_TEXT.get(name) if figures["role"] == "key" else (
                    "Censoring of %s: -1 the true value is below the one delivered, 0 observed, +1 above" % owner if owner
                    else "Edition or form of the instrument used at the visit"),
                "source": {"columns": []}}
            if owner:
                blocks[name]["companion_of"] = [owner]
            elif figures["role"] == "edition":
                blocks[name]["companion_of"] = users
                blocks[name]["tab"] = context["tab_of"].get(users[0]) if users else None
            if owner in blocks:
                blocks[name]["tab"] = blocks[owner].get("tab")
        if name not in blocks:
            continue
        block = blocks[name]
        if figures["role"] == "censoring":           # -1, 0 and +1 on every row: the counts say it all
            block["dist"] = {"all": figures["dist"]["all"]} if "all" in figures.get("dist", {}) else {}
            continue
        for field in ["n", "missing", "dist", "flags", "years", "n_sites"]:
            if figures.get(field) not in (None, {}, []):
                block[field] = figures[field]
        block["stats"] = {scope: short_figures(one, block) for scope, one in figures.get("stats", {}).items()}
        if any(figures.get("censored", {}).values()):
            block["censored"] = figures["censored"]
        if "timepoints" in figures:
            block["timepoints"] = {visit: figures["timepoints"][visit] for visit in order if visit in figures["timepoints"]}
        if len(figures.get("instruments", [])) > 1:
            block["instruments"] = figures["instruments"]
    return blocks


# ---------------------------------------------------------------- direction, construct, completeness

def turned(polarity):
    return {"worse": "better", "better": "worse"}.get(polarity, polarity)


def direction_of(name, block, annotation, cohort_blocks_of, annotations):
    """What a higher value means, with where it is known from. Empty fields when no source says it."""
    entry = annotation_of(annotation, name)
    if entry.get("higher_means") or entry.get("polarity"):
        return {key: entry[key] for key in ["higher_means", "polarity", "basis", "source"] if key in entry}
    kind = block["kind"]
    if kind in ("nominal", "date", "text", "key") or block["type"] in ("category", "text", "date") or block["level"] in ("key", "companion"):
        return {"polarity": "not_applicable"}
    for parent, sign in (block.get("parents") or {}).items():       # an item or a sub-score: the formula of its score
        parent_block = cohort_blocks_of.get(parent, {})
        parent_note = annotations.get(parent_block.get("instrument"), {})
        above = annotation_of(parent_note, parent)
        recoded = "points" in parent_block.get("derivation", {})
        keyed = "recoded" if recoded else ("same" if sign > 0 else "reversed")
        direction = {"in_score": {"score": parent, "keyed": keyed}}
        shared = annotation.get("items") or {}
        if keyed == "same" and shared.get("higher_means"):
            direction.update({key: shared[key] for key in ["higher_means", "polarity", "basis", "source"] if key in shared})
        elif above.get("polarity") and keyed != "recoded":
            direction["higher_means"] = ("raises %s" if keyed == "same" else "lowers %s (reversed in the score)") % parent
            direction["polarity"] = above["polarity"] if keyed == "same" else turned(above["polarity"])
            direction["basis"] = "formula"
            direction["source"] = "formula of %s in the schema, and the direction of that score" % parent
        elif keyed == "reversed" and shared.get("polarity"):
            direction.update({"higher_means": "the opposite of the other items (reversed in %s)" % parent,
                              "polarity": turned(shared["polarity"]), "basis": "formula", "source": "reversed item in the schema"})
        return direction
    if kind == "binary" and block["type"] == "item":
        codes = {str(raw).strip().lower(): str(value) for raw, value in (block.get("raw_codes") or {}).items()}
        labels = {str(code): str(label).strip().lower() for code, label in (block.get("answer_labels") or {}).items()}
        if any(raw in YES_WORDS and value in ("1", "1.0") for raw, value in codes.items()) or labels.get("1") in YES_WORDS:
            return {"higher_means": "1 is yes, 0 is no", "polarity": "not_applicable", "basis": "coding",
                    "source": "codes of the schema" if codes else "coding of the Excel dictionary"}
        if not codes and not labels:                 # a box read as written: the schemas keep 0 and 1 for no and yes
            return {"higher_means": "1 is yes, 0 is no", "polarity": "not_applicable", "basis": "coding",
                    "source": "docs/SCHEMA_SPEC.md, section 4: an item with the range 0 to 1 is a yes/no answer"}
    if kind == "continuous" and block.get("unit"):
        return {"higher_means": "a larger measured value (%s)" % block["unit"], "basis": "measurement", "source": "unit of the schema"}
    return {}


def incomplete_fields(record, block, instrument):
    """The fields of a variable that no source gives. A field that does not apply is not listed."""
    missing = []
    if block["level"] in ("key", "companion"):
        return missing
    if not record.get("meaning") and (not block.get("label") or GENERIC_LABEL.search(block["label"])):
        missing.append("meaning")
    if not record.get("construct"):
        missing.append("construct")
    direction = record.get("direction") or {}
    if not direction.get("polarity") and not direction.get("higher_means"):
        missing.append("direction")
    if block["kind"] in ("ordinal", "continuous") and block["type"] in ("item", "score", "number") and "range" not in block:
        missing.append("range")
    if block["kind"] == "ordinal" and block["type"] == "item" and not block.get("raw_codes") and not block.get("answer_labels"):
        missing.append("answer_labels")
    return missing


def differences_between(blocks):
    """What the cohorts do not say alike about a name they share: a list of {field, values}."""
    found = []
    for field in ["type", "unit", "range", "categories", "level", "table", "instrument"]:
        values = {cohort: block.get(field) for cohort, block in blocks.items()}
        if len({json.dumps(value, sort_keys=True, ensure_ascii=False) for value in values.values()}) > 1:
            found.append({"field": field, "values": values})
    methods = {cohort: (block.get("derivation") or {}).get("method") for cohort, block in blocks.items()}
    counts = {cohort: len((block.get("derivation") or {}).get("items") or []) for cohort, block in blocks.items()}
    if len(set(methods.values())) > 1 or len(set(counts.values())) > 1:
        found.append({"field": "derivation", "values": {cohort: "%s of %d" % (methods[cohort], counts[cohort]) if counts[cohort]
                                                        else methods[cohort] for cohort in blocks}})
    return found


# ---------------------------------------------------------------- putting the cohorts together

def instrument_records(contexts, annotations, constructs, catalogue, config):
    """One record per instrument name, with what each cohort says about it."""
    in_catalogue = {}
    for key, entry in catalogue.items():
        for cohort, schema_name in entry["schemas"].items():
            in_catalogue[(cohort, schema_name)] = {"entry": key, "domain": entry["domain"], "stack": entry["stack"],
                                                   "use": entry.get("use", []), "note": " ".join(entry["note"].split())}
    merged = {}
    for name, cohorts in config["tabs"].items():     # sheet of a workbook -> tab of the view "all cohorts"
        for cohort, sheets in cohorts.items():
            for sheet in sheets if isinstance(sheets, list) else [sheets]:
                merged[(cohort, sheet)] = name
    records = {}
    for cohort in COHORTS:
        context = contexts[cohort]
        for name, schema in context["schemas"].items():
            parent = schema.get("derived_from")
            note = annotations.get(name) or annotations.get(parent) or {}
            record = records.setdefault(name, {"id": name, "title": schema.get("title", name), "cohorts": {}, "variables": []})
            if "description" not in record:
                for field in ["description", "version", "reference", "reference_confidence", "respondent", "period", "sources", "flags"]:
                    if note.get(field) not in (None, "", []):
                        record[field] = note[field]
                key = note.get("construct")
                if isinstance(key, str) and key in constructs:
                    record["construct"] = key
                elif isinstance(key, dict):
                    record["construct_other"] = key.get("other")
                record["annotation_file"] = note.get("file")
                if parent:
                    record["derived_from"] = parent
            sheet = context["tab_of"][name]
            folder = schema["tab"]
            path = next(iter((MODULES[cohort].SCHEMAS).glob("*/%s.yaml" % (parent or schema.get("file", name)))), None)
            block = {"tab": sheet, "tab_all": merged.get((cohort, sheet), sheet), "section": schema.get("section", ""),
                     "level": schema.get("level", "visit"), "table": TABLE_OF_LEVEL[schema.get("level", "visit")],
                     "status": schema.get("status"), "notes": " ".join(str(schema.get("notes", "")).split()),
                     "schema": str(path.relative_to(ROOT)) if path else None}
            if "version" in schema:
                editions = (schema.get("defaults") or {}).get("versions") or []
                block["edition"] = {"column": schema["version"]["name"], "values": list(editions)}
            if (cohort, name) in in_catalogue:
                block["catalogue"] = in_catalogue[(cohort, name)]["entry"]
                record["common"] = in_catalogue[(cohort, name)]
            if name in context["differences"]:
                block["difference"] = " ".join(str(context["differences"][name]).split())
            record["cohorts"][cohort] = block
            record.setdefault("tab", block["tab_all"])
            if folder != sheet:
                block["export_table"] = folder
    for record in records.values():
        missing = [field for field in ["description", "respondent"] if field not in record]
        if "construct" not in record:
            missing.append("construct")
        if record.get("reference") != "not_applicable":
            missing += [field for field in ["reference", "version"] if field not in record]
        record["incomplete"] = missing
    return records


def slim(block, record):
    """A cohort block without what the record already says: a field that is absent has the value of the record."""
    kept = dict(block)
    for field in ["label", "level", "kind", "type", "unit", "instrument", "tab", "children", "computed_from", "companion_of"]:
        if field in kept and kept[field] == record.get(field):
            del kept[field]
    if set(kept.get("parents") or {}) == set(record.get("parents") or []):
        kept.pop("parents", None)
    kept.pop("section", None)
    return kept


def variable_records(contexts, instruments, annotations, constructs, shared):
    """One record per delivered name, with one block per cohort that delivers it."""
    names = {}
    for cohort in COHORTS:
        for name in contexts[cohort]["blocks"]:
            names.setdefault(name, []).append(cohort)
    records = {}
    for name, cohorts in names.items():
        blocks = {cohort: contexts[cohort]["blocks"][name] for cohort in cohorts}
        first_cohort, first = cohorts[0], blocks[cohorts[0]]
        instrument = instruments.get(first.get("instrument")) or {}
        note = annotations.get(first.get("instrument")) or annotations.get(instrument.get("derived_from")) or {}
        entry = annotation_of(note, name)
        record = {"id": name, "label": first.get("label", ""), "level": first["level"], "kind": first["kind"], "type": first["type"],
                  "instrument": first.get("instrument"), "tab": instrument.get("tab") or first.get("tab")}
        if first.get("unit"):
            record["unit"] = first["unit"]
        if entry.get("meaning"):
            record["meaning"] = entry["meaning"]
        elif first["level"] == "key":
            record["meaning"] = KEY_TEXT.get(name)
        key = entry.get("construct") if isinstance(entry.get("construct"), str) else instrument.get("construct")
        if key in constructs and first["level"] not in ("key", "companion"):
            record["construct"] = key
        record["direction"] = direction_of(name, first, note, contexts[first_cohort]["blocks"], annotations)
        if entry.get("cutoffs"):
            record["cutoffs"] = entry["cutoffs"]
        for field in ["parents", "children", "computed_from", "companion_of"]:
            union = list(dict.fromkeys(one for block in blocks.values() for one in (block.get(field) or [])))
            if union:
                record[field] = union
        harmonisation = {}
        common = instrument.get("common")
        if common:
            harmonisation.update({"stack": common["stack"], "recommended": name in common["use"]})
        if name in shared.get("names", {}):
            harmonisation["exception"] = shared["names"][name]
        columns = {column for block in blocks.values() for column in block.get("source", {}).get("columns", [])}
        notes = [shared["columns"][column] for column in sorted(columns) if column in shared.get("columns", {})]
        if notes:
            harmonisation["raw_column_note"] = notes
        if len(blocks) > 1:
            differences = differences_between(blocks)
            if differences:
                harmonisation["differences"] = differences
        if harmonisation:
            record["harmonisation"] = harmonisation
        record["incomplete"] = incomplete_fields(record, first, instrument)
        record["cohorts"] = {cohort: slim(block, record) for cohort, block in blocks.items()}
        records[name] = record
        if first.get("instrument") in instruments:
            for cohort, block in blocks.items():
                if block.get("instrument") in instruments and name not in instruments[block["instrument"]]["variables"]:
                    instruments[block["instrument"]]["variables"].append(name)
    return records


def count_patients(instruments, variables):
    """For each instrument and cohort: the patients who have its most filled variable, in all and at baseline."""
    for record in variables.values():
        for cohort, block in record["cohorts"].items():
            name = block.get("instrument", record.get("instrument"))
            if name not in instruments or cohort not in instruments[name]["cohorts"] or record["level"] in ("key", "companion"):
                continue
            target = instruments[name]["cohorts"][cohort]
            for field, key in [("patients", "max_patients"), ("baseline", "max_baseline")]:
                target[key] = max(target.get(key, 0), block.get("n", {}).get(field, 0))


def cohort_summary(cohort, context, config):
    """What the page says about a cohort as a whole."""
    stats = context["stats_file"]
    tabs = list(dict.fromkeys(context["tab_of"].values()))
    if context["workbook"]:                          # in the order of the workbook
        tabs = [sheet for sheet in context["workbook"]["sheets"] if sheet in tabs] + [tab for tab in tabs if tab not in context["workbook"]["sheets"]]
    summary = {"title": config["cohorts"][cohort], "extraction": config["extractions"][cohort],
               "excel_dictionary": config["thesauri"][cohort] if context["workbook"] else None, "tabs": tabs,
               "n_instruments": len(context["schemas"]), "n_variables": len(context["blocks"])}
    for field in ["n_patients", "n_visits", "visits", "tables", "computed", "git", "winsorised"]:
        if field in stats:
            summary[field] = stats[field]
    return summary


FIELD_NOTES = {
    "meta": "Where the file comes from and how to read it.",
    "cohorts.<cohort>": "Title, extraction file, Excel dictionary, tabs in the order of the workbook, patients, visits (label, planned month, number), tables (rows, columns).",
    "constructs.<key>": "area and label of each construct that a variable can measure (dictionary/constructs.yaml).",
    "flags.<code>": "severity and meaning of each flag code of facedata (docs/ARCHITECTURE.md, section 6).",
    "instruments.<name>": "title, description, version, reference, reference_confidence, respondent, construct, period, sources, flags (caveats written by hand), common (stack verdict across cohorts, variables to use, note), cohorts.<cohort> (tab, tab_all, section, level, table, schema file, notes of the schema, edition, difference from the other cohort), variables (ids), incomplete.",
    "variables.<id>": "One record per delivered column name. The id is the column name in the tables returned by facedata.<cohort>.load().",
    "variables.<id>.level": "item (counted in a score), subscore, score, standalone (belongs to no score), companion (censoring or edition column), key.",
    "variables.<id>.kind": "continuous, ordinal, binary, nominal, date, text or key: how to treat the values in an analysis. type is the type of the schema (number, item, band, category, date, time, text, score).",
    "variables.<id>.meaning": "Plain sentence written by hand; absent when only the label is known.",
    "variables.<id>.construct": "Key of constructs: of the variable when its annotation gives one, else of its instrument.",
    "variables.<id>.direction": "higher_means, polarity (worse, better, neutral, not_applicable), basis (stated, anchors, literature: written by hand with a source; formula, coding, measurement: derived from the schema), source, in_score (the score an item counts in, keyed same, reversed or recoded). Empty when no source says it.",
    "variables.<id>.cutoffs": "List of value, meaning, source, confidence. Only cut-offs that a project document gives.",
    "variables.<id>.parents / children / computed_from / companion_of": "The hierarchy: the scores that count this value, the values a score counts, the raw score a standard score is read from, the variable a companion column goes with.",
    "variables.<id>.harmonisation": "stack (yes, with care, no: can the cohorts be put under one another), recommended (named among the variables to use across cohorts), note, exception and raw_column_note (facedata/shared_names.yaml), differences (fields that the schemas of two cohorts do not give alike).",
    "variables.<id>.incomplete": "Names of the fields that no source gives: meaning, construct, direction, range, answer_labels.",
    "variables.<id>.cohorts.<cohort>": "What one cohort says. label, level, kind, type, unit, instrument and tab are written here only when they differ from the record: an absent field has the value of the record. table (data, patients, treatments or relatives: where the value is delivered, under the column name <id>), source.columns (raw columns of the extraction file named in cohorts.<cohort>.extraction; source.stored_score: the raw column of the score as stored), range, categories (delivered labels), raw_codes (raw text to delivered value), answer_labels (code to label, read in the Excel dictionary, not verified), missing_codes, edition (column and values: the visits on which it is read), derivation (method, formula in words, items, reverse, points, scale, min_items, norm_table, function, stored_in), reading (fields of the schema), rules (the same as sentences), excel (label and coding of the Excel dictionary when they say something else).",
    "variables.<id>.cohorts.<cohort>.n": "rows (rows of the table), valid (rows with a value), patients (patients with a value), patients_2plus (patients with a value at two visits or more), baseline (patients with a value in the baseline row).",
    "variables.<id>.cohorts.<cohort>.missing": "Percentages. all: rows of the table without a value. baseline: patients without a value in the baseline row (inclusion visit, completed by the screening visit, facedata.common.baseline). in_instrument: visits without a value among the visits that hold at least one value of the instrument.",
    "variables.<id>.cohorts.<cohort>.timepoints": "Number of values at each visit label, in visit order.",
    "variables.<id>.cohorts.<cohort>.stats": "all (every row) and baseline (one row per patient): n, mean, sd, min, max, p01, p05, p25, median, p75, p95, p99, n_distinct, at_minimum_pct and at_maximum_pct (share at each end of the range); for a date first_year and last_year; for a text n and n_distinct only. Values are not winsorised.",
    "variables.<id>.cohorts.<cohort>.dist": "all and baseline. kind bins: x holds the edges (one more than n) between the 1st and 99th percentile, the end bins hold the tails. kind levels: one count per answer or label. kind years: one count per year.",
    "variables.<id>.cohorts.<cohort>.flags": "Number of cells per flag code (see flags). censored: left and right. years: first and last year with a value. n_sites: number of centres with a value.",
    "counts": "A count from 1 to 4 is never written: it is given as -1 and means 'fewer than 5'. A variable with fewer than 5 values has no statistics, one with fewer than 20 no distribution.",
}


def write_json(dictionary, path):
    """The file with one line per instrument and per variable, so that a search for an id finds its whole record."""
    def line(value):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    parts = ["{"]
    for key in ["meta", "cohorts", "constructs", "flags"]:
        parts.append('"%s":%s,' % (key, line(dictionary[key])))
    for key in ["instruments", "variables"]:
        parts.append('"%s":{' % key)
        entries = list(dictionary[key].items())
        for position, (name, record) in enumerate(entries):
            parts.append("%s:%s%s" % (line(name), line(record), "," if position < len(entries) - 1 else ""))
        parts.append("}," if key == "instruments" else "}")
    parts.append("}")
    Path(path).write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_incomplete(dictionary, path):
    """The instruments and the variables with a field that no source gives, as a table to work through."""
    lines = ["what,id,instrument,tab,cohorts,level,kind,label,not_documented"]
    def cell(text):
        text = str(text or "")
        return '"%s"' % text.replace('"', '""') if any(mark in text for mark in ',"\n') else text
    for name, record in dictionary["instruments"].items():
        if record["incomplete"]:
            lines.append(",".join(cell(value) for value in ["instrument", name, name, record.get("tab"), " ".join(record["cohorts"]), "", "",
                                                             record["title"], " ".join(record["incomplete"])]))
    for name, record in dictionary["variables"].items():
        if record["incomplete"]:
            lines.append(",".join(cell(value) for value in ["variable", name, record.get("instrument"), record.get("tab"), " ".join(record["cohorts"]),
                                                             record["level"], record["kind"], record.get("label"), " ".join(record["incomplete"])]))
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build():
    """The whole dictionary as a dict."""
    config = read_yaml(FOLDER / "config.yaml")
    constructs = read_yaml(FOLDER / "constructs.yaml")
    annotations = read_annotations()
    catalogue = read_yaml(ROOT / "facedata" / "common_instruments.yaml", as_text=True)
    shared = read_yaml(ROOT / "facedata" / "shared_names.yaml", as_text=True)
    contexts = {}
    for cohort in COHORTS:
        stats_path = FOLDER / "stats" / (cohort + ".json")
        stats_file = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {"variables": {}, "visits": []}
        schemas = load_schemas(MODULES[cohort].SCHEMAS)
        workbook = read_workbook(ROOT / config["thesauri"][cohort])
        differences_path = MODULES[cohort].FOLDER / "differences.yaml"
        context = {"schemas": schemas, "stats_file": stats_file, "stats": stats_file["variables"], "visits": stats_file["visits"],
                   "workbook": workbook, "extraction": config["extractions"][cohort], "tab_of": tabs_of_cohort(schemas, workbook),
                   "differences": read_yaml(differences_path, as_text=True) if differences_path.exists() else {}}
        context["blocks"] = add_statistics(cohort_blocks(cohort, context), context)
        contexts[cohort] = context
    instruments = instrument_records(contexts, annotations, constructs, catalogue, config)
    variables = variable_records(contexts, instruments, annotations, constructs, shared)
    count_patients(instruments, variables)
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    meta = {"title": "FACE data dictionary", "generated": datetime.date.today().isoformat(), "git": git,
            "ids": "A variable id is the name of the column in the tables that facedata.<cohort>.load() returns "
                   "(data, patients, treatments, relatives). The raw column of the extraction is in cohorts.<cohort>.source.columns.",
            "how_to_load": "from facedata import bp; result = bp.load('<extraction>', instruments=[...]); result.data[['usubjid', 'visit', '<id>']]",
            "n_instruments": len(instruments), "n_variables": len(variables),
            "tabs_all": list(config["tabs"]), "fields": FIELD_NOTES}
    return {"meta": meta, "cohorts": {cohort: cohort_summary(cohort, contexts[cohort], config) for cohort in COHORTS},
            "constructs": constructs, "flags": flag_meanings(), "instruments": instruments, "variables": variables}


def main():
    dictionary = build()
    target = FOLDER / "face_dictionary.json"
    write_json(dictionary, target)
    incomplete = sum(bool(record["incomplete"]) for record in dictionary["variables"].values())
    write_incomplete(dictionary, FOLDER / "incomplete.csv")
    print("%d instruments, %d variables (%d with a field left empty), %.1f MB -> %s" % (
        len(dictionary["instruments"]), len(dictionary["variables"]), incomplete, target.stat().st_size / 1e6, target.relative_to(ROOT)))


if __name__ == "__main__":
    main()
