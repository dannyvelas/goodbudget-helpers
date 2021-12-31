import re

_CH_REGEX_STR = (r'(?P<deb_or_cred>DEBIT|CREDIT)'  # DEB_OR_CRED
                 r',(?P<date>\d\d\/\d\d\/\d{4})'   # DATE
                 r',(?P<title>"[^"]+")'            # TITLE
                 r',(?P<amt>-?\d+\.\d\d)'          # AMT
                 r',[A-Z_]+'                       # TYPE
                 r',(?P<balance>-?\d+.\d\d| )'     # BALANCE
                 r','                              # CHECK_OR_SPLIT_NUM
                 r',')                             # TRAILING COMMA

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
