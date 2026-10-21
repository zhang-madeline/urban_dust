#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 11:45:13 2026

@author: madelinezhang
"""

## loading libraries
import os
import glob

## set up working directory and folder 
# folder destination
folder_base = '/Users/madelinezhang/Downloads/adnet' 
os.chdir(folder_base) # set working directory 


# set years [toggle for data extent]
start_year = 2018
end_year = 2022

for year in range(start_year, end_year+1):
    
    # truncate year
    YY = str(year % 100)

    for MM in range(1,13): 
        
        # add leading zero if needed to month var
        MM = str(MM).zfill(2)
        
        for file in glob.glob(folder_base+'/'+YY+MM+'/*'):
            
            print(file) 
    
            