import matplotlib.pyplot as plt
from netCDF4 import Dataset
from wrf import get_cartopy, latlon_coords, getvar, get_basemap
import cartopy.crs as ccrs
from glob import glob

# Open the WRF NetCDF file (output or geogrid file)
model_type = "real"
chem_opt = "300"
dust_opt = "1"
model_input = chem_opt+"_"+dust_opt
# wrfout_folder = f"/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_{model_type}/{model_input}/"
wrfout_folder = f"/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/wrf_chem/ea_{model_type}/v2-domain/"
wrfout_files = glob(wrfout_folder+"wrfout_d01*")

ncfile = Dataset(wrfout_files[0])
slp = getvar(ncfile, "slp")

# Get the Cartopy projection object directly from the file
crs = get_cartopy(slp)

# Extract latitude and longitude coordinates from the actual variable
lat, lon = latlon_coords(slp)

# Set up the Matplotlib figure with the WRF native projection
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": crs})

# Add geographic features and borders
ax.coastlines(resolution="50m", color="black", linewidth=1)
ax.stock_img()  # Optional background image

# Plot domain boundaries or grid outline
ax.set_extent([lon.min(), lon.max(), lat.min(), lat.max()], crs=ccrs.PlateCarree())
ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)

plt.title("WRF Domain Map")
plt.savefig("wrf_v2-domain_map.png", dpi=300, bbox_inches="tight")
plt.show()
