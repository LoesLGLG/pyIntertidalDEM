#!/usr/bin/env python3

#Section--Imports

from termcolor import colored          #Visualization ease

import argparse                        #Commandline agrument

from osgeo import gdal                 #GeoTiff file processing

import matplotlib.pyplot as plt        #Image/Graphical Visualization

import sys                             #System 

import numpy as np                     #Array manupulation ease

import time                            #Time profiling

import subprocess                      #For GDALinfo

#-----------------------------------------------------------------------------------------------------------------------------------------------

#Section--Structre
#Passing Arguments
parser = argparse.ArgumentParser()
parser.add_argument("unzipped_directory", help="Directory of unzipped Sentiniel2 product",type=str)
args = parser.parse_args()

#Debugger
def debug_print_value(debug_object,Debug_Identifier):
    print('')
    print(colored('DEBUG OBJECT:'+colored(Debug_Identifier,'blue'),'cyan'))
    print(colored('*********************************************************************************************','red'))
    print(colored(debug_object,'green'))
    print(colored('*********************************************************************************************','red'))
    print('')
#Banner
def print_banner():
    print('')
    print(colored('*********************************************************************************************','blue'))
    print(colored('****************************'+colored('        SENTINIEL2        ','red')+colored('***************************************','green'),'green'))
    print(colored('*********************************************************************************************','blue'))
    print('')
#-----------------------------------------------------------------------------------------------------------------------------------------------

#Section--file listing
def list_files_sentiniel(unzipped_directory):
    print_banner()
    directory_strings=str(unzipped_directory).split('/')  #split the directory to extract specific folder
    identifier_strings=directory_strings[-1].split('_')   #split the specific folder data identifiers
    date_time_stamp=identifier_strings[1].split('-')      #Time stamp data 

    #display product information
    print(colored('    Satelite Name  :','green')+ colored(identifier_strings[0],'blue'))
    print(colored('             Date  :','green')+ colored(date_time_stamp[0][6:]+'-'+date_time_stamp[0][4:6]+'-'+date_time_stamp[0][0:4],'blue'))
    print(colored('             Time  :','green')+ colored(date_time_stamp[1][0:2]+':'+date_time_stamp[1][2:4]+':'+date_time_stamp[1][4:]+':'+date_time_stamp[2]+'(ms)','blue'))
    print(colored('     Product Type  :','green')+ colored(identifier_strings[2]+colored('(See Handbook for description)','red'),'blue'))
    print(colored('Geographical Zone  :','green')+ colored(identifier_strings[3]+colored('(Zone,Tile,OrbitNumber)','red'),'blue'))
    print(colored('    Metadata Type  :','green')+ colored(identifier_strings[4]+' Version:'+identifier_strings[5][1]+colored('(See Handbook for description)','red'),'blue'))
    #------------------------------------------------------------------------------------------------------------------------
    
    #Files to take data from --Customized for now
 
    Band_file_no_1=str(unzipped_directory)+'/'+directory_strings[-1]+'_FRE_B2.tif'
    Band_file_no_2=str(unzipped_directory)+'/'+directory_strings[-1]+'_FRE_B4.tif'
    Band_file_no_3=str(unzipped_directory)+'/'+directory_strings[-1]+'_FRE_B8.tif'
    Band_file_no_4=str(unzipped_directory)+'/'+directory_strings[-1]+'_FRE_B11.tif'

    Cloud_mask_file=str(unzipped_directory)+'/MASKS/'+directory_strings[-1]+'_CLM_R1.tif'
    Cloud_mask_file_20m=str(unzipped_directory)+'/MASKS/'+directory_strings[-1]+'_CLM_R2.tif'

    list_of_file_to_read=[Band_file_no_1,Band_file_no_2,Band_file_no_3,Band_file_no_4,Cloud_mask_file,Cloud_mask_file_20m]

    print('')
    print(colored('***Files to be used for processing***','cyan'))

    print('')
    for file_to_read in list_of_file_to_read:
        print(colored(file_to_read,'green'))
        print('')
    
    return list_of_file_to_read 
#-----------------------------------------------------------------------------------------------------------------------------------------------
  
#Section--Processing 
      
def Decimals_with_end_Bit_detection(max_value):
    result=[]

    for i in range(0,max_value+1):
        bin_str=format(i,'08b')
        if(bin_str[-1]=='1'):
            result.append(i)
    return result



def CLOUD_MASK_CORRECTION(Cloud_mask_data,Band_data,Data_Identifier):
    start_time = time.time()
    #process 
        #detect max value of array(<=255)
        #get vaules whose binary ends with 1
    print('')
    print(colored('processing cloud mask with:'+colored(Data_Identifier,'blue'),'green'))

    value_decimals=Decimals_with_end_Bit_detection(np.amax(Cloud_mask_data))

    for v in range(0,len(value_decimals)):
        Band_data[Cloud_mask_data==value_decimals[v]]=255

    print(colored("Elapsed Time: %s seconds " % (time.time() - start_time),'yellow'))
    
    return Band_data


  
