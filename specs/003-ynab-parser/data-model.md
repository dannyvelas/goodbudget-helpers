# Data Model: Replace Goodbudget Parser with YNAB Parser

**Branch**: `003-ynab-parser` | **Date**: 2026-03-26

## Existing Entities (unchanged by this feature)

### YnabTxn (defined in `datatypes.py` — feature 001)

| Field | Type | Source |
|-------|------|--------|
| `id_` | `int` | Sequential line index from parser |
| `ts` | `int` | Unix timestamp derived from `date` |
| `date` | `str` | MM/DD/YYYY from YNAB CSV Date column |
| `title` | `str` | Payee column via `_shorten` |
| `category` | `str` | Category column (deepest level, col 6) |
| `amt_dollars` | `str` | Signed decimal string derived from Outflow/Inflow |
| `amt_cents` | `int` | Derived from `amt_dollars` via `_dollars_to_cents` |
| `cleared` | `str` | Cleared column value |
| `bal` | `int` | Initialized to 0; set by running balance pass |

**Balance convention**: negative `amt_cents` = expense; positive = income.

### ParseResult (returned by `read_ynab_txns`)

The existing `ParseResult` namedtuple (or equivalent result type) used by `read_ch_txns` is reused:

| Field | Type | Description |
|-------|------|-------------|
| `txns` | `list[YnabTxn]` | Successfully parsed transactions |
| `lines_failed` | `list[str]` | Lines that did not match `YNAB_REGEX` |

## New Symbols (this feature)

### YNAB_REGEX (in `regex.py`)

A compiled `re.Pattern` replacing `GB_EXPENSE_REGEX` and `GB_INCOME_REGEX`.

| Named Group | CSV Column | Example Value |
|-------------|-----------|---------------|
| `date` | Col 2 (Date) | `"03/25/2026"` |
| `payee` | Col 3 (Payee) | `"PATH"` |
| `category` | Col 6 (Category) | `"Transportation"` |
| `outflow` | Col 8 (Outflow, `$` stripped) | `"3.00"` |
| `inflow` | Col 9 (Inflow, `$` stripped) | `"0.00"` |
| `cleared` | Col 10 (Cleared) | `"Uncleared"` |

### IN_YNAB_FILE (in `file_in.py`)

| Constant | Value |
|----------|-------|
| `IN_YNAB_FILE` | `'./in/ynab.csv'` |

Replaces `IN_GB_FILE = './in/gb.csv'`.

## Removed Symbols (this feature)

| Symbol | Module | Replaced By |
|--------|--------|-------------|
| `GB_EXPENSE_REGEX` | `regex.py` | `YNAB_REGEX` |
| `GB_INCOME_REGEX` | `regex.py` | `YNAB_REGEX` |
| `read_gb_txns` | `file_in.py` | `read_ynab_txns` |
| `IN_GB_FILE` | `file_in.py` | `IN_YNAB_FILE` |

## YNAB CSV Format Reference

```
"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"
"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"
```

- Col indices: 0=Account, 1=Flag, 2=Date, 3=Payee, 4=CatGroup/Cat, 5=CatGroup, 6=Category, 7=Memo, 8=Outflow, 9=Inflow, 10=Cleared
- Outflow and Inflow are unquoted with a leading `$`
- All other fields are double-quoted
- File may begin with UTF-8 BOM (`\ufeff`) — handled by `encoding='utf-8-sig'`
