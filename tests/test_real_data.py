"""The real FACE BP extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/bp/PROGRESS.md ("What the first
schemas must produce"). No patient row appears here.
"""

from pathlib import Path

import pandas as pd
import pytest

from facedata import bp
from facedata.read import prepare_visits, read_extraction
from facedata.relatives import stack_relatives
from facedata.schema import load_schemas
from facedata.treatments import open_lists
from test_pipeline import assert_invariant

ROOT = Path(__file__).parent.parent
EXTRACTION = ROOT / "data" / "bp" / "BPALL_20261113_2.tsv"
NORMS = ROOT / "norms"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the BP extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return bp.load(EXTRACTION, norms=NORMS)


@pytest.fixture(scope="module")
def qc(result):
    return result.qc.set_index("variable")


def test_visits(result):
    assert len(result.data) == 22171
    assert not result.data.duplicated(subset=["usubjid", "visit"]).any()
    assert result.data["usubjid"].nunique() == 6498 == len(result.patients)


def test_tables_say_their_cohort_and_patients_have_the_stable_code(result):
    for table in [result.data, result.patients, result.flags, result.treatments, result.relatives]:
        assert table.columns[0] == "cohort" and set(table["cohort"]) == {"bp"}
    # The patient code of the foundation: one per patient, the key between two extractions and two cohorts.
    assert list(result.patients.columns[:2]) == ["cohort", "usubjid"] and "fondacode" in result.patients.columns
    assert result.patients["fondacode"].notna().all() and result.patients["fondacode"].is_unique


def test_versions(result):
    data = result.data
    assert data["bis_form"].value_counts().to_dict() == {"bis10": 4689, "bis12": 1451}
    assert data["wais_version"].value_counts().to_dict() == {"wais4": 5011, "wais3": 1302}
    assert data["dsm_version"].value_counts().to_dict() == {"dsm4": 16380, "dsm5": 5506}
    assert data["visit_form"].value_counts().to_dict() == {"follow_up": 11686, "inclusion": 6498}
    # Counted on every visit that holds a value of a mood section (inclusion and follow-up forms).
    flags = result.flags[result.flags["variable"] == "dsm_version"]["flag"].value_counts().to_dict()
    # A placeholder date alone does not make a form filled (D122). A follow-up that holds a column of the old form is
    # DSM-IV whatever its label or date (D180): 35 labelled DSM-5 are overridden, 14 with no version get none.
    assert flags == {"version_inferred": 359, "version_overridden": 35, "version_unknown": 18}


def test_scores_agree_with_the_stored_ones(result, qc):
    assert qc.loc["madrs_total", "n_valid"] == 17334
    assert (qc.loc["bis10_total", "n_valid"], qc.loc["bis10_total", "min"], qc.loc["bis10_total", "max"]) == (4638, 36, 113)
    assert qc.loc["bis10_sum12", "n_valid"] == 4662
    assert (qc.loc["bis12_total", "n_valid"], qc.loc["bis12_total", "min"], qc.loc["bis12_total", "max"]) == (1444, 13, 48)
    mismatches = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts().to_dict()
    # A check that is not delivered files its mismatch under the stored value it checks (wais4_ds_total).
    expected = {"wais4_ds_total": 13, "wais3_vocab_total": 3, "wais4_vocab_total": 3, "wais4_mat_total": 1}
    if (NORMS / "wais3_vocabulary.csv").exists():      # the norm table is not part of the repository
        expected["wais3_vocab_scaled"] = 11              # the scaled score is read in the table from the recomputed total (D135)
    for name, count in expected.items():
        assert mismatches.get(name) == count, name


def test_biology(qc):
    crp, glucose, haemoglobin = qc.loc["crp"], qc.loc["glucose"], qc.loc["haemoglobin"]
    assert (crp["n_filled"], crp["censored_left"], crp["censored_right"], crp["unparsed"]) == (13095, 2359, 5, 0)
    assert (crp["n_valid"], crp["missing_code"]) == (12672, 399)       # a CRP of exactly 0 is not a measurement (D101); 29 shifted visits are removed (biology review, D144)
    assert (glucose["n_filled"], glucose["unit_converted"], glucose["unit_inferred"]) == (12993, 356, 124)
    assert (glucose["unit_doubt"], glucose["out_of_range"], glucose["censored_left"]) == (23, 7, 2)
    assert (haemoglobin["n_filled"], haemoglobin["unit_inferred"], haemoglobin["out_of_range"]) == (13505, 487, 12)


def test_derived_values_and_sign(result, qc):
    if (NORMS / "wais3_vocabulary.csv").exists():      # the norm table is not part of the repository
        assert (qc.loc["wais3_vocab_scaled", "derived_doubt"], qc.loc["wais3_vocab_scaled", "norm_missing"]) == (0, 0)   # read in the table, not derived (D135)
    assert qc.loc["wais4_ds_scaled", "derived_doubt"] == 0
    flipped = qc.loc[(qc["sign_flipped"] > 0) & (qc["instrument"] == "tmt"), "sign_flipped"].to_dict()
    # The TMT z-scores are computed again; a stored one with the other sign is `sign_flipped`, no value is turned (D135).
    assert flipped == {"tmt_a_time_z": 740, "tmt_a_errors_z": 756, "tmt_b_time_z": 740,
                       "tmt_b_errors_z": 739, "tmt_ba_time_z": 743}
    # The only other values turned are the eight MAThyS items of the old form (D91), and the typed errands z-scores.
    assert set(qc.loc[(qc["sign_flipped"] > 0) & (qc["instrument"] != "tmt"), "instrument"]) == {"mathys", "errands_test"}
    assert (qc["sign_flipped"] > 0).sum() == 18
    assert qc.loc["tmt_a_time_z", "sign_doubt"] == 0                   # the per-centre sign search is gone


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
    # 53 of the two lifetime treatment forms (46 variables, the IPSRT format as two boxes, and 7 censoring
    # columns), 14 counts of the family and 12 columns that sum up the relatives.
    assert patients.shape == (6498, 114)
    assert ((qc["tab"] == "PATIENT") & (qc["level"] == "patient")).sum() == 22
    assert patients["sex"].value_counts().to_dict() == {"female": 4108, "male": 2389}
    assert patients["diagnosis"].value_counts().to_dict() == {"bp2": 3111, "bp1": 2718, "bp_nos": 669}
    assert (patients["age_at_inclusion"].min(), patients["age_at_inclusion"].max()) == (17, 86)
    reason, death, collected = qc.loc["followup_end_reason"], qc.loc["death_date"], qc.loc["information_date"]
    assert (reason["n_filled"], reason["n_valid"], reason["column_conflict"]) == (848, 789, 2)
    assert (death["n_valid"], death["date_placeholder"], death["date_partial"]) == (17, 165, 1)
    assert (collected["out_of_range"], collected["unparsed"]) == (24, 2)
    assert result.data["entry_date"].notna().all()
    patient_flags = result.flags[result.flags["variable"].isin(patients.columns)]
    assert not patient_flags.duplicated(subset=["usubjid", "variable", "flag"]).any()   # once per patient


