# Feature Specification: YNAB Datatype Migration — Replace GoodbudgetTxn with YnabTxn

**Feature Branch**: `001-ynab-datatype-migration`
**Created**: 2026-03-26
**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 — YNAB Transactions Are Representable in the Organizing Module (Priority: P1)

The organizing module must be able to represent a YNAB transaction as a first-class data type.
A YNAB transaction carries a date, payee name (title), category, signed monetary amount, and
cleared status. The old `GoodbudgetTxn` type is retired and replaced by `YnabTxn` throughout
`datatypes.py`.

**Why this priority**: Every downstream operation in the organizing module (matching, grouping,
output) depends on a correct transaction type. Without this, no YNAB data can flow through
the pipeline.

**Independent Test**: Import `YnabTxn` directly from `datatypes` and construct an instance.
Verify all fields are set correctly and `amt_cents` is derived from `amt_dollars`.

**Acceptance Scenarios**:

1. **Given** an expense transaction with `amt_dollars="-25.00"`, **When** a `YnabTxn` is
   constructed, **Then** `amt_cents` is `-2500`, `bal` is `0`, and all other fields match the
   constructor arguments.

2. **Given** an income/payment transaction with `amt_dollars="500.00"`, **When** a `YnabTxn`
   is constructed, **Then** `amt_cents` is `50000`.

3. **Given** the `datatypes` module is imported, **When** it is inspected, **Then** no symbol
   named `GoodbudgetTxn` or `MergedTxn_GoodbudgetTxn` exists.

---

### User Story 2 — Dollar-Sign Monetary Strings Are Correctly Converted to Cents (Priority: P1)

YNAB's CSV export uses dollar signs in monetary columns (e.g., `$3.00`). The cents converter
must accept and strip the `$` character so YNAB values are parsed correctly. The converter must
also continue to handle signed strings without a dollar sign (e.g., `"-25.00"`).

**Why this priority**: Incorrect parsing of monetary values would silently corrupt balance
reconciliation — the core purpose of the organizing module.

**Independent Test**: Call `_dollars_to_cents` directly from `datatypes` with both `$`-prefixed
and plain signed strings and assert the integer result.

**Acceptance Scenarios**:

1. **Given** the input `'$3.00'`, **When** `_dollars_to_cents` is called, **Then** the result
   is `300`.

2. **Given** the input `'-25.00'`, **When** `_dollars_to_cents` is called, **Then** the result
   is `-2500`.

---

### User Story 3 — Grouping and Merged-Transaction Types Reference YNAB (Priority: P2)

All composite types in `datatypes.py` that previously referenced `GoodbudgetTxn` must be
updated to reference `YnabTxn`. This includes the merged-transaction wrapper types and the
grouped-transaction container. Field names must reflect the new source system.

**Why this priority**: Downstream features (matching, output) depend on these types being
internally consistent before they are updated.

**Independent Test**: Construct `MergedTxn_YnabTxn`, `MergedTxn_BothTxns`, and `TxnsGrouped`
directly from `datatypes` using `YnabTxn` instances. Verify attribute access uses the new field
names (`ynab_txn`, `only_ynab_txns`).

**Acceptance Scenarios**:

1. **Given** a `YnabTxn` instance, **When** `MergedTxn_YnabTxn` is constructed with it,
   **Then** `merged.ynab_txn` holds a copy and `merged.bal_diff` is `0`.

2. **Given** a `ChaseTxn` and a `YnabTxn`, **When** `MergedTxn_BothTxns` is constructed,
   **Then** `merged.ch_txn` and `merged.ynab_txn` hold copies and `merged.bal_diff` is `0`.

3. **Given** grouped transaction lists, **When** `TxnsGrouped` is constructed, **Then**
   `grouped.only_ynab_txns` holds the YNAB-only list.

---

### Edge Cases

- `_dollars_to_cents('$0.00')` must return `0`.
- No references to `GoodbudgetTxn` or `MergedTxn_GoodbudgetTxn` may remain in `datatypes.py`
  after this change.
