"""Harmonise parsed values: versions, units, sign, range, scores, winsorising.

Pipeline steps 4 and 7 to 12 (docs/ARCHITECTURE.md, section 5). Each function
returns the new values and a table of flags.
"""

import numpy as np
import pandas as pd

from facedata import custom
from facedata.flags import make_flags, stack_flags
from facedata.parse import PERCENTILE_BAND, band_of_z, clean_text
from facedata.tokens import EMPTY_DATE


# ---------------------------------------------------------------- step 4: versions

def detect_version(raw, keys, schema):
    """The edition or form of the instrument used at each visit."""
    version = schema["version"]
    columns = sorted({column for variable in schema["variables"].values() for column in variable["columns"]})
    has_data = ((raw[columns] != "") & (raw[columns] != EMPTY_DATE)).any(axis=1)
    flags = []
    if "filled" in version:
        result = pd.Series(np.nan, index=raw.index, dtype=object)
        for name, items in reversed(list(version["filled"].items())):   # the first one listed wins
            result = result.mask((raw[items] != "").any(axis=1), name)
        result = result.where(has_data)                  # the instrument was not administered: no version
    elif "age" in version:                               # a child form and an adult form in the same columns
        result = pd.Series(np.nan, index=raw.index, dtype=object)
        for name, (youngest, oldest) in version["age"].items():
            result = result.mask((keys["age"] >= float(youngest)) & (keys["age"] < float(oldest)), name)
        result = result.where(has_data)
    else:
        codes = {code.lower(): name for code, name in version["codes"].items()}
        result = clean_text(raw[version["column"]]).str.lower().map(codes)
        if version.get("level") == "patient":
            result, flags = patient_version(result, keys, version, has_data)
    unknown = has_data & result.isna()
    # An edition that did not exist before a day: an earlier visit has no version.
    too_early = pd.Series(False, index=raw.index)
    for name, first_day in version.get("since", {}).items():
        too_early = too_early | ((result == name) & (keys["visit_date"] < pd.Timestamp(first_day)))
    result = result.mask(too_early)
    flags = stack_flags(flags + [make_flags(unknown, version["name"], "version_unknown"),
                                 make_flags(too_early, version["name"], "version_unknown",
                                            "dated before the form came into use")])
    return result, flags


def patient_version(written, keys, version, has_data):
    """Version of each visit when it is recorded once per patient (SCHEMA_SPEC, section 7)."""
    name = version["name"]
    result = written.copy()
    flags = []
    # Rule 2: follow-up visits from a given date.
    for edition, start in version.get("follow_up", {}).items():
        is_late = (keys["visit_month"] > 0) & (keys["visit_date"] >= pd.Timestamp(start))
        result = result.mask(written.isna() & is_late, edition)
    # Rule 3: the value of the patient's earliest visit that has one.
    known = keys.assign(written=written).dropna(subset=["written"]).sort_values("visit_order")
    per_patient = known.groupby("usubjid")["written"]
    result = result.fillna(keys["usubjid"].map(per_patient.first()))
    varies = keys["usubjid"].map(per_patient.nunique()) > 1
    flags.append(make_flags(varies & written.notna(), name, "patient_value_varies"))
    # Rule 4: no value at all: decided by the date of the patient's first visit.
    first_date = keys.groupby("usubjid")["visit_date"].transform("min")
    for edition, (start, end) in version.get("by_inclusion_date", {}).items():
        inferred = result.isna() & first_date.between(pd.Timestamp(start), pd.Timestamp(end))
        result = result.mask(inferred, edition)
        flags.append(make_flags(inferred & has_data, name, "version_inferred", "from the inclusion date"))
    return result, flags


# ---------------------------------------------------------------- step 7: units

def censoring_from_units(cens, labels, name, variable):
    """Some extractions write the censoring mark in the unit column ("inf" means "<")."""
    side = labels.str.lower().map(variable.get("censor_units", {}))
    left = (side == "left") & (cens == 0)
    right = (side == "right") & (cens == 0)
    cens = cens.mask(left, -1).mask(right, 1)
    flags = stack_flags([
        make_flags(left, name, "censored_left", "mark in the unit column"),
        make_flags(right, name, "censored_right", "mark in the unit column"),
    ])
    return cens, flags


