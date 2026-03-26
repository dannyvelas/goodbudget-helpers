# Data Model: Update Chase CSV Parser

**Feature**: 002-update-chase-regex
**Date**: 2026-03-26

## Entities

### ChaseTxn (unchanged class, updated field derivations)

No fields are added or removed. Two field derivations change:

| Field | Old derivation | New derivation |
|---|---|---|
| `is_debit` | `txn['deb_or_cred'] == 'DEBIT'` | `float(txn['amt']) < 0` |
| `is_pending` | `txn['balance'] == ' '` | `False` (hardcoded) |

All other fields (`id_`, `ts`, `date`, `title`, `amt_dollars`, `amt_cents`, `bal`) are
derived the same way as before.

---

### CH_REGEX (updated)

Old regex captured groups: `deb_or_cred`, `date`, `title`, `amt`, `balance`

New regex captures groups: `date`, `description`, `amt`

| Group | Column | Pattern |
|---|---|---|
| `date` | Transaction Date (col 0) | `\d\d\/\d\d\/\d{4}` |
| `description` | Description (col 2) | `"[^"]+"\|[^,\n]+` |
| `amt` | Amount (col 5) | `-?\d+\.\d\d` |

Skipped columns (consumed but not captured): Post Date (col 1), Category (col 3),
Type (col 4), Memo (col 6).

---

### read_ch_txns (updated logic)

```
Old flow:
  for i, line in enumerate(in_file):
    match CH_REGEX → capture deb_or_cred, date, title, amt, balance
    ChaseTxn(is_debit = deb_or_cred == 'DEBIT',
             is_pending = balance == ' ',
             title = _shorten(title), ...)

New flow:
  for i, line in enumerate(in_file):
    if i == 0: continue              ← explicit header skip
    match CH_REGEX → capture date, description, amt
    ChaseTxn(is_debit = float(amt) < 0,
             is_pending = False,
             title = _shorten(description), ...)
```

Running balance calculation and file path are unchanged.

---

## Files Modified

| File | Change |
|---|---|
| `regex.py` | Replace `_CH_REGEX_STR` and regenerate `CH_REGEX` |
| `file_in.py` | Update `read_ch_txns`: skip header, use `description` group, derive `is_debit` and `is_pending` from new logic |

## Files Unchanged

`datatypes.py`, `match.py`, `file_out.py`, `config.py`, `main.py`, `graph.py`,
`add_new_txns.py`, `regex.py` (GB regexes), `file_in.py` (`read_gb_txns`)
