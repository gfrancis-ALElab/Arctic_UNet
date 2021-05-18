# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 14:54:19 2021


Workflow for deploying trained model on input image & building map from predictions
Ff timeline mode is set to True, then predictions are only for overlap areas


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import Split
import Filter
import Convert
import UNet_Predict
import Map
# import Timeline





def get_name(file_location):
    filename = file_location.split('\\')[-1]
    filename = filename.split('.')
    return filename[0]




def do_your_thang(img_dir, out_dir, truths, saved_model, w, Ovr, f, timeline):

    
    for pic in glob.glob(img_dir + '\\*.tif'):
        
        name = get_name(pic)
        out_dir = out_dir + '\\' + name

        ### Build subfolders
        if os.path.isdir(out_dir) is False:
            print('Making subfolders...')
            os.makedirs(out_dir)
            os.makedirs(out_dir + '\\tiles')
            os.makedirs(out_dir + '\\predictions')
            os.makedirs(out_dir + '\\map')
        tiles_dir = out_dir + '\\tiles'
        pred_dir = out_dir + '\\predictions'
        map_dir = out_dir + '\\map'
        
        
        ### Split mosic into tiles
        Split.split_image(
                        input = pic,
                        output_dir = tiles_dir,
                        patch_w = w,
                        patch_h = w,
                        adj_overlay_x = Ovr,
                        adj_overlay_y = Ovr,
                        out_format = f
                        )
    
        
        ### Remove bad tiles from library (edge tiles) & Re-number
        Filter.remove(tiles_dir, overlap_only=timeline)
        
        
        ### convert to .JPEG
        Convert.to_jpg(tiles_dir)
        
        
        ### create & save predictions
        UNet_Predict.deploy_model(saved_model, tiles_dir, pred_dir)
        
        
        ### create map from prediction tiles
        Map.build_map(tiles_dir, pred_dir, map_dir)
    
    
    # if timeline:
    #     Timeline.time_machine(...)
    
    
    
    
    return





























