#ifndef CRAYFISH_H
#define CRAYFISH_H

#include <QString>

#include "crayfish_mesh.h"

//class Mesh;
class DataSet;
class LoadStatus;

struct LoadStatus
{
  LoadStatus() { clear(); }

  void clear() { mLastError = Err_None; mLastWarning = Warn_None; }

  enum Error
  {
      Err_None,
      Err_NotEnoughMemory,
      Err_FileNotFound,
      Err_UnknownFormat,
      Err_IncompatibleMesh
  };


  enum Warning
  {
      Warn_None,
      Warn_UnsupportedElement,
      Warn_InvalidElements,
      Warn_ElementWithInvalidNode,
      Warn_ElementNotUnique,
      Warn_NodeNotUnique
  };

  Error mLastError;
  Warning  mLastWarning;
};


class Crayfish
{
public:
  //Crayfish();

  static Mesh* loadMesh(const QString& meshFile, LoadStatus* status = 0);

  static Mesh::DataSets loadDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status = 0);

protected:
  static Mesh::DataSets loadBinaryDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status = 0);
  static Mesh::DataSets loadAsciiDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status = 0);
  static Mesh::DataSets loadXmdfDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status = 0);

};

#endif // CRAYFISH_H
