# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:20:42 2021


Workflow to build training library for Arctic_UNet model


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import sys
import Split
import Filter
import Masks
import Augment
import geopandas as gpd
from shapely.ops import cascaded_union
from contextlib import contextmanager



def get_name(file_location):
    filename = file_location.split('/')[-1]
    filename = filename.split('.')
    return filename[0]


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout


def create_library(img, path_t, lib_dir, w, Ovr, f, aug):
    
    fn = get_name(img)

    ### Build subfolders
    if os.path.isdir(lib_dir) is False:
        print('Creating training library folders')
        os.makedirs(lib_dir)
        os.makedirs(lib_dir + '/pics')
        os.makedirs(lib_dir + '/masks')
    pics_dir = lib_dir + '/pics'
    masks_dir = lib_dir + '/masks'
    
    
    
    ### Split mosic into tiles
    print('Splitting image: %s...'%fn)
    # with suppress_stdout(): ### suppress the long output
    Split.split_image(input = img,
                            output_dir = pics_dir,
                            patch_w = w,
                            patch_h = w,
                            adj_overlay_x = Ovr,
                            adj_overlay_y = Ovr,
                            out_format = f
                            )
    os.remove('split_image_info.txt')
    
    
    truths = gpd.read_file(path_t)
    crs = truths.crs
    print('\nCascading truths for analysis...')
    truths = gpd.GeoSeries(cascaded_union(truths['geometry']))
    truths = gpd.GeoDataFrame(geometry=truths, crs=crs)
    
    
    ### Remove bad tiles from library (usually edge tiles) & Re-number
    Filter.remove(pics_dir, truths)
    
    
    
    ### Create ground truth masks for tiles. Remove non-overlapping tiles
    Masks.create_masks(path_t, lib_dir, pics_dir, masks_dir, img)
    
    
    
    ### Augment tile-mask pairs to grow library
    Augment.augment_images(lib_dir, aug)
    
    
    
    print('\nLibrary build successful\n\n')
    
    return
