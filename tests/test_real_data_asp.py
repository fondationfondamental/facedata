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
    assert result.flags[result.flags["flag"] == "visit_order"].shape[0] == 42
    # The export writes the centre codes as numbers; they are delivered with two digits, as in the other cohorts.
    assert set(result.data["siteid"].str.len()) == {2} and result.data["siteid"].nunique() == 8


def test_the_four_cohorts_can_be_stacked(result):
    from facedata import bp, dr, sz
    files = {"bp": ROOT / "data" / "bp" / "BPALL_20261113_2.tsv", "sz": ROOT / "data" / "sz" / "SZALL_20261113.tsv",
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
    assert (patients["non_drug_care_04"].sum(), patients["non_drug_care_psychiatrist"].sum()) == (0, 320)
    flags = result.flags[result.flags["variable"].isin(patients.columns)]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 32, "out_of_range": 1}


def test_medical_evaluation(result, qc):
    data = result.data
    table = qc[qc["tab"] == "evaluation_medicale"]
    assert (table["instrument"].nunique(), len(table)) == (16, 339)
    flags = result.flags[result.flags["variable"].isin(set(table.index) | {"vineland_sum_check"})]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 2345, "out_of_range": 44, "score_mismatch": 30}
    v0 = data[data["visit"] == "V0"]
    # The conclusion of the DSM criteria is the diagnosis of the cohort.
    assert (v0["dsm_asd_conclusion"] == 1).sum() == 2008 and v0["dsm_asd_conclusion"].notna().all()
    assert (v0[[f"dsm_criterion_{k}" for k in ["a1", "a2", "a3", "b1", "b2", "b3", "b4", "c", "d"]]] == 1).all(axis=1).sum() == 944
    assert v0["dsm_interview"].value_counts().to_dict() == {"kiddie_sads": 725, "digs": 427, "code_3": 98}       # the code 3 is not in the thesaurus
    # The support levels are named from their wording: the thesaurus numbers them backwards.
    assert ((v0["severity_social_support"] == 1).sum(), (v0["severity_social_very_substantial"] == 1).sum()) == (594, 127)
    # ASDI: the codes are not in order (1 yes, 2 a little, 0 no), so the answers are delivered as words.
    assert v0["asdi01"].value_counts().to_dict() == {"yes": 317, "no": 49, "a_little": 39} and (v0["asdi_criteria_met"] == 1).sum() == 252
    # An age that was first read as a list of codes.
    assert (data["language_disorder_onset_age"].notna().sum(), data["language_disorder_onset_age"].median()) == (50, 3)
    assert v0["tobacco_use"].value_counts().to_dict() == {"dependence": 86, "no": 38, "abuse": 12}
    known = {name: (int(v0[name].notna().sum()), int((v0[name] == 1).sum())) for name in ["depressive_episode", "anxiety_disorder", "adhd", "insomnia"]}
    assert known == {"depressive_episode": (1522, 434), "anxiety_disorder": (1525, 899), "adhd": (1411, 475), "insomnia": (1645, 569)}
    assert (data["depressive_episode_n_episodes"] == 0).sum() == 1144               # a count is 0 where the disorder is absent
    # Two forms in the same columns: the life at inclusion, since the last visit at follow-up.
    assert (data["suicide_attempt_lifetime"].notna().sum(), (data["suicide_attempt_lifetime"] == 1).sum()) == (1658, 191)
    assert (data["suicide_attempt_since_visit"].notna().sum(), (data["suicide_attempt_since_visit"] == 1).sum()) == (124, 4)
    assert data.loc[data["suicide_attempt_since_visit"].notna(), "visit"].isin(["V0", "screening"]).sum() == 0
    # One schema per edition of the Wechsler scales.
    valid = {name: int(data[name].notna().sum()) for name in ["wisc4_icv_index", "wisc5_icv_index", "wais4_icv_index", "gai_index"]}
    assert valid == {"wisc4_icv_index": 205, "wisc5_icv_index": 654, "wais4_icv_index": 995, "gai_index": 666}
    assert (data["wais4_qit"].median(), data["wisc5_qit"].median()) == (110, 105)
    # Vineland-II: raw scores of the sub-domains, standard scores of the domains, their sum checked.
    assert (data["vineland_receptive_raw"].notna().sum(), data["vineland_receptive_raw"].max()) == (1108, 40)
    assert (data["vineland_composite"].notna().sum(), data["vineland_composite"].median()) == (974, 63)
    assert (result.flags["variable"] == "vineland_sum_check").sum() == 30


