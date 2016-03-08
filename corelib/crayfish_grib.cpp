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

#include <gdal.h>

#include <QString>
#include <QMap>
#include <QHash>
#include <QVector>
#include <QRegExp>

typedef QMap<int, QVector<GDALRasterBandH> > timestep_map; //TIME (sorted), [X, Y]
typedef QHash<QString, timestep_map > data_hash; //Data Type, TIME (sorted), [X, Y]
struct GRIBParams
{
    uint nBands;
    uint xSize;
    uint ySize;
    uint nPoints;
    uint nVolumes;
    double GT[6]; // affine transform matrix
};

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon())
{
    return fabs(val - nodata) < eps;
}

static void parseParameters(GDALDatasetH hDataset, GRIBParams& params) {
    params.nBands = GDALGetRasterCount( hDataset );
    if (params.nBands == 0) throw LoadStatus::Err_InvalidData;

    if( GDALGetGeoTransform( hDataset, params.GT ) != CE_None ) throw LoadStatus::Err_InvalidData;

    params.xSize = GDALGetRasterXSize( hDataset ); //raster width in pixels
    if (params.xSize == 0) throw LoadStatus::Err_InvalidData;

    params.ySize = GDALGetRasterYSize( hDataset ); //raster height in pixels
    if (params.ySize == 0) throw LoadStatus::Err_InvalidData;

    params.nPoints = params.xSize * params.ySize;
    params.nVolumes = (params.xSize - 1) * (params.ySize -1);
}

static GDALDatasetH openGRIBFile(const QString& fileName) {

    GDALAllRegister();
    GDALDriverH hDriver = GDALGetDriverByName("GRIB");
    if (!hDriver) throw LoadStatus::Err_UnknownFormat;

    // Open dataset
    GDALDatasetH hDataset = GDALOpen( fileName.toAscii().data(), GA_ReadOnly );
    if( hDataset == NULL ) throw LoadStatus::Err_UnknownFormat;
    return hDataset;
}

static void initNodes(Mesh::Nodes& nodes, const GRIBParams& params) {
    Node* nodesPtr = nodes.data();
    for (uint y = 0; y < params.ySize; ++y)
    {
        for (uint x = 0; x < params.xSize; ++x, ++nodesPtr)
        {
            nodesPtr->id = x + params.xSize*y;
            nodesPtr->x = params.GT[0] + (x+0.5)*params.GT[1] + (y+0.5)*params.GT[2];
            nodesPtr->y = params.GT[3] + (x+0.5)*params.GT[4] + (y+0.5)*params.GT[5];
        }
    }
}

static void initElements(Mesh::Elements& elements, const GRIBParams& params) {
    Element* elementsPtr = elements.data();
    for (uint y = 0; y < params.ySize-1; ++y)
    {
        for (uint x = 0; x < params.xSize-1; ++x, ++elementsPtr)
        {
            elementsPtr->id = x + params.xSize*y;
            elementsPtr->eType = Element::E4Q;
            elementsPtr->p[1] = x + 1 + params.xSize*(y + 1);
            elementsPtr->p[2] = x + 1 + params.xSize*y;
            elementsPtr->p[3] = x + params.xSize*y;
            elementsPtr->p[0] = x + params.xSize*(y + 1);
        }
    }
}

static bool parseMetadata(GDALRasterBandH gdalBand, int* time, QString& elem)
{
    char** GDALmetadata = GDALGetMetadata( gdalBand, 0 );
    if ( GDALmetadata )
    {
        for ( int j = 0; GDALmetadata[j]; ++j )
        {
            QString metadata_pair = GDALmetadata[j]; //KEY = VALUE
            QStringList metadata = metadata_pair.split("=");
            if (metadata.length() == 2) {
                if (metadata[0] == "GRIB_COMMENT")
                {
                    elem = metadata[1];
                } else if (metadata[0] == "GRIB_FORECAST_SECONDS")
                {
                    QString time_s = metadata[1];
                    time_s = time_s.trimmed();
                    QStringList times = time_s.split(" ");
                    float time_sec = times[0].toFloat();
                    *time = int(time_sec/3600);
                }
            }
        }

        if (!elem.isEmpty() && *time > -999999) {
            // check data sanity
            return false;
        }
    }

    return true;
}

