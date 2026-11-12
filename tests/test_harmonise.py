"""Steps 4 and 7 to 12: versions, units, sign, range, scores, patient level, winsorising."""

import numpy as np
import pandas as pd
import pytest

from facedata.harmonise import (censoring_from_units, check_range, collapse_patient_level,
                                compute_scores, convert_units, detect_version, fix_sign, winsorise)
from helpers import flagged, make_keys, texts

GLUCOSE = {
    "unit": "mmol/L",
    "range": [1.5, 40.0],
    "units": {"mmol/L": {"factor": 1.0, "expect": [2.5, 40.0]},
              "g/L": {"factor": 5.551, "expect": [0.3, 2.5]}},
}


def test_convert_units_follows_the_decision_table():
    values = pd.Series([5.0, 1.0, 0.9, 2.0, 1.1, 5.2, 100.0])
    labels = texts(["mmol/L", "g/L", "mmol/l", "mmol/L", "erreur", "", "g/L"])
    converted, flags = convert_units(values, labels, "glucose", GLUCOSE)
    expected = [5.0, 5.551, 0.9 * 5.551, 2.0 * 5.551, 1.1 * 5.551, 5.2, 555.1]
    assert list(converted) == pytest.approx(expected)
    assert flagged(flags, "unit_converted") == [1]     # label g/L, value fits g/L
    assert flagged(flags, "unit_inferred") == [2, 4, 5]  # impossible under its label, or no usable label
    assert flagged(flags, "unit_doubt") == [3]         # possible in mmol/L, but fits g/L better
    # row 6 fits no unit: converted from its label without a flag, the range step decides


def test_convert_units_gives_up_when_several_units_fit():
    variable = {"unit": "a", "units": {"a": {"factor": 1.0, "expect": [0.0, 10.0]},
                                       "b": {"factor": 2.0, "expect": [5.0, 50.0]}}}
    converted, flags = convert_units(pd.Series([7.0]), texts([""]), "x", variable)
    assert converted.isna().all()
    assert flagged(flags, "unit_unknown") == [0]


def test_censoring_mark_in_the_unit_column():
    cens = pd.Series([0, 0, -1])
    labels = texts(["inf", "mg/L", "inf"])
    cens, flags = censoring_from_units(cens, labels, "crp", {"censor_units": {"inf": "left"}})
    assert list(cens) == [-1, 0, -1]
    assert flagged(flags, "censored_left") == [0]


def test_check_range_removes_and_never_clips():
    values, flags = check_range(pd.Series([0.0, 6.0, 7.0, np.nan]), "x", {"range": [0.0, 6.0]})
    assert list(values[:2]) == [0.0, 6.0] and values[2:].isna().all()
    assert flagged(flags, "out_of_range") == [2]


def test_compute_scores_reverses_compares_and_doubts_derived_values():
    item = {"range": [1.0, 4.0]}
    schema = {
        "variables": {"a": item, "b": item, "c": item, "stored": {}, "scaled": {"derived_from": "total"}},
        "scores": {"total": {"sum": ["a", "b", "c"], "reverse": ["c"], "compare": "stored", "compare_offset": 0.0}},
    }
    values = pd.DataFrame({"a": [1, 2, 3, np.nan], "b": [1, 2, 3, 4], "c": [4, 4, 1, 1],
                           "stored": [3, 9, 10, 5], "scaled": [10, 11, 12, 13]})
    values, flags = compute_scores(values, schema)
    assert list(values["total"][:3]) == [3, 5, 10]       # c is reversed: 1 + 4 - c
    assert pd.isna(values["total"][3])                   # an item is missing
    assert flagged(flags, "score_mismatch") == [1]
    assert flagged(flags, "derived_doubt") == [1]


def test_a_documented_offset_is_not_a_mismatch_but_still_doubts_derived_values():
    schema = {
        "variables": {"a": {}, "b": {}, "stored": {}, "scaled": {"derived_from": "total"}},
        "scores": {"total": {"mean": ["a", "b"], "min_items": 1.0, "compare": "stored", "compare_offset": -3.0}},
    }
    values = pd.DataFrame({"a": [10.0, 20.0], "b": [20.0, np.nan], "stored": [12.0, 99.0], "scaled": [7, 8]})
    values, flags = compute_scores(values, schema)
    assert list(values["total"]) == [15.0, 20.0]
    assert flagged(flags, "score_mismatch") == [1]       # 12 = 15 - 3 is explained, 99 is not
    assert flagged(flags, "derived_doubt") == [0, 1]     # the stored score is wrong on both rows


def test_winsorise_clips_at_percentiles_and_reports_the_limits():
    values = pd.Series(list(range(1, 100)) + [5000.0])
    clipped, flags, limits = winsorise(values, "x", {})
    assert limits == (2.0, 99.0)
    assert clipped.max() == 99.0 and clipped.min() == 2.0
    assert flagged(flags, "winsorised") == [0, 99]


