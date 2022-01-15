from datetime import datetime as dt, timedelta
from typing import Dict, List, Union

from dotenv import dotenv_values
from matplotlib import pyplot

from config import Config
from datatypes import GoodbudgetTxn
from file_in import read_gb_txns
from pandas import Timestamp
import pandas


# for graphs with more than one line / bar
COLORS = ['b', 'g', 'r', 'c', 'm', 'y',
          'magenta', 'tomato', 'slategray', 'peru', 'crimson']


class Balance:
    pass


class AmtFromMostPopular:
    pass


class AmtTxnsPerTitle:
    def __init__(self, envelope: str):
        self.envelope = envelope


class AmtSpentPerTitle:
    def __init__(self, envelope: str):
        self.envelope = envelope


class MonthlySpendingEnv:
    def __init__(self, envelope: str):
        self.envelope = envelope


class MonthlySpendingTitle:
    def __init__(self, title: str):
        self.title = title


Selection = Union[
    Balance,
    AmtFromMostPopular,
    AmtTxnsPerTitle,
    AmtSpentPerTitle,
    MonthlySpendingEnv,
    MonthlySpendingTitle,
]


class Err:
    def __init__(self, err: str):
        self.err = err


def safe_int(selection: str) -> Union[Err, int]:
    if not selection.isdecimal():
        return Err("Selection must be a digit.")
    return int(selection)


def get_envelope(envelopes: List[str]) -> Union[Err, str]:
    for i, envelope in enumerate(envelopes):
        print(f'({i}) {envelope}')

    envelope_chosen = input(
        'Choose the envelope you would like by entering its number: ')
    envelope_result = safe_int(envelope_chosen)
    if isinstance(envelope_result, Err):
        return envelope_result

    if envelope_result < 0 or envelope_result > len(envelopes):
        return Err("Envelope chosen out of range.")

    return envelopes[envelope_result]


def get_selection(envelopes: List[str]) -> Union[Err, Selection]:
    selection = input(
        """Select an option to graph:
    (1) Balance as a function of time
    (2) Amount of transactions from most popular title per envelope
    (3) Amount of transactions per title, in a given envelope
    (4) Amount spent per title, in a given envelope
    (5) Amount spent per month, in a given envelope
    (6) Amount spent per month, for a given title
    """
    )

    selection_result = safe_int(selection)
    if isinstance(selection_result, Err):
        return selection_result

    if selection_result < 1:
        return Err("Selection must be greater than or equal to 1.")
    elif selection_result > 6:
        return Err("Selection must be less than or equal to 4.")
    elif selection_result == 1:
        return Balance()
    elif selection_result == 2:
        return AmtFromMostPopular()
    elif selection_result == 3:
        envelope_result = get_envelope(envelopes)
        if isinstance(envelope_result, Err):
            return envelope_result
        return AmtTxnsPerTitle(envelope_result)
    elif selection_result == 4:
        envelope_result = get_envelope(envelopes)
        if isinstance(envelope_result, Err):
            return envelope_result
        return AmtSpentPerTitle(envelope_result)
    elif selection_result == 5:
        envelope_result = get_envelope(envelopes)
        if isinstance(envelope_result, Err):
            return envelope_result
        return MonthlySpendingEnv(envelope_result)
    else:
        title = input('title: ')
        return MonthlySpendingTitle(title)


