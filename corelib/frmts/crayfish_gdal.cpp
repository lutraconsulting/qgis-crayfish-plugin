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
#include <QtAlgorithms>
#include <math.h>
#include <QByteArray>

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}

#define GDAL_NODATA -999
#define CRAYFISH_NODATA -9999
#define CONTOURS_LAYER_NAME "contours"
#define CONTOURS_ATTR_NAME "CVAL"
#define FLOAT_TO_INT 1000.0

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
            if (val != GDAL_NODATA) {
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

static void classifyRawData(RawData* rd) {
    Q_ASSERT(rd);
    float* d = rd->data();

    // assign 1 to all non-NODATA values
    for (int i=0; i<rd->size(); ++i) {
        if (d[i] != GDAL_NODATA) {
            d[i] = 1.0;
        }
    }
}

static void multiply_to_get_int(RawData* rd, QVector<double>& classes) {
    // strange GDAL bug, so creation of contour lines is not working for decimal numbers
    // Assume that from GUI you can get at max 3 decimal places, so multiply by 1000
    // and hope for best

    for (int i=0; i<classes.size(); ++i) {
            classes[i] *= FLOAT_TO_INT;
        }
    rd->multiply_by(FLOAT_TO_INT);
}

static double findClassVal(double val, QVector<double>& classes) {
    Q_ASSERT(classes.size() > 1);

    if ((is_nodata(val, CRAYFISH_NODATA)) ||
        (val < classes[0]) ||
        (val > classes[classes.size() - 1]))
    {
        return CRAYFISH_NODATA;
    }

    for (int j=classes.size() - 2; j>=1; j--) {
        if (val > classes[j]) {
            return classes[j];
        }
    }

    return classes[0];
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
    GDALSetRasterNoDataValue(hBand, GDAL_NODATA);
    CPLErr err = GDALRasterIO(hBand, GF_Write, 0, 0, rd->cols(), rd->rows(),
                              rd->data(), rd->cols(), rd->rows(), GDT_Float32, 0, 0);

    if (add_mask_band) {
        GDALRasterBandH hMaskBand = GDALGetRasterBand( hDstDS, 2 );
        QVector<float> mask = rd->mask();
        err = GDALRasterIO( hMaskBand, GF_Write, 0, 0, rd->cols(), rd->rows(),
                            mask.data(), rd->cols(), rd->rows(), GDT_Float32, 0, 0 );
    }

    Q_ASSERT(err == CE_None);
    return hDstDS;
}

static OGRDataSourceH vectorDataset(const QString& outFilename, const QString& wkt, OGRwkbGeometryType wktGeometryType, bool in_memory=false) {
    QString outname(outFilename);

    OGRSFDriverH hDriver;
    if (in_memory) {
        outname += "_vector_memory.tmp";
        hDriver = OGRGetDriverByName("MEMORY");
    } else {
        hDriver = OGRGetDriverByName("ESRI Shapefile");
    }
    if (!hDriver)
      return 0;

    /* delete the file if exists, OGR_Dr_CreateDataSource cannot overwrite the existing file */
    {
        QFile file(outname);
        if (file.exists()) {
            file.remove();
        }
    }

    OGRDataSourceH hDS = OGR_Dr_CreateDataSource( hDriver, outname.toAscii().data(), NULL );
    if (!hDS)
      return 0;

    OGRSpatialReferenceH hSRS = OSRNewSpatialReference(NULL);
    QByteArray wkt_ba = wkt.toAscii();
    char * wkt_s = wkt_ba.data();
    OSRImportFromWkt(hSRS, ( char ** ) &wkt_s);

    OGRLayerH hLayer = OGR_DS_CreateLayer( hDS, CONTOURS_LAYER_NAME, hSRS, wktGeometryType, NULL );
    if (!hLayer) {
        OGR_DS_Destroy( hDS );
        return 0;
    }

    OGRFieldDefnH hFld = OGR_Fld_Create(CONTOURS_ATTR_NAME, OFTReal );
    OGR_Fld_SetWidth( hFld, 12 );
    OGR_Fld_SetPrecision( hFld, 3 );
    OGR_L_CreateField( hLayer, hFld, FALSE );
    OGR_Fld_Destroy( hFld );

    return hDS;
}

static bool contourLinesDataset(OGRLayerH hLayer, GDALRasterBandH hBand, QVector<double>& classes, bool use_nodata) {
    CPLErr err = GDALContourGenerate(
                hBand,
                0, //dfContourInterval
                0, //dfContourBase
                classes.size(), //nFixedLevelCount
                classes.data(), //padfFixedLevels
                use_nodata, //bUseNoData
                GDAL_NODATA, //dfNoDataValue
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

bool CrayfishGDAL::writeContourLinesSHP(const QString& outFilename, double interval, RawData* rd, const QString& wkt, ColorMap* cm, bool use_nodata)
{
    bool res = false;

    QVector<double> classes = generateClassification(rd, interval, cm);

    /*** 0) workaround GDAL contour bug ***/
    multiply_to_get_int(rd, classes);

    /*** 1) Create Raster ***/
    GDALDatasetH hRasterDS = rasterDataset(outFilename, rd, wkt, true, false);
    if (!hRasterDS) {
        return false;
    }
    GDALRasterBandH hBand = GDALGetRasterBand( hRasterDS, 1 );
    if (!hBand) {
        GDALClose( hRasterDS );
        return false;
    }

    /*** 2) Create Vector ***/
    GDALDatasetH hVectorDS = vectorDataset(outFilename, wkt, wkbLineString);
    if (!hVectorDS) {
        GDALClose( hRasterDS );
        return false;
    }
    OGRLayerH hLayer = OGR_DS_GetLayer( hVectorDS, 0);
    if (!hLayer) {
        GDALClose( hRasterDS );
        OGR_DS_Destroy( hVectorDS );
        return false;
    }

    /*** 3) Export Contour Lines ***/
    res = contourLinesDataset(hLayer, hBand, classes, use_nodata);
    GDALClose( hRasterDS );

    /*** 4) workaround GDAL contour bug ***/
    OGRFeatureH hFeature;
    OGR_L_ResetReading(hLayer);
    while( (hFeature = OGR_L_GetNextFeature(hLayer)) != NULL )
    {
        int field = OGR_F_GetFieldIndex(hFeature, CONTOURS_ATTR_NAME);
        double val = OGR_F_GetFieldAsDouble(hFeature, field);
        if (val != -999) {
            OGR_F_SetFieldDouble(hFeature, OGR_F_GetFieldIndex(hFeature, CONTOURS_ATTR_NAME), val/FLOAT_TO_INT);
            OGRErr err = OGR_L_SetFeature(hLayer, hFeature);
        }
    }

    OGR_DS_Destroy( hVectorDS );
    return res;
}

static bool addContourLines(const QString& outFilename, OGRGeometryH hMultiLinesGeom, QVector<double>& classes, RawData* rd, const QString& wkt, bool use_nodata) {
    bool res = false;

    // Create countour lines
    GDALDatasetH hRasterDS = rasterDataset(outFilename, rd, wkt, true, false);
    if (!hRasterDS) {
        return false;
    }
    GDALRasterBandH hBand = GDALGetRasterBand( hRasterDS, 1 );
    if (!hBand) {
        GDALClose( hRasterDS );
        return false;
    }

    OGRDataSourceH hVectorLinesDS = vectorDataset(outFilename + "_lines", wkt, wkbLineString, true);
    if (!hVectorLinesDS) {
        GDALClose( hRasterDS );
        return false;
    }
    OGRLayerH hLayerLines = OGR_DS_GetLayer( hVectorLinesDS, 0);
    if (!hLayerLines) {
        GDALClose( hRasterDS );
        OGR_DS_Destroy( hVectorLinesDS );
        return false;
    }

    res = contourLinesDataset(hLayerLines, hBand, classes, use_nodata);
    GDALClose( hRasterDS );
    if (!res) {
        OGR_DS_Destroy( hVectorLinesDS );
        return false;
    }

    // Add geometries to the hMultiLinesGeom
    OGRFeatureH hFeatureLineString;
    OGR_L_ResetReading(hLayerLines);
    while( (hFeatureLineString = OGR_L_GetNextFeature(hLayerLines)) != NULL )
    {
        OGRGeometryH hLineStringGeom = OGR_F_GetGeometryRef(hFeatureLineString);
        OGR_G_AddGeometry(hMultiLinesGeom, OGR_G_Clone(hLineStringGeom));
        OGR_F_Destroy(hFeatureLineString);
    }

    OGR_DS_Destroy( hVectorLinesDS );
    return true;
}

static bool addBoundaryLines(const QString& outFilename, OGRGeometryH hMultiLinesGeom, RawData* rd, const QString& wkt) {
    bool res = false;

    classifyRawData(rd);

    GDALDatasetH hRasterDS = rasterDataset(outFilename, rd, wkt, false, true);
    if (!hRasterDS) {
        return false;
    }
    GDALRasterBandH hBand = GDALGetRasterBand( hRasterDS, 1 );
    if (!hBand) {
        GDALClose( hRasterDS );
        return false;
    }

    OGRDataSourceH hVectorAreasDS = vectorDataset(outFilename + "areas", wkt, wkbPolygon, true);
    if (!hVectorAreasDS) {
        GDALClose( hRasterDS );
        return false;
    }
    OGRLayerH hLayerAreas = OGR_DS_GetLayer( hVectorAreasDS, 0);
    if (!hLayerAreas) {
        GDALClose( hRasterDS );
        OGR_DS_Destroy( hVectorAreasDS );
        return false;
    }

    GDALRasterBandH hMaskBand = GDALGetRasterBand( hRasterDS, 2 );
    if (!hMaskBand) {
        GDALClose( hRasterDS );
        OGR_DS_Destroy( hVectorAreasDS );
        return false;
    }
    res = contourPolygonsDataset(hLayerAreas, hBand, hMaskBand);
    GDALClose( hRasterDS );
    if (!res) {
        OGR_DS_Destroy( hVectorAreasDS );
        return false;
    }

    /*** Add areas boundaries to line layer ***/

    OGRFeatureH hFeatureArea;
    OGR_L_ResetReading(hLayerAreas);
    while( (hFeatureArea = OGR_L_GetNextFeature(hLayerAreas)) != NULL )
    {
        OGRGeometryH hAreaGeom = OGR_F_GetGeometryRef(hFeatureArea);
        // Get boundary
        OGRGeometryH hGeom = OGR_G_ForceToMultiLineString(hAreaGeom);
        for (int i=0; i< OGR_G_GetGeometryCount(hGeom); ++i) {
            OGRGeometryH hGeomIntern = OGR_G_GetGeometryRef(hGeom, i);
            Q_ASSERT(OGR_G_GetGeometryType(hGeomIntern) == wkbLineString);
            OGR_G_AddGeometry(hMultiLinesGeom, OGR_G_Clone(hGeomIntern));
        }
    }
    OGR_DS_Destroy( hVectorAreasDS );

    return true;
}

static bool outputPolygonsToFile(const QString& outFilename, OGRGeometryH hContoursMultiPolygon, const QString& wkt, const Output* output, QVector<double>& classes) {
    OGRDataSourceH hVectorDS = vectorDataset(outFilename, wkt, wkbPolygon, false);
    if (!hVectorDS) {
        return false;
    }
    OGRLayerH hLayer = OGR_DS_GetLayer( hVectorDS, 0);
    if (!hLayer) {
        OGR_DS_Destroy( hVectorDS );
        return false;
    }

    int nfeatures = 0;
    for (int i=0; i< OGR_G_GetGeometryCount(hContoursMultiPolygon); ++i) {
        OGRGeometryH hGeom = OGR_G_Clone(OGR_G_GetGeometryRef(hContoursMultiPolygon, i));
        OGRGeometryH hSurfacePointGeom = OGR_G_PointOnSurface(hGeom);
        if (hSurfacePointGeom != 0) {
            double x,y,z;
            OGR_G_GetPoint(hSurfacePointGeom, 0, &x, &y, &z);
            OGR_G_DestroyGeometry(hSurfacePointGeom);
            double val = output->dataSet->mesh()->valueAt(output, x, y); //very slow, but fortunately only one point per area
            val = findClassVal(val*FLOAT_TO_INT, classes);
            if (val != CRAYFISH_NODATA)
            {
                ++nfeatures;
                OGRFeatureH hFeature = OGR_F_Create( OGR_L_GetLayerDefn( hLayer ) );
                OGR_F_SetFieldDouble(hFeature, OGR_F_GetFieldIndex(hFeature, CONTOURS_ATTR_NAME  ), val/FLOAT_TO_INT);
                OGR_F_SetGeometry( hFeature, hGeom );
                OGR_G_DestroyGeometry(hGeom);
                if( OGR_L_CreateFeature( hLayer, hFeature ) != OGRERR_NONE )
                {
                    OGR_DS_Destroy( hVectorDS );
                    return false;
                }
                OGR_F_Destroy( hFeature );
            }
        }
    }

    OGR_DS_Destroy( hVectorDS );
    if (nfeatures == 0) {
        return false;
    } else {
        return true;
    }
}

static OGRGeometryH unionGeom(OGRGeometryH hMultiLinesGeom) {
    OGRGeometryH hMultiLinesGeomUnion = 0;
    int n = OGR_G_GetGeometryCount(hMultiLinesGeom);
    if (n < 1) {
        return hMultiLinesGeomUnion;
    }
    hMultiLinesGeomUnion = OGR_G_Clone(OGR_G_GetGeometryRef(hMultiLinesGeom, 0));
    for (int i=1; i< n; ++i) {
        OGRGeometryH hMultiLinesGeomUnion2 = OGR_G_Union(hMultiLinesGeomUnion, OGR_G_GetGeometryRef(hMultiLinesGeom, i));
        OGR_G_DestroyGeometry(hMultiLinesGeomUnion);
        hMultiLinesGeomUnion = hMultiLinesGeomUnion2;
    }

    return hMultiLinesGeomUnion;
}

bool CrayfishGDAL::writeContourAreasSHP(const QString& outFilename, double interval, RawData* rd, const QString& wkt, ColorMap* cm, const Output* output, bool add_boundary, bool use_nodata)
{
    OGRGeometryH hMultiLinesGeom = OGR_G_CreateGeometry(wkbMultiLineString);
    QVector<double> classes = generateClassification(rd, interval, cm);

    /*** 0) workaround GDAL contour bug ***/
    multiply_to_get_int(rd, classes);

    /*** 1) Add contour Lines to hMultiLinesGeom ***/
    if (!addContourLines(outFilename, hMultiLinesGeom, classes, rd, wkt, use_nodata))
    {
        OGR_G_DestroyGeometry(hMultiLinesGeom);
        return false;
    }

    /*** 2) Add boundaries areas of active elements to hMultiLinesGeom ***/
    if (add_boundary && !addBoundaryLines(outFilename, hMultiLinesGeom, rd, wkt)) {
        OGR_G_DestroyGeometry(hMultiLinesGeom);
        return false;
    }

    /*** 3) Make union of hMultiLinesGeom and create polygons from it ***/
    hMultiLinesGeom = unionGeom(hMultiLinesGeom);
    if (hMultiLinesGeom == 0){
        return false;
    }
    OGRGeometryH hContoursMultiPolygon = OGR_G_Polygonize(hMultiLinesGeom);
    OGR_G_DestroyGeometry(hMultiLinesGeom);

    /*** 4) Assign range to polygons and Store to the file ***/
    if (!outputPolygonsToFile(outFilename, hContoursMultiPolygon, wkt, output, classes)) {
        OGR_G_DestroyGeometry(hContoursMultiPolygon);
        return false;
    }
    OGR_G_DestroyGeometry(hContoursMultiPolygon);
    return true;
}


/******************************************************************************************************/
void CrayfishGDALDataset::init(const QString& dsName) {
    mDatasetName = dsName;

    // Open dataset
    mHDataset = GDALOpen( mDatasetName.toAscii().data(), GA_ReadOnly );
    if(!mHDataset) throw LoadStatus::Err_UnknownFormat;

    // Now parse it
    parseParameters();
    parseProj();
}

void CrayfishGDALDataset::parseParameters() {
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

void CrayfishGDALDataset::parseProj() {
   char* proj = const_cast<char*> (GDALGetProjectionRef( mHDataset ));
   if( proj != NULL ) {
       mProj = QString(proj);
   }
}

/******************************************************************************************************/

bool CrayfishGDALReader::meshes_equals(const CrayfishGDALDataset* ds1, const CrayfishGDALDataset* ds2) const
{
    return ((ds1->mXSize == ds2->mXSize) &&
            (ds1->mYSize == ds2->mYSize) &&
            (is_nodata(ds1->mGT[0], ds2->mGT[0])) &&
            (is_nodata(ds1->mGT[1], ds2->mGT[1])) &&
            (is_nodata(ds1->mGT[2], ds2->mGT[2])) &&
            (is_nodata(ds1->mGT[3], ds2->mGT[3])) &&
            (is_nodata(ds1->mGT[4], ds2->mGT[4])) &&
            (is_nodata(ds1->mGT[5], ds2->mGT[5])) &&
            ds1->mProj == ds2->mProj);
}


bool CrayfishGDALReader::initNodes(Mesh::Nodes& nodes) {
   Node* nodesPtr = nodes.data();
   uint mXSize = meshGDALDataset()->mXSize;
   uint mYSize = meshGDALDataset()->mYSize;
   const double* mGT = meshGDALDataset()->mGT;

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
   uint mXSize = meshGDALDataset()->mXSize;
   uint mYSize = meshGDALDataset()->mYSize;

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

QString CrayfishGDALReader::GDALFileName(const QString& fileName) {
    return fileName;
}

float CrayfishGDALReader::parseMetadataTime(const QString& time_s)
{
   QString time_trimmed = time_s.trimmed();
   QStringList times = time_trimmed.split(" ");
   return times[0].toFloat();
}

CrayfishGDALReader::metadata_hash CrayfishGDALReader::parseMetadata(GDALMajorObjectH gdalObject, const char* pszDomain /* = 0 */) {
    CrayfishGDALReader::metadata_hash meta;
    char** GDALmetadata = 0;
    GDALmetadata = GDALGetMetadata(gdalObject, pszDomain);

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

void CrayfishGDALReader::parseRasterBands(const CrayfishGDALDataset* cfGDALDataset){
   for (uint i = 1; i <= cfGDALDataset->mNBands; ++i ) // starts with 1 .... ehm....
   {
       // Get Band
       GDALRasterBandH gdalBand = GDALGetRasterBand( cfGDALDataset->mHDataset, i );
       if (!gdalBand) {
           throw LoadStatus::Err_InvalidData;
       }


       // Get metadata
       metadata_hash metadata = parseMetadata(gdalBand);

       QString band_name;
       float time = std::numeric_limits<float>::min();
       bool is_vector;
       bool is_x;
       if (parseBandInfo(cfGDALDataset, metadata, band_name, &time, &is_vector, &is_x)) {
           continue;
       }

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
}

void CrayfishGDALReader::populateScaleForVector(NodeOutput* tos){
   // there are no scalar data associated with vectors, so
   // assign vector length as scalar data at least
   // see #134
   for (uint idx=0; idx<meshGDALDataset()->mNPoints; ++idx)
   {
       if (is_nodata(tos->getValuesV()[idx].x) ||
           is_nodata(tos->getValuesV()[idx].y))
       {
           tos->getValues()[idx] = CRAYFISH_NODATA;
       }
       else {
           tos->getValues()[idx] = tos->getValuesV()[idx].length();
       }
   }
}


void CrayfishGDALReader::addDataToOutput(GDALRasterBandH raster_band, NodeOutput* tos, bool is_vector, bool is_x) {
   float nodata = (float) (GDALGetRasterNoDataValue(raster_band, 0)); // in double
   uint mXSize = meshGDALDataset()->mXSize;
   uint mYSize = meshGDALDataset()->mYSize;

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
                   GDT_Float32, //eBufType
                   0, //nPixelSpace
                   0 //nLineSpace
                   );
       if (err != CE_None) {
           throw LoadStatus::Err_InvalidData;
       }

       for (uint x = 0; x < mXSize; ++x)
       {
           int idx = x + mXSize*y;
           float val = mPafScanline[x];

           if (is_nodata(val, nodata)) {
               // store all nodata value as this hardcoded number
               val = CRAYFISH_NODATA;
           }

           if (is_vector)
           {
               if (is_x)
               {
                   tos->getValuesV()[idx].x = val;
               } else
               {
                   tos->getValuesV()[idx].y = val;
               }
           }
           else {
               tos->getValues()[idx] = val;
           }
       }

       GDALFlushRasterCache(raster_band);
   }
}

void CrayfishGDALReader::activateElements(NodeOutput* tos){
   // Activate only elements that do all node's outputs with some data
   char* active = tos->getActive().data();
   for (uint idx=0; idx<meshGDALDataset()->mNVolumes; ++idx)
   {
       Element elem = mMesh->elements().at(idx);

       if (is_nodata(tos->getValues()[elem.p(0)]) ||
           is_nodata(tos->getValues()[elem.p(1)]) ||
           is_nodata(tos->getValues()[elem.p(2)]) ||
           is_nodata(tos->getValues()[elem.p(3)]))
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
           tos->init(meshGDALDataset()->mNPoints, meshGDALDataset()->mNVolumes, is_vector);
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
       if (getRefTime().isValid())
        dsd->setRefTime(getRefTime());
       mMesh->addDataSet(dsd);
   }
}

void CrayfishGDALReader::createMesh() {
   Mesh::Nodes nodes(meshGDALDataset()->mNPoints);
   bool is_longitude_shifted = initNodes(nodes);

   Mesh::Elements elements(meshGDALDataset()->mNVolumes);
   initElements(nodes, elements, is_longitude_shifted);

   mMesh = new Mesh(nodes, elements);
   bool proj_added = addSrcProj();
   if ((!proj_added) && is_longitude_shifted) {
       QString wgs84("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs");
       mMesh->setSourceCrs(wgs84);
   }
}

bool CrayfishGDALReader::addSrcProj() {
   QString proj = meshGDALDataset()->mProj;
   if( !proj.isEmpty() ) {
       mMesh->setSourceCrsFromWKT(proj);
       return true;
   }
   return false;
}

QStringList CrayfishGDALReader::parseDatasetNames(const QString& fileName) {
    QString gdal_name = GDALFileName(fileName);
    QStringList ret;

    GDALDatasetH hDataset = GDALOpen( gdal_name.toAscii().data(), GA_ReadOnly );
    if( hDataset == NULL ) throw LoadStatus::Err_UnknownFormat;

    metadata_hash metadata = parseMetadata(hDataset, "SUBDATASETS");

    foreach(const QString &key, metadata.keys()) {
        if (key.endsWith("_name")) {
            // skip subdataset desc keys, just register names
            ret.append(metadata.value(key));
        }
    }

    // there are no GDAL subdatasets
    if (ret.isEmpty()) {
        ret.append(gdal_name);
    }

    GDALClose( hDataset );
    return ret;
}

void CrayfishGDALReader::registerDriver() {
    // re-register all
    GDALAllRegister();
    // check that our driver exists
    GDALDriverH hDriver = GDALGetDriverByName(mDriverName.toAscii().data());
    if (!hDriver) throw LoadStatus::Err_MissingDriver;
}

const CrayfishGDALDataset* CrayfishGDALReader::meshGDALDataset()
{
    Q_ASSERT(gdal_datasets.size() > 0);
    return gdal_datasets[0];
}

Mesh* CrayfishGDALReader::load(LoadStatus* status)
{
   if (status) status->clear();

   mPafScanline = 0;
   mMesh = 0;

   try
   {
       registerDriver();

       // some formats like NETCFD has data stored in subdatasets
       QStringList subdatasets = parseDatasetNames(mFileName);

       // First parse ALL datasets/bands to gather vector quantities
       // if case they are splitted in different subdatasets
       foreach (QString gdal_dataset_name, subdatasets)
       {
           // Parse dataset parameters and projection
           CrayfishGDALDataset* cfGDALDataset = new CrayfishGDALDataset;
           cfGDALDataset->init(gdal_dataset_name);

           if (!mMesh) {
               // If it is first dataset, create mesh from it
               gdal_datasets.append(cfGDALDataset);

               // Init memory for data reader
               mPafScanline = new float [cfGDALDataset->mXSize];

               // Create mMesh
               createMesh();

               // Parse bands
               parseRasterBands(cfGDALDataset);

           } else if (meshes_equals(meshGDALDataset(), cfGDALDataset)) {
                   gdal_datasets.append(cfGDALDataset);
                   // Parse bands
                   parseRasterBands(cfGDALDataset);
           } else {
                   // Do not use
                   delete cfGDALDataset;
           }
       }

       // Create CRAYFISH datasets
       addDatasets();
   }
   catch (LoadStatus::Error error)
   {
       if (status) status->mLastError = (error);
       if (mMesh) delete mMesh;
       mMesh = 0;
   }

   qDeleteAll(gdal_datasets);
   if (mPafScanline) delete[] mPafScanline;

   // do not allow mesh without any valid datasets
   if (mMesh && (mMesh->dataSets().empty())) {
       if (status) status->mLastError = LoadStatus::Err_InvalidData;
       if (mMesh) delete mMesh;
       mMesh = 0;
   }
   return mMesh;
}

