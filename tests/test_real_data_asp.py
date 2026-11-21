"""The real FACE ASP extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/asp/PROGRESS.md ("What the schemas
must produce"). No patient row appears here.
"""

from pathlib import Path

import pandas as pd
import pytest

from facedata import asp
from facedata.read import prepare_visits, read_extraction
from facedata.relatives import stack_relatives
from facedata.schema import load_schemas
from facedata.treatments import open_lists
from test_pipeline import assert_invariant

ROOT = Path(__file__).parent.parent
EXTRACTION = ROOT / "data" / "asp" / "ASPALL_20261030.tsv"
NORMS = ROOT / "norms"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the ASP extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return asp.load(EXTRACTION, norms=NORMS)


@pytest.fixture(scope="module")
def qc(result):
    return result.qc.set_index("variable")


def test_visits(result):
    assert len(result.data) == 4500
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 2318 == len(result.patients)
    # Every patient has an inclusion visit; 1,809 have a screening visit; few are seen again.
    visits = result.data["visit"].value_counts()
    assert (visits["V0"], visits["screening"], visits["V1_an"], visits["V2_ans"]) == (2318, 1809, 177, 112)
    assert (visits["V3_ans"], visits["V4_ans"], visits["V5_ans"]) == (41, 29, 8)
    assert result.flags[result.flags["flag"] == "visit_order"].shape[0] == 41
    # Five visits are dated before 2009 or in the future: the date is impossible and is not delivered.
    impossible = result.flags[(result.flags["variable"] == "visit_date") & (result.flags["flag"] == "out_of_range")]
    assert (len(impossible), result.data["visit_date"].isna().sum(), (result.data["age"] < 0).sum()) == (5, 5, 0)
    # The export writes the centre codes as numbers; they are delivered with two digits, as in the other cohorts.
    assert set(result.data["siteid"].str.len()) == {2} and result.data["siteid"].nunique() == 8


def test_the_four_cohorts_can_be_stacked(result):
    from facedata import bp, dr, sz
    files = {"bp": ROOT / "data" / "bp" / "BPALL_20261113_2.tsv", "sz": ROOT / "data" / "sz" / "SZALL_20261117.tsv",
             "dr": ROOT / "data" / "dr" / "DRALL_20261030.tsv"}
    if not all(path.exists() for path in files.values()):
        pytest.skip("the BP, the SZ or the DR extraction is not on this computer")
    for table in [result.data, result.patients, result.flags, result.treatments, result.relatives]:
        assert table.columns[0] == "cohort" and set(table["cohort"]) <= {"asp"}
    shared = ["cohort", "usubjid", "fondacode", "sex", "diagnosis", "birth_date", "age_at_inclusion"]
    others = [module.load(files[name], instruments=["identite"]).patients[shared] for name, module in [("bp", bp), ("sz", sz), ("dr", dr)]]
    patients = pd.concat(others + [result.patients[shared]], ignore_index=True)
    assert len(patients) == 6498 + 2353 + 634 + 2318
    assert not patients.duplicated(subset=["cohort", "usubjid"]).any()        # the key of a patient across cohorts
    assert patients["usubjid"].duplicated().sum() > 0                         # a number alone is not: it is given per cohort
    assert patients["fondacode"].is_unique
    assert set(patients["birth_date"].dropna().dt.day) == {15}


def test_patient_table(result, qc):
    patients = result.patients
    assert patients["sex"].value_counts().to_dict() == {"male": 1446, "female": 872}
    assert patients["diagnosis"].value_counts().to_dict() == {"asd_confirmed": 2008, "asd_not_confirmed": 310}
    age = patients["age_at_inclusion"]
    assert (age.notna().sum(), age.median(), (age < 18).sum()) == (2318, 20, 956)        # children and adults
    assert qc.loc["age_at_inclusion", "score_mismatch"] == 0
    assert qc.loc["entry_date", "n_valid"] == 4500
    # The form filled before the assessment: one value per patient, for the patients who have a screening visit.
    assert ((qc["tab"] == "patient") & (qc["level"] == "patient")).sum() == 74
    form = patients["screening_conclusion"].notna() | patients["earlier_asd_diagnosis"].notna() | patients["non_drug_care_sessad"].notna()
    screened = set(result.data.loc[result.data["visit"] == "screening", "usubjid"])
    assert (form.sum(), (form & ~patients["usubjid"].isin(screened)).sum()) == (1145, 0)
    assert patients["screening_conclusion"].value_counts().to_dict() == {"asd_evoked": 868, "deferred": 146, "asd_rejected": 21}    # the wording of the thesaurus
    assert patients["earlier_asd_diagnosis"].value_counts().to_dict() == {0: 956, 1: 106}
    assert (qc.loc["earlier_asd_diagnosis", "missing_code"], qc.loc["other_earlier_diagnosis", "missing_code"]) == (10, 22)
    assert patients["screening_criterion_a1"].notna().sum() == 125                    # the checklist of the children
    assert (patients["non_drug_care_ime"].sum(), patients["non_drug_care_psychiatrist"].sum()) == (0, 320)
    flags = result.flags[result.flags["variable"].isin(patients.columns)]
    # The answers about the birth are asked once: they are per patient, as in BP, with their flags.
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 809, "out_of_range": 21, "unit_inferred": 1, "period_removed": 2200}     # the five non-drug care boxes: the 0 from 2022 is missing (D79)