def test_hetero_questionnaires(result, qc):
    assert (qc.loc["fast_total", "n_valid"], qc.loc["fast_total", "score_mismatch"]) == (16604, 0)
    assert (qc.loc["ymrs_total", "n_valid"], qc.loc["ymrs_total", "score_mismatch"]) == (17246, 0)
    domains = ["fast_autonomy", "fast_occupational", "fast_cognitive", "fast_financial", "fast_interpersonal", "fast_leisure"]
    assert list(qc.loc[domains, "score_mismatch"]) == [50, 122, 69, 25, 91, 89]
    assert (qc.loc["etatd_total", "n_valid"], qc.loc["etatd_total", "score_mismatch"]) == (15414, 61)
    assert (qc.loc["etatm_total", "n_valid"], qc.loc["etatm_total", "score_mismatch"]) == (15283, 22)
    assert (qc.loc["gaf", "n_valid"], qc.loc["gaf", "band_middle"], qc.loc["gaf", "unparsed"]) == (14728, 149, 0)
    # The efficacy index is a score from the effect and the side effects; the stored one is the check (D170).
    assert [qc.loc["cgi_efficacy_index", flag] for flag in ["score_mismatch", "score_not_recomputed"]] == [74, 6]
    assert qc.loc["cgi_severity", "missing_code"] == 247
    # The improvement, the therapeutic effect and the index are asked at the follow-up visits only: 1,068 inclusion values are left out.
    at_inclusion = result.data["visit_month"] == 0
    assert (qc.loc["cgi_improvement", "n_valid"], result.data.loc[at_inclusion, "cgi_improvement"].notna().sum()) == (8932, 0)
    assert (result.data.loc[at_inclusion, "cgi_severity"].notna().sum(), result.data.loc[at_inclusion, "gaf"].notna().sum()) == (5648, 5264)
    assert (qc.loc["alda_total", "n_valid"], qc.loc["alda_total", "score_mismatch"]) == (1669, 14)
    assert set(result.data["etatd01"].dropna().unique()) == {0, 1}


def test_constantes_et_ecg(result, qc):
    inferred = qc.loc[qc["unit_inferred"] > 0, "unit_inferred"]
    for name, count in {"height": 182, "weight": 3, "waist": 1, "systolic_supine": 34, "diastolic_supine": 40,
                        "qt_interval": 395, "rr_interval": 109, "qtc_stored": 220}.items():
        assert inferred[name] == count, name
    assert (qc.loc["bmi", "n_valid"], qc.loc["bmi", "score_mismatch"]) == (16407, 34)
    # The QTc is computed from the heart rate of the ECG: the RR typed in two centres does not fit it.
    assert (qc.loc["qtc_bazett", "n_valid"], qc.loc["qtc_bazett", "score_mismatch"], qc.loc["rr_interval", "check_failed"]) == (8963, 1185, 739)
    assert (result.data["qtc_bazett"] < 0.35).sum() == 226                # 635 with the typed RR
    assert qc.loc["qtc_stored", "out_of_range"] == 168
    assert result.data["height"].between(100, 230).sum() == result.data["height"].notna().sum()


def test_bilan_biologique(qc):
    assert (qc.loc["cholesterol", "unit_doubt"], qc.loc["cholesterol", "unit_inferred"]) == (224, 28)
    assert qc.loc["ldl", "unit_converted"] == 270                  # the unit choice that the export forgets
    assert (qc.loc["haematocrit", "unit_inferred"], qc.loc["mchc", "unit_inferred"]) == (641, 604)
    # Prolactin with no unit chosen: read as mUI/L where the centre reported in it, unknown where it cannot be told.
    # Below 0.2 it is read as mg/L (x1000): 44 more `unit_inferred` (biology review, D144).
    assert (qc.loc["prolactin", "unit_converted"], qc.loc["prolactin", "unit_inferred"]) == (158, 376)
    assert (qc.loc["prolactin", "unit_doubt"], qc.loc["prolactin", "unit_unknown"]) == (10, 176)
    # White cells written as percentages are converted with the leukocytes of the visit.
    assert (qc.loc["basophils", "unit_inferred"], qc.loc["basophils", "out_of_range"]) == (476, 4)
    assert (qc.loc["eosinophils", "unit_doubt"], qc.loc["neutrophils", "unit_unknown"]) == (90, 4)
    assert qc.loc["leukocytes", "check_failed"] == 221                 # (biology review, D144)
    assert (qc.loc["creatinine_clearance", "missing_code"], qc.loc["creatinine_clearance", "censored_right"]) == (246, 177)
    assert (qc.loc["hcg", "censored_left"], qc.loc["hcg", "unit_inferred"]) == (2094, 0)
    assert qc.loc["cholesterol_hdl_ratio", "n_valid"] == 13174        # (biology review, D144)
    # Platelets typed in hundreds of G/L (2.47 for 247) are read as such; a prolactin of 0 is "nothing measured" (D130).
    assert (qc.loc["platelets", "unit_inferred"], qc.loc["platelets", "out_of_range"], qc.loc["prolactin", "missing_code"]) == (79, 4, 19)
    # HbA1c in mmol/mol under the label %: brought to % with the IFCC-NGSP master equation (D127).
    assert (qc.loc["hba1c", "unit_inferred"], qc.loc["hba1c", "out_of_range"]) == (8, 32)


def test_auto_questionnaires(result, qc):
    # The scores recomputed from the items are the stored ones.
    for name in ["prisem_total", "staya_total", "mars_total", "altman_total", "qids_total", "fagerstrom_total",
                 "ctq_total", "als54_total18", "als18_total", "aim40_score20", "aim20_score", "wurs61_sum25",
                 "wurs25_total", "csm_total", "bdhi_assault", "epworth_total"]:
        assert qc.loc[name, "score_mismatch"] == 0, name
    assert (qc.loc["qids_total", "n_valid"], qc.loc["staya_total", "n_valid"]) == (19430, 16678)
    # Epworth, Fagerström item 3 and CSM item 7: the answers that the export lost until November 2026 are back.
    assert (qc.loc["epworth_total", "n_valid"], qc.loc["fagerstrom_total", "n_valid"], qc.loc["csm_total", "n_valid"]) == (16648, 5738, 6076)
    assert (int((result.data["fagers03"] == 0).sum()), int((result.data["csm07"] == 5).sum())) == (2119, 451)
    assert result.data["epworth_when"].value_counts().to_dict() == {"any_time": 5476, "after_meals": 4825, "fixed_hours": 3518, "night": 2423}
    # MAThyS: a lost decimal point is repaired.
    assert qc.loc[qc["instrument"] == "mathys", "unit_inferred"].sum() == 52
    # The old form stored the eight reversed items already turned: they are turned back before September 2021,
    # and they are not delivered while the centres changed form, until the end of 2022 (D91); from 2023 a centre and year
    # whose visits clearly lean to the old direction are turned too (84 visits of one centre in 2024 and 2025, D200).
    mathys = result.data
    assert (qc.loc["mathys17", "sign_flipped"], qc.loc["mathys17", "period_removed"], qc.loc["mathys11", "period_removed"]) == (11441, 1433, 0)
    assert (qc.loc["mathys_total", "n_valid"], qc.loc["mathys_interaction", "n_valid"]) == (14251, 15811)
    changing = mathys["visit_date"].between("2021-09-01", "2022-12-31")
    assert mathys.loc[changing, ["mathys_total", "mathys_cognition", "mathys17"]].notna().sum().sum() == 0
    # Once turned, item 17 goes against the items of its sub-score on both forms, as its key says.
    old_form, new_form = mathys["visit_date"] < "2021-09-01", mathys["visit_date"] >= "2023-01-01"
    with_it = mathys[["mathys11", "mathys15", "mathys16"]].sum(axis=1, min_count=3)
    assert mathys.loc[old_form, "mathys17"].corr(with_it[old_form]) < -0.3
    assert mathys.loc[new_form, "mathys17"].corr(with_it[new_form]) < -0.3
    # PSQI: minutes written x 60 are converted; bedtimes typed as minutes are out of range.
    assert (qc.loc["psqi_latency", "unit_inferred"], qc.loc["psqi_latency", "out_of_range"]) == (279, 83)
    assert (qc.loc["psqi_latency_component", "score_mismatch"], qc.loc["psqi_total", "score_mismatch"]) == (234, 725)       # the efficiency is recomputed, with the 12-hour bedtimes corrected (BP D132)
    assert (qc.loc["psqi_efficiency", "n_valid"], qc.loc["psqi_efficiency", "score_mismatch"], qc.loc["psqi_efficiency", "score_not_recomputed"]) == (16676, 521, 24)
    # The EQ-5D index is the table of the application, from the five answers (D133); the part A of the ASRS and the criteria of the STOP-BANG are counted.
    assert (qc.loc["eq5d_index", "n_valid"], qc.loc["eq5d_index", "score_mismatch"]) == (12668, 0)
    assert (qc.loc["asrs_parta", "n_valid"], qc.loc["stopbang_count7", "n_valid"]) == (1320, 4032)
    assert (qc.loc["bis10_general", "score_not_recomputed"], qc.loc["bis12_general", "score_not_recomputed"], qc.loc["bis10_general", "score_mismatch"]) == (27, 7, 0)
    # Hours of sleep and times of day are from 0 to 24 hours: 3 nights of more than 24 hours are impossible (D130).
    assert qc.loc["psqi_sleep_hours", "out_of_range"] == 3
    # ALS, WURS and AIM: two forms each, told apart by what only the long questionnaires of the visit have.
    data = result.data
    assert data["als_form"].value_counts().to_dict() == {"als54": 4696, "als18": 1456}
    assert data["wurs_form"].value_counts().to_dict() == {"wurs61": 4640, "wurs25": 1447}
    assert data["aim_form"].value_counts().to_dict() == {"aim40": 4673, "aim20": 1442}
    assert (qc.loc["aim40_score20", "n_valid"], qc.loc["aim20_score", "n_valid"]) == (4647, 1425)
    assert (qc.loc["als54_anxiety", "n_valid"], qc.loc["als54_total18", "n_valid"]) == (4642, 4657)
    assert (qc.loc["als18_total", "n_valid"], qc.loc["wurs61_sum25", "n_valid"], qc.loc["wurs25_total", "n_valid"]) == (1444, 4586, 1439)
    # No visit is in the columns of both forms, and a form is only given where the questionnaire was filled.
    assert not (data["als54_total18"].notna() & data["als18_total"].notna()).any()
    assert not (data["wurs61_sum25"].notna() & data["wurs25_total"].notna()).any()
    assert not (data["aim40_score20"].notna() & data["aim20_score"].notna()).any()
    both = data["aim_form"].notna() & data["als_form"].notna()
    assert ((data.loc[both, "aim_form"] == "aim40") == (data.loc[both, "als_form"] == "als54")).all()
    assert (data.loc[data["als_form"] == "als54", "bis_form"].dropna() == "bis10").mean() > 0.999
    forms = result.flags[result.flags["variable"].isin(["als_form", "wurs_form", "aim_form", "bis_form"])]
    early = forms["detail"] == "dated before the form came into use"
    # A WURS or an AIM, and no ALS or BIS to tell its form.
    assert forms[~early].groupby("variable").size().to_dict() == {"aim_form": 4, "als_form": 1, "wurs_form": 49}
    # A reduced form on a visit dated before 2021, when only the long forms were in use: no form, nothing delivered.
    assert forms[early].groupby("variable").size().to_dict() == {"aim_form": 8, "als_form": 8, "bis_form": 8, "wurs_form": 8}
    reduced = data.loc[data["visit_date"] < "2021-01-01", ["als18_total", "wurs25_total", "aim20_score", "bis12_total"]]
    assert reduced.notna().sum().sum() == 0
    assert (qc.loc["bdhi_total", "n_valid"], qc.loc["aq12_total", "n_valid"]) == (4474, 1387)


