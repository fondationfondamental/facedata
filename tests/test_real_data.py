"""The real FACE BP extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/bp/PROGRESS.md ("What the first
schemas must produce"). No patient row appears here.
"""

from pathlib import Path

import pytest

from facedata import bp
from facedata.read import prepare_visits, read_extraction
from facedata.relatives import stack_relatives
from facedata.schema import load_schemas
from facedata.treatments import open_lists
from test_pipeline import assert_invariant

ROOT = Path(__file__).parent.parent
EXTRACTION = ROOT / "data" / "bp" / "BPALL_20261030.tsv"
NORMS = ROOT / "norms"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the BP extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return bp.load(EXTRACTION, norms=NORMS)


@pytest.fixture(scope="module")
def qc(result):
    return result.qc.set_index("variable")


def test_visits(result):
    assert len(result.data) == 22070
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 6476 == len(result.patients)


def test_versions(result):
    data = result.data
    assert data["bis_form"].value_counts().to_dict() == {"bis10": 4688, "bis12": 1438}
    assert data["wais_version"].value_counts().to_dict() == {"wais4": 4978, "wais3": 1302}
    assert data["dsm_version"].value_counts().to_dict() == {"dsm4": 16313, "dsm5": 5458}
    assert data["visit_form"].value_counts().to_dict() == {"follow_up": 11621, "inclusion": 6476}
    # Counted on every visit that holds a value of a mood section (inclusion and follow-up forms).
    flags = result.flags[result.flags["variable"] == "dsm_version"]["flag"].value_counts().to_dict()
    assert flags == {"version_inferred": 369, "version_unknown": 38}


def test_scores_agree_with_the_stored_ones(result, qc):
    assert qc.loc["madrs_total", "n_valid"] == 17243
    assert (qc.loc["bis10_total", "n_valid"], qc.loc["bis10_total", "min"], qc.loc["bis10_total", "max"]) == (4636, 36, 113)
    assert qc.loc["bis10_sum12", "n_valid"] == 4661
    assert (qc.loc["bis12_total", "n_valid"], qc.loc["bis12_total", "min"], qc.loc["bis12_total", "max"]) == (1428, 13, 48)
    mismatches = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts().to_dict()
    expected = {"wais4_ds_total_check": 13, "wais3_vocab_total": 3, "wais4_vocab_total": 3, "wais4_mat_total": 1}
    if (NORMS / "wais3_vocabulary.csv").exists():      # the norm table is not part of the repository
        expected["wais3_vocab_scaled_check"] = 19
    for name, count in expected.items():
        assert mismatches.get(name) == count, name


def test_biology(qc):
    crp, glucose, haemoglobin = qc.loc["crp"], qc.loc["glucose"], qc.loc["haemoglobin"]
    assert (crp["n_filled"], crp["censored_left"], crp["censored_right"], crp["unparsed"]) == (13026, 2353, 5, 0)
    assert (glucose["n_filled"], glucose["unit_converted"], glucose["unit_inferred"]) == (12930, 354, 124)
    assert (glucose["unit_doubt"], glucose["out_of_range"], glucose["censored_left"]) == (23, 6, 2)
    assert (haemoglobin["n_filled"], haemoglobin["unit_inferred"], haemoglobin["out_of_range"]) == (13435, 485, 12)


def test_derived_values_and_sign(result, qc):
    if (NORMS / "wais3_vocabulary.csv").exists():      # the norm table is not part of the repository
        assert qc.loc["wais3_vocab_scaled", "derived_doubt"] == 19
        wais_check = result.flags[result.flags["variable"] == "wais3_vocab_scaled_check"]
        assert "norm_missing" not in set(wais_check["flag"])          # every WAIS-III visit is in the table
    assert qc.loc["wais4_ds_scaled", "derived_doubt"] == 13
    flipped = qc.loc[qc["sign_flipped"] > 0, "sign_flipped"].to_dict()
    assert flipped == {"tmt_a_time_z": 778, "tmt_a_errors_z": 771, "tmt_b_time_z": 769,
                       "tmt_b_errors_z": 759, "tmt_ba_time_z": 770}
    assert qc.loc["tmt_a_time_z", "sign_doubt"] == 193


def test_nothing_disappears_silently():
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    for schema in load_schemas(bp.SCHEMAS).values():
        if schema.get("level") == "list":            # cells that hold lists: the invariant holds on the items
            items, item_keys, list_flags = open_lists(raw, keys, schema)
            assert_invariant(items, item_keys, schema)
        elif schema.get("level") == "relatives":     # one row per relative: the invariant holds on these rows
            rows, row_keys, varying_flags = stack_relatives(raw, keys, schema)
            assert_invariant(rows, row_keys, schema)
        elif "derived_from" not in schema:           # columns computed from other rows have no raw cell
            assert_invariant(raw, keys, schema)


