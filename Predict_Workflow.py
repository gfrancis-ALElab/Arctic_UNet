# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:54:19 2021


Workflow for deploying trained model on input image & building map from predictions
Ff timeline mode is set to True, then predictions are only for overlap areas


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import sys
import shutil
import glob
import Split
import Filter
import Convert
import UNet_Predict
import Map
import Metrics
from shapely import speedups
speedups.disable()
from shapely.ops import cascaded_union
import geopandas as gpd
from contextlib import contextmanager




def get_name(file_location):
    filename = file_location.split('/')[-1]
    filename = filename.split('.')
    return filename[0]

def get_number(path, pattern):
    count = 0
    for file in glob.glob(path + '/' + pattern):
        count += 1
    return count


@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout


def do_your_thang(img_dir, out_dir, path_t, saved_model, w, Ovr, f, timeline):

    truths = gpd.read_file(path_t)
    crs = truths.crs
    print('\nCascading truths for analysis...')
    truths = gpd.GeoSeries(cascaded_union(truths['geometry']))
    truths = gpd.GeoDataFrame(geometry=truths, crs=crs)

    total = get_number(img_dir, '*tif')
    
    count = 1
    for pic in glob.glob(img_dir + '/*.tif'):
        
        if timeline:
            print('############################# \
                  Timeline Image: %s / %s \
                      ####################################'%(count,total))
    
        out_path = out_dir
        fn = get_name(pic)
        out_dir = out_dir + '/' + fn

        ### Build subfolders
        if os.path.isdir(out_dir) is False:
            os.makedirs(out_dir)
            os.makedirs(out_dir + '/tiles')
            os.makedirs(out_dir + '/predictions')
            os.makedirs(out_dir + '/map')
            os.makedirs(out_dir + '/metrics')
        tiles_dir = out_dir + '/tiles'
        pred_dir = out_dir + '/predictions'
        map_dir = out_dir + '/map'
        met_dir = out_dir + '/metrics'
        
        
        ### Split mosic into tiles
        # print('Splitting image: %s...'%fn)
        # with suppress_stdout(): ### suppress the long output
        #     Split.split_image(
        #                     input = pic,
        #                     output_dir = tiles_dir,
        #                     patch_w = w,
        #                     patch_h = w,
        #                     adj_overlay_x = Ovr,
        #                     adj_overlay_y = Ovr,
        #                     out_format = f
        #                     )
        # os.remove('split_image_info.txt')
    
        
        ### Remove tiles that don't intersect ground truths & Re-number
        # Filter.remove(tiles_dir, truths, overlap_only=True)
        
        
        ### convert to .JPEG
        # Convert.to_jpg(tiles_dir)
        
        
        ### create & save predictions
        UNet_Predict.deploy_model(saved_model, tiles_dir, pred_dir)
        
        
        ### create map from prediction tiles
        if Map.build_map(tiles_dir, pred_dir, map_dir, fn, truths):
        
        
            ### calculate performance metrics (and save True Posities for timeline)
            Metrics.run_metrics(truths, map_dir, pic, fn, met_dir, timeline)
    
        count += 1
    
    
    top_folder = out_path + '/Maps'
    ### create topfolder to consolidate prediction/timeline output
    if os.path.isdir(top_folder) is False:
        os.makedirs(top_folder)
    
        ### copy output maps to top folder
        for file in glob.glob(out_path + '/**/map/*cascaded_map*'):
            shutil.copy(file, top_folder)

    return





























