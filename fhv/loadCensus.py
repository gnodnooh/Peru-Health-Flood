# -*- coding: utf-8 -*-
'''
    This script imports 2017 Peruvian national census data and distribute to 
    1km x 1km grids. The original census data was obtained from the Nathional 
    Institute of Statistics and Information (INEI): 
    http://censos2017.inei.gob.pe/redatam/
    
    Donghoon Lee, Apr-10-2019
'''
import os
import numpy as np
import gdal
import fhvuln as fhv
import pandas as pd
import rasterio

# Load a raster of district IDs
with rasterio.open(os.path.join('data', 'distid_30s.tif')) as src:
    did = src.read().squeeze()
    meta = src.meta.copy()
    

#%% Load INEI Census 2017 data
# C2P1: Type of Housing (hous, 0-1) 
# (#house_Kutcha_and_Jhupri / #house_total)
# *Pucca means high quality materials (e.g., cement or RCC)
# *Kutcha & Jhupri means weaker materials (e.g., mud, clay, lime, or thatched)
fn = os.path.join('census', 'C2P1.xlsx')
df = fhv.ineiCensus(fn)
totalHous1 = df.sum(axis=1).sum()

fn = os.path.join('census', 'C2P2.xlsx')
df = fhv.ineiCensus(fn)
totalHous2 = df.sum(axis=1).sum()


# Age
# Surveyed population:  29,381,884
# Ommited population:    1,855,501
# Total population:     31,237,385  
fn = os.path.join('census', 'EDQUINQ.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
popu = df.sum(axis=1)           # Total population: 29381884
# - Percent of elderly population (65+ years)
page5 = df[df.columns[1]]/df.sum(axis=1)
# - Percent children under 5 years
page65 = df[df.columns[14:]].sum(axis=1)/df.sum(axis=1)

# Gender
fn = os.path.join('census', 'C5P2.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
# - Percent females
pfem = df['Woman']/df.sum(axis=1)
# - Percent housholds that are female owned
# *** DOWNLOAD ***


# Special needs population
# - Percent population with disability
fn = os.path.join('census', 'P09DISC.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
pdisability = 1 - df[df.columns[-1]]/df.sum(axis=1)
# Medical services
# - Percent population with health insurance
fn = os.path.join('census', 'P08AFILIA.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
pinsurance = 1 - df[df.columns[-1]]/df.sum(axis=1)


# Built environment
# - Percent households without strong walls
# This excludes 
fn = os.path.join('census', 'C2P3.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
hous = df.sum(axis=1)           # Total households 7698900
PNOCEMENT = 1 - df[df.columns[1:4]].sum(axis=1)/df.sum(axis=1)
# - Percent household without public water supply
fn = os.path.join('census', 'C2P6.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PNOWATER = 1 - df[df.columns[1:3]].sum(axis=1)/df.sum(axis=1)
# - Percent household without electricity
fn = os.path.join('census', 'C2P11.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PNOELECT = df[df.columns[2]]/df.sum(axis=1)
# - Percent household without sewage infrastructure
# This excludes 'Public drainage network within the dwelling' and
# 'Public drainage network outside the home, but inside the building'
fn = os.path.join('census', 'C2P10.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PNOSEWER = 1 - df[df.columns[1:3]].sum(axis=1)/df.sum(axis=1)


# Education
# - Percent population who cannot read and write
fn = os.path.join('census', 'C5P12.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PILLIT = df[df.columns[2]]/df.sum(axis=1)
# - Percent population who don't complete primary education
fn = os.path.join('census', 'C5P13NIV.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PPEDU = df[df.columns[1:3]].sum(axis=1)/df.sum(axis=1)
# - Percent population who don't complete college degree
PCOLLEGE = df[df.columns[1:-2]].sum(axis=1)/df.sum(axis=1)
# fhv.censusToRaster('./census/page5.tif', meta, did, page5)
# fhv.censusToRaster('./census/page5.tif', meta, did, page65)


# Renters
# - Percent 
# Includes: 'Rented', 'Assignment', 'Another way'
fn = os.path.join('census', 'C2P13.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PRENTER = df[df.columns[[1,4,5]]].sum(axis=1)/df.sum(axis=1)


# Socioeconomic status
#TODO: Find cross table from REDATUM
# - Percent households with cell phone or landline
fn = os.path.join('census', 'C3P210.xlsx')
df_phone = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
#fn = os.path.join('census', 'C3P211.xlsx')
#df_landline = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PPHONE = df_phone[df_phone.columns[1]]/df_phone.sum(axis=1)
# - Percent households with automobiles
fn = os.path.join('census', 'C3P214.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
PVEHICLE = df[df.columns[1]]/df.sum(axis=1)
# - Percent households without access to communication and transportation means
#PNOCOM = 


# Family structure
fn = os.path.join('census', 'C4P1.xlsx')
df = fhv.distCorrect(fhv.ineiCensus(fn), 'sum')
AVGHH = df[df.columns[1:]].values.dot(np.arange(31))/df.sum(axis=1)











