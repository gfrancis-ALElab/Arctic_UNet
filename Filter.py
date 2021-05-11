# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:06:45 2021

@author: gfrancis
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
# import datetime

import warnings
warnings.filterwarnings("ignore")



def data_check(M):
    return ((len(np.unique(M)) == 1) and (np.unique(M)[0] != 0))


def remove_imperfect(lib):
    
    total_tiles = len([name for name in os.listdir(lib)
                       if os.path.isfile(lib + '\\' + name)])
    
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













