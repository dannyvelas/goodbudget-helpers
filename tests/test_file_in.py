import tempfile
import os
from unittest.mock import patch

from file_in import read_ch_txns, IN_CH_FILE, read_ynab_txns, IN_YNAB_FILE


def test_read_ch_txns():
    csv_content = (
        'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'
        '01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,\n'
        '01/01/2025,01/02/2025,PAYMENT THANK YOU,Payment,Payment,500.00,\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_CH_FILE', tmp_path):
            result = read_ch_txns(ch_start_bal=-100000)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 2
    assert len(result.lines_failed) == 0

    amazon = next(t for t in result.txns if 'AMAZON' in t.title)
    assert amazon.amt_cents == -5000
    assert amazon.is_debit is True
    assert amazon.is_pending is False

    payment = next(t for t in result.txns if 'PAYMENT' in t.title)
    assert payment.amt_cents == 50000
    assert payment.is_debit is False


def test_read_ynab_txns():
    csv_content = (
        '"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"\n'
        '"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"\n'
        '"Chase Credit Card","","03/26/2026","Paycheck","Income: Salary","Income","Salary","",$0.00,$1000.00,"Cleared"\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_YNAB_FILE', tmp_path):
            result = read_ynab_txns(ynab_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 2
    assert len(result.lines_failed) == 0

    path_txn = next(t for t in result.txns if 'PATH' in t.title)
    assert path_txn.amt_cents == -300
    assert path_txn.category == 'Transportation'
    assert path_txn.cleared == 'Uncleared'

    paycheck = next(t for t in result.txns if 'Paycheck' in t.title)
    assert paycheck.amt_cents == 100000
    assert paycheck.cleared == 'Cleared'


def test_read_ch_txns_sale():
    csv_content = (
        'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'
        '01/05/2025,01/06/2025,AMAZON,Shopping,Sale,-50.00,\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_CH_FILE', tmp_path):
            result = read_ch_txns(ch_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 1
    assert len(result.lines_failed) == 0
    assert result.txns[0].amt_cents == -5000
    assert result.txns[0].is_debit is True
    assert result.txns[0].is_pending is False


def test_read_ch_txns_payment():
    csv_content = (
        'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'
        '01/15/2025,01/15/2025,PAYMENT THANK YOU,Payment,Payment,500.00,\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_CH_FILE', tmp_path):
            result = read_ch_txns(ch_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 1
    assert len(result.lines_failed) == 0
    assert result.txns[0].amt_cents == 50000
    assert result.txns[0].is_debit is False


def test_read_ch_txns_header_not_in_failed():
    csv_content = 'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_CH_FILE', tmp_path):
            result = read_ch_txns(ch_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.lines_failed) == 0


def test_read_ch_txns_malformed():
    csv_content = (
        'Transaction Date,Post Date,Description,Category,Type,Amount,Memo\n'
        'bad,data,row\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_CH_FILE', tmp_path):
            result = read_ch_txns(ch_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 0
    assert len(result.lines_failed) == 1


def test_read_ynab_txns_expense():
    csv_content = (
        '"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"\n'
        '"Chase Credit Card","","03/25/2026","PATH","Needs: Transportation","Needs","Transportation","",$3.00,$0.00,"Uncleared"\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_YNAB_FILE', tmp_path):
            result = read_ynab_txns(ynab_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 1
    assert len(result.lines_failed) == 0
    assert result.txns[0].amt_cents == -300
    assert result.txns[0].category == 'Transportation'
    assert result.txns[0].cleared == 'Uncleared'


def test_read_ynab_txns_income():
    csv_content = (
        '"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"\n'
        '"Chase Credit Card","","03/26/2026","Paycheck","Income: Salary","Income","Salary","",$0.00,$1000.00,"Cleared"\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_YNAB_FILE', tmp_path):
            result = read_ynab_txns(ynab_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 1
    assert len(result.lines_failed) == 0
    assert result.txns[0].amt_cents == 100000


def test_read_ynab_txns_header_not_in_failed():
    csv_content = '"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_YNAB_FILE', tmp_path):
            result = read_ynab_txns(ynab_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.lines_failed) == 0


def test_read_ynab_txns_malformed():
    csv_content = (
        '"Account","Flag","Date","Payee","Category Group/Category","Category Group","Category","Memo","Outflow","Inflow","Cleared"\n'
        'bad,data,row\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        tmp_path = f.name

    try:
        with patch('file_in.IN_YNAB_FILE', tmp_path):
            result = read_ynab_txns(ynab_start_bal=0)
    finally:
        os.unlink(tmp_path)

    assert len(result.txns) == 0
    assert len(result.lines_failed) == 1
