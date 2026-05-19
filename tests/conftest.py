import pandas as pd
import pytest
from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market


@pytest.fixture
def battery():
    return BatterySpec(max_charge_rate=2.0, max_discharge_rate=2.0, capacity=4.0)


@pytest.fixture
def half_hourly_index():
    return pd.date_range("2020-01-01", periods=48, freq="30min")


@pytest.fixture
def hourly_index():
    return pd.date_range("2020-01-01", periods=24, freq="1h")


@pytest.fixture
def quarter_hourly_index():
    return pd.date_range("2020-01-01", periods=96, freq="15min")


@pytest.fixture
def m1(half_hourly_index):
    prices = pd.DataFrame({"price": [50.0] * 48}, index=half_hourly_index)
    return Market(name="M1", prices=prices, interval=pd.Timedelta("30min"))


@pytest.fixture
def m2(hourly_index):
    prices = pd.DataFrame({"price": [50.0] * 24}, index=hourly_index)
    return Market(name="M2", prices=prices, interval=pd.Timedelta("1h"))


@pytest.fixture
def m3(quarter_hourly_index):
    prices = pd.DataFrame({"price": [50.0] * 96}, index=quarter_hourly_index)
    return Market(name="M3", prices=prices, interval=pd.Timedelta("15min"))


@pytest.fixture
def m1_alternating(half_hourly_index):
    """M1 with alternating low/high prices to incentivise arbitrage."""
    prices = [10.0, 90.0] * 24
    return Market(
        name="M1",
        prices=pd.DataFrame({"price": prices}, index=half_hourly_index),
        interval=pd.Timedelta("30min"),
    )
