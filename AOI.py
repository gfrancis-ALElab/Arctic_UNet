# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 15:18:37 2021

@author: gfrancis
"""

# import numpy as np

# import os
# os.environ['PROJ_LIB'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data\\proj'
# os.environ['GDAL_DATA'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data'
import geopandas as gpd
# from osgeo import gdal
import pandas as pd

from shapely import speedups
speedups.disable()
from shapely.geometry import shape

import rasterio
import rasterio.features
import rasterio.warp





def get_bounds(file_path):

    geo_list = []
    with rasterio.open(file_path) as dataset:
    
        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask()
        # mask = np.where(mask>0, 1, np.nan)
        
        crs = dataset.crs
    
        # Extract feature shapes and values from the array.
        for g, val in rasterio.features.shapes(
                mask, transform=dataset.transform):
    
            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                crs, crs, g, precision=6)
    
            geo_list.append(geom)
    
            # Print GeoJSON shapes to stdout.
            # print(geom)
    
    
    l = []
    for i in range(len(geo_list)):
        l.append(shape(geo_list[i]))
    
    df = pd.DataFrame(l)
    gdf = gpd.GeoDataFrame(geometry=df[0], crs=crs)

    
    
    return gdf
    
    
    
    
    
    
    
    
    
