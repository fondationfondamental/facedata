"""The guide to the FACE cohorts, one Markdown file for researchers and coding agents.

Step 3 of 4 (dictionary/README.md). Reads facedata/dictionary/face_dictionary.json
only, so it runs without the extractions, and fills dictionary/guide_template.md
with tables built from it: the cohorts, the instruments they share, the same
subject under other instruments, the editions, the constructs, every
instrument and the flags. Writes facedata/dictionary/FACE-guide.md, which ships
with the package (`facedata guide` prints it).

    .venv/bin/python dictionary/build_guide.py
"""

import json
from pathlib import Path

FOLDER = Path(__file__).resolve().parent
PACKAGE = FOLDER.parent / "facedata" / "dictionary"
COHORTS = ["bp", "sz", "dr", "asp"]
REPO = "https://github.com/fondationfondamental/facedata/blob/main"


def number(count):
    """A count as the guide writes it: -1 is a count from 1 to 4, never shown."""
    if count is None:
        return "?"
    return "fewer than 5" if count == -1 else f"{count:,}"


def cell(text):
    """Text that can sit in a Markdown table cell."""
    return " ".join(str(text).split()).replace("|", "/")


def cohorts_present(record):
    """The cohorts of an instrument record, in the order of COHORTS, as BP, SZ..."""
    return ", ".join(cohort.upper() for cohort in COHORTS if cohort in record["cohorts"])


def cohort_section(cohort, summary, variables):
    """What the guide says about one cohort."""
    about = summary.get("about") or {}
    age = (((variables.get("age_at_inclusion") or {}).get("cohorts") or {}).get(cohort) or {}).get("stats", {}).get("all", {})
    diagnoses = (((variables.get("diagnosis") or {}).get("cohorts") or {}).get(cohort) or {}).get("categories") or []
    visits = ", ".join(f"{visit['visit']} {number(visit['n'])}" for visit in summary.get("visits", []))
    tables = ", ".join(f"`{name}` {number(rows)} rows" for name, (rows, columns) in summary.get("tables", {}).items())
    lines = [f"### {summary['title']}", "", " ".join(about.get("population", "").split()), ""]
    lines.append(f"- **Patients:** {number(summary.get('n_patients'))}; age at inclusion: median {age.get('median', 0):.0f}, "
                 f"quartiles {age.get('p25', 0):.0f} to {age.get('p75', 0):.0f} years." if age else f"- **Patients:** {number(summary.get('n_patients'))}.")
    if diagnoses:
        lines.append("- **`diagnosis`** (in `patients`): " + ", ".join(f"`{name}`" for name in diagnoses) + ".")
    lines.append(f"- **Visits:** {' '.join(about.get('design', '').split())}")
    lines.append(f"  Visits in the extraction: {visits}.")
    lines.append(f"- **Delivered:** {summary.get('n_instruments')} instruments, {summary.get('n_variables'):,} variables; {tables}.")
    lines.append(f"- **Extraction:** `{Path(summary.get('extraction', '')).name}`; figures computed on {summary.get('computed', '?')}.")
    lines.append(f"- **Load it:** `from facedata import {cohort}; result = {cohort}.load(path)`.")
    if about.get("tutorial"):
        lines.append(f"- **Tutorial:** [{about['tutorial']}]({REPO}/{about['tutorial']}).")
    lines += ["", "The traps of this cohort:", ""]
    lines += [f"{position}. {' '.join(trap.split())}" for position, trap in enumerate(about.get("traps", []), start=1)]
    return "\n".join(lines)


def shared_section(instruments):
    """The instruments of the catalogue (common_instruments.yaml), one row each, by domain."""
    entries = {}
    for name, record in instruments.items():
        common = record.get("common")
        if not common:
            continue
        entry = entries.setdefault(common["entry"], {"common": common, "title": record.get("title", ""), "ids": {}})
        for cohort in record["cohorts"]:
            entry["ids"][cohort] = name
        if name == common["entry"]:
            entry["title"] = record.get("title", "")
    lines = []
    domains = list(dict.fromkeys(entry["common"]["domain"] for entry in entries.values()))
    for domain in domains:
        lines += [f"**{domain}**", "", "| Instrument | Title | BP | SZ | DR | ASP | Stack | Use |", "|---|---|---|---|---|---|---|---|"]
        for key, entry in entries.items():
            if entry["common"]["domain"] != domain:
                continue
            where = ["–" if cohort not in entry["ids"] else "✓" if entry["ids"][cohort] == key else f"`{entry['ids'][cohort]}`" for cohort in COHORTS]
            use = ", ".join(f"`{name}`" for name in entry["common"].get("use") or []) or "–"
            lines.append(f"| `{key}` | {cell(entry['title'])} | " + " | ".join(where) + f" | {entry['common']['stack']} | {use} |")
        lines.append("")
    return "\n".join(lines).rstrip()


