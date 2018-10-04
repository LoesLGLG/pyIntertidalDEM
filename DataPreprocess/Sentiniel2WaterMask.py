#!/usr/bin/env python3
import time
import matplotlib
import numpy as np
import sys
import matplotlib.pyplot as plt
import os
import scipy.ndimage
from osgeo import gdal,osr




##Read DataSet
def ReadTiffData(File):
    '''
        Reads the Dataset
    '''
    gdal.UseExceptions()
    try:
        __DataSet=gdal.Open(File,gdal.GA_ReadOnly)        #taking readonly data
    
    except RuntimeError as e_Read:                             #Error handling
        print('Error while opening file!')
        print('Error Details:')
        print(e_Read)
        sys.exit(1)
    return __DataSet
##Read Raster Data
def GetTiffData(File):
    '''
        Returns single Raster data as array
    '''
    __DataSet=ReadTiffData(File)

    if(__DataSet.RasterCount==1):                          
        try:
            __RasterBandData=__DataSet.GetRasterBand(1)
            
            __data=__RasterBandData.ReadAsArray()
            
        except RuntimeError as e_arr:                                   #Error handling
            print('Error while data extraction file!')
            print('Error Details:')
            print(e_arr)
            sys.exit(1)
        return __data
    else:
        print('The file contains Multiple bands')
        sys.exit(1)

##Save Geotiff
def SaveArrayToGeotiff(Array,DIRGTIFF,Identifier):
    OutDir=str(os.getcwd())+'/'
    if str(Identifier).find('Zone')!=-1:
        OutDir=OutDir+'Zone/'
        if not os.path.exists(OutDir):
            os.mkdir(OutDir)
    if str(Identifier).find('WaterMask__STD')!=-1:
        OutDir=OutDir+'WaterMask__STD/'
        if not os.path.exists(OutDir):
            os.mkdir(OutDir)
    
    if str(Identifier).find('WaterMask__FIXED')!=-1:
        OutDir=OutDir+'WaterMask__FIXED/'
        if not os.path.exists(OutDir):
            os.mkdir(OutDir)
    
    if str(Identifier).find('Filtered')!=-1:
        OutDir=OutDir+'Filtered/'
        if not os.path.exists(OutDir):
            os.mkdir(OutDir)
    

    print('Saving:'+str(Identifier))
    DataSet=ReadTiffData(DIRGTIFF)
    Projection=DataSet.GetProjection()
    GeoTransform=DataSet.GetGeoTransform()    
    
    GeoTiffFileName =OutDir+str(Identifier)+'.tiff'   # Output geotiff file name according to identifier
    
    Driver = gdal.GetDriverByName('GTiff')
    OutputDataset = Driver.Create(GeoTiffFileName,np.shape(Array)[0],np.shape(Array)[1], 1,gdal.GDT_Float32)
    OutputDataset.GetRasterBand(1).WriteArray(Array)
    OutputDataset.SetGeoTransform(GeoTransform)
    OutputDataset.SetProjection(Projection)
    OutputDataset.FlushCache()
    print('Saved:'+str(Identifier))

##CloudMask
def CloudMaskCorrection(BandData,MaskData):
    Decimals=GetDecimalsWithEndBit(np.amax(MaskData))
    for v in range(0,len(Decimals)):
        BandData[MaskData==Decimals[v]]=-10000                #Exclude data point Identifier= - Reflectance value
    return BandData 

def GetDecimalsWithEndBit(MaxValue):
    results=[]
    for i in range(0,MaxValue+1):
        BinaryString=format(i,'08b')
        if(BinaryString[-1]=='1'):
            results.append(i)
    return results



def ProcessAlpha(Directory,AllData):
    DirectoryStrings=str(Directory).split('/')             #split the directory to extract specific folder
        
    DirectoryStrings=list(filter(bool,DirectoryStrings))

    SWIRB11File=str(Directory)+str(DirectoryStrings[-1])+'_FRE_B11.tif'
    SWIRB12File=str(Directory)+str(DirectoryStrings[-1])+'_FRE_B12.tif'
    CloudMask20m=str(Directory)+'/MASKS/'+str(DirectoryStrings[-1])+'_CLM_R2.tif'
    print('Processing Alpha Data:'+str(DirectoryStrings[-1]))
    B11=GetTiffData(SWIRB11File)
    B12=GetTiffData(SWIRB12File)
    CLM=GetTiffData(CloudMask20m)

    B11=CloudMaskCorrection(B11,CLM)
    B12=CloudMaskCorrection(B12,CLM)

    B11=np.array(B11.repeat(2,axis=0).repeat(2,axis=1))
    B12=np.array(B12.repeat(2,axis=0).repeat(2,axis=1))
    
    B11=B11.astype(np.float)
    B12=B12.astype(np.float)
    
    
    iPosB11=(B11==-10000)
    iPosB12=(B12==-10000)

    B11[iPosB11]=AllData[iPosB11]
    B12[iPosB11]=AllData[iPosB12]
    

    B11=(B11-np.nanmin(B11))/(np.nanmax(B11)-np.nanmin(B11))
    B12=(B12-np.nanmin(B12))/(np.nanmax(B12)-np.nanmin(B12))

    Alpha=B11+B12

    Alpha=(Alpha-np.nanmin(Alpha))/(np.nanmax(Alpha)-np.nanmin(Alpha))
    
    return Alpha
    
    
