/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2016 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#ifndef CRAYFISH_H
#define CRAYFISH_H

#include <QString>

#include "crayfish_mesh.h"

//class Mesh;
class DataSet;
class ColorMap;

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
      Err_IncompatibleMesh,
      Err_InvalidData,
      Err_MissingDriver
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

  static bool exportRawDataToTIF(const Output* output, double mupp, const QString& outFilename, const QString& projWkt);
  static bool exportContoursToSHP(const Output* output, double mupp, double interval, const QString& outFilename, const QString& projWkt, bool useLines, ColorMap* cm);

protected:
  static Mesh* loadSWW(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadGRIB(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadMesh2DM(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadFlo2D(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadHec2D(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadNetCDF(const QString& fileName, LoadStatus* status = 0);
  static Mesh* loadSerafin(const QString& fileName, LoadStatus* status = 0);

  static Mesh::DataSets loadBinaryDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status = 0);
  static Mesh::DataSets loadAsciiDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status = 0);
  static Mesh::DataSets loadXmdfDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status = 0);
};

#endif // CRAYFISH_H
