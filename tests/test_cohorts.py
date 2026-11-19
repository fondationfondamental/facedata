"""The same instrument in two cohorts: the same schema, or a difference that is written down.

A schema of FACE SZ that has the name of a FACE BP schema starts as a copy of
it (docs/ARCHITECTURE.md, section 9). The two must say the same thing, so
that the tables of the two cohorts can be put together. Where the SZ data
require another reading, facedata/sz/differences.yaml gives the reason.
"""

from itertools import combinations
from pathlib import Path

import yaml

from facedata.schema import load_schemas

PACKAGE = Path(__file__).parent.parent / "facedata"
COHORTS = ["bp", "sz", "dr", "asp"]
NUMBERS = {"number", "item", "band", "time", "score"}       # delivered as numbers: they can sit in one column
COMPARED = ["defaults", "variables", "scores", "version", "sign"]   # not the notes, the title, the tab or the status


def read_as_written(folder):
    """Every schema file of a cohort, as written: {instrument name: content}."""
    schemas = {}
    for path in sorted(Path(folder).glob("*/*.yaml")):
        with open(path, encoding="utf-8") as file:
            schema = yaml.load(file, Loader=yaml.BaseLoader)
        schemas[schema.get("instrument", path.stem)] = schema
    return schemas


def blocks_that_differ(first, second):
    """The names of the compared blocks that are not the same in the two schemas."""
    return [block for block in COMPARED if first.get(block) != second.get(block)]


def test_blocks_that_differ():
    one = {"notes": "BP", "variables": {"it1": {"range": ["0", "3"]}}, "scores": {"total": {"sum": ["it1"]}}}
    same = {"notes": "SZ, other numbers", "variables": {"it1": {"range": ["0", "3"]}}, "scores": {"total": {"sum": ["it1"]}}}
    other = {"notes": "SZ", "variables": {"it1": {"range": ["0", "4"]}}, "scores": {"total": {"sum": ["it1"]}}}
    assert blocks_that_differ(one, same) == []
    assert blocks_that_differ(one, other) == ["variables"]


