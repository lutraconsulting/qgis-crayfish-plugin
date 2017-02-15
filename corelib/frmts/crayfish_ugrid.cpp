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
#include <stdlib.h>

#include <netcdf.h>

static inline double val_or_nodata(float val, float nodata, float eps=std::numeric_limits<float>::epsilon())
{
    if (fabs(val - nodata) < eps) {
        return -9999.0;
    } else {
        return val;
    }
}

static inline double scale(float val_x, float val_y, float nodata_x, float nodata_y, float eps=std::numeric_limits<float>::epsilon())
{
    if (fabs(val_x - nodata_x) < eps) {
        return -9999.0;
    } else if (fabs(val_y - nodata_y) < eps) {
        return -9999.0;
    } else {
        Output::float2D vec;
        vec.x = val_x;
        vec.y = val_y;
        return vec.length();
    }
}


#define UGRID_THROW_ERR throw LoadStatus::Err_UnknownFormat

QMap<QString, QString> initHumanReadableNamesMap() {
    QMap<QString, QString> map;
    map.insert("sea_surface_level_above_geoid", "water level");
    return map;
}
QMap<QString, QString> STANDARD_NAMES_TO_HUMAN_READABLE_NAMES = initHumanReadableNamesMap();

struct Edge {
    size_t node_1;
    size_t node_2;
};


void get_dimension(const QString& name, int ncid, size_t* val, int* ncid_val) {
    if (nc_inq_dimid(ncid, name.toStdString().c_str(), ncid_val) != NC_NOERR) UGRID_THROW_ERR;
    if (nc_inq_dimlen(ncid, *ncid_val, val) != NC_NOERR) UGRID_THROW_ERR;
}

QString get_attr_str(const QString& name, int ncid, int varid) {
    size_t attlen = 0;

    if (nc_inq_attlen (ncid, varid, name.toStdString().c_str(), &attlen)) UGRID_THROW_ERR;

    char *string_attr;
    string_attr = (char *) malloc(attlen + 1);

    if (nc_get_att_text(ncid, varid, name.toStdString().c_str(), string_attr)) UGRID_THROW_ERR;
    string_attr[attlen] = '\0';

    QString res(string_attr);
    free(string_attr);

    return res;
}

struct Dimensions {
    void read(int ncid) {
        get_dimension("nmesh2d_node", ncid, &nNodes, &ncid_node);
        get_dimension("nmesh2d_face", ncid, &nElements, &ncid_element);
        get_dimension("nmesh2d_edge", ncid, &nEdges, &ncid_edge);
        get_dimension("time", ncid, &nTimesteps, &ncid_timestep);
    }

    int ncid_node;
    size_t nNodes;

    int ncid_element;
    size_t nElements;

    int ncid_edge;
    size_t nEdges;

    int ncid_timestep;
    size_t nTimesteps;
};


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

static QString getAttrStr(const QString& name, const QString& attr_name, int ncid) {
    int arr_id;
    if (nc_inq_varid(ncid, name.toStdString().c_str(), &arr_id)) UGRID_THROW_ERR;
    return get_attr_str(attr_name, ncid, arr_id);
}

////////////////////////////////////////////////////////////////
static void setProjection(Mesh* m, int ncid) {
    QString wkt = getAttrStr("projected_coordinate_system", "wkt", ncid);
    if (wkt.isEmpty()) {
        int epsg = getAttrInt("projected_coordinate_system", "epsg", ncid);
        m->setSourceCrsFromEPSG(epsg);
    } else {
        m->setSourceCrsFromWKT(wkt);
    }
}

static Mesh::Nodes createNodes(const Dimensions& dims, int ncid) {
    QVector<double> nodes_x = readDoubleArr("mesh2d_node_x", dims.nNodes, ncid);
    QVector<double> nodes_y = readDoubleArr("mesh2d_node_y", dims.nNodes, ncid);

    Mesh::Nodes nodes(dims.nNodes);
    Node* nodesPtr = nodes.data();
    for (size_t i = 0; i < dims.nNodes; ++i, ++nodesPtr)
    {
              nodesPtr->setId(i);
              nodesPtr->x = nodes_x[i];
              nodesPtr->y = nodes_y[i];
    }
    return nodes;
}

