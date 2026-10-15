import xarray as xr

def process_radar_data_rain(ds, zoom=None):

    lat_min, lat_max, lon_min, lon_max = zoom
    ds_cropped = ds.sel(latitude=slice(lat_min, lat_max),
                        longitude=slice(lon_min, lon_max))

    return ds_cropped

# ---------------------------
# Parameter settings
# ---------------------------
# Spatial extent parameters (for example, part of the Tokyo metropolitan area)
lat_min, lat_max = 34.70706, 36.26041
lon_min, lon_max = 139.01997, 140.92776

# Set the tag used to generate output filenames automatically
date = "20210315"

# Source data file path
radar_file = f'/gucnas2/bank/data/raindata/rain2021/Z__C_RJTD_{date}_SRF_GPV_Ggis1km_Prr60lv_ANAL.nc'

# ---------------------------
# Read and crop data
# ---------------------------
# Use automatic chunking when opening the dataset to reduce memory usage
ds = xr.open_dataset(radar_file, chunks='auto')

# Crop the spatial extent without adjusting time to reduce computational cost
ds_cropped = process_radar_data_rain(ds, zoom=(lat_min, lat_max, lon_min, lon_max))

# ---------------------------
# Compression encoding settings
# ---------------------------
encoding = {}
for var in ds_cropped.variables:
    encoding[var] = {'zlib': True, 'complevel': 9}

# Generate the output filename automatically using the tag
output_file = f'/gucnas3/madeline/radar_crop/{date}_radar_crop_utc0.nc'

# ---------------------------
# Save the cropped data
# ---------------------------
ds_cropped.to_netcdf(output_file, encoding=encoding)

print("Cropped data saved to:", output_file)
