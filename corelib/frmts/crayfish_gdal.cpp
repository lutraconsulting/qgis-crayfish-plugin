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

#include "crayfish_gdal.h"
#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#include <gdal.h>
#include "ogr_api.h"
#include "ogr_srs_api.h"
#include "gdal_alg.h"
#include <QFile>
#include <QString>
#include <QMap>
#include <QHash>
#include <QVector>
#include <QRegExp>
#include <math.h>

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}

#define CONTOURS_LAYER_NAME "contours"
#define CONTOURS_ATTR_NAME "CVAL"

static QVector<double>  generateClassification(const RawData* rd, double interval, ColorMap* cm ) {
    Q_ASSERT((interval > 1e-5) || cm);
    QVector<double> classes;
    if (cm) {
        // from colormap
        for (int i=0; i<cm->items.size(); ++i) {
            classes.push_back(cm->items[i].value);
        }
    } else {
        // interval
        double minv = 1e100;
        double maxv = -1e100;

        for (int i=0; i<rd->size(); ++i) {
            double val =rd->dataAt(i);
            if (val != -999) {
                if (val < minv) minv = val;
                if (val > maxv) maxv = val;
            }
        }

        double val = minv;
        while (val < maxv) {
            classes.push_back(val);
            val += interval;
        }
    }
    return classes;
}

static void classifyRawData(RawData* rd, QVector<double>& classes) {
    Q_ASSERT(rd);
    Q_ASSERT(classes.size() > 1);

    float* d = rd->data();

    //////////// FILL INTO CLASSES
    for (int i=0; i<rd->size(); ++i) {
        if (d[i] != -999) {

            if (d[i] > classes[classes.size() - 1]) {
                d[i] = classes[classes.size() - 1];
            }
            else if (d[i] < classes[0]) {
                d[i] = classes[0];
            } else {
                for (int j=classes.size() - 1; j>=0; j--) {
                    double val = classes[j];
                    if (d[i]>val) {
                        d[i] = val;
                        break;
                    }
                }
            }
        }
    }
}

static GDALDatasetH rasterDataset(const QString& outFilename, RawData* rd, const QString& wkt, bool in_memory=false, bool add_mask_band=false) {
    QString outName(outFilename);

    GDALAllRegister();
    GDALDriverH hDriver = 0;

    if (in_memory) {
        outName += "_raster_memory.tmp";
        hDriver = GDALGetDriverByName("MEM");
    } else {
        hDriver = GDALGetDriverByName("GTiff");
    }
    if (!hDriver)
      return 0;

    const char *papszOptions[] = {"COMPRESS=LZW", NULL};
    if (in_memory) {
        papszOptions[0] = NULL;
    }

    int nbands = add_mask_band ? 2 : 1;

    GDALDatasetH hDstDS = GDALCreate( hDriver,
                                      outName.toAscii().data(),
                                      rd->cols(),
                                      rd->rows(),
                                      nbands, // data band and mask band
                                      GDT_Float32,
                                      (char**) papszOptions );
    if (!hDstDS)
      return 0;

    GDALSetGeoTransform( hDstDS, rd->geoTransform().data() );
    GDALSetProjection( hDstDS, wkt.toAscii().data() );

    GDALRasterBandH hBand = GDALGetRasterBand( hDstDS, 1 );
    GDALSetRasterNoDataValue(hBand, -999);
    GDALRasterIO( hBand, GF_Write, 0, 0, rd->cols(), rd->rows(),
                  rd->data(), rd->cols(), rd->rows(), GDT_Float32, 0, 0 );

    if (add_mask_band) {
        GDALRasterBandH hMaskBand = GDALGetRasterBand( hDstDS, 2 );
        QVector<float> mask = rd->mask();
        GDALRasterIO( hMaskBand, GF_Write, 0, 0, rd->cols(), rd->rows(),
                      mask.data(), rd->cols(), rd->rows(), GDT_Float32, 0, 0 );
    }
    return hDstDS;
}

