from datetime import datetime as dt
from enum import Enum
from typing import List, Union

from dotenv import dotenv_values
from matplotlib import pyplot

from config import Config
from datatypes import GoodbudgetTxn
from file_in import read_gb_txns


class Selection(Enum):
    BALANCE = 1


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
    """
    )

    if len(selection) > 1:
        return ErrInput("Selection must be one character.")
    elif not selection.isdecimal():
        return ErrInput("Selection must be a digit.")

    selection_int = int(selection)
    if selection_int < 1:
        return ErrInput("Selection must be greater than or equal to 1.")
    elif selection_int > 1:
        return ErrInput("Selection must be less than or equal to 1.")
    else:
        return OkInput(Selection(selection_int))


def graph(selection: Selection, txns: List[GoodbudgetTxn]):
    if selection == Selection.BALANCE:
        dates = [dt.fromtimestamp(x.ts) for x in txns]
        balances = [x.bal/100 for x in txns]

        pyplot.plot_date(dates, balances, color='green', linestyle='solid')
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
