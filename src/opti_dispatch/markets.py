from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import math

@dataclass
class Market:
    name: str
    prices: pd.Series # datetime index
    interval: pd.Timedelta # Unaffected by resampling 

    def __post_init__(self):
        if not isinstance(self.prices.index, pd.DatetimeIndex):
            raise TypeError("Prices must have a DatetimeIndex")

        if not self.prices.index.is_monotonic_increasing:
            raise ValueError("DatetimeIndex must be sorted")

        if self.prices.isna().values.any():
            raise ValueError("Prices contains NaNs")

    def upsample(self, freq: pd.Timedelta) -> "Market":
        # Extend time series so that final step is broken down rather than truncated
        extended_index = self.prices.index.append(pd.DatetimeIndex([self.prices.index[-1] + self.interval]))
        extended_prices = self.prices.reindex(extended_index)

        # Resample with extended index
        resampled = extended_prices.resample(freq).ffill()

        # There will only be one extra timestep added which needs to be trimmed
        resampled = resampled.iloc[:-1]

        return Market(name=self.name, prices=resampled, interval=self.interval)

# Assumes market time series have same start and end time
def align_market_freqs(markets: list[Market])->tuple[list[Market], pd.Timedelta]:
    freqs = [int(pd.Timedelta(m.interval).total_seconds()) for m in markets]
    # Highest common frequency = greatest common divisor
    hcf = pd.Timedelta(seconds=math.gcd(*freqs))
    resampled_markets = []
    for m in markets:
        m_r = m.upsample(hcf)
        resampled_markets.append(m_r)
    return resampled_markets, hcf