static GDALDatasetH vectorDataset(const QString& outFilename, const QString& wkt, OGRwkbGeometryType wktGeometryType) {
    OGRSFDriverH hDriver = OGRGetDriverByName("ESRI Shapefile");
    if (!hDriver)
      return 0;

    /* delete the file if exists, OGR_Dr_CreateDataSource cannot overwrite the existing file */
    {
        QFile file(outFilename);
        if (file.exists()) {
            file.remove();
        }
    }

    OGRDataSourceH hDS = OGR_Dr_CreateDataSource( hDriver, outFilename.toAscii().data(), NULL );
    if (!hDS)
      return 0;

    OGRSpatialReferenceH hSRS = OSRNewSpatialReference(NULL);
    char * wkt_s = wkt.toAscii().data();
    OSRImportFromWkt(hSRS, ( char ** ) &wkt_s);

    OGRLayerH hLayer = OGR_DS_CreateLayer( hDS, CONTOURS_LAYER_NAME, hSRS, wktGeometryType, NULL );
    if (!hLayer) {
        GDALClose( hDS );
        return 0;
    }

    OGRFieldDefnH hFld = OGR_Fld_Create(CONTOURS_ATTR_NAME, OFTReal );
    OGR_Fld_SetWidth( hFld, 12 );
    OGR_Fld_SetPrecision( hFld, 3 );
    OGR_L_CreateField( hLayer, hFld, FALSE );
    OGR_Fld_Destroy( hFld );

    return hDS;
}

static bool contourLinesDataset(OGRLayerH hLayer, GDALRasterBandH hBand, QVector<double>& classes) {
    CPLErr err = GDALContourGenerate(
                hBand,
                0, //dfContourInterval
                0, //dfContourBase
                classes.size(), //nFixedLevelCount
                classes.data(), //padfFixedLevels
                TRUE, //bUseNoData
                -999, //dfNoDataValue
                hLayer,
                -1, // ID attribute index
                OGR_FD_GetFieldIndex( OGR_L_GetLayerDefn( hLayer ), CONTOURS_ATTR_NAME ),
                NULL, //pfnProgress
                NULL //pProgressArg
                );
    return err == CPLE_None;
}

static bool contourPolygonsDataset(OGRLayerH hLayer, GDALRasterBandH hBand, GDALRasterBandH hMaskBand) {
    CPLErr err = GDALFPolygonize(
                         hBand,
                         hMaskBand,
                         hLayer,
                         OGR_FD_GetFieldIndex( OGR_L_GetLayerDefn( hLayer ), CONTOURS_ATTR_NAME ),
                         NULL, //options
                         NULL, //pfnProgress
                         NULL //pProgressArg
                 );
    return err == CPLE_None;
}

bool CrayfishGDAL::writeGeoTIFF(const QString& outFilename, RawData* rd, const QString& wkt)
{
  GDALDatasetH hDstDS = rasterDataset(outFilename, rd, wkt, false);

  if (!hDstDS) {
    return false;
  } else {
    GDALClose( hDstDS );
    return true;
  }
}

bool CrayfishGDAL::writeContoursSHP(const QString& outFilename, double interval, RawData* rd, const QString& wkt, bool useLines, ColorMap* cm)
{
    bool res = false;

    QVector<double> classes = generateClassification(rd, interval, cm);

    /*** 1) Create Raster ***/
    if (!useLines)
        classifyRawData(rd, classes);

    GDALDatasetH hRasterDS = rasterDataset(outFilename, rd, wkt, true, !useLines);
    if (!hRasterDS) {
        return false;
    }
    GDALRasterBandH hBand = GDALGetRasterBand( hRasterDS, 1 );
    if (!hBand) {
        GDALClose( hRasterDS );
        return false;
    }

    /*** 2) Create Vector ***/
    GDALDatasetH hVectorDS = vectorDataset(outFilename, wkt, useLines ? wkbLineString:wkbPolygon);
    if (!hVectorDS) {
        GDALClose( hRasterDS );
        return false;
    }
    OGRLayerH hLayer = OGR_DS_GetLayer( hVectorDS, 0);
    if (!hLayer) {
        GDALClose( hRasterDS );
        GDALClose( hVectorDS );
        return false;
    }

    /*** 3) Export ***/
    if (useLines) {
        /*** Export Contour Lines ***/
        res = contourLinesDataset(hLayer, hBand, classes);
    } else {
        /*** Export Contour Areas ***/
        GDALRasterBandH hMaskBand = GDALGetRasterBand( hRasterDS, 2 );
        if (!hMaskBand) {
            GDALClose( hRasterDS );
            GDALClose( hVectorDS );
            return false;
        }
        res = contourPolygonsDataset(hLayer, hBand, hMaskBand);
    }

    GDALClose( hRasterDS );
    GDALClose( hVectorDS );
    return res;
}


