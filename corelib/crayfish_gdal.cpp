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

#include "crayfish_gdal.h"

#include <gdal.h>


bool CrayfishGDAL::writeGeoTIFF(const QString& outFilename, RawData* rd, const QString& wkt)
{
  GDALAllRegister();

  GDALDriverH hDriver = GDALGetDriverByName("GTiff");
  if (!hDriver)
    return false;

  const char *papszOptions[] = { "COMPRESS=LZW", NULL };
  GDALDatasetH hDstDS = GDALCreate( hDriver, outFilename.toAscii().data(), rd->cols(), rd->rows(), 1, GDT_Float32,
                       (char**) papszOptions );
  if (!hDstDS)
    return false;

  GDALSetGeoTransform( hDstDS, rd->geoTransform().data() );
  GDALSetProjection( hDstDS, wkt.toAscii().data() );

  GDALRasterBandH hBand = GDALGetRasterBand( hDstDS, 1 );
  GDALSetRasterNoDataValue(hBand, -999);
  GDALRasterIO( hBand, GF_Write, 0, 0, rd->cols(), rd->rows(),
                rd->data(), rd->cols(), rd->rows(), GDT_Float32, 0, 0 );

  GDALClose( hDstDS );
  return true;
}
