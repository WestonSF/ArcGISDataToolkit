#-------------------------------------------------------------
# Name:       Convert to CSV
# Purpose:    Converts a table or feature class to a CSV file. Optionally adds in header and footer
#             records also.
# Author:     Shaun Weston (shaun_weston@eagle.co.nz)
# Date Created:    16/01/2014
# Last Updated:    16/01/2014
# Copyright:   (c) Eagle Technology
# ArcGIS Version:   10.1+
# Python Version:   2.7
#--------------------------------

# Import modules and enable data to be overwritten
import os
import sys
import datetime
import smtplib
import string
import csv
import arcpy
arcpy.env.overwriteOutput = True

# Set variables
logInfo = "false"
logFile = r""
sendEmail = "true"
emailTo = ""
emailUser = ""
emailPassword = ""
emailSubject = ""
emailMessage = ""
output = None

# Start of main function
def mainFunction(featureClasses,tables,csvDelimiter,headerFooter,outputFolder): # Get parameters from ArcGIS Desktop tool by seperating by comma e.g. (var1 is 1st parameter,var2 is 2nd parameter,var3 is 3rd parameter)  
    try:
        # Log start
        if logInfo == "true":
            loggingFunction(logFile,"start","")

        # --------------------------------------- Start of code --------------------------------------- #
        # Check input datasets are provided
        if ((len(featureClasses) > 0) or (len(tables) > 0)):
            arcpy.AddMessage("Creating CSV(s)...")        
            # Load the feature classes and tables into a list if input values provided
            if (len(featureClasses) > 0):       
                # Remove out apostrophes
                featureclassList = string.split(str(featureClasses).replace("'", ""), ";")
                
                # Loop through the feature classes
                for featureclass in featureclassList:
                    # Create a Describe object from the dataset
                    describeDataset = arcpy.Describe(featureclass)
                
                    # Create a CSV file and write values from feature class
                    with open(os.path.join(outputFolder, describeDataset.name + ".csv"), 'wb') as f:
                        if csvDelimiter == "|":
                            writer = csv.writer(f, delimiter="|")                            
                        if csvDelimiter == ";":
                            writer = csv.writer(f, delimiter=";")                            
                        if csvDelimiter == ",":                            
                            writer = csv.writer(f, delimiter=",")

                        # Add in header information if required
                        headerRow = []
                        if headerFooter == "true":
                            headerRow.append("H")
                            headerRow.append(describeDataset.name + ".csv")                                  
                        writer.writerow(headerRow)
                        
                        fieldNames = []
                        # Open up feature class and get the header values then write to first line
                        for f in arcpy.ListFields(featureclass):
                            fieldNames.append(f.name)
                        writer.writerow(fieldNames)
                        # Write in each of the values for all of the records
                        with arcpy.da.SearchCursor(featureclass, "*") as cursor:
                            # For each row in the table
                            for row in cursor:
                                # For each value in the row
                                values = []
                                for value in row:
                                    # Append to list
                                    values.append( str(value) )
                                # Write the row to the CSV file       
                                writer.writerow(values)

                        # Add in footer information if required
                        footerRow = []
                        if headerFooter == "true":
                            footerRow.append("F")
                            footerRow.append(describeDataset.name + ".csv")
                            rowCount = arcpy.GetCount_management(featureclass)
                            footerRow.append(rowCount)
                        writer.writerow(footerRow)                                      
            if (len(tables) > 0):
                # Remove out apostrophes            
                tableList = string.split(str(tables).replace("'", ""), ";")

                # Loop through the tables
                for table in tableList:
                    # Create a Describe object from the dataset
                    describeDataset = arcpy.Describe(table)
               
                    # Create a CSV file and write values from table
                    with open(os.path.join(outputFolder, describeDataset.name + ".csv"), 'wb') as f:
                        if csvDelimiter == "|":
                            writer = csv.writer(f, delimiter="|")                            
                        if csvDelimiter == ";":
                            writer = csv.writer(f, delimiter=";")                            
                        if csvDelimiter == ",":
                            writer = csv.writer(f, delimiter=",")

                        # Add in header information if required
                        headerRow = []
                        if headerFooter == "true":
                            headerRow.append("H")
                            headerRow.append(describeDataset.name + ".csv")                                  
                        writer.writerow(headerRow)
                        
                        fieldNames = []
                        # Open up table and get the header values then write to first line
                        for f in arcpy.ListFields(table):
                            fieldNames.append(f.name)
                        writer.writerow(fieldNames)
                        # Write in each of the values for all of the records
                        with arcpy.da.SearchCursor(table, "*") as cursor:
                            # For each row in the table
                            for row in cursor:
                                # For each value in the row
                                values = []
                                for value in row:  
                                    # Append to list
                                    values.append( str(value) )
                                # Write the row to the CSV file       
                                writer.writerow(values)

                        # Add in footer information if required
                        footerRow = []
                        if headerFooter == "true":
                            footerRow.append("F")
                            footerRow.append(describeDataset.name + ".csv")
                            rowCount = arcpy.GetCount_management(table)
                            footerRow.append(rowCount)
                        writer.writerow(footerRow)                            
        else:
            arcpy.AddMessage("Process stopped: No datasets provided") 
            # Log error
            if logInfo == "true":         
                loggingFunction(logFile,"error","\nProcess stopped: No datasets provided")
                
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
        arcpy.AddMessage(e.args[1])
        arcpy.AddMessage(e.args[2])
        arcpy.AddMessage(e.args[3])
        arcpy.AddMessage(e.args[4])          
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
    