/******************************************************************************************************/
void CrayfishGDALReader::parseParameters() {
   mNBands = GDALGetRasterCount( mHDataset );
   if (mNBands == 0) throw LoadStatus::Err_InvalidData;

   GDALGetGeoTransform( mHDataset, mGT ); // in case of error it returns Identid

   mXSize = GDALGetRasterXSize( mHDataset ); //raster width in pixels
   if (mXSize == 0) throw LoadStatus::Err_InvalidData;

   mYSize = GDALGetRasterYSize( mHDataset ); //raster height in pixels
   if (mYSize == 0) throw LoadStatus::Err_InvalidData;

   mNPoints = mXSize * mYSize;
   mNVolumes = (mXSize - 1) * (mYSize -1);
}

void CrayfishGDALReader::openFile() {

   GDALAllRegister();
   GDALDriverH hDriver = GDALGetDriverByName(mDriverName.toAscii().data());
   if (!hDriver) throw LoadStatus::Err_MissingDriver;

   // Open dataset
   mHDataset = GDALOpen( mFileName.toAscii().data(), GA_ReadOnly );
   if( mHDataset == NULL ) throw LoadStatus::Err_UnknownFormat;
}

bool CrayfishGDALReader::initNodes(Mesh::Nodes& nodes) {
   Node* nodesPtr = nodes.data();
   for (uint y = 0; y < mYSize; ++y)
   {
       for (uint x = 0; x < mXSize; ++x, ++nodesPtr)
       {
           nodesPtr->setId(x + mXSize*y);
           nodesPtr->x = mGT[0] + (x+0.5)*mGT[1] + (y+0.5)*mGT[2];
           nodesPtr->y = mGT[3] + (x+0.5)*mGT[4] + (y+0.5)*mGT[5];
       }
   }

   BBox extent = computeExtent(nodes.constData(), nodes.size());
   // we want to detect situation when there is whole earth represented in dataset
   bool is_longitude_shifted = (extent.minX>=0.0f) &&
                               (fabs(extent.minX + extent.maxX - 360.0f) < 1.0f) &&
                               (extent.minY>=-90.0f) &&
                               (extent.maxX<=360.0f) &&
                               (extent.maxX>180.0f) &&
                               (extent.maxY<=90.0f);
   if (is_longitude_shifted)  {
       for (int n=0; n<nodes.size(); ++n)
       {
           if (nodes[n].x>180.0f) {
               nodes[n].x -= 360.0f;
           }
       }
   }

   return is_longitude_shifted;
}

