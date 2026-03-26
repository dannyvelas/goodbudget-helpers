# Research: Add Tests for match.py YNAB Type Migration

**Branch**: `005-match-ynab-tests` | **Date**: 2026-03-26

## Decision 1: match.py Is Already Fully Updated — No Source Changes Needed

**Decision**: `match.py` was updated in commit `37c6d82`. All six banned Goodbudget
symbols (`GoodbudgetTxn`, `MergedTxn_GoodbudgetTxn`, `gb_txn`, `gb_sorted`,
`gb_bal`, `only_gb_txns`) have been replaced. Verified by reading the file:

- Import: `MergedTxn_YnabTxn` (not `MergedTxn_GoodbudgetTxn`)
- `_sort_merged_txns`: uses `txn.ynab_txn.id_` and `isinstance(..., MergedTxn_YnabTxn)`
- `get_txns_grouped` signature: `ynab_txns: List[YnabTxn]`, `yn_start_bal: int`
- Loop variables: `ynab_txn`, `yn_sorted`, `yn_bal`, `yn_i`
- `TxnsGrouped(only_ynab_txns=...)` — uses the updated constructor parameter

**Alternatives considered**: Checking git diff instead. Rejected — reading the file
directly is authoritative.

---

## Decision 2: YnabTxn.bal Is 0 by Default — No Manual Override in Tests

**Decision**: `YnabTxn.__init__` sets `self.bal = 0` unconditionally (verified in
`datatypes.py:52`). Tests do not need to set `ynab_txn.bal = 0` explicitly before
passing to `get_txns_grouped`.

**Rationale**: The matching algorithm sets `bal` during the balance pass inside
`get_txns_grouped`; the initial value from the constructor is irrelevant to the
`both_txns`/`only_ch_txns`/`only_ynab_txns` outcome being asserted.

---

## Decision 3: get_txns_grouped Signature Confirmed

**Decision**: `get_txns_grouped(ch_txns, ynab_txns, ch_start_bal, yn_start_bal)`.
Tests call it as `get_txns_grouped([ch_txn], [ynab_txn], 0, 0)`.

**Verified from** `match.py:54-59`:
```python
def get_txns_grouped(
    ch_txns: List[ChaseTxn],
    ynab_txns: List[YnabTxn],
    ch_start_bal: int,
    yn_start_bal: int,
) -> TxnsGrouped:
```

---

## Decision 4: TxnsGrouped Attribute Names Confirmed

**Decision**: `TxnsGrouped` has attributes `both_txns`, `only_ch_txns`,
`only_ynab_txns` (updated in feature 001 when `only_gb_txns` was renamed).
Tests assert on all three.

---

## Decision 5: No New Dependencies Required

**Decision**: `tests/test_match.py` imports only from `datatypes` and `match` —
both already present. No `tempfile`, `patch`, or file I/O needed since
`get_txns_grouped` takes plain lists, not file paths.

**Rationale**: The matching function is pure (list in, TxnsGrouped out). Tests are
simpler than parser tests — no temp files, no mocking.

---

## Decision 6: Test Timestamps

**Decision**: Use the exact timestamps specified in the spec:
- `1735689600` = 2025-01-01 00:00:00 UTC
- `1736380800` = 2025-01-09 00:00:00 UTC (8 days later, exceeds MAX_DAYS_APART=7)

**Verified**: `(1736380800 - 1735689600) / (60*60*24) = 8.0` days > 7.
