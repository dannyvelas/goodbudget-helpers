from operator import attrgetter
from typing import Dict, List

from datatypes import (
    BalanceDifferenceFrequency,
    ChaseTxn,
    GoodbudgetTxn,
    MergedTxn,
    TxnsGrouped,
    TxnsGroupedInfo,
    TxnType,
)

MAX_DAYS_APART = 7
CH_START_BAL = 362335
GB_START_BAL = 0


def get_txns_grouped_info(ch_txns: List[ChaseTxn], gb_txns: List[GoodbudgetTxn]) -> TxnsGroupedInfo:
    # sort by amount
    ch_txns.sort(key=attrgetter('amt', '_ts', 'title'))
    gb_txns.sort(key=attrgetter('amt', '_ts', 'title'))

    # merge chase txns and gb txns
    merged_txns: List[MergedTxn] = []
    ch_i, gb_i = 0, 0
    while ch_i < len(ch_txns) and gb_i < len(gb_txns):
        ch_txn, gb_txn = ch_txns[ch_i], gb_txns[gb_i]
        if ch_txn.amt < gb_txn.amt:
            merged_txns.append(MergedTxn(ch_txn))
            ch_i += 1
        elif ch_txn.amt > gb_txn.amt:
            merged_txns.append(MergedTxn(gb_txn))
            gb_i += 1
        else:
            days_apart = (gb_txn._ts - ch_txn._ts) / (60 * 60 * 24)
            if days_apart < (MAX_DAYS_APART * -1):
                # if gb too far in past, add it by itself
                merged_txns.append(MergedTxn(gb_txn))
                gb_i += 1
            elif days_apart > MAX_DAYS_APART:
                # if ch too far in past, add it by itself
                merged_txns.append(MergedTxn(ch_txn))
                ch_i += 1
            else:
                merged_txns.append(MergedTxn(ch_txn, gb_txn))
                ch_i += 1
                gb_i += 1

    # if there are some txns left in one list but not the other,
    # add those txns individually
    while ch_i < len(ch_txns):
        merged_txns.append(MergedTxn(ch_txns[ch_i]))
        ch_i += 1
    while gb_i < len(gb_txns):
        merged_txns.append(MergedTxn(gb_txns[gb_i]))
        gb_i += 1

    # sort by date and title
    merged_txns = sorted(merged_txns, key=lambda x: x.to_ts_and_title_tuple())

    # set SingleTxn.bal and MergedTxn.bal_diff
    bal_diff_freq: Dict[int, int] = {}
    ch_bal, gb_bal = CH_START_BAL, GB_START_BAL
    for merged_txn in merged_txns:
        if merged_txn.type_ in [TxnType.CHASE, TxnType.BOTH]:
            ch_bal += merged_txn.ch_txn.amt
            merged_txn.ch_txn.bal = ch_bal
        if merged_txn.type_ in [TxnType.GOODBUDGET, TxnType.BOTH]:
            gb_bal += merged_txn.gb_txn.amt
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

    # sort by balance differences that occur the most
    bal_diff_freq_sorted = [BalanceDifferenceFrequency(x)
                            for x in sorted(bal_diff_freq.items(),
                            key=lambda item: item[1], reverse=True)]

    # split merged_txns into 3 different lists
    only_ch_txns: List[ChaseTxn] = []
    only_gb_txns: List[GoodbudgetTxn] = []
    both_txns: List[MergedTxn] = []
    for txn in merged_txns:
        if txn.type_ == TxnType.CHASE:
            only_ch_txns.append(txn.ch_txn)
        elif txn.type_ == TxnType.GOODBUDGET:
            only_gb_txns.append(txn.gb_txn)
        else:
            both_txns.append(txn)

    txns_grouped = TxnsGrouped(
        only_ch_txns=only_ch_txns,
        only_gb_txns=only_gb_txns,
        both_txns=both_txns,
        merged_txns=merged_txns)

    return TxnsGroupedInfo(
        txns_grouped=txns_grouped,
        bal_diff_freq=bal_diff_freq_sorted,
        amt_unmatched_ch_txns=len(only_ch_txns),
        amt_unmatched_gb_txns=len(only_gb_txns),
        amt_matched_txns=len(both_txns),
        last_gb_txn_ts=gb_txns[-1]._ts if len(gb_txns) > 0 else 0)