#extracting band data 
def file_data_validation(given_file):
    start_time = time.time()
    
    print('')
    print(colored('Validating data File:'+colored(given_file,'blue'),'red'))

    data_array=None
    
    try:
        data_set=gdal.Open(given_file,gdal.GA_ReadOnly)   #taking readonly data
    
    except RuntimeError as e_Read:                       #Error handling
        print(colored('Error while opening file!','red'))
        print(colored('Error Details:','blue'))
        print(e_Read)
        sys.exit(1)
    
    #Mostly single band files are needed for construction 
    if(data_set.RasterCount==1):                          
        try:
            raster_band_data=data_set.GetRasterBand(1)
            data_array=raster_band_data.ReadAsArray()
            #debug_print_value(data_array,'data_array')
        except RuntimeError as e_arr:                      #Error handling
            print(colored('Error while data extraction file!','red'))
            print(colored('Error Details:','blue'))
            print(e_arr)
            sys.exit(1)
    else:
        print('The file contains multiple bands','red')
        sys.exit(1)
    
    
    #Mannual cleanup
    data_set=None
    raster_band_data=None
    
    print(colored('Data Validation Done!','cyan'))
    
    print(colored("Elapsed Time: %s seconds " % (time.time() - start_time),'yellow'))
    
    return data_array
#-----------------------------------------------------------------------------------------------------------------------------------------------


#Section--Plotting
def Plot_with_Geo_ref(data_array,Data_Identifier):
    
    start_time = time.time()
    
    print(colored('plotting data:'+Data_Identifier,'blue'))
    
    plt.figure(Data_Identifier)
    
    plt.imshow(data_array,cmap=plt.get_cmap('gray'))
    
    plt.title(Data_Identifier)
    
    plt.grid(True)
    
    print(colored("Elapsed Time: "+Data_Identifier+ " %s seconds " % (time.time() - start_time),'yellow'))


#-----------------------------------------------------------------------------------------------------------------------------------------------


#____MAIN_____
def main():

    gdal.UseExceptions()                                     #Throw any exception while processing with GDAL  
    
    start_time = time.time()

    data_files=list_files_sentiniel(args.unzipped_directory) #Getting proper file paths
    
    band_files=data_files[0:4]                               #B2,B4,B8
    
    mask_files=data_files[4:]                                #Cloud,Cloud_20m
    
    
    
    #File data extraction
    #B2
    B2_band_data=file_data_validation(band_files[0])
    
    #B4
    B4_band_data=file_data_validation(band_files[1])
    
    #B8
    B8_band_data=file_data_validation(band_files[2])
    
    #B11
    B11_band_data=file_data_validation(band_files[3])
    
    #CLM
    Cloud_mask_data=file_data_validation(mask_files[0])
    
    #CLM_R2
    Cloud_mask_data_20m=file_data_validation(mask_files[1])
    
    
    #No data correction(-10000(REFLECTANCE_QUANTIFICATION_VALUE) value removal)
    B2_band_data[B2_band_data== -10000]=255

    B4_band_data[B4_band_data== -10000]=255

    B8_band_data[B8_band_data== -10000]=255
    
    B11_band_data[B11_band_data== -10000]=255
    
    #cloud masking correction(bit 1)
   
    B2_band_data=CLOUD_MASK_CORRECTION(Cloud_mask_data,B2_band_data,'Edge_corrected_B2')
    
    B4_band_data=CLOUD_MASK_CORRECTION(Cloud_mask_data,B4_band_data,'Edge_corrected_B4')
    
    B8_band_data=CLOUD_MASK_CORRECTION(Cloud_mask_data,B8_band_data,'Edge_corrected_B8')
    
    #B11 with 20m CLM
    B11_band_data=CLOUD_MASK_CORRECTION(Cloud_mask_data_20m,B11_band_data,'Edge_corrected_B11')

    # Repeating rows and coloumns to increase data points(discuss)
    B11_interpolated=np.array(B11_band_data.repeat(2,axis=0).repeat(2,axis=1))
    
    print('')
    print(colored("Total Elapsed Time: %s seconds " % (time.time() - start_time),'green'))
    
    #Plot_with_Geo_ref(B2_band_data,'Band2 Band')
    #Plot_with_Geo_ref(B4_band_data,'Band4 Band')
    #Plot_with_Geo_ref(B8_band_data,'Band8 Band')
    Plot_with_Geo_ref(B11_band_data,'Band11')
    Plot_with_Geo_ref(B11_interpolated,'Band11_interpolated')
    
    plt.show()
        
    
main()

