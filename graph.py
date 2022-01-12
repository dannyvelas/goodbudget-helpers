from datetime import datetime as dt
from enum import Enum
from typing import Dict, List, Union

from dotenv import dotenv_values
from matplotlib import pyplot

from config import Config
from datatypes import GoodbudgetTxn
from file_in import read_gb_txns


class Selection(Enum):
    BALANCE = 1
    MAX_TXNS = 2
    AMT_TXNS = 3
    BALANCE_ENV = 4


class ErrInput:
    def __init__(self, err: str):
        self.err = err


class OkInput:
    def __init__(self, selection: Selection):
        self.selection = selection


def get_selection() -> Union[ErrInput, OkInput]:
    selection = input(
        """Select an option to graph:
    (1) Balance as a function of time
    (2) Most popular transaction title per envelope
    (3) Amount of transactions per title in a given envelope
    (4) Amount of dollars spent as a function of months, in a given envelope
    """
    )

    if len(selection) > 1:
        return ErrInput("Selection must be one character.")
    elif not selection.isdecimal():
        return ErrInput("Selection must be a digit.")

    selection_int = int(selection)
    if selection_int < 1:
        return ErrInput("Selection must be greater than or equal to 1.")
    elif selection_int > 4:
        return ErrInput("Selection must be less than or equal to 4.")
    else:
        return OkInput(Selection(selection_int))


def graph(selection: Selection, txns: List[GoodbudgetTxn]):
    if selection == Selection.BALANCE:
        dates = [dt.fromtimestamp(x.ts) for x in txns]
        balances = [x.bal/100 for x in txns]

        pyplot.plot_date(dates, balances, color='green', linestyle='solid')
        pyplot.show()
    elif selection == Selection.MAX_TXNS:
        env_to_title_to_amt_txns: Dict[str, Dict[str, int]] = {}
        for txn in txns:
            envelope = txn.envelope
            title = txn.title
            if envelope not in env_to_title_to_amt_txns:
                env_to_title_to_amt_txns[envelope] = {title: 1}
            elif title not in env_to_title_to_amt_txns[envelope]:
                env_to_title_to_amt_txns[envelope][title] = 1
            else:
                env_to_title_to_amt_txns[envelope][title] += 1

        envelopes: List[str] = []
        most_txns_list: List[int] = []
        titles_with_most_txns: List[str] = []
        for envelope in env_to_title_to_amt_txns:
            most_txns = 0
            title_with_most_txns = ''
            for title in env_to_title_to_amt_txns[envelope]:
                curr_txns = env_to_title_to_amt_txns[envelope][title]
                if curr_txns > most_txns:
                    most_txns = curr_txns
                    title_with_most_txns = title
            envelopes.append(envelope)
            most_txns_list.append(most_txns)
            titles_with_most_txns.append(title_with_most_txns)

        _, ax = pyplot.subplots()
        ax.bar(envelopes, most_txns_list)
        for i, title in enumerate(titles_with_most_txns):
            ax.text(i - 0.25, most_txns_list[i] + 3, title,
                    color='blue', size='small', rotation=45)
        pyplot.show()
    elif selection == Selection.AMT_TXNS:
        title_to_amt_txns: Dict[str, int] = {}
        for txn in txns:
            # TODO: make programmable
            if txn.envelope == 'Housing':
                title = txn.title
                if title not in title_to_amt_txns:
                    title_to_amt_txns[title] = 1
                else:
                    title_to_amt_txns[title] += 1

        _, ax = pyplot.subplots()
        ax.bar(list(title_to_amt_txns.keys()),
               list(title_to_amt_txns.values()))
        pyplot.setp(ax.get_xticklabels(), rotation=45, ha="right",
                    rotation_mode="anchor", size='small')
        pyplot.show()
    elif selection == Selection.BALANCE_ENV:
        month_to_spent: Dict[dt, int] = {}
        for txn in txns:
            if txn.envelope == 'Groceries':
                date_obj = dt.fromtimestamp(txn.ts)
                first_of_month = dt(year=date_obj.year,
                                    month=date_obj.month, day=1)
                if first_of_month not in month_to_spent:
                    month_to_spent[first_of_month] = txn.amt_cents
                else:
                    month_to_spent[first_of_month] += txn.amt_cents

        dollars = [(x/100) * -1 for x in month_to_spent.values()]

        _, ax = pyplot.subplots()
        ax.bar(month_to_spent.keys(), dollars)
        ax.xaxis_date()

        pyplot.setp(ax.get_xticklabels(), rotation=45, ha="right",
                    rotation_mode="anchor", size='small')

        pyplot.show()


if __name__ == "__main__":
    # load config
    ENV = dotenv_values(".env")
    if not ENV:
        print("Error, no .env file found.")
        exit(1)
    config = Config(ENV)

    gb_txns = read_gb_txns(config.gb_start_bal).txns

    try:
        selection_result = get_selection()
        if isinstance(selection_result, ErrInput):
            print('Error,', selection_result.err)
        else:
            graph(selection_result.selection, gb_txns)

    except EOFError:
        print('Exiting.\n')
        exit(1)
