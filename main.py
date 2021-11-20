import sys

from dotenv import dotenv_values

from add_new_txns import add_new_txns
from config import Config
from file_in import read_ch_txns, read_gb_txns
from file_out import OUT_DIR, write_txns_grouped_to_files
from match import get_txns_grouped

ENV = dotenv_values(".env")
if not ENV:
    print("Error, no .env file found.")
    exit(1)

config = Config(ENV)

MAX_DAYS_APART = 7
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

txns_grouped = get_txns_grouped(
    ch_txns, gb_txns, config.ch_start_bal, config.gb_start_bal, MAX_DAYS_APART)

# print some helpful numbers
print(f'AMT OF UNMATCHED CHASE TXNS: {len(txns_grouped.only_ch_txns)}')
print(f'AMT OF UNMATCHED GOODBUDGET TXNS: {len(txns_grouped.only_gb_txns)}')
print(f'AMT OF MATCHED TXNS: {len(txns_grouped.both_txns)}\n')

write_txns_grouped_to_files(txns_grouped)

print(f"Saved to: {OUT_DIR}")

if add_txns:
    ENVELOPES = dotenv_values(".envelopes.env")
    if not ENVELOPES:
        print("Error, no .envelopes.env file found.")
        exit(1)

    last_gb_txn_ts = gb_txns[-1].ts if len(gb_txns) > 0 else 0

    add_new_txns(txns_grouped, ENVELOPES, config.gb_username,
                 config.gb_password, last_gb_txn_ts)

    # print amts
    amt_pending = 0
    for txn in txns_grouped.only_ch_txns:
        if txn.ts > last_gb_txn_ts and txn.is_pending:
            amt_pending += txn.amt

    print(
        f"\nAll done! Dollar amount not added from pending txns: ${amt_pending/100}")
