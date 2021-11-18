import sys

from add_new_txns import add_new_txns
from file_in import read_ch_txns, read_gb_txns
from file_out import OUT_DIR, write_txns_grouped_to_files
from match import get_txns_grouped

add_txns = False
graph = False

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--add" and not add_txns:
        add_txns = True
    elif arg == "--graph" and not graph:
        graph = True
    else:
        print("usage: python3 main.py [--add] [--graph]")
        exit(1)
    i += 1

ch_txns = read_ch_txns()
gb_txns = read_gb_txns()

txns_grouped = get_txns_grouped(ch_txns, gb_txns)

# print some helpful numbers
print(f'AMT OF UNMATCHED CHASE TXNS: {len(txns_grouped.only_ch_txns)}')
print(f'AMT OF UNMATCHED GOODBUDGET TXNS: {len(txns_grouped.only_gb_txns)}')
print(f'AMT OF MATCHED TXNS: {len(txns_grouped.both_txns)}\n')

write_txns_grouped_to_files(txns_grouped)

print(f"Saved to: {OUT_DIR}")

if add_txns:
    last_gb_txn_ts = gb_txns[-1].ts if len(gb_txns) > 0 else 0
    add_new_txns(txns_grouped, last_gb_txn_ts)
