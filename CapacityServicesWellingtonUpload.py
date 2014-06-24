#-------------------------------------------------------------
# Name:       Capacity Services Wellington Upload
# Purpose:    Updates services data for Capacity Services Wellington, packages this data up and uploads to an FTP site for download by Capacity.       
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    12/06/2014
# Last Updated:    24/06/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import csv
import string
import DatabaseReplication
import FTPUpload

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
def mainFunction(sourceGeodatabase,configFile,ftpSite,ftpFolder,ftpUsername,ftpPassword): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # Get a list of the feature datasets in the database
        arcpy.env.workspace = sourceGeodatabase
        
        # Set to copy datasets from config
        datasetsOption = "Config"
        # Set update mode to new        
        updateMode = "New"

        # Setup the destination folder as a temporary folder
        destinationFolder = os.path.join(arcpy.env.scratchFolder, "CapacityServices")
        if not os.path.exists(destinationFolder):
            os.makedirs(destinationFolder)        
        # Logging
        if (enableLogging == "true"):
            logger.info("Temporary desination folder - " + destinationFolder)                                  
        arcpy.AddMessage("Temporary desination folder - " + destinationFolder) 

        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # EXTERNAL FUNCTION - Copy over these feature datasets
        DatabaseReplication.copyDatasets(sourceGeodatabase,destinationFolder,datasetsOption,updateMode,configFile,featureDatasetList,"Feature Dataset")

        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()
        # EXTERNAL FUNCTION - Copy over these feature classes
        DatabaseReplication.copyDatasets(sourceGeodatabase,destinationFolder,datasetsOption,updateMode,configFile,featureClassList,"Feature Class")

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()
        # EXTERNAL FUNCTION - Copy over these tables
        DatabaseReplication.copyDatasets(sourceGeodatabase,destinationFolder,datasetsOption,updateMode,configFile,tableList,"Table")  

        # Join tables onto feature classes
        # Set CSV delimiter                         
        csvDelimiter = ","
        # Open the CSV file
        with open(configFile, 'rb') as csvFile:
            # Read the CSV file
            rows = csv.reader(csvFile, delimiter=csvDelimiter)
            
            # For each row in the CSV
            count = 0
            for row in rows:
                # Ignore the first line containing headers
                if (count > 0):
                    sourceDataset = row[0]
                    destinationDataset = row[1]
                    version = row[2]
                    joinTable = row[3]
                    renameFields = row[4]                    
                    removeFields = row[5]
                                
                    # Join the table to the feature class if there is a join table provided
                    if joinTable:
                        # Copy table to memory first
                        arcpy.CopyRows_management(os.path.join(sourceGeodatabase, joinTable), "in_memory\Tbl", "")

                        # If renaming fields in table
                        if renameFields:
                            renameFields = string.split(renameFields, ";")
                            # For each rename field
                            for renameField in renameFields:
                                # Get the current field name and the new field name
                                fields = string.split(renameField, ":")
                                # Logging
                                if (enableLogging == "true"):
                                    logger.info("Renaming field in " + joinTable + " from " + fields[0] + " to " + fields[1] + "...")                                  
                                arcpy.AddMessage("Renaming field in " + joinTable + " from " + fields[0] + " to " + fields[1] + "...") 

                                # Alter field name
                                arcpy.AlterField_management("in_memory\Tbl", fields[0], fields[1], fields[1])

                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Joining dataset " + joinTable + " to dataset " + destinationDataset + "...")                                 
                        arcpy.AddMessage("Joining dataset " + joinTable + " to dataset " + destinationDataset + "...")
                        
                        # Join on table to feature class
                        arcpy.JoinField_management(os.path.join(destinationFolder, destinationDataset), "Feature_ID", "in_memory\Tbl", "asset_id")

                    # Remove unecessary fields if provided
                    if removeFields:
                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Removing fields " + removeFields + " from dataset " + destinationDataset + "...")                                 
                        arcpy.AddMessage("Removing fields " + removeFields + " from dataset " + destinationDataset + "...")

                        # Remove unecessary fields
                        arcpy.DeleteField_management(os.path.join(destinationFolder, destinationDataset), removeFields)

                count = count + 1

        # EXTERNAL FUNCTION - Send data to server
        FTPUpload.mainFunction(destinationFolder,ftpSite,ftpFolder,ftpUsername,ftpPassword)

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
    
