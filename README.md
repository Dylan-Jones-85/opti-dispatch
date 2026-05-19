# opti-dispatch

A Python package built around pyomo for optimising battery charge/discharge scheduling across wholesale electricity markets to maximise arbitrage revenue.

## Installation

Clone the repository and install in editable mode:

```bash
git clone <https://github.com/Dylan-Jones-85/opti-dispatch.git>
cd opti-dispatch
pip install -e .
```

### Dependencies

- `pandas`
- `pyomo`
- A Pyomo-compatible solver (see below)

### Solver setup

opti-dispatch requires an external solver accessible to Pyomo via `SolverFactory`. Any Pyomo-compatible solver can be used — the recommended options are:

| Solver                                     | Type      | Install                                                           |
| ------------------------------------------ | --------- | ----------------------------------------------------------------- |
| [HiGHS](https://highs.dev)                 | LP / MILP | `pip install highspy`                                             |
| [GLPK](https://www.gnu.org/software/glpk/) | LP / MILP | `conda install -c conda-forge glpk` or via system package manager |
| [CBC](https://github.com/coin-or/Cbc)      | LP / MILP | `conda install -c conda-forge coincbc`                            |

HiGHS is recommended — it is fast, actively maintained, and installs cleanly via pip.

---

## Data Format

### Battery specification

A CSV with `Name`, `Value`, `Units`, and `Description` columns. The following named rows are required:

| Name                 | Example Value | Units |
| -------------------- | ------------- | ----- |
| Max charging rate    | 2             | MW    |
| Max discharging rate | 2             | MW    |
| Max storage volume   | 4             | MWh   |

### Market price data

The `Market` class is designed to hold a single pandas Series (datetime index) containing price data with units `Currency/MWh`.

---

## Usage

Preconfigured model-builder functions can be found in `opti_dispatch.optimisation.arbitrage_models`. However constraint and objective rules are defined separately in `opti_dispatch.optimisation.rules` for use as building blocks in custom models.

See `example_01.py` for a complete worked example covering data loading, model construction, solving, and result extraction.
Reproducible results can be found in the example_results directory.

---

## Model details

### Market alignment

When multiple markets are provided, prices are resampled to the highest common frequency using forward-fill. A market commitment constraint can be used to ensure that power allocated to any market interval is kept constant throughout the entire interval.

### Battery constraints

- State of charge is initialised to zero at `t=0`
- SOC is bounded between `0` and `battery.capacity` at all timesteps
- Total charge and discharge across all markets is bounded by `max_charge_rate` and `max_discharge_rate` respectively
- The MILP model enforces that the battery cannot charge and discharge simultaneously via a binary variable `z` (1 = charging, 0 = discharging)

### Objective

Revenue is maximised as:

```
maximise Σ price[m,t] × dt × (discharge[m,t] − charge[m,t])
```

over all markets `m` and timesteps `t`.

### Analysis

Some simple functions are provided in the `analysis` module to extract and post-process results for easy visualisation and validation.
