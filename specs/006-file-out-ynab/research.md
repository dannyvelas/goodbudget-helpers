# Research: Update file_out.py to Use YNAB Types

**Branch**: `006-file-out-ynab` | **Date**: 2026-03-26

## Summary

No open questions. This feature is a pure mechanical rename — all decisions are
determined by the existing codebase and the feature specification. No external
research required.

## Decisions

### D-001: `_ynab_txn_to_row` uses `ynab_txn.category`

**Decision**: Use `ynab_txn.category` in place of `gb_txn.envelope`.
**Rationale**: `YnabTxn` has a `category` field (YNAB's transaction category); the
old `GoodbudgetTxn` had `envelope` (Goodbudget's equivalent concept). The field
purpose is identical — the budget category the transaction belongs to — only the
name differs between the two systems.
**Alternatives considered**: None — `YnabTxn` does not have an `envelope` field.

### D-002: `goodbudget.csv` → `ynab.csv`

**Decision**: Rename the output file from `goodbudget.csv` to `ynab.csv`.
**Rationale**: The file contains unmatched YNAB transactions. Naming it after
the data source (`ynab.csv`) makes the output directory self-documenting.
**Alternatives considered**: `unmatched_ynab.csv` — rejected; consistent with
the existing `chase.csv` naming convention (source name only, no qualifier).

### D-003: Type label `'GOODBUDGET'` → `'YNAB'`

**Decision**: Replace the string literal `'GOODBUDGET'` with `'YNAB'` as the type
discriminator in `merged.csv` and `both.csv` rows.
**Rationale**: The type label identifies the data source of an unmatched transaction.
Since the source is now YNAB, `'YNAB'` is the correct label.
**Alternatives considered**: None.

### D-004: `MergedTxn_YnabTxn.ynab_txn` attribute name

**Decision**: Access the wrapped transaction as `merged_txn.ynab_txn` in
`_merged_txn_to_row`.
**Rationale**: `MergedTxn_YnabTxn` (defined in `datatypes.py`, feature 001) exposes
the wrapped transaction as `.ynab_txn`, not `.gb_txn`. Confirmed from the existing
datatype definition.
**Alternatives considered**: None.

### D-005: `GoodbudgetTxn`/`MergedTxn_GoodbudgetTxn` retained in `datatypes.py`

**Decision**: Do not remove `GoodbudgetTxn` or `MergedTxn_GoodbudgetTxn` from
`datatypes.py` in this feature.
**Rationale**: `graph.py` and `add_new_txns.py` may still reference these types.
Removing them is deferred to a future cleanup feature.
**Alternatives considered**: Remove now — rejected; out-of-scope per IV. Scope
Isolation and not part of this feature's specification.

## No NEEDS CLARIFICATION Items

All technical choices were deterministic from the spec and existing code. Phase 0
research is complete.
