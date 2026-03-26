---

description: "Task list for 004-csv-reader-parsers"
---

# Tasks: Replace Regex Parsers with csv.reader

**Input**: Design documents from `/specs/004-csv-reader-parsers/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec (FR-013). Written before implementation per
Constitution Principle III. The 3 existing `test_ch_regex_*` tests are removed in
Phase 1 (they test a symbol that will not exist after this feature).

**Organization**: US1 (Chase refactor) and US2 (YNAB new parser) are both P1 and
independent — they touch the same file (`file_in.py`) but different functions, so
they are implemented sequentially within one phase. US3 (dead code removal) is P2
and follows once both parsers are green.

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

**Purpose**: Prepare the test file — update imports and remove the three regex-pattern
tests that directly tested `CH_REGEX` (which will not exist after this feature).

- [x] T001 Update `tests/test_file_in.py`:
  (a) remove `from regex import CH_REGEX` from the import line;
  (b) add `from file_in import read_ynab_txns, IN_YNAB_FILE` to the imports;
  (c) delete `test_ch_regex_sale`, `test_ch_regex_payment`,
  `test_ch_regex_no_match_header` (these three functions test a symbol that will
  not exist); keep `test_read_ch_txns` as-is

---

## Phase 2: Foundational

No shared infrastructure beyond Phase 1. Both user stories can begin once the
test file has been updated.

**Checkpoint**: `tests/test_file_in.py` has updated imports and 3 regex tests removed
→ user story work begins

---

## Phase 3: User Stories 1 + 2 — csv.reader Parsers (Priority: P1)

**Goal (US1)**: `read_ch_txns` uses `csv.reader` internally; behavior for callers
is identical — same `ReadResults` structure, same `ChaseTxn` fields, same
`lines_failed` semantics. Malformed rows (wrong column count) land in `lines_failed`.

**Goal (US2)**: New `read_ynab_txns` uses `csv.reader` with `encoding='utf-8-sig'`;
correctly handles payees containing commas; produces `YnabTxn` objects with the
signed `amt_dollars` derived from Outflow/Inflow columns.

**Independent Test**:
```
.venv/bin/python -m pytest tests/test_file_in.py::test_read_ch_txns_sale \
  tests/test_file_in.py::test_read_ch_txns_payment \
  tests/test_file_in.py::test_read_ch_txns_header_not_in_failed \
  tests/test_file_in.py::test_read_ch_txns_malformed \
  tests/test_file_in.py::test_read_ynab_txns_expense \
  tests/test_file_in.py::test_read_ynab_txns_income \
  tests/test_file_in.py::test_read_ynab_txns_header_not_in_failed \
  tests/test_file_in.py::test_read_ynab_txns_malformed
