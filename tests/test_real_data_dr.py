"""The real FACE DR extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/dr/PROGRESS.md ("What the schemas
must produce"). No patient row appears here.
"""

from pathlib import Path

import pandas as pd
import pytest

from facedata import dr
from facedata.read import prepare_visits, read_extraction
from facedata.relatives import stack_relatives
from facedata.schema import load_schemas
from facedata.treatments import open_lists
from test_pipeline import assert_invariant

ROOT = Path(__file__).parent.parent
EXTRACTION = ROOT / "data" / "dr" / "DRALL_20261030.tsv"
THESAURUS = ROOT / "thesauri" / "FACEDR_thesaurus_V4.16.xlsx"
NORMS = ROOT / "norms"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the DR extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return dr.load(EXTRACTION, norms=NORMS)


@pytest.fixture(scope="module")
def qc(result):
    return result.qc.set_index("variable")


def test_visits(result):
    assert len(result.data) == 2193
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 634 == len(result.patients)
    # Every patient has a screening visit and an inclusion visit; then 6, 12, 18, 24 months and 4 years.
    visits = result.data["visit"].value_counts()
    assert (visits["screening"], visits["V0"], visits["V6_mois"], visits["V1_an"]) == (634, 634, 298, 253)
    assert (visits["V18_mois"], visits["V2_ans"], visits["V4_ans"]) == (150, 146, 69)
    assert (result.data["visit"] == "").sum() == 1                       # one row has no visit label
    assert result.flags[result.flags["flag"] == "visit_order"].shape[0] == 14
    # The export writes the centre codes as numbers; they are delivered with two digits, as in BP and SZ.
    assert set(result.data["siteid"].str.len()) == {2} and result.data["siteid"].nunique() == 14


def test_the_three_cohorts_can_be_stacked(result):
    from facedata import bp, sz
    files = {"bp": ROOT / "data" / "bp" / "BPALL_20261113_2.tsv", "sz": ROOT / "data" / "sz" / "SZALL_20261117.tsv"}
    if not all(path.exists() for path in files.values()):
        pytest.skip("the BP or the SZ extraction is not on this computer")
    for table in [result.data, result.patients, result.flags, result.treatments, result.relatives]:
        assert table.columns[0] == "cohort" and set(table["cohort"]) <= {"dr"}
    shared = ["cohort", "usubjid", "fondacode", "sex", "diagnosis", "birth_date", "age_at_inclusion"]
    others = [bp.load(files["bp"], instruments=["identite"]).patients[shared], sz.load(files["sz"], instruments=["identite"]).patients[shared]]
    patients = pd.concat(others + [result.patients[shared]], ignore_index=True)
    assert len(patients) == 6498 + 2353 + 634
    assert not patients.duplicated(["cohort", "usubjid"]).any()
    assert patients["fondacode"].is_unique
    # A usubjid is a number given inside a cohort: 199 DR numbers are BP numbers and 209 are SZ numbers.
    numbers = {cohort: set(group["usubjid"]) for cohort, group in patients.groupby("cohort")}
    assert (len(numbers["dr"] & numbers["bp"]), len(numbers["dr"] & numbers["sz"])) == (199, 209)
    assert (patients["birth_date"].dt.day == 15).all()


def test_patient_and_inclusion_tabs(result, qc):
    patients = result.patients
    assert patients["sex"].value_counts().to_dict() == {"female": 370, "male": 264}
    assert patients["diagnosis"].value_counts().to_dict() == {"major_depressive_disorder": 634}
    # The stored age was computed at a later date for the patients who came back: the age at inclusion is recomputed.
    assert (patients["age_at_inclusion"].notna().sum(), patients["age_at_inclusion"].median()) == (634, 51)
    assert (qc.loc["age_at_inclusion", "score_mismatch"], qc.loc["birth_date", "date_partial"]) == (71, 88)
    assert (qc.loc["referred_by", "n_valid"], qc.loc["visit_purpose_code", "n_valid"]) == (111, 593)
    assert patients["visit_purpose_code"].value_counts().to_dict() == {"code_3": 307, "code_2": 250, "code_1": 36}
    assert qc.loc[qc["tab"].isin(["PATIENT", "INCLUSION"]), ["unknown_code", "unparsed", "out_of_range", "patient_value_varies"]].sum().sum() == 0
    # The criteria are ticked at the screening visit, for all patients but one.
    screening = result.data[result.data["visit"] == "screening"]
    assert (screening["eligible"].notna().sum(), result.data["eligible"].notna().sum()) == (633, 633)
    assert qc.loc["criterion_depressive_episode", "n_valid"] == 633


