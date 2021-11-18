from datetime import datetime as dt
from pathlib import Path

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    GoodbudgetTxn,
    MergedTxn,
    TxnsGrouped,
)

OUT_DIR = f'./out/{dt.now().strftime("%Y-%m-%dT%H:%M")}'

OUT_CH_FILE = f'{OUT_DIR}/chase.csv'
OUT_GB_FILE = f'{OUT_DIR}/goodbudget.csv'
OUT_BOTH_FILE = f'{OUT_DIR}/both.csv'
OUT_MERGED_FILE = f'{OUT_DIR}/merged.csv'
OUT_BAL_DIFF_FREQ_FILE = f'{OUT_DIR}/bal_diff_freq.csv'


AMT_CH_FIELDS = 4


def ch_txn_to_row(ch_txn: ChaseTxn):
    return f'{ch_txn.date},{ch_txn.title},{ch_txn.amt},{ch_txn.bal}'


AMT_GB_FIELDS = 5


def gb_txn_to_row(gb_txn: GoodbudgetTxn):
    return f'{gb_txn.date},{gb_txn.title},{gb_txn.envelope},{gb_txn.amt},{gb_txn.bal}'


def merged_txn_to_row(merged_txn: MergedTxn):
    if hasattr(merged_txn, 'ch_txn'):
        ch_row = ch_txn_to_row(merged_txn.ch_txn)
    else:
        ch_row = ',' * (AMT_CH_FIELDS - 1)

    if hasattr(merged_txn, 'gb_txn'):
        gb_row = gb_txn_to_row(merged_txn.gb_txn)
    else:
        gb_row = ',' * (AMT_GB_FIELDS - 1)

    return ','.join([merged_txn.type_.name, ch_row, gb_row, str(merged_txn.bal_diff / 100)])


def bal_and_freq_to_row(bal_and_freq: BalanceDifferenceFrequency) -> str:
    return f'{bal_and_freq.balance / 100},{bal_and_freq.frequency}'


def write_txns_grouped_to_files(txns_grouped: TxnsGrouped):
    Path(OUT_DIR).mkdir()

    with open(OUT_CH_FILE, 'w') as out_file:
        for txn in txns_grouped.only_ch_txns:
            out_file.write(f"{ch_txn_to_row(txn)}\n")

    with open(OUT_GB_FILE, 'w') as out_file:
        for txn in txns_grouped.only_gb_txns:
            out_file.write(f"{gb_txn_to_row(txn)}\n")

    with open(OUT_BOTH_FILE, 'w') as out_file:
        for txn in txns_grouped.both_txns:
            out_file.write(f"{merged_txn_to_row(txn)}\n")

    with open(OUT_MERGED_FILE, 'w') as out_file:
        for txn in txns_grouped.merged_txns:
            out_file.write(f"{merged_txn_to_row(txn)}\n")

    with open(OUT_BAL_DIFF_FREQ_FILE, 'w') as out_file:
        for bal_and_freq in txns_grouped.bal_diff_freq:
            out_file.write(f"{bal_and_freq_to_row(bal_and_freq)}\n")
