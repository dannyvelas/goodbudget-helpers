from operator import itemgetter
from datetime import datetime as dt
from typing import Tuple, List
import re

##### CHASE ##################################################################
CH_FILE = './in/chase.csv'

# INDEX =    1              2                   3         4                 5         6
# COLS =     debit/credit   date                title     amt               type      balance
CH_REGEX = r'(DEBIT|CREDIT),(\d\d\/\d\d\/\d{4}),("[^"]+"),(-?\d{1,4}\.\d\d),([A-Z_]+),(\d{1,4}.\d\d),,'

CH_DATE_TITLE_AMT_INDICES = (2, 3, 4)
##############################################################################

##### GOODBUDGET #############################################################
GB_FILE = './in/goodbudget.csv'

# INDEX =      1                   2                                   3                         4                       5
# COLS =       date                envelope            account         title                     notes                   amt
GB_REGEX = r"""(\d\d\/\d\d\/\d{4}),("[^"]+"|[A-Za-z]*),"Chase Account",("[^"]+"|[A-Za-z0-9'’-]+),("[^"]+"|[A-Za-z'’-]*),,(-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?"""

GB_DATE_TITLE_AMT_INDICES = (1, 3, 5)
##############################################################################

##### SORTED OUTPUT ##########################################################
CH_SORTED_FILE_NAME = './out/sorted/chase.csv'
GB_SORTED_FILE_NAME = './out/sorted/goodbudget.csv'
##############################################################################

##### MATCHED OUTPUT #########################################################
CH_ONLY_FILE_NAME = './out/matched/chase_only.csv'
GB_ONLY_FILE_NAME = './out/matched/goodbudget_only.csv'
MATCHED_FILE_NAME = './out/matched/matched.csv'
##############################################################################


def sort_txns(file_name: str, regex: str, indices: Tuple):
    txns = []
    with open(file_name) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (match := re.match(regex, line)):
                split = list(match.group(*indices))

                # [ date_ts, date, title, amt ]
                date_ts = dt.strptime(split[0], "%m/%d/%Y").timestamp()
                txn = [date_ts, *split]

                txn[2] = re.sub(r'\s+', ' ', txn[2])
                txn[3] = float(txn[3].replace('"', '').replace(",", ''))

                txns.append(txn)
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return sorted(txns, key=itemgetter(3, 0, 2))


def txns_to_file(file_name: str, txns: List):
    if len(txns) > 0:
        with open(file_name, 'w') as out_file:
            if isinstance(txns[0], list):
                for txn in txns:
                    out_file.write(f"{','.join(txn[1:])}\n")
            else:
                assert(isinstance(txns[0], tuple))
                for txn_pair in txns:
                    out_file.write(
                        f"{' | '.join([','.join(txn[1:]) for txn in txn_pair])}\n")


def cells_to_str(table: List[List]): return [
    [str(cell) for cell in row] for row in table]


##### SORT #############################
print('CHASE')
ch_sorted = sort_txns(CH_FILE, CH_REGEX, CH_DATE_TITLE_AMT_INDICES)
ch_sorted = cells_to_str(ch_sorted)
txns_to_file(CH_SORTED_FILE_NAME, ch_sorted)

print('GOODBUDGET')
gb_sorted = sort_txns(GB_FILE, GB_REGEX, GB_DATE_TITLE_AMT_INDICES)
gb_sorted = cells_to_str(gb_sorted)
txns_to_file(GB_SORTED_FILE_NAME, gb_sorted)

##### MATCH ############################
ch_only, gb_only, matched = [], [], []
ch_i, gb_i = 0, 0
while ch_i < len(ch_sorted) and gb_i < len(gb_sorted):
    ch_txn, gb_txn = ch_sorted[ch_i], gb_sorted[gb_i]
    ch_amt, gb_amt = float(ch_txn[3]), float(gb_txn[3])

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

while ch_i < len(ch_sorted):
    ch_only.append(ch_sorted[ch_i])
    ch_i += 1

while gb_i < len(gb_sorted):
    gb_only.append(gb_sorted[gb_i])
    gb_i += 1

# remove charges that were offset with a refund
charges_seen = {}
i = 0
while i < len(ch_only):
    txn = ch_only[i]
    amt = float(txn[3])

    if amt < 0:
        charges_seen[amt] = i
        i += 1
    elif amt > 0 and -amt in charges_seen and (not (should_del := input(f"Remove {ch_only[charges_seen[-amt]][1:]} and {ch_only[i][1:]}?: (yes) ")) or should_del.lower() in ['y', 'yes']):
        del ch_only[charges_seen[-amt]]
        del ch_only[i-1]
        i -= 1
    else:
        i += 1

ch_only = sorted(ch_only, key=lambda x: x[0])
gb_only = sorted(gb_only, key=lambda x: x[0])
matched = sorted(matched, key=lambda x: x[0][0])

txns_to_file(CH_ONLY_FILE_NAME, ch_only)
txns_to_file(GB_ONLY_FILE_NAME, gb_only)
txns_to_file(MATCHED_FILE_NAME, matched)
