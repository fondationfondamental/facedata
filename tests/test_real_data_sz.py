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
EXTRACTION = ROOT / "data" / "sz" / "SZALL_20261117.tsv"
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
    assert len(result.data) == 6616
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 2353 == len(result.patients)
    # A screening row for seven patients in ten, and yearly visits: no six-month visit.
    visits = result.data["visit"].value_counts()
    assert (visits["V0"], visits["screening"], visits["V1_an"]) == (2353, 1675, 1012)
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
    assert (reason["n_filled"], reason["n_valid"], reason["missing_code"]) == (583, 492, 91)
    # The column named for the cause of death holds the date of death, for patients recorded as deceased only.
    deceased = patients["followup_end_reason"] == "deceased"
    assert (deceased.sum(), patients.loc[deceased, "death_date"].notna().sum()) == (12, 8)
    assert patients.loc[~deceased, "death_date"].isna().all()
    assert result.data["entry_date"].notna().all()


def test_hetero_questionnaires(result, qc):
    tab = qc[qc["tab"] == "HETERO-QUESTIONNAIRE"]
    assert (len(tab), tab["instrument"].nunique()) == (130, 10)
    assert tab[["unknown_code", "unparsed"]].sum().sum() == 0
    # PANSS: the three scales, the total and the fifteen factor scores are the sums of their items.
    panss = tab[tab["instrument"] == "panss"]
    assert (len(panss), panss["score_mismatch"].sum()) == (49, 0)
    stored = result.flags[result.flags["variable"].str.startswith("panss_") & result.flags["variable"].str.endswith("_stored")]
    assert len(stored) == 0                               # every stored PANSS score is inside its limits and compared
    assert (qc.loc["panss_total", "n_valid"], qc.loc["panss_total", "min"], qc.loc["panss_total", "max"]) == (4646, 30, 160)
    assert (qc.loc["panss_wallwork_positive", "n_valid"], qc.loc["panss_vandergaag_disorganised", "n_valid"]) == (4663, 4655)
    # Three factor scores follow their publication, not the stored formula, which sums a wrong item.
    data = result.data
    for name, items in [("panss_wallwork_positive", ["p1", "p3", "p5", "g9"]), ("panss_wallwork_negative", ["n1", "n2", "n3", "n4", "n6", "g7"]),
                        ("panss_lancon_negative", ["n1", "n2", "n3", "n4", "n6", "g7", "g16"])]:
        published = data[["panss_" + item for item in items]].sum(axis=1, min_count=len(items))
        assert published.equals(data[name]), name
        assert name + "_as_stored" not in data.columns            # the stored formula is only a check
    assert (qc.loc["panss_wallwork_negative", "n_valid"], qc.loc["panss_lancon_negative", "n_valid"]) == (4662, 4660)
    # Calgary: eight items; item 8 is not in the extraction, so no CDSS total.
    assert (qc.loc["calgary_sum8", "n_valid"], qc.loc["calgary_sum8", "max"]) == (4672, 20)
    assert "calgary08" not in result.data.columns and "calgary_total" not in result.data.columns
    # YMRS: items 5, 8 and 9 are stored as levels (0 to 4) and delivered in points, as published and as in BP (D26).
    assert (qc.loc["ymrs_total", "n_valid"], qc.loc["ymrs_total", "score_mismatch"], qc.loc["ymrs_total", "max"]) == (4538, 0, 38)
    for item in ["ymrs05", "ymrs06", "ymrs08", "ymrs09"]:
        assert set(data[item].dropna()) <= {0, 2, 4, 6, 8}, item
    assert "ymrs_total_as_stored" not in data.columns and (result.flags["variable"] == "ymrs_total_as_stored").sum() == 0     # the twin equals the stored total
    higher = data["ymrs_total"].notna() & (data["ymrs05"] + data["ymrs08"] + data["ymrs09"] > 0)
    assert higher.sum() == 776                                     # visits whose published total is above the stored one
    assert (qc.loc["barnes_sum", "score_mismatch"], qc.loc["esrsa_mean", "score_mismatch"]) == (3, 10)
    assert (qc.loc["cgi_efficacy_index", "check_failed"], qc.loc["psp_band", "check_failed"]) == (23, 215)
    assert (qc.loc["bars_doses_per_day", "out_of_range"], qc.loc["psp_total", "out_of_range"]) == (250, 3)
    assert (qc.loc["cgi_severity", "missing_code"], qc.loc["cgi_improvement", "missing_code"]) == (12, 125)
    # The improvement, the therapeutic effect and the index are asked at the follow-up visits only, as in BP.
    assert (qc.loc["cgi_improvement", "n_valid"], data.loc[data["visit_month"] == 0, "cgi_improvement"].notna().sum()) == (2195, 0)
    # SUMD: 0 is "cannot be rated", a missing code.
    assert (qc.loc["sumd01", "missing_code"], qc.loc["sumd04_awareness", "missing_code"]) == (29, 2121)
    assert (qc.loc["aims_movements", "n_valid"], qc.loc["bars_adherence", "n_valid"], qc.loc["gaf", "n_valid"]) == (4149, 4383, 4534)


