"""Two generic rules: a value that must not be above another (not_above) and a direction decided by the data (sign)."""

import pandas as pd

from facedata.harmonise import fix_sign
from facedata.pipeline import run_instrument
from facedata.schema import check_schema, load_schema

from helpers import flagged, make_keys, texts

EPISODES = """
instrument: episodes
title: Episodes
tab: TEST
section: Episodes
status: draft
defaults: {type: number, range: [0, 90], winsor: false}
variables:
  n_mania: {}
  n_mania_psychotic: {not_above: n_mania}
  first_episode_age: {not_above: age}
"""


def test_a_value_above_another_of_the_same_row_is_kept_and_flagged(tmp_path):
    path = tmp_path / "episodes.yaml"
    path.write_text(EPISODES, encoding="utf-8")
    schema = load_schema(path)
    assert check_schema(schema) == []
    raw = pd.DataFrame({"n_mania": texts(["2", "2", "", "3"]), "n_mania_psychotic": texts(["1", "3", "4", "3"]),
                        "first_episode_age": texts(["20", "41", "35", ""])})
    keys = make_keys(["P1", "P2", "P3", "P4"], [0] * 4, ["2020-01-01"] * 4)
    keys["age"] = [30.5, 40.2, 35.0, 50.0]
    result = run_instrument(raw, keys, schema)
    assert list(result["values"]["n_mania_psychotic"]) == [1, 3, 4, 3]           # the values are not changed
    flags = result["flags"]
    psychotic = flags[flags["variable"] == "n_mania_psychotic"]
    assert flagged(psychotic, "check_failed") == [1]                             # 3 above 2; an empty count is not checked
    assert list(psychotic["detail"]) == ["above n_mania"]
    age = flags[flags["variable"] == "first_episode_age"]
    assert flagged(age, "check_failed") == [1]                                   # 41 above 40.2; 35 is not above 35.0


def test_not_above_names_a_variable_a_score_or_a_key_column(tmp_path):
    text = EPISODES.replace("{not_above: n_mania}", "{not_above: n_manic}").replace(
        "  first_episode_age: {not_above: age}", "  first_episode_age: {not_above: age}\n  kind: {type: category, codes: {A: a}, not_above: n_mania}")
    path = tmp_path / "episodes.yaml"
    path.write_text(text, encoding="utf-8")
    problems = " | ".join(check_schema(load_schema(path)))
    assert "n_mania_psychotic: not_above goes on a number or an item and names a variable, a score or a key column" in problems
    assert "kind: not_above goes on a number or an item" in problems
    assert "first_episode_age" not in problems


def scale(groups):
    """Visits of a scale of 0 to 10: a reference item and an item that goes against it on the form of today.

    groups: (centre, date, how many visits, how the item is stored: "today", "old" or "unclear").
    """
    reference = list(range(11)) + [5]                                            # 12 visits at most per group
    unclear = [3, 1, 4, 0, 5, 9, 2, 6, 5, 3, 8, 7]                               # rank correlation +0.56 with it
    rows = []
    for centre, date, count, stored in groups:
        for i in range(count):
            item = {"today": 10 - reference[i], "old": reference[i], "unclear": unclear[i]}[stored]
            rows.append({"siteid": centre, "date": date, "a": float(reference[i]), "t": float(item)})
    table = pd.DataFrame(rows)
    keys = make_keys(["P"] * len(table), [0] * len(table), list(table["date"]), list(table["siteid"]))
    return table[["a", "t"]], keys


def test_the_data_decide_the_direction_of_each_centre_and_year():
    values, keys = scale([("A", "2018-06-01", 12, "old"),       # rows 0-11: before the day, and the data agree
                          ("A", "2021-06-01", 12, "old"),       # rows 12-23: after the day, but clearly the old direction
                          ("B", "2018-06-01", 12, "today"),     # rows 24-35: before the day, but clearly today's direction
                          ("B", "2021-06-01", 5, "old"),        # rows 36-40: too few visits: the day decides
                          ("C", "2021-06-01", 12, "unclear"),   # rows 41-52: lean to the old direction, not clearly
                          ("C", None, 1, "old")])               # row 53: no date
    schema = {"variables": {"a": {}, "t": {"range": [0.0, 10.0]}},
              "sign": {"turn": ["t"], "against": ["a"], "relation": "negative", "by": "siteid", "before": pd.Timestamp("2019-01-01")}}
    stored, reference = values["t"].copy(), values["a"].copy()
    values, flags = fix_sign(values, keys, schema)
    turned = list(range(24))
    assert flagged(flags, "sign_flipped") == turned
    assert list(values["t"][turned]) == list(10 - stored[turned])                # around the middle of the range
    assert list(values["t"][24:]) == list(stored[24:])
    assert list(values["a"]) == list(reference)                                  # the reference is never turned
    doubts = flags[flags["flag"] == "sign_doubt"]
    assert sorted(doubts.loc[doubts["detail"].str.contains("lean"), "row"]) == list(range(41, 53))
    assert sorted(doubts.loc[doubts["detail"].str.contains("change of form"), "row"]) == [53]


def test_without_a_day_only_the_data_turn_a_centre_and_year():
    values, keys = scale([("A", "2014-06-01", 12, "old"), ("A", "2016-06-01", 12, "today"), ("B", "2014-06-01", 9, "old")])
    schema = {"variables": {"a": {}, "t": {"range": [0.0, 10.0]}},
              "sign": {"turn": ["t"], "against": ["a"], "relation": "negative", "by": "siteid"}}
    values, flags = fix_sign(values, keys, schema)
    assert flagged(flags, "sign_flipped") == list(range(12))                     # 9 visits are too few to tell
    assert flagged(flags, "sign_doubt") == []


def test_check_schema_reads_the_three_forms_of_a_sign_block(tmp_path):
    base = EPISODES.replace("defaults: {type: number, range: [0, 90], winsor: false}", "defaults: {type: number, range: [0, 10], winsor: false}")
    blocks = {"sign: {turn: [n_mania], before: 2021-09-01}": [],
              "sign: {turn: [n_mania], against: [first_episode_age], relation: negative, by: siteid}": [],
              "sign: {turn: [n_mania], against: [first_episode_age], relation: negative, by: siteid, before: 2021-09-01}": [],
              "sign: {turn: [n_mania]}": ["sign: needs turn"],
              "sign: {turn: [n_mania], against: [nothing], relation: down, by: centre}": [
                  "sign: 'nothing' is not a variable", "sign: relation is negative or positive", "sign: by must be a key column"]}
    for block, expected in blocks.items():
        path = tmp_path / "episodes.yaml"
        path.write_text(base + block + "\n", encoding="utf-8")
        problems = [problem for problem in check_schema(load_schema(path)) if "sign:" in problem]
        assert len(problems) == len(expected), (block, problems)
        for sentence in expected:
            assert any(sentence in problem for problem in problems), (block, problems)
