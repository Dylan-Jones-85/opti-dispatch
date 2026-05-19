import pandas as pd
import pytest
from pyomo.environ import SolverFactory, value

from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market
from opti_dispatch.optimisation.arbitrage_models import build_linear_arb_model,build_MILP_arb_model

solver = SolverFactory("highs")

def solve(model):
    results = solver.solve(model)
    return results


# Model construction
def test_linear_model_builds(m1, battery):
    model = build_linear_arb_model([m1], battery)
    assert hasattr(model, "soc_constraint")
    assert hasattr(model, "charge_limit_constraint")
    assert hasattr(model, "discharge_limit_constraint")
    assert hasattr(model, "objective")


def test_MILP_model_builds(m2, m3, battery):
    model = build_MILP_arb_model([m2,m3], battery)
    assert hasattr(model, "soc_constraint")
    assert hasattr(model, "charge_limit_constraint")
    assert hasattr(model, "discharge_limit_constraint")
    assert hasattr(model, "objective")


def test_timeseries_slicing(m1, battery):
    t_start = pd.Timestamp("2020-01-01 06:00")
    t_end = pd.Timestamp("2020-01-01 12:00")
    model = build_linear_arb_model([m1], battery, t_start=t_start, t_end=t_end)
    expected_steps = len(m1.prices.loc[t_start:t_end])
    assert len(list(model.T)) == expected_steps


# SOC modelling
def test_soc_initialises_at_zero(m1, battery):
    """SOC at t=0 should equal charge minus discharge over first interval."""
    model = build_linear_arb_model([m1], battery)
    solve(model)
    soc_0 = value(model.soc[0])
    c_0 = value(model.c["M1", 0])
    d_0 = value(model.d["M1", 0])
    dt = value(model.dt)
    assert soc_0 == pytest.approx(dt * (c_0 - d_0), abs=1e-6)


def test_soc_never_exceeds_capacity(m1_alternating, battery):
    model = build_linear_arb_model([m1_alternating], battery)
    solve(model)
    for t in model.T:
        assert value(model.soc[t]) <= battery.capacity + 1e-6


def test_soc_never_negative(m1_alternating, battery):
    model = build_linear_arb_model([m1_alternating], battery)
    solve(model)
    for t in model.T:
        assert value(model.soc[t]) >= -1e-6


# Power limits
def test_total_charge_never_exceeds_max_rate(m1_alternating, battery):
    model = build_linear_arb_model([m1_alternating], battery)
    solve(model)
    for t in model.T:
        total_c = sum(value(model.c[m, t]) for m in model.M)
        assert total_c <= battery.max_charge_rate + 1e-6


def test_total_discharge_never_exceeds_max_rate(m1_alternating, battery):
    model = build_linear_arb_model([m1_alternating], battery)
    solve(model)
    for t in model.T:
        total_d = sum(value(model.d[m, t]) for m in model.M)
        assert total_d <= battery.max_discharge_rate + 1e-6


# Charge/discharge exclusivity
def test_milp_no_simultaneous_charge_discharge(m1, m2, battery):
    model = build_MILP_arb_model([m1, m2], battery)
    solve(model)
    for t in model.T:
        total_c = sum(value(model.c[m, t]) for m in model.M)
        total_d = sum(value(model.d[m, t]) for m in model.M)
        assert total_c * total_d == pytest.approx(0.0, abs=1e-6)


# Market commitment
def test_market_commitment_m2_constant_within_hour(m1, m2, battery):
    """M2 charge and discharge must be identical in both half-hour slots
    within each hour."""
    model = build_linear_arb_model([m1, m2], battery)
    solve(model)
    n = len(list(model.T))
    for t in range(0, n - 1, 2):
        if t + 1 in model.T:
            assert value(model.c["M2", t]) == pytest.approx(value(model.c["M2", t + 1]), abs=1e-6)
            assert value(model.d["M2", t]) == pytest.approx(value(model.d["M2", t + 1]), abs=1e-6)


# Known-optimum tests
def test_flat_prices_zero_revenue(battery):
    """With identical prices across all timesteps there is no arbitrage
    opportunity and optimal revenue should be zero."""
    index = pd.date_range("2020-01-01", periods=4, freq="30min")
    prices = pd.DataFrame({"price": [50.0] * 4}, index=index)
    m = Market(name="M1", prices=prices, interval=pd.Timedelta("30min"))
    model = build_linear_arb_model([m], battery)
    solve(model)
    assert value(model.objective) == pytest.approx(0.0, abs=1e-6)


def test_single_cycle_known_revenue(battery):
    """Two timesteps: charge at 10 £/MWh, discharge at 90 £/MWh.
    Battery: 2 MW max rate, 4 MWh capacity, dt=0.5h.

    Optimal: charge 2 MW for 0.5h = 1 MWh stored, discharge 2 MW for 0.5h.
    Revenue = 2 * 0.5 * 90 - 2 * 0.5 * 10 = 90 - 10 = £80
    """
    index = pd.date_range("2020-01-01", periods=2, freq="30min")
    prices = pd.DataFrame({"price": [10.0, 90.0]}, index=index)
    m = Market(name="M1", prices=prices, interval=pd.Timedelta("30min"))
    model = build_linear_arb_model([m], battery)
    solve(model)
    assert value(model.objective) == pytest.approx(80.0, abs=1e-6)
