"""Turn the text of one raw column into clean values (pipeline steps 3, 5 and 6).

Every function takes the text of one column (a Series of strings) and returns
the cleaned values and a table of flags.
"""

import html

import pandas as pd

from facedata.flags import make_flags, stack_flags
from facedata.tokens import EMPTY_DATE, MISSING_TOKENS, PLACEHOLDER_DATES

# An optional censoring mark, an optional sign, digits with a decimal point or
# comma, then an optional trailing dot and an optional % sign.
NUMBER = r"^([<>]=?)?\s*([+-]?)\s*(\d+(?:[.,]\d+)?)\.?\s*%?$"
# The same number written the usual way: nothing to repair.
PLAIN_NUMBER = r"([<>]=?\s*)?[+-]?\d+(\.\d+)?"


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


def parse_number(text, name, variable):
    """Text to numbers. Also returns the censoring: -1 for "<5", +1 for ">5", else 0."""
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
        make_flags(repaired, name, "format_repaired"),
        make_flags(cens == -1, name, "censored_left", limit),
        make_flags(cens == 1, name, "censored_right", limit),
        make_flags((text != "") & values.isna(), name, "unparsed"),
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


def parse_column(text, name, variable):
    """Step 6. Parse one column according to the variable's type.

    Returns the values, the censoring (0 everywhere except for numbers) and
    the flags.
    """
    kind = variable["type"]
    no_cens = pd.Series(0, index=text.index)
    if kind == "number":
        return parse_number(text, name, variable)
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
