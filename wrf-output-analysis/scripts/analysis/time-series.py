import xarray as xr
from glob import glob
import matplotlib.pyplot as plt
import pandas as pd
from datetime import timedelta

### functions ###
def fix_time(xr_ds, offset_hours):
    # offset_hours for JP = 9 
    xr_ds = xr_ds.assign_coords(Time=(pd.to_datetime(xr_ds.XTIME.values) + timedelta(hours=offset_hours)))
    xr_ds = xr_ds.sortby("Time")
    return xr_ds.sel(Time=~xr_ds.get_index("Time").duplicated())

# set variables ##!! Change for each output
model_type = "real"
chem_opt = "401" 
dust_opt = "1"
model_input = chem_opt+"_"+dust_opt
wrfout_folder = f"/gs/bs/tga-guc-lab/users/madeline/simulations/dust_test/outputs/ea_{model_type}/{model_input}/"
wrfout_files = glob(wrfout_folder+"wrfout*d01*")

# file = wrfout_files[0]
df = xr.open_mfdataset(wrfout_files, concat_dim='Time', combine='nested')
# df = xr.open_dataset(file)
df_fix = fix_time(df,9)


##  plotting 
fig,axs = plt.subplots(1,1,figsize=(10,5))
#df_fix['DUST_1'].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='red',label='DUST_1')
#df_fix['DUST_2'].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='green',label='DUST_2')
#df_fix['DUST_3'].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='blue',label='DUST_3')
#df_fix['DUST_4'].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='orange',label='DUST_4')
#df_fix['DUST_5'].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='purple',label='DUST_5')
axs.set_xlabel('Date',fontsize=16)
#axs.set_ylabel(f'{df_fix["DUST_1"].units}',fontsize=14)
#axs.set_ylim([0,250])
axs.legend()
axs2 = axs.twinx()
df_fix['QRAIN'][:,0:10,:,:].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs,color='black',linestyle='-',label='qrain_total')
df_fix['QCLOUD'][:,0:10,:,:].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs2,color='black',linestyle='--',label='qcloud_total')
# df_fix['QVAPOR'][:,0:10,:,:].sum(dim=['bottom_top','south_north','west_east']).plot(ax=axs2,color='black',linestyle='-.',label='qvapor_total')
# df_fix['T2'][:,:,:].mean(dim=['south_north','west_east']).plot(ax=axs2,color='black',linestyle=':',label='T2')

# set title
if model_type == "real":
    model_type_string = "Realistic"
elif  model_type == "ideal":
    model_type_string = "Idealized" 

axs.set_title(f'{model_type_string} WRF Output (chem_opt = {chem_opt}, dust_opt = {dust_opt})')

plt.legend()
plt.savefig(f'timeseries-{model_input}-{model_type}.png')
