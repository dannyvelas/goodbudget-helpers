from datetime import datetime as dt
import re
from typing import Generic, List, TypeVar

from datatypes import ChaseTxn, YnabTxn
from regex import CH_REGEX, YNAB_REGEX

IN_CH_FILE = './in/chase.csv'
IN_YNAB_FILE = './in/ynab.csv'


def _shorten(s: str) -> str:
    s = re.sub(r',', '', s)
    s = re.sub(r'\s+', ' ', s)
    s = s[0:26]
    if ' ' in s and s[-1] != '"':
        s += '"'

    return s


T = TypeVar('T', ChaseTxn, YnabTxn)


class ReadResults(Generic[T]):
    def __init__(self, txns: List[T], lines_failed: List[str]):
        self.txns = txns
        self.lines_failed = lines_failed


def read_ch_txns(ch_start_bal: int) -> ReadResults[ChaseTxn]:
    txns: List[ChaseTxn] = []
    lines_failed: List[str] = []
    with open(IN_CH_FILE) as in_file:
        for i, line in enumerate(in_file):
            if i == 0:
                continue
            if (txn := CH_REGEX.match(line)):
                txn = txn.groupdict()
                txns.append(ChaseTxn(
                    id_=i,
                    ts=int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    is_debit=float(txn['amt']) < 0,
                    is_pending=False,
                    date=txn['date'],
                    title=_shorten(txn['description']),
                    amt_dollars=txn['amt']
                ))
            else:
                lines_failed.append(line)

    curr_bal = ch_start_bal
    for txn in reversed(txns):
        curr_bal += txn.amt_cents
        txn.bal = curr_bal

    return ReadResults(txns, lines_failed)


def read_ynab_txns(ynab_start_bal: int) -> ReadResults[YnabTxn]:
    txns: List[YnabTxn] = []
    lines_failed: List[str] = []
    with open(IN_YNAB_FILE, encoding='utf-8-sig') as in_file:
        for i, line in enumerate(in_file):
            if i == 0:
                continue
            if (txn := YNAB_REGEX.match(line)):
                txn = txn.groupdict()
                outflow_val = float(txn['outflow'])
                inflow_val = float(txn['inflow'])
                if outflow_val > 0.0:
                    amt_dollars = f"-{txn['outflow']}"
                elif inflow_val > 0.0:
                    amt_dollars = txn['inflow']
                else:
                    amt_dollars = '0.00'
                txns.append(YnabTxn(
                    id_=i,
                    ts=int(dt.strptime(txn['date'], "%m/%d/%Y").timestamp()),
                    date=txn['date'],
                    title=_shorten(txn['payee']),
                    category=txn['category'],
                    amt_dollars=amt_dollars,
                    cleared=txn['cleared']
                ))
            else:
                lines_failed.append(line)

    curr_bal = ynab_start_bal
    for txn in reversed(txns):
        curr_bal += txn.amt_cents
        txn.bal = curr_bal

    return ReadResults(txns, lines_failed)
