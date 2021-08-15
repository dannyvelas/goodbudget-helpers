from operator import attrgetter
from datetime import datetime as dt
from typing import Union, List, Dict, Tuple
from re import Pattern
from enum import Enum
from pathlib import Path
import re
import sys

##### CHASE ##################################################################
CH_FILE = './in/chase.csv'
CH_START_BAL = 362335

# COLUMNS =  debit/credit   date                        title              amt                      type      balance
CH_REGEX = r'(DEBIT|CREDIT),(?P<date>\d\d\/\d\d\/\d{4}),(?P<title>"[^"]+"),(?P<amt>-?\d{1,4}\.\d\d),([A-Z_]+),(-?\d{1,4}.\d\d),,'
CH_REGEX = re.compile(CH_REGEX)
##############################################################################

##### GOODBUDGET #############################################################
GB_FILE = './in/goodbudget.csv'
GB_START_BAL = 0

# COLUMNS =    date                        envelope                            account         title                              notes                   amt                                         status details
GB_REGEX = r"""(?P<date>\d\d\/\d\d\/\d{4}),("[^"]+"|[A-Za-z]*|\[Unallocated\]),"Chase Account",(?P<title>"[^"]+"|[A-Za-z0-9'’-]+),("[^"]+"|[A-Za-z'’-]*),,(?P<amt>-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?"""
GB_REGEX = re.compile(GB_REGEX)
##############################################################################

##### SORTED OUTPUT ##########################################################
CH_SORTED_FILE = './out/sorted/chase.csv'
GB_SORTED_FILE = './out/sorted/goodbudget.csv'
##############################################################################

##### OUTPUT #################################################################
OUT_DIR = sys.argv[2] \
    if len(sys.argv) > 2 and sys.argv[1] == '--dir' else './out/merged/'

Path(OUT_DIR).mkdir(exist_ok=True)

MERGED_FILE = f'{OUT_DIR}/merged.csv'
CH_ONLY_FILE = f'{OUT_DIR}/chase_only.csv'
GB_ONLY_FILE = f'{OUT_DIR}/goodbudget_only.csv'
BOTH_ONLY_FILE = f'{OUT_DIR}/both_only.csv'
BAL_FREQ_FILE = f'{OUT_DIR}/bal_freq.csv'
##############################################################################


class TxnType(Enum):
    CHASE = 'ch'
    GOODBUDGET = 'gb'
    BOTH = 'both'


class SingleTxn:
    def __init__(self, _type: TxnType, _ts: int, date: str, title: str, amt: int):
        self._type = _type
        self._ts = _ts
        self.date = date
        self.title = title
        self.amt = amt
        self.bal = 0

    def to_dict(self):
        return {key: value for key, value in vars(self).items() if key[0] != '_'}

    def to_row(self) -> str:
        dollars_dict = dict(self.to_dict(), amt=self.amt/100, bal=self.bal/100)
        return ','.join([str(value) for value in dollars_dict.values()])


class MergedTxn:
    def __init__(self, txn_1: SingleTxn, txn_2: SingleTxn = None):
        assert txn_2 is None or txn_1._type != txn_2._type

        self.type_ = TxnType.BOTH if txn_1 and txn_2 else txn_1._type

        for txn in [txn_1, txn_2]:
            if txn:
                if txn._type == TxnType.CHASE:
                    self.ch_txn: SingleTxn = txn
                elif txn._type == TxnType.GOODBUDGET:
                    self.gb_txn: SingleTxn = txn

        self.bal_diff = 0

    def to_ts_and_title_tuple(self) -> Union[Tuple[int, int, str, str], Tuple[int, int, str]]:
        if self.type_ == TxnType.BOTH:
            return (self.ch_txn._ts, self.gb_txn._ts, ch_txn.title, gb_txn.title)
        else:
            my_txn = self.ch_txn if self.type_ == TxnType.CHASE else self.gb_txn
            return (my_txn._ts, 0, my_txn.title)

    def to_row(self) -> str:
        ch_row = self.ch_txn.to_row() \
            if hasattr(self, 'ch_txn') else ',' * (len(self.gb_txn.to_dict())-1)
        gb_row = self.gb_txn.to_row() \
            if hasattr(self, 'gb_txn') else ',' * (len(self.ch_txn.to_dict())-1)

        return ','.join([self.type_.name, ch_row, gb_row, str(self.bal_diff / 100)])


