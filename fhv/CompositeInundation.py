# -*- coding: utf-8 -*-

'''
This script download remotely sensed flood inundation shapefiles from Dartmouth Flood Observatory (DFO) and
generate composite flood prone areas with frequency.

Donghoon Lee @ Apr-15-2019
'''

import os
import numpy as np
import pandas as pd
import urllib
from bs4 import BeautifulSoup
import zipfile
import rasterio
from rasterio.merge import merge
import rasterio.mask
import fiona
import geopandas as gpd
import re


#%%
#%% Download and Unzip available daily inundation Shapefile from DFO repository
def LinkFromURL(url):
    '''
    Returns all hyperlinks in the URL.
    '''
    # Retreive links in the URL path
    urlpath = urllib.request.urlopen(url)
    html_doc = urlpath.read().decode('utf-8')
    # BeautifulSoup object
    soup = BeautifulSoup(html_doc, 'html.parser')
    # Make a list of hyerlinks
    links = []
    for link in soup.find_all('a'):
        links.append(link.get('href'))
    links.pop(0)     # Remove the parent link        
    return links


def LinkToDirectory(url, links, path_save, underscoreText = None):
    '''
    Returns file directory and names that links will be saved to.
    '''
    
    fullURL = [os.path.join(url, link) for link in links]
    if underscoreText == None:
        fullDIR = [os.path.join(path_save, link) for link in links]
    else:
        fullDIR = [os.path.join(path_save, link+'_'+underscoreText) for link in links]
    return fullURL, fullDIR


def DownloadFromURL(fullURL, fullDIR, showLog = False):
    '''
    Downloads the inserted hyperlinks (URLs) to the inserted files in the disk
    '''
    # Make parent directories if they do not exist
    if type(fullDIR) == list:
        parentDIRS = list(np.unique([os.path.dirname(DIR) for DIR in fullDIR]))
        for parentDIR in parentDIRS:
            os.makedirs(parentDIR, exist_ok=True)
        # Download all files
        nError = 0
        nExist = 0
        nDown = 0
        for file_url, file_dir in zip(fullURL, fullDIR):
            if not os.path.exists(file_dir):
                try:
                    urllib.request.urlretrieve(file_url, file_dir)
                    nDown += 1
                    print(file_dir, 'is saved.')
                except:
                    nError += 1
                    pass
            else:
                nExist += 1
        if showLog:
            print('%d files are tried: %d exist, %d downloads, %d errors' % (len(fullURL),nExist,nDown,nError))
            
    elif type(fullDIR) == str:
        parentDIRS = os.path.dirname(fullDIR)
        # Download all files
        nError = 0
        nExist = 0
        nDown = 0
        if not os.path.exists(fullDIR):
                try:
                    urllib.request.urlretrieve(fullURL, fullDIR)
                    nDown += 1
                    print(fullDIR, 'is saved.')
                except:
                    nError += 1
                    pass
                else:
                    nExist += 1
        if showLog:
            print('%d files are tried: %d exist, %d downloads, %d errors' % (len(fullURL),nExist,nDown,nError))
    return
    
    
def MosaicArea(currentPathList, out_ras):
    '''
    Make a mosaic raster of multiple rasters
    '''
#    https://automating-gis-processes.github.io/CSC18/lessons/L6/raster-mosaic.html
    
    # List for the datafiles that will be part of the mosaic
    src_files_to_mosaic = []
    for currentPath in currentPathList:
        src = rasterio.open(currentPath)
        src_files_to_mosaic.append(src)
    # Merge together and create a mosaic object
    mosaic, out_trans = merge(src_files_to_mosaic)
    mosaic = mosaic.astype(rasterio.int16)
    # Update the metadata with new dimensions, transform, and CRS
    out_meta = src.meta.copy()
    out_meta.update({'driver': 'GTiff',
                     'dtype': 'int16',
                     'height': mosaic.shape[1],
                     'width': mosaic.shape[2],
                     'transform': out_trans})
    # Write it
    with rasterio.open(out_ras, 'w', **out_meta) as dst:
        dst.write(mosaic)
    return
        
        
