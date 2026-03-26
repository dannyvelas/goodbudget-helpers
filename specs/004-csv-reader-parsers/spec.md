# Feature Specification: Replace Regex Parsers with csv.reader

**Feature Branch**: `004-csv-reader-parsers`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Chase CSV Is Parsed Using csv.reader (Priority: P1)

The organizing module must read Chase transaction files using Python's `csv.reader`
instead of a hand-written regex. The behavior visible to callers — the `ReadResults`
structure, `amt_cents`, `is_debit`, `is_pending`, `title`, and `lines_failed` — must
be identical to the current regex-based implementation.

**Why this priority**: The Chase parser is already in use. Replacing its internals
while preserving its contract is the safest first step.

**Independent Test**: Call `read_ch_txns` with a temp file containing a header, a sale
row, and a payment row. Verify two `ChaseTxn` objects are returned, `lines_failed` is
empty, and amounts and flags are correct.

**Acceptance Scenarios**:

1. **Given** a Chase CSV with one sale row (Amount < 0),
   **When** `read_ch_txns` is called, **Then** the resulting `ChaseTxn` has
   `is_debit=True`, a negative `amt_cents`, and `is_pending=False`.

2. **Given** a Chase CSV with one payment row (Amount > 0),
   **When** `read_ch_txns` is called, **Then** the resulting `ChaseTxn` has
   `is_debit=False` and a positive `amt_cents`.

3. **Given** a Chase CSV whose first line is the header row,
   **When** `read_ch_txns` is called, **Then** the header does not appear in
   `lines_failed` and exactly the data rows are returned.

4. **Given** a Chase CSV row with a wrong column count (e.g., only 3 columns),
   **When** `read_ch_txns` is called, **Then** that row appears in `lines_failed`.

---

### User Story 2 — YNAB CSV Is Parsed Using csv.reader (Priority: P1)

The organizing module must read YNAB export files using `csv.reader`. This is a new
function (`read_ynab_txns`) that produces `YnabTxn` objects. Using `csv.reader`
correctly handles quoted payee names that contain commas (e.g., `"Smith, John"`),
which the previous regex approach could not.

**Why this priority**: This is the core YNAB data ingestion path. It is P1 alongside
US1 because neither story depends on the other and both are required for the pipeline
to work end-to-end.

**Independent Test**: Call `read_ynab_txns` with a temp file containing a header, one
expense row, and one income row. Verify two `YnabTxn` objects are returned,
`lines_failed` is empty, and `amt_cents`, `category`, and `cleared` are correct.

**Acceptance Scenarios**:

1. **Given** a YNAB CSV with one expense row (Outflow > 0, Inflow = 0),
   **When** `read_ynab_txns` is called, **Then** the resulting `YnabTxn` has a
   negative `amt_cents` and the correct `category` and `cleared` values.

2. **Given** a YNAB CSV with one income row (Outflow = 0, Inflow > 0),
   **When** `read_ynab_txns` is called, **Then** the resulting `YnabTxn` has a
   positive `amt_cents`.

3. **Given** a YNAB CSV whose first line is the header row,
   **When** `read_ynab_txns` is called, **Then** the header does not appear in
   `lines_failed` and exactly the data rows are returned.

4. **Given** a YNAB CSV row with a wrong column count,
   **When** `read_ynab_txns` is called, **Then** that row appears in `lines_failed`.

5. **Given** a YNAB CSV file beginning with a UTF-8 BOM,
   **When** `read_ynab_txns` is called, **Then** the BOM is silently stripped and all
   rows parse correctly.

6. **Given** a YNAB CSV with a payee value that contains a comma (e.g.,
   `"Smith, John"`), **When** `read_ynab_txns` is called, **Then** the full payee
   string (comma included) is captured correctly and the row does not appear in
   `lines_failed`.

---

### User Story 3 — Remove Obsolete Regex Symbols and Dead Code (Priority: P2)

`CH_REGEX`, `GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`, `read_gb_txns`, and `IN_GB_FILE`
are removed. `IN_YNAB_FILE` is added pointing to `./in/ynab.csv`. The `TypeVar` in
`file_in.py` is updated from `GoodbudgetTxn` to `YnabTxn`. If `regex.py` becomes
empty after removals, it is left with only `import re`.

**Why this priority**: Dead code cleanup follows working implementation. The parsers
must be correct before the old symbols are removed.

**Independent Test**: Grep `regex.py` and `file_in.py` for the old symbols and verify
zero matches.

**Acceptance Scenarios**:

1. **Given** the updated `regex.py`, **When** grepped for `CH_REGEX`, `GB_EXPENSE_REGEX`,
   or `GB_INCOME_REGEX`, **Then** zero matches are found.

2. **Given** the updated `file_in.py`, **When** grepped for `read_gb_txns`,
   `IN_GB_FILE`, `CH_REGEX`, `GB_EXPENSE_REGEX`, or `GB_INCOME_REGEX`,
   **Then** zero matches are found.

---

### Edge Cases

- A Chase Description containing a comma (e.g., `"SMITH, JOHN"`) — `csv.reader`
  handles RFC-4180 quoting; the full value must be captured as one field.
- A YNAB Payee containing a comma — same as above.
- A Chase row where Amount is `0.00` — `is_debit` must be `False`.
- Both YNAB Outflow and Inflow are `$0.00` — `amt_dollars` must be `"0.00"`.
- A YNAB file with UTF-8 BOM — `encoding='utf-8-sig'` strips it transparently.
- A row with the wrong number of columns — must appear in `lines_failed` as a
  comma-joined string of its parsed fields (or the raw line if parsing fails entirely).
