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
#include <QFileInfo>
#include <QStringList>
#include <QDir>
#include <QRegExp>
#include <QDateTime>

class MultipleTifsReader: public CrayfishGDALReader
{
public:
    // We assume we have a directory with the multiple TIF files
    // that have the same naming convention: filename_<timestamp>.[asc|tif|tiff]
    // each file is readable by GDAL reader and has one band with data
    MultipleTifsReader(const QString& fileName): CrayfishGDALReader(fileName, "NETCDF"){}

    QStringList parseDatasetNames(const QString& fileName) {
        QStringList ret;

        QFileInfo fi = QFileInfo(fileName);
        QDir fd = fi.absoluteDir();

        QStringList filters;
        filters << "*.asc" << "*.tif" << "*.tiff" << "*.ASC" << "*.TIF" << "*.TIFF" ;

        QStringList files = fd.entryList(filters, QDir::Files|QDir::NoSymLinks|QDir::NoDotAndDotDot|QDir::Readable, QDir::Name);
        foreach (QString file, files) {
            ret.push_back(fd.filePath(file));
        }

        return ret;
    }

    bool parseBandInfo(const CrayfishGDALDataset* cfGDALDataset,
                       const metadata_hash& metadata, QString& band_name,
                       float* time, bool* is_vector, bool* is_x
                       ) {
       static int err_counter = 0;

       QFileInfo fi = QFileInfo(cfGDALDataset->mDatasetName);

       // we except filename to be <prefix><YYYYMMDD_HHMM><suffix>.[asc|tif|tiff]
       // e.g. 5FQPE_20140819_0705_20140819020010_asc.asc
       QRegExp rx("^(.*)(\\d{4})(\\d{2})(\\d{2})_(\\d{2})(\\d{2}).*$");
       rx.indexIn(fi.fileName());
       QStringList matches = rx.capturedTexts();
       if (matches.length() !=  7) {
           *time = err_counter++;
           band_name = matches[0];
       } else {
           band_name = matches[1];
           // we need time in hours
           QDate band_date(matches[2].toFloat(), matches[3].toFloat(), matches[4].toFloat());
           QTime band_time(matches[5].toFloat(), matches[6].toFloat());

           if (!refTime.isValid()) {
               refTime.setDate(band_date);
               refTime.setTime(band_time);
               *time = 0;
           } else {
               int secs_to = refTime.secsTo(QDateTime(band_date, band_time));
               *time = secs_to / 3600.0;
            }
       }

       *is_vector = false; // vector
       *is_x =  true; //X-Axis
       return false; // SUCCESS
    }

    QDateTime getRefTime() {
        return refTime;
    }

private:
    QDateTime refTime; //!< reference (base) time for output's times
};

Mesh* Crayfish::loadMultipleTifs(const QString& fileName, LoadStatus* status)
{
    MultipleTifsReader reader(fileName);
    return reader.load(status);
}
