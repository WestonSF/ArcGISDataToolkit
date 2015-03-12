#-------------------------------------------------------------
# Name:       Map Service Download
# Purpose:    Downloads the data used in a map service layer by querying the json
#             and converting to a feature class.        
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/08/2013
# Last Updated:    12/03/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1+
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
def mainFunction(mapService,featureClass): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")

        # --------------------------------------- Start of code --------------------------------------- #        

        # Query the map service to get the number of features as Object IDs
        arcpy.AddMessage("Querying the map service...")
        mapServiceQuery1 = mapService + "/query?where=1%3D1&returnIdsOnly=true&f=pjson"
        urlResponse = urllib.urlopen(mapServiceQuery1);
        # Get json for the response - Object IDs
        mapServiceQuery1JSONData = json.loads(urlResponse.read())
        objectIDs = mapServiceQuery1JSONData["objectIds"]
        objectIDs.sort()

        arcpy.AddMessage("Number of records in the map service - " + str(len(objectIDs)) + "...")       
        maxRequests = 1000
        requestsMade = 0

        # For each record returned        
        for i in range(len(objectIDs)):
            # For every 1000th record
            if ((i % maxRequests) == 0):
                # Create the query
                startObjectID = int(objectIDs[i])
                endObjectID = startObjectID + 1000
                serviceQuery = "OBJECTID >= " + str(startObjectID) + " AND OBJECTID < " + str(endObjectID)

                # Query the map service to get all data     
                mapServiceQuery2 = mapService + "/query?where=" + serviceQuery + "&returnCountOnly=false&returnIdsOnly=false&returnGeometry=true&outFields=*&f=pjson"
                urlResponse = urllib.urlopen(mapServiceQuery2);
                # Get json for feature returned
                mapServiceQuery2JSONData = json.loads(urlResponse.read())
 
                # Get the geometry and create temporary feature class
                arcpy.AddMessage("Converting JSON to feature class...")
                count = 0
                while (len(mapServiceQuery2JSONData["features"]) > count):                
                    GeometryJSON = mapServiceQuery2JSONData["features"][count]["geometry"]
                    # Add spatial reference to geometry
                    SpatialReference = mapServiceQuery2JSONData["spatialReference"]["wkid"]
                    GeometryJSON["spatialReference"] = {'wkid' : SpatialReference}
                    Geometry = arcpy.AsShape(GeometryJSON, "True")

                    # If on the first record and first request
                    if ((count == 0) and (requestsMade == 0)):
                        # If it's the first request, create new feature class
                        arcpy.CopyFeatures_management(Geometry, featureClass)

                        # Reset data
                        arcpy.DeleteFeatures_management(featureClass)
                        
                        # Go through the attributes
                        for key, value in mapServiceQuery2JSONData["features"][count]["attributes"].iteritems():
                            # Add new field - Don't include ArcGIS generated fields
                            if ((key.lower() <> "objectid") and (key.lower() <> "shape.starea()") and (key.lower() <> "shape.stlength()") and (key.lower() <> "shape.area") and (key.lower() <> "shape.len")):
                                arcpy.AddField_management(featureClass, key, "TEXT", "", "", "500")
                    
                    # Get the field names and values
                    fields = ["SHAPE@"]
                    values = [Geometry]
                    
                    for key, value in mapServiceQuery2JSONData["features"][count]["attributes"].iteritems():
                        # Don't include ArcGIS generated fields
                        if ((key.lower() <> "objectid") and (key.lower() <> "shape.starea()") and (key.lower() <> "shape.stlength()") and (key.lower() <> "shape.area") and (key.lower() <> "shape.len")):
                            # Replace invalid characters
                            if "(" in key:
                                key = key.replace("(", "_")
                            if ")" in key:
                                key = key.replace(")", "_")
                            fields.append(key)
                            values.append(value)

                    # Load it into existing feature class
                    cursor = arcpy.da.InsertCursor(featureClass,fields)
                    cursor.insertRow(values)

                    count = count + 1
                    arcpy.AddMessage("Loaded " + str(count+(requestsMade*1000)) + " of " + str(len(objectIDs)) + " features...")

                requestsMade = requestsMade + 1
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