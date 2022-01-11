import readline
from typing import Dict, List, Union

from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from datatypes import ChaseTxn, TxnsGrouped, GoodbudgetTxn


class Driver:
    def __init__(self):
        self.chrome = Chrome()
        self.chrome.get('https://goodbudget.com/login')
        self.chrome.implicitly_wait(10)

    def login(self, gb_username: str, gb_password: str):
        self.chrome.find_element_by_id(
            'username').send_keys(gb_username)
        self.chrome.find_element_by_id(
            'password').send_keys(gb_password)

        # login submit button
        self.chrome.find_element_by_xpath(
            '//*[@id="content"]/div/div/div/section[2]/div/div/div/div/div/section/div/div/div[1]/div/div/section/div/div/div/div/div/div[1]/div/form/div/div[4]/button').click()

    def _click_add_txn(self): self.chrome.find_element_by_xpath(
        '/html/body/div[1]/div/div/div/div[1]/a[2]').click()

    def _click_save_txn(self): self.chrome.find_element_by_id(
        'addTransactionSave').click()

    def add_expense(self, envelopes_dict: Dict[str, Union[str, None]],
                    gb_txn: GoodbudgetTxn):
        self._click_add_txn()

        date_field = self.chrome.find_element_by_id('expense-date')
        date_field.clear()
        date_field.send_keys(gb_txn.date)

        payee_el: WebElement = self.chrome.find_element_by_id(
            'expense-receiver')
        payee_el.send_keys(gb_txn.title)
        payee_el.send_keys(Keys.RETURN)

        # flip sign
        amt = gb_txn.amt_dollars.replace('-', '') \
            if '-' in gb_txn.amt_dollars \
            else '-' + gb_txn.amt_dollars
        amt_el = self.chrome.find_element_by_id('expense-amount')
        amt_el.click()
        amt_el.send_keys(amt)

        # select envelope
        Select(self.chrome.find_element_by_xpath(
            '//*[@id="expenseCredit"]/form/fieldset/div[4]/div/select')
        ).select_by_value(
            envelopes_dict[gb_txn.envelope.replace(' ', '_').upper()])

        if gb_txn.notes:
            self.chrome \
                .find_element_by_id('expense-notes') \
                .send_keys(gb_txn.notes)

        self._click_save_txn()

    def add_income(self, gb_txn: GoodbudgetTxn):
        self._click_add_txn()

        self.chrome.find_element_by_xpath(
            '//*[@id="myTab"]/li[3]/a').click()  # click income tab

        date_field = self.chrome.find_element_by_id('income-date')
        date_field.clear()
        date_field.send_keys(gb_txn.date)

        payer_el: WebElement = self.chrome.find_element_by_id(
            'income-payer')
        payer_el.send_keys(gb_txn.title)
        payer_el.send_keys(Keys.RETURN)

        self.chrome.find_element_by_xpath(
            '//*[@id="income"]/form/fieldset/div[3]/div/input') \
            .send_keys(gb_txn.amt_dollars)

        if gb_txn.notes:
            self.chrome \
                .find_element_by_id('income-notes') \
                .send_keys(gb_txn.notes)

        self._click_save_txn()


class MatchedTxn:
    def __init__(self, ch_title: str, gb_title: str, gb_envelope: str):
        self.ch_title = ch_title
        self.gb_title = gb_title
        self.gb_envelope = gb_envelope


def env_completer(envelopes_dict: Dict[str, Union[str, None]]):
    def index_env(text: str, state: int):
        options = [
            x for x in envelopes_dict if x.lower().startswith(text.lower())]
        try:
            return options[state]
        except IndexError:
            return None

    return index_env


def title_completer(matched_txns: List[MatchedTxn]):
    def index_title(text: str, state: int):
        options = [matched_txn.gb_title for matched_txn in matched_txns if matched_txn.gb_title.lower(
        ).startswith(text.lower())]
        try:
            return options[state]
        except IndexError:
            return None

    return index_title


def is_correct_match(matched_txn: MatchedTxn):
    print(
        f'\tTitle: {matched_txn.gb_title}. Envelope: {matched_txn.gb_envelope}')
    answer = input('\tIs this correct? (yes): ')
    return not answer or answer.lower() in ['y', 'yes']


def should_add(chase_txn: ChaseTxn):
    answer = input(
        f'Add {"DEBIT" if chase_txn.is_debit else "CREDIT"}, {chase_txn.date}, {chase_txn.title}, {chase_txn.amt_dollars}? (yes): ')
    return not answer or answer.lower() in ['y', 'yes']


def add_new_txns(txns_grouped: TxnsGrouped,
                 envelopes_dict: Dict[str, Union[str, None]],
                 gb_username: str,
                 gb_password: str,
                 last_gb_txn_ts: int):
    # cast MergedTxns which were matched into MatchedTxns. remove quotes from titles and envelopes
    matched_txns: List[MatchedTxn] = [MatchedTxn(
        x.ch_txn.title, x.gb_txn.title.replace('"', ''), x.gb_txn.envelope.replace('"', ''))
        for x in txns_grouped.both_txns]

    # set up tab completion
    readline.parse_and_bind("tab: complete")
    title_completer_injected = title_completer(matched_txns)
    env_completer_injected = env_completer(envelopes_dict)

    driver = Driver()
    driver.login(gb_username, gb_password)

    # add each txn
    for txn in txns_grouped.only_ch_txns:
        if txn.ts > last_gb_txn_ts and not txn.is_pending and should_add(txn):
            # find txn in `matched_txns` with most similar chase title to `txn`
            similar_txn = matched_txns[0] if len(matched_txns) > 0 else None
            max_eq_chars = -1
            for matched_txn in matched_txns:
                i = 0
                while i < len(txn.title) and i < len(matched_txn.ch_title) and txn.title[i] == matched_txn.ch_title[i]:
                    i += 1
                if i > max_eq_chars:
                    max_eq_chars = i
                    similar_txn = matched_txn

            # get user input info for this new txn
            while True:
                try:
                    gb_title = similar_txn.gb_title if similar_txn else ""
                    gb_envelope = similar_txn.gb_envelope if similar_txn else ""

                    if similar_txn is None or not is_correct_match(similar_txn):
                        readline.set_completer(title_completer_injected)
                        gb_title = input('\tTitle: ')

                        if txn.is_debit:
                            readline.set_completer(env_completer_injected)
                            gb_envelope = input('\tEnvelope: ')

                        # add this new txn to `matched_txns` so that it could
                        # be guessed as a `similar_txn` for a future `txn`
                        matched_txns.append(MatchedTxn(
                            ch_title=txn.title, gb_title=gb_title,
                            gb_envelope=gb_envelope))

                    gb_notes = input('\tNote? (none): ')

                    gb_txn = GoodbudgetTxn(-1, txn.ts, txn.date, gb_title, gb_envelope,
                                           txn.amt_dollars, gb_notes)
                    break
                except EOFError:
                    # if user made a mistake, they press `Ctrl+D`, which will print a
                    # new line and let them re-insert the information
                    print('\n')

            # run selenium code to add to GB
            if txn.is_debit:
                driver.add_expense(envelopes_dict, gb_txn)
            else:
                driver.add_income(gb_txn)

    return