def main(directory,Zones):    

    DataPath=directory
    
    for zone in Zones:
        DataPath=DataPath+str(zone)+'/'
        print('Executing Module for zone:'+str(zone))
        DataFolders=os.listdir(path=DataPath)
        DirGtiff=DataPath+str(DataFolders[0])+'/'+str(DataFolders[0])+'_FRE_B8.tif'#10m resolution Size (10980,10980)
        Gtiff=GetTiffData(DirGtiff)
       
        All=np.zeros(Gtiff.shape)

        for df in DataFolders:
            dirc=DataPath+df+'/'
            Alpha=ProcessAlpha(dirc,All)
            All=All+Alpha
            All=(All-np.nanmin(All))/(np.nanmax(All)-np.nanmin(All))
        
        DataPath=directory
        
        SaveArrayToGeotiff(All,DirGtiff,str(zone)+'__Zone')
        
        
def FilterWaterMask(Data):
    LabeledData,_=scipy.ndimage.measurements.label(Data)
    Value,PixelCount=np.unique(LabeledData,return_counts=True)
    MaxPixel=np.amax(PixelCount[Value>0])
    MaxVal=Value[PixelCount==MaxPixel]
    WF=np.zeros(Data.shape)
    WF[LabeledData==MaxVal[0]]=1
    return WF

def CreateFilteredWaterMask(Zones):
    Png_Dir=str(os.getcwd())+'/Analysis/'
    if not os.path.exists(Png_Dir):
        os.mkdir(Png_Dir)
    
    
    textfile_path=str(os.getcwd())+'/Analysis/Analysis.txt'
    
    with open(textfile_path, 'a') as textfile:
        textfile.write("|ZONE            Fixed                 0.5*STD\n")
        textfile.write("|---------------------------------------------------------------------------------------------------------------------------\n")
    
    
    for zone in Zones:
        print('*Executing for Zone:'+str(zone))
        ZFile=str(os.getcwd())+'/Zone/'+str(zone)+'__Zone.tiff'
        Data=GetTiffData(ZFile)
        STDthresh=0.5*np.nanstd(Data)
        print('0.5*STD='+str(STDthresh))
        Data=Data/np.nanstd(Data)
        WM_STD=np.ones(Data.shape)
        WM_STD[Data>0.5]=0
        plt.figure('0.5*STD threshold WaterMask:'+str(zone))
        plt.title('0.5*STD threshold WaterMask:'+str(zone))
        plt.imshow(WM_STD)
        plt.savefig(Png_Dir+str(zone)+'__0.5STD.png')
        plt.clf()
        plt.close()
    
        HData=GetTiffData(ZFile)
        sFlag='n'
        while True:
            
            WM_FIXED=np.zeros(HData.shape)
            WM_F_F=np.zeros(HData.shape)
            
            fixedThresh=float(input('Max thresh for watermasking:'))
            
            WM_FIXED[HData<=fixedThresh]=1
            
            plt.figure('Fixed threshold WaterMask of Zone:'+str(zone))
            plt.subplot(121)
            plt.title('Full Water Region:'+str(zone)+':'+str(fixedThresh))
            plt.imshow(WM_FIXED)

            WM_F_F=FilterWaterMask(WM_FIXED)
            

            plt.subplot(122)
            plt.title('Largest Water Body:'+str(zone)+':'+str(fixedThresh))
            plt.imshow(WM_F_F)
            
            plt.show()
            plt.clf()
            plt.close() 
            
            sFlag=str(input('Finalize WaterMask?(y/n)'))

            if(sFlag=='y'):
                plt.figure('Fixed threshold WaterMask of Zone:'+str(zone))
                plt.subplot(121)
                plt.title('Full Water Region:'+str(zone)+':'+str(fixedThresh))
                plt.imshow(WM_FIXED)

                WM_F_F=FilterWaterMask(WM_FIXED)

                plt.subplot(122)
                plt.title('Largest Water Body:'+str(zone)+':'+str(fixedThresh))
                plt.imshow(WM_F_F)

                plt.savefig(Png_Dir+str(zone)+'__Final.png',bbox_inches='tight')
                plt.clf()
                plt.close() 
                break
        print('Saving Fixed threshold WaterMask For:'+str(zone))
        SaveArrayToGeotiff(WM_F_F,ZFile,str(zone)+'__WaterMask__FIXED')
        
        with open(textfile_path, 'a') as textfile:
            textfile.write('|'+str(zone)+'          '+str(fixedThresh)+'          '+str(STDthresh)+"\n")



if __name__=='__main__':
    #directory=input('The Directory of the Data:')
    #Zones=os.listdir(directory)
    #main(directory,Zones)
    Zones=['T45QWE', 'T45QXE', 'T45QYE', 'T46QBK', 'T46QCK', 'T46QBL']
    CreateFilteredWaterMask(Zones)
    