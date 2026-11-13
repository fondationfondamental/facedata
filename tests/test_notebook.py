"""Notebooks are saved without their results: a result under a cell is patient data."""

import ast
import json
from pathlib import Path

NOTEBOOKS = sorted(Path(__file__).parent.parent.glob("*.ipynb"))


def test_notebooks_are_saved_without_results():
    assert len(NOTEBOOKS) >= 1
    for path in NOTEBOOKS:
        cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
        code = [cell for cell in cells if cell["cell_type"] == "code"]
        assert len(code) > 0, path.name
        for cell in code:
            # Clear the results before saving (Edit > Clear Outputs of All Cells): they hold patient rows and figures.
            assert cell["outputs"] == [] and cell["execution_count"] is None, f"{path.name} is saved with results"
            ast.parse("".join(cell["source"]))               # every cell is Python that can be read
