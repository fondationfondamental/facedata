"""Steps 3, 5 and 6: text repairs, missing codes and parsing."""

import pandas as pd

from facedata.parse import (clean_text, parse_category, parse_column, parse_date, parse_item,
                            parse_number, parse_time, split_missing)
from helpers import flagged, texts


def test_clean_text_repairs_without_changing_meaning():
    column = texts(["  12 ", "&gt;5", "d\\'une", "ligne\\nsuivante"])
    assert list(clean_text(column)) == ["12", ">5", "d'une", "ligne suivante"]


def test_split_missing_recognises_tokens_and_placeholder_dates():
    column = texts(["Ne sais pas", "NaN", "12", "1000-01-01", "0000-00-00", "0"])
    variable = {"missing": {"0": "not_recorded"}}
    text, flags = split_missing(column, "x", variable)
    assert list(text) == ["", "", "12", "", "", ""]
    assert flagged(flags, "missing_code") == [0, 1, 5]
    assert flagged(flags, "date_placeholder") == [3]
    assert list(flags["detail"][:2]) == ["unknown", "not_a_number"]


def test_a_code_listed_by_the_variable_is_not_a_missing_code():
    column = texts(["NA", "Ne sais pas"])
    text, flags = split_missing(column, "x", {"codes": {"NA": "sodium"}})
    assert list(text) == ["NA", ""]


def test_parse_number_reads_usual_and_unusual_spellings():
    column = texts(["12", "27,90", "28.2.", "25%", "- 3", "abc", ""])
    values, cens, flags = parse_number(column, "x", {})
    assert list(values[:5]) == [12, 27.9, 28.2, 25, -3]
    assert values[5:].isna().all()
    assert flagged(flags, "format_repaired") == [1, 2, 3, 4]
    assert flagged(flags, "unparsed") == [5]


def test_parse_number_separates_censoring_marks():
    column = texts(["<5", "> 240", "<=0,3", "7"])
    values, cens, flags = parse_number(column, "x", {})
    assert list(values) == [5, 240, 0.3, 7]
    assert list(cens) == [-1, 1, -1, 0]
    assert flagged(flags, "censored_left") == [0, 2]
    assert flagged(flags, "censored_right") == [1]


def test_parse_item_accepts_whole_numbers_only():
    column = texts(["3", "2.5", "<4", "x"])
    values, flags = parse_item(column, "x", {})
    assert values[0] == 3
    assert values[1:].isna().all()
    assert flagged(flags, "unparsed") == [1, 2, 3]
    assert "censored_left" not in set(flags["flag"])


def test_parse_category_ignores_case_and_flags_unknown_codes():
    column = texts(["Oui", "non", "1", "Peut-être", ""])
    variable = {"codes": {"Oui": "yes", "Non": "no", "1": "yes"}}
    values, flags = parse_category(column, "x", variable)
    assert list(values[:3]) == ["yes", "no", "yes"]
    assert flagged(flags, "unknown_code") == [3]


def test_parse_date_puts_partial_dates_in_the_middle_of_the_period():
    column = texts(["2015-03-21", "2015-03-00", "2015-00-00", "21/03/2015"])
    values, flags = parse_date(column, "x", {})
    assert list(values[:3]) == list(pd.to_datetime(["2015-03-21", "2015-03-15", "2015-07-01"]))
    assert flagged(flags, "date_partial") == [1, 2]
    assert flagged(flags, "unparsed") == [3]


def test_parse_time_returns_hours():
    values, flags = parse_time(texts(["12:30", "7:15", "midi"]), "x", {})
    assert list(values[:2]) == [12.5, 7.25]
    assert flagged(flags, "unparsed") == [2]


def test_parse_column_follows_the_type():
    values, cens, flags = parse_column(texts(["a", ""]), "x", {"type": "text"})
    assert values[0] == "a" and pd.isna(values[1])
    assert len(flags) == 0
