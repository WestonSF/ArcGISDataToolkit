# Data Update

### Two tools are available:

### Remote Server Data Update
This tool is a process to update data on a remote web server. It consists of two geoporcessing tasks (one to be
setup on the server and one to be setup where the data is located).

* WebDataUpload will zip up datasets and upload them to the server via FTP
* DataUpdateFromZip will unzip datasets and load them into the database on the server
* WebDataUpload is the main script to be run and will call the DataUpdateFromZip tool via a geoprocessing service

### Update from Link
This tool will update data in a geodatabase from a link provided. This link provided will contain a zipped up geodatabase.

![Screenshot](/Screenshot.jpg)


## Features

* Easy way to update data on web server
* Two options - New or existing


## Requirements

* FTP server setup on server
* Setup DataUpdateFromZip tool as Geoprocessing service with these parameters:
	* Log File is a constant (defined when publishing tool)
	* Database is a constant (defined when publishing tool)
	* Update folder is a constant (defined when publishing tool)
	* Update mode can be existing or new (defined when running)


## Resources

* [Blog](http://westonelli.wordpress.com)
* [Twitter](https://twitter.com/Westonelli)


## Issues

Find a bug or want to request a new feature?  Please let us know by submitting an issue.


## Contributing

Anyone and everyone is welcome to contribute. 


## Licensing
Copyright 2013 Shaun Weston

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.