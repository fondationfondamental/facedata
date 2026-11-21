"""Check the figures of the dictionary against the data, by another road than build_stats.py.

Run it after a rebuild. It prints counts only, never a row of a patient.

    .venv/bin/python dictionary/check_numbers.py            # the four cohorts
    .venv/bin/python dictionary/check_numbers.py dr 60      # one cohort, 60 items drawn at random

Three checks:

1. Every variable: the number of values in dictionary/stats equals the number
   that the quality-control table of facedata gives for the same load (n_valid).
2. Items drawn at random among those that the schema reads as they are (one raw
   column, whole numbers, no code, no rule): the raw column of the extraction is
   read again as text and counted by hand. The number of values, the mean and
   the count of each answer must be those of face_dictionary.json.
3. Sums of such items (a score with no reversed item and no other rule): the
   score is added up again from the raw columns, on the visits where every item
   is present. The number of values, the mean and the median must agree.
"""

import json
import random
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import facedata.asp  # noqa: E402
import facedata.bp  # noqa: E402
import facedata.dr  # noqa: E402
import facedata.sz  # noqa: E402
from facedata.schema import load_schemas  # noqa: E402

FOLDER = Path(__file__).resolve().parent
MODULES = {"bp": facedata.bp, "sz": facedata.sz, "dr": facedata.dr, "asp": facedata.asp}
RULES = ["codes", "missing", "asked_if", "box_list", "shown_if", "separator", "doubt", "versions", "derived_from", "parse", "not_above"]
SCORE_RULES = ["reverse", "points", "minus", "scale", "floor", "min_items", "otherwise", "versions", "stop_at_zero"]


def raw_table(path):
    """The extraction as text, one row per visit record (a repeated record is dropped, as facedata does)."""
    raw = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return raw.drop_duplicates(subset=["visitnum"]).reset_index(drop=True)


def whole_numbers(text, limits):
    """A raw column as numbers: what is not a whole number inside the range is missing."""
    numbers = pd.to_numeric(text.str.strip(), errors="coerce")
    inside = numbers.between(limits[0], limits[1]) & (numbers % 1 == 0)
    return numbers.where(inside)


def plain_items(schema, columns):
    """The items of a schema that are delivered as written: {name: (raw column, range)}."""
    if schema.get("level", "visit") != "visit" or any(field in schema for field in ["version", "sign", "implausible_visits", "derived_from"]):
        return {}
    found = {}
    for name, variable in schema["variables"].items():
        simple = variable.get("type") == "item" and variable.get("keep", True) and len(variable["columns"]) == 1
        if simple and "range" in variable and not any(rule in variable for rule in RULES) and variable["columns"][0] in columns:
            found[name] = (variable["columns"][0], variable["range"])
    return found


def close(a, b, tolerance=0.0006):
    """Two figures that agree to the 4 significant digits of the dictionary."""
    if a is None or b is None or pd.isna(a) or pd.isna(b):
        return a is None and (b is None or pd.isna(b))
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def check_counts_against_qc(cohort):
    """Check 1: the counts of build_stats.py against the n_valid of facedata's own QC table."""
    stats = json.loads((FOLDER / "stats" / (cohort + ".json")).read_text(encoding="utf-8"))["variables"]
    checked, wrong = 0, []
    for name, block in stats.items():
        if "qc" not in block or block["n"]["valid"] == -1:
            continue
        checked += 1
        if block["n"]["valid"] != block["qc"]["n_valid"]:
            wrong.append("%s: %d in the table, %d in the QC" % (name, block["n"]["valid"], block["qc"]["n_valid"]))
    return checked, wrong