def test_auto_questionnaires_scores_of_the_review_of_2026_11_20(result, qc):
    """Scores that the package computes where the application or the export gets them wrong (D183 to D197)."""
    data, flags = result.data, result.flags

    def count(variable, flag):
        return int(((flags["variable"] == variable) & (flags["flag"] == flag)).sum())

    # CTQ denial: the items 10, 16 and 22 answered 5, computed when the three are answered; the stored score is the check.
    # 66 visits gain a score, 42 lose it (one to three items empty: `score_not_recomputed`), D183.
    assert qc.loc["ctq_denial", "n_valid"] == 6194
    assert (qc.loc["ctq_denial", "score_mismatch"], qc.loc["ctq_denial", "score_not_recomputed"]) == (0, 42)
    # ASRS screen: 1 positive, 0 negative (was a category), from part A; the stored screen is the check (D187).
    assert qc.loc["asrs_screen", "n_valid"] == 1320
    assert data["asrs_screen"].value_counts().to_dict() == {1.0: 708, 0.0: 612}
    assert (qc.loc["asrs_screen", "score_not_recomputed"], qc.loc["asrs_screen", "score_mismatch"]) == (6, 2)
    # MDQ: the stored screen is negative on 17 visits where a missing answer is the only thing that could have made it so (R88).
    assert count("mdq_screen_check", "score_mismatch") == 17
    # PSQI: components 5 and 7 are computed, a blank 5j counts 0 (D184); the latency is no longer winsorised.
    assert (qc.loc["psqi_disturbances", "n_valid"], qc.loc["psqi_total", "n_valid"]) == (16687, 16437)
    assert (qc.loc["psqi_dysfunction", "n_valid"], qc.loc["psqi_dysfunction", "score_mismatch"]) == (16709, 0)
    assert (qc.loc["psqi_disturbances", "score_mismatch"], qc.loc["psqi_total", "score_mismatch"]) == (0, 725)
    assert qc.loc["psqi_latency", "winsorised"] == 0 and count("psqi_latency", "winsorised") == 0
    assert qc.loc["psqi_latency", "max"] == 240
    assert (qc.loc["psqi05k", "not_shown"], count("psqi05k", "not_shown")) == (2, 2)
    # PRISE-M: the total needs 31 items, 239 partial sums of 28 to 30 items are lost (D191).
    assert (qc.loc["prisem_total", "n_valid"], qc.loc["prisem_total", "score_not_recomputed"]) == (15899, 328)
    assert qc.loc["prisem_total", "score_mismatch"] == 0


def test_bdhi_items_are_delivered_as_asked(result):
    """The extraction stores the 75 statements keyed to hostility. Fifteen have "false" as the hostile answer: they are read back to
    1 true, 0 false (D190), and the sub-scores reverse them, so that no sub-score cell changes."""
    flipped = [1, 10, 17, 21, 27, 34, 39, 50, 55, 63, 66, 67, 71, 72, 74]
    names = ["bdhi%02d" % n for n in range(1, 76)]
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    typed = pd.concat([keys[["usubjid", "visit"]], raw[names].replace("", pd.NA).astype("Float64").astype(float)], axis=1)
    delivered = result.data
    both = typed.merge(delivered[["usubjid", "visit"] + names + ["bdhi_assault", "bdhi_indirect", "bdhi_irritability", "bdhi_negativism",
                                                                  "bdhi_resentment", "bdhi_suspicion", "bdhi_verbal", "bdhi_guilt"]],
                       on=["usubjid", "visit"], suffixes=("_typed", ""))
    assert len(both) == len(delivered) == len(typed)
    turned_cells = 0
    for number in range(1, 76):
        name = "bdhi%02d" % number
        filled = both[name + "_typed"].notna()
        assert (both[name].notna() == filled).all(), name           # the same cells are filled
        if number in flipped:
            assert (both.loc[filled, name] + both.loc[filled, name + "_typed"] == 1).all(), name
            turned_cells += int(filled.sum())
        else:
            assert (both.loc[filled, name] == both.loc[filled, name + "_typed"]).all(), name
    assert turned_cells == 67999
    # The mean of a turned item and of an item that is not (stored 0.249 and 0.176 on 4,541 and 4,543 cells).
    assert both["bdhi01"].mean() == pytest.approx(1 - both["bdhi01_typed"].mean())
    assert both["bdhi02"].mean() == pytest.approx(both["bdhi02_typed"].mean())
    # Every sub-score cell is the plain sum of the items as typed, as before the change (one 1 minus value cancels the other).
    schema = load_schemas(bp.SCHEMAS)["bdhi"]
    expected_cells = {"bdhi_assault": 4511, "bdhi_indirect": 4514, "bdhi_irritability": 4509, "bdhi_negativism": 4527,
                      "bdhi_resentment": 4511, "bdhi_suspicion": 4512, "bdhi_verbal": 4506, "bdhi_guilt": 4514}
    for score, cells in expected_cells.items():
        items = schema["scores"][score]["sum"]
        plain = both[[item + "_typed" for item in items]].sum(axis=1, min_count=len(items))
        assert (both[score].notna() == plain.notna()).all() and both[score].notna().sum() == cells, score
        assert (both[score].dropna() == plain.dropna()).all(), score


