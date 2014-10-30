#include "crayfish_gdal.h"

#include <gdal/gdal.h>

#include "crayfish_viewer.h"


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