def test_patient_tab(result, qc):
    patients = result.patients
    # One row per patient: the key, 23 columns of the PATIENT tab, 11 of the perinatal schema,
    # 52 of the two lifetime treatment forms (45 variables and 7 censoring columns),
    # 14 counts of the family and 12 columns that sum up the relatives.
    assert patients.shape == (6476, 113)
    assert ((qc["tab"] == "PATIENT") & (qc["level"] == "patient")).sum() == 23
    assert patients["sex"].value_counts().to_dict() == {"female": 4097, "male": 2377}
    assert patients["diagnosis"].value_counts().to_dict() == {"bp2": 3095, "bp1": 2714, "bp_nos": 667}
    assert (patients["age_at_inclusion"].min(), patients["age_at_inclusion"].max()) == (17, 86)
    reason, death, collected = qc.loc["followup_end_reason"], qc.loc["death_date"], qc.loc["information_date"]
    assert (reason["n_filled"], reason["n_valid"], reason["column_conflict"]) == (850, 791, 2)
    assert (death["n_valid"], death["date_placeholder"], death["date_partial"]) == (17, 157, 1)
    assert (collected["out_of_range"], collected["unparsed"]) == (24, 2)
    assert result.data["entry_date"].notna().all()
    patient_flags = result.flags[result.flags["variable"].isin(patients.columns)]
    assert not patient_flags.duplicated(subset=["usubjid", "variable", "flag"]).any()   # once per patient


def test_hetero_questionnaires(result, qc):
    assert (qc.loc["fast_total", "n_valid"], qc.loc["fast_total", "score_mismatch"]) == (16507, 0)
    assert (qc.loc["ymrs_total", "n_valid"], qc.loc["ymrs_total", "score_mismatch"]) == (17154, 0)
    domains = ["fast_autonomy", "fast_occupational", "fast_cognitive", "fast_financial", "fast_interpersonal", "fast_leisure"]
    assert list(qc.loc[domains, "score_mismatch"]) == [49, 122, 68, 25, 89, 89]
    assert (qc.loc["etatd_total", "n_valid"], qc.loc["etatd_total", "score_mismatch"]) == (15332, 60)
    assert (qc.loc["etatm_total", "n_valid"], qc.loc["etatm_total", "score_mismatch"]) == (15207, 22)
    assert (qc.loc["gaf", "n_valid"], qc.loc["gaf", "band_middle"], qc.loc["gaf", "unparsed"]) == (14650, 149, 0)
    assert (qc.loc["cgi_efficacy_index", "check_failed"], qc.loc["cgi_severity", "missing_code"]) == (79, 246)
    assert (qc.loc["alda_total", "n_valid"], qc.loc["alda_total", "score_mismatch"]) == (1638, 14)
    assert set(result.data["etatd01"].dropna().unique()) == {0, 1}


def test_constantes_et_ecg(result, qc):
    inferred = qc.loc[qc["unit_inferred"] > 0, "unit_inferred"]
    for name, count in {"height": 182, "weight": 3, "waist": 1, "systolic_supine": 34, "diastolic_supine": 40,
                        "qt_interval": 394, "rr_interval": 106, "qtc_stored": 220}.items():
        assert inferred[name] == count, name
    assert (qc.loc["bmi", "n_valid"], qc.loc["bmi", "score_mismatch"]) == (16319, 34)
    assert (qc.loc["qtc_bazett", "n_valid"], qc.loc["qtc_bazett", "score_mismatch"]) == (7792, 46)
    assert qc.loc["qtc_stored", "out_of_range"] == 164
    assert result.data["height"].between(100, 230).sum() == result.data["height"].notna().sum()


def test_bilan_biologique(qc):
    assert (qc.loc["cholesterol", "unit_doubt"], qc.loc["cholesterol", "unit_inferred"]) == (222, 28)
    assert qc.loc["ldl", "unit_converted"] == 270                  # the unit choice that the export forgets
    assert (qc.loc["haematocrit", "unit_inferred"], qc.loc["mchc", "unit_inferred"]) == (637, 600)
    # Prolactin with no unit chosen: read as mUI/L where the centre reported in it, unknown where it cannot be told.
    assert (qc.loc["prolactin", "unit_converted"], qc.loc["prolactin", "unit_inferred"]) == (157, 330)
    assert (qc.loc["prolactin", "unit_doubt"], qc.loc["prolactin", "unit_unknown"]) == (10, 174)
    # White cells written as percentages are converted with the leukocytes of the visit.
    assert (qc.loc["basophils", "unit_inferred"], qc.loc["basophils", "out_of_range"]) == (475, 4)
    assert (qc.loc["eosinophils", "unit_doubt"], qc.loc["neutrophils", "unit_unknown"]) == (90, 4)
    assert qc.loc["leukocytes", "check_failed"] == 222
    assert (qc.loc["creatinine_clearance", "missing_code"], qc.loc["creatinine_clearance", "censored_right"]) == (246, 177)
    assert (qc.loc["hcg", "censored_left"], qc.loc["hcg", "unit_inferred"]) == (2088, 0)
    assert qc.loc["cholesterol_hdl_ratio", "n_valid"] == 13129


