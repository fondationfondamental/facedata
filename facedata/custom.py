"""The rare rules that cannot be written as data in a schema.

A schema refers to a function of this file by its name:

- `parse: name` on a variable: name(text) takes the cleaned text of the
  column and returns the values.
- `checks: {variable: name}` on an instrument: name(values) takes the table
  of the instrument's values and returns True for the rows where the
  variable fails the check.
- `custom: name` on a score: name(values, keys) takes the same table and the
  key columns, and returns the score, when it is not a sum or a mean. Most
  scores do not use the keys.
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


def laterality_quotient(values, keys=None):
    """Edinburgh inventory: 100 x (right - left) / (right + left) over its ten activities.

    The foot and the eye (lines 11 and 12) are not counted. Missing when a
    line is missing or when there is no cross at all.
    """
    numbers = [str(number).zfill(2) for number in range(1, 11)]
    right = values[["laterality_" + number + "_right" for number in numbers]].sum(axis=1, min_count=10)
    left = values[["laterality_" + number + "_left" for number in numbers]].sum(axis=1, min_count=10)
    crosses = (right + left).where(right + left > 0)
    return 100 * (right - left) / crosses


def body_mass_index(values, keys=None):
    """Weight in kg divided by the square of the height in metres."""
    return values["weight"] / (values["height"] / 100) ** 2


def corrected_qt(values, keys=None):
    """Bazett's formula: the QT interval divided by the square root of the RR interval, in seconds."""
    return values["qt_interval"] / values["rr_interval"] ** 0.5


def cholesterol_ratio(values, keys=None):
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


def age_at_inclusion(values, keys):
    """Age in whole years at the inclusion visit (V0), from the date of birth.

    The same value on every row of a patient; missing for a patient with no
    V0 or no date of birth. For an extraction whose stored age is not the age
    at inclusion.
    """
    at_inclusion = keys.loc[keys["visit"] == "V0"].drop_duplicates("usubjid").set_index("usubjid")["age"]
    return np.floor(keys["usubjid"].map(at_inclusion))


def stai_shift(values, keys):
    """STAI: the number to add to the answers of a visit to bring them to the coding 1 to 4.

    The twenty answers have four levels. One extraction stores them from 0 to
    3, from 1 to 4 or from 2 to 5, depending on the centre and the year, and
    no column says which. A visit that holds a 0 is coded from 0 (add 1), a
    visit that holds a 5 from 2 (subtract 1), and a visit that holds both a 1
    and a 4 from 1. Any other visit could be read two ways: it takes the
    coding of the visits of its centre in the same year when they all have
    the same one and its answers fit it. Otherwise missing.
    """
    answers = values[[f"staya{number:02d}_stored" for number in range(1, 21)]]
    low, high = answers.min(axis=1), answers.max(axis=1)
    shift = pd.Series(np.nan, index=values.index)
    shift[(low == 0) & (high <= 3)] = 1
    shift[(low == 1) & (high == 4)] = 0
    shift[(low >= 2) & (high == 5)] = -1
    place = [keys["siteid"], keys["visit_date"].dt.year]
    one_coding = shift.groupby(place).transform("nunique") == 1
    of_the_place = shift.groupby(place).transform("min").where(one_coding)
    fits = (low + of_the_place >= 1) & (high + of_the_place <= 4)
    return shift.fillna(of_the_place.where(fits))


def shaps_total(values, keys=None):
    """SHAPS: the number of items answered "disagree" or "strongly disagree" (0 or 1).

    From 0 to 14; a higher score is more anhedonia. Missing unless the
    fourteen items are answered.
    """
    items = values[[f"shaps{number:02d}" for number in range(1, 15)]]
    return (items <= 1).sum(axis=1).where(items.notna().all(axis=1))


def shaps_total_as_stored(values, keys=None):
    """SHAPS as one EMR counts it: "agree" on items 2, 4, 5, 7 and 9, "disagree" on the nine others.

    Not the score of the scale: it is computed only to check the stored column.
    """
    items = values[[f"shaps{number:02d}" for number in range(1, 15)]]
    counted_on_agree = ["shaps02", "shaps04", "shaps05", "shaps07", "shaps09"]
    points = (items <= 1).astype(int)
    points[counted_on_agree] = (items[counted_on_agree] >= 2).astype(int)
    return points.sum(axis=1).where(items.notna().all(axis=1))


