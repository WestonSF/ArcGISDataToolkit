#-------------------------------------------------------------
# Name:                 Convert ArcFM Objects
# Purpose:              Converts datasets in a geodatabase from ArcFM format to Esri. Will either copy all
#                       datasets to a new geodatabase or convert the input geodatabase (not file geodatabase).
#                       If copying the datasets, ArcFM Desktop or ArcFM Object Reader will be need to be installed
#                       and will copy the datasets to a file geodatabase using GP tools, which automatically converts
#                       ArcFM objects to Esri objects. If converting the datasets, the class extension IDs will be
#                       updated in the GDB_Items table, but will not work for file geodatabases.
#                       - Need to install pyodbc python package (For converting option).
# Author:               Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:         05/02/2019
# Last Updated:         18/02/2019
# ArcGIS Version:       ArcMap (ArcPy) 10.2+
# Python Version:       2.7.10
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.mime.application
# Import ArcGIS modules
useArcPy = "true"
useArcGISAPIPython = "false"
if (useArcPy == "true"):
    # Import arcpy module
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
if (useArcGISAPIPython == "true"):
    # Import arcgis module
    import arcgis
import pyodbc

# Set global variables
# Logging
enableLogging = "true" # Use within code to print and log messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "Logs\\ConvertArcFMObjects.log") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email Use within code to send email - sendEmail(subject,message,attachment)
sendErrorEmail = "false"
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = None # e.g. 25
emailTo = "" # Address of email sent to
emailUser = "" # Address of email sent from
emailPassword = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None


# Start of main function
def mainFunction(inputGeodatabase,outputGeodatabase,copyDatabase,datasetsIgnore): # Add parameters sent to the script here e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        # Check input geodatabase exists
        if arcpy.Exists(inputGeodatabase):
            if (copyDatabase.lower() == "true"):
                printMessage("Converting all datasets in geodatabase to Esri objects (Copy)...","info")                
                # Create output geodatabase
                arcpy.CreateFileGDB_management(os.path.dirname(outputGeodatabase), os.path.basename(outputGeodatabase))
                # Load data into output geodatabase
                copyData(inputGeodatabase,outputGeodatabase,datasetsIgnore)               
                printMessage("New Esri geodatabase created - " + outputGeodatabase + "...","info")
            else:
                printMessage("Converting all datasets in geodatabase to Esri objects (Convert)...","info")
                # If file geodatabase
                if (os.path.splitext(inputGeodatabase)[1].lower() == ".gdb"):                
                    printMessage("File geodatabases are not supported with the convert option...","error")
                # If personal geodatabase
                elif (os.path.splitext(inputGeodatabase)[1].lower() == ".mdb"):   
                    # Get a list of datasets from the database
                    datasetList = getDatasetList(inputGeodatabase,datasetsIgnore)
                    # If there are datasets in the database
                    if (len(datasetList) > 0):
                        # Connect to access database
                        connection = pyodbc.connect('DRIVER={};DBQ={};PWD={}'.format('{Microsoft Access Driver (*.mdb)}',inputGeodatabase,'pw'))
                        cursor = connection.cursor()
                            
                        # For each dataset in the database
                        for dataset in datasetList:
                            printMessage("Querying " + dataset + "...","info")

                            # Get all the names and definitions for the GDB items in the database
                            SQL = 'SELECT Name,Definition FROM GDB_Items;'
                            rows = cursor.execute(SQL).fetchall()
                            definition = ""
                            for row in rows:
                                # If there is a name
                                if row[0]:
                                    # If the name is for this dataset
                                    if row[0].lower() == dataset.lower():
                                        # Get the definition
                                        definition = row[1]
                                        
                                        # If there is a definition
                                        if definition:
                                            # Check for ArcFM object IDs in CLSID and EXTCLSID tags
                                            if ("{EA831E02-7D3D-11D4-9A1B-0001031AE963}" in definition) or ("{91BC9A23-B210-4EE5-B524-93BCD640E58D}" in definition) or ("{27E88E1C-9598-49C3-9B48-08FB5F5836B2}" in definition) or ("{BF77404C-E8B3-4EE8-9456-BCA121416675}"  in definition) or ("{D94429F6-466F-4DF9-8262-DE969EF4491C}" in definition):
                                                printMessage(dataset + " is an ArcFM object...","info")

                                                # Update the record to be an Esri object by updating the CLSID and removing the EXTCLS value
                                                # Feature class
                                                if "FeatureClassInfo" in definition:
                                                    definition = definition.replace("{EA831E02-7D3D-11D4-9A1B-0001031AE963}","{52353152-891A-11D0-BEC6-00805F7C4268}")
                                                # Table
                                                else:
                                                    definition = definition.replace("{EA831E02-7D3D-11D4-9A1B-0001031AE963}","{7A566981-C114-11D2-8A28-006097AFF44E}")
                                                definition = definition.replace("{91BC9A23-B210-4EE5-B524-93BCD640E58D}","")
                                                definition = definition.replace("{27E88E1C-9598-49C3-9B48-08FB5F5836B2}","")
                                                definition = definition.replace("{BF77404C-E8B3-4EE8-9456-BCA121416675}","")
                                                definition = definition.replace("{D94429F6-466F-4DF9-8262-DE969EF4491C}","")
                                                definition = definition.replace("\'","\"")
                                                
                                                updateSQL = 'UPDATE GDB_Items SET Definition = \'' + definition + '\' where Name = \'' + dataset + '\';'
                                                cursor.execute(updateSQL)
                                                cursor.commit()                                
                                            # Esri objects have a "{52353152-891A-11D0-BEC6-00805F7C4268}" for feature classes and "{7A566981-C114-11D2-8A28-006097AFF44E}" for tables CLSID
                                            else:
                                                printMessage(dataset + " is already an Esri object...","info")                                                                        
                        # Close connection
                        cursor.close()
                        connection.close()                        
                    else:
                        printMessage("No datasets in database...","error")                        
                # If enterprise geodatabase - TODO
                elif (os.path.splitext(inputGeodatabase)[1].lower() == ".sde"):
                    printMessage("Database is not currently supported...","error")                    
                # Else other
                else:
                    printMessage("Database is not supported...","error")
        else:
            printMessage("Database does not exist - " + inputGeodatabase + "...","error")           
        # --------------------------------------- End of code --------------------------------------- #
        # If called from ArcGIS GP tool
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If using ArcPy
                if (useArcPy == "true"):
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
    # If error
    except Exception as e:
        # Build and show the error message
        # errorMessage = arcpy.GetMessages(2)

        errorMessage = ""
        # Build and show the error message
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):
                if (i == 0):
                    errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                else:
                    errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
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
            sendEmail("Python Script Error",errorMessage,None)
