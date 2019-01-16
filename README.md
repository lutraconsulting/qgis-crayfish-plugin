[![Coverage Status](https://coveralls.io/repos/github/lutraconsulting/qgis-crayfish-plugin/badge.svg?branch=iss_366_setup_travis)](https://coveralls.io/github/lutraconsulting/qgis-crayfish-plugin?branch=master)

Crayfish (QGIS plugin)
======================

<img align="right" src="https://raw.githubusercontent.com/lutraconsulting/qgis-crayfish-plugin/master/crayfish/images/crayfish_128px.png">

The Crayfish Plugin is a visualiser for temporal structured/unstructured grids in QGIS.

You can use Crayfish to load the file formats supported by [MDAL](https://github.com/lutraconsulting/MDAL)

Works on Windows, Linux and MacOS.

### Crayfish 3 vs Crayfish 2

In QGIS 2.x & Crayfish 2.x all features were implemented through QGIS's plugin layer. Rendering and format reading 
were written in C++ language and hence Crayfish 2 was shipped as C++ library and QGIS python plugin. 

In QGIS 3.4 & Crayfish 3.x, the C++ library was abandon and replaced by [MDAL](https://github.com/lutraconsulting/MDAL) 
data provider for data (format) reading and QGIS Core enhancement (QgsMeshLayer). 
 
Here is the table that helps to understand where the implementation was moved and where to report issues with Crayfish:

|                   | MDAL  | QGIS 3.x  |  Crayfish 3.x  | 
|-------------------|-------|-----------|----------------|
| grid input        |   X   |           |                |
| data input        |   X   |           |                |
| rendering         |       |     X     |                |
| identify          |       |     X     |                |
| styling           |       |     X     |                |
| time slider       |       |     X     |                |
| export grid       |       |     X*    |                |
| export contours   |       |     X*    |                |
| trace animation   |       |     X*    |                |
| plots             |       |           |        X       |
| export animations |       |           |        X       |

`*` marks not implemented features

### Using Crayfish

For instructions of how to install and use Crayfish, please refer to the [Crayfish resources page][crp] on our website.

* load mesh layer with data source manager in QGIS 
* load datasets from properties panel in QGIS 
* style and browse with styling panel (f7)
* use plots and export animations with Crayfish plugin

### Installing

Use QGIS3 plugin manager to install latest crayfish version.

[crp]: http://www.lutraconsulting.co.uk/resources/crayfish

### Developement 

Please refer to QGIS official plugin development cookbook and practises.