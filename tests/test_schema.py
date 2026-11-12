"""Schemas: how they are read, and what check_schema catches."""

from pathlib import Path

import pytest

from facedata.schema import check_cohort, check_schema, load_schema, load_schemas

PACKAGE = Path(__file__).parent.parent / "facedata"
GOOD = """
instrument: demo
title: Demo
tab: TEST
section: Demo
status: draft
defaults: {type: item, range: [0, 4]}
variables:
  it1: {label: First item}
  it2: {}
  answer: {type: category, codes: {No: no, Oui: yes, 0: no}, missing: {0000-00-00: not_recorded}}
  tot_stored: {column: tot, range: [0, 8], keep: false}
scores:
  total: {sum: [it1, it2], compare: tot_stored}
"""


def write(folder, name, text):
    path = folder / "tab" / (name + ".yaml")
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_every_schema_of_the_package_is_correct():
    for cohort in ["bp"]:
        schemas = load_schemas(PACKAGE / cohort / "schemas")
        assert len(schemas) > 0
        problems = check_cohort(schemas)
        for schema in schemas.values():
            problems = problems + check_schema(schema)
        assert problems == []


def test_values_are_read_as_text_and_numbers_are_converted(tmp_path):
    schema = load_schema(write(tmp_path, "demo", GOOD))
    assert schema["variables"]["answer"]["codes"] == {"No": "no", "Oui": "yes", "0": "no"}   # not False, not 0
    assert schema["variables"]["answer"]["missing"] == {"0000-00-00": "not_recorded"}
    assert schema["variables"]["it1"] == {"type": "item", "range": [0.0, 4.0], "label": "First item",
                                          "column": "it1", "keep": True}
    assert schema["variables"]["tot_stored"]["keep"] is False
    schema["file"] = "demo"
    assert check_schema(schema, columns={"it1", "it2", "answer", "tot"}) == []


def test_check_schema_names_each_problem(tmp_path):
    bad = GOOD.replace("it2: {}", "it2: {type: number, colour: red, derived_from: nothing}")
    bad = bad.replace("sum: [it1, it2]", "sum: [it1, it9]")
    schema = load_schema(write(tmp_path, "demo", bad))
    problems = " | ".join(check_schema(schema, columns={"it1", "it2", "answer"}))
    assert "unknown field 'colour'" in problems
    assert "derived_from must name a score that has compare" in problems
    assert "'it9' is not a variable" in problems
    assert "column 'tot' is not in the extraction" in problems


def test_check_cohort_finds_clashes_between_schemas(tmp_path):
    write(tmp_path, "demo", GOOD)
    write(tmp_path, "other", GOOD.replace("instrument: demo", "instrument: other"))
    problems = " | ".join(check_cohort(load_schemas(tmp_path)))
    assert "output 'it1' is in demo and in other" in problems
    assert "raw column 'tot' feeds several variables" in problems
