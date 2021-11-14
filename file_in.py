from datetime import datetime as dt
import re
from typing import List

from datatypes import ChaseTxn, GoodbudgetTxn

IN_CH_FILE = './in/chase.csv'
IN_GB_FILE = './in/goodbudget.csv'

# COLUMNS =      debit/credit                  date                        title              amt                      type    balance
CH_REGEX_STR = r'(?P<deb_or_cred>DEBIT|CREDIT),(?P<date>\d\d\/\d\d\/\d{4}),(?P<title>"[^"]+"),(?P<amt>-?\d{1,4}\.\d\d),[A-Z_]+,(?P<balance>-?\d{1,5}.\d\d| ),,'
CH_REGEX = re.compile(CH_REGEX_STR)

# COLUMNS =        date                        envelope                                        account         title                                notes                     amt                                         status details
GB_REGEX_STR = r"""(?P<date>\d\d\/\d\d\/\d{4}),(?P<envelope>"[^"]+"|[A-Za-z]*|\[Unallocated\]),"Chase Account",(?P<title>"[^"]+"|[A-Za-z0-9\.'’-]+),("[^"]+"|[A-Za-z\.'’-]*),,(?P<amt>-?\d{1,3}\.\d\d|"-?\d,\d{3}\.\d\d"),(CLR)?,(((\[Unallocated\]|[A-Za-z]+)\|-?\d{1,3}.\d\d)|("[^"]+"))?"""
GB_REGEX = re.compile(GB_REGEX_STR)


def _shorten(string: str) -> str:
    string = re.sub(r',', '', string)
    string = re.sub(r'\s+', ' ', string)
    string = string[0:26]
    if ' ' in string and string[-1] != '"':
        string += '"'

    return string


def read_ch_txns() -> List[ChaseTxn]:
    txns: List[ChaseTxn] = []
    with open(IN_CH_FILE) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := CH_REGEX.match(line)) and (txn := txn.groupdict()):
                txns.append(ChaseTxn(**{
                    '_ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    '_is_debit': txn['deb_or_cred'] == 'DEBIT',
                    '_is_pending': txn['balance'] == ' ',
                    'date': txn['date'],
                    'title':  _shorten(txn['title']),
                    'amt': int(txn['amt'].replace('"', '').replace(",", '').replace(".", ''))
                }))
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns


def read_gb_txns() -> List[GoodbudgetTxn]:
    txns: List[GoodbudgetTxn] = []
    with open(IN_GB_FILE) as in_file:
        amt_unmatched = 0
        for line in in_file:
            if (txn := GB_REGEX.match(line)) and (txn := txn.groupdict()):
                txns.append(GoodbudgetTxn(**{
                    '_ts': int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    'date': txn['date'],
                    'title':  _shorten(txn['title']),
                    'envelope': txn['envelope'],
                    'amt': int(txn['amt'].replace('"', '').replace(",", '').replace(".", ''))
                }))
            else:
                amt_unmatched += 1
                print(f'No match: {line}', end='')

    print(f"Didn't match {amt_unmatched} lines\n")

    return txns
