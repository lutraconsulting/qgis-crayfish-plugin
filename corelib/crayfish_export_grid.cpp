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

#include "crayfish_dataset.h"
#include "crayfish_gdal.h"
#include "crayfish_output.h"
#include "crayfish_renderer.h" // for MapToPixel


static void exportRawDataElements(Element::Type elemType, const Output* output, RawData* rd, const MapToPixel& xform)
{
  const Mesh* mesh = output->dataSet->mesh();
  const Mesh::Elements& elems = mesh->elements();
  for (int i=0; i < elems.count(); i++)
  {
    const Element& elem = elems[i];
    if(elem.eType() != elemType)
      continue;

    if (elem.isDummy())
      continue;

    // If the element's activity flag is off, ignore it
    if(!output->isActive(i))
      continue;

    const BBox& bbox = mesh->projectedBBox(i);

    // Get the BBox of the element in pixels
    QPointF ll = xform.realToPixel(bbox.minX, bbox.minY);
    QPointF ur = xform.realToPixel(bbox.maxX, bbox.maxY);

    // TODO: floor/ceil ?
    int topLim = ur.y();
    int bottomLim = ll.y();
    int leftLim = ll.x();
    int rightLim = ur.x();

    double val;
    for (int j=topLim; j<=bottomLim; j++)
    {
      float* line = rd->scanLine(j);

      for (int k=leftLim; k<=rightLim; k++)
      {
        Q_ASSERT(k >= 0 && k < rd->cols());
        QPointF p = xform.pixelToReal(k, j);
        if( mesh->valueAt(i, p.x(), p.y(), &val, output) )
            line[k] = val; // The supplied point was inside the element
      }
    }
  }
}



//! Return new raw data image for the given dataset/output time, sampled with given resolution
static RawData* exportRawData(const Output* output, double mupp)
{
  if (!output)
    return 0;
  if (mupp <= 0)
    return 0;

  const Mesh* mesh = output->dataSet->mesh();

  // keep one pixel around
  // e.g. if we have mesh with coords 0..10 with sampling of 1, then we actually need 11 pixels
  BBox bbox = mesh->projectedExtent();
  double xMin = bbox.minX - mupp;
  double xMax = bbox.maxX + mupp;
  double yMin = bbox.minY - mupp;
  double yMax = bbox.maxY + mupp;

  // calculate transform
  // (uses envelope of the mesh)
  int imgWidth = ceil((xMax - xMin) / mupp);
  int imgHeight = ceil((yMax - yMin) / mupp);
  if (!imgWidth || !imgHeight)
    return 0;
  MapToPixel xform(xMin, yMin, mupp, imgHeight);

  // prepare geometry transform
  yMax = yMin + imgHeight*mupp;  // this is different from yMax previously - due to using fixed pixel size
  // also shift the exported raster by half of pixel size in both directions
  // sampled value for X needs to occupy interval (X-mupp/2,X+mupp/2) - without the shift the value would be misaligned to (X,X+mupp)
  QVector<double> geo;
  geo << xMin - mupp/2 << mupp << 0
      << yMax + mupp/2 << 0    << -mupp;

  RawData* rd = new RawData(imgWidth, imgHeight, geo);

  // First export quads, then triangles.
  // We use this ordering because from 1D simulation we will get tesselated river polygons from linestrings
  // and we want them to be on top of the terrain (quads)
  exportRawDataElements(Element::ENP, output, rd, xform);
  exportRawDataElements(Element::E4Q, output, rd, xform);
  exportRawDataElements(Element::E3T, output, rd, xform);
  exportRawDataElements(Element::E2L, output, rd, xform);

  return rd;
}


bool Crayfish::exportRawDataToTIF(const Output* output, double mupp, const QString& outFilename, const QString& projWkt)
{
  RawData* rd = exportRawData(output, mupp);
  if (!rd)
    return false;

  bool res = CrayfishGDAL::writeGeoTIFF(outFilename, rd, projWkt);
  delete rd;

  return res;
}

bool Crayfish::exportContoursToSHP(const Output* output, double mupp, double interval, const QString& outFilename, const QString& projWkt, bool useLines, ColorMap* cm, bool add_boundary, bool use_nodata)
{


  RawData* rd = exportRawData(output, mupp);
  if (!rd)
    return false;

  bool res;
  if (useLines) {
      // lines
      res = CrayfishGDAL::writeContourLinesSHP(outFilename, interval, rd, projWkt, cm, use_nodata);
  } else {
      //areas
      res = CrayfishGDAL::writeContourAreasSHP(outFilename, interval, rd, projWkt, cm, output, add_boundary, use_nodata);
  }
  delete rd;

  return res;
}
