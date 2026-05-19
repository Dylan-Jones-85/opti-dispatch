import pandas as pd
import pytest
from opti_dispatch.markets import Market, align_market_freqs


# Market validation
def test_market_rejects_non_datetime_index():
    prices = pd.DataFrame({"price": [1.0, 2.0]}, index=[0, 1])
    with pytest.raises(TypeError, match="DatetimeIndex"):
        Market(name="M", prices=prices, interval=pd.Timedelta("30min"))


def test_market_rejects_unsorted_index():
    index = pd.to_datetime(["2020-01-01 01:00", "2020-01-01 00:00"])
    prices = pd.DataFrame({"price": [1.0, 2.0]}, index=index)
    with pytest.raises(ValueError, match="sorted"):
        Market(name="M", prices=prices, interval=pd.Timedelta("30min"))


def test_market_rejects_nans():
    index = pd.date_range("2020-01-01", periods=3, freq="30min")
    prices = pd.DataFrame({"price": [1.0, float("nan"), 3.0]}, index=index)
    with pytest.raises(ValueError, match="NaN"):
        Market(name="M", prices=prices, interval=pd.Timedelta("30min"))


def test_market_valid_construction(m1):
    assert m1.name == "M1"
    assert isinstance(m1.prices.index, pd.DatetimeIndex)
    assert len(m1.prices) == 48


# Market.upsample
def test_upsample_scales_length(m2):
    doubled = m2.upsample(pd.Timedelta("30min"))
    quadroupled = m2.upsample(pd.Timedelta("15min"))
    assert len(doubled.prices) == len(m2.prices) * 2
    assert len(quadroupled.prices) == len(m2.prices) * 4


def test_upsample_forward_fills_values(m2):
    upsampled = m2.upsample(pd.Timedelta("30min"))
    for i in range(len(m2.prices)):
        assert upsampled.prices.iloc[i * 2, 0] == m2.prices.iloc[i, 0]
        assert upsampled.prices.iloc[i * 2 + 1, 0] == m2.prices.iloc[i, 0]


def test_upsample_same_freq_is_identity(m1):
    upsampled = m1.upsample(pd.Timedelta("30min"))
    pd.testing.assert_frame_equal(upsampled.prices, m1.prices)


# align_market_freqs
def test_align_returns_hcf_freq(m1, m2):
    _, freq = align_market_freqs([m1, m2])
    assert freq == pd.Timedelta("30min")


def test_align_single_market_unchanged(m1):
    aligned, freq = align_market_freqs([m1])
    assert freq == pd.Timedelta("30min")
    assert len(aligned[0].prices) == len(m1.prices)


def test_align_upsamples_lower_freq_market(m1, m2):
    aligned, _ = align_market_freqs([m1, m2])
    # M2 should be upsampled to match M1's length
    assert len(aligned[0].prices) == len(aligned[1].prices)
