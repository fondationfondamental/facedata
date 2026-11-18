"""Constants shared by the whole pipeline. There are no functions in this file."""

# Key columns of the output tables, in order.
KEY_COLUMNS = ["usubjid", "visit", "visit_order", "visit_month", "visit_date", "siteid", "age"]

# The export writes an empty date as 0000-00-00.
EMPTY_DATE = "0000-00-00"

# Dates that were typed to say "unknown".
PLACEHOLDER_DATES = {"1000-01-01", "1850-01-01", "1900-01-01"}
PLACEHOLDER_VISIT_DATES = {"1950-01-01"}

# Text that means "no value" (in lower case), with the reason.
MISSING_TOKENS = {
    "ne sais pas": "unknown",
    "ne sait pas": "unknown",
    "nsp": "unknown",
    "?": "unknown",
    "inconnu": "unknown",
    "non applicable": "not_applicable",
    "na": "not_applicable",
    "n/a": "not_applicable",
    "non renseigné": "not_recorded",
    "nr": "not_recorded",
    "nc": "not_recorded",
    ".": "not_recorded",
    "nan": "not_a_number",
    "none": "not_a_number",
    "null": "not_a_number",
    "infinity": "not_a_number",
    "-infinity": "not_a_number",
}

# Every flag code and how serious it is (docs/ARCHITECTURE.md, section 6).
#   info         harmonised, the value is trusted
#   discrepancy  the value is kept but conflicts with other information
#   danger       could not be harmonised, the value is missing in the output
SEVERITY = {
    "missing_code": "info",
    "date_placeholder": "info",
    "date_partial": "info",
    "format_repaired": "info",
    "censored_left": "info",
    "censored_right": "info",
    "band_from_z": "info",
    "unit_converted": "info",
    "unit_inferred": "info",
    "sign_flipped": "info",
    "version_inferred": "info",
    "duplicate_row": "info",
    "winsorised": "info",
    "unit_doubt": "discrepancy",
    "sign_doubt": "discrepancy",
    "band_middle": "discrepancy",
    "column_conflict": "discrepancy",
    "score_mismatch": "discrepancy",
    "score_as_stored": "discrepancy",
    "derived_doubt": "discrepancy",
    "patient_value_varies": "discrepancy",
    "list_crossed": "discrepancy",
    "visit_order": "discrepancy",
    "check_failed": "discrepancy",
    "period_doubt": "discrepancy",
    "period_removed": "danger",
    "unparsed": "danger",
    "unknown_code": "danger",
    "out_of_range": "danger",
    "not_shown": "danger",
    "unit_unknown": "danger",
    "version_unknown": "danger",
    "norm_missing": "danger",
    "score_not_recomputed": "danger",
}

FLAG_COLUMNS = ["usubjid", "visit", "variable", "raw", "value", "flag", "severity", "detail"]
