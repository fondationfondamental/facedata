"""The rare rules that cannot be written as data in a schema.

A schema refers to a function of this file by its name:

- `parse: name` on a variable: name(text) takes the cleaned text of the
  column and returns the values.
- `checks: {variable: name}` on an instrument: name(values) takes the table
  of the instrument's values and returns True for the rows where the
  variable fails the check.
- `custom: name` on a score: name(values) takes the same table and returns
  the score, when it is not a sum or a mean.
- `unit_rule: name` on a variable: name(values, keys) takes the values that
  have no usable unit label and the key columns, and returns the unit of
  each value (missing where it cannot tell).

Use them rarely (docs/SCHEMA_SPEC.md, section 10).
"""

import numpy as np
import pandas as pd


def cgi_index_differs(values):
    """CGI efficacy index: (therapeutic effect - 1) x 4 + side effects.

    True where the stored index is another number.
    """
    expected = (values["cgi_therapeutic_effect"] - 1) * 4 + values["cgi_side_effects"]
    stored = values["cgi_efficacy_index"]
    return stored.notna() & expected.notna() & (stored != expected)


def psp_band_differs(values):
    """PSP: the ten-point band of the score, from 1 (100 to 91) to 10 (10 to 1).

    True where the stored band is another one.
    """
    expected = 11 - np.ceil(values["psp_total"] / 10)
    stored = values["psp_band"]
    return stored.notna() & expected.notna() & (stored != expected)


def barona_occupation_follows_diploma(values):
    """Barona estimate: the occupation holds the same place in its list as the diploma.

    The form lists seven occupations and seven diplomas. An occupation that
    mirrors the diploma (a farmer with a vocational certificate, a retired
    patient with a general baccalaureate) cannot be told from a copy. True
    where that is the case.
    """
    same_place = {"manual_worker": "no_diploma", "employee": "primary_certificate",
                  "farmer": "vocational_certificate", "craft_trade": "vocational_baccalaureate",
                  "retired": "general_baccalaureate", "intermediate": "university_first_cycle",
                  "higher_professional": "university_higher"}
    return values["barona_occupation"].map(same_place) == values["barona_education"]


def laterality_quotient(values):
    """Edinburgh inventory: 100 x (right - left) / (right + left) over its ten activities.

    The foot and the eye (lines 11 and 12) are not counted. Missing when a
    line is missing or when there is no cross at all.
    """
    numbers = [str(number).zfill(2) for number in range(1, 11)]
    right = values[["laterality_" + number + "_right" for number in numbers]].sum(axis=1, min_count=10)
    left = values[["laterality_" + number + "_left" for number in numbers]].sum(axis=1, min_count=10)
    crosses = (right + left).where(right + left > 0)
    return 100 * (right - left) / crosses


def body_mass_index(values):
    """Weight in kg divided by the square of the height in metres."""
    return values["weight"] / (values["height"] / 100) ** 2


def corrected_qt(values):
    """Bazett's formula: the QT interval divided by the square root of the RR interval, in seconds."""
    return values["qt_interval"] / values["rr_interval"] ** 0.5


def cholesterol_ratio(values):
    """Total cholesterol divided by HDL cholesterol."""
    return values["cholesterol"] / values["hdl"]


def differential_differs(values):
    """The five kinds of white cells must add up to the leukocytes, within 10%.

    True where they do not.
    """
    kinds = ["neutrophils", "lymphocytes", "monocytes", "eosinophils", "basophils"]
    total = values[kinds].sum(axis=1, min_count=len(kinds))
    return (total - values["leukocytes"]).abs() > 0.1 * values["leukocytes"]


