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
#include "crayfish_gdal.h"
#include "crayfish_mesh.h"
#include <limits>
#include <QString>

/* ************************************************************************** */
;

class GribReader: public CrayfishGDALReader
{
public:
    GribReader(const QString& fileName): CrayfishGDALReader(fileName, "GRIB"),
        mRefTime(std::numeric_limits<int>::min()) {}
protected:
    bool parseBandInfo(const metadata_hash& metadata, QString& band_name, int* time) {
       metadata_hash::const_iterator iter;

       iter = metadata.find("GRIB_COMMENT");
       if (iter == metadata.end()) return true; //FAILURE
       band_name = iter.value();

       if (mRefTime == std::numeric_limits<int>::min())
       {
           iter = metadata.find("GRIB_REF_TIME");
           if (iter == metadata.end()) return true; //FAILURE
           mRefTime = parseMetadataTime(iter.value());
       }

       iter = metadata.find("GRIB_VALID_TIME");
       if (iter == metadata.end()) return true; //FAILURE
       int valid_time = parseMetadataTime(iter.value());
       *time = valid_time - mRefTime;

       return false; // SUCCESS
    }
private:
    int mRefTime; // ref time is parsed only once, because
                  // some GRIB files do not use FORECAST_SEC, but VALID_TIME
                  // metadata, so ref time varies with dataset-to-dataset
};


Mesh* Crayfish::loadGRIB(const QString& fileName, LoadStatus* status)
{
    GribReader reader(fileName);
    return reader.load(status);
}
