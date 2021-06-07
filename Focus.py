# -*- coding: utf-8 -*-
"""
Created on Mon May 31 12:29:20 2021


Plotting tools for visualizing timeline output maps


@author: gfrancis
"""


import os
home = os.path.expanduser('~')
### Set OSGEO env PATHS
os.environ['PROJ_LIB'] = home + r'\Appdata\Roaming\Python\Python37\site-packages\osgeo\data\proj'
os.environ['GDAL_DATA'] = home + r'\Appdata\Roaming\Python\Python37\site-packages\osgeo\data'
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.features as features
from shapely.geometry import shape
from shapely import speedups
speedups.disable()





maps_lib = r'C:\Users\gfrancis\Documents\Planet\SuperReg\Timeline\maps'
pics_lib = r'C:\Users\gfrancis\Documents\Planet\SuperReg\NIR_G_R_mosaics_balanced'
out_dir = r'C:\Users\gfrancis\Documents\Planet\SuperReg\Timeline\Focused'
truths = r'C:\Users\gfrancis\Documents\Planet\WR\Data\ground_truths'
aoi = r'C:\Users\gfrancis\Documents\Planet\SuperReg\AOI\20170701_v2_sreg_ch4_AOI.shp'



def get_name(file_location):
    filename = file_location.split('\\')[-1]
    filename = filename.split('.')
    return filename[0]


def max_bounds(lib):
    
    h = w = 0
    for raster in glob.glob(lib + '/*.tif'):
        
        r = rasterio.open(raster)
        
        if r.meta['height'] > h:
            h = r.meta['height']
        
        if r.meta['width'] > w:
            w = r.meta['width']
    
    return h, w




def stack_filter(maps_lib, pics_lib, out_dir, thresh=0.8, win=10):

    if os.path.isdir(out_dir) is False:
        os.makedirs(out_dir)

    h, w = max_bounds(pics_lib)
    arr = np.zeros((h, w))

    print('Stacking prediction outputs...')
    count = 0
    for raster in glob.glob(pics_lib + '/*.tif'):

        fn = get_name(raster)
        shapefile = maps_lib + '\\' + fn + r'_cascaded_map.shp'

        ras = rasterio.open(raster)
        shapefile = gpd.read_file(shapefile)
        meta = ras.meta.copy()

        temp = out_dir + r'\temp_%s.tif'%fn
        with rasterio.open(temp, 'w+', **meta) as out:
            out_arr = out.read(1)

            # this is where we create a generator of geom, value pairs to use in rasterizing
            shapes = (geom for geom in shapefile.geometry)

            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)

        ras_arr = rasterio.open(temp).read(1)
        # os.remove(temp)

        # if os.path.isfile(temp + r'.aux.xml'):
        #     os.remove(temp + r'.aux.xml')

        if ras_arr.max() > 1:
            ras_arr = np.where(ras_arr > 1, 0, 1)

        if ras_arr.shape == arr.shape:
            arr += ras_arr
        else:
            arr[:ras_arr.shape[0], :ras_arr.shape[1]] += ras_arr

        count += 1
        assert count==arr.max()




    cut = arr.max()*(1 - thresh)
    filtered = np.where(arr > cut, 1, 0)

    ### sliding window max filter
    s = np.int(win/2)
    expanded = np.zeros(filtered.shape)

    print('Performing sliding window max filtering...')
    for j in range(s, filtered[:,0].size - s):
        for i in range(s, filtered[0,:].size - s):
            expanded[j, i] = np.max(filtered[j-s:j+s, i-s:i+s])


    saved_exp = out_dir + '\\expanded.tif'
    meta['nodata'] = 0
    with rasterio.open(saved_exp, 'w+', **meta) as out:
        out.write(expanded.astype(rasterio.uint8), 3) ### visulaize in blue


    with rasterio.open(saved_exp) as data:

        crs = data.crs
        M = data.dataset_mask()
        mask = M != 0

        geo_list = []
        for g, val in features.shapes(M, transform=data.transform, mask=mask):

            # Transform shapes from the dataset's own coordinate system
            geom = rasterio.warp.transform_geom(
                crs, crs, g, precision=6)
            geo_list.append(geom)

    l = []
    for k in range(len(geo_list)):
        l.append(shape(geo_list[k]))

    if len(l) > 0:
        df = pd.DataFrame(l)
        polys = gpd.GeoDataFrame(geometry=df[0], crs=crs)

        polys.to_file(out_dir + '\\expanded.shp')
        print('Focus region saved.')

    return polys



Found_polys = stack_filter(maps_lib, pics_lib, out_dir) #, thresh=0.8, win=10)





