"""The real FACE SZ extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/sz/PROGRESS.md ("What the schemas
must produce"). No patient row appears here.
"""

from pathlib import Path

import pandas as pd
import pytest

from facedata import sz
from facedata.read import prepare_visits, read_extraction
from facedata.relatives import stack_relatives
from facedata.schema import load_schemas
from facedata.treatments import open_lists
from test_pipeline import assert_invariant

ROOT = Path(__file__).parent.parent
EXTRACTION = ROOT / "data" / "sz" / "SZALL_20261121.tsv"
THESAURUS = ROOT / "thesauri" / "FACESZ_thesaurus_V4.20.xlsx"
NORMS = ROOT / "norms"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the SZ extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return sz.load(EXTRACTION, norms=NORMS)


@pytest.fixture(scope="module")
def qc(result):
    return result.qc.set_index("variable")


def test_visits(result):
    assert len(result.data) == 6612
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 2353 == len(result.patients)
    # A screening row for seven patients in ten, and yearly visits: no six-month visit.
    visits = result.data["visit"].value_counts()
    assert (visits["V0"], visits["screening"], visits["V1_an"]) == (2353, 1675, 1011)
    assert result.flags[result.flags["flag"] == "visit_order"].shape[0] == 21


def test_the_two_cohorts_can_be_stacked(result):
    from facedata import bp
    bp_file = ROOT / "data" / "bp" / "BPALL_20261113_2.tsv"
    if not bp_file.exists():
        pytest.skip("the BP extraction is not on this computer")
    for table in [result.data, result.patients, result.flags, result.treatments, result.relatives]:
        assert table.columns[0] == "cohort" and set(table["cohort"]) <= {"sz"}
    other = bp.load(bp_file, instruments=["identite"])
    patients = pd.concat([other.patients, result.patients[other.patients.columns]], ignore_index=True)
    assert len(patients) == 6498 + 2353
    # A usubjid is a number given inside a cohort: 824 are used in both, for different patients.
    assert patients["usubjid"].duplicated().sum() == 824
    assert not patients.duplicated(["cohort", "usubjid"]).any()
    assert patients["fondacode"].is_unique
    assert set(patients["diagnosis"]) == {"bp1", "bp2", "bp_nos", "schizophrenia", "schizoaffective", "schizophreniform"}


def test_patient_tab(result, qc):
    patients = result.patients
    assert ((qc["tab"] == "PATIENT") & (qc["level"] == "patient")).sum() == 16
    assert patients["sex"].value_counts().to_dict() == {"male": 1706, "female": 647}
    assert patients["diagnosis"].value_counts().to_dict() == {"schizophrenia": 1797, "schizoaffective": 513, "schizophreniform": 43}
    assert (patients["age_at_inclusion"].min(), patients["age_at_inclusion"].max()) == (17, 84)
    assert qc.loc[qc["tab"] == "PATIENT", ["unknown_code", "unparsed", "out_of_range", "patient_value_varies"]].sum().sum() == 0
    # The non-opposition form is administrative: it is not delivered, as in FACE BP.
    assert "opposition_form" not in patients.columns
    assert (qc.loc["referred_by", "n_valid"], qc.loc["referral_letter_date", "date_placeholder"]) == (1591, 10)
    reason = qc.loc["followup_end_reason"]
    assert (reason["n_filled"], reason["n_valid"], reason["missing_code"]) == (581, 490, 91)
    # The column named for the cause of death holds the date of death, for patients recorded as deceased only.
    deceased = patients["followup_end_reason"] == "deceased"
    assert (deceased.sum(), patients.loc[deceased, "death_date"].notna().sum()) == (12, 8)
    assert patients.loc[~deceased, "death_date"].isna().all()
    assert result.data["entry_date"].notna().all()


