from pathlib import Path
from datetime import datetime as dt

from datatypes import OrganizedTxns

OUT_DIR = f'./out/{dt.now().strftime("%Y-%m-%dT%H:%M")}'

OUT_CH_FILE = f'{OUT_DIR}/chase.csv'
OUT_GB_FILE = f'{OUT_DIR}/goodbudget.csv'
OUT_BOTH_FILE = f'{OUT_DIR}/both.csv'
OUT_MERGED_FILE = f'{OUT_DIR}/merged.csv'
OUT_BAL_DIFF_FREQ_FILE = f'{OUT_DIR}/bal_diff_freq.csv'


def write_organized_txns_to_files(organized_txns: OrganizedTxns):
    Path(OUT_DIR).mkdir()

    with open(OUT_CH_FILE, 'w') as out_file:
        for txn in organized_txns.only_ch_txns:
            out_file.write(f"{txn.to_row()}\n")

    with open(OUT_GB_FILE, 'w') as out_file:
        for txn in organized_txns.only_gb_txns:
            out_file.write(f"{txn.to_row()}\n")

    with open(OUT_BOTH_FILE, 'w') as out_file:
        for txn in organized_txns.both_txns:
            out_file.write(f"{txn.to_row()}\n")

    with open(OUT_MERGED_FILE, 'w') as out_file:
        for txn in organized_txns.merged_txns:
            out_file.write(f"{txn.to_row()}\n")

    with open(OUT_BAL_DIFF_FREQ_FILE, 'w') as out_file:
        for bal_and_freq in organized_txns.bal_diff_freq:
            out_file.write(f"{bal_and_freq.to_row()}\n")