def test_medical_evaluation(result, qc):
    data = result.data
    table = qc[qc["tab"] == "evaluation_medicale"]
    # 22 instruments: six of the old ones are split into an inclusion and a follow-up schema (clinical scales review, D48-D53).
    assert (table["instrument"].nunique(), len(table)) == (22, 545)
    flags = result.flags[result.flags["variable"].isin(set(table.index) | {"vineland_sum_check"})]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 2373, "out_of_range": 44, "score_mismatch": 23}      # a not known 9 is flagged on the 0/1 substance twins (+28); the Vineland check adds the motor domain (-7)
    v0 = data[data["visit"] == "V0"]
    # The conclusion of the DSM criteria is the diagnosis of the cohort.
    assert (v0["dsm_asd_conclusion"] == 1).sum() == 2008 and v0["dsm_asd_conclusion"].notna().all()
    assert (v0[[f"dsm_criterion_{k}" for k in ["a1", "a2", "a3", "b1", "b2", "b3", "b4", "c", "d"]]] == 1).all(axis=1).sum() == 944
    assert v0["axis1_interview_v0"].value_counts().to_dict() == {"kiddie_sads": 725, "digs": 427, "mini": 98}       # the code 3 is the MINI; the thesaurus lists two interviews only
    # The support levels are named from their wording: the thesaurus numbers them backwards.
    assert ((v0["severity_social_support"] == 1).sum(), (v0["severity_social_very_substantial"] == 1).sum()) == (594, 127)
    # ASDI: the codes are not in order (1 yes, 2 a little, 0 no), so the answers are delivered as words.
    assert v0["asdi01"].value_counts().to_dict() == {"yes": 317, "no": 49, "a_little": 39} and (v0["asdi_criteria_met"] == 1).sum() == 252
    # An age that was first read as a list of codes.
    assert (data["language_disorder_onset_age_v0"].notna().sum(), data["language_disorder_onset_age_v0"].median()) == (50, 3)
    assert v0["tobacco_use_disorder_v0"].value_counts().to_dict() == {"dependence": 86, "no": 38, "abuse": 12}
    known = {name: (int(v0[name].notna().sum()), int((v0[name] == 1).sum())) for name in ["depressive_episode_v0", "anxiety_disorder_v0", "adhd_v0", "insomnia_v0"]}
    assert known == {"depressive_episode_v0": (1522, 434), "anxiety_disorder_v0": (1525, 899), "adhd_v0": (1411, 475), "insomnia_v0": (1645, 569)}
    assert (data["depressive_episode_n_episodes_v0"] == 0).sum() == 1088               # a count is 0 where the disorder is absent; the 56 zeros of 1,144 that sat at follow-up are in the _fu twin
    # The anxiety, developmental, psychotic, learning and sleep lists are one schema at inclusion and one at follow-up (an empty follow-up list means no change).
    assert (int(data["panic_disorder_v0"].notna().sum()), int((data["panic_disorder_v0"] == 1).sum())) == (1430, 157)      # the highest of the two panic questions
    assert (int(data["panic_disorder_fu"].notna().sum()), int((data["panic_disorder_fu"] == 1).sum())) == (63, 4)
    assert int(data["delusions_v0"].notna().sum()) == 1506                                  # the four psychotic groups are asked after the gate: 0 after a no
    assert (data.loc[data["depressive_episode_fu"].notna(), "visit"].isin(["V0", "screening"]).sum(), int(data["axis1_summary_changed_fu"].notna().sum())) == (0, 212)
    # Two forms in the same columns: the life at inclusion, the same life asked again at follow-up (form 203 prints no period).
    assert (data["isf05_lifetime"].notna().sum(), (data["isf05_lifetime"] == 1).sum()) == (1658, 191)
    assert (data["isf05_lifetime_fu"].notna().sum(), (data["isf05_lifetime_fu"] == 1).sum()) == (124, 4)
    assert data.loc[data["isf05_lifetime_fu"].notna(), "visit"].isin(["V0", "screening"]).sum() == 0
    # The serious attempt is 0 after a no (never filled under a no), a count of attempts is not.
    assert (int(data["serious_suicide_attempt"].notna().sum()), int((data["serious_suicide_attempt"] == 0).sum()), int(data["serious_suicide_attempt_fu"].notna().sum())) == (1632, 1542, 124)
    # Substances: the clinician's list at inclusion, one 0/1 item per substance that is 0 after a no to the opening question (as BP and SZ).
    gate = data["substance_disorder_v0"]
    assert (int(gate.notna().sum()), int((gate == 1).sum()), int((gate == 0).sum()), set(data.loc[gate.notna(), "visit"])) == (1523, 142, 1381, {"V0"})
    assert {name: (int(data[name].notna().sum()), int((data[name] == 1).sum())) for name in ["alcohol_disorder_v0", "cannabis_disorder_v0", "tobacco_disorder_v0"]} == {
        "alcohol_disorder_v0": (1510, 61), "cannabis_disorder_v0": (1518, 67), "tobacco_disorder_v0": (1517, 98)}
    assert (int(data["alcohol_onset_age_v0"].notna().sum()), data["alcohol_onset_age_v0"].median(), int(data["smoking_start_age_clinician"].notna().sum())) == (42, 18.5, 68)
    # One schema per edition of the Wechsler scales.
    valid = {name: int(data[name].notna().sum()) for name in ["wisc4_icv_index", "wisc5_icv_index", "wais4_icv_index_clinician", "gai_index"]}
    assert valid == {"wisc4_icv_index": 205, "wisc5_icv_index": 654, "wais4_icv_index_clinician": 995, "gai_index": 666}      # the clinician's copy of the WAIS-IV indices keeps its own names (WAIS review, D138-D143)
    assert (data["wais4_qit_clinician"].median(), data["wisc5_qit"].median()) == (110, 105)
    # Vineland-II: raw scores of the sub-domains, standard scores of the domains, their sum checked.
    assert (data["vineland_receptive_raw"].notna().sum(), data["vineland_receptive_raw"].max()) == (1108, 40)
    assert (data["vineland_composite"].notna().sum(), data["vineland_composite"].median()) == (974, 63)
    # The check is not delivered: its mismatch is filed under the stored sum that the analyst sees.
    assert ((result.flags["variable"] == "vineland_sum_standard") & (result.flags["flag"] == "score_mismatch")).sum() == 23      # the check adds the motor domain: 7 four-domain sums now agree


