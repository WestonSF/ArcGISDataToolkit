#-------------------------------------------------------------
# Name:       WFS Download
# Purpose:    Downloads a dataset from a WFS service. Parameters required:
#             - URL TO WFS Server - e.g. "http://Servername/geoserver/wfs?key=xxx"
#             - WFS Server Version (optional) e.g. "2.0.0", "1.1.0" or "1.0.0"
#             - Layer/table ID - e.g. "layer-319" or "layer-319-changeset"
#             - Data type - e.g. "Layer" or "Table"
#             - Dataset of extent of data to download (optional) e.g.  "C:\Temp\Scratch.gdb\FeatureClass"
#             - Last update file (optional) e.g. "C:\Development\Python for ArcGIS Tools\ArcGIS Data Toolkit\Configuration\WFSDownload-LINZDataServiceRail.json"
#             - Changeset Dataset ID (optional) e.g. "id"
#             - Output Dataset ID (optional) e.g. "id"
#             - WFS download type - e.g. "Shape-Zip", "CSV" or "JSON"
#             - Output workspace - e.g. "C:\Temp\Scratch.gdb"
#             - Dataset name - e.g. "FeatureClass"
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    23/10/2015
# Last Updated:    26/09/2016
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcGIS for Desktop 10.1+ or ArcGIS Pro 1.1+ (Need to be signed into a portal site)
# Python Version:   2.7.10+ or 3.4+
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib

# Set global variables
# Logging
enableLogging = "false" # Use within code - logger.info("Example..."), logger.warning("Example..."), logger.error("Example...") and to print messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
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
# ArcGIS desktop installed
arcgisDesktop = "true"

# If ArcGIS desktop installed
if (arcgisDesktop == "true"):
    # Import extra modules
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
# Python version check
if sys.version_info[0] >= 3:
    # Python 3.x
    import urllib.request as urllib2
else:
    # Python 2.x
    import urllib2
import urllib
import zipfile
import glob
import uuid
import csv
import json
import datetime
import io
import ssl