def test_clinical_measures_and_biology(result, qc):
    data = result.data
    table = qc[qc["tab"].isin(["clinique", "bilan_biologique"])]
    assert (table["instrument"].nunique(), len(table)) == (15, 97)
    flags = result.flags[result.flags["variable"].isin(set(table.index) | {"qtc_bazett", "bmi", "cholesterol_hdl_ratio"})]
    assert "unknown_code" not in set(flags["flag"]) and "unparsed" not in set(flags["flag"])
    counts = flags["flag"].value_counts()
    assert (counts["unit_inferred"], counts["unit_converted"], counts["unit_unknown"], counts["unit_doubt"], counts["out_of_range"]) == (226, 164, 29, 7, 84)
    # Children are measured too: the ranges of the other cohorts would refuse them.
    assert (qc.loc["height", "n_valid"], qc.loc["height", "unit_inferred"], qc.loc["height", "out_of_range"]) == (1100, 3, 9)
    assert (qc.loc["weight", "n_valid"], data["weight"].min() < 25) == (1104, True)
    assert (qc.loc["systolic", "unit_inferred"], qc.loc["diastolic", "unit_inferred"]) == (7, 7)                 # typed in cmHg
    assert data["bmi"].notna().sum() == 1091 and (result.flags["variable"] == "qtc_bazett").sum() == 3
    v0 = data[data["visit"] == "V0"]
    assert v0["tobacco_status"].value_counts().to_dict() == {"non_smoker": 492, "current_smoker": 49, "ex_smoker": 22}
    # No unit column for most analytes: the size of the value gives the unit.
    assert (qc.loc["haemoglobin", "n_valid"], qc.loc["haemoglobin", "unit_inferred"]) == (545, 113)              # g/L brought to g/dL
    assert (qc.loc["glucose", "unit_inferred"], qc.loc["phosphate", "unit_inferred"], qc.loc["monocytes", "unit_inferred"]) == (8, 13, 10)
    assert (qc.loc["cholesterol", "n_valid"], qc.loc["cholesterol", "unit_converted"], qc.loc["triglycerides", "unit_converted"]) == (352, 67, 64)
    assert (qc.loc["vitamin_d", "n_valid"], qc.loc["vitamin_d", "unit_converted"], qc.loc["vitamin_d", "unit_unknown"]) == (265, 19, 29)
    assert (qc.loc["prolactin", "n_valid"], qc.loc["prolactin", "unit_converted"]) == (104, 14)
    assert qc.loc["crp", "censored_left"] == 1
    assert v0["mri"].value_counts().to_dict() == {"not_done": 577, "normal": 167, "abnormal": 54, "result_unknown": 36}
    assert v0["handedness"].value_counts().to_dict() == {"right": 745, "left": 109, "both": 29}      # the names of BP
    assert ((v0["biobank_sample"] == 1).sum(), v0["biobank_sample"].notna().sum()) == (387, 623)


