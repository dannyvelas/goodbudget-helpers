from datatypes import YnabTxn, MergedTxn_YnabTxn
from file_out import _ynab_txn_to_row, _merged_txn_to_row


def test_ynab_txn_to_row():
    txn = YnabTxn(id_=3, ts=1735689600, date='01/01/2025', title='Trader Joes',
                  category='Groceries', amt_dollars='-25.00', cleared='Cleared')
    txn.bal = 97500

    result = _ynab_txn_to_row(txn)

    assert result == '3,01/01/2025,Trader Joes,Groceries,-25.00,975.0'


def test_merged_txn_ynab_only_type_label():
    txn = YnabTxn(id_=3, ts=1735689600, date='01/01/2025', title='Trader Joes',
                  category='Groceries', amt_dollars='-25.00', cleared='Cleared')
    txn.bal = 97500
    merged_txn = MergedTxn_YnabTxn(txn)

    result = _merged_txn_to_row(merged_txn)

    assert result.startswith('YNAB,')
