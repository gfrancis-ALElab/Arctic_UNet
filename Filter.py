# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:06:45 2021


Functions for filtering tiles if containing areas of no data


@author: Grant Francis
email: gfrancis@uvic.ca
"""



import os
import numpy as np
import glob
import rasterio
import rasterio.features as features
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely import speedups
speedups.disable()
from shapely.geometry import shape


import warnings
warnings.filterwarnings("ignore")



def data_check(M):
    return ((len(np.unique(M)) == 1) and (np.unique(M)[0] != 0))


def get_name(file_location):
    filename = file_location.split('\\')[-1]
    filename = filename.split('.')
    return filename[0]


def remove(lib, truths_path, overlap_only=True):
    
    total_tiles = len([name for name in os.listdir(lib)
                       if os.path.isfile(lib + '\\' + name)])
    
    
    ### keep only overlap tiles
    if overlap_only:
        
        truths = gpd.read_file(truths_path)
    
    
        print('\nFiltering non-overlapping tiles...')
        
        count = 0
        r = 0
        for pic in glob.glob(lib + '\\*.tif'):
    
            geo_list = []
            with rasterio.open(pic) as dataset:
    
                # copy meta data for mask
                meta = dataset.meta.copy()
    
                # Read the dataset's valid data mask as a ndarray.
                mask = dataset.dataset_mask()
    
                # Extract feature shapes and values from the array.
                for g, val in rasterio.features.shapes(
                        mask, transform=dataset.transform):
    
                    # Transform shapes from the dataset's own coordinate
                    geom = rasterio.warp.transform_geom(
                        dataset.crs, dataset.crs, g, precision=6)
    
                    geo_list.append(geom)
            l = []
            for k in range(len(geo_list)):
                l.append(shape(geo_list[k]))
    
            df = pd.DataFrame(l)
            raster_outline = gpd.GeoDataFrame(geometry=df[0], crs=dataset.crs)
    
            ### only consider ground truths included in current patch to save time
            intersection = gpd.overlay(truths, raster_outline, how='intersection')
    
    
            if intersection.empty == True:
                # print('Removing: %s'%pic)
                os.remove(pic)
                r += 1
            else:
                fn = get_name(pic)
                # print('Ground Truth Overlap at: %s'%fn)
        
            count += 1
        
        print('Total removed: %s'%r)
        print('%s files remaining'%(total_tiles-r))
        
        print('Re-numbering...')
        count = 0
        for pic in glob.glob(lib + '\\*.tif'):
            os.rename(pic, lib + '\\n%s.tif'%count)
            count += 1
        count = 0
        for pic in glob.glob(lib + '\\*.tif'):
            os.rename(pic, lib + '\\%s.tif'%count)
            count += 1
        
        return
    



    else: ### keep all good tiles
    
        print('\nFiltering bad tiles...')
        
        count = 0
        r = 0
        for pic in glob.glob(lib + '\\*.tif'):
            
            # print('Filtering: %s / %s'%(count+1, total_tiles))
        
            geo_list = []
            with rasterio.open(pic) as dataset:
        
                # Read the dataset's valid data mask as a ndarray.
                mask = dataset.dataset_mask()
                meta = dataset.meta.copy()
        
                ### Skip over tile if missing data (blank white areas)
                if not data_check(mask):
                    dataset.close()
                    os.remove(pic)
                    r += 1
                    count += 1
                    continue
                
                if meta['height'] != meta['width']:
                    dataset.close()
                    os.remove(pic)
                    r += 1                
                    
    
            count += 1
        
        print('Total removed: %s'%r)
        print('%s files remaining'%(total_tiles-r))
        
        print('Re-numbering...')
        count = 0
        for pic in glob.glob(lib + '\\*.tif'):
            os.rename(pic, lib + '\\n%s.tif'%count)
            count += 1
        count = 0
        for pic in glob.glob(lib + '\\*.tif'):
            os.rename(pic, lib + '\\%s.tif'%count)
            count += 1
    
    return













