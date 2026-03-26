# goodbudget-helpers Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-26

## Active Technologies
- Python 3 + pytest, re (stdlib) (002-update-chase-regex)
- Python 3.14.3 (system), venv at `.venv/` + `re` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only) (003-ynab-parser)
- CSV file at `./in/ynab.csv` (003-ynab-parser)
- Python 3.14.3 (system), venv at `.venv/` + `csv` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only) (004-csv-reader-parsers)
- CSV files at `./in/chase.csv` and `./in/ynab.csv` (004-csv-reader-parsers)
- Python 3.14.3 (system), venv at `.venv/` + `pytest 9.0.2` (test-only); `datatypes`, `match` (stdlib) (005-match-ynab-tests)
- N/A — tests construct objects directly, no file I/O (005-match-ynab-tests)

- Python 3 + pytest (001-ynab-datatype-migration)

## Project Structure

```text
src/
tests/
```

## Commands

python3 -m pytest

## Code Style

Python 3: Follow standard conventions

## Recent Changes
- 005-match-ynab-tests: Added Python 3.14.3 (system), venv at `.venv/` + `pytest 9.0.2` (test-only); `datatypes`, `match` (stdlib)
- 004-csv-reader-parsers: Added Python 3.14.3 (system), venv at `.venv/` + `csv` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only)
- 003-ynab-parser: Added Python 3.14.3 (system), venv at `.venv/` + `re` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
