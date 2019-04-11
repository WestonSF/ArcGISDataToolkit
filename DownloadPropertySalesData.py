#-------------------------------------------------------------
# Name:                 Download Property Sales Data
# Purpose:              Downloads property sales data for the past six months
#                       from Homes.co.nz. Data is then uploaded to a portal site.
# Author:               Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:         05/04/2019
# Last Updated:         06/04/2019
# ArcGIS Version:       ArcGIS API for Python 1.4.2+ or ArcGIS Pro (ArcPy) 2.1+
# Python Version:       3.6.5+ (Anaconda Distribution)
#--------------------------------

# Import main modules
import os
import sys
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.mime.application
# Import ArcGIS modules
useArcPy = "true"
useArcGISAPIPython = "true"
if (useArcPy == "true"):
    # Import arcpy module
    import arcpy
    # Enable data to be overwritten
    arcpy.env.overwriteOutput = True
if (useArcGISAPIPython == "true"):
    # Import arcgis module
    import arcgis
import urllib.request
import json
import tempfile
import zipfile
import uuid
import shutil

# Set global variables
propertyMapWebService = "https://property-service.homes.co.nz/map/items" # Homes property map web service
propertyCardWebService = "https://gateway.homes.co.nz/property?url=%url" # Homes property details web service
propertyDetailsWebService = "https://gateway.homes.co.nz/property/%id/detail" # Homes property details web service
propertyTimelineWebService = "https://gateway.homes.co.nz/property/%id/timeline" # Homes property sales web service
propertyValuesWebService = "https://gateway.homes.co.nz/estimate/history/%id" # Homes property values web service
outputFeatureClass = r"C:\Projects\Research\Property\PropertySales.gdb\Property" # Output feature class
# Can find extents here - http://bboxfinder.com
# Wider Wellington region
extent = "174.539795,-41.429342,175.208588,-41.030679" # XMin,YMin,XMax,YMax
# Auckland region
# extent = "174.586487,-37.026677,174.949036,-36.714669"
# Paparangi, Wellington suburb
# extent = "174.810505,-41.222181,174.822607,-41.212625" # XMin,YMin,XMax,YMax
portalURL = "https://organsation.maps.arcgis.com" # Portal URL
portalUser = "sfweston" # Portal username
portalPassword = "*****" # Portal password
portalItemFGDBID = "9ba7105f8b304cdcb459dd4634c42ed7" # Portal FGDB item ID
portalItemTitle = "Wellington Property Sales" # Portal item title
portalItemSummary = "Wellington property sales for the past six months." # Portal item summary
portalItemDescription = "Wellington property sales for the past six months." # Portal item description
portalItemCredits = "Homes.co.nz" # Portal item credits

# Logging
enableLogging = "false" # Use within code to print and log messages - printMessage("xxx","info"), printMessage("xxx","warning"), printMessage("xxx","error")
logFile = os.path.join(os.path.dirname(__file__), "") # e.g. os.path.join(os.path.dirname(__file__), "Example.log")
# Email Use within code to send email - sendEmail(subject,message,attachment)
sendErrorEmail = "false"
emailSubject = "" # Subject in email
emailServerName = "" # e.g. smtp.gmail.com
emailServerPort = None # e.g. 25
emailTo = [] # Address of email sent to e.g. ["name1@example.com", "name2@example.com"]
emailUser = "" # Address of email sent from e.g. "name1@example.com"
emailPassword = ""
# Proxy
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
# Output
output = None


