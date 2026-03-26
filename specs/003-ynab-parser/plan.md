# Implementation Plan: Replace Goodbudget Parser with YNAB Parser

**Branch**: `003-ynab-parser` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-ynab-parser/spec.md`

## Summary

Replace the two Goodbudget regexes (`GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`) and `read_gb_txns` function in `file_in.py` with a single `YNAB_REGEX` and `read_ynab_txns`. The YNAB CSV export uses a quoted 11-column format with separate Outflow and Inflow columns; the parser derives a signed `amt_dollars` string before constructing `YnabTxn`. Four new tests cover the regex and parser; all existing Chase tests continue to pass.

## Technical Context

**Language/Version**: Python 3.14.3 (system), venv at `.venv/`
**Primary Dependencies**: `re` (stdlib), `datetime` (stdlib), `pytest 9.0.2` (test-only)
**Storage**: CSV file at `./in/ynab.csv`
**Testing**: pytest via `.venv/bin/python -m pytest`
**Target Platform**: macOS / local CLI
**Project Type**: CLI data pipeline module
**Performance Goals**: N/A — processes hundreds of transactions per run
**Constraints**: Must not break `graph.py` or `add_new_txns.py` at import time (see Complexity Tracking)
**Scale/Scope**: Single flat-file project; 2 modified files (`regex.py`, `file_in.py`)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Importable Core | ✅ PASS | `read_ynab_txns` callable directly from `file_in` |
| II. Cents-Only Monetary Arithmetic | ✅ PASS | `YnabTxn.amt_cents` computed via `_dollars_to_cents` |
| III. Pytest-First Testing | ✅ PASS | 4 new tests in `tests/test_file_in.py`; written before implementation |
| IV. Scope Isolation | ⚠️ KNOWN VIOLATION | Removing `read_gb_txns` breaks `graph.py` (see Complexity Tracking) |
| V. Simplicity | ✅ PASS | Single regex replaces two; single function replaces one |

## Project Structure

### Documentation (this feature)

```text
specs/003-ynab-parser/
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
regex.py          # Add YNAB_REGEX; remove GB_EXPENSE_REGEX, GB_INCOME_REGEX
file_in.py        # Add read_ynab_txns, IN_YNAB_FILE; remove read_gb_txns, IN_GB_FILE

tests/
└── test_file_in.py   # Add 4 YNAB tests (append to existing 4 Chase tests)
```

**Structure Decision**: Single flat project. Only `regex.py` and `file_in.py` are modified. `datatypes.py`, `match.py`, `file_out.py`, `config.py`, `main.py` are untouched.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Scope Isolation (Principle IV): removing `read_gb_txns` breaks `graph.py` | FR-010 requires removing it; dead code is worse than a known breakage documented in assumptions | Keeping `read_gb_txns` as a shim adds complexity; updating `graph.py` is deferred to a follow-up feature |

## Implementation Notes

### YNAB Regex Pattern

```python
_YNAB_REGEX_STR = (
    r'"[^"]*"'                           # Account (col 0, skip)
    r',"[^"]*"'                          # Flag (col 1, skip)
    r',"(?P<date>[^"]+)"'                # Date (col 2)
    r',"(?P<payee>[^"]*)"'               # Payee (col 3)
    r',"[^"]*"'                          # Category Group/Category (col 4, skip)
    r',"[^"]*"'                          # Category Group (col 5, skip)
    r',"(?P<category>[^"]*)"'            # Category (col 6, deepest)
    r',"[^"]*"'                          # Memo (col 7, skip)
    r',\$(?P<outflow>\d+\.\d\d)'         # Outflow (col 8, $ stripped)
    r',\$(?P<inflow>\d+\.\d\d)'          # Inflow (col 9, $ stripped)
    r',"(?P<cleared>[^"]+)"'             # Cleared (col 10)
)
YNAB_REGEX = re.compile(_YNAB_REGEX_STR)
```

Header non-match: The header `"Account","Flag",...,"Outflow","Inflow","Cleared"` has quoted strings in cols 8 and 9 — the `\$\d+\.\d\d` pattern won't match them.

### read_ynab_txns Signed Amount Logic

```python
outflow_val = float(outflow_str)
inflow_val  = float(inflow_str)
if outflow_val > 0.0:
    amt_dollars = f"-{outflow_str}"
elif inflow_val > 0.0:
    amt_dollars = inflow_str
else:
    amt_dollars = "0.00"
```

### TypeVar Update

The `TypeVar` in `file_in.py` references `GoodbudgetTxn`. Update to `YnabTxn`.

### File Open Encoding

```python
with open(IN_YNAB_FILE, encoding='utf-8-sig') as in_file:
```

`utf-8-sig` strips BOM transparently when present.
