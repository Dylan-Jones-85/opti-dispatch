'''Reusable rules for building different arbitrage models'''
from pyomo.environ import *

# Total flow helpers
def total_charge(model, t):
    return sum(model.c[m,t] for m in model.M)

def total_discharge(model, t):
    return sum(model.d[m,t] for m in model.M)

#==============================================================================
# Constraints
#==============================================================================

# Soc chronology rule
def soc_rule(model, t):
    # Battery assumed to be at zero charge at t==0
    if t == 0:
        return model.soc[t] == 0 + model.dt*(total_charge(model, t) - total_discharge(model, t))
    return model.soc[t] == model.soc[t-1] + model.dt*(total_charge(model, t) - total_discharge(model, t))


# Charge/discharge limit rules
# Mixed integer variants for strict exclusivity
def mi_charge_limit_rule(model, t):
    return total_charge(model, t) <= model.max_charge_rate * model.z[t]

def mi_discharge_limit_rule(model, t):
    return total_discharge(model, t) <= model.max_discharge_rate * (1-model.z[t])

# Linear variants where optimal solution negates simultaneous charge+discharge
def lin_charge_limit_rule(model, t):
    return total_charge(model, t) <= model.max_charge_rate

def lin_discharge_limit_rule(model, t):
    return total_discharge(model, t) <= model.max_discharge_rate


# Market interval commitment constraints
# Note: this function modifies the model directly as opposed to the other rules
#   in this module
def add_market_commitment_constraints(model):
    model.market_commitment_constraints = ConstraintList()

    for m in model.M:

        steps_in_interval = int(model.market_interval[m] / model.dt)

        if steps_in_interval == 1:
            continue
        
        for t in model.T:
            if t % steps_in_interval != 0:
                continue
            
            for k in range(1, steps_in_interval):
                if (t + k) not in model.T:
                    continue
                model.market_commitment_constraints.add(model.c[m, t+k] == model.c[m, t])
                model.market_commitment_constraints.add(model.d[m, t+k] == model.d[m, t])

    return model.market_commitment_constraints

#==============================================================================
# Objectives
#==============================================================================

def simple_arb_obj(model):
    return sum(model.price[m,t] * model.dt * (model.d[m, t] - model.c[m, t])
        for m in model.M
        for t in model.T)