def test_hetero_questionnaires(result, qc):
    tab = result.qc[result.qc["tab"] == "HETERO-QUESTIONNAIRES"]
    assert (len(tab), tab["instrument"].nunique()) == (271, 12)
    assert tab[["unknown_code", "unparsed", "version_unknown"]].sum().sum() == 0
    # Stored totals that follow their items on every visit: MADRS, YMRS, FAST, BAS, and the ERD on items 1 to 14.
    for score, visits in [("madrs_total", 2065), ("ymrs_total", 1033), ("fast_total", 513), ("bas_total", 1038), ("erd_total", 518)]:
        assert (qc.loc[score, "n_valid"], qc.loc[score, "score_mismatch"]) == (visits, 0)
    # SACHS (Bipolarity Index): the ratings are read the way the stored total counts them; 4 totals still differ.
    assert (qc.loc["sachs_total", "n_valid"], qc.loc["sachs_total", "score_mismatch"]) == (243, 4)
    assert set(result.data["sachs_course"].dropna().unique()) <= {0, 2, 5, 10, 15, 20}
    # The MADRS is rated at screening and again at inclusion; the Thase and Rush stage at screening only.
    visits = result.data.loc[result.data["madrs_total"].notna(), "visit"].value_counts()
    assert (visits["screening"], visits["V0"]) == (561, 605)
    stage = result.data.loc[result.data["visit"] == "screening", "thase_rush_stage"]
    assert stage.value_counts().sort_index().tail(4).to_dict() == {2.0: 256, 3.0: 211, 4.0: 22, 5.0: 26}
    assert result.data["thase_rush_stage"].notna().sum() == 517
    # Current depressive episode: two forms of the weight and sleep details, never in one column.
    data = result.data
    assert data["etatd_detail_form"].value_counts().to_dict() == {"list": 1132, "boxes": 348}
    assert data["etatd03a"].value_counts().to_dict() == {"gain": 261, "loss": 161, "loss_and_gain": 29}
    assert data["etatd04a"].value_counts().to_dict() == {"insomnia": 397, "hypersomnia": 142, "insomnia_and_hypersomnia": 15}
    assert data.loc[data["etatd_detail_form"] == "list", ["etatd03_loss_box", "etatd04_insomnia_box"]].notna().sum().sum() == 0
    assert data.loc[data["etatd_detail_form"] == "boxes", ["etatd03a", "etatd04a"]].notna().sum().sum() == 0
    assert (qc.loc["etatd_total", "n_valid"], qc.loc["etatm_total", "n_valid"]) == (1403, 1432)
    assert (qc.loc["cgi_severity", "n_valid"], qc.loc["cgi_severity", "missing_code"], qc.loc["gaf", "n_valid"]) == (1432, 2, 1351)
    assert (qc.loc["amiel_events", "n_valid"], qc.loc["athf_venlafaxine", "n_valid"]) == (483, 1035)
    assert tab["out_of_range"].sum() == 0


def test_vital_signs_and_ecg(result, qc):
    tab = result.qc[result.qc["tab"] == "VITAL SIGN et ECG"]
    assert (len(tab), tab["instrument"].nunique()) == (15, 3)
    assert tab[["unknown_code", "unparsed"]].sum().sum() == 0
    assert (qc.loc["height", "n_valid"], qc.loc["weight", "n_valid"], qc.loc["weight", "unit_inferred"]) == (1280, 1278, 10)
    # The stored body mass index is cut to one decimal from 2017, or keeps a typing error: 59 differ.
    assert (qc.loc["bmi", "n_valid"], qc.loc["bmi", "score_mismatch"]) == (1275, 59)
    assert (qc.loc["systolic_supine", "n_valid"], qc.loc["systolic_supine", "unit_inferred"], qc.loc["systolic_standing", "n_valid"]) == (1223, 7, 1186)
    # QT and RR typed in milliseconds, most of them until 2016; the stored QTc follows Bazett since 2017.
    assert (qc.loc["qt_interval", "unit_inferred"], qc.loc["rr_interval", "unit_inferred"], qc.loc["rr_interval", "out_of_range"]) == (87, 61, 38)
    assert (qc.loc["qtc_bazett", "n_valid"], qc.loc["qtc_bazett", "score_mismatch"], qc.loc["rr_interval", "check_failed"]) == (1009, 70, 28)


