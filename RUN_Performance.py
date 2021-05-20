# -*- coding: utf-8 -*-
"""
Created on Mon May 10 14:23:12 2021


Functions and workfflow to gauge performance metrics of trained moadel


@author: Grant Francis
email: gfrancis@uvic.ca
"""


import os
os.environ['PROJ_LIB'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data\\proj'
os.environ['GDAL_DATA'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data'
import geopandas as gpd
import numpy as np
from shapely import speedups
speedups.disable()
from shapely.ops import cascaded_union



def area(df):
    df['area'] = df['geometry'].area
    return np.sum(df['area']) ### area in m^2

def IOU(df1, df2):
    U = gpd.overlay(df1, df2, how='union')
    I = gpd.overlay(df1, df2, how='intersection')
    return area(I)/area(U)

def process(path_t, path_p, path_AOI):

    truths = gpd.read_file(path_t)
    predicted = gpd.read_file(path_p)
    crs = truths.crs
    
    aoi = gpd.read_file(path_AOI)
    aoi = aoi.to_crs(crs)
    aoi['area'] = aoi['geometry'].area
    aoi_spec = aoi.loc[aoi['area']==aoi['area'].max()]
    
    print('\nCascading truths for analysis...')
    truths = gpd.GeoSeries(cascaded_union(truths['geometry']))
    truths = gpd.GeoDataFrame(geometry=truths, crs=crs)
    
    ### for non-cascaded .shp predictions
    # print('cascading predictions...')
    # predicted = gpd.GeoSeries(cascaded_union(predicted['geometry']))
    # predicted = gpd.GeoDataFrame(geometry=predicted, crs=crs)
    
    assert truths.crs == predicted.crs
    assert aoi_spec.crs == truths.crs
    assert aoi_spec.crs == predicted.crs
    
    ### if aoi is smaller than the truths domain
    # print('Clipping truths to AOI')
    # truths = gpd.clip(truths, aoi)
    
    print('Calculating areas for:\n...Between Truths...')
    between_t = gpd.overlay(aoi_spec, truths, how='difference')
    
    print('...True Positives...')
    TP = gpd.overlay(predicted, between_t, how='difference')
    print('...False Positives...')
    FP = gpd.overlay(predicted, truths, how='difference')
    print('...False Negatives...')
    FN = gpd.overlay(truths, predicted, how='difference')

    prec = area(TP)/(area(TP)+area(FP))
    rec = area(TP)/(area(TP)+area(FN))
    f1 = (2*prec*rec)/(prec+rec)

    return TP, FP, FN, prec, rec, f1, truths, between_t, predicted, aoi_spec


##############################################################################
name = 'Banks_training_eval_40000'
### INPUT DIRECTORIES
truths = r'C:\Users\gfrancis\Documents\Planet\Banks\data\ground_truths\Banks_Island_slumps.shp'
predicted = r'C:\Users\gfrancis\Documents\Planet\Banks\Training_Library_Banks_40000\Prediction_Map_Banks_40000_UNet_100x100_Ovr0_rmsprop_21b_20e_40000a_Banks_40000\Banks_Island_mosaic_NIR_G_R\map\cascaded_map.shp'
AOI = r'C:\Users\gfrancis\Documents\Planet\Banks\Training_Library_Banks_40000\AOI\Banks_Island_mosaic_NIR_G_R_AOI.shp'

### OUTPUT DIRECTORY
HOME = os.path.expanduser('~')
RESULTS_DIR = r'\Documents\Planet\Banks\Training_Library_Banks_40000\Performance_Results_%s' % (name)
path = HOME+RESULTS_DIR
##############################################################################





if os.path.isdir(path) is False:
    os.mkdir(path)
    print ('\nSuccessfully created save directory: \'%s\'' % path)
    SAVE_DIR = path+'\\'

else:
    print('\nDirectory: \'%s\' already exists.' % path)
    input('Continue?')
    SAVE_DIR = path+'\\'

TP, FP, FN, Precision, Recall, F1, tru, betw, pred, aoi = process(truths, predicted, AOI)

print('\nPrecision: %s' % (Precision))
print('Recall: %s' % (Recall))
print('F1: %s' % (F1))


with open(SAVE_DIR+'results_%s.txt' % (name), 'w') as file:
    file.write('Precision: %s\nRecall: %s\nF1: %s' % (Precision, Recall, F1))


TP.to_file(SAVE_DIR+'%s_TP.shp' % name)
FP.to_file(SAVE_DIR+'%s_FP.shp' % name)
FN.to_file(SAVE_DIR+'%s_FN.shp' % name)
tru.to_file(SAVE_DIR+'%s_truths.shp' % name)
betw.to_file(SAVE_DIR+'%s_between.shp' % name)
pred.to_file(SAVE_DIR+'%s_predictions.shp' % name)
aoi.to_file(SAVE_DIR+'%s_AOI.shp' % name)

print('Results saved.')









