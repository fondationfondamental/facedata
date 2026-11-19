"""The HTML report: an index page, one page per instrument, and the figures.

Only aggregates are written. Patient-level rows stay in result.flags.
"""

import html
from pathlib import Path

import pandas as pd

from facedata.harmonise import first_rows
from facedata.plots import plot_instrument, plot_variable
from facedata.tokens import KEY_COLUMNS

STYLE = """<style>
body {font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 1100px; padding: 0 1rem; color: #0b0b0b;}
table {border-collapse: collapse; font-size: 0.8rem;}
th, td {border-bottom: 1px solid #e4e3df; padding: 3px 8px; text-align: right;}
th:first-child, td:first-child {text-align: left;}
.wide {overflow-x: auto;}
img {max-width: 100%;}
p.notes {white-space: pre-wrap; color: #52514e;}
</style>"""
QC_COLUMNS = ["variable", "label", "type", "unit", "n_filled", "n_valid", "pct_valid", "n_info",
              "n_discrepancy", "n_danger", "min", "median", "max", "winsor_low", "winsor_high",
              "site_shift", "year_shift"]


def page(title, body):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>{STYLE}</head><body>{body}</body></html>"


def table_html(table):
    return "<div class='wide'>" + table.to_html(index=False, na_rep="", float_format=lambda x: f"{x:.4g}") + "</div>"


def as_written(after, flags):
    """The numbers as they were written: read again from the raw text of the flagged cells."""
    before = after.copy()
    text = flags["raw"].astype(str).str.replace(",", ".", regex=False).str.extract(r"(-?\d+(?:\.\d+)?)")[0]
    before.loc[flags["row"]] = pd.to_numeric(text, errors="coerce").to_numpy()
    return before


def value_classes(after, flags):
    """What each raw cell held: value, censored, missing code, unparsed or empty."""
    classes = pd.Series("empty", index=after.index).mask(after.notna(), "value")
    groups = [("value", ["out_of_range", "unit_unknown"]),
              ("censored", ["censored_left", "censored_right"]),
              ("missing code", ["missing_code", "date_placeholder"]),
              ("unparsed", ["unparsed", "unknown_code"])]
    for label, codes in groups:
        classes.loc[flags.loc[flags["flag"].isin(codes), "row"]] = label
    return classes


def patient_frame(result):
    """Patient-level values, on the row of each patient's first visit.

    One row per patient, with the key columns of that visit, so that these
    variables can be plotted per year and per site like the others.
    """
    first = result.data.loc[first_rows(result.data), KEY_COLUMNS]
    return first.join(result.patients.set_index("usubjid"), on="usubjid")


def rows_frame(result, table, visit):
    """The rows of result.treatments or result.relatives with the key columns of the patient's first visit.

    One row per item or relative, so that these variables can be plotted
    per year and per site like the others. visit: what the flag log writes
    in its visit column for each row.
    """
    first = result.data.loc[first_rows(result.data), KEY_COLUMNS].set_index("usubjid").drop(columns="visit")
    return table.join(first, on="usubjid").assign(visit=visit)


