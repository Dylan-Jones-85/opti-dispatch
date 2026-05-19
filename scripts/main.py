'''Example script for using opti-dispatch with pyomo'''
import pandas as pd
from pyomo.environ import SolverFactory, value

from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market
from opti_dispatch.optimisation.arbitrage_models import build_MILP_arb_model, build_linear_arb_model

print("Loading input data...")
battery = BatterySpec.from_csv('data/battery_spec.csv')

market1_ts = pd.read_csv('data/market1_data.csv', index_col="Time")
market1_ts.index = pd.to_datetime(market1_ts.index, dayfirst=True)
# Correct for Market 1 DST anomalies
market1_UTC_index = pd.date_range(start=market1_ts.index[0], end=market1_ts.index[-1], freq="30min")
assert len(market1_UTC_index) == len(market1_ts.index)
market1_ts.index = market1_UTC_index
m1 = Market(name="M1", prices=market1_ts, interval = pd.Timedelta("30min"))

market2_ts = pd.read_csv('data/market2_data.csv', index_col="Time").dropna()
market2_ts.index = pd.to_datetime(market2_ts.index, dayfirst=True)
m2 = Market(name="M2", prices = market2_ts, interval = pd.Timedelta("1h"))

# Align market frequencies for MILP DVs
markets = [m1,m2]

print("Building pyomo model...")
# Limit number of timesteps to solve for to allow quick local runs
t_start = pd.Timestamp("2020-11-1")
t_end = pd.Timestamp("2020-12-1")
arb_model = build_MILP_arb_model(markets=markets, battery=battery, t_start=t_start, t_end=t_end)

print("Solving pyomo model...")
solver = SolverFactory("highs")
results = solver.solve(arb_model)

from pyomo.contrib.solver.common.results import TerminationCondition

if results.solver.termination_condition == TerminationCondition.optimal:
    print("Optimal solution found!")

    print("Analysing results")
    results_df = pd.DataFrame(index=markets[0].prices.loc[t_start:t_end].index, data={
        "soc":[value(arb_model.soc[t]) for t in arb_model.T],
        "c30":[value(arb_model.c[markets[0].name, t]) for t in arb_model.T],
        "d30":[-1*value(arb_model.d[markets[0].name, t]) for t in arb_model.T],
        "c60":[value(arb_model.c[markets[1].name, t]) for t in arb_model.T],
        "d60":[-1*value(arb_model.d[markets[1].name, t]) for t in arb_model.T],
    })

    results_df.tail(100).plot()


    from opti_dispatch.analysis import compute_cashflow_trace, check_simul_charge_and_discharge, check_capacity_limit, check_power_limits, compute_total_profit
    import numpy as np

    simul_c_and_d_violation = any(check_simul_charge_and_discharge(arb_model))
    print(f"Simul charge and discharge check: {"FAILED" if simul_c_and_d_violation else "PASSED"}")
    capacity_violation = any(check_capacity_limit(arb_model))
    print(f"Simul charge and discharge check: {"FAILED" if capacity_violation else "PASSED"}")
    power_flow_violation = any(check_power_limits(arb_model))
    print(f"Simul charge and discharge check: {"FAILED" if power_flow_violation else "PASSED"}")

    time_index = m1.prices.loc[t_start:t_end].index
    cashflow_df = compute_cashflow_trace(arb_model, time_index)
    cashflow_df.cumsum().plot()
    print(f"Total profit in {t_end-t_start} = £{np.round(cashflow_df['TOTAL'].iloc[-1])}")

else:
    print("Optimisation failed.")
    