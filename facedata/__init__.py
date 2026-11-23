"""facedata: load, harmonise and quality-check FACE cohort extractions.

Four cohorts, one module each: bp (bipolar disorder), sz (schizophrenia),
dr (treatment-resistant depression), asp (autism spectrum, children and adults).

    from facedata import bp
    result = bp.load("/path/to/BPALL_<date>.tsv", norms="/path/to/norms")
    result.data, result.patients, result.flags, result.qc, result.treatments, result.relatives

Start with the guide and the data dictionary, which ship with the package:

    facedata guide          # the cohorts, their visits and traps, what they share
    facedata find anxiety   # variables; facedata show <id> gives one record
    facedata page           # the dictionary page in the browser
    facedata init           # in a research project: tells its coding agents (AGENTS.md, CLAUDE.md)

The same from Python: facedata.guide. Across cohorts: facedata.common.
The design and the schema fields: docs/ARCHITECTURE.md and docs/SCHEMA_SPEC.md
of the repository, https://github.com/fondationfondamental/facedata
"""
