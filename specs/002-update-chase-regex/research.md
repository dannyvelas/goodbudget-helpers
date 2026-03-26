# Research: Update Chase CSV Parser for New Export Format

**Feature**: 002-update-chase-regex
**Date**: 2026-03-26

## Findings

### Decision: No external research required
**Rationale**: All technology choices are fixed (Python 3, `re` module, pytest). The new CSV
format is fully specified in the feature description. No new dependencies are introduced.

---

### Decision: New `CH_REGEX` pattern
**Rationale**: The new Chase CSV format is:
```
Transaction Date,Post Date,Description,Category,Type,Amount,Memo
03/24/2026,03/25/2026,HEADWAY,Health & Wellness,Sale,-15.00,
```

Named groups required: `date` (column 0), `description` (column 2), `amt` (column 5).

Columns 1 (Post Date), 3 (Category), 4 (Type), 6 (Memo) are consumed but not captured.

Pattern:
```python
_CH_REGEX_STR = (
    r'(?P<date>\d\d\/\d\d\/\d{4})'        # Transaction Date
    r',\d\d\/\d\d\/\d{4}'                 # Post Date (skipped)
    r',(?P<description>"[^"]+"|[^,\n]+)'  # Description (quoted or unquoted)
    r',[^,\n]+'                            # Category (skipped)
    r',[^,\n]+'                            # Type (skipped)
    r',(?P<amt>-?\d+\.\d\d)'              # Amount
    r',.*'                                 # Memo (skipped, may be empty)
)
```

**Header no-match**: The header row starts with `Transaction Date` which does not match
`\d\d\/\d\d\/\d{4}` — so the regex naturally won't match it. The spec also requires
explicit skip in code to prevent it appearing in `lines_failed`.

**Alternatives considered**:
- Anchor with `^` — unnecessary since `re.match` already anchors at the start.
- Capture all seven fields — REJECTED: only three are needed; extra groups add noise.

---

### Decision: `is_debit` derived from `float(amt) < 0`
**Rationale**: The old format had a `DEBIT|CREDIT` prefix. The new format has only a signed
Amount column. Negative amount = expense/debit. Positive = income/credit. This aligns with
the constitution's Cents Convention (Principle II).

**Implementation**: `is_debit = float(txn['amt']) < 0`

**Alternatives considered**:
- Derive from `amt_cents < 0` after construction — REJECTED: `is_debit` is set at
  construction time before `amt_cents` is available via the constructor.
- Parse as `_dollars_to_cents(amt) < 0` — valid alternative but `float()` is simpler for
  a sign check; the actual cents value is handled by `_dollars_to_cents` inside `ChaseTxn`.

---

### Decision: `is_pending = False` unconditionally
**Rationale**: The old format used a blank balance column to indicate pending status. The
new format has no balance column. No heuristic is available. The bot-adding feature that
consumed `is_pending` is out of scope. Setting `False` is the safe default.

---

### Decision: Header row skipped explicitly at `i == 0`
**Rationale**: The spec requires the header NOT appear in `lines_failed`. The regex won't
match it, so without an explicit skip it would be appended to `lines_failed`. An explicit
`if i == 0: continue` before the regex check is the simplest fix.

**Alternatives considered**:
- Match and discard the header via a separate regex — REJECTED: unnecessary complexity;
  `i == 0` is simpler and equally correct since the header is always the first row.
- Strip the header in the caller — REJECTED: `read_ch_txns` is responsible for its own
  input file.

---

### Out-of-scope module import audit
| File | Imports `CH_REGEX`? | Imports `read_ch_txns`? | Impact |
|---|---|---|---|
| `graph.py` | No | No (imports `read_gb_txns` only) | None |
| `add_new_txns.py` | No | No (calls via `main.py` pipeline) | None |

Both out-of-scope files are unaffected. Constitution Principle IV satisfied.

---

### Decision: `_shorten` applied to `description` group (not `title`)
**Rationale**: The new regex captures the group as `description` (matching the CSV column
name). `read_ch_txns` must read `txn['description']` and pass it to `_shorten`. The
resulting value is stored as `ChaseTxn.title` as before.

**Note on `_shorten` behavior**: `_shorten` appends `'"'` when the string contains a space
and does not already end with `'"'`. For unquoted descriptions like `'PAYMENT THANK YOU'`
this produces `'PAYMENT THANK YOU"'`. This is existing behavior; tests must account for it.
