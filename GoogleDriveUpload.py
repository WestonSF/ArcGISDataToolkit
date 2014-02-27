#-------------------------------------------------------------
# Name:       Google Drive Upload
# Purpose:    Uploads a specified file or folder to Google Drive account. Need to get an authorization code manually first from here:
#             https://accounts.google.com/o/oauth2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&response_type=code&client_id={CLIENTID}&access_type=offline
#             There are then two options - Generate Credentials File or not. You will need to generate the credentials file
#             the first time this is run.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/02/2014
# Last Updated:    24/04/2014
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
import zipfile
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from apiclient import errors
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
def mainFunction(uploadFileFolder,fileName,generateCredentialsFile,inputCredentialsFile,clientID,clientSecret,authorisationCode,outputCredentialsFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # If input is a folder  
        if os.path.isdir(uploadFileFolder):
            arcpy.AddMessage("Zipping up data in folder - " + uploadFileFolder)
            # Logging
            if (enableLogging == "true"):
                logger.info("Zipping up data in folder - " + uploadFileFolder)

            # If file name provided
            if (len(fileName) > 0):
                zipFile = os.path.join(arcpy.env.scratchFolder, fileName + ".zip")
                zippedFolder = zipfile.ZipFile(zipFile, "w", allowZip64=True)
            # Otherwise use default name
            else:
                zipFile = os.path.join(arcpy.env.scratchFolder, "Data.zip")
                zippedFolder = zipfile.ZipFile(zipFile, "w", allowZip64=True)

            
            # Zip up the folder
            root_len = len(os.path.abspath(str(uploadFileFolder)))
            for root, dirs, files in os.walk(str(uploadFileFolder)):
              archive_root = os.path.abspath(root)[root_len:]
              for f in files:
                fullpath = os.path.join(root, f)
                archive_name = os.path.join(archive_root, f)
                zippedFolder.write(fullpath, archive_name)
            zippedFolder.close()

            # Update the file to point at the zipped file
            uploadFileFolder = zipFile
        
        # If need to generate credentials file first
        if (generateCredentialsFile == "true"):
            # Set the credentials file to output
            inputCredentialsFile = outputCredentialsFile
                
        # Get the folder for the credentials file
        credentialsFolder = os.path.dirname(inputCredentialsFile)
        # Set the working directory as the credentials folder
        os.chdir(credentialsFolder)

        credentialsFile = os.path.basename(inputCredentialsFile)  

        # For storing token
        storage = Storage(credentialsFile)
        
        # If need to generate credentials file first
        if (generateCredentialsFile == "true"):
            # Check https://developers.google.com/drive/scopes for all available scopes
            oAuthScope = 'https://www.googleapis.com/auth/drive'

            # Redirect URI for installed apps
            redirectURI = 'urn:ietf:wg:oauth:2.0:oob'

            # Run through the OAuth flow and retrieve authorization code
            flow = OAuth2WebServerFlow(clientID, clientSecret, oAuthScope, redirectURI)
            authorize_url = flow.step1_get_authorize_url()
            credentials = flow.step2_exchange(authorisationCode)
            
            # Storing access token and a refresh token in credentials file
            storage.put(credentials)
            
            arcpy.AddMessage("Stored credentials file here - " + os.getcwd())
            # Logging
            if (enableLogging == "true"):
                logger.info("Stored credentials file here - " + os.getcwd())   
            
        # Else already have the crdentials file
        else:         
            # Getting token credentials
            arcpy.AddMessage("Using credentials file stored here - " + os.path.join(os.getcwd(), credentialsFile))
            # Logging
            if (enableLogging == "true"):
                logger.info("Using credentials file stored here - " + os.path.join(os.getcwd(), credentialsFile))
                
            credentials = storage.get()
            

        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()
        http = credentials.authorize(http)
        # Drive API service instance
        drive_service = build('drive', 'v2', http=http)

        # Query the list of files to find if one is already there with the same title
        filesList = []
        files = drive_service.files().list(q="title='" + os.path.basename(uploadFileFolder) + "'").execute()
        filesList.extend(files['items'])

        # If a file has been found, overwrite it
        if (len(filesList) > 0):
            # Get the file ID
            fileID = filesList[0]['id']

            # Insert a file
            media_body = MediaFileUpload(uploadFileFolder, resumable=False)
            body = {
                'title': os.path.basename(uploadFileFolder)
            }

            # Update the file
            updatedFile = drive_service.files().update(fileId=fileID,body=uploadFileFolder,media_body=media_body).execute()

            arcpy.AddMessage("Successfully uploaded file to Google Drive - " + uploadFileFolder)
            # Logging
            if (enableLogging == "true"):
                logger.info("Successfully uploaded file to Google Drive - " + uploadFileFolder)
                
        # Otherwise, create new one
        else:    
            # Insert a file
            media_body = MediaFileUpload(uploadFileFolder, resumable=False)
            body = {
                'title': os.path.basename(uploadFileFolder)
            }

            # Upload the file
            newFile = drive_service.files().insert(body=body, media_body=media_body).execute()
            
            arcpy.AddMessage("Successfully uploaded file to Google Drive - " + uploadFileFolder)
            # Logging
            if (enableLogging == "true"):
                logger.info("Successfully uploaded file to Google Drive - " + uploadFileFolder)
                
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