def test_auto_questionnaires(result, qc):
    # The scores recomputed from the items are the stored ones.
    for name in ["prisem_total", "staya_total", "mars_total", "altman_total", "qids_total", "fagerstrom_total",
                 "ctq_total", "als54_total18", "als18_total", "aim_score", "wurs61_sum25", "wurs25_total",
                 "csm_total", "bdhi_assault"]:
        assert qc.loc[name, "score_mismatch"] == 0, name
    assert (qc.loc["qids_total", "n_valid"], qc.loc["staya_total", "n_valid"]) == (19235, 16578)
    # Fagerström: the stored total exists on 3,628 visits only, ours wherever five items are filled.
    assert (qc.loc["fagerstrom_total", "n_valid"], qc.loc["csm_total", "n_valid"]) == (5755, 5605)
    # MAThyS: a lost decimal point is repaired, and the stored total then differs from ours.
    assert qc.loc[qc["instrument"] == "mathys", "unit_inferred"].sum() == 52
    assert qc.loc["mathys_total", "score_mismatch"] == 49
    # PSQI: minutes written x 60 are converted; bedtimes typed as minutes are out of range.
    assert (qc.loc["psqi_latency", "unit_inferred"], qc.loc["psqi_latency", "out_of_range"]) == (277, 83)
    assert (qc.loc["psqi_latency_component", "score_mismatch"], qc.loc["psqi_total", "score_mismatch"]) == (232, 231)
    # ALS and WURS: two forms each, told apart by what only the long questionnaires of the visit have.
    data = result.data
    assert data["als_form"].value_counts().to_dict() == {"als54": 4695, "als18": 1442}
    assert data["wurs_form"].value_counts().to_dict() == {"wurs61": 4639, "wurs25": 1435}
    assert (qc.loc["als54_anxiety", "n_valid"], qc.loc["als54_total18", "n_valid"]) == (4641, 4656)
    assert (qc.loc["als18_total", "n_valid"], qc.loc["wurs61_sum25", "n_valid"], qc.loc["wurs25_total", "n_valid"]) == (1429, 4585, 1426)
    # No visit is in the columns of both forms, and a form is only given where the questionnaire was filled.
    assert not (data["als54_total18"].notna() & data["als18_total"].notna()).any()
    assert not (data["wurs61_sum25"].notna() & data["wurs25_total"].notna()).any()
    assert (data.loc[data["als_form"] == "als54", "bis_form"].dropna() == "bis10").mean() > 0.999
    assert (result.flags["variable"] == "wurs_form").sum() == 49        # a WURS, and no ALS or BIS to tell its form
    assert (qc.loc["bdhi_total", "n_valid"], qc.loc["aq12_total", "n_valid"]) == (4472, 1367)


def test_neuropsychologie(result, qc):
    # Percentile bands: every time and fluency cell is read.
    assert (qc.loc["tmt_a_time_band", "n_valid"], qc.loc["tmt_a_time_band", "unparsed"]) == (5865, 0)
    assert (qc.loc["tmt_ba_time_band", "n_valid"], qc.loc["tmt_ba_time_band", "censored_left"]) == (5869, 72)
    # The TMT error bands are read in the norm tables, with the errors, the age and the years of education.
    assert (qc.loc["tmt_a_errors_band", "n_valid"], qc.loc["tmt_a_errors_band", "norm_missing"]) == (5836, 8)
    assert (qc.loc["tmt_a_errors_band", "censored_right"], qc.loc["tmt_b_errors_band", "censored_right"]) == (5290, 4703)
    band = result.data["tmt_a_errors_band"].dropna()
    years = result.data["visit_date"].dt.year[band.index]
    shares = [(band[(years >= low) & (years <= high)] >= 10).mean() for low, high in [(2009, 2015), (2016, 2021), (2022, 2026)]]
    assert max(shares) - min(shares) < 0.10              # one rule for every year (the stored cells moved by 0.75)
    assert (qc.loc["fluency_p_band", "n_valid"], qc.loc["fluency_p_band", "censored_right"]) == (5836, 0)
    # CVLT: one band for every age. It is read where the cell holds a percentile, and computed from the z-score elsewhere.
    assert (qc.loc["cvlt_trial5_band", "n_valid"], qc.loc["cvlt_trial5_band", "band_from_z"]) == (5817, 68)
    assert (qc.loc["cvlt_short_free_band", "n_valid"], qc.loc["cvlt_short_free_band", "band_from_z"]) == (5801, 2926)
    # Where the EMR wrote a percentile, the band is read again in the norm table: a perfect recall is "this band or higher".
    assert (qc.loc["cvlt_trial5_band", "censored_right"], qc.loc["cvlt_trial5_band", "norm_missing"]) == (1602, 3)
    assert (result.data["cvlt_trial5_band"] == 99).sum() == 0            # the EMR wrote 99 for 1,598 perfect recalls
    assert (qc.loc["cvlt_serial_band", "n_valid"], qc.loc["cvlt_serial_band", "censored_right"]) == (4951, 0)   # as the EMR wrote it
    assert (qc.loc["cvlt_trial1_band", "n_valid"], qc.loc["cvlt_trial1_band", "band_from_z"]) == (5807, 5807)
    assert (qc.loc["cvlt_total_1_5_band", "n_valid"], qc.loc["cvlt_total_1_5_band", "out_of_range"]) == (5556, 246)
    assert (qc.loc["cvlt_trial5_z", "n_filled"], qc.loc["cvlt_short_free_z", "n_filled"]) == (69, 2930)    # the z-scores stay
    assert (qc.loc["cvlt_recency_z", "missing_code"], qc.loc["cvlt_total_1_5_z", "out_of_range"]) == (995, 246)
    assert qc.loc["cvlt_recency_z", "check_failed"] == 43         # a z-score computed from an empty recency
    assert qc.loc["cvlt_recency_band", "check_failed"] == 43      # and the band computed from it
    assert (qc.loc["cvlt_total_1_5", "n_valid"], qc.loc["cvlt_total_1_5", "score_mismatch"]) == (5816, 54)
    # Scores recomputed from the items.
    assert (qc.loc["stroop_interference", "n_valid"], qc.loc["stroop_interference", "score_mismatch"]) == (5767, 29)
    assert (qc.loc["spatial_total", "n_valid"], qc.loc["spatial_total", "score_mismatch"]) == (5210, 41)
    assert (qc.loc["cobra_total", "n_valid"], qc.loc["cobra_total", "score_mismatch"]) == (582, 0)
    assert (qc.loc["errands_errors", "n_valid"], qc.loc["errands_errors", "score_mismatch"]) == (789, 9)
    # CPT-3: about 37 visits hold something else than a T-score.
    assert (qc.loc["cpt3_omissions_t", "n_valid"], qc.loc["cpt3_omissions_t", "out_of_range"]) == (471, 37)
    assert result.data["handedness"].value_counts().to_dict() == {"right": 5440, "left": 568, "both": 121}


