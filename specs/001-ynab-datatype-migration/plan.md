# Implementation Plan: YNAB Datatype Migration — Replace GoodbudgetTxn with YnabTxn

**Branch**: `001-ynab-datatype-migration` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-ynab-datatype-migration/spec.md`

## Summary

Add `YnabTxn` to `datatypes.py` as the YNAB-native transaction type, update
`_dollars_to_cents` to handle `$`-prefixed strings, introduce `MergedTxn_YnabTxn`, rename
`TxnsGrouped.only_gb_txns` → `only_ynab_txns`, and add four unit tests. `GoodbudgetTxn` and
`MergedTxn_GoodbudgetTxn` are retained in this task because out-of-scope files (`graph.py`,
`add_new_txns.py`) still depend on them — removal is deferred to a follow-up feature.

## Technical Context

**Language/Version**: Python 3
**Primary Dependencies**: pytest
**Storage**: N/A
**Testing**: pytest (`python3 -m pytest` from repo root)
**Target Platform**: macOS / local CLI
**Project Type**: cli
**Performance Goals**: N/A
**Constraints**: Out-of-scope files (`graph.py`, `add_new_txns.py`) must remain importable
**Scale/Scope**: Single file change (`datatypes.py`) + one new test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Importable Core | ✅ PASS | `YnabTxn` importable directly from `datatypes`; no `main.py` dependency |
| II. Cents Convention | ✅ PASS | `amt_cents` derived via `_dollars_to_cents`; negative = expense |
| III. Pytest-First | ✅ PASS | 4 tests in `tests/test_datatypes.py`; run with `python3 -m pytest` |
| IV. Scope Isolation | ⚠️ VIOLATION (mitigated) | See below |
| V. Simplicity | ✅ PASS | Only adds one strip character to existing function; no new abstraction |

**Principle IV violation details and resolution**:

Research revealed that `graph.py` (line 8) and `add_new_txns.py` (line 9) both import
`GoodbudgetTxn` from `datatypes`. `add_new_txns.py` line 146 also accesses `x.gb_txn` on
`MergedTxn_BothTxns`. Therefore:

- `GoodbudgetTxn` MUST remain exported from `datatypes.py` in this task.
- `MergedTxn_GoodbudgetTxn` MUST remain exported (it is still instantiated in `match.py`,
  an in-scope but intentionally-broken file).
- Renaming `MergedTxn_BothTxns.gb_txn` → `ynab_txn` is DEFERRED (breaks `add_new_txns.py`).
- Spec FR-008 ("zero references to `GoodbudgetTxn`") is a post-migration end-state requirement,
  not achievable in this single task without breaking out-of-scope files.

The Complexity Tracking table below documents this justified deviation.

**Post-Phase 1 re-check**: Design (data-model.md) confirms the above. All four tests pass
without touching out-of-scope files. Gate status unchanged.

## Project Structure

### Documentation (this feature)

```text
specs/001-ynab-datatype-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
datatypes.py             # Modified: add YnabTxn, MergedTxn_YnabTxn; update helpers
tests/
└── test_datatypes.py    # New: 4 unit tests
```

**Structure Decision**: Flat layout — all in-scope Python modules live at the repo root.
Tests live in `./tests/` per the project constitution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| `GoodbudgetTxn` retained in `datatypes.py` despite FR-008 | `graph.py` and `add_new_txns.py` import it; removing it breaks out-of-scope files (Constitution IV) | Aliasing is impossible — the types have incompatible fields (`envelope`/`notes` vs `category`/`cleared`) |
| `MergedTxn_BothTxns.gb_txn` rename deferred | `add_new_txns.py:146` accesses `x.gb_txn` directly; renaming breaks it | Updating `add_new_txns.py` is out of scope for this task per the spec |
| `MergedTxn_GoodbudgetTxn` retained | `match.py` (in-scope, intentionally broken) still instantiates it; removing it would change the nature of the breakage in unexpected ways | Deferred removal is safe and explicit |