- Broken imports in `file_in.py`, `match.py`, `file_out.py`, and `main.py` are expected and
  intentional; they will be fixed in subsequent features.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `datatypes` module MUST export a `YnabTxn` class with instance fields:
  `id_` (int), `ts` (int), `date` (str), `title` (str), `category` (str), `amt_dollars` (str),
  `amt_cents` (int), `cleared` (str), `bal` (int, initialized to `0`).

- **FR-002**: `YnabTxn.amt_cents` MUST be derived from `amt_dollars` via `_dollars_to_cents`
  at construction time.

- **FR-003**: `_dollars_to_cents` MUST strip `$`, `"`, `,`, and `.` from its input string
  before converting to an integer, preserving any leading `-` sign.

- **FR-004**: The `datatypes` module MUST export `MergedTxn_YnabTxn` (replacing
  `MergedTxn_GoodbudgetTxn`); its constructor MUST accept a `YnabTxn`; its `ynab_txn`
  attribute MUST hold a deep copy.

- **FR-005**: `MergedTxn_BothTxns` MUST rename its `gb_txn` attribute to `ynab_txn` and
  accept a `YnabTxn` in its constructor alongside the existing `ChaseTxn`.

- **FR-006**: `TxnsGrouped` MUST rename its `only_gb_txns` attribute to `only_ynab_txns`.

- **FR-007**: The `MergedTxn` union type MUST reference `MergedTxn_YnabTxn` instead of
  `MergedTxn_GoodbudgetTxn`.

- **FR-008**: `datatypes.py` MUST contain zero references to `GoodbudgetTxn` or
  `MergedTxn_GoodbudgetTxn` after this change.

- **FR-009**: No other file (`file_in.py`, `match.py`, `file_out.py`, `main.py`, `graph.py`,
  `add_new_txns.py`) MUST be modified as part of this feature.

- **FR-010**: Four unit tests MUST be added to `tests/test_datatypes.py` covering: outflow
  construction, inflow construction, `$`-prefixed cents conversion, and signed cents conversion.
  All four MUST pass under `python3 -m pytest tests/test_datatypes.py`.

### Key Entities

- **YnabTxn**: Represents a single transaction from a YNAB CSV export. Key attributes: date
  (MM/DD/YYYY), payee as title, deepest-level category, signed amount in cents, cleared status,
  Unix timestamp, running balance (initialized to `0`, computed externally).

- **MergedTxn_YnabTxn**: Wrapper for a YNAB-only transaction in the merged view (no matching
  Chase transaction). Contains a deep copy of the `YnabTxn` and a `bal_diff` field.

- **MergedTxn_BothTxns**: Wrapper for a transaction present in both Chase and YNAB exports.
  Contains deep copies of both the `ChaseTxn` and `YnabTxn`.

- **TxnsGrouped**: Container holding four lists — Chase-only, YNAB-only, both, and merged —
  plus balance-difference frequency data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `python3 -m pytest tests/test_datatypes.py` exits with code `0` and all four
  specified tests pass with zero failures.

- **SC-002**: A search for `GoodbudgetTxn` or `MergedTxn_GoodbudgetTxn` in `datatypes.py`
  returns zero matches.

- **SC-003**: `from datatypes import YnabTxn, MergedTxn_YnabTxn, MergedTxn_BothTxns,
  TxnsGrouped, _dollars_to_cents` succeeds without any import error.

- **SC-004**: The out-of-scope modules remain importable: `python3 -c "import graph;
  import add_new_txns"` raises no `ImportError` or `AttributeError`.

## Assumptions

- The caller (`file_in.py`, updated in a later feature) is responsible for producing a signed
  decimal string from YNAB's separate Outflow/Inflow columns before passing it to `YnabTxn`.
- `graph.py` and `add_new_txns.py` do not import `GoodbudgetTxn` directly; this will be
  verified at implementation time.
- The `date` field format is MM/DD/YYYY as exported by YNAB.
- All monetary amounts follow the project constitution's balance convention: negative = expense,
  positive = income, stored as integers in cents.
- Broken imports in the other in-scope files are intentional and out of scope for this feature.