def prolactin_unit(values, keys):
    """Unit of the prolactin results for which nobody chose a unit on the form.

    ng/mL and mUI/L overlap: 1 ng/mL is 21.2 mUI/L. A result under 30 can
    only be ng/mL, and a result of 500 or more is mUI/L. In between, the
    centre's other results of the time decide. In ng/mL about 2 results in
    100 reach 100; in mUI/L most do. So where a quarter or more of the
    centre's other results within 180 days reach 100, the centre was
    reporting in mUI/L, at least in part:

    - there, a result of 100 to 500 is mUI/L, and one of 30 to 100 cannot be told;
    - elsewhere, a result of 30 to 100 is ng/mL, and one of 100 to 500 cannot be told.

    Decision D31 in docs/bp/PROGRESS.md gives the evidence.
    """
    table = pd.DataFrame({"site": keys["siteid"], "date": keys["visit_date"], "value": values}).dropna()
    share = pd.Series(np.nan, index=values.index)    # share of the centre's other results that reach 100
    for site, part in table.groupby("site"):
        day = (part["date"] - pd.Timestamp("2000-01-01")).dt.days.to_numpy()
        reaches_100 = (part["value"] >= 100).to_numpy()
        for position, row in enumerate(part.index):
            near = np.abs(day - day[position]) <= 180
            near[position] = False                   # a result does not vote for itself
            if near.sum() >= 10:                     # fewer than 10 other results say too little
                share[row] = reaches_100[near].mean()
    in_mui_period = share >= 0.25

    unit = pd.Series(np.nan, index=values.index, dtype=object)
    unit = unit.mask(values < 30, "ng/mL")
    unit = unit.mask((values >= 30) & (values < 100) & ~in_mui_period, "ng/mL")
    unit = unit.mask((values >= 100) & (values < 500) & in_mui_period, "mUI/L")
    unit = unit.mask(values >= 500, "mUI/L")
    return unit


def qids_total(values):
    """QIDS-SR16 total: one value per symptom, 0 to 27.

    Sleep, appetite and weight, and psychomotor change are each asked in
    several items: the highest answer counts. The other six symptoms have one
    item each. Missing when one of the sixteen items is missing.
    """
    sleep = values[["qidsr101", "qidsr102", "qidsr103", "qidsr104"]].max(axis=1)
    appetite = values[["qidsr106", "qidsr107", "qidsr108", "qidsr109"]].max(axis=1)
    psychomotor = values[["qidsr115", "qidsr116"]].max(axis=1)
    alone = ["qidsr105", "qidsr110", "qidsr111", "qidsr112", "qidsr113", "qidsr114"]
    total = sleep + appetite + psychomotor + values[alone].sum(axis=1)
    items = ["qidsr1" + str(number).zfill(2) for number in range(1, 17)]
    return total.where(values[items].notna().all(axis=1))


def psqi_latency(values):
    """PSQI component 2, sleep latency (0 to 3).

    The minutes to fall asleep count 0 (15 or less), 1 (16 to 30), 2 (31 to
    60) or 3 (more). Item 5a is added, and the sum is cut again: 0 gives 0,
    1 or 2 give 1, 3 or 4 give 2, 5 or 6 give 3.
    """
    minutes = values["psqi_latency"]
    points = (minutes > 15).astype(float) + (minutes > 30) + (minutes > 60) + values["psqi05a"]
    points = points.where(minutes.notna())
    return ((points >= 1).astype(float) + (points >= 3) + (points >= 5)).where(points.notna())


def stroop_interference(values):
    """Stroop interference: the colour-word score minus the score predicted from the two other plates.

    The prediction is words x colours / (words + colours), with the scores corrected for age.
    """
    words, colours = values["stroop_word_corrected"], values["stroop_colour_corrected"]
    return values["stroop_colour_word_corrected"] - words * colours / (words + colours)


def recency_z_without_recency(values):
    """A CVLT recency z-score with no recency next to it.

    The EMR computed it from an empty cell, as if the recency were 0. True
    where that is the case.
    """
    return values["cvlt_recency_z"].notna() & values["cvlt_recency"].isna()


def medication_name(names):
    """The stem of a medication name: "TERALITHE LP 400 mg, comprimé sécable" gives "TERALITHE LP"."""
    stems = names.str.upper().str.replace(r"\s+\d.*|[,(/*].*", "", regex=True)
    return stems.str.replace(r"\s+", " ", regex=True).str.strip()

