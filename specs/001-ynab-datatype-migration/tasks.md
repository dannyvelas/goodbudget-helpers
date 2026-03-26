---

description: "Task list for 001-ynab-datatype-migration"
---

# Tasks: YNAB Datatype Migration — Replace GoodbudgetTxn with YnabTxn

**Input**: Design documents from `/specs/001-ynab-datatype-migration/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec. Written before implementation per Constitution Principle III.

**Organization**: Tasks are grouped by user story. US2 precedes US1 because
`_dollars_to_cents` (US2) is called inside `YnabTxn.__init__` (US1).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 per spec.md
- All file paths are from the repository root

## Path Conventions

Single project — flat layout at repository root:
- Source modules: `datatypes.py`, `regex.py`, etc. (repo root)
- Tests: `tests/` (repo root)

---

## Phase 1: Setup

**Purpose**: Create the test infrastructure required by all user stories

- [x] T001 Create `tests/` directory and empty `tests/__init__.py` at repo root
- [x] T002 [P] Create `tests/test_datatypes.py` with module-level import:
  `from datatypes import _dollars_to_cents, YnabTxn`
  (file may import-error until implementation is done — that is expected)

---

## Phase 2: Foundational

No blocking foundational work required beyond Phase 1. `_dollars_to_cents` and `YnabTxn`
are both in-scope within `datatypes.py` and can be implemented story-by-story.

**Checkpoint**: `tests/` directory and `tests/test_datatypes.py` exist → user story work begins

---

## Phase 3: User Story 2 — Dollar-Sign Monetary String Conversion (Priority: P1)

**Goal**: `_dollars_to_cents` correctly handles `$`-prefixed strings from YNAB CSV columns.
This story is implemented first because US1's `YnabTxn` calls `_dollars_to_cents` internally.

**Independent Test**: `python3 -m pytest tests/test_datatypes.py::test_dollars_to_cents_dollar_sign tests/test_datatypes.py::test_dollars_to_cents_negative`

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, run `python3 -m pytest` to confirm they FAIL, then implement**

- [x] T003 [P] [US2] Add `test_dollars_to_cents_dollar_sign` to `tests/test_datatypes.py`:
  call `_dollars_to_cents('$3.00')` and assert result is `300`
- [x] T004 [P] [US2] Add `test_dollars_to_cents_negative` to `tests/test_datatypes.py`:
  call `_dollars_to_cents('-25.00')` and assert result is `-2500`

### Implementation for User Story 2

- [x] T005 [US2] Update `_dollars_to_cents` in `datatypes.py` to also strip `'$'` from the
  input string (add `.replace('$', '')` to the existing chain of replacements); run
  `python3 -m pytest tests/test_datatypes.py` to confirm T003 and T004 now pass

**Checkpoint**: `test_dollars_to_cents_dollar_sign` and `test_dollars_to_cents_negative` pass ✅

---

## Phase 4: User Story 1 — YnabTxn Transaction Type (Priority: P1)

**Goal**: `YnabTxn` is importable from `datatypes` and correctly stores all fields with
`amt_cents` derived from `amt_dollars` via the updated `_dollars_to_cents`.

**Independent Test**: `python3 -m pytest tests/test_datatypes.py::test_ynab_txn_outflow tests/test_datatypes.py::test_ynab_txn_inflow`

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, run `python3 -m pytest` to confirm they FAIL, then implement**

- [x] T006 [P] [US1] Add `test_ynab_txn_outflow` to `tests/test_datatypes.py`:
  construct `YnabTxn(id_=1, ts=1735689600, date='01/01/2025', title='Trader Joes',
  category='Groceries', amt_dollars='-25.00', cleared='Cleared')`;
  assert `txn.amt_cents == -2500`, `txn.category == 'Groceries'`,
  `txn.cleared == 'Cleared'`, `txn.bal == 0`
- [x] T007 [P] [US1] Add `test_ynab_txn_inflow` to `tests/test_datatypes.py`:
  construct `YnabTxn(id_=2, ts=1736985600, date='01/16/2025', title='PAYMENT',
  category='Payment', amt_dollars='500.00', cleared='Cleared')`;
  assert `txn.amt_cents == 50000`

### Implementation for User Story 1

- [x] T008 [US1] Add `YnabTxn` class to `datatypes.py` after `ChaseTxn` with instance fields:
  `id_` (int), `ts` (int), `date` (str), `title` (str), `category` (str),
  `amt_dollars` (str), `amt_cents = _dollars_to_cents(amt_dollars)` (int),
  `cleared` (str), `bal = 0` (int); run `python3 -m pytest tests/test_datatypes.py` to
  confirm all four tests pass

**Checkpoint**: All four required tests pass ✅
`python3 -m pytest tests/test_datatypes.py` → 4 passed, 0 failed

---

## Phase 5: User Story 3 — Composite Types Reference YNAB (Priority: P2)

**Goal**: `MergedTxn_YnabTxn`, updated `TxnsGrouped.only_ynab_txns`, and updated `MergedTxn`
union are all importable from `datatypes` and usable directly.

**Independent Test**: `python3 -c "from datatypes import MergedTxn_YnabTxn, TxnsGrouped; print('ok')"` succeeds

### Implementation for User Story 3

- [x] T009 [P] [US3] Add `MergedTxn_YnabTxn` class to `datatypes.py` (after
  `MergedTxn_GoodbudgetTxn`): constructor takes a `YnabTxn`; stores `self.ynab_txn =
  deepcopy(ynab_txn)` and `self.bal_diff = 0`; keep `MergedTxn_GoodbudgetTxn` unchanged

- [x] T010 [US3] Rename `only_gb_txns` → `only_ynab_txns` in `TxnsGrouped.__init__`
  signature and body in `datatypes.py`; verify the rename is safe by confirming
  `add_new_txns.py` and `graph.py` do not reference `only_gb_txns` (grep confirms zero hits)

- [x] T011 [US3] Update the `MergedTxn` union type in `datatypes.py` to include
  `MergedTxn_YnabTxn`: `MergedTxn = Union[MergedTxn_ChaseTxn, MergedTxn_YnabTxn,
  MergedTxn_BothTxns]`; keep `MergedTxn_GoodbudgetTxn` exported but remove it from the union

**Checkpoint**: User Stories 1, 2, and 3 all independently functional

---

## Phase 6: Polish & Verification

**Purpose**: Safety checks and final validation

- [x] T012 Verify out-of-scope module safety: run
  `python3 -c "import graph; import add_new_txns"` from repo root and confirm no
  `ImportError` or `AttributeError` is raised (if the virtual environment lacks Selenium,
  a missing-dependency error is acceptable — only import-level attribute errors matter)

- [x] T013 Confirm `datatypes.py` has zero references to being called from `main.py`:
  run `from datatypes import YnabTxn, MergedTxn_YnabTxn, MergedTxn_BothTxns, TxnsGrouped,
  _dollars_to_cents` in a standalone Python REPL and verify no error

- [x] T014 Run full test suite `python3 -m pytest tests/test_datatypes.py -v` and confirm
  exactly 4 tests collected and all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US2 (Phase 3)**: Depends on Phase 1 (test file must exist)
- **US1 (Phase 4)**: Depends on US2 implementation (T005) — `YnabTxn` calls `_dollars_to_cents`
- **US3 (Phase 5)**: Depends on US1 (T008) — `MergedTxn_YnabTxn` wraps `YnabTxn`
- **Polish (Phase 6)**: Depends on US3 completion

### Within Each User Story

- Tests (T003/T004, T006/T007) MUST be written and FAIL before implementation (T005, T008)
- T003 and T004 are parallel (separate test functions)
- T006 and T007 are parallel (separate test functions)
- T009 is parallel with T010 and T011 (all touch different parts of datatypes.py — but since
  they're in the same file, sequence them to avoid edit conflicts: T009 → T010 → T011)

### Parallel Opportunities

```bash
# Phase 1: run in parallel
Task: "Create tests/__init__.py"
Task: "Create tests/test_datatypes.py stub"