def test_neuropsychology(result, qc):
    data = result.data
    table = qc[qc["tab"] == "neuropsychologie"]
    assert (table["instrument"].nunique(), len(table)) == (16, 373)
    flags = result.flags[result.flags["variable"].isin(table.index)]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 731, "winsorised": 25, "out_of_range": 17}
    # The WAIS-IV item by item: every stored total is the sum of its items, and the digit span total of its three parts.
    wais = result.flags[result.flags["variable"].str.startswith("wais4_")]
    assert "score_mismatch" not in set(wais["flag"])
    valid = {name: int(data[name].notna().sum()) for name in ["wais4_mat_total", "wais4_simil_total", "wais4_vocab_total", "wais4_bd_total", "wais4_ds_total", "wais4_pc_total"]}
    assert valid == {"wais4_mat_total": 286, "wais4_simil_total": 293, "wais4_vocab_total": 212, "wais4_bd_total": 215, "wais4_ds_total": 293, "wais4_pc_total": 5}
    assert ((data["wais4_mat_z"] - (data["wais4_mat_scaled"] - 10) / 3).abs().max() < 0.011)             # the z-score of a scaled score
    # Two sources for an index: the neuropsychology form (_np) and the copy of the clinician in the medical evaluation.
    both = data["wais4_icv_index_np"].notna() & data["wais4_icv_index"].notna()
    assert (data["wais4_icv_index_np"].notna().sum(), both.sum(), (data.loc[both, "wais4_icv_index_np"] == data.loc[both, "wais4_icv_index"]).sum()) == (205, 187, 161)
    assert (data["barona_expected_qit"].notna().sum(), data["barona_qit_difference"].notna().sum()) == (241, 131)
    difference = (data["barona_expected_qit"] - data["wais4_qit_np"] - data["barona_qit_difference"]).abs()
    assert difference.notna().sum() == 131 and difference.max() < 0.2                                    # expected minus measured
    assert (data["trbapp01"].notna().sum(), (data["trbapp01"] == 1).sum(), qc.loc["trbapp01", "missing_code"]) == (746, 71, 55)
    assert (data["lis_score"].notna().sum(), data["face_emotion_total"].notna().sum(), data["errands_time"].notna().sum()) == (698, 701, 563)


