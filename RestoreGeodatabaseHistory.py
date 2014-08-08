#-------------------------------------------------------------
# Name:       Restore Geodatabase History
# Purpose:    Re-attachs an orphaned history dataset to its base dataset, by re-enabling archiving and
#             loading in the orphaned archived dataset records in a SQL Server database.      
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    06/08/2014
# Last Updated:    08/08/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.2+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
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
def mainFunction(geodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #
        
        # Get a list of the feature datasets in the database
        arcpy.env.workspace = geodatabase
        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # Loop through the datasets
        datasetList = []
        for dataset in featureDatasetList:   
            datasetList = datasetList + arcpy.ListFeatureClasses("","",dataset)
            
        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()

        # Get the full list of datasets in the database
        fullDatasetList = featureClassList + tableList

        # Connect directly to SQL server
        sqlConnection = arcpy.ArcSDESQLExecute(geodatabase)

        # Compress the database        
        arcpy.Compress_management(geodatabase)
        
        # Loop through the list of datasets
        for dataset in fullDatasetList:
            # If dataset is an orphaned dataset - "_H" suffix
            if (dataset[-2:].upper() == "_H"):
                # Logging
                if (enableLogging == "true"):
                    logger.info("Orphaned archive dataset found - " + dataset + "...")
                arcpy.AddMessage("Orphaned archive dataset found - " + dataset + "...")

                baseDataset = dataset[:-2]

                # If the base dataset exists for the orphaned archive
                if arcpy.Exists(baseDataset):
                    # Create a copy of the base dataset
                    arcpy.CopyFeatures_management(baseDataset, baseDataset + "_Current")
                    
                    # Delete all records in the base dataset                    
                    arcpy.DeleteFeatures_management(baseDataset)
                    
                    # If archive rename already exists
                    if arcpy.Exists(baseDataset + "_Archive"):
                        # Delete the archive rename
                        arcpy.Delete_management(baseDataset + "_Archive")
    
                    # Rename the archive dataset
                    arcpy.Rename_management(dataset, baseDataset + "_Archive", "Feature Class")

                    # Load all records from archive dataset into the base dataset
                    arcpy.Append_management(baseDataset + "_Archive", baseDataset, "NO_TEST","","")
                    
                    # Describe the properties of the dataset to see if archiving is enabled
                    desc = arcpy.Describe(baseDataset)
                    isArchived = desc.IsArchived

                    # Enable Archiving if it is not already enabled
                    if isArchived == False:
                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Enabling archiving - " + baseDataset + "...")
                        arcpy.AddMessage("Enabling archiving - " + baseDataset + "...")
                        
                        # Enable archiving
                        arcpy.EnableArchiving_management(baseDataset)

                        # Delete all records in the base dataset                    
                        arcpy.DeleteFeatures_management(baseDataset)

                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Loading in orphaned archive dataset records - " + dataset + "...")
                        arcpy.AddMessage("Loading in orphaned archive dataset records - " + dataset + "...")
                    
                        # Update the dates in the new archive dataset from the old archive dataset
                        sqlQuery = "UPDATE " + baseDataset + " SET " + dataset ".GDB_FROM_DATE = " + dataset + ".GDB_FROM_DATE, " + baseDataset + "_Archive" + ".GDB_TO_DATE = " + dataset + ".GDB_TO_DATE FROM " + baseDataset + "_Archive" + " INNER JOIN " + dataset + " ON " + dataset + ".GDB_ARCHIVE_OID = " + baseDataset + "_Archive" + ".OBJECTID"
                        sqlResult = sqlConnection.execute(sqlQuery)

                        # Update the current dates in the new archive dataset to a year of "8888"
                        sqlQuery = "UPDATE " + baseDataset + " SET GDB_TO_DATE = convert(datetime, '8888-12-31 00:00:00',20) WHERE GDB_TO_DATE = convert(datetime, '9999-12-31 00:00:00',20)"
                        sqlResult = sqlConnection.execute(sqlQuery)

                        # Load all records from current base dataset into the base dataset
                        arcpy.Append_management(baseDataset + "_Current", baseDataset, "NO_TEST","","")
                    
                       
                        
                    elif isArchived == False:
                        # Logging
                        if (enableLogging == "true"):
                            logger.warning("Archiving is already enabled - " + baseDataset + "...")
                        arcpy.AddWarning("Archiving is already enabled - " + baseDataset + "...")                 
        # --------------------------------------- End of code --------------------------------------- #  
                else:
                    # Logging
                    if (enableLogging == "true"):
                        logger.warning("No base dataset found - " + baseDataset + "...")
                    arcpy.AddWarning("No base dataset found - " + baseDataset + "...")
                    
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
                errorMessage = unicode(e.args[i]).encode('utf-8')
            else:
                errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
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
    
