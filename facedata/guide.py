"""Find your way in the FACE data: the guide, the data dictionary, the agent instructions.

After installing facedata in a research project, run once in that project:

    facedata init        # AGENTS.md (and CLAUDE.md) tell coding agents where all this is

Then, from the terminal (or `python -m facedata ...`, `uv run facedata ...`):

    facedata guide [--section 4]           # the four cohorts, their traps, what they share
    facedata find depression --cohort dr   # variables whose id, label or meaning holds the words
    facedata show madrs_total madrs        # the records of variables or instruments (JSON)
    facedata instruments --cohort sz       # the instruments of a cohort (--shared: of two cohorts or more)
    facedata page                          # the dictionary page in the browser
    facedata files                         # where the guide, the JSON and the page are

From Python, the same as tables and dicts: `guide.find(...)`, `guide.variable(...)`,
`guide.instrument(...)`, `guide.instruments(...)`. Each reads the 18 MB JSON;
to ask many questions, read it once with `read_dictionary()` and pass it on.
"""

import argparse
import difflib
import json
import os
import sys
import webbrowser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import pandas as pd

FOLDER = Path(__file__).parent
GUIDE = FOLDER / "dictionary" / "FACE-guide.md"
DICTIONARY = FOLDER / "dictionary" / "face_dictionary.json"
PAGE = FOLDER / "dictionary" / "FACE-data-dictionary.html"
BLOCK = FOLDER / "agents.md"
COHORTS = ["bp", "sz", "dr", "asp"]
START = "<!-- facedata:start"
END = "<!-- facedata:end -->"


def files():
    """Where the guide, the dictionary (JSON) and its page are on this computer."""
    return {"guide": GUIDE, "dictionary": DICTIONARY, "page": PAGE}


def read_dictionary(path=DICTIONARY):
    """The whole data dictionary as a dict: meta, cohorts, subjects, constructs, flags, instruments, variables."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def record_of(name, kind, dictionary):
    """The record of a variable or an instrument; the error names the closest ids."""
    records = dictionary[kind]
    if name not in records:
        close = difflib.get_close_matches(name, list(records), n=5)
        raise KeyError(f"no {kind[:-1]} named {name!r}" + (f"; did you mean {', '.join(close)}?" if close else ""))
    return records[name]


def variable(name, dictionary=None):
    """The record of one variable: meaning, direction, harmonisation, and one block per cohort."""
    return record_of(name, "variables", dictionary or read_dictionary())


def instrument(name, dictionary=None):
    """The record of one instrument: description, reference, caveats (flags), across cohorts (common), schema notes."""
    return record_of(name, "instruments", dictionary or read_dictionary())


def find(words, cohort=None, level=None, dictionary=None):
    """The variables whose id, label, meaning, construct, instrument or instrument title holds every word.

    words: one string ("depression score") or a list. cohort: bp, sz, dr or asp.
    level: item, subscore, score, standalone, companion or key.
    Returns a table: variable, instrument, level, cohorts, label.
    """
    dictionary = dictionary or read_dictionary()
    words = (words.split() if isinstance(words, str) else list(words))
    rows = []
    for name, record in dictionary["variables"].items():
        if cohort and cohort not in record["cohorts"]:
            continue
        if level and record.get("level") != level:
            continue
        title = dictionary["instruments"].get(record.get("instrument"), {}).get("title", "")
        text = " ".join(str(part or "") for part in [name, record.get("label"), record.get("meaning"), record.get("construct"),
                                                      record.get("instrument"), title]).lower()
        if all(word.lower() in text for word in words):
            rows.append({"variable": name, "instrument": record.get("instrument"), "level": record.get("level"),
                         "cohorts": ",".join(c for c in COHORTS if c in record["cohorts"]), "label": record.get("label")})
    return pd.DataFrame(rows, columns=["variable", "instrument", "level", "cohorts", "label"])


def instruments(cohort=None, shared=False, dictionary=None):
    """The instruments, one row each: title, tab, cohorts, construct, stack verdict across cohorts, variables.

    cohort: only the instruments of that cohort. shared: only those that two cohorts or more deliver.
    """
    dictionary = dictionary or read_dictionary()
    rows = []
    for name, record in dictionary["instruments"].items():
        present = [c for c in COHORTS if c in record["cohorts"]]
        if (cohort and cohort not in present) or (shared and len(present) < 2):
            continue
        rows.append({"instrument": name, "title": record.get("title"), "tab": record.get("tab"), "cohorts": ",".join(present),
                     "construct": record.get("construct"), "stack": (record.get("common") or {}).get("stack"),
                     "n_variables": len(record.get("variables", []))})
    return pd.DataFrame(rows, columns=["instrument", "title", "tab", "cohorts", "construct", "stack", "n_variables"])


def package_version():
    """The installed version of facedata, or "unknown" in a copy that is not installed."""
    try:
        return version("facedata")
    except PackageNotFoundError:
        return "unknown"


def put_block(path, block):
    """Write the block between its markers in a file: replaced if there, added at the end if not. Says what it did."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if START in text and END in text:
        before, rest = text.split(START, 1)
        after = rest.split(END, 1)[1]
        path.write_text(before + block.strip() + after, encoding="utf-8")
        return f"{path.name}: the facedata block is updated"
    path.write_text(text.rstrip() + ("\n\n" if text.strip() else "") + block.strip() + "\n", encoding="utf-8")
    return f"{path.name}: the facedata block is {'added' if text.strip() else 'written'}"