def test_hetero_questionnaires(result, qc):
    tab = qc[qc["tab"] == "HETERO-QUESTIONNAIRE"]
    assert (len(tab), tab["instrument"].nunique()) == (131, 10)
    assert tab[["unknown_code", "unparsed"]].sum().sum() == 0
    # PANSS: the three scales, the total and the fifteen factor scores are the sums of their items.
    panss = tab[tab["instrument"] == "panss"]
    assert (len(panss), panss["score_mismatch"].sum()) == (50, 0)
    # The composite (positive minus negative scale) is a score of the package: no stored twin, no flag (D77).
    assert (qc.loc["panss_composite", "n_valid"], qc.loc["panss_composite", "min"], qc.loc["panss_composite", "max"]) == (4652, -33, 25)
    stored = result.flags[result.flags["variable"].str.startswith("panss_") & result.flags["variable"].str.endswith("_stored")]
    assert len(stored) == 0                               # every stored PANSS score is inside its limits and compared
    assert (qc.loc["panss_total", "n_valid"], qc.loc["panss_total", "min"], qc.loc["panss_total", "max"]) == (4642, 30, 160)
    assert (qc.loc["panss_wallwork_positive", "n_valid"], qc.loc["panss_vandergaag_disorganised", "n_valid"]) == (4659, 4651)
    # Three factor scores follow their publication, not the stored formula, which sums a wrong item.
    data = result.data
    for name, items in [("panss_wallwork_positive", ["p1", "p3", "p5", "g9"]), ("panss_wallwork_negative", ["n1", "n2", "n3", "n4", "n6", "g7"]),
                        ("panss_lancon_negative", ["n1", "n2", "n3", "n4", "n6", "g7", "g16"])]:
        published = data[["panss_" + item for item in items]].sum(axis=1, min_count=len(items))
        assert published.equals(data[name]), name
        assert name + "_as_stored" not in data.columns            # the stored formula is only a check
    assert (qc.loc["panss_wallwork_negative", "n_valid"], qc.loc["panss_lancon_negative", "n_valid"]) == (4658, 4656)
    # Calgary: eight items; the export mis-wires items 7 to 9 (D76: item 8 is the suicide item, in the column named for item 9; item 9 is not exported), so no CDSS total.
    assert (qc.loc["calgary_sum8", "n_valid"], qc.loc["calgary_sum8", "max"], qc.loc["calgary08", "n_valid"]) == (4668, 20, 4670)
    assert "calgary08" in result.data.columns and "calgary09" not in result.data.columns and "calgary_total" not in result.data.columns
    # YMRS: items 5, 8 and 9 are exported as levels (0 to 4: a slip of the export, request R135) and delivered in points, as published and as in BP (D75).
    assert (qc.loc["ymrs_total", "n_valid"], qc.loc["ymrs_total", "score_mismatch"], qc.loc["ymrs_total", "max"]) == (4534, 0, 38)
    for item in ["ymrs05", "ymrs06", "ymrs08", "ymrs09"]:
        assert set(data[item].dropna()) <= {0, 2, 4, 6, 8}, item
    assert "ymrs_total_as_stored" not in data.columns and (result.flags["variable"] == "ymrs_total_as_stored").sum() == 0     # the twin equals the stored total
    higher = data["ymrs_total"].notna() & (data["ymrs05"] + data["ymrs08"] + data["ymrs09"] > 0)
    assert higher.sum() == 774                                     # visits whose published total is above the stored one
    assert (qc.loc["barnes_sum", "score_mismatch"], qc.loc["esrsa_mean", "score_mismatch"]) == (3, 10)
    # The efficacy index is a score recomputed from the effect and the side effects (D79); the stored one is the check.
    index = qc.loc["cgi_efficacy_index"]
    assert (index["n_valid"], index["score_mismatch"], index["score_not_recomputed"], index["check_failed"]) == (2033, 23, 3, 0)
    assert qc.loc["psp_band", "check_failed"] == 215
    assert (qc.loc["bars_doses_per_day", "out_of_range"], qc.loc["psp_total", "out_of_range"]) == (250, 3)
    assert (qc.loc["cgi_severity", "missing_code"], qc.loc["cgi_improvement", "missing_code"]) == (12, 125)
    # The improvement, the therapeutic effect and the index are asked at the follow-up visits only, as in BP.
    assert (qc.loc["cgi_improvement", "n_valid"], data.loc[data["visit_month"] == 0, "cgi_improvement"].notna().sum()) == (2192, 0)
    # SUMD: 0 is "cannot be rated", a missing code.
    assert (qc.loc["sumd01", "missing_code"], qc.loc["sumd04_awareness", "missing_code"]) == (29, 2119)
    assert (qc.loc["aims_movements", "n_valid"], qc.loc["bars_adherence", "n_valid"], qc.loc["gaf", "n_valid"]) == (4145, 4379, 4530)


def test_vitals_and_ecg(result, qc):
    # None of the scale errors of BP: no height in millimetres, no weight with a lost decimal point.
    assert (qc.loc["height", "n_valid"], qc.loc["height", "out_of_range"], qc.loc["height", "unit_inferred"]) == (4313, 3, 0)
    assert (qc.loc["weight", "n_valid"], qc.loc["weight", "out_of_range"], qc.loc["waist", "out_of_range"]) == (4317, 1, 9)
    assert (qc.loc["bmi", "n_valid"], qc.loc["bmi", "score_mismatch"]) == (4298, 0)
    assert (qc.loc["systolic_supine", "n_valid"], qc.loc["diastolic_supine", "unit_inferred"]) == (4118, 1)
    assert (qc.loc["qtc_stored", "n_valid"], qc.loc["qtc_stored", "out_of_range"], qc.loc["qtc_stored", "unit_inferred"]) == (2826, 27, 1)


def test_biology(qc):
    tab = qc[qc["tab"] == "BILAN BIOLOGIQUE"]
    assert (len(tab), tab["instrument"].nunique(), tab["unparsed"].sum()) == (27, 7, 0)
    crp, glucose, haemoglobin = qc.loc["crp"], qc.loc["glucose"], qc.loc["haemoglobin"]
    assert (crp["n_valid"], crp["censored_left"], crp["censored_right"]) == (3084, 333, 1)
    assert crp["missing_code"] == 477                                   # a CRP of exactly 0 is not a measurement (BP D101)
    assert (glucose["n_valid"], glucose["unit_converted"], glucose["unit_inferred"], glucose["out_of_range"]) == (3137, 66, 20, 0)   # the unit mg/dL is read: 3 cells gained (biology review, D144)
    # HbA1c typed in mmol/mol under the label %: brought to % with the IFCC-NGSP master equation (D41).
    assert (qc.loc["hba1c", "unit_inferred"], qc.loc["hba1c", "out_of_range"]) == (5, 1)
    assert (haemoglobin["n_valid"], haemoglobin["unit_inferred"], haemoglobin["out_of_range"]) == (3655, 34, 4)
    assert (qc.loc["neutrophils", "unit_inferred"], qc.loc["eosinophils", "unit_doubt"]) == (23, 37)
    # The stored cholesterol ratio is not the ratio of the stored values on 4% of the visits.
    assert (qc.loc["cholesterol_hdl_ratio", "n_valid"], qc.loc["cholesterol_hdl_ratio", "score_mismatch"]) == (3576, 157)
    prolactin = qc.loc["prolactin"]
    assert (prolactin["n_valid"], prolactin["unit_converted"], prolactin["unit_inferred"]) == (3040, 632, 195)      # below 0.2 the value is mg/L: 56 cells gained (biology review, D144)
    assert (prolactin["unit_unknown"], prolactin["unit_doubt"], prolactin["out_of_range"]) == (162, 36, 11)         # (biology review, D144)
    assert (qc.loc["clozapine", "n_valid"], qc.loc["clozapine", "unit_inferred"], qc.loc["clozapine_treated", "n_valid"]) == (592, 11, 1598)
    assert (qc.loc["vitamin_d_as_written", "n_valid"], qc.loc["vitamin_d_as_written", "censored_left"], qc.loc["vitamin_d_as_written", "out_of_range"]) == (2717, 11, 2)
    assert (qc.loc["toxo_igg_titre", "n_valid"], qc.loc["toxo_igg_titre", "censored_right"], qc.loc["toxo_serology", "n_valid"]) == (632, 16, 2826)


