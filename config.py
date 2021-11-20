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
        gb_start_bal = env["GB_START_BAL"] if "GB_START_BAL" in env and env["GB_START_BAL"] is not None else ""

        self.ch_start_bal = _str_to_int(ch_start_bal)
        self.gb_start_bal = _str_to_int(gb_start_bal)

        if "GB_USERNAME" in env and env["GB_USERNAME"] is not None:
            self.gb_username = env["GB_USERNAME"]
        else:
            print("Warning: GB_USERNAME not found in environment")
            self.gb_username = ""

        if "GB_PASSWORD" in env and env["GB_PASSWORD"] is not None:
            self.gb_password = env["GB_PASSWORD"]
        else:
            print("Warning: GB_PASSWORD not found in environment")
            self.gb_password = ""
