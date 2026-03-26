# Feature Specification: Update file_out.py to Use YNAB Types

**Feature Branch**: `006-file-out-ynab`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — file_out.py Uses YNAB Types and Output (Priority: P1)

`file_out.py` currently writes YNAB-unaware output: it references `GoodbudgetTxn`,
`MergedTxn_GoodbudgetTxn`, outputs a file named `goodbudget.csv`, and uses column
headers/type labels with "Goodbudget". This feature updates all of those references
to the YNAB equivalents so that the output files accurately reflect the YNAB data
being processed.

**Why this priority**: The pipeline already processes `YnabTxn` objects from
`match.py`. Without this update, `file_out.py` will raise an `AttributeError`
(`gb_txn.envelope` does not exist on `YnabTxn`) and produce a `goodbudget.csv`
output file that no longer matches the data source. This is the entire deliverable
of the feature.

**Independent Test**: `.venv/bin/python -m pytest tests/test_file_out.py` — both
new tests pass.

**Acceptance Scenarios**:

1. **Given** a `YnabTxn` with known fields and `bal` set, **When** `_ynab_txn_to_row`
   is called, **Then** the returned CSV row uses `txn.category` (not `txn.envelope`)
   and formats `bal` as dollars.

2. **Given** a `MergedTxn_YnabTxn`, **When** `_merged_txn_to_row` is called,
   **Then** the row starts with `'YNAB,'` (not `'GOODBUDGET,'`).

3. **Given** a `Logger` instance, **When** `txns_grouped` is called with a
   `TxnsGrouped` result, **Then** YNAB transactions are written to `ynab.csv`
   (not `goodbudget.csv`).

4. **Given** a `Logger` instance, **When** `amt_matched_and_unmatched` is called,
   **Then** the log contains `'AMT OF UNMATCHED YNAB TXNS'` (not `'GOODBUDGET'`).

---

### User Story 2 — file_out.py Contains No Goodbudget Symbol References (Priority: P1)

`file_out.py` must contain zero references to the banned Goodbudget symbols after
this migration. This is verified as part of the Definition of Done.

**Why this priority**: Any lingering reference would cause a runtime error since
`GoodbudgetTxn` and `MergedTxn_GoodbudgetTxn` are being removed from the pipeline.

**Independent Test**: `grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|_GB_FIELD_NAMES\|_AMT_GB_FIELDS\|gb_file\|gb_txn\|only_gb_txns' file_out.py` returns `0`.

**Acceptance Scenarios**:

1. **Given** the updated `file_out.py`, **When** grepped for any of the banned
   symbols, **Then** zero matches are found.

---

### Edge Cases

- `_merged_txn_to_row` handles three distinct `MergedTxn` subtypes: `MergedTxn_ChaseTxn`
  (Chase-only), `MergedTxn_YnabTxn` (YNAB-only), and the base `MergedTxn` (both).
  The `txn_type` label must be `'YNAB'` for `MergedTxn_YnabTxn` and `'BOTH'` for
  the base case.
- `bal` is stored as integer cents; rows display it as `bal/100` (Python float division).
  `97500` → `975.0`.
- `_MERGED_TXN_FIELD_NAMES` is derived from `_CH_FIELD_NAMES` and `_YNAB_FIELD_NAMES`.
  It must be updated after `_YNAB_FIELD_NAMES` is defined.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `file_out.py` MUST rename the constant `_AMT_GB_FIELDS` to
  `_AMT_YNAB_FIELDS` (value remains `6`).

- **FR-002**: `file_out.py` MUST rename the constant `_GB_FIELD_NAMES` to
  `_YNAB_FIELD_NAMES` with value
  `'YNAB ID,YNAB Date,YNAB Title,YNAB Category,YNAB Txn Amount,YNAB Balance'`.

- **FR-003**: `file_out.py` MUST rename `_gb_txn_to_row` to `_ynab_txn_to_row`;
  the function parameter must be `ynab_txn: YnabTxn` and use `ynab_txn.category`
  instead of `gb_txn.envelope`.

- **FR-004**: In `_merged_txn_to_row`, the type label for a `MergedTxn_YnabTxn`
  MUST be `'YNAB'` (replacing `'GOODBUDGET'`), and calls to `_gb_txn_to_row` MUST
  become calls to `_ynab_txn_to_row`.