def test_biology(result, qc):
    tab = result.qc[result.qc["tab"] == "BILAN BIOLOGIQUE"]
    assert (len(tab), tab["instrument"].nunique()) == (80, 11)
    assert tab["unknown_code"].sum() == 0
    # Units chosen on the form are exported as codes: HDL, haematocrit, MCHC, prolactin and the vitamins are converted.
    assert (qc.loc["hdl", "n_valid"], qc.loc["hdl", "unit_converted"]) == (1101, 207)
    assert (qc.loc["haematocrit", "unit_converted"], qc.loc["mchc", "unit_converted"]) == (205, 287)
    prolactin = qc.loc["prolactin"]
    assert (prolactin["n_valid"], prolactin["unit_converted"], prolactin["unit_inferred"], prolactin["out_of_range"]) == (645, 223, 13, 38)
    vitamin_d = qc.loc["vitamin_d"]
    assert (vitamin_d["n_valid"], vitamin_d["unit_converted"], vitamin_d["out_of_range"]) == (945, 239, 80)
    # Once in nmol/L, the vitamin D has the same level in every year.
    yearly = result.data.groupby(result.data["visit_date"].dt.year)["vitamin_d"].median().loc[2012:]
    assert (round(yearly.min()), round(yearly.max())) == (49, 67)
    assert (qc.loc["vitamin_b12", "unit_converted"], qc.loc["vitamin_b12", "unit_unknown"], qc.loc["folates", "unit_converted"]) == (685, 27, 580)
    assert (qc.loc["cortisol", "n_valid"], qc.loc["cortisol", "unit_converted"]) == (988, 143)
    assert (qc.loc["crp", "n_valid"], qc.loc["crp", "censored_left"], qc.loc["hba1c", "out_of_range"]) == (1105, 80, 22)
    assert (qc.loc["glucose", "n_valid"], qc.loc["glucose", "unit_inferred"], qc.loc["ferritin", "n_valid"]) == (1085, 10, 460)
    assert (qc.loc["leukocytes", "check_failed"], qc.loc["cholesterol_hdl_ratio", "n_valid"]) == (23, 1097)
    # Drug levels: the antidepressants hold two scales a thousand times apart, delivered in µg/L.
    assert (qc.loc["clomipramine", "n_valid"], qc.loc["clomipramine", "unit_inferred"], qc.loc["lithium", "n_valid"]) == (136, 89, 157)
    assert (qc.loc["urine_test_done", "n_valid"], qc.loc["brain_mri_done", "n_valid"], qc.loc["brain_mri_date", "n_valid"]) == (831, 962, 55)


