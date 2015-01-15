#-------------------------------------------------------------
# Name:       Geodatabase Documentation
# Purpose:    Documents a geodatabase by exporting feature class, table and domain information to
#             a CSV file.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    15/01/2015
# Last Updated:    15/01/2015
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.3+
# Python Version:   2.7
#--------------------------------

# Import modules
import os
import sys
import logging
import smtplib
import arcpy
import csv

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
def mainFunction(geodatabase,outputFolder): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # --------------------------------------- Start of code --------------------------------------- #

        # Get a list of the feature classes and tables in the database
        arcpy.env.workspace = geodatabase
        featureClassList = arcpy.ListFeatureClasses()
        tableList = arcpy.ListTables()
        datasetList = featureClassList + tableList
        
        # Describe the workspace
        descWorkspace = arcpy.Describe(geodatabase)
        workspaceType = descWorkspace.workspaceType

        # Create the CSV files and setup headers
        datasetsCSVFile = open(os.path.join(outputFolder, descWorkspace.baseName + "_Datasets.csv"), 'wb')
        domainsCSVFile = open(os.path.join(outputFolder, descWorkspace.baseName + "_Domains.csv"), 'wb')

        datasetsWriter = csv.writer(datasetsCSVFile, delimiter=",")
        domainsWriter = csv.writer(domainsCSVFile, delimiter=",")
    
        # Add in header information   
        datasetsHeaderRow = ["Name","Dataset Type","Geometry","Spatial Reference","Versioned","Archived"]
        domainsHeaderRow = ["Name","Description","Domain Type", "Field Type"]
        singleDatasetHeaderRow = ["Name","Alias Name","Type","Domain","Is Nullable","Is Editable","Length"]
        singleDomainHeaderRow = ["Code","Description"]
        datasetsWriter.writerow(datasetsHeaderRow)
        domainsWriter.writerow(domainsHeaderRow)

        # For each dataset
        for dataset in datasetList:
            # Describe the dataset
            descDataset = arcpy.Describe(dataset)
            datasetName = descDataset.name
            dataType = descDataset.dataType

            arcpy.AddMessage("Documenting dataset - " + datasetName + "...")
            
            if (dataType.lower() == "featureclass"):
                shapeType = descDataset.shapeType
            else:
                shapeType = "Non-Spatial"
                
            if (dataType.lower() == "featureclass"):
                spatialReference = descDataset.spatialReference.name
            else:
                spatialReference = "Non-Spatial"
                
            if (workspaceType.lower() == "remotedatabase"):
                versionedEnabled = descDataset.isVersioned
            else:
                versionedEnabled = "False"
                
            if (workspaceType.lower() == "remotedatabase"):
                archiveEnabled = descDataset.isArchived
            else:
                archiveEnabled = "False"
                
            # Write in dataset information
            row = [datasetName,dataType,shapeType,spatialReference,versionedEnabled,archiveEnabled]
            datasetsWriter.writerow(row)

            with open(os.path.join(outputFolder, "Dataset_" + datasetName + ".csv"), 'wb') as file:
                singleDatasetWriter = csv.writer(file, delimiter=",")                                    
                singleDatasetWriter.writerow(singleDatasetHeaderRow)
                
                # Get a list of fields
                fields = arcpy.ListFields(dataset)
                
                # Iterate through the list of fields
                for field in fields:
                    fieldInfo = [field.name,field.aliasName,field.type,field.domain,field.isNullable,field.editable,field.length]
                    singleDatasetWriter.writerow(fieldInfo)

        # Get a list of domains on the geodatabase
        geodatabaseDomains = arcpy.da.ListDomains(geodatabase)      
        # For each of the domains
        for domain in geodatabaseDomains:
            domainName = domain.name
            domainDescription = domain.description
            domainType = domain.domainType
            domainFieldType = domain.type
            codedValues = domain.codedValues
            arcpy.AddMessage("Documenting domain - " + domainName + "...")            

            # Write in domain information
            row = [domainName,domainDescription,domainType,domainFieldType]
            domainsWriter.writerow(row)

            with open(os.path.join(outputFolder, "Domain_" + domainName + ".csv"), 'wb') as file:
                singleDomainWriter = csv.writer(file, delimiter=",")                                    
                singleDomainWriter.writerow(singleDomainHeaderRow)

                for codedValue in codedValues:
                    domainValue = codedValue
                    domainDescription = codedValues[codedValue]
                    domainInfo = [domainValue,domainDescription]
                    singleDomainWriter.writerow(domainInfo)
                
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
    
