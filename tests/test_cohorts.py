"""The same instrument in two cohorts: the same schema, or a difference that is written down.

A schema of FACE SZ that has the name of a FACE BP schema starts as a copy of
it (docs/ARCHITECTURE.md, section 9). The two must say the same thing, so
that the tables of the two cohorts can be put together. Where the SZ data
require another reading, facedata/sz/differences.yaml gives the reason.
"""

from pathlib import Path

import yaml

PACKAGE = Path(__file__).parent.parent / "facedata"
COMPARED = ["defaults", "variables", "scores", "version"]      # not the notes, the title, the tab or the status


def read_as_written(folder):
    """Every schema file of a cohort, as written: {instrument name: content}."""
    schemas = {}
    for path in sorted(Path(folder).glob("*/*.yaml")):
        with open(path, encoding="utf-8") as file:
            schema = yaml.load(file, Loader=yaml.BaseLoader)
        schemas[schema.get("instrument", path.stem)] = schema
    return schemas


def blocks_that_differ(first, second):
    """The names of the compared blocks that are not the same in the two schemas."""
    return [block for block in COMPARED if first.get(block) != second.get(block)]


def test_blocks_that_differ():
    one = {"notes": "BP", "variables": {"it1": {"range": ["0", "3"]}}, "scores": {"total": {"sum": ["it1"]}}}
    same = {"notes": "SZ, other numbers", "variables": {"it1": {"range": ["0", "3"]}}, "scores": {"total": {"sum": ["it1"]}}}
    other = {"notes": "SZ", "variables": {"it1": {"range": ["0", "4"]}}, "scores": {"total": {"sum": ["it1"]}}}
    assert blocks_that_differ(one, same) == []
    assert blocks_that_differ(one, other) == ["variables"]


def test_shared_instruments_are_the_same_in_bp_and_sz():
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    with open(PACKAGE / "sz" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    shared = sorted(set(bp) & set(sz))
    differing = {name: blocks_that_differ(bp[name], sz[name]) for name in shared}
    differing = {name: blocks for name, blocks in differing.items() if blocks}
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/sz/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is the BP one (or has another name)"


def test_shared_instruments_are_the_same_in_dr():
    """A DR schema is compared with the BP schema of the same name, or with the SZ one when BP has none."""
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    dr = read_as_written(PACKAGE / "dr" / "schemas")
    with open(PACKAGE / "dr" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    differing = {}
    for name in sorted(dr):
        reference = bp.get(name, sz.get(name))
        if reference is not None and blocks_that_differ(reference, dr[name]):
            differing[name] = blocks_that_differ(reference, dr[name])
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/dr/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is the BP or SZ one (or has another name)"


def test_shared_instruments_are_the_same_in_asp():
    """An ASP schema is compared with the BP schema of the same name, then the SZ one, then the DR one."""
    bp = read_as_written(PACKAGE / "bp" / "schemas")
    sz = read_as_written(PACKAGE / "sz" / "schemas")
    dr = read_as_written(PACKAGE / "dr" / "schemas")
    asp = read_as_written(PACKAGE / "asp" / "schemas")
    with open(PACKAGE / "asp" / "differences.yaml", encoding="utf-8") as file:
        listed = yaml.load(file, Loader=yaml.BaseLoader) or {}
    differing = {}
    for name in sorted(asp):
        reference = bp.get(name, sz.get(name, dr.get(name)))
        if reference is not None and blocks_that_differ(reference, asp[name]):
            differing[name] = blocks_that_differ(reference, asp[name])
    not_explained = {name: blocks for name, blocks in differing.items() if name not in listed}
    assert not_explained == {}, "add the reason to facedata/asp/differences.yaml, or bring the schemas together"
    no_longer_true = [name for name in listed if name not in differing]
    assert no_longer_true == [], "listed in differences.yaml, but the schema is that of the other cohort (or has another name)"
