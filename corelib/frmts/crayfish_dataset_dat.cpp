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

#include "crayfish.h"

#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_mesh.h"

#include <QFile>
#include <QFileInfo>
#include <QScopedPointer>
#include <QTextStream>

#include <math.h>


static const int CT_VERSION   = 3000;
static const int CT_OBJTYPE   = 100;
static const int CT_SFLT      = 110;
static const int CT_SFLG      = 120;
static const int CT_BEGSCL    = 130;
static const int CT_BEGVEC    = 140;
static const int CT_VECTYPE   = 150;
static const int CT_OBJID     = 160;
static const int CT_NUMDATA   = 170;
static const int CT_NUMCELLS  = 180;
static const int CT_NAME      = 190;
static const int CT_TS        = 200;
static const int CT_ENDDS     = 210;
static const int CT_RT_JULIAN = 240;
static const int CT_TIMEUNITS = 250;

static const int CT_2D_MESHES = 3;
static const int CT_FLOAT_SIZE = 4;
static const int CF_FLAG_SIZE = 1;
static const int CF_FLAG_INT_SIZE = 4;

#define EXIT_WITH_ERROR(error)       {  if (status) status->mLastError = (error); return Mesh::DataSets(); }

static NodeOutput* _readTimestep(float t, bool isVector, bool hasStatus, QTextStream& stream, int nodeCount, int elemCount, QVector<int>& nodeIDToIndex);
static ElementOutput* _readTimestampElementCentered(float t, bool isVector, QTextStream& stream, int elemCount);

static bool readIStat(QDataStream& in, int sflg, char* flag) {
    if (sflg == CF_FLAG_SIZE) {
      if( in.readRawData(flag, sflg) != sflg )
          return true; // error
    } else {
      int istat;
      if( in.readRawData( (char*)&istat, sflg) != sflg )
          return true; // error
      else
          *flag = (istat == 1);
    }
    return false;
}