def test_substances_and_comorbidity(result, qc):
    data = result.data
    tab = qc[qc["instrument"].isin(["tobacco", "anxiety_v0", "anxiety_fu", "substance_v0", "substance_fu",
                                    "eating_disorder_v0", "eating_disorder_fu", "somatoform_v0", "somatoform_fu"])]
    assert tab["unknown_code"].sum() == 0 and tab["version_unknown"].sum() == 0
    # The inclusion visit and the yearly visits do not answer the same question: two sets of columns.
    assert data["visit_form"].value_counts().to_dict() == {"follow_up": 11621, "inclusion": 6476}
    assert (qc.loc["anxiety_disorder_v0", "n_valid"], qc.loc["anxiety_disorder_fu", "n_valid"]) == (5151, 4531)
    assert (qc.loc["substance_disorder_v0", "n_valid"], qc.loc["substance_disorder_fu", "n_valid"]) == (5232, 4561)
    assert 0.47 < data["anxiety_disorder_v0"].mean() < 0.50 and 0.33 < data["anxiety_disorder_fu"].mean() < 0.36
    assert 0.36 < data["substance_disorder_v0"].mean() < 0.39 and 0.22 < data["substance_disorder_fu"].mean() < 0.25
    for name in ["anxiety_disorder", "substance_disorder", "eating_disorder", "somatoform_disorder"]:
        assert not (data[name + "_v0"].notna() & data[name + "_fu"].notna()).any(), name
    # The boxes of the anxiety disorders are exported only after a yes; after a no they are read as 0,
    # like those of the substances. Both are then shares among all the patients.
    assert (qc.loc["panic_disorder_v0", "n_valid"], qc.loc["alcohol_disorder_v0", "n_valid"]) == (5126, 5218)
    assert 0.15 < data["panic_disorder_v0"].mean() < 0.16 and 0.25 < data["alcohol_disorder_v0"].mean() < 0.26
    assert (data["anxiety_disorder_v0"].isna() & data["panic_disorder_v0"].notna()).sum() == 3    # boxes typed without the first answer
    assert qc.loc["panic_disorder_v0", "n_info"] == 0                  # no flag: no cell was changed
    # Panic disorder: the two detail columns of the form are read as one.
    assert (qc.loc["panic_onset_age_v0", "n_valid"], tab["column_conflict"].sum()) == (413, 5)
    # Tobacco: pack-years typed freely.
    assert qc.loc["tobacco_status", "n_valid"] == 16270
    pack = qc.loc["pack_years"]
    assert (pack["n_valid"], pack["missing_code"], pack["unparsed"], pack["out_of_range"]) == (6305, 101, 34, 29)
    assert tab.loc[tab.index.str.contains("_months_"), "out_of_range"].sum() == 2


