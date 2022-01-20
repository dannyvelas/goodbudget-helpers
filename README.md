# Goodbudget Helpers

* This repo is based on a budgeting app called [Goodbudget](https://goodbudget.com/).

## Use Cases
* This repo has three main modules, one that matches Goodbudget transactions with Chase transactions, an adding module, and
  a graphing module.
* You would want to use the first module if, say, you've been a long-time user of Goodbudget and for some reason your balance
  on your account doesn't match that of your Chase account. In this case, you can use the organizing module to spot the
  transactions you should add to Goodbudget, or which ones you've added erroneously.
* With the adding module, you can also keep your Goodbudget updated without needing to constantly enter everything manually or
  worrying about entering anything wrong.
* With the graphing module, you can see more information about your spending habits and history, since, in my opinion, the
  graphing capabilities of Goodbudget fall short.

## API
* For the organizing module, run: `python3 main.py`
* For the adding module, run: `python3 main.py --add`
* For the graphing module, run: `python3 graphy.py`

## Requirements:
* To use this program, you must have both a Chase account and a Goodbudget account.
* You must also download your transaction history files and place them under the `in` directory of this repository, and call
  them "chase.csv" and "goodbudget.csv".
* You also have to set up the virtual environment with anything equivalent to: `pipenv shell`

## Module Descriptions
1. Goodbudget Transaction Organizing module:
    * This module reads a csv file of Chase transactions, a csv file of Goodbudget transactions, and prints out these lists
      in the form of files:
        * the transactions that both files have in common: `both.csv`
        * the transactions that the Chase file has, but the Goodbudget does not: `goodbudget.csv`
        * the transactions that the Goodbudget file has, but the Chase does not: `chase.csv`
    * This module prints out an additional file, which is a list of all of the transactions above,
      sorted by transaction time: `merged.csv`
    * These files are printed in a folder which will be named after the time at which you run the program.
    * This folder will be inside another folder called `out/`.
2. Goodbudget Bot Adding module:
    * This module depends on the Transaction Organizing module.
    * It reads the transactions that the Chase file has, but the Goodbudget file does not, and adds them to Goodbudget, using
      a Selenium bot.
    * It will only add the Chase transactions that are newer than every transaction in the input Goodbudget transaction file.
    * For each Chase transaction, this module will try to guess the Goodbudget title of each transaction and the envelope that
      it belongs to, by using the list of transactions that both files have in common as a reference.
    * It will ask the user if its guess was correct. If not, the user can correctly enter the correct title and envelope.
    * In addition the user can enter a note.
    * The selenium bot will then automatically add it.
3. Goodbudget Transaction Graphing module:
    * This module simply reads the input Goodbudget transaction file, gives you a few options about what you would like to see
      graphically, and outputs a matplotlib graph.

## Possible Improvements
* Using a web server or a GUI to offer a better graphical interface:
    * It would be much nicer if this repo was an API endpoint or a downloadable app so that all the data handling logic could
      happen on some backend and the graphing logic on a user-friendly, interactive front-end.
    * As it stands this repo is just for people with python3, a goodbudget account, and enough willpower to keep it updated
      (a very small Venn diagram).
* Using Plaid:
    * Requiring a Chase account and making the user download files manually into a folder is not ideal.
    * With Plaid I may be able to process a user's past transactions, regardless of their bank, without making them download
      their transaction history.
    * Plaid is also nice in that the developer can continue not needing access to the users' personal bank account data.
* Using Spark:
    * All three modules run on a single thread.
    * I could probably use spark to parallelize reading the transactions and the matching and sorting algorithms behind the
      organizing module.
* Partitioning data to avoid overusing RAM:
    * I'm reading all the files and keeping their contents in memory as lists of classes. If these files were too big, the program
      wouldn't be able to hold all the data in RAM and it would crash.
    * To fix this I might have to split each file into chunks, process each chunk, and then aggregate in the output.
* Using a better data structure when guessing the names and envelopes of new transactions:
    * At the moment, when the program reads a candidate transaction to add, it guesses the name and envelope it should have.
      To make this guess, the program reads the list of all the Chase transactions and looks for one with the most similar name.
      Once it finds it, it uses the name and envelope that that transaction was given in Goodbudget as a guess.
    * The program must read the entire list of Chase transactions for every transaction that will be added. If the amount of
      transactions to be added is n, and the amount of Chase transactions is k, then the runtime is Θ(nk).
    * I think that if I stored the Chase transactions and their Goodbudget equivalents in a data structure which optimizes for
      string seaches using the Levenshtein distance algorithm, I might be able to improve the runtime when searching for a
      similarly-named transaction.
* Using AI to guess the name and envelope of a new transaction:
    * I could parametrize the names of transactions and their envelopes, so that when the program reads a new transaction
      with a particular name, it can guess what name and envelope that new transaction should have, using historical matches.
    * However, this becomes hard for transaction titles like "Venmo" or "Amazon" that don't carry much information and can
      belong to any envelope.
    * So, I would have to parametrize on other data points with a pattern that may be a bit harder to notice, like the time of day
      or the transaction amount. In other words, if I tend to shop for groceries on Friday afternoons and spend around $100, it
      would be nice if I could record this so that if the program saw an Amazon Friday 8pm purchase of $105, it would be more
      inclined to guess it belongs in the grocery envelope than if it saw an Amazon transaction on a Tuesday, with an amount
      of $17.