```

### Tests for User Stories 1 + 2 ⚠️

> **NOTE: Write ALL tests FIRST, run `.venv/bin/python -m pytest tests/test_file_in.py`
> to confirm they FAIL (or error), then implement**

- [x] T002 [P] [US1] Add `test_read_ch_txns_sale` to `tests/test_file_in.py`:
  write a temp CSV (header + one sale row
  `'01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,'`);
  patch `file_in.IN_CH_FILE`; call `read_ch_txns(ch_start_bal=0)`;
  assert `len(result.txns) == 1`, `len(result.lines_failed) == 0`;
  assert `result.txns[0].amt_cents == -5000`,
  `result.txns[0].is_debit is True`,
  `result.txns[0].is_pending is False`

- [x] T003 [P] [US1] Add `test_read_ch_txns_payment` to `tests/test_file_in.py`:
  write a temp CSV (header + one payment row
  `'01/15/2025,01/15/2025,PAYMENT THANK YOU,Payment,Payment,500.00,'`);
  patch `file_in.IN_CH_FILE`; call `read_ch_txns(ch_start_bal=0)`;
  assert `len(result.txns) == 1`, `len(result.lines_failed) == 0`;
  assert `result.txns[0].amt_cents == 50000`,
  `result.txns[0].is_debit is False`

- [x] T004 [P] [US1] Add `test_read_ch_txns_header_not_in_failed` to
  `tests/test_file_in.py`:
  write a temp CSV with only the header line
  `'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'`;
  patch `file_in.IN_CH_FILE`; call `read_ch_txns(ch_start_bal=0)`;
  assert `len(result.lines_failed) == 0`

- [x] T005 [US1] Add `test_read_ch_txns_malformed` to `tests/test_file_in.py`:
  write a temp CSV (header + one 3-column row `'bad,data,row\n'`);
  patch `file_in.IN_CH_FILE`; call `read_ch_txns(ch_start_bal=0)`;
  assert `len(result.txns) == 0`;
  assert `len(result.lines_failed) == 1`

- [x] T006 [P] [US2] Add `test_read_ynab_txns_expense` to `tests/test_file_in.py`:
  write a temp CSV (YNAB header + one expense row
  `'"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"\n'`);
  patch `file_in.IN_YNAB_FILE`; call `read_ynab_txns(ynab_start_bal=0)`;
  assert `len(result.txns) == 1`, `len(result.lines_failed) == 0`;
  assert `result.txns[0].amt_cents == -300`,
  `result.txns[0].category == 'Transportation'`,
  `result.txns[0].cleared == 'Uncleared'`

- [x] T007 [P] [US2] Add `test_read_ynab_txns_income` to `tests/test_file_in.py`:
  write a temp CSV (YNAB header + one income row
  `'"Chase Credit Card","","03/26/2026","Paycheck","Income: Salary","Income","Salary","",$0.00,$1000.00,"Cleared"\n'`);
  patch `file_in.IN_YNAB_FILE`; call `read_ynab_txns(ynab_start_bal=0)`;
  assert `len(result.txns) == 1`, `len(result.lines_failed) == 0`;
  assert `result.txns[0].amt_cents == 100000`

- [x] T008 [P] [US2] Add `test_read_ynab_txns_header_not_in_failed` to
  `tests/test_file_in.py`:
  write a temp CSV with only the YNAB header line;
  patch `file_in.IN_YNAB_FILE`; call `read_ynab_txns(ynab_start_bal=0)`;
  assert `len(result.lines_failed) == 0`

- [x] T009 [US2] Add `test_read_ynab_txns_malformed` to `tests/test_file_in.py`:
  write a temp CSV (YNAB header + one 3-column row `'bad,data,row\n'`);
  patch `file_in.IN_YNAB_FILE`; call `read_ynab_txns(ynab_start_bal=0)`;
  assert `len(result.txns) == 0`;
  assert `len(result.lines_failed) == 1`

### Implementation for User Stories 1 + 2

- [x] T010 [US1] Refactor `read_ch_txns` in `file_in.py`:
  add `import csv` at the top of the file;
  replace the `CH_REGEX.match(line)` loop with `csv.reader(in_file)` enumerated loop;
  keep `if i == 0: continue` for header skip;
  validate `len(row) == 7`; parse `float(row[5])` for Amount;
  set `is_debit=float(row[5]) < 0`, `is_pending=False`,
  `title=_shorten(row[2])`, `date=row[0]`, `amt_dollars=row[5]`;
  append `','.join(row)` to `lines_failed` for invalid rows;
  add `YnabTxn` to imports from `datatypes` and `YNAB_REGEX` removal from regex import
  (update `from regex import CH_REGEX, GB_EXPENSE_REGEX, GB_INCOME_REGEX` →
  leave that import line empty or remove it if nothing is needed from regex)

- [x] T011 [US2] Add `read_ynab_txns` + `IN_YNAB_FILE` to `file_in.py`:
  add `IN_YNAB_FILE = './in/ynab.csv'` constant;
  add `from datatypes import ChaseTxn, YnabTxn` (replace `GoodbudgetTxn`);
  implement `read_ynab_txns(ynab_start_bal: int)` opening `IN_YNAB_FILE` with
  `encoding='utf-8-sig'` and `csv.reader`; skip index 0; validate `len(row) == 11`;
  strip `$` from `row[8]` and `row[9]`; derive signed `amt_dollars`; construct
  `YnabTxn`; running balance pass; then run
  `.venv/bin/python -m pytest tests/test_file_in.py` to confirm all tests pass

**Checkpoint**: All 9 specified tests pass ✅ (8 new + existing `test_read_ch_txns`)
`.venv/bin/python -m pytest tests/test_file_in.py` → 9 passed, 0 failed

---

## Phase 4: User Story 3 — Remove Obsolete Symbols (Priority: P2)

**Goal**: `regex.py` contains only `import re`; `file_in.py` has no references to
`CH_REGEX`, `GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`, `read_gb_txns`, or `IN_GB_FILE`.

**Independent Test**:
```bash
grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py         # must print 0
grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|read_gb_txns\|IN_GB_FILE' file_in.py  # must print 0
```

- [x] T012 [P] [US3] Strip all symbols from `regex.py` — remove `_CH_REGEX_STR`,
  `CH_REGEX`, `_GB_INCOME_REGEX_STR`, `GB_INCOME_REGEX`, `_GB_EXPENSE_REGEX_STR`,
  `GB_EXPENSE_REGEX`; leave file containing only `import re`

- [x] T013 [US3] Clean up `file_in.py`:
  (a) remove `from regex import ...` import line entirely (nothing is imported
  from `regex` after T010);
  (b) remove `from datatypes import ... GoodbudgetTxn ...` — already replaced by
  `ChaseTxn, YnabTxn` in T011 if not done there;
  (c) remove `IN_GB_FILE = './in/goodbudget.csv'` constant;
  (d) remove `read_gb_txns` function body;
  (e) update `TypeVar` to `T = TypeVar('T', ChaseTxn, YnabTxn)` if not done in T010;
  then run `.venv/bin/python -m pytest tests/test_file_in.py` to confirm 9 tests still pass

**Checkpoint**: SC-002 and SC-003 pass; 9 tests still green

---

## Phase 5: Polish & Verification

**Purpose**: Verify all spec Success Criteria

- [x] T014 [P] Verify SC-002: `grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py`
  → output must be `0`

- [x] T015 [P] Verify SC-003:
  `grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|read_gb_txns\|IN_GB_FILE' file_in.py`
  → output must be `0`

