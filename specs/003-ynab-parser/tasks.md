---

description: "Task list for 003-ynab-parser"
---

# Tasks: Replace Goodbudget Parser with YNAB Parser

**Input**: Design documents from `/specs/003-ynab-parser/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec (FR-011). Written before implementation per Constitution Principle III.

**Organization**: US1 (parser) and US2 (regex) are both P1 and tightly coupled — the regex must exist before the parser can import it. Both are implemented together in Phase 3. US3 (symbol removal) is P2 and follows in Phase 4.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2, US3 per spec.md
- All file paths are from the repository root

## Path Conventions

Single project — flat layout at repository root:
- Source modules: `regex.py`, `file_in.py` (repo root)
- Tests: `tests/` (repo root)

---

## Phase 1: Setup

**Purpose**: Add YNAB import symbols to the existing test file before writing tests

- [x] T001 Add YNAB imports to `tests/test_file_in.py`:
  append `from regex import YNAB_REGEX` and `from file_in import read_ynab_txns, IN_YNAB_FILE`
  after the existing Chase imports (these will error until YNAB symbols are defined —
  that is expected and confirms tests are failing)

---

## Phase 2: Foundational

No shared infrastructure required beyond Phase 1. All user story work can begin
once `tests/test_file_in.py` has the YNAB imports.

**Checkpoint**: `tests/test_file_in.py` has YNAB imports → user story work begins

---

## Phase 3: User Stories 1 + 2 — YNAB_REGEX + read_ynab_txns (Priority: P1)

**Goal**: `YNAB_REGEX` matches the quoted 11-column YNAB CSV format (US2);
`read_ynab_txns` parses the file into `YnabTxn` objects, skipping the header,
deriving a signed `amt_dollars`, and applying `_shorten` to Payee (US1).

**Independent Test**:
```
.venv/bin/python -m pytest tests/test_file_in.py::test_ynab_regex_outflow \
  tests/test_file_in.py::test_ynab_regex_inflow \
  tests/test_file_in.py::test_ynab_regex_no_match_header \
  tests/test_file_in.py::test_read_ynab_txns
```

### Tests for User Stories 1 + 2 ⚠️

> **NOTE: Write ALL tests FIRST, run `.venv/bin/python -m pytest tests/test_file_in.py`
> to confirm they FAIL (or error with ImportError), then implement**

- [x] T002 [P] [US2] Add `test_ynab_regex_outflow` to `tests/test_file_in.py`:
  match `'"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"'`
  against `YNAB_REGEX`; assert match is not `None`;
  assert `m['date'] == '03/25/2026'`, `m['payee'] == 'PATH'`,
  `m['category'] == 'Transportation'`, `m['outflow'] == '3.00'`,
  `m['inflow'] == '0.00'`, `m['cleared'] == 'Uncleared'`

- [x] T003 [P] [US2] Add `test_ynab_regex_inflow` to `tests/test_file_in.py`:
  match `'"Chase Credit Card","","03/26/2026","Paycheck","Income: Salary","Income","Salary","",$0.00,$1000.00,"Cleared"'`
  against `YNAB_REGEX`; assert match is not `None`;
  assert `m['outflow'] == '0.00'`, `m['inflow'] == '1000.00'`, `m['cleared'] == 'Cleared'`

- [x] T004 [P] [US2] Add `test_ynab_regex_no_match_header` to `tests/test_file_in.py`:
  assert `YNAB_REGEX.match('"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"')`
  is `None`

- [x] T005 [US1] Add `test_read_ynab_txns` to `tests/test_file_in.py`:
  write a temp CSV file (using `tempfile` + `unittest.mock.patch` on `file_in.IN_YNAB_FILE`)
  with header + 2 data rows (one expense row: PATH, $3.00 outflow, $0.00 inflow, Uncleared;
  one income row: Paycheck, $0.00 outflow, $1000.00 inflow, Cleared);
  call `read_ynab_txns(ynab_start_bal=0)`;
  assert `len(result.txns) == 2`, `len(result.lines_failed) == 0`;
  assert PATH txn has `amt_cents == -300`, `category == 'Transportation'`, `cleared == 'Uncleared'`;
  assert Paycheck txn has `amt_cents == 100000`, `cleared == 'Cleared'`

### Implementation for User Stories 1 + 2

- [x] T006 [US2] Add `YNAB_REGEX` to `regex.py`:
  define `_YNAB_REGEX_STR` capturing named groups `date` (col 2), `payee` (col 3),
  `category` (col 6), `outflow` (col 8, after `\$`), `inflow` (col 9, after `\$`),
  `cleared` (col 10); compile as `YNAB_REGEX = re.compile(_YNAB_REGEX_STR)`;
  pattern must skip cols 0, 1, 4, 5, 7 without capturing them;
  the `\$\d+\.\d\d` pattern for outflow/inflow is what prevents the header from matching

- [x] T007 [US1] Add `read_ynab_txns` + `IN_YNAB_FILE` to `file_in.py`:
  (a) add `IN_YNAB_FILE = './in/ynab.csv'` constant;
  (b) add `from regex import YNAB_REGEX` import (alongside existing `CH_REGEX` import);
  (c) implement `read_ynab_txns(ynab_start_bal: int)` that opens `IN_YNAB_FILE` with
  `encoding='utf-8-sig'`, skips line 0 explicitly (`if i == 0: continue`),
  matches each line against `YNAB_REGEX`, derives `amt_dollars` from outflow/inflow
  (negative if outflow > 0, positive if inflow > 0, else `"0.00"`),
  constructs `YnabTxn(id_=i, ts=..., date=..., title=_shorten(payee), category=...,
  amt_dollars=..., cleared=...)`, appends non-matching lines to `lines_failed`,
  then runs the running balance pass using `ynab_start_bal`;
  (d) update the `TypeVar` in `file_in.py` from `GoodbudgetTxn` to `YnabTxn`;
  then run `.venv/bin/python -m pytest tests/test_file_in.py` to confirm all 8 tests pass

**Checkpoint**: All 8 specified tests pass ✅
`.venv/bin/python -m pytest tests/test_file_in.py` → 8 passed, 0 failed

---

## Phase 4: User Story 3 — Remove Old Goodbudget Symbols (Priority: P2)

**Goal**: `regex.py` has zero references to `GB_EXPENSE_REGEX` or `GB_INCOME_REGEX`;
`file_in.py` has zero references to `read_gb_txns`, `GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`,
or `IN_GB_FILE`.

**Independent Test**:
```bash
grep -c 'GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py       # must print 0
grep -c 'read_gb_txns\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|IN_GB_FILE' file_in.py  # must print 0
```

- [x] T008 [P] [US3] Remove `GB_EXPENSE_REGEX` and `GB_INCOME_REGEX` definitions from `regex.py`
  (remove the `_GB_EXPENSE_REGEX_STR`, `_GB_INCOME_REGEX_STR`, `GB_EXPENSE_REGEX`,
  `GB_INCOME_REGEX` symbols and any associated imports)

- [x] T009 [US3] Remove `read_gb_txns`, `IN_GB_FILE`, and all references to `GB_EXPENSE_REGEX`
  and `GB_INCOME_REGEX` from `file_in.py`
  (remove the function body, the constant, and update any imports from `regex` that
  no longer need those symbols); then confirm `.venv/bin/python -m pytest tests/test_file_in.py`
  still shows 8 passed

**Checkpoint**: SC-002 and SC-003 pass; all 8 tests still green

---

## Phase 5: Polish & Verification

**Purpose**: Safety checks and final validation against spec Success Criteria

- [x] T010 [P] Verify SC-002: run `grep -c 'GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py`
  and confirm output is `0`

