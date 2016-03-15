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

static void readUnsteadyResults(Mesh* mesh, const QString fileName, const HdfFile& hdfFile, int nElems, ElementOutput* bed_elevation)
{
    HdfGroup gResults = openHdfGroup(hdfFile, "Results");
    HdfGroup gUnsteady = openHdfGroup(gResults, "Unsteady");
    HdfGroup gOutput = openHdfGroup(gUnsteady, "Output");
    HdfGroup gOBlocks = openHdfGroup(gOutput, "Output Blocks");
    HdfGroup gBaseO = openHdfGroup(gOBlocks, "Base Output");
    HdfGroup gUnsteadTS = openHdfGroup(gBaseO, "Unsteady Time Series");
    HdfGroup g2DFlowRes = openHdfGroup(gUnsteadTS, "2D Flow Areas");
    HdfGroup gFlowAreaRes = openHdfGroup(g2DFlowRes, "BaldEagleCr"); // #TODO


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

Mesh* Crayfish::loadHec2D(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();
    Mesh* mesh = 0;

    try
    {
        HdfFile hdfFile = openHdfFile(fileName);

        HdfGroup gGeom = openHdfGroup(hdfFile, "Geometry");
        HdfGroup gGeom2DFlowAreas = openHdfGroup(gGeom, "2D Flow Areas");
        //TODO parse dataset names
        //TODO loop over areas
        QString flowArea = "BaldEagleCr";
        HdfGroup gArea = openHdfGroup(gGeom2DFlowAreas, flowArea);

        HdfDataset dsCoords = openHdfDataset(gArea, "FacePoints Coordinate");
        QVector<hsize_t> cdims = dsCoords.dims();
        QVector<double> coords = dsCoords.readArrayDouble(); //2xnNodes matrix in array
        int nNodes = cdims[0];
        Mesh::Nodes nodes(nNodes);
        Node* nodesPtr = nodes.data();
        for (uint n = 0; n < nNodes; ++n, ++nodesPtr)
        {
            nodesPtr->id = n;
            nodesPtr->x = coords[cdims[1]*n];
            nodesPtr->y = coords[cdims[1]*n+1];
        }

        HdfDataset dsElems = openHdfDataset(gArea, "Cells FacePoint Indexes");
        QVector<hsize_t> edims = dsElems.dims();
        int nElems = edims[0];
        QVector<int> elem_nodes = dsElems.readArrayInt(); //8xnElements matrix in array
        Mesh::Elements elements(nElems); // ! we need to ignore other than triangles or rectagles!
        Element* elemPtr = elements.data();
        for (uint e = 0; e < nElems; ++e, ++elemPtr)
        {

            elemPtr->id = e;
            elemPtr->p[0] = elem_nodes[edims[1]*e + 0];
            elemPtr->p[1] = elem_nodes[edims[1]*e + 1];
            elemPtr->p[2] = elem_nodes[edims[1]*e + 2];
            elemPtr->p[3] = elem_nodes[edims[1]*e + 3];

            if (elemPtr->p[2] == -1) {
                // transform lines to malformed triangles
                elemPtr->eType = Element::E3T;
                elemPtr->p[2] = elemPtr->p[0];
            } else if (elemPtr->p[3] == -1) { // TRIANGLE
                elemPtr->eType = Element::E3T;
            } else {
                // RECTANGLE
                // Note that here falls also all general polygons with >4 vertexes
                // where we do not yet have appropriate mesh element
                elemPtr->eType = Element::E4Q;

                // Few points here are ordered clockwise
                // and few anti-clockwise
                // WE need clockwise to work
                if (! E4Q_isOrientedOk(*elemPtr, nodes.data())) {
                    // Swap
                    float tmp = elemPtr->p[1];
                    elemPtr->p[1] = elemPtr->p[3];
                    elemPtr->p[3] = tmp;
                }
            }
        }

        mesh = new Mesh(nodes, elements);

        //Elevation
        ElementOutput* bed_elevation = readBedElevation(mesh, fileName, gArea, nElems);

        // Values
        readUnsteadyResults(mesh, fileName, hdfFile, nElems, bed_elevation);
    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}

