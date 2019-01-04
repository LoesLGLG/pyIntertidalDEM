# -*- coding: utf-8 -*-
from __future__ import print_function
import numpy as np
import os
from glob import glob
from scipy.spatial import distance
import csv
from pyproj import Proj

class Dem(object):
    def __init__(self, shorelinedir, waterleveldir, vertrefdir):
       self.__csvdir=shorelinedir 
       self.__wldir=waterleveldir
       self.__outdir=vertrefdir

    def __createOutdir(self,zone):
        '''
        Creates the output directory for each zone at outdir location. 
        '''
        self.outcsvdir = os.path.join(self.__outdir, zone) 
            
        if not os.path.exists(self.outcsvdir):
            os.mkdir(self.outcsvdir)

    def listStation(self,zone):
        '''
        Given the zone name, this function looks for a <zone>.dat file in water
        level directory and loads the corresponding node points where the water
        level was extracted.

        Currently the <zone>.dat file has a header indicating the number of points
        in the following lines - so skip_header=1 was used. 
        '''
        stationfileloc = os.path.join(self.__wldir, str(zone), str(zone)+'.dat')
        nodes = np.genfromtxt(fname=stationfileloc, dtype=float, skip_header=1)
        return nodes

    def __FinddatFile(self, fname, zone):
        '''
        Given the fname of the original shoreline csv file and, tile it belongs 
        to, this function finds the corresponding file with waterlevel information.
        Currently, the waterlevel are expected to be in yyyymmddhhmmss.csv format.
        '''
        pathstr=os.path.basename(fname)
        identifier=pathstr.replace('.csv','')
        identifier=str(identifier).replace('5.0.','')
        date=str(identifier).split('_')[0]
        time=str(identifier).split('_')[1]
        self.__FILEIdent=identifier
        day=date.split('-')[0]
        month=date.split('-')[1]
        year=date.split('-')[2]

        hour=time.split('-')[0]
        minute=time.split('-')[1]
        seconds=time.split('-')[2]
        
        datIdentifier=year+month+day+hour+minute+seconds #name of dat file
        datfile=os.path.join(self.__wldir,str(zone),str(datIdentifier)+'.dat')
        return datfile

    def __findHeights(self, datfile):
        '''
        Return the corresponding water level information only from a comodo
        produced water level file. 
        '''
        with open(str(datfile)) as f:
            lines = f.readlines()
            data = lines[2]
                
        data = str(data).split()
        self.__time=data[0] + ' ' + data[1]
        del data[0] #Date
        del data[0] #time
        
        heightdata = np.array([float(i) for i in data]) #Height data for all given points
        return heightdata

    def __GetPoints(self, csvfile):
        '''
        Reads shoreline csv files, without headers, comma delimited.
        Returns the lon, lat variables
        '''
        points = np.genfromtxt(fname=csvfile, delimiter=',')
        return points

    def __GetInformation(self,point,nodes):
        '''
        Calculate various informaiton regarding a given point and nodes from where
        the depth value will be interpolated.
        The output information is an array of time, lon, lat, nearest lon, nearest lat, distance, height. 
        '''
        btm = Proj('+proj=tmerc +lat_0=0 +lon_0=90 +k=0.9996 +x_0=500000 +y_0=0 +a=6377276.345 +b=6356075.41314024 +units=m +no_defs')
        x = point[0]
        y = point[1]
        x_btm, y_btm = btm(x, y) # find position in BTM
        node=[x_btm,y_btm]
        
        xs = nodes[:,0]
        ys = nodes[:,1]
        
        xs_btm,ys_btm = btm(xs,ys)
        nodes_btm = np.column_stack((xs_btm,ys_btm))
        dist_mat = distance.cdist([node], nodes_btm)
        
        closest_dist = dist_mat.min()
        closest_ind = dist_mat.argmin()
        
        timeInfo = self.__time
        lonInfo = x
        latInfo = y
        nnlonInfo = nodes[closest_ind][0]
        nnlatInfo = nodes[closest_ind][1]
        distanceInfo = closest_dist
        heightInfo = self.heightdata[closest_ind]

        Information=[timeInfo,lonInfo,latInfo,nnlonInfo,nnlatInfo,distanceInfo,heightInfo]
        return Information


    def findClosest(self, nodes, csvfile):
        '''
        findClosest finds the nearest lon,lat point from wl nodes for all the points
        given in csvfile generated by shoreline generation algorithm.
        '''

        outcsvfile = os.path.join(self.outcsvdir, self.__FILEIdent+'.csv')

        points = self.__GetPoints(csvfile)
        
        with open(outcsvfile,"w") as output:
            writer = csv.writer(output, lineterminator='\n')

            for point in points:
                Information = self.__GetInformation(point,nodes)
                writer.writerow(Information)

    def setVertRef(self):
        '''
        setVertRef assembles a dem out of the given shoreline directory and water 
        level information. 
        '''
        zones = os.listdir(self.__csvdir)
        
        for zone in zones:
            self.__createOutdir(zone)
            nodes = self.listStation(zone)
            
            for fname in glob(os.path.join(self.__csvdir, str(zone), '*', '*.csv')):
                datfile = self.__FinddatFile(fname, zone)
                self.heightdata = self.__findHeights(datfile)
                self.findClosest(nodes, fname)

if __name__=='__main__':
    '''
    The setting below is for debugging purpose. It is expected to be removed 
    entirely in the course of refactoring of the codebase.
    '''
    shorelinedir = '/run/media/khan/Workbench/Projects/Sentinel2/T46QCK/Analysis/ImageProcessing'
    waterleveldir = '/run/media/khan/Workbench/Projects/Sentinel2/T46QCK/Analysis/VerticalReferencing/WaterLevels'
    vertrefdir = '/run/media/khan/Workbench/Projects/Sentinel2/T46QCK/Analysis/VerticalReferencing'
    dem = Dem(shorelinedir=shorelinedir, waterleveldir=waterleveldir, vertrefdir=vertrefdir)
    dem.setVertRef()