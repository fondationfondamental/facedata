"""Cells that hold lists: one row per patient and item, names looked up in a table, columns of a visit."""

from pathlib import Path

import pandas as pd

from facedata import custom
from facedata.pipeline import run_cohort
from facedata.schema import check_schema, load_schemas

# Made-up medications. P1 has the same lists on its two rows; P3 has no list.
EXTRACTION = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tnames\tstarts\tends\tper_day
P1\tV0\t2\t1\t2020-01-10\t01\t['CALMIX 10 mg, comprimé', 'Sedaline Labo', 'ZZZ']\t['2019-06-15', '2020-03-15', '2018-01-15']\t['0000-00-00', '2020-09-15', '0000-00-15']\t['2', 'Si besoin', None]
P1\tV1_an\t3\t2\t2021-01-12\t01\t['CALMIX 10 mg, comprimé', 'Sedaline Labo', 'ZZZ']\t['2019-06-15', '2020-03-15', '2018-01-15']\t['0000-00-00', '2020-09-15', '0000-00-15']\t['2', 'Si besoin', None]
P2\tV0\t2\t3\t2020-06-01\t01\t['SEDALINE']\t['0000-00-00']\t['0000-00-00']\t['1']
P3\tV0\t2\t4\t2020-06-02\t01\t\t\t\t
"""

TABLE = """name,molecule,group
CALMIX,calmine,calming
SEDALINE,sedaline,sleeping
"""

SCHEMA = """
instrument: pills
title: Pills
tab: TEST
section: Pills
status: draft
level: list
names: {column: names, clean: medication_name, table: pills.csv, gives: [molecule, group]}
variables:
  pill: {column: names, type: text}
  molecule: {column: molecule, type: text}
  pill_group: {column: group, type: category, codes: {calming: calming, sleeping: sleeping}}
  start_date: {column: starts, type: date, range: [1950-01-01, 2026-12-31]}
  end_date: {column: ends, type: date, range: [1950-01-01, 2026-12-31], missing: {"0000-00-15": not_recorded}}
  units_per_day: {column: per_day, type: number, range: [0, 100], winsor: false, missing: {"si besoin": as_needed}}
at_visit:
  title: Pills on the day of the visit
  start: start_date
  end: end_date
  columns:
    on_calming: {where: {pill_group: calming}, label: On a calming pill}
    on_sleeping: {where: {pill_group: sleeping}, label: On a sleeping pill}
"""


def write_cohort(folder, schema=SCHEMA):
    (folder / "schemas" / "tab").mkdir(parents=True)
    (folder / "schemas" / "tab" / "pills.yaml").write_text(schema, encoding="utf-8")
    (folder / "pills.csv").write_text(TABLE, encoding="utf-8")
    (folder / "extraction.tsv").write_text(EXTRACTION, encoding="utf-8")


def test_the_stem_of_a_medication_name():
    names = pd.Series(["CALMIX LP 400 mg, comprimé sécable", "Sedaline Labo", "calmix* (essai)", "DEUX MOTS/JOUR"])
    assert list(custom.medication_name(names)) == ["CALMIX LP", "SEDALINE LABO", "CALMIX", "DEUX MOTS"]


def test_lists_are_opened_into_one_row_per_item(tmp_path):
    write_cohort(tmp_path)
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    items = result.treatments
    # P1's two rows hold the same lists: they are read once. P3 has no list.
    assert list(items["usubjid"]) == ["P1", "P1", "P1", "P2"] and list(items["item"]) == [1, 2, 3, 1]
    assert list(items["pill"]) == ["CALMIX 10 mg, comprimé", "Sedaline Labo", "ZZZ", "SEDALINE"]       # as written
    # The name is found by its stem, then by its first word; a name that is not in the table is never guessed.
    assert list(items["molecule"][:2]) == ["calmine", "sedaline"] and items["molecule"][3] == "sedaline"
    assert list(items["pill_group"][:2]) == ["calming", "sleeping"] and pd.isna(items["pill_group"][2])
    assert pd.isna(items["end_date"][0]) and items["end_date"][1] == pd.Timestamp("2020-09-15")
    assert list(items["units_per_day"]) [:1] == [2] and items["units_per_day"][1:3].isna().all()
    flags = result.flags[result.flags["usubjid"] == "P1"]
    found = sorted(zip(flags["visit"], flags["variable"], flags["flag"]))
    assert found == [("item 2", "units_per_day", "missing_code"), ("item 3", "end_date", "missing_code"),
                     ("item 3", "molecule", "unknown_code")]
    assert "ZZZ" in flags.loc[flags["flag"] == "unknown_code", "detail"].iloc[0]


def test_columns_of_a_visit_come_from_the_dates(tmp_path):
    write_cohort(tmp_path)
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    data = result.data.set_index(["usubjid", "visit"])
    # P1: the calming pill started in 2019 and has no end; the sleeping pill ran from March to September 2020.
    assert list(data.loc["P1", "on_calming"]) == [1, 1] and list(data.loc["P1", "on_sleeping"]) == [0, 0]
    # P2: a sleeping pill with no start date cannot be placed; it has items, and none is calming.
    assert pd.isna(data.loc[("P2", "V0"), "on_sleeping"]) and data.loc[("P2", "V0"), "on_calming"] == 0
    # P3 has no list at all: nothing can be said.
    assert data.loc["P3", ["on_calming", "on_sleeping"]].isna().all().all()
    qc = result.qc.set_index("variable")
    assert qc.loc["on_calming", "instrument"] == "pills_at_visit" and qc.loc["on_calming", "n_valid"] == 3
    assert qc.loc["pill", "instrument"] == "pills" and qc.loc["molecule", "unknown_code"] == 1


def test_check_schema_checks_the_fields_of_a_list(tmp_path):
    bad = SCHEMA.replace("level: list\n", "").replace("clean: medication_name", "clean: no_such_function")
    bad = bad.replace("start: start_date", "start: no_such_variable").replace("label: On a sleeping pill", "note: none")
    write_cohort(tmp_path, bad)
    problems = " | ".join(check_schema(load_schemas(tmp_path / "schemas")["pills"]))
    assert "names and at_visit need level: list" in problems
    assert "there is no function 'no_such_function'" in problems
    assert "at_visit needs start and end, two variables of the schema" in problems


def test_the_names_table_of_the_package_is_coherent():
    package = Path(__file__).parent.parent / "facedata" / "bp"
    table = pd.read_csv(package / "medications.csv", dtype=str, keep_default_na=False)
    assert table["name"].is_unique and (table["name"] == table["name"].str.upper()).all()
    # One ATC code and one group per molecule, and no group outside the ten of the schema.
    assert (table.groupby("molecule")[["atc", "treatment_group"]].nunique() == 1).all().all()
    schema = load_schemas(package / "schemas")["medications"]
    assert set(table["treatment_group"]) == set(schema["variables"]["treatment_group"]["codes"])
