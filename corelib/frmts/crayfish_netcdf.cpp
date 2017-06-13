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

    QString GDALFileName(const QString& fileName) {
        #ifdef WIN32
            // Force usage of the predefined GDAL driver
            // http://gis.stackexchange.com/a/179167
            // on Windows, HDF5 driver is checked before NETCDF driver in GDAL
            return  "NETCDF:\"" + fileName + "\"";
        #else
            return  fileName;
        #endif
    }

    bool parseBandInfo(const CrayfishGDALDataset* cfGDALDataset,
                       const metadata_hash& metadata, QString& band_name,
                       float* time, bool* is_vector, bool* is_x
                       ) {
       metadata_hash::const_iterator iter;

       // TIME
       iter = metadata.find("netcdf_dim_time");
       if (iter == metadata.end()) return true; //FAILURE, skip no-time bands
       *time = parseMetadataTime(iter.value());

       // NAME
       iter = metadata.find("long_name");
       if (iter == metadata.end())
       {
           iter = metadata.find("netcdf_varname");
           if (iter == metadata.end()) return true; //FAILURE, should be always present
           band_name = iter.value();
       } else {
           band_name = iter.value();
       }

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

       // VECTOR
       if (band_name.contains("x-component")) {
           *is_vector = true; // vector
           *is_x =  true; //X-Axis
       }
       else if (band_name.contains("y-component")) {
           *is_vector = true; // vector
           *is_x =  false; //Y-Axis
       } else {
           *is_vector = false; // scalar
           *is_x =  true; //X-Axis
       }

       band_name = band_name.replace("x-component", "")
                            .replace("y-component", "");

       return false; // SUCCESS
    }
};

Mesh* Crayfish::loadNetCDF(const QString& fileName, LoadStatus* status)
{
    NetCDFReader reader(fileName);
    return reader.load(status);
}
