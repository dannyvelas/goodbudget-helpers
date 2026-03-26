# Data Model: YNAB Datatype Migration

**Feature**: 001-ynab-datatype-migration
**Date**: 2026-03-26

## Entities

### YnabTxn (new)

Represents a single transaction from a YNAB CSV export.

| Field | Type | Source | Notes |
|---|---|---|---|
| `id_` | `int` | constructor | Sequential read-order ID assigned by parser |
| `ts` | `int` | constructor | Unix timestamp derived from `date` by parser |
| `date` | `str` | constructor | MM/DD/YYYY string as exported by YNAB |
| `title` | `str` | constructor | YNAB "Payee" column, optionally shortened |
| `category` | `str` | constructor | Deepest level of YNAB category hierarchy |
| `amt_dollars` | `str` | constructor | Signed decimal string, e.g. `"-25.00"` or `"500.00"` |
| `amt_cents` | `int` | derived | `_dollars_to_cents(amt_dollars)` at construction |
| `cleared` | `str` | constructor | YNAB "Cleared" column value (e.g. `"Cleared"`) |
| `bal` | `int` | computed | Running balance in cents; initialized to `0`, set externally |

**Sign convention**: `amt_cents < 0` = expense (debit), `amt_cents > 0` = income (credit).

**Relationship**: Replaces `GoodbudgetTxn` in the organizing pipeline.
`GoodbudgetTxn` is retained in `datatypes.py` for the duration of this migration phase.

---

### _dollars_to_cents (updated helper function)

Converts a formatted dollar string to an integer number of cents.

**Current behavior**: Strips `"`, `,`, `.` then calls `int()`.

**Updated behavior**: Also strips `$` before the existing strip chain.

Strip order (left to right, all via `str.replace`):
1. `'"'` (double-quote)
2. `'$'` (dollar sign — new)
3. `','` (comma thousands separator)
4. `'.'` (decimal point)

Result: `int()` of the remaining string. The `-` sign is preserved by this process.

**Examples**:

| Input | After strip | Result |
|---|---|---|
| `'$3.00'` | `'300'` | `300` |
| `'-25.00'` | `'-2500'` | `-2500` |
| `'"1,234.56"'` | `'123456'` | `123456` |
| `'$0.00'` | `'0'` | `0` |

---

### MergedTxn_YnabTxn (new)

Wraps a `YnabTxn` representing a transaction present in YNAB but not in Chase.

| Field | Type | Notes |
|---|---|---|
| `ynab_txn` | `YnabTxn` | Deep copy of the input `YnabTxn` |
| `bal_diff` | `int` | Balance difference in cents; initialized to `0`, set externally |

**Relationship**: Parallel to `MergedTxn_ChaseTxn`. Replaces `MergedTxn_GoodbudgetTxn` in
the new pipeline. `MergedTxn_GoodbudgetTxn` is retained for the migration phase.

---

### MergedTxn_BothTxns (field rename deferred)

Wraps a matched Chase + YNAB transaction pair.

**Deferred**: Renaming `gb_txn` → `ynab_txn` on this class is deferred because
`add_new_txns.py` (out-of-scope) accesses `x.gb_txn` on line 146. Renaming now would break it.

The constructor signature and attribute name remain unchanged in this task.

---

### TxnsGrouped (field rename: only_gb_txns → only_ynab_txns)

Container grouping all transaction lists.

| Field | Old name | New name | Type |
|---|---|---|---|
| Chase-only list | `only_ch_txns` | `only_ch_txns` | `List[ChaseTxn]` |
| YNAB-only list | `only_gb_txns` | **`only_ynab_txns`** | `List[YnabTxn]` |
| Both list | `both_txns` | `both_txns` | `List[MergedTxn_BothTxns]` |
| Merged list | `merged_txns` | `merged_txns` | `List[MergedTxn]` |
| Balance frequency | `bal_diff_freq` | `bal_diff_freq` | `List[BalanceDifferenceFrequency]` |

**Note**: `only_ynab_txns` rename is safe — `add_new_txns.py` does not reference
`only_gb_txns` directly (it reads `only_ch_txns`); `graph.py` does not reference it.
`match.py` and `file_out.py` do reference it but those files are in-scope and intentionally
broken per the spec (to be fixed in later tasks).

---

### MergedTxn union (updated)

```python
MergedTxn = Union[MergedTxn_ChaseTxn, MergedTxn_YnabTxn, MergedTxn_BothTxns]
```

`MergedTxn_GoodbudgetTxn` is removed from the union because:
- It is still instantiated in `match.py`, but `match.py` is an in-scope file that is
  intentionally broken in this task (imports `MergedTxn_GoodbudgetTxn` by name).
- The union type is used for type annotations; updating it to `MergedTxn_YnabTxn` reflects
  the intended post-migration state.

---

## State Transitions

`bal` on both `YnabTxn` and `ChaseTxn` starts at `0` and is mutated externally during
the matching pass in `match.py` (or its replacement). This pattern is unchanged.

## Retained Classes (unchanged in this task)

- `GoodbudgetTxn` — retained for `graph.py` and `add_new_txns.py` compatibility
- `MergedTxn_GoodbudgetTxn` — retained (still exported; removal deferred)
- `MergedTxn_BothTxns.gb_txn` — field rename deferred
- `ChaseTxn`, `MergedTxn_ChaseTxn`, `BalanceDifferenceFrequency` — unchanged
