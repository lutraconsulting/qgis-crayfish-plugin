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
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_gdal.h"

#include <QString>
#include <QtGlobal>

class NetCDFReader: public CrayfishGDALReader
{
public:
    NetCDFReader(const QString& fileName): CrayfishGDALReader(fileName, "NETCDF"){}

    bool parseBandInfo(const metadata_hash& metadata, QString& band_name, float* time) {
       metadata_hash::const_iterator iter;

       iter = metadata.find("netcdf_dim_time");
       if (iter == metadata.end()) return true; //FAILURE, skip no-time bands
       *time = parseMetadataTime(iter.value());

       iter = metadata.find("netcdf_varname");
       if (iter == metadata.end()) return true; //FAILURE
       band_name = iter.value();

       // Loop throught all additional dimensions but time
       for (iter = metadata.begin(); iter != metadata.end(); ++iter) {
         QString key = iter.key();
         if (key.contains("netcdf_dim_")) {
             key = key.replace("netcdf_dim_", "");
             if (key != "time") {
                band_name += "_" + key + ":" + iter.value();
             }
         }
       }

       return false; // SUCCESS
    }

    void determineBandVectorInfo(QString& , bool* is_vector, bool* is_x)
    {
        *is_vector = false; // ONLY scalars supported so far
        *is_x =  true;
    }
};

Mesh* Crayfish::loadNetCDF(const QString& fileName, LoadStatus* status)
{
    NetCDFReader reader(fileName);
    return reader.load(status);
}