def test_auto_questionnaires(result, qc):
    data = result.data
    tab = result.qc[result.qc["tab"] == "AUTO-QUESTIONNAIRES"]
    assert (len(tab), tab["instrument"].nunique()) == (764, 26)
    assert (tab["unknown_code"].sum(), tab["unparsed"].sum(), tab["version_unknown"].sum()) == (0, 1, 0)
    # Stored totals that follow their items on every visit.
    for score, visits in [("altman_total", 1067), ("csm_total", 718), ("prisem_total", 1041), ("mathys_total", 937), ("epworth_total", 719),
                          ("staya_total", 1065), ("rosenberg_total", 946), ("spin_total", 147), ("ptsd_total", 127), ("leaps_total", 168)]:
        assert (qc.loc[score, "n_valid"], qc.loc[score, "score_mismatch"]) == (visits, 0), score
    # QIDS: one answer of each appetite and weight pair is enough; the EMR stores a total on 1,643 visits only.
    assert (qc.loc["qids_total", "n_valid"], qc.loc["qids_total", "score_mismatch"]) == (1870, 0)
    # Forms that store their reverse-keyed items already reversed: the items are read back to the BP coding, the stored
    # scores reverse them twice and are reproduced by twin scores that are not delivered.
    for score, visits in [("ctq_total", 517), ("ctq_emotional_neglect", 521), ("ctq_physical_neglect", 523), ("bis10_total", 530), ("bis10_planning", 539)]:
        assert (qc.loc[score, "n_valid"], qc.loc[score, "score_mismatch"]) == (visits, 0), score
    assert "ctq_total_as_stored" not in data and "bis10_total_as_stored" not in data
    assert round(data["ctq_emotional_abuse"].corr(data["ctq_emotional_neglect"]), 2) == 0.61       # abuse and neglect rise together
    assert (round(data["ctq_emotional_neglect"].mean(), 1), round(data["ctq_total"].mean(), 1)) == (13.3, 44.1)
    assert (data["ctq02"].median(), data["bis1033"].median()) == (4, 1)                             # as asked, like BP
    assert data["bis_form"].value_counts().to_dict() == {"bis10": 549}
    # MARS: stored 1 = yes here and 1 = no in BP; delivered on the BP coding, and the total is the adherence.
    assert (qc.loc["mars_total", "n_valid"], qc.loc["mars_total", "score_mismatch"], data["mars_total"].median()) == (1026, 0, 7)
    assert round(data["mars05"].mean(), 2) == 0.86
    # STAI: three codings of the answers; the items are delivered from 1 to 4 once the coding is known.
    assert data["staya_shift"].value_counts().to_dict() == {1.0: 693, 0.0: 252, -1.0: 127}
    items = data[[f"staya{number:02d}" for number in range(1, 21)]]
    assert (items.min().min(), items.max().max(), items.notna().any(axis=1).sum()) == (1, 4, 1072)
    # Stored scores that are wrong and are flagged: Fagerstrom (the code of item 3 added as points), the MAThyS
    # sub-scores of 68 visits (no item reversed), two BFI means swapped on 16 visits.
    assert (qc.loc["fagerstrom_total", "n_valid"], qc.loc["fagerstrom_total", "score_mismatch"]) == (392, 129)
    assert [qc.loc[name, "score_mismatch"] for name in ["mathys_emotion", "mathys_motivation", "mathys_perception", "mathys_interaction", "mathys_cognition"]] == [64, 63, 59, 0, 58]
    assert [qc.loc[name, "score_mismatch"] for name in ["bfi_extraversion", "bfi_agreeableness", "bfi_conscientiousness", "bfi_neuroticism", "bfi_openness"]] == [0, 0, 16, 16, 0]
    # SHAPS: the number of items answered "disagree"; the stored score counts five items the other way.
    assert (qc.loc["shaps_total", "n_valid"], data["shaps_total"].median()) == (943, 5)
    assert round(data["shaps_total"].corr(data["madrs_total"]), 2) == 0.61
    # Direction of the scales that only this cohort has.
    assert round(data["rosenberg_total"].corr(data["qids_total"]), 2) == -0.70
    assert round(data["mars_total"].corr(data["qids_total"]), 2) == -0.38
    # The other questionnaires.
    assert (qc.loc["psqi_total", "n_valid"], qc.loc["psqi_total", "score_mismatch"], qc.loc["psqi_latency", "unit_inferred"]) == (1007, 1, 1)
    assert (qc.loc["mdq_total", "n_valid"], data["mdq_screen"].value_counts().to_dict()) == (982, {"negative": 922, "positive": 60})
    assert (qc.loc["eq5d_vas", "n_valid"], qc.loc["eq5d_vas", "out_of_range"]) == (1422, 1)
    assert (qc.loc["sitting_weekday_hours", "out_of_range"], qc.loc["sitting_weekend_hours", "out_of_range"]) == (75, 28)
    assert (qc.loc["detc_cage_total", "n_valid"], qc.loc["food_01", "n_valid"], qc.loc["leaps_not_working", "n_valid"]) == (100, 863, 754)
    assert (qc.loc["paykel_events", "n_valid"], int(tab.loc[tab["instrument"] == "paykel", "out_of_range"].sum())) == (530, 43)
    # Traumatic events: the form writes 0 in the impact of an event that nobody answered.
    assert (qc.loc["trauma_events", "n_valid"], qc.loc["trau01", "n_valid"], qc.loc["trau01_impact", "n_valid"]) == (533, 544, 633)
    assert int(tab.loc[tab["instrument"] == "traumatic_events", "derived_doubt"].sum()) == 1536


