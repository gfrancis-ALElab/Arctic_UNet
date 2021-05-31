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

import Library_Workflow
import UNet_Train
import Predict_Workflow




### Name for training sequence
### (area abr. & date YYYYMMDD)
Train_name = 'WR_8b_40e_70000_balanced'




###                 Training Library Build Settings
##############################################################################
### INPUT DIRECTORIES: training image (.GEOTIFF), ground truths (.SHP)
main_folder = home + r'\Documents\Planet\SuperReg'
img_dir = main_folder + r'\data\NIR_G_R_mosaics'
img = img_dir + r'\20200818_mosaic_NIR_G_R_avg50_scaled(0_255).tif'
path_t = r'C:\Users\gfrancis\Documents\Planet\WR\Data\ground_truths'


### Training Library OUTPUT DIRECTORY
lib_dir = main_folder + r'\Training_Library_' + Train_name

### PARAMETERS:
###    For: Split
w = 100 ### width (pixels)
Ovr = 0 ### overlap (pixels)
f = 'GTIFF' ### output format

###    For: Augmentation
aug = 70000 ### number of augmented images to include in library
##############################################################################
# Library_Workflow.create_library(img, path_t, lib_dir, w, Ovr, f, aug)







###                    Model Training Settings
##############################################################################
### PARAMETERS:
###    For: Training
lib = lib_dir
c = 2 ### number of classes
b = 8 ### batch size
e = 40 ### epochs

### NAME FOR RUN:   (format as: model_dim_opt_batch_epochs_#augs_areaYYMMDD)
name = 'UNet_%sx%s_Ovr%s_rmsprop_%sb_%se_%sa_'%(w,w,Ovr,b,e,aug) + Train_name

### DIRECTORIES FOR MODEL TRAINING HISTORY
save_dir = main_folder + r'\saved_models'
callback_dir = save_dir + '\\' + name
##############################################################################
# UNet_Train.get_smarter(lib, name, callback_dir, save_dir, c, b, e)







###             Deploy Trained Model & Prediction Map Settings
##############################################################################
### OUTPUT DIRECTORY (single map save location)
out_dir = lib_dir + r'\Prediction_Map'

### SAVED MODEL NAME & DIRECTORY
model_name = name + '.h5'
# saved_model = save_dir + '\\' + model_name
saved_model = r'C:\Users\gfrancis\Documents\Planet\WR\saved_models' + '\\' + model_name

### PARAMETERS:
###    For: Split
w = 50 ### width (pixels)
Ovr = 25 ### overlap (pixels)
f = 'GTIFF' ### output format

### Build Timeline?
timeline = True ### set to false for full metrics output

### Reset Directories if making timeline
if timeline:
    img_dir = r'C:\Users\gfrancis\Documents\Planet\SuperReg\NIR_G_R_mosaics_balanced'
    out_dir = main_folder + r'\Timeline_output_typo_test'
##############################################################################
Predict_Workflow.do_your_thang(img_dir, out_dir, path_t, saved_model, w, Ovr, f, timeline)

















