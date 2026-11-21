"""DR MINI: the suicide risk level, the major depressive episode and the agoraphobia conclusions recomputed (DR decision D85)."""

from pathlib import Path

import numpy as np
import pandas as pd

from facedata import custom
from facedata.harmonise import compute_scores
from facedata.schema import load_schema

MINI = Path(__file__).parent.parent / "facedata" / "dr" / "schemas" / "mini"


def test_risk_level_uses_the_bands_of_mini_7():
    """1 to 8 low, 9 to 16 moderate, 17 or more high; a score of 0 or no score has no level."""
    values = pd.DataFrame({"mini_suicide_risk_score": [0, 1, 8, 9, 16, 17, 52, np.nan]})
    level = custom.mini_risk_level(values)
    assert pd.isna(level[0]) and pd.isna(level[7])
    assert list(level[1:7]) == [1, 1, 2, 2, 3, 3]


def two_weeks(core, symptoms, impairment):
    """One visit of the last two weeks: A1b and A2b, the seven A3 (1 yes, 0 no, None empty) and A4."""
    row = {"mini_a01b": core[0], "mini_a02b": core[1], "mini_a04_p2w": impairment}
    row.update({"mini_a03" + letter + "_p2w": answer for letter, answer in zip("abcdefg", symptoms)})
    return row


def test_current_episode_needs_five_symptoms_a1_or_a2_and_a4():
    visits = pd.DataFrame([
        two_weeks([1, 0], [1, 1, 1, 1, 0, 0, 0], 1),                      # 5 with A1: yes
        two_weeks([1, 0], [1, 1, 1, 0, 0, 0, 0], 1),                      # 4: no
        two_weeks([1, 1], [1, 1, 1, 1, 1, 1, 1], 0),                      # A4 no: no
        two_weeks([0, 0], [None] * 7, None),                              # A1b and A2b no, the rest hidden: no
        two_weeks([0, 0], [1, 1, 1, 1, 1, 1, 1], 1),                      # 7 symptoms but neither A1 nor A2: no
        two_weeks([0, 1], [1, 1, 1, 1, None, None, None], 1),             # 5 yes, 3 empty: yes all the same
        two_weeks([0, 1], [1, 1, 0, None, None, None, None], 1),          # 3 yes, 4 empty: could be 5, missing
        two_weeks([1, 0], [None] * 7, None),                              # A1b yes, nothing after: missing
        two_weeks([1, 0], [0, 0, 0, 0, None, None, None], None),          # 1 yes, 3 empty: cannot reach 5, no
        two_weeks([None, None], [None] * 7, None),                        # module not answered: missing
    ], dtype=float)
    current = custom.mini_mde_current(visits)
    assert list(current[:6]) == [1, 0, 0, 0, 0, 1]
    assert pd.isna(current[6]) and pd.isna(current[7]) and current[8] == 0 and pd.isna(current[9])


def test_past_episode_reads_the_items_of_its_own_form():
    """At inclusion the past items, at follow-up their _fu twins."""
    symptoms = ["mini_a03" + letter + "_pe" for letter in "abcdefg"]
    inclusion = pd.DataFrame([[1, 1] + [1, 1, 1, 0, 0, 0, 0] + [1]], columns=["mini_a01a", "mini_a02a"] + symptoms + ["mini_a04_pe"], dtype=float)
    follow_up = inclusion.rename(columns=lambda name: name + "_fu")
    follow_up["mini_a04_pe_fu"] = 0.0
    assert list(custom.mini_mde_past(inclusion)) == [1]
    assert list(custom.mini_mde_past_fu(follow_up)) == [0]


def test_agoraphobia_conclusions_follow_e2_d5_and_d7():
    """The three conclusions of module E as the form writes them, in the YAML of the DR schema."""
    schema = load_schema(MINI / "mini_e_agoraphobia.yaml")
    values = pd.DataFrame({
        "mini_e02":                        [1, 0, 1, 0, 1, np.nan],
        "mini_d07_every_visit":            [1, 1, 0, 0, np.nan, 1],
        "mini_panic_lifetime_every_visit": [1, 1, 0, 0, 0, 1],
    })
    for name, variable in schema["variables"].items():
        if name not in values:
            values[name] = np.nan                     # the stored conclusions: nothing to compare here
    values, flags = compute_scores(values, schema)
    assert list(values["mini_panic_with_agoraphobia_current"][:4]) == [1, 0, 0, 0]
    assert list(values["mini_panic_without_agoraphobia_current"][:4]) == [0, 1, 0, 0]
    assert list(values["mini_agoraphobia_without_panic_current"][:5]) == [0, 0, 1, 0, 1]
    assert values.loc[4:, ["mini_panic_with_agoraphobia_current", "mini_panic_without_agoraphobia_current"]].isna().all().all()
    assert pd.isna(values.loc[5, "mini_agoraphobia_without_panic_current"])


def test_ticked_boxes_keep_only_a_tick():
    """The fallback where the rule cannot be computed: a box at 1, never the 0 that the form writes when it opens."""
    values = pd.DataFrame({"mini_mde_current_stored": [1, 0, np.nan, 1],
                           "mini_mde_past_stored":    [1, 0, np.nan, np.nan],
                           "mini_mde_past_fu_stored": [np.nan, np.nan, 0, 1]})
    current = custom.mini_mde_current_ticked(values)
    past = custom.mini_mde_past_ticked(values)
    assert current[0] == 1 and current.iloc[1:3].isna().all() and current[3] == 1
    assert past[0] == 1 and past.iloc[1:3].isna().all() and past[3] == 1