def test_clinical_measures_and_biology(result, qc):
    data = result.data
    table = qc[qc["tab"].isin(["clinique", "bilan_biologique"])]
    assert (table["instrument"].nunique(), len(table)) == (15, 97)
    flags = result.flags[result.flags["variable"].isin(set(table.index) | {"qtc_bazett", "bmi", "cholesterol_hdl_ratio"})]
    assert "unknown_code" not in set(flags["flag"]) and "unparsed" not in set(flags["flag"])
    counts = flags["flag"].value_counts()
    assert (counts["unit_inferred"], counts["unit_converted"], counts["unit_unknown"], counts["unit_doubt"], counts["out_of_range"]) == (230, 164, 3, 7, 79)   # ALP in µkat/L and creatinine in mg/dL are read: 5 cells gained; vitamin D code 64387 is nmol/L (biology review, D144)
    # Children are measured too: the ranges of the other cohorts would refuse them.
    assert (qc.loc["height", "n_valid"], qc.loc["height", "unit_inferred"], qc.loc["height", "out_of_range"]) == (1100, 3, 9)
    assert (qc.loc["weight", "n_valid"], data["weight"].min() < 25) == (1104, True)
    assert (qc.loc["systolic_supine", "unit_inferred"], qc.loc["diastolic_supine", "unit_inferred"]) == (7, 7)                 # typed in cmHg
    assert data["bmi"].notna().sum() == 1091 and (result.flags["variable"] == "qtc_bazett").sum() == 0
    v0 = data[data["visit"] == "V0"]
    assert v0["tobacco_status"].value_counts().to_dict() == {"non_smoker": 492, "current_smoker": 49, "ex_smoker": 22}
    # No unit column for most analytes: the size of the value gives the unit.
    assert (qc.loc["haemoglobin", "n_valid"], qc.loc["haemoglobin", "unit_inferred"]) == (545, 113)              # g/L brought to g/dL
    assert (qc.loc["glucose", "unit_inferred"], qc.loc["phosphate", "unit_inferred"], qc.loc["monocytes", "unit_inferred"]) == (8, 12, 10)   # the phosphate factor is 0.0323 (biology review, D144)
    assert (qc.loc["cholesterol", "n_valid"], qc.loc["cholesterol", "unit_converted"], qc.loc["triglycerides", "unit_converted"]) == (352, 67, 64)
    assert (qc.loc["vitamin_d", "n_valid"], qc.loc["vitamin_d", "unit_converted"], qc.loc["vitamin_d", "unit_unknown"]) == (291, 19, 3)   # vitamin D code 64387 is read as nmol/L: 26 cells gained (biology review, D144)
    assert (qc.loc["prolactin", "n_valid"], qc.loc["prolactin", "unit_converted"]) == (104, 14)
    assert (qc.loc["crp", "censored_left"], qc.loc["crp", "missing_code"]) == (1, 45)       # a CRP of exactly 0 (BP D101)
    assert v0["mri"].value_counts().to_dict() == {"not_done": 577, "normal": 167, "abnormal": 54, "result_unknown": 36}
    assert v0["handedness"].value_counts().to_dict() == {"right": 745, "left": 109, "both": 29}      # the names of BP
    assert ((v0["biobank_sample"] == 1).sum(), v0["biobank_sample"].notna().sum()) == (387, 623)


