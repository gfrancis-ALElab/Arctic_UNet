# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 09:18:43 2021


Function that makes corresponding mask for image tiles that overalp ground truths

- Masks are saved as .GEOTIFF (red band only) & .PNG (monochromatic) for model input.
- Corresponding .JPEG copies of original tiles are also created for model input


@author: Grant Francis
email: gfrancis@uvic.ca
"""

import os
import numpy as np
import geopandas as gpd
import rasterio
import rasterio.features as features
import pandas as pd
from shapely.geometry import shape
from PIL import Image
import glob
import shutil




def create_masks(truths_path, lib_dir, pics_dir, masks_dir, img):

    truths = gpd.read_file(truths_path)

    total_tiles = len([name for name in os.listdir(pics_dir)
                   if os.path.isfile(pics_dir + '\\' + name)])

    print('\nLooking for ground truth overlap....')

    c_mask = 0
    c_skip = 0
    joined_tiles = gpd.GeoDataFrame({'geometry':[]})
    for i in range(total_tiles):

        Gtif = pics_dir + '\\%s.tif'%i
        saved_mask = masks_dir + '\\%s.tif'%i
        saved_mask_png = masks_dir + '\\%s.png'%i

        geo_list = []
        with rasterio.open(Gtif) as dataset:

            # copy meta data for mask
            meta = dataset.meta.copy()

            # Read the dataset's valid data mask as a ndarray.
            mask = dataset.dataset_mask()

            # Extract feature shapes and values from the array.
            for g, val in rasterio.features.shapes(
                    mask, transform=dataset.transform):

                # Transform shapes from the dataset's own coordinate
                geom = rasterio.warp.transform_geom(
                    dataset.crs, dataset.crs, g, precision=6)

                geo_list.append(geom)
        l = []
        for k in range(len(geo_list)):
            l.append(shape(geo_list[k]))

        df = pd.DataFrame(l)
        raster_outline = gpd.GeoDataFrame(geometry=df[0], crs=dataset.crs)

        ### only consider ground truths included in current patch to save time
        intersection = gpd.overlay(truths, raster_outline, how='intersection')


        if intersection.empty == False and len(l) == 1:

            c_mask += 1
            print('Creating mask for tile: %s / %s    Total: %s'%(str(i+1),total_tiles,c_mask))

            joined_tiles = joined_tiles.geometry.append(raster_outline.geometry)

            ### original masks saved as .GEOTIF in red band only
            with rasterio.open(saved_mask, 'w+', **meta) as out:
                out_arr = out.read(1)

                # this is where we create a generator of geom, value pairs to use in rasterizing
                shapes = (geom for geom in intersection.geometry)

                burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
                out.write_band(1, burned)

            ### Create PNG Mask
            arr = Image.open(saved_mask).convert('L')
            arr = np.array(arr)
            arr = np.where(arr == 0, 1, 0)
            Image.fromarray(arr.astype(np.uint8)).save(saved_mask_png)

            ### Create JPEG copy of original tile for training
            G = Image.open(Gtif)
            arr_G = np.array(G)
            Image.fromarray(arr_G.astype(np.uint8)).save(pics_dir + '\\%s.jpg'%i)


        ### Otherwise delete tile if not overlapping ground truths
        else:
            # print('******   Removing tile: %s / %s    Saved: %s'%(i,total_tiles,c_mask))

            for retry in range(5):
                try:
                    os.remove(Gtif)
                    break
                except:
                    print('rename failed, retrying...')

            c_skip += 1


    print('\nTotal masks: %s\nTiles not used: %s'%(c_mask, c_skip))
    print('Renumbering .jpgs and .png...')

    ### Re-number 0->N (.jpg tiles)
    count = 0
    for pic in glob.glob(pics_dir + '\\*.jpg'):
        os.rename(pic, pics_dir + '\\N%s.jpg'%count)
        count += 1
    count = 0
    for pic in glob.glob(pics_dir + '\\*.jpg'):
        os.rename(pic, pics_dir + '\\%s.jpg'%count)
        count += 1
        
    ### Re-number 0->N (.png masks)
    count = 0
    for pic in glob.glob(masks_dir + '\\*.png'):
        os.rename(pic, masks_dir + '\\N%s.png'%count)
        count += 1
    count = 0
    for pic in glob.glob(masks_dir + '\\*.png'):
        os.rename(pic, masks_dir + '\\%s.png'%count)
        count += 1



    if os.path.isdir(lib_dir + '\\map') is False:
        os.makedirs(lib_dir + '\\map')

    joined_tiles.to_file(lib_dir + '\\map\\masked_tiles.shp')
    truths.to_file(lib_dir + '\\map\\truths.shp')
    shutil.copy(img, lib_dir + '\\map')

    print('masks & tile .shp files saved.')

    return c_mask
