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
                                          "column": "it1", "columns": ["it1"], "keep": True}
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


UNITS = """
instrument: cells
title: Cells
tab: TEST
section: Cells
status: draft
defaults: {type: number}
variables:
  part:
    unit: G/L
    units:
      G/L: {factor: 1, expect: [0, 25]}
      "%": {percent_of: whole, expect: [0, 100]}
      other: {expect: [0, 1]}
    unit_rule: no_such_rule
    range: [0, 25]
  whole: {range: [0, 100]}
"""


def test_check_schema_checks_the_units(tmp_path):
    problems = " | ".join(check_schema(load_schema(write(tmp_path, "cells", UNITS))))
    assert "percent_of must name a number with a range, listed before part" in problems
    assert "unit other needs a factor or percent_of" in problems
    assert "there is no function 'no_such_rule'" in problems


BANDS = """
instrument: bands
title: Bands
tab: TEST
section: Bands
status: draft
variables:
  a_band: {column: std, type: band, limits: [50, 25], shared: true, lookup: some_table}
  a_z: {column: std, type: number, shared: true, z_range: [-5, 5]}
  a_copy: {column: std, type: number, shared: true}
"""


def test_check_schema_checks_bands_and_shared_columns(tmp_path):
    write(tmp_path, "bands", BANDS)
    schemas = load_schemas(tmp_path)
    assert "a_band: a band needs limits, numbers in rising order" in " | ".join(check_schema(schemas["bands"]))
    assert "raw column 'std' must be shared by one band and one number" in " | ".join(check_cohort(schemas))
    assert "a_z: z_range must be [low, high], on a band" in " | ".join(check_schema(schemas["bands"]))
    assert "a_band: lookup and from go together" in " | ".join(check_schema(schemas["bands"]))


def test_a_variable_that_is_not_delivered_may_read_a_delivered_column(tmp_path):
    """The years of education are delivered by one schema and read again by another, for a norm table."""
    write(tmp_path, "demo", GOOD)
    helper = GOOD.replace("instrument: demo", "instrument: other").replace("it1: {label: First item}", "it9: {column: it1, keep: false}")
    helper = helper.replace("it2: {}", "it8: {}").replace("answer:", "answer2:").replace("sum: [it1, it2]", "sum: [it9, it8], by: it9")
    helper = helper.replace("tot_stored: {column: tot,", "tot2: {column: tot2,").replace("total:", "total2:").replace("compare: tot_stored", "compare: tot2")
    write(tmp_path, "other", helper)
    schemas = load_schemas(tmp_path)
    problems = " | ".join(check_cohort(schemas) + check_schema(schemas["other"]))
    assert "raw column" not in problems                      # it9 is not delivered: it may read it1 again
    assert "total2: by goes with lookup" in problems


DOUBT = """
instrument: doubt
title: Doubt
tab: TEST
section: Doubt
status: draft
defaults:
  type: item
  range: [0, 1]
  doubt: {period: [2022-01-01, 2023-12-31], values: [1, last_week], note: why}
variables:
  good: {}
  no_period: {doubt: {values: [1]}}
  backwards: {doubt: {period: [2023-12-31, 2022-01-01]}}
  not_dates: {doubt: {period: [1, 2]}}
  extra_field: {doubt: {period: [2022-01-01, 2023-12-31], reason: why}}
"""


def test_a_doubtful_period_is_read_as_dates_and_checked(tmp_path):
    schema = load_schema(write(tmp_path, "doubt", DOUBT))
    good = schema["variables"]["good"]["doubt"]
    assert [str(day.date()) for day in good["period"]] == ["2022-01-01", "2023-12-31"]
    assert good["values"] == [1.0, "last_week"] and good["note"] == "why"
    problems = check_schema(schema)
    for name in ["no_period", "backwards", "not_dates", "extra_field"]:
        assert f"doubt: {name}: doubt needs a period [first day, last day]" in " | ".join(problems), name
    assert len(problems) == 4


ASKED = """
instrument: asked
title: Asked
tab: TEST
section: Asked
status: draft
defaults: {type: item, range: [0, 1]}
variables:
  too_early: {asked_if: disorder}
  disorder: {}
  good: {asked_if: disorder}
  no_such: {asked_if: nothing}
  a_count: {type: number, range: [0, 50], asked_if: disorder}
  a_rating: {range: [1, 5], asked_if: disorder}
  after_a_count: {asked_if: a_count}
"""


def test_asked_if_names_a_yes_no_question_listed_before(tmp_path):
    problems = check_schema(load_schema(write(tmp_path, "asked", ASKED)))
    # A box or a count may be asked after a yes/no question; a rating that cannot be 0 may not,
    # and the question named must itself be a yes/no.
    for name in ["too_early", "no_such", "a_rating", "after_a_count"]:
        assert f"asked: {name}: asked_if must name a yes/no item listed before" in " | ".join(problems), name
    assert len(problems) == 4
