#Data Upload & Update

- WebDataUpload will zip up datasets and upload them to the server via FTP
- DataUpdateFromZip will unzip datasets and load them into the database on the server
- WebDataUpload is the main script to be run and will call the DataUpdateFromZip tool via a geoprocessing service

This is where you write an awesome description of your project.  Who, what, why, when, where.

[](View it live)

![](Screenshot)


## Features
* feature 1
* feature 2


## Instructions

1. Fork and then clone the repo or download the .zip file. 
2. Run and try the examples.


## Requirements

* FTP server setup
* Setup DataUpdateFromZip tool as Geoprocessing service (public as secure doesn't work) with these parameters:
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
Copyright 2013 Splice Group

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the repository's [license.txt]() file.
