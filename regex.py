import re

_CH_REGEX_STR = (r'(?P<date>\d\d\/\d\d\/\d{4})'        # Transaction Date
                 r',\d\d\/\d\d\/\d{4}'                  # Post Date (skipped)
                 r',(?P<description>"[^"]+"|[^,\n]+)'   # Description
                 r',[^,\n]+'                             # Category (skipped)
                 r',[^,\n]+'                             # Type (skipped)
                 r',(?P<amt>-?\d+\.\d\d)'               # Amount
                 r',.*')                             # TRAILING COMMA

_GB_INCOME_REGEX_STR = (r'(?P<date>\d\d\/\d\d\/\d{4})'  # DATE
                        r',(?P<envelope>)'              # ENVELOPE
                        r',"Chase Account"'             # ACCOUNT
                        r',(?P<title>"[^"]+"|[^,]+)'    # TITLE
                        r',(?P<notes>"[^"]+"|[^,]*)'    # NOTES
                        r','                            # CHECK_NUM
                        r',(?P<amt>"[^"]+"|[^,]+)'      # AMT
                        r',(CLR)?'                      # STATUS
                        r',("[^"]+"|[^\n]+)')           # DETAILS

_GB_EXPENSE_REGEX_STR = (r'(?P<date>\d\d\/\d\d\/\d{4})'  # DATE
                         # ENVELOPE
                         r',(?P<envelope>"[^"]+"|[A-Za-z]+|\[Unallocated\])'
                         r',"Chase Account"'             # ACCOUNT
                         r',(?P<title>"[^"]+"|[^,]+)'    # TITLE
                         r',(?P<notes>"[^"]+"|[^,]*)'    # NOTES
                         r','                            # CHECK_NUM
                         r',(?P<amt>"[^"]+"|[^,]+)'      # AMT
                         r',(CLR)?'                      # STATUS
                         r',')                           # DETAILS

CH_REGEX = re.compile(_CH_REGEX_STR)
GB_INCOME_REGEX = re.compile(_GB_INCOME_REGEX_STR)
GB_EXPENSE_REGEX = re.compile(_GB_EXPENSE_REGEX_STR)