Mesh::DataSets Crayfish::loadBinaryDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status)
{
  // implementation based on information from:
  // http://www.xmswiki.com/wiki/SMS:Binary_Dataset_Files_*.dat

  QFile file(datFileName);
  if (!file.open(QIODevice::ReadOnly))
    EXIT_WITH_ERROR(LoadStatus::Err_FileNotFound);  // Couldn't open the file

  int nodeCount = mesh->nodes().count();
  int elemCount = mesh->elements().count();

  int card = 0;
  int version;
  int objecttype;
  int sflt;
  int sflg;
  int vectype;
  int objid;
  int numdata;
  int numcells;
  char name[40];
  char istat;
  float time;

  QDataStream in(&file);

  if( in.readRawData( (char*)&version, 4) != 4 )
    EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

  if( version != CT_VERSION ) // Version should be 3000
    EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

  QScopedPointer<DataSet> ds(new DataSet(datFileName));
  ds->setIsTimeVarying(true);

  // in TUFLOW results there could be also a special timestep (99999) with maximums
  // we will put it into a separate dataset
  QScopedPointer<DataSet> dsMax(new DataSet(datFileName));
  dsMax->setIsTimeVarying(false);

  while (card != CT_ENDDS)
  {
    if( in.readRawData( (char*)&card, 4) != 4 )
    {
      // We've reached the end of the file and there was no ends card
      break;
    }

    switch (card)
    {

    case CT_OBJTYPE:
      // Object type
      if( in.readRawData( (char*)&objecttype, 4) != 4 || objecttype != CT_2D_MESHES )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      break;

    case CT_SFLT:
      // Float size
      if( in.readRawData( (char*)&sflt, 4) != 4 || sflt != CT_FLOAT_SIZE )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      break;

    case CT_SFLG:
      // Flag size
      if( in.readRawData( (char*)&sflg, 4) != 4 )
        if (sflg != CF_FLAG_SIZE && sflg != CF_FLAG_INT_SIZE)
            EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      break;

    case CT_BEGSCL:
      ds->setType(DataSet::Scalar);
      dsMax->setType(DataSet::Scalar);
      break;

    case CT_BEGVEC:
      ds->setType(DataSet::Vector);
      dsMax->setType(DataSet::Vector);
      break;

    case CT_VECTYPE:
      // Vector type
      if( in.readRawData( (char*)&vectype, 4) != 4 || vectype != 0 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      break;

    case CT_OBJID:
      // Object id
      if( in.readRawData( (char*)&objid, 4) != 4 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      break;

    case CT_NUMDATA:
      // Num data
      if ( in.readRawData( (char*)&numdata, 4) != 4 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      if (numdata != nodeCount)
        EXIT_WITH_ERROR(LoadStatus::Err_IncompatibleMesh);
      break;

    case CT_NUMCELLS:
      // Num data
      if( in.readRawData( (char*)&numcells, 4) != 4 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      if(numcells != elemCount)
        EXIT_WITH_ERROR(LoadStatus::Err_IncompatibleMesh);
      break;

    case CT_NAME:
      // Name
      if( in.readRawData( (char*)&name, 40) != 40 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      if(name[39] != 0)
          name[39] = 0;
      ds->setName(QString(name).trimmed());
      dsMax->setName(ds->name() + "/Maximums");
      break;

    case CT_TS:
      // Time step!
      if( readIStat(in, sflg, &istat) )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

      if( in.readRawData( (char*)&time, 4) != 4 )
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

      QScopedPointer<NodeOutput> o(new NodeOutput);
      o->time = time;
      try
      {
        o->init(nodeCount, elemCount, ds->type() == DataSet::Vector);
      }
      catch (const std::bad_alloc &)
      {
        EXIT_WITH_ERROR(LoadStatus::Err_NotEnoughMemory);
      }

      if (istat)
      {
        // Read status flags
        char* active = o->getActive().data();
        for (int i=0; i < elemCount; i++)
        {
          if(readIStat(in, sflg, active+i))
            EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
        }
      } else {
        memset(o->getActive().data(), 1, elemCount); // there is no status flag -> everything is active
      }

      float* values = o->getValues().data();
      NodeOutput::float2D* valuesV = o->getValuesV().data();
      for (int i=0; i<nodeCount; i++)
      {
        // Read values flags
        if (ds->type() == DataSet::Vector)
        {
          NodeOutput::float2D v;
          if( in.readRawData( (char*)&v.x, 4) != 4 )
            EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
          if( in.readRawData( (char*)&v.y, 4) != 4 )
            EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
          valuesV[i] = v;
          values[i] = v.length(); // Determine the magnitude
        }
        else
        {
          if( in.readRawData( (char*)&values[i], 4) != 4 )
            EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
        }
      }

      if (o->time == 99999)
        dsMax->addOutput(o.take()); // special timestep (in TUFLOW) with maximums
      else
        ds->addOutput(o.take());  // ordinary timestep
      break;
    }
  }

  if (ds->outputCount() == 0)
    EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

  ds->updateZRange();

  Mesh::DataSets datasets;
  datasets << ds.take();

  if (dsMax->outputCount() != 0)
  {
    dsMax->updateZRange();
    datasets << dsMax.take();
  }

  return datasets;
}

// for both nodes and elements
template <typename T>
QVector<int> _mapIDToIndex(const T& items)
{
  int maxID = 0;
  for (int i = 0; i < items.count(); ++i)
  {
    int itemID = items[i].id();
    if (itemID > maxID)
      maxID = itemID;
  }

  QVector<int> map(maxID, -1);
  for (int i = 0; i < items.count(); ++i)
  {
    int itemID = items[i].id();
    map[itemID-1] = i;
  }

  return map;
}

Mesh::DataSets Crayfish::loadAsciiDataSet(const QString& fileName, const Mesh* mesh, LoadStatus* status)
{
  QFile file(fileName);
  if (!file.open(QIODevice::ReadOnly))
    EXIT_WITH_ERROR(LoadStatus::Err_FileNotFound);  // Couldn't open the file

  QTextStream stream(&file);
  QString firstLine = stream.readLine();

  // http://www.xmswiki.com/xms/SMS:ASCII_Dataset_Files_*.dat
  // Apart from the format specified above, there is an older supported format used in BASEMENT (and SMS?)
  // which is simpler (has only one dataset in one file, no status flags etc)

  bool oldFormat;
  bool isVector = false;
  QScopedPointer<DataSet> ds;

  if (firstLine.trimmed() == "DATASET")
    oldFormat = false;
  else if (firstLine == "SCALAR" || firstLine == "VECTOR")
  {
    oldFormat = true;
    isVector = (firstLine == "VECTOR");

    ds.reset(new DataSet(fileName));
    ds->setIsTimeVarying(true);
    ds->setType(isVector ? DataSet::Vector : DataSet::Scalar);
    ds->setName(QFileInfo(fileName).baseName());
  }
  else
    EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

  // see if it contains element-centered results - supported by BASEMENT
  bool elementCentered = false;
  if (!oldFormat && QFileInfo(fileName).baseName().contains("_els_"))
    elementCentered = true;

  int nodeCount = mesh->nodes().count();
  int elemCount = mesh->elements().count();

  QVector<int> nodeIDToIndex = _mapIDToIndex(mesh->nodes());
  QVector<int> elemIDToIndex = _mapIDToIndex(mesh->elements());

  QRegExp reSpaces("\\s+");

  Mesh::DataSets datasets;

  while (!stream.atEnd())
  {
    QString line = stream.readLine();
    QStringList items = line.split(reSpaces, QString::SkipEmptyParts);
    if (items.count() < 1)
      continue; // empty line?? let's skip it

    QString cardType = items[0];
    if (cardType == "ND" && items.count() >= 2)
    {
      int fileNodeCount = items[1].toInt();
      if (nodeIDToIndex.count() != fileNodeCount)
        EXIT_WITH_ERROR(LoadStatus::Err_IncompatibleMesh);
    }
    else if (!oldFormat && cardType == "NC" && items.count() >= 2)
    {
      int fileElemCount = items[1].toInt();
      if (elemIDToIndex.count() != fileElemCount)
        EXIT_WITH_ERROR(LoadStatus::Err_IncompatibleMesh);
    }
    else if (!oldFormat && cardType == "OBJTYPE")
    {
      if (items[1] != "mesh2d" && items[1] != "\"mesh2d\"")
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
    }
    else if (!oldFormat && (cardType == "BEGSCL" || cardType == "BEGVEC"))
    {
      if (ds)
      {
        qDebug("Crayfish: New dataset while previous one is still active!");
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      }
      isVector = cardType == "BEGVEC";
      ds.reset(new DataSet(fileName));
      ds->setIsTimeVarying(true);
      ds->setType(isVector ? DataSet::Vector : DataSet::Scalar);
    }
    else if (!oldFormat && cardType == "ENDDS")
    {
      if (!ds)
      {
        qDebug("Crayfish: ENDDS card for no active dataset!");
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      }
      ds->updateZRange();
      datasets << ds.take();
    }
    else if (!oldFormat && cardType == "NAME" && items.count() >= 2)
    {
      if (!ds)
      {
        qDebug("Crayfish: NAME card for no active dataset!");
        EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);
      }

      int quoteIdx1 = line.indexOf('\"');
      int quoteIdx2 = line.indexOf('\"', quoteIdx1+1);
      if (quoteIdx1 > 0 && quoteIdx2 > 0)
        ds->setName(line.mid(quoteIdx1+1, quoteIdx2-quoteIdx1-1));
    }
    else if (oldFormat && (cardType == "SCALAR" || cardType == "VECTOR"))
    {
      // just ignore - we know the type from earlier...
    }
    else if (cardType == "TS" && items.count() >= (oldFormat ? 2 : 3))
    {
      float t = items[oldFormat ? 1 : 2].toFloat();

      if (elementCentered)
      {
        ElementOutput* o = _readTimestampElementCentered(t, isVector, stream, elemCount);
        ds->addOutput(o);
      }
      else
      {
        bool hasStatus = (oldFormat ? false : items[1].toInt());
        NodeOutput* o = _readTimestep(t, isVector, hasStatus, stream, nodeCount, elemCount, nodeIDToIndex);
        ds->addOutput(o);
      }

    }
    else
    {
      qDebug("Crafish: Unknown card: %s", items.join(" ").toAscii().data());
    }
  }

  if (oldFormat)
  {
    if (ds->outputCount() == 0)
      EXIT_WITH_ERROR(LoadStatus::Err_UnknownFormat);

    ds->updateZRange();
    datasets << ds.take();
  }

  return datasets;
}


static NodeOutput* _readTimestep(float t, bool isVector, bool hasStatus, QTextStream& stream, int nodeCount, int elemCount, QVector<int>& nodeIDToIndex)
{
  NodeOutput* o = new NodeOutput;
  o->init(nodeCount, elemCount, isVector);
  o->time = t / 3600.;

  QRegExp reSpaces("\\s+");

  if (hasStatus)
  {
    // only for new format
    char* active = o->getActive().data();
    for (int i = 0; i < elemCount; ++i)
    {
      active[i] = stream.readLine().toInt();
    }
  }
  else
    memset(o->getActive().data(), 1, elemCount); // there is no status flag -> everything is active

  float* values = o->getValues().data();
  NodeOutput::float2D* valuesV = o->getValuesV().data();
  for (int i = 0; i < nodeIDToIndex.count(); ++i)
  {
    QStringList tsItems = stream.readLine().split(reSpaces, QString::SkipEmptyParts);
    int index = nodeIDToIndex[i];
    if (index < 0)
      continue; // node ID that does not exist in the mesh

    if (isVector)
    {
      NodeOutput::float2D v;
      if (tsItems.count() >= 2) // BASEMENT files with vectors have 3 columns
      {
        v.x = tsItems[0].toFloat();
        v.y = tsItems[1].toFloat();
      }
      else
      {
        qDebug("Crayfish: invalid timestep line");
        v.x = v.y = 0;
      }
      valuesV[index] = v;
      values[index] = v.length(); // Determine the magnitude
    }
    else
    {
      if (tsItems.count() >= 1)
        values[index] = tsItems[0].toFloat();
      else
      {
        qDebug("Crayfish: invalid timestep line");
        values[index] = 0;
      }
    }
  }

  return o;
}


static ElementOutput* _readTimestampElementCentered(float t, bool isVector, QTextStream& stream, int elemCount)
{
  ElementOutput* o = new ElementOutput;
  o->init(elemCount, isVector);
  o->time = t / 3600.;

  QRegExp reSpaces("\\s+");

  // TODO: hasStatus

  float* values = o->getValues().data();
  Output::float2D* valuesV = o->getValuesV().data();
  for (int i = 0; i < elemCount; ++i)
  {
    QStringList tsItems = stream.readLine().split(reSpaces, QString::SkipEmptyParts);

    if (isVector)
    {
      Output::float2D v;
      if (tsItems.count() >= 2) // BASEMENT files with vectors have 3 columns
      {
        v.x = tsItems[0].toFloat();
        v.y = tsItems[1].toFloat();
      }
      else
      {
        qDebug("Crayfish: invalid timestep line");
        v.x = v.y = 0;
      }
      valuesV[i] = v;
      values[i] = v.length(); // Determine the magnitude
    }
    else
    {
      if (tsItems.count() >= 1)
        values[i] = tsItems[0].toFloat();
      else
      {
        qDebug("Crayfish: invalid timestep line");
        values[i] = 0;
      }
    }
  }

  return o;
}


bool Crayfish::saveBinaryDataSet(const QString& datFileName, const DataSet *dataset) {
    QFile file(datFileName);
    if (!file.open(QIODevice::WriteOnly)) return false;  // Couldn't open the file

    const Mesh* mesh = dataset->mesh();
    int nodeCount = mesh->nodes().count();
    int elemCount = mesh->elements().count();

    QDataStream out(&file);

    // version card
    if (out.writeRawData((char*)&CT_VERSION, 4) != 4) return false;

    // objecttype
    if (out.writeRawData((char*)&CT_OBJTYPE, 4) != 4) return false;
    if (out.writeRawData((char*)&CT_2D_MESHES, 4) != 4) return false;

    // float size
    if (out.writeRawData((char*)&CT_SFLT, 4) != 4) return false;
    if (out.writeRawData((char*)&CT_FLOAT_SIZE, 4) != 4) return false;

    // Flag size
    if (out.writeRawData((char*)&CT_SFLG, 4) != 4) return false;
    if (out.writeRawData((char*)&CF_FLAG_SIZE, 4) != 4) return false;

    // Dataset Type
    if (dataset->type() == DataSet::Scalar) {
        if (out.writeRawData((char*)&CT_BEGSCL, 4) != 4) return false;
    } else if (dataset->type() == DataSet::Vector) {
        if (out.writeRawData((char*)&CT_BEGVEC, 4) != 4) return false;
    } else {
        return false;
    }

    // Object id (ignored)
    int ignored_val = 1;
    if (out.writeRawData((char*)&CT_OBJID, 4) != 4) return false;
    if (out.writeRawData((char*)&ignored_val, 4) != 4) return false;

    // Num nodes
    if (out.writeRawData((char*)&CT_NUMDATA, 4) != 4) return false;
    if (out.writeRawData((char*)&nodeCount, 4) != 4) return false;

    // Num cells
    if (out.writeRawData((char*)&CT_NUMCELLS, 4) != 4) return false;
    if (out.writeRawData((char*)&elemCount, 4) != 4) return false;

    // Name
    if (out.writeRawData((char*)&CT_NAME, 4) != 4) return false;
    if (out.writeRawData(dataset->name().leftJustified(39, ' ', true).toStdString().c_str(), 40) != 40) return false;

    // Time steps
    int istat = 1; // include if elements are active

    for (int time_index=0; time_index<dataset->outputCount(); ++ time_index ) {
        const Output* output = dataset->constOutput(time_index);

        if (output->type() != Output::TypeNode) return false; // Element outputs not supported in the format

        const NodeOutput* nodeOutput = static_cast<const NodeOutput*>(output);

        if (out.writeRawData((char*)&CT_TS, 4) != 4) return false;
        if (out.writeRawData((char*)&istat, 1) != 1) return false;
        if (out.writeRawData((char*)&output->time, 4) != 4) return false;

        if (istat)
        {
          // Write status flags
          for (int i=0; i<elemCount; i++)
          {
              bool active = nodeOutput->isActive(i);
              if( out.writeRawData( (char*)&active, 1) != 1 ) return false;
          }
        }

        for (int i=0; i<nodeCount; i++)
        {
          // Read values flags
          if (dataset->type() == DataSet::Vector)
          {
            float x = nodeOutput->loadedValuesV()[i].x;
            float y = nodeOutput->loadedValuesV()[i].y;
            if( out.writeRawData( (char*)&x, 4) != 4 ) return false;
            if( out.writeRawData( (char*)&y, 4) != 4 ) return false;
          }
          else
          {
            float val = nodeOutput->loadedValues()[i];
            if( out.writeRawData( (char*)&val, 4) != 4 ) return false;
          }
        }
    }

    if (out.writeRawData((char*)&CT_ENDDS, 4) != 4) return false;

    return true;
}