def test_shared_instruments_are_the_same_in_bp_and_sz():
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    with open(PACKAGE / "sz" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    shared = sorted(set(bp) & set(sz))
    differing = {name: blocks_that_differ(bp[name], sz[name]) for name in shared}
    differing = {name: blocks for name, blocks in differing.items() if blocks}
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/sz/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is the BP one (or has another name)"


def test_shared_instruments_are_the_same_in_dr():
    """A DR schema is compared with the BP schema of the same name, or with the SZ one when BP has none."""
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    dr = read_as_written(PACKAGE / "dr" / "schemas")
    with open(PACKAGE / "dr" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    differing = {}
    for name in sorted(dr):
        reference = bp.get(name, sz.get(name))
        if reference is not None and blocks_that_differ(reference, dr[name]):
            differing[name] = blocks_that_differ(reference, dr[name])
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/dr/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is the BP or SZ one (or has another name)"


def test_shared_instruments_are_the_same_in_asp():
    """An ASP schema is compared with the BP schema of the same name, then the SZ one, then the DR one."""
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    dr = read_as_written(PACKAGE / "dr" / "schemas")
    asp = read_as_written(PACKAGE / "asp" / "schemas")
    with open(PACKAGE / "asp" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    differing = {}
    for name in sorted(asp):
        reference = bp.get(name, sz.get(name, dr.get(name)))
        if reference is not None and blocks_that_differ(reference, asp[name]):
            differing[name] = blocks_that_differ(reference, asp[name])
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/asp/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is that of the other cohort (or has another name)"


def delivered(cohort):
    """What a cohort delivers: {output name: what it is} and {raw column: the output names read from it}.

    What it is: the kind of value (number, category, date or text), the unit
    of a measurement ("" when the schema gives none), the level (visit,
    patient, list or relatives: the table it is delivered in), the labels
    of a category, and what each raw answer becomes (its label or number, or
    "(missing)" for a missing code).
    """
    outputs, readers = {}, {}
    for schema in load_schemas(PACKAGE / cohort / "schemas").values():
        level = schema.get("level", "visit")
        specs = {**schema["variables"], **schema.get("scores", {})}
        for name, spec in specs.items():
            if not spec["keep"]:
                continue
            kind = spec.get("type", "score")
            outputs[name] = {"kind": "number" if kind in NUMBERS else kind, "level": level,
                             "unit": spec.get("unit", "") if kind == "number" else None,
                             "labels": set(spec.get("codes", {}).values()) if kind == "category" else set(),
                             "codes": answers(spec), "range": hard_range(spec, kind)}
            for column in spec.get("columns", []):
                readers.setdefault(column, set()).add(name)
    return outputs, readers


def hard_range(spec, kind):
    """The hard limits of a measurement or a date as text ("0.0 to 90.0"), or None when it has none."""
    if kind not in NUMBERS | {"date"} or "range" not in spec:
        return None
    return " to ".join(str(limit) for limit in spec["range"])


def answers(spec):
    """What each raw answer of a variable becomes: {answer as written, lower case: label, number or "(missing)"}."""
    read = {str(token).lower().replace(" ", ""): "(missing)" for token in spec.get("missing") or {}}
    read.update({str(token).lower().replace(" ", ""): str(value) for token, value in (spec.get("codes") or {}).items()})
    return read


def what_differs(one, other):
    """The ways in which two delivered variables of the same name are not the same thing."""
    differing = [field for field in ["kind", "level"] if one[field] != other[field]]
    if one["unit"] is not None and other["unit"] is not None and one["unit"] != other["unit"]:
        differing.append("unit")                     # two measurements (a unit of None is not a measurement)
    # A form with more boxes is the same question; two lists that each have labels of their own are not.
    if not (one["labels"] <= other["labels"] or other["labels"] <= one["labels"]):
        differing.append("labels")
    # One variable, one hard limit: a value that one cohort removes as impossible must not be kept by another.
    if one["range"] is not None and other["range"] is not None and one["range"] != other["range"]:
        differing.append("range")
    # The same answer must become the same thing: 1 is not "right" in one cohort and "left" in the other.
    if any(one["codes"][token] != other["codes"][token] for token in set(one["codes"]) & set(other["codes"])):
        differing.append("codes")
    return differing


def test_what_differs():
    glucose = {"kind": "number", "level": "visit", "unit": "mmol/L", "labels": set(), "codes": {}, "range": "1.5 to 40.0"}
    assert what_differs(glucose, dict(glucose)) == []
    assert what_differs(glucose, {**glucose, "range": "1.0 to 40.0"}) == ["range"]
    assert what_differs(glucose, {**glucose, "range": None}) == []                  # no limit is not another limit
    assert hard_range({"range": [0.0, 90.0]}, "item") == "0.0 to 90.0" and hard_range({"range": [0.0, 1.0]}, "category") is None
    assert what_differs(glucose, {**glucose, "unit": "g/L", "level": "patient"}) == ["level", "unit"]
    short = {"kind": "category", "level": "visit", "unit": None, "labels": {"yes", "no"}, "codes": {"1": "yes", "2": "no"}, "range": None}
    assert what_differs(short, {**short, "labels": {"yes", "no", "unknown"}}) == []         # one more box
    assert what_differs(short, {**short, "labels": {"code_1", "code_2"}}) == ["labels"]
    assert what_differs(short, {**short, "codes": {"1": "no", "2": "yes"}}) == ["codes"]   # the same labels, read the other way
    assert what_differs(short, {**short, "codes": {"2": "(missing)", "9": "(missing)"}}) == ["codes"]
    assert answers({"codes": {"Oui": 1}, "missing": {"NSP": "unknown"}}) == {"oui": "1", "nsp": "(missing)"}


def test_the_cohorts_can_be_stacked():
    """Two cohorts give the same name to the same raw column, and a name holds the same thing in both.

    The tables of the cohorts are put together with pd.concat. What cannot be
    the same is written in facedata/shared_names.yaml, with its reason.
    """
    with open(PACKAGE / "shared_names.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader)
    other_names, other_content = {}, {}
    for first, second in combinations(COHORTS, 2):
        outputs, readers = delivered(first)
        outputs_2, readers_2 = delivered(second)
        for column in sorted(set(readers) & set(readers_2)):
            if not readers[column] & readers_2[column]:
                other_names.setdefault(column, []).append(f"{first} {sorted(readers[column])}, {second} {sorted(readers_2[column])}")
        for name in sorted(set(outputs) & set(outputs_2)):
            differing = what_differs(outputs[name], outputs_2[name])
            if differing:
                other_content.setdefault(name, []).append(f"{first} and {second}: {differing}")
    not_listed = {column: where for column, where in other_names.items() if column not in listed["columns"]}
    assert not_listed == {}, "one raw column, two names: give it one name, or add the reason to shared_names.yaml (columns)"
    not_listed = {name: where for name, where in other_content.items() if name not in listed["names"]}
    assert not_listed == {}, "one name, two contents: bring them together, or add the reason to shared_names.yaml (names)"
    no_longer_true = [column for column in listed["columns"] if column not in other_names]
    no_longer_true = no_longer_true + [name for name in listed["names"] if name not in other_content]
    assert no_longer_true == [], "listed in shared_names.yaml, but the cohorts now agree"


def test_a_time_has_a_range_of_hours():
    """The hard range is applied to times too: a time of day or a night's sleep is from 0 to 24 hours.

    A schema with item defaults would give a time the range of its items (0 to 3), so each time sets its own.
    """
    wrong = {}
    for cohort in COHORTS:
        for schema in load_schemas(PACKAGE / cohort / "schemas").values():
            for name, spec in schema["variables"].items():
                if spec["type"] == "time" and spec.get("range") != [0.0, 24.0]:
                    wrong[f"{cohort} {name}"] = spec.get("range")
    assert wrong == {}, "a time needs range: [0, 24]"
