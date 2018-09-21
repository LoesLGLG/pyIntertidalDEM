from Sentiniel2Logger import Info,TiffReader,TiffWritter,ViewData
import numpy as np,sys 

class BandData(object):
    '''
        The purpose of this class is to Process the Band data
    '''
    def __init__(self,Directory):

        InfoObj=Info(Directory)
        Files=InfoObj.DisplayFileList()
        #Files to be used
        self.__RedBandFile=Files[2]
        self.__GreenBandFile=Files[1]
        self.__BlueBandFile=Files[0]
        self.__AlphaBandFile=Files[3]
        self.__CloudMask10mFile=Files[4]
        self.__CloudMask20mFile=Files[5]
        
        self.TiffReader=TiffReader(Directory)
        self.TiffWritter=TiffWritter(Directory)
        self.DataViewer=ViewData(Directory)
        
   
    
    def __CloudMaskCorrection(self,BandData,MaskData,Identifier):
        
        
        '''
            A cloud mask for each resolution (CLM_R1.tif ou CLM_R2.tif) contains the following 8 Bit data
                - bit 0 (1) : all clouds except the thinnest and all shadows
                - bit 1 (2) : all clouds (except the thinnest)
                - bit 2 (4) : clouds detected via mono-temporal thresholds
                - bit 3 (8) : clouds detected via multi-temporal thresholds
                - bit 4 (16) : thinnest clouds
                - bit 5 (32) : cloud shadows cast by a detected cloud
                - bit 6 (64) : cloud shadows cast by a cloud outside image
                - bit 7 (128) : high clouds detected by 1.38 µm
            
            An aggresive cloud masking is done based on the bit 0 (all clouds except the thinnest and all shadows)
            
            The algorithm for cloud detecting all clouds except the thinnest and all shadows is as follows:
            > Get the maximum value of CLM File
            > Get the decimal numbers that ends with 1 upto the maximum value
            > Set the pixels contains these decimals to negative Reflectance and return the data file  
        
        '''
        print('Processing Cloud Mask With:'+Identifier)                                                                               
        
        __Decimals=self.__GetDecimalsWithEndBit(np.amax(MaskData))

        for v in range(0,len(__Decimals)):
            BandData[MaskData==__Decimals[v]]=-10000                #Exclude data point Identifier= - Reflectance value
        
        return BandData 
    
    
    def __GetDecimalsWithEndBit(self,MaxValue):
        '''
            Detects all the values that contains endbit set to 1
        '''
        __results=[]
        
        for i in range(0,MaxValue+1):
        
            __BinaryString=format(i,'08b')
        
            if(__BinaryString[-1]=='1'):
        
                __results.append(i)
        
        return __results
        
    
    def __NanConversion(self,Data):
        '''
            Converts negative Relfectance values(Cloud and No data values) to Nan
        '''
        Data=Data.astype(np.float)
        Data[Data==-10000]=np.nan
        return Data

    def __NormalizeData(self,Data):
        '''
            Normalizes the data as follows:
            > Cuts of data at 3rd Standard Deviation from mean to avoid highly exceptional valued data
                    
                                Data - Min
            > Data Normalized=-------------
                                Max - Min
        '''        
        Mean=np.nanmean(Data)
        Std=np.nanstd(Data)
      
        Data[Data>Mean+3*Std]=Mean+3*Std
        Data[Data<Mean-3*Std]=Mean-3*Std
        Data=(Data-np.nanmin(Data))/(np.nanmax(Data)-np.nanmin(Data))
        return Data



    def __SaveChannelData(self,Data,Identifier):
        '''
            Save's the Channel data as TIFF and PNG
        '''
        self.DataViewer.PlotWithGeoRef(Data,str(Identifier))
        self.TiffWritter.SaveArrayToGeotiff(Data,str(Identifier))

    
    def __ProcessAlphaChannel(self):
        '''
            The alpha band is taken to be B12 resolution 20m and processed as follows
            > Correct values with 20m cloud mask
            > Upsample the data to 10m
            > Set negative reflectance values to Nan
            > Normalize the data
            > Cut off data which are less than half of Standard deviation to zero
        '''
        self.__AlphaBand=self.TiffReader.GetTiffData(self.__AlphaBandFile) #Read
        
        __CloudMask20m=self.TiffReader.GetTiffData(self.__CloudMask20mFile) #CloudMask
        
        self.__AlphaBand=self.__CloudMaskCorrection(self.__AlphaBand,__CloudMask20m,'Alpha Band 20m')
        
        self.__AlphaBand=np.array(self.__AlphaBand.repeat(2,axis=0).repeat(2,axis=1))
        
        self.__AlphaBand=self.__NanConversion(self.__AlphaBand)
        
        
        ##1.1.1 Alpha CLOUD
        self.__SaveChannelData(self.__AlphaBand,'1.1.1_Alpha_CLM_Upsampled')

        self.__AlphaBand=self.__NormalizeData(self.__AlphaBand)
        
        ##1.1.2 Alpha NORM
        self.__SaveChannelData(self.__AlphaBand,'1.1.2_Alpha_NORM')
        
        self.__AlphaBand[self.__AlphaBand<0.5*np.nanstd(self.__AlphaBand)]=0
        ##1.1.3 Alpha Modified
        self.__SaveChannelData(self.__AlphaBand,'1.1.3 Alpha Modified')
        
        
            
    def __ProcessRedChannel(self):
        '''
            The Red band is taken to be B8 resolution 10m and processed as follows
            > Correct values with 10m cloud mask
            > Set negative reflectance values to Nan
            > Normalize the data
            > Apply alpha to data as Data=(1- Alpha)+ Data*Alpha
        '''
        

        __RedBand=self.TiffReader.GetTiffData(self.__RedBandFile)  #Read

        __CloudMask10m=self.TiffReader.GetTiffData(self.__CloudMask10mFile) #CloudMask
        
        __RedBand=self.__CloudMaskCorrection(__RedBand,__CloudMask10m,'Red Band 10m')
        
        __RedBand=self.__NanConversion(__RedBand)

        #1.2.1 Red CLM
        self.__SaveChannelData(__RedBand,'1.2.1_RED_CLM')

        __RedBand=self.__NormalizeData(__RedBand)

        #1.2.2 Red NORM
        self.__SaveChannelData(__RedBand,'1.2.2_RED_NORM')

        __RedBand=(1-self.__AlphaBand)+(self.__AlphaBand*__RedBand)

        #1.2.3 Red Alpha Applied
        self.__SaveChannelData(__RedBand,'1.2.3_Red_Alpha_Applied')
 
    def __ProcessGreenChannel(self):
        '''
            The Green band is taken to be B4 resolution 10m and processed as follows
            > Correct values with 10m cloud mask
            > Set negative reflectance values to Nan
            > Normalize the data
            > Apply alpha to data as Data=(1- Alpha)+ Data*Alpha
        '''
        
        __GreenBand=self.TiffReader.GetTiffData(self.__GreenBandFile)  #Read

        __CloudMask10m=self.TiffReader.GetTiffData(self.__CloudMask10mFile) #CloudMask
        
        __GreenBand=self.__CloudMaskCorrection(__GreenBand,__CloudMask10m,'Green Band 10m')
        
        __GreenBand=self.__NanConversion(__GreenBand)

        #1.3.1 Green CLM
        self.__SaveChannelData(__GreenBand,'1.3.1_Green_CLM')

        __GreenBand=self.__NormalizeData(__GreenBand)

        #1.3.2 Green NORM
        self.__SaveChannelData(__GreenBand,'1.3.2_Green_NORM')

        __GreenBand=(1-self.__AlphaBand)+(self.__AlphaBand*__GreenBand)

        #1.3.3 Green Alpha Applied
        self.__SaveChannelData(__GreenBand,'1.3.3_Green_Alpha_Applied')


    def __ProcessBlueChannel(self):
        '''
            The Blue band is taken to be B2 resolution 10m and processed as follows
            > Correct values with 10m cloud mask
            > Set negative reflectance values to Nan
            > Normalize the data
            > Apply alpha to data as Data=(1- Alpha)+ Data*Alpha
        '''
        
        __BlueBand=self.TiffReader.GetTiffData(self.__BlueBandFile)  #Read

        __CloudMask10m=self.TiffReader.GetTiffData(self.__CloudMask10mFile) #CloudMask
        
        __BlueBand=self.__CloudMaskCorrection(__BlueBand,__CloudMask10m,'Blue Band 10m')
        
        __BlueBand=self.__NanConversion(__BlueBand)

        #1.4.1 Blue CLM
        self.__SaveChannelData(__BlueBand,'1.4.1_Blue_CLM')

        __BlueBand=self.__NormalizeData(__BlueBand)

        #1.4.2 Blue NORM
        self.__SaveChannelData(__BlueBand,'1.4.2_Blue_NORM')

        __BlueBand=(1-self.__AlphaBand)+(self.__AlphaBand*__BlueBand)

        #1.4.3 Blue Alpha Applied
        self.__SaveChannelData(__BlueBand,'1.4.3_Blue_Alpha_Applied')
        
    def Data(self):
        '''
            Process all the channel data step by step and save the following
            
            1.1-Alpha
                --1.1.1 Alpha Band CLOUD mask applied and upsampled
                --1.1.2 Alpha Normalized
                --1.1.3 Alpha Modified
            
            1.2-Red
                --1.2.1 Red Cloud mask applied
                --1.2.2 Red Normalized
                --1.2.3 Red Alpha Applied
            
            1.3-Green
                --1.3.1 Green Cloud mask applied
                --1.3.2 Green Normalized
                --1.3.3 Green Alpha Applied

            1.4-Blue
                --1.4.1 Blue Cloud mask applied
                --1.4.2 Blue Normalized
                --1.4.3 Blue Alpha Applied

        '''
        self.__ProcessAlphaChannel()
        self.__ProcessRedChannel()
        self.__ProcessGreenChannel()
        self.__ProcessBlueChannel()
        