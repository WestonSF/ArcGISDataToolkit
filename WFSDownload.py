#-------------------------------------------------------------
# Name:       WFS Download
# Purpose:    Downloads a dataset from a WFS service. Parameters required:
#             - URL TO WFS Server - e.g. "http://Servername/geoserver/wfs?key=xxx"
#             - Layer/table ID - e.g. "layer-319" or "layer-319-changeset"
#             - Data type - e.g. "Layer" or "Table"
#             - Extent of data to download e.g. 1707030,5390440,1909170,5508180,EPSG:2193
#             - Last update file e.g. "C:\Development\Python for ArcGIS Tools\ArcGIS Data Toolkit\Configuration\WFSDownload-LINZDataServiceRail.json"
#             - Changeset Dataset ID e.g. "id"
#             - Output Dataset ID e.g. "id"
#             - WFS download type - e.g. "Shape-Zip", "CSV" or "JSON"
#             - Output workspace - e.g. "C:\Temp\Scratch.gdb"
#             - Dataset name - e.g. "FeatureClass"
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    23/10/2015
# Last Updated:    13/01/2016
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcGIS for Desktop 10.1+ or ArcGIS Pro 1.1+ (Need to be signed into a portal site)
# Python Version:   2.7 or 3.4
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2  
import arcpy
import zipfile
import glob
import uuid
import csv
import json
import datetime
import io

# Enable data to be overwritten
arcpy.env.overwriteOutput = True
            
# Set global variables
# Logging
enableLogging = "false" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = "" # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email logging
sendErrorEmail = "false"
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = 0 # e.g. 25
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None

