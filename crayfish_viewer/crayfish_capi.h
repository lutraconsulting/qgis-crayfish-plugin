#ifndef CRAYFISH_CAPI_H
#define CRAYFISH_CAPI_H

extern "C"
{

int CF_Version();

/*#ifndef CF_TYPES
#define CF_TYPES
typedef void* MeshH;
#endif*/

MeshH CF_LoadMesh(const char* meshFile);

void CF_CloseMesh(MeshH mesh);

int CF_LastLoadError();
int CF_LastLoadWarning();

// Mesh functions

int CF_Mesh_nodeCount(MeshH mesh);
NodeH CF_Mesh_nodeAt(MeshH mesh, int index);

int CF_Mesh_elementCount(MeshH mesh);
ElementH CF_Mesh_elementAt(MeshH mesh, int index);

int CF_Mesh_dataSetCount(MeshH mesh);
DataSetH CF_Mesh_dataSetAt(MeshH mesh, int index);


bool CF_Mesh_loadDataSet(MeshH mesh, const char* path);

// DataSet functions

int CF_DS_type(DataSetH ds);
const char* CF_DS_name(DataSetH ds);

int CF_DS_outputCount(DataSetH ds);
OutputH CF_DS_outputAt(DataSetH ds, int index);

MeshH CF_DS_mesh(DataSetH ds);

// Output functions
float CF_O_time(OutputH o);
float CF_O_valueAt(OutputH o, int index);
char CF_O_statusAt(OutputH o, int index);
DataSetH CF_O_dataSet(OutputH o);

}

#endif // CRAYFISH_CAPI_H
