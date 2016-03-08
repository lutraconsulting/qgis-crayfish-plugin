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

#include <QString>
#include <QVector>



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

#endif // CRAYFISH_GDAL_H
