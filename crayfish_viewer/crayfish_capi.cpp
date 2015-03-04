
#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#define CF_TYPES
typedef Mesh* MeshH;
typedef const Node* NodeH;
typedef const Element* ElementH;
typedef DataSet* DataSetH;
typedef const Output* OutputH;

#include "crayfish_capi.h"

static LoadStatus sLastLoadStatus;


int CF_Version()
{
  // TODO: generate automatically
  return 0x010300; // 1.3
}


MeshH CF_LoadMesh(const char* meshFile)
{
  return (MeshH) Crayfish::loadMesh(QString::fromUtf8(meshFile), &sLastLoadStatus);
}


void CF_CloseMesh(MeshH mesh)
{
  delete mesh;
}


int CF_Mesh_nodeCount(MeshH mesh)
{
  return mesh->nodes().count();
}


int CF_Mesh_elementCount(MeshH mesh)
{
  return mesh->elements().count();
}


NodeH CF_Mesh_nodeAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->nodes().count())
    return 0;

  const Node& n = mesh->nodes()[index];
  return &n;
}


ElementH CF_Mesh_elementAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->elements().count())
    return 0;

  const Element& e = mesh->elements()[index];
  return &e;
}


int CF_Mesh_dataSetCount(MeshH mesh)
{
  return mesh->dataSets().count();
}


DataSetH CF_Mesh_dataSetAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->dataSets().count())
    return 0;

  DataSet* ds = mesh->dataSets()[index];
  return ds;
}


int CF_DS_type(DataSetH ds)
{
  return ds->type();
}


// helper to return string data - without having to deal with memory too much.
// returned pointer is valid only next call. also not thread-safe.
const char* _return_str(const QString& str)
{
  static QByteArray lastStr;
  lastStr = str.toUtf8();
  return lastStr.constData();
}


const char* CF_DS_name(DataSetH ds)
{
  return _return_str(ds->name());
}


int CF_DS_outputCount(DataSetH ds)
{
  return ds->outputCount();
}


OutputH CF_DS_outputAt(DataSetH ds, int index)
{
  if (index < 0 || index >= ds->outputCount())
    return 0;

  return ds->output(index);
}


float CF_O_time(OutputH o)
{
  return o->time;
}


float CF_O_valueAt(OutputH o, int index)
{
  return o->values[index];
}

char CF_O_statusAt(OutputH o, int index)
{
  return o->statusFlags[index];
}

bool CF_Mesh_loadDataSet(MeshH mesh, const char* path)
{
  Mesh::DataSets lst = Crayfish::loadDataSet(QString::fromUtf8(path), mesh, &sLastLoadStatus);
  if (!lst.count())
    return false;

  mesh->dataSets() << lst;
  return true;
}


int CF_LastLoadError()
{
  return sLastLoadStatus.mLastError;
}


int CF_LastLoadWarning()
{
  return sLastLoadStatus.mLastWarning;
}


