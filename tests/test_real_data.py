"""The real FACE BP extraction, when it is on this computer. Aggregates only.

The numbers are the ones listed in docs/bp/PROGRESS.md ("What the first
schemas must produce"). No patient row appears here.
"""

from pathlib import Path

import pytest

from facedata import bp
from facedata.read import prepare_visits, read_extraction
from facedata.schema import load_schemas
from test_pipeline import assert_invariant

EXTRACTION = Path(__file__).parent.parent / "data" / "bp" / "BPALL_20261030.tsv"
pytestmark = pytest.mark.skipif(not EXTRACTION.exists(), reason="the BP extraction is not on this computer")


@pytest.fixture(scope="module")
def result():
    return bp.load(EXTRACTION)


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
    flags = result.flags[result.flags["variable"] == "dsm_version"]["flag"].value_counts().to_dict()
    assert flags == {"version_inferred": 316, "version_unknown": 22}


def test_scores_agree_with_the_stored_ones(result, qc):
    assert qc.loc["madrs_total", "n_valid"] == 17243
    assert (qc.loc["bis10_total", "n_valid"], qc.loc["bis10_total", "min"], qc.loc["bis10_total", "max"]) == (4636, 36, 113)
    assert qc.loc["bis10_sum12", "n_valid"] == 4661
    assert (qc.loc["bis12_total", "n_valid"], qc.loc["bis12_total", "min"], qc.loc["bis12_total", "max"]) == (1428, 13, 48)
    mismatches = result.flags[result.flags["flag"] == "score_mismatch"]["variable"].value_counts().to_dict()
    assert mismatches == {"wais4_ds_total_check": 13, "wais3_vocab_total": 3, "wais4_vocab_total": 3,
                          "wais4_mat_total": 1}


def test_biology(qc):
    crp, glucose, haemoglobin = qc.loc["crp"], qc.loc["glucose"], qc.loc["haemoglobin"]
    assert (crp["n_filled"], crp["censored_left"], crp["censored_right"], crp["unparsed"]) == (13026, 2353, 5, 0)
    assert (glucose["n_filled"], glucose["unit_converted"], glucose["unit_inferred"]) == (12930, 354, 124)
    assert (glucose["unit_doubt"], glucose["out_of_range"], glucose["censored_left"]) == (23, 6, 2)
    assert (haemoglobin["n_filled"], haemoglobin["unit_inferred"], haemoglobin["out_of_range"]) == (13435, 485, 12)


def test_derived_values_and_sign(result, qc):
    assert qc.loc["wais3_vocab_scaled", "derived_doubt"] == 1210
    assert qc.loc["wais4_ds_scaled", "derived_doubt"] == 13
    flipped = qc.loc[qc["sign_flipped"] > 0, "sign_flipped"].to_dict()
    assert flipped == {"tmt_a_time_z": 778, "tmt_a_errors_z": 771, "tmt_b_time_z": 769,
                       "tmt_b_errors_z": 759, "tmt_ba_time_z": 770}
    assert qc.loc["tmt_a_time_z", "sign_doubt"] == 193


def test_nothing_disappears_silently():
    raw, keys, visit_flags = prepare_visits(read_extraction(EXTRACTION))
    for schema in load_schemas(bp.SCHEMAS).values():
        assert_invariant(raw, keys, schema)
