"""The guide and the command `facedata` (facedata/guide.py): find, show, init, and what ships.

The searches run on a made-up dictionary of a few records. The last tests read
the committed files, which hold aggregates only.
"""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from facedata import guide

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "dictionary"))

import build_guide  # noqa: E402

DICTIONARY = {
    "instruments": {
        "madrs": {"title": "Montgomery-Asberg Depression Rating Scale", "tab": "HETERO", "construct": "depression",
                  "cohorts": {"bp": {}, "dr": {}}, "common": {"stack": "yes"}, "variables": ["madrs01", "madrs_total"]},
        "calgary": {"title": "Calgary Depression Scale", "tab": "HETERO", "construct": "depression",
                    "cohorts": {"sz": {}}, "variables": ["calgary_sum8"]},
    },
    "variables": {
        "madrs01": {"label": "Apparent sadness", "level": "item", "instrument": "madrs", "cohorts": {"bp": {}, "dr": {}}},
        "madrs_total": {"label": "MADRS total", "meaning": "Sum of the ten items", "level": "score", "instrument": "madrs",
                        "construct": "depression", "cohorts": {"bp": {}, "dr": {}}},
        "calgary_sum8": {"label": "Calgary, sum of eight items", "level": "score", "instrument": "calgary",
                         "construct": "depression", "cohorts": {"sz": {}}},
    },
}


def test_find_keeps_the_variables_that_hold_every_word():
    assert list(guide.find("depression", dictionary=DICTIONARY)["variable"]) == ["madrs01", "madrs_total", "calgary_sum8"]
    assert list(guide.find("depression sum", dictionary=DICTIONARY)["variable"]) == ["madrs_total", "calgary_sum8"]
    assert list(guide.find("depression", cohort="dr", level="score", dictionary=DICTIONARY)["variable"]) == ["madrs_total"]
    assert list(guide.find(["SUM", "ten"], dictionary=DICTIONARY)["variable"]) == ["madrs_total"]      # case does not matter
    assert list(guide.find("depression", level="item", dictionary=DICTIONARY)["cohorts"]) == ["bp,dr"]
    assert guide.find("mania", dictionary=DICTIONARY).empty


def test_a_record_is_found_by_its_id_and_a_wrong_id_names_the_closest():
    assert guide.variable("madrs_total", DICTIONARY)["level"] == "score"
    assert guide.instrument("calgary", DICTIONARY)["cohorts"] == {"sz": {}}
    with pytest.raises(KeyError, match="did you mean madrs_total"):
        guide.variable("madrs_totl", DICTIONARY)
    assert list(json.loads(guide.show(["madrs", "madrs_total"], DICTIONARY))) == ["madrs", "madrs_total"]
    assert list(json.loads(guide.show(["madrs"], DICTIONARY))["madrs"]) == ["instrument"]
    with_dist = {**DICTIONARY, "variables": {"x": {"cohorts": {"bp": {"n": {"valid": 30}, "dist": {"all": {}}}}}}}
    assert json.loads(guide.show(["x"], with_dist))["x"]["variable"]["cohorts"]["bp"] == {"n": {"valid": 30}}
    assert "dist" in json.loads(guide.show(["x"], with_dist, full=True))["x"]["variable"]["cohorts"]["bp"]


def test_instruments_of_a_cohort_or_of_several():
    table = guide.instruments(dictionary=DICTIONARY)
    assert list(table["instrument"]) == ["madrs", "calgary"]
    assert list(table["n_variables"]) == [2, 1]
    assert list(guide.instruments(cohort="sz", dictionary=DICTIONARY)["instrument"]) == ["calgary"]
    assert list(guide.instruments(shared=True, dictionary=DICTIONARY)["stack"]) == ["yes"]


def test_init_writes_one_block_and_keeps_the_rest(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# My project\n\nOur own rules.\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("Use pytest.\n", encoding="utf-8")
    assert guide.init(tmp_path) == ["AGENTS.md: the facedata block is added", "CLAUDE.md: now reads AGENTS.md"]
    assert guide.init(tmp_path) == ["AGENTS.md: the facedata block is updated", "CLAUDE.md: already reads AGENTS.md"]
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.startswith("# My project\n\nOur own rules.\n\n<!-- facedata:start")
    assert agents.count(guide.START) == 1 and agents.count(guide.END) == 1 and agents.endswith(guide.END + "\n")
    assert "facedata guide" in agents and "{version}" not in agents
    claude = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude.startswith("Use pytest.\n\n") and claude.count("@AGENTS.md") == 1


def test_init_in_an_empty_project(tmp_path):
    assert guide.init(tmp_path) == ["AGENTS.md: the facedata block is written", "CLAUDE.md: now reads AGENTS.md"]
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8").startswith(guide.START)


def test_the_command_line(tmp_path, capsys):
    guide.main(["init", str(tmp_path)])
    assert "AGENTS.md: the facedata block is written" in capsys.readouterr().out
    guide.main(["files"])
    assert "face_dictionary.json" in capsys.readouterr().out
    guide.main(["guide"])
    assert capsys.readouterr().out.startswith("# FACE cohorts")
    guide.main(["guide", "--section", "4"])
    section = capsys.readouterr().out
    assert section.startswith("## 4. The cohorts") and "## 5." not in section
    guide.main(["guide", "--section", "5.2"])
    section = capsys.readouterr().out
    assert section.startswith("### 5.2 The same subject") and "### 5.3" not in section
    guide.main(["guide", "--section", "8"])
    assert capsys.readouterr().out.startswith("## 8. Further reading")
    with pytest.raises(SystemExit, match="no section 9"):
        guide.main(["guide", "--section", "9"])
    with pytest.raises(SystemExit, match="no variable named 'not_a_variable'"):
        guide.main(["show", "not_a_variable"])
    with pytest.raises(SystemExit):
        guide.main(["find", "x", "--cohort", "xx"])                                      # not a cohort


def test_the_committed_guide_is_the_one_the_committed_dictionary_gives():
    """The guide is stale: run dictionary/build_guide.py (dictionary/README.md)."""
    dictionary = guide.read_dictionary()
    assert build_guide.build(dictionary) == guide.GUIDE.read_text(encoding="utf-8")


def test_the_guide_the_block_and_the_command_ship_with_the_package():
    for path in [guide.GUIDE, guide.DICTIONARY, guide.PAGE, guide.BLOCK, ROOT / "facedata" / "__main__.py"]:
        assert path.exists(), path
        ignored = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", str(path)]).returncode == 0
        assert not ignored, path                                     # the wheel takes what git does not ignore
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["scripts"]["facedata"] == "facedata.guide:main"
