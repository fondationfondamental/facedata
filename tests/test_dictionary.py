"""The data dictionary (dictionary/): figures, hierarchy, direction, and the files it writes.

A tiny hand-written extraction of 12 made-up patients goes through facedata
and then through the three steps of the dictionary. No real data is read.
"""

import fnmatch
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "dictionary"))

import build_html  # noqa: E402
import build_json  # noqa: E402
import build_stats  # noqa: E402

from facedata.pipeline import run_cohort  # noqa: E402
from facedata.schema import load_schemas  # noqa: E402

COMMITTED = ROOT / "facedata" / "dictionary"          # the dictionary that every install has

SCHEMA = """
instrument: demo
title: Demo scale
tab: TEST
section: Demo
status: draft
defaults: {type: item, range: [0, 4]}
variables:
  it1: {label: First item}
  it2: {label: Demo item 2}
  rare: {label: Seldom asked}
  tot_stored: {column: tot, range: [0, 8], keep: false}
  note: {type: text, label: Free text}
  sex: {column: sexe, type: category, codes: {F: female, M: male}, label: Sex}
scores:
  total:
    label: Demo total
    sum: [it1, it2]
    reverse: [it2]
    range: [0, 8]
    compare: tot_stored
"""
CONFIG = {"smallest_count": 5, "smallest_histogram": 20, "extractions": {"demo": "extraction.tsv"}}


def made_up_rows():
    """12 patients at V0, the first 8 again at one year. it2 is asked at V0 only."""
    lines = ["usubjid\tvisit\tid_visit\tvisitnum\tsvdtc\tsiteid\tit1\tit2\trare\ttot\tnote\tsexe"]
    number = 0
    for patient in range(12):
        number += 1
        it1, it2 = patient % 4, patient % 5
        rare = "1" if patient < 3 else ""
        note = "private note %d" % patient if patient < 6 else ""
        sex = "M" if patient < 2 else "F"
        lines.append("P%02d\tV0\t2\t%d\t2015-01-%02d\t01\t%d\t%d\t%s\t%d\t%s\t%s" % (
            patient, number, 10 + patient, it1, it2, rare, it1 + 4 - it2, note, sex))
    for patient in range(8):
        number += 1
        it1 = 4 if patient < 2 else 0
        lines.append("P%02d\tV1_an\t4\t%d\t2016-01-%02d\t01\t%d\t\t\t\t\t" % (patient, number, 10 + patient, it1))
    return "\n".join(lines) + "\n"


