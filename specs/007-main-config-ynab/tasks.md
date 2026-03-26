---

description: "Task list for 007-main-config-ynab"
---

# Tasks: Update main.py and config.py to Use YNAB Types

**Input**: Design documents from `/specs/007-main-config-ynab/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Tests**: Explicitly required by spec (FR-010, FR-011). TDD: write both tests
first, verify they fail, then implement.

**Organization**: Both user stories are P1. US1 drives all implementation;
US2 is a read-only grep verification. No blocking foundational phase — all
dependencies already exist.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no inter-task dependency)
- **[Story]**: US1, US2 per spec.md
- All paths relative to repository root

---

## Phase 1: Setup

No project initialization needed. All modules (`file_in`, `match`, `file_out`,
`config`, `datatypes`) are already in place.

---

## Phase 2: Foundational

No shared infrastructure blocks any story. Proceeding directly to user stories.

---

## Phase 3: User Story 1 — Pipeline Runs End-to-End with YNAB Data (Priority: P1)

**Goal**: (1) Write two failing integration tests in `tests/test_main.py`;
(2) update `config.py` and rewrite `main.py` so both tests pass.

**Independent Test**:
```
.venv/bin/python -m pytest tests/test_main.py -v
```
→ 2 collected, 2 passed.

### Tests (TDD — write first, verify they fail before implementation)

- [x] T001 [US1] Create `tests/test_main.py` with `test_main_end_to_end`:
  add `import os, subprocess, sys, tempfile` and `from pathlib import Path`;
  compute `MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'`;
  use `tempfile.TemporaryDirectory()` as `tmpdir`;
  create `Path(tmpdir) / 'in'` directory;
  write `(Path(tmpdir) / 'in' / 'chase.csv')` with contents:
  ```
  Transaction Date,Post Date,Description,Category,Type,Amount,Memo
  01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,
  ```
  write `(Path(tmpdir) / 'in' / 'ynab.csv')` with contents:
  ```
  "Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"
  "Chase Credit Card","","01/05/2025","Amazon","Wants: Shopping","Wants","Shopping","",$50.00,$0.00,"Cleared"
  ```
  write `(Path(tmpdir) / '.env')` with contents `'CH_START_BAL=0\nYNAB_START_BAL=0'`;
  run `subprocess.run([sys.executable, str(MAIN_PY)], cwd=tmpdir, capture_output=True, text=True)`;
  assert `result.returncode == 0`;
  find subdirectories under `Path(tmpdir) / 'out'` and assert at least one exists;
  let `out_dir` be the first subdirectory;
  assert each of `chase.csv`, `ynab.csv`, `both.csv`, `merged.csv`,
  `bal_diff_freq.csv`, `log.txt` exists in `out_dir`;
  read `both.csv` and assert it has exactly 2 lines (header + 1 data row);
  read `log.txt` and assert `'AMT OF MATCHED TXNS: 1'` is in its contents

- [x] T002 [US1] Add `test_main_no_env` to `tests/test_main.py`:
  use `tempfile.TemporaryDirectory()` as `tmpdir`;
  create `Path(tmpdir) / 'in'` directory;
  write the same `chase.csv` and `ynab.csv` as T001 but write no `.env`;
  run `subprocess.run([sys.executable, str(MAIN_PY)], cwd=tmpdir, capture_output=True, text=True)`;
  assert `result.returncode != 0`;
  assert `'no .env' in (result.stdout + result.stderr).lower()`

- [x] T003 [US1] Run `.venv/bin/python -m pytest tests/test_main.py -v` and
  confirm both tests are collected and FAIL (expected: `ImportError` for
  `read_gb_txns` or `AttributeError` for `config.gb_start_bal` or
  `AttributeError` for `config.ynab_start_bal`)

### Implementation

- [x] T004 [P] [US1] Update `config.py`: replace the `gb_start_bal` block
  (`gb_start_bal = env["GB_START_BAL"] ...` and `self.gb_start_bal = _str_to_int(gb_start_bal)`)
  with `ynab_start_bal = env["YNAB_START_BAL"] if "YNAB_START_BAL" in env and env["YNAB_START_BAL"] is not None else ""`
  and `self.ynab_start_bal = _str_to_int(ynab_start_bal)`;
  remove the `GB_USERNAME` block (the `if "GB_USERNAME" in env ...` conditional
  and `print("Warning: GB_USERNAME not found...")` and `self.gb_username = ...`);
  remove the `GB_PASSWORD` block similarly