# Start of main function
def mainFunction(wfsURL,wfsVersion,wfsDataID,dataType,extentDataset,lastUpdateFile,changesetDatasetID,targetDatasetID,wfsDownloadType,outputWorkspace,datasetName): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Get the current record count of the dataset
        if arcpy.Exists(os.path.join(outputWorkspace, datasetName)):
            datasetCount = arcpy.GetCount_management(os.path.join(outputWorkspace, datasetName)) 
            printMessage("Current dataset record count for " + datasetName + " - " + str(datasetCount),"info")
            if (enableLogging == "true"):
                logger.info("Current dataset record count for " + datasetName + " - " + str(datasetCount))

        # Setup the parameters for the request
        wfsRequestDict = {}
        wfsRequestDict['service'] = "wfs"
        wfsRequestDict['request'] = "getfeature"     
        wfsRequestDict['outputformat'] = wfsDownloadType.lower()
        wfsRequestDict['typename'] = wfsDataID  

        # If WFS version number provided
        if wfsVersion:
            # Setup the wfs version parameter
            wfsRequestDict['version'] = wfsVersion

        # Set the spatial reference
        if (dataType.lower() == "layer"):
            # Setup the coordinate system parameter
            wfsRequestDict['srsName'] = 'EPSG:2193'    

        # If a changeset is being requested
        if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
            # Maximum number of days between a changeset to allow
            maxDaysChange = 60
            
            # Get the last updated date
            with io.open(lastUpdateFile) as jsonFile:    
                jsonConfig = json.load(jsonFile)
                lastUpdateDate = datetime.datetime.strptime(jsonConfig["lastUpdated"],"%Y-%m-%dT%H:%M:%S")

            # Get the days between now and the last update
            lastUpdateChange = datetime.datetime.now() - lastUpdateDate

            printMessage("Last update was " + str(lastUpdateChange.days) + " days ago...","info")

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
         
            # Setup the to and from dates for the viewparams parameter
            wfsRequestDict['viewparams'] = "from:" + str(lastUpdateDate) + ";to:" + str(currentDate)  

        # If setting an extent for the data
        if (extentDataset) and (dataType.lower() == "layer"):
            # Get the extent from the feature class
            extentDataDesc = arcpy.Describe(extentDataset)
            extent = extentDataDesc.extent
            
            # Setup the bbox parameter from the extent of the feature class
            wfsRequestDict['bbox'] = str(extent.XMin) + "," + str(extent.YMin) + "," + str(extent.XMax) + "," + str(extent.YMax) + ",EPSG:2193"

        # Setup parameters encoding for export  
        # Python version check
        if sys.version_info[0] >= 3:
            # Python 3.x
            # Encode parameters
            params = urllib.parse.urlencode(wfsRequestDict)
        else:
            # Python 2.x
            # Encode parameters
            params = urllib.urlencode(wfsRequestDict)
        params = params.encode('utf-8')

        # -------------------- Downloading Data --------------------
        printMessage("WFS request made - " + wfsURL + "...","info")
        printMessage("WFS request parameters - " + str(wfsRequestDict) + "...","info")
        if (enableLogging == "true"):
            logger.info("WFS request made - " + wfsURL)
            logger.info("WFS request parameters - " + str(wfsRequestDict))            
        # POST the WFS request
        context = ssl._create_unverified_context()
        requestURL = urllib2.Request(wfsURL,params)
        response = urllib2.urlopen(requestURL, context=context)

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
            printMessage("Downloading data...","info")
            fileChunk = 16 * 1024
            downloadedFile = os.path.join(arcpy.env.scratchFolder, "Data-" + str(uuid.uuid1()) + fileType)
            with open(downloadedFile, 'wb') as file:
                downloadCount = 0
                while True:
                    chunk = response.read(fileChunk)
                    # If data size is small
                    if ((downloadCount == 0) and (len(chunk) < 1000)):
                        # Log error and end download
                        printMessage("No data returned...","warning")  
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
            printMessage("Downloaded to " + downloadedFile + "...","info")

        # -------------------- Extracting Data --------------------
        # Shape file
        if (wfsDownloadType.lower() == "shape-zip"):
            # Unzip the file to the scratch folder
            printMessage("Extracting zip file...","info")
            zip = zipfile.ZipFile(downloadedFile, mode="r")

            zip.extractall(arcpy.env.scratchFolder)

            # Get the extracted shape file
            extractedShp = max(glob.iglob(str(arcpy.env.scratchFolder) + r"\*.shp"), key=os.path.getmtime)

            # Copy to feature class
            printMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...","info")
            if (enableLogging == "true"):
                logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")  
            arcpy.CopyFeatures_management(extractedShp, os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
        # CSV
        elif (wfsDownloadType.lower() == "csv"):
            # Unzip the file to the scratch folder
            printMessage("Translating CSV file...","info")

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

            printMessage(str(numberRecords) + " records downloaded...","info")
            if (enableLogging == "true"):
                logger.info(str(numberRecords) + " records downloaded...")
                
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
                                        arcpy.CreateFeatureclass_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"), geometryType, "", "", "", arcpy.SpatialReference(2193))
                                    # If table
                                    else:
                                        # create new table
                                        arcpy.CreateTable_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"), "")

                                    # Add the fields
                                    for field in fields:
                                        if (field.lower() != "shape@"):
                                            arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), str(field.replace("-", "_")), "TEXT")

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
                                        # Check length of field
                                        fieldLength = len(value)
                                        # Strip field length to be under 250
                                        if (fieldLength > 250):
                                            charsToStrip = fieldLength - 250
                                            value = value[:-charsToStrip] + "..."

                                        # Add each of the values to an array
                                        values.append(str(value))
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
                                cursor = arcpy.da.InsertCursor(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")),fields)
                                cursor.insertRow(values)

                                printMessage("Loaded " + str(count) + " of " + str(numberRecords) + " records...","info")
                        
                        count = count + 1
                # Delete cursor
                del cursor

                # If a changeset is being requested
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Clip to the extent feature class if necessary
                    scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"))
                    if (extentDataset) and (dataType.lower() == "layer"):
                        printMessage("Clipping dataset to extent...","info")
                        if (enableLogging == "true"):
                            logger.info("Clipping dataset to extent...")  
                        scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_") + "_Clip")
                        arcpy.Clip_analysis(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), extentDataset, scratchDataset, "")

                    # Apply changes to target dataset
                    applyChangeset(lastUpdateFile,str(currentDate),scratchDataset,outputWorkspace,os.path.join(outputWorkspace, datasetName),changesetDatasetID,targetDatasetID)

                    # Get the new record count of the dataset
                    datasetCount = arcpy.GetCount_management(os.path.join(outputWorkspace, datasetName)) 
                    printMessage("New dataset record count for " + datasetName + " - " + str(datasetCount),"info")
                    if (enableLogging == "true"):
                        logger.info("New dataset record count for " + datasetName + " - " + str(datasetCount))   
                # Full dataset
                else:
                    printMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...","info")                
                    if (enableLogging == "true"):
                        logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")
                    # If layer
                    if (dataType.lower() == "layer"):
                        # Clip to the extent feature class if necessary
                        scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"))
                        if (extentDataset) and (dataType.lower() == "layer"):
                            printMessage("Clipping dataset to extent...","info")
                            if (enableLogging == "true"):
                                logger.info("Clipping dataset to extent...")  
                            scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_") + "_Clip")
                            arcpy.Clip_analysis(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), extentDataset, scratchDataset, "")

                        arcpy.CopyFeatures_management(scratchDataset, os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
                    # If table
                    else:
                        arcpy.Copy_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), os.path.join(outputWorkspace, datasetName))  
                    # Get the new record count of the dataset
                    datasetCount = arcpy.GetCount_management(os.path.join(outputWorkspace, datasetName)) 
                    printMessage("New dataset record count for " + datasetName + " - " + str(datasetCount),"info")
                    if (enableLogging == "true"):
                        logger.info("New dataset record count for " + datasetName + " - " + str(datasetCount))    
            # No records
            else:
                printMessage("No data returned...","warning")  
                if (enableLogging == "true"):
                    logger.warning("No data returned...")
                # If a changeset
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Update changes config file
                    updateChangesConfig(lastUpdateFile,str(currentDate))
                sys.exit()
        # JSON
        else:      
            printMessage("Translating JSON data...","info")       

            # Convert geometry (GeoJSON) to shape - For each feature in GeoJSON
            numberRecords = len(JSONData["features"])

            printMessage(str(numberRecords) + " records downloaded...","info")
            if (enableLogging == "true"):
                logger.info(str(numberRecords) + " records downloaded...")
                        
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
                            arcpy.CreateFeatureclass_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"), geometryType, "", "", "", arcpy.SpatialReference(2193))
                        # If table
                        else:
                            # create new table
                            arcpy.CreateTable_management(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"), "")

                        # Add the fields
                        for field in fields:
                            if (field.lower() != "shape@"):
                                arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB,wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), str(field.replace("-", "_")), "TEXT")

                    # Add the field values
                    for field in fields:
                        if (field.lower() != "shape@"):
                            # Python version check
                            if sys.version_info[0] >= 3:
                                # Python 3.x
                                value = str(feature["properties"][field]).encode('utf-8').decode('utf-8')
                            else:
                                # Python 2.x
                                value = unicode(feature["properties"][field]).encode('utf-8')
    
                            # Check length of field
                            fieldLength = len(value)
                            # Strip field length to be under 250
                            if (fieldLength > 250):
                                charsToStrip = fieldLength - 250
                                value = value[:-charsToStrip] + "..."

                            # Add each of the values to an array
                            values.append(str(value))

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
                    cursor = arcpy.da.InsertCursor(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")),fields)
                    cursor.insertRow(values)
                    count = count + 1

                    printMessage("Loaded " + str(count) + " of " + str(numberRecords) + " records...","info")
                # Delete cursor
                del cursor
                
                # If a changeset is being requested
                if ("changeset" in wfsDataID.lower()) and (lastUpdateFile):
                    # Clip to the extent feature class if necessary
                    scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"))
                    if (extentDataset) and (dataType.lower() == "layer"):
                        printMessage("Clipping dataset to extent...","info")
                        if (enableLogging == "true"):
                            logger.info("Clipping dataset to extent...")                        
                        scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_") + "_Clip")
                        arcpy.Clip_analysis(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), extentDataset, scratchDataset, "")

                    # Apply changes to target dataset
                    applyChangeset(lastUpdateFile,str(currentDate),scratchDataset,outputWorkspace,os.path.join(outputWorkspace, datasetName),changesetDatasetID,targetDatasetID)

                    # Get the new record count of the dataset
                    datasetCount = arcpy.GetCount_management(os.path.join(outputWorkspace, datasetName)) 
                    printMessage("New dataset record count for " + datasetName + " - " + str(datasetCount),"info")
                    if (enableLogging == "true"):
                        logger.info("New dataset record count for " + datasetName + " - " + str(datasetCount))    
                # Full dataset
                else:
                    printMessage("Copying to " + os.path.join(outputWorkspace, datasetName) + "...","info")                
                    if (enableLogging == "true"):
                        logger.info("Copying to " + os.path.join(outputWorkspace, datasetName) + "...")
                    # If layer
                    if (dataType.lower() == "layer"):
                        # Clip to the extent feature class if necessary
                        scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_"))
                        if (extentDataset) and (dataType.lower() == "layer"):
                            printMessage("Clipping dataset to extent...","info")
                            if (enableLogging == "true"):
                                logger.info("Clipping dataset to extent...")  
                            scratchDataset = os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_") + "_Clip")
                            arcpy.Clip_analysis(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), extentDataset, scratchDataset, "")

                        # Copy over dataset
                        arcpy.CopyFeatures_management(scratchDataset, os.path.join(outputWorkspace, datasetName), "", "0", "0", "0")
                    # If table
                    else:
                        arcpy.Copy_management(os.path.join(arcpy.env.scratchGDB, wfsDataID.replace("-", "_").replace(".", "_").replace("=", "_").replace(":", "_").replace("&", "_")), os.path.join(outputWorkspace, datasetName))
                    # Get the new record count of the dataset
                    datasetCount = arcpy.GetCount_management(os.path.join(outputWorkspace, datasetName)) 
                    printMessage("New dataset record count for " + datasetName + " - " + str(datasetCount),"info")
                    if (enableLogging == "true"):
                        logger.info("New dataset record count for " + datasetName + " - " + str(datasetCount))

        # Execute any custom updates needed on the data
        customUpdates(datasetName)
        # --------------------------------------- End of code --------------------------------------- #
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If ArcGIS desktop installed
                if (arcgisDesktop == "true"):
                    arcpy.SetParameterAsText(1, output)
                # ArcGIS desktop not installed
                else:
                    return output 
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
        printMessage(errorMessage,"error")           
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
        printMessage(errorMessage,"error")
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


