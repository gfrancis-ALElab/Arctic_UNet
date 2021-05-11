# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 15:37:37 2021

@author: gfrancis
"""


import os
os.environ['PROJ_LIB'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data\\proj'
os.environ['GDAL_DATA'] = 'C:\\Users\\gfrancis\\Appdata\\Roaming\\Python\\Python37\\site-packages\\osgeo\\data'

# import datetime
from PIL import Image
import glob
import numpy as np





def to_jpg(lib):
    
    
    total_tiles = len([name for name in os.listdir(lib)
                   if os.path.isfile(lib + '\\' + name)])
    
    
    ### Re-number 0->N
    # count = 0
    # for pic in glob.glob(lib + '\\*.tif'):
    #     os.rename(pic, lib + '\\%s.tif'%count)
    #     count += 1
    
    print('Making .jpg copies...')
    for i in range(total_tiles):
        
        Gtif = lib + '\\%s.tif'%i
        G = Image.open(Gtif)
        arr_G = np.array(G)
        Image.fromarray(arr_G.astype(np.uint8)).save(lib + '\\%s.jpg'%i)
    

    return












