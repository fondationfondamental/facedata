"""The data dictionary (thesaurus): a helper to start a schema, never used by load().

Its labels and formulas are sometimes wrong, so a schema drafted from it must
be checked against the data (docs/SCHEMA_SPEC.md, section 14).
"""

import re

import pandas as pd

ONE_END = r"(\D*)(\d+)([A-Za-z]?)(\w*)"       # STAYA + 01, MSD + 01 + A + _, SIMIL + 01 + _wais4


def expand_range(name):
    """'STAYA01 à STAYA20' -> ['STAYA01', ..., 'STAYA20']. Any other name -> [name]."""
    ends = re.split(r"\s+à\s+", name.strip())
    if len(ends) != 2:
        return [name.strip()]
    first, last = re.fullmatch(ONE_END, ends[0]), re.fullmatch(ONE_END, ends[1])
    if first is None or last is None:
        return [name.strip()]
    start, number, letter, tail = first.groups()
    if (start, tail) != (last.group(1), last.group(4)):
        return [name.strip()]
    letters = [chr(code) for code in range(ord(letter), ord(last.group(3)) + 1)] if letter else [""]
    names = []
    for value in range(int(number), int(last.group(2)) + 1):
        for one_letter in letters:
            names.append(start + str(value).zfill(len(number)) + one_letter + tail)
    return names


def read_thesaurus(path):
    """The dictionary workbook as one table: tab, section, name, label, coding.

    Names are in lower case, as in the extraction, and item ranges are expanded.
    """
    sheets = pd.read_excel(path, sheet_name=None, header=None, dtype=str)
    lines = []
    for tab, sheet in sheets.items():
        sheet = sheet.fillna("")
        if (sheet[0].str.strip().str.upper() == "CODELIST").any():    # one tab has a code-list column before the names
            sheet = sheet.iloc[:, 1:]
        if sheet.shape[1] < 5:                     # contents and instructions tabs
            continue
        section = ""
        for row in sheet.itertuples(index=False):
            name = row[0].strip()
            if name == "" or name.upper().startswith("NOM VARIABLE"):
                continue
            if "".join(row[1:]).strip() == "":     # a line with a name only is a section header
                section = name
                continue
            for one_name in expand_range(name):
                lines.append({"tab": tab, "section": section, "name": one_name.lower(),
                              "label": row[2].strip(), "coding": row[4].strip()})
    return pd.DataFrame(lines)


def describe(column, patient):
    """What a raw column holds, in a few words.

    A text is shown only if at least 5 patients share it, so that no name,
    date or free text of one patient is printed. patient: the patient of each row.
    """
    is_filled = (column.str.strip() != "") & (column != "0000-00-00")
    filled = column[is_filled].str.strip()
    numbers = pd.to_numeric(filled.str.replace(",", ".", regex=False), errors="coerce")
    words = [f"{len(filled)} filled"]
    if numbers.notna().any():
        words.append(f"{int(numbers.notna().sum())} numbers from {numbers.min():g} to {numbers.max():g}")
    is_text = numbers.isna()
    counts = patient[is_filled][is_text].groupby(filled[is_text]).nunique().sort_values(ascending=False)
    common = [f"'{text}' in {count} patients" for text, count in counts[counts >= 5].head(6).items()]
    if common:
        words.append("texts: " + ", ".join(common))
    return "; ".join(words)


def draft_schema(thesaurus, raw, tab, section):
    """A YAML skeleton for one section of the dictionary, to complete by hand.

    Returns text. Each variable comes with its label and, as a comment, what
    the extraction holds and how the dictionary says it is coded.
    """
    rows = thesaurus[(thesaurus["tab"] == tab) & (thesaurus["section"] == section)]
    lines = ["instrument: TODO", "title: TODO", f"tab: {tab}", f"section: {section}", "status: draft",
             "notes: >", "  TODO", "", "variables:"]
    for row in rows.itertuples():
        if row.name not in raw.columns:
            lines.append(f"  # {row.name}: not in the extraction")
            continue
        label = row.label.replace('"', "'")
        lines.append(f'  {row.name}: {{label: "{label}", type: TODO}}')
        lines.append(f"    # data: {describe(raw[row.name], raw['usubjid'])}")
        if row.coding:
            lines.append(f"    # dictionary coding: {row.coding}")
    return "\n".join(lines)