- [x] T011 [P] Verify SC-003: run
  `grep -c 'read_gb_txns\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|IN_GB_FILE' file_in.py`
  and confirm output is `0`

- [x] T012 [P] Verify SC-004: run
  `python3 -c "from regex import YNAB_REGEX; m = YNAB_REGEX.match('\"Chase Credit Card\",\"\",\"03/25/2026\",\"PATH\",\"Needs: Transportation\",\"Needs\",\"Transportation\",\"\",$3.00,$0.00,\"Uncleared\"'); print(m['outflow'], m['inflow'], m['cleared'])"`
  and confirm output is `3.00 0.00 Uncleared`

- [x] T013 Run full test suite `.venv/bin/python -m pytest tests/test_file_in.py -v`
  and confirm exactly 8 tests collected and all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1+US2 (Phase 3)**: Depends on Phase 1 (YNAB imports in test file)
  - Tests (T002–T005) MUST be written and FAIL before implementation (T006–T007)
  - T006 (`regex.py`) before T007 (`file_in.py`) — `read_ynab_txns` imports `YNAB_REGEX`
- **US3 (Phase 4)**: Depends on Phase 3 completion (all 8 tests green before removing dead code)
- **Polish (Phase 5)**: Depends on Phase 4 completion; T010, T011, T012 are parallel

### Within Phase 3

- T002, T003, T004 are parallel (separate test functions, write sequentially to avoid conflicts)
- T005 depends on none of the above but is in the same file — add after T004
- T006 must complete before T007 (YNAB_REGEX must exist before file_in imports it)

### Within Phase 4

- T008 (`regex.py`) and T009 (`file_in.py`) touch different files — logically parallel,
  but write sequentially; T009 should be done last so `grep` checks can confirm both

### Parallel Opportunities

```bash
# Phase 3 tests (write sequentially into same file, logically parallel):
Task: "Add test_ynab_regex_outflow"
Task: "Add test_ynab_regex_inflow"
Task: "Add test_ynab_regex_no_match_header"
Task: "Add test_read_ynab_txns"

# Phase 5 verification (truly parallel):
Task: "Verify SC-002 (regex.py grep)"
Task: "Verify SC-003 (file_in.py grep)"
Task: "Verify SC-004 (YNAB_REGEX example match)"
```

---

## Implementation Strategy

### MVP (All 4 tests — single phase)

1. T001: Add YNAB imports to `tests/test_file_in.py`
2. T002–T005: Write all 4 tests → confirm they FAIL (ImportError or AssertionError)
3. T006: Add `YNAB_REGEX` in `regex.py`
4. T007: Add `read_ynab_txns` + `IN_YNAB_FILE` in `file_in.py`; update TypeVar
5. Confirm all 8 tests pass (4 new YNAB + 4 existing Chase)
6. T008–T009: Remove old Goodbudget symbols
7. T010–T013: Polish verification

---

## Notes

- `_shorten` appends `'"'` when a string has spaces and doesn't end with `'"'`. Tests should
  use `'PATH' in t.title` (or check `t.title == 'PATH'` — single-word payees are unaffected).
- The `TypeVar` update in T007 is mechanical: `GoodbudgetTxn` → `YnabTxn`. No behavioral change.
- Removing `read_gb_txns` (T009) will break `graph.py` at runtime — this is acknowledged in the
  spec Assumptions and plan Complexity Tracking. `graph.py` is out of scope; its fix is deferred.
- Only `regex.py` and `file_in.py` are modified; `datatypes.py`, `match.py`, `file_out.py`,
  `config.py`, `main.py` are untouched.
- Tests run via `.venv/bin/python -m pytest` (not system `python3 -m pytest`).
