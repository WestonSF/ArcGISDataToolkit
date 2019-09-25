#-------------------------------------------------------------
# Name:       Geodatabase Replication
# Purpose:    Copies data from one geodatabase to another using a CSV file to map dataset names. Two update options:
#             Existing Mode - Will delete and append records, so field names need to be the same.
#             New Mode - Copies full dataset over to destination. Can set a list of dataset names to exclude.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    10/04/2014
# Last Updated:    09/10/2017
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcGIS for Desktop 10.1+
# Python Version:   2.7
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib

# Set global variables
# Logging
enableLogging = "true" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...") and to print messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "GeodatabaseReplication.log") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
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
import csv


# Start of main function
def mainFunction(sourceGeodatabase,destinationGeodatabase,datasetsOption,updateMode,configFile,excludeList,includeViews): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # Convert exclude list to a list
        excludeList = excludeList.split(',')

        # Get a list of the feature datasets in the database
        arcpy.env.workspace = sourceGeodatabase
        featureDatasetList = arcpy.ListDatasets("", "Feature")
        # FUNCTION - Copy over these feature datasets
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,updateMode,configFile,excludeList,featureDatasetList,"Feature Dataset",includeViews)

        # Get a list of the feature classes in the database
        featureClassList = arcpy.ListFeatureClasses()
        # FUNCTION - Copy over these feature classes
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,updateMode,configFile,excludeList,featureClassList,"Feature Class",includeViews)

         # Get a list of the tables in the database
        tableList = arcpy.ListTables()
        # FUNCTION - Copy over these tables
        copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,updateMode,configFile,excludeList,tableList,"Table",includeViews)

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