def test_winsorise_fixed_limits_switch_off_and_reuse():
    values = pd.Series([1.0, 50.0, 500.0])
    clipped, flags, limits = winsorise(values, "x", {"winsor": {"limits": [10.0, 100.0]}})
    assert list(clipped) == [10.0, 50.0, 100.0]
    clipped, flags, limits = winsorise(values, "x", {"winsor": False})
    assert list(clipped) == [1.0, 50.0, 500.0] and len(flags) == 0
    clipped, flags, limits = winsorise(values, "x", {}, limits=(0.0, 60.0))
    assert list(clipped) == [1.0, 50.0, 60.0]


def test_version_from_a_column():
    raw = pd.DataFrame({"ver": ["WAIS3", "wais4", "WAIS9", ""], "x": ["1", "2", "3", ""]})
    keys = make_keys(["A", "B", "C", "D"], [0, 0, 0, 0], ["2015-01-01"] * 4)
    schema = {"version": {"name": "wais_version", "column": "ver", "codes": {"WAIS3": "wais3", "WAIS4": "wais4"}},
              "variables": {"v": {"column": "x"}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:2]) == ["wais3", "wais4"] and version[2:].isna().all()
    assert flagged(flags, "version_unknown") == [2]      # data, but a code that is not listed


def test_version_from_which_items_are_filled():
    raw = pd.DataFrame({"i1": ["1", "1", ""], "i2": ["2", "", ""], "i3": ["3", "", ""]})
    keys = make_keys(["A", "B", "C"], [0, 0, 0], ["2015-01-01"] * 3)
    schema = {"version": {"name": "form", "filled": {"long": ["i2", "i3"], "short": ["i1"]}},
              "variables": {"a": {"column": "i1"}, "b": {"column": "i2"}, "c": {"column": "i3"}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:2]) == ["long", "short"] and pd.isna(version[2])
    assert len(flags) == 0


def test_version_recorded_once_per_patient():
    usubjid = ["A", "A", "A", "B", "B", "C", "C", "C", "D", "D", "E"]
    months = [0, 12, 84, 0, 6, 0, 12, 60, 0, 6, 0]
    dates = ["2015-03-01", "2016-03-01", "2022-06-01", "2021-05-01", "2021-12-01",
             "2018-01-01", "2019-01-01", "2023-01-01", "2021-03-01", "2021-09-01", "2024-02-01"]
    written = ["DSM4", "", "", "DSM5", "", "", "", "", "", "", ""]
    raw = pd.DataFrame({"dsm": written, "x": ["1"] * 11})
    keys = make_keys(usubjid, months, dates)
    schema = {"version": {"name": "dsm_version", "column": "dsm", "codes": {"DSM4": "dsm4", "DSM5": "dsm5"},
                          "level": "patient", "follow_up": {"dsm5": "2022-01-01"},
                          "by_inclusion_date": {"dsm4": ["1900-01-01", "2019-12-31"],
                                                "dsm5": ["2023-01-01", "2100-12-31"]}},
              "variables": {"v": {"column": "x"}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:3]) == ["dsm4", "dsm4", "dsm5"]   # A: follow-up before 2022, then from 2022
    assert list(version[3:5]) == ["dsm5", "dsm5"]          # B: the inclusion value
    assert list(version[5:8]) == ["dsm4", "dsm4", "dsm5"]  # C: no value, included in 2018
    assert version[8:10].isna().all()                      # D: no value, included in 2021
    assert version[10] == "dsm5"                           # E: no value, included in 2024
    assert flagged(flags, "version_inferred") == [5, 6, 10]
    assert flagged(flags, "version_unknown") == [8, 9]


def test_fix_sign_flips_the_scores_written_before_a_centre_changed():
    months = pd.date_range("2012-01-01", periods=30, freq="MS")
    time = np.array([20 + (7 * i) % 23 for i in range(30)], dtype=float)
    good = -(time - 30) / 10                       # a slow time gives a low z-score
    old = months < "2013-03-01"                    # centre A used the opposite sign until March 2013
    values = pd.DataFrame({"time": np.tile(time, 2), "z": np.concatenate([np.where(old, -good, good), good])})
    keys = make_keys(["P"] * 60, [0] * 60, list(months) * 2, ["A"] * 30 + ["B"] * 30)
    schema = {"sign": {"relation": "negative", "by": "siteid", "pairs": {"z": "time"}}}
    values, flags, switch = fix_sign(values, keys, schema)
    assert switch == {"A": pd.Timestamp("2013-03-01")}
    assert list(values["z"]) == pytest.approx(list(good) * 2)
    assert flagged(flags, "sign_flipped") == list(range(14))
    assert flagged(flags, "sign_doubt") == [11, 12, 13, 14, 15, 16]   # within 90 days of the switch


def test_collapse_patient_level_keeps_the_first_value_and_flags_changes():
    keys = make_keys(["A", "A", "A", "B", "B"], [0, 6, 12, 0, 6], ["2015-01-01"] * 5)
    values = pd.DataFrame({"sex": ["F", None, "F", "M", "F"]})
    patients, flags = collapse_patient_level(values, keys)
    assert list(patients["usubjid"]) == ["A", "B"]
    assert list(patients["sex"]) == ["F", "M"]
    assert flagged(flags, "patient_value_varies") == [3]
