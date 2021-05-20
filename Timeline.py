# -*- coding: utf-8 -*-
"""
Created on Wed May 19 09:02:32 2021


Function for building timeline from prediction map ground truths


@author: Grant Francis
email: gfrancis@uvic.ca
"""


import geopandas as gpd
import glob



def time_machine(path_t, path_p, path_AOI, out_dir, name):
    
    truths = gpd.read_file(path_t)
    crs = truths.crs
    
    aoi = gpd.read_file(path_AOI)
    aoi = aoi.to_crs(crs)
    aoi['area'] = aoi['geometry'].area
    aoi_spec = aoi.loc[aoi['area']==aoi['area'].max()]
    
    print('\nCascading truths for analysis...')
    truths = gpd.GeoSeries(cascaded_union(truths['geometry']))
    truths = gpd.GeoDataFrame(geometry=truths, crs=crs)
    

    for pred_map in glob.glob(path_p + '\\cascaded_map.shp'):
        
        predicted = gpd.read_file(pred_map)
        
        assert truths.crs == predicted.crs
        assert aoi_spec.crs == predicted.crs
        
        print('Calculating areas for:\n...Between Truths...')
        between_t = gpd.overlay(aoi_spec, truths, how='difference')
        
        print('...True Positives...')
        TP = gpd.overlay(predicted, between_t, how='difference')
        
        TP.to_file(out_dir+'%s_TP.shp' % name)
        
    return
        
        
        





