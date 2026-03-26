# Data Model: Replace Regex Parsers with csv.reader

**Branch**: `004-csv-reader-parsers` | **Date**: 2026-03-26

## Existing Entities (unchanged by this feature)

### ChaseTxn (defined in `datatypes.py`)

| Field | Type | Source |
|-------|------|--------|
| `id_` | `int` | Sequential row index from parser |
| `ts` | `int` | Unix timestamp derived from `date` |
| `date` | `str` | MM/DD/YYYY — col 0 of Chase CSV |
| `title` | `str` | Description (col 2) via `_shorten` |
| `amt_dollars` | `str` | Amount (col 5) |
| `amt_cents` | `int` | Derived from `amt_dollars` |
| `is_debit` | `bool` | `True` if Amount < 0 |
| `is_pending` | `bool` | Always `False` |
| `bal` | `int` | Set by running balance pass |

### YnabTxn (defined in `datatypes.py` — feature 001)

| Field | Type | Source |
|-------|------|--------|
| `id_` | `int` | Sequential row index from parser |
| `ts` | `int` | Unix timestamp derived from `date` |
| `date` | `str` | MM/DD/YYYY — col 2 of YNAB CSV |
| `title` | `str` | Payee (col 3) via `_shorten` |
| `category` | `str` | Category (col 6, deepest level) |
| `amt_dollars` | `str` | Signed decimal string derived from Outflow/Inflow |
| `amt_cents` | `int` | Derived from `amt_dollars` via `_dollars_to_cents` |
| `cleared` | `str` | Cleared (col 10) |
| `bal` | `int` | Set by running balance pass |

### ParseResult (returned by both parsers)

| Field | Type | Description |
|-------|------|-------------|
| `txns` | `list[ChaseTxn]` or `list[YnabTxn]` | Successfully parsed transactions |
| `lines_failed` | `list[str]` | Rows that failed validation |

## Chase CSV Column Map (7 columns, 0-indexed)

| Index | Header | Used? | Notes |
|-------|--------|-------|-------|
| 0 | Transaction Date | ✅ `date` | MM/DD/YYYY |
| 1 | Post Date | skip | |
| 2 | Description | ✅ `title` | via `_shorten` |
| 3 | Category | skip | |
| 4 | Type | skip | |
| 5 | Amount | ✅ `amt_dollars` | float-parseable, may be negative |
| 6 | Memo | skip | |

**Validity check**: `len(row) == 7` and `float(row[5])` succeeds.

## YNAB CSV Column Map (11 columns, 0-indexed)

| Index | Header | Used? | Notes |
|-------|--------|-------|-------|
| 0 | Account | skip | |
| 1 | Flag | skip | |
| 2 | Date | ✅ `date` | MM/DD/YYYY |
| 3 | Payee | ✅ `title` | via `_shorten`; may contain commas |
| 4 | Category Group/Category | skip | |
| 5 | Category Group | skip | |
| 6 | Category | ✅ `category` | deepest level |
| 7 | Memo | skip | |
| 8 | Outflow | ✅ `outflow` | e.g. `$3.00` → strip `$` → `"3.00"` |
| 9 | Inflow | ✅ `inflow` | e.g. `$0.00` → strip `$` → `"0.00"` |
| 10 | Cleared | ✅ `cleared` | |

**Validity check**: `len(row) == 11` and `float(row[8].lstrip('$'))` and
`float(row[9].lstrip('$'))` both succeed.

**File encoding**: `encoding='utf-8-sig'` (strips optional UTF-8 BOM).

## Removed Symbols (this feature)

| Symbol | Module | Reason |
|--------|--------|--------|
| `_CH_REGEX_STR` | `regex.py` | No longer needed |
| `CH_REGEX` | `regex.py` | Replaced by `csv.reader` in `read_ch_txns` |
| `_GB_INCOME_REGEX_STR` | `regex.py` | Dead code (GB retired) |
| `_GB_EXPENSE_REGEX_STR` | `regex.py` | Dead code (GB retired) |
| `GB_INCOME_REGEX` | `regex.py` | Dead code (GB retired) |
| `GB_EXPENSE_REGEX` | `regex.py` | Dead code (GB retired) |
| `read_gb_txns` | `file_in.py` | Dead code (GB retired) |
| `IN_GB_FILE` | `file_in.py` | Dead code (GB retired) |

## New Symbols (this feature)

| Symbol | Module | Value / Description |
|--------|--------|---------------------|
| `IN_YNAB_FILE` | `file_in.py` | `'./in/ynab.csv'` |
| `read_ynab_txns` | `file_in.py` | New parser using `csv.reader` |
