"""Statistics of every delivered variable, for the data dictionary.

Step 1 of 4 (dictionary/README.md). Loads each cohort with facedata, without
winsorising, and writes dictionary/stats/<cohort>.json: how many values each
variable has, at which visits, how much is missing, and how the values are
spread. Aggregates only: no row of a patient, no value of a text column, no
centre, and no count from 1 to 4 (written -1, "fewer than 5"; a percentage
that would give such a count away is left out). These files are committed.

    .venv/bin/python dictionary/build_stats.py            # the four cohorts, a few minutes
    .venv/bin/python dictionary/build_stats.py dr sz      # some cohorts
    .venv/bin/python dictionary/build_stats.py --cached   # reuse the loads kept in local/cache by an earlier run
"""

import datetime
import json
import math
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import facedata.asp  # noqa: E402
import facedata.bp  # noqa: E402
import facedata.dr  # noqa: E402
import facedata.sz  # noqa: E402
from facedata import common  # noqa: E402
from facedata.pipeline import Result  # noqa: E402
from facedata.schema import load_schemas  # noqa: E402

FOLDER = Path(__file__).resolve().parent
MODULES = {"bp": facedata.bp, "sz": facedata.sz, "dr": facedata.dr, "asp": facedata.asp}
TABLE_OF_LEVEL = {"visit": "data", "patient": "patients", "list": "treatments", "relatives": "relatives"}
KEYS = {                                             # the columns that facedata adds: name -> type
    "data": {"cohort": "text", "usubjid": "text", "visit": "category", "visit_order": "item", "visit_month": "item",
             "visit_date": "date", "siteid": "text", "age": "number"},
    "patients": {"cohort": "text", "usubjid": "text"},
    "treatments": {"cohort": "text", "usubjid": "text", "list": "category", "item": "item", "visit": "category"},
    "relatives": {"cohort": "text", "usubjid": "text", "relative": "category"},
}
QUANTILES = [("p01", 0.01), ("p05", 0.05), ("p25", 0.25), ("median", 0.5), ("p75", 0.75), ("p95", 0.95), ("p99", 0.99)]


