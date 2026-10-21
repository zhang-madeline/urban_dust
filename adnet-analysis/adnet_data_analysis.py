#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 11:45:13 2026

@author: madelinezhang
"""

## loading libraries
import os
import glob
import pandas as pd 

## set up working directory and folder 
# folder destination
folder_base = '/gucnas3/madeline/adnet' 
os.chdir(folder_base) # set working directory 

# station name codes
FIXED_STATIONS = ['CHB', 'FKE', 'FKO', 'HED', 'JEJ', 'MTS', 'NGS',
                  'NIG', 'OSK', 'PHM', 'SEO', 'SND', 'SNS', 'SPR', 
                  'TKB', 'TKO', 'TYM', 'ULN', 'ULS', 'UTY', 'ZMY']
            

# set years [toggle for data extent]
start_year = 2018
end_year = 2026

# seen = set()
years, months, stations = [], [], []
for year in range(start_year, end_year+1):
    
    # truncate year
    YY = str(year % 100)

    for MM in range(1,13): 
        
        # add leading zero if needed to month var
        MM = str(MM).zfill(2)
        
 
        for file in glob.glob(folder_base+'/'+YY+MM+'/*'):
            
            file_name = os.path.basename(file)
            station = file_name[0:3]
            
            # if station in seen:
               # continue
            # seen.add(station)
            
            years.append(int(year))
            months.append(int(MM))
            stations.append(station)
            
            
            # print(station) 

# create dataframe and export
df = pd.DataFrame({
        "year": years,
        "month": months,
        "station": stations}).drop_duplicates()

df2 = (pd.crosstab([df["year"], df["month"]], df["station"])
      .reindex(columns=FIXED_STATIONS, fill_value=0)   # include stations that never appear
      .astype(bool))

df2.to_csv(f'adnet_data_availability_{start_year}_{end_year}.csv', index = False)
