# Implementation Plan: Update main.py and config.py to Use YNAB Types

**Branch**: `007-main-config-ynab` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/007-main-config-ynab/spec.md`

## Summary

`main.py` still calls `read_gb_txns` (removed in feature 004) and passes
`config.gb_start_bal` (not yet renamed in `config.py`) — both cause `AttributeError`
or `ImportError` at runtime. This feature:
1. Rewrites `config.py` to expose `ynab_start_bal` instead of `gb_start_bal` and
   drops `gb_username`/`gb_password`.
2. Rewrites `main.py` to use `read_ynab_txns`, removing the `--add` flag, the
   `add_new_txns` call, and the pending-amounts block.
3. Adds `tests/test_main.py` with two subprocess-based integration tests.

After this feature the pipeline compiles and runs end-to-end: read → match → log →
print path.

## Technical Context

**Language/Version**: Python 3.14.3 (system), venv at `.venv/`
**Primary Dependencies**: `python-dotenv` (`dotenv_values`), `pytest 9.0.2`
**Storage**: Input: `./in/chase.csv`, `./in/ynab.csv`; Output: `./out/<timestamp>/`
**Testing**: pytest via `.venv/bin/python -m pytest`; subprocess integration tests
**Target Platform**: macOS / local CLI
**Project Type**: CLI data pipeline entrypoint
**Performance Goals**: N/A
**Constraints**: N/A
**Scale/Scope**: 2 modified files (`main.py`, `config.py`), 1 new file (`tests/test_main.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Importable Core | ✅ PASS | `main.py` is orchestration-only; changes to `config.py` do not affect importability of `file_in`, `match`, or `file_out` |
| II. Cents-Only Monetary Arithmetic | ✅ PASS | `YNAB_START_BAL` parsed by `_str_to_int` → integer cents; no float arithmetic |
| III. Pytest-First Testing | ✅ PASS | Two integration tests in `tests/test_main.py`; written before implementation |
| IV. Scope Isolation | ⚠️ VERIFY | Removing `gb_username`/`gb_password` from `Config` could break `add_new_txns.py` if it imports from `config`. Must run `python3 -c "import graph; import add_new_txns"` after changes and confirm no errors. Research phase confirms `add_new_txns.py` receives credentials as function args — does not import `Config` directly. |
| V. Simplicity | ✅ PASS | Net deletion of ~35 lines; no new abstractions; arg-parsing block removed entirely |

## Project Structure

### Documentation (this feature)

```text
specs/007-main-config-ynab/
├── plan.md          # This file
├── spec.md          # Feature specification
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md         # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
main.py              # MODIFIED — YNAB types, no --add, no add_new_txns
config.py            # MODIFIED — ynab_start_bal, no gb_username/gb_password
tests/
└── test_main.py     # NEW — 2 subprocess integration tests
```

**Structure Decision**: Two modified source files + one new test file. No new
modules, no new directories.

## Implementation Notes

### config.py changes

Remove `gb_start_bal` assignment; replace with:
```python
ynab_start_bal = env["YNAB_START_BAL"] if "YNAB_START_BAL" in env and env["YNAB_START_BAL"] is not None else ""
self.ynab_start_bal = _str_to_int(ynab_start_bal)
```
Remove the `GB_USERNAME` and `GB_PASSWORD` blocks entirely.

### main.py changes

**Before** (relevant sections):
```python
import sys
from add_new_txns import add_new_txns
from file_in import read_ch_txns, read_gb_txns
...
# parse cmd-line args (--add flag)
# read gb_txns
# get_txns_grouped(..., gb_txns, ..., config.gb_start_bal)
# if add_txns: ...add_new_txns..., pending amounts block
```

**After** (complete new main.py):
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

The `sys` import, `--add` parsing loop, `add_new_txns` import, and pending-amounts
block are all removed. No `import sys` needed.

### test_main.py subprocess pattern

```python
import os, subprocess, sys, tempfile
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'

def test_main_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'in').mkdir()
        # write chase.csv, ynab.csv, .env
        result = subprocess.run(
            [sys.executable, str(MAIN_PY)],
            cwd=tmpdir, capture_output=True, text=True)
        assert result.returncode == 0
        # verify out/ directory and files
        ...

def test_main_no_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / 'in').mkdir()
        # write chase.csv, ynab.csv — no .env
        result = subprocess.run(
            [sys.executable, str(MAIN_PY)],
            cwd=tmpdir, capture_output=True, text=True)
        assert result.returncode != 0
        assert 'no .env' in (result.stdout + result.stderr).lower()
```

`sys.executable` ensures the venv Python runs `main.py`, giving access to
`python-dotenv` and all project modules.

### Error message update

Current `main.py` prints: `"Error, no .env file found."` — this contains the
substring `no .env` (case-insensitive). The test checks
`'no .env' in (result.stdout + result.stderr).lower()` so the current wording
satisfies FR-009 without any change.

### Scope isolation verification

After modifying `config.py`, run:
```bash
python3 -c "import graph; import add_new_txns"
```
`add_new_txns.py` receives `gb_username` and `gb_password` as positional arguments
(confirmed by how `main.py` calls it: `add_new_txns(txns_grouped, ENVELOPES,
config.gb_username, config.gb_password, last_gb_txn_ts)`). It does not import
`Config` itself — removing the attributes from `Config` does not break its import.
`graph.py` likely imports `file_in` or `datatypes` but not `config`. Both should
import cleanly.
