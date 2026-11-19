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
    on_any: {where: {molecule: [calmine, sedaline]}, label: On calmine or sedaline}
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
    assert list(data.loc["P1", "on_any"]) == [1, 1]                      # where takes a list of values too
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
    package = Path(__file__).parent.parent / "facedata"
    table = pd.read_csv(package / "medications.csv", dtype=str, keep_default_na=False)       # shared by the cohorts
    assert table["name"].is_unique and (table["name"] == table["name"].str.upper()).all()
    # One ATC code and one group per molecule, and no group outside the ten of the schema.
    assert (table.groupby("molecule")[["atc", "treatment_group"]].nunique() == 1).all().all()
    schema = load_schemas(package / "bp" / "schemas")["medications"]
    assert set(table["treatment_group"]) == set(schema["variables"]["treatment_group"]["codes"])


# Made-up lists that the export crossed. Q1 has two products and three lines: six items. Q2 has one product and two lines.
CROSSED = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tnames\tstrengths\tstarts\tper_day\tother
Q1\tV0\t2\t1\t2020-01-10\t01\t['CALMIX', 'CALMIX', 'CALMIX', 'SEDALINE', 'SEDALINE', 'SEDALINE']\t['10 mg', '10 mg', '10 mg', '5 mg', '5 mg', '5 mg']\t['15/06/2019', '15/03/2020', '06/2018', '15/06/2019', '15/03/2020', '06/2018']\t['2', '1', '3', '4', '2', '6']\t['ASPIRIX']
Q2\tV0\t2\t2\t2020-06-01\t01\t['SEDALINE', 'SEDALINE']\t['5 mg', '5 mg']\t['15/01/2020', '15/05/2020']\t['1', '2']\t
"""

CROSSED_SCHEMA = """
instrument: pills
title: Pills
tab: TEST
section: Pills
status: draft
level: list
crossed: [names, strengths]
names: {column: names, clean: medication_name, table: pills.csv, gives: [molecule, group]}
variables:
  pill: {column: names, type: text}
  molecule: {column: molecule, type: text}
  strength: {column: strengths, type: text}
  start_date: {column: starts, type: date, range: [1950-01-01, 2026-12-31]}
  units_per_day: {column: per_day, type: number, range: [0, 100], winsor: false}
"""

OTHER_SCHEMA = """
instrument: other_pills
title: Other pills
tab: TEST
section: Other pills
status: draft
level: list
variables:
  pill: {column: other, type: text}
