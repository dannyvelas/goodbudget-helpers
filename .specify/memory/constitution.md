<!--
SYNC IMPACT REPORT
==================
Version change: (none) → 1.0.0  (initial ratification)
Modified principles: N/A — first edition
Added sections:
  - Core Principles (5 principles)
  - Module Scope & Boundaries
  - Development Workflow
  - Governance
Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (Constitution Check section present)
  - .specify/templates/spec-template.md ✅ aligned (no constitution-specific constraints conflict)
  - .specify/templates/tasks-template.md ✅ aligned (pytest task paths match ./tests/ convention)
Deferred TODOs: none
-->

# Goodbudget Helpers Constitution

## Core Principles

### I. Importable Core (NON-NEGOTIABLE)

Functions in `file_in.py`, `match.py`, and `datatypes.py` MUST be directly importable and
callable without going through `main.py`. No pipeline logic may be baked into the entrypoint
such that core functionality is inaccessible from outside it.

**Rationale**: Testability and reuse require that the business logic layer be a proper library,
not a side effect of running the CLI entrypoint. This also allows the bot-adding module
(`add_new_txns.py`) and graphing module (`graph.py`) to import shared types safely.

**Gate**: Any function that reads transactions, parses CSV, or performs matching MUST be callable
in isolation: `from file_in import <fn>` and `from match import <fn>` MUST work without
importing `main`.

### II. Cents-Only Monetary Arithmetic (NON-NEGOTIABLE)

All monetary amounts MUST be stored and passed as integers denominated in cents.
Floating-point representations of dollars MUST NOT be used for storage or arithmetic.

- Negative value = expense / debit (money leaving the account).
- Positive value = income / credit (money entering the account).
- For a credit card account, the running balance is typically negative (amount owed).

**Rationale**: Floating-point dollar arithmetic introduces rounding errors that cause incorrect
balance reconciliation — the core purpose of the organizing module.

### III. Pytest-First Testing

All tests MUST live in `./tests/` and MUST be runnable with:

```
python3 -m pytest
```

from the repository root without additional arguments or setup steps (beyond the project's
normal virtual environment).

Every task that introduces or changes observable behavior MUST include corresponding tests in
`./tests/`. Tests MUST be written before implementation (red → green → refactor).

**Rationale**: Automated regression coverage is essential for a reconciliation tool; an
undetected off-by-one error in balance math can silently corrupt financial records.

### IV. Scope Isolation

The **in-scope** files for the transaction organizing module are:
`datatypes.py`, `regex.py`, `file_in.py`, `match.py`, `file_out.py`, `config.py`, `main.py`.

The **out-of-scope** files (`graph.py`, `add_new_txns.py`) MUST NOT be broken by changes to
in-scope files. They do not need to be updated, but any refactor of shared datatypes or imports
MUST verify that out-of-scope modules still import and run without errors.

**Rationale**: The graphing and bot-adding modules are production utilities; breaking them
silently is unacceptable even when they are not the focus of a feature.

### V. Simplicity

Prefer the simplest implementation that satisfies the current requirement. Do not introduce
abstractions, helpers, or generalization for hypothetical future needs (YAGNI). Three concrete
lines are better than a premature utility function.

Complexity MUST be justified in the plan's Complexity Tracking table when a violation is
necessary.

**Rationale**: This is a personal-use Python tool; maintainability for a solo developer is best
served by readable, minimal code rather than extensible architecture.

## Module Scope & Boundaries

### In-Scope Module Responsibilities

| File | Responsibility |
|---|---|
| `datatypes.py` | Data classes for `ChaseTxn`, `GoodbudgetTxn`, `MergedTxn*`, `TxnsGrouped`, and helpers |
| `regex.py` | All regular expressions used for CSV parsing and title normalization |
| `file_in.py` | Reading and parsing Chase and Goodbudget CSV input files into typed objects |
| `match.py` | Matching Chase transactions to Goodbudget transactions; grouping logic |
| `file_out.py` | Writing output CSV files (`both.csv`, `chase.csv`, `goodbudget.csv`, `merged.csv`) |
| `config.py` | Configuration constants (input/output paths, file names, thresholds) |
| `main.py` | CLI entrypoint only — orchestrates calls to the above; contains no business logic |

### Boundary Rules

- `main.py` MUST contain orchestration only; business logic belongs in the modules above.
- `config.py` values MAY be imported by any in-scope module.
- `datatypes.py` MUST NOT import from any other in-scope module (no circular deps).
- `regex.py` MUST NOT import from `file_in.py`, `match.py`, or `file_out.py`.

## Development Workflow

### Test Execution

```bash
python3 -m pytest          # run all tests
python3 -m pytest tests/   # explicit path (equivalent)
```

Tests MUST pass before any PR or commit is considered complete.

### Input / Output Conventions

- Input files: `in/chase.csv` and `in/goodbudget.csv` (paths configurable via `config.py`).
- Output directory: `out/<timestamp>/` containing `both.csv`, `chase.csv`, `goodbudget.csv`,
  `merged.csv`.
- All CSV amounts are parsed into cents immediately upon ingestion in `file_in.py`; dollar
  string representations are retained only for display/output.

### Out-of-Scope Module Safety Check

Before merging any change that touches `datatypes.py` or `config.py`, verify:

```bash
python3 -c "import graph; import add_new_txns"
```

No `ImportError` or `AttributeError` MUST be raised.

## Governance

This constitution supersedes all ad-hoc conventions and informal agreements about the
transaction organizing module. When in conflict, this document is authoritative.

**Amendment procedure**:
1. Propose the amendment with a rationale referencing a concrete need.
2. Update `constitution.md` and increment the version per the policy below.
3. Run the consistency propagation checklist (plan/spec/tasks templates).
4. Commit with message: `docs: amend constitution to vX.Y.Z (<summary>)`.

**Versioning policy**:
- MAJOR: Removal or backward-incompatible redefinition of a principle.
- MINOR: New principle or section added, or materially expanded guidance.
- PATCH: Clarifications, wording fixes, or non-semantic refinements.

**Compliance review**: Every implementation plan (`plan.md`) MUST include a Constitution Check
section that gates Phase 0 research and is re-checked after Phase 1 design.

**Version**: 1.0.0 | **Ratified**: 2026-03-26 | **Last Amended**: 2026-03-26
