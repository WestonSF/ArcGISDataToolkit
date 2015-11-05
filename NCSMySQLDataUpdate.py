#-------------------------------------------------------------
# Name:       NCS MySQL Data Update
# Purpose:    Extracts tables from the MySQL NCS database and updates the property, licenses, lims, building consents and
#             resource consents feature classes from the NCS spatial views in the central GIS database.
#             - Need to install MySQLdb python package.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    05/09/2013
# Last Updated:    04/11/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import urllib
import zipfile
import uuid
import glob
import MySQLdb
import string

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "true" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = os.path.join(os.path.dirname(__file__), "Logs\NCSUpdate.log") # os.path.join(os.path.dirname(__file__), "Example.log")
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
def mainFunction(ncsMySQLString,ncsTableNames,ncsTables,propertyView,propertyFeatureClass,licencesView,licencesFeatureClass,limsView,limsFeatureClass,resourceConsentsView,resourceConsentsFeatureClass,buildingConsentsView,buildingConsentsFeatureClass): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:       
        # --------------------------------------- Start of code --------------------------------------- #
        # Connect to the MySQL database
        ncsMySQLString = string.split(ncsMySQLString, ";")
        mySQLDatabase = MySQLdb.connect(host=ncsMySQLString[0],user=ncsMySQLString[1],passwd=ncsMySQLString[2],db=ncsMySQLString[3]) 

        # For each NCS table
        ncsTableNames = string.split(ncsTableNames, ";")
        ncsTables = string.split(ncsTables, ";")
        datasetCount = 0
        for ncsTableName in ncsTableNames:
            # Remove out apostrophes
            ncsTables[datasetCount] = str(ncsTables[datasetCount]).replace("'", "")

            arcpy.AddMessage("Copying " + ncsTableName + " table to " + ncsTables[datasetCount] + "...")
            # Create a cursor object
            ncsCursor = mySQLDatabase.cursor() 

            # Query to select data from NCS
            ncsCursor.execute("SELECT * FROM " + ncsTableName)
        
            # Get the field names
            fieldNames = [i[0] for i in ncsCursor.description]
            # Create the gdb table
            ncsTableNameSplit = ncsTables[datasetCount].rsplit("\\",1)
            arcpy.CreateTable_management(ncsTableNameSplit[0], ncsTableNameSplit[1], "", "")
            # Add the necesary fields
            for fieldName in fieldNames:
                arcpy.AddField_management(ncsTables[datasetCount], fieldName, "TEXT", "", "", "500")
            
            # Create the ubsert cursor for the rable
            insertCursor = arcpy.InsertCursor(ncsTables[datasetCount])
            
            # Iterate through all the rows
            rowCount = 0
            for row in ncsCursor.fetchall():
                rowCount = rowCount + 1      
                datasetRow = insertCursor.newRow()
                
                # Write values into table
                columnCount = 0
                for fieldName in fieldNames:
                    datasetRow.setValue(str(fieldName), str(row[columnCount]))
                    columnCount = columnCount + 1
                insertCursor.insertRow(datasetRow)
            del insertCursor
            ncsCursor.close()
            datasetCount = datasetCount + 1
        
        # Copy view into temporary location - Property
        arcpy.CopyFeatures_management(propertyView, os.path.join(arcpy.env.scratchGDB, "Property"))
        # Alter some of the fields
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "Property"), "Location", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "Property"), "House_No", "!House_No!.rstrip()", "PYTHON_9.3", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "Property"), "House_No", "changeValue( !House_No!)", "PYTHON_9.3", "def changeValue(var):\\n  if (var == \"0\"):\\n    return \"\"\\n  else:\\n    return var\\n")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "Property"), "Location", "!House_No! + \" \" + !Address_1! + \", \" + !Address_2!", "PYTHON_9.3", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "Property"), "Location", "!Location!.strip()", "PYTHON_9.3", "")
        # Dissolve on valuation ID
        arcpy.Dissolve_management(os.path.join(arcpy.env.scratchGDB, "Property"), os.path.join(arcpy.env.scratchGDB, "PropertyDissolved"), "Valuation_ID", "", "MULTI_PART", "DISSOLVE_LINES")
        arcpy.JoinField_management(os.path.join(arcpy.env.scratchGDB, "PropertyDissolved"), "Valuation_ID", os.path.join(arcpy.env.scratchGDB, "Property"), "Valuation_ID", "")
  
        recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "PropertyDissolved"))
        arcpy.AddMessage("Number of records for " + propertyFeatureClass + " - " + str(recordCount)) 
        # Logging
        if (enableLogging == "true"):
            # Log record count
            logger.info("Number of records for " + propertyFeatureClass + " - " + str(recordCount))
        # Load in data
        if (recordCount > 0):
            arcpy.AddMessage("Refreshing records for " + propertyFeatureClass + "...")
            arcpy.DeleteFeatures_management(propertyFeatureClass)            
            arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "PropertyDissolved"), propertyFeatureClass, "NO_TEST", "", "")

                
        # Copy view into temporary location - Licences
        arcpy.Select_analysis(licencesView, os.path.join(arcpy.env.scratchGDB, "Licences"), "") 
        # Convert to points
        arcpy.FeatureToPoint_management(os.path.join(arcpy.env.scratchGDB, "Licences"), os.path.join(arcpy.env.scratchGDB, "LicencesPoints"), "CENTROID")

        recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "LicencesPoints"))
        arcpy.AddMessage("Number of records for " + licencesFeatureClass + " - " + str(recordCount)) 
        # Logging
        if (enableLogging == "true"):
            # Log record count
            logger.info("Number of records for " + licencesFeatureClass + " - " + str(recordCount))
        # Load in data
        if (recordCount > 0):
            arcpy.AddMessage("Refreshing records for " + licencesFeatureClass + "...")            
            arcpy.DeleteFeatures_management(licencesFeatureClass)            
            arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "LicencesPoints"), licencesFeatureClass, "NO_TEST", "", "")
                
        # Copy view into temporary location - LIMs
        arcpy.CopyFeatures_management(limsView, os.path.join(arcpy.env.scratchGDB, "LIMs"))

        recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "LIMs"))
        arcpy.AddMessage("Number of records for " + limsFeatureClass + " - " + str(recordCount)) 
        # Logging
        if (enableLogging == "true"):
            # Log record count
            logger.info("Number of records for " + limsFeatureClass + " - " + str(recordCount))
        # Load in data
        if (recordCount > 0):
            arcpy.AddMessage("Refreshing records for " + limsFeatureClass + "...")               
            arcpy.DeleteFeatures_management(limsFeatureClass)            
            arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "LIMs"), limsFeatureClass, "NO_TEST", "", "")
              
        # Copy view into temporary location - Resource Consents
        arcpy.CopyFeatures_management(resourceConsentsView, os.path.join(arcpy.env.scratchGDB, "ResourceConsents"))
        # Alter some of the fields
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Location", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "House_No", "!House_No!.rstrip()", "PYTHON_9.3", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "House_No", "changeValue( !House_No!)", "PYTHON_9.3", "def changeValue(var):\\n  if (var == \"0\"):\\n    return \"\"\\n  else:\\n    return var\\n")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Location", "!House_No! + \" \" + !Address_1! + \", \" + !Address_2!", "PYTHON_9.3", "")        
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Location", "!Location!.strip()", "PYTHON_9.3", "")
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Proposal", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Proposal", "!Proposal_1! + \" \" + !Proposal_2! + \" \" + !Proposal_3! + \" \" + !Proposal_4!", "PYTHON_9.3", "")        
        # Dissolve feature class by applicant number
        arcpy.Dissolve_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolved"), "Applicant_Debtor_No", "", "MULTI_PART", "DISSOLVE_LINES")
        arcpy.JoinField_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolved"), "Applicant_Debtor_No", os.path.join(arcpy.env.scratchGDB, "ResourceConsents"), "Applicant_Debtor_No", "")
        # Convert to points
        arcpy.FeatureToPoint_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolved"), os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolvedPoints"), "CENTROID")

        recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolvedPoints"))
        arcpy.AddMessage("Number of records for " + resourceConsentsFeatureClass + " - " + str(recordCount)) 
        # Logging
        if (enableLogging == "true"):
            # Log record count
            logger.info("Number of records for " + resourceConsentsFeatureClass + " - " + str(recordCount))
        # Load in data
        if (recordCount > 0):
            arcpy.AddMessage("Refreshing records for " + resourceConsentsFeatureClass + "...")              
            arcpy.DeleteFeatures_management(resourceConsentsFeatureClass)            
            arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "ResourceConsentsDissolvedPoints"), resourceConsentsFeatureClass, "NO_TEST", "", "")
                
        # Copy view into temporary location - Building Consents
        arcpy.CopyFeatures_management(buildingConsentsView, os.path.join(arcpy.env.scratchGDB, "BuildingConsents"))
        # Alter some of the fields
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Location", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "House_No", "!House_No!.rstrip()", "PYTHON_9.3", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "House_No", "changeValue( !House_No!)", "PYTHON_9.3", "def changeValue(var):\\n  if (var == \"0\"):\\n    return \"\"\\n  else:\\n    return var\\n")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Location", "!House_No! + \" \" + !Address_1! + \", \" + !Address_2!", "PYTHON_9.3", "")        
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Location", "!Location!.strip()", "PYTHON_9.3", "")
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Proposal", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Proposal", "!Proposal_1! + \" \" + !Proposal_2! + \" \" + !Proposal_3! + \" \" + !Proposal_4!", "PYTHON_9.3", "")        
        # Dissolve feature class by applicant number
        arcpy.Dissolve_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolved"), "Applicant_Debtor_No", "", "MULTI_PART", "DISSOLVE_LINES")
        arcpy.JoinField_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolved"), "Applicant_Debtor_No", os.path.join(arcpy.env.scratchGDB, "BuildingConsents"), "Applicant_Debtor_No", "")
        # Convert to points
        arcpy.FeatureToPoint_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolved"), os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolvedPoints"), "CENTROID")

        recordCount = arcpy.GetCount_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolvedPoints"))
        arcpy.AddMessage("Number of records for " + buildingConsentsFeatureClass + " - " + str(recordCount)) 
        # Logging
        if (enableLogging == "true"):
            # Log record count
            logger.info("Number of records for " + buildingConsentsFeatureClass + " - " + str(recordCount))
        # Load in data
        if (recordCount > 0):
            arcpy.AddMessage("Refreshing records for " + buildingConsentsFeatureClass + "...") 
            arcpy.DeleteFeatures_management(buildingConsentsFeatureClass)            
            arcpy.Append_management(os.path.join(arcpy.env.scratchGDB, "BuildingConsentsDissolvedPoints"), buildingConsentsFeatureClass, "NO_TEST", "", "")
                
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
