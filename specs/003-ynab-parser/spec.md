# Feature Specification: Replace Goodbudget Parser with YNAB Parser

**Feature Branch**: `003-ynab-parser`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — YNAB Export CSV Is Parsed into YnabTxn Objects (Priority: P1)

The organizing module must read a YNAB export CSV file and produce a list of `YnabTxn`
objects. The YNAB export uses a quoted 11-column format with a header row and may begin with
a UTF-8 BOM character. Each data row carries a date, payee, category, outflow, inflow, and
cleared status. The parser must derive a single signed amount from the separate Outflow and
Inflow columns and pass it to `YnabTxn`.

**Why this priority**: This is the core data ingestion path for the organizing module. Without
it, no YNAB transactions can enter the pipeline.

**Independent Test**: Call `read_ynab_txns` directly with a temp file containing a header and
two data rows. Verify two `YnabTxn` objects are returned, `lines_failed` is empty, and the
fields (amount, category, cleared) are set correctly.

**Acceptance Scenarios**:

1. **Given** a YNAB CSV with one expense row (Outflow > 0, Inflow = 0),
   **When** `read_ynab_txns` is called, **Then** the resulting `YnabTxn` has a negative
   `amt_cents` and the correct `category` and `cleared` values.

2. **Given** a YNAB CSV with one income row (Outflow = 0, Inflow > 0),
   **When** `read_ynab_txns` is called, **Then** the resulting `YnabTxn` has a positive
   `amt_cents`.

3. **Given** a YNAB CSV whose first line is the header row,
   **When** `read_ynab_txns` is called, **Then** the header does not appear in `lines_failed`
   and exactly the data rows are returned as transactions.

4. **Given** a YNAB CSV file beginning with a UTF-8 BOM,
   **When** `read_ynab_txns` is called, **Then** the BOM is silently stripped and all rows
   parse correctly.

---

### User Story 2 — YNAB Regex Correctly Matches the Export Format (Priority: P1)

A single `YNAB_REGEX` in `regex.py` replaces the two Goodbudget regexes. It must capture
the fields needed by the parser (date, payee, category, outflow, inflow, cleared) and must
not match the header row.

**Why this priority**: The regex is the boundary between raw CSV text and structured data.
An incorrect regex silently drops rows or captures wrong values.

**Independent Test**: Apply `YNAB_REGEX` to known-good data rows and the header row directly.
Verify named group values and header non-match.

**Acceptance Scenarios**:

1. **Given** a YNAB CSV data row with an outflow amount, **When** `YNAB_REGEX.match` is
   applied, **Then** groups `date`, `payee`, `category`, `outflow`, `inflow`, `cleared` are
   all captured with correct values.

2. **Given** a YNAB CSV data row with an inflow amount, **When** `YNAB_REGEX.match` is
   applied, **Then** `outflow='0.00'` and `inflow` contains the payment amount.

3. **Given** the YNAB header row, **When** `YNAB_REGEX.match` is applied, **Then** the
   result is `None`.

---

### User Story 3 — Old Goodbudget Symbols Are Removed from `regex.py` and `file_in.py` (Priority: P2)

`GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`, `read_gb_txns`, and `IN_GB_FILE` are removed. The
input file constant is renamed to `IN_YNAB_FILE` pointing to `./in/ynab.csv`.

**Why this priority**: Removing dead code keeps the codebase consistent with the constitution
and prevents future confusion. It is lower priority than the working parser but is part of the
same migration.

**Independent Test**: Grep `regex.py` and `file_in.py` for the old symbols and verify zero
matches.

**Acceptance Scenarios**:

1. **Given** the updated `regex.py`, **When** it is grepped for `GB_EXPENSE_REGEX` or
   `GB_INCOME_REGEX`, **Then** zero matches are found.

2. **Given** the updated `file_in.py`, **When** it is grepped for `read_gb_txns`,
   `GB_EXPENSE_REGEX`, `GB_INCOME_REGEX`, or `IN_GB_FILE`, **Then** zero matches are found.

---

### Edge Cases

- A row where Payee contains special characters or spaces — `_shorten` normalization must
  still be applied.
