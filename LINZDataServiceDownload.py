#-------------------------------------------------------------
# Name:       LINZ Data Service Download
# Purpose:    Downloads the data  from the LINZ data service by either downloading the entire dataset for WFS or downloading
#             the changeset and updating the data.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    09/05/2014
# Last Updated:    11/05/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1/10.2
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
output = None

# Start of main function
def mainFunction(key,layerID,downloadType,lastUpdateConfig,dataset): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Logging
        if (enableLogging == "true"):
            # Setup logging
            logger, logMessage = setLogging(logFile)
            # Log start of process
            logger.info("Process started.")
            
        # --------------------------------------- Start of code --------------------------------------- #
   
        # If downloading all data
        if (downloadType == "All"):

            # Setup URL
            wfsURL = "http://wfs.data.linz.govt.nz/" + key + "/v/x" + str(layerID)

            # Download data via WFS feed       
            arcpy.QuickImport_interop("WFS," + wfsURL + "/wfs?version=1.0.0&SRSName=EPSG:2193,\"RUNTIME_MACROS,\"\"PREFER_POST,No,PREFERRED_VERSION,1.0.0,USE_HTTP_AUTH,NO,HTTP_AUTH_USER,,HTTP_AUTH_PASSWORD,,HTTP_AUTH_METHOD,Basic,USE_PROXY_SERVER,NO,HTTP_PROXY,null,HTTP_PROXY_PORT,null,HTTP_PROXY_USER,,HTTP_PROXY_PASSWORD,,HTTP_PROXY_AUTH_METHOD,Basic,TABLELIST,\"\"\"\"\"\"\"\"\"\"\"\"x" + str(layerID) + "\"\"\"\"\"\"\"\"\"\"\"\",MAX_RESULT_FEATURES,,OUTPUT_FORMAT,,FILTER_EXPRESSION,,XSD_DOC,,FME_FEATURE_IDENTIFIER,,SRS_AXIS_ORDER,,MAP_EMBEDDED_OBJECTS_AS,ATTRIBUTES,MAP_PREDEFINED_GML_PROPERTIES,NO,MAP_GEOMETRY_COLUMNS,YES,MAP_COMPLEX_PROPERTIES_AS,\"\"\"\"Nested Attributes\"\"\"\",MAX_MULTI_LIST_LEVEL,,XML_FRAGMENTS_AS_DOCUMENTS,YES,FLATTEN_XML_FRAGMENTS,NO,FLATTEN_XML_FRAGMENTS_OPEN_LIST_BRACE,,FLATTEN_XML_FRAGMENTS_CLOSE_LIST_BRACE,,FLATTEN_XML_FRAGMENTS_SEPARATOR,,GML_READER_GROUP,,USE_OLD_READER,NO,DISABLE_XML_NAMESPACE_PROCESSING,NO,ARCGIS_CACHE_GROUP,,LOCAL_CACHE_EXPIRY,60,EXPOSE_ATTRS_GROUP,,WFS_EXPOSE_FORMAT_ATTRS,,USE_SEARCH_ENVELOPE,NO,SEARCH_ENVELOPE_MINX,0,SEARCH_ENVELOPE_MINY,0,SEARCH_ENVELOPE_MAXX,0,SEARCH_ENVELOPE_MAXY,0,CLIP_TO_ENVELOPE,NO,BBOX_COORDINATE_SYSTEM,<Unused>,_MERGE_SCHEMAS,YES\"\",META_MACROS,\"\"SourcePREFER_POST,No,SourcePREFERRED_VERSION,1.0.0,SourceUSE_HTTP_AUTH,NO,SourceHTTP_AUTH_USER,,SourceHTTP_AUTH_PASSWORD,,SourceHTTP_AUTH_METHOD,Basic,SourceUSE_PROXY_SERVER,NO,SourceHTTP_PROXY,null,SourceHTTP_PROXY_PORT,null,SourceHTTP_PROXY_USER,,SourceHTTP_PROXY_PASSWORD,,SourceHTTP_PROXY_AUTH_METHOD,Basic,SourceMAX_RESULT_FEATURES,,SourceOUTPUT_FORMAT,,SourceFILTER_EXPRESSION,,SourceXSD_DOC,,SourceFME_FEATURE_IDENTIFIER,,SourceSRS_AXIS_ORDER,,SourceMAP_EMBEDDED_OBJECTS_AS,ATTRIBUTES,SourceMAP_PREDEFINED_GML_PROPERTIES,NO,SourceMAP_GEOMETRY_COLUMNS,YES,SourceMAP_COMPLEX_PROPERTIES_AS,\"\"\"\"Nested Attributes\"\"\"\",SourceMAX_MULTI_LIST_LEVEL,,SourceXML_FRAGMENTS_AS_DOCUMENTS,YES,SourceFLATTEN_XML_FRAGMENTS,NO,SourceFLATTEN_XML_FRAGMENTS_OPEN_LIST_BRACE,,SourceFLATTEN_XML_FRAGMENTS_CLOSE_LIST_BRACE,,SourceFLATTEN_XML_FRAGMENTS_SEPARATOR,,SourceGML_READER_GROUP,,SourceUSE_OLD_READER,NO,SourceDISABLE_XML_NAMESPACE_PROCESSING,NO,SourceARCGIS_CACHE_GROUP,,SourceLOCAL_CACHE_EXPIRY,60,SourceEXPOSE_ATTRS_GROUP,,SourceWFS_EXPOSE_FORMAT_ATTRS,,SourceUSE_SEARCH_ENVELOPE,NO,SourceSEARCH_ENVELOPE_MINX,0,SourceSEARCH_ENVELOPE_MINY,0,SourceSEARCH_ENVELOPE_MAXX,0,SourceSEARCH_ENVELOPE_MAXY,0,SourceCLIP_TO_ENVELOPE,NO,SourceBBOX_COORDINATE_SYSTEM,<Unused>\"\",METAFILE,WFS,COORDSYS,,IDLIST,\"\"\"\"\"\"x" + str(layerID) + "\"\"\"\"\"\",__FME_DATASET_IS_SOURCE__,true\"", os.path.join(arcpy.env.scratchFolder, "layer_" + str(layerID) + ".gdb"))

        else:
        # Otherwise downloading changeset
            # Get the to date (current date)

            # Get the from date (date in config)            

            # Setup URL
            wfsURL = "http://wfs.data.linz.govt.nz/" + key + "/v/x" + str(layerID) + "-changeset"

            # Download data via WFS feed
            arcpy.QuickImport_interop("WFS," + wfsURL + "/wfs?version=1.0.0&SRSName=EPSG:2193&viewparams=from:2012-03-24;to:2012-08-01,\"RUNTIME_MACROS,\"\"PREFER_POST,No,PREFERRED_VERSION,1.0.0,USE_HTTP_AUTH,NO,HTTP_AUTH_USER,,HTTP_AUTH_PASSWORD,,HTTP_AUTH_METHOD,Basic,USE_PROXY_SERVER,NO,HTTP_PROXY,null,HTTP_PROXY_PORT,null,HTTP_PROXY_USER,,HTTP_PROXY_PASSWORD,,HTTP_PROXY_AUTH_METHOD,Basic,TABLELIST,\"\"\"\"\"\"\"\"\"\"\"\"x" + str(layerID) + "-changeset" + "\"\"\"\"\"\"\"\"\"\"\"\",MAX_RESULT_FEATURES,,OUTPUT_FORMAT,,FILTER_EXPRESSION,,XSD_DOC,,FME_FEATURE_IDENTIFIER,,SRS_AXIS_ORDER,,MAP_EMBEDDED_OBJECTS_AS,ATTRIBUTES,MAP_PREDEFINED_GML_PROPERTIES,NO,MAP_GEOMETRY_COLUMNS,YES,MAP_COMPLEX_PROPERTIES_AS,\"\"\"\"Nested Attributes\"\"\"\",MAX_MULTI_LIST_LEVEL,,XML_FRAGMENTS_AS_DOCUMENTS,YES,FLATTEN_XML_FRAGMENTS,NO,FLATTEN_XML_FRAGMENTS_OPEN_LIST_BRACE,,FLATTEN_XML_FRAGMENTS_CLOSE_LIST_BRACE,,FLATTEN_XML_FRAGMENTS_SEPARATOR,,GML_READER_GROUP,,USE_OLD_READER,NO,DISABLE_XML_NAMESPACE_PROCESSING,NO,ARCGIS_CACHE_GROUP,,LOCAL_CACHE_EXPIRY,60,EXPOSE_ATTRS_GROUP,,WFS_EXPOSE_FORMAT_ATTRS,,USE_SEARCH_ENVELOPE,NO,SEARCH_ENVELOPE_MINX,0,SEARCH_ENVELOPE_MINY,0,SEARCH_ENVELOPE_MAXX,0,SEARCH_ENVELOPE_MAXY,0,CLIP_TO_ENVELOPE,NO,BBOX_COORDINATE_SYSTEM,<Unused>,_MERGE_SCHEMAS,YES\"\",META_MACROS,\"\"SourcePREFER_POST,No,SourcePREFERRED_VERSION,1.0.0,SourceUSE_HTTP_AUTH,NO,SourceHTTP_AUTH_USER,,SourceHTTP_AUTH_PASSWORD,,SourceHTTP_AUTH_METHOD,Basic,SourceUSE_PROXY_SERVER,NO,SourceHTTP_PROXY,null,SourceHTTP_PROXY_PORT,null,SourceHTTP_PROXY_USER,,SourceHTTP_PROXY_PASSWORD,,SourceHTTP_PROXY_AUTH_METHOD,Basic,SourceMAX_RESULT_FEATURES,,SourceOUTPUT_FORMAT,,SourceFILTER_EXPRESSION,,SourceXSD_DOC,,SourceFME_FEATURE_IDENTIFIER,,SourceSRS_AXIS_ORDER,,SourceMAP_EMBEDDED_OBJECTS_AS,ATTRIBUTES,SourceMAP_PREDEFINED_GML_PROPERTIES,NO,SourceMAP_GEOMETRY_COLUMNS,YES,SourceMAP_COMPLEX_PROPERTIES_AS,\"\"\"\"Nested Attributes\"\"\"\",SourceMAX_MULTI_LIST_LEVEL,,SourceXML_FRAGMENTS_AS_DOCUMENTS,YES,SourceFLATTEN_XML_FRAGMENTS,NO,SourceFLATTEN_XML_FRAGMENTS_OPEN_LIST_BRACE,,SourceFLATTEN_XML_FRAGMENTS_CLOSE_LIST_BRACE,,SourceFLATTEN_XML_FRAGMENTS_SEPARATOR,,SourceGML_READER_GROUP,,SourceUSE_OLD_READER,NO,SourceDISABLE_XML_NAMESPACE_PROCESSING,NO,SourceARCGIS_CACHE_GROUP,,SourceLOCAL_CACHE_EXPIRY,60,SourceEXPOSE_ATTRS_GROUP,,SourceWFS_EXPOSE_FORMAT_ATTRS,,SourceUSE_SEARCH_ENVELOPE,NO,SourceSEARCH_ENVELOPE_MINX,0,SourceSEARCH_ENVELOPE_MINY,0,SourceSEARCH_ENVELOPE_MAXX,0,SourceSEARCH_ENVELOPE_MAXY,0,SourceCLIP_TO_ENVELOPE,NO,SourceBBOX_COORDINATE_SYSTEM,<Unused>\"\",METAFILE,WFS,COORDSYS,,IDLIST,\"\"\"\"\"\"x" + str(layerID) + "-changeset" + "\"\"\"\"\"\",__FME_DATASET_IS_SOURCE__,true\"", os.path.join(arcpy.env.scratchFolder, "layerChanges_" + str(layerID) + ".gdb"))

            # Compare changeset with original dataset
           
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
                errorMessage = e.args[i]
            else:
                errorMessage = errorMessage + " " + e.args[i]
        arcpy.AddError(errorMessage)              
        # Logging
        if (enableLogging == "true"):
            # Log error            
            logger.error(errorMessage)               
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
    mainFunction(*argv)
    