- [x] T005 [P] [US1] Rewrite `main.py` with the following complete content
  (replacing the entire file):
  ```python
  from dotenv import dotenv_values

  from config import Config
  from file_in import read_ch_txns, read_ynab_txns
  from file_out import Logger, OUT_DIR
  from match import get_txns_grouped

  if __name__ == "__main__":
      ENV = dotenv_values(".env")
      if not ENV:
          print("Error, no .env file found.")
          exit(1)
      config = Config(ENV)

      ch_txns_result = read_ch_txns(config.ch_start_bal)
      ynab_txns_result = read_ynab_txns(config.ynab_start_bal)
      ch_txns = ch_txns_result.txns
      ynab_txns = ynab_txns_result.txns

      txns_grouped = get_txns_grouped(
          ch_txns, ynab_txns, config.ch_start_bal, config.ynab_start_bal)

      log = Logger()
      log.lines_failed(ch_txns_result.lines_failed)
      log.lines_failed(ynab_txns_result.lines_failed)
      log.amt_matched_and_unmatched(txns_grouped)
      log.txns_grouped(txns_grouped)
      print(f"Saved to: {OUT_DIR}")
  ```

- [x] T006 [US1] Run `.venv/bin/python -m pytest tests/test_main.py -v` and
  confirm exactly 2 tests collected and all pass (green)

**Checkpoint**: `tests/test_main.py` has 2 passing integration tests ✅

---

## Phase 4: User Story 2 — Banned Symbols Removed (Priority: P1)

**Goal**: Confirm zero references to the banned Goodbudget symbols in `main.py`
and `config.py`.

**Independent Test**:
```bash
grep -cE 'add_new_txns|read_gb_txns|gb_txns|gb_start_bal|--add' main.py
grep -cE 'GB_START_BAL|gb_username|gb_password' config.py
```
→ both return `0`.

- [x] T007 [US2] Run `grep -cE 'add_new_txns|read_gb_txns|gb_txns|gb_start_bal|--add' main.py`
  and confirm output is `0` (SC-003)

- [x] T008 [US2] Run `grep -cE 'GB_START_BAL|gb_username|gb_password' config.py`
  and confirm output is `0` (SC-004)

**Checkpoint**: SC-003 and SC-004 confirmed ✅

---

## Phase 5: Polish & Verification

- [x] T009 Verify scope isolation: run
  `python3 -c "import graph; import add_new_txns"` and confirm no
  `ImportError` or `AttributeError` is raised (constitution IV gate)

- [x] T010 Run full test suite `.venv/bin/python -m pytest -v` and confirm all
  21 tests pass (19 existing + 2 new) (SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **US1 (Phase 3)**: T001 + T002 written first → T003 red check → T004 + T005
  implementation (parallel, different files) → T006 green check
- **US2 (Phase 4)**: Logically independent (grep only); run after T005 completes
- **Polish (Phase 5)**: After all US phases; T009 and T010 can run in parallel

### Within Phase 3

- T001 must be written first (creates the file, defines `MAIN_PY`)
- T002 depends on T001 (appends to same file)
- T003 depends on T001–T002 (red check)
- **T004 and T005 are parallel** — different files (`config.py` and `main.py`)
- T006 depends on T004 and T005

### Parallel Opportunities

```bash
# T004 and T005 touch different files — run together:
Task T004: Update config.py (ynab_start_bal, remove gb_username/gb_password)
Task T005: Rewrite main.py (read_ynab_txns, remove --add / add_new_txns)

# T007 and T008 are independent reads — run together:
Task T007: grep main.py for banned symbols
Task T008: grep config.py for banned symbols

# T009 and T010 are independent — run together:
Task T009: scope isolation import check
Task T010: full pytest suite
```

---

## Implementation Strategy

### MVP (single sequence)

1. T001: Write `test_main_end_to_end`
2. T002: Write `test_main_no_env`
3. T003: Confirm both fail (red)
4. T004 + T005: Update `config.py` and rewrite `main.py` (parallel)
5. T006: Confirm 2 tests pass (green)
6. T007 + T008: Confirm grep = 0 (parallel)
7. T009 + T010: Scope isolation + full suite (parallel)

---

## Notes

- **TDD**: T001–T002 must be written and fail (T003) before any implementation.
- **`sys.executable`** is essential in subprocess calls — bare `python3` may not
  have `python-dotenv` installed.
- **`MAIN_PY`** must be the absolute path to `main.py`:
  `Path(__file__).resolve().parent.parent / 'main.py'`.
- **`both.csv` row count**: the file has 1 header line + N data rows. For 1 matched
  pair, `len(both_csv_lines_stripped) == 2` (or `splitlines()` count is 2 with
  a possible trailing newline — use `strip().splitlines()` to be safe).
- **`log.txt` check**: use `'AMT OF MATCHED TXNS: 1' in log_txt_content`.
- **T005**: `main.py` is a complete rewrite — read the current file first per
  tool requirements, then overwrite with the new content.
- **T004**: `config.py` is a targeted edit — remove 3 blocks, add 2 lines.
- Total tasks: 10 across 4 active phases (US1: 6, US2: 2, Polish: 2).
