from datatypes import _dollars_to_cents, YnabTxn


def test_dollars_to_cents_dollar_sign():
    assert _dollars_to_cents('$3.00') == 300


def test_dollars_to_cents_negative():
    assert _dollars_to_cents('-25.00') == -2500


def test_ynab_txn_outflow():
    txn = YnabTxn(id_=1, ts=1735689600, date='01/01/2025', title='Trader Joes',
                  category='Groceries', amt_dollars='-25.00', cleared='Cleared')
    assert txn.amt_cents == -2500
    assert txn.category == 'Groceries'
    assert txn.cleared == 'Cleared'
    assert txn.bal == 0


def test_ynab_txn_inflow():
    txn = YnabTxn(id_=2, ts=1736985600, date='01/16/2025', title='PAYMENT',
                  category='Payment', amt_dollars='500.00', cleared='Cleared')
    assert txn.amt_cents == 50000
