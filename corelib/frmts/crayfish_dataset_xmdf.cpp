/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2015 Lutra Consulting

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

#include "crayfish_hdf5.h"

static DataSet* readXmdfGroupAsDataSet(const HdfGroup& g, const QString& datFileName, const QString& name, int nNodes, int nElems);


Mesh::DataSets Crayfish::loadXmdfDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status)
{
  HdfFile file(datFileName);
  if (!file.isValid())
  {
    if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
    return Mesh::DataSets();
  }

  HdfDataset dsFileType = file.dataset("/File Type");
  if (dsFileType.readString() != "Xmdf")
  {
    if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
    return Mesh::DataSets();
  }

  // TODO: check version?

  int nNodes = mesh->nodes().count();
  int nElems = mesh->elements().count();

  QStringList rootGroups = file.groups();
  if (rootGroups.count() != 1)
  {
    qDebug("Expecting exactly one root group for the mesh data");
    if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
    return Mesh::DataSets();
  }
  HdfGroup gMesh = file.group(rootGroups[0]);

  // TODO: read Times group (e.g. time of peak velocity)

  Mesh::DataSets datasets;

  HdfGroup gTemporal = gMesh.group("Temporal");
  foreach (const QString& name, gTemporal.groups())
  {
    HdfGroup g = gTemporal.group(name);
    if (DataSet* ds = readXmdfGroupAsDataSet(g, datFileName, name, nNodes, nElems))
    {
      ds->updateZRange();
      datasets.append(ds);
    }
  }

  HdfGroup gMaximums = gMesh.group("Maximums");
  foreach (const QString& name, gMaximums.groups())
  {
    HdfGroup g = gMaximums.group(name);
    if (DataSet* ds = readXmdfGroupAsDataSet(g, datFileName, name + "/Maximums", nNodes, nElems))
    {
      if (ds->outputCount() != 1)
        qDebug("Maximum dataset should have just one timestep!");
      ds->setIsTimeVarying(false);
      ds->updateZRange();
      datasets.append(ds);
    }
  }

  return datasets;
}


static DataSet* readXmdfGroupAsDataSet(const HdfGroup& g, const QString& datFileName, const QString& name, int nNodes, int nElems)
{
    QStringList gDataNames = g.datasets();
    if (!gDataNames.contains("Times") || !gDataNames.contains("Values") || !gDataNames.contains("Active"))
    {
      qDebug("ignoring dataset %s - not having required arrays", name.toAscii().data());
      return 0;
    }

    HdfDataset dsTimes = g.dataset("Times");
    HdfDataset dsValues = g.dataset("Values");
    HdfDataset dsActive = g.dataset("Active");

    QVector<hsize_t> dimTimes = dsTimes.dims();
    QVector<hsize_t> dimValues = dsValues.dims();
    QVector<hsize_t> dimActive = dsActive.dims();

    if (dimTimes.count() != 1 || (dimValues.count() != 2 && dimValues.count() != 3) || dimActive.count() != 2)
    {
      qDebug("ignoring dataset %s - arrays not having correct dimension counts", name.toAscii().data());
      return 0;
    }
    int nTimeSteps = dimTimes[0];

    if ((int)dimValues[0] != nTimeSteps || (int)dimActive[0] != nTimeSteps )
    {
      qDebug("ignoring dataset %s - arrays not having correct dimension sizes", name.toAscii().data());
      return 0;
    }
    if ((int)dimValues[1] != nNodes || (int)dimActive[1] != nElems)
    {
      qDebug("ignoring dataset %s - not aligned with the used mesh", name.toAscii().data());
      return 0;
    }

    bool isVector = dimValues.count() == 3;

    QVector<float> times = dsTimes.readArray();
    QVector<float> values = dsValues.readArray();
    QVector<uchar> active = dsActive.readArrayUint8();

    DataSet* ds = new DataSet(datFileName);
    ds->setIsTimeVarying(true);
    ds->setName(name, false);  // name may contain slashes intentionally - do not sanitize
    ds->setType(isVector ? DataSet::Vector : DataSet::Scalar);

    for (int i = 0; i < nTimeSteps; ++i)
    {
      NodeOutput* o = new NodeOutput;
      o->init(nNodes, nElems, isVector);
      o->time = times[i];
      if (isVector)
      {
        const float* input = values.constData() + 2*i*nNodes;
        NodeOutput::float2D* data = o->valuesV.data();
        float* scalar = o->values.data();
        for (int j = 0; j < nNodes; ++j)
        {
          data[j].x = input[2*j];
          data[j].y = input[2*j+1];
          scalar[j] = data[j].length();
        }
      }
      else
      {
        memcpy(o->values.data(), values.constData()+(i*nNodes), sizeof(float)*nNodes);
      }
      memcpy(o->active.data(), active.constData()+(i*nElems), sizeof(uchar)*nElems);
      ds->addOutput(o);
    }

    return ds;
}
