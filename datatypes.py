from enum import Enum
from typing import List, Tuple, Union


class TxnType(Enum):
    CHASE = 'ch'
    GOODBUDGET = 'gb'
    BOTH = 'both'


class SingleTxn:
    amt: int
    bal: int

    def to_dict(self):
        return {key: value for key, value in vars(self).items() if key[0] != '_'}

    def to_row(self) -> str:
        dollars_dict = dict(self.to_dict(), amt=self.amt/100, bal=self.bal/100)
        return ','.join([str(value) for value in dollars_dict.values()])


AMT_CH_FIELDS = 4


class ChaseTxn(SingleTxn):
    def __init__(self, _ts: int, _is_debit: bool, _is_pending: bool, date: str, title: str, amt: int):
        self._ts = _ts
        self._is_debit = _is_debit
        self._is_pending = _is_pending
        self.date = date
        self.title = title
        self.amt = amt
        self.bal = 0


AMT_GB_FIELDS = 5


class GoodbudgetTxn(SingleTxn):
    def __init__(self, _ts: int, date: str, title: str, envelope: str, amt: int):
        self._ts = _ts
        self.date = date
        self.title = title
        self.envelope = envelope
        self.amt = amt
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

    def to_ts_and_title_tuple(self) -> Union[Tuple[int, int, str, str], Tuple[int, int, str]]:
        if self.type_ == TxnType.BOTH:
            return (self.ch_txn._ts, self.gb_txn._ts, self.ch_txn.title, self.gb_txn.title)
        else:
            my_txn = self.ch_txn if self.type_ == TxnType.CHASE else self.gb_txn
            return (my_txn._ts, 0, my_txn.title)

    def to_row(self) -> str:
        if hasattr(self, 'ch_txn'):
            ch_row = self.ch_txn.to_row()
        else:
            ch_row = ',' * (AMT_CH_FIELDS - 1)

        if hasattr(self, 'gb_txn'):
            gb_row = self.gb_txn.to_row()
        else:
            gb_row = ',' * (AMT_GB_FIELDS - 1)

        return ','.join([self.type_.name, ch_row, gb_row, str(self.bal_diff / 100)])


class BalanceDifferenceFrequency:
    def __init__(self, vals: Tuple[int, int]):
        self.balance = vals[0]
        self.frequency = vals[1]

    def to_row(self) -> str:
        return f'{self.balance / 100}, {self.frequency}'


class OrganizedTxns:
    def __init__(self, only_ch_txns: List[ChaseTxn], only_gb_txns: List[GoodbudgetTxn], both_txns: List[MergedTxn], merged_txns: List[MergedTxn], bal_diff_freq: List[BalanceDifferenceFrequency]):
        self.only_ch_txns = only_ch_txns
        self.only_gb_txns = only_gb_txns
        self.both_txns = both_txns
        self.merged_txns = merged_txns
        self.bal_diff_freq = bal_diff_freq
