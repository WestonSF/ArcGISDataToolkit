#-------------------------------------------------------------
# Name:       Google Drive Upload
# Purpose:    Uploads a specified file to Google Drive account.

# Need to create credentials file first - https://accounts.google.com/o/oauth2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&client_id={CLIENTID}&access_type=offline

# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/02/2014
# Last Updated:    14/04/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy

import httplib2
import pprint

from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage

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
def mainFunction(uploadFile,clientID,clientSecret,authorisationCode): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #
        # Set the working directory as the scratch folder
        os.chdir(arcpy.env.scratchFolder)        

        # Check https://developers.google.com/drive/scopes for all available scopes
        oAuthScope = 'https://www.googleapis.com/auth/drive'

        # Redirect URI for installed apps
        redirectURI = 'urn:ietf:wg:oauth:2.0:oob'

        # Path to the crendentials
        credFileName = 'GoogleDriveCredentials'

        # For storing token
        storage = Storage(credFileName)

        if not storage.get():        
            # Run through the OAuth flow and retrieve authorization code
            flow = OAuth2WebServerFlow(clientID, clientSecret, oAuthScope, redirectURI)
            authorize_url = flow.step1_get_authorize_url()
            credentials = flow.step2_exchange(authorisationCode)

            # Storing access token and a refresh token in CRED_FILENAME
            arcpy.AddMessage("Storing credentials file here - " + os.getcwd())
            # Logging
            if (enableLogging == "true"):
                logger.info("Storing credentials file here - " + os.getcwd())           
            storage.put(credentials)
        else:
            # Getting token credentials
            arcpy.AddMessage("Using credentials file stored here - " + os.path.join(os.getcwd(), credFileName))
            # Logging
            if (enableLogging == "true"):
                logger.info("Using credentials file stored here - " + os.path.join(os.getcwd(), credFileName))              
            credentials = storage.get()

        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()
        http = credentials.authorize(http)
        drive_service = build('drive', 'v2', http=http)

        # Insert a file
        media_body = MediaFileUpload(uploadFile, resumable=False)
        body = {
            'title': os.path.basename(uploadFile)
        }

        # Upload the file
        file = drive_service.files().insert(body=body, media_body=media_body).execute()
        pprint.pprint(file)
        arcpy.AddMessage("Successfully uploaded file to Google Drive - " + uploadFile)
        # Logging
        if (enableLogging == "true"):
            logger.info("Successfully uploaded file to Google Drive - " + uploadFile)
            
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
                errorMessage = e.args[i]
            else:
                errorMessage = errorMessage + " " + e.args[i]
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
    