def test_neuropsychology(result, qc):
    data = result.data
    tab = result.qc[result.qc["tab"] == "NEUROPSYCHOLOGIE"]
    assert (len(tab), tab["instrument"].nunique()) == (161, 16)
    assert tab["unknown_code"].sum() == 0
    assert ((result.flags["variable"] == "fluency_form") & (result.flags["flag"] == "version_unknown")).sum() == 1
    # One edition of the WAIS, read from the columns that are filled; two forms of the verbal fluency, never in one column.
    assert data["wais_version"].value_counts().to_dict() == {"wais4": 731}
    assert data["fluency_form"].value_counts().to_dict() == {"form_1": 586, "form_2": 96}
    assert (qc.loc["fluency_p_words", "n_valid"], qc.loc["fluency2_letter_words", "n_valid"]) == (582, 95)
    assert (data["fluency_animals_words"].median(), data["fluency2_category_words"].median()) == (26, 18)
    # Band labels cut by the export after four characters are read as the band they stand for.
    assert (qc.loc["tmt_ba_time_band", "n_valid"], qc.loc["tmt_ba_time_band", "unparsed"]) == (698, 4)
    assert (qc.loc["fluency_p_band", "n_valid"], qc.loc["fluency_p_band", "unparsed"]) == (579, 4)
    assert round(data["tmt_ba_time_band"].value_counts(normalize=True)[25.0], 2) == 0.25
    # TMT: the five z-scores read as in BP (higher is better); three were stored with the other sign.
    for score, raw in [("tmt_a_time_z", "tmt_a_time"), ("tmt_b_time_z", "tmt_b_time"), ("tmt_ba_time_z", "tmt_ba_time"), ("tmt_a_errors_z", "tmt_a_errors"), ("tmt_b_errors_z", "tmt_b_errors")]:
        assert data[score].rank().corr(data[raw].rank()) < -0.5, score
    assert (data["tmt_a_errors_z"].median(), data["tmt_b_errors_z"].median()) == (0.14, 0.30)
    assert (qc.loc["tmt_a_time", "n_valid"], qc.loc["tmt_a_time", "out_of_range"], qc.loc["tmt_b_time", "n_valid"]) == (715, 2, 704)
    # The error bands come from the norm tables, as in BP: most carry "this band or a higher one".
    if (NORMS / "tmt_a_errors.csv").exists():
        assert (qc.loc["tmt_a_errors_band", "n_valid"], qc.loc["tmt_a_errors_band", "censored_right"]) == (695, 639)
        assert (qc.loc["tmt_b_errors_band", "n_valid"], qc.loc["tmt_b_perseverative_band", "n_valid"], qc.loc["tmt_ba_errors_band", "n_valid"]) == (693, 672, 624)
    # Stored sums and differences against their parts: the check scores are not delivered,
    # so the flag is filed under the stored value that the analyst sees.
    mismatch = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts()
    expected = {"d2_gzf": 35, "tmt_b_errors": 31, "tmt_ba_errors": 22, "designs1_z": 19, "designs2_z": 18,
                "wais4_simil_z": 16, "wais4_arith_z": 14, "wais4_ds_z": 14, "tmt_a_errors": 9, "wais4_ivt_sum_scaled": 2, "wais4_imt_sum_scaled": 2}
    assert {name: int(mismatch.get(name, 0)) for name in expected} == expected
    assert not any(name.endswith("_check") for name in mismatch.index)
    assert (qc.loc["rlri16_free_sum", "n_valid"], qc.loc["rlri16_free_sum", "score_mismatch"]) == (712, 0)
    assert (qc.loc["rlri16_total_sum", "n_valid"], qc.loc["rlri16_total_sum", "score_mismatch"]) == (713, 0)
    assert data["rlri16_recognition_band"].value_counts().to_dict() == {99.0: 623, 5.0: 85}
    # WAIS-IV indices and the other tests.
    assert (qc.loc["wais4_ivt_index", "n_valid"], data["wais4_ivt_index"].median(), qc.loc["wais4_imt_index", "n_valid"], data["wais4_imt_index"].median()) == (712, 94, 615, 94)
    assert (qc.loc["wais4_ds_total", "n_valid"], qc.loc["wais4_simil_total", "n_valid"], qc.loc["wais4_arith_total", "n_valid"]) == (669, 654, 621)
    assert (qc.loc["d2_gz", "n_valid"], qc.loc["dual_task_mu", "n_valid"], qc.loc["dual_task_mu", "out_of_range"], qc.loc["designs1_raw", "n_valid"]) == (631, 331, 22, 243)
    assert (qc.loc["auditory_span_forward", "n_valid"], qc.loc["auditory_span_forward_z", "missing_code"]) == (426, 138)
    # The conditions of the testing: codes that the dictionary does not explain.
    assert data["handedness"].value_counts().to_dict() == {"right": 676, "left": 36, "both": 19}
    assert data["neuropsy_mood_rating_delay"].value_counts().to_dict() == {"under_a_week": 518, "over_a_week": 192}
    assert (qc.loc["education_years", "n_valid"], data["education_years"].median(), qc.loc["neuropsy_learning_disorder", "missing_code"]) == (740, 14, 28)
    assert (qc.loc["trbapp01", "n_valid"], qc.loc["trbapp01", "missing_code"], qc.loc["coffee_before_cups", "n_valid"]) == (55, 6, 711)


