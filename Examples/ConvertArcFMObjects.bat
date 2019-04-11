:: ----- Convert ArcFM Objects -----
:: Parameters:
:: 	Location of geodatabase - Can be file geodatabase, personal geodatabase or SDE connection file
::	Location of the output file geodatabase
:: 	Set to true to copy all datasets to output geodatabase or false to convert input geodatabase
:: 	List of datasets to ignore - Seperated by a comma e.g. "Dataset1,Dataset2"
c:\python27\arcgis10.6\python "C:\Development\Python for ArcGIS Tools\ArcGIS Data Toolkit\ConvertArcFMObjects.py" ^
 "C:\Temp\ArcFMGasMDB.mdb" ^
 "C:\Temp\NewDatabase.gdb" ^
 "true" ^
 ""