def test_neuropsychology(result, qc):
    data = result.data
    table = qc[qc["tab"] == "neuropsychologie"]
    assert (table["instrument"].nunique(), len(table)) == (16, 374)      # the block design z-score is added (WAIS review, D138-D143)
    flags = result.flags[result.flags["variable"].isin(table.index)]
    # The total of the errands test is recomputed as in BP: 2 stored totals differ, 1 has an item missing.
    actual_flags = flags["flag"].value_counts().to_dict()
    assert actual_flags == {"missing_code": 735, "score_mismatch": 330, "score_not_recomputed": 114, "norm_missing": 91, "out_of_range": 18, "censored_left": 14,
                            "winsorised": 12, "censored_right": 7, "derived_doubt": 4}      # the WAIS-IV scores are read in the tables (D135); the coding raw score is the boxes filled minus the errors (D136), the index sums are recomputed (D137); the WAIS lookups read the age at the assessment, the expected IQ of Barona is recomputed, "executive_done" 9 is unknown (WAIS review, D138-D143)
    # The WAIS-IV item by item: every stored total is the sum of its items, and the digit span total of its three parts.
    wais = result.flags[result.flags["variable"].str.startswith("wais4_")]
    assert not any(name.endswith("_total") for name in wais.loc[wais["flag"] == "score_mismatch", "variable"])      # every stored total is the sum of its items
    valid = {name: int(data[name].notna().sum()) for name in ["wais4_mat_total", "wais4_simil_total", "wais4_vocab_total", "wais4_bd_total", "wais4_ds_total", "wais4_pc_total"]}
    assert valid == {"wais4_mat_total": 286, "wais4_simil_total": 293, "wais4_vocab_total": 212, "wais4_bd_total": 215, "wais4_ds_total": 293, "wais4_pc_total": 5}
    assert ((data["wais4_mat_z"] - (data["wais4_mat_scaled"] - 10) / 3).abs().max() < 0.011)             # the z-score of a scaled score
    # Two sources for an index: the neuropsychology form (the shared name) and the copy of the clinician in the medical evaluation (_clinician).
    both = data["wais4_icv_index"].notna() & data["wais4_icv_index_clinician"].notna()
    assert (data["wais4_icv_index"].notna().sum(), both.sum(), (data.loc[both, "wais4_icv_index"] == data.loc[both, "wais4_icv_index_clinician"]).sum()) == (205, 187, 162)
    assert (data["barona_expected_qit"].notna().sum(), data["barona_qit_difference"].notna().sum()) == (763, 131)      # the expected IQ is recomputed by regression: 537 gained and 15 lost against the stored one, none for the 42 child visits (WAIS review, D138-D143)
    difference = (data["barona_expected_qit"] - data["wais4_qit"] - data["barona_qit_difference"]).abs()
    assert difference.notna().sum() == 123 and (difference < 0.2).sum() == 115                          # expected minus measured: 8 follow the stored IQ, not the recomputed one (D137); 7 pairs lose their expected IQ, 1 IQ moves with the age at the assessment (WAIS review, D138-D143)
    assert (data["trbapp01"].notna().sum(), (data["trbapp01"] == 1).sum(), qc.loc["trbapp01", "missing_code"]) == (746, 71, 55)
    assert (data["lis_total"].notna().sum(), data["face_emotion_total"].notna().sum(), data["errands_time"].notna().sum()) == (698, 701, 563)


