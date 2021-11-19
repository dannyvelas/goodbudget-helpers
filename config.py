from typing import Dict, Union


def _str_to_int(s: str) -> int:
    if s[0] in ('-', '+') and s[1:].isdigit():
        return int(s)
    elif s.isdigit():
        return int(s)
    else:
        return 0


def get_ch_start_bal(env: Dict[str, Union[str, None]]) -> int:
    env_ch_start_bal = env["CH_START_BAL"] if "CH_START_BAL" in env and env["CH_START_BAL"] is not None else ""
    return _str_to_int(env_ch_start_bal)


def get_gb_start_bal(env: Dict[str, Union[str, None]]) -> int:
    env_gb_start_bal = env["GB_START_BAL"] if "GB_START_BAL" in env and env["GB_START_BAL"] is not None else ""
    return _str_to_int(env_gb_start_bal)


def get_gb_username(env: Dict[str, Union[str, None]]) -> str:
    if "GB_USERNAME" in env and env["GB_USERNAME"] is not None:
        return env["GB_USERNAME"]
    else:
        print("Warning: GB_USERNAME not found in environment")
        return ""


def get_gb_password(env: Dict[str, Union[str, None]]) -> str:
    if "GB_PASSWORD" in env and env["GB_PASSWORD"] is not None:
        return env["GB_PASSWORD"]
    else:
        print("Warning: GB_PASSWORD not found in environment")
        return ""