"""


def write_crossed(folder, schemas):
    (folder / "schemas" / "tab").mkdir(parents=True)
    for name, text in schemas.items():
        (folder / "schemas" / "tab" / f"{name}.yaml").write_text(text, encoding="utf-8")
    (folder / "pills.csv").write_text(TABLE, encoding="utf-8")
    (folder / "extraction.tsv").write_text(CROSSED, encoding="utf-8")


def test_lists_crossed_by_the_export_are_put_back(tmp_path):
    write_crossed(tmp_path, {"pills": CROSSED_SCHEMA})
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    items = result.treatments
    # Q1: two products, the link with the three lines is lost: one item per product, no date and no dose.
    q1 = items[items["usubjid"] == "Q1"]
    assert list(q1["pill"]) == ["CALMIX", "SEDALINE"] and list(q1["strength"]) == ["10 mg", "5 mg"]
    assert q1["start_date"].isna().all() and q1["units_per_day"].isna().all()
    crossed = result.flags[result.flags["flag"] == "list_crossed"]
    assert sorted(set(crossed["variable"])) == ["start_date", "units_per_day"] and set(crossed["usubjid"]) == {"Q1"}
    # Q2: one product, every line is its own. The dates are written day/month/year.
    q2 = items[items["usubjid"] == "Q2"]
    assert list(q2["pill"]) == ["SEDALINE", "SEDALINE"] and list(q2["units_per_day"]) == [1, 2]
    assert list(q2["start_date"].dt.strftime("%Y-%m-%d")) == ["2020-01-15", "2020-05-15"]
    assert "list" not in items                       # one list instrument: no column list


def test_several_list_instruments_are_stacked(tmp_path):
    write_crossed(tmp_path, {"pills": CROSSED_SCHEMA, "other_pills": OTHER_SCHEMA})
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    items = result.treatments
    assert list(items.columns[:3]) == ["usubjid", "list", "item"]
    assert items["list"].value_counts().to_dict() == {"pills": 4, "other_pills": 1}
    assert list(items.loc[items["list"] == "other_pills", "pill"]) == ["ASPIRIX"]      # the same column for the two lists
    assert set(result.flags.loc[result.flags["flag"] == "list_crossed", "visit"]) == {"pills item 1", "pills item 2"}
    problems = check_schema({**load_schemas(tmp_path / "schemas")["pills"], "level": "visit"}, {"names", "strengths", "starts", "per_day"})
    assert any("crossed needs level: list" in problem for problem in problems)



PACKED = """usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tills\twho\tnames
P1\tscreening\t1\t1\t2020-01-02\t01\t\t\t['CALMIX']
P1\tV0\t2\t2\t2020-01-10\t01\t(3 - a cold - then a cough - 4 - 1) | (5 -  - 12 - 0) | (7 - x)\t2 | 4 | 4\t['SEDALINE', 'ZZZ']
P2\tV0\t2\t3\t2020-06-01\t01\t\t\t
"""

ILLNESSES = """
instrument: illnesses
title: Illnesses
tab: TEST
section: Illnesses
status: draft
level: list
packed:
  ills: {fields: [ill_code, ill_text, ill_age, ill_over], text: ill_text}
  who: {fields: [ill_who]}
variables:
  illness: {column: ill_code, type: category, codes: {"3": cold, "5": flu, "7": other}}
  illness_text: {column: ill_text, type: text}
  illness_age: {column: ill_age, type: number, range: [0, 100], winsor: false}
  illness_over: {column: ill_over, type: item, range: [0, 1]}
  illness_who: {column: ill_who, type: category, codes: {"2": mother, "4": father}}
"""

PILLS_OF_THE_VISIT = """
instrument: pills
title: Pills
tab: TEST
section: Pills
status: draft
level: list
per_visit: true
variables:
  pill: {column: names, type: text}