def test_neuropsychologie(result, qc):
    # Percentile bands: every time and fluency cell is read.
    assert (qc.loc["tmt_a_time_band", "n_valid"], qc.loc["tmt_a_time_band", "unparsed"]) == (5914, 0)
    assert (qc.loc["tmt_ba_time_band", "n_valid"], qc.loc["tmt_ba_time_band", "censored_left"]) == (5856, 0)         # the bands are read in the table: no open band at the low end
    # The TMT error bands are read in the norm tables, with the errors, the age and the years of education.
    assert (qc.loc["tmt_a_errors_band", "n_valid"], qc.loc["tmt_a_errors_band", "norm_missing"]) == (5860, 8)
    assert (qc.loc["tmt_a_errors_band", "censored_right"], qc.loc["tmt_b_errors_band", "censored_right"]) == (4875, 4726)   # rebuilt from the application's scripts (TMT review, D138-D143)
    band = result.data["tmt_a_errors_band"].dropna()
    years = result.data["visit_date"].dt.year[band.index]
    shares = [(band[(years >= low) & (years <= high)] >= 10).mean() for low, high in [(2009, 2015), (2016, 2021), (2022, 2026)]]
    assert max(shares) - min(shares) < 0.10              # one rule for every year (the stored cells moved by 0.75)
    assert (qc.loc["fluency_p_band", "n_valid"], qc.loc["fluency_p_band", "censored_right"]) == (5857, 0)
    # CVLT: the z-scores are computed again with the regressions of the norms, the same rule in every year.
    assert (qc.loc["cvlt_total_1_5_z", "n_valid"], qc.loc["cvlt_total_1_5_z", "out_of_range"]) == (5834, 0)     # 241 stored ones were above 5
    assert (qc.loc["cvlt_total_1_5_z", "score_mismatch"], qc.loc["cvlt_total_1_5_z", "norm_missing"]) == (380, 8)
    total_z = result.data["cvlt_total_1_5_z"]
    in_2013_2014 = result.data["visit_date"].dt.year.isin([2013, 2014])
    assert abs(total_z[in_2013_2014].mean() - total_z[~in_2013_2014].mean()) < 0.1    # the stored ones were 2 points apart
    assert (qc.loc["cvlt_trial1_z", "n_valid"], qc.loc["cvlt_trial1_z", "score_mismatch"]) == (5841, 45)
    assert (qc.loc["cvlt_trial5_z", "n_valid"], qc.loc["cvlt_short_free_z", "n_valid"]) == (72, 2930)       # where the norms have a regression
    assert (qc.loc["cvlt_recency_z", "n_valid"], qc.loc["cvlt_recency_z", "score_not_recomputed"]) == (5196, 45)   # 43 came from an empty recency
    # Recency: the norm of the patients of 40 and over is corrected, so the same raw recency gives the same level at every age.
    assert qc.loc["cvlt_recency_z", "score_mismatch"] == 1697
    age = result.data["age"]
    recency_z = result.data["cvlt_recency_z"]
    means = [recency_z[(age >= low) & (age < high)].mean() for low, high in [(0, 40), (40, 70), (70, 200)]]
    assert max(means) - min(means) < 0.4                     # as the application computes it: 0.05, -0.82 and -3.71
    assert (qc.loc["cvlt_semantic_z", "n_valid"], qc.loc["cvlt_semantic_z", "out_of_range"]) == (2578, 13)
    # An index of 8 or more is a typed count, not an index: out of range, with its z-score and band (D130).
    assert (qc.loc["cvlt_semantic", "out_of_range"], qc.loc["cvlt_semantic_band", "norm_missing"]) == (216, 15)
    assert not [name for name in result.data.columns if name.startswith("cvlt") and name.endswith("_stored")]
    # CVLT: one band for every age, read in the percentile table where the norms have one, the band of the z-score elsewhere.
    assert (qc.loc["cvlt_trial5_band", "n_valid"], qc.loc["cvlt_trial5_band", "band_from_z"]) == (5847, 72)
    assert (qc.loc["cvlt_short_free_band", "n_valid"], qc.loc["cvlt_short_free_band", "band_from_z"]) == (5841, 2930)
    # In the table a perfect recall is "this band or a higher one".
    assert (qc.loc["cvlt_trial5_band", "censored_right"], qc.loc["cvlt_trial5_band", "norm_missing"]) == (1608, 1)
    assert (result.data["cvlt_trial5_band"] == 99).sum() == 0            # the EMR wrote 99 for 1,598 perfect recalls
    # Serial clustering is read in the table of the application's script too (D129): its ties are open bands.
    assert (qc.loc["cvlt_serial_band", "n_valid"], qc.loc["cvlt_serial_band", "censored_right"], qc.loc["cvlt_serial_band", "norm_missing"]) == (4970, 625, 1)
    assert (qc.loc["cvlt_trial1_band", "n_valid"], qc.loc["cvlt_trial1_band", "band_from_z"]) == (5841, 5841)
    assert (qc.loc["cvlt_total_1_5_band", "n_valid"], qc.loc["cvlt_total_1_5_band", "band_from_z"]) == (5834, 5834)
    assert (qc.loc["cvlt_total_1_5", "n_valid"], qc.loc["cvlt_total_1_5", "score_mismatch"]) == (5842, 54)
    # Scores recomputed from the items.
    assert (qc.loc["stroop_interference", "n_valid"], qc.loc["stroop_interference", "score_mismatch"]) == (5796, 54)
    assert (qc.loc["spatial_total", "n_valid"], qc.loc["spatial_total", "score_mismatch"]) == (5234, 0)          # the total stops at the first failure: its 41 doubtful sums are gone (D135)
    assert (qc.loc["cobra_total", "n_valid"], qc.loc["cobra_total", "score_mismatch"]) == (596, 0)
    assert (qc.loc["errands_errors", "n_valid"], qc.loc["errands_errors", "score_mismatch"]) == (808, 9)
    # The typed z-scores of the errands test mix two sign conventions (D126): they are checks, the z-scores are computed again (D135).
    errands_z = ["errands_minutes_z", "errands_detours_z", "errands_late_trips_z", "errands_logic_errors_z", "errands_errors_z"]
    # The education basis is the years of education (12 or more), so no z-score lacks its norm any more: +958 z-scores (errands review, D138-D143).
    assert (qc.loc[errands_z, "n_valid"].sum(), qc.loc[errands_z, "period_removed"].sum()) == (3598, 0)
    # CPT-3: about 37 visits hold something else than a T-score.
    assert (qc.loc["cpt3_omissions_t", "n_valid"], qc.loc["cpt3_omissions_t", "out_of_range"]) == (488, 37)
    assert result.data["handedness"].value_counts().to_dict() == {"right": 5468, "left": 570, "both": 121}


