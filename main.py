import sys
from typing import List

from dotenv import dotenv_values

from add_new_txns import add_new_txns
from config import Config
from datatypes import GoodbudgetTxn
from file_in import read_ch_txns, read_gb_txns
from file_out import (
    OUT_DIR,
    log_amt_matched_and_unmatched,
    log_lines_failed,
    write_txns_grouped,
)
from match import get_txns_grouped

# set constants
MAX_DAYS_APART = 7

# load config
ENV = dotenv_values(".env")
if not ENV:
    print("Error, no .env file found.")
    exit(1)
config = Config(ENV)

# parse cmd-line args
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

ch_txns_result = read_ch_txns()
gb_txns_result = read_gb_txns()

log_lines_failed(ch_txns_result.lines_failed)
log_lines_failed(gb_txns_result.lines_failed)

ch_txns = ch_txns_result.txns
gb_txns = gb_txns_result.txns

txns_grouped = get_txns_grouped(
    ch_txns, gb_txns, config.ch_start_bal, config.gb_start_bal, MAX_DAYS_APART)

log_amt_matched_and_unmatched(txns_grouped)
write_txns_grouped(txns_grouped)

print(f"Saved to: {OUT_DIR}")

gb_txns_added: List[GoodbudgetTxn] = []
if add_txns:
    ENVELOPES = dotenv_values(".envelopes.env")
    if not ENVELOPES:
        print("Error, no .envelopes.env file found.")
        exit(1)

    last_gb_txn_ts = gb_txns[0].ts if len(gb_txns) > 0 else 0

    gb_txns_added = add_new_txns(txns_grouped, ENVELOPES, config.gb_username,
                                 config.gb_password, last_gb_txn_ts)

    # print amts
    amt_pending = 0
    for txn in txns_grouped.only_ch_txns:
        if txn.ts > last_gb_txn_ts and txn.is_pending:
            amt_pending += txn.amt_cents

    print(
        f"\nAll done! Dollar amount not added from pending txns: ${amt_pending/100}")

if graph:
    txns_to_graph = gb_txns + gb_txns_added
    # TODO
    # while True:
    #    selection = graphpy.show_selections()
    #    graphpy(selection, txns_to_graph)
