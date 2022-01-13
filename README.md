# Transaction Organizer, Goodbudget Bot Adder, and Transaction Statistic Grapher

## Function
* This repository has three main modules:
  1. Transaction Organizing module:
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
      it belongs to by using the list of transactions that both files have in common as a reference.
    * It will ask the user if its guess was correct. If not, the user can correctly enter the correct title and envelope.
    * In addition the user can enter a note.
    * The selenium bot will then automatically add it.
  3. Graphing module:
    * This module simply reads the input Goodbudget transaction file, gives you a few options about what you would like to see
      graphically, and outputs a matplotlib graph.

## Use:
* To use this program, you must have both a Chase account and a Goodbudget account.
* You must also download your transaction history files and place them under the `in` directory of this repository, and call
  them "chase.csv" and "goodbudget.csv".

* For the organizing module, run: `python3 main.py`
* For the adding module, run: `python3 main.py --add`
* For the graphing module, run: `python3 graphy.py`

## Possible Improvements
* Using Plaid:
  * Requiring a Chase account and making the user download files manually into a folder is not ideal.
  * With Plaid I may be able to process a user's past transactions, regardless of their bank, without making them download
    their transaction history.
  * Plaid is also nice in that the developer can continue not needing access to the users' personal bank account data.
* Using Spark:
  * All three modules run on a single thread.
  * I could probably use spark to parallelize reading the transactions and the matching and sorting algorithms behind the
    organizing module.
* Paritioning data to avoid overusing RAM:
  * I'm reading all the files and keeping their contents in memory as lists of classes. If these files were too big, the program
    wouldn't be able to hold all the data in RAM and it would crash.
  * To fix this I might have to split each file into chunks, process each chunk, and then aggregate in the output.
* Using a web server or a GUI to offer a better graphical interface:
  * It would be much nicer if this repo was an API endpoint or a downloadable app so that all the data handling logic could
    happen on some backend and the graphing logic on a user-friendly, interactive front-end.
