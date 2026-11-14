"""facedata: load, harmonise and quality-check FACE cohort extractions.

One module per cohort (bp, sz, dr, asp):

    from facedata import bp
    result = bp.load("data/bp/BPALL_20261113_2.tsv")

The design is in docs/ARCHITECTURE.md, the schema fields in docs/SCHEMA_SPEC.md.
"""
