#-------------------------------------------------------------
# Name:       Stats Property Data Import
# Purpose:    Imports data from Census NZ stats relating to property and aggregates
#             this data by meshblock and suburb.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    21/12/2014
# Last Updated:    22/12/2014
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
def mainFunction(meshblocks,suburbs,householdTable2013,individualTablePart12013,individualTablePart22013,householdTable2006,individualTablePart12006,individualTablePart22006,householdTable2001,individualTablePart12001,individualTablePart22001,propertyStatsMeshblocks,propertyStatsSuburbs): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #
        
        # Copy the meshblocks feature class
        arcpy.CopyFeatures_management(meshblocks, propertyStatsMeshblocks, "", "0", "0", "0")

        # Join on the stats data
        arcpy.AddMessage("Joining 2013 Census data...")        
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", householdTable2013, "MeshblockNumber", "Tenure_Hh_Not_Own_2013;Tenure_Total_Hh_2013;Weekly_Rent_Median_Dollars_2013")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart12013, "MeshblockNumber", "Population_Count_Usual_Resident_2013")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart22013, "MeshblockNumber", "Personal_Inc_UR_Median_Dollars_2013")
        arcpy.AddMessage("Joining 2006 Census data...")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", householdTable2006, "MeshblockNumber", "Tenure_Hh_Not_Own_2006;Tenure_Total_Hh_2006;Weekly_Rent_Median_Dollars_2006")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart12006, "MeshblockNumber", "Population_Count_Usual_Resident_2006")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart22006, "MeshblockNumber", "Personal_Inc_UR_Median_Dollars_2006")        
        arcpy.AddMessage("Joining 2001 Census data...")          
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", householdTable2001, "MeshblockNumber", "Tenure_Hh_Not_Own_2001;Tenure_Total_Hh_2001;Weekly_Rent_Median_Dollars_2001")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart12001, "MeshblockNumber", "Population_Count_Usual_Resident_2001")
        arcpy.JoinField_management(propertyStatsMeshblocks, "MeshblockNumber", individualTablePart22001, "MeshblockNumber", "Personal_Inc_UR_Median_Dollars_2001")

        arcpy.AddMessage("Cleaning up fields...")           
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Hh_Not_Own_2013", "NotOwnedProperty2013", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Total_Hh_2013", "TotalProperty2013", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Weekly_Rent_Median_Dollars_2013", "WeeklyRent2013", "", "DOUBLE", "8", "NULLABLE", "false")        
        arcpy.AlterField_management(propertyStatsMeshblocks, "Population_Count_Usual_Resident_2013", "Population2013", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Personal_Inc_UR_Median_Dollars_2013", "MedianIncome2013", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Hh_Not_Own_2006", "NotOwnedProperty2006", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Total_Hh_2006", "TotalProperty2006", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Weekly_Rent_Median_Dollars_2006", "WeeklyRent2006", "", "DOUBLE", "8", "NULLABLE", "false")         
        arcpy.AlterField_management(propertyStatsMeshblocks, "Population_Count_Usual_Resident_2006", "Population2006", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Personal_Inc_UR_Median_Dollars_2006", "MedianIncome2006", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Hh_Not_Own_2001", "NotOwnedProperty2001", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Tenure_Total_Hh_2001", "TotalProperty2001", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Weekly_Rent_Median_Dollars_2001", "WeeklyRent2001", "", "DOUBLE", "8", "NULLABLE", "false")        
        arcpy.AlterField_management(propertyStatsMeshblocks, "Population_Count_Usual_Resident_2001", "Population2001", "", "DOUBLE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(propertyStatsMeshblocks, "Personal_Inc_UR_Median_Dollars_2001", "MedianIncome2001", "", "DOUBLE", "8", "NULLABLE", "false")

        arcpy.AddMessage("Calculating statistics...")
        arcpy.AddField_management(propertyStatsMeshblocks, "OwnedProperty2013", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "OwnedProperty2006", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "OwnedProperty2001", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "PercentRented2013", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "PercentRented2006", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "PercentRented2001", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "PopulationChangePercent2013", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(propertyStatsMeshblocks, "PopulationChangePercent2006", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")       
        arcpy.CalculateField_management(propertyStatsMeshblocks, "OwnedProperty2013", "!TotalProperty2013! - !NotOwnedProperty2013!", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "PercentRented2013", "(!NotOwnedProperty2013! / !TotalProperty2013!) * 100", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "OwnedProperty2006", "!TotalProperty2006! - !NotOwnedProperty2006!", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "PercentRented2006", "(!NotOwnedProperty2006! / !TotalProperty2006!) * 100", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "OwnedProperty2001", "!TotalProperty2001! - !NotOwnedProperty2001!", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "PercentRented2001", "(!NotOwnedProperty2001! / !TotalProperty2001!) * 100", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "PopulationChangePercent2013", "(( !Population2013! - !Population2006!)/ !Population2006!)*100", "PYTHON_9.3", "")
        arcpy.CalculateField_management(propertyStatsMeshblocks, "PopulationChangePercent2006", "(( !Population2006! - !Population2001!)/ !Population2001!)*100", "PYTHON_9.3", "")

        # Spatially join suburbs data
        arcpy.AddMessage("Creating statistics by suburb...")
        arcpy.SpatialJoin_analysis(suburbs, propertyStatsMeshblocks, os.path.join(arcpy.env.scratchGDB, "SuburbsMeshblocks"), "JOIN_ONE_TO_MANY", "KEEP_ALL", "", "INTERSECT", "", "")
        arcpy.Statistics_analysis(os.path.join(arcpy.env.scratchGDB, "SuburbsMeshblocks"), os.path.join(arcpy.env.scratchGDB, "SuburbsStats"), "NotOwnedProperty2013 SUM;TotalProperty2013 SUM; WeeklyRent2013 MEAN; Population2013 SUM;MedianIncome2013 MEAN;OwnedProperty2013 SUM;PercentRented2013 MEAN;PopulationChangePercent2013 MEAN;NotOwnedProperty2006 SUM;TotalProperty2006 SUM; WeeklyRent2006 MEAN; Population2006 SUM;MedianIncome2006 MEAN;OwnedProperty2006 SUM;PercentRented2006 MEAN;PopulationChangePercent2006 MEAN;NotOwnedProperty2001 SUM;TotalProperty2001 SUM;WeeklyRent2001 MEAN;Population2001 SUM;MedianIncome2001 MEAN;OwnedProperty2001 SUM;PercentRented2001 MEAN", "SUBURB_4THORDER")
        # Copy the suburbs feature class
        arcpy.CopyFeatures_management(suburbs, propertyStatsSuburbs, "", "0", "0", "0")
        # Join on property stats suburb data
        arcpy.JoinField_management(propertyStatsSuburbs, "SUBURB_4THORDER", os.path.join(arcpy.env.scratchGDB, "SuburbsStats"), "SUBURB_4THORDER", "")
        arcpy.AlterField_management(propertyStatsSuburbs, "SUBURB_4THORDER", "Suburb", "", "TEXT", "60", "NULLABLE", "false")

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
    
