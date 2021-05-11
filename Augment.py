# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 14:41:41 2021

@author: gfrancis
"""


import Augmentor
from natsort import natsorted
import glob
import os
from PIL import Image
import numpy as np





def augment_images(lib_dir, num_sample):
    
    rotate = True
    flip_lr = True
    flip_tb = True
    zoom = True
    
    print('\nCreating augmented images')
    
    pics_dir = lib_dir + '\\pics'
    masks_dir = lib_dir + '\\masks'
    
    ground_truth_images = natsorted(glob.glob(pics_dir + '/*.jpg'))
    segmentation_mask_images = natsorted(glob.glob(masks_dir + '/*.png'))
    
    print('\nOriginal tile-mask pairs:')
    for i in range(0, len(ground_truth_images)):
        print("%s: Ground: %s | Mask: %s" % 
              (i+1, os.path.basename(ground_truth_images[i]),
               os.path.basename(segmentation_mask_images[i])))
    
    
    
    collated_images_and_masks = list(zip(ground_truth_images, 
                                         segmentation_mask_images))
    
    images = [[np.asarray(Image.open(y)) for y in x] for x in collated_images_and_masks]
    
    
    p = Augmentor.DataPipeline(images)
    if rotate:
        p.rotate(probability=1, max_left_rotation=5, max_right_rotation=5)
    if flip_lr:
        p.flip_left_right(probability=0.5)
    if zoom:
        p.zoom_random(probability=0.5, percentage_area=0.8)
    if flip_tb:
        p.flip_top_bottom(probability=0.5)
    
    
    ndx = len(ground_truth_images)
    
    augmented_images = p.sample(num_sample)
    
    print('\n')
    for i in range(num_sample):
        print('Adding augmented image: %s / %s'%(i+1, num_sample))
        Image.fromarray(augmented_images[i][0].astype(np.uint8)).save(pics_dir + '\\%s.jpg'%str(i+ndx))
        Image.fromarray(augmented_images[i][1].astype(np.uint8)).save(masks_dir + '\\%s.png'%str(i+ndx))
    
    size_p = len(glob.glob(pics_dir + '/*.jpg'))
    size_m = len(glob.glob(masks_dir + '/*.png'))
    
    print('\nTraining library size:\nTiles: %s\nMasks: %s'%(size_p,size_m))

    return







