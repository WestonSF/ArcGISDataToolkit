#-------------------------------------------------------------
# Name:       Data Update from Link
# Purpose:    Downloads a zipped up file geodatabase from a download link. Updates data in a geodatabase
#             from the zip file. Two update options:
#             Existing Mode - Will only update datasets that have the same name and will delete and
#             append records, so field names need to be the same.
#             New Mode - Copies all datasets from the geodatabase and loads into geodatabase. Requires
#             no locks on geodatabase.
# Created:    05/09/2013
# Copyright:   (c) Splice Group
# ArcGIS Version:   10.1+
# Python Version:   2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import datetime
import urllib
import zipfile
import uuid
import glob
import arcpy
arcpy.env.overwriteOutput = True
    
def gotoFunction(logFile,downloadLink,updateMode,geodatabase,featureDataset): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        #--------------------------------------------Logging--------------------------------------------#        
        #Set the start time
        setdateStart = datetime.datetime.now()
        datetimeStart = setdateStart.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set start time
        with open(logFile, "a") as f:
            f.write("---" + "\n" + "Data update process started at " + datetimeStart)
        #-----------------------------------------------------------------------------------------------#

        # Download the file from the link
        urllib.urlretrieve(downloadLink, os.path.join(arcpy.env.scratchFolder, "Data.zip"))
        
        # Unzip the file to the scrtach folder
        arcpy.AddMessage("Extracting zip file...")  
        zip = zipfile.ZipFile(os.path.join(arcpy.env.scratchFolder, "Data.zip"), mode="r")
        zip.extractall(arcpy.env.scratchFolder)

        # Get the newest unzipped database from the scratch folder
        database = max(glob.iglob(arcpy.env.scratchFolder + r"\*.gdb"), key=os.path.getmtime)

        # Assign the geodatbase workspace and load in the datasets to the lists
        arcpy.env.workspace = database
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
                   # If feature dataset provided, add that to path
                   if featureDataset:
                      arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase + "\\" + featureDataset, describeDataset.name), "", "0", "0", "0")                                      
                   else:
                      arcpy.CopyFeatures_management(eachFeatureclass, os.path.join(geodatabase, describeDataset.name), "", "0", "0", "0")
               else:
                    # If dataset exists in geodatabase, delete features and load in new data
                    if arcpy.Exists(os.path.join(geodatabase, eachFeatureclass)):
                        # If feature dataset provided, add that to path
                        if featureDataset:
                            arcpy.DeleteFeatures_management(os.path.join(geodatabase + "\\" + featureDataset, eachFeatureclass))
                            arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase + "//" + featureDataset, eachFeatureclass), "NO_TEST", "", "")                            
                        else:
                            arcpy.DeleteFeatures_management(os.path.join(geodatabase, eachFeatureclass))
                            arcpy.Append_management(os.path.join(arcpy.env.workspace, eachFeatureclass), os.path.join(geodatabase, eachFeatureclass), "NO_TEST", "", "")
                    else:
                        #--------------------------------------------Logging--------------------------------------------#
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated") 
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            f.write("\nWarning: " + os.path.join(geodatabase, eachFeatureclass) + " does not exist and won't be updated")
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
                        arcpy.DeleteRows_management(os.path.join(geodatabase, eachTable))
                        arcpy.Append_management(os.path.join(arcpy.env.workspace, eachTable), os.path.join(geodatabase, eachTable), "NO_TEST", "", "")
                    else:
                        #--------------------------------------------Logging--------------------------------------------#
                        arcpy.AddMessage("Warning: " + os.path.join(geodatabase, eachTable) + " does not exist and won't be updated") 
                        # Open log file to set warning
                        with open(logFile, "a") as f:
                            f.write("\nWarning: " + os.path.join(geodatabase, eachTable) + " does not exist and won't be updated")
                        #-----------------------------------------------------------------------------------------------#
                            
                           
        #--------------------------------------------Logging--------------------------------------------#           
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Data update process ended at " + datetimeEnd + "\n")
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------#                
        pass
    # If arcpy error    
    except arcpy.ExecuteError:
        #--------------------------------------------Logging--------------------------------------------#            
        arcpy.AddMessage(arcpy.GetMessages(2))    
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Data update process ended at " + datetimeEnd + "\n")
            f.write("There was an error: " + arcpy.GetMessages(2) + "\n")        
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------#
    # If python error
    except Exception as e:
        #--------------------------------------------Logging--------------------------------------------#           
        arcpy.AddMessage(e.args[0])           
        #Set the end time
        setdateEnd = datetime.datetime.now()
        datetimeEnd = setdateEnd.strftime("%d/%m/%Y - %H:%M:%S")
        # Open log file to set end time
        with open(logFile, "a") as f:
            f.write("\n" + "Data update process ended at " + datetimeEnd + "\n")
            f.write("There was an error: " + e.args[0] + "\n")        
            f.write("---" + "\n")
        #-----------------------------------------------------------------------------------------------# 
# End of function

# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE, 
# as a geoprocessing script tool, or as a module imported in
# another script
if __name__ == '__main__':
    # Arguments are optional - If running from ArcGIS Desktop tool, parameters will be loaded into *argv
    argv = tuple(arcpy.GetParameterAsText(i)
        for i in range(arcpy.GetArgumentCount()))
    gotoFunction(*argv)
    
