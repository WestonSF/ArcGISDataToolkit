#-------------------------------------------------------------
# Name:       Export Metadata
# Purpose:    Exports all metadata in a geodatabase out to a text file.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    30/06/2014
# Last Updated:    30/06/2014
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
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
import uuid

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
def mainFunction(geodatabase,outputFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #
        
        # Set the workspace 
        arcpy.env.workspace = geodatabase

        # Set the directory for the translator
        installDirectory = arcpy.GetInstallInfo("desktop")["InstallDir"]
        # Use the FGDC to get into clean xml format
        translator = installDirectory + "Metadata/Translator/ARCGIS2FGDC.xml"

        # Get a list of the feature datasets in the database
        featureDatasetList = arcpy.ListDatasets("", "Feature")

        # Loop through the feature datasets
        datasetList = []
        for featureDataset in featureDatasetList:
            # Get a list of the feature classes in the feature dataset and add to list
            datasetList = arcpy.ListFeatureClasses("","",featureDataset)
         
        # Get a list of the feature classes and add to list
        datasetList = datasetList + arcpy.ListFeatureClasses()

         # Get a list of the tables and add to list
        datasetList = datasetList + arcpy.ListTables()      

        # Go through the datasets in the list
        for dataset in datasetList:  
            arcpy.AddMessage("Exporting metadata for " + dataset + "...")
            # Logging
            if (enableLogging == "true"):
                logger.info("Exporting metadata for " + dataset + "...")

            # Export the metadata for the dataset
            arcpy.ExportMetadata_conversion(dataset, translator, os.path.join(arcpy.env.scratchFolder, "Metadata.xml"))

            # Convert file to xml
            tree = ET.ElementTree(file=os.path.join(arcpy.env.scratchFolder, "Metadata.xml"))   
            # Import and reference the xml file
            root = tree.getroot()

            # Set default values
            abstract = "No Abstract"
            purpose = "No Purpose"
            # Look at the metadata
            description = root.find("idinfo/descript")
            # If there are description values
            if description:
                # Look at the description xml element
                for child in root.find("idinfo/descript"):
                    # Get abstract
                    if (child.tag.lower() == "abstract"):
                        abstract = child.text
                    # Get purpose
                    if (child.tag.lower() == "purpose"):
                        purpose = child.text                

            # If any variables are none
            if (abstract is None):
                abstract = "No Abstract"
            if (purpose is None):
                purpose = "No Purpose"
                
            # Write to text file
            with open(outputFile, "a") as f:
                f.write("Dataset - " + str(dataset) + "\n")
                f.write("Abstract - " + str(abstract) + "\n")
                f.write("Purpose - " + str(purpose) + "\n")
                f.write("--------------------" + "\n")
                f.close()
                
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
    
