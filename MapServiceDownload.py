#-------------------------------------------------------------
# Name:       Map Service Download
# Purpose:    Downloads the data used in a map service layer by querying the json
#             and converting to a feature class.        
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    14/08/2013
# Last Updated:    20/09/2013
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1+
# Python Version:   2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import datetime
import string
import json
import urllib
import smtplib
import arcpy
arcpy.env.overwriteOutput = True

# Set variables
logInfo = "true"
logFile = os.path.join(os.path.dirname(__file__), r"Logs\MapServiceDownload.log")
sendEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(mapService,featureClass): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Log start
        if logInfo == "true":
            loggingFunction(logFile,"start","")

        # --------------------------------------- Start of code --------------------------------------- #        

        # Create map service query
        arcpy.AddMessage("Getting JSON from map service...")
        mapServiceQuery = mapService + "/query?text=&geometry=&geometryType=&inSR=&spatialRel=esriSpatialRelIntersects&relationParam=&objectIds=&where=1%3D1&time=&returnCountOnly=false&returnIdsOnly=false&returnGeometry=true&maxAllowableOffset=&outSR=&outFields=*&f=pjson"
        urlResponse = urllib.urlopen(mapServiceQuery);
        # Get json for feature returned
        mapServiceQueryJSONData = json.loads(urlResponse.read())
              
        # Get the geometry and create temporary feature class
        arcpy.AddMessage("Converting JSON to feature class...")
        count = 0
        while (len(mapServiceQueryJSONData["features"]) > count): 
            GeometryJSON = mapServiceQueryJSONData["features"][count]["geometry"]
            # Add spatial reference to geometry
            SpatialReference = mapServiceQueryJSONData["spatialReference"]["wkid"]
            GeometryJSON["spatialReference"] = {'wkid' : SpatialReference}
            Geometry = arcpy.AsShape(GeometryJSON, "True")
            # If on the first record
            if (count == 0):
                # Create new feature class
                arcpy.CopyFeatures_management(Geometry, featureClass)
                # Load the attributes
                for key, value in mapServiceQueryJSONData["features"][count]["attributes"].iteritems():
                    # Add new field
                    if key.lower() <> "objectid":
                        arcpy.AddField_management(featureClass, key, "TEXT", "", "", "5000")
                        # Insert value into field
                        cursor = arcpy.UpdateCursor(featureClass)
                        for row in cursor:
                            row.setValue(key, value)
                            cursor.updateRow(row)
            else:
                # Create new feature class then load into existing
                arcpy.CopyFeatures_management(Geometry, "in_memory\TempFeature")
                # Load the attributes
                for key, value in mapServiceQueryJSONData["features"][count]["attributes"].iteritems():
                    # Add new field
                    if key.lower() <> "objectid":
                        arcpy.AddField_management("in_memory\TempFeature", key, "TEXT", "", "", "")                    
                        # Insert value into field
                        cursor = arcpy.UpdateCursor("in_memory\TempFeature")
                        for row in cursor:
                            row.setValue(key, value)
                            cursor.updateRow(row)
                arcpy.Append_management("in_memory\TempFeature", featureClass, "NO_TEST", "", "")
            count = count + 1
            arcpy.AddMessage("Loaded " + str(count) + " of " + str(len(mapServiceQueryJSONData["features"])) + " features...")

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
        # Log start
        if logInfo == "true":
            loggingFunction(logFile,"end","")        
        pass
    # If arcpy error
    except arcpy.ExecuteError:
        # Show the message
        arcpy.AddError(arcpy.GetMessages(2))        
        # Log error
        if logInfo == "true":  
            loggingFunction(logFile,"error",arcpy.GetMessages(2))
    # If python error
    except Exception as e:
        # Show the message
        arcpy.AddError(e.args[0])             
        # Log error
        if logInfo == "true":         
            loggingFunction(logFile,"error",e.args[0])
# End of main function

# Start of logging function
def loggingFunction(logFile,result,info):
    #Get the time/date
    setDateTime = datetime.datetime.now()
    currentDateTime = setDateTime.strftime("%d/%m/%Y - %H:%M:%S")
    
    # Open log file to log message and time/date
    if result == "start":
        with open(logFile, "a") as f:
            f.write("---" + "\n" + "Process started at " + currentDateTime)
    if result == "end":
        with open(logFile, "a") as f:
            f.write("\n" + "Process ended at " + currentDateTime + "\n")
            f.write("---" + "\n")
    if result == "warning":
        with open(logFile, "a") as f:
            f.write("\n" + "Warning: " + info)               
    if result == "error":
        with open(logFile, "a") as f:
            f.write("\n" + "Process ended at " + currentDateTime + "\n")
            f.write("Error: " + info + "\n")        
            f.write("---" + "\n")
        # Send an email
        if sendEmail == "true":
            arcpy.AddMessage("Sending email...")
            # Server and port information
            smtpserver = smtplib.SMTP("smtp.gmail.com",587) 
            smtpserver.ehlo()
            smtpserver.starttls() 
            smtpserver.ehlo
            # Login with sender email address and password
            smtpserver.login(emailUser, emailPassword)
            # Email content
            header = 'To:' + emailTo + '\n' + 'From: ' + emailUser + '\n' + 'Subject:' + emailSubject + '\n'
            message = header + '\n' + emailMessage + '\n' + '\n' + info
            # Send the email and close the connection
            smtpserver.sendmail(emailUser, emailTo, message)
            smtpserver.close()                
# End of logging function     

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))
    mainFunction(*argv)