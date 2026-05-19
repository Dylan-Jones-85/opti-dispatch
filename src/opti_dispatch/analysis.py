import pandas as pd
import numpy as np
from pyomo.environ import value


def compute_cashflow_trace(model, time_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Returns a DataFrame of cumulative cashflows with one column per market,
    a TOTAL column, and the actual datetime index.
    """
    dt = value(model.dt)
    data = {}

    for m in model.M:
        data[m] = [
            value(model.price[m, t]) * dt * (value(model.d[m, t]) - value(model.c[m, t]))
            for t in model.T
        ]

    df = pd.DataFrame(data, index=time_index)
    df["TOTAL"] = df.sum(axis=1)

    return df


def check_simul_charge_and_discharge(model, tol=1e-6) -> list[tuple]:
    violations = []

    for t in model.T:
        total_c = sum(value(model.c[m, t]) or 0.0 for m in model.M)
        total_d = sum(value(model.d[m, t]) or 0.0 for m in model.M)

        if total_c > tol and total_d > tol:
            violations.append((t, total_c, total_d))

    return violations


def check_capacity_limit(model, tol=1e-6) -> list[tuple]:
    violations = []
    capacity = value(model.capacity)

    for t in model.T:
        soc = value(model.soc[t]) or 0.0

        if soc < -tol or soc > capacity + tol:
            violations.append((t, soc))

    return violations


def check_power_limits(model, tol=1e-6) -> list[tuple]:
    violations = []
    max_charge = value(model.max_charge_rate)
    max_discharge = value(model.max_discharge_rate)

    for t in model.T:
        total_c = sum(value(model.c[m, t]) or 0.0 for m in model.M)
        total_d = sum(value(model.d[m, t]) or 0.0 for m in model.M)

        if total_c > max_charge + tol:
            violations.append(("charge", t, total_c))

        if total_d > max_discharge + tol:
            violations.append(("discharge", t, total_d))

    return violations


def compute_total_profit(cashflow_df: pd.DataFrame) -> float:
    return cashflow_df[cashflow_df["market"] == "TOTAL"]["cashflow"].sum()