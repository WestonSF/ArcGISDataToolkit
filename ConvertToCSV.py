#-------------------------------------------------------------
# Name:       Convert to CSV
# Purpose:    Converts a table or feature class to a CSV file. Optionally adds in header and footer
#             records also.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    16/01/2014
# Last Updated:    03/05/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
# Python Version:   2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import logging
import datetime
import smtplib
import string
import csv
import arcpy
arcpy.env.overwriteOutput = True

# Set variables
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
def mainFunction(featureClasses,tables,dataCSVDelimiter,headerFooter,headerFooterCSVDelimiter,outputFolder): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")

        # --------------------------------------- Start of code --------------------------------------- #
        # Check input datasets are provided
        if ((len(featureClasses) > 0) or (len(tables) > 0)):
            arcpy.AddMessage("Creating CSV(s)...")        
            # Load the feature classes and tables into a list if input values provided
            if (len(featureClasses) > 0):       
                # Remove out apostrophes
                featureclassList = string.split(str(featureClasses).replace("'", ""), ";")
                
                # Loop through the feature classes
                for featureClass in featureclassList:
                    # Create a Describe object from the dataset
                    describeDataset = arcpy.Describe(featureClass)
                
                    # Create a CSV file and write values from feature class
                    with open(os.path.join(outputFolder, describeDataset.name + ".csv"), 'wb') as file:
                        # Add in header information if required
                        if headerFooter == "true":
                            # Set header delimiter
                            if headerFooterCSVDelimiter == "|":
                                writer = csv.writer(file, delimiter="|")                            
                            if headerFooterCSVDelimiter == ";":
                                writer = csv.writer(file, delimiter=";")                            
                            if headerFooterCSVDelimiter == ",":
                                writer = csv.writer(file, delimiter=",")
                            # Add in header information   
                            headerRow = []                               
                            headerRow.append("H")
                            headerRow.append(describeDataset.name + ".csv" + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".gz")                                
                            writer.writerow(headerRow)

                        # Set data delimiter
                        if dataCSVDelimiter == "|":
                            writer = csv.writer(file, delimiter="|")                            
                        if dataCSVDelimiter == ";":
                            writer = csv.writer(file, delimiter=";")                            
                        if dataCSVDelimiter == ",":
                            writer = csv.writer(file, delimiter=",")
                            
                        fieldNames = []
                        # Open up feature class and get the header values then write to first line
                        for record in arcpy.ListFields(featureClass):
                            fieldNames.append(record.name)
                        writer.writerow(fieldNames)
                        # Write in each of the values for all of the records
                        with arcpy.da.SearchCursor(featureClass, "*") as cursor:
                            # For each row in the table
                            for row in cursor:
                                # For each value in the row
                                values = []
                                for value in row:
                                    # Encode any ascii characters
                                    value = unicode(value).encode('utf-8')
                                    # Append to list
                                    values.append(value)                             
                                # Write the row to the CSV file
                                writer.writerow(values)
                        
                        # Add in footer information if required
                        if headerFooter == "true":
                            # Set footer delimiter
                            if headerFooterCSVDelimiter == "|":
                                writer = csv.writer(file, delimiter="|")                            
                            if headerFooterCSVDelimiter == ";":
                                writer = csv.writer(file, delimiter=";")                            
                            if headerFooterCSVDelimiter == ",":
                                writer = csv.writer(file, delimiter=",")
                            
                            # Add in footer information
                            footerRow = []                             
                            footerRow.append("F")
                            footerRow.append(describeDataset.name + ".csv" + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".gz")
                            rowCount = arcpy.GetCount_management(featureClass)
                            footerRow.append(rowCount)
                            writer.writerow(footerRow)
                            
            if (len(tables) > 0):
                # Remove out apostrophes            
                tableList = string.split(str(tables).replace("'", ""), ";")

                # Loop through the tables
                for table in tableList:
                    # Create a Describe object from the dataset
                    describeDataset = arcpy.Describe(table)
               
                    # Create a CSV file and write values from table
                    with open(os.path.join(outputFolder, describeDataset.name + ".csv"), 'wb') as file:              
                        # Add in header information if required
                        if headerFooter == "true":
                            # Set header delimiter
                            if headerFooterCSVDelimiter == "|":
                                writer = csv.writer(file, delimiter="|")                            
                            if headerFooterCSVDelimiter == ";":
                                writer = csv.writer(file, delimiter=";")                            
                            if headerFooterCSVDelimiter == ",":
                                writer = csv.writer(file, delimiter=",")
                            # Add in header information   
                            headerRow = []                               
                            headerRow.append("H")
                            headerRow.append(describeDataset.name + ".csv" + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".gz")                                
                            writer.writerow(headerRow)

                        # Set data delimiter
                        if dataCSVDelimiter == "|":
                            writer = csv.writer(file, delimiter="|")                            
                        if dataCSVDelimiter == ";":
                            writer = csv.writer(file, delimiter=";")                            
                        if dataCSVDelimiter == ",":
                            writer = csv.writer(file, delimiter=",")
                            
                        fieldNames = []
                        # Open up table and get the header values then write to first line
                        for record in arcpy.ListFields(table):
                            fieldNames.append(record.name)
                        writer.writerow(fieldNames)
                        # Write in each of the values for all of the records
                        with arcpy.da.SearchCursor(table, "*") as cursor:
                            # For each row in the table
                            for row in cursor:
                                # For each value in the row
                                values = []
                                for value in row:
                                    # Encode any ascii characters
                                    value = unicode(value).encode('utf-8')
                                    # Append to list
                                    values.append(value)                             
                                # Write the row to the CSV file
                                writer.writerow(values)

                        # Add in footer information if required
                        if headerFooter == "true":
                            # Set footer delimiter
                            if headerFooterCSVDelimiter == "|":
                                writer = csv.writer(file, delimiter="|")                            
                            if headerFooterCSVDelimiter == ";":
                                writer = csv.writer(file, delimiter=";")                            
                            if headerFooterCSVDelimiter == ",":
                                writer = csv.writer(file, delimiter=",")
                            
                            # Add in footer information
                            footerRow = []                             
                            footerRow.append("F")
                            footerRow.append(describeDataset.name + ".csv" + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".gz")
                            rowCount = arcpy.GetCount_management(table)
                            footerRow.append(rowCount)
                            writer.writerow(footerRow)                            
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
    