def test_new_questionnaires(result, qc):
    data, flags = result.data, result.flags
    table = qc[qc["tab"] == "autoquestionnaires"]
    assert (table["instrument"].nunique(), len(table)) == (29, 1217)
    counts = flags[flags["variable"].isin(table.index)]["flag"].value_counts().to_dict()
    assert counts == {"score_as_stored": 14724, "missing_code": 1457, "score_mismatch": 749, "out_of_range": 59}
    mismatch = lambda name: int(((flags["variable"] == name) & (flags["flag"] == "score_mismatch")).sum())
    # A score typed without any of its items is kept as stored.
    kept = {name: (int(qc.loc[name, "n_valid"]), int(qc.loc[name, "score_as_stored"])) for name in ["adi_a1", "raads_social", "gsq_total", "bdi_total", "adhdrs_total", "cdi_total", "staic_trait"]}
    assert kept == {"adi_a1": (1622, 419), "raads_social": (480, 159), "gsq_total": (602, 157), "bdi_total": (518, 82), "adhdrs_total": (1065, 218),
                    "cdi_total": (457, 114), "staic_trait": (402, 149)}
    # ADI-R: the published algorithm; the stored totals A and C count too many items and are checked by formulas "as stored".
    assert (qc.loc["adi_social_total", "n_valid"], qc.loc["adi_communication_verbal_total", "n_valid"], qc.loc["adi_repetitive_total", "n_valid"]) == (1520, 1531, 1538)
    assert (data["adi_social_total"].median(), data["adi_social_total"].max(), data["adi_repetitive_total"].max()) == (12, 29, 12)
    assert (mismatch("adi_social_total_as_stored"), mismatch("adi_repetitive_total_as_stored"), mismatch("adi_b3")) == (0, 0, 139)
    assert data["adi50_past"].dropna().isin([0, 1, 2, 3, 7, 8, 9]).all()                       # the codes as recorded
    # ADOS: one instrument per module; the stored scores that count a code 3 as 3 are recomputed.
    valid = {name: int(qc.loc[name, "n_valid"]) for name in ["ados3_total", "ados4_total", "ados4_communication", "ados4_social_interaction"]}
    assert valid == {"ados3_total": 797, "ados4_total": 1349, "ados4_communication": 1355, "ados4_social_interaction": 1350}
    assert (mismatch("ados3_total"), mismatch("ados4_total"), mismatch("ados4_stereotyped_restricted")) == (23, 39, 79)
    assert (mismatch("ados4_communication_as_stored"), mismatch("ados4_social_interaction_as_stored")) == (1, 0)
    assert (data["ados4_communication"].max(), data["ados4_social_interaction"].max()) == (8, 14)        # the published maxima
    assert (data["ados3_b08"].isna() & data["ados3_b07"].notna()).sum() == 96                              # the visits of the first edition
    # SRS of a relative: the child form and the adult form share the columns and are told apart by the age at the visit.
    assert data["srs_relative_form"].value_counts().to_dict() == {"srs_relative_adult": 985, "srs_relative_child": 982}
    assert (data["srsc_total"].notna() & data["srsr_total"].notna()).sum() == 0
    # The published key, where the stored scores reverse no item.
    assert (qc.loc["srsc_total", "n_valid"], data["srsc_total"].median(), mismatch("srsc_total_as_stored"), mismatch("srsc_awareness_as_stored")) == (887, 94, 0, 0)
    assert (qc.loc["srsr_total", "n_valid"], data["srsr_total"].median(), mismatch("srsr_total_as_stored"), mismatch("srsr_awareness_as_stored")) == (830, 98, 0, 0)
    assert "srsc_total_t_stored" not in data.columns and "srsr_awr_t_stored" not in data.columns           # the T-scores are not delivered
    # GSQ: the stored proprioceptive sub-score counts the item 40 for the item 41; the delivered one is the sum of its two parts.
    assert (qc.loc["gsq_proprioceptive", "n_valid"], mismatch("gsq_proprioceptive_as_stored"), mismatch("gsq_hyper_proprioceptive")) == (609, 2, 1)
    assert (data["adhdrs19"].value_counts().to_dict(), qc.loc["adhdrs19", "missing_code"]) == ({"yes": 675, "no": 31}, 50)
    # BRIEF: the form of children and the form of adults are two instruments.
    assert data["brief_form"].value_counts().to_dict() == {"brief_parent": 858, "brief_adult": 786}
    assert (qc.loc["briefp_gec", "n_valid"], qc.loc["briefa_gec", "n_valid"], qc.loc["briefa_self_monitor", "n_valid"]) == (793, 757, 777)
    assert (data["briefp_gec"].notna() & data["briefa_gec"].notna()).sum() == 0
    # The questionnaires shared with the other cohorts, and those of this one.
    totals = {name: (int(qc.loc[name, "n_valid"]), float(data[name].median())) for name in ["raads_total", "srsa_total", "ctq_total", "mars_total", "epworth_total", "asrs_total", "staya_total",
                                                                                            "ssp_total", "aqc_total", "cgi_severity", "gaf"]}
    assert totals == {"raads_total": (479, 151), "srsa_total": (467, 110), "ctq_total": (400, 40), "mars_total": (241, 6), "epworth_total": (415, 8), "asrs_total": (559, 40),
                      "staya_total": (581, 49), "ssp_total": (951, 145), "aqc_total": (500, 19), "cgi_severity": (1368, 4), "gaf": (1351, 55)}
    assert (mismatch("ctq_emotional_neglect"), mismatch("ctq_physical_neglect"), mismatch("ctq_total_as_stored"), mismatch("mars_total_as_stored")) == (83, 26, 0, 0)