# Start of main function
def mainFunction(): # Add parameters sent to the script here e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        printMessage("Creating extent feature class for queries - " + os.path.join(arcpy.env.scratchGDB,"Extents") + "...","info")
        arcpy.CreateFishnet_management(os.path.join(arcpy.env.scratchGDB,"Extents"), extent.split(',')[0] + " " + extent.split(',')[1], extent.split(',')[0] + " " + str(float(extent.split(',')[1])+5), "", "", "5", "5", extent.split(',')[2] + " " + extent.split(',')[3], "NO_LABELS", "", "POLYGON")

        propertyIDsAdded = []
        # Check if the feature class exists
        if arcpy.Exists(outputFeatureClass):
            printMessage("Feature class already exists - " + outputFeatureClass + "...","info")
            # Search the existing feature class
            with arcpy.da.SearchCursor(outputFeatureClass, "ID") as rows:
                for row in rows:
                    # Add to property IDs added array
                    propertyIDsAdded.append(row[0])
        else:           
            printMessage("Creating output feature class - " + outputFeatureClass + "...","info")
            arcpy.CreateFeatureclass_management(os.path.dirname(outputFeatureClass), os.path.basename(outputFeatureClass), "Point", "", "DISABLED", "DISABLED", "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision", "", "0", "0", "0")
            arcpy.AddField_management(outputFeatureClass, "ID", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "Address", "TEXT", "", "", "255", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "Bedrooms", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "Bathrooms", "SHORT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "SaleDate", "DATE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "SalePrice", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "DecadeBuilt", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "FloorArea", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "LandArea", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "CapitalValue", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "EstimatedValue", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.AddField_management(outputFeatureClass, "EstimatedRent", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")       

        with arcpy.da.SearchCursor(os.path.join(arcpy.env.scratchGDB,"Extents"), "SHAPE@") as rows:
            for row in rows:  
                # Setup the parameters for the web request
                parameters = urllib.parse.urlencode({
                              'limit': '5000',
                              'just_sold': 'true',
                              'for_sale': 'false',
                              'sale_min':'0',
                              'sale_max':'0',                      
                              'num_bathrooms':'0',
                              'num_bedrooms':'0',
                              'display_rentals': 'false',
                              'for_rent': 'false',
                              'rent_bathrooms':'0',
                              'rent_bedrooms':'0',
                              'rent_max':'0',
                              'rent_min':'0',
                              'off_market':'false',
                              'off_market_bathrooms':'0',
                              'off_market_bedrooms':'0',
                              'off_market_max':'0',
                              'off_market_min':'0',
                              'use_expanded_bounding_box':'true',
                              'nw_lat':str(row[0].extent.YMax), # YMax
                              'nw_long':str(row[0].extent.XMin), # XMin
                              'se_lat':str(row[0].extent.YMin), # YMin
                              'se_long':str(row[0].extent.XMax) # XMax
                              })
                queryString = parameters.encode('utf-8')
    
                # Query web service
                printMessage("Querying web service - " + propertyMapWebService + " at extent - " + str(row[0].extent.XMin) + "," + str(row[0].extent.YMin) + "," + str(row[0].extent.XMax) + "," + str(row[0].extent.YMax) + "...","info")
                response = json.loads(urllib.request.urlopen(propertyMapWebService + "?" + parameters).read())
                
                # Download data
                printMessage("Downloading data - " + os.path.join(tempfile.gettempdir(), "Download.json") + "...","info")
                with open(os.path.join(tempfile.gettempdir(), "Download.json"), 'w') as downloadFile:
                    downloadFile.write(json.dumps(response))

                # Open data file
                printMessage("Reading downloaded data...","info")
                propertyMapWebServicePropertyIDsAdded = []
                with open(os.path.join(tempfile.gettempdir(), "Download.json")) as jsonFile:  
                    jsonData = json.load(jsonFile)
                    printMessage("Processing " + str(len(jsonData["map_items"])) + " records (Duplicate property IDs will not be added)...","info")
                    cursor = arcpy.da.InsertCursor(outputFeatureClass, ["ID","Address","Bedrooms","Bathrooms","SaleDate","SalePrice","DecadeBuilt","FloorArea","LandArea","CapitalValue","EstimatedValue","EstimatedRent","SHAPE@XY"])
                   
                    # For each property returned
                    for record in jsonData["map_items"]:
                        # Get location geometry
                        point = (record["point"]["long"],record["point"]["lat"])

                        # If the property has not been added yet
                        if (record["id"] not in propertyIDsAdded):
                            # Query the property card
                            address,bedrooms,bathrooms,saleDate,salePrice = queryPropertyCard(propertyCardWebService,record["url"])
                            # Query the property details
                            decadeBuilt,floorArea,landArea,capitalValue,estimatedValue,estimatedRent = queryPropertyDetails(propertyDetailsWebService,record["id"])
                        
                            # Insert record into feature class
                            cursor.insertRow([record["id"],address,bedrooms,bathrooms,saleDate,salePrice,decadeBuilt,floorArea,landArea,capitalValue,estimatedValue,estimatedRent,point])
                            # Add to property IDs added array
                            propertyIDsAdded.append(record["id"])
                            propertyMapWebServicePropertyIDsAdded.append(record["id"])
                printMessage("Added " + str(len(propertyMapWebServicePropertyIDsAdded)) + " records...","info")                

        printMessage("Adding and calculating extra fields - " + outputFeatureClass + "...","info")
        arcpy.AddField_management(outputFeatureClass, "EstimateGrossYield", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(outputFeatureClass, "SalePercentAboveCV", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(outputFeatureClass, "EstimateGrossYield", "((!EstimatedRent!*52)/ !EstimatedValue!)*100", "PYTHON_9.3", "")
        arcpy.CalculateField_management(outputFeatureClass, "SalePercentAboveCV", "((!SalePrice!-!CapitalValue!)/ !CapitalValue!)*100", "PYTHON_9.3", "")    

        resultCount = arcpy.GetCount_management(outputFeatureClass)
        printMessage("Number of records in " + outputFeatureClass + " - " + str(resultCount[0]) + "...","info")

        # Setup a temporary folder
        printMessage("Creating temporary folder...","info")
        tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()))
        # Copy FGDB to this folder
        arcpy.Copy_management(arcpy.Describe(outputFeatureClass).path, os.path.join(str(tempFolder),arcpy.Describe(outputFeatureClass).path.split(".")[0].split("\\")[-1] + ".gdb"), "Workspace")

        # Zip up FGDB
        printMessage("Zipping up data - " + os.path.join(arcpy.env.scratchFolder,arcpy.Describe(outputFeatureClass).path.split(".")[0].split("\\")[-1] + ".zip") + "...","info")
        zippedFolder = zipfile.ZipFile(os.path.join(arcpy.env.scratchFolder,arcpy.Describe(outputFeatureClass).path.split(".")[0].split("\\")[-1] + ".zip"), "w", allowZip64=True)
        # Zip up the geodatabase
        root_len = len(os.path.abspath(str(tempFolder)))
        # For each of the directories in the folder
        for root, dirs, files in os.walk(str(tempFolder)):
          archive_root = os.path.abspath(root)[root_len:]
          # For each file
          for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            zippedFolder.write(fullpath, archive_name)
        # Close zip file
        zippedFolder.close()

        printMessage("Connecting to GIS Portal - " + portalURL + "...","info")
        gisPortal = arcgis.GIS(url=portalURL, username=portalUser, password=portalPassword, verify_cert=False)

        # If portal ID provided
        if (portalItemFGDBID):
            # Get the portal item
            item = gisPortal.content.get(portalItemFGDBID)
            # Update the FGDB in portal
            printMessage("Uploading file geodatabase to portal - " + portalItemFGDBID + "...", "info")
            item.update({"title":portalItemTitle,
                                    "snippet":portalItemSummary,
                                    "description":portalItemDescription,
                                    "accessInformation":portalItemCredits,
                                    "tags":portalItemTitle},
                                   os.path.join(arcpy.env.scratchFolder,arcpy.Describe(outputFeatureClass).path.split(".")[0].split("\\")[-1] + ".zip"))
            printMessage("Publishing feature service...", "info")
            serviceItem = item.publish()
            printMessage("Feature service has been published - " + serviceItem.id + "...","info") 
        else:
            # Upload the FGDB to portal
            printMessage("Uploading file geodatabase to portal...", "info")
            item = gisPortal.content.add({"title":portalItemTitle,
                                          "snippet":portalItemSummary,
                                          "description":portalItemDescription,
                                          "accessInformation":portalItemCredits,
                                          "tags":portalItemTitle,
                                          "type":"File Geodatabase"},
                                         os.path.join(arcpy.env.scratchFolder,arcpy.Describe(outputFeatureClass).path.split(".")[0].split("\\")[-1] + ".zip"))
            printMessage("File geodatabase uploaded - " + item.id + "...", "info")
            printMessage("Publishing feature service...", "info")
            serviceItem = item.publish()
            printMessage("Feature service has been published - " + serviceItem.id + "...","info") 
            
        # --------------------------------------- End of code --------------------------------------- #
        # If called from ArcGIS GP tool
        if __name__ == '__main__':
            # Return the output if there is any
            if output:
                # If using ArcPy
                if (useArcPy == "true"):
                    arcpy.SetParameter(1, output)
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
    # If error
    except Exception as e:
        # Build and show the error message
        # errorMessage = arcpy.GetMessages(2)

        errorMessage = ""
        # Build and show the error message
        # If many arguments
        if (e.args):
            for i in range(len(e.args)):
                if (i == 0):
                    errorMessage = str(e.args[i]).encode('utf-8').decode('utf-8')
                else:
                    errorMessage = errorMessage + " " + str(e.args[i]).encode('utf-8').decode('utf-8')
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
            sendEmail(errorMessage,None)
# End of main function


# Start of query property card function
def queryPropertyCard(propertyCardWebService,propertyURL):
        # Query web service
        printMessage("Querying web service - " + propertyCardWebService.replace("%url", propertyURL) + "...","info")
        response = json.loads(urllib.request.urlopen(propertyCardWebService.replace("%url", propertyURL)).read())

        # If there is a sale date
        if (response["card"]["date"]):
            saleDate = response["card"]["date"].replace("T00:00:00Z", "")
        else:
            saleDate = response["card"]["date"]
        # Return data
        return response["card"]["property_details"]["address"],response["card"]["property_details"]["num_bedrooms"],response["card"]["property_details"]["num_bathrooms"],saleDate,response["card"]["price"]
# End of query property card function


# Start of query property details function
def queryPropertyDetails(propertyDetailsWebService,propertyID):
        # Query web service
        printMessage("Querying web service - " + propertyDetailsWebService.replace("%id", propertyID) + "...","info")
        response = json.loads(urllib.request.urlopen(propertyDetailsWebService.replace("%id", propertyID)).read())

        # If there are upper and lower rental estimates
        if (response["property"]["estimated_rental_upper_value"] and response["property"]["estimated_rental_lower_value"]):
            estimatedRentValue = (response["property"]["estimated_rental_upper_value"]+response["property"]["estimated_rental_lower_value"])/2
        else:
            estimatedRentValue = 0
        # Return data
        return response["property"]["decade_built"],response["property"]["floor_area"],response["property"]["land_area"],response["property"]["capital_value"],response["property"]["estimated_value"],estimatedRentValue
# End of query property details function


# Start of query property sales function
def queryPropertySales(propertyTimelineWebService,propertyURL):
        # Query web service
        printMessage("Querying web service - " + propertyTimelineWebService.replace("%id", propertyID) + "...","info")
        response = json.loads(urllib.request.urlopen(propertyTimelineWebService.replace("%id", propertyID)).read())
        # Return data
        return response
# End of query property sales function


# Start of print and logging message function
def printMessage(message,type):
    useArcPy = "false"
    # If using ArcPy
    if (useArcPy == "true"):
        if (type.lower() == "warning"):
            arcpy.AddWarning(message)
            # Logging
            if (enableLogging == "true"):
                logger.warning(message)
        elif (type.lower() == "error"):
            arcpy.AddError(message)
            # Logging
            if (enableLogging == "true"):
                logger.error(message)
        else:
            arcpy.AddMessage(message)
            # Logging
            if (enableLogging == "true"):
                logger.info(message)
    else:
        print(message)
        # Logging
        if (enableLogging == "true"):
            logger.info(message)
# End of print and logging message function


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
def sendEmail(message,attachment):
    # Send an email
    printMessage("Sending email...","info")
    # Server and port information
    smtpServer = smtplib.SMTP(emailServerName,emailServerPort)
    smtpServer.ehlo()
    smtpServer.starttls()
    smtpServer.ehlo
    # Setup content for email (In html format)
    emailMessage = MIMEMultipart('alternative')
    emailMessage['Subject'] = emailSubject
    emailMessage['From'] = emailUser
    emailMessage['To'] = ", ".join(emailTo)
    emailText = MIMEText(message, 'html')
    emailMessage.attach(emailText)

    # If there is a file attachment
    if (attachment):
        fp = open(attachment,'rb')
        fileAttachment = email.mime.application.MIMEApplication(fp.read(),_subtype="pdf")
        fp.close()
        fileAttachment.add_header('Content-Disposition','attachment',filename=os.path.basename(attachment))
        emailMessage.attach(fileAttachment)

    # Login with sender email address and password
    if (emailUser and emailPassword):
        smtpServer.login(emailUser, emailPassword)
    # Send the email and close the connection
    smtpServer.sendmail(emailUser, emailTo, emailMessage.as_string())
    smtpServer.quit()
# End of send email function


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # If using ArcPy
    if (useArcPy == "true"):
        argv = tuple(arcpy.GetParameterAsText(i)
            for i in range(arcpy.GetArgumentCount()))
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
