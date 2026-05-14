from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import math

@dataclass
class Market:
    name: str
    prices: pd.Series # datetime index
    market_freq: pd.Timedelta # Unaffected by resampling 

    def __post_init__(self):
        if not isinstance(self.prices.index, pd.DatetimeIndex):
            raise TypeError("Prices must have a DatetimeIndex")

        if not self.prices.index.is_monotonic_increasing:
            raise ValueError("DatetimeIndex must be sorted")

        if self.prices.isna().values.any():
            raise ValueError("Prices contains NaNs")

    def upsample(self, freq: pd.Timedelta) -> "Market":
        resampled_prices = self.prices.resample(freq).ffill()
        return Market(name=self.name, prices=resampled_prices, market_freq=self.market_freq)
    
def align_market_freqs(markets: list[Market]):
    freqs = [int(pd.Timedelta(m.market_freq).total_seconds()) for m in markets]
    # Highest common frequency = greatest common divisor
    hcf = pd.Timedelta(seconds=math.gcd(*freqs))
    resampled_markets = []
    for m in markets:
        m_r = m.upsample(hcf)
        resampled_markets.append(m_r)
    return resampled_markets