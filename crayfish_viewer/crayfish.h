#ifndef CRAYFISH_H
#define CRAYFISH_H

#include <QString>

class Mesh;
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

  static DataSet* loadDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status = 0);

protected:
  static DataSet* loadBinaryDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status = 0);
  static DataSet* loadAsciiDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status = 0);
};

#endif // CRAYFISH_H
