"""
Created on Tue Oct 20 11:03:24 2026

@author: madelinezhang
"""

## loading libraries
import os
import requests
import calendar

## set up intitial variables
# station name codes
stations = ['CHB', 'FKE', 'FKO', 'HED', 'JEJ', 'MTS', 'NGS',
            'NIG', 'OSK', 'PHM', 'SEO', 'SND', 'SNS', 'SPR', 
            'TKB', 'TKO', 'TYM', 'ULN', 'ULS', 'UTY', 'ZMY']

## set up working directory and folder 
# folder destination
folder_base = '/gucnas3/madeline/adnet' 
os.chdir(folder_base) # set working directory 

# set years [toggle for data extent]
start_year = 2024
end_year = 2026

for year in range(start_year, end_year+1):
    
    YY = str(year % 100)

    for MM in range(1,13): 
        
        # detect how many days in the month
        num_days = calendar.monthrange(year, MM)[1]
        days = [str(day).zfill(2) for day in list(range(1,num_days+1))]
        
        # add leading zero if needed to month var
        MM = str(MM).zfill(2)
        
        # make a folder if it doesn't already exist 
        if not os.path.exists(YY+MM):
            os.mkdir(YY+MM)
        
        for PPP in stations: 
            
            for DD in days: 
            
                file_name = PPP+YY+MM+DD + '.nc'
                file_path = folder_base + '/' + YY+MM + ''
                
                ## download file 
                # download url 
                url_base = 'https://www-lidar.nies.go.jp/AD-Net/ncdf/'
                
                # download url with file information
                url = url_base + YY+MM + '/' + file_name
                
                # url = 'https://www-lidar.nies.go.jp/AD-Net/ncdf/1801/TKO180101.nc' 
                response = requests.get(url) 
                
                if response.status_code == 200:
                    with open(file_path+'/' +file_name, 'wb') as file:
                        file.write(response.content)
                    print('Success: ' + file_name)
                else:
                    print('Fail: ' + file_name)
    