def test_substances_and_comorbidity(result, qc):
    data = result.data
    tab = qc[qc["instrument"].isin(["tobacco", "anxiety_v0", "anxiety_fu", "substance_v0", "substance_fu",
                                    "eating_disorder_v0", "eating_disorder_fu", "somatoform_v0", "somatoform_fu"])]
    assert tab["unknown_code"].sum() == 0 and tab["version_unknown"].sum() == 0
    # The inclusion visit and the yearly visits do not answer the same question: two sets of columns.
    assert data["visit_form"].value_counts().to_dict() == {"follow_up": 11686, "inclusion": 6498}
    assert (qc.loc["anxiety_disorder_v0", "n_valid"], qc.loc["anxiety_disorder_fu", "n_valid"]) == (5173, 4560)
    assert (qc.loc["substance_disorder_v0", "n_valid"], qc.loc["substance_disorder_fu", "n_valid"]) == (5254, 4590)
    assert 0.47 < data["anxiety_disorder_v0"].mean() < 0.50 and 0.33 < data["anxiety_disorder_fu"].mean() < 0.36
    assert 0.36 < data["substance_disorder_v0"].mean() < 0.39 and 0.22 < data["substance_disorder_fu"].mean() < 0.25
    for name in ["anxiety_disorder", "substance_disorder", "eating_disorder", "somatoform_disorder"]:
        assert not (data[name + "_v0"].notna() & data[name + "_fu"].notna()).any(), name
    # The boxes of the anxiety disorders are exported only after a yes; after a no they are read as 0,
    # like those of the substances. Both are then shares among all the patients.
    assert (qc.loc["panic_disorder_v0", "n_valid"], qc.loc["alcohol_disorder_v0", "n_valid"]) == (4942, 5240)
    assert 0.12 < data["panic_disorder_v0"].mean() < 0.13 and 0.25 < data["alcohol_disorder_v0"].mean() < 0.26
    assert (data["anxiety_disorder_v0"].isna() & data["panic_disorder_v0"].notna()).sum() == 2    # boxes typed without the first answer
    assert qc.loc["panic_disorder_v0", "n_info"] == 0                  # no info flag: the score_not_recomputed flag is a danger flag
    # Panic disorder is a score (D151): the export's box also matches "agoraphobia without panic disorder", so it is
    # missing where the agoraphobia box is ticked and no panic detail is filled, with the stored 1 in the flag log.
    assert (qc.loc["panic_disorder_v0", "score_not_recomputed"], qc.loc["panic_disorder_fu", "score_not_recomputed"]) == (206, 156)
    assert (qc.loc["panic_disorder_fu", "n_valid"], qc.loc["alcohol_disorder_fu", "n_valid"]) == (4391, 4575)
    # The eight substance boxes hang on the first question (D154): 0 after a "no" on every visit that has one, and
    # missing after a "yes" that ticks no box (14 inclusion visits, 15 yearly visits).
    substances = ["alcohol", "sedative", "cannabis", "stimulant", "opiate", "cocaine", "hallucinogen", "other_substance"]
    for ending, after_no, yes_and_no_box in [("v0", 3288, 14), ("fu", 3513, 15)]:
        boxes = data[[name + "_disorder_" + ending for name in substances]]
        gate = data["substance_disorder_" + ending]
        assert (gate == 0).sum() == after_no and (boxes[gate == 0] == 0).all().all()
        assert ((gate == 1) & boxes.isna().all(axis=1)).sum() == yes_and_no_box
    # Panic disorder: the two detail columns of the form are read as one.
    assert (qc.loc["panic_onset_age_v0", "n_valid"], tab["column_conflict"].sum()) == (415, 5)
    # Tobacco: pack-years typed freely.
    assert (qc.loc["tobacco_status", "n_valid"], qc.loc["tobacco_status", "missing_code"]) == (16352, 85)
    pack = qc.loc["pack_years"]
    assert (pack["n_valid"], pack["missing_code"], pack["unparsed"], pack["out_of_range"]) == (6335, 101, 34, 29)
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
    assert (qc.loc["dsm4_lt_n_mde", "n_valid"], qc.loc["dsm4_lt_n_mde", "censored_right"]) == (3748, 236)
    assert (qc.loc["dsm5_lt_n_mde", "n_valid"], qc.loc["dsm5_lt_n_mde", "censored_right"]) == (923, 58)
    # Counts asked only after a yes: 0 where there was no episode in the past year, or since the last visit.
    assert (qc.loc["dsm4_ly_n_mde", "n_valid"], int((data["dsm4_ly_n_mde"] == 0).sum())) == (4036, 1387)
    assert (qc.loc["dsm4_fu_n_mde", "n_valid"], int((data["dsm4_fu_n_mde"] == 0).sum())) == (6924, 4617)
    # One visit holds a count typed after a "no": a cell that is not empty is kept as written.
    assert (data.loc[data["dsm4_ly_any_episode"] == 0, "dsm4_ly_n_mde"] > 0).sum() == 1
    # The current episode is asked at every visit; the psychotic disorder is split like the comorbidities.
    assert (qc.loc["dsm4_current_episode", "n_valid"], qc.loc["dsm5_current_episode", "n_valid"]) == (11758, 3456)
    assert (qc.loc["psychotic_disorder_v0", "n_valid"], qc.loc["psychotic_disorder_fu", "n_valid"]) == (5394, 9389)
    assert qc.loc["psychotic_onset_date_v0", "date_placeholder"] + qc.loc["psychotic_onset_date_fu", "date_placeholder"] == 741
    # DSM-5 form: the column is the age at the first depressive episode; the first episode is the earliest of three ages (D89).
    assert (qc.loc["dsm5_first_mde_age", "n_valid"], qc.loc["dsm5_first_episode_age", "n_valid"]) == (715, 867)   # "<5" is read as 5 (D122)
    first = data[["dsm5_first_mde_age", "dsm5_first_hypomania_age", "dsm5_first_mania_age"]].min(axis=1)
    assert (data["dsm5_first_episode_age"].dropna() == first.dropna()).all()
    # Three columns of the DSM-5 form only.
    assert [qc.loc[name, "n_valid"] for name in ["dsm5_first_hypomania_age", "dsm5_first_mania_age", "dsm5_first_mood_stabiliser_age"]] == [530, 283, 935]
    # DIVA: the number of criteria is recomputed where the nine are answered.
    totals = ["diva_adult_a_total", "diva_child_a_total", "diva_adult_hi_total", "diva_child_hi_total"]
    assert [qc.loc[name, "n_valid"] for name in totals] == [45, 41, 41, 42] and qc.loc[totals, "score_mismatch"].sum() == 7
    # Counts of episodes are mostly 0 and are not winsorised: the rare episodes keep their number.
    assert tab["winsorised"].sum() == 0
    assert (data["dsm4_fu_n_mixed_psychotic"].max(), int((data["dsm4_fu_n_mixed_psychotic"] > 0).sum())) == (4, 44)   # 44 since the override (D180)
    # A question that the form hides, or that is implied, after a count of 0 of its kind is 0 (D122).
    assert [qc.loc[name, "n_valid"] for name in ["dsm5_ly_mania_psychotic", "dsm5_lt_mania_psychotic", "dsm4_ly_mde_psychotic", "dsm4_fu_n_mde_psychotic"]] == [1007, 971, 4050, 6672]
    # The export loses the DSM-5 count of manic episodes with psychotic features (R68): not delivered.
    assert "dsm5_lt_n_mania_psychotic" not in data.columns
    # The follow-up total is the sum of its counts; the stored one is a check. No DSM-5 visit holds a stored total any more:
    # the total exists on the old form only and the 35 DSM-5 visits that held one are read as DSM-IV (D180).
    assert (qc.loc["dsm5_fu_n_episodes", "n_valid"], qc.loc["dsm5_fu_n_episodes", "score_mismatch"]) == (2143, 0)
    # The old form's total is the sum of its four counts; the typed total is the check, and is delivered (score_as_stored)
    # where a count is unknown or empty: the sum is a hidden score that is the only item of the delivered one (D177).
    assert [qc.loc["dsm4_fu_n_episodes", name] for name in ["n_valid", "score_mismatch", "score_as_stored"]] == [6905, 204, 349]
    assert "dsm4_fu_n_episodes_sum" not in data.columns and "dsm4_fu_n_episodes_stored" not in data.columns
    # Lifetime counts stop at 20 like the form (D176); the three psychotic yes/no are 0 after a count of 0 (D178).
    counts = [name for name in qc.index if name.startswith(("dsm4_lt_n_", "dsm5_lt_n_"))]
    assert qc.loc[counts, "max"].max() == 20 and qc.loc[counts, "out_of_range"].sum() == 0
    assert [qc.loc[name, "n_valid"] for name in ["dsm4_lt_mde_psychotic", "dsm4_lt_mania_psychotic", "dsm4_lt_mixed_psychotic"]] == [4169, 4244, 4110]
    # The details of the most recent episode follow the display rule of the form; its start must precede the visit (D179).
    assert [qc.loc[name, "not_shown"] for name in ["dsm4_recent_specifier", "dsm4_recent_chronic", "dsm4_recent_severity", "dsm4_recent_postpartum"]] == [7, 13, 6, 2]
    assert (qc.loc["dsm4_recent_start_date", "out_of_range"], qc.loc["dsm4_recent_start_date", "n_valid"]) == (100, 3723)


