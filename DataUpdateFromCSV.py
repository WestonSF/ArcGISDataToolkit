#-------------------------------------------------------------
# Name:       Data Update From CSV
# Purpose:    Updates a dataset in a geodatabase from a CSV file. Will get latest
#             CSV file from the folder specified.         
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    05/12/2013
# Last Updated:    28/11/2014
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
import glob
import string

# Enable data to be overwritten
arcpy.env.overwriteOutput = True

# Set global variables
enableLogging = "true" # Use logger.info("Example..."), logger.warning("Example..."), logger.error("Example...")
logFile = r"C:\Data\Tools & Scripts\ArcGIS Data Toolkit\Logs\DataUpdateFromCSV.log" # os.path.join(os.path.dirname(__file__), "Example.log")
sendErrorEmail = "true"
emailTo = "shaun_weston@eagle.co.nz"
emailUser = "northlandgisserver@gmail.com"
emailPassword = "E@gleT3chnology"
emailSubject = "NRC Web GIS Server Error"
emailMessage = "The bathings sites python script on the Northland GIS Web Server failed..."
output = None

# Start of main function
def mainFunction(updateFolder,geodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #        
        # Get the newest CSV file from the dropbox folder, copy it and call it latest
        latestFile = max(glob.iglob(updateFolder + r"\*.csv"), key=os.path.getmtime)

        # Create a Describe object from the dataset
        describeDataset = arcpy.Describe(latestFile)
        datasetName = string.split(describeDataset.name, ".")
        # Change CSV name if starts with a digit
        if datasetName[0].isdigit():
            datasetName[0] = "Layer" + datasetName[0]
                   
        # Convert CSV table to layer
        arcpy.MakeXYEventLayer_management(latestFile, "Easting", "Northing", "Layer", "PROJCS['NZGD_2000_New_Zealand_Transverse_Mercator',GEOGCS['GCS_NZGD_2000',DATUM['D_NZGD_2000',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Transverse_Mercator'],PARAMETER['False_Easting',1600000.0],PARAMETER['False_Northing',10000000.0],PARAMETER['Central_Meridian',173.0],PARAMETER['Scale_Factor',0.9996],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]];-4020900 1900 10000;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision", "")
        arcpy.CopyFeatures_management("Layer", os.path.join("in_memory", datasetName[0]))

        # If dataset exists in geodatabase, delete features and load in new data
        if arcpy.Exists(os.path.join(geodatabase, datasetName[0])):
            # Custom updates to data when bathing sites data is uploaded by NRC
            if arcpy.Exists(os.path.join("in_memory", "BathingSites")):
                arcpy.AddField_management(os.path.join("in_memory", "BathingSites"), "GradeDescription", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.CalculateField_management(os.path.join("in_memory", "BathingSites"), "GradeDescription", "changeValue(!Grade!)", "PYTHON_9.3", "def changeValue(var):\\n  if var == 1:\\n    return \"Considered suitable for swimming\"\\n  if var == 2:\\n    return \"Potentially considered unsuitable for swimming\"\\n  if var == 3:\\n    return \"Considered unsuitable for swimming\"")
                arcpy.AddField_management(os.path.join("in_memory", "BathingSites"), "URL", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.CalculateField_management(os.path.join("in_memory", "BathingSites"), "URL", "changeValue (!Test!)", "PYTHON_9.3", "def changeValue(var):\\n  if (var == \"ECOLI\"):\\n    return \"http://www.nrc.govt.nz/Living-in-Northland/At-the-beach/Swimming-water-quality/Freshwater-quality\"\\n  else:\\n    return \"http://www.nrc.govt.nz/Living-in-Northland/At-the-beach/Swimming-water-quality/Beach-water-quality\"")
            # Custom updates to data when bathing sites data is uploaded by NRC
            if arcpy.Exists(os.path.join("in_memory", "FollowUp")):
                arcpy.AddField_management(os.path.join("in_memory", "FollowUp"), "GradeDescription", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.CalculateField_management(os.path.join("in_memory", "FollowUp"), "GradeDescription", "changeValue(!Grade!)", "PYTHON_9.3", "def changeValue(var):\\n  if var == 1:\\n    return \"Considered suitable for swimming\"\\n  if var == 2:\\n    return \"Potentially considered unsuitable for swimming\"\\n  if var == 3:\\n    return \"Considered unsuitable for swimming\"")
                arcpy.AddField_management(os.path.join("in_memory", "FollowUp"), "URL", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
                arcpy.CalculateField_management(os.path.join("in_memory", "FollowUp"), "URL", "changeValue (!Test!)", "PYTHON_9.3", "def changeValue(var):\\n  if (var == \"ECOLI\"):\\n    return \"http://www.nrc.govt.nz/Living-in-Northland/At-the-beach/Swimming-water-quality/Freshwater-quality\"\\n  else:\\n    return \"http://www.nrc.govt.nz/Living-in-Northland/At-the-beach/Swimming-water-quality/Beach-water-quality\"")
            arcpy.DeleteFeatures_management(os.path.join(geodatabase, datasetName[0]))
            arcpy.Append_management(os.path.join("in_memory", datasetName[0]), os.path.join(geodatabase, datasetName[0]), "NO_TEST", "", "")
        else:
            arcpy.AddMessage("Warning: " + os.path.join(geodatabase, datasetName[0]) + " does not exist and won't be updated")
            # Log warning
            if logInfo == "true":  
                logger.warning(os.path.join(geodatabase, datasetName[0]) + " does not exist and won't be updated")            
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
    mainFunction(*argv)
      
