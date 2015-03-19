Crayfish (QGIS plugin)
======================

<img align="right" src="https://raw.githubusercontent.com/lutraconsulting/qgis-crayfish-plugin/master/plugin/crayfish_128px.png">

The Crayfish Plugin for QGIS aspires to be a complete set of pre and post-processing tools for hydraulic modellers using TUFLOW and other packages.

<img src="https://travis-ci.org/lutraconsulting/qgis-crayfish-plugin.svg?branch=master">

### Using Crayfish

For instructions of how to install and use Crayfish, please refer to the [Crayfish resources page][crp] on our website.

### Installing Crayfish on Linux

For installing Crayfish on Linux you need:

* development environment and a compiler installed
* Qt4 and development tools
* HDF5 library
* GDAL library

On Debian/Ubuntu you need to install the following packages:

```bash
sudo apt-get install build-essential libqt4-dev qt4-qmake libgdal-dev libhdf5-dev libproj-dev git
```


If all this packages are installed you can clone the crayfish plugin using the command:


```bash
git clone https://github.com/lutraconsulting/qgis-crayfish-plugin.git
```

After cloning the source you should enter the directory corelib:
```bash
cd qgis-crayfish-plugin/corelib
```

now use the commands:
```bash
qmake
make
./install.py 
```

This copies the compiled cpp library to its place in the users homedirectory

~/.qgis2/python/plugins/crayfish/

Now you only need to change from corelib into the plugin directory and install the python code with this commands:

```bash
cd ../plugin
./install.py 
```
Now restart QGIS and you are able to use crayfish plugin on your Linux Computer.


[crp]: http://www.lutraconsulting.co.uk/resources/crayfish
