/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2014 Lutra Consulting

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

#ifndef CRAYFISH_GDAL_H
#define CRAYFISH_GDAL_H

#include "gdal.h"

#include <QString>
#include <QVector>
#include <QMap>
#include <QHash>

#include "crayfish_mesh.h"

class LoadStatus;
class NodeOutput;

/******************************************************************************************************/

class RawData
{
public:
  RawData(int c, int r, QVector<double> g): mCols(c), mRows(r), mData(new float[r*c]), mGeo(g)
  {
    int size = r*c;
    for (int i = 0; i < size; ++i)
      mData[i] = -999; // nodata value
  }
  ~RawData() { delete [] mData; }

  int cols() const { return mCols; }
  int rows() const { return mRows; }
  QVector<double> geoTransform() const { return mGeo; }
  float* data() const { return mData; }
  float* scanLine(int row) const { Q_ASSERT(row >= 0 && row < mRows); return mData+row*mCols; }
  float dataAt(int index) const { return mData[index]; }

private:
  int mCols;
  int mRows;
  float* mData;
  QVector<double> mGeo;  // georef data (2x3 matrix): xp = a0 + x*a1 + y*a2    yp = a3 + x*a4 + y*a5

  Q_DISABLE_COPY(RawData)
};

class CrayfishGDAL
{
public:
  static bool writeGeoTIFF(const QString& outFilename, RawData* rd, const QString& wkt);
};

/******************************************************************************************************/

class CrayfishGDALReader
{
public:
    CrayfishGDALReader(const QString& fileName): mFileName(fileName), mHDataset(0), mPafScanline(0), mMesh(0){}
    virtual ~CrayfishGDALReader(){}
    Mesh* load(LoadStatus* status);

protected:
    virtual void createMesh();
    virtual void addDatasets();
    virtual void activateElements(NodeOutput* tos);
    virtual void addSrcProj();
    virtual void addDataToOutput(GDALRasterBandH raster_band, NodeOutput* tos, bool is_vector, bool is_x);
    virtual void populateScaleForVector(NodeOutput* tos);
    virtual void parseRasterBands();
    virtual void parseBandInfo(const QString& elem, QString& band_name, int* data_count, int* data_index);
    virtual bool parseMetadata(GDALRasterBandH gdalBand, int* time, int* ref_time, QString& elem);
    virtual int parseMetadataTime(const QString& time_s);
    virtual void initElements(Mesh::Elements& elements);
    virtual void initNodes(Mesh::Nodes& nodes);
    virtual void openFile();
    virtual void parseParameters();

private:
    typedef QMap<int, QVector<GDALRasterBandH> > timestep_map; //TIME (sorted), [X, Y]
    typedef QHash<QString, QString> metadata_hash; // KEY, VALUE
    typedef QHash<QString, timestep_map > data_hash; //Data Type, TIME (sorted), [X, Y]

    QString mFileName;
    GDALDatasetH mHDataset;
    float *mPafScanline;
    Mesh* mMesh;
    data_hash mBands;

    uint mNBands;
    uint mXSize;
    uint mYSize;
    uint mNPoints;
    uint mNVolumes;
    double mGT[6]; // affine transform matrix
};

#endif // CRAYFISH_GDAL_H
