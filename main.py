from datetime import datetime as dt
import sys

from add_new_txns import add_new_txns
from match import organize_txns

out_dir = './out/merged'
add_txns = False
after_ts = 0
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--dir" and i + 1 < len(sys.argv) and out_dir == "./out/merged":
        compare_to = sys.argv[i + 1]
        i += 1
    elif arg == "--add" and not add_txns:
        add_txns = True
    elif arg == '--after' and i + 1 < len(sys.argv) and add_txns and after_ts == 0:
        after_ts = int(dt.strptime(sys.argv[i+1], "%m/%d/%Y").timestamp())
        i += 1
    else:
        print(
            "usage: python3 main.py [--dir <out-dir>] [--add [--after mm/dd/yyyy]]")
        exit(1)
    i += 1

organized_txns = organize_txns(out_dir)

if add_txns:
    add_new_txns(organized_txns, after_ts)
