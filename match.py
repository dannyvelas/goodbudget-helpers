from datetime import datetime as dt
from enum import Enum
from operator import attrgetter
from pathlib import Path
from re import Pattern
import re
from typing import Dict, List, Tuple, Union

##### CHASE ##################################################################
IN_CH_FILE = './in/chase.csv'
CH_START_BAL = 362335

# COLUMNS =      debit/credit                  date                        title              amt                      type    balance
CH_REGEX_STR = r'(?P<deb_or_cred>DEBIT|CREDIT),(?P<date>\d\d\/\d\d\/\d{4}),(?P<title>"[^"]+"),(?P<amt>-?\d{1,4}\.\d\d),[A-Z_]+,(?P<balance>-?\d{1,5}.\d\d| ),,'
CH_REGEX = re.compile(CH_REGEX_STR)
##############################################################################

##### GOODBUDGET #############################################################
IN_GB_FILE = './in/goodbudget.csv'
GB_START_BAL = 0

# COLUMNS =        date                        envelope                                        account         title                                notes                     amt                                         status details
GB_REGEX_STR = r"""(?P<date>\d\d\/\d\d\/\d{4}),(?P<envelope>"[^"]+"|[A-Za-z]*|\[Unallocated\]),"Chase Account",(?P<title>"[^"]+"|[A-Za-z0-9\.'’-]+),("[^"]+"|[A-Za-z\.'’-]*),,(?P<amt>-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?"""
GB_REGEX = re.compile(GB_REGEX_STR)
##############################################################################


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


class OrganizedTxns:
    def __init__(self, ch_txns: List[ChaseTxn], gb_txns: List[GoodbudgetTxn], both_txns: List[MergedTxn], merged_txns: List[MergedTxn]):
        self.ch_txns = ch_txns
        self.gb_txns = gb_txns
        self.both_txns = both_txns
        self.merged_txns = merged_txns


def read_txns(file_name: str, regex: Pattern[str], txn_type: TxnType):
    txns = []
    with open(file_name) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := regex.match(line)) and (txn := txn.groupdict()):
                txn_title = txn['title']
                txn_title = re.sub(r',', '', txn_title)
                txn_title = re.sub(r'\s+', ' ', txn_title)
                txn_title = txn_title[0:26]
                if ' ' in txn_title and txn_title[-1] != '"':
                    txn_title += '"'

                if txn_type == TxnType.CHASE:
                    new_txn = ChaseTxn(**{
                        '_ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                        '_is_debit': txn['deb_or_cred'] == 'DEBIT',
                        '_is_pending': txn['balance'] == ' ',
                        'date': txn['date'],
                        'title':  txn_title,
                        'amt': int(txn['amt'].replace('"', '').replace(",", '').replace(".", ''))
                    })
                else:
                    new_txn = GoodbudgetTxn(**{
                        '_ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                        'date': txn['date'],
                        'title':  txn_title,
                        'envelope': txn['envelope'],
                        'amt': int(txn['amt'].replace('"', '').replace(",", '').replace(".", ''))
                    })

                txns.append(new_txn)
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns


def txns_to_file(file_name: str, txns: Union[List[ChaseTxn], List[GoodbudgetTxn], List[MergedTxn]]):
    with open(file_name, 'w') as out_file:
        for txn in txns:
            out_file.write(f"{txn.to_row()}\n")