def MaskByShape(in_ras, in_shp):
    '''
    Mask a raster with a shapefile
    '''
    # Load a raster
    with fiona.open(in_shp, 'r') as shapefile:
        features = [feature["geometry"] for feature in shapefile]
    # Mask with features
    with rasterio.open(in_ras) as src:
        out_image, out_transform = rasterio.mask.mask(src, features, 
                                                      crop=True)
        out_meta = src.meta.copy()
        out_meta.update({"driver": "GTiff",
                         "dtype": 'int16',
                         'compress': 'lzw',
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})
    with rasterio.open(in_ras, "w", **out_meta) as dest:
        dest.write(out_image)
    return


def GetDatesFromURL(areaList, url_daily):
    '''
    Search available dates of data in each areaCode
    '''
    # DataFrame of dates
    dateFrame = pd.DataFrame(columns = areaList)
    for areaCode in areaList:
        # Read hyperlinks in the URL
        fileList = LinkFromURL(url_daily+areaCode)
        tim = [re.search(r'\d{7}', file).group() for file in fileList]
        yr = np.array([ind[:4] for ind in tim]).astype(int)
        day = np.array([ind[4:] for ind in tim]).astype(int)
        tim = pd.to_datetime(yr*1000+day, format = '%Y%j')
        # Date Series of each areaCode
        idx = pd.date_range(start=tim[0], end=tim[-1])
        temp = pd.Series(index = idx, name = areaList[0])
        temp = temp.fillna(0).astype(int)
        temp.loc[tim] = 1
        dateFrame[areaCode] = temp
    return dateFrame

def appendText(filename, text):
    return "{0}{2}.{1}".format(*filename.rsplit('.',1) + [text])


def DownShapefile(url_daily, areaList, date, path_temp):
    '''
    Download available shapefile at the inserted date
    '''
    
    




    return
    

def BurnShapefile():
    '''
    Burn shapefile
    '''
    # Masking?
    return

def DeleteFilesDirectory(path):
    '''
    Delete files in the directory
    '''
    files = [file for file in os.listdir(path) if not file.startswith('.DS')]
    for file in files:
        os.remove(os.path.join(path, file))
    print('Temporary files are removed.')
    return


def DownBurnDelete(url_daily, dates, in_ras, mask_shp, path_temp, path_save):
    '''
    Download daily shapefiles, Burn to the raster, and Delete shapfiles
    '''
    #%%
    dates = dates[dates.sum(axis=1) > 0]
    datesStr = dates.index
    areaList = list(dates.columns)
    os.makedirs(os.path.join(path_save, 'day'), exist_ok=True)
    
    # Delete all files in the temporary folder
    DeleteFilesDirectory(path_temp)
    
    # for each date
    for date in datesStr:
        dateJuln = date.strftime('%Y%j')
        out_ras_day = os.path.join(path_save, 'day', 'inun_'+date.strftime('%Y%m%d')+'.tif')
        if not os.path.exists(out_ras_day):
        
            # Download available shapefiles
            for areaCode in areaList:
                if dates.loc[date][areaCode] == 1:
                    full_url = os.path.join(url_daily, areaCode, dateJuln+'_'+areaCode+'.zip')
                    full_dir = os.path.join(path_temp, dateJuln+'_'+areaCode+'.zip')
                    DownloadFromURL(full_url, full_dir)
            # Unzip downloaded files
            files = [file for file in os.listdir(path_temp) if file.endswith('.zip')]
            for file in files:
                path_file = os.path.join(path_temp, file)
                if zipfile.is_zipfile(path_file):
                    zip_ref = zipfile.ZipFile(path_file, 'r')
                    try:
                        zip_ref.extractall(path_temp)
                    except:
                        pass
                    zip_ref.close()
                    print('%s is unzipped.' % (path_file))
            # Read unzipped shapefiles
            inshpList = [file for file in os.listdir(path_temp) if file.endswith('.shp')]    
            
            # Load default map information
            with rasterio.open(in_ras) as src:
                kwargs = src.meta.copy()
                kwargs.update({
                    'driver': 'GTiff',
                    'compress': 'lzw',
                    'dtype': 'int16'
                })
                # Daily composite inundations
                arr_day = np.zeros(src.read(1).shape).astype('int16')
                with rasterio.open(out_ras_day, 'w', **kwargs) as dst_day:
                    for inshp in inshpList:
                        shapefile = gpd.read_file(os.path.join(path_temp, inshp))
                        if len(shapefile) > 0:
                            shapefile['Junk'] = 1
                            # Get the feagure
                            shapes = ((geom,value) for geom, value in zip(shapefile.geometry, shapefile['Junk']))
                            # Burn the feature
                            burned = rasterio.features.rasterize(shapes=shapes, 
                                                                 fill=0, 
                                                                 out_shape=src.read(1).shape, 
                                                                 transform=src.transform)
                            # Composite array
                            arr_day = arr_day + burned
                            print('%s is burned.' % (inshp))
                        else:
                            pass
                
                    # Write the output raster
                    dst_day.write_band(1, arr_day.astype('int16'))
                
                # Mask with a country shapefile
                MaskByShape(out_ras_day, mask_shp)
                print('%s is saved.' % out_ras_day)
                
                # Delete all files in the temporary folder
                DeleteFilesDirectory(path_temp)
                

    #%%
    return


