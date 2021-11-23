# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 17:22:36 2021


Full process sccript for building training library, training, & processing predition map
last updated: 2021-08-03


@author: Grant Francis
email: gfrancis@uvic.ca
"""



import os
home = os.path.expanduser('~')
os.chdir(home + '/repos/Arctic_UNet') ### directory with code

### Set OSGEO env PATHS
os.environ['PROJ_LIB'] = '/usr/share/proj'
os.environ['GDAL_DATA'] = '/usr/share/gdal'

import Library_Workflow
import UNet_Train
import Predict_Workflow




### Name for training sequence
Train_name = 'HWC_full'




###                 Training Library Build Settings
##############################################################################
### INPUT DIRECTORIES: training image (.GEOTIFF), ground truths (.SHP)
main_folder = home + '/Planet/HWC'
img_dir = main_folder + '/Data/NIR_G_R_mosaics'
# img = img_dir + '/HotWeatherCreek_Mosaic_NIR_G_R_avg50_scaled0_255.tif'
path_t = main_folder + '/Data/Slumps'


### Training Library OUTPUT DIRECTORY
lib_dir = main_folder + '/TL_' + Train_name

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
c = 2 ### number of classes (DON'T CHANGE THIS)
b = 8 ### batch size
e = 100 ### epochs

### NAME FOR RUN:   (format as: model_dim_opt_batch_epochs_#augs_areaYYMMDD)
name = 'UNet_%sx%s_Ovr%s_rmsprop_%sb_%se_%sa_'%(w,w,Ovr,b,e,aug) + Train_name

### DIRECTORIES FOR MODEL TRAINING HISTORY
save_dir = main_folder + '/saved_models'
callback_dir = save_dir + '/' + name
##############################################################################
UNet_Train.get_smarter(lib, name, callback_dir, save_dir, c, b, e)







###       Deploy Trained Model & Prediction Map / Timeline Settings
##############################################################################
### DIRECOTY WITH IMAGE(S)
img_dir = img_dir

### SAVED MODEL NAME & DIRECTORY
model_name = name + '.h5'
# model_name = ''
saved_model = save_dir + '/' + model_name

### OUTPUT DIRECTORY (single map save location)
out_dir = lib_dir + '/PredMap_' + model_name

### PARAMETERS:
###    For: Split
w = 50 ### width (pixels)
Ovr = 25 ### overlap (pixels)
f = 'GTIFF' ### output format

### Build Timeline?
timeline = False ### full metrics output only if False

### Reset Directories if making timeline
if timeline:
    img_dir = home + '/Planet/Banks_timeline/NIR_G_R_mosaics'
    out_dir = home + '/Planet/Banks_timeline/Timeline'
##############################################################################
Predict_Workflow.do_your_thang(img_dir, out_dir, path_t, saved_model, w, Ovr, f, timeline)
