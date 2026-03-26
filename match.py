from functools import cmp_to_key
from typing import Dict, List

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    YnabTxn,
    MergedTxn,
    MergedTxn_BothTxns,
    MergedTxn_ChaseTxn,
    MergedTxn_YnabTxn,
    TxnsGrouped,
)

MAX_DAYS_APART = 7


def _sort_merged_txns(merged_txns: List[MergedTxn]) -> List[MergedTxn]:
    def get_yn_id(txn: MergedTxn) -> int:
        if isinstance(txn, MergedTxn_ChaseTxn):
            return 1
        else:
            return -txn.ynab_txn.id_

    def compare(txn_1: MergedTxn, txn_2: MergedTxn):
        def get_ts(txn: MergedTxn):
            if isinstance(txn, MergedTxn_ChaseTxn):
                return txn.ch_txn.ts
            else:
                return txn.ynab_txn.ts

        if not isinstance(txn_1, MergedTxn_ChaseTxn) and not isinstance(
            txn_2, MergedTxn_ChaseTxn
        ):
            return -1 if txn_1.ynab_txn.id_ > txn_2.ynab_txn.id_ else 1
        elif not isinstance(txn_1, MergedTxn_YnabTxn) and not isinstance(
            txn_2, MergedTxn_YnabTxn
        ):
            return -1 if txn_1.ch_txn.id_ > txn_2.ch_txn.id_ else 1
        else:
            txn_1_ts = get_ts(txn_1)
            txn_2_ts = get_ts(txn_2)
            if txn_1_ts < txn_2_ts:
                return -1
            elif txn_1_ts > txn_2_ts:
                return 1
            else:
                return 0

    sorted_by_yn_id = sorted(merged_txns, key=get_yn_id)
    return sorted(sorted_by_yn_id, key=cmp_to_key(compare))


def get_txns_grouped(
    ch_txns: List[ChaseTxn],
    ynab_txns: List[YnabTxn],
    ch_start_bal: int,
    yn_start_bal: int,
) -> TxnsGrouped:
    # sort by amount, on a tie, give priority to the earlier txn
    ch_sorted = sorted(ch_txns, key=lambda x: (x.amt_cents, -x.id_))
    yn_sorted = sorted(ynab_txns, key=lambda x: (x.amt_cents, -x.id_))

    # merge chase txns and yn txns
    merged_txns: List[MergedTxn] = []
    ch_i, yn_i = 0, 0
    while ch_i < len(ch_sorted) and yn_i < len(yn_sorted):
        ch_txn, ynab_txn = ch_sorted[ch_i], yn_sorted[yn_i]
        if ch_txn.amt_cents < ynab_txn.amt_cents:
            merged_txns.append(MergedTxn_ChaseTxn(ch_txn))
            ch_i += 1
        elif ch_txn.amt_cents > ynab_txn.amt_cents:
            merged_txns.append(MergedTxn_YnabTxn(ynab_txn))
            yn_i += 1
        else:
            days_apart = (ynab_txn.ts - ch_txn.ts) / (60 * 60 * 24)
            if days_apart < (MAX_DAYS_APART * -1):
                # if yn too far in past, add it by itself
                merged_txns.append(MergedTxn_YnabTxn(ynab_txn))
                yn_i += 1
            elif days_apart > MAX_DAYS_APART:
                # if ch too far in past, add it by itself
                merged_txns.append(MergedTxn_ChaseTxn(ch_txn))
                ch_i += 1
            else:
                merged_txns.append(MergedTxn_BothTxns(ch_txn, ynab_txn))
                ch_i += 1
                yn_i += 1

    # if there are some txns left in one list but not the other,
    # add those txns individually
    while ch_i < len(ch_sorted):
        merged_txns.append(MergedTxn_ChaseTxn(ch_sorted[ch_i]))
        ch_i += 1
    while yn_i < len(yn_sorted):
        merged_txns.append(MergedTxn_YnabTxn(yn_sorted[yn_i]))
        yn_i += 1

    # sort by earliest txn
    merged_txns_sorted = _sort_merged_txns(merged_txns)

    # set MergedTxn.bal_diff
    bal_diff_freq: Dict[int, int] = {}
    ch_bal, yn_bal = ch_start_bal, yn_start_bal
    for merged_txn in merged_txns_sorted:
        if isinstance(merged_txn, (MergedTxn_ChaseTxn, MergedTxn_BothTxns)):
            ch_bal += merged_txn.ch_txn.amt_cents
            merged_txn.ch_txn.bal = ch_bal
        if isinstance(merged_txn, (MergedTxn_YnabTxn, MergedTxn_BothTxns)):
            yn_bal += merged_txn.ynab_txn.amt_cents
            merged_txn.ynab_txn.bal = yn_bal

        # store in dict:
        # NEGATIVE: CHASE IS LOWER THAN YNAB
        # POSITIVE: CHASE IS HIGHER THAN YNAB
        diff = ch_bal - yn_bal
        if diff in bal_diff_freq:
            bal_diff_freq[diff] += 1
        else:
            bal_diff_freq[diff] = 1

        merged_txn.bal_diff = diff

    # sort by balance differences that occur the most and store in its own class
    bal_diff_freq_sorted = [
        BalanceDifferenceFrequency(x[0], x[1])
        for x in sorted(bal_diff_freq.items(), key=lambda item: item[1], reverse=True)
    ]

    # split merged_txns into 3 different lists
    only_ch_txns: List[ChaseTxn] = []
    only_ynab_txns: List[YnabTxn] = []
    both_txns: List[MergedTxn_BothTxns] = []
    for txn in merged_txns_sorted:
        if isinstance(txn, MergedTxn_ChaseTxn):
            only_ch_txns.append(txn.ch_txn)
        elif isinstance(txn, MergedTxn_YnabTxn):
            only_ynab_txns.append(txn.ynab_txn)
        else:
            both_txns.append(txn)

    # restore sorting of only_ch_txns and only_ynab_txns by using
    # the id they were given when they were read
    # reverse=True because the smaller the ID, the newer the txn and
    # we want the older txns first
    only_ch_txns_ssorted = sorted(only_ch_txns, key=lambda x: -x.id_)
    only_ynab_txns_ssorted = sorted(only_ynab_txns, key=lambda x: -x.id_)

    return TxnsGrouped(
        only_ch_txns=only_ch_txns_ssorted,
        only_ynab_txns=only_ynab_txns_ssorted,
        both_txns=both_txns,
        merged_txns=merged_txns_sorted,
        bal_diff_freq=bal_diff_freq_sorted,
    )