void CrayfishGDALReader::initElements(Mesh::Nodes& nodes, Mesh::Elements& elements, bool is_longitude_shifted) {
   Element* elementsPtr = elements.data();
   int reconnected = 0;
   int eid = 0;
   for (uint y = 0; y < mYSize-1; ++y)
   {
       for (uint x = 0; x < mXSize-1; ++x)
       {
           if (is_longitude_shifted &&
                   (nodes[x + mXSize*y].x > 0.0f) &&
                   (nodes[x + 1 + mXSize*y].x < 0.0f))
               // omit border element
           {
               --reconnected;
               continue;
           }

           if (is_longitude_shifted && (x==0))
           {
               // create extra elements around prime meridian
               elementsPtr->setId(eid++);
               elementsPtr->setEType(Element::E4Q);
               elementsPtr->setP(0, mXSize*(y + 1));
               elementsPtr->setP(3, mXSize*y);
               elementsPtr->setP(2, mXSize - 1 + mXSize*y);
               elementsPtr->setP(1, mXSize - 1 + mXSize*(y + 1));
               ++reconnected;
               ++elementsPtr;
           }

           // other elements
           elementsPtr->setId(eid++);
           elementsPtr->setEType(Element::E4Q);
           elementsPtr->setP(0, x + 1 + mXSize*(y + 1));
           elementsPtr->setP(3, x + 1 + mXSize*y);
           elementsPtr->setP(2, x + mXSize*y);
           elementsPtr->setP(1, x + mXSize*(y + 1));
           ++elementsPtr;
       }
   }
   //make sure we have discarded same amount of elements that we have added
   Q_ASSERT(reconnected == 0);
}

float CrayfishGDALReader::parseMetadataTime(const QString& time_s)
{
   QString time_trimmed = time_s.trimmed();
   QStringList times = time_trimmed.split(" ");
   return times[0].toFloat();
}

CrayfishGDALReader::metadata_hash CrayfishGDALReader::parseMetadata(GDALRasterBandH gdalBand)
{
    CrayfishGDALReader::metadata_hash meta;

    char** GDALmetadata = GDALGetMetadata( gdalBand, 0 );
    if ( GDALmetadata )
    {
        for ( int j = 0; GDALmetadata[j]; ++j )
        {
            QString metadata_pair = GDALmetadata[j]; //KEY = VALUE
            QStringList metadata = metadata_pair.split("=");
            if (metadata.length() > 1) {
                QString key = metadata.takeFirst().toLower();
                QString value = metadata.join("=");
                meta[key] = value;
            }
        }
    }

    return meta;
}

void CrayfishGDALReader::parseRasterBands() {
   for (uint i = 1; i <= mNBands; ++i ) // starts with 1 .... ehm....
   {
       // Get Band
       GDALRasterBandH gdalBand = GDALGetRasterBand( mHDataset, i );
       if (!gdalBand) throw LoadStatus::Err_InvalidData;


       // Get metadata
       metadata_hash metadata = parseMetadata(gdalBand);

       QString band_name;
       float time = std::numeric_limits<float>::min();
       if (parseBandInfo(metadata, band_name, &time)) {
           continue;
       }

       bool is_vector;
       bool is_x;
       determineBandVectorInfo(band_name, &is_vector, &is_x);

       // Add to data structures
       int data_count = is_vector ? 2 : 1;
       int data_index = is_x ? 0 : 1;
       if (mBands.find(band_name) == mBands.end())
       {
           // this element is not yet added at all
           // => create new map
           timestep_map qMap;
           QVector<GDALRasterBandH> raster_bands(data_count);

           raster_bands[data_index] = gdalBand;
           qMap[time] = raster_bands;
           mBands[band_name] = qMap;

       } else {
           timestep_map::iterator timestep = mBands[band_name].find(time);
           if (timestep == mBands[band_name].end())
           {
               // element is there, but new timestep
               // => create just new map entry
               QVector<GDALRasterBandH> raster_bands(data_count);
               raster_bands[data_index] = gdalBand;
               mBands[band_name].insert(time, raster_bands);

           } else
           {
               // element is there, and timestep too, this must be other part
               // of the existing vector
               timestep.value().replace(data_index, gdalBand);
           }
       }
   }

   if (mBands.empty()) throw LoadStatus::Err_InvalidData;
}

