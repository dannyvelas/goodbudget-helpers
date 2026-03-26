# Data Model: Update main.py and config.py to Use YNAB Types

**Branch**: `007-main-config-ynab` | **Date**: 2026-03-26

## Modified Entities

### Config (`config.py`)

| Attribute | Type | Env Key | Before | After |
|-----------|------|---------|--------|-------|
| `ch_start_bal` | `int` (cents) | `CH_START_BAL` | unchanged | unchanged |
| `ynab_start_bal` | `int` (cents) | `YNAB_START_BAL` | ❌ did not exist (`gb_start_bal` used `GB_START_BAL`) | ✅ new |
| `gb_start_bal` | `int` (cents) | `GB_START_BAL` | ✅ existed | ❌ removed |
| `gb_username` | `str` | `GB_USERNAME` | ✅ existed | ❌ removed |
| `gb_password` | `str` | `GB_PASSWORD` | ✅ existed | ❌ removed |

**`.env` file shape after this feature**:
```
CH_START_BAL=<integer cents>
YNAB_START_BAL=<integer cents>
```
Both are integer cents. Negative = account balance is negative (credit card owed
amount). Example: `CH_START_BAL=-2984426` → -$29,844.26.

### main.py — Pipeline Shape

| Step | Before | After |
|------|--------|-------|
| Arg parsing | `--add` flag loop | Removed entirely |
| Config load | `Config(ENV)` with `GB_*` | `Config(ENV)` with `YNAB_*` |
| Read Chase | `read_ch_txns(config.ch_start_bal)` | Unchanged |
| Read YNAB | `read_gb_txns(config.gb_start_bal)` | `read_ynab_txns(config.ynab_start_bal)` |
| Match | `get_txns_grouped(ch, gb, ch_bal, gb_bal)` | `get_txns_grouped(ch, ynab, ch_bal, ynab_bal)` |
| Log lines_failed | `ch + gb` | `ch + ynab` |
| Log grouped | `log.txns_grouped(...)` | Unchanged |
| Print | `Saved to: {OUT_DIR}` | Unchanged |
| Bot step | `add_new_txns(...)` + pending print | Removed entirely |

## Existing Entities (unchanged)

All of `ChaseTxn`, `YnabTxn`, `TxnsGrouped`, `MergedTxn_*`, `ReadResults` are
used as-is. No changes to `datatypes.py`, `file_in.py`, `match.py`, or
`file_out.py`.

## Test Data Model (`tests/test_main.py`)

### `test_main_end_to_end` — temp directory layout

```text
<tmpdir>/
├── .env                  # CH_START_BAL=0\nYNAB_START_BAL=0
├── in/
│   ├── chase.csv         # 1 data row: AMAZON, -50.00, 01/05/2025
│   └── ynab.csv          # 1 data row: Amazon, $50.00 outflow, 01/05/2025
└── out/
    └── <timestamp>/      # created by Logger()
        ├── chase.csv
        ├── ynab.csv
        ├── both.csv      # must have exactly 1 data row
        ├── merged.csv
        ├── bal_diff_freq.csv
        └── log.txt       # must contain 'AMT OF MATCHED TXNS: 1'
```

### `test_main_no_env` — temp directory layout

```text
<tmpdir>/
├── in/
│   ├── chase.csv         # same as above
│   └── ynab.csv          # same as above
└── (no .env)
```

Expected: `returncode != 0`, `'no .env'` in combined stdout+stderr (lowercase).

## Modified Files

| File | Change |
|------|--------|
| `config.py` | Replace `gb_start_bal`/`GB_START_BAL` with `ynab_start_bal`/`YNAB_START_BAL`; remove `GB_USERNAME` and `GB_PASSWORD` blocks |
| `main.py` | Use `read_ynab_txns`, `config.ynab_start_bal`; remove `--add`, `add_new_txns`, pending-amounts block, `import sys` |
| `tests/test_main.py` | NEW — 2 subprocess integration tests |

## Unchanged Files

`datatypes.py`, `match.py`, `file_in.py`, `file_out.py`, `regex.py`,
`graph.py`, `add_new_txns.py` — untouched.
