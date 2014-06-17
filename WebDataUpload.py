#-------------------------------------------------------------
# Name:       Web Data Upload
# Purpose:    Copies data to be replicated into geodatabase and zips this up.
#             Zip file is then uploaded to FTP site for loading into database.
#             NOTE: If using ArcGIS 10.0 need to set scratch workspace as a folder.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    31/05/2013
# Last Updated:    17/06/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0+
# Python Version:   2.6/2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import string
import zipfile
import uuid
import FTPUpload

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "false" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), r"Logs\WebDataUpload.log") # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(featureClasses,tables,csvFiles,csvXYFieldNames,ftpSite,ftpFolder,ftpUsername,ftpPassword,gpService): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")

        # --------------------------------------- Start of code --------------------------------------- #
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

        # If CSV files provided
        if (len(csvFiles) > 0):    
            csvList = string.split(str(csvFiles).replace("'", ""), ";")
            # Loop through of the CSVs
            for eachCSV in csvList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachCSV)
               datasetName = string.split(describeDataset.name, ".")
               # Change CSV name if starts with a digit
               if datasetName[0].isdigit():
                   datasetName[0] = "Layer" + datasetName[0]
               # Create feature layer and convert to feature class
               csvFields = string.split(str(csvXYFieldNames).replace("'", ""), ",")
               # Copy feature class into geodatabase using the same dataset name
               arcpy.MakeXYEventLayer_management(eachCSV, csvFields[0], csvFields[1], "Layer", "PROJCS['NZGD_2000_New_Zealand_Transverse_Mercator',GEOGCS['GCS_NZGD_2000',DATUM['D_NZGD_2000',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',1600000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',173.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];-4020900 1900 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision", "")
               arcpy.CopyFeatures_management("Layer", os.path.join(geodatabase, datasetName[0]), "", "0", "0", "0")
               
        # Check input datasets are provided before zipping up
        if ((len(featureClasses) > 0) or (len(tables) > 0) or (len(csvFiles) > 0)):
            arcpy.AddMessage("Zipping data...")
            # Setup the zip file
            if (arcgisVersion == "10.0"):
                zipFile = os.path.join(arcpy.env.scratchWorkspace, "WebData-" + str(uuid.uuid1()) + ".zip")               
            else:
                zipFile = os.path.join(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()) + ".zip")
            zippedFolder = zipfile.ZipFile(zipFile, "w", allowZip64=True)

            # Zip up the geodatabase
            root_len = len(os.path.abspath(str(fileFolder)))
            # For each of the directories in the folder
            for root, dirs, files in os.walk(str(fileFolder)):
              archive_root = os.path.abspath(root)[root_len:]
              # For each file
              for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(archive_root, f)
                zippedFolder.write(fullpath, archive_name)
            # Close zip file
            zippedFolder.close()
            
            # EXTERNAL FUNCTION - Send data to server
            FTPUpload.mainFunction(zipFile,ftpSite,ftpFolder,ftpUsername,ftpPassword)
        else:
            #--------------------------------------------Logging--------------------------------------------#
            arcpy.AddMessage("Process stopped: No datasets provided") 
            # Log error
            if logInfo == "true":         
                loggingFunction(logFile,"error","\nProcess stopped: No datasets provided")
            #-----------------------------------------------------------------------------------------------#

        # Call geoprocessing service to update data on server
        arcpy.AddMessage("Updating data on server...")
        arcpy.ImportToolbox(gpService, "toolbox")
        arcpy.DataUpdateFromZipSWDC_toolbox("Existing")
        
        # --------------------------------------- End of code --------------------------------------- #  
            
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                arcpy.SetParameterAsText(1, output)
        # Otherwise return the result          
        else:
            # Return the output if there is any
            if output:
                return output      
        # Logging
        if (enableLogging == "true"):
            # Log end of process
            logger.info("Process ended.")
            # Remove file handler and close log file            
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        pass
    # If arcpy error
    except arcpy.ExecuteError:           
        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)   
        arcpy.AddError(errorMessage)           
        # Logging
        if (enableLogging == "true"):
            # Log error          
            logger.error(errorMessage)                 
            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
    # If python error
    except Exception as e:
        errorMessage = ""
        # Build and show the error message
        for i in range(len(e.args)):
            if (i == 0):
                errorMessage = str(e.args[i])
            else:
                errorMessage = errorMessage + " " + str(e.args[i])
        arcpy.AddError(errorMessage)              
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)               
            # Remove file handler and close log file
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)            
# End of main function


# Start of set logging function
def setLogging(logFile):
    # Create a logger
    logger = logging.getLogger(os.path.basename(__file__))
    logger.setLevel(logging.DEBUG)
    # Setup log message handler
    logMessage = logging.FileHandler(logFile)
    # Setup the log formatting
    logFormat = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s", "%d/%m/%Y - %H:%M:%S")
    # Add formatter to log message handler
    logMessage.setFormatter(logFormat)
    # Add log message handler to logger
    logger.addHandler(logMessage) 

    return logger, logMessage               
# End of set logging function


# Start of send email function
def sendEmail(message):
    # Send an email
    arcpy.AddMessage("Sending email...")
    # Server and port information
    smtpServer = smtplib.SMTP("smtp.gmail.com",587) 
    smtpServer.ehlo()
    smtpServer.starttls() 
    smtpServer.ehlo
    # Login with sender email address and password
    smtpServer.login(emailUser, emailPassword)
    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
    body = header + '\n' + emailMessage + '\n' + '\n' + message
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, body)    
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))
    mainFunction(*argv)
