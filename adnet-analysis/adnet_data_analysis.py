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

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

# Make sure every month in the range has a row (months with no files = all False)
full_index = pd.MultiIndex.from_product(
    [range(start_year, end_year + 1), range(1, 13)], names=["year", "month"]
)
avail = df2.reindex(full_index, fill_value=False)

# Station counts per month
counts = avail.sum(axis=1)

# Heatmap data: stations on y, year-month on x
data = avail.astype(int).T
labels = [f"{y}-{m:02d}" for y, m in avail.index]
data.columns = labels

fig, (ax_bar, ax_heat) = plt.subplots(
    2, 1, figsize=(24, 8), sharex=True,
    gridspec_kw={"height_ratios": [1, 4], "hspace": 0.05},
)

# Top: number of stations per month
ax_bar.bar(range(len(labels)), counts.values, color="#4a7ab5", width=0.9)
ax_bar.axhline(len(FIXED_STATIONS), color="gray", ls="--", lw=0.8)   # full coverage line
ax_bar.set_ylabel("# stations")
ax_bar.set_title("Station data availability by month")

# Bottom: availability heatmap
sns.heatmap(
    data,
    cmap=ListedColormap(["#d9534f", "#5cb85c"]),
    cbar=False, vmin=0, vmax=1,
    linewidths=0.5, linecolor="white",
    ax=ax_heat,
)
ax_heat.set_xlabel("Year-Month")
ax_heat.set_ylabel("Station")
ax_heat.set_xticks([i + 0.5 for i in range(0, len(labels), 3)])          # label every 3rd month
ax_heat.set_xticklabels(labels[::3], rotation=90)
ax_heat.legend(
    handles=[Patch(color="#5cb85c", label="Available"),
             Patch(color="#d9534f", label="Not available")],
    bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False,
)

plt.savefig(f"adnet_availability_{start_year}_{end_year}.png", dpi=200, bbox_inches="tight")
plt.show()
