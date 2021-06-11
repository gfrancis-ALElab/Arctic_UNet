# -*- coding: utf-8 -*-
"""
Created on Mon May 31 12:29:20 2021


Tool for deliniating & expanding on extent which predictions appear in at least
(THRESH) fractoin of timeline images. Boundary expansion is adjusted with (WIN)


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





maps_lib = r'C:\Users\gfrancis\Documents\Planet\WR_timeline\Timeline\Maps'
pics_lib = r'C:\Users\gfrancis\Documents\Planet\WR_timeline\NIR_G_R_mosaics_balanced'
out_dir = r'C:\Users\gfrancis\Documents\Planet\WR_timeline\Priority_Regions'
truths_dir = r'C:\Users\gfrancis\Documents\Planet\WR\Data\ground_truths'




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
    
    return h, w, r.meta


### thresh ### minimum faction of frames needing detection agreement
### win ### window size for sliding window filter
def stack_filter_expand(maps_lib, pics_lib, out_dir, truths_dir, thresh=0.2, win=10):

    if os.path.isdir(out_dir) is False:
        os.makedirs(out_dir)
    
    h, w, meta = max_bounds(pics_lib)
    arr = np.zeros((h, w))
    arr_list = []
    names_list = []
    print('Stacking prediction outputs...')
    count = 0
    for raster in glob.glob(pics_lib + '/*.tif'):
    
        fn = get_name(raster)
        names_list.append(fn[2:10])
        shapefile = maps_lib + '\\' + fn + r'_cascaded_map.shp'
    
        ras = rasterio.open(raster)
        shapefile = gpd.read_file(shapefile)
        # meta = ras.meta.copy()
        # meta['nodata'] = 255
        # meta['height'] = h
        # meta['width'] = w
        # print(meta)
    
        temp = out_dir + r'\temp_%s.tif'%fn
        with rasterio.open(temp, 'w+', **meta) as out:
            out_arr = out.read(1)
    
            # this is where we create a generator of geom, value pairs to use in rasterizing
            shapes = (geom for geom in shapefile.geometry)
    
            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)
    
        ras_arr = rasterio.open(temp).read(1)
        os.remove(temp)
    
        if os.path.isfile(temp + r'.aux.xml'):
            os.remove(temp + r'.aux.xml')
    
        if ras_arr.max() > 1:
            ras_arr = np.where(ras_arr > 1, 0, 1)
    
        if ras_arr.shape == arr.shape:
            arr += ras_arr
            arr_list.append(ras_arr)
        else:
            arr[:ras_arr.shape[0], :ras_arr.shape[1]] += ras_arr
            temp_arr = np.zeros(arr.shape)
            temp_arr[:ras_arr.shape[0], :ras_arr.shape[1]] += ras_arr
            arr_list.append(temp_arr)
    
        count += 1
    
    
    ### calculate differences between dates
    fstack = np.zeros(arr.shape)
    bstack = np.zeros(arr.shape)
    diff_count = 0
    print('Stacking differences...')
    for i in range(len(arr_list)-1):
        diff = arr_list[i+1] - arr_list[i]
        fdiff = np.where(diff==1, 1, 0)
        fstack += fdiff
        bdiff = np.where(diff==-1, -1, 0)
        bstack += bdiff
        diff_count += 1
    
    
    
    cut = arr.max()*(thresh)
    filtered = np.where(arr > cut, 1, 0)
    
    
    ### save array as .GEOTIF with same meta data as before
    saved = out_dir + '\\stack_%sperc.tif'%str(int(thresh*100))
    meta['nodata'] = 0
    with rasterio.open(saved, 'w+', **meta) as out:
        out.write(filtered.astype(rasterio.uint8), 3) ### visulaize in blue
    
    
    with rasterio.open(saved) as data:
    
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
    
        polys.to_file(out_dir + '\\stack_%sperc.shp'%str(int(thresh*100)))
        # print('Stack saved.')
    
    
    
    print('Applying truths overlap filter')
    truths = gpd.read_file(truths_dir)
    polys['mask'] = list(polys.intersects(truths.unary_union))
    polys_overlap = polys[polys['mask'] == True].geometry
    polys_overlap = gpd.GeoDataFrame(polys_overlap)
    polys_overlap.to_file(out_dir + '\\overlap_stack_%sperc.shp'%str(int(thresh*100)))
    
    
    
    ### project filtered & overlapped polygons back into raster for expanding window filter
    temp = out_dir + r'\temp.tif'
    with rasterio.open(temp, 'w+', **meta) as out:
        out_arr = out.read(1)
    
        # this is where we create a generator of geom, value pairs to use in rasterizing
        shapes = (geom for geom in polys_overlap.geometry)
    
        burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
        out.write_band(1, burned)
    
    ras_arr2 = rasterio.open(temp).read(1)
    os.remove(temp)
    
    if os.path.isfile(temp + r'.aux.xml'):
        os.remove(temp + r'.aux.xml')
    
    
    ### sliding window max filter
    s = np.int(win/2)
    expanded = np.zeros(ras_arr2.shape)
    
    print('Performing sliding window max filtering...\n(window size: %s pixels)'%str(s*2))
    for j in range(s, ras_arr2[:,0].size - s):
        for i in range(s, ras_arr2[0,:].size - s):
            expanded[j, i] = np.max(ras_arr2[j-s:j+s, i-s:i+s])
        
            
    ### crop forward & backward differences with expanded priority areas
    fstack = np.where(expanded==1, fstack, 0)
    bstack = np.where(expanded==1, bstack, 0)
    
    
    ### save array as .GEOTIF with same meta data as before
    saved = out_dir + '\\Priority_%st_%sw.tif'%(str(int(thresh*100)), win)
    meta['nodata'] = 0
    with rasterio.open(saved, 'w+', **meta) as out:
        out.write(expanded.astype(rasterio.uint8), 3) ### visulaize in blue
    
    
    with rasterio.open(saved) as data:
    
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
        polys_exp = gpd.GeoDataFrame(geometry=df[0], crs=crs)
    
        polys_exp.to_file(out_dir + '\\Priority_%st_%sw.shp'%(str(int(thresh*100)), win))
        print('Priority regions saved.')


    return arr, arr_list, fstack, bstack



Stack, List, FDiff, BDiff = stack_filter_expand(maps_lib, pics_lib, out_dir, truths_dir)






#%%

DIFF = FDiff + BDiff

#%%

import matplotlib.pyplot as plt
fig, ax = plt.subplots()
# truths.plot(ax=ax, facecolor='black', alpha=0.5)
plt.imshow(DIFF)














