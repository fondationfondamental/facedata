"""The flag log: one line per cell that was changed, doubted or removed.

Inside the pipeline a flag table has four columns: row (the row number in the
extraction), variable, flag and detail. finish_flags() turns it into the
table that load() returns.
"""

import pandas as pd

from facedata.tokens import FLAG_COLUMNS, SEVERITY

WORKING_COLUMNS = ["row", "variable", "flag", "detail"]


def make_flags(rows, variable, flag, detail=""):
    """Flag the rows where `rows` is True.

    `rows` is a True/False Series. `detail` is one text for all the rows, or a
    Series with one text per row.
    """
    where = rows.index[rows.fillna(False).astype(bool)]
    table = pd.DataFrame({"row": where})
    table["variable"] = variable
    table["flag"] = flag
    if isinstance(detail, pd.Series):
        table["detail"] = detail.loc[where].astype(str).to_numpy()
    else:
        table["detail"] = detail
    return table


def stack_flags(tables):
    """Put several flag tables under one another."""
    tables = [table for table in tables if len(table) > 0]
    if len(tables) == 0:
        return pd.DataFrame(columns=WORKING_COLUMNS)
    return pd.concat(tables, ignore_index=True)


def finish_flags(flags, keys, raw_text, values):
    """Add who, where, the original text, the final value and the severity.

    raw_text and values are tables with one column per variable.
    """
    flags = flags.drop_duplicates().reset_index(drop=True)
    flags["usubjid"] = keys["usubjid"].loc[flags["row"]].to_numpy()
    flags["visit"] = keys["visit"].loc[flags["row"]].to_numpy()
    flags["raw"] = pd.Series("", index=flags.index, dtype=object)
    flags["value"] = pd.Series("", index=flags.index, dtype=object)   # numbers, labels or dates
    for variable, lines in flags.groupby("variable"):
        if variable in raw_text.columns:
            flags.loc[lines.index, "raw"] = raw_text[variable].loc[lines["row"]].to_numpy()
        if variable in values.columns:
            final = values[variable].loc[lines["row"]]
            flags.loc[lines.index, "value"] = final.astype(object).where(final.notna(), "").to_numpy()
    flags["severity"] = flags["flag"].map(SEVERITY)
    return flags[FLAG_COLUMNS]
