"""Steps 4 and 7 to 12: versions, units, sign, range, scores, patient level, winsorising."""

import numpy as np
import pandas as pd
import pytest

from facedata import custom
from facedata.harmonise import (censoring_from_units, check_range, collapse_patient_level,
                                compute_scores, convert_units, detect_version, doubt_period, fix_sign,
                                look_up, winsorise)
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
    assert flagged(flags, "unit_inferred") == [2, 4]   # impossible under its label, or an unusable label
    assert flagged(flags, "unit_doubt") == [3]         # possible in mmol/L, but fits g/L better
    # row 5 has no label at all and is simply in the schema's unit: no flag
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


def test_doubt_period_flags_and_keeps_the_values():
    values = pd.Series([1.0, 1.0, 0.0, np.nan, 1.0])
    dates = pd.Series(pd.to_datetime(["2021-12-31", "2022-01-01", "2022-06-01", "2022-06-02", "2023-12-31"]))
    period = [pd.Timestamp("2022-01-01"), pd.Timestamp("2023-12-31")]
    # Only the "yes" (1) of the period: its first and its last day are inside.
    flags = doubt_period(values, dates, "x", {"period": period, "values": [1.0], "note": "why"})
    assert flagged(flags, "period_doubt") == [1, 4] and set(flags["detail"]) == {"why"}
    # Without values, every filled cell of the period.
    assert flagged(doubt_period(values, dates, "x", {"period": period}), "period_doubt") == [1, 2, 4]
    # A category: the labels are listed.
    labels = pd.Series(["last_week", "long_ago", None, "last_week", "last_week"], dtype=object)
    flags = doubt_period(labels, dates, "x", {"period": period, "values": [1.0, "last_week"]})
    assert flagged(flags, "period_doubt") == [3, 4]


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


def test_a_value_derived_from_an_empty_variable_is_doubted():
    """derived_from may name a variable: a percentile computed from an empty score is kept and flagged."""
    schema = {"variables": {"score": {}, "percentile": {"derived_from": "score"}}}
    values = pd.DataFrame({"score": [5.0, np.nan, np.nan], "percentile": [25.0, 0.0, np.nan]})
    values, flags = compute_scores(values, schema)
    assert list(values["percentile"][:2]) == [25.0, 0.0]
    assert flagged(flags, "derived_doubt") == [1]


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
              "variables": {"v": {"columns": ["x"]}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:2]) == ["wais3", "wais4"] and version[2:].isna().all()
    assert flagged(flags, "version_unknown") == [2]      # data, but a code that is not listed


def test_version_from_which_items_are_filled():
    raw = pd.DataFrame({"i1": ["1", "1", ""], "i2": ["2", "", ""], "i3": ["3", "", ""]})
    keys = make_keys(["A", "B", "C"], [0, 0, 0], ["2015-01-01"] * 3)
    schema = {"version": {"name": "form", "filled": {"long": ["i2", "i3"], "short": ["i1"]}},
              "variables": {"a": {"columns": ["i1"]}, "b": {"columns": ["i2"]}, "c": {"columns": ["i3"]}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:2]) == ["long", "short"] and pd.isna(version[2])
    assert len(flags) == 0


def test_version_from_the_columns_of_another_instrument():
    # q1 is the instrument's own item. The form is told by another questionnaire of the same visit.
    raw = pd.DataFrame({"q1": ["1", "2", "", "3"], "other_long": ["4", "", "4", ""], "other_item": ["1", "1", "1", ""]})
    keys = make_keys(["A", "B", "C", "D"], [0, 0, 0, 0], ["2015-01-01"] * 4)
    schema = {"version": {"name": "form", "filled": {"long": ["other_long"], "short": ["other_item"]}},
              "variables": {"a": {"columns": ["q1"]}}}
    version, flags = detect_version(raw, keys, schema)
    assert list(version[:2]) == ["long", "short"]
    assert pd.isna(version[2])                           # the other questionnaire is filled, this one is not
    assert pd.isna(version[3]) and flagged(flags, "version_unknown") == [3]   # an answer, and nothing tells the form


