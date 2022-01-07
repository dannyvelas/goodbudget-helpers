from datetime import datetime as dt
from enum import Enum
from operator import attrgetter
from typing import List, Union

from matplotlib import pyplot

from datatypes import GoodbudgetTxn


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
    txns_sorted = sorted(txns, key=attrgetter('ts'))

    if selection == Selection.BALANCE:
        dates = [dt.fromtimestamp(x.ts) for x in txns_sorted]
        balances = [x.bal/100 for x in txns_sorted]

        pyplot.plot_date(dates, balances, color='green', linestyle='solid')
        pyplot.show()
