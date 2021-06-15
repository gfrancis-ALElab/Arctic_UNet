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
from PIL import Image
import datetime
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 14})
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
#%%



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
    arr_stack = np.zeros((h, w))
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

        ### read in .SHP & convert to .GEOTIF to extract array from raster
        ### arrays are help individually in arr_list
        ### arrays are aggregated into arr_stack
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
    
        if ras_arr.shape == arr_stack.shape:
            arr_stack += ras_arr
            arr_list.append(ras_arr)
        else:
            arr_stack[:ras_arr.shape[0], :ras_arr.shape[1]] += ras_arr
            temp_arr = np.zeros(arr_stack.shape)
            temp_arr[:ras_arr.shape[0], :ras_arr.shape[1]] += ras_arr
            arr_list.append(temp_arr)
    
        count += 1
    
    
    ### filter out everything below 20th percentile
    ### threshold is 20% of max prominance in stack
    cut = arr_stack.max()*(thresh)
    filtered = np.where(arr_stack > cut, 1, 0)
    
    
    ### save array as .GEOTIF with same meta data as before
    saved = out_dir + '\\stack_%sperc.tif'%str(int(thresh*100))
    meta['nodata'] = 0
    with rasterio.open(saved, 'w+', **meta) as out:
        out.write(filtered.astype(rasterio.uint8), 3) ### visulaize in blue
    
    
    ### convert .GEOTIF into .SHP
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
    
        # polys.to_file(out_dir + '\\stack_%sperc.shp'%str(int(thresh*100)))
    
    
    ### remove polygons that don't overlap ground truths
    print('Applying truths overlap filter')
    truths = gpd.read_file(truths_dir)
    polys['mask'] = list(polys.intersects(truths.unary_union))
    polys_overlap = polys[polys['mask'] == True].geometry
    polys_overlap = gpd.GeoDataFrame(polys_overlap)
    # polys_overlap.to_file(out_dir + '\\overlap_stack_%sperc.shp'%str(int(thresh*100)))
    
    
    ### project filtered & overlapped polygons back into raster for buffer filter
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
    
    
    ### Create buffer around polygons
    ### using sliding window max filter
    s = np.int(win/2)
    expanded = np.zeros(ras_arr2.shape)
    
    print('Performing sliding window max filtering...\n(window size: %s pixels)'%str(s*2))
    for j in range(s, ras_arr2[:,0].size - s):
        for i in range(s, ras_arr2[0,:].size - s):
            expanded[j, i] = np.max(ras_arr2[j-s:j+s, i-s:i+s])
    
    
    ### save array as .GEOTIF with same meta data as before
    saved = out_dir + '\\Priority_%sthresh_%sbuffer.tif'%(str(int(thresh*100)), win)
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
    
        polys_exp.to_file(out_dir + '\\Priority_%sthresh_%sbuffer.shp'%(str(int(thresh*100)), win))
        print('Priority regions saved.')


    ### crop stack and stack list with buffered regions
    stack_clipped = np.where(expanded==1, arr_stack, 0)
    arr_list_clipped = []
    for i in range(len(arr_list)):
        arr_list_clipped.append(np.where(expanded==1, arr_list[i], 0))


    return stack_clipped, arr_list_clipped, meta, names_list



Stack, List, meta, dates = stack_filter_expand(maps_lib, pics_lib, out_dir, truths_dir)



#%%    Process stack list into cumulative list & difference list

if os.path.isdir(out_dir + r'\cumulatives') is False:
    os.makedirs(out_dir + r'\cumulatives')
    os.makedirs(out_dir + r'\differences')
c_out = out_dir + r'\cumulatives'
d_out = out_dir + r'\differences'

### create cumulative list stack in which each is the union of all previous
cumulative = [List[0]]
Image.fromarray(np.uint8(cumulative[0]*255)).save(c_out + '\\%s.jpg'%dates[0])

for i in range(1,len(List)):
    cumulative.append(np.where((List[i]+cumulative[i-1])>0, 1, 0))
    Image.fromarray(np.uint8(cumulative[i]*255)).save(c_out + '\\%s.jpg'%dates[i])

### stack & list consecutive differences
diff = np.zeros(cumulative[0].shape)
diff_list = []
for i in range(len(cumulative)-1):
    diff += cumulative[i+1] - cumulative[i]
    diff_list.append(cumulative[i+1] - cumulative[i])
    Image.fromarray(np.uint8(diff_list[i]*255)).save(d_out + '\\%s.jpg'%dates[i])


#%%    Convert & save .SHP files for cumulatives and differences
    
