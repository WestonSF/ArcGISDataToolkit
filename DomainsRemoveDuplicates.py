#-------------------------------------------------------------
# Name:       Remove Duplicate Domains
# Purpose:    Gets a list of used domains in the database then removes those not being used. Also looks at configuration
#             file to find duplicate domains, then re-assigns a domain and removes the unused duplicate domain.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/04/2014
# Last Updated:    30/04/2014
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
def mainFunction(geodatabase,configFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #
            
        # Get a list of assigned domains
        assignedDomains = []
        
        # Get a list of the feature datasets in the database
        arcpy.env.workspace = geodatabase
        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # FUNCTION - Get the domains for these feature datasets
        assignedDomains = assignedDomains + getDomains(geodatabase,featureDatasetList,configFile,"Feature Dataset")
        
        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()
        # FUNCTION - Get the domains for these feature calsses
        assignedDomains = assignedDomains + getDomains(geodatabase,featureClassList,configFile,"Feature Class")

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()
        # FUNCTION - Get the domains for these tables
        assignedDomains = assignedDomains + getDomains(geodatabase,featureClassList,configFile,"Table")
        
        # Get a list of domains on the geodatabase
        geodatabaseDomains = arcpy.da.ListDomains(geodatabase)      
        # For each of the domains
        for domain in geodatabaseDomains:
            usedDomainCount = 0
            # Check it is being used by looking at the assigned domains list
            for assignedDomain in assignedDomains:
                if (domain.name == assignedDomain):               
                    usedDomainCount = usedDomainCount + 1                           

            # If domain is not being used            
            if (usedDomainCount == 0):
                # Remove the domain from the geodatabase
                arcpy.AddMessage("Removing domain " + domain.name + " as not being used...")
                arcpy.DeleteDomain_management(geodatabase, domain.name)              
        
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


# Get a list of domains used in the database and reassigns duplicates
def getDomains(geodatabase,datasetList,configFile,dataType):
    assignedDomains = []   
    # Loop through the datasets
    for dataset in datasetList:
        # Setup the source and destination paths
        sourceDatasetPath = os.path.join(geodatabase, dataset)
        
        # If feature datasets
        if (dataType == "Feature Dataset"):
            # Get a list of the feature classes in the feature dataset
            featureClassList = arcpy.ListFeatureClasses("","",dataset)

            # Change dataset name to be just name (remove user and schema if SDE database)
            splitDataset = dataset.split('.')
            dataset = splitDataset[-1]
            
            # Loop through the feature classes in the feature dataset
            for featureClass in featureClassList:  
                # Change feature class name to be just name (remove user and schema if SDE database)
                splitDataset = featureClass.split('.')
                featureClass = splitDataset[-1]

                # Don't include _H or VW
                if ("_H" not in featureClass) and ("VW" not in featureClass) and ("vw" not in featureClass):   
                    # Setup the source and destination paths                
                    sourceDatasetPath = os.path.join(geodatabase + "\\" + dataset, featureClass)
                    
                    # List fields in feature class
                    fields = arcpy.ListFields(featureClass)

                    # Loop through fields
                    for field in fields:
                        # Check if field has domain
                        if field.domain != "":
                            # If configuration provided
                            if (configFile):
                                # Set CSV delimiter                         
                                csvDelimiter = ","

                                domain = field.domain
                                # Look through configuration file to see if domain exists
                                # Open the CSV file
                                with open(configFile, 'rb') as csvFile:
                                    # Read the CSV file
                                    rows = csv.reader(csvFile, delimiter=csvDelimiter)

                                    # For each row in the CSV
                                    count = 0
                                    for row in rows:
                                        # Ignore the first line containing headers
                                        if (count > 0):
                                            originalDomain = row[0]
                                            duplicateDomain = row[1]
                                            # If duplicate domain is in config file
                                            if (field.domain == duplicateDomain):
                                                arcpy.AddMessage("Reassigning domain on feature class " + featureClass + " from " + field.domain + " to " + originalDomain + " as it is duplicated...")
                                                # Re-assign domain to other domain
                                                arcpy.AssignDomainToField_management(sourceDatasetPath, field.name, originalDomain, "")
                                                domain = originalDomain

                                        count = count + 1
                                        
                                    # Add the domain to the list
                                    assignedDomains.append(domain)        
                            else:
                                # Add the domain to the list
                                assignedDomains.append(field.domain)                            
                        
        # If feature classes/tables
        else:       
            # List fields in feature class
            fields = arcpy.ListFields(dataset)

            # Change dataset name to be just name (remove user and schema if SDE database)
            splitDataset = dataset.split('.')
            dataset = splitDataset[-1]

            # Don't include _H or VW
            if ("_H" not in dataset) and ("VW" not in dataset) and ("vw" not in dataset):                            
                # Loop through fields
                for field in fields:
                    # Check if field has domain
                    if field.domain != "":
                        # If configuration provided
                        if (configFile):
                            # Set CSV delimiter                         
                            csvDelimiter = ","
                
                            domain = field.domain
                            # Look through configuration file to see if domain exists
                            # Open the CSV file
                            with open(configFile, 'rb') as csvFile:
                                # Read the CSV file
                                rows = csv.reader(csvFile, delimiter=csvDelimiter)

                                # For each row in the CSV
                                count = 0
                                for row in rows:
                                    # Ignore the first line containing headers
                                    if (count > 0):
                                        originalDomain = row[0]
                                        duplicateDomain = row[1]
                        
                                        # If duplicate domain is in config file
                                        if (field.domain == duplicateDomain):
                                            arcpy.AddMessage("Reassigning domain on feature class " + dataset + " from " + field.domain + " to " + originalDomain + " as it is duplicated...")
                                            # Re-assign domain to other domain
                                            arcpy.AssignDomainToField_management(sourceDatasetPath, field.name, originalDomain, "")
                                            domain = originalDomain

                                    count = count + 1
                                        
                                # Add the domain to the list
                                assignedDomains.append(domain)                             
                        else:
                            # Add the domain to the list
                            assignedDomains.append(field.domain)
                            
    # Return a list of assigned domains
    return assignedDomains
        
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
    