def test_new_questionnaires(result, qc):
    data, flags = result.data, result.flags
    table = qc[qc["tab"] == "autoquestionnaires"]
    assert (table["instrument"].nunique(), len(table)) == (30, 1240)      # the ADOS total of the summary line is not delivered; the ADHD-RS is two forms (D63)
    assert (qc.loc["eq5d_index", "n_valid"], qc.loc["eq5d_index", "score_mismatch"], qc.loc["asrs_parta", "n_valid"]) == (1020, 0, 579)
    counts = flags[flags["variable"].isin(table.index)]["flag"].value_counts().to_dict()
    # 19,157 scores typed without their items (and totals built on them); 776 stored scores whose items are incomplete.
    # The BVAQ factors and the STAIC state are recomputed with the stored ones as checks (2,339 and 17 cells of score_mismatch; D62),
    # and the CTQ neglect scores reproduce the script of the form through their twins (109 mismatches fewer).
    assert counts == {"score_as_stored": 19157, "missing_code": 1460, "score_not_recomputed": 776, "score_mismatch": 2996, "out_of_range": 34}
    mismatch = lambda name: int(((flags["variable"] == name) & (flags["flag"] == "score_mismatch")).sum())
    fl = lambda name, flag: int(((flags["variable"] == name) & (flags["flag"] == flag)).sum())
    # A score typed without any of its items is kept as stored.
    kept = {name: (int(qc.loc[name, "n_valid"]), int(qc.loc[name, "score_as_stored"])) for name in ["adi_a1", "raads_social", "gsq_total", "bdi_total", "adhdrsc_total", "adhdrsa_total",
                                                                                                    "cdi_total", "staic_trait", "staic_state"]}
    assert kept == {"adi_a1": (1622, 419), "raads_social": (480, 159), "gsq_total": (602, 157), "bdi_total": (518, 82), "adhdrsc_total": (887, 210), "adhdrsa_total": (178, 8),
                    "cdi_total": (457, 114), "staic_trait": (402, 149), "staic_state": (168, 150)}
    # ADI-R: the published algorithm; the stored totals A and C count too many items and are checked by formulas "as stored".
    assert (qc.loc["adi_social_total", "n_valid"], qc.loc["adi_communication_verbal_total", "n_valid"], qc.loc["adi_repetitive_total", "n_valid"]) == (1520, 1531, 1538)
    assert (data["adi_social_total"].median(), data["adi_social_total"].max(), data["adi_repetitive_total"].max()) == (12, 29, 12)
    assert (mismatch("adi_social_total_as_stored"), mismatch("adi_repetitive_total_as_stored"), mismatch("adi_b3")) == (0, 0, 139)
    assert data["adi50_past"].dropna().isin([0, 1, 2, 3, 7, 8, 9]).all()                       # the codes as recorded
    # ADOS: one instrument per module; the stored scores that count a code 3 as 3 are recomputed.
    valid = {name: int(qc.loc[name, "n_valid"]) for name in ["ados3_total", "ados4_total", "ados4_communication", "ados4_social_interaction"]}
    assert valid == {"ados3_total": 797, "ados4_total": 1349, "ados4_communication": 1355, "ados4_social_interaction": 1350}
    assert (mismatch("ados3_total"), mismatch("ados4_total"), mismatch("ados4_stereotyped_restricted")) == (23, 39, 79)
    assert (mismatch("ados4_communication_as_stored"), mismatch("ados4_social_interaction_as_stored")) == (0, 0)      # the export sums the raw codes: the checks are exact (D62, D64)
    assert (data["ados4_communication"].max(), data["ados4_social_interaction"].max()) == (8, 14)        # the published maxima
    assert (data["ados3_b08"].isna() & data["ados3_b07"].notna()).sum() == 96                              # the visits of the first edition
    # SRS of a relative: the child form and the adult form share the columns and are told apart by the age at the visit.
    # Two of these visits have an impossible date, so no age: their form cannot be told any more.
    assert data["srs_relative_form"].value_counts().to_dict() == {"srs_relative_adult": 984, "srs_relative_child": 981}
    assert (data["srsc_total"].notna() & data["srsr_total"].notna()).sum() == 0
    # The published key, where the stored scores reverse no item.
    assert (qc.loc["srsc_total", "n_valid"], data["srsc_total"].median(), mismatch("srsc_total_as_stored"), mismatch("srsc_awareness_as_stored")) == (886, 94, 0, 0)
    assert (qc.loc["srsr_total", "n_valid"], data["srsr_total"].median(), mismatch("srsr_total_as_stored"), mismatch("srsr_awareness_as_stored")) == (829, 98, 0, 0)
    assert "srsc_total_t_stored" not in data.columns and "srsr_awr_t_stored" not in data.columns           # the T-scores are not delivered
    # GSQ: the stored proprioceptive sub-score counts the item 40 for the item 41; the delivered one is the sum of its two parts.
    # Where the two parts were typed without their items it is their sum, and says so (156 visits).
    assert (qc.loc["gsq_proprioceptive", "n_valid"], mismatch("gsq_proprioceptive_as_stored"), mismatch("gsq_hyper_proprioceptive")) == (611, 2, 1)
    assert qc.loc["gsq_proprioceptive", "score_as_stored"] == 156
    # ADHD-RS: the form of children (a parent rates) and the form of adults (the adult recalls childhood) share the columns and are told apart by the age (D63).
    assert data["adhdrs_form"].value_counts().to_dict() == {"adhd_rs_child": 900, "adhd_rs_adult": 192}
    assert (data["adhdrsc_total"].notna() & data["adhdrsa_total"].notna()).sum() == 0
    assert (data["adhdrsc19"].value_counts().to_dict(), qc.loc["adhdrsc19", "missing_code"]) == ({"yes": 579, "no": 16}, 14)       # the form prints 9 as NA: none is a child under 7
    assert (data["adhdrsa19"].value_counts().to_dict(), qc.loc["adhdrsa19", "missing_code"]) == ({"yes": 96, "no": 15}, 36)
    # BRIEF: the form of children and the form of adults are two instruments.
    assert data["brief_form"].value_counts().to_dict() == {"brief_parent": 858, "brief_adult": 786}
    assert (qc.loc["briefp_gec", "n_valid"], qc.loc["briefa_gec", "n_valid"], qc.loc["briefa_self_monitor", "n_valid"]) == (793, 757, 777)
    assert (data["briefp_gec"].notna() & data["briefa_gec"].notna()).sum() == 0
    # The questionnaires shared with the other cohorts, and those of this one.
    totals = {name: (int(qc.loc[name, "n_valid"]), float(data[name].median())) for name in ["raads_total", "srsa_total", "ctq_total", "mars_total", "epworth_total", "asrs_total", "staya_total",
                                                                                            "ssp_total", "aqc_total", "cgi_severity", "gaf"]}
    assert totals == {"raads_total": (479, 151), "srsa_total": (467, 110), "ctq_total": (400, 40), "mars_total": (241, 6), "epworth_total": (415, 8), "asrs_total": (559, 40),
                      "staya_total": (581, 49), "ssp_total": (951, 145), "aqc_total": (500, 19), "cgi_severity": (1368, 4), "gaf": (1351, 55)}
    # The stored neglect scores are the script's rule (an answer 1 of a reversed item counts 1): their twins reproduce them on every visit (D62).
    assert (mismatch("ctq_emotional_neglect"), mismatch("ctq_physical_neglect"), mismatch("ctq_total_as_stored"), mismatch("mars_total_as_stored")) == (0, 0, 0, 0)
    # STAIC state: the script reverses the positive adjectives; the state total is computed from the items and the stored one is the check (R27, D62).
    assert (qc.loc["staic_state", "n_valid"], qc.loc["staic_state", "score_as_stored"], mismatch("staic_state"), data["staic_state"].max() <= 60) == (168, 150, 17, True)
    # ASRS screen: computed from the six items of part A (the form of this cohort stores no result): 362 of 579 positive.
    assert (qc.loc["asrs_screen", "n_valid"], int((data["asrs_screen"] == 1).sum())) == (579, 362)
    # BVAQ: the stored factors were inverted before 2025 on most centres; the five factors, the two components and the total are computed from the items (R27, D62).
    assert (qc.loc["bvaq_total", "n_valid"], qc.loc["bvaq_total", "score_as_stored"], mismatch("bvaq_total"), data["bvaq_total"].median()) == (615, 172, 296, 57)
    # BRIEF validity scores have a range now: three infrequency values and three "years known" values are missing with out_of_range.
    assert (fl("briefa_infrequency", "out_of_range"), fl("briefp_known_for", "out_of_range"), data["briefa_infrequency"].max()) == (3, 3, 5)