def test_old_questionnaires(result, qc):
    data, flags = result.data, result.flags
    table = qc[qc["tab"].isin(["autoquestionnaires_old_part1", "autoquestionnaires_old_part2"])]
    assert (table["instrument"].nunique(), len(table)) == (28, 1772)
    counts = flags[flags["variable"].isin(table.index)]["flag"].value_counts()
    assert "unknown_code" not in counts and "unparsed" not in counts
    assert (counts["score_mismatch"], counts["missing_code"], counts["score_as_stored"]) == (550, 405, 99)
    mismatch = lambda name: int(qc.loc[name, "score_mismatch"])
    # The scores that are right as stored: recomputed, no difference.
    right = ["abc_irritability", "cca_pragmatic_skills", "cshq_total", "hama_total", "hamd_total", "lsas_anxiety_total", "rbsr_total", "spq_total", "tas_total", "dcdq_total"]
    assert [mismatch(name) for name in right] == [0] * len(right)
    valid = {name: int(qc.loc[name, "n_valid"]) for name in right + ["lsas_total", "ccc_gcc"]}
    assert valid == {"abc_irritability": 252, "cca_pragmatic_skills": 232, "cshq_total": 106, "hama_total": 360, "hamd_total": 340, "lsas_anxiety_total": 243, "rbsr_total": 308,
                     "spq_total": 184, "tas_total": 38, "dcdq_total": 55, "lsas_total": 235, "ccc_gcc": 106}
    # The three quotients: points for the answers on the scored side, not a sum of the codes.
    quotients = {name: (int(qc.loc[name, "n_valid"]), mismatch(name), float(data[name].median())) for name in ["aq_total", "empathy_quotient_total", "systemizing_quotient_total"]}
    assert quotients == {"aq_total": (250, 1, 35), "empathy_quotient_total": (443, 2, 24), "systemizing_quotient_total": (158, 6, 34)}
    assert (data["aq_total"].max() <= 50, data["empathy_quotient_total"].max() <= 80) == (True, True)
    # Two forms of the communication checklist in the same columns.
    assert data["communication_checklist_form"].value_counts().to_dict() == {"cca": 235, "ccc2": 106}
    forms = flags[flags["flag"] == "version_unknown"]["variable"].value_counts().to_dict()
    assert forms == {"communication_checklist_form": 21, "srs_relative_form": 1}      # a visit with SRS answers and no age
    # PSQI: the components 4, 5 and 7 are recomputed; the stored ones do not cross midnight or do not follow the items.
    psqi = {name: (int(qc.loc[name, "n_valid"]), mismatch(name)) for name in ["psqi_latency_component", "psqi_efficiency", "psqi_disturbances", "psqi_dysfunction", "psqi_total"]}
    assert psqi == {"psqi_latency_component": (189, 0), "psqi_efficiency": (193, 94), "psqi_disturbances": (200, 158), "psqi_dysfunction": (201, 98), "psqi_total": (182, 147)}
    assert data["psqi_total"].median() == 7
    # An instrument on a handful of visits is read with types and ranges only.
    rare = table[table["instrument"].isin(["aim", "als", "anhedonia", "asq", "atac", "bis_old_form", "tci"])]
    assert (rare["instrument"].nunique(), int(rare["n_valid"].max())) == (7, 5)


