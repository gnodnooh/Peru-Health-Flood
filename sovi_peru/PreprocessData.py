# -*- coding: utf-8 -*-
'''
    Prepares dataset for the vulnerability assessments
    
    Outputs:
        - dem/dem_30s_peru_admin.tif
        - data/popu_admin_landscan17.tif
        - data/distid_30s.tif
'''
import os
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import fiona

#TODO: function crops raster with shapfile's extent
#def cropRasterExtent(rst_fn, shp_fn, out_fn):


def cropRasterShape(rst_fn, shp_fn, out_fn, all_touched=False):
    '''
    crops raster with shapefile and save as new raster (GeoTiff)
    '''
    # Get feature of the polygon (supposed to be a single polygon)
    with fiona.open(shp_fn, 'r') as shapefile:
        geoms = [feature['geometry'] for feature in shapefile]
    # Crop raster including cells over the lines (all_touched)
    with rasterio.open(rst_fn) as src:
        out_image, out_transform = mask(src, geoms, 
                                        crop=True, 
                                        all_touched=all_touched)
        out_meta = src.meta.copy()
    # Update spatial transform and height & width
    out_meta.update({'driver': 'GTiff',
                     'height': out_image.shape[1],
                     'width': out_image.shape[2],
                     'transform': out_transform})
    # Write the cropped raster
    with rasterio.open(out_fn, 'w', **out_meta) as dest:
        dest.write(out_image)
        print('%s is saved.' % out_fn)



#%% Crop Hydroshed DEM with a country shapefile
#rst_fn = '/Users/dlee/data/gis/hydrosheds/dem_void/sa_dem_30s/sa_dem_30s.tif'
rst_fn = '/Users/dlee/data/gis/hydrosheds/dem_void/sa_dem_30s/sa_dem_30s'
shp_fn = '/Users/dlee/data/per/land/admin_ocha_ign/per_admbnda_adm0_2018.shp'
out_fn = os.path.join('dem', 'dem_30s_peru_admin.tif')
cropRasterShape(rst_fn, shp_fn, out_fn, all_touched=False)


#%% Crop GLOFRIS inundation with a country shapefile
rst_fn = '/Users/dlee/data/glofris/inun_dynRout_RP_00010.tif'
shp_fn = '/Users/dlee/data/per/land/admin_ocha_ign/per_admbnda_adm0_2018.shp'
out_fn = os.path.join('hydro', 'glofris_inun_rp_00010.tif')
cropRasterShape(rst_fn, shp_fn, out_fn, all_touched=False)


#%% Crop LandScan population raster with a country shapeifle
#rst_fn = '/Users/dlee/data/population/LandScan_2015/Population/lspop2015'
rst_fn = '/Users/dlee/data/population/landscan/LandScan Global 2017/lspop2017'
shp_fn = '/Users/dlee/data/per/land/admin_ocha_ign/per_admbnda_adm0_2018.shp'
out_fn = os.path.join('data', 'popu_admin_landscan17.tif')
cropRasterShape(rst_fn, shp_fn, out_fn, all_touched=False)

# Total population of Peru in 2017 was 31,237,385 (INEI) or 32,165,485 (UNPD)
with rasterio.open(out_fn) as src: 
    popu = src.read().squeeze()
    popu17 = np.sum(popu[popu != popu[0,0]])    # 30,931,229

# Calibrate population with PER Census data
#TODO: 





#%% Converting administrative boundary polygon to raster
shp_fn = os.path.join('land', 'admin_ign_idep', 'DISTRITOS.shp')
rst_fn = os.path.join('dem', 'dem_30s_peru_admin.tif')
out_fn = os.path.join('data', 'distid_30s.tif')

# Open the shapefile with GeoPandas
dist = gpd.read_file(shp_fn)
# Open the raster file as a template for feature burning using rasterio
rst = rasterio.open(rst_fn)
# Copy and update the metadata frm the input raster for the output
meta = rst.meta.copy()
meta.update(dtype=rasterio.int32)
# Before burning it, we need to 
dist = dist.assign(IDDIST_int = dist.IDDIST.values.astype(rasterio.int32))
# Burn the features into the raster and write it out
with rasterio.open(out_fn, 'w+', **meta) as out:
    out_arr = out.read(1)
    shapes = ((geom, value) for geom, value in zip(dist.geometry, dist.IDDIST_int))
    burned = rasterio.features.rasterize(shapes=shapes, fill=0, out=out_arr, 
                                         transform=out.transform,
                                         all_touched=False)
    out.write_band(1, burned)
    print('%s is saved' % out_fn)



















#%% Creating a raster of percent of pixel occupied from shapefile
# https://gis.stackexchange.com/questions/281310/creating-a-raster-of-percent-of-pixel-occupied-from-shapefile