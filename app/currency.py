"""Presentation helpers for native-currency synthetic market data."""
from .data import MARKETS

def currency_symbol(market: str) -> str:
    return "₹" if market == "IN" else "$"

def format_amount(value, market: str) -> str:
    rounded=int(round(float(value)))
    if market != "IN": return f"${rounded:,}"
    digits=str(abs(rounded))
    if len(digits)<=3: grouped=digits
    else:
        last=digits[-3:]; rest=digits[:-3]; pairs=[]
        while rest:
            pairs.insert(0,rest[-2:]); rest=rest[:-2]
        grouped=",".join(pairs+[last])
    return f"{'-' if rounded<0 else ''}₹{grouped}"

def format_compact(value, market: str) -> str:
    amount=float(value)
    if market == "IN":
        if abs(amount)>=10_000_000: return f"₹{amount/10_000_000:,.1f}Cr"
        if abs(amount)>=100_000: return f"₹{amount/100_000:,.1f}L"
        return format_amount(amount,market)
    if abs(amount)>=1_000_000: return f"${amount/1_000_000:,.1f}M"
    if abs(amount)>=1_000: return f"${amount/1_000:,.0f}K"
    return format_amount(amount,market)