def test_a_form_is_not_read_before_the_day_it_came_into_use():
    # The four visits hold the short form's item. The first is dated before the form existed.
    raw = pd.DataFrame({"i1": ["1", "1", "1", "1"], "i2": ["", "", "2", "2"]})
    keys = make_keys(["A", "B", "C", "D"], [0, 0, 0, 0], ["2019-06-01", "2021-01-01", "2019-06-01", "2022-03-01"])
    keys.loc[3, "visit_date"] = pd.NaT
    schema = {"version": {"name": "form", "filled": {"long": ["i2"], "short": ["i1"]}, "since": {"short": "2021-01-01"}},
              "variables": {"a": {"columns": ["i1"]}, "b": {"columns": ["i2"]}}}
    version, flags = detect_version(raw, keys, schema)
    assert pd.isna(version[0]) and list(version[1:]) == ["short", "long", "long"]   # no fall back on the long form
    assert flagged(flags, "version_unknown") == [0]
    assert list(flags["detail"]) == ["dated before the form came into use"]
    raw["i2"] = ""                                       # now the four visits look like the short form
    version, flags = detect_version(raw, keys, schema)
    assert version[1] == "short" and version[3] == "short"   # the first day counts; a visit with no date keeps its form
    assert flagged(flags, "version_unknown") == [0, 2]


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
              "variables": {"v": {"columns": ["x"]}}}
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


def test_a_score_can_subtract_and_have_a_floor():
    schema = {"variables": {"a": {}, "b1": {}, "b2": {}, "stored": {}},
              "scores": {"b": {"sum": ["b1", "b2"], "compare_offset": 0.0},
                         "total": {"sum": ["a"], "minus": ["b"], "floor": 0.0, "compare": "stored", "compare_offset": 0.0}}}
    values = pd.DataFrame({"a": [8.0, 2.0, 5.0, 4.0], "b1": [1.0, 2.0, 1.0, np.nan], "b2": [2.0, 2.0, 0.0, 1.0],
                           "stored": [5.0, 0.0, 9.0, 3.0]})
    values, flags = compute_scores(values, schema)
    assert list(values["total"][:3]) == [5.0, 0.0, 4.0]      # 8 - 3; 2 - 4 raised to 0; 5 - 1
    assert pd.isna(values["total"][3])                       # b cannot be computed
    assert flagged(flags, "score_mismatch") == [2]


def test_a_score_can_be_scaled():
    schema = {"variables": {"a": {"range": [1.0, 5.0]}, "b": {"range": [1.0, 5.0]}, "stored": {}},
              "scores": {"percent": {"mean": ["a", "b"], "scale": [25.0, -25.0], "compare": "stored", "compare_offset": 0.0},
                         "half": {"sum": ["a", "b"], "reverse": ["b"], "scale": [0.5, 0.0], "compare_offset": 0.0}}}
    values = pd.DataFrame({"a": [1.0, 5.0, 3.0, 4.0], "b": [1.0, 5.0, 4.0, np.nan], "stored": [0.0, 100.0, 50.0, 75.0]})
    values, flags = compute_scores(values, schema)
    assert list(values["percent"][:3]) == [0.0, 100.0, 62.5]     # (mean - 1) x 25
    assert list(values["half"][:3]) == [3.0, 3.0, 2.5]           # (a + 6 - b) / 2
    assert values[["percent", "half"]].iloc[3].isna().all()      # an item is missing
    assert flagged(flags, "score_mismatch") == [2]


def test_units_without_a_unit_column_are_read_from_the_size_of_the_value():
    height = {"unit": "cm", "range": [100.0, 230.0],
              "units": {"cm": {"factor": 1.0, "expect": [100.0, 230.0]}, "mm": {"factor": 0.1, "expect": [1000.0, 2300.0]}}}
    values = pd.Series([172.0, 1650.0, 18.0])
    converted, flags = convert_units(values, texts(["", "", ""]), "height", height)
    assert list(converted) == pytest.approx([172.0, 165.0, 18.0])
    assert flagged(flags, "unit_inferred") == [1]      # only the value that was really converted