def test_auto_questionnaires(result, qc):
    tab = qc[qc["tab"] == "AUTO-QUESTIONNAIRE"]
    # 475 -> 485 in the auto-questionnaires review (D82-D91): the S-QoL items 17 and 18, the psychological dimension and the index are
    # no longer delivered (-4), and the seven DSM-5 forms gain two criteria counts each (+14). 485 -> 507 with SZALL_20261121 (D104): the
    # four S-QoL variables are delivered again (+4) with the 18 boxes "does not concern me" (+18).
    assert (len(tab), tab["instrument"].nunique(), tab["unknown_code"].sum()) == (507, 21, 0)
    for name in ["ctq_total", "eq5d_index", "fagerstrom_total", "wurs25_total", "sqol_resilience"]:
        assert qc.loc[name, "score_mismatch"] == 0, name
    counts = (qc.loc["ctq_total", "n_valid"], qc.loc["eq5d_index", "n_valid"], qc.loc["fagerstrom_total", "n_valid"], qc.loc["wurs25_total", "n_valid"])
    assert counts == (2166, 3905, 1977, 295)
    # The CTQ denial score is the strict count of its three items, the same rule in the four cohorts (D82): the stored score counts a blank item as 0,
    # so 43 values are gained (the stored score is missing where the three items are there) and 20 are lost (a stored score with one item blank).
    denial = qc.loc["ctq_denial"]
    assert (denial["n_valid"], denial["score_mismatch"], denial["score_not_recomputed"]) == (2191, 2, 20)
    assert (qc.loc["mars_total", "n_valid"], qc.loc["mars_total", "score_mismatch"]) == (4262, 2)
    # PSQI: 35 totals gained (component 5 is computed from the items, a blank 5j counts 0), the latency is no longer winsorised (D83).
    assert (qc.loc["psqi_total", "n_valid"], qc.loc["psqi_total", "score_mismatch"], qc.loc["psqi_latency", "unparsed"]) == (2992, 106, 26)
    assert (qc.loc["psqi_disturbances", "n_valid"], qc.loc["psqi_disturbances", "score_mismatch"], qc.loc["psqi_dysfunction", "n_valid"], qc.loc["psqi_dysfunction", "score_mismatch"]) == (3158, 0, 3195, 0)
    assert qc.loc["psqi_latency", "winsorised"] == 0 and qc.loc["psqi10f", "n_valid"] == 171
    assert "psqi10e_text" not in result.data.columns and "psqi_disturbances_stored" not in result.data.columns
    # Birchwood: a score typed with no item is delivered as stored (D86): 36, 32, 39 and 24 visits.
    assert (qc.loc["birchwood_total", "n_valid"], qc.loc["birchwood_total", "score_mismatch"]) == (4264, 5)
    assert [qc.loc["birchwood_" + name, "score_as_stored"] for name in ["symptoms", "illness", "treatment", "total"]] == [36, 32, 39, 24]
    # S-QoL: the export reads items 17 and 18 with the labels of the form since SZALL_20261121 (D104, request R150; they were mis-coded, D87):
    # the two items hold 1 to 5, and the psychological dimension and the index are recomputed, equal to the stored ones. A dimension is the
    # mean of the items present, one missing at most; the index the mean of seven dimensions at least.
    assert [qc.loc[name, "n_valid"] for name in ["sqol16", "sqol17", "sqol18"]] == [4263, 4191, 4228]
    assert sorted(result.data["sqol17"].dropna().unique()) == [1, 2, 3, 4, 5]
    dimensions = ["sentimental_life", "self_esteem", "family", "friends", "autonomy", "psychological_wellbeing", "physical_wellbeing", "resilience", "index"]
    assert [qc.loc["sqol_" + name, "n_valid"] for name in dimensions] == [4191, 4327, 4300, 4243, 4317, 4254, 4320, 4273, 4256]
    assert [qc.loc["sqol_" + name, "score_mismatch"] + qc.loc["sqol_" + name, "score_not_recomputed"] for name in dimensions] == [0] * 9
    # The 18 boxes "does not concern me": OUI is 1, NON and def are 0 (O47); 1,652 boxes ticked on 703 visits.
    boxes = ["sqol%02d_pc" % number for number in range(1, 19)]
    assert [qc.loc[name, "n_valid"] for name in boxes] == [4538] * 18
    assert (int(result.data[boxes].sum().sum()), int((result.data[boxes] == 1).any(axis=1).sum())) == (1652, 703)
    assert (qc.loc["stori_stage1", "n_valid"], qc.loc["stori_stage1", "score_mismatch"]) == (3085, 2)
    # EPHP: code 7 ("cannot be assessed") stays missing in the items and counts 0 in the scores, as the application since 2026-10-28 (D98).
    assert (qc.loc["ephp_total", "n_valid"], qc.loc["ephp_total", "score_mismatch"], tab.loc[tab["instrument"] == "ephp", "missing_code"].sum()) == (1784, 229, 377)
    assert (qc.loc["ybocs_total", "n_valid"], qc.loc["ybocs_total", "score_mismatch"], qc.loc["sogs_total", "n_valid"]) == (281, 28, 122)
    # SOGS: the 11 yes/no items 16a to 16k are 0 after a "no" to question 16 (asked_if, D88): 132 visits, 1,430 cells gained, 143 answered in all.
    sogs16 = ["sogs16" + letter for letter in "abcdefghijk"]
    assert int((result.data["sogs16"] == 0).sum()) == 132 and (result.data.loc[result.data["sogs16"] == 0, sogs16] == 0).all().all()
    assert [qc.loc[name, "n_valid"] for name in sogs16] == [143] * 7 + [142] + [143] * 3
    assert (tab.loc[tab["instrument"] == "presenteeism", "out_of_range"].sum(), tab.loc[tab["instrument"] == "physical_activity", "out_of_range"].sum()) == (13, 4)
    # Physical activity: hours and minutes of a duration are hidden by the number of days (D85): 7 cells typed under 0 days or an empty number.
    assert tab.loc[tab["instrument"] == "physical_activity", "not_shown"].sum() == 7
    # Seven substances, the same twelve criteria; "do not know" is a missing code. The criteria are 0 where the patient used the substance
    # ten times or fewer, and for the five illicit drugs where no illicit drug was used (asked_if, D97): 456,972 cells become 0.
    assert (qc.loc["alcohol_larger_amounts", "n_valid"], qc.loc["alcohol_larger_amounts", "missing_code"], qc.loc["heroin_tolerance", "n_valid"]) == (2929, 9, 3390)
    # The stems of three forms are sedative_, opiate_ and other_substance_ (D90, as on the SUBSTANCES tab); no value changes.
    assert [qc.loc[name, "n_valid"] for name in ["sedative_larger_amounts", "opiate_larger_amounts", "other_substance_larger_amounts"]] == [3377, 3386, 3303]
    assert not [name for name in result.data.columns if name.startswith(("sedatives_", "opiates_", "other_larger"))]
    # The 14 criteria counts (D90): the number of yes among the eleven criteria a to k (all eleven needed), ever and in the last 12 months;
    # 0 where the use question gates the criteria (D97).
    substances = ["alcohol", "cannabis", "cocaine", "heroin", "opiate", "sedative", "other_substance"]
    criteria = qc.loc[[f"{name}_criteria_count{suffix}" for name in substances for suffix in ["", "_12m"]]]
    assert criteria["n_valid"].tolist() == [2854, 2839, 2914, 2896, 3331, 3329, 3389, 3389, 3386, 3386, 3372, 3372, 3299, 3299]
    assert (int(criteria["n_valid"].sum()), criteria["min"].min(), criteria["max"].max(), criteria["out_of_range"].sum()) == (45055, 0, 11, 0)
    assert criteria[["score_mismatch", "score_not_recomputed"]].sum().sum() == 0


