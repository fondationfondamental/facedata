"""The cohorts together: one baseline row per patient, and the catalogue of the shared instruments."""

from pathlib import Path

import pandas as pd
import yaml

from facedata import common
from facedata.pipeline import Result
from facedata.schema import load_schemas

PACKAGE = Path(__file__).parent.parent / "facedata"
DOMAINS = ["Patient and visits", "Scales rated by the clinician", "Questionnaires filled by the patient", "Neuropsychology",
           "Diagnosis, comorbidities and substances", "Suicide", "Physical examination and laboratory", "Medical and family history",
           "Treatments", "Social situation and use of care"]


def small_result():
    """Three patients. A has a screening and an inclusion visit, B the inclusion only, C the screening only."""
    data = pd.DataFrame({
        "cohort": "bp",
        "usubjid": ["A", "A", "A", "B", "C"],
        "visit": ["screening", "V0", "V1_an", "V0", "screening"],
        "visit_order": [0, 1, 2, 1, 0],
        "visit_month": [None, 0.0, 12.0, 0.0, None],
        "visit_date": pd.to_datetime(["2020-01-10", "2020-03-10", "2021-03-10", "2019-05-02", "2022-06-01"]),
        "siteid": ["01", "01", "01", "02", "03"],
        "age": [30.0, 30.2, 31.2, 45.0, 52.0],
        "mdq_total": [9.0, None, None, None, 4.0],          # filled at screening only
        "qids01": [1.0, 3.0, 2.0, 0.0, None],               # filled at both visits of A
        "qids02": [2.0, None, 2.0, 1.0, None],              # ... and one item is missing at the inclusion
        "hcg": [5.0, None, None, 2.0, None],
        "hcg_cens": [-1.0, None, None, 0.0, None],          # the censoring column goes with its variable
        "bis_form": ["bis10", None, None, "bis12", None],   # a column that names a form
    })
    qc = pd.DataFrame({"variable": ["mdq_total", "qids01", "qids02", "hcg", "sex"],
                       "instrument": ["mdq", "qids", "qids", "biology", "identite"],
                       "level": ["visit", "visit", "visit", "visit", "patient"]})
    empty = pd.DataFrame()
    return Result(data, empty, empty, qc, empty, empty)


def test_baseline_takes_an_instrument_from_the_screening_visit_when_the_inclusion_has_none():
    table, source = common.baseline(small_result())
    assert list(table["usubjid"]) == ["A", "B", "C"] and list(table["visit"]) == ["baseline"] * 3
    a = table.set_index("usubjid").loc["A"]
    assert a["mdq_total"] == 9.0                              # the inclusion visit holds nothing of the MDQ: taken at screening
    assert a["qids01"] == 3.0 and pd.isna(a["qids02"])        # the QIDS is taken whole at the inclusion: no item of the screening
    assert (a["hcg"], a["hcg_cens"]) == (5.0, -1.0)
    assert a["bis_form"] == "bis10"
    assert a["visit_date"] == pd.Timestamp("2020-03-10") and a["age"] == 30.2      # the first columns are those of the inclusion
    assert a["screening_date"] == pd.Timestamp("2020-01-10") and a["days_from_screening"] == 60
    where = source.set_index("usubjid")
    assert list(where.loc["A", ["mdq", "qids", "biology"]]) == ["screening", "V0", "screening"]
    assert list(source.columns) == ["cohort", "usubjid", "mdq", "qids", "biology"]              # a patient-level instrument has no visit


def test_baseline_of_a_patient_with_one_of_the_two_visits():
    table, source = common.baseline(small_result())
    rows = table.set_index("usubjid")
    where = source.set_index("usubjid")
    assert rows.loc["B", "qids01"] == 0.0 and pd.isna(rows.loc["B", "screening_date"]) and pd.isna(rows.loc["B", "mdq_total"])
    assert where.loc["B", "qids"] == "V0" and pd.isna(where.loc["B", "mdq"])
    # C was screened and not included: the row is the screening visit, with its date and its centre
    assert rows.loc["C", "mdq_total"] == 4.0 and rows.loc["C", "visit_date"] == pd.Timestamp("2022-06-01") and rows.loc["C", "siteid"] == "03"
    assert where.loc["C", "mdq"] == "screening" and rows.loc["C", "cohort"] == "bp"
    assert "V1_an" not in set(table["visit"]) and len(table) == 3                               # the follow-up visits are not in the table


