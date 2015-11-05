#-------------------------------------------------------------
# Name:       Map Service Download
# Purpose:    Downloads the data used in a map service layer by querying the json
#             and converting to a feature class.
#             Existing Mode - Will delete and append records, so field names need to be the same.
#             New Mode - Copies data over (including archive datasets if needed). Requires no locks on geodatabase datasets being overwritten.              
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/08/2013
# Last Updated:    05/11/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.3+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import json
import urllib
import urllib2
import uuid

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
def mainFunction(mapServiceLayer,outputFeatureClass,updateMode): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Querying thet map service to get the count of records
        arcpy.AddMessage("Querying the map service...")
        mapServiceQuery1 = mapServiceLayer + "/query?where=1%3D1&returnIdsOnly=true&f=pjson"
        urlResponse = urllib.urlopen(mapServiceQuery1);
        # Get json for the response - Object IDs
        mapServiceQuery1JSONData = json.loads(urlResponse.read())
        objectIDs = mapServiceQuery1JSONData["objectIds"]
        objectIDs.sort()
        arcpy.AddMessage("Number of records in the layer - " + str(len(objectIDs)) + "...")
        # Set the number of records per request and the number of requests that need to be made
        maxRecords = 1000
        requestsToMake = 1 + (len(objectIDs) / maxRecords)

        # For every request
        count = 0
        arcpy.AddMessage("Downloading data to " + arcpy.env.scratchFolder + "...")
        while (int(requestsToMake) > count):
            # Create the query
            startObjectID = int(objectIDs[count*maxRecords])
            # If at the final request
            if (int(requestsToMake) == (count+1)):
                # Get the last object ID
                endObjectID = int(objectIDs[len(objectIDs)])
            else:
                endObjectID = int(objectIDs[startObjectID+maxRecords])
            serviceQuery = "OBJECTID >= " + str(startObjectID) + " AND OBJECTID < " + str(endObjectID)
                
            # Query the map service to data in json format   
            mapServiceQuery2 = mapServiceLayer + "/query?where=" + serviceQuery + "&returnCountOnly=false&returnIdsOnly=false&returnGeometry=true&outFields=*&f=pjson"
            response = urllib2.urlopen(mapServiceQuery2)  
            
            # Download the data
            fileChunk = 16 * 1024
            downloadedFile = os.path.join(arcpy.env.scratchFolder, "Data-" + str(uuid.uuid1()) + ".json")
            with open(downloadedFile, 'wb') as file:
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
                    file.write(chunk)
                    downloadCount = downloadCount + 1
            file.close()
     
            # If it's the first request
            if (count == 0):
                # Create new dataset
                arcpy.JSONToFeatures_conversion(downloadedFile, os.path.join(arcpy.env.scratchGDB, "Dataset"))
            else:
                # Create dataset and load into existing
                arcpy.JSONToFeatures_conversion(downloadedFile, "in_memory\\DatasetTemp")
                arcpy.Append_management("in_memory\\DatasetTemp", os.path.join(arcpy.env.scratchGDB, "Dataset"), "NO_TEST", "", "")           

            # If at the final request
            if (int(requestsToMake) == (count+1)):
                arcpy.AddMessage("Downloaded and converted JSON for " + str(len(objectIDs)) + " of " + str(len(objectIDs)) + " features...")                
            else:
                arcpy.AddMessage("Downloaded and converted JSON for " + str(count*maxRecords) + " of " + str(len(objectIDs)) + " features...")
            count = count + 1
            
        # Convert JSON to feature class
        arcpy.AddMessage("Copying over final dataset...")
        # Overwrite dataset
        if (updateMode.lower() == "new"):
            # Get record count
            recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "Dataset"))
            arcpy.AddMessage("Number of records for " + outputFeatureClass + " - " + str(recordCount))  
            # Logging 
            if (enableLogging == "true"): 
                # Log record count 
                logger.info("Number of records for " + outputFeatureClass + " - " + str(recordCount)) 
            # Load in data 
            if (recordCount > 0): 
                arcpy.CopyFeatures_management(os.path.join(arcpy.env.scratchGDB, "Dataset"), outputFeatureClass, "", "0", "0", "0")
        # Delete and append
        else:
            # Get record count
            recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "Dataset"))
            arcpy.AddMessage("Number of records for " + outputFeatureClass + " - " + str(recordCount))  
            # Logging 
            if (enableLogging == "true"): 
                # Log record count 
                logger.info("Number of records for " + outputFeatureClass + " - " + str(recordCount)) 
            # Load in data 
            if (recordCount > 0): 
                arcpy.DeleteFeatures_management(outputFeatureClass)             
                arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "Dataset"), outputFeatureClass, "NO_TEST", "", "")           
            
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
