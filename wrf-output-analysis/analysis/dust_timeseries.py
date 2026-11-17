import glob
from netCDF4 import Dataset
from wrf import getvar, ALL_TIMES
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.dates as mdates
import pandas as pd
from datetime import timedelta
def fix_time(xr_ds, offset_hours):
    # offset_hours for JP = 9 
    xr_ds = xr_ds.assign_coords(Time=(pd.to_datetime(xr_ds.XTIME.values) + timedelta(hours=offset_hours)))
    xr_ds = xr_ds.sortby("Time")
    return xr_ds.sel(Time=~xr_ds.get_index("Time").duplicated())

# ---- CONFIGURATION ----
# List the directories for each WRF run, in chronological order.
# Each directory should contain that run's wrfout_d01_* files.
runs = [
    ("300_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/300_1"),
    ("300_3", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/300_3"),
    ("301_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/301_1"),
    ("303_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/303_1"),
    ("401_1", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_1"),
    ("401_3", "/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_3"),
]

domain = "d01"
dust_vars = ["DUST_1", "DUST_2", "DUST_3", "DUST_4", "DUST_5"]

# ---- SET UP PLOT ----
fig, ax = plt.subplots(figsize=(10, 5))

# ---- PROCESS EACH RUN SEPARATELY ----
for label,run_dir in runs:
    files = sorted(glob.glob(f"{run_dir}/wrfout_{domain}_*"))
    if not files:
        print(f"WARNING: no wrfout files found in {run_dir}, skipping.")
        continue

    print(f"{label}: found {len(files)} wrfout files.")

    
    ncfiles = [Dataset(f) for f in files]
        
    df = xr.open_mfdataset(files, concat_dim='Time', combine='nested')
    # df = xr.open_dataset(file)
    df_fix = fix_time(df,9)


    ##  plotting
    dust_1 = df_fix['DUST_1'].sum(dim=['bottom_top','south_north','west_east'])
    dust_2 = df_fix['DUST_2'].sum(dim=['bottom_top','south_north','west_east'])
    dust_3 = df_fix['DUST_3'].sum(dim=['bottom_top','south_north','west_east'])
    dust_4 = df_fix['DUST_4'].sum(dim=['bottom_top','south_north','west_east'])
    dust_5 = df_fix['DUST_5'].sum(dim=['bottom_top','south_north','west_east'])
    total_dust = dust_1+dust_2+dust_3+dust_4+dust_5
        #total_dust = None
       # for var in dust_vars:
        #    da = getvar(ncfiles, var, timeidx=ALL_TIMES, method="cat")
        #    var_sum = da.sum(dim=["bottom_top", "south_north", "west_east"])
        #    total_dust = var_sum if total_dust is None else total_dust + var_sum

        
    ax.plot(df_fix['Time'],total_dust, linewidth=1.5, label=label)


    # Plot this run's line
    #total_dust.plot(ax=ax, linewidth=1.5, label=label)

    #for nc in ncfiles:
        #nc.close()

# ---- FINALIZE PLOT ----
ax.set_title("Total Dust Comparison")
ax.set_xlabel("Date")
ax.set_ylabel('Total Dust (ug/kg-dryair)',fontsize=14)
ax.legend()
ax.grid(alpha=0.3)

ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("total_dust_comparison.png")
plt.show()
