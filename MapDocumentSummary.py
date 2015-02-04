#-------------------------------------------------------------
# Name:       Map Document Summary
# Purpose:    Creates a summary for each map document in a folder, stating description information about the map document
#             as well as a list of data sources used in the map documents.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    27/05/2014
# Last Updated:    04/02/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10/.2
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
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
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

# Start of main function
def mainFunction(mxdFolder,outputCSV,csvDelimiter,subDirectories): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Create a CSV file
        csvFile = open(outputCSV, 'wb')
        # Setup writer
        if csvDelimiter == "|":
            writer = csv.writer(csvFile, delimiter="|")                            
        if csvDelimiter == ";":
            writer = csv.writer(csvFile, delimiter=";")                            
        if csvDelimiter == ",":
            writer = csv.writer(csvFile, delimiter=",")

        # If including subdirectories
        if subDirectories == "true":                    
            # Loop through the folder and all subdirectories
            for subDirectory, directory, mxdFiles in os.walk(mxdFolder):
                for mxdFile in mxdFiles:
                    fullMXDPath = os.path.join(subDirectory, mxdFile)                    
                    mapDocumentSummary(writer,fullMXDPath,mxdFile)
                    
        else:
            # Loop through each of the MXD files in the folder
            for mxdFile in os.listdir(mxdFolder):
                fullMXDPath = os.path.join(mxdFolder, mxdFile)                      
                mapDocumentSummary(writer,fullMXDPath,mxdFile)
                    
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


# Start of map document summary function
def mapDocumentSummary(writer,fullMXDPath,mxdFile):
    # If a file
    if os.path.isfile(fullMXDPath):
        # If an mxd file
        if mxdFile.lower().endswith(".mxd"):
            # Reference MXD
            mxd = arcpy.mapping.MapDocument(fullMXDPath)
            arcpy.AddMessage("Getting information for " + fullMXDPath + "...")
         
            # Add in map document path
            row = []
            row.append("Map Document")
            row.append(fullMXDPath)
            writer.writerow(row)

            # Add in map document title
            row = []
            row.append("Title")
            row.append(mxd.title)
            writer.writerow(row)
            
            # Add in map document summary
            row = []
            row.append("Summary")
            row.append(mxd.summary)
            writer.writerow(row)
            
            # Reference each data frame
            dataFrameList = arcpy.mapping.ListDataFrames(mxd)
            # For each data frame
            for dataFrame in dataFrameList:
                # Add in data frame name
                row = []
                row.append("Data Frame")
                row.append(dataFrame.name)
                writer.writerow(row)

                # Reference each layer in a data frame
                layerList = arcpy.mapping.ListLayers(mxd, "", dataFrame)
                # For each layer
                for layer in layerList:
                    # Add in layer name
                    row = []
                    row.append("Layer")
                    row.append(layer.longName)
                    writer.writerow(row)

                    if layer.supports("dataSource"):
                        # Add in layer data source
                        row = []
                        row.append("Data Source")
                        row.append(layer.dataSource)
                        writer.writerow(row)                         

                # Reference each table in a data frame
                tableList = arcpy.mapping.ListTableViews(mxd, "", dataFrame)
                # For each table
                for table in tableList:
                    # Add in table
                    row = []
                    row.append("Table")
                    row.append(table.name)
                    writer.writerow(row)

                    # Add in table data source
                    row = []
                    row.append("Data Source")
                    row.append(table.dataSource)
                    writer.writerow(row)
                        
            # Add in spacer rows
            row = []
            writer.writerow(row)
            row = []
            writer.writerow(row)       
# End of map document summary function


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
    