def read_txns(file_name: str, regex: Pattern, txn_type: TxnType) -> List[SingleTxn]:
    txns: List[SingleTxn] = []
    with open(file_name) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := regex.match(line)) and (txn := txn.groupdict()):
                txns.append(SingleTxn(**{
                    '_type': txn_type,
                    '_ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    'date': txn['date'],
                    'title':  re.sub(r'\s+', ' ', txn['title']),
                    'amt': int(txn['amt'].replace('"', '').replace(",", '').replace(".", ''))
                }))
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns


def txns_to_file(file_name: str, txns: Union[List[SingleTxn], List[MergedTxn]]):
    with open(file_name, 'w') as out_file:
        for txn in txns:
            out_file.write(f"{txn.to_row()}\n")


# read
ch_txns: List[SingleTxn] = read_txns(CH_FILE, CH_REGEX, TxnType.CHASE)
gb_txns: List[SingleTxn] = read_txns(GB_FILE, GB_REGEX, TxnType.GOODBUDGET)

# sort by amount
ch_txns = sorted(ch_txns, key=attrgetter('amt', '_ts', 'title'))
gb_txns = sorted(gb_txns, key=attrgetter('amt', '_ts', 'title'))

# print sorted txns to file for debugging
txns_to_file(CH_SORTED_FILE, ch_txns)
txns_to_file(GB_SORTED_FILE, gb_txns)

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
        assert ch_txn and gb_txn and ch_txn.amt == gb_txn.amt
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

# remove ch_only txns that were never on gb bc they were offset by a refund
merged_txns_dict = dict(enumerate(merged_txns))
charges_seen: Dict[int, int] = {}
amt_removed = 0
i = 0
while i in merged_txns_dict:
    if merged_txns_dict[i].type_ == TxnType.CHASE:
        ch_txn = merged_txns_dict[i].ch_txn

        if ch_txn.amt < 0:
            charges_seen[ch_txn.amt] = i
        elif ch_txn.amt > 0 and -ch_txn.amt in charges_seen:
            neg_to_del = merged_txns_dict[charges_seen[-ch_txn.amt]].ch_txn
            should_del = input(
                f"Remove {neg_to_del.to_row()} and {ch_txn.to_row()}?: (yes) ")
            if not should_del or should_del.lower() in ['y', 'yes']:
                del merged_txns_dict[charges_seen[-ch_txn.amt]]
                del merged_txns_dict[i]
                del charges_seen[-ch_txn.amt]
                amt_removed += 2
    i += 1
print(f'\nAMT REMOVED: {amt_removed}')
merged_txns = list(merged_txns_dict.values())

# sort by date
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
only_ch_txns = [x.ch_txn for x in merged_txns if x.type_ == TxnType.CHASE]
only_gb_txns = [x.gb_txn for x in merged_txns if x.type_ == TxnType.GOODBUDGET]
only_both_txns = [x for x in merged_txns if x.type_ == TxnType.BOTH]

# print each list to a file
txns_to_file(MERGED_FILE, merged_txns)
txns_to_file(CH_ONLY_FILE, only_ch_txns)
txns_to_file(GB_ONLY_FILE, only_gb_txns)
txns_to_file(BOTH_ONLY_FILE, only_both_txns)

# print the sorted balance differences
with open(BAL_FREQ_FILE, 'w') as out_file:
    for key, value in bal_diff_freq.items():
        out_file.write(f'{key / 100}, {value}\n')

# print some helpful numbers
print(f'AMT OF UNMATCHED CHASE TXNS: {len(only_ch_txns)}')
print(f'AMT OF UNMATCHED GOODBUDGET TXNS: {len(only_gb_txns)}')
print(f'AMT OF MATCHED TXNS: {len(only_both_txns)}')
