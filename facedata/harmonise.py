"""Harmonise parsed values: versions, units, sign, range, scores, winsorising.

Pipeline steps 4 and 7 to 12 (docs/ARCHITECTURE.md, section 5). Each function
returns the new values and a table of flags.
"""

import numpy as np
import pandas as pd

from facedata.flags import make_flags, stack_flags
from facedata.parse import clean_text
from facedata.tokens import EMPTY_DATE


# ---------------------------------------------------------------- step 4: versions

def detect_version(raw, keys, schema):
    """The edition or form of the instrument used at each visit."""
    version = schema["version"]
    columns = sorted({variable["column"] for variable in schema["variables"].values()})
    has_data = ((raw[columns] != "") & (raw[columns] != EMPTY_DATE)).any(axis=1)
    flags = []
    if "filled" in version:
        result = pd.Series(np.nan, index=raw.index, dtype=object)
        for name, items in reversed(list(version["filled"].items())):   # the first one listed wins
            result = result.mask((raw[items] != "").any(axis=1), name)
    else:
        codes = {code.lower(): name for code, name in version["codes"].items()}
        result = clean_text(raw[version["column"]]).str.lower().map(codes)
        if version.get("level") == "patient":
            result, flags = patient_version(result, keys, version, has_data)
    unknown = has_data & result.isna()
    flags = stack_flags(flags + [make_flags(unknown, version["name"], "version_unknown")])
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


