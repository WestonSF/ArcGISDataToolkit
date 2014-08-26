#-------------------------------------------------------------
# Name:       Field Aliases Export and Import
# Purpose:    Exports field aliases for datasets specified to a CSV file. Can also use a configuration CSV file to import
#             field aliases to datasets.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    25/08/2014
# Last Updated:    25/08/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.2+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import string
import csv

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
def mainFunction(featureClasses,importExport,folder): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #

        # Load the feature classes into a list if input values provided
        if (len(featureClasses) > 0):
            # Remove out apostrophes
            featureclassList = string.split(str(featureClasses).replace("'", ""), ";")

            # Loop through the feature classes
            for featureClass in featureclassList:
                # Create a Describe object from the dataset
                describeDataset = arcpy.Describe(featureClass)

                # If exporting field aliases
                if (importExport.lower() == "export"):                        
                    # Create a CSV file for the datasets fields
                    with open(os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv"), 'wb') as file:
                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Creating CSV - " + os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv") + "...")                                
                        arcpy.AddMessage("Creating CSV - " + os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv") + "...")

                        # Write the header role
                        writer = csv.writer(file, delimiter=",")
                        row = ["Field","Field Alias"] 
                        writer.writerow(row)
                        
                        # Create a list of fields using the ListFields function
                        fields = arcpy.ListFields(featureClass)

                        # Iterate through the list of fields
                        for field in fields:
                            row = []
                            # If field name doesn't include shape or OBJECTID
                            fieldName = field.name
                            if (("shape" not in fieldName.lower()) and ("objectid" not in fieldName.lower())):
                                # Write the fields
                                row.append(field.name)
                                row.append(field.aliasName)
                                writer.writerow(row)
                    # Close the file
                    file.close()
                # If importing field aliases
                if (importExport.lower() == "import"):
                    # If configuration file exists for this feature class
                    if (os.path.isfile(os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv")) == True):
                        # Logging
                        if (enableLogging == "true"):
                            logger.info("Configuration file located for " + describeDataset.name + " - " + os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv") + "...")                                
                        arcpy.AddMessage("Configuration file located for " + describeDataset.name + " - " + os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv") + "...")

                        # Create a list of fields using the ListFields function
                        fields = arcpy.ListFields(featureClass)

                        # Iterate through the list of fields
                        for field in fields:
                            # Open the CSV file
                            with open(os.path.join(folder, "FieldAliases_" + describeDataset.name + ".csv"), 'rb') as csvFile:
                                # Read the CSV file
                                rows = csv.reader(csvFile, delimiter=",")

                                # For each row in the CSV
                                count = 0
                                for row in rows:
                                    # Ignore the first line containing headers
                                    if (count > 0):
                                        # Get the field and field alias
                                        configField = row[0]
                                        configFieldAlias = row[1]
                                        # If field is in config                                      
                                        if (field.name == configField):
                                            # Logging
                                            if (enableLogging == "true"):
                                                logger.info("Setting field alias to " + configFieldAlias + " for " + field.name + " field in " + describeDataset.name)                                
                                            arcpy.AddMessage("Setting field alias to " + configFieldAlias + " for " + field.name + " field in " + describeDataset.name)  

                                            # Set field alias to what is in config
                                            arcpy.AlterField_management(featureClass, field.name, "", configFieldAlias)    
                                    count = count + 1                                                                
        else:
            arcpy.AddError("No datasets provided") 
            # Logging
            if (enableLogging == "true"):
                # Log error          
                logger.error("No datasets provided")                 
                # Remove file handler and close log file
                logging.FileHandler.close(logMessage)
                logger.removeHandler("No datasets provided")
            if (sendErrorEmail == "true"):
                # Send email
                sendEmail("No datasets provided")
            
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
                errorMessage = unicode(e.args[i]).encode('utf-8')
            else:
                errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
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
    