- **FR-005**: `Logger.__init__` MUST rename `self.gb_file` to `self.ynab_file`
  and set it to `f'{OUT_DIR}/ynab.csv'` (replacing `goodbudget.csv`).

- **FR-006**: `Logger.amt_matched_and_unmatched` MUST write
  `'AMT OF UNMATCHED YNAB TXNS'` (replacing `'AMT OF UNMATCHED GOODBUDGET TXNS'`),
  and use `txns_grouped.only_ynab_txns` (replacing `txns_grouped.only_gb_txns`).

- **FR-007**: `Logger.txns_grouped` MUST write YNAB transactions to `self.ynab_file`
  using `txns_grouped.only_ynab_txns`, using `_YNAB_FIELD_NAMES` as the header
  and `_ynab_txn_to_row` per row.

- **FR-008**: All `datatypes` imports in `file_out.py` MUST replace
  `GoodbudgetTxn` and `MergedTxn_GoodbudgetTxn` with `YnabTxn` and
  `MergedTxn_YnabTxn`.

- **FR-009**: `tests/test_file_out.py` MUST be created with test
  `test_ynab_txn_to_row`: construct
  `YnabTxn(id_=3, ts=1735689600, date='01/01/2025', title='Trader Joes',
  category='Groceries', amt_dollars='-25.00', cleared='Cleared')`,
  set `txn.bal = 97500`, call `_ynab_txn_to_row(txn)`,
  assert result equals `'3,01/01/2025,Trader Joes,Groceries,-25.00,975.0'`.

- **FR-010**: `tests/test_file_out.py` MUST contain test
  `test_merged_txn_ynab_only_type_label`: construct a `MergedTxn_YnabTxn` wrapping
  the same `YnabTxn` from FR-009, call `_merged_txn_to_row(merged_txn)`,
  assert the result starts with `'YNAB,'`.

### Key Entities

- **YnabTxn**: YNAB transaction. Fields: `id_`, `ts`, `date`, `title`, `category`,
  `amt_dollars`, `amt_cents`, `cleared`, `bal` (default `0`). Replaces
  `GoodbudgetTxn`; `category` replaces `envelope`.
- **MergedTxn_YnabTxn**: Unmatched YNAB-only transaction wrapper. Has `ynab_txn`
  attribute and `bal_diff`. Replaces `MergedTxn_GoodbudgetTxn`.
- **TxnsGrouped**: Return type of `get_txns_grouped`. The attribute `only_ynab_txns`
  replaces `only_gb_txns`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `.venv/bin/python -m pytest tests/test_file_out.py -v` exits code `0`
  with exactly 2 tests collected and passed.

- **SC-002**: `grep -c 'GoodbudgetTxn\|MergedTxn_GoodbudgetTxn\|_GB_FIELD_NAMES\|_AMT_GB_FIELDS\|gb_file\|only_gb_txns' file_out.py`
  returns `0`.

- **SC-003**: `.venv/bin/python -m pytest` (full suite) exits code `0` — no
  existing tests broken.

- **SC-004**: After a pipeline run, the output directory contains `ynab.csv` and
  does not contain `goodbudget.csv`.

- **SC-005**: Rows in `merged.csv` for YNAB-only transactions contain `'YNAB'` in
  the type column (first field).

## Assumptions

- `file_out.py` is the only file modified in this feature. `datatypes.py`, `match.py`,
  `file_in.py`, `graph.py`, `main.py` are untouched.
- `GoodbudgetTxn` and `MergedTxn_GoodbudgetTxn` remain in `datatypes.py` for
  backward compatibility with `graph.py` and `main.py` (deferred cleanup).
- `YnabTxn.bal` initialises to `0`; tests set it manually via `txn.bal = 97500`.
- `_ynab_txn_to_row` returns `bal/100` as a Python float (e.g., `97500/100` → `975.0`).
- `MergedTxn_YnabTxn` has attribute `ynab_txn` (not `gb_txn`). This is the
  attribute used in `_merged_txn_to_row`.
- Tests run via `.venv/bin/python -m pytest` (not system `python3`).
- `tests/test_file_out.py` does not currently exist and must be created as a new file.
- `_ynab_txn_to_row` and `_merged_txn_to_row` are module-level functions; tests
  import them directly from `file_out`.
