#-------------------------------------------------------------
# Name:       Summit Forests Data Clean
# Purpose:    Cleans the Summit Forests GIS data by merging datasets and fixing up any issues.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    12/01/2015
# Last Updated:    12/01/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.3+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import string

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
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

# Start of main function
def mainFunction(datasets,inputGeodatabase,outputGeodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Get the list of datasets
        datasetsList = string.split(datasets, ";")

        # For each of the datasets in the list
        for dataset in datasetsList:
            # Get dataset name and type
            datasetType = string.split(dataset, ":")

            # Get a list of the feature classes in the database
            arcpy.env.workspace = inputGeodatabase
            featureClassList = arcpy.ListFeatureClasses()
            datasetMergeList = []
            # Go through each of the datasets in the database
            for featureClass in featureClassList:
                # If feature class is present matching the name
                if (datasetType[0].lower() in featureClass.lower()):
                    # Check dataset type
                    desc = arcpy.Describe(featureClass)
                    shapeType = desc.shapeType
                    if (shapeType.lower() == (datasetType[1].lower())):
                        # Add in the forest and tenure info
                        forestName = string.split(desc.name, "_")
                        descWorkspace = arcpy.Describe(inputGeodatabase)

                        addForest = 0
                        addTenure = 0
                        # Check if field is already present
                        fieldList = arcpy.ListFields(featureClass)
                        for field in fieldList:   
                            if (field.name == "Forest"):
                                addForest += 1
                            if (field.name == "Tenure"):
                                addTenure += 1

                        if (addForest == 0):
                            arcpy.AddField_management(featureClass, "Forest", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")                            
                        if (addTenure == 0):                            
                            arcpy.AddField_management(featureClass, "Tenure", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                            
                        arcpy.CalculateField_management(featureClass, "Forest", "\"" + forestName[0] + "\"", "PYTHON_9.3", "")
                        arcpy.CalculateField_management(featureClass, "Tenure", "\"" + descWorkspace.baseName + "\"", "PYTHON_9.3", "")

                        # Add to merge list 
                        datasetMergeList.append(featureClass)

            # If dataset to be merged
            if (len(datasetMergeList) > 0):
                arcpy.AddMessage("Merging and creating " + datasetType[0] + " dataset...")
                arcpy.Merge_management(datasetMergeList, os.path.join(outputGeodatabase, datasetType[0]), "")
            else:
                arcpy.AddWarning("No data for " + datasetType[0] + " dataset...")                


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
    # Setup the use of a proxy for requests
    if (enableProxy == "true"):
        # Setup the proxy
        proxy = urllib2.ProxyHandler({requestProtocol : proxyURL})
        openURL = urllib2.build_opener(proxy)
        # Install the proxy
        urllib2.install_opener(openURL)
    mainFunction(*argv)
    