def test_a_score_can_be_a_formula_of_custom_py_with_a_tolerance():
    schema = {"variables": {"weight": {}, "height": {}, "stored": {}},
              "scores": {"bmi": {"custom": "body_mass_index", "compare": "stored", "compare_offset": 0.0,
                                 "compare_tolerance": 0.051}}}
    values = pd.DataFrame({"weight": [70.0, 80.0], "height": [175.0, 160.0], "stored": [22.9, 35.0]})
    values, flags = compute_scores(values, schema)
    assert list(values["bmi"]) == pytest.approx([22.857, 31.25], abs=0.001)
    assert flagged(flags, "score_mismatch") == [1]     # 22.9 is 22.857 rounded; 35.0 is not 31.25


def test_a_percentage_of_another_variable():
    """A kind of white cells written in percent is converted with the leukocytes of the visit."""
    count = {"unit": "G/L", "range": [0.0, 25.0],
             "units": {"G/L": {"factor": 1.0, "expect": [0.0, 25.0]},
                       "%": {"factor": None, "percent_of": "leukocytes", "expect": [0.0, 100.0]}}}
    wholes = pd.DataFrame({"leukocytes": [6.0, 6.0, 8.0, np.nan]})
    labels = texts(["G/L", "%", "G/L", "%"])
    converted, flags = convert_units(pd.Series([3.8, 50.0, 60.0, 55.0]), labels, "neutrophils", count, wholes=wholes)
    assert list(converted[:3]) == pytest.approx([3.8, 3.0, 4.8])
    assert pd.isna(converted[3])                       # no leukocytes at that visit
    assert flagged(flags, "unit_converted") == [1]     # labelled %: 50% of 6.0
    assert flagged(flags, "unit_inferred") == [2]      # 60 G/L is impossible: 60% of 8.0
    assert flagged(flags, "unit_unknown") == [3]
    assert len(flags) == 3


def test_a_unit_rule_reads_the_values_without_a_label(monkeypatch):
    """Two units on overlapping scales: a function of custom.py decides where there is no label."""
    def rule(values, keys):
        assert list(values.isna()) == [False, True, False]     # it is not asked about the labelled value
        return pd.Series(["b", None, None], dtype=object)

    monkeypatch.setattr(custom, "demo_rule", rule, raising=False)
    variable = {"unit": "a", "unit_rule": "demo_rule",
                "units": {"a": {"factor": 1.0, "expect": [0.0, 10.0]}, "b": {"factor": 2.0, "expect": [5.0, 50.0]}}}
    converted, flags = convert_units(pd.Series([7.0, 7.0, 7.0]), texts(["", "b", ""]), "x", variable)
    assert list(converted[:2]) == [14.0, 14.0]
    assert pd.isna(converted[2])                       # the rule cannot tell, and both units fit
    assert flagged(flags, "unit_inferred") == [0]
    assert flagged(flags, "unit_converted") == [1]
    assert flagged(flags, "unit_unknown") == [2]


