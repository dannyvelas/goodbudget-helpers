---

description: "Task list for 006-file-out-ynab"
---

# Tasks: Update file_out.py to Use YNAB Types

**Input**: Design documents from `/specs/006-file-out-ynab/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec (FR-009, FR-010). The two test functions in
`tests/test_file_out.py` are written before the implementation (TDD).

**Organization**: US1 (update `file_out.py` + write tests) and US2 (verify no
Goodbudget symbols) are both P1. US1 drives all implementation; US2 is a read-only
grep verification that follows US1. No blocking foundational phase — `datatypes.py`
already exports `YnabTxn` and `MergedTxn_YnabTxn`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or no inter-task dependencies)
- **[Story]**: US1, US2 per spec.md
- All file paths from the repository root

---

## Phase 1: Setup

No project initialization required. `datatypes`, `file_out`, and `pytest` are
already available in the existing venv. Proceeding directly to user story phases.

---

## Phase 2: Foundational

No shared infrastructure blocks any user story. `YnabTxn` and `MergedTxn_YnabTxn`
are already importable from `datatypes`. Tests and implementation can start
immediately.

---

## Phase 3: User Story 1 — Update file_out.py + Write Tests (Priority: P1)

**Goal**: (1) Write two failing tests in `tests/test_file_out.py`; (2) Update
`file_out.py` with all YNAB renames so both tests pass.

**Independent Test**:
```
.venv/bin/python -m pytest tests/test_file_out.py -v
```
→ 2 collected, 2 passed.

### Tests (TDD — write first, verify they fail before implementation)

- [x] T001 [US1] Create `tests/test_file_out.py` with imports and `test_ynab_txn_to_row`:
  add `from datatypes import YnabTxn, MergedTxn_YnabTxn` and
  `from file_out import _ynab_txn_to_row, _merged_txn_to_row`;
  construct `YnabTxn(id_=3, ts=1735689600, date='01/01/2025', title='Trader Joes',
  category='Groceries', amt_dollars='-25.00', cleared='Cleared')`;
  set `txn.bal = 97500`;
  call `result = _ynab_txn_to_row(txn)`;
  assert `result == '3,01/01/2025,Trader Joes,Groceries,-25.00,975.0'`

- [x] T002 [US1] Add `test_merged_txn_ynab_only_type_label` to `tests/test_file_out.py`:
  construct `MergedTxn_YnabTxn(ynab_txn)` using the same `txn` from T001;
  call `result = _merged_txn_to_row(merged_txn)`;
  assert `result.startswith('YNAB,')`

- [x] T003 [US1] Run `.venv/bin/python -m pytest tests/test_file_out.py -v` and
  confirm both tests are collected and FAIL (ImportError or AttributeError expected
  since `_ynab_txn_to_row` does not yet exist in `file_out.py`)

### Implementation

- [x] T004 [US1] Update imports in `file_out.py`: replace `GoodbudgetTxn` and
  `MergedTxn_GoodbudgetTxn` with `YnabTxn` and `MergedTxn_YnabTxn` in the
  `from datatypes import (...)` block

- [x] T005 [US1] Rename constants and row function in `file_out.py`:
  rename `_AMT_GB_FIELDS` → `_AMT_YNAB_FIELDS` (value stays `6`);
  rename `_GB_FIELD_NAMES` → `_YNAB_FIELD_NAMES` with value
  `'YNAB ID,YNAB Date,YNAB Title,YNAB Category,YNAB Txn Amount,YNAB Balance'`;
  rename `_gb_txn_to_row` → `_ynab_txn_to_row`, change parameter to
  `ynab_txn: YnabTxn`, change body to use `ynab_txn.category` instead of
  `gb_txn.envelope`

- [x] T006 [US1] Update `_merged_txn_to_row` in `file_out.py`:
  replace `isinstance(merged_txn, MergedTxn_GoodbudgetTxn)` with
  `isinstance(merged_txn, MergedTxn_YnabTxn)`;
  replace `txn_type = 'GOODBUDGET'` with `txn_type = 'YNAB'`;
  replace `gb_row = _gb_txn_to_row(merged_txn.gb_txn)` with
  `ynab_row = _ynab_txn_to_row(merged_txn.ynab_txn)`;
  update `gb_row` variable references to `ynab_row` and `_AMT_GB_FIELDS` to
  `_AMT_YNAB_FIELDS` throughout the function;
  update the `_MERGED_TXN_FIELD_NAMES` constant to reference `_YNAB_FIELD_NAMES`

- [x] T007 [US1] Update `Logger.__init__` in `file_out.py`:
  rename `self.gb_file = f'{OUT_DIR}/goodbudget.csv'` to
  `self.ynab_file = f'{OUT_DIR}/ynab.csv'`

- [x] T008 [US1] Update `Logger.amt_matched_and_unmatched` in `file_out.py`:
  replace `'AMT OF UNMATCHED GOODBUDGET TXNS: {len(txns_grouped.only_gb_txns)}'`
  with `'AMT OF UNMATCHED YNAB TXNS: {len(txns_grouped.only_ynab_txns)}'`

- [x] T009 [US1] Update `Logger.txns_grouped` in `file_out.py`:
  replace `with open(self.gb_file, 'w')` with `with open(self.ynab_file, 'w')`;
  replace `_GB_FIELD_NAMES` with `_YNAB_FIELD_NAMES`;
  replace `txns_grouped.only_gb_txns` with `txns_grouped.only_ynab_txns`;
  replace `_gb_txn_to_row` with `_ynab_txn_to_row`

- [x] T010 [US1] Run `.venv/bin/python -m pytest tests/test_file_out.py -v` and
  confirm exactly 2 tests collected and all pass

**Checkpoint**: `tests/test_file_out.py` exists with 2 passing tests ✅

---

## Phase 4: User Story 2 — Verify No Goodbudget Symbols in file_out.py (Priority: P1)

**Goal**: Confirm SC-002 — `file_out.py` contains zero references to the six banned
Goodbudget symbols.

**Independent Test**:
```bash
grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|_GB_FIELD_NAMES\|_AMT_GB_FIELDS\|gb_file\|only_gb_txns' file_out.py
```
→ output must be `0`.

- [x] T011 [US2] Run `grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|_GB_FIELD_NAMES\|_AMT_GB_FIELDS\|gb_file\|only_gb_txns' file_out.py`
  and confirm output is `0` (SC-002)

