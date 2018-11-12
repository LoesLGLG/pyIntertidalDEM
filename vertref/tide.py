# -*- coding: utf-8 -*-
from __future__ import print_function
import utide 
import numpy as np
import datetime
import os
import pandas as pd
import matplotlib.dates as mdates
import csv
# Time series input
# Harmonic analysis using utide.solve
# Save the amplitude and phase for the constituents
# CSV or netCDF

class Reader(object):
    def __init__(self):
        __Data=None

    def read_schism(self):
        pass

    def __date_parser(self,year, month, day, hour):
        year, month, day, hour = map(int, (year, month, day, hour))
        return datetime.datetime(year, month, day, hour)
    
    def read_refmar(self,path):
        time=[]
        elev=[]
        
        with open(path) as f:
            lines = f.readlines()
            for i in range (0,len(lines)):
                line=lines[i]
                if str(line).find('#')==-1:
                    DATA=line.split(' ')
                    DMY=DATA[0]
                    HMS=DATA[1]
                    HEIGHT=float(DATA[2])
                    #
                    DMYOB=DMY.split('/')
                    Date=int(DMYOB[0])
                    Month=int(DMYOB[1])
                    Year=int(DMYOB[2])
                    #
                    Hour=int(str(HMS.split(':')[0]))
                    date_time=self.__date_parser(Year,Month,Date,Hour)
                    
                    time.append(date_time)
                    elev.append(HEIGHT)
                
                elif str(line).find('# Latitude: ')!=-1:
                    lat=float(str(line).replace('# Latitude: ',''))
                    
        
        return time,elev,lat
    
    
class TimeSeries(object):
    def __init__(self):
        self.time = None
        self.elev = None
        self.lat= None
        self.reader=Reader()

    def load(self, file,ts):
        self.time, self.elev, self.lat = self.reader.read_refmar(file)
        self.time=mdates.date2num(self.time)
        self.elev=np.array(self.elev)
        setattr(ts,'time',self.time)
        setattr(ts,'elev',self.elev)
        setattr(ts,'lat',self.lat)
        return ts
    

class Analyzer(object):
    def __init__(self,file,Outdir):
        self.__Identifier=str(file).split('/')[-1]+'.csv'
        self.__fileoutdir=os.path.join(Outdir,self.__Identifier)
        self.__TimeseriesObj = TimeSeries()
        self.ts=self.__TimeseriesObj.load(file,self.__TimeseriesObj)
    
    def analyze(self):
       
        self.ha = utide.solve(self.ts.time, self.ts.elev,lat=self.ts.lat,method='ols',conf_int='MC')
        
        
    


    