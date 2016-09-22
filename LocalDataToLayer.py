#-------------------------------------------------------------
# Name:       Local Data to Layer
# Purpose:    Converts CSV, Excel, GPX, KML or shapefile to a layer.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    27/06/2016
# Last Updated:    20/07/2016
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   ArcMap 10.3+
# Python Version:   2.7
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
import zipfile
import uuid
import glob


# Start of main function
def mainFunction(dataFile,geometryType,inputCoordinateSystemName,outputCoordinateSystemName,xField,yField,spreadsheetUniqueID,output): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Get coordinate systems and transformation
        inputCoordinateSystem,outputCoordinateSystem,transformation = getCoordinateDetails(inputCoordinateSystemName,outputCoordinateSystemName)

        # If url set as data file
        urlCheck = ['http', 'https']
        if any(file in dataFile for file in urlCheck):
            printMessage("Downloading file from - " + dataFile + "...","info")
            # Download the file from the link
            file = urllib2.urlopen(dataFile)
            fileName, fileExt = os.path.splitext(dataFile)
            # Download in chunks
            fileChunk = 16 * 1024
            with open(os.path.join(arcpy.env.scratchFolder, "Data" + fileExt), 'wb') as output:
                while True:
                    chunk = file.read(fileChunk)
                    if not chunk:
                        break
                    # Write chunk to output file
                    output.write(chunk)
            output.close()
            dataFile = os.path.join(arcpy.env.scratchFolder, "Data" + fileExt)

        # If data type is excel
        if dataFile.lower().endswith(('.xls', '.xlsx')):
            # If x and y fields provided
            if ((xField) and (yField)):
                # Get geometry type - line or polygon
                if ((geometryType.lower() == "line") or (geometryType.lower() == "polygon")):
                    # If unique Id provided
                    if (spreadsheetUniqueID):
                        # Call function to get layer from spreadsheet
                        output = spreadsheetToLinePolygon(dataFile,geometryType,xField,yField,spreadsheetUniqueID,inputCoordinateSystemName,inputCoordinateSystem,outputCoordinateSystemName,outputCoordinateSystem,transformation)
                    else:
                        printMessage("Please provide a ID field in the spreadsheet to uniquely identify each feature...","error")
                        sys.exit()
                # Get geometry type - point
                else:
                    # If projection needed
                    if (transformation.lower() != "none"):
                        printMessage("Importing Excel sheet...","info")
                        arcpy.ExcelToTable_conversion(dataFile, "in_memory\\Dataset", "")
                        arcpy.MakeXYEventLayer_management("in_memory\\Dataset", xField, yField, "InputLayer", inputCoordinateSystem, "")
                        printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
                        arcpy.Project_management("InputLayer", os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
                        printMessage("Creating layer...","info")
                        output = arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), "Layer", "", "", "")
                    else:
                        printMessage("Importing Excel sheet...","info")
                        arcpy.ExcelToTable_conversion(dataFile, "in_memory\\Dataset", "")
                        printMessage("Creating layer...","info")
                        output = arcpy.MakeXYEventLayer_management("in_memory\\Dataset", xField, yField, "Layer", inputCoordinateSystem, "")
            else:
                printMessage("Please provide an X and Y field for the Excel file...","error")
                sys.exit()
        # If data type is shapefile
        elif dataFile.lower().endswith('.zip'):
            printMessage("Importing Shapefile...","info")         
            # Extract the zip file to a temporary location
            zip = zipfile.ZipFile(dataFile, mode="r")
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "Data-" + str(uuid.uuid1()))
            zip.extractall(str(tempFolder))
            # Get the extracted shapefile
            shapefile = max(glob.iglob(str(tempFolder) + r"\*.shp"), key=os.path.getmtime)
            # If projection needed
            if (transformation.lower() != "none"):
                printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
                arcpy.Project_management(shapefile, os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
                printMessage("Creating layer...","info")
                output = arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), "Layer", "", "", "")
            else:
                printMessage("Creating layer...","info")
                output = arcpy.MakeFeatureLayer_management(shapefile, "Layer", "", "", "")
        # If data type is gpx
        elif dataFile.lower().endswith('.gpx'):
            printMessage("Importing GPX...","info")
            arcpy.GPXtoFeatures_conversion(dataFile, "in_memory\\Dataset")
            # If projection needed
            if (transformation.lower() != "none"):
                printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
                arcpy.Project_management("in_memory\\Dataset", os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
                printMessage("Creating layer...","info")
                output = arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), "Layer", "", "", "")
            else:
                printMessage("Creating layer...","info")
                output = arcpy.MakeFeatureLayer_management("in_memory\\Dataset", "Layer", "", "", "")
        # If data type is kml
        elif dataFile.lower().endswith(('.kml', '.kmz')):
            # If kml geometry type provided
            if (geometryType):
                printMessage("Importing KML...","info")
                arcpy.KMLToLayer_conversion(dataFile, arcpy.env.scratchFolder, "KML", "NO_GROUNDOVERLAY")
                outputGeodatabase = os.path.join(arcpy.env.scratchFolder,"KML.gdb")

                # Get the kml dataset as specified
                if (geometryType.lower() == "line"):
                    kmlDataset = os.path.join(outputGeodatabase,"Placemarks\Polylines")
                elif (geometryType.lower() == "polygon"):
                    kmlDataset = os.path.join(outputGeodatabase,"Placemarks\Polygons")                
                else:
                    kmlDataset = os.path.join(outputGeodatabase,"Placemarks\Points")  
                # If projection needed
                if (transformation.lower() != "none"):
                    printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
                    arcpy.Project_management(kmlDataset, os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
                    printMessage("Creating layer...","info")
                    output = arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), "Layer", "", "", "")
                else:
                    printMessage("Creating layer...","info")
                    output = arcpy.MakeFeatureLayer_management(kmlDataset, "Layer", "", "", "")
            else:
                printMessage("Please provide a geometry type for the KML file...","error")
                sys.exit()
        # If data type is csv
        elif dataFile.lower().endswith('.csv'):
            # If x and y fields provided
            if ((xField) and (yField)):
                # Get geometry type - line or polygon
                if ((geometryType.lower() == "line") or (geometryType.lower() == "polygon")):
                    # If unique Id provided
                    if (spreadsheetUniqueID):
                        # Call function to get layer from spreadsheet
                        output = spreadsheetToLinePolygon(dataFile,geometryType,xField,yField,spreadsheetUniqueID,inputCoordinateSystemName,inputCoordinateSystem,outputCoordinateSystemName,outputCoordinateSystem,transformation)
                    else:
                        printMessage("Please provide a ID field in the spreadsheet to uniquely identify each feature...","error")
                        sys.exit()
                # Get geometry type - point
                else:
                    # If projection needed
                    if (transformation.lower() != "none"):
                        printMessage("Importing CSV...","info")
                        arcpy.MakeXYEventLayer_management(dataFile, xField, yField, "InputLayer", inputCoordinateSystem, "")
                        printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
                        arcpy.Project_management("InputLayer", os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
                        printMessage("Creating layer...","info")
                        output = arcpy.MakeFeatureLayer_management(os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), "Layer", "", "", "")
                    else:
                        printMessage("Importing CSV...","info")
                        printMessage("Creating layer...","info")
                        output = arcpy.MakeXYEventLayer_management(dataFile, xField, yField, "Layer", inputCoordinateSystem, "")
            else:
                printMessage("Please provide an X and Y field for the CSV file...","error")
                sys.exit()
        else:
            printMessage("Not a valid data file. Please use .csv,.xls,.xlsx,.zip,.gpx,.kml or .kmz...","error")
            sys.exit()
                
        # --------------------------------------- End of code --------------------------------------- #
        # If called from gp tool return the arcpy parameter   
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If ArcGIS desktop installed
                if (arcgisDesktop == "true"):
                    arcpy.SetParameter(7, output)
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