def test_evaluation_medicale(result, qc):
    data = result.data
    tab = qc[qc["tab"] == "EVALUATION MEDICALE"]
    assert tab["instrument"].nunique() == 15
    # The only label without a code: the DSM-5 specifier "mixed" on two visits read with the DSM-IV form.
    assert tab["unknown_code"].sum() == 2 and qc.loc["dsm4_current_specifier", "unknown_code"] == 2
    # Each section is split by DSM version: no visit is in the columns of both.
    for name in ["lt_n_mde", "ly_n_mde", "fu_n_mde", "current_episode", "recent_type", "first_episode_type"]:
        assert not (data["dsm4_" + name].notna() & data["dsm5_" + name].notna()).any(), name
    # Lifetime counts: ">20" is censored at 20; "Ne sais pas" is a missing code.
    assert (qc.loc["dsm4_lt_n_mde", "n_valid"], qc.loc["dsm4_lt_n_mde", "censored_right"]) == (3746, 236)
    assert (qc.loc["dsm5_lt_n_mde", "n_valid"], qc.loc["dsm5_lt_n_mde", "censored_right"]) == (903, 55)
    # Counts asked only after a yes: 0 where there was no episode in the past year, or since the last visit.
    assert (qc.loc["dsm4_ly_n_mde", "n_valid"], int((data["dsm4_ly_n_mde"] == 0).sum())) == (4034, 1386)
    assert (qc.loc["dsm4_fu_n_mde", "n_valid"], int((data["dsm4_fu_n_mde"] == 0).sum())) == (6864, 4603)
    # One visit holds a count typed after a "no": a cell that is not empty is kept as written.
    assert (data.loc[data["dsm4_ly_any_episode"] == 0, "dsm4_ly_n_mde"] > 0).sum() == 1
    # The current episode is asked at every visit; the psychotic disorder is split like the comorbidities.
    assert (qc.loc["dsm4_current_episode", "n_valid"], qc.loc["dsm5_current_episode", "n_valid"]) == (11694, 3433)
    assert (qc.loc["psychotic_disorder_v0", "n_valid"], qc.loc["psychotic_disorder_fu", "n_valid"]) == (5370, 9336)
    assert qc.loc["psychotic_onset_date_v0", "date_placeholder"] + qc.loc["psychotic_onset_date_fu", "date_placeholder"] == 686
    # Three columns of the DSM-5 form only.
    assert [qc.loc[name, "n_valid"] for name in ["dsm5_first_hypomania_age", "dsm5_first_mania_age", "dsm5_agethym"]] == [520, 280, 915]
    # DIVA: the number of criteria is recomputed where the nine are answered.
    totals = ["diva_adult_a_total", "diva_child_a_total", "diva_adult_hi_total", "diva_child_hi_total"]
    assert [qc.loc[name, "n_valid"] for name in totals] == [45, 41, 41, 42] and qc.loc[totals, "score_mismatch"].sum() == 7
    # Counts of episodes are mostly 0 and are not winsorised: the rare episodes keep their number.
    assert tab["winsorised"].sum() == 0
    assert (data["dsm4_fu_n_mixed_psychotic"].max(), int((data["dsm4_fu_n_mixed_psychotic"] > 0).sum())) == (4, 43)


def test_care_and_sick_leave(result, qc):
    data = result.data
    tab = qc[qc["tab"] == "SOIN SUIVI HOSP ARRET TRAVAIL"]
    assert tab["instrument"].nunique() == 6 and tab["unknown_code"].sum() == 0 and tab["winsorised"].sum() == 0
    # Hospitalisations: over the life at inclusion, since the last visit at follow-up, in separate columns.
    assert (qc.loc["n_hospitalisations_v0", "n_valid"], qc.loc["n_hospitalisations_fu", "n_valid"]) == (5043, 8374)
    assert round(data["n_hospitalisations_v0"].mean(), 1) == 2.5 and round(data["n_hospitalisations_fu"].mean(), 2) == 0.17
    assert not (data["n_hospitalisations_v0"].notna() & data["n_hospitalisations_fu"].notna()).any()
    assert (qc.loc["n_hospitalisations_v0", "censored_right"], qc.loc["first_hospitalisation_age", "censored_left"]) == (25, 21)
    assert data["hospitalisation_months_fu"].isin([0.25, 0.5, 0.75]).sum() == 378            # a quarter, half, three quarters of a month
    # Sick leave: "Non applicable" is a missing code; number and duration are 0 after a "no".
    assert (qc.loc["sick_leave_12m", "n_valid"], qc.loc["sick_leave_12m", "missing_code"]) == (4042, 1198)
    assert (qc.loc["sick_leave_fu", "n_valid"], qc.loc["sick_leave_fu", "missing_code"]) == (6287, 3074)
    assert (data.loc[data["sick_leave_fu"] == 0, "sick_leave_weeks_fu"] == 0).all()
    weeks = qc.loc["sick_leave_weeks_12m"]
    assert (weeks["n_valid"], weeks["unparsed"], weeks["out_of_range"]) == (3646, 91, 44)
    # Use of care: boxes and numbers are 0 where the part was answered "no".
    assert (qc.loc["care_usual", "n_valid"], qc.loc["care_urgent", "n_valid"]) == (9457, 9295)
    # Two visits have the box ticked after a "no" to the part: a cell that is not empty is kept as written.
    assert (data.loc[data["care_urgent"] == 0, "n_urgent_psychiatrist"] != 0).sum() == 3
    assert (data.loc[data["care_urgent"] == 0, "urgent_psychiatrist"] == 1).sum() == 2
    assert (data["n_urgent_psychologist"].max(), int((data["n_urgent_psychologist"] > 0).sum())) == (24, 37)
    assert data["drug_advice_followed"].value_counts().to_dict() == {"fully": 5879, "partly": 2364, "not_followed": 1200}


