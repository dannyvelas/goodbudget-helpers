from dotenv import dotenv_values

from config import Config
from file_in import read_ch_txns, read_ynab_txns
from file_out import Logger, OUT_DIR
from match import get_txns_grouped

if __name__ == "__main__":
    ENV = dotenv_values(".env")
    if not ENV:
        print("Error, no .env file found.")
        exit(1)
    config = Config(ENV)

    ch_txns_result = read_ch_txns(config.ch_start_bal)
    ynab_txns_result = read_ynab_txns(config.ynab_start_bal)
    ch_txns = ch_txns_result.txns
    ynab_txns = ynab_txns_result.txns

    txns_grouped = get_txns_grouped(
        ch_txns, ynab_txns, config.ch_start_bal, config.ynab_start_bal)

    log = Logger()
    log.lines_failed(ch_txns_result.lines_failed)
    log.lines_failed(ynab_txns_result.lines_failed)
    log.amt_matched_and_unmatched(txns_grouped)
    log.txns_grouped(txns_grouped)
    print(f"Saved to: {OUT_DIR}")
