import readline
from typing import Dict, List, Union

from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from datatypes import TxnsGrouped


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
                    date: str, payee: str, amount: str, envelope: str, note: str):
        self._click_add_txn()

        date_field = self.chrome.find_element_by_id('expense-date')
        date_field.clear()
        date_field.send_keys(date)

        payee_el: WebElement = self.chrome.find_element_by_id(
            'expense-receiver')
        payee_el.send_keys(payee)
        payee_el.send_keys(Keys.RETURN)

        # flip sign
        amount = amount.replace('-', '') if '-' in amount else '-' + amount
        amt_el = self.chrome.find_element_by_id('expense-amount')
        amt_el.click()
        amt_el.send_keys(amount)

        Select(self.chrome.find_element_by_xpath('//*[@id="expenseCredit"]/form/fieldset/div[4]/div/select')) \
            .select_by_value(envelopes_dict[envelope.replace(' ', '_').upper()])

        if note:
            self.chrome.find_element_by_id('expense-notes').send_keys(note)

        self._click_save_txn()

    def add_income(self, date: str, payer: str, amount: str, note: str):
        self._click_add_txn()

        self.chrome.find_element_by_xpath(
            '//*[@id="myTab"]/li[3]/a').click()  # click income tab

        date_field = self.chrome.find_element_by_id('income-date')
        date_field.clear()
        date_field.send_keys(date)

        payer_el: WebElement = self.chrome.find_element_by_id(
            'income-payer')
        payer_el.send_keys(payer)
        payer_el.send_keys(Keys.RETURN)

        self.chrome.find_element_by_xpath(
            '//*[@id="income"]/form/fieldset/div[3]/div/input').send_keys(amount)  # income amt

        if note:
            self.chrome.find_element_by_id('income-notes').send_keys(note)

        self._click_save_txn()


class TrimmedChaseTxn:
    def __init__(self, ts: int, is_debit: bool, is_pending: bool, date: str, title: str, amt: str):
        self.ts = ts
        self.is_debit = is_debit
        self.is_pending = is_pending
        self.date = date
        self.title = title
        self.amt = amt


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


def should_add(chase_txn: TrimmedChaseTxn):
    answer = input(
        f'Add {"DEBIT" if chase_txn.is_debit else "CREDIT"}, {chase_txn.date}, {chase_txn.title}, {chase_txn.amt}? (yes): ')
    return not answer or answer.lower() in ['y', 'yes']


def add_new_txns(txns_grouped: TxnsGrouped, envelopes_dict: Dict[str, Union[str, None]],
                 gb_username: str, gb_password: str, last_gb_txn_ts: int):
    # set up tab completion
    readline.parse_and_bind("tab: complete")

    # Cast ChaseTxns to TrimmedChaseTxns
    only_ch_txns = [TrimmedChaseTxn(
        x.ts, x.is_debit, x.is_pending, x.date, x.title, str(x.amt/100)) for x in txns_grouped.only_ch_txns]

    # cast MergedTxns which were matched into MatchedTxns. remove quotes from titles and envelopes
    matched_txns: List[MatchedTxn] = [MatchedTxn(
        x.ch_txn.title, x.gb_txn.title.replace('"', ''), x.gb_txn.envelope.replace('"', ''))
        for x in txns_grouped.both_txns]

    driver = Driver()
    driver.login(gb_username, gb_password)

    # add each txn
    for txn in only_ch_txns:
        if txn.ts > last_gb_txn_ts and not txn.is_pending and should_add(txn):
            # find txn in `matched_txns` with most similar chase title to `txn`
            similar_txn: MatchedTxn = matched_txns[0]
            max_eq_chars = -1
            for matched_txn in matched_txns:
                i = 0
                while i < len(txn.title) and i < len(matched_txn.ch_title) and txn.title[i] == matched_txn.ch_title[i]:
                    i += 1
                if i > max_eq_chars:
                    max_eq_chars = i
                    similar_txn = matched_txn

            # get info for this new txn
            while True:
                try:
                    new_gb_title, new_gb_envelope = similar_txn.gb_title, similar_txn.gb_envelope
                    if not is_correct_match(similar_txn):
                        readline.set_completer(title_completer(matched_txns))
                        new_gb_title = input('\tTitle: ')

                        if txn.is_debit:
                            readline.set_completer(
                                env_completer(envelopes_dict))
                            new_gb_envelope = input('\tEnvelope: ')

                        # add this new txn to `matched_txns` so that it could be guessed as a `similar_txn` for a future `txn`
                        matched_txns.append(MatchedTxn(
                            ch_title=txn.title, gb_title=new_gb_title, gb_envelope=new_gb_envelope))

                    new_note = input('\tNote? (none): ')
                    break
                except EOFError:
                    # if user made a mistake, they press `Ctrl+D`, which will print a
                    # new line and let them re-insert the information
                    print('\n')

            # run selenium code to add to GB
            if txn.is_debit:
                driver.add_expense(envelopes_dict, txn.date, new_gb_title,
                                   txn.amt, new_gb_envelope, new_note)
            else:
                driver.add_income(txn.date, new_gb_title, txn.amt, new_note)
