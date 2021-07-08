# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 09:30:27 2021


Functions to create .shp map from predition masks using corresponding original tile meta data


@author: Grant Francis
email: gfrancis@uvic.ca
"""
### TODO: make faster by combining shapes without saving every one first

import os
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.features as features
from rasterio.features import shapes
from shapely.geometry import shape
from shapely import speedups
speedups.disable()
from shapely.ops import cascaded_union
from PIL import Image
import glob
import shutil
import pandas as pd





def get_name(file_location):
    filename = file_location.split('/')[-1]
    filename = filename.split('.')
    return int(filename[0])




def combine_shps(map_dir, fn, truths):
    
    input_shp_paths = sorted([
        os.path.join(map_dir, fname)
        for fname in os.listdir(map_dir)
        if fname.endswith(".shp")
    ])
    
    
    joined_shps = gpd.GeoDataFrame({'geometry':[]})
    
    for i in range(len(input_shp_paths)):
        
        S = gpd.read_file(input_shp_paths[i])
        joined_shps = joined_shps.geometry.append(S.geometry)
    
    
    if joined_shps.empty == False:
        joined_shps.to_file(map_dir + '/prediction_map.shp')
        print('Prediction map saved as .SHP')
        
        print('\nCascading predictions...')
        Map = gpd.read_file(map_dir + '/prediction_map.shp')
        crs = Map.crs
        Map = gpd.GeoSeries(cascaded_union(Map['geometry']))
        Map = gpd.GeoDataFrame(geometry=Map, crs=crs)
        Map.to_file(map_dir + '/%s_cascaded_map.shp'%fn)
        print('Cascaded map saved as .SHP\n\n')
        
    else:
        print('** No prediction shapes were found **\n\n\n\n')
        return False
    
    return True



def build_map(tiles_dir, preds_dir, map_dir, fn, truths):

    input_img_paths = sorted([
            os.path.join(preds_dir, fname)
            for fname in os.listdir(preds_dir)
            if fname.endswith(".png")
        ])
        
    print('\nConverting predictions to .GEOTIFF & extracting polygons as .SHP')    
    
    for i in range(len(input_img_paths)):
        
        img = Image.open(input_img_paths[i])
        img_arr = np.array(img)

        
        
        ### convert prediction tile to geotiff using original geotiff metadata
        tif_number = get_name(input_img_paths[i])
        Gtif = tiles_dir + '/%s.tif'%tif_number
        raster = rasterio.open(Gtif)
        meta = raster.meta.copy()
        meta['nodata'] = 0
        # meta['count'] = 1
        
        saved_mask = preds_dir + '/%s.tif'%tif_number
        with rasterio.open(saved_mask, 'w+', **meta) as out:
            # out.write(img_arr.astype(rasterio.uint8), 1)
            # out.write(img_arr.astype(rasterio.uint8), 2)
            out.write(img_arr.astype(rasterio.uint8), 3) ### visulaize in blue
        
        
        
        with rasterio.open(saved_mask) as data:
            
            crs = data.crs
            M = data.dataset_mask()
            mask = M != 0
            
            geo_list = []
            for g, val in features.shapes(M, transform=data.transform, mask=mask):
        
                # Transform shapes from the dataset's own coordinate system
                geom = rasterio.warp.transform_geom(
                    crs, crs, g, precision=6)
                geo_list.append(geom)
        
        l = []
        for k in range(len(geo_list)):
            l.append(shape(geo_list[k]))
        
        if len(l) > 0:
            df = pd.DataFrame(l)
            polys = gpd.GeoDataFrame(geometry=df[0], crs=crs)
            
            polys.to_file(map_dir + '/%s.shp'%tif_number)


    print('\n.GEOTIFF & .SHP files saved in Predictions & Map directories.')
    
    
    print('\nBuilding Map...')
    if combine_shps(map_dir, fn, truths):
        return True
    else:
        return False

















