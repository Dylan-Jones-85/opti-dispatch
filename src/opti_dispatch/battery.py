from dataclasses import dataclass
import pandas as pd

@dataclass
class BatterySpec:
    max_charge_rate: float # MW
    max_discharge_rate: float # MW
    capacity: float # MWh

    @classmethod
    def from_csv(cls, file_path) -> "BatterySpec":
        df = pd.read_csv(file_path, index_col="Name")
        
        def get(name: str) -> float:
            return pd.to_numeric(df.loc[name, "Value"])
        
        return cls(max_charge_rate=get("Max charging rate"),
                   max_discharge_rate=get("Max discharging rate"),
                   capacity=get("Max storage volume"))