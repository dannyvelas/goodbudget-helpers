from enum import Enum
from typing import List, Union


def _dollars_to_cents(dollars: str):
    return int(dollars
               .replace('"', '')
               .replace(",", '')
               .replace(".", ''))


class TxnType(Enum):
    CHASE = 'ch'
    GOODBUDGET = 'gb'
    BOTH = 'both'


class ChaseTxn:
    def __init__(self, id_: int, ts: int, is_debit: bool, is_pending: bool, date: str,
                 title: str, amt_dollars: str):
        self.id_ = id_
        self.ts = ts
        self.is_debit = is_debit
        self.is_pending = is_pending
        self.date = date
        self.title = title
        self.amt_dollars = amt_dollars
        self.amt_cents = _dollars_to_cents(amt_dollars)
        self.bal = 0


class GoodbudgetTxn:
    def __init__(self, id_: int, ts: int, date: str, title: str, envelope: str,
                 amt_dollars: str, notes: str):
        self.id_ = id_
        self.ts = ts
        self.date = date
        self.title = title
        self.envelope = envelope
        self.amt_dollars = amt_dollars
        self.amt_cents = _dollars_to_cents(amt_dollars)
        self.notes = notes
        self.bal = 0


class MergedTxn:
    def __init__(self, txn_1: Union[ChaseTxn, GoodbudgetTxn], txn_2: GoodbudgetTxn = None):
        if txn_1 and txn_2:
            assert(isinstance(txn_1, ChaseTxn))
            self.type_ = TxnType.BOTH
            self.ch_txn: ChaseTxn = txn_1
            self.gb_txn: GoodbudgetTxn = txn_2
        elif isinstance(txn_1, ChaseTxn):
            self.type_ = TxnType.CHASE
            self.ch_txn: ChaseTxn = txn_1
        else:
            assert isinstance(txn_1, GoodbudgetTxn)
            self.type_ = TxnType.GOODBUDGET
            self.gb_txn: GoodbudgetTxn = txn_1

        self.bal_diff = 0


class BalanceDifferenceFrequency:
    def __init__(self, balance: int, frequency: int):
        self.balance = balance
        self.frequency = frequency


class TxnsGrouped:
    def __init__(self, only_ch_txns: List[ChaseTxn], only_gb_txns: List[GoodbudgetTxn],
                 both_txns: List[MergedTxn], merged_txns: List[MergedTxn],
                 bal_diff_freq: List[BalanceDifferenceFrequency]):
        self.only_ch_txns = only_ch_txns
        self.only_gb_txns = only_gb_txns
        self.both_txns = both_txns
        self.merged_txns = merged_txns
        self.bal_diff_freq = bal_diff_freq
