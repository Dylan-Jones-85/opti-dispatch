from pyomo.environ import *
from opti_dispatch.battery import BatterySpec
from opti_dispatch.markets import Market, align_market_freqs
from opti_dispatch.optimisation.rules import *

def build_MILP_arb_model(markets: list[Market], battery: BatterySpec, n_timesteps=None)->ConcreteModel:
    '''Simple battery arbitrage model with a binary variable, z, to explicitly
    prevent simultaneous charging and discharging across different markets.'''
    markets, freq = align_market_freqs(markets)
    dt = freq.seconds/3600

    model = ConcreteModel()

    if n_timesteps is None:
        n_timesteps = len(markets[0].prices)

    T = range(n_timesteps-1)
    price_lookup = {
    (m.name, t): m.prices.iloc[t, 0]
    for m in markets
    for t in T
    }

    # Index sets
    model.T = Set(initialize=T)
    model.M = Set(initialize=[m.name for m in markets])

    # Decision variables
    model.c = Var(model.M, model.T, domain=NonNegativeReals, bounds=(0, battery.max_charge_rate))
    model.d = Var(model.M, model.T, domain=NonNegativeReals, bounds=(0, battery.max_discharge_rate))
    model.soc = Var(model.T, domain=NonNegativeReals, bounds=(0,battery.capacity))
    model.z = Var(model.T, domain=Binary) # 1 = charging, 0 = discharging

    # Battery params
    model.max_charge_rate = Param(initialize=battery.max_charge_rate)
    model.max_discharge_rate = Param(initialize=battery.max_discharge_rate)
    model.capacity = Param(initialize=battery.capacity)

    # Market params
    model.price = Param(model.M, model.T, initialize=price_lookup)
    model.dt = Param(initialize=dt)
    model.market_interval = Param(model.M, initialize = [m.interval.seconds/3600 for m in markets])

    # Constraints
    model.soc_constraint = Constraint(model.T, rule=soc_rule)
    model.charge_limit_constraint = Constraint(model.T, rule=mi_charge_limit_rule)
    model.discharge_limit_constraint = Constraint(model.T, rule=mi_discharge_limit_rule)
    add_market_commitment_constraints(model)

    # Objective
    model.objective = Objective(rule=simple_arb_obj, sense=maximize)

    return model

def build_linear_arb_model(markets: list[Market], battery: BatterySpec, n_timesteps=None)->ConcreteModel:
    '''Simple battery arbitrage model which allows simultaneous charging and discharging,
    reducing the MILP problem to a LP one. For single markets, the linear model should
    produce the same result as the MILP model as simultaneous charge and discharge is
    not optimal.'''
    markets, freq = align_market_freqs(markets)
    dt = freq.seconds/3600

    model = ConcreteModel()

    if n_timesteps is None:
        n_timesteps = len(markets[0].prices)

    T = range(n_timesteps-1)
    price_lookup = {
    (m.name, t): m.prices.iloc[t, 0]
    for m in markets
    for t in T
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
    model.market_interval = Param(model.M, initialize = [m.interval.seconds/3600 for m in markets])

    # Constraints
    model.soc_constraint = Constraint(model.T, rule=soc_rule)
    model.charge_limit_constraint = Constraint(model.T, rule=lin_charge_limit_rule)
    model.discharge_limit_constraint = Constraint(model.T, rule=lin_discharge_limit_rule)
    add_market_commitment_constraints(model)

    # Objective
    model.objective = Objective(rule=simple_arb_obj, sense=maximize)

    return model