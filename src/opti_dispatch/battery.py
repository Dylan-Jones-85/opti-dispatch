class BatterySpec:
    def __init__(self, max_charge_rate: float, max_discharge_rate: float, capacity: float):
        self.max_charge_rate = max_charge_rate # MW
        self.max_discharge_rate = max_discharge_rate # MW
        self.capacity = capacity # MWh