**Checkpoint**: SC-002 confirmed ✅

---

## Phase 5: Polish & Verification

- [x] T012 Run full test suite `.venv/bin/python -m pytest -v` and confirm all
  existing tests still pass alongside the 2 new ones (SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies

- **US1 (Phase 3)**: No dependencies — tests written first (T001–T003), then
  implementation (T004–T009), then green check (T010)
- **US2 (Phase 4)**: Logically independent (grep is read-only), but run after
  US1 so both are verified together in T012
- **Polish (Phase 5)**: Depends on US1 and US2 both complete

### Within Phase 3

- T001 must be written first (creates the file with imports)
- T002 depends on T001 (appends to same file)
- T003 depends on T001–T002 (red check)
- T004–T009 are implementation tasks; T004 (imports) should come first;
  T005–T009 are independent of each other but all depend on T004
- T010 depends on T001–T009

### Parallel Opportunities

```bash
# T005–T009 touch file_out.py sequentially (same file); write in order:
Task T004: Fix imports
Task T005: Rename constants + _ynab_txn_to_row
Task T006: Update _merged_txn_to_row
Task T007: Update Logger.__init__
Task T008: Update Logger.amt_matched_and_unmatched
Task T009: Update Logger.txns_grouped

# T011 and T012 are independent reads; can run together after T010:
Task T011: grep verification
Task T012: full pytest suite
```

---

## Implementation Strategy

### MVP (single phase)

1. T001: Create `tests/test_file_out.py` with `test_ynab_txn_to_row`
2. T002: Add `test_merged_txn_ynab_only_type_label`
3. T003: Confirm both fail (red)
4. T004–T009: Update `file_out.py` with all YNAB renames
5. T010: Confirm 2 passed (green)
6. T011: Confirm SC-002 grep = 0
7. T012: Confirm full suite green

---

## Notes

- TDD: tests T001–T002 must be written and fail (T003) before implementation begins.
- `_ynab_txn_to_row` and `_merged_txn_to_row` are module-level functions; import
  them directly via `from file_out import _ynab_txn_to_row, _merged_txn_to_row`.
- `MergedTxn_YnabTxn` constructor takes `ynab_txn` as its argument; check
  `datatypes.py` if uncertain of the signature.
- `bal/100` in Python produces a float: `97500/100 == 975.0`. The f-string
  `f'{txn.bal/100}'` renders as `'975.0'` — matches the expected assert.
- `file_out.py` is not a new file; every Edit must read the current state first.
- Tests run via `.venv/bin/python -m pytest` (not system `python3`).
- Total tasks: 12 across 3 active phases (US1: 10, US2: 1, Polish: 1).
