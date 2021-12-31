from datetime import datetime as dt
import re
from typing import Generic, List, TypeVar

from datatypes import ChaseTxn, GoodbudgetTxn
from regex import CH_REGEX, GB_EXPENSE_REGEX, GB_INCOME_REGEX

IN_CH_FILE = './in/chase.csv'
IN_GB_FILE = './in/goodbudget.csv'


def _shorten(s: str) -> str:
    s = re.sub(r',', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = s[0:26]
    if ' ' in s and s[-1] != '"':
        s += '"'

    return s


T = TypeVar('T', ChaseTxn, GoodbudgetTxn)


class ReadResults(Generic[T]):
    def __init__(self, txns: List[T], lines_failed: List[str]):
        self.txns = txns
        self.lines_failed = lines_failed


def read_ch_txns() -> ReadResults[ChaseTxn]:
    txns: List[ChaseTxn] = []
    lines_failed: List[str] = []
    with open(IN_CH_FILE) as in_file:
        for line in in_file:
            if (txn := CH_REGEX.match(line)):
                txn = txn.groupdict()
                txns.append(ChaseTxn(
                    ts=int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    is_debit=txn['deb_or_cred'] == 'DEBIT',
                    is_pending=txn['balance'] == ' ',
                    date=txn['date'],
                    title=_shorten(txn['title']),
                    amt_dollars=txn['amt']
                ))
            else:
                lines_failed.append(line)

    return ReadResults(txns, lines_failed)


def read_gb_txns() -> ReadResults[GoodbudgetTxn]:
    txns: List[GoodbudgetTxn] = []
    lines_failed: List[str] = []
    with open(IN_GB_FILE) as in_file:
        for line in in_file:
            if (txn := GB_EXPENSE_REGEX.match(line)) or (txn := GB_INCOME_REGEX.match(line)):
                txn = txn.groupdict()
                txns.append(GoodbudgetTxn(
                    ts=int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    date=txn['date'],
                    title=_shorten(txn['title']),
                    envelope=txn['envelope'],
                    amt_dollars=txn['amt'],
                    notes=txn['notes']
                ))
            else:
                lines_failed.append(line)

    return ReadResults(txns, lines_failed)
