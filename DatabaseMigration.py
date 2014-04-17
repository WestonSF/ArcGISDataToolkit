#-------------------------------------------------------------
# Name:       Database Migration
# Purpose:    Copies data from one geodatabase to another using a XML file to map dataset names.       
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    10/04/2014
# Last Updated:    17/04/2014
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
import xml.etree.ElementTree as ET

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
def mainFunction(sourceGeodatabase,destinationGeodatabase,datasetsOption,configFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # If config file
        configRoot = ""
        if configFile:
            # Convert config file to xml
            configFileXML = ET.parse(configFile)    
            # Import and reference the configuration file
            configRoot = configFileXML.getroot()
        
        # Get a list of the feature datasets in the database
        arcpy.env.workspace = sourceGeodatabase
        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # FUNCTION - Copy over these feature datasets
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,configRoot,featureDatasetList,"Feature Dataset")
        
        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()
        # FUNCTION - Copy over these feature classes
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,configRoot,featureClassList,"Feature Class")

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()
        # FUNCTION - Copy over these tables
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,configRoot,tableList,"Table")            

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


# Copy datasets function
def copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,configRoot,datasetList,dataType):
    # Loop through the datasets
    for dataset in datasetList:
        # Dataset in config variable 
        datasetInConfig = "false"
        versionDataset = "false"        

        # Setup the source and destination paths
        sourceDatasetPath = os.path.join(sourceGeodatabase, dataset)
        destinationDatasetPath = os.path.join(destinationGeodatabase, dataset)
        
        # If configuration provided
        if (configRoot):
            # Look through configuration file to see if source dataset is in there
            for child in configRoot.find("datasets"):
                # If dataset is in config file
                if (dataset == child.find("source").text):
                    datasetInConfig = "true"
                    # Change the destination path
                    destinationDatasetPath = os.path.join(destinationGeodatabase, child.find("destination").text)
                    arcpy.AddMessage("Changing dataset name from " + sourceDatasetPath + " to " + destinationDatasetPath + "...")

                    # If versioning the dataset
                    if (child.find("version").text == "yes"):
                        versionDataset = "true"
                        
        # If feature datasets
        if (dataType == "Feature Dataset"):
            # Get a list of the feature classes in the feature dataset
            featureClassList = arcpy.ListFeatureClasses("","",dataset)

            # Change dataset name to be just name (remove user and schema if SDE database) - Needs to go after ListFeatureClasses in 9.3 Database
            splitDataset = dataset.split('.')
            dataset = splitDataset[-1]

            # Store current dataset
            currentDataset = dataset
            
            # Loop through the feature classes in the feature dataset
            for featureClass in featureClassList:
                # Dataset in config variable 
                datasetInConfig = "false"

                # Change feature class name to be just name (remove user and schema if SDE database)
                splitDataset = featureClass.split('.')
                featureClass = splitDataset[-1]
                
                # Setup the source and destination paths                
                sourceDatasetPath = os.path.join(sourceGeodatabase + "\\" + dataset, featureClass)
                
                destinationDatasetPath = os.path.join(destinationGeodatabase + "\\" + dataset, featureClass)
                
                # If configuration provided
                needFeatureDataset = "true"
                if (configRoot):
                    # Look through configuration file to see if source dataset is in there
                    for child in configRoot.find("datasets"):                         
                        # If dataset is in config file
                        if ((dataset + "\\" + featureClass) == child.find("source").text):                        
                            datasetInConfig = "true"                            
                            # Change the destination path
                            destinationDatasetPath = os.path.join(destinationGeodatabase, child.find("destination").text)
                            arcpy.AddMessage("Changing dataset name from " + sourceDatasetPath + " to " + destinationDatasetPath + "...")

                            # Change the destination feature dataset name
                            splitDataset = child.find("destination").text.split('\\')
                            # If split has occured, dataset is necessary in destination database
                            if (len(splitDataset) > 1):
                                dataset = splitDataset[0]
                            else:
                                needFeatureDataset = "false"
                                
                            # If versioning the dataset
                            if (child.find("version").text == "yes"):
                                versionDataset = "true"
                                
                        
                # If feature dataset already exists in destination database
                if arcpy.Exists(os.path.join(destinationGeodatabase, dataset)):
                    # Copy over dataset if necessary                    
                    if ((datasetsOption == "All") or (datasetInConfig == "true")):
                        # Don't include _H or VW
                        if ("_H" not in featureClass) and ("VW" not in featureClass) and ("vw" not in featureClass):                          
                            # If feature class already exists in destination database
                            if arcpy.Exists(destinationDatasetPath):
                                # Delete the dataset first
                                arcpy.Delete_management(destinationDatasetPath, "FeatureClass")
                            # Copy over feature class
                            arcpy.AddMessage("Copying over feature class - " + destinationDatasetPath + "...")                              
                            arcpy.CopyFeatures_management(sourceDatasetPath, destinationDatasetPath, "", "0", "0", "0")
                            if (versionDataset == "true"):
                                # If dataset is not versioned already
                                datasetVersioned = arcpy.Describe(os.path.join(destinationGeodatabase, dataset)).isVersioned
                                if (datasetVersioned == 0):
                                    arcpy.AddMessage("Versioning dataset - " + os.path.join(destinationGeodatabase, dataset) + "...")
                                    arcpy.RegisterAsVersioned_management(os.path.join(destinationGeodatabase, dataset), "NO_EDITS_TO_BASE")
                    
                # Otherwise create the feature dataset first
                else:
                    # Copy over dataset if necessary                    
                    if ((datasetsOption == "All") or (datasetInConfig == "true")):
                        # Don't include _H or VW
                        if ("_H" not in featureClass) and ("VW" not in featureClass) and ("vw" not in featureClass):     
                            # If split has occured, dataset is necessary in destination database
                            if (needFeatureDataset == "true"):                        
                                arcpy.CreateFeatureDataset_management(destinationGeodatabase, dataset, sourceDatasetPath)                       
                            # Copy over feature class
                            arcpy.AddMessage("Copying over feature class - " + destinationDatasetPath + "...")                        
                            arcpy.CopyFeatures_management(sourceDatasetPath, destinationDatasetPath, "", "0", "0", "0")
                            if (versionDataset == "true"):
                                # If dataset is not versioned already
                                datasetVersioned = arcpy.Describe(os.path.join(destinationGeodatabase, dataset)).isVersioned
                                if (datasetVersioned == 0):                                
                                    arcpy.AddMessage("Versioning dataset - " + os.path.join(destinationGeodatabase, dataset) + "...")
                                    arcpy.RegisterAsVersioned_management(os.path.join(destinationGeodatabase, dataset), "NO_EDITS_TO_BASE")
                    
                # Change dataset name back to current dataset
                dataset = currentDataset
                versionDataset = "false"
                
        # If feature classes
        elif (dataType == "Feature Class"):
            # Change dataset name to be just name (remove user and schema if SDE database) - Needs to go after ListFeatureClasses in 9.3 Database
            splitDataset = dataset.split('.')
            dataset = splitDataset[-1]
            
            # Copy over dataset if necessary                    
            if ((datasetsOption == "All") or (datasetInConfig == "true")):               
                # Copy over feature class - Not _H or VW
                if ("_H" not in dataset) and ("VW" not in dataset) and ("vw" not in dataset):                  
                    arcpy.AddMessage("Copying over feature class - " + destinationDatasetPath + "...")                      
                    arcpy.CopyFeatures_management(sourceDatasetPath, destinationDatasetPath, "", "0", "0", "0")
                    if (versionDataset == "true"):
                        # If dataset is not versioned already
                        datasetVersioned = arcpy.Describe(os.path.join(destinationDatasetPath, dataset)).isVersioned
                        if (datasetVersioned == 0):                         
                            arcpy.AddMessage("Versioning dataset - " + destinationDatasetPath + "...")
                            arcpy.RegisterAsVersioned_management(destinationDatasetPath, "NO_EDITS_TO_BASE")
                            
        # If tables
        elif (dataType == "Table"):
            # Change dataset name to be just name (remove user and schema if SDE database) - Needs to go after ListFeatureClasses in 9.3 Database
            splitDataset = dataset.split('.')
            dataset = splitDataset[-1]
            
            # Copy over dataset if necessary                    
            if ((datasetsOption == "All") or (datasetInConfig == "true")):               
                # Copy over table - Not _H or VW
                if ("_H" not in dataset) and ("VW" not in dataset) and ("vw" not in dataset):  
                    arcpy.AddMessage("Copying over table - " + destinationDatasetPath + "...")                      
                    arcpy.CopyRows_management(sourceDatasetPath, destinationDatasetPath, "")
                    if (versionDataset == "true"):
                        # If dataset is not versioned already
                        datasetVersioned = arcpy.Describe(os.path.join(destinationDatasetPath, dataset)).isVersioned
                        if (datasetVersioned == 0):                          
                            arcpy.AddMessage("Versioning dataset - " + destinationDatasetPath + "...")
                            arcpy.RegisterAsVersioned_management(destinationDatasetPath, "NO_EDITS_TO_BASE")
                    
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
    