def test_mini(result, qc):
    data = result.data
    tab = result.qc[result.qc["tab"] == "MINI"]
    assert (len(tab), tab["instrument"].nunique()) == (318, 17)
    assert (tab["unknown_code"].sum(), tab["unparsed"].sum(), tab["out_of_range"].sum()) == (0, 1, 2)
    # The interview is answered at screening, and again at 2 and 4 years.
    first = ["mini_a01a", "mini_b01", "mini_c01a", "mini_d01a", "mini_e01", "mini_f01", "mini_g01", "mini_h01", "mini_i01", "mini_j01a",
             "mini_k01a", "mini_l01c", "mini_m01", "mini_n01a", "mini_o01a", "mini_p01a"]
    answered = data[first].notna().any(axis=1)
    assert data.loc[answered, "visit"].value_counts().head(3).to_dict() == {"screening": 491, "V2_ans": 57, "V4_ans": 32}
    assert (answered.sum(), data.loc[answered, "usubjid"].nunique()) == (583, 493)
    # Boxes that the form sets to 0 when it is opened: flagged where the module has no answer.
    assert tab.groupby("instrument")["derived_doubt"].sum().loc[lambda s: s > 0].to_dict() == {
        "mini_a_depression": 195, "mini_b_suicidality": 150, "mini_c_mania": 408, "mini_j_substances": 2769, "mini_q_conclusion": 1170}
    assert (qc.loc["mini_mdd_current", "n_valid"], (data["mini_mdd_current"] == 1).sum(), (data["mini_mde_current"] == 1).sum()) == (630, 361, 308)
    # The suicidality score is the weighted sum of the MINI; 0 where no question is answered yes.
    assert (qc.loc["mini_suicide_risk_score", "n_valid"], data["mini_suicide_risk_score"].median(), (data["mini_suicide_risk_score"] == 0).sum()) == (553, 4, 107)
    points = {"mini_b02": 1, "mini_b03": 1, "mini_b04": 2, "mini_b05": 6, "mini_b06": 8, "mini_b07": 8, "mini_b08": 9, "mini_b09": 4, "mini_b10": 9, "mini_b11": 4}
    weighted = sum(data[name].fillna(0) * weight for name, weight in points.items())
    stored = data["mini_suicide_risk_score"] > 0
    assert (weighted[stored] == data.loc[stored, "mini_suicide_risk_score"]).all() and stored.sum() == 446
    assert data["mini_suicide_risk_level"].value_counts().sort_index().to_dict() == {1.0: 279, 2.0: 90, 3.0: 73}
    # Symptom counts and conclusions.
    assert (qc.loc["mini_mde_symptoms_2_weeks", "n_valid"], data["mini_mde_symptoms_2_weeks"].median(), qc.loc["mini_mde_episodes", "missing_code"]) == (421, 7, 6)
    yes = {name: int((data[name] == 1).sum()) for name in ["mini_panic_lifetime", "mini_gad_current", "mini_social_phobia_current", "mini_agoraphobia_current", "mini_ptsd_current",
                                                           "mini_alcohol_dependence_current", "mini_substance_dependence_current", "mini_antisocial_lifetime"]}
    assert list(yes.values()) == [125, 175, 136, 104, 24, 23, 19, 6]
    assert data["mini_social_phobia_type"].value_counts().to_dict() == {"generalised": 97, "non_generalised": 43}
    assert data["mini_o02"].value_counts().to_dict() == {"yes": 381, "no": 135, "uncertain": 26}


def test_suicide_mood_care_and_social_tabs(result, qc):
    data = result.data
    tabs = ["SUICIDE", "SUBSTANCES", "PERINATALITE", "EVALUATION MEDICALE", "SOIN SUIVI HOSP ARRET TRAVAIL", "MODULE SOCIAL ET PERINATALITE"]
    tab = result.qc[result.qc["tab"].isin(tabs)]
    assert (len(tab), tab["instrument"].nunique()) == (287, 20)
    assert (tab["unknown_code"].sum(), tab["version_unknown"].sum()) == (0, 0)
    # One column, two questions: the whole life at inclusion, the time since the last visit at follow-up. Never in one column.
    assert data["visit_form"].value_counts().to_dict() == {"inclusion": 1268, "follow_up": 924}
    assert (qc.loc["isf01_lifetime", "n_valid"], qc.loc["isf01_since_visit", "n_valid"]) == (452, 140)
    assert data.loc[data["visit_form"] == "follow_up", "isf01_lifetime"].notna().sum() == 0
    assert (qc.loc["n_mde_lifetime", "n_valid"], data["n_mde_lifetime"].median(), qc.loc["n_mde_since_visit", "n_valid"], data["n_mde_since_visit"].median()) == (343, 3, 809, 0)
    assert (qc.loc["cssrs01_lifetime", "n_valid"], (data["cssrs01_lifetime"] == 1).sum(), qc.loc["cssrs01_since_visit", "n_valid"], (data["cssrs01_since_visit"] == 1).sum()) == (557, 427, 784, 366)
    # An answer about the whole life at a follow-up visit is flagged.
    assert int(tab.loc[tab["instrument"] == "isf_since_visit", "period_doubt"].sum()) == 136
    # Scores and counts.
    assert (qc.loc["sis_total", "n_valid"], qc.loc["sis_total", "score_mismatch"], data["sis_total"].median()) == (139, 0, 15)
    assert (qc.loc["cssrs_intensity_lifetime", "n_valid"], data["cssrs_intensity_lifetime"].median()) == (252, 14)
    assert (qc.loc["n_attempts", "n_valid"], (data["violent_attempts"] == 1).sum(), (data["serious_attempts"] == 1).sum()) == (172, 41, 66)
    assert (qc.loc["n_attempts_since_visit", "n_valid"], (data["n_attempts_since_visit"] > 0).sum()) == (796, 44)
    # Codes of the dictionary, and codes that it does not give.
    assert data["tobacco_status"].value_counts().to_dict() == {"non_smoker": 701, "current_smoker": 417, "ex_smoker": 192}
    assert result.patients["birth_term"].value_counts().to_dict() == {"term": 435, "preterm": 47, "post_term": 14}     # asked once: per patient
    assert data["mdd_course"].value_counts().to_dict() == {"recurrent": 509, "single_episode": 123}
    assert data["current_episode_severity"].value_counts().head(2).to_dict() == {"severe": 218, "moderate": 102}
    assert data["marital_status"].value_counts().to_dict() == {"couple": 399, "single": 169, "divorced": 64, "separated": 28, "widowed": 20}
    assert data["serious_method_code"].value_counts().head(2).to_dict() == {"code_1": 61, "code_2": 7}
    assert data["closest_person_code"].value_counts().head(2).to_dict() == {"code_1": 330, "code_10": 117}
    # Sick leave, hospitalisations and care.
    assert (qc.loc["sick_leave_12m", "n_valid"], qc.loc["sick_leave_12m", "missing_code"], (data["sick_leave_12m"] == 1).sum(), qc.loc["sick_leave_weeks_12m", "out_of_range"]) == (433, 244, 241, 32)
    assert (qc.loc["sick_leave_fu", "n_valid"], (data["sick_leave_fu"] == 1).sum(), qc.loc["sick_leave_days_fu", "n_valid"]) == (714, 229, 742)
    assert (qc.loc["ever_hospitalised_v0", "n_valid"], (data["ever_hospitalised_v0"] == 1).sum(), qc.loc["n_hospitalisations_depression_fu", "n_valid"]) == (304, 259, 792)
    assert (qc.loc["hospitalised_year", "n_valid"], (data["hospitalised_year"] == 1).sum(), (data["saw_gp"] == 1).sum(), (data["saw_psychologist"] == 1).sum()) == (996, 394, 747, 315)
    assert (qc.loc["cannabis_use", "n_valid"], (data["cannabis_use"] == 1).sum(), qc.loc["episode_number", "n_valid"]) == (582, 24, 220)