# End of main function


# Start of copy data function
def copyData(sourceGeodatabase,targetGeodatabase,datasetsIgnore):
    # Get a list of datasets from the database
    datasetList = getDatasetList(sourceGeodatabase,datasetsIgnore)

    printMessage("Copying data into database - " + targetGeodatabase + "...","info")
    for dataset in datasetList:
        # Get dataset properties
        datasetProperties = arcpy.Describe(os.path.join(sourceGeodatabase,dataset))

        printMessage("Copying - " + dataset + "...","info")
        # If a table
        if (datasetProperties.datasetType.lower() == "table"):
            arcpy.CopyRows_management(os.path.join(sourceGeodatabase,dataset), os.path.join(targetGeodatabase,dataset), "")
        # Else feature class
        else:
            arcpy.CopyFeatures_management(os.path.join(sourceGeodatabase,dataset), os.path.join(targetGeodatabase,dataset), "", "0", "0", "0")            
# End of copy data function

    
# Start of get dataset list function
def getDatasetList(geodatabase,datasetsIgnore):
    printMessage("Getting a list of datasets - " + geodatabase + "...","info")
    # Get a list of the feature datasets in the database
    arcpy.env.workspace = geodatabase
    datasetList = []
    featureDatasetList = arcpy.ListDatasets("", "Feature")
    for featureDataset in featureDatasetList:    
        # Get a list of the feature classes in the feature dataset
        datasetList = datasetList + arcpy.ListFeatureClasses("","",featureDataset) 
    # Get a list of the feature classes in the database
    datasetList = datasetList + arcpy.ListFeatureClasses()
    # Get a list of the tables in the database
    datasetList = datasetList + arcpy.ListTables()

    # Remove datasets from the list
    printMessage("Ignoring the following datasets - " + datasetsIgnore + "...","info")
    for datasetIgnore in datasetsIgnore.split(","):
        if datasetIgnore in datasetList:
            datasetList.remove(datasetIgnore)
        
    return datasetList
# End of get dataset list function


# Start of print and logging message function
def printMessage(message,type):
    # If using ArcPy
    if (useArcPy == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
            # Logging
            if (enableLogging == "true"):
                logger.warning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
            # Logging
            if (enableLogging == "true"):
                logger.error(message)
        else:
            arcpy.AddMessage(message)
            # Logging
            if (enableLogging == "true"):
                logger.info(message)
    else:
        print(message)
        # Logging
        if (enableLogging == "true"):
            logger.info(message)
# End of print and logging message function


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
def sendEmail(message,attachment):
    # Send an email
    printMessage("Sending email...","info")
    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort)
    smtpServer.ehlo()
    smtpServer.starttls()
    smtpServer.ehlo
    # Setup content for email (In html format)
    emailMessage = MIMEMultipart('alternative')
    emailMessage['Subject'] = emailSubject
    emailMessage['From'] = emailUser
    emailMessage['To'] = emailTo
    emailText = MIMEText(message, 'html')
    emailMessage.attach(emailText)

    # If there is a file attachment
    if (attachment):
        fp = open(attachment,'rb')
        fileAttachment = email.mime.application.MIMEApplication(fp.read(),_subtype="pdf")
        fp.close()
        fileAttachment.add_header('Content-Disposition','attachment',filename=os.path.basename(attachment))
        emailMessage.attach(fileAttachment)

    # Login with sender email address and password
    if (emailUser and emailPassword):
        smtpServer.login(emailUser, emailPassword)
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, emailMessage.as_string())
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # If using ArcPy
    if (useArcPy == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
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