"""


def test_records_packed_in_a_cell_and_lists_of_the_visit(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "illnesses.yaml").write_text(ILLNESSES, encoding="utf-8")
    (tmp_path / "schemas" / "tab" / "pills.yaml").write_text(PILLS_OF_THE_VISIT, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(PACKED, encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    items = result.treatments
    ills = items[items["list"] == "illnesses"].reset_index(drop=True)
    assert list(ills["item"]) == [1, 2, 3] and list(ills["illness"]) == ["cold", "flu", "other"]
    assert ills["illness_text"].fillna("").tolist() == ["a cold - then a cough", "", "x"]      # the separator inside the free text
    assert list(ills["illness_age"][:2]) == [4, 12] and pd.isna(ills["illness_age"][2])          # the short record has its last fields empty
    assert list(ills["illness_who"]) == ["mother", "father", "father"]                           # a cell of single values
    pills = items[items["list"] == "pills"].reset_index(drop=True)
    assert list(zip(pills["visit"], pills["item"], pills["pill"])) == [("screening", 1, "CALMIX"), ("V0", 1, "SEDALINE"), ("V0", 2, "ZZZ")]
    assert "patient_value_varies" not in set(result.flags["flag"])                                # the two visits of P1 hold two lists


def test_check_schema_checks_per_visit_and_packed(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "illnesses.yaml").write_text(ILLNESSES.replace("level: list\n", "").replace("text: ill_text", "text: no_such_field"), encoding="utf-8")
    (tmp_path / "schemas" / "tab" / "pills.yaml").write_text(PILLS_OF_THE_VISIT.replace("level: list\n", ""), encoding="utf-8")
    schemas = load_schemas(tmp_path / "schemas")
    assert "packed needs level: list" in " | ".join(check_schema(schemas["illnesses"]))
    assert "per_visit needs level: list" in " | ".join(check_schema(schemas["pills"]))
    assert "packed: column 'ills' is not in the extraction" in " | ".join(check_schema(schemas["illnesses"], {"who"}))


def test_accents_written_twice_are_put_back_and_a_second_column_of_names_is_read(tmp_path):
    from facedata.read import read_extraction, twice_encoded
    assert twice_encoded("dÃ©pression") == "dépression" and twice_encoded("déjà") == "déjà" and twice_encoded("Ã") == "Ã"
    assert twice_encoded("déjà Ã©té – ['Ã\\xa0 jeun']") == "déjà été – ['à jeun']"          # a cell that is only partly broken
    assert list(custom.medication_name_plain(pd.Series(["Mélatonine 2 mg", "CALMIX LP 10 mg"]))) == ["MELATONINE", "CALMIX LP"]
    extraction = EXTRACTION.replace("\tper_day", "\tper_day\tgeneric").replace("['2', 'Si besoin', None]", "['2', 'Si besoin', None]\t[None, None, 'SÃ©daline']")
    extraction = extraction.replace("['1']\n", "['1']\t[None]\n").replace("\t\t\t\t\n", "\t\t\t\t\t\n")
    schema = SCHEMA.replace("clean: medication_name,", "clean: medication_name_plain, otherwise: generic,").replace("  pill: {column: names, type: text}", "  pill: {column: names, type: text}\n  generic: {column: generic, type: text}")
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "pills.yaml").write_text(schema, encoding="utf-8")
    (tmp_path / "pills.csv").write_text(TABLE, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(extraction, encoding="utf-8")
    assert read_extraction(tmp_path / "extraction.tsv", repair_accents=True)["generic"][0] == "[None, None, 'Sédaline']"
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", repair_accents=True)
    items = result.treatments
    assert list(items["molecule"]) == ["calmine", "sedaline", "sedaline", "sedaline"]       # ZZZ is unknown, its generic name is found
    assert "unknown_code" not in set(result.flags["flag"])


def test_the_strength_read_from_the_name_and_the_daily_dose():
    """DM-14: the form stores no strength since 2015; the name holds it (rule R54 of EXPORT_REQUESTS.md)."""
    names = pd.Series(["DRUGA 500 mg, comprimé", "DRUGB 0,5 g", "DRUGC 25 microgrammes", "DRUGD 2 mg/ml, solution",
                       "DRUGE 10 mg + 5 mg", "DRUGF 1 %", "DRUGG LP", "DRUGH 100mgx"])
    found = custom.strength_in_name(names)
    assert list(found[:3]) == [500, 500, 0.025] and found[3:].isna().all()
    values = pd.DataFrame({"strength": ["400 mg", None, "2 COMPRIM", None, None],
                           "dose_unit": ["MG", None, "COMPRIM", None, None],
                           "medication": ["DRUGA 400 mg", "DRUGB 500 mg", "DRUGC", "DRUGD", "DRUGE 50 mg"],
                           "units_per_day": [0.5, 2.0, 1.0, 3.0, None]})
    # The stored strength first, else the name; a strength in tablets gives no dose; no units, no dose.
    dose = custom.daily_dose(values)
    assert list(dose[:2]) == [200, 1000] and dose[2:].isna().all()
    values["daily_dose"] = dose
    assert list(custom.strength_from_name(values)[:2]) == [0, 1] and custom.strength_from_name(values)[2:].isna().all()


def test_a_treatment_that_ends_before_it_starts():
    values = pd.DataFrame({"start_date": pd.to_datetime(["2015-03-15", "2015-03-15", None]),
                           "end_date": pd.to_datetime(["2015-01-15", "2015-03-15", "2015-01-15"])})
    assert list(custom.end_before_start(values)) == [True, False, False]
