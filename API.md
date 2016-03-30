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
