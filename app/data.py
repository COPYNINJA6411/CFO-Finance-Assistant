"""Stable synthetic sample data generator used for demo and local validation."""
from datetime import date
from decimal import Decimal
import random
import pandas as pd

REGIONS = ["North", "South", "East", "West"]
PRODUCTS = ["Analytics Suite", "Cloud Platform", "Advisory Services", "Payments Hub", "Security Stack"]
SEGMENTS = ["Enterprise", "Mid-Market", "SMB"]
MARKETS = {
    "US": {"name": "United States", "currency": "USD", "seed": 20261031, "low": 18_000, "high": 125_000},
    "IN": {"name": "India", "currency": "INR", "seed": 20311031, "low": 1_500_000, "high": 10_000_000},
}

def sample_data(market: str = "US") -> pd.DataFrame:
    """Generate one deterministic synthetic market dataset in its native currency.

    India figures are independently generated INR values, not USD converted at an
    assumed exchange rate. Both datasets deliberately share the same dimensions.
    """
    if market not in MARKETS: raise ValueError(f"Unsupported market: {market}")
    cfg=MARKETS[market]
    rng = random.Random(cfg["seed"])
    rows = []
    for year in range(2024, 2027):
      for month in range(1, 13):
        for region in REGIONS:
          for product in PRODUCTS:
            for segment in SEGMENTS:
              revenue = rng.randrange(cfg["low"], cfg["high"], 1000 if market=="US" else 100_000)
              rate = rng.uniform(.42, .72)
              # Intentional South margin deterioration in Q2 2026 for reproducible RCA.
              if region == "South" and year == 2026 and month in (4, 5, 6): rate -= .18
              cost = int(revenue * (1-rate))
              rows.append({"market": market, "currency": cfg["currency"], "date": date(year,month,1), "region": region, "product": product,
                           "segment": segment, "revenue": Decimal(revenue), "cost": Decimal(cost)})
    frame=pd.DataFrame(rows)
    frame["date"]=pd.to_datetime(frame["date"])
    return frame