void CrayfishGDALReader::populateScaleForVector(NodeOutput* tos){
   // there are no scalar data associated with vectors, so
   // assign vector length as scalar data at least
   // see #134
   for (uint idx=0; idx<mNPoints; ++idx)
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


void CrayfishGDALReader::addDataToOutput(GDALRasterBandH raster_band, NodeOutput* tos, bool is_vector, bool is_x) {
   float nodata = (float) (GDALGetRasterNoDataValue(raster_band, 0)); // in double

   for (uint y = 0; y < mYSize; ++y)
   {
       // buffering per-line
       CPLErr err = GDALRasterIO(
                   raster_band,
                   GF_Read,
                   0, //nXOff
                   y, //nYOff
                   mXSize,  //nXSize
                   1, //nYSize
                   mPafScanline, //pData
                   mXSize, //nBufXSize
                   1, //nBufYSize
                   GDT_Float32,
                   0, //nPixelSpace
                   0 //nLineSpace
                   );
       if (err != CE_None) throw LoadStatus::Err_InvalidData;

       for (uint x = 0; x < mXSize; ++x)
       {
           int idx = x + mXSize*y;
           float val = mPafScanline[x];

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

void CrayfishGDALReader::activateElements(NodeOutput* tos){
   // Activate only elements that do all node's outputs with some data
   char* active = tos->active.data();
   for (uint idx=0; idx<mNVolumes; ++idx)
   {
       Element elem = mMesh->elements().at(idx);

       if (is_nodata(tos->values[elem.p(0)]) ||
           is_nodata(tos->values[elem.p(1)]) ||
           is_nodata(tos->values[elem.p(2)]) ||
           is_nodata(tos->values[elem.p(3)]))
       {
           active[idx] = 0; //NOT ACTIVE
       } else {
           active[idx] = 1; //ACTIVE
       }
   }
}

void CrayfishGDALReader::addDatasets()
{
   // Add dataset to mMesh
   for (data_hash::const_iterator band = mBands.begin(); band != mBands.end(); band++)
   {
       DataSet* dsd = new DataSet(mFileName);
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
           tos->init(mNPoints, mNVolumes, is_vector);
           tos->time = time_step.key();

           for (int i=0; i<raster_bands.size(); ++i)
           {
               addDataToOutput(raster_bands[i], tos, is_vector, i==0);
           }
           if (is_vector)
           {
               populateScaleForVector(tos);
           }

           activateElements(tos);

           dsd->addOutput(tos);
       }
       dsd->updateZRange();
       mMesh->addDataSet(dsd);
   }
}

void CrayfishGDALReader::createMesh() {
   Mesh::Nodes nodes(mNPoints);
   bool is_longitude_shifted = initNodes(nodes);

   Mesh::Elements elements(mNVolumes);
   initElements(nodes, elements, is_longitude_shifted);

   mMesh = new Mesh(nodes, elements);
   bool proj_added = addSrcProj();
   if ((!proj_added) && is_longitude_shifted) {
       QString wgs84("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs");
       mMesh->setSourceCrs(wgs84);
   }
}

bool CrayfishGDALReader::addSrcProj() {
   char* proj = const_cast<char*> (GDALGetProjectionRef( mHDataset ));
   if( proj != NULL ) {
       QString proj_wkt(proj);
       mMesh->setSourceCrsFromWKT(proj_wkt);
       return true;
   }
   return false;
}

Mesh* CrayfishGDALReader::load(LoadStatus* status)
{
   if (status) status->clear();

   mHDataset = 0;
   mPafScanline = 0;
   mMesh = 0;

   try
   {
       openFile();

       // Parse parameters
       parseParameters();

       // Init memory
       mPafScanline = (float *) malloc(sizeof(float)*mXSize);
       if (!mPafScanline) throw LoadStatus::Err_NotEnoughMemory;

       // Create mMesh
       createMesh();

       // Parse bands
       parseRasterBands();

       // Create datasets
       addDatasets();
   }
   catch (LoadStatus::Error error)
   {
       if (status) status->mLastError = (error);
       if (mMesh) delete mMesh;
       mMesh = 0;
   }

   if (mHDataset) GDALClose( mHDataset );
   if (mPafScanline) free(mPafScanline);

   return mMesh;
}

