"""The whole pipeline on a tiny hand-written extraction."""

import pandas as pd
import pytest

from facedata.parse import clean_text, own_cells
from facedata.pipeline import run_cohort, run_instrument
from facedata.read import prepare_visits, read_extraction, visit_month
from facedata.schema import load_schemas
from facedata.tokens import EMPTY_DATE

EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tit1\tit2\ttot\tglu\tglu_unit
P1\tV0\t2\t1\t2015-01-10\t01\t1\t2\t3\t5,2\tmmol/L
P1\tV6_mois\t3\t2\t2015-07-12\t01\t4\tNe sais pas\t4\t0.95\tg/L
P2\tV0\t2\t3\t2016-02-01\t02\t2\t2\t9\t<0.5\tg/L
P2\tV0\t2\t3\t2016-02-01\t02\t2\t2\t9\t<0.5\tg/L
P2\tV1_an\t4\t4\t1950-01-01\t02\tx\t3\t\t300\tmmol/L
"""

SCHEMA = """
instrument: demo
title: Demo
tab: TEST
section: Demo
status: draft
defaults: {type: item, range: [0, 4]}
variables:
  it1: {}
  it2: {}
  tot_stored: {column: tot, range: [0, 8], keep: false}
  glucose:
    column: glu
    unit_column: glu_unit
    type: number
    unit: mmol/L
    units:
      mmol/L: {factor: 1, expect: [2.5, 40]}
      g/L: {factor: 5.551, expect: [0.3, 2.5]}
    range: [1.5, 40]
    winsor: false
scores:
  total: {sum: [it1, it2], compare: tot_stored}
"""


@pytest.fixture
def folder(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "demo.yaml").write_text(SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(EXTRACTION, encoding="utf-8")
    return tmp_path


def flags_of(result, variable):
    lines = result.flags[result.flags["variable"] == variable]
    return sorted(zip(lines["usubjid"], lines["visit"], lines["flag"]))


def test_visit_month_is_read_from_the_label():
    assert visit_month("V0") == 0
    assert visit_month("V6_mois") == 6
    assert visit_month("V2_ans") == 24
    assert pd.isna(visit_month("screening"))


def test_the_tiny_extraction_end_to_end(folder):
    result = run_cohort(folder / "extraction.tsv", folder / "schemas")
    data = result.data

    assert len(data) == 4                                         # the duplicated visit record is dropped
    assert list(data.columns[:6]) == ["usubjid", "visit", "visit_order", "visit_month", "visit_date", "siteid"]
    assert list(data["visit_month"]) == [0, 6, 0, 12]
    assert pd.isna(data["visit_date"][3])                         # 1950-01-01 is a placeholder
    assert "tot_stored" not in data.columns                       # keep: false

    assert list(data["it1"][:3]) == [1, 4, 2] and pd.isna(data["it1"][3])
    assert list(data["total"][[0, 2]]) == [3, 4] and data["total"][[1, 3]].isna().all()
    assert list(data["glucose"][:3]) == pytest.approx([5.2, 0.95 * 5.551, 0.5 * 5.551])
    assert pd.isna(data["glucose"][3])                            # 300 mmol/L is impossible
    assert list(data["glucose_cens"]) == [0, 0, -1, 0]

    assert flags_of(result, "visit") == [("P2", "V0", "duplicate_row")]
    assert flags_of(result, "visit_date") == [("P2", "V1_an", "date_placeholder")]
    assert flags_of(result, "it1") == [("P2", "V1_an", "unparsed")]
    assert flags_of(result, "it2") == [("P1", "V6_mois", "missing_code")]
    assert flags_of(result, "tot_stored") == [("P2", "V0", "out_of_range")]
    assert flags_of(result, "glucose") == [("P1", "V0", "format_repaired"), ("P1", "V6_mois", "unit_converted"),
                                           ("P2", "V0", "censored_left"), ("P2", "V0", "unit_converted"),
                                           ("P2", "V1_an", "out_of_range")]
    unparsed = result.flags[result.flags["flag"] == "unparsed"].iloc[0]
    assert unparsed["raw"] == "x" and unparsed["value"] == "" and unparsed["severity"] == "danger"

    qc = result.qc.set_index("variable")
    assert list(qc.index) == ["it1", "it2", "glucose", "total"]
    assert qc.loc["glucose", "n_filled"] == 4 and qc.loc["glucose", "n_valid"] == 3
    assert qc.loc["glucose", "n_cens_left"] == 1 and qc.loc["glucose", "out_of_range"] == 1


def test_the_cohort_is_the_first_column_of_every_table(folder):
    result = run_cohort(folder / "extraction.tsv", folder / "schemas", cohort="demo")
    for table in [result.data, result.patients, result.flags, result.treatments, result.relatives]:
        assert table.columns[0] == "cohort" and set(table["cohort"]) <= {"demo"}
    assert "cohort" not in result.qc.columns                      # the QC table has one line per variable
    without = run_cohort(folder / "extraction.tsv", folder / "schemas")
    assert "cohort" not in without.data.columns


def test_nothing_disappears_silently(folder):
    """The invariant: every filled raw cell ends as a value or as a flag."""
    raw, keys, visit_flags = prepare_visits(read_extraction(folder / "extraction.tsv"))
    for schema in load_schemas(folder / "schemas").values():
        assert_invariant(raw, keys, schema)


def assert_invariant(raw, keys, schema):
    result = run_instrument(raw, keys, schema)
    for name, variable in schema["variables"].items():
        filled = pd.Series(False, index=raw.index)
        for column in variable["columns"]:
            text = clean_text(raw[column])           # a cell that held only a line break is empty
            if variable.get("shared"):               # a shared column: only the cells of this variable
                text = own_cells(text, variable)
            filled = filled | ((text != "") & (raw[column] != EMPTY_DATE))
        if "versions" in variable:
            filled = filled & result["version"].isin(variable["versions"])
        flagged_rows = result["flags"].loc[result["flags"]["variable"] == name, "row"]
        lost = filled & result["values"][name].isna() & ~raw.index.isin(flagged_rows)
        assert lost.sum() == 0, f"{name}: {int(lost.sum())} cells lost without a flag"
    for name, score in schema.get("scores", {}).items():     # a stored score that is not delivered: a score or a flag
        stored = schema["variables"].get(score.get("compare"), {"keep": True})
        if score["keep"] and not stored["keep"]:
            flagged_rows = result["flags"].loc[result["flags"]["variable"] == name, "row"]
            lost = result["values"][score["compare"]].notna() & result["values"][name].isna() & ~raw.index.isin(flagged_rows)
            assert lost.sum() == 0, f"{name}: {int(lost.sum())} stored scores lost without a flag"


def test_unknown_instrument_and_reused_winsor_limits(folder):
    with pytest.raises(ValueError):
        run_cohort(folder / "extraction.tsv", folder / "schemas", instruments=["nope"])
    # Let glucose be winsorised (the demo schema switches it off), then reuse limits from a qc table.
    path = folder / "schemas" / "tab" / "demo.yaml"
    path.write_text(SCHEMA.replace("winsor: false", "winsor: [0, 1]"), encoding="utf-8")
    first = run_cohort(folder / "extraction.tsv", folder / "schemas")
    assert first.qc.set_index("variable").loc["glucose", "winsor_high"] == pytest.approx(0.95 * 5.551)
    qc = first.qc.copy()
    qc.loc[qc["variable"] == "glucose", ["winsor_low", "winsor_high"]] = [3.0, 5.0]
    second = run_cohort(folder / "extraction.tsv", folder / "schemas", winsor_limits=qc)
    assert list(second.data["glucose"][:3]) == [5.0, 5.0, 3.0]
    assert flags_of(second, "glucose").count(("P1", "V0", "winsorised")) == 1


PATIENT_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tsexe\traison_new\traison_old\tdeces
P1\tV0\t2\t1\t2015-01-10\t01\tFeminin\t\tRefus du patient\t1000-01-01
P1\tV6_mois\t3\t2\t2015-07-12\t01\tFeminin\t\tRefus du patient\t1000-01-01
P2\tV0\t2\t3\t2016-02-01\t02\tMasculin\tAutre\tDéménagement\t2020-05-17
P2\tV1_an\t4\t4\t2017-02-01\t02\tMasculin\tAutre\tDéménagement\t2020-05-17
P3\tV0\t2\t5\t2018-03-01\t02\tMasculin\t\t\t1999-01-01
"""

