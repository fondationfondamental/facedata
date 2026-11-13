"""Turn the text of one raw column into clean values (pipeline steps 3, 5 and 6).

Every function takes the text of one column (a Series of strings) and returns
the cleaned values and a table of flags.
"""

import html
from math import erf

import numpy as np
import pandas as pd

from facedata.flags import make_flags, stack_flags
from facedata.tokens import EMPTY_DATE, MISSING_TOKENS, PLACEHOLDER_DATES

# An optional censoring mark, an optional sign, digits with a decimal point or
# comma (".45" is read as 0.45), then an optional trailing dot and an optional % sign.
NUMBER = r"^([<>]=?)?\s*([+-]?)\s*(\d+(?:[.,]\d+)?|[.,]\d+)\.?\s*%?$"
# The same number written the usual way: nothing to repair.
PLAIN_NUMBER = r"([<>]=?\s*)?[+-]?\d+(\.\d+)?"
# A band of values written with its two ends: "60-51", "41 - 50".
BAND = r"^(\d+(?:[.,]\d+)?)\s*[-_]\s*(\d+(?:[.,]\d+)?)$"
# A percentile band: an optional < or >, a whole number, and perhaps a second one: "25 - 50", ">95", "50".
# Some are written "[25-50]", "25<50" or ">=75".
PERCENTILE_BAND = r"\[?([<>≥≤]?)=?\s*(\d+)(?:\s*[-_<]\s*(\d+))?\]?"
# A z-score: a number written with a decimal point, such as "-0.19" or "1.00".
Z_SCORE = r"[+-]?\d*[.,]\d+"


def clean_text(column):
    """Step 3. Repair text damage that does not change the meaning."""
    text = column.str.strip()
    text = text.str.replace("\\'", "'", regex=False)
    text = text.str.replace("\\r\\n", " ", regex=False)
    text = text.str.replace("\\n", " ", regex=False)
    has_entity = text.str.contains("&", regex=False)
    text = text.where(~has_entity, text.map(html.unescape))
    return text.str.strip()


def split_missing(text, name, variable):
    """Step 5. Empty the cells that hold a missing code or a placeholder date."""
    tokens = dict(MISSING_TOKENS)
    for token, reason in variable.get("missing", {}).items():
        tokens[token.lower()] = reason
    for code in variable.get("codes", {}):
        tokens.pop(code.lower(), None)             # a code the variable lists is a value
    reason = text.str.lower().map(tokens)          # missing where the cell is not a missing code
    is_missing = reason.notna()
    is_placeholder = text.isin(PLACEHOLDER_DATES)
    flags = stack_flags([
        make_flags(is_missing, name, "missing_code", reason),
        make_flags(is_placeholder, name, "date_placeholder"),
    ])
    keep = ~is_missing & ~is_placeholder & (text != EMPTY_DATE)
    return text.where(keep, ""), flags


def read_bands(text, name):
    """A cell that holds a band ("60-51") is read as the middle of the band (55.5)."""
    ends = text.str.extract(BAND)
    one_end = pd.to_numeric(ends[0].str.replace(",", ".", regex=False), errors="coerce")
    other_end = pd.to_numeric(ends[1].str.replace(",", ".", regex=False), errors="coerce")
    is_band = one_end.notna() & other_end.notna()
    middle = ((one_end + other_end) / 2).astype(str)
    return text.where(~is_band, middle), make_flags(is_band, name, "band_middle", "band " + text)


def parse_number(text, name, variable):
    """Text to numbers. Also returns the censoring: -1 for "<5", +1 for ">5", else 0."""
    band_flags = stack_flags([])
    if variable.get("bands") == "middle":
        text, band_flags = read_bands(text, name)
    parts = text.str.extract(NUMBER)               # columns 0, 1, 2: mark, sign, digits
    digits = parts[2].str.replace(",", ".", regex=False)
    values = pd.to_numeric(parts[1] + digits, errors="coerce")
    mark = parts[0].fillna("")
    cens = pd.Series(0, index=text.index)
    cens = cens.mask(mark.str.startswith("<"), -1)
    cens = cens.mask(mark.str.startswith(">"), 1)
    repaired = values.notna() & ~text.str.fullmatch(PLAIN_NUMBER)
    limit = "limit " + values.astype(str)
    flags = stack_flags([
        band_flags,
        make_flags(repaired, name, "format_repaired"),
        make_flags(cens == -1, name, "censored_left", limit),
        make_flags(cens == 1, name, "censored_right", limit),
        make_flags((text != "") & values.isna(), name, "unparsed"),
    ])
    return values, cens, flags


def own_cells(text, variable):
    """A raw column shared by a percentile band and a z-score: keep the cells of this variable.

    A percentile is written as a band or a whole number, a z-score with a
    decimal point. Everything that is not a band belongs to the number. A
    band that has z_range also takes the z-scores, to turn them into bands.
    """
    is_band = text.str.fullmatch(PERCENTILE_BAND)
    if variable["type"] == "band" and "z_range" in variable:
        return text
    if variable["type"] == "band":
        return text.where(is_band, "")
    return text.where(~is_band, "")


def band_of_z(z, limits):
    """The band a z-score has under the normal law: the lower limit of the band, 0 under the first limit."""
    percent = 50 * (1 + (z / 2 ** 0.5).map(erf))       # share of the normal law that lies under z
    band = pd.Series(0.0, index=z.index)
    for limit in limits:
        band = band.mask(percent >= limit, limit)
    return band.where(z.notna())