def test_vitals_and_ecg(result, qc):
    # None of the scale errors of BP: no height in millimetres, no weight with a lost decimal point.
    assert (qc.loc["height", "n_valid"], qc.loc["height", "out_of_range"], qc.loc["height", "unit_inferred"]) == (4318, 3, 0)
    assert (qc.loc["weight", "n_valid"], qc.loc["weight", "out_of_range"], qc.loc["waist", "out_of_range"]) == (4322, 1, 9)
    assert (qc.loc["bmi", "n_valid"], qc.loc["bmi", "score_mismatch"]) == (4303, 0)
    assert (qc.loc["systolic_supine", "n_valid"], qc.loc["diastolic_supine", "unit_inferred"]) == (4123, 1)
    assert (qc.loc["qtc_stored", "n_valid"], qc.loc["qtc_stored", "out_of_range"], qc.loc["qtc_stored", "unit_inferred"]) == (2828, 27, 1)


def test_biology(qc):
    tab = qc[qc["tab"] == "BILAN BIOLOGIQUE"]
    assert (len(tab), tab["instrument"].nunique(), tab["unparsed"].sum()) == (27, 7, 0)
    crp, glucose, haemoglobin = qc.loc["crp"], qc.loc["glucose"], qc.loc["haemoglobin"]
    assert (crp["n_valid"], crp["censored_left"], crp["censored_right"]) == (3086, 334, 1)
    assert crp["missing_code"] == 477                                   # a CRP of exactly 0 is not a measurement (BP D101)
    assert (glucose["n_valid"], glucose["unit_converted"], glucose["unit_inferred"], glucose["out_of_range"]) == (3136, 66, 17, 3)
    assert (haemoglobin["n_valid"], haemoglobin["unit_inferred"], haemoglobin["out_of_range"]) == (3658, 34, 4)
    assert (qc.loc["neutrophils", "unit_inferred"], qc.loc["eosinophils", "unit_doubt"]) == (23, 37)
    # The stored cholesterol ratio is not the ratio of the stored values on 4% of the visits.
    assert (qc.loc["cholesterol_hdl_ratio", "n_valid"], qc.loc["cholesterol_hdl_ratio", "score_mismatch"]) == (3578, 157)
    prolactin = qc.loc["prolactin"]
    assert (prolactin["n_valid"], prolactin["unit_converted"], prolactin["unit_inferred"]) == (2985, 633, 139)
    assert (prolactin["unit_unknown"], prolactin["unit_doubt"], prolactin["out_of_range"]) == (162, 36, 67)
    assert (qc.loc["clozapine", "n_valid"], qc.loc["clozapine", "unit_inferred"], qc.loc["clozapine_treated", "n_valid"]) == (592, 11, 1600)
    assert (qc.loc["vitamin_d_as_written", "n_valid"], qc.loc["vitamin_d_as_written", "censored_left"], qc.loc["vitamin_d_as_written", "out_of_range"]) == (2718, 11, 2)
    assert (qc.loc["toxo_igg_titre", "n_valid"], qc.loc["toxo_igg_titre", "censored_right"], qc.loc["toxo_serology", "n_valid"]) == (632, 16, 2828)