# Start of main function
def mainFunction(wfsURL,wfsDataID,dataType,extent,lastUpdateFile,changesetDatasetID,targetDatasetID,wfsDownloadType,outputWorkspace,datasetName): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Check the URL parameters
        if "?" in wfsURL:
            # If first parameter already provided
            firstParameter = "&"
        else:
            firstParameter = "?"           

        # Setup the request URL
        requestURL = wfsURL + firstParameter + "SERVICE=WFS&REQUEST=GetFeature&TYPENAME=" + wfsDataID
        
        # If setting an extent for the data
        if ((len(extent) > 0) and (dataType.lower() == "layer")):
            # Add the bounding box to the request
            requestURL = requestURL + "&bbox=" + str(extent)

        # Set the spatial reference
        if (dataType.lower() == "layer"):
            requestURL = requestURL + "&srsName=EPSG:2193"

        # If a changeset is being requested
        if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
            # Maximum number of days between a changeset to allow
            maxDaysChange = 30
            
            # Get the last updated date
            with io.open(lastUpdateFile) as jsonFile:    
                jsonConfig = json.load(jsonFile)
                lastUpdateDate = datetime.datetime.strptime(jsonConfig["lastUpdated"],"%Y-%m-%dT%H:%M:%S")

            # Get the days between now and the last update
            lastUpdateChange = datetime.datetime.now() - lastUpdateDate

            arcpy.AddMessage("Last update was " + str(lastUpdateChange.days) + " days ago...")

            # If last update date is less than the max days change variable
            if (lastUpdateChange.days <= maxDaysChange):
                # Get the current date as a string
                currentDate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                lastUpdateDate = lastUpdateDate.strftime("%Y-%m-%dT%H:%M:%S")
            # Last update date more than the max days change variable
            else:
                # Set current date to be the max days change variable more than the last update date
                currentDate = (lastUpdateDate + datetime.timedelta(days=maxDaysChange)).strftime("%Y-%m-%dT%H:%M:%S")
                lastUpdateDate = lastUpdateDate.strftime("%Y-%m-%dT%H:%M:%S")
         
            # Setup the to and from dates for the changeset
            requestURL = requestURL + "&viewparams=from:" + str(lastUpdateDate) + ";to:" + str(currentDate)          

        # Set the output request parameter
        requestURL = requestURL + "&outputformat=" + wfsDownloadType

        # -------------------- Downloading Data --------------------
        arcpy.AddMessage("WFS request made - " + requestURL)
        urllib2.urlopen(requestURL)
        response = urllib2.urlopen(requestURL)
        
        # Shape file
        if (wfsDownloadType.lower() == "shape-zip"):
            fileType = ".zip"
        # CSV
        elif (wfsDownloadType.lower() == "csv"):
            fileType = ".csv"
        # JSON   
        else:
            # Python version check
            if sys.version_info[0] >= 3:
                # Python 3.x
                # Read json response
                JSONData = json.loads(response.read().decode('utf8'))
            else:
                # Python 2.x
                # Read json response
                JSONData = json.loads(response.read())

        # Shape file or CSV
        if ((wfsDownloadType.lower() == "shape-zip") or (wfsDownloadType.lower() == "csv")):
            # Download the data
            arcpy.AddMessage("Downloading data...")
            fileChunk = 16 * 1024
            downloadedFile = os.path.join(arcpy.env.scratchFolder, "Data-" + str(uuid.uuid1()) + fileType)
            with open(downloadedFile, 'wb') as file:
                downloadCount = 0
                while True:
                    chunk = response.read(fileChunk)
                    # If data size is small
                    if ((downloadCount == 0) and (len(chunk) < 1000)):
                        # Log error and end download
                        arcpy.AddWarning("No data returned...")  
                        if (enableLogging == "true"):
                            logger.warning("No data returned...")
                        # If a changeset
                        if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                            # Update changes config file
                            updateChangesConfig(lastUpdateFile,str(currentDate))
                        sys.exit()
                    if not chunk:
                        break
                    # Write chunk to output file
                    file.write(chunk)
                    downloadCount = downloadCount + 1
            file.close()
            arcpy.AddMessage("Downloaded to " + downloadedFile + "...")

        # -------------------- Extracting Data --------------------
        # Shape file
        if (wfsDownloadType.lower() == "shape-zip"):
            # Unzip the file to the scratch folder
            arcpy.AddMessage("Extracting zip file...")
            zip = zipfile.ZipFile(downloadedFile, mode="r")

            zip.extractall(arcpy.env.scratchFolder)

            # Get the extracted shape file
            extractedShp = max(glob.iglob(str(arcpy.env.scratchFolder) + r"\*.shp"), key=os.path.getmtime)

            # Copy to feature class
            arcpy.AddMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")
            if (enableLogging == "true"):
                logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")  
            arcpy.CopyFeatures_management(extractedShp, os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
        # CSV
        elif (wfsDownloadType.lower() == "csv"):
            # Unzip the file to the scratch folder
            arcpy.AddMessage("Translating CSV file...")

            # Set the max size of the csv fields
            csv.field_size_limit(10000000)

            # Set CSV delimiter                         
            csvDelimiter = ","

            # Count number of records in CSV
            with io.open(downloadedFile, 'rt', encoding='utf-8') as csvFile:
                # Python version check
                if sys.version_info[0] >= 3:
                    # Python 3.x
                    numberRecords = sum(1 for row in csv.reader(csvFile, delimiter=csvDelimiter)) - 1
                else:
                    # Python 2.x
                    # Read in CSV data as unicode
                    def unicodeEncoder(csvData):
                        for row in csvData:
                            yield row.encode('utf-8')
                    numberRecords = sum(1 for row in csv.reader(unicodeEncoder(csvFile), delimiter=csvDelimiter)) - 1

            arcpy.AddMessage(str(numberRecords) + " records to load...")
            if (enableLogging == "true"):
                logger.info(str(numberRecords) + " records to load...")
                
            # If there are some records
            if (numberRecords > 0):            
                # Open the CSV file
                with io.open(downloadedFile, 'rt', encoding='utf-8') as csvFile:
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        rows = csv.reader(csvFile, delimiter=csvDelimiter)
                    else:
                        # Python 2.x
                        # Read in CSV data as unicode
                        def unicodeEncoder(csvData):
                            for row in csvData:
                                yield row.encode('utf-8')
                        rows = csv.reader(unicodeEncoder(csvFile), delimiter=csvDelimiter)

                    # For each row in the CSV
                    count = 0
                    fields = []
                    for row in rows:
                        # If at the header line
                        if (count == 0):
                            # For each field
                            for field in row:
                                # Add each of the fields to an array
                                if ((field.lower() != "geometry") and (field.lower() != "shape")):
                                    fields.append(field)
                            if (dataType.lower() == "layer"):
                                fields.append("SHAPE@")                                
                                    
                        # For each row after the header
                        else:
                            values = []

                            if (dataType.lower() == "layer"):
                                # Get the last column - geometry
                                geometryWKT = row[len(row)-1]

                                # If geometry not null
                                if (geometryWKT):
                                    # Convert to Esri geometry
                                    Geometry = arcpy.FromWKT(geometryWKT,arcpy.SpatialReference(2193))
                                    
                            # If table or geometry not null
                            if ((dataType.lower() == "table") or (geometryWKT)):    
                                # If it's the first feature, create new feature class
                                if (count == 1):
                                    # If layer
                                    if (dataType.lower() == "layer"):
                                        # Create temporary feature class to get shape type
                                        arcpy.CopyFeatures_management(Geometry, "in_memory\outputDataset")                   
                                        geometryType = arcpy.Describe("in_memory\outputDataset").shapeType
                                        # Create new feature class
                                        arcpy.CreateFeatureclass_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_"), geometryType, "", "", "", arcpy.SpatialReference(2193))
                                    # If table
                                    else:
                                        # create new table
                                        arcpy.CreateTable_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_"), "")

                                    # Add the fields
                                    for field in fields:
                                        if (field.lower() != "shape@"):
                                            arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), str(field.replace("-", "_")), "TEXT")

                                # Add the field values
                                valueCount = 0
                                for value in row:
                                    # If layer
                                    if (dataType.lower() == "layer"):
                                        # Get the number of columns
                                        columnLength = len(row)-1
                                    else:
                                        # Get the number of columns
                                        columnLength = len(row)
                                        
                                    # If it's not the last column - geometry
                                    if (valueCount != columnLength):                            
                                        # Add each of the values to an array
                                        values.append(value)
                                    valueCount = valueCount + 1
                                    
                                if (dataType.lower() == "layer"):
                                    # If geometry not null
                                    if (geometryWKT):
                                        # Add in the geometry
                                        values.append(Geometry)             
                                    # Blank geometry
                                    else:
                                        # Create a blank geometry
                                        if (geometryType.lower() == "point"):    
                                            Geometry = arcpy.PointGeometry(arcpy.Point(None))
                                        if (geometryType.lower() == "polygon"):
                                            Geometry = arcpy.Polygon(arcpy.Array(None))
                                        else:
                                            Geometry = arcpy.Polyline(arcpy.Array(None))
                                        # Add in the geometry
                                        values.append(Geometry)

                                # Load it into existing feature class
                                cursor = arcpy.da.InsertCursor(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")),fields)
                                cursor.insertRow(values)

                                arcpy.AddMessage("Loaded " + str(count) + " of " + str(numberRecords) + " records...")
                        
                        count = count + 1
                # Delete cursor
                del cursor

                # If a changeset is being requested
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Apply changes to target dataset
                    applyChangeset(lastUpdateFile,str(currentDate),os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")),os.path.join(outputWorkspace, datasetName),changesetDatasetID,targetDatasetID)            
                # Full dataset
                else:
                    arcpy.AddMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")                
                    if (enableLogging == "true"):
                        logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")
                    # If layer
                    if (dataType.lower() == "layer"):                
                        arcpy.CopyFeatures_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
                    # If table
                    else:
                        arcpy.Copy_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), os.path.join(outputWorkspace, datasetName))  
            # No records
            else:
                arcpy.AddWarning("No data returned...")  
                if (enableLogging == "true"):
                    logger.warning("No data returned...")
                # If a changeset
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Update changes config file
                    updateChangesConfig(lastUpdateFile,str(currentDate))
                sys.exit()
        # JSON
        else:      
            arcpy.AddMessage("Translating JSON data...")       

            # Convert geometry (GeoJSON) to shape - For each feature in GeoJSON
            numberRecords = len(JSONData["features"])

            arcpy.AddMessage(str(numberRecords) + " records to load...")
            if (enableLogging == "true"):
                logger.info(str(numberRecords) + " records to load...")
                        
            # If there are some records
            if (numberRecords > 0):
                count = 0
                fields = []
                for feature in JSONData["features"]:
                    values = []

                    if (dataType.lower() == "layer"):         
                        # If geometry not null
                        if (feature["geometry"]):
                            # Convert to Esri geometry
                            Geometry = arcpy.AsShape(feature["geometry"])
                            
                    # If it's the first feature, create new feature class
                    if (count == 0):
                        # Get the fields
                        for field in feature["properties"]:
                            fields.append(field)
                        if (dataType.lower() == "layer"):                        
                            fields.append("SHAPE@")

                        # If layer
                        if (dataType.lower() == "layer"):                     
                            # Create temporary feature class to get shape type
                            arcpy.CopyFeatures_management(Geometry, "in_memory\outputDataset")                   
                            geometryType = arcpy.Describe("in_memory\outputDataset").shapeType
                            # Create new feature class  
                            arcpy.CreateFeatureclass_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_"), geometryType, "", "", "", arcpy.SpatialReference(2193))
                        # If table
                        else:
                            # create new table
                            arcpy.CreateTable_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_"), "")

                        # Add the fields
                        for field in fields:
                            if (field.lower() != "shape@"):
                                arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), str(field.replace("-", "_")), "TEXT")

                    # Add the field values
                    for field in fields:
                        if (field.lower() != "shape@"):
                            # Add each of the values to an array
                            values.append(feature["properties"][field])

                    if (dataType.lower() == "layer"):
                        # If geometry not null
                        if (feature["geometry"]):
                            # Add in the geometry
                            values.append(Geometry)             
                        # Blank geometry
                        else:
                            # Create a blank geometry
                            if (geometryType.lower() == "point"):    
                                Geometry = arcpy.PointGeometry(arcpy.Point(None))
                            if (geometryType.lower() == "polygon"):
                                Geometry = arcpy.Polygon(arcpy.Array(None))
                            else:
                                Geometry = arcpy.Polyline(arcpy.Array(None))
                            # Add in the geometry
                            values.append(Geometry)

                    # Load it into existing feature class
                    cursor = arcpy.da.InsertCursor(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")),fields)
                    cursor.insertRow(values)
                        
                    count = count + 1

                    arcpy.AddMessage("Loaded " + str(count) + " of " + str(numberRecords) + " records...")
                # Delete cursor
                del cursor
                
                # If a changeset is being requested
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Apply changes to target dataset
                    applyChangeset(lastUpdateFile,str(currentDate),os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")),os.path.join(outputWorkspace, datasetName),changesetDatasetID,targetDatasetID)
                # Full dataset
                else:
                    arcpy.AddMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")                
                    if (enableLogging == "true"):
                        logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")
                    # If layer
                    if (dataType.lower() == "layer"):                
                        arcpy.CopyFeatures_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
                    # If table
                    else:
                        arcpy.Copy_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_")), os.path.join(outputWorkspace, datasetName))
                    
        # --------------------------------------- End of code --------------------------------------- #  
            # No records
            else:
                arcpy.AddWarning("No data returned...")  
                if (enableLogging == "true"):
                    logger.warning("No data returned...")
                # If a changeset
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Update changes config file
                    updateChangesConfig(lastUpdateFile,str(currentDate))
                sys.exit()
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
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):        
                if (i == 0):
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = unicode(e.args[i]).encode('utf-8')
                else:
                    # Python version check
                    if sys.version_info[0] >= 3:
                        # Python 3.x
                        errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
                    else:
                        # Python 2.x
                        errorMessage = errorMessage + " " + unicode(e.args[i]).encode('utf-8')
        # Else just one argument
        else:
            errorMessage = e
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


# Start of apply changeset function
def applyChangeset(lastUpdateFile,currentDate,changesetDataset,targetDataset,changesetDatasetID,targetDatasetID):
    arcpy.AddMessage("Changeset dataset downloaded to " + changesetDataset + "...")                
    if (enableLogging == "true"):
        logger.info("Changeset dataset downloaded to " + changesetDataset + "...")

    # Setup the fields to query
    deleteIDs = []
    fields = ["__change__"]
    fields.append(changesetDatasetID)
    
    # Open change dataset - Find records to be deleted
    arcpy.AddMessage("Identifying records to be deleted...")
    with arcpy.da.SearchCursor(changesetDataset,fields) as searchCursor: 
        # For each row in the change dataset
        for row in searchCursor:
            changeID = row[1]
            change = row[0]                       
            # If this row is in the changes dataset and the update is delete or update
            if ((change.lower() == "update") or (change.lower() == "delete")):
                # Add the ID to the deletes list
                deleteIDs.append(str(changeID))
              
    # Open dataset being updated - Delete these records from the target dataset
    arcpy.AddMessage("Deleting records...")
    with arcpy.da.UpdateCursor(targetDataset,targetDatasetID) as updateCursor:
        # For each row in the dataset
        for row in updateCursor:
            datasetID = row[0]
            # If record is in delete list
            if str(datasetID) in deleteIDs:
                # Delete the record from the dataset being updated
                updateCursor.deleteRow()

    # Open change dataset - Delete the delete records
    with arcpy.da.UpdateCursor(changesetDataset,"__change__") as updateCursorChange:
        # For each row in the change dataset
        for row in updateCursorChange:
            change = row[0]
            # If this row is a delete
            if (change.lower() == "delete"):
                # Delete the record from the change dataset
                updateCursorChange.deleteRow()
                          
    # Delete cursor objects
    del updateCursor, updateCursorChange, searchCursor

    # Append in all the new data from the change dataset - All records with add or update, assuming all field names are the same
    arcpy.AddMessage("Loading in new records...")
    arcpy.Append_management(changesetDataset, targetDataset, "NO_TEST", "", "")

    # Logging
    arcpy.AddMessage("Applied changeset dataset to " + targetDataset + "...")
    if (enableLogging == "true"):
        logger.info("Applied changeset dataset to " + targetDataset + "...")

    # Update changes config file
    updateChangesConfig(lastUpdateFile,str(currentDate))
# End of apply changeset function


# Start of update changes config function
def updateChangesConfig(configFile,date):
    arcpy.AddMessage("Updating changes configuration file - " + configFile + "...")                
    if (enableLogging == "true"):
        logger.info("Updating changes configuration file - " + configFile + "...")

    # Read json data from file
    with open(configFile, "r") as jsonFile:
        data = json.load(jsonFile)

    # Update the last updated date
    tmp = data["lastUpdated"]
    data["lastUpdated"] = date

    # Write new date back into json file
    with open(configFile, "w") as jsonFile:
        jsonFile.write(json.dumps(data))
# End of update changes config function


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
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort) 
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