import glob
from netCDF4 import Dataset
from wrf import getvar, ALL_TIMES
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# ============================================================
# SELECT YOUR VARIABLE HERE
# Options: "QVAPOR", "QRAIN", "QCLOUD", "RAINC", "RAINNC", or a dust bin like "DUST_1"
# ============================================================
SELECTED_VAR = "RAINC"
def fix_time(xr_ds, offset_hours):
    # offset_hours for JP = 9 
    xr_ds = xr_ds.assign_coords(Time=(pd.to_datetime(xr_ds.XTIME.values) + timedelta(hours=offset_hours)))
    xr_ds = xr_ds.sortby("Time")
    return xr_ds.sel(Time=~xr_ds.get_index("Time").duplicated())



# ---- CONFIGURATION ----
# runs = [
  #  ("300_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/300_1"),
  #  ("300_3", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/300_3"),
  #  ("301_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/301_1"),
  #  ("303_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/303_1"),
  #  ("401_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_1"),
  #  ("401_3", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_3"),
# ]
runs = [ ("401_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_real/401_1")]

domain = "d01"
overlap_tolerance = 0.01  # 1% — flags lines that are nearly indistinguishable

# variable name -> whether it has a vertical (bottom_top) dimension, aggregation method, and y-label
variables = {
    "QVAPOR":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total QVAPOR (kg kg-1)"},
    "QRAIN":   {"has_vert": True,  "agg": "sum",  "ylabel": "Total QRAIN (kg kg-1)"},
    "QCLOUD":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total QCLOUD (kg kg-1)"},
    "QSNOW":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total QSNOW (kg kg-1)"},
    "RAINC":   {"has_vert": False, "agg": "mean", "ylabel": "Mean RAINC (mm)"},
    "RAINNC":  {"has_vert": False, "agg": "mean", "ylabel": "Mean RAINNC (mm)"},
    "DUST_1":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total DUST_1 (domain-summed)"},
    "DUST_2":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total DUST_2 (domain-summed)"},
    "DUST_3":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total DUST_3 (domain-summed)"},
    "DUST_4":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total DUST_4 (domain-summed)"},
    "DUST_5":  {"has_vert": True,  "agg": "sum",  "ylabel": "Total DUST_5 (domain-summed)"},
}

if SELECTED_VAR not in variables:
    raise ValueError(f"'{SELECTED_VAR}' is not configured. Choose from: {list(variables.keys())}")

cfg = variables[SELECTED_VAR]

# ---- FUNCTION: extract a run's time series for the selected variable ----
def get_run_timeseries(run_dir, var_name, has_vert, agg):
    files = sorted(glob.glob(f"{run_dir}/wrfout_{domain}_*"))
    if not files:
        print(f"WARNING: no wrfout files found in {run_dir}")
        return None

    ncfiles = [Dataset(f) for f in files]
    try:
        da = getvar(ncfiles, var_name, timeidx=ALL_TIMES, method="cat")
        da = fix_time(
            da,
            offset_hours=offset_hours
        )
        dims = ["south_north", "west_east"]
        if has_vert:
            dims = ["bottom_top"] + dims

        result = da.sum(dim=dims) if agg == "sum" else da.mean(dim=dims)
        return result
    except Exception as e:
        print(f"ERROR processing {var_name} in {run_dir}: {e}")
        return None
    finally:
        for nc in ncfiles:
            nc.close()

# ---- MAIN: build the plot for the selected variable only ----
fig, ax = plt.subplots(figsize=(10, 5))
series_collected = {}

for label, run_dir in runs:
    ts = get_run_timeseries(run_dir, SELECTED_VAR, cfg["has_vert"], cfg["agg"])
    if ts is None:
        continue
    series_collected[label] = ts
    ax.plot(ts['Time'].values, ts.values, linewidth=1.5, label=label)


ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
fig.autofmt_xdate()

ax.set_title(f"{SELECTED_VAR} Comparison")
ax.set_xlabel("Date")
ax.set_ylabel(cfg["ylabel"])
ax.legend()
ax.grid(alpha=0.3)

plt.savefig(f"{SELECTED_VAR.lower()}_comparison.png", )
plt.show()