def read_config():
    with open(FOLDER / "config.yaml", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_cohort(cohort, config, cached):
    """The six tables of a cohort, loaded without winsorising (the true tails).

    cached: reuse local/cache/dictionary_<cohort>.pkl when it exists, and
    write it after a load. The folder local/ is git-ignored.
    """
    kept = ROOT / "local" / "cache" / ("dictionary_%s.pkl" % cohort)
    if cached and kept.exists():
        with open(kept, "rb") as file:
            return Result(**pickle.load(file))
    result = MODULES[cohort].load(ROOT / config["extractions"][cohort], norms=ROOT / config["norms"], winsorise=False)
    if cached:
        kept.parent.mkdir(parents=True, exist_ok=True)
        with open(kept, "wb") as file:
            pickle.dump(result._asdict(), file)
    return result


def masked(count, smallest):
    """A count as it may be written: 1 to smallest - 1 becomes -1 ("fewer than")."""
    count = int(count)
    return -1 if 0 < count < smallest else count


def rounded(number, digits=4):
    """A number with 4 significant digits, as a plain float (None when missing)."""
    if number is None or pd.isna(number):
        return None
    number = float(number)
    if number == 0 or not math.isfinite(number):
        return 0.0 if number == 0 else None
    return round(number, digits - 1 - int(math.floor(math.log10(abs(number)))))


def percent(part, whole):
    """Share in percent with one decimal, None when the whole is 0."""
    return round(100 * part / whole, 1) if whole else None


def as_numbers(values):
    """A column as floats; what is not a number is missing."""
    return pd.to_numeric(values, errors="coerce").astype(float).dropna()


def summary(numbers, limits, smallest):
    """Mean, spread and percentiles of a numeric column, and the share at each end of its range.

    A share that stands for 1 to smallest - 1 values is not written.
    """
    figures = {"n": int(len(numbers)), "mean": rounded(numbers.mean()), "sd": rounded(numbers.std()),
               "min": rounded(numbers.min()), "max": rounded(numbers.max()), "n_distinct": int(numbers.nunique())}
    for name, share in QUANTILES:
        figures[name] = rounded(numbers.quantile(share))
    if limits is not None:                           # floor and ceiling of a bounded scale
        for name, limit in [("at_minimum_pct", limits[0]), ("at_maximum_pct", limits[1])]:
            count = int((numbers == limit).sum())
            figures[name] = percent(count, len(numbers)) if masked(count, smallest) != -1 else None
    return figures


def bins(numbers, smallest):
    """A histogram of at most 20 bins between the 1st and the 99th percentile; the end bins hold the tails."""
    low, high = numbers.quantile(0.01), numbers.quantile(0.99)
    if not high > low:
        low, high = numbers.min(), numbers.max()
    if not high > low:
        return {"kind": "bins", "x": [rounded(low), rounded(low)], "n": [masked(len(numbers), smallest)]}
    if (numbers % 1 == 0).all():                     # whole numbers: bins of a whole width, [edge, next edge)
        low, high = math.floor(low), math.ceil(high)
        width = max(1, math.ceil((high - low + 1) / 20))
        edges = low + width * np.arange(math.ceil((high - low + 1) / width) + 1)
    else:
        edges = np.linspace(low, high, 21)
    counts = np.histogram(numbers.clip(edges[0], edges[-1]), bins=edges)[0]
    return {"kind": "bins", "x": [rounded(edge, 5) for edge in edges], "n": [masked(count, smallest) for count in counts]}


def levels(values, order, smallest):
    """How many values at each level: the answers of an item, the labels of a category."""
    counts = values.value_counts()
    found = [label for label in order if label in counts.index] + sorted(label for label in counts.index if label not in order)
    return {"kind": "levels", "x": [label if isinstance(label, str) else rounded(label, 6) for label in found],
            "n": [masked(counts[label], smallest) for label in found]}


def years(dates, smallest):
    """How many dates in each year."""
    counts = pd.to_datetime(dates, errors="coerce").dt.year.dropna().astype(int).value_counts().sort_index()
    return {"kind": "years", "x": [int(year) for year in counts.index], "n": [masked(count, smallest) for count in counts]}


def describe(values, kind, order, limits, config):
    """The figures and the distribution of one column: {"stats": ..., "dist": ...}.

    kind: the type of the variable (number, item, band, score, time, category,
    date, text). A text column gives its number of values only, never a value.
    """
    values = values.dropna()
    smallest = config["smallest_count"]
    n = int(len(values))
    if n < smallest:                                 # too few to describe without showing a patient
        return {"stats": {"n": masked(n, smallest)}, "dist": None}
    if kind == "text":
        return {"stats": {"n": n, "n_distinct": masked(values.nunique(), smallest)}, "dist": None}
    if kind == "date":
        dates = pd.to_datetime(values, errors="coerce").dropna()
        figures = {"n": n, "first_year": int(dates.dt.year.min()), "last_year": int(dates.dt.year.max())}
        return {"stats": figures, "dist": years(dates, smallest)}
    if kind == "category":
        return {"stats": {"n": n, "n_distinct": int(values.nunique())}, "dist": levels(values, order, smallest)}
    numbers = as_numbers(values)
    if len(numbers) < smallest:
        return {"stats": {"n": masked(len(numbers), smallest)}, "dist": None}
    figures = summary(numbers, limits, smallest)
    if len(numbers) < config["smallest_histogram"]:
        return {"stats": figures, "dist": None}
    few = numbers.nunique() <= 25 and (numbers % 1 == 0).all()
    shape = levels(numbers, [], smallest) if few or (kind == "band" and numbers.nunique() <= 25) else bins(numbers, smallest)
    return {"stats": figures, "dist": shape}


def visit_table(result, smallest):
    """The visits of the cohort, in order: label, planned month, number of visits."""
    data = result.data
    table = data.groupby("visit", dropna=False).agg(month=("visit_month", "median"), order=("visit_order", "median"), n=("visit", "size"))
    table["month"] = table["month"].where(table.index != "screening", -1)
    table = table.reset_index().sort_values(["month", "order"], na_position="last")
    return [{"visit": row["visit"], "month": None if pd.isna(row["month"]) or row["month"] < 0 else int(row["month"]),
             "n": masked(row["n"], smallest)} for index, row in table.iterrows() if row["visit"] != ""]


def specs_of(result, schemas):
    """One line per column to describe: where it is, its type, its instrument, the order of its labels, its range.

    The delivered variables come from the QC table of the load. The other
    columns of the tables are the keys, the censoring columns (<variable>_cens)
    and the columns that name an edition (bis_form, wais_version).
    """
    lines = {}
    for index, row in result.qc.iterrows():
        schema = schemas.get(row["instrument"], {})
        spec = {**schema.get("variables", {}), **schema.get("scores", {})}.get(row["variable"], {})
        codes = spec.get("codes") if row["type"] == "category" else None
        line = lines.setdefault(row["variable"], {"table": TABLE_OF_LEVEL[row["level"]], "type": row["type"], "instruments": [],
                                                  "order": list(dict.fromkeys(codes.values())) if isinstance(codes, dict) else [],
                                                  "range": spec.get("range") if row["type"] != "date" else None, "role": "variable"})
        line["instruments"].append(row["instrument"])
    for table, keys in KEYS.items():                 # data first: cohort and usubjid are described once, from the visit table
        for name in getattr(result, table).columns:
            if name in lines:
                continue
            if name in keys:
                lines[name] = {"table": table, "type": keys[name], "instruments": [], "order": [], "range": None, "role": "key"}
            elif name.endswith("_cens"):
                owner = lines.get(name[:-5], {})
                lines[name] = {"table": table, "type": "item", "instruments": owner.get("instruments", []), "order": [],
                               "range": None, "role": "censoring"}
            else:
                users = [key for key, schema in schemas.items() if schema.get("version", {}).get("name") == name]
                lines[name] = {"table": table, "type": "category", "instruments": users, "order": [], "range": None, "role": "edition"}
    return lines


def instrument_presence(result, lines):
    """For each instrument of the visit table: the visits that hold at least one of its values."""
    names_of = {}
    for name, line in lines.items():
        if line["table"] == "data" and line["role"] == "variable":
            for instrument in line["instruments"]:
                names_of.setdefault(instrument, []).append(name)
    return {instrument: result.data[names].notna().any(axis=1) for instrument, names in names_of.items()}


def qc_per_name(qc):
    """The QC table with one line per column name.

    A column of the table `treatments` can be filled by several lists (the
    start date of each list of medications): their counts are added.
    """
    counts = [name for name in qc.columns if name.startswith("n_") and name != "n_sites"]
    counts = counts + list(qc.columns[qc.columns.get_loc("missing_code"):qc.columns.get_loc("n_cens_left")])
    rules = {name: "sum" for name in dict.fromkeys(counts)}
    rules.update({"first_year": "min", "last_year": "max", "n_sites": "max"})
    return qc.groupby("variable", sort=False).agg(rules)


def cohort_stats(cohort, result, schemas, config):
    """Everything the dictionary says about the data of one cohort, as a dict ready for JSON."""
    smallest = config["smallest_count"]
    lines = specs_of(result, schemas)
    data = result.data
    first, source = common.baseline(result)          # one row per patient: inclusion, completed by screening
    in_data = [name for name, line in lines.items() if line["table"] == "data"]
    filled = data[in_data].notna()
    by_visit = filled.groupby(data["visit"]).sum()
    per_patient = filled.groupby(data["usubjid"]).sum()
    at_baseline = first[in_data].notna().sum()
    present = instrument_presence(result, lines)
    qc = qc_per_name(result.qc)
    flag_names = list(result.qc.columns[result.qc.columns.get_loc("missing_code"):result.qc.columns.get_loc("n_cens_left")])

    variables = {}
    for name, line in lines.items():
        table = getattr(result, line["table"])
        values = table[name]
        valid = int(values.notna().sum())
        few = masked(valid, smallest) == -1          # 1 to 4 values: no figure may give the count away
        block = {"table": line["table"], "role": line["role"], "instruments": line["instruments"],
                 "n": {"rows": int(len(table)), "valid": masked(valid, smallest),
                       "patients": masked(table.loc[values.notna(), "usubjid"].nunique(), smallest)},
                 "missing": {"all": None if few else percent(len(table) - valid, len(table))}}
        described = {"all": describe(values, line["type"], line["order"], line["range"], config)}
        if line["table"] == "data":
            block["n"]["patients_2plus"] = masked((per_patient[name] >= 2).sum(), smallest)
            block["n"]["baseline"] = masked(at_baseline[name], smallest)
            block["missing"]["baseline"] = None if masked(at_baseline[name], smallest) == -1 else percent(len(first) - at_baseline[name], len(first))
            block["timepoints"] = {visit: masked(count, smallest) for visit, count in by_visit[name].items() if count > 0 and visit != ""}
            instrument = line["instruments"][0] if line["instruments"] else None
            if line["role"] == "variable" and instrument in present and not few:
                with_form = present[instrument]
                block["missing"]["in_instrument"] = percent((with_form & values.isna()).sum(), with_form.sum())
            described["baseline"] = describe(first[name], line["type"], line["order"], line["range"], config)
        block["stats"] = {scope: one["stats"] for scope, one in described.items()}
        block["dist"] = {scope: one["dist"] for scope, one in described.items() if one["dist"] is not None}
        if name in qc.index:
            row = qc.loc[name]
            block["qc"] = {"n_rows": int(row["n_rows"]), "n_filled": masked(row["n_filled"], smallest), "n_valid": masked(row["n_valid"], smallest)}
            block["flags"] = {flag: masked(row[flag], smallest) for flag in flag_names if row[flag] > 0}
            block["censored"] = {"left": masked(row["n_cens_left"], smallest), "right": masked(row["n_cens_right"], smallest)}
            if not pd.isna(row["first_year"]) and not few:
                block["years"] = [int(row["first_year"]), int(row["last_year"])]
            if not few:
                block["n_sites"] = int(row["n_sites"])
        variables[name] = block

    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {"cohort": cohort, "extraction": config["extractions"][cohort], "computed": datetime.date.today().isoformat(), "git": git,
            "winsorised": False, "smallest_count": smallest,
            "n_patients": int(data["usubjid"].nunique()), "n_visits": int(len(data)), "n_baseline_rows": int(len(first)),
            "tables": {table: [int(len(getattr(result, table))), int(getattr(result, table).shape[1])] for table in KEYS},
            "visits": visit_table(result, smallest), "variables": variables}


def main(arguments):
    config = read_config()
    cached = "--cached" in arguments
    cohorts = [name for name in arguments if name in MODULES] or list(MODULES)
    (FOLDER / "stats").mkdir(exist_ok=True)
    for cohort in cohorts:
        result = load_cohort(cohort, config, cached)
        schemas = load_schemas(MODULES[cohort].SCHEMAS)
        stats = cohort_stats(cohort, result, schemas, config)
        with open(FOLDER / "stats" / (cohort + ".json"), "w", encoding="utf-8") as file:
            json.dump(stats, file, ensure_ascii=False, separators=(",", ":"))
        print("%s: %d patients, %d visits, %d columns described" % (cohort, stats["n_patients"], stats["n_visits"], len(stats["variables"])))


if __name__ == "__main__":
    main(sys.argv[1:])
