#-------------------------------------------------------------
# Name:       Livestock Improvement Corporation Datawarehouse Sync
# Purpose:    Syncronises data between the LIC data warehouse and GIS database, producing error and change reports.       
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    18/09/2015
# Last Updated:    10/11/2015 (TWH)
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
import string
import datetime
import time

# Set global variables
enableLogging = "true" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), "Logs\LICDataWarehouseSync.log") # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "true"
emailTo = "cgriffin@lic.co.nz, araj@lic.co.nz"
emailUser = "svcaGIS@lic.co.nz"
emailPassword = ""
emailSubject = "EDW/GIS Sync"
emailMessage = ""
enableProxy = "false"
requestProtocol = "http" # http or https
proxyURL = ""
output = None

if arcpy.CheckProduct("ArcEditor") == "Available":
    print "License OK"
else:
    print "License not available"
    sendEmail("Quitting","Cant get a desktop GIS license.")
    sys.exit(-99999)

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Setup up reporting dictionary
gisReportDict = {}
gisReportCount = 0
        
# Start of main function
def mainFunction(gisProperty,gisShed,gisEntrance,gisPropertyEntranceRelate,gisPropertyShedRelate,gisshedEntranceRelate,dwProperty,dwShed,gisDataSyncReport,dwLoadStatus): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Check the DW has finished its job
        dwLoadNotComplete = True

        while dwLoadNotComplete:
            #Check if there is a row with both start and end times from today
            dwLoadStatusSearchCursor = arcpy.da.SearchCursor(dwLoadStatus, ["start_datetime","end_datetime"], "start_date = CAST(GETDATE() AS DATE) AND end_date = CAST(GETDATE() AS DATE)")        
            for row in dwLoadStatusSearchCursor:
                dwLoadNotComplete = False                

            if dwLoadNotComplete:
                # Insert row to say we are waiting for DW to complete
                gisReportInsertCursor = arcpy.da.InsertCursor(gisDataSyncReport,["ID","Date","LogType","Description"])
                gisReportInsertCursor.insertRow([0,datetime.datetime.now(),"WAIT","The DW ETL is not complete, waiting 5 minutes."])
                del gisReportInsertCursor

                time.sleep(300) #sleep for 5 minutes 
                
                #If after 11am then quit
                if datetime.datetime.now().hour >= 11:
                    # Insert row to say we are quitting
                    gisReportInsertCursor = arcpy.da.InsertCursor(gisDataSyncReport,["ID","Date","LogType","Description"])
                    gisReportInsertCursor.insertRow([0,datetime.datetime.now(),"QUIT","The GIS Data Sync is quitting as its after 11am."])
                    del gisReportInsertCursor
                    sendEmail("Quitting","The GIS Data Sync is quitting as its after 11am.")
                    sys.exit(-99999)
        
        # Insert row to say we are starting
        gisReportInsertCursor = arcpy.da.InsertCursor(gisDataSyncReport,["ID","Date","LogType","Description"])
        gisReportInsertCursor.insertRow([0,datetime.datetime.now(),"START","The DW GIS Data Sync is starting"])
        del gisReportInsertCursor
        
        # --------------------------------------- Start of code --------------------------------------- #
        global gisReportDict
        global gisReportCount
        
        # Set up search cursors
        # GIS Property
        gisPropertySearchCursor = arcpy.da.SearchCursor(gisProperty, ["Id","GlobalID","SHAPE@X","SHAPE@Y"], "RecordStatus <> 'I'")
        # GIS Shed
        gisPropertyShedSearchCursor = arcpy.da.SearchCursor(gisShed, ["Id"], "RecordStatus <> 'I'")
        # GIS Property/Entrance Relationship
        gisPropertyEntranceRelateSearchCursor = arcpy.da.SearchCursor(gisPropertyEntranceRelate, ["PropertyGlobalID","EntranceGlobalID"])
        # GIS Property/Shed Relationship
        gisPropertyShedRelateSearchCursor = arcpy.da.SearchCursor(gisPropertyShedRelate, ["ShedID","PropertyID"])

        dwPropertyShedSearchCursor = arcpy.da.SearchCursor(dwShed, ["shed_bsns_partner_num"])
        dwPropertySearchCursor = arcpy.da.SearchCursor(dwProperty, ["property_bsns_partner_num"])        

        # ---------------- Log the differing IDs - Property not in Data Warehouse ----------------
        # Add GIS property into array and dictionary
        gisPropertyIDsArray = []
        gisPropertyDict = {}
        for row in gisPropertySearchCursor:
            # Add IDs as strings to an array
            gisPropertyIDsArray.append(str(row[0]).strip().rstrip().upper())
            # Add ID, global ID and XY coordinate into a dictionary
            gisPropertyDict[str(row[0]).strip().rstrip().upper()] = [str(row[1]).strip().rstrip(),row[2],row[3]]

        # Add Data Warehouse property into array         
        dwPropertyIDsArray = []
        for row in dwPropertySearchCursor:
            # Add IDs as strings to an array
            dwPropertyIDsArray.append(str(row[0]).strip().rstrip().upper())

        # Setup array containing IDs that are in GIS and the Data Warehouse
        gisdwPropertyIDsArray = []
        
        for gisPropertyID in gisPropertyIDsArray:
            # If GIS property not in Data Warehouse property
            if gisPropertyID not in dwPropertyIDsArray:
                # Info message
                describeDataset = arcpy.Describe(dwProperty)
                descriptionString = "Property not in Data Warehouse - " + gisPropertyID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                # Add to logs dictionary
                gisReportDict[gisReportCount] = [gisPropertyID,datetime.datetime.now(),"ERROR",descriptionString]
                gisReportCount = gisReportCount + 1
            else:
                # Add to property (GIS and Data Warehouse) array
                gisdwPropertyIDsArray.append(gisPropertyID)


        # ---------------- Log the differing IDs - Property not in GIS ----------------
        for dwPropertyID in dwPropertyIDsArray:
            # If Data Warehouse property not in GIS property
            if dwPropertyID not in gisPropertyIDsArray:
                # Info message
                describeDataset = arcpy.Describe(gisProperty)
                descriptionString = "Property not in GIS - " + dwPropertyID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                # Add to logs dictionary
                gisReportDict[gisReportCount] = [dwPropertyID,datetime.datetime.now(),"ERROR",descriptionString]
                gisReportCount = gisReportCount + 1
                # Remove out ID from property (GIS and Data Warehouse) array if it's in there
                if dwPropertyID in gisdwPropertyIDsArray:
                    gisdwPropertyIDsArray.remove(dwPropertyID)
            
        # Add GIS property entrance relate into array and dictionary
        gisPropertyEntranceArray = []
        gisPropertyEntranceDict = {}
        for row in gisPropertyEntranceRelateSearchCursor:
            # Add property global IDs to an array
            gisPropertyEntranceArray.append(str(row[0]).strip().rstrip())            
            # Add both global IDs into a dictionary
            gisPropertyEntranceDict[str(row[0]).strip().rstrip()] = str(row[1]).strip().rstrip()

        # Delete cursor objects
        del gisPropertySearchCursor
        del dwPropertySearchCursor
        del gisPropertyEntranceRelateSearchCursor

        # ---------------- Create Property Entrance Point - If Property not in Property Entrance Relate ----------------
        gisPropertyGlobalIDsArray = []
        gisPropertyEntranceRelatesToAddDict = {}        
        for gisdwPropertyID in gisdwPropertyIDsArray:
            # Get the property global ID
            propertyGlobalID = gisPropertyDict[gisdwPropertyID][0]
            # Check if property not in property entrance relate
            if propertyGlobalID not in gisPropertyEntranceArray:
                # Info message    
                describeDataset = arcpy.Describe(gisPropertyEntranceRelate)
                descriptionString = "Property not in Property to Entrance Relationship - " + gisdwPropertyID + ", " + propertyGlobalID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                
                # Create property entrance point at same location as the property point
                propertyXPoint = gisPropertyDict[gisdwPropertyID][1]
                propertyYPoint = gisPropertyDict[gisdwPropertyID][2]
                propertyPoint = arcpy.Point(propertyXPoint,propertyYPoint)

                # Insert new record
                propertyEntranceOID = -1
                with arcpy.da.InsertCursor(gisEntrance,["SHAPE@XY","RecordStatus","SpatialAccuracy","CreatedUser","CreatedDate","LastEditedUser","LastEditedDate","EntranceNumber"]) as gisPropertyEntranceInsertCursor:
                    propertyEntranceOID = gisPropertyEntranceInsertCursor.insertRow([propertyPoint,"M","MIG","SCRIPT",datetime.datetime.now(),"SCRIPT",datetime.datetime.now(),1])
                
                # Get the global ID for the record just created
                #gisEntranceRows = [row for row in arcpy.da.SearchCursor(gisEntrance, "GlobalID", sql_clause=(None, "ORDER BY OBJECTID ASC"))]
                gisEntranceRows = [row for row in arcpy.da.SearchCursor(gisEntrance, "GlobalID", "OBJECTID = " + str(propertyEntranceOID))]                 
                propertyEntranceGlobalID = gisEntranceRows[-1][0]

                # Info message    
                describeDataset = arcpy.Describe(gisEntrance)
                descriptionString = "New feature record created - " + propertyEntranceGlobalID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                # Add to logs dictionary
                gisReportDict[gisReportCount] = [gisdwPropertyID,datetime.datetime.now(),"CHANGE",descriptionString]
                gisReportCount = gisReportCount + 1
                
                # Add entry to property entrance relates to add dictionary
                gisPropertyEntranceRelatesToAddDict[propertyGlobalID] = propertyEntranceGlobalID


        # ---------------- Create Property to Property Entrance Relationship - From dictionary created above ----------------
        # Setup up cursor for property entrance relationship
        gisPropertyEntranceRelateInsertCursor = arcpy.da.InsertCursor(gisPropertyEntranceRelate, ["PropertyGlobalID","EntranceGlobalID"])

        for key, value in gisPropertyEntranceRelatesToAddDict.iteritems():
            # Create record for property entrance to property relate
            newOID = gisPropertyEntranceRelateInsertCursor.insertRow([key,value])

            # Update property entrance to property relate dictionary
            gisPropertyEntranceDict[key] = value           

            # Get the property ID
            for keyProp, valueProp in gisPropertyDict.iteritems():
                if (str(key) == str(valueProp[0])):
                    # Info message   
                    describeDataset = arcpy.Describe(gisPropertyEntranceRelate)
                    descriptionString = "New relationship record created - " + keyProp + ": " + describeDataset.name
                    arcpy.AddMessage(descriptionString)                        
                    # Add to logs dictionary
                    gisReportDict[gisReportCount] = [keyProp,datetime.datetime.now(),"CHANGE",descriptionString]
                    gisReportCount = gisReportCount + 1
                
        # Delete cursor object
        del gisPropertyEntranceRelateInsertCursor       


        # ---------------- Create Property Shed - If shed in property to shed relationship ----------------
        # Add property shed relate into array and dictionary
        gisPropertyShedRelateArray = []
        gisPropertyShedRelateDict = {}
        for row in gisPropertyShedRelateSearchCursor:
            # Add property IDs to an array
            gisPropertyShedRelateArray.append(str(row[1]).strip().rstrip().upper())
            # Add shed ID and Property IDs into a dictionary
            gisPropertyShedRelateDict[str(row[0]).strip().rstrip().upper()] = str(row[1]).strip().rstrip().upper()

        # Add GIS property shed into array
        gisPropertyShedArray = []
        for row in gisPropertyShedSearchCursor:
            # Add property shed IDs to an array
            gisPropertyShedArray.append(str(row[0]).strip().rstrip().upper())

        # For each property
        for gisdwPropertyID in gisdwPropertyIDsArray:
            # Check if property in property shed relate
            if gisdwPropertyID in gisPropertyShedRelateArray:
                 # FUNCTION - Sync property shed and shed relationships         
                 gisPropertyShedSync(gisdwPropertyID,gisPropertyDict,gisShed,gisPropertyShedRelate,gisshedEntranceRelate,gisPropertyShedArray,gisPropertyShedRelateDict,gisPropertyEntranceDict)
            # If property not in property shed relate
            else:
                # Info message
                describeDataset = arcpy.Describe(gisPropertyShedRelate)
                descriptionString = "Property not in Property to Shed Relationship - " + gisdwPropertyID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)                   

        del gisPropertyShedSearchCursor
        del gisPropertyShedRelateSearchCursor


        # ---------------- Log the differing IDs - Shed not in Data Warehouse ----------------
        # Add GIS property shed into array
        gisPropertyShedIDsArray = []
        gisPropertyShedSearchCursor = arcpy.da.SearchCursor(gisShed, ["Id"], "RecordStatus <> 'I'")
        for row in gisPropertyShedSearchCursor:
            # Add property shed IDs to an array
            gisPropertyShedIDsArray.append(str(row[0]).strip().rstrip().upper())

        # Add Data Warehouse property shed into array         
        dwPropertyShedIDsArray = []
        for row in dwPropertyShedSearchCursor:
            # Add IDs as strings to an array
            dwPropertyShedIDsArray.append(str(row[0]).strip().rstrip().upper())

        for gisPropertyShedID in gisPropertyShedIDsArray:
            # If GIS shed not in Data Warehouse sheds
            if gisPropertyShedID not in dwPropertyShedIDsArray:
                # Info message
                describeDataset = arcpy.Describe(dwShed)
                descriptionString = "Shed not in Data Warehouse - " + gisPropertyShedID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                # Add to logs dictionary
                gisReportDict[gisReportCount] = [gisPropertyShedID,datetime.datetime.now(),"ERROR",descriptionString]
                gisReportCount = gisReportCount + 1


        # ---------------- Log the differing IDs - Shed not in GIS ----------------
        for dwPropertyShedID in dwPropertyShedIDsArray:
            # If data warehouse shed not in GIS sheds
            if dwPropertyShedID not in gisPropertyShedIDsArray:            
                # Info message
                describeDataset = arcpy.Describe(dwShed)
                descriptionString = "Shed not in GIS - " + dwPropertyShedID + ": " + describeDataset.name
                arcpy.AddMessage(descriptionString)
                # Add to logs dictionary
                gisReportDict[gisReportCount] = [dwPropertyShedID,datetime.datetime.now(),"ERROR",descriptionString]
                gisReportCount = gisReportCount + 1

        del gisPropertyShedSearchCursor
        

        # ---------------- Create Change and Error Report - From dictionary being logged to ----------------
        # Setup up cursor for report
        gisReportInsertCursor = arcpy.da.InsertCursor(gisDataSyncReport,["ID","Date","LogType","Description"])

        for key, value in gisReportDict.iteritems():
            # Write to log
            gisReportInsertCursor.insertRow([value[0],value[1],value[2],value[3]])

        # Delete cursor object
        del gisReportInsertCursor

        # Insert row to say we are stopping
        gisReportInsertCursor = arcpy.da.InsertCursor(gisDataSyncReport,["ID","Date","LogType","Description"])
        gisReportInsertCursor.insertRow([0,datetime.datetime.now(),"STOP","The DW GIS Data Sync is stopping"])
        del gisReportInsertCursor
        
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
            sendEmail("Error",errorMessage)
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
            sendEmail("Error",errorMessage)            
