from typing import Dict, Union


def _str_to_int(s: str) -> int:
    if s[0] in ('-', '+') and s[1:].isdigit():
        return int(s)
    elif s.isdigit():
        return int(s)
    else:
        return 0


class Config:
    def __init__(self, env: Dict[str, Union[str, None]]):
        ch_start_bal = env["CH_START_BAL"] if "CH_START_BAL" in env and env["CH_START_BAL"] is not None else ""
        ynab_start_bal = env["YNAB_START_BAL"] if "YNAB_START_BAL" in env and env["YNAB_START_BAL"] is not None else ""

        self.ch_start_bal = _str_to_int(ch_start_bal)
        self.ynab_start_bal = _str_to_int(ynab_start_bal)