def test_care_and_sick_leave(result, qc):
    data = result.data
    tab = qc[qc["tab"] == "SOIN SUIVI HOSP ARRET TRAVAIL"]
    assert tab["instrument"].nunique() == 6 and tab["unknown_code"].sum() == 0 and tab["winsorised"].sum() == 0
    # Hospitalisations: over the life at inclusion, since the last visit at follow-up, in separate columns.
    assert (qc.loc["n_hospitalisations_v0", "n_valid"], qc.loc["n_hospitalisations_fu", "n_valid"]) == (5065, 8415)
    assert round(data["n_hospitalisations_v0"].mean(), 1) == 2.5 and round(data["n_hospitalisations_fu"].mean(), 2) == 0.17
    assert not (data["n_hospitalisations_v0"].notna() & data["n_hospitalisations_fu"].notna()).any()
    # The lists of the forms stop at 20 hospitalisations: the range is 0 to 20 and no count is out of range (D161).
    counts = ["n_hospitalisations_v0", "n_hospitalisations_12m", "n_hospitalisations_fu"]
    assert qc.loc[counts, "out_of_range"].sum() == 0 and data[counts].max().max() == 20
    # "<5" as the age at the first hospitalisation is mostly chosen by patients never hospitalised: missing (D123).
    assert (qc.loc["n_hospitalisations_v0", "censored_right"], qc.loc["first_hospitalisation_age", "censored_left"]) == (25, 0)
    # A total is 0 where its count is 0; the 12-month count is 0 after no mood episode in the year (D123).
    assert [qc.loc[name, "n_valid"] for name in ["hospitalisation_months_v0", "n_hospitalisations_12m", "hospitalisation_weeks_12m", "hospitalisation_months_fu"]] == [4516, 5122, 5007, 8350]
    assert data["hospitalisation_months_fu"].isin([0.25, 0.5, 0.75]).sum() == 379            # a quarter, half, three quarters of a month
    # Sick leave: "Non applicable" is a missing code; number and duration are 0 after a "no".
    # The yes/no is the stored one, but yes on 8 DSM-IV inclusions where a script read ">20" sick leaves as "no" (D123).
    assert (qc.loc["sick_leave_12m", "n_valid"], qc.loc["sick_leave_12m", "score_mismatch"]) == (4057, 8)
    # A number above 20 cannot come from the forms (the social form's weeks, R74); a follow-up length above two years is out of range.
    assert (qc.loc["n_sick_leaves_12m", "out_of_range"], qc.loc["sick_leave_weeks_fu", "out_of_range"]) == (40, 22)
    assert (qc.loc["sick_leave_fu", "n_valid"], qc.loc["sick_leave_fu", "missing_code"]) == (6323, 3091)
    assert (data.loc[data["sick_leave_fu"] == 0, "sick_leave_weeks_fu"] == 0).all()
    weeks = qc.loc["sick_leave_weeks_12m"]
    assert (weeks["n_valid"], weeks["unparsed"], weeks["out_of_range"]) == (3661, 91, 44)
    # Use of care: boxes and numbers are 0 where the part was answered "no".
    assert (qc.loc["care_usual", "n_valid"], qc.loc["care_urgent", "n_valid"]) == (9510, 9347)
    # Two visits have the box ticked after a "no" to the part: a cell that is not empty is kept as written.
    assert (data.loc[data["care_urgent"] == 0, "n_urgent_psychiatrist"] != 0).sum() == 3
    assert (data.loc[data["care_urgent"] == 0, "urgent_psychiatrist"] == 1).sum() == 2
    assert (data["n_urgent_psychologist"].max(), int((data["n_urgent_psychologist"] > 0).sum())) == (24, 38)
    assert data["drug_advice_followed"].value_counts().to_dict() == {"fully": 5913, "partly": 2379, "not_followed": 1207}


def test_treatments(result, qc):
    items, data = result.treatments, result.data
    # One row per patient and medication: the lists of a patient are the same on every row.
    assert (len(items), items["usubjid"].nunique(), items["molecule"].nunique()) == (22758, 4779, 125)
    assert qc.loc["medication", "patient_value_varies"] == 0
    # 99% of the names are found in the table; the others keep what was written and are flagged.
    assert (qc.loc["molecule", "n_valid"], qc.loc["molecule", "unknown_code"]) == (22585, 173)
    groups = items["treatment_group"].value_counts()
    assert (groups["lithium"], groups["anticonvulsant"], groups["antidepressant"], len(groups)) == (2992, 5120, 4807, 10)
    assert (qc.loc["start_date", "n_valid"], qc.loc["end_date", "n_valid"], qc.loc["end_date", "missing_code"]) == (22608, 10890, 11868)
    # A start of 0000-00-00 is "Aucune date indiquée" (128 running treatments) and joins the 20 placeholders of 1950-01-01 (D167).
    assert (qc.loc["start_date", "missing_code"], qc.loc["start_date", "out_of_range"]) == (148, 2)
    # "Traitement en cours" is written 0000-00-15 or 0000-00-00: running. An end before the start is flagged (D124).
    assert (result.flags.loc[result.flags["variable"] == "end_date", "detail"] == "running").sum() == 11855
    assert qc.loc["end_date", "check_failed"] == 148
    # The daily dose in mg: the stored strength, else the one in the name (DM-14, D124).
    assert (qc.loc["units_per_day", "missing_code"], qc.loc["daily_dose", "n_valid"]) == (893, 19349)
    assert ((items["strength_from_name"] == 1).sum(), qc.loc["daily_dose", "score_mismatch"], qc.loc["daily_dose", "out_of_range"]) == (12948, 2, 3)
    from_2018 = items["start_date"].dt.year >= 2018
    assert (items.loc[from_2018, "daily_dose"].notna().sum(), from_2018.sum()) == (7664, 8654)
    # On the day of the visit: computed for the patients who have a list.
    assert qc.loc["on_lithium", "instrument"] == "medications_at_visit"
    assert (data["on_lithium"].notna().sum(), round(data["on_lithium"].mean(), 2)) == (18127, 0.36)
    assert (data["on_valproate"] == 1).sum() == 3625                  # valproate or valpromide (D124)
    first = data[data["visit"] == "V0"]
    assert round(first["on_lithium"].mean(), 2) == 0.30 and round(first["on_anticonvulsant"].mean(), 2) == 0.44
    assert data.loc[~data["usubjid"].isin(items["usubjid"]), "on_lithium"].isna().all()


def test_treatment_forms(result, qc):
    data, patients = result.data, result.patients
    forms = qc[qc["instrument"].isin(["drug_classes_lifetime", "non_drug_lifetime", "non_drug_fu"])]
    assert forms["unknown_code"].sum() == 0 and forms["winsorised"].sum() == 0 and forms["patient_value_varies"].sum() == 0
    # The two lifetime forms are repeated on every row of the patient: one value per patient.
    assert "ever_lithium" in patients.columns and "ever_lithium" not in data.columns
    assert (qc.loc["ever_lithium", "n_valid"], round(patients["ever_lithium"].mean(), 2)) == (2530, 0.47)
    # Months of exposure: a list that stops at 240, and 0 where the patient never took the class.
    assert (qc.loc["lithium_months", "n_valid"], qc.loc["lithium_months", "censored_right"], patients["lithium_months"].max()) == (2185, 35, 240)
    assert (patients.loc[patients["ever_lithium"] == 0, "lithium_months"] == 0).all()
    # The same in the six classes: a total of exposure is 0 after a "no" (D122, D166): 5,143 patient-class cells; one anticonvulsant patient keeps months typed after a "no".
    classes = ["antidepressant", "antipsychotic_1g", "antipsychotic_2g", "anxiolytic_hypnotic", "lithium", "anticonvulsant"]
    assert sum(int(((patients["ever_" + name] == 0) & (patients[name + "_months"] == 0)).sum()) for name in classes) == 5143
    assert sum(int(((patients["ever_" + name] == 0) & (patients[name + "_months"] > 0)).sum()) for name in classes) == 1
    assert (qc.loc["ever_non_drug_treatment", "n_valid"], round(patients["ever_cbt"].mean(), 2)) == (1250, 0.16)
    # The follow-up form: boxes are 0 after a "no" to the first question.
    assert (qc.loc["non_drug_treatment_fu", "n_valid"], round(data["non_drug_treatment_fu"].mean(), 2)) == (9304, 0.34)
    assert (data.loc[data["non_drug_treatment_fu"] == 0, "cbt_fu"] == 0).all()
    # After a yes, an empty box beside a ticked one is a no (box_list, D124).
    assert (qc.loc["ect_fu", "n_valid"], qc.loc["cbt_fu", "n_valid"], qc.loc["ever_ect", "n_valid"]) == (9253, 9218, 1244)
    assert (qc.loc["ipsrt_individual_fu", "n_valid"], qc.loc["ipsrt_individual", "n_valid"]) == (9242, 1238)
    # 1000-01-01 is written in every date that was not typed.
    assert forms.loc[forms["instrument"] != "drug_classes_lifetime", "date_placeholder"].sum() == 5713


