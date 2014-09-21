#-------------------------------------------------------------
# Name:       Data Update From Zip
# Purpose:    Updates data in a geodatabase from a zip file containing a geodatabase. Will get latest
#             zip file from update folder. Two update options:
#             Existing Mode - Will only update datasets that have the same name and will delete and
#             append records, so field names need to be the same. If dataset doesn't exist will copy it
#             over.
#             New Mode - Copies all datasets from the geodatabase and loads into geodatabase. Requires
#             no locks on geodatabase.
#             NOTE: If using ArcGIS 10.0 need to set scratch workspace as folder.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    31/05/2013
# Last Updated:    14/07/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0+
# Python Version:   2.6/2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import zipfile
import uuid
import glob
import arcpy

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
def mainFunction(updateFolder,updateMode,geodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
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

        # Get the newest zip file from the update folder
        latestFile = max(glob.iglob(updateFolder + r"\*.zip"), key=os.path.getmtime)

        # Setup scratch folder differently depending on ArcGIS version
        if (arcgisVersion == "10.0"):     
            # Setup geodatabase to load data into in temporary workspace
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchWorkspace, "WebData-" + str(uuid.uuid1()))
        else:        
            # Setup geodatabase to load data into in temporary workspace
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()))

        arcpy.AddMessage("Extracting zip file...")             
        # Extract the zip file to a temporary location
        zip = zipfile.ZipFile(latestFile, mode="r")
        zip.extractall(str(tempFolder))

        # Assign the geodatbase workspace and load in the datasets to the lists
        arcpy.env.workspace = os.path.join(str(tempFolder), "Data.gdb")
        featureclassList = arcpy.ListFeatureClasses()
        tableList = arcpy.ListTables()       

        arcpy.AddMessage("Copying datasets...")        
        # Load the feature classes into the geodatabase if at least one is in the geodatabase provided
        if (len(featureclassList) > 0):        
            # Loop through the feature classes
            for eachFeatureclass in featureclassList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachFeatureclass)
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):
                   # Logging
                   arcpy.AddMessage("Copying over feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                   if (enableLogging == "true"):
                      logger.info("Copying over feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                            
                   # Copy feature class into geodatabase using the same dataset name
                   arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                        # Logging
                        arcpy.AddMessage("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                        if (enableLogging == "true"):
                           logger.info("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
         
                        arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddWarning("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                        # Logging
                        if (enableLogging == "true"):
                            logger.warning(os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                            
                        # Copy feature class into geodatabase using the same dataset name
                        arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
                       
        if (len(tableList) > 0):    
            # Loop through of the tables
            for eachTable in tableList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachTable)
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):
                   # Logging
                   arcpy.AddMessage("Copying over table - " + os.path.join(geodatabase, eachTable) + "...")
                   if (enableLogging == "true"):
                      logger.info("Copying over table - " + os.path.join(geodatabase, eachTable) + "...")
                      
                   # Copy table into geodatabase using the same dataset name
                   arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachTable)):
                        # Logging
                        arcpy.AddMessage("Updating table - " + os.path.join(geodatabase, eachTable) + "...")
                        if (enableLogging == "true"):
                           logger.info("Updating table - " + os.path.join(geodatabase, eachTable) + "...")

                        arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachTable))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachTable), os.path.join(geodatabase, eachTable), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddWarning("Warning: " + os.path.join(geodatabase, eachTable) + " does not exist. Copying over...")
                        # Logging
                        if (enableLogging == "true"):
                            logger.warning(os.path.join(geodatabase, eachTable) + " does not exist. Copying over...")

                        # Copy table into geodatabase using the same dataset name
                        arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")
                   
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
    