import pandas as pd
from dataclasses import dataclass
from opti_dispatch.battery import Battery

battery = Battery(2, 2, 4)

battery_info = pd.read_csv('data/battery_spec.csv')
market1_ts = pd.read_csv('data/market1_data.csv', index_col="Time")
market2_ts = pd.read_csv('data/market2_data.csv', index_col="Time")

