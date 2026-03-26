import subprocess
import sys
import tempfile
from pathlib import Path

MAIN_PY = Path(__file__).resolve().parent.parent / 'main.py'

CHASE_CSV = """\
Transaction Date,Post Date,Description,Category,Type,Amount,Memo
01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,
"""

YNAB_CSV = """\
"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"
"Chase Credit Card","","01/05/2025","Amazon","Wants: Shopping","Wants","Shopping","",$50.00,$0.00,"Cleared"
"""


def test_main_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / 'in').mkdir()
        (tmppath / 'in' / 'chase.csv').write_text(CHASE_CSV)
        (tmppath / 'in' / 'ynab.csv').write_text(YNAB_CSV)
        (tmppath / '.env').write_text('CH_START_BAL=0\nYNAB_START_BAL=0')

        result = subprocess.run(
            [sys.executable, str(MAIN_PY)],
            cwd=tmpdir, capture_output=True, text=True)

        assert result.returncode == 0, \
            f"Expected exit 0, got {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"

        out_dirs = list((tmppath / 'out').iterdir())
        assert len(out_dirs) >= 1, "Expected at least one directory under ./out/"
        out_dir = out_dirs[0]

        for fname in ('chase.csv', 'ynab.csv', 'both.csv', 'merged.csv',
                      'bal_diff_freq.csv', 'log.txt'):
            assert (out_dir / fname).exists(), f"Missing output file: {fname}"

        both_lines = (out_dir / 'both.csv').read_text().strip().splitlines()
        assert len(both_lines) == 2, \
            f"Expected 1 data row in both.csv (header + 1), got {len(both_lines)} lines"

        log_txt = (out_dir / 'log.txt').read_text()
        assert 'AMT OF MATCHED TXNS: 1' in log_txt, \
            f"'AMT OF MATCHED TXNS: 1' not found in log.txt:\n{log_txt}"


def test_main_no_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / 'in').mkdir()
        (tmppath / 'in' / 'chase.csv').write_text(CHASE_CSV)
        (tmppath / 'in' / 'ynab.csv').write_text(YNAB_CSV)

        result = subprocess.run(
            [sys.executable, str(MAIN_PY)],
            cwd=tmpdir, capture_output=True, text=True)

        assert result.returncode != 0, \
            f"Expected non-zero exit, got 0.\nstdout: {result.stdout}"
        combined = (result.stdout + result.stderr).lower()
        assert 'no .env' in combined, \
            f"'no .env' not found in output:\nstdout: {result.stdout}\nstderr: {result.stderr}"
