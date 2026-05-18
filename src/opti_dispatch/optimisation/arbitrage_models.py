'''Pre-configured pyomo model-building functions for battery arbitrage problems'''
from pyomo.environ import *
from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market, align_market_freqs
from opti_dispatch.optimisation.rules import *


def build_linear_arb_model(markets: list[Market], battery: BatterySpec, t_start=None, t_end=None)->ConcreteModel:
    '''Simple battery arbitrage model which allows simultaneous charging and discharging,
    reducing the MILP problem to a LP one. For single markets, the linear model should
    produce the same result as the MILP model as simultaneous charge and discharge is
    not optimal.'''
    markets, freq = align_market_freqs(markets)
    dt = freq.seconds/3600

    model = ConcreteModel()

    if t_start is None:
        t_start = markets[0].prices.index[0]
    if t_end is None:
        t_end = markets[0].prices.index[-1]

    sliced_prices = {m.name: m.prices.loc[t_start:t_end] for m in markets}

    T = range(len(sliced_prices[markets[0].name]))

    price_lookup = {
        (m.name, t): price
        for m in markets
        for t, price in enumerate(sliced_prices[m.name].values[:, 0])
    }

    # Index sets
    model.T = Set(initialize=T)
    model.M = Set(initialize=[m.name for m in markets])

    # Decision variables
    model.c = Var(model.M, model.T, domain=NonNegativeReals, bounds=(0, battery.max_charge_rate))
    model.d = Var(model.M, model.T, domain=NonNegativeReals, bounds=(0, battery.max_discharge_rate))
    model.soc = Var(model.T, domain=NonNegativeReals, bounds=(0,battery.capacity), initialize=0) # Battery initialised to 0 charge

    # Battery params
    model.max_charge_rate = Param(initialize=battery.max_charge_rate)
    model.max_discharge_rate = Param(initialize=battery.max_discharge_rate)
    model.capacity = Param(initialize=battery.capacity)

    # Market params
    model.price = Param(model.M, model.T, initialize=price_lookup)
    model.dt = Param(initialize=dt)
    model.market_interval = Param(model.M, initialize = {m.name: m.interval.seconds/3600 for m in markets})

    # Constraints
    model.soc_constraint = Constraint(model.T, rule=soc_rule)
    model.charge_limit_constraint = Constraint(model.T, rule=lin_charge_limit_rule)
    model.discharge_limit_constraint = Constraint(model.T, rule=lin_discharge_limit_rule)
    add_market_commitment_constraints(model)

    # Objective
    model.objective = Objective(rule=simple_arb_obj, sense=maximize)

    return model


def build_MILP_arb_model(markets: list[Market], battery: BatterySpec,  t_start=None, t_end=None)->ConcreteModel:
    '''Simple battery arbitrage model with a binary variable, z, to explicitly
    prevent simultaneous charging and discharging across different markets.'''

    model = build_linear_arb_model(markets, battery,  t_start, t_end)
    model.z = Var(model.T, domain=Binary) # 1 = charging, 0 = discharging
    
    model.del_component(model.charge_limit_constraint)
    model.del_component(model.discharge_limit_constraint)
    model.charge_limit_constraint = Constraint(model.T, rule=mi_charge_limit_rule)
    model.discharge_limit_constraint = Constraint(model.T, rule=mi_discharge_limit_rule)
    
    return model