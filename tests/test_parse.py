"""Steps 3, 5 and 6: text repairs, missing codes and parsing."""

import pandas as pd

from facedata.parse import (clean_text, parse_band, parse_category, parse_column, parse_date,
                            parse_item, parse_number, parse_time, split_missing)
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
    column = texts(["2015-03-21", "2015-03-00", "2015-00-00", "21 mars 2015"])
    values, flags = parse_date(column, "x", {})
    assert list(values[:3]) == list(pd.to_datetime(["2015-03-21", "2015-03-15", "2015-07-01"]))
    assert flagged(flags, "date_partial") == [1, 2]
    assert flagged(flags, "unparsed") == [3]              # a date in words is not read


def test_parse_time_returns_hours():
    values, flags = parse_time(texts(["12:30", "7:15", "midi", "07:30:00"]), "x", {})
    assert list(values[:2]) == [12.5, 7.25]
    assert values[3] == 7.5                              # one extraction writes the seconds too
    assert flagged(flags, "unparsed") == [2]


def test_parse_column_follows_the_type():
    values, cens, flags = parse_column(texts(["a", ""]), "x", {"type": "text"})
    assert values[0] == "a" and pd.isna(values[1])
    assert len(flags) == 0


def test_letter_answers_can_be_counted():
    """An item with codes: the letters are replaced by numbers before parsing."""
    variable = {"type": "item", "range": [0.0, 1.0], "codes": {"Y": "1", "N": "0"}, "missing": {"U": "unknown"}}
    text, missing_flags = split_missing(texts(["Y", "n", "U", "1", "X"]), "x", variable)
    values, cens, flags = parse_column(text, "x", variable)
    assert list(values[:2]) == [1, 0] and values[3] == 1
    assert pd.isna(values[2]) and pd.isna(values[4])
    assert flagged(missing_flags, "missing_code") == [2]
    assert flagged(flags, "unparsed") == [4]


def test_a_band_is_read_as_its_middle():
    column = texts(["60-51", "41 - 50", "100_91", "70", "-5", "a-b"])
    values, cens, flags = parse_number(column, "x", {"bands": "middle"})
    assert list(values[:5]) == [55.5, 45.5, 95.5, 70, -5]
    assert flagged(flags, "band_middle") == [0, 1, 2]
    assert flagged(flags, "unparsed") == [5]
    assert list(flags.loc[flags["flag"] == "band_middle", "detail"])[0] == "band 60-51"
    values, cens, flags = parse_number(column, "x", {})          # without the field, a band is not read
    assert flagged(flags, "unparsed") == [0, 1, 2, 5]


def test_parse_number_reads_a_number_without_its_leading_zero():
    values, cens, flags = parse_number(texts([".45", "-.02", ",5"]), "x", {})
    assert list(values) == [0.45, -0.02, 0.5]
    assert flagged(flags, "format_repaired") == [0, 1, 2]


def test_parse_band_gives_the_lower_limit_of_the_band():
    """The decision table of SCHEMA_SPEC, section 6."""
    variable = {"limits": [5.0, 10.0, 25.0, 50.0, 75.0, 90.0, 95.0]}
    column = texts(["25 - 50", "50 - 25", "[25-50]", "50", ">95", "<5", ">10", "10 - 50", "<10", ">=75", "12", "30 - 40", ""])
    values, cens, flags = parse_band(column, "x", variable)
    assert list(values[:10]) == [25, 25, 25, 50, 95, 0, 10, 10, 5, 75]
    assert values[10:].isna().all()
    assert list(cens[:10]) == [0, 0, 0, 0, 0, 0, 1, 1, -1, 1]
    assert flagged(flags, "censored_right") == [6, 7, 9]     # this band or a higher one
    assert flagged(flags, "censored_left") == [8]            # this band or a lower one
    assert flagged(flags, "unparsed") == [10, 11]            # 12 is no limit, 30 - 40 is no band


def test_a_band_label_cut_by_the_export_is_written_out_with_codes():
    variable = {"type": "band", "limits": [5.0, 10.0, 25.0, 50.0, 75.0, 90.0, 95.0], "codes": {"25-5": "25-50", "<": "<5"}}
    values, cens, flags = parse_column(texts(["25-5", "25-50", "<", "10-2", "5-25"]), "band", variable)
    assert list(values[:3]) == [25, 25, 0]              # the cut labels are the bands that the codes name
    assert pd.isna(values[3]) and list(flags["flag"]) == ["censored_right", "unparsed"]    # a label that no code names
    assert (values[4], cens[4]) == (5, 1)               # a real "5 to 25", wider than one band


def test_parse_band_turns_a_z_score_into_its_band():
    """With z_range, a z-score gets the band it has under the normal law."""
    variable = {"limits": [1.0, 5.0, 25.0, 50.0, 75.0, 95.0, 99.0], "z_range": [-5.0, 5.0]}
    column = texts(["0.00", "0.80", "-1.70", "2.40", "-3.00", "25 - 50", "7.50", "1,65"])
    values, cens, flags = parse_band(column, "x", variable)
    assert list(values[:6]) == [50, 75, 1, 99, 0, 25]        # 50th, 79th and 4th percentile, above the 99th, under the 1st
    assert pd.isna(values[6]) and values[7] == 95            # 7.50 is no z-score; a decimal comma is read
    assert flagged(flags, "band_from_z") == [0, 1, 2, 3, 4, 7]
    assert flagged(flags, "out_of_range") == [6]
    assert list(cens) == [0] * 8


def test_parse_date_reads_dates_written_day_month_year():
    column = texts(["15/06/2018", "5/6/2018", "06/2018", "2018", "/", "31/02/2018"])
    values, flags = parse_date(column, "x", {})
    assert list(values[:4].dt.strftime("%Y-%m-%d")) == ["2018-06-15", "2018-06-05", "2018-06-15", "2018-07-01"]
    assert flagged(flags, "date_partial") == [2, 3]         # no day, no month: the middle of the period
    assert flagged(flags, "unparsed") == [4, 5]             # a slash alone, a day that does not exist


def test_parse_date_gives_the_day_that_the_export_writes():
    """day: 15. The export blurs a date of birth to the 15th; a cell that kept its day is blurred here."""
    column = texts(["1970-03-15", "1970-03-27", "1970-03-00", ""])
    values, flags = parse_date(column, "x", {"day": 15.0})
    assert list(values[:3]) == list(pd.to_datetime(["1970-03-15", "1970-03-15", "1970-03-15"]))
    assert flagged(flags, "date_partial") == [1, 2]
    assert pd.isna(values[3])
