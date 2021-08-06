from operator import attrgetter
from datetime import datetime as dt
from typing import Union, List, Dict
from re import Pattern
from enum import Enum
import re

##### CHASE ##################################################################
CH_FILE = './in/chase.csv'
CH_START_BAL = 362335

# INDEX = 1            2                         3                  4                        5         6
# COLS =  debit/credit date                      title              amt                      type      balance
CH_REGEX = re.compile(
    r'(DEBIT|CREDIT),(?P<date>\d\d\/\d\d\/\d{4}),(?P<title>"[^"]+"),(?P<amt>-?\d{1,4}\.\d\d),([A-Z_]+),(-?\d{1,4}.\d\d),,')
##############################################################################

##### GOODBUDGET #############################################################
GB_FILE = './in/goodbudget.csv'
GB_START_BAL = 0

# INDEX = 1                         2                                                   3                                  4                       5                                           6      7
# COLS =  date                      envelope                            account         title                              notes                   amt                                         status details
GB_REGEX = re.compile(
    r"""(?P<date>\d\d\/\d\d\/\d{4}),("[^"]+"|[A-Za-z]*|\[Unallocated\]),"Chase Account",(?P<title>"[^"]+"|[A-Za-z0-9'’-]+),("[^"]+"|[A-Za-z'’-]*),,(?P<amt>-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?""")
##############################################################################

##### SORTED OUTPUT ##########################################################
CH_SORTED_FILE = './out/sorted/chase.csv'
GB_SORTED_FILE = './out/sorted/goodbudget.csv'
##############################################################################

##### MATCHED OUTPUT #########################################################
MERGED_FILE = './out/merged/merged.csv'
CH_ONLY_FILE = './out/merged/chase_only.csv'
GB_ONLY_FILE = './out/merged/goodbudget_only.csv'
BOTH_ONLY_FILE = './out/merged/both_only.csv'
##############################################################################


class TxnType(Enum):
    CHASE = 'ch'
    GOODBUDGET = 'gb'
    BOTH = 'both'


class SingleTxn:
    def __init__(self, ts: int, date: str, title: str, amt: int):
        self.ts = ts
        self.date = date
        self.title = title
        self.amt = amt
        self.bal = -1

    def to_row(self) -> str:
        return ','.join([str(value) for key, value in vars(self).items() if key != 'ts'])


class MergedTxn:
    def __init__(self, txn_group: Dict[TxnType, SingleTxn]):
        if TxnType.CHASE in txn_group and TxnType.GOODBUDGET in txn_group:
            self.type_ = TxnType.BOTH
        else:
            self.type_ = list(txn_group)[0]

        if TxnType.CHASE in txn_group:
            self.ch_txn = txn_group[TxnType.CHASE]
        if TxnType.GOODBUDGET in txn_group:
            self.gb_txn = txn_group[TxnType.GOODBUDGET]

        self.special = False

    def get_ts(self) -> int:
        if self.type_ in [TxnType.BOTH, TxnType.CHASE]:
            return self.ch_txn.ts
        else:
            return self.gb_txn.ts

    def to_row(self) -> str:
        ch_row = self.ch_txn.to_row() \
            if hasattr(self, 'ch_txn') else ','.join(['' for _ in range(len(vars(self.gb_txn))-1)])
        gb_row = self.gb_txn.to_row() \
            if hasattr(self, 'gb_txn') else ','.join(['' for _ in range(len(vars(self.ch_txn))-1)])

        return ','.join([self.type_.name, ch_row, gb_row, str(self.special)])


def read_txns(file_name: str, regex: Pattern) -> List[SingleTxn]:
    txns: List[SingleTxn] = []
    with open(file_name) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := regex.match(line)) and (txn := txn.groupdict()):
                txn_amt = int(txn['amt']
                              .replace('"', '').replace(",", '').replace(".", ''))
                txns.append(SingleTxn(**{
                    'ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    'date': txn['date'],
                    'title':  re.sub(r'\s+', ' ', txn['title']),
                    'amt': txn_amt,
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
ch_txns: List[SingleTxn] = read_txns(CH_FILE, CH_REGEX)
gb_txns: List[SingleTxn] = read_txns(GB_FILE, GB_REGEX)

# sort by amount
ch_txns = sorted(ch_txns, key=attrgetter('amt', 'ts', 'title'))
gb_txns = sorted(gb_txns, key=attrgetter('amt', 'ts', 'title'))

# print sorted txns to file for debugging
txns_to_file(CH_SORTED_FILE, ch_txns)
txns_to_file(GB_SORTED_FILE, gb_txns)

# merge chase txns and gb txns
merged_txns: List[MergedTxn] = []
ch_i, gb_i = 0, 0
while ch_i < len(ch_txns) or gb_i < len(gb_txns):
    ch_txn = ch_txns[ch_i] if ch_i < len(ch_txns) else None
    gb_txn = gb_txns[gb_i] if gb_i < len(gb_txns) else None

    ch_amt = ch_txn.amt if ch_txn else None
    gb_amt = gb_txn.amt if gb_txn else None

    amt_days_diff = ((gb_txn.ts - ch_txn.ts) / (60 * 60 * 24)) \
        if ch_txn and gb_txn else None

    merged_txn = {}
    if (ch_amt and gb_amt and ch_amt <= gb_amt) or (ch_amt and gb_amt is None):
        # add ch txn
        merged_txn[TxnType.CHASE] = ch_txn
        ch_i += 1
    if (ch_amt and gb_amt and ch_amt >= gb_amt) or (gb_amt and ch_amt is None):
        if not merged_txn or (amt_days_diff is not None and -7 < amt_days_diff < 7):
            # add either gb by itself or a match of within 7 days
            merged_txn[TxnType.GOODBUDGET] = gb_txn
            gb_i += 1

    merged_txns.append(MergedTxn(merged_txn))

# sort by date
merged_txns = sorted(merged_txns, key=lambda x: x.get_ts())

# set balances and mark when balances are equal to eachother
ch_bal, gb_bal = CH_START_BAL, GB_START_BAL
for merged_txn in merged_txns:
    if merged_txn.type_ in [TxnType.CHASE, TxnType.BOTH]:
        ch_bal += merged_txn.ch_txn.amt
        merged_txn.ch_txn.bal = ch_bal
    if merged_txn.type_ in [TxnType.GOODBUDGET, TxnType.BOTH]:
        gb_bal += merged_txn.gb_txn.amt
        merged_txn.gb_txn.bal = gb_bal
    if ch_bal == gb_bal:
        merged_txn.special = True

# print to files
txns_to_file(MERGED_FILE, merged_txns)
txns_to_file(CH_ONLY_FILE,
             [x for x in merged_txns if x.type_ == TxnType.CHASE])
txns_to_file(GB_ONLY_FILE,
             [x for x in merged_txns if x.type_ == TxnType.GOODBUDGET])
txns_to_file(BOTH_ONLY_FILE,
             [x for x in merged_txns if x.type_ == TxnType.BOTH])
