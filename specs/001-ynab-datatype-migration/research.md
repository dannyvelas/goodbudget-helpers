# Research: YNAB Datatype Migration

**Feature**: 001-ynab-datatype-migration
**Date**: 2026-03-26

## Findings

### Decision: No external research required
**Rationale**: All technology choices are already fixed by the existing codebase and project
constitution. Python 3, `copy.deepcopy`, `typing.Union`, and pytest are all in current use.
No new dependencies are introduced.

**Alternatives considered**: None — this is a rename/extension of existing types within a
single file.

---

### Decision: `GoodbudgetTxn` must remain in `datatypes.py` during this migration phase
**Rationale**: Both `graph.py` (line 8) and `add_new_txns.py` (line 9) import `GoodbudgetTxn`
directly from `datatypes`. These are out-of-scope files that the constitution (Principle IV)
mandates MUST NOT be broken. Removing `GoodbudgetTxn` from `datatypes.py` in this task would
break both files.

Furthermore, `GoodbudgetTxn` and `YnabTxn` are not interchangeable — `add_new_txns.py`
accesses `gb_txn.envelope` and `gb_txn.notes`, fields that `YnabTxn` does not have. A simple
type alias is therefore impossible.

**Resolution**: `GoodbudgetTxn` is retained unchanged in `datatypes.py` for this feature.
Spec FR-008 ("zero references to GoodbudgetTxn") applies to the *end state* of the full
migration, not to this individual task. The Complexity Tracking table documents this.

**Alternatives considered**:
- Remove `GoodbudgetTxn` immediately → REJECTED: breaks out-of-scope files (constitution
  violation, Principle IV).
- Type alias `GoodbudgetTxn = YnabTxn` → REJECTED: fields are incompatible (`envelope`/`notes`
  vs `category`/`cleared`).

---

### Decision: `_dollars_to_cents` strip order — strip `$` before processing sign
**Rationale**: YNAB Outflow/Inflow columns use the format `$3.00` (positive, no sign). The
parser in `file_in.py` (future task) will negate the value for outflows. When `amt_dollars` is
already a signed string like `"-25.00"`, the `$` may not be present. The function strips `$`,
`"`, `,`, and `.` and then converts to int. The `-` sign must be preserved; stripping removes
only the listed characters.

**Implementation note**: Current `_dollars_to_cents` strips `"`, `,`, `.` and calls `int()`.
Adding `$` to the strip chain is the only change needed.

**Alternatives considered**:
- Strip `$` only from leading position → REJECTED: overly specific, unnecessary constraint.
- Add a separate `_ynab_dollars_to_cents` function → REJECTED: violates Simplicity principle;
  the existing function can handle the additional character with a trivial change.

---

### Decision: `copy.deepcopy` used in all MergedTxn constructors
**Rationale**: All existing `MergedTxn_*` constructors use `deepcopy`. `MergedTxn_YnabTxn`
must follow the same pattern so that mutations to the original `YnabTxn` after construction
do not affect the wrapped copy (e.g., `bal` field is set externally in `match.py`).

---

### Out-of-scope module import audit
| File | Imports `GoodbudgetTxn`? | Uses `MergedTxn_GoodbudgetTxn`? | Uses `gb_txn` field? |
|---|---|---|---|
| `graph.py` | Yes (line 8) | No | No |
| `add_new_txns.py` | Yes (line 9) | No (uses `TxnsGrouped`) | Yes (line 146: `x.gb_txn.title`) |

Both files must continue to work. `GoodbudgetTxn` stays in `datatypes.py`.

`add_new_txns.py` line 146 accesses `x.gb_txn.title` on a `MergedTxn_BothTxns`. Since we are
renaming `MergedTxn_BothTxns.gb_txn` → `ynab_txn`, **this will break `add_new_txns.py`**.

**Revised resolution**: `MergedTxn_BothTxns.gb_txn` MUST NOT be renamed in this task.
Renaming it is deferred to a follow-up feature that also updates `add_new_txns.py`.

This means the spec's rename of `MergedTxn_BothTxns.gb_txn` → `ynab_txn` is deferred.
The spec's rename of `MergedTxn_GoodbudgetTxn` → `MergedTxn_YnabTxn` and
`TxnsGrouped.only_gb_txns` → `only_ynab_txns` must also be checked:

- `add_new_txns.py` line 146: accesses `x.gb_txn` on `MergedTxn_BothTxns` → deferred
- `add_new_txns.py` does NOT reference `MergedTxn_GoodbudgetTxn` by name → rename is safe
- `add_new_txns.py` does NOT reference `only_gb_txns` directly → rename is safe
- `graph.py` does NOT reference `MergedTxn_GoodbudgetTxn` or `only_gb_txns` → renames safe

**Final scope for this task**:
- ✅ Add `YnabTxn` class
- ✅ Update `_dollars_to_cents` (add `$` strip)
- ✅ Keep `GoodbudgetTxn` unchanged (no removal)
- ✅ Add `MergedTxn_YnabTxn` class (new class, does not remove `MergedTxn_GoodbudgetTxn` yet)
- ✅ Rename `TxnsGrouped.only_gb_txns` → `only_ynab_txns` (safe — `add_new_txns.py` does not use it)
- ❌ Rename `MergedTxn_BothTxns.gb_txn` → `ynab_txn` — DEFERRED (breaks `add_new_txns.py` line 146)
- ❌ Remove `MergedTxn_GoodbudgetTxn` — DEFERRED (may still be used in match.py which is in-scope but intentionally broken per spec)
- ✅ Update `MergedTxn` union type to add `MergedTxn_YnabTxn`
- ✅ Four unit tests in `tests/test_datatypes.py`
