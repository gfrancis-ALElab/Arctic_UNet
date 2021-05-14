# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:54:19 2021


Workflow for deploying trained model on input image & building map from predictions


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import Split
import Filter
import Convert
import UNet_Predict
import Map





##############################################################################
##################### Build Prediction Map Process ###########################
##############################################################################


def do_your_thang(img, lib_dir, model_name, saved_model, w, Ovr, f):

    ### Build subfolders
    if os.path.isdir(lib_dir) is False:
        print('Making subfolders')
        os.makedirs(lib_dir)
        os.makedirs(lib_dir + '\\tiles')
        os.makedirs(lib_dir + '\\predictions')
        os.makedirs(lib_dir + '\\map')
    tiles_dir = lib_dir + '\\tiles'
    pred_dir = lib_dir + '\\predictions'
    map_dir = lib_dir + '\\map'
    
    
    
    
    
    ### Split mosic into tiles
    Split.split_image(input = img,
                            output_dir = tiles_dir,
                            patch_w = w,
                            patch_h = w,
                            adj_overlay_x = Ovr,
                            adj_overlay_y = Ovr,
                            out_format = f
                            )
    
    
    
    ### Remove bad tiles from library (edge tiles) & Re-number
    Filter.remove_imperfect(tiles_dir)
    
    
    
    ### convert to .JPEG
    Convert.to_jpg(tiles_dir)
    
    
    
    ### create & save predictions
    UNet_Predict.deploy_model(saved_model, tiles_dir, pred_dir)
    
    
    
    ### create map from prediction tiles
    Map.build_map(tiles_dir, pred_dir, map_dir)
    
    return





























