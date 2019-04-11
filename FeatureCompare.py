#-------------------------------------------------------------
# Name:                 Feature Compare
# Purpose:              Looks through a feature class and compares to another feature class finding all
#                       features within a specified distance and creates a list of correct and incorrect features.
#                       Process:
#                       - Add Match field to feature class 1
#                       - For each feature in feature class 1
#                           - Check location against features in feature class 2
#                           - If there is a feature within 8 metres mark as correct
#                           - If more than 8 metres mark feature as incorrect
#                           - Export all correct features to a feature class
#                           - Export all incorrect features to a feature class
#                       Parameters:
#                       - Input feature class 1
#                       - Input feature class 2
#                       - Match distance e.g. 8 will match closest feature within 8 metres
# Author:               Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:         21/03/2019
# Last Updated:         21/03/2019
# ArcGIS Version:       ArcGIS Pro (ArcPy) 2.3+
# Python Version:       3.6.6+ (Anaconda Distribution)
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

# Set global variables
# Logging
enableLogging = "false" # Use within code to print and log messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email Use within code to send email - sendEmail(subject,message,attachment)
sendErrorEmail = "false"
emailSubject = "" # Subject in email
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
def mainFunction(featureClass1,featureClass2,matchDistance,matchedFeatureClass,unmatchedFeatureClass): # Add parameters sent to the script here e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        printMessage("Copying feature class to " + os.path.join(arcpy.env.scratchGDB, arcpy.Describe(featureClass1).name) + "...","info")
        # Copy the feature class and add a match field     
        arcpy.CopyFeatures_management(featureClass1, os.path.join(arcpy.env.scratchGDB, arcpy.Describe(featureClass1).name))
        printMessage("Comparing features in feature class...","info")
        # Compare feature class 1 to 2 with near analysis
        arcpy.Near_analysis(os.path.join(arcpy.env.scratchGDB, arcpy.Describe(featureClass1).name), featureClass2, str(matchDistance) + " Meters", "NO_LOCATION", "NO_ANGLE", "PLANAR")
        printMessage("Copying matched and unmatched features...","info")
        # Select matched features        
        arcpy.Select_analysis(os.path.join(arcpy.env.scratchGDB, arcpy.Describe(featureClass1).name), matchedFeatureClass, "NEAR_DIST > 0")
        arcpy.DeleteField_management(matchedFeatureClass, "NEAR_FID;NEAR_DIST")
        # Select unmatched features
        arcpy.Select_analysis(os.path.join(arcpy.env.scratchGDB, arcpy.Describe(featureClass1).name), unmatchedFeatureClass, "NEAR_DIST = -1")
        arcpy.DeleteField_management(unmatchedFeatureClass, "NEAR_FID;NEAR_DIST")        
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
            sendEmail(errorMessage,None)
# End of main function


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
    smtpServer.quit()
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
