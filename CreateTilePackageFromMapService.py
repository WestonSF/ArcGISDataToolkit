#-------------------------------------------------------------
# Name:                 #
# Purpose:              #
# Author:               Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:         01/01/2019
# Last Updated:         01/01/2019
# ArcGIS Version:       ArcGIS API for Python 1.4.2+ or ArcGIS Pro (ArcPy) 2.1+
# Python Version:       3.6.5+ (Anaconda Distribution)
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.mime.application
import urllib.request
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
import datetime

# Set global variables
# Logging
enableLogging = "true" # Use within code to print and log messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "PythonTemplate.log") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
enableLogTable = "false" # Use to log the completion of the process to a geodatabase table
logTable = "" # e.g. "C:\Temp\Scratch.gdb\Logging"
# Email Use within code to send email - sendEmail(subject,message,attachment)
sendErrorEmail = "false"
emailSubject = "" # Subject in email
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = None # e.g. 25
emailTo = [] # Address of email sent to e.g. ["name1@example.com", "name2@example.com"]
emailUser = "" # Address of email sent from e.g. "name1@example.com"
emailPassword = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None

# Parameters
mapService = "https://tiledbasemaps.arcgis.com/arcgis/rest/services/World_Imagery/MapServer"
portalUser = "****"
portalPassword = "****"

# Start of main function
def mainFunction(): # Add parameters sent to the script here e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        
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
        printMessage("Process ended...","info")
        if (enableLogTable == "true"):
            # Log end message to table
            currentDate = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logToTable({"Date": currentDate,"Process": os.path.basename(__file__).replace(".py",""),"Status": "Success","Organisation": None,"DataName": None,"Message": "Process ended...","RecordCount":None})        
    # If error
    except Exception as e:
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
        printMessage("Process ended...","info")
        if (sendErrorEmail == "true"):
            # Send email
            sendEmail(errorMessage,None)
        if (enableLogTable == "true"):
            # Log end message to table
            currentDate = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            logToTable({"Date": currentDate,"Process": os.path.basename(__file__).replace(".py",""),"Status": "Fail","Organisation": None,"DataName": None,"Message": errorMessage,"RecordCount":None})            
# End of main function


# Start of print and logging message function
def printMessage(message,type):
    if (type.lower() == "warning"):
        # If using ArcPy
        if (useArcPy == "true"):
            arcpy.AddWarning(message)
        else:
            print(message)
        # Logging
        if (enableLogging == "true"):
            logger.warning(message)     
    elif (type.lower() == "error"):
        # If using ArcPy
        if (useArcPy == "true"):
            arcpy.AddError(message)
        else:
            print(message)
        # Logging
        if (enableLogging == "true"):
            logger.error(message)   
    else:
        # If using ArcPy
        if (useArcPy == "true"):            
            arcpy.AddMessage(message)
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


# Start of log to table function
def logToTable(logData):
    try:
        # If using ArcPy
        if (useArcPy == "true"):
            # If table exists
            if arcpy.Exists(logTable):
                requiredFieldNames = ["Date","Process","Status","Organisation","DataName","Message","RecordCount"]
                fieldNames = [f.name.lower() for f in arcpy.ListFields(logTable)]
                requiredFieldsNotPresentCount = 0
                for requiredFieldName in requiredFieldNames:
                    if requiredFieldName.lower() not in fieldNames:
                        printMessage(requiredFieldName + " is required in the log table...","error") 
                        requiredFieldsNotPresentCount  += 1
                if (requiredFieldsNotPresentCount == 0):
                    # Check whether all the dictionary values have been provided
                    value1 = None
                    if "Date" in logData:
                        value1 = logData["Date"]
                    value2 = None
                    if "Process" in logData:
                        # If not blank
                        if (logData["Process"]):
                            value2 = logData["Process"][:200] # Strip to be below 200 characters
                    value3 = None
                    if "Status" in logData:
                        # If not blank
                        if (logData["Status"]):
                            value3 = logData["Status"][:50] # Strip to be below 50 characters
                    value4 = None
                    if "Organisation" in logData:
                        # If not blank
                        if (logData["Organisation"]):
                            value4 = logData["Organisation"][:50] # Strip to be below 50 characters
                    value5 = None        
                    if "DataName" in logData:
                        # If not blank
                        if (logData["DataName"]):
                            value5 = logData["DataName"][:50] # Strip to be below 50 characters
                    value6 = None
                    if "Message" in logData:
                        # If not blank
                        if (logData["Message"]):
                            value6 = logData["Message"][:1000] # Strip to be below 1000 characters
                    value7 = None 
                    if "RecordCount" in logData:
                        # If not blank
                        if (str(logData["RecordCount"])):
                            # If a number
                            if (str(logData["RecordCount"]).isdigit()):
                                value7 = logData["RecordCount"]
                        
                    # Write to table
                    cursor = arcpy.da.InsertCursor(logTable, requiredFieldNames)
                    cursor.insertRow([value1,value2,value3,value4,value5,value6,value7])
                    del cursor
            else:
                printMessage("Log table does not exist - " + logTable + "...","error")
        else:
            printMessage("This message will not be logged to table. Table logging is only supported with ArcPy...","warning")        
    # If error
    except Exception as e:
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
        printMessage("Log to table error...","error") 
        printMessage(errorMessage,"error")        
# End of log to table function


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
    emailMessage['To'] = ", ".join(emailTo)
    emailText = MIMEText(str(message), 'html')
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
    printMessage("Process started...","info")
    # Setup the use of a proxy for requests
    if (enableProxy == "true"):
        # Setup the proxy
        proxy = urllib.request.ProxyHandler({requestProtocol : proxyURL})
        openURL = urllib.request.build_opener(proxy)
        # Install the proxy
        urllib.request.install_opener(openURL)
    mainFunction(*argv)
