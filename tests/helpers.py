"""Small helpers to write test tables by hand."""

import pandas as pd


def texts(values):
    """A column of an extraction: a Series of strings."""
    return pd.Series(values, dtype=str)


def make_keys(usubjid, visit_month, visit_date, siteid=None):
    """The key columns of a few visits."""
    keys = pd.DataFrame({"usubjid": usubjid})
    keys["visit"] = ["V" + str(month) for month in visit_month]
    keys["visit_order"] = range(len(keys))
    keys["visit_month"] = visit_month
    keys["visit_date"] = pd.to_datetime(visit_date)
    keys["siteid"] = siteid if siteid is not None else "01"
    return keys


def flagged(flags, code):
    """The row numbers that carry a flag."""
    return sorted(flags.loc[flags["flag"] == code, "row"])
