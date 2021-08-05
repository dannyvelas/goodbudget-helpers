from operator import itemgetter
from datetime import datetime as dt
from typing import List, Dict
from re import Pattern
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

# INDEX = 1                         2                                                               3                                  4                       5                                           6      7
# COLS =  date                      envelope                                        account         title                              notes                   amt                                         status details
GB_REGEX = re.compile(
    r"""(?P<date>\d\d\/\d\d\/\d{4}),(?P<envelope>"[^"]+"|[A-Za-z]*|\[Unallocated\]),"Chase Account",(?P<title>"[^"]+"|[A-Za-z0-9'’-]+),("[^"]+"|[A-Za-z'’-]*),,(?P<amt>-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?""")
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
                polished_txn = {
                    '_ts': dt.strptime(txn['date'], "%m/%d/%Y").timestamp(),
                    'date': txn['date'],
                    'title':  re.sub(r'\s+', ' ', txn['title']),
                    'amt': txn['amt'].replace('"', '').replace(",", ''),
                }
                if 'envelope' in txn:
                    polished_txn['envelope'] = txn['envelope']

                txns.append(polished_txn)
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns


def sort_txns(txns: List[Dict]):
    # make 'amt' a float to allow numeric sorting
    txns = [dict(txn, amt=float(txn['amt'])) for txn in txns]

    # sort
    txns = sorted(txns, key=itemgetter('amt', '_ts', 'title'))

    # make 'amt' a string again
    return [dict(txn, amt=str(txn['amt'])) for txn in txns]


def dict_vals(a_dict: Dict[str, str]) -> List[str]:
    return [value for key, value in a_dict.items() if key[0] != '_']


def txns_to_file(file_name: str, txns: List) -> None:
    if len(txns) > 0:
        with open(file_name, 'w') as out_file:
            if isinstance(txns[0], dict):
                for txn in txns:
                    out_file.write(f"{','.join(dict_vals(txn))}\n")
            else:
                assert(isinstance(txns[0], tuple))
                for txn_pair in txns:
                    out_file.write(
                        f"{','.join([','.join(dict_vals(txn)) for txn in txn_pair])}\n")


##### SORT #############################
print('CHASE')
ch_txns = read_txns(CH_FILE, CH_REGEX)
ch_txns = sort_txns(ch_txns)
txns_to_file(CH_SORTED_FILE, ch_txns)

print('GOODBUDGET')
gb_txns = read_txns(GB_FILE, GB_REGEX)
gb_txns = sort_txns(gb_txns)
txns_to_file(GB_SORTED_FILE, gb_txns)

##### MATCH ############################
ch_only, gb_only, matched = [], [], []
ch_i, gb_i = 0, 0
while ch_i < len(ch_txns) and gb_i < len(gb_txns):
    ch_txn, gb_txn = ch_txns[ch_i], gb_txns[gb_i]
    ch_amt, gb_amt = float(ch_txn['amt']), float(gb_txn['amt'])

    if ch_amt < gb_amt:
        ch_only.append(ch_txn)
        ch_i += 1
    elif ch_amt == gb_amt:
        matched.append((ch_txn, gb_txn))
        ch_i += 1
        gb_i += 1
    else:
        gb_only.append(gb_txn)
        gb_i += 1

while ch_i < len(ch_txns):
    ch_only.append(ch_txns[ch_i])
    ch_i += 1

while gb_i < len(gb_txns):
    gb_only.append(gb_txns[gb_i])
    gb_i += 1

assert(len(ch_only) + len(matched) == len(ch_txns))
assert(len(gb_only) + len(matched) == len(gb_txns))

# remove chase charges that were offset with a refund
charges_seen = {}
i = 0
while i < len(ch_only):
    txn = ch_only[i]
    amt = float(txn['amt'])

    if amt < 0:
        charges_seen[amt] = i
        i += 1
    elif amt > 0 and -amt in charges_seen and (not (should_del := input(f"Remove {dict_vals(ch_only[charges_seen[-amt]])} and {dict_vals(ch_only[i])}?: (yes) ")) or should_del.lower() in ['y', 'yes']):
        del ch_only[charges_seen[-amt]]
        del ch_only[i-1]
        i -= 1
    else:
        i += 1

# sort by date
ch_only = sorted(ch_only, key=lambda txn: txn['_ts'])
gb_only = sorted(gb_only, key=lambda txn: txn['_ts'])
matched = sorted(matched, key=lambda txn: txn[0]['_ts'])

# print to file
txns_to_file(CH_ONLY_FILE, ch_only)
txns_to_file(GB_ONLY_FILE, gb_only)
txns_to_file(MATCHED_FILE, matched)
