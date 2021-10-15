# IMPORT GUITAR PRO MARKERS TO ABLETON

Script that put Guitar Pro markers into an already created Ableton project.

````
usage: main.py [-h] als_file gp_xml_file

Script to import Guitar Pro markers as locators in Ableton

positional arguments:
  als_file     Relative or absolute path to Ableton project '.als' file. It's been tested only with Ableton 10.1.41.
  gp_xml_file  XML file exported from Guitar Pro. It's been tested only witg Guitar Pro 7.5.5.

options:
  -h, --help   show this help message and exit
````

It's been tested using:
* **Ableton 10.1.41**
* **Guitar Pro 7.5.5**
* **Python 3.10.1**