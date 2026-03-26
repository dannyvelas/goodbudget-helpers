import re

_CH_REGEX_STR = (r'(?P<date>\d\d\/\d\d\/\d{4})'        # Transaction Date
                 r',\d\d\/\d\d\/\d{4}'                  # Post Date (skipped)
                 r',(?P<description>"[^"]+"|[^,\n]+)'   # Description
                 r',[^,\n]+'                             # Category (skipped)
                 r',[^,\n]+'                             # Type (skipped)
                 r',(?P<amt>-?\d+\.\d\d)'               # Amount
                 r',.*')                             # TRAILING COMMA

_YNAB_REGEX_STR = (r'"[^"]*"'                           # Account (col 0, skip)
                   r',"[^"]*"'                          # Flag (col 1, skip)
                   r',"(?P<date>[^"]+)"'                # Date (col 2)
                   r',"(?P<payee>[^"]*)"'               # Payee (col 3)
                   r',"[^"]*"'                          # Category Group/Category (col 4, skip)
                   r',"[^"]*"'                          # Category Group (col 5, skip)
                   r',"(?P<category>[^"]*)"'            # Category (col 6, deepest)
                   r',"[^"]*"'                          # Memo (col 7, skip)
                   r',\$(?P<outflow>\d+\.\d\d)'         # Outflow (col 8, $ stripped)
                   r',\$(?P<inflow>\d+\.\d\d)'          # Inflow (col 9, $ stripped)
                   r',"(?P<cleared>[^"]+)"')             # Cleared (col 10)

CH_REGEX = re.compile(_CH_REGEX_STR)
YNAB_REGEX = re.compile(_YNAB_REGEX_STR)