def test_treatments(result, qc):
    items, data = result.treatments, result.data
    # One row per patient and medication: the lists of a patient are the same on every row.
    assert (len(items), items["usubjid"].nunique(), items["molecule"].nunique()) == (22634, 4762, 103)
    assert qc.loc["medication", "patient_value_varies"] == 0
    # 99% of the names are found in the table; the others keep what was written and are flagged.
    assert (qc.loc["molecule", "n_valid"], qc.loc["molecule", "unknown_code"]) == (22405, 229)
    groups = items["treatment_group"].value_counts()
    assert (groups["lithium"], groups["anticonvulsant"], groups["antidepressant"], len(groups)) == (2977, 4980, 4786, 10)
    assert (qc.loc["start_date", "n_valid"], qc.loc["end_date", "n_valid"], qc.loc["end_date", "missing_code"]) == (22506, 10832, 3111)
    assert (qc.loc["units_per_day", "missing_code"], qc.loc["daily_dose", "n_valid"]) == (889, 6402)
    # On the day of the visit: computed for the patients who have a list.
    assert qc.loc["on_lithium", "instrument"] == "medications_at_visit"
    assert (data["on_lithium"].notna().sum(), round(data["on_lithium"].mean(), 2)) == (18050, 0.36)
    first = data[data["visit"] == "V0"]
    assert round(first["on_lithium"].mean(), 2) == 0.30 and round(first["on_anticonvulsant"].mean(), 2) == 0.44
    assert data.loc[~data["usubjid"].isin(items["usubjid"]), "on_lithium"].isna().all()


def test_treatment_forms(result, qc):
    data, patients = result.data, result.patients
    forms = qc[qc["instrument"].isin(["drug_classes_lifetime", "non_drug_lifetime", "non_drug_fu"])]
    assert forms["unknown_code"].sum() == 0 and forms["winsorised"].sum() == 0 and forms["patient_value_varies"].sum() == 0
    # The two lifetime forms are repeated on every row of the patient: one value per patient.
    assert "ever_lithium" in patients.columns and "ever_lithium" not in data.columns
    assert (qc.loc["ever_lithium", "n_valid"], round(patients["ever_lithium"].mean(), 2)) == (2521, 0.47)
    # Months of exposure: a list that stops at 240, and 0 where the patient never took the class.
    assert (qc.loc["lithium_months", "n_valid"], qc.loc["lithium_months", "censored_right"], patients["lithium_months"].max()) == (2177, 35, 240)
    assert (patients.loc[patients["ever_lithium"] == 0, "lithium_months"] == 0).all()
    assert (qc.loc["ever_non_drug_treatment", "n_valid"], round(patients["ever_cbt"].mean(), 2)) == (1243, 0.16)
    # The follow-up form: boxes are 0 after a "no" to the first question.
    assert (qc.loc["non_drug_treatment_fu", "n_valid"], round(data["non_drug_treatment_fu"].mean(), 2)) == (9254, 0.34)
    assert (data.loc[data["non_drug_treatment_fu"] == 0, "cbt_fu"] == 0).all()
    # 1000-01-01 is written in every date that was not typed.
    assert forms.loc[forms["instrument"] != "drug_classes_lifetime", "date_placeholder"].sum() == 5268


def test_social(result, qc):
    data = result.data
    tab = qc[qc["tab"] == "SOCIAL"]
    assert tab["unknown_code"].sum() == 0 and tab["unparsed"].sum() == 0
    assert data["marital_status"].value_counts().to_dict() == {"couple": 2404, "single": 1975, "divorced": 383, "separated": 181, "widowed": 29}
    # Education is a list of levels: two of them are exported as words, the others as codes.
    levels = data["education_level"].value_counts()
    assert (levels["bac"], levels["bac_plus_5"], levels["primary_certificate"], len(levels)) == (712, 1198, 21, 17)
    # Code 7 of the source of income holds "other" as well as "no income"; code 3 of the work status never appears.
    assert data["income_source"].value_counts()["none_or_other"] == 1067
    assert "student" not in set(data["work_status"].dropna()) and (data["work_status"] == "employed").sum() == 2300
    assert (qc.loc["last_job_end_date", "n_valid"], qc.loc["last_job_end_date", "date_placeholder"]) == (827, 162)
    assert (qc.loc["total_work_years", "out_of_range"], qc.loc["longest_job_years", "out_of_range"], qc.loc["household_size", "out_of_range"]) == (4, 1, 5)
    assert (qc.loc["debt_level", "n_valid"], qc.loc["debt_level", "missing_code"]) == (4464, 153)
    assert qc.loc["job_class_fu", "n_valid"] == 214
    # The legal protection measure: one column of the PATIENT tab, once per patient.
    assert result.patients["protection_measure"].value_counts().to_dict() == {"none": 4774, "curatorship": 62, "guardianship": 4}


