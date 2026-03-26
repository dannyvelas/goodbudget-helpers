# Implementation Plan: Update file_out.py to Use YNAB Types

**Branch**: `006-file-out-ynab` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-file-out-ynab/spec.md`

## Summary

`file_out.py` still references `GoodbudgetTxn`, `MergedTxn_GoodbudgetTxn`, and
`only_gb_txns` — symbols that were renamed in `match.py` (feature 005) and
`datatypes.py` (feature 001). This makes the current `file_out.py` already broken
against the updated `TxnsGrouped.only_ynab_txns`. This feature renames all
Goodbudget symbols to their YNAB equivalents, renames the output file to `ynab.csv`,
updates column headers and type labels, and adds two unit tests. No source files
other than `file_out.py` and `tests/test_file_out.py` are modified.

## Technical Context

**Language/Version**: Python 3.14.3 (system), venv at `.venv/`
**Primary Dependencies**: `pytest 9.0.2` (test-only); `datatypes`, `file_out` (stdlib)
**Storage**: Output files under `./out/<timestamp>/` (CSV + log.txt)
**Testing**: pytest via `.venv/bin/python -m pytest`
**Target Platform**: macOS / local CLI
**Project Type**: CLI data pipeline module
**Performance Goals**: N/A
**Constraints**: N/A
**Scale/Scope**: 1 modified file (`file_out.py`), 1 new file (`tests/test_file_out.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Importable Core | ✅ PASS | `_ynab_txn_to_row` and `_merged_txn_to_row` are module-level functions; `from file_out import _ynab_txn_to_row` works without importing `main` |
| II. Cents-Only Monetary Arithmetic | ✅ PASS | `bal` and `amt_cents` remain integers; `bal/100` float division is display-only in CSV output rows |
| III. Pytest-First Testing | ✅ PASS | Two new tests in `tests/test_file_out.py` written before implementation |
| IV. Scope Isolation | ✅ PASS | Only `file_out.py` modified; `graph.py` and `add_new_txns.py` do not import `file_out`; `GoodbudgetTxn`/`MergedTxn_GoodbudgetTxn` retained in `datatypes.py` |
| V. Simplicity | ✅ PASS | Pure rename — no new abstractions, no new modules |

## Project Structure

### Documentation (this feature)

```text
specs/006-file-out-ynab/
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
file_out.py          # MODIFIED — all Goodbudget symbols → YNAB equivalents
tests/
└── test_file_out.py # NEW — 2 unit tests for _ynab_txn_to_row and _merged_txn_to_row
```

**Structure Decision**: Single modified source file + one new test file.
No new modules, no new directories.

## Implementation Notes

### Rename Map

| Old | New |
|-----|-----|
| `GoodbudgetTxn` (import) | `YnabTxn` |
| `MergedTxn_GoodbudgetTxn` (import) | `MergedTxn_YnabTxn` |
| `_AMT_GB_FIELDS = 6` | `_AMT_YNAB_FIELDS = 6` |
| `_GB_FIELD_NAMES = 'Goodbudget ID,...'` | `_YNAB_FIELD_NAMES = 'YNAB ID,YNAB Date,YNAB Title,YNAB Category,YNAB Txn Amount,YNAB Balance'` |
| `_gb_txn_to_row(gb_txn: GoodbudgetTxn)` | `_ynab_txn_to_row(ynab_txn: YnabTxn)` |
| `gb_txn.envelope` | `ynab_txn.category` |
| `'GOODBUDGET'` (type label) | `'YNAB'` |
| `self.gb_file = f'{OUT_DIR}/goodbudget.csv'` | `self.ynab_file = f'{OUT_DIR}/ynab.csv'` |
| `txns_grouped.only_gb_txns` | `txns_grouped.only_ynab_txns` |
| `'AMT OF UNMATCHED GOODBUDGET TXNS'` | `'AMT OF UNMATCHED YNAB TXNS'` |

### `_merged_txn_to_row` logic change

The existing `else` branch calls `_gb_txn_to_row(merged_txn.gb_txn)` — this must
become `_ynab_txn_to_row(merged_txn.ynab_txn)`. The `isinstance(merged_txn,
MergedTxn_GoodbudgetTxn)` check becomes `isinstance(merged_txn, MergedTxn_YnabTxn)`.

### `_MERGED_TXN_FIELD_NAMES` update

Derived from `_CH_FIELD_NAMES` and `_YNAB_FIELD_NAMES`, so it updates automatically
once `_YNAB_FIELD_NAMES` is defined. No separate change needed beyond renaming the
constant reference.

### Test construction pattern

```python
from datatypes import YnabTxn, MergedTxn_YnabTxn
from file_out import _ynab_txn_to_row, _merged_txn_to_row

txn = YnabTxn(id_=3, ts=1735689600, date='01/01/2025', title='Trader Joes',
              category='Groceries', amt_dollars='-25.00', cleared='Cleared')
txn.bal = 97500
```

`bal/100` in Python integer division is `97500/100 = 975.0` (float).
Expected row: `'3,01/01/2025,Trader Joes,Groceries,-25.00,975.0'`