def main():
    
    # Path to inundation parent directory
    path = '/Users/dlee/data/inundation/dfo'
    # URLs of daily and current inundation
    url_daily = 'https://csdms.colorado.edu/pub/flood_observatory/MODISlance/'
    url_current = 'https://csdms.colorado.edu/pub/flood_observatory/MODISlance_2wkpro/'
    

    # *** INPUT INFORMATION ***
    if False:
        path_save = os.path.join(path, 'per')      # Peru
        areaList = ['090w000s','080w000s','070w000s','080w010s','070w010s']
        mask_shp = '/Users/dlee/data/per/land/admin_ocha_ign/per_admbnda_adm0_2018.shp'
    else:
        path_save = os.path.join(path, 'bgd')      # Bangladesh
        areaList = ['080e030n','090e030n']
        mask_shp = '/Users/dlee/gdrive/bgd/land/boundary_gadm/gadm36_BGD_0.shp'

    
    # Initial folders
    path_temp = os.path.join(path_save, 'temp')
    os.makedirs(path_temp, exist_ok=True)       # Temporary folder
    path_current = os.path.join(path_save, 'current')
    os.makedirs(path_current, exist_ok=True)    # Current folder
    # Download current inundation rasters
    for areaCode in areaList:
        links = LinkFromURL(os.path.join(url_current,areaCode))
        fullURL = [os.path.join(url_current, areaCode, link) for link in links]
        fullDIR = [os.path.join(path_current, appendText(link, '_'+areaCode)) for link in links]
        DownloadFromURL(fullURL, fullDIR, showLog=True)
    # Paths of current GeoTiff files
    currentPathList = [os.path.join(path_current, file) for file in os.listdir(path_current) if file.endswith('.tif')]
    # Current mosaic raster
    in_ras = os.path.join(path_save, 'current_mosaic.tif')
    MosaicArea(currentPathList, in_ras)
    # Mask with a shapefile
    MaskByShape(in_ras, mask_shp)
    # Get available dates of daily inundation
    dates = GetDatesFromURL(areaList, url_daily)        
    # DownBurnDelete at the temporary folder
    DownBurnDelete(url_daily, dates, in_ras, mask_shp, path_temp, path_save)
    
    
#TODO: How about saving spatial indices



if __name__ == "__main__":
    main()







#%%

