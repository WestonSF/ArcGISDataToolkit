#-------------------------------------------------------------
# Name:       LINZ Mortgage Data Import
# Purpose:    Creates a mortgage feature class by parcel and suburb based of LINZ parcels and encumbrance data.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    25/04/2014
# Last Updated:    20/12/2014
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
def mainFunction(parcelFeatureClass,parcelTitleMatchTable,encumbranceTable,suburbsFeatureClass,mortgageFeatureClass,mortgageSuburbsFeatureClass): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Set the banks
        banks = ["ANZ","Westpac","BNZ","ASB","Kiwibank","Mortgage Holding Trust","Co-operative Bank","Rabobank","TSB","New Zealand Home Loans","Countrywide","AMP","Home Mortgage Company","PGG Wrightson","Sovereign","Other"]

        # Select out mortgage data
        arcpy.AddMessage("Extracting mortgage data...")
        arcpy.TableSelect_analysis(encumbranceTable, os.path.join(arcpy.env.scratchGDB, "Mortgage"), "instrument_type = 'Mortgage'")
        arcpy.TableSelect_analysis(parcelTitleMatchTable, os.path.join(arcpy.env.scratchGDB, "ParcelTitleMatch"), "")
        # Select parcel data
        arcpy.Select_analysis(parcelFeatureClass, os.path.join(arcpy.env.scratchGDB, "Parcel"), "")
        
        # Select most recent mortgage record for each title
        arcpy.AddMessage("Getting the most recent mortgage records...")
        # Add unique ID
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "Mortgage"), "FullID", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "Mortgage"), "FullID", "!title_no! + \" \" + !instrument_lodged_datetime!", "PYTHON_9.3", "")        
        arcpy.Statistics_analysis(os.path.join(arcpy.env.scratchGDB, "Mortgage"), os.path.join(arcpy.env.scratchGDB, "MortgageRecent"), "instrument_lodged_datetime MAX", "title_no")
        # Add unique ID
        arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "MortgageRecent"), "FullID", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "MortgageRecent"), "FullID", "!title_no! + \" \" + !MAX_instrument_lodged_datetime!", "PYTHON_9.3", "")
        # Join on description text
        arcpy.JoinField_management(os.path.join(arcpy.env.scratchGDB, "MortgageRecent"), "FullID", os.path.join(arcpy.env.scratchGDB, "Mortgage"), "FullID", "memorial_text")

        arcpy.AddMessage("Creating mortgage feature class...")
        # Join parcel and title data
        arcpy.MakeQueryTable_management(os.path.join(arcpy.env.scratchGDB, "Parcel") + ";" + os.path.join(arcpy.env.scratchGDB, "ParcelTitleMatch"), "ParcelTitlesLayer", "USE_KEY_FIELDS", "", "", "Parcel.id = ParcelTitleMatch.par_id")
        arcpy.Select_analysis("ParcelTitlesLayer", os.path.join(arcpy.env.scratchGDB, "ParcelTitles"), "")
        # Join parcel and mortgage data
        arcpy.MakeQueryTable_management(os.path.join(arcpy.env.scratchGDB, "ParcelTitles") + ";" + os.path.join(arcpy.env.scratchGDB, "MortgageRecent"), "ParcelTitlesMortgageLayer", "USE_KEY_FIELDS", "", "", "ParcelTitles.ttl_title_no = MortgageRecent.title_no")
        arcpy.Select_analysis("ParcelTitlesMortgageLayer", mortgageFeatureClass, "")

        # Cleaning up fields
        arcpy.AddMessage("Cleaning up fields...")
        arcpy.AddField_management(mortgageFeatureClass, "mortgage_provider", "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(mortgageFeatureClass, "mortgage_provider", "changeValue(!memorial_text!)", "PYTHON_9.3", "def changeValue(var):\\n  if \"ANZ\" in var:\\n    return \"ANZ\"\\n  if \"National Bank\" in var:\\n    return \"ANZ\"\\n  if \"Westpac\" in var:\\n    return \"Westpac\"\\n  if \"ASB\" in var:\\n    return \"ASB\"\\n  if \"Bank of New Zealand\" in var:\\n    return \"BNZ\"\\n  if \"Kiwibank\" in var:\\n    return \"Kiwibank\"\\n  if \"TSB\" in var:\\n    return \"TSB\"\\n  if \"Rabobank\" in var:\\n    return \"Rabobank\"\\n  if \"Co-operative Bank\" in var:\\n    return \"Co-operative Bank\"\\n  if \"PSIS\" in var:\\n    return \"Co-operative Bank\"\\n  if \"New Zealand Home Lending\" in var:\\n    return \"New Zealand Home Loans\"\\n  if \"AMP\" in var:\\n    return \"AMP\"\\n  if \"Home Mortgage Company\" in var:\\n    return \"Home Mortgage Company\"\\n  if \"Mortgage Holding Trust\" in var:\\n    return \"Mortgage Holding Trust\"\\n  if \"PGG Wrightson\" in var:\\n    return \"PGG Wrightson\"\\n  if \"Countrywide\" in var:\\n    return \"Countrywide\"\\n  if \"Sovereign\" in var:\\n    return \"Sovereign\"\\n  else:\\n    return \"Other\"\\n")
        arcpy.DeleteField_management(mortgageFeatureClass, "id;appellation;affected_surveys;parcel_intent;topology_type;statutory_actions;titles;survey_area;OBJECTID_1;id_1;ttl_title_no;source;OBJECTID_12;FREQUENCY;FullID")
        arcpy.AlterField_management(mortgageFeatureClass, "MAX_instrument_lodged_datetime", "date_lodged", "", "DATE", "8", "NULLABLE", "false")
        arcpy.AlterField_management(mortgageFeatureClass, "memorial_text", "description", "", "TEXT", "18000", "NULLABLE", "false")
        arcpy.AddField_management(mortgageFeatureClass, "land_area", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(mortgageFeatureClass, "land_area", "!SHAPE_Area!", "PYTHON_9.3", "")        

        # Spatially join suburb info
        arcpy.AddMessage("Analysing mortgages by suburb...")
        arcpy.SpatialJoin_analysis(mortgageFeatureClass, suburbsFeatureClass, os.path.join(arcpy.env.scratchGDB, "MortgageSuburbs"), "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT", "", "")
        # Summary stats for suburbs
        arcpy.Statistics_analysis(os.path.join(arcpy.env.scratchGDB, "MortgageSuburbs"), os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStats"), "mortgage_provider COUNT", "SUBURB_4THORDER;mortgage_provider")

        # Add the banks count fields
        for bank in banks:
            arcpy.AddField_management(os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStats"), bank.replace(" ", "_").replace("-", "_"), "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
            arcpy.CalculateField_management(os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStats"), bank.replace(" ", "_").replace("-", "_"), "0", "PYTHON_9.3", "")

        # Get the banks fields
        for count,value in enumerate(banks):
            banks[count] = value.replace(" ", "_").replace("-", "_")
            
        fields = ["SUBURB_4THORDER","mortgage_provider","FREQUENCY"] + banks
        with arcpy.da.UpdateCursor(os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStats"), fields) as cursor:
            # For each row
            for row in cursor:
                suburb = row[0]
                mortgageProvider = row[1]
                mortgageProvider = mortgageProvider.replace(" ", "_").replace("-", "_")
                count = row[2]

                # Update the mortgage provider row with its count
                row[fields.index(mortgageProvider)] = count
                cursor.updateRow(row)

        # Dissolve the stats
        arcpy.Statistics_analysis(os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStats"), os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStatsDissolved"), "FREQUENCY SUM;ANZ SUM;Westpac SUM;BNZ SUM;ASB SUM;Kiwibank SUM;Mortgage_Holding_Trust SUM;Co_operative_Bank SUM;Rabobank SUM;TSB SUM;New_Zealand_Home_Loans SUM;Countrywide SUM;AMP SUM;Home_Mortgage_Company SUM;PGG_Wrightson SUM;Sovereign SUM;Other SUM", "SUBURB_4THORDER")

        # Create mortgage suburbs feature class
        arcpy.AddMessage("Creating mortgage suburbs feature class...")
        arcpy.Select_analysis(suburbsFeatureClass, mortgageSuburbsFeatureClass, "")
        arcpy.AddField_management(mortgageSuburbsFeatureClass, "land_area", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.CalculateField_management(mortgageSuburbsFeatureClass, "land_area", "!SHAPE_Area!", "PYTHON_9.3", "")                
        # Join on mortgages suburb data
        arcpy.JoinField_management(mortgageSuburbsFeatureClass, "SUBURB_4THORDER", os.path.join(arcpy.env.scratchGDB, "MortgageSuburbsStatsDissolved"), "SUBURB_4THORDER", "")
        arcpy.DeleteField_management(mortgageSuburbsFeatureClass, "FREQUENCY;SUBURB_1STORDER;SUBURB_2NDORDER;SUBURB_3RDORDER")
        arcpy.AlterField_management(mortgageSuburbsFeatureClass, "SUBURB_4THORDER", "Suburb", "", "TEXT", "60", "NULLABLE", "false")
        arcpy.AlterField_management(mortgageSuburbsFeatureClass, "SUM_FREQUENCY", "SUM_ALL", "", "DOUBLE", "8", "NULLABLE", "false")
     
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
    