def pick(table, names):
    """For each row, the value of the column whose name is given (missing where no name is)."""
    result = pd.Series(np.nan, index=table.index)
    for column in table.columns:
        result = result.mask(names == column, table[column])
    return result


def convert_units(values, labels, name, variable, keys=None, wholes=None):
    """Bring numbers to the schema's unit, from the unit label and the size of the value.

    keys: the key columns, for a unit rule. wholes: the numbers of the
    instrument read so far, for a unit that is a percentage of one of them.
    """
    units = variable["units"]
    target = variable["unit"]
    spelling = {}                                      # label as written (lower case) -> unit
    for unit, spec in units.items():
        for label in [unit] + spec.get("aliases", []):
            spelling[label.lower().replace(" ", "")] = unit
    labelled = labels.str.lower().str.replace(" ", "", regex=False).map(spelling)

    fits = pd.DataFrame(index=values.index)            # one True/False column per unit
    factor = pd.DataFrame(index=values.index)          # and the factor of each unit, row by row
    for unit, spec in units.items():
        low, high = spec["expect"]
        fits[unit] = (values >= low) & (values < high)
        if "percent_of" in spec:                       # a percentage of another result of the visit
            factor[unit] = wholes[spec["percent_of"]] / 100
        else:
            factor[unit] = spec["factor"]
    n_fits = fits.sum(axis=1)
    only_fit = fits.idxmax(axis=1).where(n_fits == 1)  # the single unit whose range holds the value
    if "unit_rule" in variable:                        # custom.py decides for the values with no usable label
        ruled = getattr(custom, variable["unit_rule"])(values.where(labelled.isna()), keys)
        only_fit = only_fit.mask(labelled.isna() & ruled.notna(), ruled)
    fits_label = pd.Series(False, index=values.index)
    for unit in units:
        fits_label = fits_label | ((labelled == unit) & fits[unit])

    present = values.notna()
    known = present & labelled.notna()
    other = known & ~fits_label & only_fit.notna()             # the size points to another unit
    guessed = present & labelled.isna() & only_fit.notna()     # no usable label, one unit is found
    unclear = present & labelled.isna() & only_fit.isna() & (n_fits > 1)   # no usable label, several fit

    used = labelled.fillna(target)
    used = used.mask(other | guessed, only_fit)
    as_labelled = values * pick(factor, labelled)
    converted = (values * pick(factor, used)).where(~unclear)
    done = converted.notna()
    no_whole = present & ~unclear & ~done              # a percentage of a result that is missing

    low, high = variable.get("range", [-np.inf, np.inf])
    impossible = (as_labelled < low) | (as_labelled > high)
    detail = used.astype(str) + " -> " + target
    said = "label " + labelled.astype(str) + ", read as " + used.astype(str)
    flags = stack_flags([
        make_flags(done & known & fits_label & (labelled != target), name, "unit_converted", detail),
        make_flags(done & other & impossible, name, "unit_inferred", said),
        make_flags(done & other & ~impossible, name, "unit_doubt", said),
        # With no label at all, a value that is simply in the schema's unit needs no flag.
        make_flags(done & guessed & ((labels != "") | (used != target)), name, "unit_inferred",
                   "no usable label, read as " + used.astype(str)),
        make_flags(unclear, name, "unit_unknown", "no usable label, several units fit"),
        make_flags(no_whole, name, "unit_unknown", "read as " + used.astype(str) + " of a missing value"),
    ])
    return converted, flags


# ---------------------------------------------------------------- step 8: sign conventions

def rank_correlation(a, b):
    """Spearman correlation: the usual correlation, computed on the ranks."""
    both = a.notna() & b.notna()
    if both.sum() < 3:
        return np.nan
    return a[both].rank().corr(b[both].rank())


def mean_correlation(table, scores, flip_before=None):
    """Average over the pairs of the rank correlation between raw value and standard score.

    With flip_before, the standard scores dated before it are multiplied by -1 first.
    """
    results = []
    for score in scores:
        standard = table[score]
        if flip_before is not None:
            standard = standard.where(table["date"] >= flip_before, -standard)
        results.append(rank_correlation(table["raw of " + score], standard))
    results = [result for result in results if not np.isnan(result)]
    return np.mean(results) if results else np.nan


# A centre is flipped only if, before the switch, its scores follow the wrong sign this strongly (mean rank correlation).
CLEAR_SIGN = 0.5