# =============================================================================
# # Unzip all files
# dir_path = './hydro/inundation/temp_' + areaCode
# if not os.path.exists(dir_path):
#     os.mkdir(dir_path)
# for link in listLink:
#     if zipfile.is_zipfile(dir_out + '/' + link):
#         zip_ref = zipfile.ZipFile(dir_out + '/' + link, 'r')
#         try:
#             zip_ref.extractall(dir_path)
#         except:
#             pass
#         zip_ref.close()
#         print('%s is unzipped.' % (dir_out+'/'+link))
# =============================================================================



# =============================================================================
# #%% Control files and Generate monthly & annual inundation rasters
# # Check filenames and Make time vector to count data
# fileList = [item for item in os.listdir(dir_path) if item.startswith('MSW') and item.endswith('shp')]
# fileList = sorted(fileList)
# tim = [re.search(r'\d{7}', file).group() for file in fileList]
# yr = np.array([ind[:4] for ind in tim]).astype(int)
# day = np.array([ind[4:] for ind in tim]).astype(int)
# tim = pd.to_datetime(yr*1000+day, format = '%Y%j')
# yr = np.unique(tim.year)
# nyr = len(yr)
# timMat = np.zeros([nyr,12])     # To count the number of days in each month
# for y in range(nyr):
#     for m in range(12):
#         timMat[y,m] = np.sum( (tim.year == yr[0]+y) & (tim.month == m+1))
# timMat_nodata = timMat.copy()
# 
# # Load default map information
# inras = './hydro/inundation/current_' + areaCode +'.tif'
# with rasterio.open(inras) as src:
#     kwargs = src.meta.copy()
#     kwargs.update({
#         'driver': 'GTiff',
#         'compress': 'lzw',
#         'dtype': 'int32'
#     })
#     
#     # Aggregate inundation in each month
#     for year in range(nyr):
#         cum_yr = np.zeros(src.read(1).shape).astype('int')
#         outras_yr = './hydro/inundation/inun_%s_%04d.tif' % (areaCode, year+yr[0])
#         
#         with rasterio.open(outras_yr, 'w', **kwargs) as dst_yr:
#             for mon in range(12):
#                 cum_mon = np.zeros(src.read(1).shape).astype('int')
#                 
#                 if not timMat[year,mon] == 0:    
#                     # Input and Output filename
#                     inshpList = np.array(fileList)[(tim.year == yr[0]+year) & (tim.month == mon+1)]
#                     outras_mon = './hydro/inundation/inun_%s_%04d%02d.tif' % (areaCode, year+yr[0], mon+1)
#                     
#                     with rasterio.open(outras_mon, 'w', **kwargs) as dst_mon:
#                         for inshp in inshpList:
#                             shapefile = gpd.read_file(dir_path+'/'+inshp)
#                             if len(shapefile) > 0:
#                                 shapefile['Junk'] = 1
#                                 # Get the feagure
#                                 shapes = ((geom,value) for geom, value in zip(shapefile.geometry, shapefile['Junk']))
#                                 # Burn the feature
#                                 burned = rasterio.features.rasterize(shapes=shapes, 
#                                                                      fill=0, 
#                                                                      out_shape=src.read(1).shape, 
#                                                                      transform=src.transform)
#                                 # Cumulative values
#                                 cum_mon = cum_mon + burned
#                                 cum_yr = cum_yr + burned
#                                 print('%s is burned.' % (dir_path+'/'+inshp))
#                             else:
#                                 timMat_nodata[year,mon] = timMat_nodata[year,mon] - 1
#                     
#                         # The freq_mon is inundated days / available days in a month
#                         freq_mon = cum_mon/timMat_nodata[year,mon] * 100
#                         dst_mon.write_band(1, freq_mon.astype('int32'))
#                         print('%s is saved.' % outras_mon)
#                         
#             # The freq_yr is inundated days / available days in a year
#             freq_yr = cum_yr/sum(timMat_nodata[year,:]) * 100
#             dst_yr.write_band(1, freq_yr.astype('int32'))
#             print('%s is saved.' % outras_yr)
# =============================================================================
     
        
#%%
# How about creating one large (fitted to country line) raster base map and burn
# all shapefiles each day? Burning will work on larger extent...
        

        
        
        
        
        


