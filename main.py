import sys

from add_new_txns import add_new_txns
from file_in import read_ch_txns, read_gb_txns
from file_out import OUT_DIR, write_txns_grouped_info_to_files
from match import get_txns_grouped_info

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

txns_grouped_info = get_txns_grouped_info(ch_txns, gb_txns)

write_txns_grouped_info_to_files(txns_grouped_info)

print(f"Saved to: {OUT_DIR}")

if add_txns:
    add_new_txns(txns_grouped_info)