def init(folder="."):
    """Tell the coding agents of a project about facedata: a block in AGENTS.md, and CLAUDE.md made to read it.

    Run it again after an upgrade: the block is replaced, the rest of the files is kept.
    Returns what was done, one sentence per file.
    """
    folder = Path(folder)
    block = BLOCK.read_text(encoding="utf-8").replace("{version}", package_version())
    said = [put_block(folder / "AGENTS.md", block)]
    claude = folder / "CLAUDE.md"
    text = claude.read_text(encoding="utf-8") if claude.exists() else ""
    if "@AGENTS.md" in text:
        said.append("CLAUDE.md: already reads AGENTS.md")
    else:
        line = "<!-- Claude Code reads AGENTS.md through the next line (facedata init) -->\n@AGENTS.md\n"
        claude.write_text(text.rstrip() + ("\n\n" if text.strip() else "") + line, encoding="utf-8")
        said.append("CLAUDE.md: now reads AGENTS.md")
    return said


def show(names, dictionary, full=False):
    """What `facedata show` prints: one JSON object, name -> {"variable": record, "instrument": record}.

    full: keep the distributions (dist) of the cohort blocks, which are long and left out by default.
    """
    shown = {}
    for name in names:
        found = {kind[:-1]: dictionary[kind][name] for kind in ["variables", "instruments"] if name in dictionary[kind]}
        if not found:
            record_of(name, "variables", dictionary)      # raises, with the closest ids
        if "variable" in found and not full:
            blocks = found["variable"]["cohorts"]
            found["variable"] = {**found["variable"], "cohorts": {c: {k: v for k, v in b.items() if k != "dist"} for c, b in blocks.items()}}
        shown[name] = found
    return json.dumps(shown, ensure_ascii=False, indent=1)


def guide_text(section=None):
    """The guide, or one of its sections: 4 is "## 4. The cohorts", 5.2 is "### 5.2 The same subject..."."""
    text = GUIDE.read_text(encoding="utf-8")
    if section is None:
        return text
    marker = "\n### " if "." in section else "\n## "
    parts = [part.split("\n## ")[0] for part in text.split(marker) if part.startswith((section + " ", section + ". "))]
    if not parts:
        raise KeyError(f"the guide has no section {section}: try 1 to 8, or 5.1 to 5.4")
    return marker.strip() + " " + parts[0].rstrip()


def main(argv=None):
    """The command line: facedata <command> (see the docstring of this module)."""
    parser = argparse.ArgumentParser(prog="facedata", description="Find your way in the FACE data. Start with: facedata guide")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="write the facedata block into AGENTS.md and CLAUDE.md").add_argument("folder", nargs="?", default=".")
    commands.add_parser("guide", help="print the guide to the four cohorts (Markdown)").add_argument(
        "--section", help="only one section: 4 (the cohorts), 5 (across cohorts), 5.2...")
    search = commands.add_parser("find", help="variables whose id, label or meaning holds every word")
    search.add_argument("words", nargs="+")
    search.add_argument("--cohort", choices=COHORTS)
    search.add_argument("--level", choices=["item", "subscore", "score", "standalone", "companion", "key"])
    record = commands.add_parser("show", help="the records of variables or instruments, as JSON")
    record.add_argument("names", nargs="+")
    record.add_argument("--full", action="store_true", help="keep the distributions")
    listing = commands.add_parser("instruments", help="the instruments, with their cohorts and stack verdict")
    listing.add_argument("--cohort", choices=COHORTS)
    listing.add_argument("--shared", action="store_true", help="only those of two cohorts or more")
    commands.add_parser("page", help="open the dictionary page in the browser")
    commands.add_parser("files", help="where the guide, the JSON and the page are")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "init":
            print("\n".join(init(arguments.folder)))
            print("Next: read `facedata guide`, or open the page with `facedata page`.")
        elif arguments.command == "guide":
            print(guide_text(arguments.section))
        elif arguments.command == "find":
            table = find(arguments.words, arguments.cohort, arguments.level)
            print(f"{len(table)} variables" + (":\n" + table.to_string(index=False, max_colwidth=70) if len(table) else ""))
        elif arguments.command == "show":
            print(show(arguments.names, read_dictionary(), arguments.full))
        elif arguments.command == "instruments":
            table = instruments(arguments.cohort, arguments.shared)
            print(f"{len(table)} instruments:\n" + table.to_string(index=False, max_colwidth=60))
        elif arguments.command == "page":
            webbrowser.open(PAGE.as_uri())
            print(PAGE)
        elif arguments.command == "files":
            print("\n".join(f"{key}: {path}" for key, path in files().items()))
    except KeyError as error:
        sys.exit(error.args[0])
    except BrokenPipeError:                          # the reader (head, less) stopped early
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