def find_switch_date(table, scores, wanted):
    """The month before which the standard scores of one centre move the wrong way.

    wanted is -1 or +1: the sign the correlation must have. Returns the month
    (None when the centre never changed convention) and whether the scores
    before it clearly follow the other convention.
    """
    best_date = None
    best = wanted * mean_correlation(table, scores)
    last_month = table["date"].max() + pd.offsets.MonthBegin(1)
    for month in pd.date_range(table["date"].min(), last_month, freq="MS"):
        if (table["date"] < month).sum() < 10:
            continue
        agreement = wanted * mean_correlation(table, scores, flip_before=month)
        if np.isnan(agreement):
            continue
        if np.isnan(best) or agreement > best + 1e-9:
            best_date, best = month, agreement
    if best_date is None:
        return None, False
    before = table[table["date"] < best_date]
    agreement_before = wanted * mean_correlation(before, scores)
    if not agreement_before < 0:                       # the scores before it do not move the wrong way
        return None, False
    return best_date, agreement_before <= -CLEAR_SIGN


def fix_sign(values, keys, schema):
    """Bring standard scores to one sign convention.

    Returns the values, the flags and the switch date found in each centre.
    """
    sign = schema["sign"]
    if "before" in sign:                               # the day of the change is known: nothing to search
        return turn_before(values, keys, schema)
    wanted = -1 if sign["relation"] == "negative" else 1
    scores = list(sign["pairs"])
    table = pd.DataFrame({"date": keys["visit_date"], "group": keys[sign["by"]]})
    for score, raw_names in sign["pairs"].items():
        raw_names = [raw_names] if isinstance(raw_names, str) else raw_names
        table[score] = values[score]
        table["raw of " + score] = values[raw_names].sum(axis=1, min_count=len(raw_names))

    usable = table[table[scores].notna().any(axis=1) & table["date"].notna()]
    switch, unsure = {}, {}
    for group, rows in usable.groupby("group"):
        date, is_clear = find_switch_date(rows, scores, wanted)
        if date is not None and is_clear:
            switch[group] = date
        elif date is not None:                         # a mixture of the two conventions: nothing is flipped
            unsure[group] = date
    switch_date = pd.to_datetime(table["group"].map(switch))     # missing where nothing changed
    unsure_date = pd.to_datetime(table["group"].map(unsure))

    flags = []
    days_apart = (table["date"] - switch_date).dt.days.abs()
    for score in scores:
        present = values[score].notna()
        before = present & (table["date"] < switch_date)
        doubtful = present & switch_date.notna() & ((days_apart <= 90) | table["date"].isna())
        values[score] = values[score].where(~before, -values[score])
        flags.append(make_flags(before, score, "sign_flipped"))
        flags.append(make_flags(doubtful, score, "sign_doubt", "close to the centre's change of convention"))
        maybe_old = present & (table["date"] < unsure_date)
        flags.append(make_flags(maybe_old, score, "sign_doubt", "the early scores of the centre may follow the other convention"))
    return values, stack_flags(flags), switch


def turn_before(values, keys, schema):
    """Turn the variables of the visits dated before a known change of direction.

    A variable with a range is turned around its middle (min + max - value);
    one without a range changes sign. Returns the values, the flags and no
    switch date.
    """
    sign = schema["sign"]
    date = keys["visit_date"]
    close = (date - sign["before"]).dt.days.abs() <= 90
    flags = []
    for name in sign["turn"]:
        present = values[name].notna()
        before = present & (date < sign["before"])
        middle = sum(schema["variables"][name].get("range", [0, 0]))
        values[name] = values[name].where(~before, middle - values[name])
        flags.append(make_flags(before, name, "sign_flipped"))
        flags.append(make_flags(present & (close | date.isna()), name, "sign_doubt", "close to the change of form"))
    return values, stack_flags(flags), {}


# ---------------------------------------------------------------- step 9: range

def check_range(values, name, variable):
    """A value outside the hard range is impossible: it becomes missing, never clipped."""
    low, high = variable["range"]
    outside = values.notna() & ((values < low) | (values > high))
    if isinstance(low, pd.Timestamp):
        low, high = low.date(), high.date()
    detail = "outside " + str(low) + " to " + str(high)
    return values.where(~outside), make_flags(outside, name, "out_of_range", detail)