def instrument_page(schema, data, qc, flags, folder):
    """Write the page and the figures of one instrument. Returns the page's file name.

    data: result.data, or patient_frame(result) for a patient-level instrument.
    """
    name = schema["instrument"]
    plots = folder / "plots" / name
    plots.mkdir(parents=True, exist_ok=True)
    specs = {**schema["variables"], **schema.get("scores", {})}
    version = data[schema["version"]["name"]] if "version" in schema else None
    figures = []
    sign_pairs = {}
    for row in qc.to_dict("records"):
        variable, spec = row["variable"], specs[row["variable"]]
        if row["type"] in ("text", "date") or variable not in data.columns or row["n_valid"] < 20:
            continue                                 # nothing to draw, or too few values to show
        own_flags = flags[flags["variable"] == variable]
        after = data[variable]
        numeric = row["type"] not in ("category",)
        before = as_written(after, own_flags) if numeric and "column" in spec else after
        limits = {"range": spec.get("range", []), "winsor": [row["winsor_low"], row["winsor_high"]]}
        title = f"{variable}: {row['label']}"
        plot_variable(plots / f"{variable}.png", title, row["type"], before, after,
                      value_classes(after, own_flags), data, limits)
        figures.append(f"<h3 id='{variable}'>{html.escape(title)}</h3><img src='plots/{name}/{variable}.png' alt='{variable}'>")
        for score, raw_names in schema.get("sign", {}).get("pairs", {}).items():
            if score == variable:
                raw_names = [raw_names] if isinstance(raw_names, str) else raw_names
                sign_pairs[score] = (data[raw_names].sum(axis=1, min_count=len(raw_names)), before)
    delivered = data[[v for v in qc["variable"] if v in data.columns]]
    unit = {"patient": "patients", "list": "items", "relatives": "relatives"}.get(schema.get("level"), "visits")
    plot_instrument(plots / "_instrument.png", schema["title"], delivered, version, sign_pairs, data, unit)

    body = f"<p><a href='index.html'>Index</a></p><h1>{html.escape(schema['title'])}</h1>"
    body += f"<p>{html.escape(schema['tab'])} / {html.escape(schema['section'])} &middot; schema <code>{name}</code> &middot; status {schema['status']}</p>"
    body += f"<p class='notes'>{html.escape(schema.get('notes', ''))}</p>"
    body += f"<img src='plots/{name}/_instrument.png' alt='instrument overview'>"
    flipped = flags[flags["variable"].isin(sign_pairs) & (flags["flag"] == "sign_flipped")]
    if len(flipped) > 0:
        dates = data.loc[flipped["row"], ["siteid", "visit_date"]].groupby("siteid")["visit_date"]
        centres = pd.DataFrame({"values flipped": dates.size(), "last flipped visit": dates.max().dt.strftime("%Y-%m")})
        body += "<h2>Change of sign convention, per centre</h2>" + table_html(centres.reset_index())
    body += "<h2>Quality control</h2>" + table_html(qc[QC_COLUMNS])
    counts = flags[flags["variable"].isin(specs)].groupby(["variable", "flag", "severity"]).size()
    body += "<h2>Flags</h2>" + table_html(counts.rename("cells").reset_index())
    body += "<h2>Variables</h2>" + "".join(figures)
    (folder / f"{name}.html").write_text(page(schema["title"], body), encoding="utf-8")
    return f"{name}.html"


def write_report(result, schemas, folder):
    """Write the report of a load: folder/index.html, one page per instrument, folder/plots/."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rows = result.data[["usubjid", "visit"]].assign(row=result.data.index)
    flags = result.flags.merge(rows, on=["usubjid", "visit"], how="left")
    contents = []
    per_patient = patient_frame(result)
    first_row = pd.Series(per_patient.index, index=per_patient["usubjid"])
    frames = {"relatives": rows_frame(result, result.relatives, result.relatives["relative"])}
    for name, schema in schemas.items():
        qc = result.qc[result.qc["instrument"] == name]
        if len(qc) == 0:                             # this instrument was not loaded
            continue
        if schema.get("level") == "patient":         # a flag is drawn on the patient's first visit, with the value
            link = instrument_page(schema, per_patient, qc, flags.assign(row=flags["usubjid"].map(first_row)), folder)
        elif schema.get("level") in ("list", "relatives"):     # several rows per patient: items or relatives
            frame = frames.get(schema["level"])
            if schema["level"] == "list":                # the items of this list, named as the flag log names them
                items, label = result.treatments, "item "
                if "list" in items:
                    items, label = items[items["list"] == name], name + " item "
                frame = rows_frame(result, items, label + items["item"].astype(str))
            own = result.flags.merge(frame[["usubjid", "visit"]].assign(row=frame.index), on=["usubjid", "visit"])
            link = instrument_page(schema, frame, qc, own, folder)
        else:
            link = instrument_page(schema, result.data, qc, flags, folder)
        contents.append({"instrument": f"<a href='{link}'>{html.escape(schema['title'])}</a>", "tab": schema["tab"],
                         "status": schema["status"], "variables": len(qc), "values": int(qc["n_valid"].sum()),
                         "info": int(qc["n_info"].sum()), "discrepancy": int(qc["n_discrepancy"].sum()),
                         "danger": int(qc["n_danger"].sum())})
    severity = result.flags["severity"].value_counts()
    body = "<h1>FACE quality-control report</h1>"
    body += (f"<p>{len(result.data):,} visits of {result.data['usubjid'].nunique():,} patients &middot; "
             f"{len(contents)} instruments &middot; {len(result.qc)} variables &middot; flagged cells: "
             f"{severity.get('info', 0):,} info, {severity.get('discrepancy', 0):,} discrepancy, {severity.get('danger', 0):,} danger</p>")
    body += "<h2>Instruments</h2><div class='wide'>" + pd.DataFrame(contents).to_html(index=False, escape=False) + "</div>"
    body += "<h2>Flags</h2>" + table_html(result.flags.groupby(["severity", "flag"]).size().rename("cells").reset_index())
    body += "<h2>All variables</h2>" + table_html(result.qc[["instrument"] + QC_COLUMNS])
    (folder / "index.html").write_text(page("FACE quality-control report", body), encoding="utf-8")
    return folder / "index.html"
