#-------------------------------------------------------------
# Name:       FTP Upload
# Purpose:    Uploads a file to an FTP site.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    16/06/2014
# Last Updated:    17/06/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.6/2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import ftplib

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "false" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), r"Logs\FTPUpload.log") # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(fileFolder,ftpSite,ftpFolder,ftpUsername,ftpPassword): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")

        # --------------------------------------- Start of code --------------------------------------- #

        arcpy.AddMessage("Sending data to FTP server...")
        # Setup connection to FTP site
        ftpSession = ftplib.FTP(ftpSite,ftpUsername,ftpPassword)

        # If a folder
        if (os.path.isdir(fileFolder) == 1):
            root_len = len(os.path.abspath(str(fileFolder)))
            # For each of the directories in the folder
            for root, dirs, files in os.walk(str(fileFolder)):
              archive_root = os.path.abspath(root)[root_len:]
              # For each file
              for f in files:
                fullpath = os.path.join(root, f)
                
                # File to send to FTP site
                sendFile = open(fullpath,"rb")                

                # Get just the filename
                splitFile = fullpath.split('\\')
                file = splitFile[-1]

                # If putting into ftp folder, add folder to string
                if (ftpFolder):
                    ftpSession.storbinary("STOR " + ftpFolder + "//" + file, sendFile)
                else:
                    ftpSession.storbinary("STOR " + file, sendFile)
                        
                # Close the file
                sendFile.close()            
        # If a file
        else:  
            # File to send to FTP site
            sendFile = open(fileFolder,"rb")

            # Get just the filename
            splitFile = fileFolder.split('\\')
            file = splitFile[-1]
                  
            # If putting into ftp folder, add folder to string
            if (ftpFolder):
                ftpSession.storbinary("STOR " + ftpFolder + "//" + file, sendFile)
            else:
                ftpSession.storbinary("STOR " + file, sendFile)
                    
            # Close the file
            sendFile.close()

        # Close the FTP session            
        ftpSession.quit()
        
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
