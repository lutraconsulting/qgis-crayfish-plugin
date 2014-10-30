#ifndef CRAYFISH_GDAL_H
#define CRAYFISH_GDAL_H

class RawData;
class QString;

class CrayfishGDAL
{
public:

  static bool writeGeoTIFF(const QString& outFilename, RawData* rd, const QString& wkt);
};

#endif // CRAYFISH_GDAL_H