PATIENT_SCHEMA = """
instrument: who
title: Who
tab: TEST
section: Who
status: draft
level: patient
variables:
  sex: {column: sexe, type: category, codes: {Feminin: female, Masculin: male}}
  end_reason:
    column: [raison_new, raison_old]
    type: category
    codes: {Refus du patient: refused, Déménagement: moved, Autre: other}
  death_date: {column: deces, type: date, range: [2008-01-01, 2030-12-31]}
"""


def test_patient_level_instrument(tmp_path):
    """One row per patient; a variable read from two columns; a date with a range."""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "who.yaml").write_text(PATIENT_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(PATIENT_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")

    assert list(result.data.columns) == ["usubjid", "visit", "visit_order", "visit_month", "visit_date", "siteid", "age"]
    patients = result.patients
    assert list(patients["usubjid"]) == ["P1", "P2", "P3"]
    assert list(patients["sex"]) == ["female", "male", "male"]
    assert list(patients["end_reason"][:2]) == ["refused", "other"]      # P2: the first column listed wins
    assert pd.isna(patients["end_reason"][2])
    assert patients["death_date"][1] == pd.Timestamp("2020-05-17")
    assert patients["death_date"][[0, 2]].isna().all()                   # a placeholder, and a date before 2008

    # Each flag is given once per patient, on the patient's first visit.
    assert flags_of(result, "death_date") == [("P1", "V0", "date_placeholder"), ("P3", "V0", "out_of_range")]
    assert flags_of(result, "end_reason") == [("P2", "V0", "column_conflict")]

    qc = result.qc.set_index("variable")                                 # counts are patients, not visit rows
    assert list(qc.loc["sex", ["n_rows", "n_filled", "n_valid"]]) == [3, 3, 3]
    assert list(qc.loc["end_reason", ["n_filled", "n_valid", "column_conflict"]]) == [2, 2, 1]
    assert list(qc.loc["death_date", ["n_filled", "n_valid", "out_of_range"]]) == [3, 1, 1]

    raw, keys, visit_flags = prepare_visits(read_extraction(tmp_path / "extraction.tsv"))
    for schema in load_schemas(tmp_path / "schemas").values():
        assert_invariant(raw, keys, schema)


def test_a_patient_level_flag_keeps_the_visit_and_the_text_of_its_cell(tmp_path):
    """A flag raised at a later visit is logged on that visit, with what was written there."""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "who.yaml").write_text(PATIENT_SCHEMA, encoding="utf-8")
    extraction = PATIENT_EXTRACTION + "P4\tV0\t2\t6\t2018-04-01\t02\tMasculin\t\t\t\n"
    extraction += "P4\tV1_an\t4\t7\t2019-04-01\t02\tFeminin\t\t\t1999-02-02\n"
    (tmp_path / "extraction.tsv").write_text(extraction, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")

    lines = result.flags[result.flags["usubjid"] == "P4"].set_index("variable")
    assert list(lines.loc["death_date", ["visit", "flag", "raw"]]) == ["V1_an", "out_of_range", "1999-02-02"]
    assert list(lines.loc["sex", ["visit", "flag", "raw"]]) == ["V1_an", "patient_value_varies", "Feminin"]
    assert result.patients.set_index("usubjid").loc["P4", "sex"] == "male"           # the first value is kept
    assert flags_of(result, "death_date").count(("P1", "V0", "date_placeholder")) == 1   # two visits, one flag


NORM_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tbrthdtc\ta\tb\tscaled
P1\tV0\t2\t1\t2015-06-15\t01\t1990-06-15\t3\t4\t10
P1\tV1_an\t4\t2\t2016-06-20\t01\t1990-06-15\t3\t4\t12
P2\tV0\t2\t3\t2015-06-15\t01\t1950-01-15\t9\t9\t13
P3\tV0\t2\t4\t\t01\t1980-01-15\t1\t1\t5
"""

NORM_SCHEMA = """
instrument: test
title: A test with norms
tab: TEST
section: Test
status: draft
defaults: {type: item, range: [0, 10]}
variables:
  a: {}
  b: {}
  scaled: {range: [1, 19], derived_from: scaled_check}
scores:
  total: {sum: [a, b]}
  scaled_check: {lookup: made_up, from: total, compare: scaled, keep: false}
"""

# A made-up norm table: two age bands, three cells each.
NORM_TABLE = """age_min,age_max,raw_min,raw_max,value
16,25,0,5,8
16,25,6,9,10
16,25,10,20,12
26,120,0,5,9
26,120,6,9,12
26,120,10,20,13
"""


def test_age_at_the_visit_and_norm_lookup(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "test.yaml").write_text(NORM_SCHEMA, encoding="utf-8")
    (tmp_path / "norms").mkdir()
    (tmp_path / "norms" / "made_up.csv").write_text(NORM_TABLE, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(NORM_EXTRACTION, encoding="utf-8")

    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path / "norms")
    assert list(result.data["age"][:3]) == pytest.approx([25.0, 26.015, 65.413], abs=0.001)   # years at the visit
    assert pd.isna(result.data["age"][3])                                   # no visit date, no age
    assert list(result.data["total"]) == [7, 7, 18, 2]
    assert list(result.data["scaled"]) == [10, 12, 13, 5]                   # delivered as stored
    assert "scaled_check" not in result.data.columns
    # Visit 1: age 25, total 7 -> 10. Visit 2: age 26 -> 12. Visit 3: total 18 -> 13. All agree.
    # Visit 4 has no age, so nothing can be read in the table.
    assert flags_of(result, "scaled_check") == [("P3", "V0", "norm_missing")]
    assert flags_of(result, "scaled") == []

    # Without the folder of norm tables, the check cannot run and says so on every row.
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path / "nowhere")
    assert [flag for patient, visit, flag in flags_of(result, "scaled_check")] == ["norm_missing"] * 4

    # A stored scaled score that the table contradicts is kept and doubted.
    text = NORM_EXTRACTION.replace("\t3\t4\t12", "\t3\t4\t11")
    (tmp_path / "extraction.tsv").write_text(text, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path / "norms")
    assert result.data["scaled"][1] == 11
    assert flags_of(result, "scaled") == [("P1", "V1_an", "derived_doubt")]
    assert ("P1", "V1_an", "score_mismatch") in flags_of(result, "scaled_check")


def test_a_custom_check_flags_its_variable(folder, monkeypatch):
    """checks: {variable: function of custom.py}; the rows where it returns True get check_failed."""
    from facedata import custom
    monkeypatch.setattr(custom, "first_item_above_two", lambda values: values["it1"] > 2, raising=False)
    path = folder / "schemas" / "tab" / "demo.yaml"
    path.write_text(SCHEMA + "checks:\n  it1: first_item_above_two\n", encoding="utf-8")
    result = run_cohort(folder / "extraction.tsv", folder / "schemas")
    assert ("P1", "V6_mois", "check_failed") in flags_of(result, "it1")
    assert result.data["it1"][1] == 4                        # the value is kept

    # The same function named for another variable: its cell is empty on that row, so no flag.
    path.write_text(SCHEMA + "checks:\n  it1: first_item_above_two\n  it2: first_item_above_two\n", encoding="utf-8")
    result = run_cohort(folder / "extraction.tsv", folder / "schemas")
    assert ("P1", "V6_mois", "check_failed") in flags_of(result, "it1")
    assert ("P1", "V6_mois", "check_failed") not in flags_of(result, "it2")

    path.write_text(SCHEMA + "checks:\n  it1: no_such_function\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no function 'no_such_function'"):
        run_cohort(folder / "extraction.tsv", folder / "schemas")


UNIT_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tldl\tchoice\tdefault
P1\tV0\t2\t1\t2015-01-10\t01\t1.2\tg/L\tmmol/L
P2\tV0\t2\t2\t2015-01-11\t01\t3.0\t\tmmol/L
P3\tV0\t2\t3\t2015-01-12\t01\t4\tinf\tmmol/L
"""

UNIT_SCHEMA = """
instrument: lipids
title: Lipids
tab: TEST
section: Lipids
status: draft
variables:
  ldl:
    type: number
    unit_column: [choice, default]
    unit: mmol/L
    units:
      mmol/L: {factor: 1, expect: [0.8, 10]}
      g/L: {factor: 2.586, expect: [0.3, 2.6]}
    censor_units: {inf: left}
    range: [0.3, 12]
    winsor: false
"""


def test_the_unit_label_can_sit_in_two_columns(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "lipids.yaml").write_text(UNIT_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(UNIT_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    assert list(result.data["ldl"]) == pytest.approx([1.2 * 2.586, 3.0, 4.0])
    # P1: the first column says g/L. P2: it is empty, so the second column is read.
    # P3: "inf" is a censoring mark, not a unit, and raises no unit flag.
    assert flags_of(result, "ldl") == [("P1", "V0", "unit_converted"), ("P3", "V0", "censored_left")]
    assert list(result.data["ldl_cens"]) == [0, 0, -1]


CELLS_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\twbc\tneu\tneu_unit\tglu\tglu_unit
P1\tV0\t2\t1\t2015-01-10\t01\t6.0\t3.6\tG/L\t5.2\tDéfaut
P2\tV0\t2\t2\t2015-01-11\t01\t8.0\t60\tG/L\t\t
P3\tV0\t2\t3\t2015-01-12\t01\t300\t55\t%\t\t
"""

CELLS_SCHEMA = """
instrument: cells
title: Cells
tab: TEST
section: Cells
status: draft
defaults: {type: number, winsor: false}
variables:
  leukocytes: {column: wbc, range: [0.5, 100]}
  neutrophils:
    column: neu
    unit_column: neu_unit
    unit: G/L
    units:
      G/L: {factor: 1, expect: [0, 25]}
      "%": {percent_of: leukocytes, expect: [0, 100]}
    range: [0, 25]
  glucose:
    column: glu
    unit_column: glu_unit
    ignore_units: [défaut]
    unit: mmol/L
    units:
      mmol/L: {factor: 1, expect: [2.5, 40]}
      g/L: {factor: 5.551, expect: [0.3, 2.5]}
    range: [1.5, 40]
"""


def test_a_percentage_and_a_label_that_says_nothing(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "cells.yaml").write_text(CELLS_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(CELLS_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    # P2: 60 G/L is impossible, so it is 60% of 8.0. P3: the leukocytes are out of range,
    # so the percentage cannot be converted.
    assert list(result.data["neutrophils"][:2]) == pytest.approx([3.6, 4.8])
    assert pd.isna(result.data["neutrophils"][2])
    assert flags_of(result, "neutrophils") == [("P2", "V0", "unit_inferred"), ("P3", "V0", "unit_unknown")]
    assert flags_of(result, "leukocytes") == [("P3", "V0", "out_of_range")]
    # The label "Défaut" is ignored: the glucose is read by its size, with no flag.
    assert result.data["glucose"][0] == 5.2
    assert flags_of(result, "glucose") == []


SHARED_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tstd
P1\tV0\t2\t1\t2015-01-10\t01\t25 - 50
P2\tV0\t2\t2\t2015-01-11\t01\t50
P3\tV0\t2\t3\t2015-01-12\t01\t1.25
P4\tV0\t2\t4\t2015-01-13\t01\t-0.40
P5\tV0\t2\t5\t2015-01-14\t01\tNaN
P6\tV0\t2\t6\t2015-01-15\t01\t<1
"""

SHARED_SCHEMA = """
instrument: recall
title: Recall
tab: TEST
section: Recall
status: draft
variables:
  recall_band: {column: std, type: band, limits: [1, 5, 25, 50, 75, 95, 99], shared: true}
  recall_z: {column: std, type: number, range: [-5, 5], shared: true, winsor: false}
"""


def test_a_column_shared_by_a_band_and_a_z_score(tmp_path):
    """Each cell goes to one of the two variables, and none is lost."""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "recall.yaml").write_text(SHARED_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(SHARED_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    band, z = result.data["recall_band"], result.data["recall_z"]
    assert list(band[[0, 1, 5]]) == [25, 50, 0]              # a band, a limit, the band under the first limit
    assert list(z[[2, 3]]) == [1.25, -0.40]                  # written with a decimal point
    assert band[[2, 3, 4]].isna().all() and z[[0, 1, 4, 5]].isna().all()
    assert flags_of(result, "recall_band") == []             # the z-scores are not its cells
    assert flags_of(result, "recall_z") == [("P5", "V0", "missing_code")]
    qc = result.qc.set_index("variable")
    assert (qc.loc["recall_band", "n_filled"], qc.loc["recall_z", "n_filled"]) == (3, 3)
    raw, keys, visit_flags = prepare_visits(read_extraction(tmp_path / "extraction.tsv"))
    assert_invariant(raw, keys, load_schemas(tmp_path / "schemas")["recall"])

    # With z_range the band also takes the z-scores, and every patient is on one scale.
    both = SHARED_SCHEMA.replace("limits: [1, 5, 25, 50, 75, 95, 99], shared: true", "limits: [1, 5, 25, 50, 75, 95, 99], shared: true, z_range: [-5, 5]")
    (tmp_path / "schemas" / "tab" / "recall.yaml").write_text(both, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    assert list(result.data["recall_band"][[0, 1, 2, 3, 5]]) == [25, 50, 75, 25, 0]    # 1.25 is the 89th percentile, -0.40 the 34th
    assert list(result.data["recall_z"][[2, 3]]) == [1.25, -0.40]                       # the z-scores are still delivered
    assert flags_of(result, "recall_band") == [("P3", "V0", "band_from_z"), ("P4", "V0", "band_from_z"), ("P5", "V0", "missing_code")]
    assert_invariant(raw, keys, load_schemas(tmp_path / "schemas")["recall"])


BAND_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tbrthdtc\terr\tschool
P1\tV0\t2\t1\t2015-01-10\t01\t1990-01-15\t0\t15
P2\tV0\t2\t2\t2015-01-11\t01\t1990-01-15\t2\t15
P3\tV0\t2\t3\t2015-01-12\t01\t1990-01-15\t0\t
"""

BAND_SCHEMA = """
instrument: trail
title: A test with a table of bands
tab: TEST
section: Trail
status: draft
variables:
  errors: {column: err, type: item, range: [0, 20]}
  schooling: {column: school, type: number, range: [0, 30], winsor: false, keep: false}
scores:
  errors_band: {lookup: made_up_bands, from: errors, by: schooling}
"""

# A made-up table: with no error the patient is in the band that starts at 25, or in a higher one.
BAND_TABLE = """age_min,age_max,by_min,by_max,raw_min,raw_max,value,cens
0,99,10,99,0,0,25,1
0,99,10,99,1,99,7,0
"""


def test_a_band_read_in_a_norm_table(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "trail.yaml").write_text(BAND_SCHEMA, encoding="utf-8")
    (tmp_path / "norms").mkdir()
    (tmp_path / "norms" / "made_up_bands.csv").write_text(BAND_TABLE, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(BAND_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path / "norms")
    assert list(result.data["errors_band"][:2]) == [25, 7]
    assert list(result.data["errors_band_cens"]) == [1, 0, 0]
    assert pd.isna(result.data["errors_band"][2])            # no years of education: nothing can be read
    assert flags_of(result, "errors_band") == [("P1", "V0", "censored_right"), ("P3", "V0", "norm_missing")]
    assert "schooling" not in result.data.columns


RECALL_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tbrthdtc\twords\tstd
P1\tV0\t2\t1\t2015-01-10\t01\t1990-01-15\t16\t99
P2\tV0\t2\t2\t2015-01-11\t01\t1990-01-15\t10\t50 - 75
P3\tV0\t2\t3\t2015-01-12\t01\t1990-01-15\t12\t0.80
P4\tV0\t2\t4\t2015-01-13\t01\t1990-01-15\t\t50
"""

RECALL_SCHEMA = """
instrument: words
title: A recall with a table of bands
tab: TEST
section: Words
status: draft
variables:
  words: {column: words, type: item, range: [0, 16]}
  words_band: {column: std, type: band, limits: [1, 5, 25, 50, 75, 95, 99], lookup: made_up_recall, from: words, shared: true, z_range: [-5, 5]}
  words_z: {column: std, type: number, range: [-5, 5], shared: true, winsor: false}
"""

# A made-up table: a perfect recall is in the band that starts at 75, or in a higher one.
RECALL_TABLE = """age_min,age_max,raw_min,raw_max,value,cens
0,99,0,9,5,0
0,99,10,15,25,0
0,99,16,16,75,1
"""


def test_a_band_read_again_in_a_norm_table(tmp_path):
    """Where the cell holds a percentile, the band comes from the raw score and the table, not from the cell."""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "words.yaml").write_text(RECALL_SCHEMA, encoding="utf-8")
    (tmp_path / "norms").mkdir()
    (tmp_path / "norms" / "made_up_recall.csv").write_text(RECALL_TABLE, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(RECALL_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path / "norms")
    assert list(result.data["words_band"][:3]) == [75, 25, 75]   # 99 and "50 - 75" are not read; 0.80 is the 79th percentile
    assert list(result.data["words_band_cens"]) == [1, 0, 0, 0]
    assert pd.isna(result.data["words_band"][3])                 # a percentile cell, but no raw score to look up
    assert flags_of(result, "words_band") == [("P1", "V0", "censored_right"), ("P3", "V0", "band_from_z"),
                                              ("P4", "V0", "norm_missing")]
    raw, keys, visit_flags = prepare_visits(read_extraction(tmp_path / "extraction.tsv"))
    assert_invariant(raw, keys, load_schemas(tmp_path / "schemas")["words"])


FORMS_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tq1\tlong_score\tother_long\tother_item
P1\tV0\t2\t1\t2015-01-10\t01\t2\t1.5\t\t
P2\tV0\t2\t2\t2015-01-11\t01\t3\t\t4\t1
P3\tV0\t2\t3\t2022-01-12\t01\t1\t\t\t1
P4\tV0\t2\t4\t2015-01-13\t01\t\t0.5\t\t
P5\tV0\t2\t5\t2022-01-14\t01\t\t\t4\t1
P6\tV0\t2\t6\t2022-01-15\t01\t2\t\t\t
"""

FORMS_VERSION = """
version:
  name: quest_form
  filled:
    long: [long_score, other_long]
    short: [q1, other_item]
"""

# The short form is loaded first: the long form then completes the version column.
FORMS_SHORT = """
instrument: a_short
title: Short form
tab: TEST
section: Forms
status: draft
""" + FORMS_VERSION + """
defaults: {type: item, range: [0, 3], versions: [short]}
variables:
  short_q1: {column: q1}
"""

FORMS_LONG = """
instrument: b_long
title: Long form
tab: TEST
section: Forms
status: draft
""" + FORMS_VERSION + """
defaults: {type: item, range: [0, 3], versions: [long]}
variables:
  long_q1: {column: q1}
  long_stored_score: {column: long_score, type: number, winsor: false}
"""


def test_two_forms_split_by_the_questionnaires_of_the_same_visit(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "a_short.yaml").write_text(FORMS_SHORT, encoding="utf-8")
    (tmp_path / "schemas" / "tab" / "b_long.yaml").write_text(FORMS_LONG, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(FORMS_EXTRACTION, encoding="utf-8")
    data = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas").data
    # P1: a score of the long form. P2: an item that only the long questionnaires have. P3: neither.
    # P4: the score alone, which only the long schema reads. P5: the other questionnaire alone.
    assert list(data["quest_form"][:4]) == ["long", "long", "short", "long"]
    assert pd.isna(data["quest_form"][4])
    assert data["quest_form"][5] == "short"
    # Each answer is in the columns of its own form, never in both.
    assert list(data["long_q1"][:2]) == [2, 3] and data["long_q1"][2:].isna().all()
    assert data["short_q1"][2] == 1 and data["short_q1"][5] == 2 and data["short_q1"][[0, 1, 3, 4]].isna().all()
    assert data["long_stored_score"][3] == 0.5


ASKED_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tgate\tbox\tage
P1\tV0\t2\t1\t2015-01-10\t01\tY\t1\t20
P2\tV0\t2\t2\t2015-01-11\t01\tY\t0\t
P3\tV0\t2\t3\t2015-01-12\t01\tN\t\t
P4\tV0\t2\t4\t2015-01-13\t01\tU\t\t
P5\tV0\t2\t5\t2015-01-14\t01\t\t\t
P6\tV0\t2\t6\t2015-01-15\t01\tY\t\t
"""

ASKED_SCHEMA = """
instrument: asked
title: Asked
tab: TEST
section: Asked
status: draft
variables:
  disorder: {column: gate, type: item, range: [0, 1], codes: {Y: 1, N: 0}, missing: {U: unknown}}
  panic: {column: box, type: item, range: [0, 1], asked_if: disorder}
  panic_onset_age: {column: age, type: item, range: [0, 90]}
"""


def test_a_question_asked_only_after_a_yes(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "asked.yaml").write_text(ASKED_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(ASKED_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    data, qc = result.data, result.qc.set_index("variable")
    # P3: no disorder, so no panic disorder. P4 (unknown), P5 (form not filled) and P6 (yes, box empty) stay missing.
    assert list(data["panic"][:3]) == [1, 0, 0] and data["panic"][3:].isna().all()
    assert data["panic_onset_age"][1:].isna().all()              # a detail has no value after a "no"
    assert flags_of(result, "panic") == []                       # nothing was changed, nothing is flagged
    assert (qc.loc["panic", "n_filled"], qc.loc["panic", "n_valid"]) == (3, 3)


def test_centre_codes_have_two_digits():
    """One extraction writes the centre codes as numbers ("4"), the others as two characters ("04")."""
    raw = pd.DataFrame({"usubjid": ["a", "b"], "visit": ["V0", "V0"], "id_visit": ["2", "2"], "visitnum": ["1", "2"],
                        "svdtc": ["2015-01-01", "2015-01-02"], "siteid": ["4", "12"]})
    raw, keys, flags = prepare_visits(raw)
    assert list(keys["siteid"]) == ["04", "12"]


def test_a_visit_dated_before_the_cohort_opened_has_no_date_and_no_age():
    raw = pd.DataFrame({"usubjid": ["a", "b", "c"], "visit": ["V0", "V0", "V0"], "id_visit": ["2", "2", "2"],
                        "visitnum": ["1", "2", "3"], "svdtc": ["2001-05-01", "2015-01-02", "2999-01-01"], "siteid": ["01", "01", "01"],
                        "brthdtc": ["1990-06-15", "2020-06-15", "1990-06-15"]})
    raw, keys, flags = prepare_visits(raw, first_day="2010-01-01")
    assert list(keys["visit_date"].isna()) == [True, False, True]     # before the cohort, and in the future
    assert keys["age"].isna().all()                                   # the second patient would be minus five years old
    out_of_range = flags[flags["flag"] == "out_of_range"]
    assert sorted(zip(out_of_range["row"], out_of_range["variable"])) == [(0, "visit_date"), (1, "age"), (2, "visit_date")]


def test_winsorising_can_be_switched_off(folder):
    clipped = run_cohort(folder / "extraction.tsv", folder / "schemas")
    as_is = run_cohort(folder / "extraction.tsv", folder / "schemas", winsorise_values=False)
    assert "winsorised" not in set(as_is.flags["flag"])
    assert as_is.qc["winsor_low"].isna().all()
    assert as_is.data.shape == clipped.data.shape


LISTS_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tany\tect\ttms\tect_n\tmethod\tfirearm\tfirst\tlater\tn_later
P1\tV0\t2\t1\t2015-01-10\t01\tOui\t\tOui\t\tNoyade\tPas de dommage\t2014-05-15\tNon\t
P2\tV0\t2\t2\t2015-01-11\t01\tOui\t\t\t\tArme à feu\tPas de dommage\t2015-01-11\tNon\t
P3\tV0\t2\t3\t2015-01-12\t01\tOui\tNe sais pas\tOui\t\t\tPas de dommage\t2016-03-15\tOui\t2
P4\tV0\t2\t4\t2022-06-12\t01\tNon\t\t\t\t\t\t\tNon\t
"""

LISTS_SCHEMA = """
instrument: lists
title: Lists
tab: TEST
section: Lists
status: draft
defaults: {type: item, range: [0, 1]}
variables:
  any_treatment: {column: any, codes: {Oui: 1, Non: 0}}
  ect: {codes: {Oui: 1, Non: 0}, asked_if: any_treatment, box_list: kinds}
  tms: {codes: {Oui: 1, Non: 0}, asked_if: any_treatment, box_list: kinds}
  ect_sessions: {column: ect_n, range: [0, 365], asked_if: ect}
  method: {type: category, codes: {Noyade: drowning, Arme à feu: firearm}}
  firearm_lethality: {column: firearm, type: category, codes: {Pas de dommage: no_damage}, shown_if: {method: [firearm]}}
  first_date: {column: first, type: date, range: [1920-01-01, 2026-12-31], before_visit: true}
  gate_later: {column: later, codes: {Oui: 1, Non: 0}, keep: false, doubt: {period: [2022-01-01, 2023-12-31], remove: true}}
  count_later: {column: n_later, range: [0, 50], asked_if: gate_later}
"""


def test_boxes_of_a_list_hidden_answers_and_dates_before_the_visit(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "lists.yaml").write_text(LISTS_SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(LISTS_EXTRACTION, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    data = result.data
    # P1 ticked tms only: ect is a no, and its sessions follow. P2 ticked nothing: unknown.
    # P3 does not know about ect: it stays missing. P4 said no: every box is 0.
    assert list(data["ect"][[0, 3]]) == [0, 0] and data["ect"][[1, 2]].isna().all()
    assert list(data["ect_sessions"][[0, 3]]) == [0, 0] and data["ect_sessions"][[1, 2]].isna().all()
    assert flags_of(result, "ect") == [("P3", "V0", "missing_code")]
    # The lethality of a firearm is shown only for a firearm: the drowning's and the empty method's are defaults.
    assert data["firearm_lethality"][1] == "no_damage" and data["firearm_lethality"][[0, 2]].isna().all()
    assert flags_of(result, "firearm_lethality") == [("P1", "V0", "not_shown"), ("P3", "V0", "not_shown")]
    # A first date on the day of the visit or later is impossible.
    assert data["first_date"][0] == pd.Timestamp("2014-05-15") and data["first_date"][[1, 2]].isna().all()
    assert flags_of(result, "first_date") == [("P2", "V0", "out_of_range"), ("P3", "V0", "out_of_range")]
    # A "no" of a removed period is no answer: nothing after it becomes 0, and the empty cell is not flagged.
    assert list(data["count_later"][:3]) == [0, 0, 2] and pd.isna(data["count_later"][3])
    assert flags_of(result, "count_later") == []


def test_a_time_outside_its_hours_is_impossible(tmp_path):
    """The hard range holds for a time too: 90 hours of sleep and a bedtime of 25:30 end out_of_range (BP D130)."""
    schema = """
instrument: sleep
title: Sleep
tab: TEST
section: Sleep
status: draft
defaults: {type: item, range: [0, 3]}
variables:
  bedtime: {column: bed, type: time, range: [0, 24]}
  sleep_hours: {column: sleep, type: time, range: [0, 24]}
"""
    extraction = "usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tbed\tsleep\nP1\tV0\t2\t1\t2015-01-10\t01\t23:30\t7:30\nP2\tV0\t2\t2\t2016-02-01\t02\t25:30\t90:00\nP3\tV0\t2\t3\t2016-03-01\t02\t24:00\t\n"
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "sleep.yaml").write_text(schema, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(extraction, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    data = result.data.set_index("usubjid")
    assert list(data["bedtime"]) == pytest.approx([23.5, float("nan"), 24.0], nan_ok=True)    # 24:00 is midnight
    assert data["sleep_hours"].notna().tolist() == [True, False, False]
    assert flags_of(result, "bedtime") == [("P2", "V0", "out_of_range")]
    assert flags_of(result, "sleep_hours") == [("P2", "V0", "out_of_range")]


def test_an_empty_box_with_a_typed_count_is_not_a_no(tmp_path):
    """A box beside a ticked one is a no, unless a count that hangs on it was typed: it is shown only after a yes."""
    extraction = ("usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tany\tect\ttms\tect_n\n"
                  "P1\tV0\t2\t1\t2015-01-10\t01\tOui\t\tOui\t\n"         # tms ticked, ect left empty: a no, 0 sessions
                  "P2\tV0\t2\t2\t2015-01-11\t01\tOui\t\tOui\t3\n"        # the same, but 3 sessions were typed for ect
                  "P3\tV0\t2\t3\t2015-01-12\t01\tOui\tOui\t\t4\n")       # ect ticked: its 4 sessions as written
    schema = """
instrument: boxes
title: Boxes
tab: TEST
section: Boxes
status: draft
defaults: {type: item, range: [0, 1]}
variables:
  any_treatment: {column: any, codes: {Oui: 1, Non: 0}}
  ect: {codes: {Oui: 1, Non: 0}, asked_if: any_treatment, box_list: kinds}
  tms: {codes: {Oui: 1, Non: 0}, asked_if: any_treatment, box_list: kinds}
  ect_sessions: {column: ect_n, range: [0, 365], asked_if: ect}
"""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "boxes.yaml").write_text(schema, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(extraction, encoding="utf-8")
    data = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas").data
    assert data["ect"][0] == 0 and data["ect_sessions"][0] == 0
    assert pd.isna(data["ect"][1]) and data["ect_sessions"][1] == 3          # left as written: not turned into a no
    assert data["ect"][2] == 1 and data["tms"][2] == 0 and data["ect_sessions"][2] == 4


USES = """
instrument: aaa_doubled
title: Doubled
tab: TEST
section: Doubled
status: draft
uses: [total]
defaults: {type: item, range: [0, 20]}
variables:
  dbl_stored: {column: dbl, keep: false}
scores:
  doubled: {sum: [total], scale: [2, 0], range: [0, 20], compare: dbl_stored}
"""

USES_EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tit1\tit2\ttot\tglu\tglu_unit\tdbl
P1\tV0\t2\t1\t2016-01-10\t01\t1\t2\t3\t5\tmmol/L\t6
P2\tV0\t2\t2\t2016-02-01\t02\t2\t2\t4\t5\tmmol/L\t9
P3\tV0\t2\t3\t2016-03-01\t02\t1\t\t1\t5\tmmol/L\t4
"""


def test_a_score_can_add_up_the_scores_of_another_schema(folder):
    """A schema with `uses` runs last (its file name sorts first here) and reads the delivered scores of the others."""
    (folder / "schemas" / "tab" / "aaa_doubled.yaml").write_text(USES, encoding="utf-8")
    (folder / "extraction.tsv").write_text(USES_EXTRACTION, encoding="utf-8")
    result = run_cohort(folder / "extraction.tsv", folder / "schemas")
    data = result.data.set_index("usubjid")
    assert data["total"].fillna(-1).tolist() == [3, 4, -1]          # P3 lacks an item
    assert data["doubled"].fillna(-1).tolist() == [6, 8, -1]
    assert "total" in result.data.columns and "dbl_stored" not in result.data.columns
    assert flags_of(result, "doubled") == [("P2", "V0", "score_mismatch"), ("P3", "V0", "score_not_recomputed")]
    only = run_cohort(folder / "extraction.tsv", folder / "schemas", instruments=["aaa_doubled"])
    assert only.data["doubled"].isna().all()                        # the schema it uses is not loaded: nothing to add up
