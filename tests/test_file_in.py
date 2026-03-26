import tempfile
import os
from unittest.mock import patch

from regex import CH_REGEX
from file_in import read_ch_txns, IN_CH_FILE


def test_ch_regex_sale():
    line = '01/01/2025,01/02/2025,TRADER JOES,Groceries,Sale,-25.00,'
    m = CH_REGEX.match(line)
    assert m is not None
    assert m['date'] == '01/01/2025'
    assert m['description'] == 'TRADER JOES'
    assert m['amt'] == '-25.00'


def test_ch_regex_payment():
    line = '01/15/2025,01/15/2025,PAYMENT THANK YOU,Payment,Payment,500.00,'
    m = CH_REGEX.match(line)
    assert m is not None
    assert m['date'] == '01/15/2025'
    assert m['description'] == 'PAYMENT THANK YOU'
    assert m['amt'] == '500.00'


def test_ch_regex_no_match_header():
    line = 'Transaction Date,Post Date,Description,Category,Type,Amount,Memo'
    assert CH_REGEX.match(line) is None


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
