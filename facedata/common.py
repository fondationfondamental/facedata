"""The cohorts together: the instruments they share, and one baseline row per patient.

Transdiagnostic work puts the tables of several cohorts under one another
(docs/ARCHITECTURE.md, section 2). Two things come first: to know which
instruments the cohorts share and whether they hold the same form, and to put
the screening visit and the inclusion visit of a patient in one row.
"""

from pathlib import Path

import pandas as pd
import yaml

FOLDER = Path(__file__).parent
COHORTS = ["bp", "sz", "dr", "asp"]
FIRST_COLUMNS = ["cohort", "usubjid", "visit", "visit_order", "visit_month", "visit_date", "siteid", "age"]


def catalogue():
    """The instruments that two cohorts or more deliver, one row per instrument.

    Read from facedata/common_instruments.yaml, which is written by hand after
    the schemas and the data of the cohorts were compared. Columns: the
    instrument, its title and its domain; one column per cohort with the name
    of its schema there (missing when the cohort does not have the
    instrument); `n_cohorts`; `stack` ("yes", "with care" or "no"); `use`, the
    variables to analyse across cohorts; and `note`, what to know first.
    """
    with open(FOLDER / "common_instruments.yaml", encoding="utf-8") as file:
        written = yaml.load(file, Loader=yaml.BaseLoader)
    rows = []
    for name, entry in written.items():
        row = {"instrument": name, "title": entry["title"], "domain": entry["domain"]}
        for cohort in COHORTS:
            row[cohort] = entry["schemas"].get(cohort)
        row["n_cohorts"] = len(entry["schemas"])
        row["stack"] = entry["stack"]
        row["use"] = ", ".join(entry.get("use", []))
        row["note"] = " ".join(entry["note"].split())
        rows.append(row)
    return pd.DataFrame(rows)


def instruments_of(cohort, table=None):
    """The names to give to `load(..., instruments=)` of a cohort: its schemas of the shared instruments.

    table: the catalogue, or some of its rows (only the instruments to stack, only one domain).
    """
    if table is None:
        table = catalogue()
    return sorted(table[cohort].dropna().unique())


def baseline(result, max_days=None):
    """One row per patient: the inclusion visit, completed by the screening visit.

    The screening visit and the inclusion visit (V0) are two rows of `data`,
    and an instrument may be filled at the one or at the other. Each
    instrument is taken from the inclusion visit; when the inclusion visit
    holds nothing of an instrument, the instrument is taken whole from the
    screening visit. The items and the scores of an instrument therefore
    always come from the same visit.

    max_days: use the screening visit only when it took place at most that
    many days before or after the inclusion visit. Default: always.

    Returns two tables with one row per patient:
    - the visit, named "baseline": the first columns of the inclusion visit,
      then `screening_date` and `days_from_screening`, then every variable;
    - the source: for each instrument, the visit its values come from ("V0"
      or "screening"; missing when the instrument is filled at neither).
    """
    data = result.data
    inclusion = data[data["visit"] == "V0"].set_index("usubjid")
    screening = data[data["visit"] == "screening"].set_index("usubjid")
    patients = inclusion.index.union(screening.index)
    inclusion = inclusion.reindex(patients)
    screening = screening.reindex(patients)
    days = (inclusion["visit_date"] - screening["visit_date"]).dt.days
    usable = pd.Series(True, index=patients)
    if max_days is not None:                                 # a screening visit with no date is not used...
        usable = (days.abs() <= max_days) | inclusion["visit"].isna()      # ... unless it is the only visit of the patient

    in_qc = result.qc[result.qc["level"] == "visit"]
    names_of = in_qc.groupby("instrument", sort=False)["variable"].apply(list).to_dict()
    table = inclusion.copy()
    source = pd.DataFrame({"cohort": data["cohort"].iloc[0], "usubjid": patients})
    taken = {}
    for instrument, names in names_of.items():
        names = [name for name in names if name in data.columns]
        if not names:
            continue
        at_inclusion = inclusion[names].notna().any(axis=1)
        from_screening = screening[names].notna().any(axis=1) & ~at_inclusion & usable
        columns = names + [name + "_cens" for name in names if name + "_cens" in data.columns]
        table.loc[from_screening, columns] = screening.loc[from_screening, columns]
        where = pd.Series(None, index=patients, dtype="object")
        where[at_inclusion] = "V0"
        where[from_screening] = "screening"
        taken[instrument] = where.to_numpy()
    source = pd.concat([source, pd.DataFrame(taken)], axis=1)

    described = set(in_qc["variable"]) | {name + "_cens" for name in in_qc["variable"]}
    not_included = inclusion["visit"].isna()                 # screened and never included: the row is the screening visit
    for column in table.columns:
        if column in FIRST_COLUMNS:
            table[column] = table[column].where(~not_included, screening[column])
        elif column not in described:                        # a column that names a form
            other = screening[column].where(usable)
            table[column] = table[column].where(table[column].notna(), other)
    table["visit"] = "baseline"
    table["visit_month"] = 0.0
    table = table.reset_index()
    first = [column for column in FIRST_COLUMNS if column in table.columns]
    table.insert(len(first), "screening_date", screening["visit_date"].to_numpy())
    table.insert(len(first) + 1, "days_from_screening", days.to_numpy())
    others = [column for column in table.columns if column not in first + ["screening_date", "days_from_screening"]]
    return table[first + ["screening_date", "days_from_screening"] + others], source
