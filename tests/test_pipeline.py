"""The whole pipeline on a tiny hand-written extraction."""

import pandas as pd
import pytest

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


def test_nothing_disappears_silently(folder):
    """The invariant: every filled raw cell ends as a value or as a flag."""
    raw, keys, visit_flags = prepare_visits(read_extraction(folder / "extraction.tsv"))
    for schema in load_schemas(folder / "schemas").values():
        assert_invariant(raw, keys, schema)


def assert_invariant(raw, keys, schema):
    result = run_instrument(raw, keys, schema)
    for name, variable in schema["variables"].items():
        filled = (raw[variable["column"]].str.strip() != "") & (raw[variable["column"]] != EMPTY_DATE)
        if "versions" in variable:
            filled = filled & result["version"].isin(variable["versions"])
        flagged_rows = result["flags"].loc[result["flags"]["variable"] == name, "row"]
        lost = filled & result["values"][name].isna() & ~raw.index.isin(flagged_rows)
        assert lost.sum() == 0, f"{name}: {int(lost.sum())} cells lost without a flag"


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
