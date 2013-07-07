Data Upload & Update Tool

Prerequisites:
 - FTP server setup
 - Setup DataUpdateFromZip tool as Geoprocessing service (public as secure doesn't work) with these parameters:
	- Log File is a constant (defined when publishing tool)
	- Database is a constant (defined when publishing tool)
	- Update folder is a constant (defined when publishing tool)
	- Update mode can be existing or new (defined when running)

- WebDataUpload will zip up datasets and upload them to the server via FTP
- DataUpdateFromZip will unzip datasets and load them into the database on the server
- WebDataUpload is the main script to be run and will call the DataUpdateFromZip tool via a geoprocessing service