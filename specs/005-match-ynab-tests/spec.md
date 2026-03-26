# Feature Specification: Add Tests for match.py YNAB Type Migration

**Feature Branch**: `005-match-ynab-tests`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Matching Algorithm Is Tested Against YNAB Types (Priority: P1)

The matching module (`match.py`) has already been updated to use `YnabTxn` and
`MergedTxn_YnabTxn` in place of `GoodbudgetTxn` and `MergedTxn_GoodbudgetTxn`.
This feature adds three unit tests that verify the matching algorithm works correctly
with those YNAB types, covering the three primary branching outcomes: matched pair,
amount mismatch, and timestamp too far apart.

**Why this priority**: The implementation is already complete but untested. The tests
are the only deliverable; without them there is no confidence the rename was correct.

**Independent Test**: `.venv/bin/python -m pytest tests/test_match.py` — all three
tests pass.

**Acceptance Scenarios**:

1. **Given** a `ChaseTxn` and a `YnabTxn` with identical `amt_cents` and timestamps
   within 7 days of each other, **When** `get_txns_grouped` is called, **Then**
   `result.both_txns` has exactly 1 entry and both unmatched lists are empty.

2. **Given** a `ChaseTxn` and a `YnabTxn` with different `amt_cents`,
   **When** `get_txns_grouped` is called, **Then** each appears only in its own
   unmatched list and `result.both_txns` is empty.

3. **Given** a `ChaseTxn` and a `YnabTxn` with identical `amt_cents` but timestamps
   more than 7 days apart, **When** `get_txns_grouped` is called, **Then**
   `result.both_txns` is empty and each appears in its own unmatched list.

---

### User Story 2 — match.py Contains No Goodbudget Symbol References (Priority: P1)

`match.py` must contain zero references to the six banned Goodbudget symbols:
`GoodbudgetTxn`, `MergedTxn_GoodbudgetTxn`, `gb_txn`, `gb_sorted`, `gb_bal`,
`only_gb_txns`. This is verified as part of the Definition of Done.

**Why this priority**: Any lingering reference would cause a runtime import error
since those symbols are being removed from the pipeline.

**Independent Test**: `grep -c 'GoodbudgetTxn\|gb_txn\|gb_sorted\|gb_bal\|only_gb_txns' match.py`
returns `0`.

**Acceptance Scenarios**:

1. **Given** the current `match.py`, **When** grepped for any of the six banned
   symbols, **Then** zero matches are found.

---

### Edge Cases

- A `ChaseTxn` and `YnabTxn` with identical `amt_cents` and timestamps exactly
  7 days apart — boundary condition for `MAX_DAYS_APART`. Not required for the
  three specified tests; noted for future coverage.
- Empty transaction lists passed to `get_txns_grouped` — must not raise.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tests/test_match.py` MUST be created containing exactly the three
  test functions: `test_match_both_txns`, `test_match_only_ch_and_only_ynab`,
  `test_match_outside_7_days`.

- **FR-002**: `test_match_both_txns` MUST construct a `ChaseTxn` with
  `id_=0, ts=1735689600, date='01/01/2025', title='Amazon', is_debit=True,
  is_pending=False, amt_dollars='-25.00'` and a `YnabTxn` with `id_=0,
  ts=1735689600, date='01/01/2025', title='Amazon', category='Shopping',
  amt_dollars='-25.00', cleared='Cleared'`; call `get_txns_grouped([ch_txn],
  [ynab_txn], 0, 0)`; assert `len(result.both_txns) == 1`,
  `len(result.only_ch_txns) == 0`, `len(result.only_ynab_txns) == 0`.

- **FR-003**: `test_match_only_ch_and_only_ynab` MUST construct a `ChaseTxn` with
  `amt_dollars='-25.00'` and a `YnabTxn` with `amt_dollars='-30.00'`; call
  `get_txns_grouped`; assert `len(result.only_ch_txns) == 1`,
  `len(result.only_ynab_txns) == 1`, `len(result.both_txns) == 0`.

- **FR-004**: `test_match_outside_7_days` MUST construct a `ChaseTxn` with
  `amt_dollars='-25.00', ts=1735689600` (2025-01-01) and a `YnabTxn` with
  `amt_dollars='-25.00', ts=1736380800` (2025-01-09, 8 days later); call
  `get_txns_grouped`; assert `len(result.both_txns) == 0`,
  `len(result.only_ch_txns) == 1`, `len(result.only_ynab_txns) == 1`.

- **FR-005**: `match.py` MUST contain zero references to `GoodbudgetTxn`,
  `MergedTxn_GoodbudgetTxn`, `gb_txn`, `gb_sorted`, `gb_bal`, or `only_gb_txns`.

### Key Entities

- **ChaseTxn**: Existing datatype in `datatypes.py`. Constructed directly in tests.
- **YnabTxn**: Existing datatype (added feature 001). `bal` initialises to `0`;
  no manual override needed.
- **TxnsGrouped**: Return type of `get_txns_grouped`. Attributes: `both_txns`,
  `only_ch_txns`, `only_ynab_txns`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `.venv/bin/python -m pytest tests/test_match.py -v` exits code `0`
  with exactly 3 tests collected and passed.

- **SC-002**: `grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|gb_txn\|gb_sorted\|gb_bal\|only_gb_txns' match.py`
  returns `0`.

- **SC-003**: `.venv/bin/python -m pytest` (full suite) exits code `0` — no existing
  tests broken.

## Assumptions

- `match.py` is already fully updated with all YNAB renames (committed). No source
  changes to `match.py` are required in this feature.
- `YnabTxn.bal` initialises to `0` in the constructor — tests do not set it manually.
- `get_txns_grouped` signature: `(ch_txns, ynab_txns, ch_start_bal, yn_start_bal)`.
  Tests pass `0` for both balance arguments.
- `tests/test_match.py` does not currently exist and must be created as a new file.
- Tests run via `.venv/bin/python -m pytest` (not system `python3`).
