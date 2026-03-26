# Implementation Plan: Replace Regex Parsers with csv.reader

**Branch**: `004-csv-reader-parsers` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-csv-reader-parsers/spec.md`

## Summary

Replace the regex-based CSV parsing loops in `read_ch_txns` and the new
`read_ynab_txns` with Python's stdlib `csv.reader`. Column access by index replaces
named regex groups; row validity is checked by column count and float-parseability
of the amount columns. All remaining regex symbols (`CH_REGEX`, `GB_EXPENSE_REGEX`,
`GB_INCOME_REGEX`) and dead GB code (`read_gb_txns`, `IN_GB_FILE`) are removed.
Eight new reader-based tests replace the six existing regex-pattern tests.

## Technical Context

**Language/Version**: Python 3.14.3 (system), venv at `.venv/`
**Primary Dependencies**: `csv` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only)
**Storage**: CSV files at `./in/chase.csv` and `./in/ynab.csv`
**Testing**: pytest via `.venv/bin/python -m pytest`
**Target Platform**: macOS / local CLI
**Project Type**: CLI data pipeline module
**Performance Goals**: N/A — processes hundreds of transactions per run
**Constraints**: Must not break `add_new_txns.py` at import time; `graph.py` breakage is
accepted (see Complexity Tracking)
**Scale/Scope**: 2 modified files (`regex.py`, `file_in.py`), 1 updated test file

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Importable Core | ✅ PASS | `read_ch_txns` and `read_ynab_txns` callable directly from `file_in` |
| II. Cents-Only Monetary Arithmetic | ✅ PASS | `amt_cents` computed via `_dollars_to_cents`; float used only for sign detection, never stored |
| III. Pytest-First Testing | ✅ PASS | 8 new tests in `tests/test_file_in.py`; written before implementation |
| IV. Scope Isolation | ⚠️ KNOWN VIOLATION | Removing `read_gb_txns` breaks `graph.py` (see Complexity Tracking) |
| V. Simplicity | ✅ PASS | `csv.reader` is stdlib, no new dependencies; removes 3 regex patterns |

## Project Structure

### Documentation (this feature)

```text
specs/004-csv-reader-parsers/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── checklists/
│   └── requirements.md  # Pre-implementation checklist (all ✅)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
regex.py          # Remove all symbols; leave with only `import re` (or delete import if unused)
file_in.py        # Refactor read_ch_txns; add read_ynab_txns + IN_YNAB_FILE;
                  # remove read_gb_txns, IN_GB_FILE, GoodbudgetTxn import;
                  # update TypeVar to YnabTxn; add `import csv`

tests/
└── test_file_in.py   # Remove 4 CH_REGEX tests + 2 YNAB_REGEX tests (from 003);
                       # add 8 new reader-based tests
```

**Structure Decision**: Single flat project. Only `regex.py` and `file_in.py` are
modified. `datatypes.py`, `match.py`, `file_out.py`, `config.py`, `main.py` are
untouched.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Scope Isolation (Principle IV): removing `read_gb_txns` breaks `graph.py` | FR-011 requires removing dead GB code; retaining it is worse long-term | Keeping `read_gb_txns` as a no-op shim adds complexity with no value; updating `graph.py` is deferred to a follow-up feature |

## Implementation Notes

### read_ch_txns (refactor)

```python
import csv

def read_ch_txns(ch_start_bal: int) -> ReadResults[ChaseTxn]:
    txns: List[ChaseTxn] = []
    lines_failed: List[str] = []
    with open(IN_CH_FILE) as in_file:
        for i, row in enumerate(csv.reader(in_file)):
            if i == 0:
                continue          # skip header
            if len(row) == 7:
                try:
                    amt = float(row[5])
                except ValueError:
                    lines_failed.append(','.join(row))
                    continue
                txns.append(ChaseTxn(
                    id_=i,
                    ts=int(dt.strptime(row[0], "%m/%d/%Y").timestamp()),
                    is_debit=amt < 0,
                    is_pending=False,
                    date=row[0],
                    title=_shorten(row[2]),
                    amt_dollars=row[5]
                ))
            else:
                lines_failed.append(','.join(row))
    # running balance pass unchanged
    ...
```

### read_ynab_txns (new)

```python
def read_ynab_txns(ynab_start_bal: int) -> ReadResults[YnabTxn]:
    txns: List[YnabTxn] = []
    lines_failed: List[str] = []
    with open(IN_YNAB_FILE, encoding='utf-8-sig') as in_file:
        for i, row in enumerate(csv.reader(in_file)):
            if i == 0:
                continue          # skip header
            if len(row) == 11:
                try:
                    outflow_str = row[8].lstrip('$')
                    inflow_str  = row[9].lstrip('$')
                    outflow_val = float(outflow_str)
                    inflow_val  = float(inflow_str)
                except ValueError:
                    lines_failed.append(','.join(row))
                    continue
                if outflow_val > 0.0:
                    amt_dollars = f"-{outflow_str}"
                elif inflow_val > 0.0:
                    amt_dollars = inflow_str
                else:
                    amt_dollars = '0.00'
                txns.append(YnabTxn(
                    id_=i,
                    ts=int(dt.strptime(row[2], "%m/%d/%Y").timestamp()),
                    date=row[2],
                    title=_shorten(row[3]),
                    category=row[6],
                    amt_dollars=amt_dollars,
                    cleared=row[10]
                ))
            else:
                lines_failed.append(','.join(row))
    # running balance pass
    curr_bal = ynab_start_bal
    for txn in reversed(txns):
        curr_bal += txn.amt_cents
        txn.bal = curr_bal
    return ReadResults(txns, lines_failed)
```

### regex.py after this feature

All regex symbols removed. File contents:

```python
import re
```

(The `import re` is retained in case other modules depend on `regex` being importable;
if nothing imports it, the file can remain as a stub.)
