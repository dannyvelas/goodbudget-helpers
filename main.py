import sys

from dotenv import dotenv_values

from add_new_txns import add_new_txns
from config import Config
from file_in import read_ch_txns, read_gb_txns
from file_out import Logger, OUT_DIR
import graph
from match import get_txns_grouped

# set constants
MAX_DAYS_APART = 7

# parse cmd-line args
gen_out = False
add_txns = False
run_graph = False
i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg == "--gen-out" and not (gen_out or graph):
        gen_out = True
    elif arg == "--add" and not (add_txns or graph):
        add_txns = True
    elif arg == "--graph" and not (run_graph or gen_out or add_txns):
        run_graph = True
    else:
        print("usage: python3 main.py --gen-out | --add | --gen-out --add | --graph")
        exit(1)
    i += 1

if not (gen_out or add_txns or run_graph):
    print("usage: python3 main.py --gen-out | --add | --gen-out --add | --graph")
    exit(1)

# load config
ENV = dotenv_values(".env")
if not ENV:
    print("Error, no .env file found.")
    exit(1)
config = Config(ENV)

# read txns
ch_txns_result = read_ch_txns()
gb_txns_result = read_gb_txns()
ch_txns = ch_txns_result.txns
gb_txns = gb_txns_result.txns

txns_grouped = get_txns_grouped(
    ch_txns, gb_txns, config.ch_start_bal, config.gb_start_bal, MAX_DAYS_APART)

if gen_out or add_txns:
    if gen_out:
        log = Logger()
        log.lines_failed(ch_txns_result.lines_failed)
        log.lines_failed(gb_txns_result.lines_failed)
        log.amt_matched_and_unmatched(txns_grouped)
        log.txns_grouped(txns_grouped)
        print(f"Saved to: {OUT_DIR}")

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
elif run_graph:
    try:
        selection_result = graph.get_selection()
        if isinstance(selection_result, graph.ErrInput):
            print('Error,', selection_result.err)
        else:
            graph.graph(selection_result.selection, gb_txns)

    except EOFError:
        print('Exiting.\n')
        exit(1)
