from typing import List, Union


class ChaseTxn:
    def __init__(self, id_: int, ts: int, is_debit: bool, is_pending: bool, date: str,
                 title: str, amt_dollars: str, amt_cents: int, bal: int):
        self.id_ = id_
        self.ts = ts
        self.is_debit = is_debit
        self.is_pending = is_pending
        self.date = date
        self.title = title
        self.amt_dollars = amt_dollars
        self.amt_cents = amt_cents
        self.bal = bal


class GoodbudgetTxn:
    def __init__(self, id_: int, ts: int, date: str, title: str, envelope: str,
                 amt_dollars: str, amt_cents: int, notes: str, bal: int):
        self.id_ = id_
        self.ts = ts
        self.date = date
        self.title = title
        self.envelope = envelope
        self.amt_dollars = amt_dollars
        self.amt_cents = amt_cents
        self.notes = notes
        self.bal = bal


class MergedTxn_ChaseTxn:
    def __init__(self, ch_txn: ChaseTxn):
        self.ch_txn = ch_txn
        self.bal_diff = 0


class MergedTxn_GoodbudgetTxn:
    def __init__(self, gb_txn: GoodbudgetTxn):
        self.gb_txn = gb_txn
        self.bal_diff = 0


class MergedTxn_BothTxns:
    def __init__(self, ch_txn: ChaseTxn, gb_txn: GoodbudgetTxn):
        self.ch_txn = ch_txn
        self.gb_txn = gb_txn
        self.bal_diff = 0


MergedTxn = Union[MergedTxn_ChaseTxn,
                  MergedTxn_GoodbudgetTxn, MergedTxn_BothTxns]


class BalanceDifferenceFrequency:
    def __init__(self, balance: int, frequency: int):
        self.balance = balance
        self.frequency = frequency


class TxnsGrouped:
    def __init__(self, only_ch_txns: List[ChaseTxn], only_gb_txns: List[GoodbudgetTxn],
                 both_txns: List[MergedTxn_BothTxns], merged_txns: List[MergedTxn],
                 bal_diff_freq: List[BalanceDifferenceFrequency]):
        self.only_ch_txns = only_ch_txns
        self.only_gb_txns = only_gb_txns
        self.both_txns = both_txns
        self.merged_txns = merged_txns
        self.bal_diff_freq = bal_diff_freq