- Both Outflow and Inflow are `$0.00` — `amt_dollars` must be `"0.00"`.
- The header row starts with a quoted word `"Account"` (not a date) — the regex must not
  match it; the parser must skip it explicitly so it never reaches `lines_failed`.
- A file with a UTF-8 BOM (`\ufeff`) at byte 0 — opening with `encoding='utf-8-sig'`
  strips it before any parsing.
- Malformed rows (not matching `YNAB_REGEX`) must still be added to `lines_failed`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `YNAB_REGEX` in `regex.py` MUST match YNAB CSV data rows and capture named
  groups: `date` (Date column), `payee` (Payee), `category` (Category — 7th column),
  `outflow` (Outflow, dollar value after stripping `$`), `inflow` (Inflow, after stripping
  `$`), `cleared` (Cleared).

- **FR-002**: `YNAB_REGEX` MUST NOT match the YNAB header row.

- **FR-003**: `read_ynab_txns` in `file_in.py` MUST skip the first line (header) explicitly
  without adding it to `lines_failed`.

- **FR-004**: `read_ynab_txns` MUST derive `amt_dollars` from Outflow and Inflow:
  if `outflow > 0.0` then `amt_dollars = f"-{outflow_str}"`;
  if `inflow > 0.0` then `amt_dollars = inflow_str`;
  otherwise `amt_dollars = "0.00"`.

- **FR-005**: `read_ynab_txns` MUST apply `_shorten` to the Payee value when setting
  `YnabTxn.title`.

- **FR-006**: `read_ynab_txns` MUST open `IN_YNAB_FILE` with `encoding='utf-8-sig'` to
  handle optional UTF-8 BOM.

- **FR-007**: The input file constant `IN_YNAB_FILE` MUST point to `./in/ynab.csv`.

- **FR-008**: The running balance calculation using `ynab_start_bal` MUST be unchanged from
  the prior implementation.

- **FR-009**: `regex.py` MUST have zero references to `GB_EXPENSE_REGEX` or
  `GB_INCOME_REGEX` after this change.

- **FR-010**: `file_in.py` MUST have zero references to `read_gb_txns`, `GB_EXPENSE_REGEX`,
  `GB_INCOME_REGEX`, or `IN_GB_FILE` after this change.

- **FR-011**: Four unit tests MUST be added to `tests/test_file_in.py` covering: outflow
  regex match, inflow regex match, header no-match, and a full `read_ynab_txns` integration
  test. All four MUST pass under `python3 -m pytest tests/test_file_in.py`.

### Key Entities

- **YnabTxn**: Unchanged data class (defined in `datatypes.py`). Fields set by
  `read_ynab_txns`: `id_`, `ts`, `date`, `title` (from Payee via `_shorten`), `category`,
  `amt_dollars` (signed, derived from Outflow/Inflow), `cleared`. `bal` initialized to `0`
  and set by the running balance pass.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python3 -m pytest tests/test_file_in.py` exits with code `0` and all four new
  tests pass (in addition to the four existing Chase tests).

- **SC-002**: `grep -c 'GB_EXPENSE_REGEX\|GB_INCOME_REGEX' regex.py` returns `0`.

- **SC-003**: `grep -c 'read_gb_txns\|GB_EXPENSE_REGEX\|GB_INCOME_REGEX\|IN_GB_FILE' file_in.py`
  returns `0`.

- **SC-004**: `YNAB_REGEX.match('"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"')`
  returns a match with `outflow='3.00'`, `inflow='0.00'`, `cleared='Uncleared'`.

## Assumptions

- `datatypes.py` already exports `YnabTxn` (completed in feature 001). `read_ynab_txns`
  imports and constructs `YnabTxn` directly.
- `graph.py` imports `read_gb_txns` from `file_in` — removing `read_gb_txns` will break
  `graph.py`. This is acknowledged; updating `graph.py` is out of scope for this feature and
  will be addressed in a follow-up.
- `add_new_txns.py` does not import `read_gb_txns` directly, so it is unaffected.
- The `TypeVar` in `file_in.py` currently references `GoodbudgetTxn` — updating it to
  `YnabTxn` is in scope as a mechanical type-annotation fix with no behavioral impact.
- All YNAB CSV fields are quoted; the regex uses quoted-field patterns throughout.
- The `_shorten` function is reused unchanged.