# Start of custom updates function
def customUpdates(datasetName):
    ### Custom data update code goes here
    if (datasetName.lower() == "address"):
        # Updating new fields needed for searching - Assumes new fields already added
        arcpy.CalculateField_management("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\Cadastral.SDEADMIN.Address", "fullname", "!address! + \", \" + !locality!", "PYTHON_9.3", "")
        # Rebuild locator
        printMessage("Rebuilding address locator...","info")
        arcpy.RebuildAddressLocator_geocoding("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\SDEADMIN.AddressLocator")       
    if (datasetName.lower() == "road"):
        # Updating new fields needed for searching - Assumes new fields already added
        arcpy.CalculateField_management("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\Cadastral.SDEADMIN.Road", "fullname", "!name! + \", \" + !locality!", "PYTHON_9.3", "")
        # Rebuild locator
        printMessage("Rebuilding road locator...","info")
        arcpy.RebuildAddressLocator_geocoding("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\SDEADMIN.RoadLocator")      
    if (datasetName.lower() == "parcel"):       
        # Merge Masterton, Carterton and South Wairarapa property into one feature class
        arcpy.Merge_management("'" + "\\\\GISDATA\\Data\\Database Connections\\Administrator\\MDC_Core (Admin).sde\\MDC_Core.SDEADMIN.Property';'" + "\\\\GISDATA\\Data\\Database Connections\\Administrator\\CDC_Core (Admin).sde\\CDC_Core.SDEADMIN.Property';'" + "\\\\GISDATA\\Data\\Database Connections\\Administrator\\SWDC_Core (Admin).sde\\SWDC_Core.SDEADMIN.Property'", "\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\Cadastral.SDEADMIN.Property", "")
        datasetCount = arcpy.GetCount_management("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\Cadastral.SDEADMIN.Property")
        printMessage("New dataset record count for Property - " + str(datasetCount),"info")
        if (enableLogging == "true"):
            logger.info("New dataset record count for Property - " + str(datasetCount))                          
        # Rebuild locators
        printMessage("Rebuilding parcel and legal description locators...","info")
        arcpy.RebuildAddressLocator_geocoding("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\SDEADMIN.LegalDescriptionLocator")    
        arcpy.RebuildAddressLocator_geocoding("\\\\GISDATA\\Data\\Database Connections\\Administrator\\Cadastral (Admin).sde\\SDEADMIN.ParcelLocator")
