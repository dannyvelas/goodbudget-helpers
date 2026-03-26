# Feature Specification: Update main.py and config.py to Use YNAB Types

**Feature Branch**: `007-main-config-ynab`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Pipeline Runs End-to-End with YNAB Data (Priority: P1)

Running `python3 main.py` from a directory with `./in/chase.csv`, `./in/ynab.csv`,
and `.env` (containing `CH_START_BAL` and `YNAB_START_BAL`) reads both CSV files,
matches transactions, writes all output files to `./out/<timestamp>/`, and prints
the output path. No flags are required or accepted. The bot-adding feature is
completely removed.

**Why this priority**: This is the entire deliverable. Without this working, the
pipeline produces no output and `main.py` is broken against the updated YNAB types.

**Independent Test**: Run `python3 main.py` as a subprocess from a temp directory
containing valid input files and `.env`. Assert exit code 0, output directory
exists under `./out/`, and all expected output files are present.

**Acceptance Scenarios**:

1. **Given** valid `./in/chase.csv`, `./in/ynab.csv`, and `.env` with
   `CH_START_BAL=0` and `YNAB_START_BAL=0`, **When** `python3 main.py` is run,
   **Then** it exits 0, creates `./out/<timestamp>/` containing `chase.csv`,
   `ynab.csv`, `both.csv`, `merged.csv`, `bal_diff_freq.csv`, and `log.txt`, and
   prints the output path.

2. **Given** one matching transaction pair in each input file, **When**
   `python3 main.py` is run, **Then** `both.csv` contains exactly 1 data row and
   `log.txt` contains `'AMT OF MATCHED TXNS: 1'`.

3. **Given** no `.env` file present, **When** `python3 main.py` is run, **Then**
   it exits with a non-zero code and stdout/stderr contains `'no .env'`.

---

### User Story 2 — Banned Symbols Removed from main.py and config.py (Priority: P1)

After this feature, `main.py` contains no references to `add_new_txns`,
`read_gb_txns`, `gb_txns`, `gb_start_bal`, or `--add`. `config.py` contains no
references to `GB_START_BAL`, `gb_username`, or `gb_password`.

**Why this priority**: These stale symbols cause `ImportError`/`AttributeError`
at runtime since `read_gb_txns` was removed and `gb_start_bal` no longer exists
on `Config`.

**Independent Test**: Grep for each banned symbol in `main.py` and `config.py`;
all counts must be `0`.

**Acceptance Scenarios**:

1. **Given** the updated files, **When** grepped for any banned symbol,
   **Then** zero matches are found in both files.

---

### Edge Cases

- `dotenv_values(".env")` returns an empty dict `{}` when the file does not exist
  (not `None`). The empty-dict check `if not ENV` handles both "file missing" and
  "file empty" cases.
- The error message for a missing `.env` must contain `'no .env'` in stdout or
  stderr.
- `main.py` accepts zero command-line arguments. Any argument causes it to print
  usage and exit non-zero; the `--add` branch is fully removed.
- `config.py` prints no warnings for `GB_USERNAME` or `GB_PASSWORD` since those
  fields are removed entirely.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `config.py` MUST read `YNAB_START_BAL` from the `.env` dict and
  store it as `self.ynab_start_bal` (integer cents, via `_str_to_int`).

- **FR-002**: `config.py` MUST NOT reference `GB_START_BAL`, `gb_username`, or
  `gb_password` in any form.

- **FR-003**: `main.py` MUST import `read_ynab_txns` (not `read_gb_txns`) from
  `file_in`.

- **FR-004**: `main.py` MUST call `read_ynab_txns(config.ynab_start_bal)` and
  use the result's `.txns` as the YNAB transaction list and `.lines_failed` for
  logging.

- **FR-005**: `main.py` MUST pass `ynab_txns` and `config.ynab_start_bal` to
  `get_txns_grouped`.

- **FR-006**: `main.py` MUST NOT import or call `add_new_txns`.

- **FR-007**: `main.py` MUST NOT parse a `--add` flag or branch on any
  `add_txns` boolean.

- **FR-008**: `main.py` MUST NOT contain the "pending amounts" print block
  (the loop computing `amt_pending`).

- **FR-009**: The error message when `.env` is missing/empty MUST contain the
  substring `'no .env'` in stdout or stderr.

- **FR-010**: `tests/test_main.py` MUST contain `test_main_end_to_end`:
  create a temp directory; inside it create `./in/chase.csv`:
  ```
  Transaction Date,Post Date,Description,Category,Type,Amount,Memo
  01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,
  ```
  and `./in/ynab.csv`:
  ```
  "Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"
  "Chase Credit Card","","01/05/2025","Amazon","Wants: Shopping","Wants","Shopping","",$50.00,$0.00,"Cleared"
  ```
  and `.env` with `CH_START_BAL=0\nYNAB_START_BAL=0`;
  run `python3 main.py` as a subprocess from the temp directory;
  assert exit code 0; assert at least one directory under `./out/`;
  assert that directory contains `chase.csv`, `ynab.csv`, `both.csv`,
  `merged.csv`, `bal_diff_freq.csv`, and `log.txt`;
  assert `both.csv` has exactly 1 data row;
  assert `log.txt` contains `'AMT OF MATCHED TXNS: 1'`.

- **FR-011**: `tests/test_main.py` MUST contain `test_main_no_env`:
  create a temp directory with valid `./in/chase.csv` and `./in/ynab.csv` but no
  `.env`; run `python3 main.py` as a subprocess; assert non-zero exit code; assert
  stdout or stderr contains `'no .env'`.

### Key Entities

- **Config**: Has `ch_start_bal` and `ynab_start_bal` (replaces `gb_start_bal`).
  No `gb_username` or `gb_password` attributes.
- **main.py pipeline**: read Chase + read YNAB → match → log → print path.
  No argument parsing beyond rejecting unknown args.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python3 -m pytest tests/test_main.py -v` exits code `0` with
  exactly 2 tests collected and passed.

- **SC-002**: `python3 -m pytest` (full suite) exits code `0`.

- **SC-003**: `grep -cE 'add_new_txns|read_gb_txns|gb_txns|gb_start_bal|--add' main.py`
  returns `0`.

- **SC-004**: `grep -cE 'GB_START_BAL|gb_username|gb_password' config.py`
  returns `0`.

- **SC-005**: Running `python3 main.py` from the repo root with valid inputs exits
  0 and prints the output directory path.

## Assumptions

- `read_ynab_txns` is already defined in `file_in.py` (feature 004) and accepts a
  single integer `start_bal` argument, returning an object with `.txns` and
  `.lines_failed`.
- `python-dotenv` (`dotenv_values`) is already installed in the project venv.
- The subprocess in the tests runs `python3 main.py` by absolute path, with `cwd`
  set to the temp directory, so `file_in.py`'s hardcoded relative paths
  (`./in/chase.csv`, `./in/ynab.csv`) resolve against the temp directory.
- `config.py` retains `_str_to_int` — only the env key and attribute name change.
- `main.py` retains its argument-parsing loop skeleton but with the `--add` branch
  removed. If there are no valid args to accept, the loop and usage message can
  be removed entirely, simplifying the file.
- `tests/test_main.py` does not currently exist; it must be created as a new file.
- Tests use `sys.executable` to invoke `python3 main.py` so the correct venv
  interpreter is used.