print('Saving cumulative regions as .SHP files')
for i in range(len(cumulative)):
    
    ### save array as .GEOTIF with same meta data as before
    temp = c_out + '\\temp_%s.tif'%dates[i]
    meta['nodata'] = 0
    with rasterio.open(temp, 'w+', **meta) as out:
        out.write(cumulative[i].astype(rasterio.uint8), 3) ### visulaize in blue
    
    
    ### convert .GEOTIF into .SHP
    with rasterio.open(temp) as data:
    
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
    
        polys.to_file(c_out + '\\%s.shp'%dates[i])
    
    ### delete temporary raster
    os.remove(temp)
    if os.path.isfile(temp + r'.aux.xml'):
        os.remove(temp + r'.aux.xml')
    

print('Saving extent changes as .SHP files')
for i in range(len(diff_list)):
    
    ### save array as .GEOTIF with same meta data as before
    temp = d_out + '\\temp_%s.tif'%dates[i+1]
    meta['nodata'] = 0
    with rasterio.open(temp, 'w+', **meta) as out:
        out.write(diff_list[i].astype(rasterio.uint8), 3) ### visulaize in blue
    
    
    ### convert .GEOTIF into .SHP
    with rasterio.open(temp) as data:
    
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
    
        polys.to_file(d_out + '\\%s.shp'%dates[i+1])
    
    ### delete temporary raster
    os.remove(temp)
    if os.path.isfile(temp + r'.aux.xml'):
        os.remove(temp + r'.aux.xml')



#%%    Compile Total Area Timeline

def area(df):
    df['area'] = df['geometry'].area
    return np.sum(df['area']) ### area in m^2

area_c = []
Dates = []
i = 0
for shapefile in glob.glob(c_out + '/*.shp'):
    
    shapes = gpd.read_file(shapefile)
    area_c.append(area(shapes))
    Dates.append(datetime.date(int(dates[i][:4]), int(dates[i][4:6]), int(dates[i][6:])))
    i+=1


area_d = []
i = 0
for shapefile in glob.glob(d_out + '/*.shp'):
    
    shapes = gpd.read_file(shapefile)
    area_d.append(area(shapes))
    i+=1

### convert to ha
area_c = np.array(area_c)*0.0001

#%%    Plot timelines

fig_lib = r'C:\Users\gfrancis\Documents\Figures'


plt.figure(figsize=(20,10))
plt.scatter(Dates, area_c, color='black', s=7)
# plt.plot(Dates[1:], area_d)
plt.ylabel('Area [ha]')
plt.xlabel('Date [YYYY]')
plt.title('Willow River\nThaw Slump Extent\n(within 50 $km^2$ AOI)')
# plt.tight_layout()
plt.savefig(fig_lib + '\\timeline_scatter.svg', format="svg")


#%%

el = []
tv = []
th = []
fo = []
fi = []
si = []
se = []
ei = []
ni = []
tw = []

for i in range(len(area_c)):
    
    if Dates[i] < datetime.date(2012, 1, 1):
        el.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2013, 1, 1):
        tv.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2014, 1, 1):
        th.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2015, 1, 1):
        fo.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2016, 1, 1):
        fi.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2017, 1, 1):
        si.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2018, 1, 1):
        se.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2019, 1, 1):
        ei.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    elif Dates[i] < datetime.date(2020, 1, 1):
        ni.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
    else:
        tw.append((datetime.date(1, Dates[i].month, Dates[i].day), area_c[i]))
#%%
seasons = [tw, ni, ei, se, si, fi, fo, th, tv, el]
years = ['2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011']
m = ['x', 'o', 'v', '2', 's', '+', 'D', '^', '*', 'd']

fig, ax = plt.subplots(figsize=(8,10))
c = 0
for series in seasons:
    # ax.scatter(*zip(*series), s=7, label=years[c])
    ax.plot(*zip(*series), ':', color='black', linewidth=1, marker=m[c], markersize=4, label=years[c])
    c += 1
Fmt = mdates.DateFormatter('%b')
ax.xaxis.set_major_formatter(Fmt)
ticks = ax.get_xticks()
Ticks = []
for i in range(len(ticks)):
    if i%2 != 0: Ticks.append(ticks[i])
plt.xticks(Ticks)
plt.legend(loc=(0.86,0.12))
plt.ylabel('Area [ha]')
plt.xlabel('Date [Mon.]')
plt.title('Willow River\nThaw Slump Extent\n(within 50 $km^2$ AOI)')
# plt.tight_layout()
plt.savefig(fig_lib + '\\timeline_seasonal_bw.svg', format="svg")

















