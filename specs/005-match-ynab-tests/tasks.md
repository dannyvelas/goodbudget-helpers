---

description: "Task list for 005-match-ynab-tests"
---

# Tasks: Add Tests for match.py YNAB Type Migration

**Input**: Design documents from `/specs/005-match-ynab-tests/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec (FR-001–FR-004). The three test functions are
the entire deliverable of this feature.

**Organization**: US1 (write the 3 tests) and US2 (verify no GB symbols in match.py)
are both P1. US2 is a single grep — no implementation; it immediately follows US1.
No setup or foundational phases are needed: `tests/test_match.py` is a new file with
no blocking dependencies.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or no inter-task dependencies)
- **[Story]**: US1, US2 per spec.md
- All file paths from the repository root

---

## Phase 1: Setup

No project initialization required. `datatypes` and `match` are already importable;
no new packages need to be installed. Proceeding directly to user story phases.

---

## Phase 2: Foundational

No shared infrastructure blocks any user story. Tests/test_match.py is a new file
with no prerequisites beyond the existing venv.

---

## Phase 3: User Story 1 — Write Three Matching Tests (Priority: P1)

**Goal**: Create `tests/test_match.py` containing `test_match_both_txns`,
`test_match_only_ch_and_only_ynab`, and `test_match_outside_7_days`. All three
must pass against the already-updated `match.py`.

**Independent Test**:
```
.venv/bin/python -m pytest tests/test_match.py -v
```
→ 3 collected, 3 passed.

- [x] T001 [US1] Create `tests/test_match.py` with imports and `test_match_both_txns`:
  add `from datatypes import ChaseTxn, YnabTxn` and `from match import get_txns_grouped`;
  construct `ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
  date='01/01/2025', title='Amazon', amt_dollars='-25.00')` and
  `YnabTxn(id_=0, ts=1735689600, date='01/01/2025', title='Amazon',
  category='Shopping', amt_dollars='-25.00', cleared='Cleared')`;
  call `result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)`;
  assert `len(result.both_txns) == 1`, `len(result.only_ch_txns) == 0`,
  `len(result.only_ynab_txns) == 0`

- [x] T002 [US1] Add `test_match_only_ch_and_only_ynab` to `tests/test_match.py`:
  construct `ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
  date='01/01/2025', title='Amazon', amt_dollars='-25.00')` and
  `YnabTxn(id_=0, ts=1735689600, date='01/01/2025', title='Amazon',
  category='Shopping', amt_dollars='-30.00', cleared='Cleared')`;
  call `result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)`;
  assert `len(result.only_ch_txns) == 1`, `len(result.only_ynab_txns) == 1`,
  `len(result.both_txns) == 0`

- [x] T003 [US1] Add `test_match_outside_7_days` to `tests/test_match.py`:
  construct `ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
  date='01/01/2025', title='Amazon', amt_dollars='-25.00')` and
  `YnabTxn(id_=0, ts=1736380800, date='01/09/2025', title='Amazon',
  category='Shopping', amt_dollars='-25.00', cleared='Cleared')`;
  call `result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)`;
  assert `len(result.both_txns) == 0`, `len(result.only_ch_txns) == 1`,
  `len(result.only_ynab_txns) == 1`

- [x] T004 [US1] Run `.venv/bin/python -m pytest tests/test_match.py -v` and confirm
  exactly 3 tests collected and all pass

**Checkpoint**: `tests/test_match.py` exists with 3 passing tests ✅

---

## Phase 4: User Story 2 — Verify No Goodbudget Symbols in match.py (Priority: P1)

**Goal**: Confirm SC-002 — `match.py` contains zero references to the six banned
Goodbudget symbols.

**Independent Test**:
```bash
grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|gb_txn\|gb_sorted\|gb_bal\|only_gb_txns' match.py
```
→ output must be `0`.

- [x] T005 [US2] Run `grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|gb_txn\|gb_sorted\|gb_bal\|only_gb_txns' match.py`
  and confirm output is `0` (SC-002)

**Checkpoint**: SC-002 confirmed ✅

---

## Phase 5: Polish & Verification

- [x] T006 Run full test suite `.venv/bin/python -m pytest -v` and confirm all
  existing tests still pass alongside the 3 new ones (SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies

- **US1 (Phase 3)**: No dependencies — start immediately
- **US2 (Phase 4)**: Logically independent of US1 (grep is read-only), but run
  after US1 so both are verified together in T006
- **Polish (Phase 5)**: Depends on US1 and US2 both complete

### Within Phase 3

- T001 must be written first (creates the file with imports)
- T002 and T003 depend on T001 (append to the same file) — write sequentially
- T004 depends on T001–T003

### Parallel Opportunities

```bash
# Phase 3: all three tests go into the same file — write sequentially:
Task T001: Create file + test_match_both_txns
Task T002: Append test_match_only_ch_and_only_ynab
Task T003: Append test_match_outside_7_days

# Phase 4+5 are independent reads:
Task T005: grep match.py
Task T006: run full pytest suite
```

---

## Implementation Strategy

### MVP (single phase)

1. T001: Create `tests/test_match.py` with `test_match_both_txns`
2. T002: Add `test_match_only_ch_and_only_ynab`
3. T003: Add `test_match_outside_7_days`
4. T004: Confirm 3 passed
5. T005: Confirm SC-002 grep = 0
6. T006: Confirm full suite green

---

## Notes

- No mocking or temp files needed — `get_txns_grouped` takes plain lists.
- `YnabTxn.bal` is `0` by default; no manual assignment needed.
- Tests run via `.venv/bin/python -m pytest` (not system `python3`).
- `match.py` is not modified in this feature; T005 is a read-only verification.
- Total tasks: 6 across 3 active phases (US1: 4, US2: 1, Polish: 1).