def test_prolactin_unit_follows_the_centre_and_the_period():
    """Made-up results. Centre A reports in mUI/L, centre B in ng/mL, centre C has too few results."""
    centre_a = [150.0, 220, 310, 180, 400, 250, 190, 270, 330, 210, 160, 20, 60]
    centre_b = [8.0, 12, 15, 9, 22, 11, 14, 7, 18, 10, 13, 150, 60, 700]
    centre_c = [150.0, 60]
    values = pd.Series(centre_a + centre_b + centre_c)
    dates = (list(pd.date_range("2015-01-05", periods=13, freq="7D"))
             + list(pd.date_range("2015-01-05", periods=14, freq="7D")) + ["2015-03-01", "2015-03-08"])
    sites = ["A"] * 13 + ["B"] * 14 + ["C"] * 2
    keys = make_keys(["P" + str(number) for number in range(29)], [0] * 29, dates, sites)
    unit = custom.prolactin_unit(values, keys)
    # A: the eleven results of 150 to 400 are mUI/L, 20 is ng/mL, and 60 cannot be told there.
    assert list(unit[:11]) == ["mUI/L"] * 11
    assert unit[11] == "ng/mL" and pd.isna(unit[12])
    # B: 150 cannot be told in a centre that reports in ng/mL, 60 is ng/mL, 700 is mUI/L anywhere.
    assert list(unit[13:24]) == ["ng/mL"] * 11
    assert pd.isna(unit[24]) and unit[25] == "ng/mL" and unit[26] == "mUI/L"
    # C: with one other result nothing is known about the centre.
    assert pd.isna(unit[27]) and unit[28] == "ng/mL"


def test_qids_total_takes_the_highest_item_of_a_symptom():
    items = ["qidsr1" + str(number).zfill(2) for number in range(1, 17)]
    rows = [[0] * 16,
            [3, 1, 0, 2] + [1] + [0, 2, 1, 0] + [1, 1, 1, 1, 1] + [2, 3],
            [1] * 15 + [np.nan]]
    total = custom.qids_total(pd.DataFrame(rows, columns=items, dtype=float))
    assert total[0] == 0
    assert total[1] == 3 + 1 + 2 + 5 + 3               # sleep, item 5, appetite or weight, items 10 to 14, psychomotor
    assert pd.isna(total[2])                           # one item is missing


def test_qids_total_needs_one_answer_of_each_appetite_and_weight_pair():
    items = ["qidsr1" + str(number).zfill(2) for number in range(1, 17)]
    rows = [[1, 1, 1, 1] + [1] + [np.nan, 2, 3, np.nan] + [1, 1, 1, 1, 1] + [1, 1],     # item 7 and item 8, as the form asks
            [1, 1, 1, 1] + [1] + [2, 1, np.nan, np.nan] + [1, 1, 1, 1, 1] + [1, 1],     # no weight item
            [1, 1, 1, 1] + [1] + [np.nan, np.nan, 0, 0] + [1, 1, 1, 1, 1] + [1, 1]]     # no appetite item
    total = custom.qids_total(pd.DataFrame(rows, columns=items, dtype=float))
    assert total[0] == 1 + 1 + 3 + 5 + 1
    assert total[1:].isna().all()


def stai_answers(rows):
    """Twenty stored STAI answers per visit: the two given answers, then the first one again."""
    table = pd.DataFrame([[first, second] + [first] * 18 for first, second in rows], dtype=float)
    table.columns = [f"staya{number:02d}_stored" for number in range(1, 21)]
    return table


def test_stai_shift_finds_the_coding_of_a_visit():
    values = stai_answers([(0, 3), (1, 4), (2, 5), (1, 3), (2, 4), (2, 3), (np.nan, np.nan)])
    keys = pd.DataFrame({"siteid": ["01", "02", "03", "01", "01", "02", "01"],
                         "visit_date": pd.to_datetime(["2015-03-01"] * 3 + ["2015-06-01", "2015-07-01", "2016-01-01", "2015-08-01"])})
    shift = custom.stai_shift(values, keys)
    assert list(shift[:3]) == [1, 0, -1]               # a 0, a 1 with a 4, a 5: only one coding is possible
    assert shift[3] == 1                               # 1 to 3 could be two codings: its centre used 0 to 3 that year
    assert pd.isna(shift[4])                           # 2 to 4 does not fit the coding of the centre
    assert pd.isna(shift[5])                           # no other visit of that centre in that year
    assert pd.isna(shift[6])                           # no answer


def test_stai_shift_is_missing_when_a_centre_used_two_codings_in_a_year():
    values = stai_answers([(0, 3), (1, 4), (1, 3)])
    keys = pd.DataFrame({"siteid": ["01"] * 3, "visit_date": pd.to_datetime(["2015-03-01"] * 3)})
    assert pd.isna(custom.stai_shift(values, keys)[2])


