from typing import Dict, List


def truthful_bid(valuation: float) -> float:
    return valuation


def shaded_bid(valuation: float, shade: float = 0.8) -> float:
    return valuation * shade


def first_price_auction(bids: List[float]) -> Dict[str, float | int]:
    if not bids:
        return {"winner": -1, "price": 0.0}
    winner = max(range(len(bids)), key=lambda idx: bids[idx])
    return {"winner": winner, "price": bids[winner]}


def second_price_auction(bids: List[float]) -> Dict[str, float | int]:
    if not bids:
        return {"winner": -1, "price": 0.0}
    sorted_bids = sorted(((bid, idx) for idx, bid in enumerate(bids)), reverse=True)
    winner = sorted_bids[0][1]
    price = sorted_bids[1][0] if len(sorted_bids) > 1 else sorted_bids[0][0]
    return {"winner": winner, "price": price}