def test_neuropsychology_first_part(result, qc):
    tab = qc[qc["tab"] == "NEUROPSYCHOLOGIE"]
    assert (len(tab), tab["instrument"].nunique(), tab["unknown_code"].sum()) == (664, 30, 0)       # + neuropsy_age_used (D138-D143, D48)
    data = result.data
    # 33 visits labelled WAIS-III hold the WAIS-IV sequencing task and are read as WAIS-IV (WAIS review, D138-D143, D47).
    assert data["wais_version"].value_counts().to_dict() == {"wais4": 2684, "wais3": 748}
    # The years of education are exported for every assessment since the extraction of 17 November 2026
    # (776 visits until 2016 before): the TMT error norms can be read on every visit.
    assert (qc.loc["education_years", "n_valid"], qc.loc["education_years", "last_year"]) == (3446, 2026)
    assert (qc.loc["tmt_a_errors_band", "n_valid"], qc.loc["tmt_a_errors_band", "norm_missing"]) == (3105, 0)
    # A suspected learning disorder: several kinds can be ticked, one box each, 0 after a "no".
    assert (qc.loc["neuropsy_dyslexia", "n_valid"], (data["neuropsy_dyslexia"] == 1).sum(), (data["neuropsy_dyspraxia"] == 1).sum()) == (2848, 203, 42)
    # One centre's 23 early visits mix the two sign conventions (mean correlation 0.24 the wrong way): too weak
    # to flip, so the scores stay as written and are doubted.
    assert (qc.loc["tmt_a_time", "n_valid"], qc.loc["tmt_a_time_z", "sign_flipped"], qc.loc["tmt_a_time_z", "sign_doubt"]) == (3208, 0, 0)       # recomputed (D135)
    assert (qc.loc["errands_errors", "n_valid"], qc.loc["errands_errors", "score_mismatch"], qc.loc["fluency_p_rule_breaks", "score_mismatch"]) == (1021, 0, 0)
    # WAIS-IV matrices: items 25 and 26 are copies of item 24 in the extraction, so the total is the stored one.
    assert "wais4_mat25" not in data.columns and "wais4_mat26" not in data.columns
    # The 25 matrices visits read as WAIS-IV leave the WAIS-III total, with its 4 mismatches (WAIS review, D138-D143, D47).
    assert (qc.loc["wais3_mat_total", "n_valid"], qc.loc["wais3_mat_total", "score_mismatch"], qc.loc["wais4_mat_total", "n_valid"]) == (543, 0, 1890)
    # Digit span: the summary columns hold what their labels say (they are shifted in BP).
    checks = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts()
    # The check scores are not delivered: their mismatch is filed under the stored total that the analyst sees.
    # The 33 digit-span visits read as WAIS-IV take their mismatches with them: 30 were filed under the WAIS-III total, 1 is now under the WAIS-IV one (WAIS review, D138-D143, D47).
    assert (qc.loc["wais4_ds_total", "n_valid"], checks.get("wais4_ds_total", 0), checks.get("wais3_ds_total", 0)) == (2524, 1, 0)


