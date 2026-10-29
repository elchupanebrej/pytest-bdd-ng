# External CSV and TSV Examples

This standalone pytest-cuke project loads scenario-outline rows from a file
next to the feature. It uses pytest-cuke's public decorators and autoloads the
feature without a mirror `test_*.py` wrapper.

Install the example requirements and run it from this directory:

```sh
python -m pip install -r requirements.txt
python -m pytest --cuke-json=report.json --cuke-messages-ndjson=messages.ndjson
```

The requirements install this checkout in editable mode, so the example uses
the external Examples support from the current source tree before it is
available in a published release.

An outline can refer to a comma-separated file with any of these markers:

```gherkin
Examples: table: users.csv
Examples: <table:users.csv>
Examples: | table: users.csv |
Examples:
  | table: users.csv |
```

The marker can also be a one-cell row in Markdown Gherkin. A normal inline
Examples table stays inline. CSV files use commas; `.tsv` and `.tab` files use
tabs. UTF-8 BOMs are accepted. Quoted CSV fields may contain commas, pipes,
backslashes, and newlines; those values are escaped for Gherkin before parsing.

Relative source paths resolve from the feature file's directory. Absolute host
paths and Windows-style relative separators are supported. Collection errors
identify both the feature marker and the resolved source path. Empty sources,
blank headers, inconsistent row widths, unreadable files, and invalid UTF-8
fail collection with a diagnostic. Source files are read without changing the
working directory or writing generated tables back to disk; the data is read
again for each pytest run.

This checkout has no batch collector. If one is added later, it can use the
same file parser ingestion seam.
