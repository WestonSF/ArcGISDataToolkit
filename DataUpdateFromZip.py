#-------------------------------------------------------------
# Name:       Data Update From Zip
# Purpose:    Updates data in a geodatabase from a zip file containing a geodatabase. Will get latest
#             zip file from update folder. Two update options:
#             Existing Mode - Will only update datasets that have the same name and will delete and
#             append records, so field names need to be the same.
#             New Mode - Copies all datasets from the geodatabase and loads into geodatabase. Requires
#             no locks on geodatabase.
#             NOTE: If using ArcGIS 10.0 need to set scratch workspace as folder.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    31/05/2013
# Last Updated:    18/11/2013
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.0+
# Python Version:   2.6/2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import datetime
import zipfile
import uuid
import glob
import arcpy
arcpy.env.overwriteOutput = True

# Set variables
logInfo = "false"
logFile = r""
sendEmail = "false"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(updateFolder,updateMode,geodatabase): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Log start
        if logInfo == "true":
            loggingFunction(logFile,"start","")

        # --------------------------------------- Start of code --------------------------------------- #      
        # Get the arcgis version
        arcgisVersion = arcpy.GetInstallInfo()['Version']

        # Get the newest zip file from the update folder
        latestFile = max(glob.iglob(updateFolder + r"\*.zip"), key=os.path.getmtime)

        # Setup scratch folder differently depending on ArcGIS version
        if (arcgisVersion == "10.0"):     
            # Setup geodatabase to load data into in temporary workspace
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchWorkspace, "WebData-" + str(uuid.uuid1()))
        else:        
            # Setup geodatabase to load data into in temporary workspace
            tempFolder = arcpy.CreateFolder_management(arcpy.env.scratchFolder, "WebData-" + str(uuid.uuid1()))

        arcpy.AddMessage("Extracting zip file...")             
        # Extract the zip file to a temporary location
        zip = zipfile.ZipFile(latestFile, mode="r")
        zip.extractall(str(tempFolder))

        # Assign the geodatbase workspace and load in the datasets to the lists
        arcpy.env.workspace = os.path.join(str(tempFolder), "Data.gdb")
        featureclassList = arcpy.ListFeatureClasses()
        tableList = arcpy.ListTables()       

        arcpy.AddMessage("Copying datasets...")        
        # Load the feature classes into the geodatabase if at least one is in the geodatabase provided
        if (len(featureclassList) > 0):        
            # Loop through the feature classes
            for eachFeatureclass in featureclassList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachFeatureclass)
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):
                   # Copy feature class into geodatabase using the same dataset name
                   arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                        arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")
                    else:
                        #--------------------------------------------Logging--------------------------------------------#
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated") 
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            loggingFunction(logFile,"warning",os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated")
                        #-----------------------------------------------------------------------------------------------#
                            
        if (len(tableList) > 0):    
            # Loop through of the tables
            for eachTable in tableList:
               # Create a Describe object from the dataset
               describeDataset = arcpy.Describe(eachTable)
               # If update mode is then copy, otherwise delete and appending records                
               if (updateMode == "New"):               
                   # Copy feature class into geodatabase using the same dataset name
                   arcpy.TableSelect_analysis(eachTable, os.path.join(geodatabase, describeDataset.name), "")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachTable)):
                        arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachTable))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachTable), os.path.join(geodatabase, eachTable), "NO_TEST", "", "")
                    else:
                        # Log warning
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachTable) + " does not exist and won't be updated") 
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            loggingFunction(logFile,"warning",os.path.join(geodatabase, eachTable) + " does not exist and won't be updated")  
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
        # Log end
        if logInfo == "true":
            loggingFunction(logFile,"end","")        
        pass
    # If arcpy error
    except arcpy.ExecuteError:
        # Show the message
        arcpy.AddMessage(arcpy.GetMessages(2))        
        # Log error
        if logInfo == "true":  
            loggingFunction(logFile,"error",arcpy.GetMessages(2))
    # If python error
    except Exception as e:
        # Show the message
        arcpy.AddMessage(e.args[0])          
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
    
