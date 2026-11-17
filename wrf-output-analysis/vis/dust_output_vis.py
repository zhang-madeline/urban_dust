import matplotlib.pyplot as plt
from netCDF4 import Dataset as netcdf_dataset
import numpy as np

from cartopy import config
import cartopy.crs as ccrs

# get the path of the file. It can be found in the repo data directory.
# load file
# replace file path & file name
filepath = '/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_ideal/401_1/'
filename = 'wrfout_d01_2021-03-10_00:00:00'
dataset = netcdf_dataset(filepath+filename)

lats = dataset.variables["XLAT"][0]
lons = dataset.variables["XLONG"][0]

# Compute total dust once
total_dust = (
    dataset.variables["DUST_1"][:] +
    dataset.variables["DUST_2"][:] +
    dataset.variables["DUST_3"][:] +
    dataset.variables["DUST_4"][:] +
    dataset.variables["DUST_5"][:]
)

ntimes = total_dust.shape[0]

for i in range(ntimes):
    dust2d = np.sum(total_dust[i], axis=0)

    # projection
    ax = plt.axes(projection=ccrs.PlateCarree())

    plt.contourf(lons,
                 lats, 
                 dust2d,
                 levels=60,
                 transform=ccrs.PlateCarree())

    #ax.coastlines()

    # save as png
    plt.savefig(f"{filename}_{i+1:02d}.png")

