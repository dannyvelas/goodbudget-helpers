# Data Model: Add Tests for match.py YNAB Type Migration

**Branch**: `005-match-ynab-tests` | **Date**: 2026-03-26

## Existing Entities Used by Tests (all unchanged by this feature)

### ChaseTxn (`datatypes.py`)

| Field | Type | Test value |
|-------|------|------------|
| `id_` | `int` | `0` |
| `ts` | `int` | `1735689600` (matched/mismatch tests) or same |
| `is_debit` | `bool` | `True` |
| `is_pending` | `bool` | `False` |
| `date` | `str` | `'01/01/2025'` |
| `title` | `str` | `'Amazon'` |
| `amt_dollars` | `str` | `'-25.00'` |
| `amt_cents` | `int` | Derived: `-2500` |
| `bal` | `int` | `0` (initial) |

### YnabTxn (`datatypes.py`)

| Field | Type | Test value |
|-------|------|------------|
| `id_` | `int` | `0` |
| `ts` | `int` | `1735689600` (same day) or `1736380800` (8 days later) |
| `date` | `str` | `'01/01/2025'` |
| `title` | `str` | `'Amazon'` |
| `category` | `str` | `'Shopping'` |
| `amt_dollars` | `str` | `'-25.00'` or `'-30.00'` depending on test |
| `amt_cents` | `int` | Derived: `-2500` or `-3000` |
| `cleared` | `str` | `'Cleared'` |
| `bal` | `int` | `0` (initial, set by constructor) |

### TxnsGrouped (`datatypes.py`) — return type of `get_txns_grouped`

| Attribute | Type | Asserted in tests |
|-----------|------|-------------------|
| `both_txns` | `List[MergedTxn_BothTxns]` | Length checked in all 3 tests |
| `only_ch_txns` | `List[ChaseTxn]` | Length checked in all 3 tests |
| `only_ynab_txns` | `List[YnabTxn]` | Length checked in all 3 tests |

## Test Scenarios Data

| Test | ChaseTxn amt_cents | YnabTxn amt_cents | ts delta (days) | Expected both | Expected only_ch | Expected only_ynab |
|------|--------------------|-------------------|-----------------|---------------|------------------|--------------------|
| `test_match_both_txns` | -2500 | -2500 | 0 | 1 | 0 | 0 |
| `test_match_only_ch_and_only_ynab` | -2500 | -3000 | 0 | 0 | 1 | 1 |
| `test_match_outside_7_days` | -2500 | -2500 | 8 | 0 | 1 | 1 |

## New Files (this feature)

| File | Description |
|------|-------------|
| `tests/test_match.py` | 3 unit tests for `get_txns_grouped` |

## No Changes to Existing Files

`match.py`, `datatypes.py`, `file_in.py`, `regex.py` — untouched.