static Mesh::Elements createElements(const Dimensions& dims, int ncid) {
    size_t nMaxVertices;
    int nMaxVerticesId;
    get_dimension("max_nmesh2d_face_nodes", ncid, &nMaxVertices, &nMaxVerticesId);

    int fill_val = getAttrInt("mesh2d_face_nodes", "_FillValue", ncid);
    int start_index = getAttrInt("mesh2d_face_nodes", "start_index", ncid);
    QVector<int> face_nodes_conn = readIntArr("mesh2d_face_nodes", dims.nElements * nMaxVertices, ncid);

    Mesh::Elements elements(dims.nElements);
    Element* elementsPtr = elements.data();

    for (size_t i = 0; i < dims.nElements; ++i, ++elementsPtr)
    {
        elementsPtr->setId(i);
        Element::Type et = Element::ENP;
        int nVertices = nMaxVertices;
        QVector<uint> idxs(nMaxVertices);

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
            } else {
                idxs[j] = val - start_index;
            }
        }

        elementsPtr->setEType(et, nVertices);
        elementsPtr->setP(idxs.data());
    }
    return elements;
}

static Mesh* createMesh(const Dimensions& dims, int ncid) {
    Mesh::Nodes nodes = createNodes(dims, ncid);
    Mesh::Elements elements = createElements(dims, ncid);
    Mesh* m = new Mesh(nodes, elements);
    return m;
}


struct DatasetInfo{
    QString name;
    DataSet::Type dsType;
    QString outputType;
    size_t nTimesteps;
    int ncid_x;
    int ncid_y;
};
typedef QMap<QString, DatasetInfo> dataset_info_map; // name -> DatasetInfo

