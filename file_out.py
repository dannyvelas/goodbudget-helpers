from datetime import datetime as dt
from pathlib import Path
from typing import List

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    GoodbudgetTxn,
    MergedTxn,
    TxnsGrouped,
)


### Helper Values and Functions #########################################

_AMT_CH_FIELDS = 4


def _ch_txn_to_row(ch_txn: ChaseTxn):
    return f'{ch_txn.date},{ch_txn.title},{ch_txn.amt_dollars},{ch_txn.bal/100}'


_AMT_GB_FIELDS = 5


def _gb_txn_to_row(gb_txn: GoodbudgetTxn):
    return f'{gb_txn.date},{gb_txn.title},{gb_txn.envelope},{gb_txn.amt_dollars},{gb_txn.bal/100}'


def _merged_txn_to_row(merged_txn: MergedTxn):
    if hasattr(merged_txn, 'ch_txn'):
        ch_row = _ch_txn_to_row(merged_txn.ch_txn)
    else:
        ch_row = ',' * (_AMT_CH_FIELDS - 1)

    if hasattr(merged_txn, 'gb_txn'):
        gb_row = _gb_txn_to_row(merged_txn.gb_txn)
    else:
        gb_row = ',' * (_AMT_GB_FIELDS - 1)

    return ','.join([merged_txn.type_.name, ch_row, gb_row, str(merged_txn.bal_diff/100)])


def _bal_and_freq_to_row(bal_and_freq: BalanceDifferenceFrequency) -> str:
    return f'{bal_and_freq.balance/100},{bal_and_freq.frequency}'


### Export #############################################################

OUT_DIR = f'./out/{dt.now().strftime("%Y-%m-%dT%H:%M")}'


class Logger:
    def __init__(self):
        Path(OUT_DIR).mkdir(exist_ok=True)

        self.ch_file = f'{OUT_DIR}/chase.csv'
        self.gb_file = f'{OUT_DIR}/goodbudget.csv'
        self.both_file = f'{OUT_DIR}/both.csv'
        self.merged_file = f'{OUT_DIR}/merged.csv'
        self.bal_diff_freq_file = f'{OUT_DIR}/bal_diff_freq.csv'
        self.log_file = f'{OUT_DIR}/log.txt'

    def lines_failed(self, lines_failed: List[str]) -> None:
        with open(self.log_file, 'a') as out_file:
            out_file.write(f'Didn\'t parse {len(lines_failed)} lines:\n')
            for line in lines_failed:
                out_file.write(f'{line}')

            out_file.write('\n\n')

    def amt_matched_and_unmatched(self, txns_grouped: TxnsGrouped) -> None:
        with open(self.log_file, 'a') as out_file:
            out_file.write(
                f'AMT OF UNMATCHED CHASE TXNS: {len(txns_grouped.only_ch_txns)}\n')
            out_file.write(
                f'AMT OF UNMATCHED GOODBUDGET TXNS: {len(txns_grouped.only_gb_txns)}\n')
            out_file.write(
                f'AMT OF MATCHED TXNS: {len(txns_grouped.both_txns)}\n')

    def txns_grouped(self, txns_grouped: TxnsGrouped) -> None:
        with open(self.ch_file, 'w') as out_file:
            for txn in txns_grouped.only_ch_txns:
                out_file.write(f"{_ch_txn_to_row(txn)}\n")

        with open(self.gb_file, 'w') as out_file:
            for txn in txns_grouped.only_gb_txns:
                out_file.write(f"{_gb_txn_to_row(txn)}\n")

        with open(self.both_file, 'w') as out_file:
            for txn in txns_grouped.both_txns:
                out_file.write(f"{_merged_txn_to_row(txn)}\n")

        with open(self.merged_file, 'w') as out_file:
            for txn in txns_grouped.merged_txns:
                out_file.write(f"{_merged_txn_to_row(txn)}\n")

        with open(self.bal_diff_freq_file, 'w') as out_file:
            for bal_and_freq in txns_grouped.bal_diff_freq:
                out_file.write(f"{_bal_and_freq_to_row(bal_and_freq)}\n")