def test_treatments(result, qc):
    data, items = result.data, result.treatments
    tab = result.qc[result.qc["tab"] == "TRAITEMENTS"]
    assert (len(tab), tab["instrument"].nunique()) == (255, 9)
    assert (tab["unknown_code"].sum(), tab["version_unknown"].sum()) == (0, 0)
    # Three medication lists in one table, each put back from the lists that the export crossed.
    assert list(items.columns[:4]) == ["cohort", "usubjid", "list", "item"]
    assert items["list"].value_counts().to_dict() == {"medications": 817, "medications_lifetime": 408, "medications_somatic": 408}
    assert items.groupby("list")["usubjid"].nunique().to_dict() == {"medications": 480, "medications_lifetime": 406, "medications_somatic": 273}
    current = items[items["list"] == "medications"]
    crossed = result.flags[(result.flags["flag"] == "list_crossed") & result.flags["visit"].str.startswith("medications item")]
    lost = current["usubjid"].isin(crossed["usubjid"])
    assert (crossed["usubjid"].nunique(), lost.sum(), (~lost).sum()) == (194, 485, 332)
    # Several products: one item per product and no date. One product: its lines, with their dates.
    assert current.loc[lost, ["start_date", "end_date", "units_per_day", "daily_dose", "form"]].notna().sum().sum() == 0
    assert not current[lost].duplicated(["usubjid", "generic_name", "strength", "dose_unit"]).any()
    assert current.loc[~lost, "start_date"].notna().sum() == 248
    # Every psychotropic name finds its molecule in the table that the cohorts share.
    assert current["molecule"].notna().all() and items.loc[items["list"] == "medications_lifetime", "molecule"].notna().all()
    patients = {group: current.loc[current["treatment_group"] == group, "usubjid"].nunique() for group in ["antidepressant", "benzodiazepine", "antipsychotic_2g", "lithium"]}
    assert patients == {"antidepressant": 293, "benzodiazepine": 125, "antipsychotic_2g": 75, "lithium": 51}
    # On a treatment at the visit: known where the dates are.
    # One visit is dated 2000, before the cohort opened: it has no date, so nothing can be told for it.
    assert (data["on_antidepressant"].notna().sum(), (data["on_antidepressant"] == 1).sum(), data["on_lithium"].notna().sum()) == (972, 286, 1618)
    # Non-drug treatments and psychotherapies: the whole life at inclusion, since the last visit at follow-up.
    # The whole-life answers are asked once: they are in the patients table, as in BP.
    ever = result.patients
    assert (qc.loc["ever_ect", "n_valid"], (ever["ever_ect"] == 1).sum(), qc.loc["ect_fu", "n_valid"], (data["ect_fu"] == 1).sum()) == (504, 87, 810, 134)
    assert (qc.loc["ever_tms", "n_valid"], (ever["ever_tms"] == 1).sum(), (ever["ever_psychotherapy"] == 1).sum()) == (498, 48, 248)
    assert (qc.loc["therapy_supportive_lifetime", "n_valid"], (data["therapy_supportive_lifetime"] == 1).sum(), (data["therapy_cbt_lifetime"] == 1).sum()) == (471, 215, 80)
    assert (qc.loc["therapy_supportive_fu", "n_valid"], (data["therapy_supportive_fu"] == 1).sum()) == (736, 241)
    assert "ever_ect" not in data.columns and qc.loc["ever_ect", "level"] == "patient"
    assert (qc.loc["electronic_cigarette", "n_valid"], (data["electronic_cigarette"] == 1).sum(), (data["cpap"] == 1).sum()) == (993, 41, 35)