# End of custom updates function


# Start of apply changeset function
def applyChangeset(lastUpdateFile,currentDate,changesetDataset,outputWorkspace,targetDataset,changesetDatasetID,targetDatasetID):
    printMessage("Changeset dataset downloaded to " + changesetDataset + "...","info")                
    if (enableLogging == "true"):
        logger.info("Changeset dataset downloaded to " + changesetDataset + "...")

    # Setup the fields to query
    deleteIDs = []
    fields = ["__change__"]
    fields.append(changesetDatasetID)
    
    # Open change dataset - Find records to be deleted
    printMessage("Identifying records to be deleted...","info")
    with arcpy.da.SearchCursor(changesetDataset,fields) as searchCursor: 
        # For each row in the change dataset
        for row in searchCursor:
            changeID = row[1]
            change = row[0]                       
            # If this row is in the changes dataset and the update is delete or update
            if ((change.lower() == "update") or (change.lower() == "delete")):
                # Add the ID to the deletes list
                deleteIDs.append(str(changeID))

    # Find whether target dataset is versioned or not
    versionedDataset = arcpy.Describe(targetDataset).isVersioned
    # If versioned
    if versionedDataset is True:
        # Start an edit session
        printMessage("Starting an edit session...","info")
        editSession = arcpy.da.Editor(outputWorkspace)
        editSession.startEditing(False, True)
        editSession.startOperation()

    # Open dataset being updated - Delete these records from the target dataset
    printMessage("Deleting records...","info")
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

    # If versioned
    if versionedDataset is True:
        # Stop the edit session and save the changes
        aprintMessage("Stopping the edit session...","info")
        editSession.stopOperation()
        editSession.stopEditing(True)
        
    # Logging
    printMessage("Applied changeset dataset to " + targetDataset + "...","info")
    if (enableLogging == "true"):
        logger.info("Applied changeset dataset to " + targetDataset + "...")

    # Update changes config file
    updateChangesConfig(lastUpdateFile,str(currentDate))
# End of apply changeset function


# Start of update changes config function
def updateChangesConfig(configFile,date):
    printMessage("Updating changes configuration file - " + configFile + "...","info")                
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


# Start of print message function
def printMessage(message,type):
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
        else:
            arcpy.AddMessage(message)
    # ArcGIS desktop not installed
    else:
        print(message)
# End of print message function


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
    printMessage("Sending email...","info")
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
    # If ArcGIS desktop installed
    if (arcgisDesktop == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
    # ArcGIS desktop not installed
    else:
        argv = sys.argv
        # Delete the first argument, which is the script
        del argv[0] 
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