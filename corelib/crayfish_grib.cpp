/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2015 Lutra Consulting

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

#include <netcdf.h>
#include <gdal.h>

Mesh* Crayfish::loadGRIB(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();

    GDALAllRegister();

    GDALDriverH hDriver = GDALGetDriverByName("GRIB");
    if (!hDriver)
    {
        qDebug("error: Unable to load GDAL GRIB driver ");
        return 0;
    }

    GDALDatasetH hDataset = GDALOpen( fileName.toAscii().data(), GA_ReadOnly );
    if( hDataset == NULL )
    {
        if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
        return 0;
    }

    // Get Coordinate System data

    double nBands = GDALGetRasterCount( hDataset );
    if (nBands == 0) {
        GDALClose( hDataset );
        qDebug("error: No raster bands present");
        return 0;
    }

    double GT[6];
    if( GDALGetGeoTransform( hDataset, GT ) != CE_None )
    {
        GDALClose( hDataset );
        qDebug("error: Unable to load geo transform ");
        return 0;
    }

    int xSize = GDALGetRasterXSize( hDataset ); //raster width in pixels
    int ySize = GDALGetRasterYSize( hDataset ); //raster height in pixels
    int nPoints = xSize * ySize;
    int nVolumes = (xSize - 1) * (ySize -1);

    Mesh::Nodes nodes(nPoints);
    Node* nodesPtr = nodes.data();
    for (int y = 0; y < ySize; ++y)
    {
        for (int x = 0; x < xSize; ++x, ++nodesPtr)
        {
            nodesPtr->id = x + xSize*y;
            nodesPtr->x = GT[0] + x*GT[1] + y*GT[2];
            nodesPtr->y = GT[3] + x*GT[4] + y*GT[5];
        }
    }

    Mesh::Elements elements(nVolumes);
    Element* elementsPtr = elements.data();

    for (int y = 0; y < ySize-1; ++y)
    {
        for (int x = 0; x < xSize-1; ++x, ++elementsPtr)
        {
            elementsPtr->id = x + xSize*y;
            elementsPtr->eType = Element::E4Q;
            // !!!!!!!CLOCKWISE!!!!!!!!
            elementsPtr->p[1] = x + 1 + xSize*(y + 1); //22
            elementsPtr->p[2] = x + 1 + xSize*y; //12
            elementsPtr->p[3] = x + xSize*y; //11
            elementsPtr->p[0] = x + xSize*(y + 1); //21
        }
    }

    Mesh* mesh = new Mesh(nodes, elements);

    // Now BANDS
    QHash<QString, QMap<int, GDALRasterBandH> > bands; //ELEMENT, TIME (sorted), RASTER

    for ( int i = 1; i <= nBands; ++i ) // starts with 1 .... ehm....
    {
        GDALRasterBandH gdalBand = GDALGetRasterBand( hDataset, i );
        QString elem;
        int time = -999999;

        char** GDALmetadata = GDALGetMetadata( gdalBand, 0 );

        if ( GDALmetadata )
        {
            for ( int j = 0; GDALmetadata[j]; ++j )
            {
                QString metadata_pair = GDALmetadata[j]; //KEY = VALUE
                QStringList metadata = metadata_pair.split("=");

                if (metadata[0] == "GRIB_COMMENT") //e.g. GRIB_ELEMENT=CFRZR
                {
                    elem = metadata[1];
                } else if (metadata[0] == "GRIB_FORECAST_SECONDS") //e.g. GRIB_FORECAST_SECONDS=64800 sec
                {
                    QString time_s = metadata[1];
                    time_s = time_s.trimmed();
                    QStringList times = time_s.split(" ");
                    float time_sec = times[0].toFloat();
                    time = int(time_sec/3600);
                }
            }
        }
        else
        {
            continue;
        }

        if (!elem.isEmpty() &&
                time > -999999)
        {
            if (bands.find(elem) == bands.end())
            {
                QMap<int, GDALRasterBandH> qMap;
                qMap[time] = gdalBand;
                bands[elem] = qMap;
            } else {
                bands[elem].insert(time, gdalBand);
            }
        }
    }

    // Create datasets

    float *pafScanline = (float *) malloc(sizeof(float)*xSize);
    if (!pafScanline)
    {
        GDALClose( hDataset );
        qDebug("error: Unable to alloc memory for reading GRIB file");
        return 0;
    }

    // SCALARS!
    for (QHash<QString, QMap<int, GDALRasterBandH> >::iterator band = bands.begin(); band != bands.end(); band++)
    {
        DataSet* dsd = new DataSet(fileName);
        dsd->setType(DataSet::Scalar);
        dsd->setName(band.key());
        dsd->setIsTimeVarying(band->count() > 1);

        for (QMap<int, GDALRasterBandH>::iterator time_step = band.value().begin(); time_step != band.value().end(); time_step++)
        {
            NodeOutput* tos = new NodeOutput;
            tos->init(nPoints, nVolumes, false);
            tos->time = time_step.key();
            float* values = tos->values.data();

            for (int y = 0; y < ySize; ++y)
            {
                // buffering per-line
                CPLErr err = GDALRasterIO(
                            time_step.value(),
                            GF_Read,
                            0, //nXOff
                            y, //nYOff
                            xSize,  //nXSize
                            1, //nYSize
                            pafScanline, //pData
                            xSize, //nBufXSize
                            1, //nBufYSize
                            GDT_Float32,
                            0, //nPixelSpace
                            0 //nLineSpace
                            );
                if (err != CE_None)
                {
                    GDALClose( hDataset );
                    free(pafScanline);
                    qDebug("error: Unable to read rasterIO");
                    return 0;
                }

                for (int x = 0; x < xSize; ++x)
                {
                    int idx = x + xSize*y;
                    values[idx] = pafScanline[x];
                }

            }

            // Enable elements that do not have any nodata-value nodes
            char* active = tos->active.data();
            float nodata = (float) (GDALGetRasterNoDataValue(time_step.value(), 0)); // in double
            float eps = std::numeric_limits<float>::epsilon();

            for(int i = 0; i < nVolumes; i++)
            {
                if ( (fabs(values[elements[i].p[0]] - nodata) < eps) ||
                     (fabs(values[elements[i].p[1]] - nodata) < eps) ||
                     (fabs(values[elements[i].p[2]] - nodata) < eps) ||
                     (fabs(values[elements[i].p[3]] - nodata) < eps))
                {
                    active[i] = 0;
                } else {
                    active[i] = 1;
                }
            }


            dsd->addOutput(tos);
        }
        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }

    free(pafScanline);
    pafScanline = 0;

    GDALClose( hDataset );

    return mesh;
}
