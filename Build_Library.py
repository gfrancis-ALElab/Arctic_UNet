# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:20:42 2021


Workflow to build training library for Arctic_UNet model


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import Split
import Filter
import Masks
import Augment




##############################################################################
######################## Build Library Process ###############################
##############################################################################


def create_library(img, path_t, lib_dir, w, Ovr, f, aug):


    ### Build subfolders
    if os.path.isdir(lib_dir) is False:
        print('Creating training library folders')
        os.makedirs(lib_dir)
        os.makedirs(lib_dir + '\\pics')
        os.makedirs(lib_dir + '\\masks')
    pics_dir = lib_dir + '\\pics'
    masks_dir = lib_dir + '\\masks'
    
    
    
    ### Split mosic into tiles
    # Split.split_image(input = img,
    #                         output_dir = pics_dir,
    #                         patch_w = w,
    #                         patch_h = w,
    #                         adj_overlay_x = Ovr,
    #                         adj_overlay_y = Ovr,
    #                         out_format = f
    #                         )
    
    
    
    ### Remove bad tiles from library (usually edge tiles) & Re-number
    # Filter.remove(pics_dir, path_t)
    
    
    
    ### Create ground truth masks for tiles. Remove non-overlapping tiles
    Masks.create_masks(path_t, lib_dir, pics_dir, masks_dir, img)
    
    
    
    ### Augment tile-mask pairs to grow library
    Augment.augment_images(lib_dir, aug)
    
    
    
    print('\nLibrary build successful\n\n')
    
    return
