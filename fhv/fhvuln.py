# Functions used in analyses
import os
import gdal
import numpy as np
import rasterio
import pandas as pd
import geopandas as gpd
import xlrd
import re

def make_raster(in_ds, fn, data, data_type, nodata=None):
    """Create a one-band GeoTiff.

    in_ds     - datasource to copy projection and geotransform from
    fn        - path to the file to create
    data      - Numpy array containing data to archive
    data_type - output data type
    nodata    - optional NoData burn_values
    """

    driver = gdal.GetDriverByName('gtiff')
    out_ds = driver.Create(
        fn, in_ds.RasterXSize, in_ds.RasterYSize, 1, data_type)
    out_ds.SetProjection(in_ds.GetProjection())
    out_ds.SetGeoTransform(in_ds.GetGeoTransform())
    out_band = out_ds.GetRasterBand(1)
    if nodata is not None:
        out_band.SetNoDataValue(nodata)
    out_band.WriteArray(data)
    out_band.FlushCache()
    #out_band.ComputerStaitstics(False)
    print('"{}" is printed.'.format(fn))
    return out_ds


def upazilaToTable(df, noi, column):
    """Extracts Upazila level vertical data
    """
    import numpy as np
    
#    noi = ('Male', 'Female'); column = 'B'
    codeUp = df.A.str.extract('(\d+)')
    codeUp = codeUp[~codeUp.isna().values].values.astype(int)
    ioi = df.A.str.startswith(noi, na=False)
    count = df.loc[ioi, column].values
    count = count.reshape([int(len(count)/len(noi)),len(noi)]).astype(int)
    count = count[:-1:,:]
    table = np.concatenate((codeUp, count), 1)
    
    return table


def ineiCensus(fn):
    '''
    Read INEI 2017 National Census data (Excel) as Pandas dataframe format.
    Spanish labels are replaced by English labels.
    '''
# =============================================================================
#     #%% INPUT
#     fn = os.path.join('census', 'P08AFILIA.xlsx')
# =============================================================================
    
    # Read variable from Excel file
    df = pd.read_excel(fn, 
                       skiprows = 5,
                       header=0, 
                       index_col=1,
                       skipfooter=3)
    df = df.loc[:, ~df.columns.str.contains('^unnamed', case=False)]
    cols = df.columns
    
    # Update Spanish labels to English
    dfLabel = pd.read_excel(os.path.join('census', 'label_values.xlsx'))
    # Find all rows of variable code and value
    rowCode = np.squeeze(np.where(dfLabel['Spanish'].str.match('Nombre :') == True))
    rowLabel = np.squeeze(np.where(dfLabel['Spanish'].str.match('Value Labels') == True))
    assert len(rowCode) == len(rowLabel)
    # Find a row of the target code
    code = re.split(r"/|.xlsx", fn)[-2]
    cond1 = dfLabel['Spanish'].str.match('Nombre : %s' % code)
    cond2 = dfLabel['Spanish'].str.len() == (9 + len(code))
    row = np.where(cond1 & cond2)[0][0]
    # Read both Spanish and English labels
    idx = rowCode.searchsorted(row)
    df2 = dfLabel.iloc[rowLabel[idx]+1:rowCode[idx+1]]
    label_spn = df2['Spanish'].apply(lambda x: x[x.find('. ')+2:])
    label_eng = df2['English'].apply(lambda x: x[x.find('. ')+2:])
    # Check the number of columns
    nlabel = len(label_spn)
    assert nlabel == np.in1d(cols, label_spn).sum()
    # Replace Spanish labels to English
    index = [np.where(label_spn == x)[0][0] for i, x in enumerate(cols[1:])]
    df.columns = ['District'] + list(label_eng.values[index])
    df.index.name='IDDIST'
    return df
#%%

def bbsCensus(fn):
    '''
    From BBS Census 2011 Excel data to Pandas Dataframe
    '''
    xl = pd.ExcelFile(fn)
    df = xl.parse('Output')
    code = df['Code'].values.astype(int)[:,None]
    df = df.drop(['Code', 'Upazila/Thana Name'], axis=1)
    
    return code, df
    
