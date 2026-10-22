"""Generate the 2023 weather-year .inc files for the backcast (no investment files)."""
import sys

from pybalmorel import WEATHERYEAR
from pybalmorel.weatheryear.scenario_data import write_scenario_data

year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
wy = WEATHERYEAR(year=year, config_fn="weatheryear_2023.yml", output_folder="output/")
wy.get_vre_data()
wy.get_demand_data()
wy.get_hydro_data()
wy.get_cop_data()

# Write the actual-weather (raw) output into the backcast's data/ folder,
# overwriting the files it writes there
written = write_scenario_data(
    capdev_dir=f"output/{year}/to_balmorel/CapDev/raw",
    to_balmorel_dir=f"output/{year}/to_balmorel",
    dest_dir="../data",
)
print(f"Wrote {len(written)} files to backcast/data")