# Phase 3 tests: run in parallel
Task: "Add test_dollars_to_cents_dollar_sign"
Task: "Add test_dollars_to_cents_negative"

# Phase 4 tests: run in parallel
Task: "Add test_ynab_txn_outflow"
Task: "Add test_ynab_txn_inflow"
```

---

## Implementation Strategy

### MVP First (US2 + US1 Only — 4 Required Tests)

1. Complete Phase 1: Create test file
2. Write US2 tests (T003, T004) → confirm FAIL
3. Implement US2 (T005) → confirm PASS
4. Write US1 tests (T006, T007) → confirm FAIL
5. Implement US1 (T008) → confirm all 4 tests PASS
6. **STOP and VALIDATE**: `python3 -m pytest tests/test_datatypes.py` → 4 passed

This satisfies the spec's Definition of Done for tests and the `YnabTxn` requirement.

### Full Delivery (US3 + Polish)

7. Implement US3 (T009, T010, T011)
8. Run Polish phase (T012, T013, T014)
9. All done

---

## Notes

- `[P]` tasks touch different test functions — they can be written simultaneously but must be
  sequential when in the same file to avoid conflicts; use judgment
- `GoodbudgetTxn` and `MergedTxn_GoodbudgetTxn` are deliberately NOT removed in this task
  (see research.md and plan.md Complexity Tracking)
- `MergedTxn_BothTxns.gb_txn` field rename is deliberately NOT in this task (deferred)
- `file_in.py`, `match.py`, `file_out.py`, `main.py` will have broken imports after this
  task — that is expected per the spec
