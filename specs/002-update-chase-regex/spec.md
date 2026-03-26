# Feature Specification: Update Chase CSV Parser for New Export Format

**Feature Branch**: `002-update-chase-regex`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — New Chase CSV Format Is Parsed Correctly (Priority: P1)

The organizing module must be able to read transaction files exported from Chase in the
current format. The new format is a seven-column CSV with a header row; it no longer includes
a DEBIT/CREDIT prefix or a balance column. A user who downloads their Chase transaction history
today and places it in `./in/chase.csv` must be able to run the organizing module and have all
transactions parsed successfully.

**Why this priority**: Without this fix the module fails to parse any Chase transactions at all,
rendering the entire organizing pipeline unusable.

**Independent Test**: Provide a sample Chase CSV file in the new format and run the organizing
module (or call `read_ch_txns` directly). All data rows parse successfully; the header row does
not appear in `lines_failed`; parsed transactions have correct amounts and debit/credit flags.

**Acceptance Scenarios**:

1. **Given** a Chase CSV file in the new format with one sale and one payment row,
   **When** `read_ch_txns` is called, **Then** two `ChaseTxn` objects are returned, the sale
   has `is_debit=True` and a negative `amt_cents`, the payment has `is_debit=False` and a
   positive `amt_cents`, and `lines_failed` is empty.

2. **Given** a Chase CSV file whose first line is the header
   `Transaction Date,Post Date,Description,Category,Type,Amount,Memo`,
   **When** `read_ch_txns` is called, **Then** the header does not appear in `lines_failed`.

3. **Given** a Chase CSV row in the new format, **When** `CH_REGEX` is applied,
   **Then** the named groups `date`, `description`, and `amt` are captured correctly.

4. **Given** the old Chase CSV header line `DEBIT,01/01/2025,...`,
   **When** `CH_REGEX` is applied, **Then** it does not match (old format is no longer
   supported).

---

### User Story 2 — All Transactions Have `is_pending=False` (Priority: P1)

Because the new Chase format does not include a balance column, the pending-status heuristic
(blank balance → pending) no longer applies. Every transaction parsed from the new format must
have `is_pending=False`. The bot-adding feature that consumed `is_pending` is out of scope and
does not need to be updated.

**Why this priority**: Incorrect `is_pending` values could silently filter transactions in
downstream code. Setting it unconditionally to `False` is the safe and correct default for the
new format.

**Independent Test**: Parse a Chase CSV file in the new format and inspect `is_pending` on
every returned `ChaseTxn`. All must be `False`.

**Acceptance Scenarios**:

1. **Given** a Chase CSV file in the new format, **When** `read_ch_txns` is called,
   **Then** every `ChaseTxn` in the result has `is_pending == False`.

---

### Edge Cases

- A row where Description contains a comma (e.g., `"SMITH, JOHN"`) — the Description field
  may be quoted; the regex must handle quoted descriptions.
- A row where Amount is positive (income/payment) — `is_debit` must be `False`.
- A row where Amount is `0.00` — `is_debit` must be `False`.
- The header row must not appear in `lines_failed` regardless of its content.
- Blank or malformed rows (not matching the regex) must still be added to `lines_failed` as
  before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `CH_REGEX` in `regex.py` MUST match the new Chase CSV format:
  `Transaction Date,Post Date,Description,Category,Type,Amount,Memo` with named groups
  `date` (Transaction Date), `description` (Description), and `amt` (Amount).

- **FR-002**: `CH_REGEX` MUST NOT match the header row
  `Transaction Date,Post Date,Description,Category,Type,Amount,Memo`.

- **FR-003**: `read_ch_txns` in `file_in.py` MUST skip the first line (header) explicitly
  without adding it to `lines_failed`.

- **FR-004**: `read_ch_txns` MUST set `is_debit=True` when `amt < 0`, `is_debit=False`
  otherwise.

- **FR-005**: `read_ch_txns` MUST set `is_pending=False` for every transaction parsed from
  the new format.

- **FR-006**: The `_shorten` normalization MUST still be applied to the Description field
  when constructing the `title` of a `ChaseTxn`.

- **FR-007**: The running balance calculation using `ch_start_bal` MUST remain unchanged.

- **FR-008**: The input file path `./in/chase.csv` MUST remain unchanged.

- **FR-009**: Four unit tests MUST be added to `tests/test_file_in.py` covering: sale regex
  match, payment regex match, header no-match, and a full `read_ch_txns` integration test.
  All four MUST pass under `python3 -m pytest tests/test_file_in.py`.

### Key Entities

- **ChaseTxn**: Unchanged data class. The `is_pending` field is now always `False` for the
  new format; `is_debit` is derived from the sign of `amt`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python3 -m pytest tests/test_file_in.py` exits with code `0` and all four
  specified tests pass with zero failures.

- **SC-002**: `CH_REGEX.match('Transaction Date,Post Date,Description,Category,Type,Amount,Memo')`
  returns `None`.

- **SC-003**: `CH_REGEX.match('03/24/2026,03/25/2026,HEADWAY,Health & Wellness,Sale,-15.00,')`
  returns a match with `date='03/24/2026'`, `description='HEADWAY'`, `amt='-15.00'`.

- **SC-004**: Calling `read_ch_txns` on a two-row (plus header) Chase CSV in the new format
  returns exactly 2 transactions and 0 `lines_failed`.

## Assumptions

- Only `regex.py` (`CH_REGEX`) and `file_in.py` (`read_ch_txns`) are modified in this feature.
  `datatypes.py`, `match.py`, `file_out.py`, `config.py`, and `main.py` are not touched.
- The old Chase CSV format is fully retired; `CH_REGEX` need not remain backward-compatible
  with the old DEBIT/CREDIT prefix format.
- `is_pending` is set to `False` for all new-format transactions; the bot-adding module
  (`add_new_txns.py`) is out of scope and does not need to be updated.
- The Description field in the new Chase CSV may be optionally quoted; the regex handles both
  quoted and unquoted descriptions.
- `_shorten` is applied to Description the same way it was previously applied to title.
- The existing `GoodbudgetTxn`/YNAB migration (feature 001) is in a parallel branch; this
  feature targets only Chase-side parsing and does not depend on that migration.
