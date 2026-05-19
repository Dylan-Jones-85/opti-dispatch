import pytest
import textwrap
from opti_dispatch.battery import BatterySpec


VALID_CSV = textwrap.dedent("""\
    Name,Value,Units,Description
    Max charging rate,2,MW,Maximum import power
    Max discharging rate,2,MW,Maximum export power
    Max storage volume,4,MWh,Maximum energy storage
""")

@pytest.fixture
def valid_battery_csv(tmp_path):
    p = tmp_path / "battery_spec.csv"
    p.write_text(VALID_CSV)
    return p


def test_from_csv_loads_correctly(valid_battery_csv):
    battery = BatterySpec.from_csv(valid_battery_csv)
    assert battery.max_charge_rate == 2.0
    assert battery.max_discharge_rate == 2.0
    assert battery.capacity == 4.0


def test_from_csv_missing_row_raises(tmp_path):
    csv = textwrap.dedent("""\
        Name,Value,Units,Description
        Max charging rate,2,MW,Maximum import power
        Max storage volume,4,MWh,Maximum energy storage
    """)
    p = tmp_path / "battery_spec.csv"
    p.write_text(csv)
    with pytest.raises(KeyError):
        BatterySpec.from_csv(p)
