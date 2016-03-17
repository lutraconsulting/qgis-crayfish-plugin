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

#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_mesh.h"

#include "crayfish_hdf5.h"
#include "crayfish_e4q.h"

#include <algorithm>

static HdfFile openHdfFile(const QString& fileName)
{
    HdfFile file(fileName);
    if (!file.isValid())
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return file;
}

static HdfGroup openHdfGroup(const HdfFile& hdfFile, const QString& name)
{
    HdfGroup grp = hdfFile.group(name);
    if (!grp.isValid())
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return grp;
}

static HdfGroup openHdfGroup(const HdfGroup& hdfGroup, const QString& name)
{
    HdfGroup grp = hdfGroup.group(name);
    if (!grp.isValid())
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return grp;
}

static HdfDataset openHdfDataset(const HdfGroup& hdfGroup, const QString& name)
{
    HdfDataset dsFileType = hdfGroup.dataset(name);
    if (!dsFileType.isValid())
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return dsFileType;
}


static QString openHdfAttribute(const HdfFile& hdfFile, const QString& name)
{
    HdfAttribute attr = hdfFile.attribute(name);
    if (!attr.isValid())
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return attr.readString();
}



static ElementOutput* readBedElevation(Mesh* mesh, const QString fileName, const HdfGroup& gArea, int nElems)
{
    DataSet* dsd = new DataSet(fileName);
    dsd->setName("Bed Elevation");
    dsd->setType(DataSet::Bed);

    ElementOutput* tos = new ElementOutput;
    tos->init(nElems, false);
    tos->time = 0;

    HdfDataset dsBed = openHdfDataset(gArea, "Cells Minimum Elevation");
    QVector<float> elev_vals = dsBed.readArray();
    for (int i = 0; i < nElems; ++i) {
      float val = elev_vals[i];
      if (val != val) { //NaN
        tos->values[i] = -9999;
      } else {
        tos->values[i] = val;
      }
    }

    dsd->addOutput(tos);
    dsd->updateZRange();
    mesh->addDataSet(dsd);

    return tos;
}

static void readUnsteadyFaceResults(Mesh* mesh, const QString flowAreaName, const QString fileName, const HdfFile& hdfFile, int nElems)
{
    // First read face to node mapping
    HdfGroup gGeom = openHdfGroup(hdfFile, "Geometry");
    HdfGroup gGeom2DFlowAreas = openHdfGroup(gGeom, "2D Flow Areas");
    HdfGroup gArea = openHdfGroup(gGeom2DFlowAreas, flowAreaName);
    HdfDataset dsFace2Cells = openHdfDataset(gArea, "Faces Cell Indexes");

    QVector<hsize_t> fdims = dsFace2Cells.dims();
    QVector<int> face2Cells = dsFace2Cells.readArrayInt(); //2x nFaces
    int nFaces = fdims[0];

    HdfGroup gResults = openHdfGroup(hdfFile, "Results");
    HdfGroup gUnsteady = openHdfGroup(gResults, "Unsteady");
    HdfGroup gOutput = openHdfGroup(gUnsteady, "Output");
    HdfGroup gOBlocks = openHdfGroup(gOutput, "Output Blocks");
    HdfGroup gBaseO = openHdfGroup(gOBlocks, "Base Output");
    HdfGroup gUnsteadTS = openHdfGroup(gBaseO, "Unsteady Time Series");
    HdfGroup g2DFlowRes = openHdfGroup(gUnsteadTS, "2D Flow Areas");
    HdfGroup gFlowAreaRes = openHdfGroup(g2DFlowRes, flowAreaName);

    //TODO we already have this somewhere else!
    HdfDataset dsTimes = openHdfDataset(gUnsteadTS, "Time");
    QVector<float> times = dsTimes.readArray();

    // Face center data datasets
    QStringList datasets;
    datasets.push_back("Face Shear Stress");
    datasets.push_back("Face Velocity"); //this is magnitude

    double eps = std::numeric_limits<double>::min();

    foreach(QString dsName, datasets) {
        DataSet* dsd = new DataSet(fileName);
        dsd->setName(dsName);
        dsd->setType(DataSet::Scalar);
        dsd->setIsTimeVarying(times.size()>1);

        HdfDataset dsVals = openHdfDataset(gFlowAreaRes, dsName);
        QVector<float> vals = dsVals.readArray();

        for (int tidx=0; tidx<times.size(); ++tidx)
        {
            ElementOutput* tos = new ElementOutput;
            tos->init(nElems, false);
            tos->time = times[tidx];
            std::fill(tos->values.begin(),tos->values.end(),-9999);
            for (int i = 0; i < nFaces; ++i) {
                int idx = tidx*nFaces + i;
                float val = vals[idx]; // This is value on face!

                if (val == val && fabs(val) > eps) { //not nan and not 0
                    for (int c = 0; c < 2; ++c) {
                        int cell_idx = face2Cells[2*i + c];
                        // Take just maximum
                        if (tos->values[cell_idx] < val ) {
                            tos->values[cell_idx] = val;
                        }
                    }
                }
            }

            dsd->addOutput(tos);
        }

        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }
}