def test_auto_questionnaires(result, qc):
    tab = qc[qc["tab"] == "AUTO-QUESTIONNAIRE"]
    assert (len(tab), tab["instrument"].nunique(), tab["unknown_code"].sum()) == (475, 21, 0)
    for name in ["ctq_total", "eq5d_index", "fagerstrom_total", "wurs_sum25", "sqol_index", "sqol_resilience"]:
        assert qc.loc[name, "score_mismatch"] == 0, name
    counts = (qc.loc["ctq_total", "n_valid"], qc.loc["eq5d_index", "n_valid"], qc.loc["fagerstrom_total", "n_valid"], qc.loc["wurs_sum25", "n_valid"])
    assert counts == (2166, 3909, 1981, 295)
    assert (qc.loc["mars_total", "n_valid"], qc.loc["mars_total", "score_mismatch"]) == (4266, 2)
    assert (qc.loc["psqi_total", "n_valid"], qc.loc["psqi_total", "score_mismatch"], qc.loc["psqi_latency", "unparsed"]) == (2954, 11, 26)
    assert (qc.loc["birchwood_total", "n_valid"], qc.loc["birchwood_total", "score_mismatch"]) == (4244, 5)
    # S-QoL: items 17 and 18 hold only three of their five answers; the stored dimension is delivered.
    assert (qc.loc["sqol16", "n_valid"], qc.loc["sqol17", "n_valid"], qc.loc["sqol18", "n_valid"]) == (4267, 2734, 2784)
    assert set(result.data["sqol17"].dropna()) == {2.0, 4.0, 5.0}
    assert (qc.loc["sqol_psychological_wellbeing", "n_valid"], qc.loc["sqol_index", "n_valid"]) == (3506, 3033)
    assert (qc.loc["stori_stage1", "n_valid"], qc.loc["stori_stage1", "score_mismatch"]) == (3089, 2)
    assert (qc.loc["ephp_total", "n_valid"], qc.loc["ephp_total", "score_mismatch"], tab.loc[tab["instrument"] == "ephp", "missing_code"].sum()) == (1557, 4, 377)
    assert (qc.loc["ybocs_total", "n_valid"], qc.loc["ybocs_total", "score_mismatch"], qc.loc["sogs_total", "n_valid"]) == (281, 28, 122)
    assert (tab.loc[tab["instrument"] == "presenteeism", "out_of_range"].sum(), tab.loc[tab["instrument"] == "physical_activity", "out_of_range"].sum()) == (13, 4)
    # Seven substances, the same twelve criteria; "do not know" is a missing code.
    assert (qc.loc["alcohol_larger_amounts", "n_valid"], qc.loc["alcohol_larger_amounts", "missing_code"], qc.loc["heroin_tolerance", "n_valid"]) == (2035, 9, 38)


def test_neuropsychology_first_part(result, qc):
    tab = qc[qc["tab"] == "NEUROPSYCHOLOGIE"]
    assert (len(tab), tab["instrument"].nunique(), tab["unknown_code"].sum()) == (662, 30, 0)
    data = result.data
    assert data["wais_version"].value_counts().to_dict() == {"wais4": 2654, "wais3": 781}
    # The years of education are exported for every assessment since the extraction of 17 November 2026
    # (776 visits until 2016 before): the TMT error norms can be read on every visit.
    assert (qc.loc["education_years", "n_valid"], qc.loc["education_years", "last_year"]) == (3449, 2026)
    assert (qc.loc["tmt_a_errors_band", "n_valid"], qc.loc["tmt_a_errors_band", "norm_missing"]) == (3107, 0)
    # A suspected learning disorder: several kinds can be ticked, one box each, 0 after a "no".
    assert (qc.loc["neuropsy_dyslexia", "n_valid"], (data["neuropsy_dyslexia"] == 1).sum(), (data["neuropsy_dyspraxia"] == 1).sum()) == (2851, 203, 42)
    # One centre's 23 early visits mix the two sign conventions (mean correlation 0.24 the wrong way): too weak
    # to flip, so the scores stay as written and are doubted.
    assert (qc.loc["tmt_a_time", "n_valid"], qc.loc["tmt_a_time_z", "sign_flipped"], qc.loc["tmt_a_time_z", "sign_doubt"]) == (3210, 0, 23)
    assert (qc.loc["errands_errors", "n_valid"], qc.loc["errands_errors", "score_mismatch"], qc.loc["fluency_p_rule_breaks", "score_mismatch"]) == (1023, 0, 0)
    # WAIS-IV matrices: items 25 and 26 are copies of item 24 in the extraction, so the total is the stored one.
    assert "wais4_mat25" not in data.columns and "wais4_mat26" not in data.columns
    assert (qc.loc["wais3_mat_total", "n_valid"], qc.loc["wais3_mat_total", "score_mismatch"], qc.loc["wais4_mat_total", "n_valid"]) == (568, 4, 1867)
    # Digit span: the summary columns hold what their labels say (they are shifted in BP).
    checks = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts()
    # The check scores are not delivered: their mismatch is filed under the stored total that the analyst sees.
    assert (qc.loc["wais4_ds_total", "n_valid"], checks.get("wais4_ds_total", 0), checks.get("wais3_ds_total", 0)) == (2494, 0, 30)


