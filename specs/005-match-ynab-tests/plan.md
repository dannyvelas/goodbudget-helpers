# Implementation Plan: Add Tests for match.py YNAB Type Migration

**Branch**: `005-match-ynab-tests` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-match-ynab-tests/spec.md`

## Summary

`match.py` was already updated (commit `37c6d82`) to use `YnabTxn` and
`MergedTxn_YnabTxn` in place of all Goodbudget types. This feature's only
deliverable is creating `tests/test_match.py` with three unit tests that verify
the matching algorithm works correctly with YNAB types: matched pair, amount
mismatch, and timestamp beyond the 7-day window. No source files are modified.

## Technical Context

**Language/Version**: Python 3.14.3 (system), venv at `.venv/`
**Primary Dependencies**: `pytest 9.0.2` (test-only); `datatypes`, `match` (stdlib)
**Storage**: N/A — tests construct objects directly, no file I/O
**Testing**: pytest via `.venv/bin/python -m pytest`
**Target Platform**: macOS / local CLI
**Project Type**: CLI data pipeline module
**Performance Goals**: N/A
**Constraints**: N/A
**Scale/Scope**: 1 new file (`tests/test_match.py`), 0 modified files

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Importable Core | ✅ PASS | `get_txns_grouped` is directly importable from `match` |
| II. Cents-Only Monetary Arithmetic | ✅ PASS | Tests construct objects via `amt_dollars`; `amt_cents` is derived |
| III. Pytest-First Testing | ✅ PASS | 3 new tests in `tests/test_match.py` |
| IV. Scope Isolation | ✅ PASS | Only `tests/test_match.py` created; no out-of-scope files touched |
| V. Simplicity | ✅ PASS | Pure unit tests — no mocking, no temp files, no file I/O |

## Project Structure

### Documentation (this feature)

```text
specs/005-match-ynab-tests/
├── plan.md          # This file
├── spec.md          # Feature specification
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md         # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tests/
└── test_match.py    # NEW — 3 unit tests for get_txns_grouped
```

**Structure Decision**: Single new test file. Zero modifications to existing source.

## Implementation Notes

### Test construction pattern

All three tests construct `ChaseTxn` and `YnabTxn` directly — no parsers, no
temp files:

```python
from datatypes import ChaseTxn, YnabTxn
from match import get_txns_grouped

ch_txn = ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
                  date='01/01/2025', title='Amazon', amt_dollars='-25.00')

ynab_txn = YnabTxn(id_=0, ts=1735689600, date='01/01/2025', title='Amazon',
                   category='Shopping', amt_dollars='-25.00', cleared='Cleared')

result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)
```

### Timestamp arithmetic for `test_match_outside_7_days`

```
ts_chase = 1735689600  # 2025-01-01
ts_ynab  = 1736380800  # 2025-01-09
delta    = (1736380800 - 1735689600) / (60*60*24) = 8.0 days > MAX_DAYS_APART (7)
```

### `yn_start_bal` parameter name

The spec uses positional args `get_txns_grouped([ch_txn], [ynab_txn], 0, 0)`.
The fourth parameter is `yn_start_bal` in `match.py`. Passing `0` is correct for
all three tests since no balance assertions are made.