def check_items(cohort, raw, schemas, variables, how_many, generator):
    """Check 2: items read again from the raw columns."""
    candidates = {}
    for schema in schemas.values():
        candidates.update(plain_items(schema, set(raw.columns)))
    names = sorted(name for name in candidates if name in variables and cohort in variables[name]["cohorts"])
    drawn = generator.sample(names, min(how_many, len(names)))
    wrong = []
    for name in drawn:
        column, limits = candidates[name]
        values = whole_numbers(raw[column], limits).dropna()
        block = variables[name]["cohorts"][cohort]
        figures = block.get("stats", {}).get("all", {})
        if block["n"]["valid"] == -1:                # fewer than 5: only that can be checked
            if not 0 < len(values) < 5:
                wrong.append("%s: fewer than 5 values written, %d counted" % (name, len(values)))
            continue
        if block["n"]["valid"] != len(values):
            wrong.append("%s: %d values written, %d counted" % (name, block["n"]["valid"], len(values)))
            continue
        if len(values) >= 5 and not close(figures.get("mean"), values.mean()):
            wrong.append("%s: mean %s written, %.4f counted" % (name, figures.get("mean"), values.mean()))
        dist = block.get("dist", {}).get("all")
        if dist and dist["kind"] == "levels":
            counted = values.value_counts()
            for level, written in zip(dist["x"], dist["n"]):
                real = int(counted.get(level, 0))
                if (written == -1 and not 0 < real < 5) or (written != -1 and written != real):
                    wrong.append("%s: answer %s, %s written, %d counted" % (name, level, written, real))
    return len(drawn), len(names), wrong


def check_sums(cohort, raw, schemas, variables):
    """Check 3: plain sums added up again from the raw columns."""
    checked, wrong = 0, []
    for schema in schemas.values():
        items = plain_items(schema, set(raw.columns))
        for name, score in schema.get("scores", {}).items():
            parts = score.get("sum") or []
            usable = score.get("keep", True) and parts and all(part in items for part in parts) and not any(score.get(rule) for rule in SCORE_RULES)
            if not usable or name not in variables or cohort not in variables[name]["cohorts"]:
                continue
            table = pd.DataFrame({part: whole_numbers(raw[items[part][0]], items[part][1]) for part in parts})
            sums = table.sum(axis=1)[table.notna().all(axis=1)]
            if "range" in score:                     # a sum outside its range is not delivered
                sums = sums[sums.between(score["range"][0], score["range"][1])]
            block = variables[name]["cohorts"][cohort]
            figures = block.get("stats", {}).get("all", {})
            checked += 1
            if block["n"]["valid"] != len(sums) and not (block["n"]["valid"] == -1 and 0 < len(sums) < 5):
                wrong.append("%s: %s values written, %d added up" % (name, block["n"]["valid"], len(sums)))
            elif len(sums) >= 5 and not (close(figures.get("mean"), sums.mean()) and close(figures.get("median"), sums.median())):
                wrong.append("%s: mean %s and median %s written, %.4f and %.4f added up" % (
                    name, figures.get("mean"), figures.get("median"), sums.mean(), sums.median()))
    return checked, wrong


def main(arguments):
    with open(FOLDER / "config.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    cohorts = [name for name in arguments if name in MODULES] or list(MODULES)
    how_many = next((int(text) for text in arguments if text.isdigit()), 30)
    variables = json.loads((ROOT / "facedata" / "dictionary" / "face_dictionary.json").read_text(encoding="utf-8"))["variables"]
    generator = random.Random(20261121)              # the same draw at each run
    problems = 0
    for cohort in cohorts:
        raw = raw_table(ROOT / config["extractions"][cohort])
        schemas = load_schemas(MODULES[cohort].SCHEMAS)
        checked, wrong = check_counts_against_qc(cohort)
        print("%s  1. counts against the QC table: %d variables, %d differ" % (cohort, checked, len(wrong)))
        drawn, among, wrong_items = check_items(cohort, raw, schemas, variables, how_many, generator)
        print("%s  2. items read again from the extraction: %d drawn among %d, %d differ" % (cohort, drawn, among, len(wrong_items)))
        sums, wrong_sums = check_sums(cohort, raw, schemas, variables)
        print("%s  3. sums added up again from the extraction: %d scores, %d differ" % (cohort, sums, len(wrong_sums)))
        for line in wrong + wrong_items + wrong_sums:
            print("     ", line)
        problems += len(wrong) + len(wrong_items) + len(wrong_sums)
    print("all the figures checked agree" if problems == 0 else "%d differences to look at" % problems)
    return problems


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:]) else 0)
