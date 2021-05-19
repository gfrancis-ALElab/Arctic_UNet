# -*- coding: utf-8 -*-
"""
Created on Thu Apr 29 15:37:37 2021


Short Function to create .JPEG copies of input image tiles for model input


@author: Grant Francis
email: gfrancis@uvic.ca
"""


import os
from PIL import Image
import glob
import numpy as np




def to_jpg(lib):
    
    
    total_tiles = len([name for name in os.listdir(lib)
                   if os.path.isfile(lib + '\\' + name)])
    
    
    print('Making .JPG copies for model input...')
    for i in range(total_tiles):
        
        Gtif = lib + '\\%s.tif'%i
        G = Image.open(Gtif)
        arr_G = np.array(G)
        Image.fromarray(arr_G.astype(np.uint8)).save(lib + '\\%s.jpg'%i)
    

    return