static void readUnsteadyElemResults(Mesh* mesh, const QString flowAreaName, const QString fileName, const HdfFile& hdfFile, int nElems, ElementOutput* bed_elevation)
{
    HdfGroup gResults = openHdfGroup(hdfFile, "Results");
    HdfGroup gUnsteady = openHdfGroup(gResults, "Unsteady");
    HdfGroup gOutput = openHdfGroup(gUnsteady, "Output");
    HdfGroup gOBlocks = openHdfGroup(gOutput, "Output Blocks");
    HdfGroup gBaseO = openHdfGroup(gOBlocks, "Base Output");
    HdfGroup gUnsteadTS = openHdfGroup(gBaseO, "Unsteady Time Series");
    HdfGroup g2DFlowRes = openHdfGroup(gUnsteadTS, "2D Flow Areas");
    HdfGroup gFlowAreaRes = openHdfGroup(g2DFlowRes, flowAreaName);


    HdfDataset dsTimes = openHdfDataset(gUnsteadTS, "Time");
    QVector<float> times = dsTimes.readArray();

    // Cell center data datasets
    QStringList datasets;
    datasets.push_back("Water Surface");
    datasets.push_back("Depth");

    float eps = std::numeric_limits<float>::min();

    foreach(QString dsName, datasets) {
        DataSet* dsd = new DataSet(fileName);
        dsd->setName(dsName);
        dsd->setType(DataSet::Scalar);
        dsd->setIsTimeVarying(times.size()>1);

        HdfDataset dsVals = openHdfDataset(gFlowAreaRes, dsName);
        QVector<float> vals = dsVals.readArray();

        for (int tidx=0; tidx<times.size(); ++tidx)
        {
            ElementOutput* tos = new ElementOutput;
            tos->init(nElems, false);
            tos->time = times[tidx];
            for (int i = 0; i < nElems; ++i) {
              int idx = tidx*nElems + i;
              float val = vals[idx];
              if (val != val) { //NaN
                tos->values[i] = -9999;
              } else {
                if (dsName == "Depth") {
                    if (fabs(val) < eps) {
                        tos->values[i] = -9999; // 0 Depth is no-data
                    } else {
                        tos->values[i] = val;
                    }
                } else { //Water surface
                    float bed_elev = bed_elevation->values[i];
                    if (fabs(bed_elev - val) < eps) {
                        tos->values[i] = -9999; // no change from bed elevation
                    } else {
                        tos->values[i] = val;
                    }
                }
              }
            }

            dsd->addOutput(tos);
        }

        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }
}

QStringList read2DFlowAreasNames(HdfGroup gGeom2DFlowAreas) {
    HdfDataset dsNames = openHdfDataset(gGeom2DFlowAreas, "Names");
    QStringList names = dsNames.readArrayString();
    if (names.isEmpty()) {
        throw LoadStatus::Err_InvalidData;
    }
    return names;
}