static dataset_info_map parseDatasetInfo(const Dimensions& dims, int ncid) {
    /*
     * list of datasets:
     *   Getting the full list of variables from the file and then grouping them in two steps:
     *   - Grouping (or filtering) based on whether they’re time-dependent (find time dimension id,
     *     and check whether each of the data variables has that dimension id in its own dimensions).
     *   - Next, filtering them on whether they’re space-dependent, possibly grouping them based on
     *     their topological location: this can be inquired by getting their “:location” attribute
     *     which has either the value “face” (often), “edge” (sometimes), or “node” (rarely).
     *
     * naming:
     *     You could use the long_name to print a human readable variable name. When that is absent,
     *     use the standard_name of the variable and use your own lookup table for a human readable
     *     variable name (e.g.: sea_surface_level_above_geoid could translate into “Water level”).
     *     Finally, if also standard_name is absent, fall back to the bare variable name (e.g. “mesh2d_s1”).
     */


    /* PHASE 1 - gather all variables to be used for node/element datasets */
    dataset_info_map dsinfo_map;
    int varid = -1;

    QStringList ignore_variables;
    ignore_variables.append("mesh2d");
    ignore_variables.append("projected_coordinate_system");
    ignore_variables.append("time");
    ignore_variables.append("timestep");
    ignore_variables.append("mesh2d_node_x");
    ignore_variables.append("mesh2d_node_x");
    ignore_variables.append("mesh2d_node_y");
    ignore_variables.append("mesh2d_face_nodes");
    ignore_variables.append("mesh2d_edge_nodes");
    ignore_variables.append("mesh2d_edge_x");
    ignore_variables.append("mesh2d_edge_y");
    ignore_variables.append("mesh2d_edge_x_bnd");
    ignore_variables.append("mesh2d_edge_y_bnd");
    ignore_variables.append("mesh2d_face_x");
    ignore_variables.append("mesh2d_face_y");
    ignore_variables.append("mesh2d_face_x_bnd");
    ignore_variables.append("mesh2d_face_y_bnd");
    ignore_variables.append("mesh2d_edge_type");

    do {
        ++varid;

        // get variable name
        char variable_name_c[NC_MAX_NAME];
        if (nc_inq_varname(ncid, varid, variable_name_c)) break; // probably we are at the end of available arrays, quit endless loop
        QString variable_name(variable_name_c);

        if (!ignore_variables.contains(variable_name)) {

            // get number of dimensions
            int ndims;
            if (nc_inq_varndims(ncid, varid, &ndims)) continue;

            // we parse either timedependent or time-indepenended (e.g. Bed/Maximums)
            if ((ndims < 1) || (ndims > 2)) continue;
            int dimids[2];
            if (nc_inq_vardimid(ncid, varid, dimids)) continue;

            int nTimesteps;
            QString output_type;
            if (ndims == 1) {
                nTimesteps = 1;
                if (dimids[0] == dims.ncid_node) {
                    output_type = "Node";
                } else if (dimids[0] == dims.ncid_element) {
                    output_type = "Element";
                } else if (dimids[0] == dims.ncid_edge) {
                    output_type = "Edge";
                } else {
                    continue;
                }
            } else {
                nTimesteps = dims.nTimesteps;
                if (dimids[1] == dims.ncid_node) {
                    output_type = "Node";
                } else if (dimids[1] == dims.ncid_element) {
                    output_type = "Element";
                } else if (dimids[1] == dims.ncid_edge) {
                    output_type = "Edge";
                } else {
                    continue;
                }
            }

            // Get name, if it is vector and if it is x or y
            QString name;
            DataSet::Type dsType = DataSet::Scalar;
            if (variable_name == "mesh2d_flowelem_bl") {
                dsType = DataSet::Bed;
            }
            bool is_y = false;

            QString long_name = get_attr_str("long_name", ncid, varid);
            if (long_name.isEmpty()) {
                QString standard_name = get_attr_str("standard_name", ncid, varid);
                if (standard_name.isEmpty()) {
                    name = variable_name;
                } else {
                    if (standard_name.contains("_x_")) {
                        dsType = DataSet::Vector;
                    } else if (standard_name.contains("_y_")) {
                        dsType = DataSet::Vector;
                        is_y = true;
                    }
                    standard_name = standard_name.replace("_x_", "").replace("_y_", "");
                    if (STANDARD_NAMES_TO_HUMAN_READABLE_NAMES.contains(standard_name)) {
                        name = STANDARD_NAMES_TO_HUMAN_READABLE_NAMES[standard_name];
                    } else {
                        name = standard_name;
                    }
                }
            } else {
                if (long_name.contains(", x-component")) {
                    dsType = DataSet::Vector;
                } else if (long_name.contains(", y-component")) {
                    dsType = DataSet::Vector;
                    is_y = true;
                }
                name = long_name.replace(", x-component", "").replace(", y-component", "");
            }


            // Add it to the map
            if (dsinfo_map.contains(name)) {
                if (is_y) {
                    dsinfo_map[name].ncid_y = varid;
                } else {
                    dsinfo_map[name].ncid_y = varid;
                }
            } else {
                DatasetInfo dsInfo;
                dsInfo.nTimesteps = nTimesteps;
                dsInfo.dsType = dsType;
                if (is_y) {
                    dsInfo.ncid_y = varid;
                } else {
                    dsInfo.ncid_x = varid;
                }
                dsInfo.outputType = output_type;
                dsInfo.name = name;
                dsinfo_map[name] = dsInfo;
            }
        }
    }
    while (true);

    if (dsinfo_map.size() == 0) {
        throw LoadStatus::Err_InvalidData;
    }

    return dsinfo_map;
}