- [x] T016 [P] Verify SC-004: `grep -c 'import csv' file_in.py` → output must be `1`

- [x] T017 Run final test suite `.venv/bin/python -m pytest tests/test_file_in.py -v`
  → confirm exactly 9 tests collected and all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1+US2 (Phase 3)**: Depends on Phase 1 (test file prepared)
  - Tests (T002–T009) MUST be written and FAIL before implementation (T010–T011)
  - T010 (Chase refactor) before T011 (YNAB new function) — both touch `file_in.py`;
    do sequentially to avoid edit conflicts
- **US3 (Phase 4)**: Depends on Phase 3 (9 tests green before removing dead code)
  - T012 (`regex.py`) and T013 (`file_in.py`) touch different files — logically parallel,
    write T012 first then T013 to verify imports cleanly
- **Polish (Phase 5)**: Depends on Phase 4; T014, T015, T016 are parallel

### Within Phase 3

- T002, T003, T004, T005 are logically parallel (separate test functions, US1)
  but write sequentially into the same file
- T006, T007, T008, T009 are logically parallel (separate test functions, US2)
  but write sequentially
- T010 must complete before T011 (both modify `file_in.py`)

### Parallel Opportunities

```bash
# Phase 3 tests (write sequentially into same file, logically parallel):
Task: "Add test_read_ch_txns_sale"
Task: "Add test_read_ch_txns_payment"
Task: "Add test_read_ch_txns_header_not_in_failed"
Task: "Add test_read_ch_txns_malformed"
Task: "Add test_read_ynab_txns_expense"
Task: "Add test_read_ynab_txns_income"
Task: "Add test_read_ynab_txns_header_not_in_failed"
Task: "Add test_read_ynab_txns_malformed"

# Phase 5 verification (truly parallel):
Task: "Verify SC-002 (regex.py grep)"
Task: "Verify SC-003 (file_in.py grep)"
Task: "Verify SC-004 (import csv grep)"
```

---

## Implementation Strategy

### MVP (all 8 new tests — single phase)

1. T001: Update test file (remove regex imports + 3 old tests; add YNAB imports)
2. T002–T009: Write all 8 new tests → confirm they FAIL
3. T010: Refactor `read_ch_txns` with `csv.reader`
4. T011: Add `read_ynab_txns` + `IN_YNAB_FILE`
5. Confirm 9 tests pass (8 new + existing `test_read_ch_txns`)
6. T012–T013: Remove dead code
7. T014–T017: Polish verification

---

## Notes

- `test_read_ch_txns` (the original integration test from feature 002) is kept and
  counts toward the 9 passing tests. It tests the same full-parser behavior as the
  new focused tests but with 2 rows.
- T010 and T011 both modify `file_in.py` — write sequentially, not in parallel.
- Removing `read_gb_txns` (T013) will break `graph.py` at runtime. Acknowledged in
  spec Assumptions and plan Complexity Tracking; `graph.py` update is deferred.
- `regex.py` after T012 contains only `import re`. Leave the file; do not delete it
  since other code may `import regex`.
- Tests run via `.venv/bin/python -m pytest` (not system `python3`).
