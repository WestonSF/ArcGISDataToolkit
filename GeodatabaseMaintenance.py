#-------------------------------------------------------------
# Name:       Geodatabase Maintenance
# Purpose:    Will compress geodatabase, update statistics and rebuild tables indexes. Optionally
#             stops connections to the geodatabase while the tool runs.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    07/08/2013
# Last Updated:    13/08/2015
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
def mainFunction(geodatabase,disconnectUsers): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # If disconnecting users
        if (disconnectUsers == "true"):
            # Block any new connections to the geodatabase
            arcpy.AcceptConnections(geodatabase, False)
            arcpy.AddMessage("Disconnecting all users from " + geodatabase + "...")            
            arcpy.DisconnectUser(geodatabase, "ALL")
        
        # Compress the geodatabase
        arcpy.AddMessage("Compressing the database....")
        arcpy.env.workspace = geodatabase
        arcpy.Compress_management(geodatabase)

        # Load in datsets to a list
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

        # Execute analyze datasets
        arcpy.AddMessage("Analyzing and updating the database statistics....")
        # Note: to use the "SYSTEM" option the workspace user must be an administrator.
        arcpy.AnalyzeDatasets_management(geodatabase, "SYSTEM", userDataList, "ANALYZE_BASE","ANALYZE_DELTA","ANALYZE_ARCHIVE")

        # Execute rebuild indexes
        arcpy.AddMessage("Rebuilding the indexes for all tables in the database....")
        # Note: to use the "SYSTEM" option the workspace user must be an administrator.
        arcpy.RebuildIndexes_management(geodatabase, "SYSTEM", userDataList, "ALL")

        # If disconnecting users
        if (disconnectUsers == "true"):
            # Allow any new connections to the geodatabase
            arcpy.AddMessage("Allowing all users to connect to " + geodatabase + "...")
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
            logging.FileHandler.close(logMessage)
            logger.removeHandler(logMessage)
        pass
    # If arcpy error
    except arcpy.ExecuteError:
        # If disconnecting users
        if (disconnectUsers == "true"):
            # Allow any new connections to the geodatabase
            arcpy.AddMessage("Allowing all users to connect to " + geodatabase + "...")            
            arcpy.AcceptConnections(geodatabase, True)
            
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
        # If disconnecting users
        if (disconnectUsers == "true"):
            # Allow any new connections to the geodatabase
            arcpy.AddMessage("Allowing all users to connect to " + geodatabase + "...")            
            arcpy.AcceptConnections(geodatabase, True)
            
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
    
    