def test_old_questionnaires(result, qc):
    data, flags = result.data, result.flags
    table = qc[qc["tab"].isin(["autoquestionnaires_old_part1", "autoquestionnaires_old_part2"])]
    # The pilot forms take the names of BP (bis10NN, aim40_NN, als54_NN): 1,772 -> 1,770 variables (BIS -7, AIM +1, ALS +4); the schemas of both folders keep 28 instruments.
    assert (table["instrument"].nunique(), len(table)) == (28, 1770)
    assert {"bis1001", "bis10_total", "aim40_01", "aim40_score", "als54_01", "als54_depression"} <= set(table.index)
    assert not {"bis10_1", "bis_smi", "aim_1", "aim_score", "als_1", "alsdep"} & set(table.index)
    counts = flags[flags["variable"].isin(table.index)]["flag"].value_counts()
    assert "unknown_code" not in counts and "unparsed" not in counts
    # missing_code +26: the waking time of the CSHQ (18 visits) and the rising time of the PSQI (8) written 00:00:00 by a Time box left untouched; score_mismatch +4: ALS depression (11 items against the export's 10).
    assert (counts["score_mismatch"], counts["missing_code"], counts["score_as_stored"]) == (551, 431, 99)
    mismatch = lambda name: int(qc.loc[name, "score_mismatch"])
    fl = lambda name, flag: int(((flags["variable"] == name) & (flags["flag"] == flag)).sum())
    # The scores that are right as stored: recomputed, no difference.
    right = ["abc_irritability", "cca_pragmatic_skills", "cshq_total", "hama_total", "hamd_total", "lsas_anxiety_total", "rbsr_total", "spq_total", "tas_total", "dcdq_total"]
    assert [mismatch(name) for name in right] == [0] * len(right)
    valid = {name: int(qc.loc[name, "n_valid"]) for name in right + ["lsas_total", "ccc_gcc"]}
    assert valid == {"abc_irritability": 252, "cca_pragmatic_skills": 233, "cshq_total": 106, "hama_total": 360, "hamd_total": 340, "lsas_anxiety_total": 243, "rbsr_total": 308,
                     "spq_total": 184, "tas_total": 38, "dcdq_total": 55, "lsas_total": 235, "ccc_gcc": 106}
    # The three quotients: points for the answers on the scored side, not a sum of the codes.
    quotients = {name: (int(qc.loc[name, "n_valid"]), mismatch(name), float(data[name].median())) for name in ["aq_total", "empathy_quotient_total", "systemizing_quotient_total"]}
    assert quotients == {"aq_total": (250, 1, 35), "empathy_quotient_total": (443, 2, 24), "systemizing_quotient_total": (158, 6, 34)}
    assert (data["aq_total"].max() <= 50, data["empathy_quotient_total"].max() <= 80) == (True, True)
    # Two forms of the communication checklist in the same columns.
    # The form is also read from the questions that only one form asks: 17 visits of 17 to 24 year olds given the children's form (CCC-2), 2 of CC-A.
    assert data["communication_checklist_form"].value_counts().to_dict() == {"cca": 237, "ccc2": 123}
    forms = flags[flags["flag"] == "version_unknown"]["variable"].value_counts().to_dict()
    assert forms == {"communication_checklist_form": 2, "srs_relative_form": 3}      # two visits with items and no question of either form; three visits with SRS answers and an impossible date: no age
    # PSQI: the components 4, 5 and 7 are recomputed; the stored ones do not cross midnight or do not follow the items.
    psqi = {name: (int(qc.loc[name, "n_valid"]), mismatch(name)) for name in ["psqi_latency_component", "psqi_efficiency", "psqi_disturbances", "psqi_dysfunction", "psqi_total"]}
    assert psqi == {"psqi_latency_component": (189, 0), "psqi_efficiency": (193, 91), "psqi_disturbances": (200, 158), "psqi_dysfunction": (201, 98), "psqi_total": (182, 147)}
    assert data["psqi_total"].median() == 7
    assert (fl("psqi_rising_time", "missing_code"), fl("cshq_waking_time", "missing_code")) == (8, 18)      # 00:00:00 is a Time box left untouched
    # CCC-2 Social Interaction Deviance Composite: the stored one is a char(2) field and never negative (43 values); computed from the scaled scores it has 106 (63 negative).
    assert (qc.loc["ccc_sidc", "n_valid"], int((data["ccc_sidc"] < 0).sum()), mismatch("ccc_sidc"), data["ccc_sidc"].min(), data["ccc_sidc"].max()) == (106, 63, 0, -32, 15)
    # LSAS: twelve situations of performance and twelve of social interaction, as the form prints them; the four sub-scores equal the stored ones on every visit that has both.
    lsas = ["lsas_social_anxiety", "lsas_social_avoidance", "lsas_performance_anxiety", "lsas_performance_avoidance"]
    assert [int(qc.loc[name, "n_valid"]) for name in lsas] == [248, 242, 254, 244] and [mismatch(name) for name in lsas] == [0, 0, 0, 0]
    both = data["lsas_social_anxiety"].notna() & data["lsas_performance_anxiety"].notna() & data["lsas_anxiety_total"].notna()
    assert (data.loc[both, "lsas_social_anxiety"] + data.loc[both, "lsas_performance_anxiety"] == data.loc[both, "lsas_anxiety_total"]).all()
    # MCDD: the box "no to all the criteria" makes the script tick no on the fifteen; the criterion 8 that it left empty is 0 on 45 visits (asked_if).
    assert (qc.loc["mcdd8", "n_valid"], int((data["mcdd8"] == 0).sum()), int((data["mcdd8"] == 1).sum())) == (381, 366, 15)
    # The pilot forms (four inclusion visits): ALS depression has 11 items in the application and 10 in the export (item 1 left out); the other scores agree.
    assert (mismatch("als54_depression"), mismatch("als54_total"), mismatch("bis10_total"), mismatch("aim40_score")) == (4, 0, 0, 0)
    # An instrument on a handful of visits is read with types and ranges only.
    rare = table[table["instrument"].isin(["aim", "als", "anhedonia", "asq", "atac", "bis_old_form", "tci"])]
    assert (rare["instrument"].nunique(), int(rare["n_valid"].max())) == (7, 5)


