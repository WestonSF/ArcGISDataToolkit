#-------------------------------------------------------------
# Name:       Geodatabase Maintenance
# Purpose:    Will compress geodatabase, update statistics and rebuild table indexes. Optionally
#             stops connections to the geodatabase while the tool runs.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    07/08/2013
# Last Updated:    18/12/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcGIS for Desktop 10.1+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2  
import arcpy

# Set global variables
# Logging
enableLogging = "false" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = "" # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
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

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Start of main function
def mainFunction(geodatabase,disconnectUsers): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # If disconnecting users
        if (disconnectUsers == "true"):
            # Block any new connections to the geodatabase
            arcpy.AcceptConnections(geodatabase, False)
            arcpy.AddMessage("Disconnecting all users from " + geodatabase + "...")
            # Logging
            if (enableLogging == "true"):
                logger.info("Disconnecting all users from " + geodatabase + "...")
            arcpy.DisconnectUser(geodatabase, "ALL")
        
        # Compress the geodatabase
        arcpy.AddMessage("Compressing geodatabase - " + geodatabase + "...")
        # Logging
        if (enableLogging == "true"):
            logger.info("Compressing geodatabase - " + geodatabase + "...")
        arcpy.env.workspace = geodatabase
        arcpy.Compress_management(geodatabase)

        # Load in datasets to a list
        dataList = arcpy.ListTables() + arcpy.ListFeatureClasses() + arcpy.ListDatasets()
        # Load in datasets from feature datasets to the list
        for dataset in arcpy.ListDatasets("", "Feature"):
            arcpy.env.workspace = os.path.join(geodatabase,dataset)
            dataList += arcpy.ListFeatureClasses() + arcpy.ListDatasets()

        # Reset the workspace
        arcpy.env.workspace = geodatabase

        # Get the user name for the workspace
        userName = arcpy.Describe(geodatabase).connectionProperties.user.lower()

        # Remove any datasets that are not owned by the connected user.
        userDataList = [ds for ds in dataList if ds.lower().find(".%s." % userName) > -1]        

        # Execute rebuild indexes
        arcpy.AddMessage("Rebuilding the indexes for all tables in the database....")
        # Logging
        if (enableLogging == "true"):
            logger.info("Rebuilding the indexes for all tables in the database....")
        # Note: to use the "SYSTEM" option the workspace user must be an administrator.
        arcpy.RebuildIndexes_management(geodatabase, "SYSTEM", userDataList, "ALL")
        
        # Execute analyze datasets
        arcpy.AddMessage("Analyzing and updating the database statistics....")
        # Logging
        if (enableLogging == "true"):
            logger.info("Analyzing and updating the database statistics....")
        # Note: to use the "SYSTEM" option the workspace user must be an administrator.
        arcpy.AnalyzeDatasets_management(geodatabase, "SYSTEM", userDataList, "ANALYZE_BASE","ANALYZE_DELTA","ANALYZE_ARCHIVE")

        # If disconnecting users
        if (disconnectUsers == "true"):
            # Allow any new connections to the geodatabase
            arcpy.AddMessage("Allowing all users to connect to " + geodatabase + "...")
            # Logging
            if (enableLogging == "true"):
                logger.info("Allowing all users to connect to " + geodatabase + "...")
            arcpy.AcceptConnections(geodatabase, True)
            
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
            logMessage.flush()
            logMessage.close()
            logger.handlers = []
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
        arcpy.AddError(errorMessage)              
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
