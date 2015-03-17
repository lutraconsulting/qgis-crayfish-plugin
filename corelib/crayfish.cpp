#include "crayfish.h"

#include "crayfish_mesh_2dm.h"



Mesh* Crayfish::loadMesh(const QString& meshFile, LoadStatus* status)
{
  return loadMesh2DM(meshFile, status);
}

Mesh::DataSets Crayfish::loadDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status)
{
  if (status) status->clear();

  LoadStatus s;
  Mesh::DataSets lst;

  lst = loadBinaryDataSet(fileName, mesh, &s);
  if (status) *status = s;

  if (lst.count())
    return lst;

  // if the file format was not recognized, try to load it as ASCII dataset
  if (s.mLastError != LoadStatus::Err_UnknownFormat)
    return Mesh::DataSets();

  s.clear();

  lst = loadAsciiDataSet(fileName, mesh, &s);
  if (status) *status = s;

  if (lst.count())
    return lst;

  // if the file format was not recognized, try to load it as XMDF dataset
  if (s.mLastError != LoadStatus::Err_UnknownFormat)
    return Mesh::DataSets();

  s.clear();

  lst = loadXmdfDataSet(fileName, mesh, &s);
  if (status) *status = s;

  return lst;
}