def subjects_section(subjects):
    """The same subject under other instruments, as a table and its notes."""
    lines = ["| Subject | BP | SZ | DR | ASP |", "|---|---|---|---|---|"]
    for subject in subjects.values():
        names = [", ".join(f"`{name}`" for name in subject.get(cohort) or []) or "–" for cohort in COHORTS]
        lines.append(f"| {cell(subject['title'])} | " + " | ".join(names) + " |")
    notes = [f"- **{subject['title']}.** {' '.join(subject['note'].split())}" for subject in subjects.values() if subject.get("note")]
    return "\n".join(lines + [""] + notes)


def editions_section(instruments):
    """The companion columns that say which edition or form a visit used, and the instruments of each."""
    columns = {}
    for name, record in instruments.items():
        for cohort, block in record["cohorts"].items():
            edition = block.get("edition")
            if edition:
                entry = columns.setdefault(edition["column"], {"cohorts": set(), "names": {}})
                entry["cohorts"].add(cohort)
                values = entry["names"].setdefault(name, set())
                values.update(edition.get("values") or [])
    lines = []
    for column, entry in columns.items():
        where = ", ".join(cohort.upper() for cohort in COHORTS if cohort in entry["cohorts"])
        if column == "visit_form":
            pairs = sum(1 for name in entry["names"] if name.endswith("_fu"))
            lines.append(f"- `{column}` ({where}): the inclusion form and the follow-up form of the same questions are two "
                         f"instruments ({len(entry['names'])} of them, about {pairs} pairs such as `anxiety_v0` and `anxiety_fu`). "
                         "The inclusion form asks about the whole life, the follow-up form about the time since the last visit.")
            continue
        names = ", ".join(f"`{name}`" + (f" ({', '.join(sorted(values))})" if values and values != {name} else "")
                          for name, values in entry["names"].items())
        lines.append(f"- `{column}` ({where}): {names}.")
    return "\n".join(lines)


def constructs_section(constructs, instruments):
    """Each construct with the instruments that measure it, per cohort, by area."""
    by_construct = {}
    for name, record in instruments.items():
        if record.get("construct"):
            for cohort in record["cohorts"]:
                by_construct.setdefault(record["construct"], {}).setdefault(cohort, []).append(name)
    lines = []
    areas = list(dict.fromkeys(construct["area"] for construct in constructs.values()))
    for area in areas:
        keys = [key for key, construct in constructs.items() if construct["area"] == area and key in by_construct]
        if not keys:
            continue
        lines += [f"**{area}**", ""]
        for key in keys:
            parts = [f"{cohort.upper()} " + ", ".join(f"`{name}`" for name in by_construct[key][cohort])
                     for cohort in COHORTS if cohort in by_construct[key]]
            lines.append(f"- `{key}` ({constructs[key]['label']}): " + "; ".join(parts) + ".")
        lines.append("")
    return "\n".join(lines).rstrip()


def instruments_section(instruments, tabs):
    """Every instrument, by tab of the merged view, with its cohorts."""
    lines = []
    for tab in tabs + sorted({record.get("tab") for record in instruments.values()} - set(tabs) - {None}):
        names = [name for name, record in instruments.items() if record.get("tab") == tab]
        if not names:
            continue
        lines += [f"**{tab}** ({len(names)})", "", "| Instrument | Title | Cohorts |", "|---|---|---|"]
        lines += [f"| `{name}` | {cell(instruments[name].get('title', ''))} | {cohorts_present(instruments[name])} |" for name in names]
        lines.append("")
    return "\n".join(lines).rstrip()


def flags_section(flags):
    """The flag codes as a table."""
    lines = ["| Flag | Severity | Meaning |", "|---|---|---|"]
    lines += [f"| `{code}` | {flag['severity']} | {cell(flag['meaning'])} |" for code, flag in flags.items()]
    return "\n".join(lines)


def build(dictionary):
    """The guide as text."""
    meta = dictionary["meta"]
    instruments = dictionary["instruments"]
    parts = {
        "generated": meta["generated"], "git": meta["git"], "repo": REPO,
        "n_instruments": f"{meta['n_instruments']:,}", "n_variables": f"{meta['n_variables']:,}",
        "cohorts": "\n\n".join(cohort_section(cohort, dictionary["cohorts"][cohort], dictionary["variables"]) for cohort in COHORTS),
        "shared": shared_section(instruments),
        "subjects": subjects_section(dictionary.get("subjects") or {}),
        "editions": editions_section(instruments),
        "constructs": constructs_section(dictionary["constructs"], instruments),
        "instruments": instruments_section(instruments, meta["tabs_all"]),
        "flags": flags_section(dictionary["flags"]),
    }
    text = (FOLDER / "guide_template.md").read_text(encoding="utf-8")
    for key, value in parts.items():
        text = text.replace("{" + key + "}", str(value))
    return text


def main():
    dictionary = json.loads((PACKAGE / "face_dictionary.json").read_text(encoding="utf-8"))
    target = PACKAGE / "FACE-guide.md"
    text = build(dictionary)
    target.write_text(text, encoding="utf-8")
    print("%d lines, %.0f kB -> %s" % (text.count("\n"), len(text.encode("utf-8")) / 1e3, target.relative_to(FOLDER.parent)))


if __name__ == "__main__":
    main()