# Start of spreadsheet to line and polygon function
def spreadsheetToLinePolygon(dataFile,geometryType,xField,yField,spreadsheetUniqueID,inputCoordinateSystemName,inputCoordinateSystem,outputCoordinateSystemName,outputCoordinateSystem,transformation):
    # If excel spreadsheet
    if dataFile.lower().endswith(('.xls', '.xlsx')):
        dataFile = arcpy.ExcelToTable_conversion(dataFile, "in_memory\\DatasetExcel", "")

    # If projection needed
    if (transformation.lower() != "none"):
        printMessage("Importing CSV/Excel...","info")
        arcpy.MakeXYEventLayer_management(dataFile, xField, yField, "InputLayer", inputCoordinateSystem, "")
        printMessage("Projecting layer from " + inputCoordinateSystemName + " to " + outputCoordinateSystemName + "...","info")
        arcpy.Project_management("InputLayer", os.path.join(arcpy.env.scratchGDB,"Layer_Projected"), outputCoordinateSystem, transformation, inputCoordinateSystem, "NO_PRESERVE_SHAPE", "")
    else:
        printMessage("Importing CSV/Excel...","info")
        arcpy.MakeXYEventLayer_management(dataFile, xField, yField, "Layer", inputCoordinateSystem, "")
        arcpy.CopyFeatures_management("Layer", "in_memory\\Dataset", "", "0", "0", "0")
        
    if (transformation.lower() != "none"):
        dataset = os.path.join(arcpy.env.scratchGDB,"Layer_Projected")
    else:
        dataset = "in_memory\\Dataset"
        
    printMessage("Creating layer...","info")
    if (geometryType.lower() == "line"):
        # Convert the points to lines using the unique identifier field to create each unique line
        arcpy.PointsToLine_management(dataset, "in_memory\\DatasetLine", spreadsheetUniqueID, "", "NO_CLOSE")
        output = arcpy.MakeFeatureLayer_management("in_memory\\DatasetLine", "Layer", "", "", "")
    if (geometryType.lower() == "polygon"):
        # Convert the points to lines using the unique identifier field to create each unique line, then close the final line
        arcpy.PointsToLine_management(dataset, "in_memory\\DatasetLine", spreadsheetUniqueID, "", "CLOSE")
        # Convert the lines to polygons and join on attribute from lines
        arcpy.FeatureToPolygon_management("in_memory\\DatasetLine", "in_memory\\DatasetPolygon", "", "ATTRIBUTES", "")
        arcpy.JoinField_management("in_memory\\DatasetPolygon", "OID", "in_memory\\DatasetLine", "OID", spreadsheetUniqueID)
        output = arcpy.MakeFeatureLayer_management("in_memory\\DatasetPolygon", "Layer", "", "", "")        
    return output
