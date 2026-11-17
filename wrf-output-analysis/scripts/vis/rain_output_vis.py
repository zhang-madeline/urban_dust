import matplotlib.pyplot as plt
from netCDF4 import Dataset as netcdf_dataset
import numpy as np

from cartopy import config
import cartopy.crs as ccrs

# get the path of the file. It can be found in the repo data directory.
# load file
# replace file path & file name
filepath = '/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_1'
filename = 'wrfout_d01_2021-03-10_00:00:00'
dataset = netcdf_dataset(filepath+filename)

lats = dataset.variables["XLAT"][0]
lons = dataset.variables["XLONG"][0]

# Compute total dust once
total_rain = (
    dataset.variables["RAINC"][:] +
    dataset.variables["RAINNC"][:]
)

ntimes = total_rain.shape[0]

for i in range(ntimes):
    rain = total_rain[i]

    # projection
    ax = plt.axes(projection=ccrs.PlateCarree())

    plt.contourf(lons,
                 lats, 
                 rain,
                 levels=60,
                 transform=ccrs.PlateCarree())

   #  ax.coastlines()

    # save as png
    plt.savefig(f"{filename}_{i+1:02d}.png")

