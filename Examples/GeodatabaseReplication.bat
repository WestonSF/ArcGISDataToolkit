:: --- Geodatabase Replication ---
:: Parameters:
::	Source geodatabase connection file or location
::	Destination geodatabase connection file or location
::	Option for copying datasets - "All" will copy all datasets in database or "Only From Configuration File" will only copy those listed in the configuration file
::	Update mode - "New" will copy and overwrite any existing datasets in the destination geodatabase or "Existing" will truncate and append the datasets in the destination geodatabase
::	Location of the configuration CSV file that lists the dataset names to copy over
::	Exclude list - List of dataset names to exclude from copying
:: 	Include views - "true" or "false" - Will include database views in the copying process (Views will have "vw" in the name of the dataset)
c:\python27\arcgis10.7\python "%~dp0..\GeodatabaseReplication.py" ^
 "C:\Temp\Data\GeneralData.gdb" ^
 "C:\Temp\Scratch.gdb" ^
 "Only From Configuration File" ^
 "New" ^
 "C:\Development\Python for ArcGIS Tools\ArcGIS Data Toolkit\Configuration\GeodatabaseReplication.csv" ^
 "" ^
 "false"