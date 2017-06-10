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

#ifndef CRAYFISH_GDAL_H
#define CRAYFISH_GDAL_H

#include "gdal.h"

#include <QString>
#include <QStringList>
#include <QVector>
#include <QMap>
#include <QHash>
#include <QDateTime>

#include "crayfish_mesh.h"
#include "crayfish_colormap.h"

struct LoadStatus;
class NodeOutput;

/******************************************************************************************************/

class RawData
{
public:
  RawData(int c, int r, QVector<double> g): mCols(c), mRows(r), mData(new float[r*c]), mGeo(g)
  {
    int size = r*c;
    for (int i = 0; i < size; ++i)
      mData[i] = -999.0f; // nodata value
  }
  ~RawData() { delete [] mData; }

  int size() const { return mRows*mCols; }
  int cols() const { return mCols; }
  int rows() const { return mRows; }
  QVector<double> geoTransform() const { return mGeo; }
  float* data() const { return mData; }
  float* scanLine(int row) const { Q_ASSERT(row >= 0 && row < mRows); return mData+row*mCols; }
  float dataAt(int index) const { return mData[index]; }
  QVector<float> mask() const {
      QVector<float> dataMask(size(), 0.0f);
      for (int i=0; i<size(); i++)
          if (dataAt(i) != -999.0f) dataMask[i] = 1.0f;
      return dataMask;
  }

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
  static bool writeContoursSHP(const QString& outFilename, double interval, RawData* rd, const QString& wkt, bool useLines, ColorMap* cm);
};

/******************************************************************************************************/


class CrayfishGDALDataset
{
public:

    CrayfishGDALDataset():mHDataset(0){}
    ~CrayfishGDALDataset(){
        if (mHDataset) GDALClose( mHDataset );
    }

    void init(const QString& dsName);

    QString mDatasetName;
    QString mProj;
    GDALDatasetH mHDataset;

    uint mNBands; /* number of bands */
    uint mXSize; /* number of x pixels */
    uint mYSize; /* number of y pixels */
    uint mNPoints; /* nodes count */
    uint mNVolumes; /* elements count */
    double mGT[6]; /* affine transform matrix */

private:
    void parseParameters();
    void parseProj();
};

class CrayfishGDALReader
{
public:
    CrayfishGDALReader(const QString& fileName, const QString& driverName):
        mFileName(fileName),
        mDriverName(driverName),
        mPafScanline(0),
        mMesh(0){}

    virtual ~CrayfishGDALReader(){}
    Mesh* load(LoadStatus* status);

protected:
    typedef QHash<QString, QString> metadata_hash; // KEY, VALUE

    /* return true on failure */
    virtual bool parseBandInfo(const CrayfishGDALDataset* cfGDALDataset,
                               const metadata_hash& metadata, QString& band_name, float* time, bool* is_vector, bool* is_x) = 0;
    virtual float parseMetadataTime(const QString& time_s);
    virtual QString GDALFileName(const QString& fileName); /* some formats require e.g. adding driver name at the beginning */
    virtual QStringList parseDatasetNames(const QString& fileName);
    virtual QDateTime getRefTime(){return QDateTime();}

private:
    typedef QMap<float, QVector<GDALRasterBandH> > timestep_map; //TIME (sorted), [X, Y]
    typedef QHash<QString, timestep_map > data_hash; //Data Type, TIME (sorted), [X, Y]
    typedef QVector<CrayfishGDALDataset*> gdal_datasets_vector; //GDAL (Sub)Datasets,

    void registerDriver();

    void initElements(Mesh::Nodes& nodes, Mesh::Elements& elements, bool is_longitude_shifted);
    bool initNodes(Mesh::Nodes& nodes); //returns is_longitude_shifted

    const CrayfishGDALDataset* meshGDALDataset();

    bool meshes_equals(const CrayfishGDALDataset* ds1, const CrayfishGDALDataset* ds2) const;

    metadata_hash parseMetadata(GDALMajorObjectH gdalBand, const char* pszDomain = 0);
    void populateScaleForVector(NodeOutput* tos);
    void addDataToOutput(GDALRasterBandH raster_band, NodeOutput* tos, bool is_vector, bool is_x);
    bool addSrcProj();
    void activateElements(NodeOutput* tos);
    void addDatasets();
    void createMesh();
    void parseRasterBands(const CrayfishGDALDataset* cfGDALDataset);

    const QString mFileName;
    const QString mDriverName; /* GDAL driver name */
    float *mPafScanline; /* temporary buffer for reading one raster line */
    Mesh* mMesh;
    gdal_datasets_vector gdal_datasets;
    data_hash mBands; /* raster bands GDAL handle */
};

#endif // CRAYFISH_GDAL_H