def same(stored, formula, tolerance=0.011):
    """How many rows agree, and how many hold both values."""
    both = stored.notna() & formula.notna()
    return int(((stored - formula).abs() <= tolerance)[both].sum()), int(both.sum())


def test_cvlt_and_wais(result, qc):
    data = result.data
    # CVLT: the z-scores are computed again with the regressions of the norms, as in BP. From October 2021 to June 2026
    # the application computed part of the z-scores of trials 1 to 5 with two coefficients exchanged: they differ from the stored ones.
    assert (qc.loc["cvlt_total_1_5", "n_valid"], qc.loc["cvlt_total_1_5_z", "n_valid"], qc.loc["cvlt_total_1_5_z", "out_of_range"]) == (2273, 2273, 0)
    assert (qc.loc["cvlt_total_1_5_z", "score_mismatch"], qc.loc["cvlt_total_1_5_z", "norm_missing"], qc.loc["cvlt_trial1_z", "score_mismatch"]) == (332, 0, 5)
    total_z = data["cvlt_total_1_5_z"]
    from_2022 = data["visit_date"].dt.year >= 2022
    assert abs(total_z[from_2022].median() - total_z[~from_2022].median()) < 0.3      # the stored ones were 3 points apart
    assert (qc.loc["cvlt_total_1_5_band", "n_valid"], qc.loc["cvlt_short_free_band", "band_from_z"]) == (2273, 496)
    # Serial clustering is read in the same table as in BP (BP D129); 37 stored bands have no index to read it from.
    assert (qc.loc["cvlt_serial_band", "n_valid"], qc.loc["cvlt_serial_band", "censored_right"], qc.loc["cvlt_serial_band", "norm_missing"]) == (1613, 88, 37)
    assert not [name for name in data.columns if name.startswith("cvlt") and name.endswith("_stored")]
    # WAIS-IV similarities: items 10 and 11 are the same cell twice, so the total is the stored one.
    # 25 visits read as WAIS-IV, with the 12 WAIS-III mismatches, and one WAIS-III total lost to the total rule, no `min_items` (WAIS review, D138-D143, D47).
    assert (qc.loc["wais3_simil_total", "n_valid"], qc.loc["wais3_simil_total", "score_mismatch"], qc.loc["wais4_simil_total", "n_valid"]) == (544, 0, 1888)
    # The sums of scaled scores are those of a seven-subtest short form. The scaled scores are in other schemas.
    w3_verbal = 2 * data["wais3_simil_scaled"] + 2 * data["wais3_info_scaled"] + data["wais3_arith_scaled"] + data["wais3_ds_scaled"]
    w3_performance = 2 * data["wais3_pc_scaled"] + 2 * data["wais3_mat_scaled"] + data["wais3_code_scaled"]
    # The sums of the WAIS-III efficiency form are recomputed from the delivered scaled scores (`uses`, WAIS review, D138-D143, D47): they equal the formula by construction.
    # The counts move with the edition (visits read as WAIS-IV leave the WAIS-III sums) and with the total rule (a total with a missing item is not delivered, so its sum goes).
    assert same(data["wais3_qiv_sum_scaled"], w3_verbal) == (528, 528)
    assert same(data["wais3_qip_sum_scaled"], w3_performance) == (538, 538)
    assert same(data["wais3_imt_sum_scaled"], data["wais3_ds_scaled"] + data["wais3_arith_scaled"] + data["wais3_lns_scaled"]) == (473, 473)
    # WAIS-IV: 24 to 25 visits gained from WAIS-III, 3 to 11 lost to the total rule (WAIS review, D138-D143, D47).
    assert same(data["wais4_icv_sum_scaled"], 1.5 * (data["wais4_simil_scaled"] + data["wais4_info_scaled"])) == (474, 474)       # the sums are recomputed from the delivered scaled scores (D137): they equal the formula by construction
    assert same(data["wais4_irp_sum_scaled"], 1.5 * (data["wais4_mat_scaled"] + data["wais4_pc_scaled"])) == (475, 475)
    assert same(data["wais4_imt_sum_scaled"], data["wais4_ds_scaled"] + data["wais4_arith_scaled"]) == (471, 471)
    seven = ["wais4_simil_scaled", "wais4_info_scaled", "wais4_arith_scaled", "wais4_ds_scaled", "wais4_pc_scaled", "wais4_mat_scaled", "wais4_code_scaled"]
    assert same(data["wais4_qit_sum_scaled"], data[seven].sum(axis=1, min_count=7) * 10 / 7, 0.06) == (447, 447)
    # WAIS-IV: the working memory index and the full-scale IQ are stored 0.7 and 2.9 too low. Corrected, they are whole numbers.
    for name, count in [("wais4_imt_index", 471), ("wais4_qit", 447)]:
        index = data[name].dropna()
        assert (len(index), int((index == index.round()).sum())) == (count, count)
    # The Barona differences are the expected IQ minus the estimated one: with the corrected IQ on the WAIS-IV visits.
    # The expected IQs are recomputed with the norms and the differences stay as stored (`derived_from`): where the stored expected IQ
    # was not the recomputed one the difference no longer equals expected minus estimated, and where the expected IQ cannot be
    # recomputed it is not delivered (WAIS review, D138-D143, D48).
    assert same(data["barona_qiv_difference"], data["barona_expected_qiv"] - data["wais3_qiv"]) == (472, 501)
    assert same(data["barona_qip_difference"], data["barona_expected_qip"] - data["wais3_qip"]) == (478, 509)
    assert same(data["barona_qit_difference"], data["barona_expected_qit"] - data["wais4_qit"]) == (298, 304)       # the EMR computed the difference from its stored IQ: 6 visits differ since the IQ follows the recomputed sum (D137); 21 visits gained from WAIS-III (D47)
    assert same(data["barona_qit_difference"], data["barona_expected_qit"] - data["wais4_qi_two_subtests"]) == (143, 151)
    # The Barona occupation mirrors the diploma on 72% of the visits that have both.
    assert (qc.loc["barona_occupation", "n_valid"], qc.loc["barona_occupation", "check_failed"], qc.loc["barona_expected_qit", "check_failed"]) == (1548, 1111, 1111)       # the expected IQ is recomputed: the 32 gained check_failed (WAIS review, D138-D143, D48)
    assert "wais4_imt_index_stored" not in data.columns and "wais4_qit_stored" not in data.columns