def same(stored, formula, tolerance=0.011):
    """How many rows agree, and how many hold both values."""
    both = stored.notna() & formula.notna()
    return int(((stored - formula).abs() <= tolerance)[both].sum()), int(both.sum())


def test_cvlt_and_wais(result, qc):
    data = result.data
    # CVLT: the z-scores are computed again with the regressions of the norms, as in BP. From October 2021 to June 2026
    # the application computed part of the z-scores of trials 1 to 5 with two coefficients exchanged: they differ from the stored ones.
    assert (qc.loc["cvlt_total_1_5", "n_valid"], qc.loc["cvlt_total_1_5_z", "n_valid"], qc.loc["cvlt_total_1_5_z", "out_of_range"]) == (2275, 2275, 0)
    assert (qc.loc["cvlt_total_1_5_z", "score_mismatch"], qc.loc["cvlt_total_1_5_z", "norm_missing"], qc.loc["cvlt_trial1_z", "score_mismatch"]) == (333, 0, 5)
    total_z = data["cvlt_total_1_5_z"]
    from_2022 = data["visit_date"].dt.year >= 2022
    assert abs(total_z[from_2022].median() - total_z[~from_2022].median()) < 0.3      # the stored ones were 3 points apart
    assert (qc.loc["cvlt_total_1_5_band", "n_valid"], qc.loc["cvlt_short_free_band", "band_from_z"]) == (2275, 496)
    assert not [name for name in data.columns if name.startswith("cvlt") and name.endswith("_stored")]
    # WAIS-IV similarities: items 10 and 11 are the same cell twice, so the total is the stored one.
    assert (qc.loc["wais3_simil_total", "n_valid"], qc.loc["wais3_simil_total", "score_mismatch"], qc.loc["wais4_simil_total", "n_valid"]) == (570, 12, 1865)
    # The sums of scaled scores are those of a seven-subtest short form. The scaled scores are in other schemas.
    w3_verbal = 2 * data["wais3_simil_scaled"] + 2 * data["wais3_info_scaled"] + data["wais3_arith_scaled"] + data["wais3_ds_scaled"]
    w3_performance = 2 * data["wais3_pc_scaled"] + 2 * data["wais3_mat_scaled"] + data["wais3_code_scaled"]
    assert same(data["wais3_qiv_sum_scaled"], w3_verbal) == (528, 528)
    assert same(data["wais3_qip_sum_scaled"], w3_performance) == (539, 539)
    assert same(data["wais3_imt_sum_scaled"], data["wais3_ds_scaled"] + data["wais3_arith_scaled"] + data["wais3_lns_scaled"]) == (472, 472)
    assert same(data["wais4_icv_sum_scaled"], 1.5 * (data["wais4_simil_scaled"] + data["wais4_info_scaled"])) == (455, 456)
    assert same(data["wais4_irp_sum_scaled"], 1.5 * (data["wais4_mat_scaled"] + data["wais4_pc_scaled"])) == (451, 451)
    assert same(data["wais4_imt_sum_scaled"], data["wais4_ds_scaled"] + data["wais4_arith_scaled"]) == (445, 447)
    seven = ["wais4_simil_scaled", "wais4_info_scaled", "wais4_arith_scaled", "wais4_ds_scaled", "wais4_pc_scaled", "wais4_mat_scaled", "wais4_code_scaled"]
    assert same(data["wais4_qit_sum_scaled"], data[seven].sum(axis=1, min_count=7) * 10 / 7, 0.06) == (428, 430)
    # WAIS-IV: the working memory index and the full-scale IQ are stored 0.7 and 2.9 too low. Corrected, they are whole numbers.
    for name, count in [("wais4_imt_index", 447), ("wais4_qit", 430)]:
        index = data[name].dropna()
        assert (len(index), int((index == index.round()).sum())) == (count, count)
    # The Barona differences are the expected IQ minus the estimated one: with the corrected IQ on the WAIS-IV visits.
    assert same(data["barona_qiv_difference"], data["barona_expected_qiv"] - data["wais3_qiv"]) == (508, 508)
    assert same(data["barona_qip_difference"], data["barona_expected_qip"] - data["wais3_qip"]) == (516, 516)
    assert same(data["barona_qit_difference"], data["barona_expected_qit"] - data["wais4_qit"]) == (292, 293)
    assert same(data["barona_qit_difference"], data["barona_expected_qit"] - data["wais4_qi_two_subtests"]) == (154, 161)
    # The Barona occupation mirrors the diploma on 72% of the visits that have both.
    assert (qc.loc["barona_occupation", "n_valid"], qc.loc["barona_occupation", "check_failed"], qc.loc["barona_expected_qit", "check_failed"]) == (1548, 1111, 1079)
    assert "wais4_imt_index_stored" not in data.columns and "wais4_qit_stored" not in data.columns