def test_social(result, qc):
    data = result.data
    tab = qc[qc["tab"] == "SOCIAL"]
    assert tab["unknown_code"].sum() == 0 and tab["unparsed"].sum() == 0
    assert data["marital_status"].value_counts().to_dict() == {"couple": 2413, "single": 1984, "divorced": 384, "separated": 181, "widowed": 29}
    # Education is a list of levels: two of them are exported as words, the others as codes.
    levels = data["education_level"].value_counts()
    assert (levels["bac"], levels["bac_plus_5"], levels["primary_certificate"], len(levels)) == (714, 1202, 21, 17)
    # Code 7 of the source of income is "other" on the form; the export writes the students with "other" (D94).
    assert data["income_source"].value_counts()["other"] == 1071
    assert "student" not in set(data["work_status"].dropna()) and (data["work_status"] == "employed").sum() == 2308
    assert (data["work_status"] == "student_or_other").sum() == 1150
    # An end date after the visit is out_of_range (before_visit, D198): 16 cells.
    assert (qc.loc["last_job_end_date", "n_valid"], qc.loc["last_job_end_date", "date_placeholder"]) == (814, 176)
    assert (qc.loc["total_work_years", "out_of_range"], qc.loc["longest_job_years", "out_of_range"], qc.loc["household_size", "out_of_range"]) == (4, 1, 5)
    # The work durations are not winsorised: the long careers of the older patients are kept (D116).
    assert tab["winsorised"].sum() == 0 and (data["total_work_years"] > 42).sum() == 39
    assert (qc.loc["debt_level", "n_valid"], qc.loc["debt_level", "missing_code"]) == (4481, 153)
    assert qc.loc["job_class_fu", "n_valid"] == 219
    # The legal protection measure and the non-opposition form are administrative: they are not delivered.
    assert "protection_measure" not in result.patients.columns and "opposition_form" not in result.patients.columns


def test_perinatal(result, qc):
    patients = result.patients
    # One value per patient: the columns are in the patients table, not in the visit table.
    assert "birth_weight" in patients.columns and "birth_weight" not in result.data.columns
    assert patients["birth_term"].value_counts().to_dict() == {"term": 4119, "preterm": 478, "post_term": 161}
    assert patients["birth_type"].value_counts().to_dict() == {"vaginal": 4098, "caesarean": 446}
    # A 0 is a missing code in the measures; months typed as a gestational age are converted to weeks.
    weight, weeks = qc.loc["birth_weight"], qc.loc["gestational_age"]
    assert (weight["n_valid"], weight["missing_code"], weight["out_of_range"]) == (2436, 34, 17)
    assert (weeks["n_valid"], weeks["unit_inferred"], weeks["out_of_range"]) == (1201, 14, 22)
    assert (qc.loc["apgar_1min", "n_valid"], qc.loc["apgar_1min", "missing_code"], qc.loc["apgar_1min", "out_of_range"]) == (912, 53, 2)
    assert patients["gestational_age"].between(20, 45).sum() == 1201
    # The form filled again at a yearly visit: the first answer is kept, the patient is flagged.
    assert (qc.loc["mother_age_at_birth", "n_valid"], qc.loc["mother_age_at_birth", "patient_value_varies"]) == (4552, 56)
    tab = qc[qc["instrument"] == "perinatal"]
    assert tab["unknown_code"].sum() == 0 and tab["unparsed"].sum() == 0
    # The birth measures are not winsorised: a very low birth weight is kept as it is.
    assert tab["winsorised"].sum() == 0
    assert (patients["birth_weight"].min(), patients["gestational_age"].min()) == (500, 25)


def test_suicide(result, qc):
    data = result.data
    # The same five columns hold lifetime answers at inclusion and answers since the last visit at follow-up.
    assert (qc.loc["isf05_lifetime", "n_valid"], qc.loc["isf05_since_visit", "n_valid"]) == (5919, 8221)
    assert round(data["isf05_lifetime"].mean(), 2) == 0.38 and round(data["isf05_since_visit"].mean(), 3) == 0.024
    assert data["isf05_lifetime"].notna().sum() + data["isf05_since_visit"].notna().sum() == (data["isf05_lifetime"].notna() | data["isf05_since_visit"].notna()).sum()
    assert qc.loc[qc["instrument"].isin(["isf_lifetime", "isf_since_visit"]), "unknown_code"].sum() == 0
    # Follow-up visits of November 2021 to 2023: the form also asked about the whole life. No answer is delivered (D88, D125).
    removed = qc.loc[qc["instrument"] == "isf_since_visit", "period_removed"]
    assert (qc.loc["isf05_since_visit", "period_removed"], qc.loc["isf05_since_visit_when", "period_removed"]) == (993, 95)
    assert (qc.loc["isf01_since_visit", "period_removed"], removed.sum()) == (1001, 6360)
    assert qc.loc[qc["instrument"] == "isf_lifetime", "period_removed"].sum() == 0
    in_the_period = data["visit_date"].between("2021-11-01", "2023-12-31")
    assert data.loc[in_the_period, ["isf01_since_visit", "isf05_since_visit", "n_attempts_since_visit"]].notna().sum().sum() == 0
    flagged = result.flags[result.flags["flag"] == "period_removed"]
    assert set(flagged["severity"]) == {"danger"}
    assert (flagged["raw"].astype(str) != "").all() and (flagged["value"].astype(str) == "").all()   # the log keeps what was written
    # The history of attempts: the whole life at inclusion, since the last visit at follow-up (D86).
    # A first attempt dated on the inclusion day or later is impossible (before_visit, D125).
    assert (qc.loc["first_attempt_date", "n_valid"], qc.loc["first_attempt_date", "date_placeholder"]) == (1790, 162)
    assert qc.loc["first_attempt_date", "out_of_range"] == 307
    # The counts are 0 after a "no" (asked_if): never attempted, no attempt since the last visit (D125).
    assert (qc.loc["n_attempts", "n_valid"], qc.loc["n_attempts", "out_of_range"]) == (5785, 1)
    assert (qc.loc["n_attempts_since_visit", "n_valid"], (data["n_attempts_since_visit"] > 0).sum()) == (8194, 162)
    assert not (data["n_attempts"].notna() & data["n_attempts_since_visit"].notna()).any()
    attempts_removed = qc.loc[qc["instrument"] == "suicide_attempts_since_visit", "period_removed"]
    assert (qc.loc["n_attempts_since_visit", "period_removed"], attempts_removed.sum()) == (126, 376)
    # A date of the first attempt typed at a follow-up visit is read and not delivered; 2011-11-11 is its placeholder.
    typed_at_follow_up = result.flags[result.flags["variable"] == "first_attempt_date_follow_up"]
    assert "first_attempt_date_follow_up" not in data.columns
    assert (typed_at_follow_up["flag"] == "missing_code").sum() == 1142
    # Columbia and C-SSRS: every answer of the drop-downs has a code; one schema per form (D125).
    tab = qc[qc["tab"] == "SUICIDE"]
    assert tab["unknown_code"].sum() == 0
    assert (qc.loc["violent_method", "n_valid"], qc.loc["serious_method", "n_valid"]) == (319, 432)
    assert (qc.loc["violent_method_since_visit", "n_valid"], qc.loc["serious_method_since_visit", "n_valid"]) == (16, 24)
    # The forms of 2009-2010 saved the first option of the lists they hid: not answers (shown_if).
    assert tab["not_shown"].sum() == 241
    # The inclusion answers are about the past week and are named so (D158); no name of the tab ends in _inclusion any more.
    past_week = ["cssrs0%d" % number for number in range(1, 6)] + ["cssrs_most_severe", "cssrs_frequency", "cssrs_duration", "cssrs_control", "cssrs_deterrents", "cssrs_reasons", "cssrs_intensity"]
    assert all(name + "_past_week" in qc.index for name in past_week) and not any(name.startswith("cssrs") and name.endswith("_inclusion") for name in qc.index)
    assert (qc.loc["cssrs01_past_week", "n_valid"], qc.loc["cssrs01_since_visit", "n_valid"]) == (1251, 2355)
    assert (qc.loc["cssrs_most_severe_past_week", "n_valid"], qc.loc["cssrs_most_severe_since_visit", "n_valid"]) == (250, 428)
    assert (qc.loc["cssrs_intensity_past_week", "n_valid"], qc.loc["cssrs_intensity_since_visit", "n_valid"]) == (434, 588)


