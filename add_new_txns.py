import readline
from typing import List

from dotenv import dotenv_values
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select

from match import organize_txns
ENV = dotenv_values(".env")

##### READLINE CONFIG ########################################################
ENVELOPES = [x for x in ENV if x not in ["USERNAME", "PASSWORD"]]
def env_completer(text, state):
    options = [x for x in ENVELOPES if x.lower().startswith(text.lower())]
    try:
        return options[state]
    except IndexError:
        return None

def title_completer(text, state):
    options =  [matched_txn.gb_title for matched_txn in matched_txns if matched_txn.gb_title.lower(
    ).startswith(text.lower())]
    try:
        return options[state]
    except IndexError:
        return None

readline.parse_and_bind("tab: complete")
##############################################################################

class Driver:
    _chrome = Chrome()
    _chrome.get('https://goodbudget.com/login')
    _chrome.implicitly_wait(10)

    @staticmethod
    def login():
        Driver._chrome.find_element_by_id(
            'username').send_keys(ENV["USERNAME"])
        Driver._chrome.find_element_by_id(
            'password').send_keys(ENV["PASSWORD"])

        # login submit button
        Driver._chrome.find_element_by_xpath(
            '//*[@id="content"]/div/div/div/section[2]/div/div/div/div/div/section/div/div/div[1]/div/div/section/div/div/div/div/div/div[1]/div/form/div/div[4]/button').click()

    @staticmethod
    def _click_add_txn(): Driver._chrome.find_element_by_xpath(
        '/html/body/div[1]/div/div/div/div[1]/a[2]').click()

    @staticmethod
    def _click_save_txn(): Driver._chrome.find_element_by_id(
        'addTransactionSave').click()

    @staticmethod
    def add_expense(date: str, payee: str, amount: str, envelope: str, note: str):
        Driver._click_add_txn()

        date_field = Driver._chrome.find_element_by_id('expense-date')
        date_field.clear()
        date_field.send_keys(date)

        payee_el: WebElement = Driver._chrome.find_element_by_id(
            'expense-receiver')
        payee_el.send_keys(payee)
        payee_el.send_keys(Keys.RETURN)

        amt_el = Driver._chrome.find_element_by_id('expense-amount')
        amt_el.click()
        amt_el.send_keys(amount)

        Select(Driver._chrome.find_element_by_xpath('//*[@id="expenseCredit"]/form/fieldset/div[4]/div/select')) \
            .select_by_value(ENV[envelope.replace(' ', '_').upper()])

        if note:
            Driver._chrome.find_element_by_id('expense-notes').send_keys(note)

        Driver._click_save_txn()

    @staticmethod
    def add_income(date: str, payer: str, amount: str, note: str):
        Driver._click_add_txn()

        Driver._chrome.find_element_by_xpath(
            '//*[@id="myTab"]/li[3]/a').click()  # click income tab

        date_field = Driver._chrome.find_element_by_id('income-date')
        date_field.clear()
        date_field.send_keys(date)

        payer_el: WebElement = Driver._chrome.find_element_by_id(
            'income-payer')
        payer_el.send_keys(payer)
        payer_el.send_keys(Keys.RETURN)

        Driver._chrome.find_element_by_xpath(
            '//*[@id="income"]/form/fieldset/div[3]/div/input').send_keys(amount)  # income amt

        if note:
            Driver._chrome.find_element_by_id('income-notes').send_keys(note)

        Driver._click_save_txn()

class ChaseTxn:
    def __init__(self, is_debit: bool, date: str, title: str, amt: str):
        self.is_debit = is_debit
        self.date = date
        self.title = title
        self.amt = amt

class MatchedTxn:
    def __init__(self, ch_title: str, gb_title: str, gb_envelope: str):
        self.ch_title = ch_title
        self.gb_title = gb_title
        self.gb_envelope = gb_envelope

def is_correct_match(matched_txn: MatchedTxn):
    print(
        f'\tTitle: {matched_txn.gb_title}. Envelope: {matched_txn.gb_envelope}')
    answer = input('\tIs this correct? (yes): ')
    return not answer or answer.lower() in ['y', 'yes']

organized_txns = organize_txns()
chase_txns, both_txns = organized_txns.ch_txns, organized_txns.both_txns

# read txns
new_ch_txns: List[ChaseTxn] = [ChaseTxn(x._is_debit, x.date, x.title, str(abs(x.amt)/100)) for x in chase_txns]
matched_txns: List[MatchedTxn] = [MatchedTxn(x.ch_txn.title, x.gb_txn.title, x.gb_txn.envelope) for x in both_txns]

# reverse new_ch_txns to go from past to present
new_ch_txns.reverse()

Driver.login()

# make list of txns to add
for new_ch_txn in new_ch_txns:
    answer_if_should_add = input(f'Add {new_ch_txn.date}, {new_ch_txn.title}, {new_ch_txn.amt}? (yes):')
    if not answer_if_should_add or answer_if_should_add.lower() in ['y', 'yes']:
        # find txn in `matched_txns` with most similar chase title to `new_ch_txn`
        similar_txn: MatchedTxn = matched_txns[0]
        max_eq_chars = -1
        for matched_txn in matched_txns:
            i = 0
            while i < len(new_ch_txn.title) and i < len(matched_txn.ch_title) and new_ch_txn.title[i] == matched_txn.ch_title[i]:
                i += 1
            if i > max_eq_chars:
                max_eq_chars = i
                similar_txn = matched_txn

        # get info for this new txn
        while True:
            try:
                new_gb_title, new_gb_envelope = similar_txn.gb_title, similar_txn.gb_envelope
                if not is_correct_match(similar_txn):
                    readline.set_completer(title_completer)
                    new_gb_title = input('\tTitle: ')

                    if new_ch_txn.is_debit:
                        readline.set_completer(env_completer)
                        new_gb_envelope = input('\tEnvelope: ')

                    # add this new txn to `matched_txns` so that it could be guessed as a `similar_txn` for a future `new_ch_txn`
                    matched_txns.append(MatchedTxn(
                        ch_title=new_ch_txn.title, gb_title=new_gb_title, gb_envelope=new_gb_envelope))

                new_note = input('\tNote? (none): ')
                break
            except EOFError:
                # if user made a mistake, they press `Ctrl+D`, which will print a
                # new line and let them re-insert the information
                print('\n')

        # run selenium code to add to GB
        if new_ch_txn.is_debit:
            Driver.add_expense(new_ch_txn.date, new_gb_title,
                               new_ch_txn.amt, new_gb_envelope, new_note)
        else:
            Driver.add_income(new_ch_txn.date, new_gb_title,
                              new_ch_txn.amt, new_note)
