#-------------------------------------------------------------
# Name:       MapInfo Data Import
# Purpose:    Imports all MapInfo data to a selected geodatabase. Takes a folder as input and will find all MapInfo files
#             in this folder and subfolders. Requires data interoperability extension.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    03/12/2014
# Last Updated:    03/12/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import csv

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "false" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = "" # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(mapInfoFolder,geodatabase,notIncludeConfigFile,renameConfigFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        root_len = len(os.path.abspath(str(mapInfoFolder)))     
        # For each of the directories in the folder
        for root, dirs, files in os.walk(str(mapInfoFolder)):
          archive_root = os.path.abspath(root)[root_len:]
          # For each file
          for f in files:
            # Get the file path
            fullpath = os.path.join(root, f)
            fileName = os.path.join(archive_root, f)
            # If it is a tab file
            if fullpath.endswith(".TAB"):
                arcpy.AddMessage("MapInfo TAB file found - " + fullpath + "...")
                arcpy.AddMessage("Importing dataset...")

                noGeometryTest = fullpath + "\\NoGeometry"
                runImport = True
                # Check geometry is invalid
                if arcpy.Exists(noGeometryTest):
                    arcpy.AddWarning("Geometry is invalid...")
                    runImport = False
                # If brackets in file name
                if "(" in fileName:
                    arcpy.AddWarning("Filename is invalid because of \"(\"...")
                    runImport = False
                # If brackets in file name
                if ")" in fileName:
                    arcpy.AddWarning("Filename is invalid because of \")\"...")
                    runImport = False

                # If can continue with import
                if (runImport == True):     
                    # Import MapInfo TAB file
                    arcpy.QuickImport_interop("MITAB,\"" + fullpath + "\",\"RUNTIME_MACROS,\"\"FME_TABLE_PASSWORD,,_MITAB_FULL_ENHANCED_GEOMETRY,YES,ENCODING,,EXPOSE_ATTRS_GROUP,,MITAB_EXPOSE_FORMAT_ATTRS,,USE_SEARCH_ENVELOPE,NO,SEARCH_ENVELOPE_MINX,0,SEARCH_ENVELOPE_MINY,0,SEARCH_ENVELOPE_MAXX,0,SEARCH_ENVELOPE_MAXY,0,CLIP_TO_ENVELOPE,NO,_MERGE_SCHEMAS,YES\"\",META_MACROS,\"\"SourceFME_TABLE_PASSWORD,,Source_MITAB_FULL_ENHANCED_GEOMETRY,YES,SourceENCODING,,SourceEXPOSE_ATTRS_GROUP,,SourceMITAB_EXPOSE_FORMAT_ATTRS,,SourceUSE_SEARCH_ENVELOPE,NO,SourceSEARCH_ENVELOPE_MINX,0,SourceSEARCH_ENVELOPE_MINY,0,SourceSEARCH_ENVELOPE_MAXX,0,SourceSEARCH_ENVELOPE_MAXY,0,SourceCLIP_TO_ENVELOPE,NO\"\",METAFILE,MITAB,COORDSYS,,IDLIST,,__FME_DATASET_IS_SOURCE__,true\"", os.path.join(arcpy.env.scratchFolder, "Data.gdb"))

                    arcpy.env.workspace = os.path.join(arcpy.env.scratchFolder, "Data.gdb")
                    featureClassList = arcpy.ListFeatureClasses()
                    # If data imported
                    if (featureClassList):
                        # Loop through the list of feature classes
                        count = 0
                        for featureClass in featureClassList:
                            desc = arcpy.Describe(featureClass)
                            datasetRemoved = False

                            # Get a count for the dataset
                            rowCount = arcpy.GetCount_management(featureClass)
                            if (rowCount == 0) and (datasetRemoved == False):
                                arcpy.AddWarning("Not importing dataset with no records - " + desc.name + "...")
                                arcpy.Delete_management(featureClass, "FeatureClass")
                                datasetRemoved = True

                            # Don't include datasets with "text" in name
                            if ("text" in str(desc.name)) and (datasetRemoved == False):
                                arcpy.AddWarning("Not importing text dataset - " + desc.name + "...")
                                arcpy.Delete_management(featureClass, "FeatureClass")
                                datasetRemoved = True

                            # Remove polygon from feature class name
                            if (("_polygon" in str(desc.name)) and (datasetRemoved == False)):
                                datasetName = desc.catalogPath
                                newDatasetName = datasetName.replace("_polygon", "");

                                renameDataset = True
                                # If already been renamed    
                                if arcpy.Exists(newDatasetName):
                                    renameDataset = False
                                    
                                if (renameDataset == True):                                     
                                    # Rename feature class
                                    arcpy.AddMessage("Removing polygon from feature class name...")                           
                                    arcpy.Rename_management(datasetName, newDatasetName, "FeatureClass")

                            # Remove point from feature class name
                            if (("_point" in str(desc.name)) and (datasetRemoved == False)):
                                datasetName = desc.catalogPath
                                newDatasetName = datasetName.replace("_point", "");

                                renameDataset = True
                                # If already been renamed    
                                if arcpy.Exists(newDatasetName):
                                    renameDataset = False

                                if (renameDataset == True):                                    
                                    # Rename feature class
                                    arcpy.AddMessage("Removing point from feature class name...")                           
                                    arcpy.Rename_management(datasetName, newDatasetName, "FeatureClass")
                                
                            # Remove line from feature class name
                            if (("_line" in str(desc.name)) and (datasetRemoved == False)):
                                datasetName = desc.catalogPath
                                newDatasetName = datasetName.replace("_line", "");

                                renameDataset = True
                                # If already been renamed    
                                if arcpy.Exists(newDatasetName):
                                    renameDataset = False

                                if (renameDataset == True):                                     
                                    # Rename feature class
                                    arcpy.AddMessage("Removing line from feature class name...")                           
                                    arcpy.Rename_management(datasetName, newDatasetName, "FeatureClass")
                                
                            count = count + 1                                
                        
                        # Loop through the list of feature classes
                        featureClassList = arcpy.ListFeatureClasses()
                        for featureClass in featureClassList:
                            copyDataset = True
                            desc = arcpy.Describe(featureClass)

                            # If configuration provided
                            if (notIncludeConfigFile):
                                # Set CSV delimiter                         
                                csvDelimiter = ","

                                # Look through configuration file to see if any datasets in there to not include
                                # Open the CSV file
                                with open(notIncludeConfigFile, 'rb') as csvFile:
                                    # Read the CSV file
                                    rows = csv.reader(csvFile, delimiter=csvDelimiter)

                                    # For each row in the CSV
                                    count = 0
                                    for row in rows:
                                        # Ignore the first line containing headers
                                        if (count > 0):
                                            # Get the name of the dataset to not include
                                            datasetNotInclude = row[0]

                                            # If the current feature class is in the list
                                            if ((desc.name).lower() == datasetNotInclude.lower()):
                                                arcpy.AddWarning("Not including dataset - " + desc.name + "...")
                                                copyDataset = False
                                        count = count + 1
                            
                                # Look through configuration file to see if any datasets in there to rename
                                # Open the CSV file
                                with open(renameConfigFile, 'rb') as csvFile:
                                    # Read the CSV file
                                    rows = csv.reader(csvFile, delimiter=csvDelimiter)

                                    # For each row in the CSV
                                    count = 0
                                    for row in rows:
                                        # Ignore the first line containing headers
                                        if (count > 0):
                                            # Get the name of the dataset to rename
                                            datasetRename = row[0]
                                            # Name to change dataset to
                                            datasetRenameTo = row[1]
                                            
                                            # If the current feature class is in the list
                                            if ((desc.name).lower() == datasetRename.lower()):
                                                datasetName = desc.catalogPath
                                                newDatasetName = datasetName.replace(datasetRename, datasetRenameTo);
                                                featureClass = newDatasetName
                                                arcpy.AddWarning("Renaming " + desc.name + " to " + datasetRenameTo + "...")
                                                arcpy.Rename_management(datasetName, newDatasetName, "FeatureClass")
                                                desc = arcpy.Describe(featureClass)
                                        count = count + 1
                                        
                            # If can continue with copy
                            if (copyDataset == True):                                  
                                # Copy in the dataset to the geodatabase
                                arcpy.CopyFeatures_management(featureClass, os.path.join(geodatabase, desc.name))
                    else:
                       arcpy.AddWarning("No datasets to import...")

                    # Delete database
                    arcpy.Delete_management(arcpy.env.workspace, "Workspace")                      
                
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
            # Log end of process
            logger.info("Process ended.")            
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
                errorMessage = unicode(e.args[i]).encode('utf-8')
            else:
                errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
        arcpy.AddError(errorMessage)              
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")            
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
    # Logging
    if (enableLogging == "true"):
        # Setup logging
        logger, logMessage = setLogging(logFile)
        # Log start of process
        logger.info("Process started.")            
    mainFunction(*argv)
    
