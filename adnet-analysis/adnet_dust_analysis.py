#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 15:00:09 2026

@author: madelinezhang
"""

## loading libraries
import os
import glob
import netCDF4 as nc
import xarray as xr
import pandas as pd
from datetime import timedelta
import re 
import numpy as np
from datetime import datetime

## set up working directory and folder 
# folder destination
# folder_base = '/gucnas3/madeline/adnet' 
folder_base = '/Users/madelinezhang/Downloads/adnet' 
os.chdir(folder_base) # set working directory 

# dust variables
CV = 0.75e-6 # m, 
RHO = 2600.0 # kg/m3, density 
VMAX = 1e-2

# station name codes
FIXED_STATIONS = ['CHB', 'FKE', 'FKO', 'HED', 'JEJ', 'MTS', 'NGS',
                  'NIG', 'OSK', 'PHM', 'SEO', 'SND', 'SNS', 'SPR', 
                  'TKB', 'TKO', 'TYM', 'ULN', 'ULS', 'UTY', 'ZMY']

start_date = pd.to_datetime('2023-01-01')
end_date = pd.to_datetime('2023-12-31')

PPP = 'TKO'
#YY = '23'
#MM = '05'
#DD = '22'

# =============================================================================
# Dimensions:
# TIME: UTC Start time (sec from 00Z) # every 15 min, 96 prof./day
# HEIGHTA: altitude from ground (km) for attenuated backscatter and volume depol. #up to 18km
# HEIGHTE: altitude from ground (km) for extinction data #up to 9 km
# 
# Variables:
# ABSC532(T*HA): 532 nm attenuated backscatter coefficient (/m/sr)
# ABSC1064(T*HA): 1064 nm (/m/sr)
# DEP532(T*HA): 532 nm volume depolarization ratio #S/P
# EXT532(T*HE): 532 nm aerosol extinction coefficient (/m)
# EXTD532(T*HE): 532 nm dust extinction coefficient (/m)
# EXTS532(T*HE): 532 nm spherical particle extinction coefficient (/m)
# ADEP532(T*HE): 532 nm aerosol depolarization ratio
# MXLHT(T): estimated mixing layer height (m)
# =============================================================================

#### functions #### --------------------------
def fix_time(xr_ds, offset_hours=9):
    # offset_hours for JP = 9 
    xr_ds = xr_ds.assign_coords(Time=(pd.to_datetime(xr_ds.XTIME.values) + timedelta(hours=offset_hours)))
    xr_ds = xr_ds.sortby("Time")
    return xr_ds.sel(Time=~xr_ds.get_index("Time").duplicated())

# =============================================================================
# def dust_mass(ext_d, cv, rho=RHO):
#     """ug/m3 from dust extinction in 1/m (negative noise clipped to 0)."""
#     return ext_d.clip(min=0) * cv * rho * 1e9
# =============================================================================

year = start_date.strftime("%Y")
# truncate year
YY = str(year % 100)
MM = start_date.strftime("%m")
DD = start_date.strftime("%d")

path = folder_base+'/'+YY+MM+'/'+PPP+YY+MM+DD+'.nc'

ds = xr.open_dataset(path, decode_times=False)


# extd532
# HEIGHT_E
# T 
# TIME
#m = re.search(r"(\d{6})", os.path.basename(path))
#day = pd.to_datetime(m.group(1), format="%y%m%d") if m else pd.to_datetime(
       # str(ds.attrs.get("date", "")), errors="coerce")

extd = ds['extd532']
# extd.dims: (HEIGHT_E, TIME)
# extd.shape: (300, 96)
# AD-Net data collected 4 times per hour, every 15 minutes
# -9999: in cloud, -999: above cloud or rainy
# units: (/m)

# dust variables
CV = 0.75e-6 # m, 
RHO = 2600.0 # kg/m3, density 
# RHO = 2.6 # g/cm3, density 
VMAX = 1e-2

# extd = extd.assign_coords(HEIGHT_E=ds["HEIGHT_E"] * 1000) # from km to m
extd_clean = extd.clip(min=0) # remove faulty data
#extd_col = extd_clean.integrate("HEIGHT_E") # integrate over height
#extd_col_val = extd_col.values # dust extinction values
extd_val = extd_clean.values
height = extd.HEIGHT_E.values
dz = np.diff(height).mean()
tax = ds["extd532"].dims.index("HEIGHT_E") 

# extd_col_val = np.nansum(extd_val, axis=tax) * dz
# dust_mass = extd_col_val*CV*RHO*1e9 # ug/m3

dust_mass = extd_clean*CV*RHO*1e9
dust_mass_val = dust_mass.values

# dust_mass = extd_val*CV*RHO


# hourly = extd_val.resample(TIME="1h").mean()

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# date = pd.Timestamp("2018-01-01") 
# date = pd.Timestamp("2023-05-22") 
date = pd.Timestamp(start_date)
             
n = dust_mass.sizes["TIME"] 
times = date + pd.to_timedelta((np.arange(n) + 1) * 15, unit="min")
dust_mass = dust_mass.assign_coords(TIME=times)    

dust_mass = dust_mass.assign_coords(TIME=dust_mass.TIME + pd.Timedelta(hours=9))

fig, ax = plt.subplots(figsize=(11, 4))
dust_mass.plot(
    x="TIME", y="HEIGHT_E", ax=ax,                 # explicit axes, so no transpose needed
    cmap="plasma", vmin=0, vmax=300,               # fix the scale for comparing days
    cbar_kwargs={"label": "Dust mass concentration (µg m$^{-3}$)"},
)
ax.set_ylabel("Height (km)")                       # use m if you converted the coordinate


ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))                 # labelled ticks every hour
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.xaxis.set_minor_locator(mdates.MinuteLocator(byminute=[15, 30, 45]))    # unlabelled ticks every 15 min
# ax.set_xticks(times)                                      # one tick per profile (datetime positions)
# ax.set_xticklabels([t.strftime("%H:%M") for t in times], rotation=90, fontsize=7)
ax.set_xlabel(f"Time (JST), {date:%Y-%m-%d}")

fig.tight_layout()
fig.savefig("dust_heatmap.png", dpi=200)