static void addDatasets(Mesh* m, const Dimensions& dims, int ncid,
                        const QString& fileName, const QVector<double>& times,
                        const dataset_info_map& dsinfo_map,
                        const QDateTime& refTime,
                        const QVector<Edge>& edges) {

    /* PHASE 2 - add datasets */
    foreach (DatasetInfo dsi, dsinfo_map) {
        // Create a dataset
        DataSet* ds = new DataSet(fileName);
        ds->setType(dsi.dsType);
        ds->setName(dsi.name);
        ds->setIsTimeVarying(dsi.nTimesteps > 1);

        size_t arr_size;
        if (dsi.outputType == "Node") {
            arr_size = dsi.nTimesteps * dims.nNodes;
        } else if (dsi.outputType == "Element") {
            arr_size = dsi.nTimesteps * dims.nElements;
        } else { // Edges
            arr_size = dsi.nTimesteps * dims.nEdges;
        }

        // read X data
        double fill_val_x = 0.;
        if (nc_get_att_double(ncid, dsi.ncid_x, "_FillValue", &fill_val_x)) UGRID_THROW_ERR;

        QVector<double> vals_x(arr_size);
        if (nc_get_var_double (ncid, dsi.ncid_x, vals_x.data())) UGRID_THROW_ERR;

        // read Y data if vector
        double fill_val_y = 0.;
        QVector<double> vals_y;
        if (dsi.dsType == DataSet::Vector) {
           if (nc_get_att_double(ncid, dsi.ncid_y, "_FillValue", &fill_val_y)) UGRID_THROW_ERR;
           vals_y.resize(arr_size);
           if (nc_get_var_double (ncid, dsi.ncid_y, vals_y.data())) UGRID_THROW_ERR;
        }

        // Create output
        for (size_t ts=0; ts<dsi.nTimesteps; ++ts) {
            float time = times[ts];


            if (dsi.outputType == "Node") {
                NodeOutput* el = new NodeOutput();
                el->time = time;
                el->init(dims.nNodes, dims.nElements, (dsi.dsType == DataSet::Vector));

                QVector<float>& vals = el->getValues();
                QVector<Output::float2D>& vals_V = el->getValuesV();
                QVector<char>& active = el->getActive();

                for (size_t i = 0; i< dims.nNodes; ++i) {
                    size_t idx = ts*dims.nNodes + i;
                    if (dsi.dsType == DataSet::Vector) {
                        vals_V[i].x = val_or_nodata(vals_x[idx], fill_val_x);
                        vals_V[i].y = val_or_nodata(vals_y[idx], fill_val_y);
                        vals[i] = scale(vals_x[idx], vals_y[idx], fill_val_x, fill_val_y);
                    } else {
                        vals[i] = val_or_nodata(vals_x[idx], fill_val_x);
                    }
                }

                for (size_t i = 0; i< dims.nElements; ++i) {
                    // All active
                    active[i] = 1;
                }
                ds->addOutput(el);
             } else if (dsi.outputType == "Edge") {
                    NodeOutput* el = new NodeOutput();
                    el->time = time;
                    el->init(dims.nNodes, dims.nElements, (dsi.dsType == DataSet::Vector));

                    QVector<float>& vals = el->getValues();
                    QVector<Output::float2D>& vals_V = el->getValuesV();
                    QVector<char>& active = el->getActive();

                    for (size_t i=0; i<dims.nNodes; ++i) {
                        vals[i] = -9999;
                        if (dsi.dsType == DataSet::Vector) {
                            vals_V[i].x = -9999;
                            vals_V[i].y = -9999;
                        }
                    }

                    for (size_t i = 0; i< dims.nEdges; ++i) {

                        size_t idx = ts*dims.nEdges + i;
                        size_t node_1_idx = edges[i].node_1;
                        size_t node_2_idx = edges[i].node_2;

                        // take max
                        if (dsi.dsType == DataSet::Vector) {
                            double val_x = val_or_nodata(vals_x[idx], fill_val_x);
                            double val_y = val_or_nodata(vals_y[idx], fill_val_y);
                            double val_scale = scale(vals_x[idx], vals_y[idx], fill_val_x, fill_val_y);

                            if ((vals[node_1_idx] == -9999) || (vals[node_1_idx] < val_scale)) {
                                vals_V[node_1_idx].x = val_x;
                                vals_V[node_1_idx].y = val_y;
                                vals[node_1_idx] = val_scale;
                            }
                            if ((vals[node_2_idx] == -9999) || (vals[node_2_idx] < val_scale)) {
                                vals_V[node_2_idx].x = val_x;
                                vals_V[node_2_idx].y = val_y;
                                vals[node_2_idx] = val_scale;
                            }

                        } else {
                            double val_x = val_or_nodata(vals_x[idx], fill_val_x);
                            if ((vals[node_1_idx] == -9999) || (vals[node_1_idx] < val_x)) {
                                vals[node_1_idx] = val_x;
                            }
                            if ((vals[node_2_idx] == -9999) || (vals[node_2_idx] < val_x)) {
                                vals[node_2_idx] = val_x;
                            }
                        }
                    }

                    for (size_t i = 0; i< dims.nElements; ++i) {
                        // All active
                        active[i] = 1;
                    }
                    ds->addOutput(el);

            } else { //if (dsi.outputType == "Element")
                ElementOutput* el = new ElementOutput();
                el->time = time;
                el->init(dims.nElements, (dsi.dsType == DataSet::Vector));

                QVector<float>& vals = el->getValues();
                QVector<Output::float2D>& vals_V = el->getValuesV();

                for (size_t i = 0; i< dims.nElements; ++i) {
                    size_t idx = ts*dims.nElements + i;
                    if (dsi.dsType == DataSet::Vector) {
                        vals_V[i].x = val_or_nodata(vals_x[idx], fill_val_x);
                        vals_V[i].y = val_or_nodata(vals_y[idx], fill_val_y);
                        vals[i] = scale(vals_x[idx], vals_y[idx], fill_val_x, fill_val_y);
                    } else {
                        vals[i] = val_or_nodata(vals_x[idx], fill_val_x);
                    }
                }
                ds->addOutput(el);
            }
        }

        ds->updateZRange();
        ds->setRefTime(refTime);

        // Add to mesh
        m->addDataSet(ds);
    }
}