def test_perinatal(result, qc):
    patients = result.patients
    # One value per patient: the columns are in the patients table, not in the visit table.
    assert "birth_weight" in patients.columns and "birth_weight" not in result.data.columns
    assert patients["birth_term"].value_counts().to_dict() == {"term": 4107, "preterm": 475, "post_term": 161}
    assert patients["birth_type"].value_counts().to_dict() == {"vaginal": 4086, "caesarean": 444}
    # A 0 is a missing code in the measures; months typed as a gestational age are converted to weeks.
    weight, weeks = qc.loc["birth_weight"], qc.loc["gestational_age"]
    assert (weight["n_valid"], weight["missing_code"], weight["out_of_range"]) == (2429, 34, 17)
    assert (weeks["n_valid"], weeks["unit_inferred"], weeks["out_of_range"]) == (1193, 14, 22)
    assert (qc.loc["apgar_1min", "n_valid"], qc.loc["apgar_1min", "missing_code"], qc.loc["apgar_1min", "out_of_range"]) == (907, 53, 2)
    assert patients["gestational_age"].between(20, 45).sum() == 1193
    # The form filled again at a yearly visit: the first answer is kept, the patient is flagged.
    assert (qc.loc["mother_age_at_birth", "n_valid"], qc.loc["mother_age_at_birth", "patient_value_varies"]) == (4539, 56)
    tab = qc[qc["instrument"] == "perinatal"]
    assert tab["unknown_code"].sum() == 0 and tab["unparsed"].sum() == 0
    # The birth measures are not winsorised: a very low birth weight is kept as it is.
    assert tab["winsorised"].sum() == 0
    assert (patients["birth_weight"].min(), patients["gestational_age"].min()) == (500, 25)


def test_suicide(result, qc):
    data = result.data
    # The same five columns hold lifetime answers at inclusion and answers since the last visit at follow-up.
    assert (qc.loc["isf05_lifetime", "n_valid"], qc.loc["isf05_since_visit", "n_valid"]) == (5897, 9181)
    assert round(data["isf05_lifetime"].mean(), 2) == 0.38 and round(data["isf05_since_visit"].mean(), 2) == 0.03
    assert data["isf05_lifetime"].notna().sum() + data["isf05_since_visit"].notna().sum() == (data["isf05_lifetime"].notna() | data["isf05_since_visit"].notna()).sum()
    assert qc.loc[qc["instrument"].isin(["isf_lifetime", "isf_since_visit"]), "unknown_code"].sum() == 0
    # Follow-up visits of 2022 and 2023: every "yes" and its "when" keep their value and are flagged as doubtful.
    doubt = qc.loc[qc["instrument"] == "isf_since_visit", "period_doubt"]
    assert (qc.loc["isf05_since_visit", "period_doubt"], qc.loc["isf05_since_visit_when", "period_doubt"]) == (114, 88)
    assert (qc.loc["isf01_since_visit", "period_doubt"], doubt.sum()) == (445, 2688)
    assert qc.loc[qc["instrument"] == "isf_lifetime", "period_doubt"].sum() == 0
    flagged = result.flags[result.flags["flag"] == "period_doubt"]
    assert set(flagged["severity"]) == {"discrepancy"} and (flagged["value"].astype(str) != "").all()
    # The date of the first attempt: 2011-11-11 is a placeholder.
    assert (qc.loc["first_attempt_date", "n_valid"], qc.loc["first_attempt_date", "missing_code"]) == (2147, 1133)
    assert (qc.loc["first_attempt_date", "date_placeholder"], qc.loc["n_attempts", "out_of_range"]) == (148, 1)
    # Columbia and C-SSRS: every answer of the drop-downs has a code.
    tab = qc[qc["instrument"].isin(["most_violent_attempt", "most_serious_attempt", "cssrs", "suicide_attempts"])]
    assert tab["unknown_code"].sum() == 0
    assert (qc.loc["violent_method", "n_valid"], qc.loc["serious_method", "n_valid"]) == (336, 456)
    assert (qc.loc["css0101", "n_valid"], qc.loc["cssrs_intensity", "n_valid"]) == (3543, 1000)


