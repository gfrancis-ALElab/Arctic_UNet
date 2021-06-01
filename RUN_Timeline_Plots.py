# -*- coding: utf-8 -*-
"""
Created on Mon May 31 12:29:20 2021


Plotting tools for visualizing timeline output maps


@author: gfrancis
"""


import os
import glob
import numpy as np
import random
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import geopandas as gpd
from shapely.ops import cascaded_union

import rasterio
# import rasterio.features as features
from rasterio.plot import show_hist

#%%

maps_lib = r'C:\Users\gfrancis\Documents\Planet\SuperReg\Timeline\Maps'
out_dir = r'C:\Users\gfrancis\Documents\Planet\SuperReg\Timeline\Plots'
truths = r'C:\Users\gfrancis\Documents\Planet\WR\Data\ground_truths'
aoi = r'C:\Users\gfrancis\Documents\Planet\SuperReg\AOI\20170701_v2_sreg_ch4_AOI.shp'
raster = r'C:\Users\gfrancis\Documents\Planet\SuperReg\NIR_G_R_mosaics_balanced\20170701_v2_sreg_ch4_NIR_G_R_avg50_scaled(0_255).tif'
raster = rasterio.open(raster)

#%%

if os.path.isdir(out_dir) is False:
    os.makedirs(out_dir)
    
glist = []
arealist = []
joined = gpd.GeoDataFrame({'geometry':[]})
i = 0
for file in glob.glob(maps_lib + '/*.shp'):
    glist.append(gpd.read_file(file))
    arealist.append(glist[i].area[0])
    joined = joined.geometry.append(glist[i].geometry)
    i += 1
joined = gpd.GeoDataFrame(geometry=joined)


crs = joined.crs
joined_cascaded = gpd.GeoSeries(cascaded_union(joined['geometry']))
joined_cascaded = gpd.GeoDataFrame(geometry=joined_cascaded, crs=crs)


#%%

changelist = []
changearealist = []
for i in range(len(glist)-1):
    changelist.append(gpd.overlay(glist[i+1], glist[i], how='difference'))
    changearealist.append(changelist[i].area[0])



#%%

colors = []
for i in range(len(changelist)):
    colors.append(list(mcolors.get_named_colors_mapping())[random.randint(0,1162)])


#%%
truths = r'C:\Users\gfrancis\Documents\Planet\WR\Data\ground_truths'
truths = gpd.read_file(truths)


fig, ax = plt.subplots()
joined_cascaded.plot(ax=ax, facecolor='none', edgecolor='black')
# glist[0].plot(ax=ax, facecolor='blue', alpha=0.7)
# glist[1].plot(ax=ax, facecolor='orange', alpha=0.7)
for i in range(len(glist)):
    glist[i].plot(ax=ax, facecolor='red', alpha=0.1)
truths.plot(ax=ax, facecolor='none', edgecolor='blue')
# plt.title()
# plt.xlabel('Time')
# plt.ylabel('Area [$m^2$]')
plt.tight_layout()



#%%

fig, ax = plt.subplots()
rasterio.plot.show(raster, ax=ax)
for i in range(len(glist)):
    glist[i].plot(ax=ax, facecolor='red', alpha=0.1)
truths.plot(ax=ax, facecolor='none', edgecolor='blue')






