- The header row (index 0) — must never appear in `lines_failed` regardless of content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `read_ch_txns` in `file_in.py` MUST use `csv.reader` to parse Chase CSV
  rows instead of `CH_REGEX`.

- **FR-002**: `read_ch_txns` MUST skip line index 0 (header) explicitly without adding
  it to `lines_failed`.

- **FR-003**: `read_ch_txns` MUST treat a row as valid if and only if it has exactly 7
  columns and column 5 (Amount) parses as a float. Invalid rows go to `lines_failed`.

- **FR-004**: `read_ch_txns` MUST set `is_debit=True` when Amount < 0,
  `is_debit=False` otherwise; `is_pending=False` for all rows; `_shorten` applied to
  column 2 (Description) for `title`.

- **FR-005**: `read_ynab_txns` in `file_in.py` MUST use `csv.reader` opened with
  `encoding='utf-8-sig'` to parse YNAB CSV rows.

- **FR-006**: `read_ynab_txns` MUST skip line index 0 (header) explicitly without
  adding it to `lines_failed`.

- **FR-007**: `read_ynab_txns` MUST treat a row as valid if and only if it has exactly
  11 columns and columns 8 (Outflow) and 9 (Inflow) parse as floats after stripping `$`.
  Invalid rows go to `lines_failed`.

- **FR-008**: `read_ynab_txns` MUST derive `amt_dollars` from Outflow and Inflow:
  if `outflow > 0.0` then `amt_dollars = f"-{outflow_str}"`; if `inflow > 0.0` then
  `amt_dollars = inflow_str`; otherwise `amt_dollars = "0.00"`. `outflow_str` and
  `inflow_str` are the Outflow/Inflow values with `$` stripped.

- **FR-009**: `read_ynab_txns` MUST apply `_shorten` to column 3 (Payee) for `title`
  and use column 6 (Category) for `category` and column 10 (Cleared) for `cleared`.

- **FR-010**: The constant `IN_YNAB_FILE` MUST be added to `file_in.py` pointing to
  `'./in/ynab.csv'`.

- **FR-011**: `file_in.py` MUST have zero references to `CH_REGEX`, `GB_EXPENSE_REGEX`,
  `GB_INCOME_REGEX`, `read_gb_txns`, or `IN_GB_FILE` after this change.

- **FR-012**: `regex.py` MUST have zero references to `CH_REGEX`, `GB_EXPENSE_REGEX`,
  or `GB_INCOME_REGEX` after this change.

- **FR-013**: Eight unit tests MUST be added to `tests/test_file_in.py` replacing the
  existing regex-pattern tests. The four existing `test_ch_regex_*` tests MUST be
  removed (since `CH_REGEX` will no longer exist). All eight new tests MUST pass under
  `.venv/bin/python -m pytest tests/test_file_in.py`.

- **FR-014**: The running balance calculations using `ch_start_bal` and `ynab_start_bal`
  MUST be unchanged from their prior implementations.

### Key Entities

- **ChaseTxn**: Unchanged. Fields set by `read_ch_txns`: `id_`, `ts`, `date`, `title`,
  `amt_dollars`, `is_debit`, `is_pending=False`. `bal` set by running balance pass.
- **YnabTxn**: Defined in `datatypes.py` (feature 001). Fields set by `read_ynab_txns`:
  `id_`, `ts`, `date`, `title`, `category`, `amt_dollars`, `cleared`. `bal` set by
  running balance pass.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `.venv/bin/python -m pytest tests/test_file_in.py` exits with code `0`
  and all 8 new tests pass.

- **SC-002**: `grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py`
  returns `0`.

- **SC-003**: `grep -c 'CH_REGEX\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|read_gb_txns\|IN_GB_FILE' file_in.py`
  returns `0`.

- **SC-004**: `grep -c 'import csv' file_in.py` returns `1`.

- **SC-005**: Calling `read_ch_txns` on a two-row (plus header) Chase CSV returns
  exactly 2 transactions and 0 `lines_failed`.

- **SC-006**: Calling `read_ynab_txns` on a two-row (plus header) YNAB CSV returns
  exactly 2 transactions and 0 `lines_failed`.

## Assumptions

- `datatypes.py` already exports `YnabTxn` (completed in feature 001). `read_ynab_txns`
  imports and constructs `YnabTxn` directly.
- `graph.py` imports `read_gb_txns` from `file_in` — removing it will break `graph.py`.
  This is acknowledged; updating `graph.py` is out of scope and deferred to a follow-up.
- The `TypeVar` in `file_in.py` currently references `GoodbudgetTxn` — updating it to
  `YnabTxn` is in scope as a mechanical type-annotation fix with no behavioral impact.
- `lines_failed` entries for invalid csv rows are stored as comma-joined strings of
  the parsed column values (e.g., `','.join(row)`).
- `_dollars_to_cents` already strips `$` (updated in feature 001), so stripping `$`
  before constructing `amt_dollars` in the parser is the correct place to do it.
- The existing `test_ch_regex_*` tests in `tests/test_file_in.py` will be removed as
  part of this feature since `CH_REGEX` will no longer exist. Their coverage is replaced
  by the new reader-based tests.
