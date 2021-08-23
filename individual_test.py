#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 16 17:41:04 2021

@author: feynman
"""




import os
home = os.path.expanduser('~')
### Set OSGEO env PATHS
os.environ['PROJ_LIB'] = '/usr/share/proj'
os.environ['GDAL_DATA'] = '/usr/share/gdal'
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.features as features
from shapely.geometry import shape
from shapely import speedups
speedups.disable()
from PIL import Image
import datetime
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 14})
import matplotlib.dates as mdates
# import matplotlib.ticker as ticker
from natsort import natsorted




maps_lib = home + '/Planet/WR_timeline/Priority_Regions/cumulatives'
out_dir = home + '/Planet/WR_timeline'
truths_dir = home + '/Planet/WR/Data/ground_truths'
rivers_dir = '/Planet/WR/Data/riverbeds'

mapped_dir = home + '/Planet/WR_timeline/Priority_Regions_6/cumulatives/20200917.shp'
mapped = gpd.read_file(mapped_dir)



def get_name(file_location):
    filename = file_location.split('/')[-1]
    filename = filename.split('.')
    return filename[0]



truths = gpd.read_file(truths_dir)
truths['Id'] = truths['Id'].index
# truths.to_file(out_dir + '/truths_ids.shp')






#%%

for index, row in mapped.iterrows():
    
    print(index, ': ', truths[truths.geometry.overlaps(row['geometry'])].Id.tolist())

    

#%%

mapped['area'] = mapped['geometry'].area*0.0001


for row in mapped.iterrows():
    
    print(row[1]['Id'], row[1]['area'])
    
#%%
mapped = mapped.dissolve('Id')







