def doubt_period(values, dates, name, doubt):
    """Flag the values of the visits dated in a period in which the column is not reliable.

    The values are kept. With doubt["values"], only those values are flagged.
    With doubt["remove"], the flagged values are not delivered.
    """
    first, last = doubt["period"]
    doubtful = values.notna() & dates.between(first, last)
    if "values" in doubt:
        doubtful = doubtful & values.isin(doubt["values"])
    if doubt.get("remove"):
        return values.where(~doubtful), make_flags(doubtful, name, "period_removed", doubt.get("note", ""))
    return values, make_flags(doubtful, name, "period_doubt", doubt.get("note", ""))


# ---------------------------------------------------------------- step 10: scores

def combine_items(values, score, schema):
    """A score that is the sum, the mean, the highest or the lowest of its items, some of them reversed first.

    points: {answer: points}, the answers that count other points than their own
    value. minus: variables subtracted from a sum. scale: [factor, offset],
    applied to the sum or the mean. floor: the lowest value the score can take.
    """
    items = items_of(score)
    table = values[items].copy()
    for item in score.get("reverse", []):
        low, high = schema["variables"][item]["range"]
        table[item] = low + high - table[item]
    if "points" in score:
        table = table.replace(score["points"])
    enough = table.notna().sum(axis=1) >= score.get("min_items", len(items))
    if "max" in score:
        result = table.max(axis=1)
    elif "min" in score:
        result = table.min(axis=1)
    else:
        result = table.sum(axis=1) if "sum" in score else table.mean(axis=1)
    if "minus" in score:
        taken_off = values[score["minus"]]
        enough = enough & taken_off.notna().all(axis=1)
        result = result - taken_off.sum(axis=1)
    if "scale" in score:
        factor, offset = score["scale"]
        result = result * factor + offset
    if "floor" in score:
        result = result.clip(lower=score["floor"])
    return result.where(enough)


def items_of(score):
    """The variables that a score adds up, averages or takes the highest or the lowest of (none for a table or a function)."""
    return score.get("sum") or score.get("mean") or score.get("max") or score.get("min") or []


def keep_stored_score(result, values, score):
    """Where none of the items of a score is recorded, the score as stored is delivered.

    The form lets a clinician type a total alone. Where only some items are
    missing the score stays missing: the stored total may be a partial sum.
    Returns the score and the rows where it is the stored one.
    """
    stored = values[score["otherwise"]]
    typed_alone = values[items_of(score)].isna().all(axis=1) & stored.notna()
    return result.where(~typed_alone, stored), typed_alone


def look_up(raw, age, table, name, by=None):
    """Read a standard score in a norm table, from a raw score and the age at the visit.

    table: one line per cell (age_min, age_max, raw_min, raw_max, value), or
    None when the table was not found. by: a second variable the table
    depends on (columns by_min and by_max), such as the years of education.
    A table of percentile bands can have a column cens: 1 where the raw
    score only says "this band or a higher one".

    Returns the values, the censoring and the flags.
    """
    result = pd.Series(np.nan, index=raw.index)
    cens = pd.Series(0, index=raw.index)
    if table is not None:
        years = np.floor(age)                          # completed years
        for line in table.itertuples():
            fits = years.between(line.age_min, line.age_max) & raw.between(line.raw_min, line.raw_max)
            if by is not None:
                fits = fits & np.floor(by).between(line.by_min, line.by_max)
            result = result.mask(fits, line.value)
            cens = cens.mask(fits, getattr(line, "cens", 0))
    detail = "the norm table was not found" if table is None else "nothing in the norm table for this visit"
    flags = stack_flags([
        make_flags(raw.notna() & result.isna(), name, "norm_missing", detail),
        make_flags(cens == 1, name, "censored_right", "this band or a higher one"),
    ])
    return result, cens, flags


