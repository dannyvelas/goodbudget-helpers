from datetime import datetime as dt
from pathlib import Path
from typing import List

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    MergedTxn,
    MergedTxn_ChaseTxn,
    MergedTxn_YnabTxn,
    TxnsGrouped,
    YnabTxn,
)


### Helper Values and Functions #########################################
_AMT_CH_FIELDS = 5
_CH_FIELD_NAMES = 'Chase ID,Chase Date,Chase Title,Chase Txn Amount,Chase Balance'


def _ch_txn_to_row(ch_txn: ChaseTxn) -> str:
    return f'{ch_txn.id_},{ch_txn.date},{ch_txn.title},{ch_txn.amt_dollars},{ch_txn.bal/100}'


_AMT_YNAB_FIELDS = 6
_YNAB_FIELD_NAMES = 'YNAB ID,YNAB Date,YNAB Title,YNAB Category,YNAB Txn Amount,YNAB Balance'


def _ynab_txn_to_row(ynab_txn: YnabTxn) -> str:
    return f'{ynab_txn.id_},{ynab_txn.date},{ynab_txn.title},{ynab_txn.category},{ynab_txn.amt_dollars},{ynab_txn.bal/100}'


_MERGED_TXN_FIELD_NAMES = f'Txn Type,{_CH_FIELD_NAMES},{_YNAB_FIELD_NAMES},Balance Difference'


def _merged_txn_to_row(merged_txn: MergedTxn) -> str:
    txn_type = 'BOTH'

    if isinstance(merged_txn, MergedTxn_ChaseTxn):
        txn_type = 'CHASE'
        ynab_row = ',' * (_AMT_YNAB_FIELDS - 1)
    else:
        ynab_row = _ynab_txn_to_row(merged_txn.ynab_txn)

    if isinstance(merged_txn, MergedTxn_YnabTxn):
        txn_type = 'YNAB'
        ch_row = ',' * (_AMT_CH_FIELDS - 1)
    else:
        ch_row = _ch_txn_to_row(merged_txn.ch_txn)

    return ','.join([txn_type, ch_row, ynab_row, str(merged_txn.bal_diff/100)])


def _bal_and_freq_to_row(bal_and_freq: BalanceDifferenceFrequency) -> str:
    return f'{bal_and_freq.balance/100},{bal_and_freq.frequency}'


### Export #############################################################

OUT_DIR = f'./out/{dt.now().strftime("%Y-%m-%dT%H:%M")}'


class Logger:
    def __init__(self):
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

        self.ch_file = f'{OUT_DIR}/chase.csv'
        self.ynab_file = f'{OUT_DIR}/ynab.csv'
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
                f'AMT OF UNMATCHED YNAB TXNS: {len(txns_grouped.only_ynab_txns)}\n')
            out_file.write(
                f'AMT OF MATCHED TXNS: {len(txns_grouped.both_txns)}\n')

    def txns_grouped(self, txns_grouped: TxnsGrouped) -> None:
        with open(self.ch_file, 'w') as out_file:
            out_file.write(f'{_CH_FIELD_NAMES}\n')
            for txn in txns_grouped.only_ch_txns:
                out_file.write(f"{_ch_txn_to_row(txn)}\n")

        with open(self.ynab_file, 'w') as out_file:
            out_file.write(f'{_YNAB_FIELD_NAMES}\n')
            for txn in txns_grouped.only_ynab_txns:
                out_file.write(f"{_ynab_txn_to_row(txn)}\n")

        with open(self.both_file, 'w') as out_file:
            out_file.write(f'{_MERGED_TXN_FIELD_NAMES}\n')
            for txn in txns_grouped.both_txns:
                out_file.write(f"{_merged_txn_to_row(txn)}\n")

        with open(self.merged_file, 'w') as out_file:
            out_file.write(f'{_MERGED_TXN_FIELD_NAMES}\n')
            for txn in txns_grouped.merged_txns:
                out_file.write(f"{_merged_txn_to_row(txn)}\n")

        with open(self.bal_diff_freq_file, 'w') as out_file:
            out_file.write('Balance,Frequency\n')
            for bal_and_freq in txns_grouped.bal_diff_freq:
                out_file.write(f"{_bal_and_freq_to_row(bal_and_freq)}\n")