def test_neuropsychology_other_tests(qc):
    assert (qc.loc["sstics_total", "n_valid"], qc.loc["sstics_total", "score_mismatch"], qc.loc["sstics_z", "n_valid"]) == (2336, 2, 2336)       # z recomputed: 10 gained, 1 lost (D138-D143, D48)
    assert (qc.loc["lis_a1", "n_valid"], qc.loc["lis_total", "n_valid"]) == (1161, 1147)       # the distance score is recomputed: 137 gained, 7 lost (D138-D143, D48)
    assert (qc.loc["fnart_total", "n_valid"], qc.loc["fnart_total", "score_mismatch"], qc.loc["fnart_qit", "derived_doubt"]) == (1294, 0, 0)       # 610 totals gained as stored, IQs on 1,294 visits (D138-D143, D48)
    assert (qc.loc["cptip_dprime_mean", "n_valid"], qc.loc["cptip_dprime_mean", "score_mismatch"], qc.loc["cptip_percentile", "band_middle"]) == (999, 0, 59)
    assert (qc.loc["six_elements_points", "n_valid"], qc.loc["six_elements_points", "score_mismatch"], qc.loc["six_elements_time", "unparsed"]) == (862, 1, 83)
    # Doors: a percentile "<1" computed from an empty part B is not read again: it is not recomputed (D135).
    assert (qc.loc["doors_total", "n_valid"], qc.loc["doors_b_band", "score_not_recomputed"], qc.loc["doors_a_band", "score_not_recomputed"]) == (771, 172, 1)
    # Laterality: one centre computed the quotient on 12 lines instead of 10.
    assert (qc.loc["laterality_quotient", "n_valid"], qc.loc["laterality_quotient", "score_mismatch"]) == (502, 41)


def shape_of(qc, tab):
    """Variables, instruments, unknown codes and unparsed cells of a tab."""
    lines = qc[qc["tab"] == tab]
    return len(lines), lines["instrument"].nunique(), int(lines["unknown_code"].sum()), int(lines["unparsed"].sum())