def test_neuropsychology_other_tests(qc):
    assert (qc.loc["sstics_total", "n_valid"], qc.loc["sstics_total", "score_mismatch"], qc.loc["sstics_z", "n_valid"]) == (2338, 2, 2329)
    assert (qc.loc["lis_a1", "n_valid"], qc.loc["lis_total", "n_valid"]) == (1162, 1018)
    assert (qc.loc["fnart_total", "n_valid"], qc.loc["fnart_total", "score_mismatch"], qc.loc["fnart_qit", "derived_doubt"]) == (684, 0, 0)
    assert (qc.loc["cptip_dprime_mean", "n_valid"], qc.loc["cptip_dprime_mean", "score_mismatch"], qc.loc["cptip_percentile", "band_middle"]) == (999, 0, 59)
    assert (qc.loc["six_elements_points", "n_valid"], qc.loc["six_elements_points", "score_mismatch"], qc.loc["six_elements_time", "unparsed"]) == (862, 1, 83)
    # Doors: a percentile "<1" computed from an empty part B.
    assert (qc.loc["doors_total", "n_valid"], qc.loc["doors_b_band", "derived_doubt"], qc.loc["doors_a_band", "derived_doubt"]) == (771, 172, 1)
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
    assert (qc.loc["isf05_lifetime", "n_valid"], data["isf05_lifetime"].sum(), qc.loc["isf05_since_visit", "n_valid"], data["isf05_since_visit"].sum()) == (2231, 680, 2360, 57)
    assert (qc.loc["first_attempt_date", "n_valid"], qc.loc["first_attempt_date", "date_placeholder"], qc.loc["n_attempts", "n_valid"]) == (562, 114, 2169)
    assert (qc.loc["n_attempts_since_visit", "n_valid"], (data["n_attempts_since_visit"] > 0).sum()) == (2356, 50)       # BP D86, D125: 0 after a "no"
    assert qc.loc[qc.index.str.startswith("isf"), "period_doubt"].sum() == 0          # no doubtful period here, unlike BP

    assert shape_of(qc, "SUBSTANCES ET COMORBIDITE") == (189, 11, 0, 0)
    # Anxiety: a tree of screening questions; a question not shown after a "no" is 0.
    assert (qc.loc["anxiety_disorder_v0", "n_valid"], data["anxiety_disorder_v0"].sum()) == (2104, 826)
    assert (qc.loc["panic_without_agora_v0", "n_valid"], data["panic_without_agora_v0"].sum(), qc.loc["social_phobia_v0", "n_valid"], data["social_phobia_v0"].sum()) == (1911, 99, 1905, 146)
    # The first substance question holds "Ne sais pas" where "no" is expected at inclusion; the boxes are complete.
    assert (qc.loc["substance_disorder_v0", "n_valid"], qc.loc["substance_disorder_v0", "missing_code"], data["substance_disorder_v0"].sum()) == (608, 975, 590)
    assert (data["alcohol_disorder_v0"].sum(), data["cannabis_disorder_fu"].sum(), data["illicit_drugs_ever"].sum(), data["heroin_ever"].sum()) == (313, 553, 481, 55)


