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
os.environ['PROJ_LIB'] = '/usr/share/proj'
os.environ['GDAL_DATA'] = '/usr/share/gdal'
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
# import matplotlib.ticker as ticker
from natsort import natsorted
#%%

maps_lib = home + '/Planet/WR_timeline/Timeline/Maps'
pics_lib = home + '/Planet/WR_timeline/NIR_G_R_mosaics'
out_dir = home + '/Planet/WR_timeline/Focused_Regions'
truths_dir = home + '/Planet/WR/Data/ground_truths'
rivers_dir = home + '/Planet/WR/Data/riverbeds'

# move line into fxn
rivers = gpd.read_file(rivers_dir)


def get_name(file_location):
    filename = file_location.split('/')[-1]
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
def stack_filter_expand(maps_lib, pics_lib, out_dir, truths_dir, thresh=0.2, win=8):

    if os.path.isdir(out_dir) is False:
        os.makedirs(out_dir)

    h, w, meta = max_bounds(pics_lib)
    arr_stack = np.zeros((h, w))
    arr_list = []
    names_list = []
    print('Stacking prediction outputs...')
    count = 0
    for raster in natsorted(glob.glob(pics_lib + '/*.tif')):

        fn = get_name(raster)
        names_list.append(fn[2:10])
        shapefile = maps_lib + '/' + fn + '_cascaded_map.shp'

        # ras = rasterio.open(raster)
        shapefile = gpd.read_file(shapefile)

        ### read in .SHP & convert to .GEOTIF to extract array from raster
        ### arrays are help individually in arr_list
        ### arrays are aggregated into arr_stack
        temp = out_dir + '/temp_%s.tif'%fn
        with rasterio.open(temp, 'w+', **meta) as out:
            out_arr = out.read(1)

            # this is where we create a generator of geom, value pairs to use in rasterizing
            shapes = (geom for geom in shapefile.geometry)

            burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
            out.write_band(1, burned)

        ras_arr = rasterio.open(temp).read(1)
        os.remove(temp)

        if os.path.isfile(temp + '.aux.xml'):
            os.remove(temp + '.aux.xml')

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
    saved = out_dir + '/stack_%sperc.tif'%str(int(thresh*100))
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

        # polys.to_file(out_dir + '/stack_%sperc.shp'%str(int(thresh*100)))


    ### remove polygons that don't overlap ground truths
    print('Applying truths overlap filter')
    truths = gpd.read_file(truths_dir)
    polys['mask'] = list(polys.intersects(truths.unary_union))
    polys_overlap = polys[polys['mask'] == True].geometry
    polys_overlap = gpd.GeoDataFrame(polys_overlap)
    # polys_overlap.to_file(out_dir + '/overlap_stack_%sperc.shp'%str(int(thresh*100)))


    ### project filtered & overlapped polygons back into raster for buffer filter
    temp = out_dir + '/temp.tif'
    with rasterio.open(temp, 'w+', **meta) as out:
        out_arr = out.read(1)

        # this is where we create a generator of geom, value pairs to use in rasterizing
        shapes = (geom for geom in polys_overlap.geometry)

        burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
        out.write_band(1, burned)

    ras_arr2 = rasterio.open(temp).read(1)
    os.remove(temp)

    if os.path.isfile(temp + '.aux.xml'):
        os.remove(temp + '.aux.xml')


    ### Create buffer around polygons
    ### using sliding window max filter
    s = np.int64(win/2)
    expanded = np.zeros(ras_arr2.shape)
    # expanded = ras_arr2

    print('Performing sliding window max filtering...\n(window size: %sx%s pixels)'%(str(s*2),str(s*2)))
    for j in range(s, ras_arr2[:,0].size - s):
        for i in range(s, ras_arr2[0,:].size - s):
            expanded[j, i] = np.max(ras_arr2[j-s:j+s, i-s:i+s])


    ### save array as .GEOTIF with same meta data as before
    saved = out_dir + '/Priority_%sthresh_%sbuffer.tif'%(str(int(thresh*100)), win)
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
        ### subtract riverbeds
        polys_exp = gpd.overlay(polys_exp, rivers, how='difference')
        polys_exp = polys_exp.explode()
        ### remove separated polygons that don't overlap ground truths
        polys_exp['mask'] = list(polys_exp.intersects(truths.unary_union))
        polys_overlap_exp = polys_exp[polys_exp['mask'] == True].geometry
        polys_overlap_exp = gpd.GeoDataFrame(polys_overlap_exp)
        polys_overlap_exp.to_file(out_dir + '/Priority_%sthresh_%sbuffer.shp'%(str(int(thresh*100)), win))
        priority_ids = gpd.read_file(out_dir)
        priority_ids['Id'] = priority_ids[priority_ids.columns[0]].index
        priority_ids.to_file(out_dir + '/Priority_%sthresh_%sbuffer.shp'%(str(int(thresh*100)), win))
        print('Priority regions saved.')


    ### crop stack and stack list with buffered regions
    stack_clipped = np.where(expanded==1, arr_stack, 0)
    arr_list_clipped = []
    for i in range(len(arr_list)):
        arr_list_clipped.append(np.where(expanded==1, arr_list[i], 0))


    return stack_clipped, arr_list_clipped, meta, names_list, priority_ids



Stack, List, meta, dates, priority = stack_filter_expand(maps_lib, pics_lib, out_dir, truths_dir)