def test_history_family_and_treatments(result, qc):
    data, lists, flags = result.data, result.treatments, result.flags
    table = qc[qc["tab"].isin(["antecedents", "antecedent_famille_psy"])]
    assert (table["instrument"].nunique(), len(table)) == (17, 240)
    v0 = data[data["visit"] == "V0"]
    # Yes/no questions with a 9 for "not known": read as missing with its reason.
    asked = {name: (int(v0[name].notna().sum()), int((v0[name] == 1).sum()), int(qc.loc[name, "missing_code"]))
             for name in ["miscarriage_before", "folic_acid", "neonatal_hospitalisation", "language_delay", "history_ent", "psychiatric_contact"]}
    assert asked == {"miscarriage_before": (1647, 379, 385), "folic_acid": (1187, 362, 790), "neonatal_hospitalisation": (1843, 168, 148), "language_delay": (1804, 415, 87),
                     "history_ent": (1970, 1040, 57), "psychiatric_contact": (1867, 1374, 12)}
    # The names of BP for the birth; a weight typed in kilograms is converted.
    assert (data["gestational_age"].notna().sum(), data["gestational_age"].median(), data["birth_weight"].notna().sum(), data["birth_weight"].median()) == (1709, 39, 1257, 3300)
    assert ((v0["sudden_complex_language"] == 1).sum(), v0["sudden_complex_language"].notna().sum()) == (253, 1722)   # not a loss of language
    assert (qc.loc["birth_weight", "unit_inferred"], qc.loc["birth_weight", "out_of_range"], data["age_first_words"].median()) == (1, 3, 17)
    # Records packed in one cell are opened: one row per disease, relative or hospitalisation.
    assert lists["list"].value_counts().to_dict() == {
        "medications": 1784, "somatic_ent": 1650, "somatic_rheumatology": 797, "somatic_digestive": 665, "hospitalisations": 584, "family_neurodevelopment": 562,
        "somatic_pulmonary": 346, "somatic_neurological": 328, "somatic_cardiac": 196, "somatic_endocrine": 171, "somatic_cancer": 22}
    relatives = lists[lists["list"] == "family_neurodevelopment"]
    assert ((relatives["relative_asd"] == 1).sum(), (relatives["relative_adhd"] == 1).sum(), relatives["usubjid"].nunique()) == (186, 149, 434)
    assert relatives["relative"].value_counts().to_dict() == {"brother": 143, "mother": 67, "sister": 62, "father": 61, "son": 24, "daughter": 14}
    stays = lists[lists["list"] == "hospitalisations"]
    assert (stays["usubjid"].nunique(), stays["hospitalisation_days"].median(), stays["hospitalisation_year"].notna().sum()) == (388, 21, 342)
    # The treatments are the list of the visit: one row per visit and treatment, the molecule from the name or the generic name.
    drugs = lists[lists["list"] == "medications"]
    assert (drugs.groupby(["usubjid", "visit"]).ngroups, drugs["usubjid"].nunique(), drugs["molecule"].notna().sum()) == (966, 896, 1523)
    assert drugs["visit"].value_counts().head(2).to_dict() == {"V0": 903, "screening": 755}
    assert drugs["molecule"].value_counts().head(3).to_dict() == {"methylphenidate": 202, "melatonin": 142, "sertraline": 108}
    assert "méthylphénidate" not in set(drugs["molecule"]) and (flags["flag"] == "unknown_code").sum() == 204
    broken = sum(int(data[name].str.contains("Ã©", regex=False, na=False).sum()) for name in data.select_dtypes("object").columns)
    assert broken == 0                                                                       # the accents written twice are put back


def test_social_and_medico_economic(result, qc):
    data = result.data
    table = qc[qc["tab"] == "sociodemo_medicoeco"]
    assert (table["instrument"].nunique(), len(table)) == (10, 399)
    flags = result.flags[result.flags["variable"].isin(table.index)]
    assert flags["flag"].value_counts().to_dict() == {"missing_code": 1263, "out_of_range": 4, "unknown_code": 1}
    # "Not applicable" is a missing code, not an occupation or a kind of activity.
    assert (qc.loc["profes", "missing_code"], qc.loc["activite", "missing_code"]) == (157, 852)
    v0 = data[data["visit"] == "V0"]
    assert v0["activite"].value_counts().to_dict() == {"permanent_contract": 237, "unemployed": 97, "fixed_term_contract": 48, "apprenticeship": 23}
    assert ((v0["scolass"] == 1).sum(), v0["scolass"].notna().sum(), (v0["urg"] == 1).sum(), v0["urg"].notna().sum()) == (420, 2003, 101, 889)
    assert data[[f"pddqol{k:02d}" for k in range(1, 18)]].notna().all(axis=1).sum() == 363
    assert (v0.loc[v0["urg"].notna(), "visit_date"].dt.year < 2020).sum() == 3              # the form added in 2020 and 2021


def test_coverage():
    lines = asp.coverage(EXTRACTION)
    counts = lines["status"].value_counts()
    assert (counts.get("covered", 0), counts.get("ignored", 0), counts.get("not_assigned", 0)) == (4242, 122, 0)      # every column is read or ignored
    finished = lines
    assert set(finished["status"]) == {"covered", "ignored"}
    # The only cells left unread: the items of the communication checklist on the 21 visits whose form cannot be told,
    # and the SRS of a relative on the one visit that has no age to tell the child form from the adult form.
    unread = finished[finished["n_unread"] > 0]
    checklist = unread[unread["column"].str.fullmatch(r"comm\d+")]
    srs = unread[unread["column"].str.startswith("recs")]
    assert (len(checklist), checklist["n_unread"].sum()) == (70, 1351)
    assert (len(srs), srs["n_unread"].max(), len(unread) - len(checklist) - len(srs)) == (79, 1, 0)
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