static void parseBandInfo(const QString& elem, QString& band_name, int* data_count, int* data_index)
{
    band_name = band_name.replace("u-component of", "")
                         .replace("v-component of", "")
                         .replace("u-component", "")
                         .replace("v-component", "")
                         .replace(QRegExp("\\[.+\\/.+\\]"), "") // remove units
                         .replace("/", ""); // slash cannot be in dataset name,
                                            // because it means subdataset, see
                                            // python class DataSetModel.setMesh()
                                            // see #132

    if (elem.contains("u-component")) {
        *data_count = 2; // vector
        *data_index =  0; //X-Axis
    }
    else if (elem.contains("v-component")) {
        *data_count = 2; // vector
        *data_index =  1; //Y-Axis
    } else {
        *data_count = 1; // scalar
        *data_index =  0; //X-Axis
    }
}

static void parseRasterBands(GDALDatasetH hDataset, data_hash& bands, const GRIBParams& params) {
    for (uint i = 1; i <= params.nBands; ++i ) // starts with 1 .... ehm....
    {
        // Get Band
        GDALRasterBandH gdalBand = GDALGetRasterBand( hDataset, i );
        if (!gdalBand) throw LoadStatus::Err_InvalidData;

        // Get metadata
        QString elem;
        int time = -999999;
        if (parseMetadata(gdalBand, &time, elem)) {
            continue;
        }

        // Add to data structures
        QString band_name(elem);
        int data_count;
        int data_index;
        parseBandInfo(elem, band_name, &data_count, &data_index);

        if (bands.find(band_name) == bands.end())
        {
            // this element is not yet added at all
            // => create new map
            timestep_map qMap;
            QVector<GDALRasterBandH> raster_bands(data_count);

            raster_bands[data_index] = gdalBand;
            qMap[time] = raster_bands;
            bands[band_name] = qMap;

        } else {
            timestep_map::iterator timestep = bands[band_name].find(time);
            if (timestep == bands[band_name].end())
            {
                // element is there, but new timestep
                // => create just new map entry
                QVector<GDALRasterBandH> raster_bands(data_count);
                raster_bands[data_index] = gdalBand;
                bands[band_name].insert(time, raster_bands);

            } else
            {
                // element is there, and timestep too, this must be other part
                // of the existing vector
                timestep.value().replace(data_index, gdalBand);
            }
        }
    }

}

static void populateScaleForVector(const GRIBParams& params, NodeOutput* tos){
    // there are no scalar data associated with vectors, so
    // assign vector length as scalar data at least
    // see #134
    for (uint idx=0; idx<params.nPoints; ++idx)
    {
        if (is_nodata(tos->valuesV[idx].x) ||
            is_nodata(tos->valuesV[idx].y))
        {
            tos->values[idx] = -9999.0;
        }
        else {
            tos->values[idx] = tos->valuesV[idx].length();
        }
    }
}


