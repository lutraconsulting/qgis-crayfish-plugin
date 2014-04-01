qgis-crayfish-plugin
====================

The Crayfish Plugin for QGIS aspires to be a complete set of pre and post-processing tools for hydraulic modellers using TUFLOW and other packages.

### Using Crayfish

For instructions of how to install and use Crayfish, please refer to the [Crayfish resources page][crp] on our website.

### Installing Crayfish on Linux

For installing Crayfish on Linux you need the development environment and a compiler installed (the build-essential package on debian based distributions should provide that).
You also need the libqt4-dev package and qt4-qmake.
If all this packages are installed you can clone the crayfish plugin using the command:


```bash
git clone https://github.com/lutraconsulting/qgis-crayfish-plugin.git
```

After cloning the source you should enter the directory crayfish_viewer:
```bash
cd crayfish_viewer
```

now use the commands:
```bash
qmake
make
./build-python.py
./install.py 
```

This copies the compiled cpp library to its place in the users homedirectory

~/.qgis/python/plugins/crayfish/

Now restart QGIS and you are able to use crayfish plugin on your Linux Computer.


### Todo

* Anti-aliasing
* Consider removing apply button as it seems redundant
* Implement full sanity checking of user input values in Vector properties dialog and suitable error mesages
* Implement display vectors on arbitrary grid
* Implement filter vectors by magnitude

[crp]: http://www.lutraconsulting.co.uk/resources/crayfish