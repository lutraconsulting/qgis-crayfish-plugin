
#include "crayfish.h"

#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_mesh.h"

#include "crayfish_hdf5.h"

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

  // TODO: read non-temporal data (Maximums, Times)

  HdfGroup gTemporal = gMesh.group("Temporal");

  Mesh::DataSets datasets;

  foreach (const QString& name, gTemporal.groups())
  {
    HdfGroup g = gTemporal.group(name);
    QStringList gDataNames = g.datasets();
    if (!gDataNames.contains("Times") || !gDataNames.contains("Values") || !gDataNames.contains("Active"))
    {
      qDebug("ignoring dataset %s - not having required arrays", name.toAscii().data());
      continue;
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
      continue;
    }
    int nTimeSteps = dimTimes[0];

    if ((int)dimValues[0] != nTimeSteps || (int)dimActive[0] != nTimeSteps )
    {
      qDebug("ignoring dataset %s - arrays not having correct dimension sizes", name.toAscii().data());
      continue;
    }
    if ((int)dimValues[1] != nNodes || (int)dimActive[1] != nElems)
    {
      qDebug("ignoring dataset %s - not aligned with the used mesh", name.toAscii().data());
      continue;
    }

    bool isVector = dimValues.count() == 3;

    QVector<float> times = dsTimes.readArray();
    QVector<float> values = dsValues.readArray();
    QVector<uchar> active = dsActive.readArrayUint8();

    DataSet* ds = new DataSet(datFileName);
    ds->setIsTimeVarying(true);
    ds->setName(name);
    ds->setType(isVector ? DataSet::Vector : DataSet::Scalar);

    for (int i = 0; i < nTimeSteps; ++i)
    {
      Output* o = new Output;
      o->init(nNodes, nElems, isVector);
      o->time = times[i];
      if (isVector)
      {
        const float* input = values.constData() + 2*i*nNodes;
        Output::float2D* data = o->valuesV.data();
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

    ds->updateZRange(nNodes);
    datasets.append(ds);
  }

  return datasets;
}