def organize_txns(out_dir: str = './out/merged'):
    ##### OUTPUT #################################################################
    Path(out_dir).mkdir(exist_ok=True)

    merged_file = f'{out_dir}/merged.csv'
    out_ch_file = f'{out_dir}/chase.csv'
    out_gb_file = f'{out_dir}/goodbudget.csv'
    both_file = f'{out_dir}/both.csv'
    bal_freq_file = f'{out_dir}/bal_freq.csv'
    ##############################################################################

    # read
    ch_txns: List[ChaseTxn] = read_txns(IN_CH_FILE, CH_REGEX, TxnType.CHASE)
    gb_txns: List[GoodbudgetTxn] = read_txns(
        IN_GB_FILE, GB_REGEX, TxnType.GOODBUDGET)

    # sort by amount
    ch_txns = sorted(ch_txns, key=attrgetter('amt', '_ts', 'title'))
    gb_txns = sorted(gb_txns, key=attrgetter('amt', '_ts', 'title'))

    # merge chase txns and gb txns
    merged_txns: List[MergedTxn] = []
    ch_i, gb_i = 0, 0
    while ch_i < len(ch_txns) or gb_i < len(gb_txns):
        ch_txn = ch_txns[ch_i] if ch_i < len(ch_txns) else None
        gb_txn = gb_txns[gb_i] if gb_i < len(gb_txns) else None

        days_apart = ((gb_txn._ts - ch_txn._ts) / (60 * 60 * 24)) \
            if ch_txn and gb_txn else None

        if (ch_txn and gb_txn and ch_txn.amt < gb_txn.amt) or (ch_txn and gb_txn is None):
            merged_txns.append(MergedTxn(ch_txn))
            ch_i += 1
        elif (ch_txn and gb_txn and ch_txn.amt > gb_txn.amt) or (gb_txn and ch_txn is None):
            merged_txns.append(MergedTxn(gb_txn))
            gb_i += 1
        else:
            assert ch_txn and gb_txn and days_apart is not None and ch_txn.amt == gb_txn.amt
            if days_apart < -7:
                # if gb too far in past, add it by itself
                merged_txns.append(MergedTxn(gb_txn))
                gb_i += 1
            elif days_apart > 7:
                # if ch too far in past, add it by itself
                merged_txns.append(MergedTxn(ch_txn))
                ch_i += 1
            else:
                merged_txns.append(MergedTxn(ch_txn, gb_txn))
                ch_i += 1
                gb_i += 1

    # sort by date and title
    merged_txns = sorted(merged_txns, key=lambda x: x.to_ts_and_title_tuple())

    # set SingleTxn.bal and MergedTxn.bal_diff
    bal_diff_freq: Dict[int, int] = {}
    ch_bal, gb_bal = CH_START_BAL, GB_START_BAL
    for merged_txn in merged_txns:
        if merged_txn.type_ in [TxnType.CHASE, TxnType.BOTH]:
            ch_bal += merged_txn.ch_txn.amt
            merged_txn.ch_txn.bal = ch_bal
        if merged_txn.type_ in [TxnType.GOODBUDGET, TxnType.BOTH]:
            gb_bal += merged_txn.gb_txn.amt
            merged_txn.gb_txn.bal = gb_bal

        # NEGATIVE: CHASE IS LOWER THAN GOODBUDGET
        # POSITIVE: CHASE IS HIGHER THAN GOODBUDGET
        diff = ch_bal - gb_bal
        if diff in bal_diff_freq:
            bal_diff_freq[diff] += 1
        else:
            bal_diff_freq[diff] = 1

        merged_txn.bal_diff = diff

    # sort by balance differences that occur the most
    bal_diff_freq = dict(sorted(bal_diff_freq.items(),
                                key=lambda item: item[1], reverse=True))

    # split merged_txns into 3 different lists
    ch_txns: List[ChaseTxn] = []
    gb_txns: List[GoodbudgetTxn] = []
    both_txns: List[MergedTxn] = []
    for txn in merged_txns:
        if txn.type_ == TxnType.CHASE:
            ch_txns.append(txn.ch_txn)
        elif txn.type_ == TxnType.GOODBUDGET:
            gb_txns.append(txn.gb_txn)
        else:
            both_txns.append(txn)

    # print each list to a file
    txns_to_file(merged_file, merged_txns)
    txns_to_file(out_ch_file, ch_txns)
    txns_to_file(out_gb_file, gb_txns)
    txns_to_file(both_file, both_txns)

    # print the sorted balance differences
    with open(bal_freq_file, 'w') as out_file:
        for key, value in bal_diff_freq.items():
            out_file.write(f'{key / 100}, {value}\n')

    # print some helpful numbers
    print(f'AMT OF UNMATCHED CHASE TXNS: {len(ch_txns)}')
    print(f'AMT OF UNMATCHED GOODBUDGET TXNS: {len(gb_txns)}')
    print(f'AMT OF MATCHED TXNS: {len(both_txns)}\n')

    return OrganizedTxns(ch_txns=ch_txns, gb_txns=gb_txns, both_txns=both_txns, merged_txns=merged_txns)