def parse_band(text, name, variable):
    """Text to the lower limit of a percentile band (SCHEMA_SPEC, section 6).

    "25 - 50" gives 25, "50" gives 50, ">95" gives 95 and "<5" gives 0. Also
    returns the censoring: +1 for "this band or a higher one" (">10"), -1
    for "this band or a lower one" ("<10"). With z_range, a cell that holds a
    z-score is turned into the band it has under the normal law.
    """
    limits = variable["limits"]
    below = dict(zip(limits, [0.0] + limits))          # the limit just under each limit
    above = dict(zip([0.0] + limits, limits + [100.0]))    # where the band that starts at a limit ends
    parts = text.str.extract("^" + PERCENTILE_BAND + "$")  # columns 0, 1, 2: mark, first number, second number
    first, second = pd.to_numeric(parts[1]), pd.to_numeric(parts[2])
    low = first.where(second.isna(), np.minimum(first, second))
    high = first.where(second.isna(), np.maximum(first, second))
    mark = parts[0].fillna("").replace({"≥": ">", "≤": "<"})
    two_ends = second.notna() & (mark == "") & low.isin(above) & high.isin(limits + [100.0]) & (low < high)
    one_number = second.isna() & low.isin(limits)

    values = low.where(two_ends | one_number)
    is_less = one_number & (mark == "<")
    values = values.mask(is_less, low.map(below))      # "<10" is the band just under 10
    cens = pd.Series(0, index=text.index)
    cens = cens.mask(one_number & (mark == ">") & (low != limits[-1]), 1)
    cens = cens.mask(two_ends & (high != low.map(above)), 1)
    cens = cens.mask(is_less & (low != limits[0]), -1)
    z = pd.Series(np.nan, index=text.index)
    if "z_range" in variable:                          # the column also holds z-scores
        z = pd.to_numeric(text.where(text.str.fullmatch(Z_SCORE)).str.replace(",", ".", regex=False))
    low_z, high_z = variable.get("z_range", [0.0, 0.0])
    usable = z.between(low_z, high_z)
    values = values.mask(usable, band_of_z(z, limits))
    said = "band " + text
    flags = stack_flags([
        make_flags(cens == 1, name, "censored_right", said + ": this band or a higher one"),
        make_flags(cens == -1, name, "censored_left", said + ": this band or a lower one"),
        make_flags(usable, name, "band_from_z", "z-score " + text),
        make_flags(z.notna() & ~usable, name, "out_of_range", "z-score outside " + str(low_z) + " to " + str(high_z)),
        make_flags((text != "") & values.isna() & z.isna(), name, "unparsed"),
    ])
    return values, cens, flags


def parse_item(text, name, variable):
    """Text to whole numbers (questionnaire items, bounded scores)."""
    values, cens, flags = parse_number(text, name, variable)
    not_whole = values.notna() & ((values % 1 != 0) | (cens != 0))
    flags = flags[~flags["row"].isin(not_whole.index[not_whole])]
    flags = stack_flags([flags, make_flags(not_whole, name, "unparsed", "not a whole number")])
    return values.where(~not_whole), flags


def parse_category(text, name, variable):
    """Text to harmonised labels, through the variable's codes."""
    codes = {}
    for code, label in variable["codes"].items():
        codes[code.strip().lower()] = label
    values = text.str.lower().map(codes)
    unknown = (text != "") & values.isna()
    return values, make_flags(unknown, name, "unknown_code")


def parse_date(text, name, variable):
    """YYYY-MM-DD to dates. An unknown day or month becomes the middle of the period."""
    values = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
    no_day = text.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])-00")
    no_month = text.str.fullmatch(r"\d{4}-00-00")
    mid_month = pd.to_datetime(text.str[:8] + "15", format="%Y-%m-%d", errors="coerce")
    mid_year = pd.to_datetime(text.str[:4] + "-07-01", format="%Y-%m-%d", errors="coerce")
    values = values.where(~no_day, mid_month)
    values = values.where(~no_month, mid_year)
    flags = stack_flags([
        make_flags((no_day | no_month) & values.notna(), name, "date_partial"),
        make_flags((text != "") & values.isna(), name, "unparsed"),
    ])
    return values, flags


def parse_time(text, name, variable):
    """HH:MM to hours (12:30 -> 12.5)."""
    parts = text.str.extract(r"^(\d{1,2}):(\d{2})$")
    values = pd.to_numeric(parts[0], errors="coerce") + pd.to_numeric(parts[1], errors="coerce") / 60
    return values, make_flags((text != "") & values.isna(), name, "unparsed")


def recode(text, variable):
    """Replace the cells that hold one of the variable's codes by the code's value ("Y" becomes "1")."""
    codes = {}
    for code, value in variable["codes"].items():
        codes[code.strip().lower()] = value
    return text.str.lower().map(codes).fillna(text)


def parse_column(text, name, variable):
    """Step 6. Parse one column according to the variable's type.

    Returns the values, the censoring (0 everywhere except for numbers and bands) and
    the flags.
    """
    kind = variable["type"]
    no_cens = pd.Series(0, index=text.index)
    if kind in ("number", "item") and "codes" in variable:
        text = recode(text, variable)                  # answers written as letters, counted as numbers
    if kind == "number":
        return parse_number(text, name, variable)
    if kind == "band":
        return parse_band(text, name, variable)
    if kind == "item":
        values, flags = parse_item(text, name, variable)
    elif kind == "category":
        values, flags = parse_category(text, name, variable)
    elif kind == "date":
        values, flags = parse_date(text, name, variable)
    elif kind == "time":
        values, flags = parse_time(text, name, variable)
    else:
        values, flags = text.where(text != ""), stack_flags([])        # free text: nothing to check
    return values, no_cens, flags
