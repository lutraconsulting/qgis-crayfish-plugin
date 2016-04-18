# Crayfish API documentation

The plugin comes with Python API that may be used from console, from user scripts or within other plugins.

## Loading Data

In order to load some data with Crayfish, we will use ```Mesh``` class from ```crayfish``` module.

```python
import crayfish

mesh = crayfish.Mesh("/path/mesh.2dm")
```

Some file formats (e.g. AnuGA's SWW format) contain everything in one file - mesh structure definition
and simulation datasets - while others (like 2DM) only contain mesh structure. For such formats,
it is possible to load the extra data files:

```python
mesh.load_data("/path/mesh_data.dat")
```

## Exploring Data

```Mesh``` is the central data structure in Crayfish. It defines
structure of the mesh (nodes and elements) and it keeps track of any associated
data with the mesh (organized into datasets).

Each ```Mesh``` object contains one or more datasets (```DataSet``` objects).
One dataset represents one quantity that might be either constant or varying in time.
Data are organized into 'outputs' (```Output``` objects) - each dataset contains one or more of those,
each output represents the quantity at a particular timestep.

To get a list of datasets within a ```Mesh``` object:

```python
for dataset in mesh.datasets():
    print dataset
```

To access a particular dataset:

```python
ds1 = mesh.dataset(0)    # get first dataset
ds2 = mesh.dataset_from_name('Depth')   # get dataset identified by its name
```

To get a list of outputs of a ```DataSet``` object:

```python
ds = mesh.dataset(1)
for output in ds.outputs():
    print output
```

To access a particular output:

```python
ds.output(2)   # get third output
```


## Open Data as a Layer

The example above will only load the data files, but it will not create a map layer in QGIS.
In order to do that, we need to create instance of ```CrayfishPluginLayer``` class and add
the layer to the layer registry:

```python
import crayfish.plugin_layer

layer = crayfish.plugin_layer.CrayfishPluginLayer("/path/mesh.2dm")
QgsMapLayerRegistry.instance().addMapLayer(layer)
```

## Working with a Layer

The layer contains the ```Mesh``` object as well as other data necessary for visualization of the layer
(e.g. colormap used for rendering of contours).

If there is a need to access the underlying mesh:
```python
mesh = layer.mesh
```

Each layer also keeps track of its currently selected dataset and current time:

```python
layer.currentDataSet()   # returns DataSet instance
layer.currentOutput()    # returns Output instance at current time of current dataset
```

## Extracting Data for Plots

Crayfish has support for two types of plots:

* **Time series plot** of dataset values at a certain point on map over all timesteps of a given dataset
* **Cross-section plot** of output values (at one timestep) sampled from given linestring geometry

To extract data for time series plot:

```python
import crayfish.plot

point_geometry = QgsGeometry.fromPoint(QgsPoint(1020,1001))
x, y = crayfish.plot.timeseries_plot_data(mesh.dataset(1), point_geometry)
```

The returned variables ```x``` and ```y``` are arrays of the same length (equal to dataset's number of timesteps) with data for X/Y plot.

To extract data for cross-section plot:

```python
import crayfish.plot

line_geometry = QgsGeometry.fromPolyline([QgsPoint(1000,1005), QgsPoint(1028,1005)])
x, y = crayfish.plot.cross_section_plot_data(mesh.dataset(1).output(0), line_geometry, 0.5)
```

The function ```cross_section_plot_data``` returns ```x``` and ```y``` just like ```timeseries_plot_data``` does. In addition, it has third optional argument ```resolution``` that defines distance between samples from the input geometry in map units (the default value is ```1```).

Additionally, there is ```show_plot``` convenience function to open a new window with data visualized on X/Y plot.

```python
crayfish.plot.show_plot(x, y)
```

Crayfish internally uses [PyQtGraph](http://www.pyqtgraph.org/documentation/index.html) module for display of graphs. Users may import the module an make use of it themselves (please see PyQtGraph documentation to learn more).

```python
import crayfish.pyqtgraph as pg
```

## Using Geometries from Layers

In the code examples above we have shown how to use a manually constructed point or linestring geometry (```QgsGeometry``` objects).
It is often useful to use geometries from an existing vector layer instead of specifying coordinates in the code.
First we will need a reference to ```QgsVectorLayer``` object. Here is how to open a shapefile:

```python
layer = QgsVectorLayer("/data/my_points.shp", "Points", "ogr")

if not layer.isValid():
    print "Failed to load layer!"
```

The first argument of ```QgsVectorLayer``` constructor is the path, the second one is layer name (any name would do), and the last
one being provider name (```ogr``` stands for GDAL/OGR library used for loading of a variety of file formats).
See [Loading Layers](http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/loadlayer.html) for more details.

Other option to get a reference to a layer is to use a layer from QGIS environment. There are several ways to do that,
the easiest is to get currently selected layer:

```python
from qgis.utils import iface
layer = iface.activeLayer()
```

Once we have a reference to a vector layer, we can fetch its features that contain attributes and geometries.
This is how to access geometry from feature with ID 123:

```python
feature = layer.getFeatures(QgsFeatureRequest(123)).next()
geometry = feature.geometry()
```

The returned geometry object is of type ```QgsGeometry``` which is consumed by Crayfish plot functions mentioned above.
A geometry object may contain any type of geometry - a point, linestring, polygon or even a collection of them,
so make sure to use a layer with correct geometry type.

To get all geometries of a layer, the following code may be used to get a list of ```QgsGeometry``` objects:

```python
geometries = []
for feature in layer.getFeatures():
    geometries.append(QgsGeometry(feature.geometry()))
```

## Examples

There are several examples within the Crayfish plugin code that demonstrate data loading and plotting functionality, including writing of CSV files and export of plot images. They can be run from QGIS python console just by using one of the following imports:

```python
import crayfish.examples.plot_timeseries_simple
import crayfish.examples.plot_cross_section_simple
import crayfish.examples.plot_cross_section_from_layer
import crayfish.examples.plot_cross_section_multiple_datasets
```