def test_history_family_and_treatments(result, qc):
    data, lists, flags = result.data, result.treatments, result.flags
    table = qc[qc["tab"].isin(["antecedents", "antecedent_famille_psy"])]
    assert (table["instrument"].nunique(), len(table)) == (18, 273)
    birth = result.patients                                                        # the answers about the birth: one row per patient
    v0 = data[data["visit"] == "V0"].merge(birth[["usubjid", "neonatal_hospitalisation"]], on="usubjid")
    # Yes/no questions with a 9 for "not known": read as missing with its reason.
    asked = {name: (int(v0[name].notna().sum()), int((v0[name] == 1).sum()), int(qc.loc[name, "missing_code"]))
             for name in ["miscarriage_before", "folic_acid", "neonatal_hospitalisation", "language_delay", "history_ent_v0", "psychiatric_contact"]}
    assert asked == {"miscarriage_before": (1647, 379, 385), "folic_acid": (1187, 362, 790), "neonatal_hospitalisation": (1843, 168, 148), "language_delay": (1804, 415, 87),
                     "history_ent_v0": (1970, 1040, 57), "psychiatric_contact": (1867, 1374, 12)}
    # The names of BP for the birth; a weight typed in kilograms is converted.
    assert (birth["gestational_age"].notna().sum(), birth["gestational_age"].median(), birth["birth_weight"].notna().sum(), birth["birth_weight"].median()) == (1709, 39, 1257, 3300)
    assert ((v0["sudden_complex_language"] == 1).sum(), v0["sudden_complex_language"].notna().sum()) == (253, 1722)   # not a loss of language
    assert (qc.loc["birth_weight", "unit_inferred"], qc.loc["birth_weight", "out_of_range"], data["age_first_words"].median()) == (1, 3, 17)
    # Records packed in one cell are opened: one row per disease, relative or hospitalisation.
    assert lists["list"].value_counts().to_dict() == {
        "medications": 1784, "somatic_ent": 1658, "somatic_rheumatology": 805, "somatic_digestive": 668, "hospitalisations": 588, "family_neurodevelopment": 562,
        "somatic_pulmonary": 346, "somatic_neurological": 329, "somatic_cardiac": 196, "somatic_endocrine": 171, "somatic_cancer": 22}
    relatives = lists[lists["list"] == "family_neurodevelopment"]
    assert ((relatives["relative_asd"] == 1).sum(), (relatives["relative_adhd"] == 1).sum(), relatives["usubjid"].nunique()) == (186, 149, 434)
    assert relatives["relative"].value_counts().to_dict() == {"brother": 143, "mother": 67, "sister": 62, "father": 61, "son": 24, "daughter": 14}
    stays = lists[lists["list"] == "hospitalisations"]
    assert (stays["usubjid"].nunique(), stays["hospitalisation_days"].median(), stays["hospitalisation_year"].notna().sum()) == (388, 21, 343)
    # The treatments are the list of the visit: one row per visit and treatment, the molecule from the name or the generic name.
    drugs = lists[lists["list"] == "medications"]
    assert (drugs.groupby(["usubjid", "visit"]).ngroups, drugs["usubjid"].nunique(), drugs["molecule"].notna().sum()) == (966, 896, 1523)
    assert drugs["visit"].value_counts().head(2).to_dict() == {"V0": 903, "screening": 755}
    assert drugs["molecule"].value_counts().head(3).to_dict() == {"methylphenidate": 202, "melatonin": 142, "sertraline": 108}
    assert "méthylphénidate" not in set(drugs["molecule"]) and (flags["flag"] == "unknown_code").sum() == 203      # the code 2 of stpro2 is retired (D84)
    broken = sum(int(data[name].str.contains("Ã©", regex=False, na=False).sum()) for name in data.select_dtypes("object").columns)
    assert broken == 0                                                                       # the accents written twice are put back


