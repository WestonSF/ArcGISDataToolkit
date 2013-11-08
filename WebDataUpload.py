#-------------------------------------------------------------
# Name:       Web Data Upload
# Purpose:    Copies data to be replicated into geodatabase and zips this up.
#             Zip file is then uploaded to FTP site for loading into database.
#             NOTE: If using ArcGIS 10.0 need to set scratch workspace as a folder.
# Author:     Shaun Weston (shaun.weston@splicegroup.co.nz)
# Created:    31/05/2013
# Copyright:   (c) Splice Group
# ArcGIS Version:   10.0+
# Python Version:   2.6/2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import datetime
import string
import zipfile
import uuid
import ftplib
import arcpy
arcpy.env.overwriteOutput = True
  
def gotoFunction(logFile,featureClasses,tables,ftpSite,ftpFolder,ftpUsername,ftpPassword,gpService): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        #--------------------------------------------Logging--------------------------------------------#        
        #Set the start time
        setdateStart = datetime.datetime.now()
        datetimeStart = setdateStart.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set start time
        with open(logFile, "a") as f:
            f.write("---" + "\n" + "Web data upload process started at " + datetimeStart)
        #-----------------------------------------------------------------------------------------------#
            
        # Get the arcgis version
        arcgisVersion = arcpy.GetInstallInfo()['Version']
        # Setup scratch folder differently depending on ArcGIS version
        if (arcgisVersion == "10.0"):     
            # Setup geodatabase to load data into in temporary workspace
            arcpy.env.scratchWorkspace = r"F:\Temp"
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchWorkspace, "WebData-" + str(uuid.uuid1()))
        else:
            # Setup geodatabase to load data into in temporary workspace
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()))
        arcpy.CreateFileGDB_management(tempFolder, "Data", "CURRENT")
        geodatabase = os.path.join(str(tempFolder), "Data.gdb")

        arcpy.AddMessage("Copying datasets...")        
        # Load the feature classes and tables into a list if input values provided
        if (len(featureClasses) > 0):
            # Remove out apostrophes
            featureclassList = string.split(str(featureClasses).replace("'", ""), ";")
            # Loop through the feature classes
            for eachFeatureclass in featureclassList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachFeatureclass)
               # Copy feature class into geodatabase using the same dataset name
               arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
                
        if (len(tables) > 0):    
            tableList = string.split(str(tables).replace("'", ""), ";")
            # Loop through of the tables
            for eachTable in tableList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachTable)
               # Copy feature class into geodatabase using the same dataset name
               arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")

        # Check input datasets are provided before zipping up
        if ((len(featureClasses) > 0) or (len(tables) > 0)):
            arcpy.AddMessage("Zipping data...")
            # Setup the zip file
            if (arcgisVersion == "10.0"):
                zipFile = os.path.join(arcpy.env.scratchWorkspace, "WebData-" + str(uuid.uuid1()) + ".zip")               
            else:
                zipFile = os.path.join(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()) + ".zip")
            zippedFolder = zipfile.ZipFile(zipFile, "w")

            # Zip up the geodatabase
            root_len = len(os.path.abspath(str(tempFolder)))
            for root, dirs, files in os.walk(str(tempFolder)):
              archive_root = os.path.abspath(root)[root_len:]
              for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(archive_root, f)
                zippedFolder.write(fullpath, archive_name)
            zippedFolder.close()

            arcpy.AddMessage("Sending data to server...")            
            # Setup connection to FTP site
            ftpSession = ftplib.FTP(ftpSite,ftpUsername,ftpPassword)        
            # File to send to FTP site
            sendZipFile = open(zipFile,'rb')
            # Send the file to the FTP site
            # If putting into ftp folder, add folder to string
            if (ftpFolder):
                ftpSession.storbinary("STOR " + ftpFolder + "//" + "WebData-" + str(uuid.uuid1()) + ".zip", sendZipFile)
            else:
                ftpSession.storbinary("STOR " + "WebData-" + str(uuid.uuid1()) + ".zip", sendZipFile)
            # Close the file and the FTP session
            sendZipFile.close()
            ftpSession.quit()
        else:
            #--------------------------------------------Logging--------------------------------------------#
            arcpy.AddMessage("Process stopped: No datasets provided") 
            # Open log file to set warning
            with open(logFile, "a") as f:
                 f.write("\nProcess stopped: No datasets provided")
            #-----------------------------------------------------------------------------------------------#

        # Call geoprocessing service to update data on server
        arcpy.AddMessage("Updating data on server...")
        arcpy.ImportToolbox(gpService, "toolbox")
        arcpy.DataUpdateFromZip_toolbox("Existing")      

        #--------------------------------------------Logging--------------------------------------------#           
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Web data upload process ended at " + datetimeEnd + "\n")
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------#                
        pass
    # If arcpy error    
    except arcpy.ExecuteError:
        #--------------------------------------------Logging--------------------------------------------#            
        arcpy.AddMessage(arcpy.GetMessages(2))    
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Web data upload process ended at " + datetimeEnd + "\n")
            f.write("There was an error: " + arcpy.GetMessages(2) + "\n")        
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------#
    # If python error
    except Exception as e:
        #--------------------------------------------Logging--------------------------------------------#           
        arcpy.AddMessage(e.args[0])           
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Web data upload process ended at " + datetimeEnd + "\n")
            f.write("There was an error: " + e.args[0] + "\n")        
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------# 
# End of function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))
    gotoFunction(*argv)
    
