"""The age at inclusion in completed years and the PSQI bedtime corrected (decisions of 2026-11-21)."""

import numpy as np
import pandas as pd

from facedata import custom


def test_age_at_inclusion_counts_completed_calendar_years():
    """The year difference, one less when the birthday has not come yet in the year of the V0 visit."""
    keys = pd.DataFrame({"usubjid": ["a", "a", "b", "c", "d", "e"],
                         "visit": ["V0", "V1_an", "V0", "V0", "V0", "V0"],
                         "visit_date": pd.to_datetime(["2020-03-09", "2021-03-09", "2020-03-10", "2020-03-11",
                                                       "2020-03-10", None])})
    birth = pd.to_datetime(["1980-03-10", "1980-03-10", "1980-03-10", "1980-03-10", None, "1980-03-10"])
    values = pd.DataFrame({"birth_date_stored": birth})
    age = custom.age_at_inclusion(values, keys)
    assert list(age[:4]) == [39, 39, 40, 40]       # the day before the birthday, its follow-up row, the birthday, the day after
    assert pd.isna(age[4]) and pd.isna(age[5])      # no date of birth, no date of the V0 visit


def test_age_at_inclusion_is_not_days_over_365_25():
    """Born on 1 March 1960, seen on 28 February 2001: 40 calendar years, and 14,974 days / 365.25 is 40.997."""
    keys = pd.DataFrame({"usubjid": ["a", "b"], "visit": ["V0", "V0"],
                         "visit_date": pd.to_datetime(["2001-02-28", "2001-03-01"])})
    values = pd.DataFrame({"birth_date_stored": pd.to_datetime(["1960-03-01", "1960-03-01"])})
    assert list(custom.age_at_inclusion(values, keys)) == [40, 41]


def test_psqi_bedtime_corrects_a_12_hour_clock_and_24_hours():
    values = pd.DataFrame({"psqi_bedtime_typed": [23.0, 11.0, 8.0, 10.0, 24.0, 24.5, 12.5, 0.5, 11.0, np.nan],
                           "psqi_rising_time": [7.0, 7.0, 18.0, 6.0, 7.0, 7.0, 7.0, 7.0, np.nan, 7.0]})
    bedtime = custom.psqi_bedtime(values)
    # 23:00 as typed; 11:00 with 20 hours in bed is 23:00; 8:00 then 18:00 is a day sleeper, kept;
    # 10:00 with exactly 20 hours in bed is 22:00; 24:00 is 0:00 and 24:30 is 0:30; 12:30 with 18.5 hours
    # in bed is 0:30; 0:30 as typed; no rising time: as typed; no bedtime: missing
    assert list(bedtime[:9]) == [23.0, 23.0, 8.0, 22.0, 0.0, 0.5, 0.5, 0.5, 11.0]
    assert pd.isna(bedtime[9])


def test_psqi_efficiency_is_the_same_with_the_bedtime_corrected():
    """The efficiency reads the typed bedtime; the corrected bedtime gives the same hours in bed."""
    typed = pd.DataFrame({"psqi_bedtime_typed": [23.0, 11.0, 24.0, 12.5, 8.0],
                          "psqi_rising_time": [7.0, 7.0, 7.0, 7.0, 18.0],
                          "psqi_sleep_hours": [7.0, 7.0, 5.5, 4.0, 9.0]})
    corrected = typed.assign(psqi_bedtime_typed=custom.psqi_bedtime(typed))
    assert list(custom.psqi_efficiency(typed)) == list(custom.psqi_efficiency(corrected)) == [0.0, 0.0, 1.0, 3.0, 0.0]
