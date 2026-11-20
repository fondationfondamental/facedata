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

import re

import numpy as np
import pandas as pd


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
    """Bazett's formula: the QT interval divided by the square root of the RR interval, in seconds.

    The RR interval is 60 divided by the heart rate of the ECG where there is
    one: the RR typed in the form does not always fit that heart rate. The
    typed RR is used where the heart rate is missing.
    """
    rr = values["rr_interval"]
    if "ecg_heart_rate" in values:
        rate = values["ecg_heart_rate"]
        rr = (60 / rate).where(rate.notna(), rr)
    return values["qt_interval"] / rr ** 0.5


def sick_leave_more_than_20(values, keys=None):
    """A sick leave in the past year: the stored yes/no, but yes where it says no to more than 20 sick leaves.

    At the DSM-IV inclusions an application script wrote the yes/no from the
    number of sick leaves, and read the answer ">20" as 0 (decision D123). The
    number is then 20, censored on the right.
    """
    stored = values["sick_leave_12m_stored"]
    return stored.mask((stored == 0) & (values["n_sick_leaves_12m"] == 20), 1.0)


def panic_unless_agoraphobia_only(values, keys=None):
    """Panic disorder: the stored box, but missing where only agoraphobia can have ticked it (D151).

    The export ticks the box with ILIKE '%Trouble panique%', which also matches "Agoraphobie sans trouble
    panique": the agoraphobia box is 1 and no panic detail is filled. The twins end in _v0 and _fu.
    """
    end = "_fu" if "panic_disorder_stored_fu" in values else "_v0"
    no_detail = values["panic_onset_age" + end].isna() & values["panic_last_month" + end].isna()
    return values["panic_disorder_stored" + end].mask((values["agoraphobia" + end] == 1) & no_detail)


def rr_differs_from_rate(values):
    """The RR interval typed in the form against the heart rate of the same ECG.

    The two say the same thing: RR x rate / 60 is 1. True where it is under
    0.7 or above 1.3: the typed RR is another quantity.
    """
    product = values["rr_interval"] * values["ecg_heart_rate"] / 60
    return product.notna() & ~product.between(0.7, 1.3)


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
    only be ng/mL (one under 0.2 is mg/L typed in the default unit), and a
    result of 500 or more is mUI/L. In between, the
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
    unit = unit.mask(values < 0.2, "mg/L")            # typed in the default unit of the form, x1000 (D144)
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
    74% counts 2, less counts 3. A bedtime from 6:00 to 17:00 with more than
    16 hours in bed is a bedtime typed on a 12-hour clock (11:00 for 23:00):
    12 hours are added to it (554 BP visits, 3.3%).
    """
    in_bed = (values["psqi_rising_time"] - values["psqi_bedtime"]) % 24
    clock_of_12 = values["psqi_bedtime"].between(6, 17, inclusive="left") & (in_bed > 16)
    in_bed = in_bed.where(~clock_of_12, in_bed - 12)
    efficiency = (100 * values["psqi_sleep_hours"] / in_bed.where(in_bed > 0)).round(6)       # 75.0 and not 74.99999999999999
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



# An amount of a mass, a percentage or units, alone or per volume: the rule of R54 in docs/EXPORT_REQUESTS.md.
STRENGTH = re.compile(r"(?<![0-9] )(?<![0-9.,])([0-9]+(?:[.,][0-9]+)?)\s*(mg|g|µg|mcg|microgrammes?|ui|%)"
                      r"(\s*/\s*(?:[0-9]+(?:[.,][0-9]+)?\s*)?(?:ml|g|dose))?(?![^\W\d_])", re.IGNORECASE)
MILLIGRAMS = {"mg": 1.0, "g": 1000.0, "µg": 0.001, "mcg": 0.001, "microgramme": 0.001, "microgrammes": 0.001}


def strength_in_name(names):
    """The strength written in the name of a product, in mg (DM-14).

    Read only where the name holds exactly one amount, of a mass and not per
    volume: "DEPAKOTE 500 mg, comprimé" gives 500. Several amounts, an amount
    per ml, a percentage or units give nothing.
    """
    def read(name):
        found = STRENGTH.findall(name)
        if len(found) != 1 or found[0][2]:
            return np.nan
        number, unit, per_volume = found[0]
        return float(number.replace(",", ".")) * MILLIGRAMS.get(unit.lower(), np.nan)
    return names.map(read).astype(float)


def strength_used(values):
    """The strength in mg of each medication: the one stored where the form stored one, else the one of the name."""
    stored = values["strength"].fillna("")
    number = stored.str.extract(r"^([0-9]+(?:[.,][0-9]+)?)", expand=False).str.replace(",", ".").astype(float)
    in_mg = number * values["dose_unit"].fillna("").str.lower().map(MILLIGRAMS)
    return in_mg.where(stored != "", strength_in_name(values["medication"].fillna("")))


def daily_dose(values, keys=None):
    """The total daily dose in mg: the strength times the number of units a day (D124)."""
    return strength_used(values) * values["units_per_day"]


def strength_from_name(values, keys=None):
    """1 where the delivered daily dose rests on the strength read from the name, 0 on the stored one."""
    from_name = (values["strength"].fillna("") == "").astype(float)
    return from_name.where(values["daily_dose"].notna())


def end_before_start(values):
    """A treatment whose end date is before its start date."""
    return values["end_date"] < values["start_date"]


def neuropsy_age_used(values, keys):
    """The age that the norms of the neuropsychology tab are read with.

    The age typed in the form where it is within 1 year of the age at the
    visit, else the age at the visit (the rule of norm_age in harmonise.py).
    Missing on the visits that have no conditions form: no test was given.
    """
    typed, age = values["neuropsy_age"], keys["age"]
    used = typed.where(typed.notna() & (age.isna() | ((typed - age).abs() <= 1)), age)
    return used.where(values.notna().any(axis=1))


def cpt3_typed_raw(values):
    """CPT-3: the visit holds raw values in its T-score columns.

    A T-score of the hit reaction time never exceeds 90; the visits where it
    is above 100 hold the raw values of the report (a time in ms). True on
    them, so that a raw value that looks like a T-score (20 to 90) is flagged.
    """
    return values["cpt3_hrt_t_typed"] > 100
