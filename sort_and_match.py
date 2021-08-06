from operator import itemgetter
from datetime import datetime as dt
from typing import List, Dict
from re import Pattern
from enum import Enum
import re

##### CHASE ##################################################################
CH_FILE = './in/chase.csv'

# INDEX = 1            2                         3                  4                        5         6
# COLS =  debit/credit date                      title              amt                      type      balance
CH_REGEX = re.compile(
    r'(DEBIT|CREDIT),(?P<date>\d\d\/\d\d\/\d{4}),(?P<title>"[^"]+"),(?P<amt>-?\d{1,4}\.\d\d),([A-Z_]+),(-?\d{1,4}.\d\d),,')
##############################################################################

##### GOODBUDGET #############################################################
GB_FILE = './in/goodbudget.csv'

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
CH_ONLY_FILE = './out/matched/chase_only.csv'
GB_ONLY_FILE = './out/matched/goodbudget_only.csv'
MATCHED_FILE = './out/matched/matched.csv'
##############################################################################


def read_txns(file_name: str, regex: Pattern):
    txns = []
    with open(file_name) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := regex.match(line)) and (txn := txn.groupdict()):
                txns.append({
                    'ts': dt.strptime(txn['date'], "%m/%d/%Y").timestamp(),
                    'date': txn['date'],
                    'title':  re.sub(r'\s+', ' ', txn['title']),
                    'amt': txn['amt'].replace('"', '').replace(",", '').replace(".", '')
                })
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns


def sort_txns(txns: List[Dict]):
    # make 'amt' a int to allow numeric sorting
    txns = [dict(txn, amt=int(txn['amt'])) for txn in txns]

    # sort
    txns = sorted(txns, key=itemgetter('amt', 'ts', 'title'))

    # make 'amt' a string again
    return [dict(txn, amt=str(txn['amt'])) for txn in txns]


def dict_vals(a_dict: Dict[str, str]) -> List[str]:
    return [value for key, value in a_dict.items() if 'ts' not in key]


def txns_to_file(file_name: str, txns: List) -> None:
    with open(file_name, 'w') as out_file:
        for txn in txns:
            out_file.write(f"{','.join(dict_vals(txn))}\n")


class TxnType(Enum):
    CHASE = 'ch'
    GOODBUDGET = 'gb'
    BOTH = 'both'


MERGED_COLS = {
    'type': None,
    'ch_ts': -1.0,
    'ch_date': '',
    'ch_title': '',
    'ch_amt': '',
    'ch_bal': '',
    'gb_ts': -1.0,
    'gb_date': '',
    'gb_title': '',
    'gb_amt': '',
    'gb_bal': '',
    'special': False
}


def txn_to_row(txn_group: Dict[TxnType, Dict]):
    row = MERGED_COLS.copy()

    if TxnType.CHASE in txn_group and TxnType.GOODBUDGET in txn_group:
        row['type'] = TxnType.BOTH
    else:
        row['type'] = list(txn_group)[0]

    for txn_type, txn in txn_group.items():
        for key, value in txn.items():
            row[f'{txn_type.value}_{key}'] = value

    return row


def get_row_ts(row: Dict):
    if row['type'] in [TxnType.BOTH, TxnType.CHASE]:
        return row['ch_ts']
    else:
        return row['gb_ts']


# read
ch_txns = read_txns(CH_FILE, CH_REGEX)
gb_txns = read_txns(GB_FILE, GB_REGEX)

# sort
ch_txns = sort_txns(ch_txns)
gb_txns = sort_txns(gb_txns)

# print sorted txns to file for debugging
txns_to_file(CH_SORTED_FILE, ch_txns)
txns_to_file(GB_SORTED_FILE, gb_txns)

# merge chase txns to gb txns
merged_txns = []
ch_i, gb_i = 0, 0
while ch_i < len(ch_txns) or gb_i < len(gb_txns):
    ch_txn = ch_txns[ch_i] if ch_i < len(ch_txns) else None
    gb_txn = gb_txns[gb_i] if gb_i < len(gb_txns) else None

    ch_amt = int(ch_txn['amt']) if ch_txn else None
    gb_amt = int(gb_txn['amt']) if gb_txn else None

    amt_days_diff = ((int(gb_txn['ts']) - int(ch_txn['ts'])) / (60 * 60 * 24))  \
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

    merged_txns.append(txn_to_row(merged_txn))

# sort by date
merged_txns = sorted(merged_txns, key=get_row_ts)

# set balances
ch_bal, gb_bal = 362335, 0
for txn in merged_txns:
    if txn['type'] in [TxnType.CHASE, TxnType.BOTH]:
        ch_bal += int(txn['ch_amt'])
        txn['ch_bal'] = str(ch_bal)
    if txn['type'] in [TxnType.GOODBUDGET, TxnType.BOTH]:
        gb_bal += int(txn['gb_amt'])
        txn['gb_bal'] = str(gb_bal)
    if ch_bal == gb_bal:
        txn['special'] = True

# make 'type' and 'special' strings to allow printing to file
merged_txns = [dict(txn, type=txn['type'].name,
                    special=str(txn['special'])) for txn in merged_txns]

# print to file
txns_to_file(MATCHED_FILE, merged_txns)
