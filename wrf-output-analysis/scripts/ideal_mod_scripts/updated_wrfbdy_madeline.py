from netCDF4 import Dataset
from glob import glob
import numpy as np
import sys, os
import math

all_files = glob('wrfbdy*')
os.makedirs('modified-files',exist_ok=True)

def modify_average_z_layers(src: Dataset, var_names: list[str]) -> Dataset:
    '''
    A function to average all variables in each Z-layer
    src:    A read file pointer to source/input file
    '''
    for var_name in var_names:
        print(f'Processing variable {var_name}...', end='\r')
        # Ideally we want to use recursive, but now the size is fixed
        # so it's fine

        # I can't assign the value directly to out for some reason
        # so I make a temporary variable
        modified_out = src.variables[var_name][:]
        var_shape = src.variables[var_name].shape
        for time_idx in range(var_shape[0]):
            for bdy_width_idx in range(var_shape[1]):
                for bottom_top_idx in range(var_shape[2]):
                    mean_val_in_z_level = np.mean(src.variables[var_name][time_idx][bdy_width_idx][bottom_top_idx])
                    modified_out[time_idx][bdy_width_idx][bottom_top_idx][:] = mean_val_in_z_level
        src.variables[var_name][:] = modified_out

    return src

# %%

def modify_remove_wind(src: Dataset) -> Dataset:
    '''
    A function to remove boundary condition wind
    src:    A read file pointer to source/input file
    '''
    for var_name in src.variables.keys():
        if (var_name.split('_')[0] in ['U', 'V', 'W']):
            src.variables[var_name][:] = 0.0
    return src

# %%

def modify_reduce_vapor(src: Dataset) -> Dataset:
    reduction_factor = 0.01
    for var_name in src.variables.keys():
        initial = var_name.split('_')[0]
        if initial == 'QVAPOR':
            src.variables[var_name][:] *= reduction_factor
    return src

# %%

import os
file_name: str = 'wrfbdy_d01'
output_name: str = 'modified-files/' + file_name

if len(glob(output_name)) > 0:
    os.remove(output_name)

# Three things need to be set: attributes, dimensions, and variables
# What we want to modify here is the variables
with Dataset(all_files[0], 'r', format='NETCDF4') as src:
    with Dataset(output_name, 'w', format='NETCDF4') as out:
        # Get the attributes of the original file
        attributes = src.__dict__

        # Add extra field to attrs, e.g. notes
        attributes['TITLE'] += ' (MODIFIED)'
        attributes['NOTE'] = 'Average Top-bottom direction by Mok'

        # Set it into the output
        out.setncatts(attributes)

        # Copy dimensions
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

        # Modify the variable, see function on the cell above
        var_names = []
        for var_name in src.variables.keys():
            initial = var_name.split('_')[0]
            if initial in ['PH', 'T', 'QVAPOR']:
                var_names.append(var_name)
        out = modify_average_z_layers(out, var_names)
        out = modify_remove_wind(out)
        out = modify_reduce_vapor(out)

    print('Done! Congrats 🎉')


#subprocess.call(['mv', output_name, all_files[0]])
