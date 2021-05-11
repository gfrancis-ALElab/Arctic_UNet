# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:20:42 2021

Workflow to build library for Arctic_UNet model

@author: gfrancis
"""

import os
# os.environ['PROJ_LIB'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data\\proj'
# os.environ['GDAL_DATA'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data'
import Split
import Filter
import Masks
import Augment
# import datetime



# start = datetime.datetime.now()
# print(str(start))



##############################################################################
######################## Build Library Process ###############################
##############################################################################


def create_library(img, truths, lib_dir, w, Ovr, f, aug):


    ### Build subfolders
    if os.path.isdir(lib_dir) is False:
        print('Creating training library folders')
        os.makedirs(lib_dir)
        os.makedirs(lib_dir + '\\pics')
        os.makedirs(lib_dir + '\\masks')
    pics_dir = lib_dir + '\\pics'
    masks_dir = lib_dir + '\\masks'
    
    
    
    ### Split mosic into tiles
    Split.split_image(input = img,
                            output_dir = pics_dir,
                            patch_w = w,
                            patch_h = w,
                            adj_overlay_x = Ovr,
                            adj_overlay_y = Ovr,
                            out_format = f
                            )
    
    
    
    ### Remove bad tiles from library (usually edge tiles) & Re-number
    Filter.remove_imperfect(pics_dir)
    
    
    
    ### Create ground truth masks for tiles. Remove non-overlapping tiles
    Masks.create_masks(truths, lib_dir, pics_dir, masks_dir, img)
    
    
    
    ### Augment tile-mask pairs to grow library
    Augment.augment_images(lib_dir, aug)
    
    
    
    print('\nLibrary build successful\n\n')
    
    return