# Copy datasets function
def copyDatasets(sourceGeodatabase,destinationGeodatabase,datasetsOption,updateMode,configFile,excludeList,datasetList,dataType,includeViews):
    # Loop through the datasets
    for dataset in datasetList:
        # If feature datasets
        if (dataType == "Feature Dataset"):
            # Get a list of the feature classes in the feature dataset
            dataset2List = arcpy.ListFeatureClasses("","",dataset)
        # Feature classes and tables
        else:
            # Reassign list
            dataset2List = datasetList
            datasetList = []

        # Change dataset name to be just name (remove user and schema if SDE database) - Used just for source dataset
        splitDataset = dataset.split('.')
        newDataset = splitDataset[-1]

        # Store current dataset working on
        currentDataset = newDataset

        # Loop through the datasets
        for dataset2 in dataset2List:
            # Change feature class name to be just name (remove user and schema if SDE database) - Used just for source dataset
            splitDataset = dataset2.split('.')
            newDataset2 = splitDataset[-1]

            # If dataset is not in the excluded list
            if (newDataset2 not in excludeList):
                # Set default variables
                datasetInConfig = "false"
                versionDataset = "false"
                # If feature datasets
                if (dataType == "Feature Dataset"):
                    needFeatureDataset = "true"
                # Feature classes and tables
                else:
                    needFeatureDataset = "false"

                # If feature datasets
                if (dataType == "Feature Dataset"):
                    # Setup the source and destination paths - Source needs to have full name including schema and user
                    sourceDatasetPath = os.path.join(sourceGeodatabase + "\\" + dataset, dataset2)
                    destinationDatasetPath = os.path.join(destinationGeodatabase + "\\" + newDataset, newDataset2)

                # Feature classes and tables
                else:
                    # Setup the source and destination paths - Source needs to have full name including schema and user
                    sourceDatasetPath = os.path.join(sourceGeodatabase, dataset2)
                    destinationDatasetPath = os.path.join(destinationGeodatabase, newDataset2)

                # If configuration provided
                if (configFile):
                    # Set CSV delimiter
                    csvDelimiter = ","
                    # Look through configuration file to see if source dataset is in there
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

                                # If feature datasets
                                if (dataType == "Feature Dataset"):
                                    selectDataset = newDataset + "\\" + newDataset2
                                # Feature classes and tables
                                else:
                                    selectDataset = newDataset2

                                # If dataset is in config file
                                if ((selectDataset) == sourceDataset):
                                    datasetInConfig = "true"
                                    # Change the destination path
                                    destinationDatasetPath = os.path.join(destinationGeodatabase, destinationDataset)
                                    # Logging
                                    if (enableLogging == "true"):
                                        logger.info("Changing dataset name from " + sourceDatasetPath + " to " + destinationDatasetPath + "...")
                                    arcpy.AddMessage("Changing dataset name from " + sourceDatasetPath + " to " + destinationDatasetPath + "...")

                                    # Check for a backslash in dataset name
                                    splitDataset = destinationDataset.split('\\')
                                    # If split has occured, dataset is necessary in destination database
                                    if (len(splitDataset) > 1):
                                        newDataset = splitDataset[0]
                                        needFeatureDataset = "true"
                                    else:
                                        needFeatureDataset = "false"

                                    # If versioning the dataset
                                    if (version == "yes"):
                                        versionDataset = "true"

                            count = count + 1

                # If feature dataset already exists in destination database
                if arcpy.Exists(os.path.join(destinationGeodatabase, newDataset)):
                    # Copy over dataset if necessary
                    if ((datasetsOption == "All") or (datasetInConfig == "true")):
                        # Get count of the source dataset
                        datasetCount = arcpy.GetCount_management(sourceDatasetPath)
                        # Check Dataset record count is more than 0
                        if (long(str(datasetCount)) > 0):
                            # Don't include _H - archive table
                            if (newDataset2[-2:].lower() != "_h"):
                                # Don't include views if specified
                                if (("VW" not in newDataset2) and ("vw" not in newDataset2)) or ((("VW" in newDataset2) or ("vw" in newDataset2)) and (includeViews == "true")):
                                    # If dataset already exists when doing a data copy
                                    if ((arcpy.Exists(destinationDatasetPath)) and (updateMode == "New")):
                                        # Delete the dataset first
                                        arcpy.Delete_management(destinationDatasetPath, "FeatureClass")

                                    # If creating new dataset - updateMode is New
                                    if (updateMode == "New"):
                                        # If table
                                        if (dataType == "Table"):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Copying over table - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Copying over table - " + destinationDatasetPath + "...")
                                            # Copy over table
                                            arcpy.CopyRows_management(sourceDatasetPath, destinationDatasetPath, "")
                                            arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                            if (enableLogging == "true"):
                                                logger.info("Dataset record count - " + str(datasetCount))

                                            # Set the archive dataset paths
                                            sourceArchiveDatasetPath = os.path.join(sourceGeodatabase, newDataset2 + "_H")
                                            destinationArchiveDatasetPath = os.path.join(destinationGeodatabase, newDataset2 + "_H")

                                            # Check if dataset is archived
                                            datasetArchived =  arcpy.Exists(sourceArchiveDatasetPath)

                                            if (datasetArchived == 1):
                                                # Logging
                                                if (enableLogging == "true"):
                                                    logger.info("Copying over archive table - " + destinationArchiveDatasetPath + "...")
                                                arcpy.AddMessage("Copying over archive table - " + destinationArchiveDatasetPath + "...")
                                                # Copy over archive dataset (_H) too
                                                arcpy.CopyRows_management(sourceArchiveDatasetPath, destinationArchiveDatasetPath, "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

                                        # Feature classes
                                        else:
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Copying over feature class - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Copying over feature class - " + destinationDatasetPath + "...")
                                            # Copy over feature class
                                            arcpy.CopyFeatures_management(sourceDatasetPath, destinationDatasetPath, "", "0", "0", "0")
                                            arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                            if (enableLogging == "true"):
                                                logger.info("Dataset record count - " + str(datasetCount))

                                            # Set the archive dataset paths
                                            sourceArchiveDatasetPath = os.path.join(sourceGeodatabase, newDataset2 + "_H")
                                            destinationArchiveDatasetPath = os.path.join(destinationGeodatabase, newDataset2 + "_H")

                                            # Check if dataset is archived
                                            datasetArchived =  arcpy.Exists(sourceArchiveDatasetPath)

                                            if (datasetArchived == 1):
                                                # Logging
                                                if (enableLogging == "true"):
                                                    logger.info("Copying over archive feature class - " + destinationArchiveDatasetPath + "...")
                                                arcpy.AddMessage("Copying over archive feature class - " + destinationArchiveDatasetPath + "...")
                                                # Copy over archive dataset (_H) too
                                                arcpy.CopyFeatures_management(sourceArchiveDatasetPath, destinationArchiveDatasetPath, "", "0", "0", "0")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

                                    # Else refreshing existing dataset - updateMode is Existing
                                    else:
                                        # If table
                                        if (dataType == "Table"):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Loading in records for table - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Loading in records for table - " + destinationDatasetPath + "...")
                                            # Refreshing table
                                            arcpy.DeleteRows_management(destinationDatasetPath)
                                            # Try append in data - Catch error if there are any and continue
                                            try:
                                                arcpy.Append_management(sourceDatasetPath, destinationDatasetPath, "NO_TEST", "", "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

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
                                                logger.warning(errorMessage)

                                        # Feature classes
                                        else:
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Loading in records for feature class - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Loading in records for feature class - " + destinationDatasetPath + "...")
                                            # Refreshing feature class
                                            arcpy.DeleteFeatures_management(destinationDatasetPath)
                                            # Try append in data - Catch error if there are any and continue
                                            try:
                                                arcpy.Append_management(sourceDatasetPath, destinationDatasetPath, "NO_TEST", "", "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

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
                                                logger.warning(errorMessage)

                                    if (versionDataset == "true"):
                                        # If dataset is not versioned already and update mode is new - Feature dataset
                                        datasetVersioned = arcpy.Describe(os.path.join(destinationGeodatabase, dataset)).isVersioned
                                        if ((datasetVersioned == 0) and (updateMode == "New")):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Versioning dataset - " + os.path.join(destinationGeodatabase, newDataset) + "...")
                                            arcpy.AddMessage("Versioning dataset - " + os.path.join(destinationGeodatabase, newDataset) + "...")
                                            arcpy.RegisterAsVersioned_management(os.path.join(destinationGeodatabase, newDataset), "NO_EDITS_TO_BASE")
                        else:
                            arcpy.AddWarning("Dataset " + destinationDatasetPath + " is empty and won't be copied...")
                            # Logging
                            if (enableLogging == "true"):
                                logger.warning("Dataset " + destinationDatasetPath + " is empty and won't be copied...")


                # Otherwise
                else:
                    # Copy over dataset if necessary
                    if ((datasetsOption == "All") or (datasetInConfig == "true")):
                        # Get count of the source dataset
                        datasetCount = arcpy.GetCount_management(sourceDatasetPath)
                        # Check Dataset record count is more than 0
                        if (long(str(datasetCount)) > 0):
                            # Don't include _H - archive table
                            if (newDataset2[-2:].lower() != "_h"):
                                # Don't include views if specified
                                if (("VW" not in newDataset2) and ("vw" not in newDataset2)) or ((("VW" in newDataset2) or ("vw" in newDataset2)) and (includeViews == "true")):
                                    # If feature dataset is necessary in destination database
                                    if (needFeatureDataset == "true"):
                                        # Create feature dataset
                                        arcpy.CreateFeatureDataset_management(destinationGeodatabase, newDataset, sourceDatasetPath)

                                    # If creating new dataset - updateMode is New
                                    if (updateMode == "New"):
                                        # If table
                                        if (dataType == "Table"):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Copying over table - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Copying over table - " + destinationDatasetPath + "...")
                                            # Copy over table
                                            arcpy.CopyRows_management(sourceDatasetPath, destinationDatasetPath, "")
                                            arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                            if (enableLogging == "true"):
                                                logger.info("Dataset record count - " + str(datasetCount))

                                            # Set the archive dataset paths
                                            sourceArchiveDatasetPath = os.path.join(sourceGeodatabase, newDataset2 + "_H")
                                            destinationArchiveDatasetPath = os.path.join(destinationGeodatabase, newDataset2 + "_H")

                                            # Check if dataset is archived
                                            datasetArchived =  arcpy.Exists(sourceArchiveDatasetPath)

                                            if (datasetArchived == 1):
                                                # Logging
                                                if (enableLogging == "true"):
                                                    logger.info("Copying over archive table - " + destinationArchiveDatasetPath + "...")
                                                arcpy.AddMessage("Copying over archive table - " + destinationArchiveDatasetPath + "...")
                                                # Copy over archive dataset (_H) too
                                                arcpy.CopyRows_management(sourceArchiveDatasetPath, destinationArchiveDatasetPath, "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

                                        # Feature classes
                                        else:
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Copying over feature class - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Copying over feature class - " + destinationDatasetPath + "...")
                                            # Copy over feature class
                                            arcpy.CopyFeatures_management(sourceDatasetPath, destinationDatasetPath, "", "0", "0", "0")
                                            arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                            if (enableLogging == "true"):
                                                logger.info("Dataset record count - " + str(datasetCount))

                                            # Set the archive dataset paths
                                            sourceArchiveDatasetPath = os.path.join(sourceGeodatabase, newDataset2 + "_H")
                                            destinationArchiveDatasetPath = os.path.join(destinationGeodatabase, newDataset2 + "_H")

                                            # Check if dataset is archived
                                            datasetArchived =  arcpy.Exists(sourceArchiveDatasetPath)

                                            if (datasetArchived == 1):
                                                # Logging
                                                if (enableLogging == "true"):
                                                    logger.info("Copying over archive feature class - " + destinationArchiveDatasetPath + "...")
                                                arcpy.AddMessage("Copying over archive feature class - " + destinationArchiveDatasetPath + "...")
                                                # Copy over archive dataset (_H) too
                                                arcpy.CopyFeatures_management(sourceArchiveDatasetPath, destinationArchiveDatasetPath, "", "0", "0", "0")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

                                    # Else refreshing existing dataset - updateMode is Existing
                                    else:
                                        # If table
                                        if (dataType == "Table"):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Loading in records for table - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Loading in records for table - " + destinationDatasetPath + "...")
                                            # Refreshing table
                                            arcpy.DeleteRows_management(destinationDatasetPath)
                                            # Try append in data - Catch error if there are any and continue
                                            try:
                                                arcpy.Append_management(sourceDatasetPath, destinationDatasetPath, "NO_TEST", "", "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

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
                                                logger.warning(errorMessage)

                                        # Feature classes
                                        else:
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Loading in records for feature class - " + destinationDatasetPath + "...")
                                            arcpy.AddMessage("Loading in records for feature class - " + destinationDatasetPath + "...")
                                            # Refreshing feature class
                                            arcpy.DeleteFeatures_management(destinationDatasetPath)
                                            # Try append in data - Catch error if there are any and continue
                                            try:
                                                arcpy.Append_management(sourceDatasetPath, destinationDatasetPath, "NO_TEST", "", "")
                                                arcpy.AddMessage("Dataset record count - " + str(datasetCount))
                                                if (enableLogging == "true"):
                                                    logger.info("Dataset record count - " + str(datasetCount))

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
                                                logger.warning(errorMessage)

                                    if (versionDataset == "true"):
                                        # If feature dataset has been created - Set path to that
                                        if (needFeatureDataset == "true"):
                                            datasetPath = os.path.join(destinationGeodatabase, newDataset)
                                        # Otherwise - Set path to feature class
                                        else:
                                            datasetPath = destinationDatasetPath

                                        # If dataset is not versioned already and update mode is new
                                        datasetVersioned = arcpy.Describe(datasetPath).isVersioned
                                        if ((datasetVersioned == 0) and (updateMode == "New")):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Versioning dataset - " + datasetPath + "...")
                                            arcpy.AddMessage("Versioning dataset - " + datasetPath + "...")
                                            arcpy.RegisterAsVersioned_management(datasetPath, "NO_EDITS_TO_BASE")
                        else:
                            arcpy.AddWarning("Dataset " + destinationDatasetPath + " is empty and won't be copied...")
                            # Logging
                            if (enableLogging == "true"):
                                logger.warning("Dataset " + destinationDatasetPath + " is empty and won't be copied...")

                # Change dataset name back to current dataset
                newDataset = currentDataset
                versionDataset = "false"
            # Dataset is in the excluded list
            else:
                printMessage("Dataset " + newDataset2 + " is excluded and won't be copied...","info")
                # Logging
                if (enableLogging == "true"):
                    logger.info("Dataset " + newDataset2 + " is excluded and won't be copied...")


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
