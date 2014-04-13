#-------------------------------------------------------------
# Name:       Database Contents To CSV
# Purpose:    Exports out the names of datasets in a geodatabase to a CSV file.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    11/04/2014
# Last Updated:    13/04/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0/10.1/10.2
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
def mainFunction(geodatabase,csvFile,csvDelimiter): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # Create a CSV file and setup header
        file = open(csvFile, 'wb')
        # Setup writer
        if csvDelimiter == "|":
            writer = csv.writer(file, delimiter="|")                            
        if csvDelimiter == ";":
            writer = csv.writer(file, delimiter=";")                            
        if csvDelimiter == ",":
            writer = csv.writer(file, delimiter=",")
    
        # Add in header information   
        headerRow = []                               
        headerRow.append("Dataset")
        writer.writerow(headerRow)
                  
        # Get a list of the feature datasets in the database
        arcpy.env.workspace = geodatabase
        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # FUNCTION - Get a list of the feature datasets
        getDatasets(geodatabase,file,csvDelimiter,featureDatasetList,"Feature Dataset")
        
        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()
        # FUNCTION - Get a list of the feature classes
        getDatasets(geodatabase,file,csvDelimiter,featureClassList,"Feature Class")

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()
        # FUNCTION - Get a list of the tables
        getDatasets(geodatabase,file,csvDelimiter,tableList,"Table")
                

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


# List datasets function
def getDatasets(geodatabase,csvFile,csvDelimiter,datasetList,dataType):
    # Setup writer
    if csvDelimiter == "|":
        writer = csv.writer(csvFile, delimiter="|")                            
    if csvDelimiter == ";":
        writer = csv.writer(csvFile, delimiter=";")                            
    if csvDelimiter == ",":
        writer = csv.writer(csvFile, delimiter=",")

    # Loop through the datasets
    for dataset in datasetList:
        # Change dataset name to be just name (remove user and schema if SDE database)
        splitDataset = dataset.split('.')
        dataset = splitDataset[-1]

        # If feature datasets
        if (dataType == "Feature Dataset"):
            # Get a list of the feature classes in the feature dataset
            featureClassList = arcpy.ListFeatureClasses("","",dataset)
            
            # Loop through the feature classes in the feature dataset
            for featureClass in featureClassList:
                # Change feature dataset name to be just name (remove user and schema if SDE database)
                splitDataset = featureClass.split('.')
                featureClass = splitDataset[-1]

                # Write the name of the feature class to the CSV
                row = []                               
                row.append(dataset + "\\" + featureClass)
                writer.writerow(row)
                arcpy.AddMessage("Feature class added to list - " + dataset + "\\" + featureClass + "...")                      

        # If feature classes
        elif (dataType == "Feature Class"):
                # Write the name of the feature class to the CSV 
                row = []                               
                row.append(dataset)
                writer.writerow(row)            
                arcpy.AddMessage("Feature class added to list - " + dataset + "...")                      

        # If tables
        elif (dataType == "Table"):
                # Write the name of the table to the CSV  
                row = []                               
                row.append(dataset)
                writer.writerow(row)            
                arcpy.AddMessage("Table added to list - " + dataset + "...")                      

                
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