def band_from_table(text, values, cens, flags, name, variable, age, others, norms):
    """A band that the EMR read in a norm table is read again there, from the raw score.

    Only the cells that hold a percentile are concerned; what the cell said
    is dropped. A band computed from a z-score stays as it is. others: the
    values of the instrument read so far.
    """
    is_percentile = text.str.fullmatch(PERCENTILE_BAND)
    raw = others[variable["from"]].where(is_percentile)
    looked, looked_cens, lookup_flags = look_up(raw, age, (norms or {}).get(variable["lookup"]), name)
    values = values.mask(is_percentile, looked)
    cens = cens.mask(is_percentile, looked_cens)
    flags = stack_flags([
        flags[~flags["row"].isin(text.index[is_percentile])],
        lookup_flags[lookup_flags["flag"] == "censored_right"],
        make_flags(is_percentile & values.isna(), name, "norm_missing", "no band can be read in the norm table"),
    ])
    return values, cens, flags


def regress(raw, age, table, terms, name):
    """A z-score from the regression of a norm table: (raw score - expected score) / sd.

    table: one line per age group (age_min, age_max, intercept, age, one
    column per term, sd), or None when the table was not found. terms:
    {column of the table: values}, the other variables of the regression,
    such as the years of education. An age that is in no line of the table
    gives no z-score and no flag: the norm has no regression for that age.

    Returns the z-scores and the flags.
    """
    result = pd.Series(np.nan, index=raw.index)
    in_table = pd.Series(table is None, index=raw.index)       # with no table, every raw score is flagged
    if table is not None:
        years = np.floor(age)                          # completed years
        for line in table.itertuples():
            fits = years.between(line.age_min, line.age_max)
            expected = line.intercept + line.age * years
            for term, others in terms.items():
                expected = expected + getattr(line, term) * others
            result = result.mask(fits, (raw - expected) / line.sd)
            in_table = in_table | fits
    detail = "the norm table was not found" if table is None else "a variable of the regression is missing"
    flags = make_flags(raw.notna() & in_table & result.isna(), name, "norm_missing", detail)
    return result.round(2), flags


def complete_with_z(band, flags, z, limits, name):
    """Where no band was read in a norm table, the band that the z-score has under the normal law.

    band, flags: what the norm table gave. The rows filled here get
    band_from_z and lose their norm_missing.
    """
    from_z = band.isna() & z.notna()
    band = band.mask(from_z, band_of_z(z, limits))
    filled = flags["row"].isin(band.index[from_z]) & (flags["flag"] == "norm_missing")
    return band, stack_flags([flags[~filled], make_flags(from_z, name, "band_from_z", "z-score " + z.astype(str))])


