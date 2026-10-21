import numpy as np
import netCDF4 as nc

# ---------------------------
# Parameter settings
# ---------------------------
lat_min, lat_max = 34.70706, 36.26041
lon_min, lon_max = 139.01997, 140.92776
date = "20210315"

radar_file = f"/gucnas2/bank/data/raindata/rain2021/Z__C_RJTD_{date}_SRF_GPV_Ggis1km_Prr60lv_ANAL.nc"
output_file = f"/gucnas3/madeline/radar_crop/{date}_radar_crop_utc0.nc"

LAT, LON = "latitude", "longitude"   # dimension / coordinate names

with nc.Dataset(radar_file) as ds, nc.Dataset(output_file, "w", format="NETCDF4") as out:
    # ---------------------------
    # Find index range of the crop box (works for ascending or descending axes)
    # ---------------------------
    lat = ds.variables[LAT][:]
    lon = ds.variables[LON][:]
    ilat = np.where((lat >= lat_min) & (lat <= lat_max))[0]
    ilon = np.where((lon >= lon_min) & (lon <= lon_max))[0]
    if ilat.size == 0 or ilon.size == 0:
        raise ValueError("Crop box does not overlap the data grid.")
    sl = {LAT: slice(ilat.min(), ilat.max() + 1),
          LON: slice(ilon.min(), ilon.max() + 1)}

    # ---------------------------
    # Copy global attributes and dimensions (cropped)
    # ---------------------------
    out.setncatts({k: ds.getncattr(k) for k in ds.ncattrs()})
    for name, dim in ds.dimensions.items():
        if name in sl:
            size = sl[name].stop - sl[name].start
        elif dim.isunlimited():
            size = None
        else:
            size = len(dim)
        out.createDimension(name, size)

    # ---------------------------
    # Copy variables with zlib compression
    # ---------------------------
    for name, var in ds.variables.items():
        attrs = var.ncattrs()
        fill = var.getncattr("_FillValue") if "_FillValue" in attrs else None
        compress = var.ndim > 0 and var.dtype != str
        kw = dict(zlib=True, complevel=9) if compress else {}

        v = out.createVariable(name, var.dtype, var.dimensions,
                               fill_value=fill, **kw)
        v.setncatts({k: var.getncattr(k) for k in attrs if k != "_FillValue"})

        if var.ndim == 0:
            v.assignValue(var.getValue())
            continue
        index = tuple(sl.get(d, slice(None)) for d in var.dimensions)
        v[...] = var[index]

print("Cropped data saved to:", output_file)