def test_medical_evaluation_care_and_social(result, qc):
    data = result.data
    assert shape_of(qc, "PERINATALITE") == (19, 1, 0, 17)
    assert (qc.loc["birth_weight", "n_valid"], qc.loc["gestational_age", "n_valid"]) == (1017, 822)     # per patient, as in BP
    assert shape_of(qc, "EVALUATION MEDICALE") == (91, 3, 0, 2)
    assert (qc.loc["n_psychotic_episodes", "n_valid"], data["symptom_persecution_ever"].sum(), data["violence_verbal"].sum()) == (1899, 1807, 925)
    assert shape_of(qc, "SOIN SUIVI HOSP ARRET TRAVAIL") == (27, 5, 0, 25)
    assert (qc.loc["first_hospitalisation_age", "n_valid"], qc.loc["hospitalisation_months_v0", "censored_right"], qc.loc["hospitalised_12m", "n_valid"]) == (1868, 105, 4494)
    # The psychiatric sick leave since the last visit is the BP question, under the BP names; 0 after a "no" (BP D123).
    assert [qc.loc[name, "n_valid"] for name in ["sick_leave_fu", "n_sick_leaves_fu", "sick_leave_weeks_fu", "sick_leave_weeks_12m"]] == [1306, 1288, 1283, 797]
    assert (data.loc[data["sick_leave_fu"] == 0, "sick_leave_weeks_fu"] == 0).all()
    assert shape_of(qc, "SOCIAL - PERINATALITE") == (11, 1, 0, 0)
    # Lost answers: no patient is married or living as a couple, none has a salary or a disability pension.
    assert data["marital_status"].value_counts().to_dict() == {"single": 1652, "divorced": 42, "separated": 30, "widowed": 4}
    assert set(data["income_source"].dropna()) == {"disability_allowance", "other", "no_income", "minimum_income", "unemployment_benefit", "housing_benefit"}


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
    assert (data["on_antipsychotic_2g"].notna().sum(), round(data["on_antipsychotic_2g"].mean(), 2)) == (5888, 0.88)
    # The daily dose in mg from the strength in the name: SZ stores no strength (BP D124).
    assert (items["daily_dose"].notna().sum(), (items["strength_from_name"] == 1).sum(), qc.loc["end_date", "check_failed"]) == (9014, 6504, 41)
    assert qc.loc["daily_dose", "out_of_range"] == 8            # laxatives in grams, 5.9 g or 10 g a unit
    assert round(data.loc[data["visit"] == "V0", "on_clozapine"].mean(), 2) == 0.18
    # The counts of the export are one value per patient, not per visit.
    assert patients["n_listed_antipsychotics"].notna().sum() == 1975 and "n_listed_antipsychotics" not in data.columns
    assert (qc.loc["non_drug_treatment_fu", "n_valid"], data["non_drug_treatment_fu"].sum(), data["cbt_fu"].sum()) == (2257, 836, 376)
    assert (data["treatment_help_alone"].sum(), data["care_change"].sum()) == (2977, 648)


def test_medical_and_family_history(result, qc):
    data, patients, relatives = result.data, result.patients, result.relatives
    assert shape_of(qc, "ANTECEDENTS") == (215, 21, 0, 0)
    # The two migraine columns are swapped in the extraction; the schema reads them the other way round.
    assert (data["migraine_v0"].notna().sum(), data["migraine_v0"].sum(), data["migraine_treated_v0"].notna().sum()) == (2046, 157, 143)
    assert (data["head_injury_v0"].sum(), data["head_injury_fu"].notna().sum(), data["head_injury_fu"].sum()) == (202, 398, 14)
    assert (data["dyslipidaemia_v0"].sum(), data["asthma_v0"].notna().sum(), data["asthma_v0"].sum(), data["psoriasis_v0"].sum()) == (233, 2021, 192, 30)
    assert (len(relatives), relatives["usubjid"].nunique()) == (1887, 1200)
    assert relatives["kinship"].value_counts().to_dict() == {"mother": 688, "father": 659, "brother": 294, "sister": 239, "daughter": 6, "son": 1}
    assert [int((patients[name] == 1).sum()) for name in ["fdr_bipolar", "fdr_depression", "fdr_schizophrenia", "fdr_suicide", "fdr_suicide_attempt"]] == [110, 506, 158, 42, 189]
    assert patients["n_sisters"].notna().sum() == 2066


def test_coverage():
    """Every column of the extraction is read by a schema or ignored with a reason."""
    table = sz.coverage(EXTRACTION, THESAURUS)
    counts = table["status"].value_counts().to_dict()
    assert (counts["covered"], counts["ignored"], counts.get("not_assigned", 0)) == (1667, 53, 0)
    assert counts["covered"] + counts["ignored"] == 1720


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
