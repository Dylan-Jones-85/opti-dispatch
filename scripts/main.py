import pandas as pd
from dataclasses import dataclass
from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market, align_market_freqs
import math

battery = BatterySpec(2, 2, 4)

battery_info = pd.read_csv('data/battery_spec.csv')

market1_ts = pd.read_csv('data/market1_data.csv', index_col="Time")
market1_ts.index = pd.to_datetime(market1_ts.index, dayfirst=True)
# Correct for Market 1 DST anomalies
market1_UTC_index = pd.date_range(start=market1_ts.index[0], end=market1_ts.index[-1], freq="30min")
assert len(market1_UTC_index) == len(market1_ts.index)
market1_ts.index = market1_UTC_index
m1 = Market(name="M1", prices=market1_ts, market_freq = pd.Timedelta("30min"))

market2_ts = pd.read_csv('data/market2_data.csv', index_col="Time").dropna()
market2_ts.index = pd.to_datetime(market2_ts.index, dayfirst=True)
m2 = Market(name="M2", prices = market2_ts, market_freq = pd.Timedelta("1h"))

# Align market frequencies for MILP DVs
markets = align_market_freqs([m1,m2])

