# ArcGIS Data Toolkit

The ArcGIS Data Toolkit contains a number of tools and scripts to update and convert data from a varierty of different sources. The following tools are available:

#### Update from Link
Downloads a zipped up file geodatabase from a download link. Updates data in a geodatabase from the zip file and 
will update the datasets with the same name in the specified geodatabase.

![DataUpdateFromLinkScreenshot](/images/DataUpdateFromLinkScreenshot.jpg)

#### Update from Zip
Updates data in a geodatabase from a zip file containing a geodatabase. Will get the latest zip file from update folder and 
update the datasets with the same name in the specified geodatabase.

#### Update from CSV
Updates data in a geodatabase from a CSV file. Will get the latest zip CSV from update folder and 
updates the dataset with the same name in the specified geodatabase.

#### Google Drive Upload (IN DEVELOPMENT)
Uploads a specified file to Google Drive account.

#### Web Data Upload
Copies data to be replicated into geodatabase and zips this up. Zip file is then uploaded to FTP site 
for loading into a geodatabase.

#### Remote Server Data Update
This combines two of the above tools to update data on a remote web server. It consists of two geoporcessing tasks (one to be
setup on the server and one to be setup where the data is located).

* WebDataUpload will zip up datasets and upload them to the server via FTP
* DataUpdateFromZip will unzip datasets and load them into the database on the server
* WebDataUpload is the main script to be run and will call the DataUpdateFromZip tool via a geoprocessing service

#### Convert to CSV
Converts a table or feature class to a CSV file. Optionally adds in header and footer records also.


## Features

* Automate the data update process.
* Get data from zip or CSV and import into database.
* Easy way to update data on web server.
* Two options - New or existing.

## Requirements

* ArcGIS for Desktop 10.0+
	* Update from Zip

* ArcGIS for Desktop 10.1+
	* Update from Link
	* Update from CSV
	* Web Data Upload

* Remote Server Data Update Requirements
	* ArcGIS for Server 10.1+
	* FTP server setup on server
	* Setup DataUpdateFromZip tool as Geoprocessing service with these parameters:
		* Log File is a constant (defined when publishing tool)
		* Database is a constant (defined when publishing tool)
		* Update folder is a constant (defined when publishing tool)
		* Update mode can be existing or new (defined when running)


## Installation Instructions

* Setup a script to run as a scheduled task
	* Fork and then clone the repository or download the .zip file. 
	* Edit the [batch file](/Examples) to be automated and change the parameters to suit your environment.
	* Open Windows Task Scheduler and setup a new basic task.
	* Set the task to execute the batch file at a specified time.

## Resources

* [LinkedIn](http://www.linkedin.com/in/sfweston)
* [GitHub](https://github.com/WestonSF)
* [Twitter](https://twitter.com/Westonelli)
* [Blog](http://westonelli.wordpress.com)
* [ArcGIS API for Javascript](https://developers.arcgis.com/en/javascript)
* [Python for ArcGIS](http://resources.arcgis.com/en/communities/python)


## Issues

Find a bug or want to request a new feature?  Please let me know by submitting an issue.


## Contributing

Anyone and everyone is welcome to contribute. 


## Licensing
Copyright 2014 - Shaun Weston

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.