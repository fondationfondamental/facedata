"""The same questions asked for each relative: one row per relative, boxes ticked in one cell, summaries per patient."""

import pandas as pd
import pytest

from facedata.parse import parse_boxes
from facedata.pipeline import run_cohort
from facedata.schema import check_cohort, check_schema, load_schemas
from helpers import texts

# A made-up family form: the mother (mo) and two sisters (si1, si2), three questions each.
COLUMNS = ["usubjid", "visit", "id_visit", "visitnum", "svdtc", "siteid", "mo_has", "n_sis", "n_sis_has",
           "mo_dis", "mo_sub", "mo_born", "si1_dis", "si1_sub", "si1_born", "si2_dis", "si2_sub", "si2_born"]
ROWS = [
    # P1: the mother is described at V0 and differently at V1; one of two sisters has something.
    ["P1", "V0", "2", "1", "2020-01-10", "01", "Y", "2", "1", "Dep", "Alcohol,Other", "1950-03-02", "Bip", "None", "1000-01-01", "", "", ""],
    ["P1", "V1_an", "3", "2", "2021-01-12", "01", "", "", "", "Bip", "", "", "Bip", "", "", "", "", ""],
    # P2: nobody has anything, and no sister: the number of sisters who have something is not asked.
    ["P2", "V0", "2", "3", "2020-02-01", "01", "N", "0", "", "", "", "", "", "", "", "", "", ""],
    # P3: nothing is known about the mother.
    ["P3", "V0", "2", "4", "2020-02-02", "01", "U", "1", "0", "", "", "", "", "", "", "", "", ""],
    # P4: the mother has no disorder, "none, and I do not know" for what she drinks; the sister's disorder is unknown.
    ["P4", "V0", "2", "5", "2020-02-03", "01", "Y", "1", "1", "None", "None,Ne sais pas", "", "U", "Other", "", "", "", ""],
    # P5: only a date that was never typed.
    ["P5", "V0", "2", "6", "2020-02-04", "01", "", "", "", "", "", "", "", "", "", "", "", "1000-01-01"],
    # P6: the mother is described at the second visit only, with a box that the schema does not list.
    ["P6", "V0", "2", "7", "2020-02-05", "01", "Y", "0", "", "", "", "", "", "", "", "", "", ""],
    ["P6", "V1_an", "3", "8", "2021-02-06", "01", "", "", "", "Bip", "Wine", "", "", "", "", "", "", ""],
]

COUNTS = """
instrument: counts
title: Who has something
tab: TEST
section: Family
status: draft
level: patient
defaults: {type: item}
variables:
  mother_has: {column: mo_has, range: [0, 1], codes: {Y: 1, N: 0}, missing: {U: unknown}}
  n_sisters: {column: n_sis, range: [0, 20]}
  n_sisters_have: {column: n_sis_has, range: [0, 20], asked_if: n_sisters}
"""

FAMILY = """
instrument: family
title: Family
tab: TEST
section: Family
status: draft
level: relatives
relatives:
  mo: {relative: mother, kin: mother}
  si1: {relative: sister_1, kin: sister}
  si2: {relative: sister_2, kin: sister}
variables:
  kin: {column: kin, type: category, codes: {mother: mother, sister: sister}}
  disorder: {column: dis, type: category, codes: {Bip: bipolar, Dep: depression, None: none}, missing: {U: unknown}}
  drinks: {column: sub, type: item, range: [0, 1], separator: ",", codes: {Alcohol: 1, Other: 0, None: 0}}
  takes_other: {column: sub, type: item, range: [0, 1], separator: ",", codes: {Alcohol: 0, Other: 1, None: 0}}
  born: {column: born, type: date, range: [1900-01-01, 2026-12-31]}
per_patient:
  title: Family, per patient
  by: kin
  counts: {mother: mother_has, sister: n_sisters_have}
  columns:
    any_bipolar: {among: [mother, sister], where: {disorder: bipolar}, label: A relative with bipolar disorder}
    any_mood: {among: [mother, sister], where: {disorder: [bipolar, depression]}, label: A relative with a mood disorder}
    any_drinks: {among: [mother, sister], where: {drinks: 1}, label: A relative who drinks}
    mother_bipolar: {among: [mother], where: {disorder: bipolar}, label: The mother has bipolar disorder}
"""