def test_shaps_counts_the_items_answered_disagree():
    items = [f"shaps{number:02d}" for number in range(1, 15)]
    rows = [[3] * 14, [0] * 14, [1, 0] + [2] * 12, [2, 2, 0, 3, 3, 0, 2, 0, 3, 0, 0, 0, 0, 0], [0] * 13 + [np.nan]]
    values = pd.DataFrame(rows, columns=items, dtype=float)
    assert list(custom.shaps_total(values)[:4]) == [0, 14, 2, 8]
    assert pd.isna(custom.shaps_total(values)[4])                         # one item is missing
    # The EMR counts "agree" on items 2, 4, 5, 7 and 9 and "disagree" on the nine others.
    assert list(custom.shaps_total_as_stored(values)[:4]) == [5, 9, 5, 13]


def test_psqi_latency_puts_minutes_and_item_5a_in_classes():
    values = pd.DataFrame({"psqi_latency": [10.0, 20.0, 45.0, 90.0, np.nan, 30.0],
                           "psqi05a": [0.0, 0.0, 2.0, 3.0, 1.0, np.nan]})
    component = custom.psqi_latency(values)
    assert list(component[:4]) == [0, 1, 2, 3]         # 0 + 0, 1 + 0, 2 + 2 and 3 + 3 points
    assert component[4:].isna().all()


def test_look_up_with_a_second_variable_and_open_bands():
    """A made-up table of percentile bands that depends on the age and on the years of education."""
    table = pd.DataFrame({
        "age_min": [0, 0, 0, 50, 50], "age_max": [49, 49, 49, 99, 99],
        "by_min": [0, 10, 10, 0, 0], "by_max": [9, 99, 99, 99, 99],
        "raw_min": [0, 0, 1, 0, 2], "raw_max": [99, 0, 99, 1, 99],
        "value": [10, 25, 0, 50, 5], "cens": [0, 1, 0, 1, 0]})
    raw = pd.Series([0.0, 0.0, 3.0, 1.0, 0.0, 0.0])
    age = pd.Series([30.9, 30.2, 25.0, 55.0, 30.0, np.nan])
    education = pd.Series([9.0, 15.0, 12.5, 8.0, np.nan, 15.0])
    values, cens, flags = look_up(raw, age, table, "errors_band", education)
    assert list(values[:4]) == [10, 25, 0, 50]
    assert list(cens[:4]) == [0, 1, 0, 1]                    # with no error, "this band or a higher one"
    assert values[4:].isna().all()                           # no education, or no age
    assert flagged(flags, "censored_right") == [1, 3]
    assert flagged(flags, "norm_missing") == [4, 5]


def test_psp_band_of_the_score():
    values = pd.DataFrame({"psp_total": [95.0, 91.0, 90.0, 55.0, 10.0, 1.0, 55.0, None],
                           "psp_band": [1.0, 1.0, 2.0, 5.0, 10.0, 10.0, 6.0, 3.0]})
    assert list(custom.psp_band_differs(values)) == [False, False, False, False, False, False, True, False]


def test_a_custom_score_can_use_the_key_columns():
    """custom: name(values, keys). The age at the inclusion visit is the same on every row of a patient."""
    keys = pd.DataFrame({"usubjid": ["a", "a", "a", "b"], "visit": ["screening", "V0", "V1_an", "screening"],
                         "age": [40.9, 41.2, 42.3, 30.0]})
    schema = {"variables": {}, "scores": {"age_at_inclusion": {"custom": "age_at_inclusion", "keep": True}}}
    values, flags = compute_scores(pd.DataFrame(index=keys.index), schema, keys=keys)
    assert list(values["age_at_inclusion"][:3]) == [41, 41, 41]          # the age at V0, also on the other rows
    assert pd.isna(values["age_at_inclusion"][3])                         # no inclusion visit
