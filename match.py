from functools import cmp_to_key
from typing import Dict, List

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    GoodbudgetTxn,
    MergedTxn,
    TxnType,
    TxnsGrouped,
)


def _sort_merged_txns(merged_txns: List[MergedTxn]) -> List[MergedTxn]:
    def compare(txn_1: MergedTxn, txn_2: MergedTxn):
        def get_ts(txn: MergedTxn):
            if txn.type_ == TxnType.CHASE:
                return txn.ch_txn.ts
            else:
                return txn.gb_txn.ts

        if txn_1.type_ != TxnType.CHASE and txn_2.type_ != TxnType.CHASE:
            return -1 if txn_1.gb_txn.id_ > txn_2.gb_txn.id_ else 1
        elif txn_1.type_ == TxnType.CHASE and txn_2.type_ == TxnType.CHASE:
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

    return sorted(merged_txns, key=cmp_to_key(compare))


def get_txns_grouped(ch_txns: List[ChaseTxn], gb_txns: List[GoodbudgetTxn],
                     ch_start_bal: int, gb_start_bal: int,
                     max_days_apart: int) -> TxnsGrouped:
    # sort by amount, on a tie, give priority to the earlier txn
    ch_sorted = sorted(ch_txns, key=lambda x: (x.amt_cents, -x.id_))
    gb_sorted = sorted(gb_txns, key=lambda x: (x.amt_cents, -x.id_))

    # merge chase txns and gb txns
    merged_txns: List[MergedTxn] = []
    ch_i, gb_i = 0, 0
    while ch_i < len(ch_sorted) and gb_i < len(gb_sorted):
        ch_txn, gb_txn = ch_sorted[ch_i], gb_sorted[gb_i]
        if ch_txn.amt_cents < gb_txn.amt_cents:
            merged_txns.append(MergedTxn(ch_txn))
            ch_i += 1
        elif ch_txn.amt_cents > gb_txn.amt_cents:
            merged_txns.append(MergedTxn(gb_txn))
            gb_i += 1
        else:
            days_apart = (gb_txn.ts - ch_txn.ts) / (60 * 60 * 24)
            if days_apart < (max_days_apart * -1):
                # if gb too far in past, add it by itself
                merged_txns.append(MergedTxn(gb_txn))
                gb_i += 1
            elif days_apart > max_days_apart:
                # if ch too far in past, add it by itself
                merged_txns.append(MergedTxn(ch_txn))
                ch_i += 1
            else:
                merged_txns.append(MergedTxn(ch_txn, gb_txn))
                ch_i += 1
                gb_i += 1

    # if there are some txns left in one list but not the other,
    # add those txns individually
    while ch_i < len(ch_sorted):
        merged_txns.append(MergedTxn(ch_sorted[ch_i]))
        ch_i += 1
    while gb_i < len(gb_sorted):
        merged_txns.append(MergedTxn(gb_sorted[gb_i]))
        gb_i += 1

    # sort by earliest txn
    merged_txns_sorted = _sort_merged_txns(merged_txns)

    # set bal and MergedTxn.bal_diff
    bal_diff_freq: Dict[int, int] = {}
    ch_bal, gb_bal = ch_start_bal, gb_start_bal
    for merged_txn in merged_txns_sorted:
        if merged_txn.type_ in [TxnType.CHASE, TxnType.BOTH]:
            ch_bal += merged_txn.ch_txn.amt_cents
            merged_txn.ch_txn.bal = ch_bal
        if merged_txn.type_ in [TxnType.GOODBUDGET, TxnType.BOTH]:
            gb_bal += merged_txn.gb_txn.amt_cents
            merged_txn.gb_txn.bal = gb_bal

        # store in dict:
        # NEGATIVE: CHASE IS LOWER THAN GOODBUDGET
        # POSITIVE: CHASE IS HIGHER THAN GOODBUDGET
        diff = ch_bal - gb_bal
        if diff in bal_diff_freq:
            bal_diff_freq[diff] += 1
        else:
            bal_diff_freq[diff] = 1

        merged_txn.bal_diff = diff

    # sort by balance differences that occur the most and store in its own class
    bal_diff_freq_sorted = [BalanceDifferenceFrequency(x[0], x[1])
                            for x in sorted(bal_diff_freq.items(),
                                            key=lambda item: item[1],
                                            reverse=True)]

    # split merged_txns into 3 different lists
    only_ch_txns: List[ChaseTxn] = []
    only_gb_txns: List[GoodbudgetTxn] = []
    both_txns: List[MergedTxn] = []
    for txn in merged_txns_sorted:
        if txn.type_ == TxnType.CHASE:
            only_ch_txns.append(txn.ch_txn)
        elif txn.type_ == TxnType.GOODBUDGET:
            only_gb_txns.append(txn.gb_txn)
        else:
            both_txns.append(txn)

    # restore sorting of only_ch_txns and only_gb_txns by using
    # the id they were given when they were read
    # reverse=True because the smaller the ID, the newer the txn and
    # we want the older txns first
    only_ch_txns_ssorted = sorted(
        only_ch_txns, key=lambda x: x.id_, reverse=True)
    only_gb_txns_ssorted = sorted(
        only_gb_txns, key=lambda x: x.id_, reverse=True)

    return TxnsGrouped(
        only_ch_txns=only_ch_txns_ssorted,
        only_gb_txns=only_gb_txns_ssorted,
        both_txns=both_txns,
        merged_txns=merged_txns_sorted,
        bal_diff_freq=bal_diff_freq_sorted)
