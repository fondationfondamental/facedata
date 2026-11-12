"""The dictionary helper and the coverage table."""

import pandas as pd

from facedata import qc
from facedata.read import prepare_visits, read_extraction
from facedata.schema import load_schemas
from facedata.thesaurus import describe, draft_schema, expand_range, read_thesaurus
from test_pipeline import EXTRACTION, SCHEMA


def test_expand_range():
    assert expand_range("STAYA01 à STAYA03") == ["STAYA01", "STAYA02", "STAYA03"]
    assert expand_range("SIMIL09_wais4  à  SIMIL10_wais4") == ["SIMIL09_wais4", "SIMIL10_wais4"]
    assert expand_range("MSD01A_ à MSD02B_") == ["MSD01A_", "MSD01B_", "MSD02A_", "MSD02B_"]
    assert expand_range("MADRS_") == ["MADRS_"]
    assert expand_range("Depuis la dernière visite à la visite de suivi") == ["Depuis la dernière visite à la visite de suivi"]


def write_workbook(path):
    rows = [["TEST TAB", "", "", "", "", ""],
            ["NOM VARIABLE EXTRACTION", "NOM VARIABLE INFORMATIQUE", "LABEL", "COCHER", "CODAGE", "TABLE"],
            ["Demo", "", "", "", "", ""],
            ["IT1 à IT2", "item", "An item", "", "0=No; 1=Yes", "QS"],
            ["GLU", "glucose", "Fasting glucose", "", "", "LB"],
            ["OLD", "gone", "No longer extracted", "", "", ""]]
    pd.DataFrame(rows).to_excel(path, sheet_name="TEST", header=False, index=False)


def test_read_thesaurus_and_draft_schema(tmp_path):
    write_workbook(tmp_path / "thesaurus.xlsx")
    (tmp_path / "extraction.tsv").write_text(EXTRACTION, encoding="utf-8")
    thesaurus = read_thesaurus(tmp_path / "thesaurus.xlsx")
    assert list(thesaurus["name"]) == ["it1", "it2", "glu", "old"]
    assert set(thesaurus["section"]) == {"Demo"}
    raw = read_extraction(tmp_path / "extraction.tsv")
    draft = draft_schema(thesaurus, raw, "TEST", "Demo")
    assert '  it1: {label: "An item", type: TODO}' in draft
    assert "# dictionary coding: 0=No; 1=Yes" in draft
    assert "# old: not in the extraction" in draft
    assert describe(raw["glu"]) == "5 filled; 3 numbers from 0.95 to 300"      # "<0.5" is not a plain number


def test_coverage(tmp_path):
    (tmp_path / "tab").mkdir()
    (tmp_path / "tab" / "demo.yaml").write_text(SCHEMA, encoding="utf-8")
    (tmp_path / "extraction.tsv").write_text(EXTRACTION + "P3\tV0\t2\t9\t2017-01-01\t01\t1\t1\t2\t5\tmmol/L\n", encoding="utf-8")
    raw, keys, flags = prepare_visits(read_extraction(tmp_path / "extraction.tsv"))
    raw["extra"] = "1"
    table = qc.coverage(raw, keys, load_schemas(tmp_path), {"it1", "old"}, {"extra": "not needed", "gone": "retired"})
    status = table.set_index("column")["status"].to_dict()
    assert status["it1"] == status["glu_unit"] == status["svdtc"] == "covered"
    assert status["extra"] == "ignored"
    assert status["gone"] == "missing_in_extraction"
    assert status["old"] == "thesaurus_only"
    assert table["n_unread"].sum() == 0
