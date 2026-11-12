"""The rare rules that cannot be written as data in a schema.

A schema refers to a function of this file by its name:

- `parse: name` on a variable: name(text) takes the cleaned text of the
  column and returns the values.
- `checks: [name]` on an instrument: name(values) takes the table of the
  instrument's values and returns True for the rows that fail the check.

Use them rarely (docs/SCHEMA_SPEC.md, section 10). No schema needs one yet.
"""