def compute_scores(values, schema, version=None, age=None, norms=None, cens=None, keys=None):
    """Recompute scores from the items and compare them with the stored scores.

    age and norms (the norm tables) are needed only by scores read in a norm
    table or computed with its regression. cens: the censoring table of the
    instrument; a band read in a norm table writes its own column there. keys: the key columns, for the few
    custom scores that need the visit or the patient.
    """
    flags = []
    stored_differs = {}                # score -> rows where the stored score is not the recomputed one
    as_stored = {}                     # score -> rows where it is the stored score, or is built on one
    specs = {**schema["variables"], **schema.get("scores", {})}
    for name, score in schema.get("scores", {}).items():
        if "lookup" in score:
            by = values[score["by"]] if "by" in score else None
            table = (norms or {}).get(score["lookup"])
            result, censoring, lookup_flags = look_up(values[score["from"]], age, table, name, by)
            if "band_of" in score:                     # an age the table does not have: the band of the z-score
                result, lookup_flags = complete_with_z(result, lookup_flags, values[score["band_of"]], score["limits"], name)
            flags.append(lookup_flags)
            if cens is not None and (censoring != 0).any():
                cens[name] = censoring
        elif "regression" in score:                    # a z-score from the regression of a norm table
            terms = {term: values[variable] for term, variable in score["with"].items()}
            table = (norms or {}).get(score["regression"])
            result, regression_flags = regress(values[score["from"]], age, table, terms, name)
            flags.append(regression_flags)
        elif "band_of" in score:                       # the band of a z-score, with no table
            nothing = pd.Series(np.nan, index=values.index)
            result, band_flags = complete_with_z(nothing, stack_flags([]), values[score["band_of"]], score["limits"], name)
            flags.append(band_flags)
        elif "custom" in score:                        # a formula written as a function of custom.py
            result = getattr(custom, score["custom"])(values, keys)
        else:
            result = combine_items(values, score, schema)
        if "versions" in score:
            result = result.where(version.isin(score["versions"]))
        if "range" in score:
            result, range_flags = check_range(result, name, score)
            flags.append(range_flags)
        parts = [part for part in items_of(score) if part in as_stored]
        if parts:                                      # built on scores, some of them delivered as stored
            as_stored[name] = pd.concat([as_stored[part] for part in parts], axis=1).any(axis=1) & result.notna()
            flags.append(make_flags(as_stored[name], name, "score_as_stored", "built on a score delivered as stored"))
        if "otherwise" in score:                       # a score typed without any of its items
            result, typed_alone = keep_stored_score(result, values, score)
            as_stored[name] = typed_alone | as_stored.get(name, False)
            flags.append(make_flags(typed_alone, name, "score_as_stored", "none of its items is recorded"))
        values[name] = result
        if "compare" in score:
            stored = values[score["compare"]]
            both = stored.notna() & result.notna()
            tolerance = score.get("compare_tolerance", 0.01)
            stored_differs[name] = both & ((stored - result).abs() > tolerance)
            unexplained = both & ((stored - result - score["compare_offset"]).abs() > tolerance)
            detail = "stored " + stored.astype(str) + ", computed " + result.astype(str)
            stored_is_delivered = specs[score["compare"]].get("keep", True)
            is_check = not score.get("keep", True)
            # A check that is not delivered speaks about the stored value: the flag goes where the analyst looks,
            # unless that value is derived from the check and gets derived_doubt below.
            doubted_below = specs[score["compare"]].get("derived_from") == name
            where = score["compare"] if stored_is_delivered and is_check and not doubted_below else name
            flags.append(make_flags(unexplained, where, "score_mismatch", detail))
            if not is_check and not stored_is_delivered:     # neither is delivered on these rows: say what was stored
                alone = stored.notna() & result.isna()
                flags.append(make_flags(alone, name, "score_not_recomputed", "stored " + stored.astype(str)))
    for name, variable in schema["variables"].items():
        if "derived_from" in variable:
            source = variable["derived_from"]
            if source in stored_differs:                 # a score: its stored value is wrong
                doubtful = values[name].notna() & stored_differs[source]
                detail = "the stored score it comes from differs from " + source
            else:                                        # a variable: it is empty
                doubtful = values[name].notna() & values[source].isna()
                detail = "the value it comes from, " + source + ", is empty"
            flags.append(make_flags(doubtful, name, "derived_doubt", detail))
    return values, stack_flags(flags)


# ---------------------------------------------------------------- step 11: patient level

def first_rows(keys):
    """The row of each patient's first visit: a Series, patient -> row number."""
    first = keys.sort_values("visit_order").groupby("usubjid").head(1)
    return pd.Series(first.index, index=first["usubjid"])


def collapse_patient_level(values, keys):
    """One row per patient: the first value that is not missing, in visit order."""
    ordered = values.assign(usubjid=keys["usubjid"], order=keys["visit_order"]).sort_values("order")
    per_patient = ordered.drop(columns="order").groupby("usubjid")
    patients = per_patient.first()
    n_values = per_patient.nunique()
    is_first = keys.index.isin(first_rows(keys))             # the flag goes on the patient's first visit
    flags = []
    for name in values.columns:
        varying = n_values.index[n_values[name] > 1]
        rows = keys["usubjid"].isin(varying) & is_first
        flags.append(make_flags(rows, name, "patient_value_varies"))
    return patients.reset_index(), stack_flags(flags)


# ---------------------------------------------------------------- step 12: winsorising

def winsorise(values, name, variable, limits=None):
    """Clip the tails of a continuous variable.

    limits: (low, high) from an earlier load, to reuse them on new data.
    Returns the values, the flags and the limits used.
    """
    rule = variable.get("winsor", [0.01, 0.99])
    if rule is False or values.notna().sum() == 0:
        return values, stack_flags([]), (np.nan, np.nan)
    if limits is not None:
        low, high = limits
    elif isinstance(rule, dict):
        low, high = rule["limits"]
    else:
        # "nearest" makes each limit a value that was really observed
        low = values.quantile(rule[0], interpolation="nearest")
        high = values.quantile(rule[1], interpolation="nearest")
    clipped = values.clip(low, high)
    changed = values.notna() & (clipped != values)
    detail = "limits " + str(round(low, 4)) + " to " + str(round(high, 4))
    return clipped, make_flags(changed, name, "winsorised", detail), (low, high)
