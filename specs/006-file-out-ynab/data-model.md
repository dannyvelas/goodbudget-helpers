# Data Model: Update file_out.py to Use YNAB Types

**Branch**: `006-file-out-ynab` | **Date**: 2026-03-26

## Existing Entities Used by This Feature (all unchanged)

### YnabTxn (`datatypes.py`)

| Field | Type | Notes |
|-------|------|-------|
| `id_` | `int` | Row identifier |
| `ts` | `int` | Unix timestamp |
| `date` | `str` | Display date `'MM/DD/YYYY'` |
| `title` | `str` | Transaction description |
| `category` | `str` | YNAB budget category (replaces `GoodbudgetTxn.envelope`) |
| `amt_dollars` | `str` | Dollar string e.g. `'-25.00'` |
| `amt_cents` | `int` | Derived: `-2500` |
| `cleared` | `str` | YNAB cleared status |
| `bal` | `int` | Running balance in cents (default `0`) |

### MergedTxn_YnabTxn (`datatypes.py`)

| Field | Type | Notes |
|-------|------|-------|
| `ynab_txn` | `YnabTxn` | Deep copy of the wrapped YNAB transaction |
| `bal_diff` | `int` | Balance difference in cents (default `0`) |

Replaces `MergedTxn_GoodbudgetTxn`. The wrapped transaction attribute is
`ynab_txn` (was `gb_txn`).

### TxnsGrouped (`datatypes.py`)

| Attribute | Type | Notes |
|-----------|------|-------|
| `both_txns` | `List[MergedTxn_BothTxns]` | Matched pairs |
| `only_ch_txns` | `List[ChaseTxn]` | Chase-only transactions |
| `only_ynab_txns` | `List[YnabTxn]` | YNAB-only transactions (was `only_gb_txns`) |
| `merged_txns` | `List[MergedTxn]` | All transactions in merge order |
| `bal_diff_freq` | `List[BalanceDifferenceFrequency]` | Balance diff histogram |

## Output Files (unchanged structure, updated names/content)

| File | Description | Change |
|------|-------------|--------|
| `chase.csv` | Unmatched Chase transactions | No change |
| `ynab.csv` | Unmatched YNAB transactions | Renamed from `goodbudget.csv` |
| `both.csv` | Matched transaction pairs | Type label `'GOODBUDGET'` → `'YNAB'` |
| `merged.csv` | All transactions in order | Type label `'GOODBUDGET'` → `'YNAB'` |
| `bal_diff_freq.csv` | Balance diff frequency | No change |
| `log.txt` | Parse errors + match counts | `'GOODBUDGET'` → `'YNAB'` in log line |

## Column Headers

### ynab.csv (new `_YNAB_FIELD_NAMES`)

```
YNAB ID,YNAB Date,YNAB Title,YNAB Category,YNAB Txn Amount,YNAB Balance
```

Previously: `Goodbudget ID,Goodbudget Date,Goodbudget Title,Goodbudget Envelope,Goodbudget Txn Amount,Goodbudget Balance`

### merged.csv / both.csv (`_MERGED_TXN_FIELD_NAMES`)

Derived: `Txn Type,{_CH_FIELD_NAMES},{_YNAB_FIELD_NAMES},Balance Difference`

## Modified Files (this feature)

| File | Change |
|------|--------|
| `file_out.py` | All Goodbudget symbols renamed to YNAB equivalents |
| `tests/test_file_out.py` | NEW — 2 unit tests |

## Unchanged Files

`datatypes.py`, `match.py`, `file_in.py`, `regex.py`, `main.py`, `graph.py`,
`add_new_txns.py` — untouched.