def test_baseline_keeps_the_first_columns_of_the_inclusion_visit():
    result = small_result()
    data = result.data.copy()
    data.loc[(data["usubjid"] == "A") & (data["visit"] == "V0"), "visit_date"] = pd.NaT       # an impossible date, removed by the loader
    table, source = common.baseline(result._replace(data=data))
    a = table.set_index("usubjid").loc["A"]
    assert pd.isna(a["visit_date"]) and pd.isna(a["days_from_screening"])      # not the date of the screening visit
    assert a["screening_date"] == pd.Timestamp("2020-01-10") and a["siteid"] == "01" and a["age"] == 30.2
    assert a["mdq_total"] == 9.0                                               # the screening visit still completes the row


def test_baseline_can_leave_out_a_screening_visit_that_is_too_far():
    table, source = common.baseline(small_result(), max_days=30)       # A was screened 60 days before the inclusion
    a = table.set_index("usubjid").loc["A"]
    assert pd.isna(a["mdq_total"]) and pd.isna(a["hcg"]) and pd.isna(a["bis_form"])
    assert a["days_from_screening"] == 60                              # the distance is still given
    assert pd.isna(source.set_index("usubjid").loc["A", "mdq"])
    assert table.set_index("usubjid").loc["C", "mdq_total"] == 4.0     # C has the screening visit only: it stays
    table, source = common.baseline(small_result(), max_days=90)
    assert table.set_index("usubjid").loc["A", "mdq_total"] == 9.0


def test_the_catalogue_is_well_formed():
    table = common.catalogue()
    assert list(table.columns) == ["instrument", "title", "domain", "bp", "sz", "dr", "asp", "n_cohorts", "stack", "use", "note"]
    assert table["instrument"].is_unique
    assert set(table["stack"]) <= {"yes", "with care", "no"}
    assert set(table["domain"]) <= set(DOMAINS), set(table["domain"]) - set(DOMAINS)
    assert (table["n_cohorts"] >= 2).all()
    assert (table.loc[table["stack"] != "yes", "note"].str.len() > 20).all()       # a reserve is always explained
    assert (table.loc[table["stack"] != "no", "use"] != "").all()                  # what can be stacked names its variables


def test_the_catalogue_follows_the_schemas():
    """Every instrument that two cohorts have under one name is in the catalogue, and what the catalogue names exists."""
    with open(PACKAGE / "common_instruments.yaml", encoding="utf-8") as file:
        written = yaml.load(file, Loader=yaml.BaseLoader)
    schemas = {cohort: load_schemas(PACKAGE / cohort / "schemas") for cohort in common.COHORTS}
    listed = {(cohort, name) for entry in written.values() for cohort, name in entry["schemas"].items()}
    missing = []
    for cohort in common.COHORTS:
        for name in schemas[cohort]:
            elsewhere = [other for other in common.COHORTS if other != cohort and name in schemas[other]]
            if elsewhere and (cohort, name) not in listed:
                missing.append(f"{cohort} {name}")
    assert missing == [], "shared by two cohorts and not in common_instruments.yaml"
    unknown = [f"{cohort} {name}" for cohort, name in sorted(listed) if name not in schemas[cohort]]
    assert unknown == [], "common_instruments.yaml names a schema that the cohort does not have"
    not_delivered = []
    for instrument, entry in written.items():
        for variable in entry.get("use", []):
            cohorts = [cohort for cohort, name in entry["schemas"].items()
                       if {**schemas[cohort][name]["variables"], **schemas[cohort][name].get("scores", {})}.get(variable, {}).get("keep")]
            if len(cohorts) < 2:
                not_delivered.append(f"{instrument}: {variable} (delivered by {cohorts})")
    assert not_delivered == [], "a variable to use across cohorts must be delivered by two cohorts of the entry at least"


def test_instruments_of_a_cohort():
    table = common.catalogue()
    names = common.instruments_of("sz", table)
    assert names == sorted(set(names)) and "ctq" in names and "madrs" not in names        # FACE SZ has no MADRS
    stackable = common.instruments_of("bp", table[table["stack"] == "yes"])
    assert set(stackable) < set(common.instruments_of("bp", table))