def test_family_history(result, qc):
    relatives, patients = result.relatives, result.patients
    # One row per patient and relative about whom something is known.
    assert (len(relatives), relatives["usubjid"].nunique(), relatives.shape[1]) == (29849, 5555, 21)
    kinship = relatives["kinship"].value_counts()
    assert (kinship["mother"], kinship["father"], kinship["sister"], len(kinship)) == (5250, 5124, 1721, 10)
    assert not relatives.duplicated(["usubjid", "relative"]).any()
    disorder = relatives["relative_disorder"].value_counts()
    assert (disorder["unipolar"], disorder["bipolar"], disorder["schizophrenia"], disorder["none"]) == (4683, 1873, 243, 5329)
    assert (qc.loc["relative_disorder", "missing_code"], qc.loc["relative_disorder", "unknown_code"]) == (2473, 0)
    # Boxes ticked in one cell: one yes/no variable per box, and one for any substance.
    boxes = relatives[["relative_substance", "relative_alcohol", "relative_cannabis", "relative_other_substance"]]
    assert list(boxes.sum()) == [3495, 2861, 596, 516] and qc.loc["relative_alcohol", "unknown_code"] == 0
    known = boxes[boxes.notna().all(axis=1)]
    assert len(known) == 12753 and (known["relative_substance"] == known.drop(columns="relative_substance").max(axis=1)).all()
    # The death of the mother is exported since the second extraction of 13 November 2026.
    died = relatives.groupby("kinship")["relative_deceased"].agg(["count", "sum"])
    assert (died.loc["mother", "count"], died.loc["mother", "sum"]) == (4303, 727)
    assert (died.loc["father", "count"], died.loc["father", "sum"]) == (4161, 1199)
    # Most dates were never typed: a placeholder is a missing code.
    assert (qc.loc["relative_birth_date", "date_placeholder"], qc.loc["relative_birth_date", "n_valid"]) == (11781, 16434)
    # The type of diabetes is shown after the diabetes box only: 3 types under another box are not shown (decision D146).
    assert (qc.loc["relative_diabetes_type", "n_valid"], qc.loc["relative_diabetes_type", "not_shown"]) == (808, 3)
    # Counts: with no sister, no sister has anything.
    assert (qc.loc["n_sisters", "n_valid"], qc.loc["n_sisters_affected", "n_valid"]) == (5379, 5145)
    assert ((patients["n_sisters"] == 0).sum(), (patients.loc[patients["n_sisters"] == 0, "n_sisters_affected"] == 0).sum()) == (2092, 2091)
    assert (qc.loc["mother_affected", "missing_code"], round(patients["mother_affected"].mean(), 2)) == (199, 0.60)
    # The relatives summed up per patient: yes, no, or not known.
    assert qc.loc["fdr_bipolar", "instrument"] == "family_history_per_patient"
    assert patients["fdr_bipolar"].value_counts().to_dict() == {0.0: 2399, 1.0: 1213}
    assert patients["gp_bipolar"].value_counts().to_dict() == {0.0: 2039, 1.0: 452}
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
    assert (qc.loc["migraine_v0", "n_valid"], data["migraine_v0"].sum(), data.loc[~first, "migraine_v0"].notna().sum()) == (4775, 1076, 0)
    assert (qc.loc["migraine_fu", "n_valid"], data["migraine_fu"].sum(), data.loc[first, "migraine_fu"].notna().sum()) == (1815, 250, 0)
    assert (data["hypertension_v0"].sum(), data["diabetes_v0"].sum()) == (449, 164)
    # Every list of boxes is read whole, and almost nothing is lost: one count and two dates.
    flags = medical[["unknown_code", "unparsed", "out_of_range", "winsorised"]].sum()
    assert list(flags) == [0, 1, 2, 0] and medical["date_placeholder"].sum() == 23831
    # Boxes shown only after a yes are 0 after a no, and stay missing after "unknown".
    no_allergy = data["allergic_inflammatory_v0"] == 0
    assert (no_allergy.sum(), (data.loc[no_allergy, "asthma_v0"] == 0).sum(), data["asthma_v0"].sum()) == (4211, 4211, 462)
    assert data.loc[data["allergic_inflammatory_v0"].isna(), "asthma_v0"].isna().all()
    # The kinds of cancer and the causes of a drug eruption are boxes shown after a yes too: a "no" answers them.
    assert (qc.loc["cancer_v0", "n_valid"], qc.loc["cancer_gynaecological_v0", "n_valid"], (data["cancer_gynaecological_v0"] == 1).sum()) == (4687, 4686, 96)
    assert (qc.loc["drug_eruption_antibiotic_v0", "n_valid"], (data["drug_eruption_antibiotic_v0"] == 1).sum()) == (4667, 127)
    assert (data.loc[data["eye_disease_v0"] == 0, "closed_angle_glaucoma_v0"] == 0).all() and data["closed_angle_glaucoma_v0"].sum() == 7
    # Numbers of pregnancies: "Aucune" is 0, and with no pregnancy the other numbers are 0 unless typed otherwise.
    assert (qc.loc["n_pregnancies_v0", "n_valid"], data["n_pregnancies_v0"].sum(), data["n_pregnancies_v0"].max()) == (3621, 5229, 11)
    none = data["n_pregnancies_v0"] == 0
    assert (none.sum(), (data.loc[none, "n_live_births_v0"] == 0).sum()) == (1518, 1511)
    # The retention boxes hang on the retention: 0 after a "no", missing when a "yes" has no box ticked (decision D145).
    for form, no, yes_without_box in [("v0", 4396, 31), ("fu", 1725, 8)]:
        retention = data[f"urinary_retention_{form}"]
        boxes = data[[f"urinary_retention_{kind}_{form}" for kind in ("neuroleptic", "antidepressant", "other_treatment")]]
        assert ((retention == 0).sum(), (boxes[retention == 0] == 0).all(axis=1).sum(), boxes[retention == 1].isna().all(axis=1).sum()) == (no, no, yes_without_box)
    # The hormone therapy of the menopause is asked after a menopause "yes" only, and is missing otherwise (decision D145).
    for form, answered in [("v0", 570), ("fu", 190)]:
        therapy = data[f"menopause_hormone_therapy_{form}"]
        assert (qc.loc[f"menopause_hormone_therapy_{form}", "n_valid"], therapy[data[f"menopause_{form}"] == 0].notna().sum()) == (answered, 0)
    assert (qc.loc["nephropathy_lithium_v0", "n_valid"], qc.loc["nephropathy_lithium_fu", "n_valid"]) == (104, 55)
