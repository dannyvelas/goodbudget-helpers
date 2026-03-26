from datatypes import ChaseTxn, YnabTxn
from match import get_txns_grouped


def test_match_both_txns():
    ch_txn = ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
                      date='01/01/2025', title='Amazon', amt_dollars='-25.00')
    ynab_txn = YnabTxn(id_=0, ts=1735689600, date='01/01/2025', title='Amazon',
                       category='Shopping', amt_dollars='-25.00', cleared='Cleared')

    result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)

    assert len(result.both_txns) == 1
    assert len(result.only_ch_txns) == 0
    assert len(result.only_ynab_txns) == 0


def test_match_only_ch_and_only_ynab():
    ch_txn = ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
                      date='01/01/2025', title='Amazon', amt_dollars='-25.00')
    ynab_txn = YnabTxn(id_=0, ts=1735689600, date='01/01/2025', title='Amazon',
                       category='Shopping', amt_dollars='-30.00', cleared='Cleared')

    result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)

    assert len(result.only_ch_txns) == 1
    assert len(result.only_ynab_txns) == 1
    assert len(result.both_txns) == 0


def test_match_outside_7_days():
    ch_txn = ChaseTxn(id_=0, ts=1735689600, is_debit=True, is_pending=False,
                      date='01/01/2025', title='Amazon', amt_dollars='-25.00')
    ynab_txn = YnabTxn(id_=0, ts=1736380800, date='01/09/2025', title='Amazon',
                       category='Shopping', amt_dollars='-25.00', cleared='Cleared')

    result = get_txns_grouped([ch_txn], [ynab_txn], 0, 0)

    assert len(result.both_txns) == 0
    assert len(result.only_ch_txns) == 1
    assert len(result.only_ynab_txns) == 1
