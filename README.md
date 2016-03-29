Crayfish (QGIS plugin)
======================

<img align="right" src="https://raw.githubusercontent.com/lutraconsulting/qgis-crayfish-plugin/master/crayfish/crayfish_128px.png">

The Crayfish Plugin for QGIS aspires to be a complete set of pre and post-processing tools for hydraulic modellers
using TUFLOW, BASEMENT, AnuGA, ISIS 2D and other packages.

<img src="https://travis-ci.org/lutraconsulting/qgis-crayfish-plugin.svg?branch=master">

### Using Crayfish

For instructions of how to install and use Crayfish, please refer to the [Crayfish resources page][crp] on our website.

### Installing Crayfish on Linux

For installing Crayfish on Linux you need:

* development environment and a compiler installed
* Qt4 and development tools
* HDF5 library (for XMDF format)
* NetCDF library (for AnuGA SWW format)
* GDAL library

On Debian/Ubuntu you need to install the following packages:

```bash
sudo apt-get install build-essential libqt4-dev qt4-qmake libgdal-dev libhdf5-dev libnetcdf-dev libproj-dev git
```

If all this packages are installed you can clone the crayfish plugin using the command:

```bash
git clone https://github.com/lutraconsulting/qgis-crayfish-plugin.git
```

After cloning the source you should run the installation script which compiles and installs everything
to user's QGIS python plugin directory (`~/.qgis2/python/plugins/crayfish`):

```bash
cd qgis-crayfish-plugin
./install.py
```

Now restart QGIS and you are able to use crayfish plugin on your Linux Computer.


### Installing Crayfish on Windows

For 32-bit version:

* Install Microsoft Visual Studio 2008
* Install OSGeo4W (32bit) to C:\OSGeo4W
* Run scripts\crayfish32.bat to build the crayfish DLL

For 64-bit version:

* Install Microsoft Visual Studio 2010
* Install OSGeo4W (64bit) to C:\OSGeo4W64
* Run scripts\crayfish64.bat to build the crayfish DLL


[crp]: http://www.lutraconsulting.co.uk/resources/crayfish