def test_suicide_and_comorbidity(result, qc):
    data = result.data
    assert shape_of(qc, "SUICIDE") == (31, 4, 0, 1)
    # Two forms in the same columns: the whole life at inclusion, since the last visit at follow-up.
    assert (qc.loc["isf05_lifetime", "n_valid"], data["isf05_lifetime"].sum(), qc.loc["isf05_since_visit", "n_valid"], data["isf05_since_visit"].sum()) == (2231, 680, 2356, 57)
    assert (qc.loc["first_attempt_date", "n_valid"], qc.loc["first_attempt_date", "date_placeholder"], qc.loc["n_attempts", "n_valid"]) == (562, 114, 2169)
    assert (qc.loc["n_attempts_since_visit", "n_valid"], (data["n_attempts_since_visit"] > 0).sum()) == (2352, 50)       # BP D86, D125: 0 after a "no"
    assert qc.loc[qc.index.str.startswith("isf"), "period_doubt"].sum() == 0          # no doubtful period here, unlike BP

    assert shape_of(qc, "SUBSTANCES ET COMORBIDITE") == (188, 11, 0, 0)       # sedative_route_sniffed is not delivered (D66)
    # Anxiety: a tree of screening questions; a question not shown after a "no" is 0.
    assert (qc.loc["anxiety_disorder_v0", "n_valid"], data["anxiety_disorder_v0"].sum()) == (2104, 826)
    assert (qc.loc["panic_disorder_v0", "n_valid"], data["panic_disorder_v0"].sum(), qc.loc["social_phobia_v0", "n_valid"], data["social_phobia_v0"].sum()) == (1911, 99, 1905, 146)
    # The first substance question is derived by the export from the boxes (D65): "Ne sais pas" on 975 inclusion visits, most of them where the drug boxes are blank.
    assert (qc.loc["substance_disorder_v0", "n_valid"], qc.loc["substance_disorder_v0", "missing_code"], data["substance_disorder_v0"].sum()) == (608, 975, 590)
    # Hidden gates (D63): after "no" to rad_add_4 the five drug boxes are 0, after a "no" to the use question the "never once" question is 0, the number of episodes is 0 after "no" to the depression.
    assert [qc.loc[name, "n_valid"] for name in ["sedative_disorder_v0", "opiate_disorder_v0", "cocaine_disorder_v0", "hallucinogen_disorder_v0", "sedative_disorder_fu", "other_substance_disorder_fu"]] == [1589, 1603, 1578, 1552, 2297, 2283]
    assert (qc.loc["alcohol_never_once", "n_valid"], qc.loc["cannabis_never_once", "n_valid"], qc.loc["gad_v0", "n_valid"], qc.loc["mde_count", "n_valid"]) == (3426, 3372, 1902, 1662)
    assert (qc.loc["alcohol_dose_lifetime", "n_valid"], qc.loc["alcohol_dose_lifetime", "out_of_range"], qc.loc["alcohol_dose_12m", "out_of_range"]) == (1777, 49, 5)         # range 0 to 40 (D66)
    assert (data["alcohol_disorder_v0"].sum(), data["cannabis_disorder_fu"].sum(), data["illicit_drugs_over_ten_times"].sum(), data["heroin_over_ten_times"].sum()) == (313, 553, 479, 55)


def test_medical_evaluation_care_and_social(result, qc):
    data = result.data
    assert shape_of(qc, "PERINATALITE") == (19, 1, 0, 17)
    assert (qc.loc["birth_weight", "n_valid"], qc.loc["gestational_age", "n_valid"]) == (1017, 822)     # per patient, as in BP
    assert shape_of(qc, "EVALUATION MEDICALE") == (92, 3, 0, 2)
    assert (qc.loc["n_psychotic_episodes", "n_valid"], data["symptom_persecution_ever"].sum(), data["violence_verbal"].sum()) == (1899, 1807, 925)
    # The clinical-scales review (D80): the age at the first psychotic episode has its own name (DR's first_episode_age is another question).
    assert qc.loc["first_psychotic_episode_age", "n_valid"] == 2165 and "first_episode_age" not in data.columns
    # The last-month question of the 22 symptoms is 0 after a "no" to the first question (all at inclusion): 43,053 valid cells.
    last_month = [name for name in qc.index if name.endswith("_last_month")]
    assert (len(last_month), int(qc.loc[last_month, "n_valid"].sum())) == (22, 43053)
    # The number of suicide attempts of the past year is 0 after a "no" (+4,319 zeros; the largest is 17).
    assert (qc.loc["n_suicide_attempts_12m", "n_valid"], qc.loc["n_suicide_attempts_12m", "max"]) == (4483, 17)
    # Homicide is delivered since the review: asked after physical violence, 8 yes among 1,798 answers.
    assert (qc.loc["violence_physical_homicide", "n_valid"], data["violence_physical_homicide"].sum()) == (1798, 8)
    assert shape_of(qc, "SOIN SUIVI HOSP ARRET TRAVAIL") == (27, 5, 0, 25)
    assert (qc.loc["first_hospitalisation_age", "n_valid"], qc.loc["hospitalisation_months_v0", "censored_right"], qc.loc["hospitalised_12m", "n_valid"]) == (1868, 105, 4490)
    # The lifetime block is hidden after "Pas d'hospitalisations" (D70): 0 on the 384, 384, 388 and 397 cells that the form hides; "ever hospitalised" is derived from the number by the export (44 "Ne sais pas" read as yes).
    assert [qc.loc[name, "n_valid"] for name in ["ever_hospitalised_v0", "n_hospitalisations_v0", "hospitalisation_months_v0", "first_episode_hospitalisation_weeks"]] == [2251, 2207, 2040, 1670]
    assert (data["ever_hospitalised_v0"].sum(), qc.loc["ever_hospitalised_v0", "derived_doubt"]) == (1812, 44)
    # The number and the weeks of the past year are 0 after a "no" (D70): +3,257 and +3,258 cells.
    assert [qc.loc[name, "n_valid"] for name in ["n_hospitalisations_12m", "hospitalisation_weeks_12m"]] == [4431, 4370]
    # The psychiatric sick leave since the last visit is the BP question, under the BP names; 0 after a "no" (BP D123).
    assert [qc.loc[name, "n_valid"] for name in ["sick_leave_fu", "n_sick_leaves_fu", "sick_leave_weeks_fu", "sick_leave_weeks_12m"]] == [1303, 1286, 1279, 800]
    assert (data.loc[data["sick_leave_fu"] == 0, "sick_leave_weeks_fu"] == 0).all()
    assert shape_of(qc, "SOCIAL - PERINATALITE") == (10, 1, 0, 0)
    # Lost answers: no patient is married or living as a couple (O22).
    assert data["marital_status"].value_counts().to_dict() == {"single": 1652, "divorced": 42, "separated": 30, "widowed": 4}
    # The source of income is not delivered: the export keeps one of the boxes ticked, the first its list finds (D94).
    assert "income_source" not in data.columns


