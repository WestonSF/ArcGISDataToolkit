#-------------------------------------------------------------
# Name:       NZAA ArchSite Data Download
# Purpose:    Downloads archaeological data from the NZAA ArchSite and loads it into a database. 
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    22/05/2015
# Last Updated:    25/05/2015
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
import json
import urllib
import urllib2
import zipfile
import glob
import shutil

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
def mainFunction(username,password,dataFormat,outputLocation,updateMode): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        
        # Setup the parameters
        gpService = "https://nzaa.eaglegis.co.nz/arcgis/rest/services/NZAAExportSitesTool/GPServer/NZAA%20Export%20Sites%20Tool"
        sdeConnectionOnServer = "D:\Data\Database Connections\NZAA (Viewer).sde"
        # If geodatabase
        if (dataFormat.lower() == "file geodatabase"):
            dataFormat = "gdb"
        else:
            dataFormat = "shp"

        # Get a token as it's a secure service
        token = getToken(username, password, "nzaa.eaglegis.co.nz", "80")
        
        # Query the gp service with the parameters
        arcpy.AddMessage("Querying the GP service...")
        gpServiceQuery = gpService + "/execute?User_Name=" + username + "&Output_Format=" + dataFormat + "&Connection_SDE=" + sdeConnectionOnServer + "&token=" + token + "&f=pjson"        
        urlResponse = urllib.urlopen(gpServiceQuery);

        # Get json for the response
        gpServiceQueryJSONData = json.loads(urlResponse.read())
        gpResultValue = gpServiceQueryJSONData["results"][0]["value"]
        downloadLink = "https://nzaa.eaglegis.co.nz/NZAAExports/" + username + "/" + gpResultValue

        arcpy.AddMessage("Downloading the data...")
        # Download the file from the link
        file = urllib2.urlopen(downloadLink)
        # Download in chunks
        fileChunk = 16 * 1024
        with open(os.path.join(arcpy.env.scratchFolder, "Data.zip"), 'wb') as output:
            while True:
                chunk = file.read(fileChunk)
                if not chunk:
                    break
                # Write chunk to output file
                output.write(chunk)
        output.close()

        # Unzip the file to the scratch folder
        arcpy.AddMessage("Extracting zip file...")  
        zip = zipfile.ZipFile(os.path.join(arcpy.env.scratchFolder, "Data.zip"), mode="r")
        zip.extractall(arcpy.env.scratchFolder)

        # Get the newest unzipped folder from the scratch folder
        dirs = []
        # For each file or folder extracted
        for file in os.listdir(arcpy.env.scratchFolder):
            filePath = os.path.join(arcpy.env.scratchFolder, file)
            if os.path.isdir(filePath):
                # Append the folders into a list
                dirs.append(filePath)
        unzippedFolder = max(dirs, key=os.path.getmtime)

        # If geodatabase
        if (dataFormat.lower() == "gdb"):
            # Get the newest unzipped database from the scratch folder
            workspace = max(glob.iglob(unzippedFolder + r"\*.gdb"), key=os.path.getmtime)
        else:
            workspace = unzippedFolder
            
        # Assign the geodatabase workspace and load in the datasets to the lists
        arcpy.env.workspace = workspace
        featureclassList = arcpy.ListFeatureClasses()
        tableList = arcpy.ListTables()

        arcpy.AddMessage("Copying datasets...")        
        # Load the feature classes into the geodatabase if at least one is in the geodatabase provided
        if (len(featureclassList) > 0):        
            # Loop through the feature classes
            for eachFeatureclass in featureclassList:
               # Check output location
               outputLocationDetails = arcpy.Describe(outputLocation)
               if (outputLocationDetails.workspaceType.lower() == "filesystem"):
                   datasetName = eachFeatureclass
               else:
                   datasetName = eachFeatureclass.replace(".shp", "")                   
            
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):
                   # Copy feature class into geodatabase using the same dataset name
                   arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(outputLocation, datasetName), "", "0", "0", "0")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(outputLocation, datasetName)):
                        arcpy.DeleteFeatures_management(os.path.join(outputLocation, datasetName))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(outputLocation, datasetName), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddWarning("Warning: " + os.path.join(outputLocation, datasetName) + " does not exist and won't be updated")

        # Delete the workspace
        if os.path.exists(unzippedFolder):
            shutil.rmtree(unzippedFolder)
        
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


# Start of get token function
def getToken(username, password, serverName, serverPort):
    query_dict = {'username':   username,
                  'password':   password,
                  'expiration': "60",
                  'client':     'requestip'}
    
    query_string = urllib.urlencode(query_dict)
    url = "http://{}:{}/arcgis/tokens/generateToken?f=json".format(serverName, serverPort)
   
    try:
        token = json.loads(urllib2.urlopen(url, query_string).read())
        if "token" not in token or token == None:
            arcpy.AddError("Failed to get token, return message from server:")
            arcpy.AddError(token['messages'])            
            # Logging
            if (enableLogging == "true"):   
                logger.error("Failed to get token, return message from server:")
                logger.error(token['messages'])                
            sys.exit()
        else:
            # Return the token to the function which called for it
            return token['token']
    
    except urllib2.URLError, error:
        arcpy.AddError("Could not connect to machine {} on port {}".format(serverName, serverPort))
        arcpy.AddError(error)
        # Logging
        if (enableLogging == "true"):   
            logger.error("Could not connect to machine {} on port {}".format(serverName, serverPort))
            logger.error(error)         
        sys.exit()
# End of get token function


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
    
