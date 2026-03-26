# Research: Update main.py and config.py to Use YNAB Types

**Branch**: `007-main-config-ynab` | **Date**: 2026-03-26

## Summary

No open questions. All decisions are deterministic from the existing codebase
and the feature specification. Key questions below are resolved by inspection.

## Decisions

### D-001: Use `sys.executable` in subprocess tests (not bare `python3`)

**Decision**: `subprocess.run([sys.executable, str(MAIN_PY)], ...)` in both tests.
**Rationale**: `sys.executable` resolves to the venv Python that pytest is running
under (`.venv/bin/python`). Using bare `python3` would invoke the system Python,
which lacks `python-dotenv` and the project's test dependencies — causing an
`ImportError` in the subprocess. `sys.executable` guarantees the correct
interpreter.
**Alternatives considered**: `['python3', ...]` — rejected; relies on `python3`
resolving to the same Python that has `dotenv` installed, which is not guaranteed.

### D-002: Compute `MAIN_PY` path from `__file__`

**Decision**: `MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'`
**Rationale**: `__file__` is `tests/test_main.py`; `.parent.parent` is the repo
root where `main.py` lives. This is robust regardless of the working directory
pytest is invoked from.
**Alternatives considered**: Hardcoded string `'main.py'` — rejected; fragile
when pytest is run from a different directory.

### D-003: Remove the entire `sys.argv` parsing block from `main.py`

**Decision**: Delete the `import sys` and the `while i < len(sys.argv)` loop.
**Rationale**: The only flag that existed was `--add`, which is being removed.
With no valid flags, the loop adds no value. Removing it is simpler (Principle V).
**Alternatives considered**: Retain the loop with only the `else` branch — rejected;
a loop that unconditionally errors on any arg is confusing and unnecessary.

### D-004: `add_new_txns.py` does not import `Config`

**Decision**: Removing `gb_username`/`gb_password` from `Config` is safe for
out-of-scope modules.
**Rationale**: `add_new_txns.py` receives credentials as positional arguments
from `main.py`. It never does `from config import Config`. Confirmed by how
`main.py` calls it: `add_new_txns(txns_grouped, ENVELOPES, config.gb_username,
config.gb_password, last_gb_txn_ts)`. The function signature accepts plain
strings, not a `Config` object. `import add_new_txns` will succeed after our
changes.
**Alternatives considered**: Retaining stub attributes on `Config` — rejected;
unnecessary backward-compat shim for a module that already receives the values
as args.

### D-005: Error message wording satisfies FR-009 unchanged

**Decision**: Keep the existing error string `"Error, no .env file found."`.
**Rationale**: The test checks
`'no .env' in (result.stdout + result.stderr).lower()`. The existing message
lowercased contains `'no .env file found.'` which includes `'no .env'`. No change
needed.
**Alternatives considered**: Changing to `"Error: no .env file found"` — rejected;
unnecessary change, existing text satisfies the requirement.

### D-006: `tempfile.TemporaryDirectory` for subprocess integration tests

**Decision**: Use `tempfile.TemporaryDirectory()` as a context manager.
**Rationale**: Automatically cleans up after the test, even on failure. Requires
no teardown logic. Standard Python stdlib approach.
**Alternatives considered**: `pytest` `tmp_path` fixture — valid, but using stdlib
`tempfile` keeps the test self-contained without pytest fixtures.

## No NEEDS CLARIFICATION Items

All technical choices are deterministic. Phase 0 research is complete.