def test_treatments(result, qc):
    items, data, patients = result.treatments, result.data, result.patients
    assert shape_of(qc, "TRAITEMENTS") == (71, 6, 149, 2)
    # One row per patient and medication: every row of a patient holds the same lists.
    assert (len(items), items["usubjid"].nunique(), items["molecule"].nunique()) == (11038, 1975, 122)
    assert qc.loc["medication", "patient_value_varies"] == 0
    # The table of names is shared with BP: 99% of the SZ names are in it.
    assert (qc.loc["molecule", "n_valid"], qc.loc["molecule", "unknown_code"]) == (10889, 149)
    groups = items["treatment_group"].value_counts()
    assert (groups["antipsychotic_2g"], groups["antipsychotic_1g"], groups["antidepressant"], len(groups)) == (5278, 1325, 1492, 10)
    # The ATC code that the EMR gives for part of the medications agrees with the table.
    both = items["atc_coded"].notna() & items["atc"].notna()
    assert (int(both.sum()), int((items.loc[both, "atc_coded"] == items.loc[both, "atc"]).sum())) == (3322, 3314)
    assert (qc.loc["start_date", "n_valid"], qc.loc["end_date", "n_valid"], qc.loc["end_date", "missing_code"]) == (11038, 5792, 5246)
    assert (data["on_antipsychotic_2g"].notna().sum(), round(data["on_antipsychotic_2g"].mean(), 2)) == (5884, 0.88)
    # The daily dose in mg from the strength in the name: SZ stores no strength (BP D124).
    assert (items["daily_dose"].notna().sum(), (items["strength_from_name"] == 1).sum(), qc.loc["end_date", "check_failed"]) == (9014, 6504, 41)
    assert qc.loc["daily_dose", "out_of_range"] == 8            # laxatives in grams, 5.9 g or 10 g a unit
    assert round(data.loc[data["visit"] == "V0", "on_clozapine"].mean(), 2) == 0.18
    # The counts of the export are one value per patient, not per visit.
    assert patients["n_listed_antipsychotics"].notna().sum() == 1975 and "n_listed_antipsychotics" not in data.columns
    assert (qc.loc["non_drug_treatment_fu", "n_valid"], data["non_drug_treatment_fu"].sum(), data["cbt_fu"].sum()) == (2254, 836, 376)
    assert (data["treatment_help_autonomous"].sum(), data["care_change"].sum()) == (2974, 647)
    # The eight started/ended boxes of the care changes are 0 after a "no" and beside a ticked approach (D72): 2,418 + 422 visits, +21,594 cells.
    boxes = [f"{kind}_{when}" for kind in ["cbt", "cognitive_remediation", "psychodynamic", "family_approach"] for when in ["started", "ended"]]
    assert [int(qc.loc[name, "n_valid"]) for name in boxes] == [2836] * 8


def test_medical_and_family_history(result, qc):
    data, patients, relatives = result.data, result.patients, result.relatives
    assert shape_of(qc, "ANTECEDENTS") == (215, 21, 0, 0)
    # The two migraine columns are swapped in the extraction; the schema reads them the other way round.
    assert (data["migraine_v0"].notna().sum(), data["migraine_v0"].sum(), data["migraine_treated_v0"].notna().sum()) == (2046, 157, 143)
    assert (data["head_injury_v0"].sum(), data["head_injury_fu"].notna().sum(), data["head_injury_fu"].sum()) == (202, 397, 14)
    assert (data["dyslipidaemia_v0"].sum(), data["asthma_v0"].notna().sum(), data["asthma_v0"].sum(), data["psoriasis_v0"].sum()) == (233, 2021, 192, 30)
    assert (len(relatives), relatives["usubjid"].nunique()) == (1887, 1200)
    assert relatives["kinship"].value_counts().to_dict() == {"mother": 688, "father": 659, "brother": 294, "sister": 239, "daughter": 6, "son": 1}
    assert [int((patients[name] == 1).sum()) for name in ["fdr_bipolar", "fdr_depression", "fdr_schizophrenia", "fdr_suicide", "fdr_suicide_attempt"]] == [110, 506, 158, 42, 189]
    assert patients["n_sisters"].notna().sum() == 2066


def test_coverage():
    """Every column of the extraction is read by a schema or ignored with a reason."""
    table = sz.coverage(EXTRACTION, THESAURUS)
    counts = table["status"].value_counts().to_dict()
    assert (counts["covered"], counts["ignored"], counts.get("not_assigned", 0)) == (1685, 53, 0)
    assert counts["covered"] + counts["ignored"] == 1738


def test_nothing_disappears_silently():
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    for schema in load_schemas(sz.SCHEMAS).values():
        if schema.get("level") == "list":            # cells that hold lists: the invariant holds on the items
            items, item_keys, list_flags = open_lists(raw, keys, schema)
            assert_invariant(items, item_keys, schema)
        elif schema.get("level") == "relatives":     # one row per relative: the invariant holds on these rows
            rows, row_keys, varying_flags = stack_relatives(raw, keys, schema)
            assert_invariant(rows, row_keys, schema)
        elif "derived_from" not in schema:           # columns computed from other rows have no raw cell
            assert_invariant(raw, keys, schema)
