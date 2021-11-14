from datetime import datetime as dt
import sys
from typing import List

from add_new_txns import add_new_txns
from datatypes import ChaseTxn, GoodbudgetTxn
from file_in import read_ch_txns, read_gb_txns
from file_out import OUT_DIR, write_organized_txns_to_files
from match import get_organized_txns


add_txns = False
after_ts = 0

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--add" and not add_txns:
        add_txns = True
    elif arg == '--after' and i + 1 < len(sys.argv) and add_txns and after_ts == 0:
        after_ts = int(dt.strptime(sys.argv[i+1], "%m/%d/%Y").timestamp())
        i += 1
    else:
        print("usage: python3 main.py [--add [--after mm/dd/yyyy]]")
        exit(1)
    i += 1

ch_txns: List[ChaseTxn] = read_ch_txns()
gb_txns: List[GoodbudgetTxn] = read_gb_txns()

organized_txns = get_organized_txns(ch_txns, gb_txns)

write_organized_txns_to_files(organized_txns)

print(f"Saved to: {OUT_DIR}")

if add_txns:
    add_new_txns(organized_txns, after_ts)
