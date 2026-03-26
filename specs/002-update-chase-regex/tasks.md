---

description: "Task list for 002-update-chase-regex"
---

# Tasks: Update Chase CSV Parser for New Export Format

**Input**: Design documents from `/specs/002-update-chase-regex/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec. Written before implementation per Constitution Principle III.

**Organization**: US1 (new format parsed correctly) and US2 (`is_pending=False`) are both
P1 and tightly coupled — both are satisfied by the same regex + parser changes. They are
implemented together in a single phase after the tests are written.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1, US2 per spec.md
- All file paths are from the repository root

## Path Conventions

Single project — flat layout at repository root:
- Source modules: `regex.py`, `file_in.py` (repo root)
- Tests: `tests/` (repo root)

---

## Phase 1: Setup

**Purpose**: Create the test file before writing any tests or implementation

- [x] T001 Create `tests/test_file_in.py` with module-level imports:
  `from regex import CH_REGEX` and `from file_in import read_ch_txns, IN_CH_FILE`

---

## Phase 2: Foundational

No shared infrastructure beyond the test file. Both user stories are resolved by the same
two-file change and can be implemented together.

**Checkpoint**: `tests/test_file_in.py` exists → user story work begins

---

## Phase 3: User Story 1 — New Chase Format Parsed Correctly (Priority: P1)

**Goal**: `CH_REGEX` matches the new 7-column Chase CSV format; `read_ch_txns` skips the
header row and correctly constructs `ChaseTxn` objects from the new format.

**Independent Test**:
`python3 -m pytest tests/test_file_in.py::test_ch_regex_sale tests/test_file_in.py::test_ch_regex_payment tests/test_file_in.py::test_ch_regex_no_match_header tests/test_file_in.py::test_read_ch_txns`

### Tests for User Story 1 + User Story 2 ⚠️

> **NOTE: Write ALL tests FIRST, run `python3 -m pytest tests/test_file_in.py` to confirm
> they FAIL (or error), then implement**

- [x] T002 [P] [US1] Add `test_ch_regex_sale` to `tests/test_file_in.py`:
  match `'01/01/2025,01/02/2025,TRADER JOES,Groceries,Sale,-25.00,'` against `CH_REGEX`;
  assert match is not `None`; assert `m['date'] == '01/01/2025'`,
  `m['description'] == 'TRADER JOES'`, `m['amt'] == '-25.00'`

- [x] T003 [P] [US1] Add `test_ch_regex_payment` to `tests/test_file_in.py`:
  match `'01/15/2025,01/15/2025,PAYMENT THANK YOU,Payment,Payment,500.00,'` against
  `CH_REGEX`; assert match is not `None`; assert `m['date'] == '01/15/2025'`,
  `m['description'] == 'PAYMENT THANK YOU'`, `m['amt'] == '500.00'`

- [x] T004 [P] [US1] Add `test_ch_regex_no_match_header` to `tests/test_file_in.py`:
  assert `CH_REGEX.match('Transaction Date,Post Date,Description,Category,Type,Amount,Memo')`
  is `None`

- [x] T005 [US1] [US2] Add `test_read_ch_txns` to `tests/test_file_in.py`:
  write a temp CSV file (using `tempfile` + `unittest.mock.patch` or monkeypatch on
  `file_in.IN_CH_FILE`) with header + 2 data rows (AMAZON sale of -50.00 and PAYMENT
  THANK YOU of 500.00); call `read_ch_txns(ch_start_bal=-100000)`;
  assert `len(result.txns) == 2`, `len(result.lines_failed) == 0`;
  assert AMAZON txn has `amt_cents == -5000`, `is_debit == True`, `is_pending == False`;
  assert PAYMENT THANK YOU txn has `amt_cents == 50000`, `is_debit == False`

### Implementation for User Story 1 + User Story 2

- [x] T006 [US1] Replace `_CH_REGEX_STR` in `regex.py` with the new pattern capturing
  named groups `date` (Transaction Date), `description` (Description), `amt` (Amount);
  pattern must consume but not capture Post Date, Category, Type, Memo;
  Description group must handle both quoted (`"[^"]+"`) and unquoted (`[^,\n]+`) values

- [x] T007 [US1] [US2] Update `read_ch_txns` in `file_in.py`:
  (a) add `if i == 0: continue` before the regex check to skip the header row;
  (b) read `txn['description']` instead of `txn['title']` and pass to `_shorten`;
  (c) set `is_debit=float(txn['amt']) < 0` instead of `deb_or_cred == 'DEBIT'`;
  (d) set `is_pending=False` instead of `txn['balance'] == ' '`;
  then run `python3 -m pytest tests/test_file_in.py` to confirm all four tests pass

**Checkpoint**: All four specified tests pass ✅
`python3 -m pytest tests/test_file_in.py` → 4 passed, 0 failed

---

## Phase 4: Polish & Verification

**Purpose**: Safety checks and final validation

- [x] T008 [P] Verify out-of-scope module safety:
  run `python3 -c "import graph; import add_new_txns; print('ok')"` and confirm no
  `ImportError` or `AttributeError`

- [x] T009 [P] Confirm `read_ch_txns` and `CH_REGEX` are directly importable:
  run `python3 -c "from file_in import read_ch_txns; from regex import CH_REGEX; print('ok')"`
  and confirm no error

- [x] T010 Run full test suite `python3 -m pytest tests/test_file_in.py -v` and confirm
  exactly 4 tests collected and all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **US1+US2 (Phase 3)**: Depends on Phase 1 (test file must exist)
  - Tests (T002–T005) MUST be written and FAIL before implementation (T006–T007)
  - T006 (`regex.py`) before T007 (`file_in.py`) — `read_ch_txns` imports `CH_REGEX`
- **Polish (Phase 4)**: Depends on Phase 3 completion; T008 and T009 are parallel

### Within Phase 3

- T002, T003, T004 are parallel (separate test functions in the same file — write
  sequentially to avoid edit conflicts, but logically independent)
- T005 depends on none of the above tests but is in the same file — add after T004
- T006 must complete before T007 (changed group names must exist before parser uses them)

### Parallel Opportunities

```bash
# Phase 3 tests (write sequentially into same file, logically parallel):
Task: "Add test_ch_regex_sale"
Task: "Add test_ch_regex_payment"
Task: "Add test_ch_regex_no_match_header"
Task: "Add test_read_ch_txns"

# Phase 4 verification (truly parallel):
Task: "Verify out-of-scope module safety"
Task: "Confirm read_ch_txns and CH_REGEX importable"
```

---

## Implementation Strategy

### MVP (All 4 tests — single phase)

1. T001: Create `tests/test_file_in.py`
2. T002–T005: Write all 4 tests → confirm they FAIL
3. T006: Update `CH_REGEX` in `regex.py`
4. T007: Update `read_ch_txns` in `file_in.py`
5. Confirm all 4 tests pass
6. T008–T010: Polish verification

---

## Notes

- `_shorten` appends `'"'` when a string has spaces and doesn't end with `'"'` — e.g.,
  `_shorten('PAYMENT THANK YOU')` → `'PAYMENT THANK YOU"'`. The `test_read_ch_txns` test
  uses the "or its shortened form" qualifier from the spec to account for this.
- The `TypeVar` in `file_in.py` currently uses `GoodbudgetTxn` — this is an existing broken
  import from feature 001 and is out of scope here; do not fix it.
- Only `regex.py` and `file_in.py` are modified; `datatypes.py`, `match.py`, `file_out.py`,
  `config.py`, `main.py` are untouched.
