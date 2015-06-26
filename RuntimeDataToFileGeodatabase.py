#-------------------------------------------------------------
# Name:       Runtime Data to File Geodatabase
# Purpose:    Converts all runtime data used in ArcGIS Runtime products (.geodatabase extension) to a file geodatabase.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    26/06/2015
# Last Updated:    26/06/2015
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
import glob
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
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

# Start of main function
def mainFunction(folder,outputGeodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Go through each folder in the directory
        arcpy.AddMessage("Searching for runtime geodatabases...")
        runtimeCount = 0
        for root, subFolders, files in os.walk(folder):
            for file in files:
                if file.endswith(".geodatabase"):
                    runtimeCount = runtimeCount + 1
                    runtimeGeodatabase = os.path.join(root, file)
                    
                    arcpy.AddMessage("Copying runtime geodatabase - " + runtimeGeodatabase + "...")
                    arcpy.CopyRuntimeGdbToFileGdb_conversion(runtimeGeodatabase, os.path.join(arcpy.env.scratchFolder, "RuntimeGeodatabase-" + str(uuid.uuid1()) + ".gdb"))
                    
                    # Get the copied over gdb
                    extractedGDB = max(glob.iglob(str(arcpy.env.scratchFolder) + r"\*.gdb"), key=os.path.getmtime)   
                    # Assign the geodatbase workspace and load in the datasets to the lists
                    arcpy.env.workspace = extractedGDB
                    featuredatasetList = arcpy.ListDatasets("", "Feature")
                    featureclassList = arcpy.ListFeatureClasses()   
                    tableList = arcpy.ListTables()

                    # Load the feature datasets into the geodatabase if at least one is in the geodatabase provided
                    if (len(featuredatasetList) > 0):                 
                        # Loop through the feature classes
                        for eachFeaturedataset in featuredatasetList:
                           # Create a Describe object from the dataset
                           describeDataset = arcpy.Describe(eachFeaturedataset)       
                           # Copy feature dataset into geodatabase using the same dataset name and append unique identifier
                           arcpy.Copy_management(eachFeaturedataset, os.path.join(outputGeodatabase, describeDataset.name + "_" + str(uuid.uuid1())), "Feature Dataset")

                    # Load the feature classes into the geodatabase if at least one is in the geodatabase provided
                    if (len(featureclassList) > 0):                 
                        # Loop through the feature classes
                        for eachFeatureclass in featureclassList:
                           # Create a Describe object from the dataset
                           describeDataset = arcpy.Describe(eachFeatureclass)       
                           # Copy feature class into geodatabase using the same dataset name and append unique identifier
                           arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(outputGeodatabase, describeDataset.name + "_" + str(uuid.uuid1())), "", "0", "0", "0")
                                   
                    if (len(tableList) > 0):                        
                        # Loop through of the tables
                        for eachTable in tableList:
                           # Create a Describe object from the dataset
                           describeDataset = arcpy.Describe(eachTable)                            
                           # Copy table into geodatabase using the same dataset name and append unique identifier
                           arcpy.TableSelect_analysis(eachTable, os.path.join(outputGeodatabase, describeDataset.name + "_" + str(uuid.uuid1())), "")

        if (runtimeCount == 0):
            arcpy.AddError("No runtime data found in folder...")           
            # Logging
            if (enableLogging == "true"):
                # Log error          
                logger.error("No runtime data found in folder...")
            
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
    
