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
import AOI



# ##############################################################################
# name = 'Banks_training_eval_40000'
# ### INPUT DIRECTORIES
# truths = r'C:\Users\gfrancis\Documents\Planet\Banks\data\ground_truths\Banks_Island_slumps.shp'
# predicted = r'C:\Users\gfrancis\Documents\Planet\Banks\Training_Library_Banks_40000\Prediction_Map_Banks_40000_UNet_100x100_Ovr0_rmsprop_21b_20e_40000a_Banks_40000\Banks_Island_mosaic_NIR_G_R\map\cascaded_map.shp'
# AOI = r'C:\Users\gfrancis\Documents\Planet\Banks\Training_Library_Banks_40000\AOI\Banks_Island_mosaic_NIR_G_R_AOI.shp'

# ### OUTPUT DIRECTORY
# HOME = os.path.expanduser('~')
# RESULTS_DIR = r'\Documents\Planet\Banks\Training_Library_Banks_40000\Performance_Results_%s' % (name)
# save_path = HOME+RESULTS_DIR
# ##############################################################################



def area(df):
    df['area'] = df['geometry'].area
    return np.sum(df['area']) ### area in m^2


# def IOU(df1, df2):
#     U = gpd.overlay(df1, df2, how='union')
#     I = gpd.overlay(df1, df2, how='intersection')
#     return area(I)/area(U)


def process(truths, predicted, aoi, timeline=False):

    crs = truths.crs
    
    ### if aoi is smaller than the truths domain
    print('Clipping truths to AOI')
    truths = gpd.clip(truths, aoi)
    
    print('Calculating areas for:\n...Between Truths...')
    between_t = gpd.overlay(aoi, truths, how='difference')
    
    print('...True Positives...')
    TP = gpd.overlay(predicted, between_t, how='difference')
    
    if timeline:
        return TP, between_t, None, None, None, None, None
    
    if not timeline:
        print('...False Positives...')
        FP = gpd.overlay(predicted, truths, how='difference')
        print('...False Negatives...')
        FN = gpd.overlay(truths, predicted, how='difference')
    
        prec = area(TP)/(area(TP)+area(FP))
        rec = area(TP)/(area(TP)+area(FN))
        f1 = (2*prec*rec)/(prec+rec)

        return TP, between_t, FP, FN, prec, rec, f1




def run_metrics(truths, map_dir, pic, fn, save_path, timeline):

    crs = truths.crs
    
    aoi = AOI.get_bounds(pic)
    aoi = aoi.to_crs(crs)
    aoi['area'] = aoi['geometry'].area
    aoi_spec = aoi.loc[aoi['area']==aoi['area'].max()] ### TODO: improve with aoi bounds to remove any possible holes
    
    predicted = gpd.read_file(map_dir + '\\cascaded_map.shp')
    assert truths.crs == predicted.crs


    TP, betw, FP, FN, Precision, Recall, F1 = process(truths, predicted, aoi_spec, timeline)
    
    
    TP.to_file(save_path+'\\%s_TP.shp' % fn)
    
    if not timeline:
        print('\nPrecision: %s' % (Precision))
        print('Recall: %s' % (Recall))
        print('F1: %s' % (F1))
    
    
        with open(save_path+'\\metrics_%s.txt' % (fn), 'w') as file:
            file.write('Precision: %s\nRecall: %s\nF1: %s' % (Precision, Recall, F1))
    

        FP.to_file(save_path+'\\%s_FP.shp' % fn)
        FN.to_file(save_path+'\\%s_FN.shp' % fn)
        truths.to_file(save_path+'\\%s_truths.shp' % fn)
        betw.to_file(save_path+'\\%s_between.shp' % fn)
        predicted.to_file(save_path+'\\%s_predictions.shp' % fn)
        aoi_spec.to_file(save_path+'\\%s_AOI.shp' % fn)
    
    print('\nMetrics saved for %s.'%fn)
    

    return