def write_cohort(folder, family=FAMILY, counts=COUNTS):
    (folder / "schemas" / "tab").mkdir(parents=True)
    (folder / "schemas" / "tab" / "family.yaml").write_text(family, encoding="utf-8")
    (folder / "schemas" / "tab" / "counts.yaml").write_text(counts, encoding="utf-8")
    lines = ["\t".join(COLUMNS)] + ["\t".join(row) for row in ROWS]
    (folder / "extraction.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_boxes_ticked_in_one_cell():
    variable = {"separator": ",", "codes": {"Alcohol": "1", "Other": "0", "None": "0"}}
    text = texts(["Alcohol,Other", "Other", "None, Ne sais pas", "Alcohol,Ne sais pas", "Wine,Alcohol", ""])
    values, flags = parse_boxes(text, "drinks", variable)
    # The largest code of the boxes; "none, and I do not know" is not a no; a box that is not listed is never guessed.
    assert list(values[:2]) == [1, 0] and pd.isna(values[2]) and values[3] == 1 and pd.isna(values[4]) and pd.isna(values[5])
    assert sorted(zip(flags["row"], flags["flag"])) == [(2, "missing_code"), (4, "unknown_code")]


def test_one_row_per_relative(tmp_path):
    write_cohort(tmp_path)
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    table = result.relatives.set_index(["usubjid", "relative"])
    # A relative has a row when something is known: P2, P3 and P5 have none, and P1 has no second sister.
    assert list(table.index) == [("P1", "mother"), ("P4", "mother"), ("P6", "mother"), ("P1", "sister_1"), ("P4", "sister_1")]
    assert list(table["kin"]) == ["mother", "mother", "mother", "sister", "sister"]
    # The first visit that holds an answer is read: P1's mother keeps "Dep", P6's mother is read at the second visit.
    assert list(table["disorder"][:3]) == ["depression", "none", "bipolar"] and table.loc[("P1", "sister_1"), "disorder"] == "bipolar"
    assert pd.isna(table.loc[("P4", "sister_1"), "disorder"])
    assert table.loc[("P1", "mother"), "born"] == pd.Timestamp("1950-03-02") and pd.isna(table.loc[("P1", "sister_1"), "born"])
    # Two variables read the boxes of the same cell.
    assert list(table["drinks"].fillna(-1)) == [1, -1, -1, 0, 0] and list(table["takes_other"].fillna(-1)) == [1, -1, -1, 0, 1]
    flags = result.flags[result.flags["variable"].isin(["disorder", "drinks", "born"])]
    found = sorted(zip(flags["usubjid"], flags["visit"], flags["variable"], flags["flag"]))
    assert found == [("P1", "mother", "disorder", "patient_value_varies"), ("P1", "sister_1", "born", "date_placeholder"),
                     ("P4", "mother", "drinks", "missing_code"), ("P4", "sister_1", "disorder", "missing_code"),
                     ("P5", "sister_2", "born", "date_placeholder"), ("P6", "mother", "drinks", "unknown_code")]
    qc = result.qc.set_index("variable")
    assert qc.loc["disorder", "level"] == "relatives" and qc.loc["disorder", "n_valid"] == 4 and qc.loc["kin", "n_valid"] == 5


def test_relatives_are_summed_up_per_patient(tmp_path):
    write_cohort(tmp_path)
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas")
    patients = result.patients.set_index("usubjid")
    # With no sister, no sister has anything: the count is 0 without being asked.
    assert list(patients["n_sisters_have"].fillna(-1)) == [1, 0, 0, 1, -1, 0]
    # P1: a sister has bipolar disorder. P2: everybody is answered and nobody has it.
    assert patients.loc["P1", "any_bipolar"] == 1 and patients.loc["P2", "any_bipolar"] == 0
    # P3: nothing is known about the mother. P4: the sister who has something has no known disorder. P5: no answer.
    assert patients.loc[["P3", "P4", "P5"], "any_bipolar"].isna().all()
    # P6: the mother has it, and that is enough.
    assert patients.loc["P6", "any_bipolar"] == 1
    # A list of values means any of them; one group can be looked at alone.
    assert list(patients["any_mood"].fillna(-1)) == [1, 0, -1, -1, -1, 1]
    assert list(patients["mother_bipolar"].fillna(-1)) == [0, 0, -1, 0, -1, 1]
    # What P4's mother drinks is not known, and the box of P6's mother is not read: no answer.
    assert list(patients["any_drinks"].fillna(-1)) == [1, 0, -1, -1, -1, -1]
    qc = result.qc.set_index("variable")
    assert qc.loc["any_bipolar", "instrument"] == "family_per_patient" and qc.loc["any_bipolar", "level"] == "patient"
    assert (qc.loc["any_bipolar", "n_rows"], qc.loc["any_bipolar", "n_valid"]) == (6, 3)


def test_the_counts_must_be_loaded_with_the_relatives(tmp_path):
    write_cohort(tmp_path)
    with pytest.raises(ValueError, match="per_patient needs"):
        run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", instruments=["family"])


def test_check_schema_checks_the_fields_of_relatives(tmp_path):
    bad = FAMILY.replace("si2: {relative: sister_2, kin: sister}", "si2: {kin: sister}")
    bad = bad.replace("among: [mother], where: {disorder: bipolar}", "among: [aunt], where: {disorder: bipolar}")
    bad = bad.replace("codes: {Alcohol: 0, Other: 1, None: 0}", "note: no codes")
    write_cohort(tmp_path, bad, COUNTS.replace("n_sisters_have:", "n_have:"))
    schemas = load_schemas(tmp_path / "schemas")
    problems = " | ".join(check_schema(schemas["family"]))
    assert "relatives: 'si2' needs a relative" in problems
    assert "per_patient: column 'mother_bipolar' needs a label, an among that lists groups of counts" in problems
    assert "takes_other: separator goes on an item that has codes" in problems
    assert "per_patient counts with 'n_sisters_have', which no patient-level schema gives" in " | ".join(check_cohort(schemas))
    not_relatives = load_schemas(tmp_path / "schemas")["family"]
    del not_relatives["level"]
    assert "level: relatives and relatives go together" in " | ".join(check_schema(not_relatives))


BOXES = """
instrument: boxes
title: Boxes after a question
tab: TEST
section: Boxes
status: draft
variables:
  any_allergy: {column: mo_has, type: item, range: [0, 1], codes: {Y: 1, N: 0}, missing: {U: unknown}}
  pollen: {column: mo_sub, type: item, range: [0, 1], separator: ",", codes: {Alcohol: 1, Other: 0, None: 0}, asked_if: any_allergy}
  dust: {column: mo_sub, type: item, range: [0, 1], separator: ",", codes: {Alcohol: 0, Other: 1, None: 0}, asked_if: any_allergy}
"""


def test_boxes_shown_only_after_a_yes(tmp_path):
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "boxes.yaml").write_text(BOXES, encoding="utf-8")
    lines = ["\t".join(COLUMNS)] + ["\t".join(row) for row in ROWS]
    (tmp_path / "extraction.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    data = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas").data.set_index(["usubjid", "visit"])
    # After a "yes" the boxes are read in the list; after a "no" they are 0 without being shown.
    assert list(data.loc[("P1", "V0"), ["pollen", "dust"]]) == [1, 1] and list(data.loc[("P2", "V0"), ["pollen", "dust"]]) == [0, 0]
    # "Unknown" leaves them missing, and so does a "yes" with nothing ticked.
    assert data.loc[("P3", "V0"), ["pollen", "dust"]].isna().all() and data.loc[("P6", "V0"), ["pollen", "dust"]].isna().all()