# End of spreadsheet to line and polygon function


# Start of get coordinate system details function
def getCoordinateDetails(inputCoordinateSystemName,outputCoordinateSystemName):
    # Get the input coordinate system
    if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
        inputCoordinateSystem  = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
    if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
        inputCoordinateSystem  = "PROJCS['NZGD_2000_New_Zealand_Transverse_Mercator',GEOGCS['GCS_NZGD_2000',DATUM['D_NZGD_2000',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',1600000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',173.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
    if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
        inputCoordinateSystem  = "PROJCS['GD_1949_New_Zealand_Map_Grid',GEOGCS['GCS_New_Zealand_1949',DATUM['D_New_Zealand_1949',SPHEROID['International_1924',6378388.0,297.0]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['New_Zealand_Map_Grid'],PARAMETER['False_Easting',2510000.0],PARAMETER['False_Northing',6023150.0],PARAMETER['Longitude_Of_Origin',173.0],PARAMETER['Latitude_Of_Origin',-41.0],UNIT['Meter',1.0]]"

    # Get the output coordinate system and transformation
    if (outputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
        outputCoordinateSystem = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
            transformation = "None"
        if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
            transformation = "NZGD_2000_To_WGS_1984_1"
        if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
            transformation = "NZGD_1949_To_WGS_1984_3_NTv2"
    if (outputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
        outputCoordinateSystem = "PROJCS['NZGD_2000_New_Zealand_Transverse_Mercator',GEOGCS['GCS_NZGD_2000',DATUM['D_NZGD_2000',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',1600000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',173.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]"
        if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
            transformation = "NZGD_2000_To_WGS_1984_1"
        if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
            transformation = "None"
        if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
            transformation = "New_Zealand_1949_To_NZGD_2000_3_NTv2"
    if (outputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
        outputCoordinateSystem = "PROJCS['GD_1949_New_Zealand_Map_Grid',GEOGCS['GCS_New_Zealand_1949',DATUM['D_New_Zealand_1949',SPHEROID['International_1924',6378388.0,297.0]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['New_Zealand_Map_Grid'],PARAMETER['False_Easting',2510000.0],PARAMETER['False_Northing',6023150.0],PARAMETER['Longitude_Of_Origin',173.0],PARAMETER['Latitude_Of_Origin',-41.0],UNIT['Meter',1.0]]"
        if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
            transformation = "NZGD_2000_To_WGS_1984_1"
        if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
            transformation = "New_Zealand_1949_To_NZGD_2000_3_NTv2"
        if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
            transformation = "None"
    if (outputCoordinateSystemName == "WGS 1984 Mercator 41"):
        outputCoordinateSystem = "PROJCS['WGS_1984_Mercator_41',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',100.0],PARAMETER['Standard_Parallel_1',-41.0],UNIT['Meter',1.0]]"
        if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
            transformation = ""
        if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
            transformation = "NZGD_2000_To_WGS_1984_1"
        if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
            transformation = "NZGD_1949_To_WGS_1984_3_NTv2"
    if (outputCoordinateSystemName == "WGS 1984 Web Mercator Auxiliary Sphere"):
        outputCoordinateSystem = "PROJCS['WGS_1984_Web_Mercator_Auxiliary_Sphere',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator_Auxiliary_Sphere'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],PARAMETER['Auxiliary_Sphere_Type',0.0],UNIT['Meter',1.0]]"
        if (inputCoordinateSystemName == "World Geodetic System 1984 (WGS84)"):
            transformation = ""
        if (inputCoordinateSystemName == "New Zealand Transverse Mercator (NZTM)"):
            transformation = "NZGD_2000_To_WGS_1984_1"
        if (inputCoordinateSystemName == "New Zealand Map Grid (NZMG)"):
            transformation = "NZGD_1949_To_WGS_1984_3_NTv2"

    return inputCoordinateSystem,outputCoordinateSystem,transformation
# End of get coordinate system details function


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
    # Test to see if ArcGIS desktop installed
    if ((os.path.basename(sys.executable).lower() == "arcgispro.exe") or (os.path.basename(sys.executable).lower() == "arcmap.exe") or (os.path.basename(sys.executable).lower() == "arccatalog.exe")):
        arcgisDesktop = "true"
        
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