def qids_total(values, keys=None):
    """QIDS-SR16 total: one value per symptom, 0 to 27.

    Sleep, appetite and weight, and psychomotor change are each asked in
    several items: the highest answer counts. The other six symptoms have one
    item each. The form asks for item 6 or item 7 (appetite down or up) and
    for item 8 or item 9 (weight down or up), so one answer of each pair is
    enough. Missing when any other item is missing.
    """
    sleep = values[["qidsr101", "qidsr102", "qidsr103", "qidsr104"]].max(axis=1)
    appetite = values[["qidsr106", "qidsr107", "qidsr108", "qidsr109"]].max(axis=1)
    psychomotor = values[["qidsr115", "qidsr116"]].max(axis=1)
    alone = ["qidsr105", "qidsr110", "qidsr111", "qidsr112", "qidsr113", "qidsr114"]
    total = sleep + appetite + psychomotor + values[alone].sum(axis=1)
    always = ["qidsr101", "qidsr102", "qidsr103", "qidsr104", "qidsr115", "qidsr116"] + alone
    appetite_answered = values[["qidsr106", "qidsr107"]].notna().any(axis=1)
    weight_answered = values[["qidsr108", "qidsr109"]].notna().any(axis=1)
    return total.where(values[always].notna().all(axis=1) & appetite_answered & weight_answered)


def adi_peer_item(values, keys=None):
    """ADI-R algorithm: the peer item that counts at the age of the subject.

    Group play with peers (item 64) under ten years at the interview,
    friendships (item 65) from ten years. Missing when the age is.
    """
    under_ten = values["adi_age_years"] < 10
    item = values["adi64_past"].where(under_ten, values["adi65_past"])
    return item.where(values["adi_age_years"].notna())


def psqi_latency(values, keys=None):
    """PSQI component 2, sleep latency (0 to 3).

    The minutes to fall asleep count 0 (15 or less), 1 (16 to 30), 2 (31 to
    60) or 3 (more). Item 5a is added, and the sum is cut again: 0 gives 0,
    1 or 2 give 1, 3 or 4 give 2, 5 or 6 give 3.
    """
    minutes = values["psqi_latency"]
    points = (minutes > 15).astype(float) + (minutes > 30) + (minutes > 60) + values["psqi05a"]
    points = points.where(minutes.notna())
    return ((points >= 1).astype(float) + (points >= 3) + (points >= 5)).where(points.notna())


def psqi_efficiency(values, keys=None):
    """PSQI component 4, habitual sleep efficiency (0 to 3).

    The hours asleep over the hours in bed, from the bedtime to the rising
    time across midnight: 85% or more counts 0, 75% to 84% counts 1, 65% to
    74% counts 2, less counts 3.
    """
    in_bed = (values["psqi_rising_time"] - values["psqi_bedtime"]) % 24
    efficiency = 100 * values["psqi_sleep_hours"] / in_bed.where(in_bed > 0)
    points = (efficiency < 85).astype(float) + (efficiency < 75) + (efficiency < 65)
    return points.where(efficiency.notna())


def psqi_disturbances(values, keys=None):
    """PSQI component 5, sleep disturbances (0 to 3).

    The items 5b to 5j are added: 0 counts 0, 1 to 9 count 1, 10 to 18 count
    2, more counts 3. The last item, "another reason", counts 0 when it is
    empty; the eight others must be answered.
    """
    answered = ["psqi05b", "psqi05c", "psqi05d", "psqi05e", "psqi05f", "psqi05g", "psqi05h", "psqi05i"]
    total = values[answered].sum(axis=1) + values["psqi05j"].fillna(0)
    points = (total >= 1).astype(float) + (total >= 10) + (total >= 19)
    return points.where(values[answered].notna().all(axis=1))


def psqi_dysfunction(values, keys=None):
    """PSQI component 7, daytime dysfunction (0 to 3).

    The items 8 and 9 are added: 0 counts 0, 1 or 2 count 1, 3 or 4 count 2,
    5 or 6 count 3.
    """
    total = values["psqi08"] + values["psqi09"]
    points = (total >= 1).astype(float) + (total >= 3) + (total >= 5)
    return points.where(total.notna())


def stroop_interference(values, keys=None):
    """Stroop interference: the colour-word score minus the score predicted from the two other plates.

    The prediction is words x colours / (words + colours), with the scores corrected for age.
    """
    words, colours = values["stroop_word_corrected"], values["stroop_colour_corrected"]
    return values["stroop_colour_word_corrected"] - words * colours / (words + colours)


def medication_name(names):
    """The stem of a medication name: "TERALITHE LP 400 mg, comprimé sécable" gives "TERALITHE LP"."""
    stems = names.str.upper().str.replace(r"\s+\d.*|[,(/*].*", "", regex=True)
    return stems.str.replace(r"\s+", " ", regex=True).str.strip()


def medication_name_plain(names):
    """The stem of a medication name, without its accents: "Mélatonine 2 mg" gives "MELATONINE"."""
    plain = names.str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii")
    return medication_name(plain)

