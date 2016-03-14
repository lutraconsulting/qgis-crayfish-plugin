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
        QVector<int> elem_nodes = dsElems.readArrayInt(); //8xnElements matrix in array
        Mesh::Elements elements; // ! we need to ignore other than triangles or rectagles!
        int elem_id = 0;


        for (uint e = 0; e < edims[0]; ++e)
        {
            int index0 = elem_nodes[edims[1]*e + 0];
            int index1 = elem_nodes[edims[1]*e + 1];
            int index2 = elem_nodes[edims[1]*e + 2];
            int index3 = elem_nodes[edims[1]*e + 3];
            int index4 = elem_nodes[edims[1]*e + 4];

            // look for triangles and rectangles only
            // ignore others unfortunately
            if (index2 != -1 && index4 == -1) {
                if (index3 == -1) { // TRIANGLE
                    Element elem;
                    elem.id = elem_id;
                    elem.eType = Element::E3T;
                    elem.p[0] = index0;
                    elem.p[1] = index1;
                    elem.p[2] = index2;
                    elem_id ++;
                    elements.push_back(elem);
                } else { // RECTANGLE
                    Element elem;
                    elem.id = elem_id;
                    elem.eType = Element::E4Q;
                    elem.p[0] = index0;
                    elem.p[1] = index1;
                    elem.p[2] = index2;
                    elem.p[3] = index3;
                    elem_id ++;
                    elements.push_back(elem);
                }
            }
        }
        int nElems = elem_id;

        mesh = new Mesh(nodes, elements);

        DataSet* dsd = new DataSet(fileName);
        dsd->setName("dummy");
        dsd->setIsTimeVarying(false);
        dsd->setType(DataSet::Scalar);
        NodeOutput* tos = new NodeOutput;
        tos->init(nNodes, nElems, false);
        tos->time = 0;
        memset(tos->active.data(), 1, nElems); // All cells active
        for (int i = 0; i < nNodes; ++i)
          tos->values[i] = i;
        dsd->addOutput(tos);
        dsd->updateZRange();
        mesh->addDataSet(dsd);
    }
    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
