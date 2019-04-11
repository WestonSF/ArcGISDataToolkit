#-------------------------------------------------------------
# Name:       Data Update From Zip
# Purpose:    Updates data in a geodatabase from a zip file containing a geodatabase. Will get latest
#             zip file from update folder. Two update options:
#             Existing Mode - Will only update datasets that have the same name and will delete and
#             append records, so field names need to be the same. If dataset doesn't exist will copy it
#             over.
#             New Mode - Copies all datasets from the geodatabase and loads into geodatabase. Requires
#             no locks on geodatabase.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    31/05/2013
# Last Updated:    03/04/2019
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.4+
# Python Version:   2.6/2.7
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib

# Set global variables
# Logging
enableLogging = "true" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...") and to print messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "DataUpdateFromZip.log") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email logging
sendErrorEmail = "false"
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = 0 # e.g. 25
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None
# ArcGIS desktop installed
arcgisDesktop = "true"

# If ArcGIS desktop installed
if (arcgisDesktop == "true"):
    # Import extra modules
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2
import glob
import uuid
import zipfile


# Start of main function
def mainFunction(updateFolder,fileName,updateMode,geodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        
        # Get the arcgis version
        arcgisVersion = arcpy.GetInstallInfo()['Version']   

        # If a specific file is provided
        if (fileName):
            latestFile = os.path.join(updateFolder, fileName)
        # Otherwise get the latest file in a folder
        else:
            # Get the newest zip file from the update folder
            latestFile = max(glob.iglob(updateFolder + r"\*.zip"), key=os.path.getmtime)
      
        # Setup geodatabase to load data into in temporary workspace
        tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()))
        arcpy.AddMessage("Copying datasets...")    
          
        # Extract the zip file to a temporary location
        zip = zipfile.ZipFile(latestFile, mode="r")
        zip.extractall(str(tempFolder))

        # Loop through the files in the extracted folder
        for file in os.listdir(str(tempFolder)):               
            # If it's a shapefile
            if file.endswith(".shp"):
               # Get count of the source dataset
               datasetCount = arcpy.GetCount_management(os.path.join(str(tempFolder), file))
               eachFeatureclass = file.replace(".shp","")
          
               # Check Dataset record count is more than 0
               if (long(str(datasetCount)) > 0):
                   # If update mode is then copy, otherwise delete and appending records                
                   if (updateMode == "New"):                                           
                       # Logging
                       arcpy.AddMessage("Copying over feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                       if (enableLogging == "true"):
                          logger.info("Copying over feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                                
                       # Copy feature class into geodatabase using the same dataset name
                       arcpy.CopyFeatures_management(os.path.join(str(tempFolder), file), os.path.join(geodatabase, eachFeatureclass), "", "0", "0", "0")

                       # Get dataset count
                       datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, eachFeatureclass)) 
                       arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                       if (enableLogging == "true"):
                           logger.info("Dataset record count - " + str(datasetCount))   
                   else:
                        # If dataset exists in geodatabase, delete features and load in new data
                        if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                            # Logging
                            arcpy.AddMessage("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                            if (enableLogging == "true"):
                               logger.info("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
             
                            arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                            arcpy.Append_management(os.path.join(str(tempFolder), file), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")

                            # Get dataset count
                            datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, eachFeatureclass)) 
                            arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                            if (enableLogging == "true"):
                               logger.info("Dataset record count - " + str(datasetCount))   
                        else:
                            # Log warning
                            arcpy.AddWarning("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                            # Logging
                            if (enableLogging == "true"):
                                logger.warning(os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                                
                            # Copy feature class into geodatabase using the same dataset name
                            arcpy.CopyFeatures_management(os.path.join(str(tempFolder), file), os.path.join(geodatabase, eachFeatureclass), "", "0", "0", "0")           
               else:
                   arcpy.AddWarning("Dataset " + eachFeatureclass + " is empty and won't be copied...")                        
                   # Logging
                   if (enableLogging == "true"):
                       logger.warning("Dataset " + eachFeatureclass + " is empty and won't be copied...")
                               
            # If it's a FGDB
            if file.endswith(".gdb"):
                # Assign the geodatabase workspace and load in the datasets to the lists
                arcpy.env.workspace = os.path.join(str(tempFolder), file)
                featureclassList = arcpy.ListFeatureClasses()   
                tableList = arcpy.ListTables()       
      
                # Load the feature classes into the geodatabase if at least one is in the geodatabase provided
                if (len(featureclassList) > 0):        
                    # Loop through the feature classes
                    for eachFeatureclass in featureclassList:
                       # Get count of the source dataset
                       datasetCount = arcpy.GetCount_management(eachFeatureclass)                   
                       # Check Dataset record count is more than 0
                       if (long(str(datasetCount)) > 0):
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

                               # Get dataset count
                               datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, describeDataset.name)) 
                               arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                               if (enableLogging == "true"):
                                   logger.info("Dataset record count - " + str(datasetCount))   
                           else:
                                # If dataset exists in geodatabase, delete features and load in new data
                                if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                                    # Logging
                                    arcpy.AddMessage("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                                    if (enableLogging == "true"):
                                       logger.info("Updating feature class - " + os.path.join(geodatabase, eachFeatureclass) + "...")
                     
                                    arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                                    arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")

                                    # Get dataset count
                                    datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, eachFeatureclass)) 
                                    arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                    if (enableLogging == "true"):
                                       logger.info("Dataset record count - " + str(datasetCount))   
                                else:
                                    # Log warning
                                    arcpy.AddWarning("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                                    # Logging
                                    if (enableLogging == "true"):
                                        logger.warning(os.path.join(geodatabase, eachFeatureclass) + " does not exist. Copying over...")
                                        
                                    # Copy feature class into geodatabase using the same dataset name
                                    arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")           
                       else:
                           arcpy.AddWarning("Dataset " + eachFeatureclass + " is empty and won't be copied...")                        
                           # Logging
                           if (enableLogging == "true"):
                               logger.warning("Dataset " + eachFeatureclass + " is empty and won't be copied...")

                                                         
                if (len(tableList) > 0):    
                    # Loop through of the tables
                    for eachTable in tableList:
                       # Get count of the source dataset
                       datasetCount = arcpy.GetCount_management(eachTable)                   
                       # Check Dataset record count is more than 0
                       if (long(str(datasetCount)) > 0):
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

                               # Get dataset count
                               datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, describeDataset.name)) 
                               arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                               if (enableLogging == "true"):
                                   logger.info("Dataset record count - " + str(datasetCount))   
                           else:
                                # If dataset exists in geodatabase, delete features and load in new data
                                if arcpy.Exists(os.path.join(geodatabase, eachTable)):
                                    # Logging
                                    arcpy.AddMessage("Updating table - " + os.path.join(geodatabase, eachTable) + "...")
                                    if (enableLogging == "true"):
                                       logger.info("Updating table - " + os.path.join(geodatabase, eachTable) + "...")

                                    arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachTable))
                                    arcpy.Append_management(os.path.join(arcpy.env.workspace, eachTable), os.path.join(geodatabase, eachTable), "NO_TEST", "", "")

                                    # Get dataset count
                                    datasetCount = arcpy.GetCount_management(os.path.join(geodatabase, eachTable)) 
                                    arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                    if (enableLogging == "true"):
                                       logger.info("Dataset record count - " + str(datasetCount))   
                                else:
                                    # Log warning
                                    arcpy.AddWarning("Warning: " + os.path.join(geodatabase, eachTable) + " does not exist. Copying over...")
                                    # Logging
                                    if (enableLogging == "true"):
                                        logger.warning(os.path.join(geodatabase, eachTable) + " does not exist. Copying over...")

                                    # Copy table into geodatabase using the same dataset name
                                    arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")
                       else:
                           arcpy.AddWarning("Dataset " + eachTable + " is empty and won't be copied...")                        
                           # Logging
                           if (enableLogging == "true"):
                               logger.warning("Dataset " + eachTable + " is empty and won't be copied...")             
        
        # --------------------------------------- End of code --------------------------------------- #
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If ArcGIS desktop installed
                if (arcgisDesktop == "true"):
                    arcpy.SetParameter(1, output)
                # ArcGIS desktop not installed
                else:
                    return output 
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
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
    # If arcpy error
    except arcpy.ExecuteError:           
        # Build and show the error message
        errorMessage = arcpy.GetMessages(2)   
        printMessage(errorMessage,"error")           
        # Logging
        if (enableLogging == "true"):
            # Log error          
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")            
            # Remove file handler and close log file        
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)
    # If python error
    except Exception as e:
        errorMessage = ""         
        # Build and show the error message
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):        
                if (i == 0):
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = unicode(e.args[i]).encode('utf-8')
                else:
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
        # Else just one argument
        else:
            errorMessage = e
        printMessage(errorMessage,"error")
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)
            # Log end of process
            logger.info("Process ended.")            
            # Remove file handler and close log file        
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage)            
# End of main function


# Start of print message function
def printMessage(message,type):
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
        else:
            arcpy.AddMessage(message)
    # ArcGIS desktop not installed
    else:
        print(message)
# End of print message function


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
    printMessage("Sending email...","info")
    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort) 
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
    # Test to see if ArcGIS desktop installed
    if ((os.path.basename(sys.executable).lower() == "arcgispro.exe") or (os.path.basename(sys.executable).lower() == "arcmap.exe") or (os.path.basename(sys.executable).lower() == "arccatalog.exe")):
        arcgisDesktop = "true"
        
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
    # ArcGIS desktop not installed
    else:
        argv = sys.argv
        # Delete the first argument, which is the script
        del argv[0] 
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