def convert_units(values, labels, name, variable):
    """Bring numbers to the schema's unit, from the unit label and the size of the value."""
    units = variable["units"]
    target = variable["unit"]
    spelling = {}                                      # label as written (lower case) -> unit
    for unit, spec in units.items():
        for label in [unit] + spec.get("aliases", []):
            spelling[label.lower().replace(" ", "")] = unit
    labelled = labels.str.lower().str.replace(" ", "", regex=False).map(spelling)

    fits = pd.DataFrame(index=values.index)            # one True/False column per unit
    factor = {}
    for unit, spec in units.items():
        low, high = spec["expect"]
        fits[unit] = (values >= low) & (values < high)
        factor[unit] = spec["factor"]
    n_fits = fits.sum(axis=1)
    only_fit = fits.idxmax(axis=1).where(n_fits == 1)  # the single unit whose range holds the value
    fits_label = pd.Series(False, index=values.index)
    for unit in units:
        fits_label = fits_label | ((labelled == unit) & fits[unit])

    present = values.notna()
    known = present & labelled.notna()
    other = known & ~fits_label & only_fit.notna()             # the size points to another unit
    guessed = present & labelled.isna() & only_fit.notna()     # no usable label, one unit fits
    unclear = present & labelled.isna() & (n_fits > 1)         # no usable label, several fit

    used = labelled.fillna(target)
    used = used.mask(other | guessed, only_fit)
    as_labelled = values * labelled.map(factor)
    converted = (values * used.map(factor)).where(~unclear)

    low, high = variable.get("range", [-np.inf, np.inf])
    impossible = (as_labelled < low) | (as_labelled > high)
    detail = used.astype(str) + " -> " + target
    said = "label " + labelled.astype(str) + ", read as " + used.astype(str)
    flags = stack_flags([
        make_flags(known & fits_label & (labelled != target), name, "unit_converted", detail),
        make_flags(other & impossible, name, "unit_inferred", said),
        make_flags(other & ~impossible, name, "unit_doubt", said),
        make_flags(guessed, name, "unit_inferred", "no usable label, read as " + used.astype(str)),
        make_flags(unclear, name, "unit_unknown", "no usable label, several units fit"),
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


def find_switch_date(table, scores, wanted):
    """The month before which the standard scores of one centre move the wrong way.

    wanted is -1 or +1: the sign the correlation must have. Returns None when
    the centre never changed convention.
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
        return None
    before = table[table["date"] < best_date]
    moved_the_wrong_way = wanted * mean_correlation(before, scores) < 0
    return best_date if moved_the_wrong_way else None


def fix_sign(values, keys, schema):
    """Bring standard scores to one sign convention.

    Returns the values, the flags and the switch date found in each centre.
    """
    sign = schema["sign"]
    wanted = -1 if sign["relation"] == "negative" else 1
    scores = list(sign["pairs"])
    table = pd.DataFrame({"date": keys["visit_date"], "group": keys[sign["by"]]})
    for score, raw_names in sign["pairs"].items():
        raw_names = [raw_names] if isinstance(raw_names, str) else raw_names
        table[score] = values[score]
        table["raw of " + score] = values[raw_names].sum(axis=1, min_count=len(raw_names))

    usable = table[table[scores].notna().any(axis=1) & table["date"].notna()]
    switch = {}
    for group, rows in usable.groupby("group"):
        date = find_switch_date(rows, scores, wanted)
        if date is not None:
            switch[group] = date
    switch_date = pd.to_datetime(table["group"].map(switch))     # missing where nothing changed

    flags = []
    days_apart = (table["date"] - switch_date).dt.days.abs()
    for score in scores:
        present = values[score].notna()
        before = present & (table["date"] < switch_date)
        doubtful = present & switch_date.notna() & ((days_apart <= 90) | table["date"].isna())
        values[score] = values[score].where(~before, -values[score])
        flags.append(make_flags(before, score, "sign_flipped"))
        flags.append(make_flags(doubtful, score, "sign_doubt", "close to the centre's change of convention"))
    return values, stack_flags(flags), switch


# ---------------------------------------------------------------- step 9: range

def check_range(values, name, variable):
    """A value outside the hard range is impossible: it becomes missing, never clipped."""
    low, high = variable["range"]
    outside = values.notna() & ((values < low) | (values > high))
    detail = "outside " + str(low) + " to " + str(high)
    return values.where(~outside), make_flags(outside, name, "out_of_range", detail)


# ---------------------------------------------------------------- step 10: scores

def compute_scores(values, schema, version=None):
    """Recompute scores from the items and compare them with the stored scores."""
    flags = []
    stored_differs = {}                # score -> rows where the stored score is not the recomputed one
    for name, score in schema.get("scores", {}).items():
        items = score.get("sum") or score.get("mean")
        table = values[items].copy()
        for item in score.get("reverse", []):
            low, high = schema["variables"][item]["range"]
            table[item] = low + high - table[item]
        enough = table.notna().sum(axis=1) >= score.get("min_items", len(items))
        result = table.sum(axis=1) if "sum" in score else table.mean(axis=1)
        result = result.where(enough)
        if "versions" in score:
            result = result.where(version.isin(score["versions"]))
        if "range" in score:
            result, range_flags = check_range(result, name, score)
            flags.append(range_flags)
        values[name] = result
        if "compare" in score:
            stored = values[score["compare"]]
            both = stored.notna() & result.notna()
            stored_differs[name] = both & ((stored - result).abs() > 0.01)
            unexplained = both & ((stored - result - score["compare_offset"]).abs() > 0.01)
            detail = "stored " + stored.astype(str) + ", computed " + result.astype(str)
            flags.append(make_flags(unexplained, name, "score_mismatch", detail))
    for name, variable in schema["variables"].items():
        if "derived_from" in variable:
            source = variable["derived_from"]
            doubtful = values[name].notna() & stored_differs[source]
            flags.append(make_flags(doubtful, name, "derived_doubt", "the stored score it comes from differs from " + source))
    return values, stack_flags(flags)


# ---------------------------------------------------------------- step 11: patient level

def collapse_patient_level(values, keys):
    """One row per patient: the first value that is not missing, in visit order."""
    ordered = values.assign(usubjid=keys["usubjid"], order=keys["visit_order"]).sort_values("order")
    per_patient = ordered.drop(columns="order").groupby("usubjid")
    patients = per_patient.first()
    n_values = per_patient.nunique()
    first_rows = keys.groupby("usubjid").head(1).index       # the flag goes on the patient's first row
    flags = []
    for name in values.columns:
        varying = n_values.index[n_values[name] > 1]
        rows = keys["usubjid"].isin(varying) & keys.index.isin(first_rows)
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