def test_history_and_family(result, qc):
    data, relatives, patients = result.data, result.relatives, result.patients
    tab = result.qc[result.qc["tab"] == "ANTECEDENTS"]
    assert (len(tab), tab["instrument"].nunique()) == (405, 20)
    assert (tab["unknown_code"].sum(), tab["unparsed"].sum(), tab["out_of_range"].sum()) == (1, 0, 0)
    # Nine histories in two forms: the inclusion visit, and the visits of 2 and 4 years. Never in one column.
    yes = {name: (int(data[name].notna().sum()), int((data[name] == 1).sum())) for name in ["hypertension_v0", "migraine_v0", "dyslipidaemia_v0", "thyroid_disorder_v0", "cancer_v0", "hypertension_fu"]}
    assert yes == {"hypertension_v0": (571, 109), "migraine_v0": (574, 112), "dyslipidaemia_v0": (572, 121), "thyroid_disorder_v0": (571, 70), "cancer_v0": (570, 31), "hypertension_fu": (130, 27)}
    assert data.loc[data["visit_form"] == "follow_up", "hypertension_v0"].notna().sum() == 0
    assert data["thyroid_disorder_type_v0"].value_counts().head(2).to_dict() == {"hypothyroidism": 54, "hyperthyroidism": 8}
    assert (qc.loc["n_pregnancies_v0", "n_valid"], data["n_pregnancies_v0"].median()) == (313, 2)
    # Boxes that the form sets to 0 on every row: flagged where their question is empty.
    doubt = tab.groupby("instrument")["derived_doubt"].sum()
    assert (doubt["allergic_history_v0"], doubt["other_history_v0"], doubt["skin_history_v0"], doubt["urinary_history_v0"], doubt["family_history"]) == (85, 133, 80, 66, 14335)
    # The family: one value per patient, and one row per relative.
    family = {name: (int(patients[name].notna().sum()), int((patients[name] == 1).sum())) for name in ["mother_psychiatric_history", "father_psychiatric_history", "has_children", "has_siblings"]}
    assert family == {"mother_psychiatric_history": (532, 220), "father_psychiatric_history": (523, 153), "has_children": (551, 371), "has_siblings": (534, 480)}
    assert (len(relatives), relatives["usubjid"].nunique()) == (3748, 577)
    assert relatives["relative"].value_counts().to_dict() == {"mother": 577, "father": 577, "maternal_grandmother": 577, "maternal_grandfather": 577,
                                                              "paternal_grandmother": 577, "paternal_grandfather": 577, "siblings": 201, "children": 85}
    assert ((relatives["relative_mood_disorder"] == 1).sum(), relatives["relative_mood_disorder"].notna().sum()) == (536, 737)
    assert relatives.loc[relatives["relative_mood_disorder"] == 1, "usubjid"].nunique() == 343


def test_coverage():
    """Every column of the extraction is read by a schema or ignored with a reason."""
    table = dr.coverage(EXTRACTION, THESAURUS)
    counts = table["status"].value_counts().to_dict()
    assert (counts["covered"], counts["ignored"], counts.get("not_assigned", 0)) == (2337, 38, 0)
    assert counts["covered"] + counts["ignored"] == 2375


def test_nothing_disappears_silently():
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    for schema in load_schemas(dr.SCHEMAS).values():
        if schema.get("level") == "list":            # cells that hold lists: the invariant holds on the items
            items, item_keys, list_flags = open_lists(raw, keys, schema)
            assert_invariant(items, item_keys, schema)
        elif schema.get("level") == "relatives":     # one row per relative: the invariant holds on these rows
            rows, row_keys, varying_flags = stack_relatives(raw, keys, schema)
            assert_invariant(rows, row_keys, schema)
        elif "derived_from" not in schema:           # columns computed from other rows have no raw cell
            assert_invariant(raw, keys, schema)
