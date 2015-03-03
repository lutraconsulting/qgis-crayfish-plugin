#include "crayfish.h"

#include "crayfish_mesh_2dm.h"



Mesh* Crayfish::loadMesh(const QString& meshFile, LoadStatus* status)
{
  return loadMesh2DM(meshFile, status);
}

DataSet* Crayfish::loadDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status)
{
  if (status) status->clear();

  LoadStatus s;

  DataSet* ds = loadBinaryDataSet(fileName, mesh, &s);
  if (status) *status = s;

  if (ds)
    return ds;

  // if the file format was not recognized, try to load it as ASCII dataset
  if (s.mLastError != LoadStatus::Err_UnknownFormat)
    return 0;

  s.clear();

  ds = loadAsciiDataSet(fileName, mesh, &s);
  if (status) *status = s;
  return ds;
}

