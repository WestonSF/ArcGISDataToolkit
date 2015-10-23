#-------------------------------------------------------------
# Name:       WFS Download
# Purpose:    Downloads a dataset from a WFS feed. Parameters required:
#             - URL TO WFS Server - e.g. "http://Servername/geoserver/wfs?key=xxx"
#             - Layer/table name - e.g. "parcels"
#             - WFS download type - e.g. Shape-Zip
#             - Output feature class
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    23/10/2015
# Last Updated:    23/10/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcGIS for Desktop 10.3+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import urllib2
import zipfile
import glob
import uuid
import csv
import json

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
def mainFunction(wfsURL,wfsDataName,wfsDownloadType,outputFeatureClass): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Check the URL parameters
        if "?" in wfsURL:
            # If first parameter already provided
            firstParameter = "&"
        else:
            firstParameter = "?"           

        # Download the file from the WFS link
        requestURL = wfsURL + firstParameter + "SERVICE=WFS&REQUEST=GetFeature&TYPENAME=" + wfsDataName + "&outputformat=" + wfsDownloadType
        arcpy.AddMessage(requestURL)        
        response = urllib2.urlopen(requestURL)

        if (wfsDownloadType.lower() == "shape-zip"):
            fileType = ".zip"
        elif (wfsDownloadType.lower() == "csv"):
            fileType = ".csv"
        #json    
        else: 
            # Read json response
            geometryJSON = json.loads(response.read())

        if ((wfsDownloadType.lower() == "shape-zip") or (wfsDownloadType.lower() == "csv")):
            # Download the data
            arcpy.AddMessage("Downloading data from " + requestURL + "...")
            fileChunk = 16 * 1024
            downloadedFile = os.path.join(arcpy.env.scratchFolder, "Data-" + str(uuid.uuid1()) + fileType)
            with open(downloadedFile, 'wb') as output:
                downloadCount = 0
                while True:
                    chunk = response.read(fileChunk)
                    # If data size is small
                    if ((downloadCount == 0) and (len(chunk) < 1000)):
                        # Log error and end download
                        arcpy.AddError("No data returned, check the URL...")  
                        sys.exit()
                    if not chunk:
                        break
                    # Write chunk to output file
                    output.write(chunk)
                    downloadCount = downloadCount + 1
            output.close()
            arcpy.AddMessage("Downloaded to " + downloadedFile + "...")

        if (wfsDownloadType.lower() == "shape-zip"):
            # Unzip the file to the scratch folder
            arcpy.AddMessage("Extracting zip file...")
            zip = zipfile.ZipFile(downloadedFile, mode="r")

            zip.extractall(arcpy.env.scratchFolder)

            # Get the extracted shape file
            extractedShp = max(glob.iglob(str(arcpy.env.scratchFolder) + r"\*.shp"), key=os.path.getmtime)

            # Copy to feature class
            arcpy.AddMessage("Copying to " + outputFeatureClass + "...")
            arcpy.CopyFeatures_management(extractedShp, outputFeatureClass, "", "0", "0", "0")
            output = outputFeatureClass
        elif (wfsDownloadType.lower() == "csv"):
            # Unzip the file to the scratch folder
            arcpy.AddMessage("Translating CSV file...")       

            # Set CSV delimiter                         
            csvDelimiter = ","
            # Open the CSV file
            with open(downloadedFile, 'rb') as csvFile:
                # Read the CSV file
                arcpy.AddMessage("Reading CSV file...")                
                rows = csv.reader(csvFile, delimiter=csvDelimiter)

                # For each row in the CSV
                count = 0
                for row in rows:
                    # Ignore the first line containing headers
                    if (count > 0):
                        # Get the last column - geometry
                        geometryWKT = row[len(row)-1]

                        # Convert to Esri geometry
                        Geometry = arcpy.FromWKT(geometryWKT,arcpy.SpatialReference(4326))

                        # If it's the first feature, create new feature class
                        if (count == 0):
                            arcpy.CopyFeatures_management(Geometry, outputFeatureClass)
                            output = outputFeatureClass
                    count = count + 1                                    
        #json
        else:      
            arcpy.AddMessage("Translating GeoJSON...")       

            # Convert geometry (GeoJSON) to shape - For each feature in GeoJSON
            count = 0        
            for feature in geometryJSON["features"]:
                # Convert to Esri geometry
                Geometry = arcpy.AsShape(feature["geometry"])
       
                # If it's the first feature, create new feature class
                if (count == 0):
                    arcpy.CopyFeatures_management(Geometry, outputFeatureClass)
                    output = outputFeatureClass
                count = count + 1

        # --------------------------------------- End of code --------------------------------------- #  
 
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                arcpy.SetParameterAsText(3, output)
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
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
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
            logMessage.flush()
            logMessage.close()
            logger.handlers = []   
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
    
