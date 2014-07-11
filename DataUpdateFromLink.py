#-------------------------------------------------------------
# Name:       Data Update from Link
# Purpose:    Downloads a zipped up file geodatabase from a download link. Updates data in a geodatabase
#             from the zip file. Two update options:
#             Existing Mode - Will only update datasets that have the same name and will delete and
#             append records, so field names need to be the same.
#             New Mode - Copies all datasets from the geodatabase and loads into geodatabase. Requires
#             no locks on geodatabase.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    05/09/2013
# Last Updated:    11/07/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import logging
import urllib2
import zipfile
import uuid
import glob
import arcpy

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "false" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), r"Logs\DataUpdateFromLink.log") # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(downloadLink,updateMode,geodatabase,featureDataset): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")

        # --------------------------------------- Start of code --------------------------------------- #

        setProxy = "false"       
        # Custom proxy
        if (setProxy == "true"):
            # Setup the proxy
            proxy = urllib2.ProxyHandler({"http": ""})
            openURL = urllib2.build_opener(proxy)
            # Install the proxy
            urllib2.install_opener(openURL)
    
        # Download the file from the link
        file = urllib2.urlopen(downloadLink)
        # Download in chunks
        fileChunk = 16 * 1024
        with open(os.path.join(arcpy.env.scratchFolder, "Data.zip"), 'wb') as output:
            while True:
                chunk = file.read(fileChunk)
                if not chunk:
                    break
                # Write chunk to output file
                output.write(chunk)
        output.close()
        
        # Unzip the file to the scrtach folder
        arcpy.AddMessage("Extracting zip file...")  
        zip = zipfile.ZipFile(os.path.join(arcpy.env.scratchFolder, "Data.zip"), mode="r")
        zip.extractall(arcpy.env.scratchFolder)

        # Get the newest unzipped database from the scratch folder
        database = max(glob.iglob(arcpy.env.scratchFolder + r"\*.gdb"), key=os.path.getmtime)
        
        # Assign the geodatbase workspace and load in the datasets to the lists
        arcpy.env.workspace = database
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
                   # Copy feature class into geodatabase using the same dataset name
                   # If feature dataset provided, add that to path
                   if featureDataset:
                      arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase + "\\" + featureDataset, describeDataset.name), "", "0", "0", "0")                                      
                   else:
                      arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                        # If feature dataset provided, add that to path
                        if featureDataset:
                            arcpy.DeleteFeatures_management(os.path.join(geodatabase + "\\" + featureDataset, eachFeatureclass))
                            arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase + "//" + featureDataset, eachFeatureclass), "NO_TEST", "", "")                            
                        else:
                            arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                            arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated")
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            loggingFunction(logFile,"warning",os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated")
                            
        if (len(tableList) > 0):    
            # Loop through of the tables
            for eachTable in tableList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachTable)
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):               
                   # Copy feature class into geodatabase using the same dataset name
                   arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachTable)):
                        arcpy.DeleteRows_management(os.path.join(geodatabase, eachTable))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachTable), os.path.join(geodatabase, eachTable), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachTable) + " does not exist and won't be updated")
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            loggingFunction(logFile,"warning",os.path.join(geodatabase, eachTable) + " does not exist and won't be updated")                  
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