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

#include <QVector>
#include <QString>

#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "math.h"

#include <netcdf.h>

// threshold for determining whether an element is active (wet)
// the format does not explicitly store that information so we
// determine that when loading data
#define DEPTH_THRESHOLD   0.0001   // in meters

static int openFile(const QString& fileName) {
    int ncid;
    int res = nc_open(fileName.toUtf8().constData(), NC_NOWRITE, &ncid);
    if (res != NC_NOERR)
    {
      qDebug("error: %s", nc_strerror(res));
      throw LoadStatus::Err_UnknownFormat;
    }
    return ncid;
}

static size_t get_dimension(const QString& name, int ncid) {
    int dimId;
    size_t res;
    if (nc_inq_dimid(ncid, name.toStdString().c_str(), &dimId) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    if (nc_inq_dimlen(ncid, dimId, &res) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return res;
}

static QVector<int> readIntArr(const QString& name, size_t dim, int ncid)
{
        int arr_id;
        if (nc_inq_varid(ncid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
        {
          throw LoadStatus::Err_UnknownFormat;
        }
        QVector<int> arr_val(dim);
        if (nc_get_var_int (ncid, arr_id, arr_val.data()) != NC_NOERR)
        {
          throw LoadStatus::Err_UnknownFormat;
        }
        return arr_val;
}

static QVector<double> readDoubleArr(const QString& name, size_t dim, int ncid) {
    int arr_id;
    if (nc_inq_varid(ncid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    QVector<double> arr_val(dim);
    if (nc_get_var_double (ncid, arr_id, arr_val.data()) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }
    return arr_val;
}


static int getAttrInt(const QString& name, const QString& attr_name, int ncid) {
    int arr_id;
    if (nc_inq_varid(ncid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }

    int val;
    if (nc_get_att_int(ncid, arr_id, attr_name.toStdString().c_str(), &val))
    {
        throw LoadStatus::Err_UnknownFormat;
    }
    return val;
}

static double getAttrDouble(const QString& name, const QString& attr_name, int ncid) {
    int arr_id;
    if (nc_inq_varid(ncid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
    {
      throw LoadStatus::Err_UnknownFormat;
    }

    double val;
    if (nc_get_att_double(ncid, arr_id, attr_name.toStdString().c_str(), &val))
    {
        throw LoadStatus::Err_UnknownFormat;
    }
    return val;
}

static void setProjection(Mesh* m, int ncid) {
    // TODO
    return;
}

static Mesh::Nodes createNodes(size_t nPoints, int ncid) {
    QVector<double> nodes_x = readDoubleArr("mesh2d_node_x", nPoints, ncid);
    QVector<double> nodes_y = readDoubleArr("mesh2d_node_y", nPoints, ncid);

    Mesh::Nodes nodes(nPoints);
    Node* nodesPtr = nodes.data();
    for (size_t i = 0; i < nPoints; ++i, ++nodesPtr)
    {
              nodesPtr->setId(i);
              nodesPtr->x = nodes_x[i];
              nodesPtr->y = nodes_y[i];
    }
    return nodes;
}

static Mesh::Elements createElements(size_t nVolumes, int ncid) {
    int nMaxVertices = get_dimension("max_nmesh2d_face_nodes", ncid);
    double fill_val = getAttrInt("mesh2d_face_nodes", "_FillValue", ncid);
    QVector<int> face_nodes_conn = readIntArr("mesh2d_face_nodes", nVolumes * nMaxVertices, ncid);

    Mesh::Elements elements(nVolumes);
    Element* elementsPtr = elements.data();

    for (size_t i = 0; i < nVolumes; ++i, ++elementsPtr)
    {
        elementsPtr->setId(i);
        Element::Type et = Element::ENP;
        int nVertices = nMaxVertices;

        for (size_t j = 0; j < nMaxVertices; ++j) {
            size_t idx = nMaxVertices*i + j;
            int val = face_nodes_conn[idx];

            if (fill_val == val) {
                // found fill val
                nVertices = j;
                Q_ASSERT(nVertices > 1);
                if (nVertices == 2) {
                    et = Element::E2L;
                } else if (nVertices == 3) {
                    et = Element::E3T;
                } else if (nVertices == 4) {
                    et = Element::E4Q;
                }
                break;
            }
        }

        elementsPtr->setEType(et, nVertices);
        elementsPtr->setP(&(face_nodes_conn.data()[nMaxVertices*i]));
    }
    return elements;
}

static Mesh* createMesh(size_t nPoints, size_t nVolumes, int ncid) {
    Mesh::Nodes nodes = createNodes(nPoints, ncid);
    Mesh::Elements elements = createElements(nVolumes, ncid);
    Mesh* m = new Mesh(nodes, elements);
    return m;
}

Mesh* Crayfish::loadUGRID(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();
    int ncid = 0;
    Mesh* mesh = 0;
    try
    {
        ncid = openFile(fileName);

        // Parse dimensions
        int nPoints = get_dimension("nmesh2d_node", ncid);
        int nVolumes = get_dimension("nmesh2d_face", ncid);
        int nTimesteps = get_dimension("time", ncid);

        // Create mMesh
        mesh = createMesh(nPoints, nVolumes, ncid);
        setProjection(mesh, ncid);

        // Create datasets
        // addDatasets();
    }
    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    if (ncid != 0) nc_close(ncid);
    return mesh;
}
