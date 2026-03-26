import csv
from datetime import datetime as dt
import re
from typing import Generic, List, TypeVar

from datatypes import ChaseTxn, YnabTxn

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
        for i, row in enumerate(csv.reader(in_file)):
            if i == 0:
                continue
            if len(row) == 7:
                try:
                    amt = float(row[5])
                except ValueError:
                    lines_failed.append(','.join(row))
                    continue
                txns.append(ChaseTxn(
                    id_=i,
                    ts=int(dt.strptime(row[0], "%m/%d/%Y").timestamp()),
                    is_debit=amt < 0,
                    is_pending=False,
                    date=row[0],
                    title=_shorten(row[2]),
                    amt_dollars=row[5]
                ))
            else:
                lines_failed.append(','.join(row))

    curr_bal = ch_start_bal
    for txn in reversed(txns):
        curr_bal += txn.amt_cents
        txn.bal = curr_bal

    return ReadResults(txns, lines_failed)


def read_ynab_txns(ynab_start_bal: int) -> ReadResults[YnabTxn]:
    txns: List[YnabTxn] = []
    lines_failed: List[str] = []
    with open(IN_YNAB_FILE, encoding='utf-8-sig') as in_file:
        for i, row in enumerate(csv.reader(in_file)):
            if i == 0:
                continue
            if len(row) == 11:
                try:
                    outflow_str = row[8].lstrip('$')
                    inflow_str = row[9].lstrip('$')
                    outflow_val = float(outflow_str)
                    inflow_val = float(inflow_str)
                except ValueError:
                    lines_failed.append(','.join(row))
                    continue
                if outflow_val > 0.0:
                    amt_dollars = f"-{outflow_str}"
                elif inflow_val > 0.0:
                    amt_dollars = inflow_str
                else:
                    amt_dollars = '0.00'
                txns.append(YnabTxn(
                    id_=i,
                    ts=int(dt.strptime(row[2], "%m/%d/%Y").timestamp()),
                    date=row[2],
                    title=_shorten(row[3]),
                    category=row[6],
                    amt_dollars=amt_dollars,
                    cleared=row[10]
                ))
            else:
                lines_failed.append(','.join(row))

    curr_bal = ynab_start_bal
    for txn in reversed(txns):
        curr_bal += txn.amt_cents
        txn.bal = curr_bal

    return ReadResults(txns, lines_failed)
