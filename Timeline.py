# -*- coding: utf-8 -*-
"""
Created on Wed May 19 09:02:32 2021


Function for building timeline from prediction map ground truths


@author: Grant Francis
email: gfrancis@uvic.ca
"""


import geopandas as gpd
import glob





def time_machine(path_t, path_p, path_AOI):
    
    truths = gpd.read_file(path_t)
    crs = truths.crs
    
    aoi = gpd.read_file(path_AOI)
    aoi = aoi.to_crs(crs)
    aoi['area'] = aoi['geometry'].area
    aoi_spec = aoi.loc[aoi['area']==aoi['area'].max()]
    
    print('\nCascading truths...')
    truths = gpd.GeoSeries(cascaded_union(truths['geometry']))
    truths = gpd.GeoDataFrame(geometry=truths, crs=crs)


    predicted = gpd.read_file(path_p)






