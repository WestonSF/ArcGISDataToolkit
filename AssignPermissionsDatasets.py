#-------------------------------------------------------------
# Name:       Assign Permissions on Datasets
# Purpose:    Updates permissions for datasets specified in a CSV file. This will go through CSV file and make sure datasets have
#             the permissions specified for the relevant groups and users.      
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    12/06/2014
# Last Updated:    24/06/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import csv
import string

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
def mainFunction(databaseUsers,configFile): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # If configuration provided
        if (configFile):
            # Set CSV delimiter                         
            csvDelimiter = ","
            # Open the CSV file
            with open(configFile, 'rb') as csvFile:
                # Read the CSV file
                rows = csv.reader(csvFile, delimiter=csvDelimiter)

                # Get all the database users
                databaseUsers = string.split(databaseUsers, ",")
            
                # For each row in the CSV                              
                count = 0
                for row in rows:
                    # Ignore the first line containing headers
                    if (count > 0):                       
                        # Get the full dataset name
                        dataset = row[0]
                        # Get the permissions to be assigned to the dataset
                        viewUsers = row[1]
                        viewUsers = string.split(viewUsers, ",")
                        editUsers = row[2]
                        editUsers = string.split(editUsers, ",")
                        
                        # For each database user
                        for databaseUser in databaseUsers:
                            # Set the default value for privileges assigned
                            viewPrivilegesAssigned = "false"
                            editPrivilegesAssigned = "false"
                            
                            # For each user
                            for viewUser in viewUsers:
                                # If the database user has view privileges
                                if (databaseUser == viewUser):
                                    # Logging
                                    if (enableLogging == "true"):
                                        logger.info("Assigning View Permission to " + viewUser + " on dataset " + dataset + "...")  
                                    arcpy.AddMessage("Assigning View Permission to " + viewUser + " on dataset " + dataset + "...")                                
                                    # Change the view privileges for the user on the dataset
                                    arcpy.ChangePrivileges_management(dataset, viewUser, "GRANT", "")
                                    viewPrivilegesAssigned = "true"

                            # If privileges haven't been granted for this user on this dataset
                            if (viewPrivilegesAssigned == "false"):
                                # Logging
                                if (enableLogging == "true"):
                                    logger.info("Denying View Permission to " + databaseUser + " on dataset " + dataset + "...")                               
                                arcpy.AddMessage("Denying View Permission to " + databaseUser + " on dataset " + dataset + "...")
                                # Change the view privileges for the user on the dataset
                                arcpy.ChangePrivileges_management(dataset, databaseUser, "REVOKE", "")
                                
                            # For each user
                            for editUser in editUsers:
                                # If the database user has edit privileges
                                if (databaseUser == editUser):
                                    # Logging
                                    if (enableLogging == "true"):
                                        logger.info("Assigning Edit Permission to " + editUser + " on dataset " + dataset + "...")                                 
                                    arcpy.AddMessage("Assigning Edit Permission to " + editUser + " on dataset " + dataset + "...")                        
                                    # Change the edit privileges for the user on the dataset
                                    arcpy.ChangePrivileges_management(dataset, editUser, "GRANT", "GRANT")
                                    editPrivilegesAssigned = "true"
                                    
                            # If privileges haven't been granted for this user on this dataset
                            if (editPrivilegesAssigned == "false"):
                                # Logging
                                if (enableLogging == "true"):
                                    logger.info("Denying Edit Permission to " + databaseUser + " on dataset " + dataset + "...")                                 
                                arcpy.AddMessage("Denying Edit Permission to " + databaseUser + " on dataset " + dataset + "...")
                                # Change the edit privileges for the user on the dataset
                                arcpy.ChangePrivileges_management(dataset, databaseUser, "AS_IS", "REVOKE")
                                
                    count = count + 1
        # No configuration provided
        else:
            arcpy.AddError("No configuration file provided...")
            # Logging
            if (enableLogging == "true"):
                # Log error          
                logger.error("No configuration file provided...")                 
                # Remove file handler and close log file
                logging.FileHandler.close(logMessage)
                logger.removeHandler(logMessage)
            if (sendErrorEmail == "true"):
                # Send email
                sendEmail("No configuration file provided...")
                
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
    
