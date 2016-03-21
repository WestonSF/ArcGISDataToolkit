REM ----- LINZ Data Service Download - Last 50 Earthquakes - Greater Wellington Region -----
c:\python27\arcgis10.3\python "C:\Development\Python for ArcGIS Tools\ArcGIS Data Toolkit\WFSDownload.py" ^
 "http://wfs.geonet.org.nz/geonet/ows" ^
 "1.1.0" ^
 "geonet:quake_search_v1&maxFeatures=50" ^
 "Layer" ^
 "1707030,5390440,1909170,5508180,EPSG:2193" ^
 "" ^
 "" ^
 "" ^
 "JSON" ^
 "C:\Temp\Scratch.gdb" ^
 "Earthquake"