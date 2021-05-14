# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 17:22:36 2021


Full process sccript for building training library, training, & processing predition map


@author: Grant Francis
email: gfrancis@uvic.ca
"""



import os
home = os.path.expanduser('~')
os.chdir(home + r'\documents\code\arctic_unet') ### directory with code

### Set OSGEO env PATHS
os.environ['PROJ_LIB'] = home + r'\Appdata\Roaming\Python\Python37\site-packages\osgeo\data\proj'
os.environ['GDAL_DATA'] = home + r'\Appdata\Roaming\Python\Python37\site-packages\osgeo\data'

import Build_Library
import UNet_Train
import Predict_and_Process




### Name for Sequence
### (area abr. & date YYYYMMDD)
Train_AOI = 'WR20200818'
Predict_AOI = Train_AOI




###                 Training Library Build Settings
##############################################################################
### INPUT DIRECTORIES: training image (.GEOTIFF), ground truths (.SHP)
img = home + r'\Documents\Planet\WR\training_data\20200818_mosaic_NIR_G_R.tif'
truths = home + r'\Documents\Planet\WR\training_data\ground_truths\Willow_River_Thaw_Slumps_poly.shp'


### Training Library OUTPUT DIRECTORY
lib_dir = home + r'\Documents\Planet\WR\Training_Library_' + Train_AOI

### PARAMETERS:
###    For: Split
w = 100 ### width (pixels)
Ovr = 0 ### overlap (pixels)
f = 'GTIFF' ### output format

###    For: Augmentation
aug = 500 ### number of augmented images to include in library
##############################################################################
Build_Library.create_library(img, truths, lib_dir, w, Ovr, f, aug)







###                    Model Training Settings
##############################################################################
### PARAMETERS:
###    For: Training
c = 2 ### number of classes
b = 21 ### batch size
e = 20 ### epochs

### NAME FOR RUN:   (format as: model_dim_opt_batch_epochs_#augs_areaYYMMDD)
name = 'UNet_%sx%s_Ovr%s_rmsprop_%sb_%se_%sa_'%(w,w,Ovr,b,e,aug) + Train_AOI

### DIRECTORIES FOR MODEL TRAINING HISTORY
callback_dir = lib_dir + '\\' + name
save_dir = lib_dir + r'\saved_models'
##############################################################################
UNet_Train.get_smarter(lib_dir, name, callback_dir, save_dir, c, b, e)







###             Deploy Trained Model & Prediction Map Settings
##############################################################################
### INPUT DIRECTORY: Image for predition (.GEOTIFF)
# img = home + '\\Documents\\Planet_data\\WR\\20200818_mosaic_8bit_rgb.tif'
img = img

### OUTPUT DIRECTORY (save location)
out_dir = lib_dir + r'\Prediction_Map_%s_%s'%(Predict_AOI,name)

### SAVED MODEL NAME & DIRECTORY
model_name = name + '.h5'
saved_model = save_dir + '\\' + model_name

### PARAMETERS:
###    For: Split
w = 50 ### width (pixels)
Ovr = 25 ### overlap (pixels)
f = 'GTIFF' ### output format
##############################################################################
Predict_and_Process.do_your_thang(img, out_dir, model_name, saved_model, w, Ovr, f)

