static void setProjection(Mesh* mesh, HdfFile hdfFile) {
    try {
        QString proj_wkt = openHdfAttribute(hdfFile, "Projection");
        mesh->setSourceCrsFromWKT(proj_wkt);
    }
    catch (LoadStatus::Error error) { /* projection not set */}
}

Mesh* Crayfish::loadHec2D(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();
    Mesh* mesh = 0;

    try
    {
        HdfFile hdfFile = openHdfFile(fileName);

        // Verify it is correct file
        QString fileType = openHdfAttribute(hdfFile, "File Type");
        if (fileType != "HEC-RAS Results") {
            throw LoadStatus::Err_UnknownFormat;
        }

        HdfGroup gGeom = openHdfGroup(hdfFile, "Geometry");
        HdfGroup gGeom2DFlowAreas = openHdfGroup(gGeom, "2D Flow Areas");

        // The file may contain multiple FLOW areas. However we do not have
        // representative examples, so for now just take first one
        QStringList flowAreaNames = read2DFlowAreasNames(gGeom2DFlowAreas);
        QString flowAreaName = flowAreaNames[0];

        HdfGroup gArea = openHdfGroup(gGeom2DFlowAreas, flowAreaName);

        HdfDataset dsCoords = openHdfDataset(gArea, "FacePoints Coordinate");
        QVector<hsize_t> cdims = dsCoords.dims();
        QVector<double> coords = dsCoords.readArrayDouble(); //2xnNodes matrix in array
        int nNodes = cdims[0];
        Mesh::Nodes nodes(nNodes);
        Node* nodesPtr = nodes.data();
        for (int n = 0; n < nNodes; ++n, ++nodesPtr)
        {
            nodesPtr->setId(n);
            nodesPtr->x = coords[cdims[1]*n];
            nodesPtr->y = coords[cdims[1]*n+1];
        }

        HdfDataset dsElems = openHdfDataset(gArea, "Cells FacePoint Indexes");
        QVector<hsize_t> edims = dsElems.dims();
        int nElems = edims[0];
        QVector<int> elem_nodes = dsElems.readArrayInt(); //8xnElements matrix in array
        Mesh::Elements elements(nElems); // ! we need to ignore other than triangles or rectagles!
        Element* elemPtr = elements.data();
        for (int e = 0; e < nElems; ++e, ++elemPtr)
        {

            elemPtr->setId(e);
            uint idx[8]; // there is up to 8 vertexes
            int nValidVertexes = 8;
            for (int fi=0; fi<8; ++fi)
            {
                int elem_node_idx = elem_nodes[edims[1]*e + fi];

                if (elem_node_idx == -1) {
                    nValidVertexes = fi;
                    break;
                } else {
                   idx[fi] = elem_node_idx;
                }
            }

            if (nValidVertexes == 2) { // Line
                elemPtr->setEType(Element::E2L);
                elemPtr->setP(idx);
            } else if (nValidVertexes == 3) { // TRIANGLE
                elemPtr->setEType(Element::E3T);
                elemPtr->setP(idx);
            }
            else if (nValidVertexes == 4) { // RECTANGLE
                elemPtr->setEType(Element::E4Q);
                elemPtr->setP(idx);

                // It seems that some polygons with 4 vertexes
                // are triangles. In this case the E4Q elements
                // are not properly working
                if (! E4Q_isValid(*elemPtr, nodes.data())) {
                    elemPtr->setEType(Element::ENP, nValidVertexes);
                    elemPtr->setP(idx);
                }
             }
            else {
                // here falls also all general polygons
                elemPtr->setEType(Element::ENP, nValidVertexes);
                elemPtr->setP(idx);
            }
        }

        mesh = new Mesh(nodes, elements);
        // Get projection
        setProjection(mesh, hdfFile);

        //Elevation
        ElementOutput* bed_elevation = readBedElevation(mesh, fileName, gArea, nElems);

        // Element centered Values
        readUnsteadyElemResults(mesh, flowAreaName, fileName, hdfFile, nElems, bed_elevation);

        // Face centered Values
        readUnsteadyFaceResults(mesh, flowAreaName, fileName, hdfFile, nElems);
    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}

