# Research: Replace Goodbudget Parser with YNAB Parser

**Branch**: `003-ynab-parser` | **Date**: 2026-03-26

## Decision 1: YNAB CSV Format — Quoted 11-Column Layout

**Decision**: YNAB export CSVs use fully quoted fields in an 11-column format:

```
"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"
```

Example data row:
```
"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"
```

**Rationale**: Columns 8 (Outflow) and 9 (Inflow) use `$N.NN` notation — unquoted. All other fields are quoted. The regex must handle this mixed quoting. The `date` (col 2), `payee` (col 3), `category` (col 6 — deepest level), `outflow` (col 8), `inflow` (col 9), and `cleared` (col 10) are the fields needed.

**Alternatives considered**: Using Python `csv` module instead of regex. Rejected because the existing codebase uses regex for all parsers (Chase, Goodbudget) and the spec requires `YNAB_REGEX` as the boundary.

---

## Decision 2: YNAB_REGEX Named Group Design

**Decision**: Single regex with named groups `date`, `payee`, `category`, `outflow`, `inflow`, `cleared`. Outflow and Inflow strip the leading `$` during capture (using `\$` then a dollar-amount group).

```python
_YNAB_REGEX_STR = (
    r'"[^"]*"'           # Account (col 0, skip)
    r',"[^"]*"'          # Flag (col 1, skip)
    r',"(?P<date>[^"]+)"'                # Date (col 2)
    r',"(?P<payee>[^"]*)"'               # Payee (col 3)
    r',"[^"]*"'          # Category Group/Category (col 4, skip)
    r',"[^"]*"'          # Category Group (col 5, skip)
    r',"(?P<category>[^"]*)"'            # Category (col 6, deepest)
    r',"[^"]*"'          # Memo (col 7, skip)
    r',\$(?P<outflow>\d+\.\d\d)'         # Outflow (col 8, e.g. $3.00 → 3.00)
    r',\$(?P<inflow>\d+\.\d\d)'          # Inflow (col 9, e.g. $0.00 → 0.00)
    r',"(?P<cleared>[^"]+)"'             # Cleared (col 10)
)
```

**Why the header doesn't match**: The header row starts with `"Account"` (a word, not a dollar amount in col 8), so the `\$\d+\.\d\d` pattern for Outflow won't match.

**Alternatives considered**: A more permissive pattern capturing raw dollar strings (e.g., `[^,]+`). Rejected — the `$` prefix is mandatory in YNAB exports and anchoring on it provides the header rejection behavior for free.

---

## Decision 3: UTF-8 BOM Handling

**Decision**: Open `IN_YNAB_FILE` with `encoding='utf-8-sig'`. Python's `utf-8-sig` codec silently strips the BOM (`\ufeff`) if present, and behaves identically to `utf-8` when no BOM is present.

**Rationale**: YNAB exports sometimes include a UTF-8 BOM (observed on Windows). No explicit stripping logic is needed; `utf-8-sig` handles it transparently.

---

## Decision 4: Signed Amount Derivation

**Decision**: `read_ynab_txns` computes `amt_dollars` from captured `outflow` and `inflow` strings:

```python
outflow_val = float(outflow_str)
inflow_val  = float(inflow_str)
if outflow_val > 0.0:
    amt_dollars = f"-{outflow_str}"
elif inflow_val > 0.0:
    amt_dollars = inflow_str
else:
    amt_dollars = "0.00"
```

**Rationale**: `_dollars_to_cents` (already updated in feature 001 to strip `$`) expects a signed decimal string. Constructing it here keeps `YnabTxn` construction clean.

---

## Decision 5: Header Skip Strategy

**Decision**: `read_ynab_txns` skips line index 0 explicitly (`if i == 0: continue`), identical to the pattern used in `read_ch_txns`. This ensures the header never reaches `lines_failed` regardless of regex behavior.

**Rationale**: Belt-and-suspenders — even if the regex were accidentally loosened, the explicit index skip guarantees correctness.

---

## Decision 6: Known Constitution Violation — graph.py Breakage

**Decision**: Removing `read_gb_txns` from `file_in.py` (FR-010) will break `graph.py`, which imports it at the top level (`from file_in import read_gb_txns`). This is an acknowledged violation of **Constitution Principle IV (Scope Isolation)** — we are breaking an out-of-scope module.

**Mitigation**: The breakage is documented in the spec Assumptions section and in this plan's Complexity Tracking table. Updating `graph.py` to use `read_ynab_txns` is deferred to a follow-up feature. The violation is accepted because `graph.py` is a standalone graphing utility not part of the organizing pipeline, and deleting dead code from `file_in.py` is the simpler long-term state.

**Alternatives considered**: Keeping `read_gb_txns` as a shim that calls `read_ynab_txns`. Rejected — this adds complexity and the spec explicitly requires removing it (FR-010).

---

## Decision 7: TypeVar Update (Mechanical)

**Decision**: The `TypeVar` in `file_in.py` currently references `GoodbudgetTxn`. It will be updated to `YnabTxn`. This is a mechanical type-annotation fix with no behavioral impact and is in scope per spec Assumptions.
