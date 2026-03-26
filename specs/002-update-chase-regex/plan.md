# Implementation Plan: Update Chase CSV Parser for New Export Format

**Branch**: `002-update-chase-regex` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-update-chase-regex/spec.md`

## Summary

Replace `CH_REGEX` in `regex.py` with a pattern matching the new Chase CSV format
(7-column, header row, no DEBIT/CREDIT prefix, no balance column). Update `read_ch_txns`
in `file_in.py` to skip the header row explicitly, derive `is_debit` from the sign of
`amt`, and set `is_pending=False` unconditionally. Add four unit tests in
`tests/test_file_in.py`.

## Technical Context

**Language/Version**: Python 3
**Primary Dependencies**: pytest, re (stdlib)
**Storage**: N/A
**Testing**: pytest (`python3 -m pytest` from repo root)
**Target Platform**: macOS / local CLI
**Project Type**: cli
**Performance Goals**: N/A
**Constraints**: `graph.py` and `add_new_txns.py` must remain importable; `read_gb_txns` unchanged
**Scale/Scope**: Two file changes (`regex.py`, `file_in.py`) + one new test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Importable Core | ✅ PASS | `CH_REGEX` importable from `regex`; `read_ch_txns` importable from `file_in` without `main.py` |
| II. Cents Convention | ✅ PASS | `amt_cents` still derived via `_dollars_to_cents` inside `ChaseTxn`; negative = expense |
| III. Pytest-First | ✅ PASS | 4 tests in `tests/test_file_in.py`; TDD order enforced |
| IV. Scope Isolation | ✅ PASS | `graph.py` imports only `read_gb_txns`; `add_new_txns.py` does not import `file_in` directly; neither affected |
| V. Simplicity | ✅ PASS | Minimal change: one regex replacement + 3-line logic update in `read_ch_txns` |

**Post-Phase 1 re-check**: Design confirms no constitution violations. All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/002-update-chase-regex/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
regex.py                 # Modified: replace _CH_REGEX_STR / CH_REGEX
file_in.py               # Modified: update read_ch_txns
tests/
└── test_file_in.py      # New: 4 unit tests
```

**Structure Decision**: Flat layout — all in-scope modules at repo root; tests in `./tests/`.

## Complexity Tracking

> No constitution violations requiring justification.