def test_family_history(result, qc):
    relatives, patients = result.relatives, result.patients
    # One row per patient and relative about whom something is known.
    assert (len(relatives), relatives["usubjid"].nunique(), relatives.shape[1]) == (29101, 5529, 20)
    kinship = relatives["kinship"].value_counts()
    assert (kinship["mother"], kinship["father"], kinship["sister"], len(kinship)) == (4610, 5106, 1716, 10)
    assert not relatives.duplicated(["usubjid", "relative"]).any()
    disorder = relatives["relative_disorder"].value_counts()
    assert (disorder["unipolar"], disorder["bipolar"], disorder["schizophrenia"], disorder["none"]) == (4670, 1863, 243, 5295)
    assert (qc.loc["relative_disorder", "missing_code"], qc.loc["relative_disorder", "unknown_code"]) == (2466, 0)
    # Boxes ticked in one cell: one yes/no variable per box, and one for any substance.
    boxes = relatives[["relative_substance", "relative_alcohol", "relative_cannabis", "relative_other_substance"]]
    assert list(boxes.sum()) == [3478, 2848, 591, 513] and qc.loc["relative_alcohol", "unknown_code"] == 0
    known = boxes[boxes.notna().all(axis=1)]
    assert len(known) == 12702 and (known["relative_substance"] == known.drop(columns="relative_substance").max(axis=1)).all()
    # Most dates were never typed: a placeholder is a missing code.
    assert (qc.loc["relative_birth_date", "date_placeholder"], qc.loc["relative_birth_date", "n_valid"]) == (10994, 16420)
    # Counts: with no sister, no sister has anything.
    assert (qc.loc["n_sisters", "n_valid"], qc.loc["n_sisters_affected", "n_valid"]) == (5357, 5125)
    assert ((patients["n_sisters"] == 0).sum(), (patients.loc[patients["n_sisters"] == 0, "n_sisters_affected"] == 0).sum()) == (2081, 2080)
    assert (qc.loc["mother_affected", "missing_code"], round(patients["mother_affected"].mean(), 2)) == (199, 0.60)
    # The relatives summed up per patient: yes, no, or not known.
    assert qc.loc["fdr_bipolar", "instrument"] == "family_history_per_patient"
    assert patients["fdr_bipolar"].value_counts().to_dict() == {0.0: 2386, 1.0: 1208}
    assert patients["gp_bipolar"].value_counts().to_dict() == {0.0: 2030, 1.0: 449}
    first_degree = relatives[relatives["degree"] == 1]
    with_bipolar = first_degree.loc[first_degree["relative_disorder"] == "bipolar", "usubjid"]
    assert set(patients.loc[patients["fdr_bipolar"] == 1, "usubjid"]) == set(with_bipolar)
    counts = ["mother_affected", "father_affected", "n_sisters_affected", "n_brothers_affected", "n_daughters_affected", "n_sons_affected"]
    assert patients.loc[patients["fdr_bipolar"] == 0, counts].notna().all().all()


def test_medical_history(result, qc):
    data = result.data
    medical = qc[qc["instrument"].str.endswith(("_history_v0", "_history_fu"))]
    # Nine sections, each in an inclusion form and a yearly form: never two forms in one column.
    assert (medical["instrument"].nunique(), len(medical)) == (18, 374)
    first = data["visit"] == "V0"
    assert (qc.loc["migraine_v0", "n_valid"], data["migraine_v0"].sum(), data.loc[~first, "migraine_v0"].notna().sum()) == (4764, 1069, 0)
    assert (qc.loc["migraine_fu", "n_valid"], data["migraine_fu"].sum(), data.loc[first, "migraine_fu"].notna().sum()) == (1811, 246, 0)
    assert (data["hypertension_v0"].sum(), data["diabetes_v0"].sum()) == (444, 163)
    # Every list of boxes is read whole, and almost nothing is lost: one count and two dates.
    flags = medical[["unknown_code", "unparsed", "out_of_range", "winsorised"]].sum()
    assert list(flags) == [0, 1, 2, 0] and medical["date_placeholder"].sum() == 21903
    # Boxes shown only after a yes are 0 after a no, and stay missing after "unknown".
    no_allergy = data["allergic_inflammatory_v0"] == 0
    assert (no_allergy.sum(), (data.loc[no_allergy, "asthma_v0"] == 0).sum(), data["asthma_v0"].sum()) == (4193, 4193, 462)
    assert data.loc[data["allergic_inflammatory_v0"].isna(), "asthma_v0"].isna().all()
    assert (data.loc[data["eye_disease_v0"] == 0, "closed_angle_glaucoma_v0"] == 0).all() and data["closed_angle_glaucoma_v0"].sum() == 7
    # Numbers of pregnancies: "Aucune" is 0, and with no pregnancy the other numbers are 0 unless typed otherwise.
    assert (qc.loc["n_pregnancies_v0", "n_valid"], data["n_pregnancies_v0"].sum(), data["n_pregnancies_v0"].max()) == (3611, 5219, 11)
    none = data["n_pregnancies_v0"] == 0
    assert (none.sum(), (data.loc[none, "n_live_births_v0"] == 0).sum()) == (1513, 1506)