# End of main function

# Start of GIS property shed sync function
def gisPropertyShedSync(gisdwPropertyID,gisPropertyDict,gisShed,gisPropertyShedRelate,gisshedEntranceRelate,gisPropertyShedArray,gisPropertyShedRelateDict,gisPropertyEntranceDict):
    global gisReportDict
    global gisReportCount

    # Get the shed IDs related to the property from Data Warehouse
    gisShedIDs = []
    for key, value in gisPropertyShedRelateDict.iteritems():
        if (value == gisdwPropertyID):
            gisShedIDs.append(key)
    gisShedIDs.sort()

    # Get the number of sheds related to this property
    gisShedNumber = len(gisShedIDs)

    # For each shed
    count = 1 
    for gisShedID in gisShedIDs:
        # Check if shed is not in GIS sheds
        if gisShedID not in gisPropertyShedArray:
            # Create property shed point(s) with offset from property
            shedXPoint = gisPropertyDict[gisdwPropertyID][1] + (10 * count)
            shedYPoint = gisPropertyDict[gisdwPropertyID][2] + (10 * count)
            shedPoint = arcpy.Point(shedXPoint,shedYPoint)
            # Insert new record into GIS property shed
            with arcpy.da.InsertCursor(gisShed,["SHAPE@XY","Id","RecordStatus","SpatialAccuracy","CreatedUser","CreatedDate","LastEditedUser","LastEditedDate"]) as gisPropertyShedInsertCursor:
                gisPropertyShedInsertCursor.insertRow([shedPoint,gisShedID,"M","MIG","SCRIPT",datetime.datetime.now(),"SCRIPT",datetime.datetime.now()])
            del gisPropertyShedInsertCursor

            # Info message   
            describeDataset = arcpy.Describe(gisShed)
            descriptionString = "New feature record created - " + gisShedID + ": " + describeDataset.name
            arcpy.AddMessage(descriptionString)                        
            # Add to logs dictionary
            gisReportDict[gisReportCount] = [gisdwPropertyID,datetime.datetime.now(),"CHANGE",descriptionString]
            gisReportCount = gisReportCount + 1

            # ---------------- Create Shed to Entrance Relationship - When a new shed is created ----------------
            # Get the global ID for the record just created
            gisShedRows = [row for row in arcpy.da.SearchCursor(gisShed, "GlobalID", sql_clause=(None, "ORDER BY OBJECTID ASC"))]
            propertyShedGlobalID = gisShedRows[-1][0]
            # Get the property global ID
            propertyGlobalID = gisPropertyDict[gisdwPropertyID][0]
            # Get the property entrance related to this property
            propertyEntranceGlobalID = gisPropertyEntranceDict[propertyGlobalID]

            # Insert new record into GIS shed entrance relate
            with arcpy.da.InsertCursor(gisshedEntranceRelate,["ShedGlobalID","EntranceGlobalID"]) as gisEntranceShedRelateInsertCursor:
                gisEntranceShedRelateInsertCursor.insertRow([propertyShedGlobalID,propertyEntranceGlobalID])

            # Info message   
            describeDataset = arcpy.Describe(gisshedEntranceRelate)
            descriptionString = "New relationship record created - " + gisShedID + ": " + describeDataset.name
            arcpy.AddMessage(descriptionString)                        
            # Add to logs dictionary
            gisReportDict[gisReportCount] = [gisdwPropertyID,datetime.datetime.now(),"CHANGE",descriptionString]
            gisReportCount = gisReportCount + 1       
        count = count + 1       
# End of GIS property shed sync function


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
def sendEmail(subject, message):
    # Send an email
    arcpy.AddMessage("Sending email...")
    # Server and port information
    smtpServer = smtplib.SMTP("relay.livestock.org.nz",25) 
    smtpServer.ehlo
    # Email content
    header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + ': ' + subject + '\n'
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
    