static QDateTime parseTime(int ncid, const Dimensions& dims, QVector<double>& times) {
    QDateTime dt;

    times = readDoubleArr("time", dims.nTimesteps, ncid);

    QStringList formats_supported;
    formats_supported.append("yyyy-MM-dd HH:mm:ss");
    formats_supported.append("yyyy-MM-dd HH:mm:s.z");

    // We are trying to parse strings like
    QString units = getAttrStr("time", "units", ncid);
    // "seconds since 2001-05-05 00:00:00"
    // "hours since 1900-01-01 00:00:0.0"
    QStringList units_list = units.split(" since ");
    if (units_list.size() == 2) {
        // Give me hours
        float div_by = 1;
        if (units_list[0] == "seconds") {
            div_by = 3600.0;
        } else if (units_list[0] == "minutes") {
            div_by = 60.0;
        }
        for(size_t i=0; i<dims.nTimesteps; ++i) {
            times[i] /= div_by;
        }

        //TODO -- reuse in netcdf reader
        // now time
        foreach (QString fmt, formats_supported) {
           dt =  QDateTime::fromString(units_list[1], fmt);
           if (dt.isValid())
               break;
        }
    }
    return dt;
}

static QVector<Edge> parseEdges(const Dimensions& dims, int ncid) {
    int start_index = getAttrInt("mesh2d_edge_nodes", "start_index", ncid);
    QVector<int> edge_nodes_conn = readIntArr("mesh2d_edge_nodes", dims.nEdges * 2, ncid);

    QVector<Edge> edges;

    for (size_t i=0; i<dims.nEdges; ++i) {
        Edge edge;
        edge.node_1 = edge_nodes_conn[2*i]- start_index;
        edge.node_2 = edge_nodes_conn[2*i+1] - start_index;
        edges.push_back(edge);
    }
    return edges;
}

Mesh* Crayfish::loadUGRID(const QString& fileName, LoadStatus* status)
{
    if (status) status->clear();
    int ncid = 0;
    Mesh* mesh = 0;
    Dimensions dims;
    QVector<double> times;

    try
    {
        ncid = openFile(fileName);

        // Parse dimensions
        dims.read(ncid);

        // Create mMesh
        mesh = createMesh(dims, ncid);
        setProjection(mesh, ncid);

        // Parse Edges
        QVector<Edge> edges = parseEdges(dims, ncid);

        // Parse time array
        QDateTime refTime = parseTime(ncid, dims, times);

        // Parse dataset info
        dataset_info_map dsinfo_map = parseDatasetInfo(dims, ncid);

        // Create datasets
        addDatasets(mesh, dims, ncid, fileName, times, dsinfo_map, refTime, edges);
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