def graph(selection: Selection, txns: List[GoodbudgetTxn], date_range: List[Timestamp]):
    if isinstance(selection, Balance):
        dates = [dt.fromtimestamp(x.ts) for x in txns]
        balances = [x.bal/100 for x in txns]

        pyplot.plot_date(dates, balances, color='b', linestyle='solid')
        pyplot.show()
    elif isinstance(selection, AmtFromMostPopular):
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
    elif isinstance(selection, AmtTxnsPerTitle):
        title_to_amt_txns: Dict[str, int] = {}
        for txn in txns:
            if txn.envelope == selection.envelope:
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
    elif isinstance(selection, AmtSpentPerTitle):
        title_spent: Dict[str, int] = {}
        for txn in txns:
            if txn.envelope == selection.envelope:
                if txn.title not in title_spent:
                    title_spent[txn.title] = txn.amt_cents
                else:
                    title_spent[txn.title] += txn.amt_cents

        _, ax = pyplot.subplots()

        dollars = [(x / 100) * -1 for x in title_spent.values()]
        ax.bar(title_spent.keys(), dollars,
               color='b', label=selection.envelope)

        ax.legend()
        pyplot.setp(ax.get_xticklabels(), rotation=45, ha="right",
                    rotation_mode="anchor", size='small')

        pyplot.show()
    elif isinstance(selection, MonthlySpendingEnv):
        env_month_spent: Dict[str, Dict[dt, int]] = {}
        for txn in txns:
            # TODO: allow more than one envelope to be passed in
            if txn.envelope == selection.envelope:
                date_obj = dt.fromtimestamp(txn.ts)
                first_of_month = date_obj.replace(day=1)
                if txn.envelope not in env_month_spent:
                    env_month_spent[txn.envelope] = {
                        first_of_month: txn.amt_cents}
                elif first_of_month not in env_month_spent[txn.envelope]:
                    env_month_spent[txn.envelope][first_of_month] = txn.amt_cents
                else:
                    env_month_spent[txn.envelope][first_of_month] += txn.amt_cents

        _, ax = pyplot.subplots()
        width = 5

        for i, envelope in enumerate(env_month_spent):
            dollars: List[float] = []
            for month in date_range:
                if month not in env_month_spent[envelope]:
                    dollars.append(0)
                else:
                    dollars.append(
                        (env_month_spent[envelope][month] / 100) * -1)
            ax.bar([x - timedelta(days=i * 5) for x in date_range],
                   dollars, width, color=COLORS[i], label=envelope)

        ax.xaxis_date()
        ax.legend()
        pyplot.setp(ax.get_xticklabels(), rotation=45, ha="right",
                    rotation_mode="anchor", size='small')

        pyplot.show()
    elif isinstance(selection, MonthlySpendingTitle):
        month_spent: Dict[dt, int] = {}
        for txn in txns:
            if txn.title == selection.title:
                date_obj = dt.fromtimestamp(txn.ts)
                first_of_month = date_obj.replace(day=1)
                if first_of_month not in month_spent:
                    month_spent[first_of_month] = txn.amt_cents
                else:
                    month_spent[first_of_month] += txn.amt_cents

        _, ax = pyplot.subplots()
        width = 5

        dollars: List[float] = []
        for month in date_range:
            if month not in month_spent:
                dollars.append(0)
            else:
                dollars.append((month_spent[month] / 100) * -1)
        ax.bar(date_range, dollars, width, color='b', label=selection.title)

        ax.xaxis_date()
        ax.legend()
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

    # get txns
    gb_txns = read_gb_txns(config.gb_start_bal).txns

    # get envelopes, earliest, and latest date
    seen = set()
    envelopes: List[str] = []
    earliest_date = dt.fromtimestamp(0)
    latest_date = dt.fromtimestamp(0)
    for txn in gb_txns:
        if "Unallocated" not in txn.envelope and txn.envelope not in seen:
            seen.add(txn.envelope)
            envelopes.append(txn.envelope)
        curr_date = dt.fromtimestamp(txn.ts)
        if earliest_date.timestamp() == 0 or curr_date < earliest_date:
            earliest_date = curr_date.replace(day=1)
        if curr_date > latest_date:
            latest_date = curr_date
    date_range = pandas.date_range(
        earliest_date, latest_date, freq='MS').to_list()

    try:
        selection_result = get_selection(envelopes)
        if isinstance(selection_result, Err):
            print('Error,', selection_result.err)
        else:
            graph(selection_result, gb_txns, date_range)

    except EOFError:
        print('Exiting.\n')
        exit(1)