def test_social_and_medico_economic(result, qc):
    data = result.data
    table = qc[qc["tab"] == "sociodemo_medicoeco"]
    assert (table["instrument"].nunique(), len(table)) == (10, 398)
    flags = result.flags[result.flags["variable"].isin(table.index)]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 1263, "derived_doubt": 7184}
    # "Not applicable" is a missing code, not an occupation or a kind of activity.
    assert (qc.loc["job_class", "missing_code"], qc.loc["contract_type", "missing_code"]) == (157, 852)
    v0 = data[data["visit"] == "V0"]
    assert v0["contract_type"].value_counts().to_dict() == {"permanent_contract": 237, "unemployed": 97, "fixed_term_contract": 48, "apprenticeship": 23}
    assert ((v0["assisted_schooling"] == 1).sum(), v0["assisted_schooling"].notna().sum(), (v0["psychiatric_emergency_12m"] == 1).sum(), v0["psychiatric_emergency_12m"].notna().sum()) == (420, 2003, 101, 889)
    assert data[[f"pddqol{k:02d}" for k in range(1, 18)]].notna().all(axis=1).sum() == 363
    assert (v0.loc[v0["psychiatric_emergency_12m"].notna(), "visit_date"].dt.year < 2020).sum() == 3              # the form added in 2020 and 2021


def test_coverage():
    lines = asp.coverage(EXTRACTION)
    counts = lines["status"].value_counts()
    assert (counts.get("covered", 0), counts.get("ignored", 0), counts.get("not_assigned", 0)) == (4242, 122, 0)      # every column is read or ignored
    finished = lines
    assert set(finished["status"]) == {"covered", "ignored"}
    # The only cells left unread: the items of the communication checklist on the 2 visits whose form cannot be told,
    # and the SRS of a relative on the three visits whose date is impossible: no age to tell the child form from the adult form.
    # The 39 others are the boxes of the adult or the child medico-economic form and the time at school of the 2019 form,
    # on the visits whose form does not ask them: 0 never asked, missing (R31).
    unread = finished[finished["n_unread"] > 0]
    checklist = unread[unread["column"].str.fullmatch(r"comm\d+")]
    srs = unread[unread["column"].str.startswith("recs")]
    assert (len(checklist), checklist["n_unread"].sum()) == (70, 95)      # 1,351 when 21 visits had no form: the form is also read from the questions that only one form asks (D68)
    assert (len(srs), srs["n_unread"].max(), len(unread) - len(checklist) - len(srs)) == (80, 3, 39)
    assert counts.sum() == 4364                                             # no column named by a schema is absent from the file
    assert lines.groupby("table")["column"].size().to_dict() == {
        "patient": 93, "autoquestionnaires": 1135, "autoquestionnaires_old_part1": 991, "autoquestionnaires_old_part2": 716,
        "clinique": 24, "neuropsychologie": 376, "bilan_biologique": 82, "antecedents": 190, "antecedent_famille_psy": 20,
        "evaluation_medicale": 335, "sociodemo_medicoeco": 402}


def test_nothing_disappears_silently():
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    for schema in load_schemas(asp.SCHEMAS).values():
        if schema.get("level") == "list":            # cells that hold lists: the invariant holds on the items
            items, item_keys, list_flags = open_lists(raw, keys, schema)
            assert_invariant(items, item_keys, schema)
        elif schema.get("level") == "relatives":     # one row per relative: the invariant holds on these rows
            rows, row_keys, varying_flags = stack_relatives(raw, keys, schema)
            assert_invariant(rows, row_keys, schema)
        elif "derived_from" not in schema:           # columns computed from other rows have no raw cell
            assert_invariant(raw, keys, schema)