#%%
    
def distCorrect(dfCensus, method):
    # District map is not consistent with 2017 Census's districts.
    # 120604 (Mazamari) and 120606 (Pangoa) of census data are merged to
    # 120699 (MAZAMARI - PANGOA) of district map
    
    if method == 'sum':
        idMerg = [120604, 120606]
        df = dfCensus.copy()
        df.loc[120699] = df.loc[idMerg].sum()
        df.loc[120699].District = 'Junín, Satipo, distrito de Mazamari-Pagoa'
        
    return df.drop(idMerg)
    

def censusToRaster(out_fn, meta, idmap, data):

# =============================================================================
#     #%% Input
#     out_fn = './census/test.tif'
#     idmap = did.copy()
#     data = page5.copy()
# =============================================================================
    
    # Change metadata
    meta['dtype'] = rasterio.float32
    idmap = idmap.astype(rasterio.float32)
    meta['nodata'] = -9999
    idmap[idmap == idmap[0,0]] = -9999

    # Compare IDs between census Dataframe and idMap
    listImap = np.unique(idmap[idmap != idmap[0,0]])
    listData = data.index.values
    assert len(listImap) == len(listData)
    
    # Distributes data    
    for i in listData:
        idmap[idmap == i] = data[i]
    
    # Write a raster
    with rasterio.open(out_fn, 'w', **meta) as dest:
        dest.write(idmap[None,:,:])
        print('%s is saved.' % out_fn)
        
        


#%%
# =============================================================================
# def censusToRaster(ds, fn, imap, data):
#     '''
#     Distributes district-level data to spatial map
#     '''
#     import os
#     imap = imap.copy()
#     
#     # Distributes data    
#     for i in range(len(data)):
#         imap[imap == data[i,0]] = data[i,1]
# 
#     # Save new raster
#     if not os.path.isfile(fn):
#         out_ds = make_raster(ds, fn, imap, gdal.GDT_Float64, imap[0,0])
#         del out_ds
# 
#     return imap    
# =============================================================================
    
    
def zeroToOne(array):
    '''
    Scale data from 0 to 1
    '''
    data = array[~np.isnan(array)]
    data = (data - data.min())/(data.max()-data.min())
    array[~np.isnan(array)] = data
    
    return array


def timeToCategory(array):
    '''
    Scale travel time to 1-7
    '''
    time = array[~np.isnan(array)]
    time[time < 30] = 1
    time[(30 <= time) & (time < 60)] = 2
    time[(60 <= time) & (time < 120)] = 3
    time[(120 <= time) & (time < 180)] = 3
    time[(180 <= time) & (time < 360)] = 4
    time[(360 <= time) & (time < 720)] = 5
    time[(720 <= time) & (time < 1440)] = 6
    time[(1440 <= time) & (time < 5000)] = 7
    array[~np.isnan(array)] = time
    
    return array
    
def evaluation(name, index, code4):
    
#    index = hous
    mask = (code4 == code4[0,0])
    core = index[~mask]
    print('{} max: {:.3f}, min: {:.3f}'.format(name, core.max(), core.min()))
    
def climInterpolate(clim, code4):
    
#    clim = prec.copy()
    
    x,y = np.where((clim == clim.min()) & (code4 != code4[0,0]))
    clim[x,y] = clim[clim != clim.min()].mean()
        
    return clim
    
    
def affectedGdpFlood(gdp, fdep):
    '''
    Calculated total affected GDP by flood levels
    '''
    
    gdpdata = gdp.copy(); depth = fdep.copy()
    
    depth[depth <= 30] = depth[depth <= 30]/30
    depth[depth > 30] = 1
    
    gdpAfft = np.sum(depth*gdpdata)
    
    return gdpAfft
    

def valueToMap(value, code):
    '''
    Distribute value to Yes-Code region
    '''
    
    output = np.zeros(code.shape)
    output[code] = value
    
    return output
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    