@pytest.fixture
def cohort(tmp_path):
    """The made-up cohort loaded by facedata: the result, the schemas and the statistics of the dictionary."""
    (tmp_path / "schemas" / "tab").mkdir(parents=True)
    (tmp_path / "schemas" / "tab" / "demo.yaml").write_text(SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(made_up_rows(), encoding="utf-8")
    result = run_cohort(tmp_path / "extraction.tsv", tmp_path / "schemas", norms_folder=tmp_path, cohort="demo",
                        first_visit="2008-01-01", winsorise_values=False)
    schemas = load_schemas(tmp_path / "schemas")
    stats = build_stats.cohort_stats("demo", result, schemas, CONFIG)
    return result, schemas, stats


def blocks_of(schemas, stats):
    context = {"schemas": schemas, "stats": stats["variables"], "visits": stats["visits"], "workbook": None,
               "extraction": "extraction.tsv", "tab_of": {"demo": "TEST"}}
    return build_json.add_statistics(build_json.cohort_blocks("demo", context), context)


def test_counts_visits_and_missing_values(cohort):
    result, schemas, stats = cohort
    assert stats["n_patients"] == 12 and stats["n_visits"] == 20
    assert stats["visits"] == [{"visit": "V0", "month": 0, "n": 12}, {"visit": "V1_an", "month": 12, "n": 8}]
    it1, it2 = stats["variables"]["it1"], stats["variables"]["it2"]
    assert it1["n"] == {"rows": 20, "valid": 20, "patients": 12, "patients_2plus": 8, "baseline": 12}
    assert it1["timepoints"] == {"V0": 12, "V1_an": 8}
    assert it1["missing"] == {"all": 0.0, "baseline": 0.0, "in_instrument": 0.0}
    assert it2["n"]["valid"] == 12 and it2["n"]["patients_2plus"] == 0
    assert it2["missing"] == {"all": 40.0, "baseline": 0.0, "in_instrument": 40.0}     # not asked at one year
    total = stats["variables"]["total"]["stats"]["all"]
    assert total["n"] == 12 and total["min"] == 0.0 and total["max"] == 6.0             # it1 + (4 - it2)
    assert stats["variables"]["it1"]["qc"]["n_valid"] == 20                             # the count of facedata's own QC table


def test_a_count_from_1_to_4_is_never_written(cohort):
    result, schemas, stats = cohort
    assert [build_stats.masked(count, 5) for count in [0, 1, 4, 5, 60]] == [0, -1, -1, 5, 60]
    answers = stats["variables"]["it1"]["dist"]["all"]
    assert answers == {"kind": "levels", "x": [0.0, 1.0, 2.0, 3.0, 4.0], "n": [9, -1, -1, -1, -1]}
    assert stats["variables"]["sex"]["dist"]["all"] == {"kind": "levels", "x": ["female", "male"], "n": [10, -1]}
    rare = stats["variables"]["rare"]                                                    # 3 values: no figure at all
    assert rare["n"]["valid"] == -1 and rare["stats"]["all"] == {"n": -1} and rare["dist"] == {}
    assert "dist" not in stats["variables"]["it2"] or stats["variables"]["it2"]["dist"] == {}   # 12 values: figures, no chart
    assert stats["variables"]["it2"]["stats"]["all"]["n"] == 12


def test_the_values_of_a_text_column_are_never_written(cohort):
    result, schemas, stats = cohort
    note = stats["variables"]["note"]
    assert note["stats"]["all"] == {"n": 6, "n_distinct": 6} and note["dist"] == {}
    assert "private note" not in json.dumps(stats)                                      # nowhere in the file


def test_the_hierarchy_and_the_formula_of_a_score(cohort):
    result, schemas, stats = cohort
    blocks = blocks_of(schemas, stats)
    assert blocks["total"]["level"] == "score" and blocks["total"]["children"] == ["it1", "it2"]
    assert blocks["it1"]["level"] == "item" and blocks["it1"]["parents"] == {"total": 1}
    assert blocks["it2"]["parents"] == {"total": -1}                                     # reversed in the score
    assert blocks["note"]["level"] == "standalone" and blocks["sex"]["kind"] == "binary" and blocks["it1"]["kind"] == "ordinal"
    derivation = blocks["total"]["derivation"]
    assert derivation["method"] == "sum" and derivation["reverse"] == ["it2"] and derivation["stored_in"] == ["tot"]
    assert "Sum of 2 values (it1, it2); reversed first" in derivation["formula"] and "score_mismatch" in derivation["formula"]
    assert blocks["it1"]["source"]["columns"] == ["it1"] and blocks["sex"]["source"]["columns"] == ["sexe"]
    assert blocks["sex"]["categories"] == ["female", "male"] and blocks["sex"]["raw_codes"] == {"F": "female", "M": "male"}


def test_a_direction_is_written_or_derived_never_guessed(cohort):
    result, schemas, stats = cohort
    blocks = blocks_of(schemas, stats)
    written = {"demo": {"scores": {"tot*": {"higher_means": "more of it", "polarity": "worse", "basis": "stated", "source": "a note"}}}}
    assert build_json.annotation_of(written["demo"], "total")["polarity"] == "worse"    # a pattern with * covers the name
    total = build_json.direction_of("total", blocks["total"], written["demo"], blocks, written)
    assert total == {"higher_means": "more of it", "polarity": "worse", "basis": "stated", "source": "a note"}
    same = build_json.direction_of("it1", blocks["it1"], written["demo"], blocks, written)
    assert same["polarity"] == "worse" and same["basis"] == "formula" and same["in_score"] == {"score": "total", "keyed": "same"}
    turned = build_json.direction_of("it2", blocks["it2"], written["demo"], blocks, written)
    assert turned["polarity"] == "better" and turned["in_score"]["keyed"] == "reversed"
    assert build_json.direction_of("sex", blocks["sex"], {}, blocks, {}) == {"polarity": "not_applicable"}
    assert build_json.direction_of("total", blocks["total"], {}, blocks, {}) == {}       # no source: empty, and listed
    record = {"direction": {}, "construct": None}
    assert build_json.incomplete_fields(record, blocks["total"], {}) == ["construct", "direction"]
    generic = build_json.incomplete_fields({"direction": {}, "construct": None}, blocks["it2"], {})
    assert "meaning" in generic                                                          # "Demo item 2" says nothing


def test_codings_of_the_excel_dictionary_are_read_as_answer_labels():
    assert build_json.anchors_from("0:Absent; 1:Tolérable; 2:Pénible") == {"0": "Absent", "1": "Tolérable", "2": "Pénible"}
    assert build_json.anchors_from("Oui=1,Non=0,Non connu=9") == {"1": "Oui", "0": "Non", "9": "Non connu"}
    assert build_json.anchors_from("NUM (centimètre)") == {}


def test_the_json_has_one_line_per_variable_and_the_page_holds_it(tmp_path):
    dictionary = {"meta": {"title": "t"}, "cohorts": {}, "subjects": {}, "constructs": {}, "flags": {},
                  "instruments": {"demo": {"id": "demo"}},
                  "variables": {"it1": {"id": "it1", "label": "a </script> in a label <!-- and a comment"}, "total": {"id": "total"}}}
    target = tmp_path / "face_dictionary.json"
    build_json.write_json(dictionary, target)
    lines = target.read_text(encoding="utf-8").split("\n")
    assert json.loads(target.read_text(encoding="utf-8")) == dictionary
    assert [line for line in lines if line.startswith('"total":')] == ['"total":{"id":"total"}']
    template = tmp_path / "template.html"
    template.write_text('<script id="face-dictionary" type="application/json">%s</script>' % build_html.PLACE, encoding="utf-8")
    page = build_html.build(target, template, tmp_path / "page.html").read_text(encoding="utf-8")
    inside = page[page.index(">") + 1:page.rindex("</script>")]
    assert "</script" not in inside and "<!--" not in inside                             # the page cannot be cut by a label
    assert json.loads(inside) == dictionary


def test_the_page_reads_nothing_from_the_network():
    template = (ROOT / "dictionary" / "template.html").read_text(encoding="utf-8")
    assert template.count(build_html.PLACE) == 1
    addresses = [part for part in template.split('"') if part.startswith(("http://", "https://", "//"))]
    assert addresses == ["http://www.w3.org/2000/svg"]                                   # a name, not a download
    assert "<link" not in template and " src=" not in template and "@import" not in template


def test_annotations_name_instruments_scores_and_constructs_that_exist():
    """A hand-written annotation must not outlive the schema it describes."""
    delivered = {}
    for path in sorted(ROOT.glob("facedata/*/schemas/*/*.yaml")):
        with open(path, encoding="utf-8") as file:
            schema = yaml.load(file, Loader=yaml.BaseLoader)
        defaults = schema.get("defaults") or {}
        names = delivered.setdefault(schema["instrument"], set())
        names |= {name for name, variable in schema["variables"].items() if {**defaults, **(variable or {})}.get("keep") != "false"}
        names |= {name for name, score in (schema.get("scores") or {}).items() if (score or {}).get("keep") != "false"}
    constructs = set(build_json.read_yaml(ROOT / "dictionary" / "constructs.yaml"))
    problems = []
    for instrument, note in build_json.read_annotations().items():
        if instrument not in delivered:
            problems.append("%s: no schema has that name" % instrument)
            continue
        entries = [note] + [note.get("items") or {}]
        for kind in ["scores", "variables"]:
            for key, entry in (note.get(kind) or {}).items():
                entries.append(entry or {})
                if not fnmatch.filter(delivered[instrument], key):
                    problems.append("%s.%s.%s: no delivered name" % (instrument, kind, key))
        for entry in entries:
            if isinstance(entry.get("construct"), str) and entry["construct"] not in constructs:
                problems.append("%s: construct %s is not in constructs.yaml" % (instrument, entry["construct"]))
            if entry.get("higher_means") and not (entry.get("basis") and entry.get("source")):
                problems.append("%s: a direction without its basis and source" % instrument)
    assert problems == []


def test_the_cohorts_and_the_same_subjects_name_what_exists():
    """dictionary/cohorts.yaml describes the four cohorts; same_subject.yaml names instruments of the cohort it puts them in."""
    instruments_of = {cohort: set() for cohort in build_json.COHORTS}
    for path in sorted(ROOT.glob("facedata/*/schemas/*/*.yaml")):
        with open(path, encoding="utf-8") as file:
            instruments_of[path.parts[-4]].add(yaml.load(file, Loader=yaml.BaseLoader)["instrument"])
    abouts = build_json.read_yaml(ROOT / "dictionary" / "cohorts.yaml")
    assert sorted(abouts) == sorted(build_json.COHORTS)
    for cohort, about in abouts.items():
        assert {"population", "design", "traps", "tutorial"} <= set(about), cohort
        assert (ROOT / about["tutorial"]).exists(), about["tutorial"]
    problems = []
    for key, subject in build_json.read_yaml(ROOT / "dictionary" / "same_subject.yaml").items():
        assert subject["title"], key
        for cohort in build_json.COHORTS:
            problems += ["%s: %s is not an instrument of %s" % (key, name, cohort) for name in subject[cohort] if name not in instruments_of[cohort]]
    assert problems == []


def small_counts(block):
    """The counts of a cohort block that would show 1 to 4 patients or cells."""
    counts = [count for key, count in (block.get("n") or {}).items() if key != "rows"]
    counts += [count for key, count in (block.get("qc") or {}).items() if key != "n_rows"]
    for field in ["timepoints", "flags", "censored"]:
        counts += list((block.get(field) or {}).values())
    for scope in (block.get("dist") or {}).values():
        counts += scope["n"]
    return [count for count in counts if 0 < count < 5]


def test_the_committed_files_follow_the_data_rules():
    """What is committed holds aggregates only: no small count, no value of a text column, no label of an Excel dictionary."""
    dictionary = json.loads((COMMITTED / "face_dictionary.json").read_text(encoding="utf-8"))
    problems = []
    for name, record in dictionary["variables"].items():
        for cohort, block in record["cohorts"].items():
            if small_counts(block):
                problems.append("%s in %s: a count from 1 to 4" % (name, cohort))
            if block.get("kind", record["kind"]) == "text" and block.get("dist"):
                problems.append("%s in %s: the values of a text column" % (name, cohort))
            if "excel" in block or "answer_labels" in block:
                problems.append("%s in %s: a label of an Excel dictionary (built with excel_labels: true)" % (name, cohort))
            if block.get("n", {}).get("valid") == -1 and (block.get("missing") or {}).get("all") is not None:
                problems.append("%s in %s: a percentage that gives a masked count away" % (name, cohort))
    for path in sorted((ROOT / "dictionary" / "stats").glob("*.json")):
        for name, block in json.loads(path.read_text(encoding="utf-8"))["variables"].items():
            if small_counts(block):
                problems.append("%s in %s: a count from 1 to 4" % (name, path.name))
    for cohort, summary in dictionary["cohorts"].items():               # the guide writes these counts
        problems += ["visit %s of %s: a count from 1 to 4" % (visit["visit"], cohort) for visit in summary.get("visits", []) if 0 < visit["n"] < 5]
    assert problems == []


def test_the_committed_dictionary_describes_the_schemas_of_today():
    """A schema changed without a rebuild: run dictionary/build_json.py and dictionary/build_html.py (README of dictionary/)."""
    dictionary = json.loads((COMMITTED / "face_dictionary.json").read_text(encoding="utf-8"))
    for cohort, module in build_json.MODULES.items():
        delivered = set()
        for schema in load_schemas(module.SCHEMAS).values():
            specs = {**schema["variables"], **schema.get("scores", {})}
            delivered |= {name for name, spec in specs.items() if spec.get("keep", True)}
        written = {name for name, record in dictionary["variables"].items()
                   if cohort in record["cohorts"] and record["cohorts"][cohort].get("level", record["level"]) not in ("key", "companion")}
        assert written == delivered, cohort
    page = (COMMITTED / "FACE-data-dictionary.html").read_text(encoding="utf-8")
    mark = '<script id="face-dictionary" type="application/json">'
    start = page.index(mark) + len(mark)
    assert json.loads(page[start:page.index("</script>", start)]) == dictionary          # the page and the JSON say the same
