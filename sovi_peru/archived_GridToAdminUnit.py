# -*- coding: utf-8 -*-
'''
This script calculates spatial averages of gridded data (PISCO and NMME) to 
administrative units (Department-Province-District).
'''
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from netCDF4 import num2date, Dataset
import shapefile as shp
import math


def graticuleExtent(shp_out, extent, dx, dy):

    minx,maxx,miny,maxy = extent
    nx = int(math.ceil(abs(maxx - minx)/dx))
    ny = int(math.ceil(abs(maxy - miny)/dy))
    w = shp.Writer(shp_out, shp.POLYGON)
    w.autoBalance = 1
    w.field("ID")
    id=0
    
    for j in range(nx):
        for i in range(ny):
            id+=1
            vertices = []
            parts = []
            vertices.append([min(minx+dx*j,maxx),max(maxy-dy*i,miny)])
            vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*i,miny)])
            vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*(i+1),miny)])
            vertices.append([min(minx+dx*j,maxx),max(maxy-dy*(i+1),miny)])
            parts.append(vertices)
            w.poly(parts)
            w.record(id)
    w.close()
    
    # Save a projection file (filename.prj)
    prj = open("%s.prj" % shp_out, "w") 
    epsg = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]' 
    prj.write(epsg)
    prj.close()
    
    print('%s.shp is saved.' % shp_out)




#%% PISCO
filn = '/Users/dlee/data/pisco/PISCOp_V2.1_beta/Monthly_Products/stable/PISCOpm.nc'
nc = Dataset(filn, 'r')
lat = np.array(nc.variables['latitude']); dy = 0.1
lon = np.array(nc.variables['longitude']); dx = 0.1
tim = nc.variables['z']
tim = pd.date_range('1981-01-01', periods=len(tim), freq='M')
# extent: [minx, maxx, miny, maxy]
extent = [lon[0]-dx/2, lon[-1]+dx/2, lat[-1]-dy/2, lat[0]+dy/2]

# Creat a vector grid using latitidue and longitude
# https://gis.stackexchange.com/questions/54119/creating-square-grid-polygon-shapefile-with-python
graticuleExtent('./shp/grid_pisco', extent, dx, dy)

# Intersect with administrative units
# This is manually done in QGIS

# Reproject to UTM zone 18S
grid_dist = gpd.read_file('./shp/grid_pisco_dist.shp')
grid_dist = grid_dist.to_crs({'init': 'epsg:32718'})    # UTM zone 18S
# Caculate areas of all split polygons
grid_dist["area_km2"] = grid_dist['geometry'].area / 10**6
# Save GeoDataFrame to Shapefile
grid_dist.to_file('./shp/grid_pisco_dist_area.shp')


#%% Spatial averages in administrative units
grid = gpd.read_file('./shp/grid_pisco_dist_area.shp')
prcp = np.array(nc.variables['variable'])
ntim, nlat, nlon = prcp.shape
dim = [nlat, nlon]
prcp = np.transpose(prcp, [0,2,1])
prcp = np.reshape(prcp, [ntim, nlat*nlon])

# Grids with no data (update "grid_pisco.shp")
noval = (np.sum([prcp == prcp.min()], 1) == ntim)   # 6,717 grids
temp = gpd.read_file('./shp/grid_pisco.shp')
gid_noval = temp[noval.T].ID.astype(int)            # Grid ID has no value
temp['noval'] = np.transpose(noval*1)               # 1 (no value)
temp.to_file('./shp/grid_pisco.shp')        

# Spatial averages
listID = np.unique(grid.IDDIST)
nID = len(listID)
prcp_dist = np.zeros([prcp.shape[0],nID])
for i in range(nID):
    nid = listID[i]
    subID = grid[grid.IDDIST == nid].ID.astype(int) 
    # Exclude no-value grids
    rdx = np.in1d(subID, gid_noval)
    subID = subID[~rdx]
    # ID starts from 1 in Column-major order, so we subtract 1.
    subID = subID - 1
# =============================================================================
#     subInd = np.unravel_index(subID.values.astype(int), dim, order='F')    
#     subData = prcp[:,subInd[0],subInd[1]]
# =============================================================================
    subData = prcp[:, subID.values]
    subArea = grid[grid.IDDIST == nid][~rdx].area_km2
    prcp_dist[:,i] = (subData @ subArea)/subArea.sum()
    


#%% Snippet of intersection
# =============================================================================
# grid = gpd.read_file('./shp/grid_pisco.shp')
# dist = gpd.read_file('/Users/dlee/data/per/land/admin_ign_idep/DISTRITOS.shp')
# combined = gpd.sjoin(grid, dist, how='left', op="intersects")
# combined.to_file('./shp/grid_pisco_dist2.shp')
# =============================================================================









#%% NMME
filn = '/Users/dlee/data/nmme/precip_mon_CCSM4_19930401_r1i1p1_199304-199403.nc'
nc = Dataset(filn, 'r')
prcp = np.array(nc.variables['PRECIP'])
lat = np.array(nc.variables['LAT']); dy = 1.0
lon = np.array(nc.variables['LON']) - 180; dx = 1.0
# extent: [minx, maxx, miny, maxy]
extent = [lon[0]-dx/2, lon[-1]+dx/2, lat[0]-dy/2, lat[-1]+dy/2]

# Creat a vector grid using latitidue and longitude
graticuleExtent('grid_nmme', extent, dx, dy)