static void addDataToOutput(GDALRasterBandH raster_band, const GRIBParams& params, NodeOutput* tos, float * pafScanline, bool is_vector, bool is_x) {
    float nodata = (float) (GDALGetRasterNoDataValue(raster_band, 0)); // in double

    for (uint y = 0; y < params.ySize; ++y)
    {
        // buffering per-line
        CPLErr err = GDALRasterIO(
                    raster_band,
                    GF_Read,
                    0, //nXOff
                    y, //nYOff
                    params.xSize,  //nXSize
                    1, //nYSize
                    pafScanline, //pData
                    params.xSize, //nBufXSize
                    1, //nBufYSize
                    GDT_Float32,
                    0, //nPixelSpace
                    0 //nLineSpace
                    );
        if (err != CE_None) throw LoadStatus::Err_InvalidData;

        for (uint x = 0; x < params.xSize; ++x)
        {
            int idx = x + params.xSize*y;
            float val = pafScanline[x];

            if (is_nodata(val, nodata)) {
                // store all nodata value as this hardcoded number
                val = -9999.0;
            }

            if (is_vector)
            {
                if (is_x)
                {
                    tos->valuesV[idx].x = val;
                } else
                {
                    tos->valuesV[idx].y = val;
                }
            }
            else {
                tos->values[idx] = val;
            }
        }

    }
}

static void activateElements(Mesh* mesh, const GRIBParams& params, NodeOutput* tos){
    // Activate only elements that do all node's outputs with some data
    char* active = tos->active.data();
    for (uint idx=0; idx<params.nVolumes; ++idx)
    {
        Element elem = mesh->elements().at(idx);

        if (is_nodata(tos->values[elem.p[0]]) ||
            is_nodata(tos->values[elem.p[1]]) ||
            is_nodata(tos->values[elem.p[2]]) ||
            is_nodata(tos->values[elem.p[3]]))
        {
            active[idx] = 0; //NOT ACTIVE
        } else {
            active[idx] = 1; //ACTIVE
        }
    }
}

static void addDatasets(Mesh* mesh, const QString& fileName, const data_hash& bands, const GRIBParams& params, float * pafScanline)
{
    // Add dataset to mesh
    for (data_hash::const_iterator band = bands.begin(); band != bands.end(); band++)
    {
        DataSet* dsd = new DataSet(fileName);
        dsd->setName(band.key());
        dsd->setIsTimeVarying(band->count() > 1);

        for (timestep_map::const_iterator time_step = band.value().begin(); time_step != band.value().end(); time_step++)
        {
            QVector<GDALRasterBandH> raster_bands = time_step.value();
            bool is_vector = (raster_bands.size() > 1);
            if (is_vector)
            {
                dsd->setType(DataSet::Vector);
            } else {
                dsd->setType(DataSet::Scalar);
            }

            NodeOutput* tos = new NodeOutput;
            tos->init(params.nPoints, params.nVolumes, is_vector);
            tos->time = time_step.key();

            for (int i=0; i<raster_bands.size(); ++i)
            {
                addDataToOutput(raster_bands[i], params, tos, pafScanline, is_vector, i==0);
            }
            if (is_vector)
            {
                populateScaleForVector(params, tos);
            }

            activateElements(mesh, params, tos);

            dsd->addOutput(tos);
        }
        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }
}

static Mesh* createMesh(const GRIBParams& params) {
    Mesh::Nodes nodes(params.nPoints);
    initNodes(nodes, params);

    Mesh::Elements elements(params.nVolumes);
    initElements(elements, params);

    return new Mesh(nodes, elements);
}

/* ************************************************************************** */

Mesh* Crayfish::loadGRIB(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();

    GDALDatasetH hDataset = 0;
    float *pafScanline = 0;
    Mesh* mesh = 0;

    try
    {
        hDataset = openGRIBFile(fileName);

        // Parse parameters
        GRIBParams params;
        parseParameters(hDataset, params);

        // Init memory
        pafScanline = (float *) malloc(sizeof(float)*params.xSize);
        if (!pafScanline) throw LoadStatus::Err_NotEnoughMemory;

        // Create MESH
        mesh = createMesh(params);

        // Parse bands
        data_hash bands;
        parseRasterBands(hDataset, bands, params);

        // Create datasets
        addDatasets(mesh, fileName, bands, params, pafScanline);
    }
    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    if (hDataset) GDALClose( hDataset );
    if (pafScanline) free(pafScanline);

    return mesh;
}