#%%    Process stack list into list of cumulatives & differences

if os.path.isdir(out_dir + '/cumulatives') is False:
    os.makedirs(out_dir + '/cumulatives')
    os.makedirs(out_dir + '/differences')
c_out = out_dir + '/cumulatives'
d_out = out_dir + '/differences'

### create cumulative list stack in which each is the union of all previous
cumulative = [List[0]]
Image.fromarray(np.uint8(cumulative[0]*255)).save(c_out + '/%s.jpg'%dates[0])

for i in range(1,len(List)):
    cumulative.append(np.where((List[i]+cumulative[i-1])>0, 1, 0))
    Image.fromarray(np.uint8(cumulative[i]*255)).save(c_out + '/%s.jpg'%dates[i])

### stack & list consecutive differences
diff = np.zeros(cumulative[0].shape)
diff_list = []
for i in range(len(cumulative)-1):
    diff += cumulative[i+1] - cumulative[i]
    diff_list.append(cumulative[i+1] - cumulative[i])
    Image.fromarray(np.uint8(diff_list[i]*255)).save(d_out + '/%s.jpg'%dates[i])


#%%    Convert to .SHP files (cumulatives & differences) & subtract riverbeds before saving


print('Saving cumulative regions as .SHP files')
for i in range(len(cumulative)):

    ### save array as .GEOTIF with same meta data as before
    temp = c_out + '/temp_%s.tif'%dates[i]
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
        polys = gpd.overlay(polys, rivers, how='difference')
        polys = polys.explode()
        polys['mask'] = list(polys.intersects(priority.unary_union))
        polys_overlap = polys[polys['mask'] == True].geometry
        polys_overlap = gpd.GeoDataFrame(polys_overlap)
        polys_overlap.to_file(c_out + '/%s.shp'%dates[i])

    ### delete temporary raster
    os.remove(temp)
    if os.path.isfile(temp + r'.aux.xml'):
        os.remove(temp + r'.aux.xml')


print('Saving extent changes as .SHP files')
for i in range(len(diff_list)):

    ### save array as .GEOTIF with same meta data as before
    temp = d_out + '/temp_%s.tif'%dates[i+1]
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
        polys = gpd.overlay(polys, rivers, how='difference')
        polys = polys.explode()
        polys['mask'] = list(polys.intersects(priority.unary_union))
        polys_overlap = polys[polys['mask'] == True].geometry
        polys_overlap = gpd.GeoDataFrame(polys_overlap)
        polys_overlap.to_file(d_out + '/%s.shp'%dates[i+1])

    ### delete temporary raster
    os.remove(temp)
    if os.path.isfile(temp + '.aux.xml'):
        os.remove(temp + '.aux.xml')



#%% Give individual features truth overlap Id, Dissolve & give areas


for Map in glob.glob(c_out + '/*.shp'):

    mapped = gpd.read_file(Map)

    intersecting = []
    for index, row in mapped.iterrows():

        intersecting.append(priority[priority.geometry.intersects(row['geometry'])].Id.tolist()[0])


    mapped['Id'] = intersecting
    mapped = mapped.dissolve('Id')
    mapped['area'] = mapped['geometry'].area*0.0001 ### area in ha
    mapped.to_file(Map)



#%%    Compile Total Area Timeline

area_ci = []
area_c = []
Dates = []
i = 0
for shapefile in natsorted(glob.glob(c_out + '/*.shp')):

    Dates.append(datetime.date(int(dates[i][:4]), int(dates[i][4:6]), int(dates[i][6:])))
    shapes = gpd.read_file(shapefile)
    area_ci.append(list(zip(shapes['area'].tolist(), shapes['Id'].tolist())))
    area_c.append(np.sum(shapes['area'].tolist()))
    i+=1

# area_di = []
# area_d = []
# i = 0
# for shapefile in natsorted(glob.glob(d_out + '/*.shp')):

#     shapes = gpd.read_file(shapefile)
#     area_di.append((shapes.area.tolist(), shapes['Id'].tolist()))
#     area_d.append(np.sum(shapes['area'].tolist()))
#     i+=1


#%%    Plot timelines

fig_lib = home + '/Planet/WR_timeline'


plt.figure(figsize=(20,10))
plt.scatter(Dates, area_c, color='black', s=7)
# plt.plot(Dates[1:], area_d)
plt.ylabel('Area [ha]')
plt.xlabel('Date [YYYY]')
plt.title('Willow River\nThaw Slump Extent\n(within 50 $km^2$ AOI)')
# plt.tight_layout()
# plt.savefig(fig_lib + '/timeline_scatter.svg', format="svg")


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
# plt.savefig(fig_lib + '/timeline_seasonal_bw.svg', format="svg")


#%% Create table of individuate area timelines

slump_areas = np.zeros((len(priority['Id']), len(Dates)))

i = 0
for item in area_ci:
    for element in item:
        slump_areas[element[1], i] = element[0]
    i += 1


#%% Plot individual timelines

plt.figure()
for i in range(len(slump_areas[:,0])):

    plt.plot(Dates, slump_areas[i,:], label='Id: %s'%i)
    plt.ylabel('Area [ha]')
    plt.xlabel('Date [YYYY]')
    plt.title('Willow River\nIndividual Thaw Slump Extent\n(within 50 $km^2$ AOI)')
plt.legend(fontsize=7, loc=(1,0))
