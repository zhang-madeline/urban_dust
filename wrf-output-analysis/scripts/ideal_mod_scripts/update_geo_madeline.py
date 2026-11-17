from netCDF4 import Dataset
from glob import glob
import os, sys
import numpy as np
import math

filelist = "realistic/geo_em.d01.nc"

def modify_convert_uniform(src: Dataset, var_names: list[str]) -> Dataset:
    '''
    Convert all variables in the src file to uniform average
    src         source dataset
    var_names   list of variable names to average
    '''

    for var_name in var_names:
        modified_var = src.variables[var_name][:]
        print(f'Averaging {var_name}...', end='\r')
        for time_idx in range(src.variables[var_name].shape[0]):
            average_value = np.mean(src.variables[var_name][time_idx])
            modified_var[time_idx][:] = average_value
        src.variables[var_name][:] = modified_var

    return src

# %%

def modify_map_factor(src: Dataset) -> Dataset:
    '''
    Adjust map factor to 1
    src         source dataset
    '''
    for var_name in src.variables.keys():
        if var_name.split('_')[0] == 'MAPFAC':
            src.variables[var_name][:] = 1

    return src

# %%


WATER_CUTOFF_IDX = 20
URBAN_SIZE = (4, 5)
urban_mask = (
    slice(20 - URBAN_SIZE[0] // 2, 20 + URBAN_SIZE[0] // 2,), 
    slice(20 - URBAN_SIZE[0] // 2, 20 + URBAN_SIZE[0] // 2,), 
    None
)

def modify_landuse(src: Dataset) -> Dataset:
    '''
    Modify the land use category
    src     source dataset
    '''
    attrs = src.__dict__
    land_use_cat = {
        'urban': attrs['ISURBAN'],         # Urban and Built-up Land
        'water': attrs['ISWATER'],        # Water Bodies
        'grassland': 10,     # Grassland
        'barren': 16,     # Barren or sparsely vegetated
        'forest': 5,     # Mixed Forests
    }

    rural_land_type = 'grassland'

    # Modify the land use index. To check the variables,
    # see LANDUSE.TBL and num_land_cat in namelist.input
    # 24 - for USGS (default); 20 for MODIS
    # 28 - for USGS if including lake category
    # 21 - for MODIS if including lake category (default since 3.8)
    # 40 - for NCLD
    # Currently using USGS (num_land_cat = 24)
    modified_lu = src.variables['LU_INDEX'][:]
    modified_lu[0][:] = land_use_cat[rural_land_type]
    modified_lu[0][urban_mask] = land_use_cat['urban']
    src.variables['LU_INDEX'][:] = modified_lu

    # Modify land mask, 1 for land, 0 for water
    modified_landmask = src.variables['LANDMASK'][:]
    modified_landmask[0][:] = 1 # Land
    src.variables['LANDMASK'][:] = modified_landmask

    # Modify land use fraction
    # https://forum.mmm.ucar.edu/threads/difference-between-landusef-and-frc_urb2d.10455/
    # Basically you need to modify the fraction of land to the corresponding
    # array index
    # !!!!! IMPORTANT: The index is 0-indexed, so it should be the value in LANDUSE minus 1 !!!!!
    modified_landusef = src.variables['LANDUSEF'][:]
    modified_landusef[:] = 0 # Reset everything, probably easier
    modified_landusef[0][land_use_cat[rural_land_type] - 1][:] = 1.0

    # No grassland here
    modified_landusef[0][land_use_cat[rural_land_type] - 1][urban_mask] = 0
    modified_landusef[0][land_use_cat['urban'] - 1][urban_mask] = 1.0
    src.variables['LANDUSEF'][:] = modified_landusef

    return src

# %%

def modify_height(src: Dataset) -> Dataset:
    '''
    Modify terrain height of input file
    src     source dataset
    '''
    src.variables['HGT_M'][:] = 0

    return src

# %%

def modify_urban_area(src: Dataset) -> Dataset:
    '''
    Modify urban related variables
    src     source dataset
    '''
    urban_vars = [
        ('MH_URB2D',            10   ),
        ('ZD_URB2D',            3   ),
        ('Z0_URB2D',            1 ),
        ('BUILD_AREA_FRACTION', 0.25 ),
        ('LF_URB2D_S',          0.25 ),
    ]
    for var_name, value in urban_vars:
        modified_var = np.zeros(src.variables[var_name].shape)
        for time_idx in range(src.variables[var_name].shape[0]):
            modified_var[time_idx][urban_mask] = value
        src.variables[var_name][:] = modified_var

    # Modify AHE
    ahe_value = 10.0
    modified_ahe = np.zeros(src.variables['AHE'].shape)
    for time_idx in range(modified_ahe.shape[0]):
        for month_hour_idx in range(modified_ahe.shape[1]):
            modified_ahe[time_idx][month_hour_idx][urban_mask] = ahe_value
    src.variables['AHE'][:] = modified_ahe

    return src

# %%

def modify_urban_zero(src: Dataset) -> Dataset:
    src.variables['MH_URB2D'][:] = 0
    src.variables['Z0_URB2D'][:] = 0
    src.variables['ZD_URB2D'][:] = 0
    src.variables['BUILD_AREA_FRACTION'][:] = 0
    src.variables['LF_URB2D_S'][:] = 0
    src.variables['AHE'][:] = 0

    return src

# %%

def modify_cos_sin_a(src: Dataset) -> Dataset:
    src.variables['COSALPHA'][:] = 1
    src.variables['SINALPHA'][:] = 0

    src.variables['COSALPHA_U'][:] = 1
    src.variables['SINALPHA_U'][:] = 0
    src.variables['COSALPHA_V'][:] = 1
    src.variables['SINALPHA_V'][:] = 0

    src.variables['E'][:] = 0
    src.variables['F'][:] = 0
    return src

def modify_zero_dusts(src: Dataset) -> Dataset:
    src.variables['CLAYFRAC'][:] = 0.25
    src.variables['EROD'][:] = 0.25
    src.variables["SANDFRAC"][:] = 0.5
    return src

with Dataset(filelist, 'r', format='NETCDF4') as src:
    with Dataset(filelist.replace("realistic","ideal"), "w", format="NETCDF4") as out:

        attributes = src.__dict__
        attributes['TITLE'] += ' (MODIFIED)'
        attributes['NOTE'] = 'SANDFRAC EROD CLAYFRAC by Madeline'
        out.setncatts(attributes)

        for name, dimension in src.dimensions.items():
                dimension_size = (
                    len(dimension) if not dimension.isunlimited() else None
                ) # The value should be None for unlimited dimension

                # Create the dimension with its size, make sure to modify it
                # if you changed the variable dimension
                out.createDimension(name, dimension_size)

        for name, variable in src.variables.items():
                out.createVariable(
                    name,
                    variable.datatype,
                    variable.dimensions,
                    zlib = True,            # Lossless compression (optional)
                    complevel = 5,          # Lossless compression (optional)
                    shuffle = True          # Lossless compression (optional)
                )

                # Set output variable attributes
                out[name].setncatts(src[name].__dict__)
                out[name][:] = src[name][:]

        var_names = [
            'SOILTEMP', 'SOILCTOP', 'SCT_DOM', 'SOILCBOT',
            'SCB_DOM', 'ALBEDO12M', 'GREENFRAC', 'LAI12M',
            'SNOALB', 'CON', 'VAR', 'OA1', 'OA2', 'OA3', 'OA4',
            'OL1', 'OL2', 'OL3', 'OL4', 'VAR_SSO',
            # 'XLAT_M', 'XLONG_M',
        ]

        out = modify_convert_uniform(out, var_names)
        out = modify_landuse(out)
        out = modify_height(out)
        out = modify_map_factor(out)
        # out = modify_urban_zero(out)
        out = modify_urban_area(out)
        out = modify_cos_sin_a(out)
        out = modify_zero_dusts(out)
