# Research: Replace Regex Parsers with csv.reader

**Branch**: `004-csv-reader-parsers` | **Date**: 2026-03-26

## Decision 1: csv.reader Handles YNAB's Mixed-Quoting Correctly

**Decision**: Use `csv.reader` with default dialect settings (comma delimiter,
double-quote quotechar). No custom dialect needed.

**Rationale**: YNAB's export format has most fields double-quoted but Outflow and
Inflow unquoted (e.g., `$3.00`). Python's `csv.reader` handles this correctly:
RFC-4180 says unquoted fields are read as-is up to the next comma; a field is only
treated as quoted if it starts with a `"`. So `$3.00` → `"$3.00"` (string) and
`"PATH"` → `"PATH"` (string, outer quotes stripped). This also means payees with
embedded commas (e.g., `"Smith, John"`) are correctly read as one field.

**Verified with**: Python 3.14 REPL:
```python
import csv, io
line = '"Chase Credit Card","","03/25/2026","Smith, John","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"'
list(csv.reader([line]))
# → [['Chase Credit Card', '', '03/25/2026', 'Smith, John', 'Needs: Transportation',
#     'Needs', 'Transportation', '', '$3.00', '$0.00', 'Uncleared']]
```

**Alternatives considered**: Custom dialect with `quoting=csv.QUOTE_NONE` or
`QUOTE_MINIMAL`. Rejected — default dialect is correct and simpler.

---

## Decision 2: Row Validation Strategy

**Decision**: A row is valid if it has the expected column count AND the
amount-bearing columns parse as floats (after stripping `$` for YNAB).

- Chase: 7 columns, `float(row[5])` succeeds (Amount column)
- YNAB: 11 columns, `float(row[8].lstrip('$'))` and `float(row[9].lstrip('$'))` succeed

Invalid rows are appended to `lines_failed` as `','.join(row)`.

**Rationale**: Column count + float parse is the minimal check needed to prevent
`IndexError` or `ValueError` downstream. Stronger schema validation is not needed
for known-good export files from Chase and YNAB.

**Alternatives considered**: Re-raising `csv.Error` as a `lines_failed` entry.
Retained as a fallback — if `csv.reader` itself raises (malformed quoting), catch
and append the raw line string.

---

## Decision 3: Header Skipping

**Decision**: Same pattern as the existing `read_ch_txns` — explicit `if i == 0: continue`
using `enumerate` over the `csv.reader` iterator. Header is never validated or
added to `lines_failed`.

**Rationale**: Consistent with the existing codebase. Simpler than using `next()` to
advance past the header, and avoids a subtle bug where `next()` on an empty file raises
`StopIteration`.

---

## Decision 4: Stripping `$` from YNAB Outflow/Inflow

**Decision**: Strip `$` at the point of reading the column values in `read_ynab_txns`,
using `.lstrip('$')`. The stripped string is used both for float-parsing validation
and for constructing `amt_dollars`.

**Rationale**: `_dollars_to_cents` already strips `$` (updated in feature 001), but
the signed `amt_dollars` string passed to `YnabTxn` must not contain `$`. Stripping
in the parser keeps `YnabTxn` construction clean and `_dollars_to_cents` as a
belt-and-suspenders defence.

---

## Decision 5: `lines_failed` Representation

**Decision**: For rows with wrong column count, store `','.join(row)`. For rows
where float parsing fails on the amount column(s), store `','.join(row)`. For rows
where `csv.reader` itself raises `csv.Error`, store the raw line string.

**Rationale**: This preserves the `List[str]` type for `lines_failed` and makes
failures inspectable. The original regex implementation stored the raw line string;
the `','.join(row)` form is equivalent for well-formed rows.

---

## Decision 6: Removing `CH_REGEX` — Impact on Existing Tests

**Decision**: The four `test_ch_regex_*` tests in `tests/test_file_in.py` test
`CH_REGEX` directly. Since `CH_REGEX` is removed in this feature, those tests
must be removed and replaced with the 8 new reader-based tests specified in
FR-013. This is an intentional breaking change to the test file.

**Rationale**: The regex tests tested an implementation detail, not a behaviour.
The replacement tests verify the same observable outcomes (correct `amt_cents`,
correct `lines_failed`) through the public function interface.

---

## Decision 7: Known Constitution Violation — graph.py Breakage

**Decision**: Removing `read_gb_txns` from `file_in.py` (FR-011) will break
`graph.py`, which imports it at the top level. Same acknowledged violation as
documented in feature 003. Updating `graph.py` remains deferred to a follow-up
feature.

**Mitigation**: Documented in Assumptions (spec.md) and Complexity Tracking (plan.md).
