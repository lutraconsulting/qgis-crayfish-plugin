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
#include "crayfish_netcdf.h"
#include "crayfish_utils.h"

#include "math.h"
#include <stdlib.h>

#include <netcdf.h>



#define UGRID_THROW_ERR throw LoadStatus::Err_UnknownFormat

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

QStringList initIgnoreVariables() {
    QStringList ignore_variables;
    ignore_variables.append("projected_coordinate_system");
    ignore_variables.append("time");
    ignore_variables.append("timestep");
    ignore_variables.append("mesh2d_face_nodes");
    ignore_variables.append("mesh2d_face_x");
    ignore_variables.append("mesh2d_face_y");
    ignore_variables.append("mesh2d_face_x_bnd");
    ignore_variables.append("mesh2d_face_y_bnd");

    QStringList meshes;
    meshes.append("mesh1d");
    meshes.append("mesh2d");

    foreach (QString mesh, meshes) {
        ignore_variables.append(mesh);
        ignore_variables.append(mesh + "_flowelem_ba");
        ignore_variables.append(mesh + "_node_x");
        ignore_variables.append(mesh + "_node_y");
        ignore_variables.append(mesh + "_edge_nodes");
        ignore_variables.append(mesh + "_edge_x");
        ignore_variables.append(mesh + "_edge_y");
        ignore_variables.append(mesh + "_edge_x_bnd");
        ignore_variables.append(mesh + "_edge_y_bnd");
        ignore_variables.append(mesh + "_edge_type");
    }
    return ignore_variables;
}
QStringList IGNORE_VARIABLES = initIgnoreVariables();


struct Dimensions {
    void read(const NetCDFFile& ncFile) {
        ncFile.getDimension("nmesh2d_node", &nNodes2D, &ncid_node2D);
        ncFile.getDimension("nmesh2d_face", &nElements2D, &ncid_element2D);
        ncFile.getDimension("nmesh2d_edge", &nEdges2D, &ncid_edge2D);
        ncFile.getDimension("time", &nTimesteps, &ncid_timestep);

        // these are not required
        ncFile.getDimensionOptional("nmesh1d_node", &nNodes1D, &ncid_node1D);
        ncFile.getDimensionOptional("nmesh1d_edge", &nEdges1D, &ncid_edge1D);

        nNodes = nNodes1D + nNodes2D;
        nElements = nEdges1D + nElements2D;
    }

    int ncid_node1D;
    size_t nNodes1D;

    int ncid_edge1D;
    size_t nEdges1D;

    int ncid_node2D;
    size_t nNodes2D;

    int ncid_element2D;
    size_t nElements2D;

    int ncid_edge2D;
    size_t nEdges2D;

    size_t nNodes;
    size_t nElements;

    int ncid_timestep;
    size_t nTimesteps;
};

struct DatasetInfo{
    QString name;
    DataSet::Type dsType;
    QString outputType;
    size_t nTimesteps;
    int ncid_x;
    int ncid_y;
    size_t arr_size;
};
typedef QMap<QString, DatasetInfo> dataset_info_map; // name -> DatasetInfo

////////////////////////////////////////////////////////////////
static QString getCoordinateSystemVariableName(const NetCDFFile& ncFile) {
    QString coordinate_system_variable;

    // first try to get the coordinate system variable from grid definition
    if (ncFile.hasVariable("mesh2d_node_z")) {
        coordinate_system_variable = ncFile.getAttrStr("mesh2d_node_z", "grid_mapping");
    }

    // if automatic discovery fails, try to check some hardcoded common variables that store projection
    if (coordinate_system_variable.isEmpty()) {
        if (ncFile.hasVariable("projected_coordinate_system"))
            coordinate_system_variable = "projected_coordinate_system";
        else if (ncFile.hasVariable("wgs84"))
            coordinate_system_variable = "wgs84";
    }

    // return, may be empty
    return coordinate_system_variable;
}

static void setProjection(Mesh* m, const NetCDFFile& ncFile) {
    QString coordinate_system_variable = getCoordinateSystemVariableName(ncFile);

    if (!coordinate_system_variable.isEmpty()) {
        QString wkt = ncFile.getAttrStr(coordinate_system_variable, "wkt");
        if (wkt.isEmpty()) {
            int epsg = ncFile.getAttrInt(coordinate_system_variable, "epsg");
            if (epsg != 0) {
                m->setSourceCrsFromEPSG(epsg);
            }
        } else {
            m->setSourceCrsFromWKT(wkt);
        }
    }
}

static Mesh::Nodes createNodes(const Dimensions& dims, const NetCDFFile& ncFile) {
    Mesh::Nodes nodes(dims.nNodes);
    Node* nodesPtr = nodes.data();

    // 1D
    if (dims.nNodes1D > 0) {
        QVector<double> nodes1D_x = ncFile.readDoubleArr("mesh1d_node_x", dims.nNodes1D);
        QVector<double> nodes1D_y = ncFile.readDoubleArr("mesh1d_node_y", dims.nNodes1D);
        for (size_t i = 0; i < dims.nNodes1D; ++i, ++nodesPtr)
        {
            nodesPtr->setId(i);
            nodesPtr->x = nodes1D_x[i];
            nodesPtr->y = nodes1D_y[i];
        }
    }

    // 2D
    QVector<double> nodes2D_x = ncFile.readDoubleArr("mesh2d_node_x", dims.nNodes2D);
    QVector<double> nodes2D_y = ncFile.readDoubleArr("mesh2d_node_y", dims.nNodes2D);
    for (size_t i = 0; i < dims.nNodes2D; ++i, ++nodesPtr)
    {
        nodesPtr->setId(dims.nNodes1D+i);
        nodesPtr->x = nodes2D_x[i];
        nodesPtr->y = nodes2D_y[i];
    }
    return nodes;
}

static Mesh::Elements createElements(const Dimensions& dims, const NetCDFFile& ncFile) {
    Mesh::Elements elements(dims.nElements);
    Element* elementsPtr = elements.data();

    // 1D
    if (dims.nEdges1D > 0) {
        int start_index = ncFile.getAttrInt("mesh1d_edge_nodes", "start_index");
        QVector<int> edges_nodes_conn = ncFile.readIntArr("mesh1d_edge_nodes", dims.nEdges1D * 2);

        for (size_t i = 0; i < dims.nEdges1D; ++i, ++elementsPtr)
        {
            elementsPtr->setId(i);
            elementsPtr->setEType(Element::E2L);
            elementsPtr->setP(0, edges_nodes_conn[2*i] - start_index);
            elementsPtr->setP(1, edges_nodes_conn[2*i + 1] - start_index);
        }
    }

    // 2D
    size_t nMaxVertices;
    int nMaxVerticesId;
    ncFile.getDimension("max_nmesh2d_face_nodes", &nMaxVertices, &nMaxVerticesId);

    int fill_val = ncFile.getAttrInt("mesh2d_face_nodes", "_FillValue");
    int start_index = ncFile.getAttrInt("mesh2d_face_nodes", "start_index") - dims.nNodes1D;
    QVector<int> face_nodes_conn = ncFile.readIntArr("mesh2d_face_nodes", dims.nElements2D * nMaxVertices);

    for (size_t i = 0; i < dims.nElements2D; ++i, ++elementsPtr)
    {
        elementsPtr->setId(dims.nEdges1D + i);
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

static Mesh* createMesh(const Dimensions& dims, const NetCDFFile& ncFile) {
    Mesh::Nodes nodes = createNodes(dims, ncFile);
    Mesh::Elements elements = createElements(dims, ncFile);
    Mesh* m = new Mesh(nodes, elements);
    return m;
}

static bool output_array_type(const Dimensions& dims, int ncid_dimid, size_t& n_items, QString& output_type) {
    bool ret = true;

    if (ncid_dimid == dims.ncid_node1D) {
        output_type = "Node1D";
        n_items = dims.nNodes1D;
    } else if (ncid_dimid == dims.ncid_edge1D) {
        output_type = "Edge1D";
        n_items = dims.nEdges1D;
    } else if (ncid_dimid == dims.ncid_node2D) {
        output_type = "Node2D";
        n_items = dims.nNodes2D;
    } else if (ncid_dimid == dims.ncid_element2D) {
        output_type = "Element2D";
        n_items = dims.nElements2D;
    } else if (ncid_dimid == dims.ncid_edge2D) {
        output_type = "Edge2D";
        n_items = dims.nEdges2D;
    } else {
        ret = false;
    }

    return ret;
}

static dataset_info_map parseDatasetInfo(const Dimensions& dims, const NetCDFFile& ncFile) {
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

    do {
        ++varid;

        // get variable name
        char variable_name_c[NC_MAX_NAME];
        if (nc_inq_varname(ncFile.handle(), varid, variable_name_c)) break; // probably we are at the end of available arrays, quit endless loop
        QString variable_name(variable_name_c);

        if (!IGNORE_VARIABLES.contains(variable_name)) {
            // get number of dimensions
            int ndims;
            if (nc_inq_varndims(ncFile.handle(), varid, &ndims)) continue;

            // we parse either timedependent or time-indepenended (e.g. Bed/Maximums)
            if ((ndims < 1) || (ndims > 2)) continue;
            int dimids[2];
            if (nc_inq_vardimid(ncFile.handle(), varid, dimids)) continue;

            int nTimesteps;
            size_t arr_size;
            QString output_type;
            if (ndims == 1) {
                nTimesteps = 1;
                if (!output_array_type(dims, dimids[0], arr_size, output_type)) continue;
            } else {
                nTimesteps = dims.nTimesteps;
                if (!output_array_type(dims, dimids[1], arr_size, output_type)) continue;
            }
            arr_size *= nTimesteps;

            // Get name, if it is vector and if it is x or y
            QString name;
            DataSet::Type dsType = DataSet::Scalar;
            if (variable_name == "mesh2d_flowelem_bl") {
                dsType = DataSet::Bed;
            }
            bool is_y = false;

            QString long_name = ncFile.getAttrStr("long_name", varid);
            if (long_name.isEmpty()) {
                QString standard_name = ncFile.getAttrStr("standard_name", varid);
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

            name = name + " (" + output_type + ")";

            // Add it to the map
            if (dsinfo_map.contains(name)) {
                if (is_y) {
                    dsinfo_map[name].ncid_y = varid;
                } else {
                    dsinfo_map[name].ncid_x = varid;
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
                dsInfo.arr_size = arr_size;
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

static void populate_vals(bool is_vector, QVector<float>& vals, QVector<Output::float2D>& vals_V, size_t i,
                          const QVector<double>& vals_x, const QVector<double>& vals_y, size_t idx, double fill_val_x, double fill_val_y) {
    if (is_vector) {
        vals_V[i].x = val_or_nodata(vals_x[idx], fill_val_x);
        vals_V[i].y = val_or_nodata(vals_y[idx], fill_val_y);
        vals[i] = scale(vals_x[idx], vals_y[idx], fill_val_x, fill_val_y);
    } else {
        vals[i] = val_or_nodata(vals_x[idx], fill_val_x);
    }
}

static void populate_nodata(bool is_vector, QVector<float>& vals, QVector<Output::float2D>& vals_V, size_t from_i, size_t to_i) {
    for (size_t i=from_i; i<to_i; ++i) {
        if (is_vector) {
            vals_V[i].x = -9999.0;
            vals_V[i].y = -9999.0;
            vals[i] = -9999.0;
        } else {
            vals[i] = -9999.0;
        }
    }
}

static Output* createNode1DOutput(size_t ts, const Dimensions& dims, const DatasetInfo& dsi, const QVector<double>& vals_x, const QVector<double>& vals_y, double fill_val_x, double fill_val_y) {
    NodeOutput* el = new NodeOutput();
    el->init(dims.nNodes, dims.nElements, (dsi.dsType == DataSet::Vector));

    QVector<float>& vals = el->getValues();
    QVector<Output::float2D>& vals_V = el->getValuesV();
    QVector<char>& active = el->getActive();

    for (size_t i = 0; i< dims.nNodes1D; ++i) {
        size_t idx = ts*dims.nNodes1D + i;
        populate_vals(dsi.dsType == DataSet::Vector, vals, vals_V, i,
                      vals_x, vals_y, idx, fill_val_x, fill_val_y);
    }
    for (size_t i = 0; i< dims.nElements; ++i) {
        active[i] = (i<dims.nEdges1D);
    }

    populate_nodata(dsi.dsType == DataSet::Vector, vals, vals_V, dims.nNodes1D, dims.nNodes);

    return el;
}

static Output* createEdge1DOutput(size_t ts, const Dimensions& dims, const DatasetInfo& dsi, const QVector<double>& vals_x, const QVector<double>& vals_y, double fill_val_x, double fill_val_y) {
    ElementOutput* el = new ElementOutput();
    el->init(dims.nElements, (dsi.dsType == DataSet::Vector));

    QVector<float>& vals = el->getValues();
    QVector<Output::float2D>& vals_V = el->getValuesV();

    for (size_t i = 0; i< dims.nEdges1D; ++i) {
        size_t idx = ts*dims.nEdges1D + i;
        populate_vals(dsi.dsType == DataSet::Vector, vals, vals_V, i,
                      vals_x, vals_y, idx, fill_val_x, fill_val_y);
    }

    populate_nodata(dsi.dsType == DataSet::Vector, vals, vals_V, dims.nEdges1D, dims.nElements);

    return el;
}

static Output* createNode2DOutput(size_t ts, const Dimensions& dims, const DatasetInfo& dsi, const QVector<double>& vals_x, const QVector<double>& vals_y, double fill_val_x, double fill_val_y) {
    NodeOutput* el = new NodeOutput();
    el->init(dims.nNodes, dims.nElements, (dsi.dsType == DataSet::Vector));

    QVector<float>& vals = el->getValues();
    QVector<Output::float2D>& vals_V = el->getValuesV();
    QVector<char>& active = el->getActive();

    for (size_t i = 0; i< dims.nNodes2D; ++i) {
        size_t idx = ts*dims.nNodes2D + i;
        populate_vals(dsi.dsType == DataSet::Vector, vals, vals_V, dims.nNodes1D + i,
                      vals_x, vals_y, idx, fill_val_x, fill_val_y);
    }

    for (size_t i = 0; i< dims.nElements2D; ++i) {
        active[i] = (i>=dims.nEdges1D);
    }

    populate_nodata(dsi.dsType == DataSet::Vector, vals, vals_V, 0, dims.nNodes1D);
    return el;
}

static Output* createEdge2DOutput(const QVector<Edge>& edges, size_t ts, const Dimensions& dims, const DatasetInfo& dsi, const QVector<double>& vals_x, const QVector<double>& vals_y, double fill_val_x, double fill_val_y) {
    NodeOutput* el = new NodeOutput();
    el->init(dims.nNodes, dims.nElements, (dsi.dsType == DataSet::Vector));

    QVector<float>& vals = el->getValues();
    QVector<Output::float2D>& vals_V = el->getValuesV();
    QVector<char>& active = el->getActive();

    populate_nodata(dsi.dsType == DataSet::Vector, vals, vals_V, 0, dims.nNodes);

    for (size_t i = 0; i< dims.nEdges2D; ++i) {

        size_t idx = ts*dims.nEdges2D + i;
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
        active[i] = (i>=dims.nEdges1D);
    }

    return el;
}

static Output* createElement2DOutput(size_t ts, const Dimensions& dims, const DatasetInfo& dsi, const QVector<double>& vals_x, const QVector<double>& vals_y, double fill_val_x, double fill_val_y) {
    ElementOutput* el = new ElementOutput();
    el->init(dims.nElements, (dsi.dsType == DataSet::Vector));

    QVector<float>& vals = el->getValues();
    QVector<Output::float2D>& vals_V = el->getValuesV();

    for (size_t i = 0; i< dims.nElements2D; ++i) {
        size_t idx = ts*dims.nElements2D + i;
        populate_vals(dsi.dsType == DataSet::Vector, vals, vals_V, dims.nEdges1D + i,
                      vals_x, vals_y, idx, fill_val_x, fill_val_y);
    }

    populate_nodata(dsi.dsType == DataSet::Vector, vals, vals_V, 0, dims.nEdges1D);
    return el;
}

static void addDatasets(Mesh* m, const Dimensions& dims, const NetCDFFile& ncFile,
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

        // read X data
        double fill_val_x = -9999.;
        nc_get_att_double(ncFile.handle(), dsi.ncid_x, "_FillValue", &fill_val_x); // SKIP error, this is optional in metadata

        QVector<double> vals_x(dsi.arr_size);
        if (nc_get_var_double (ncFile.handle(), dsi.ncid_x, vals_x.data())) UGRID_THROW_ERR;

        // read Y data if vector
        double fill_val_y = -9999.;
        QVector<double> vals_y;
        if (dsi.dsType == DataSet::Vector) {
            nc_get_att_double(ncFile.handle(), dsi.ncid_y, "_FillValue", &fill_val_y); // SKIP error, this is optional in metadata
            vals_y.resize(dsi.arr_size);
            if (nc_get_var_double (ncFile.handle(), dsi.ncid_y, vals_y.data())) UGRID_THROW_ERR;
        }

        // Create output
        for (size_t ts=0; ts<dsi.nTimesteps; ++ts) {
            float time = times[ts];
            Output* el = 0;

            if (dsi.outputType == "Node1D") {
                el = createNode1DOutput(ts, dims, dsi, vals_x, vals_y, fill_val_x, fill_val_y);
            } else if (dsi.outputType == "Edge1D") {
                el = createEdge1DOutput(ts, dims, dsi, vals_x, vals_y, fill_val_x, fill_val_y);
            } else if (dsi.outputType == "Node2D") {
                el = createNode2DOutput(ts, dims, dsi, vals_x, vals_y, fill_val_x, fill_val_y);
            } else if (dsi.outputType == "Edge2D") {
                el = createEdge2DOutput(edges, ts, dims, dsi, vals_x, vals_y, fill_val_x, fill_val_y);
            } else if (dsi.outputType == "Element2D") {
                el = createElement2DOutput(ts, dims, dsi, vals_x, vals_y, fill_val_x, fill_val_y);
            } else {
                Q_ASSERT(false); //should never happen
            }

            Q_ASSERT(el);
            el->time = time;
            ds->addOutput(el);
        }

        ds->updateZRange();
        ds->setRefTime(refTime);

        // Add to mesh
        m->addDataSet(ds);
    }
}

static QDateTime parseTime(const NetCDFFile& ncFile, const Dimensions& dims, QVector<double>& times) {
    QDateTime dt;
    float div_by;
    times = ncFile.readDoubleArr("time", dims.nTimesteps);
    QString units = ncFile.getAttrStr("time", "units");
    dt = parseTimeUnits(units, &div_by);
    for(size_t i=0; i<dims.nTimesteps; ++i) {
        times[i] /= div_by;
    }
    return dt;
}

static QVector<Edge> parseEdges(const Dimensions& dims, const NetCDFFile& ncFile) {
    int start_index = ncFile.getAttrInt("mesh2d_edge_nodes", "start_index") - dims.nNodes1D;
    QVector<int> edge_nodes_conn = ncFile.readIntArr("mesh2d_edge_nodes", dims.nEdges2D * 2);

    QVector<Edge> edges;

    for (size_t i=0; i<dims.nEdges2D; ++i) {
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
    NetCDFFile ncFile;
    Mesh* mesh = 0;
    Dimensions dims;
    QVector<double> times;

    try
    {
        ncFile.openFile(fileName);

        // Parse dimensions
        dims.read(ncFile);

        // Create mMesh
        mesh = createMesh(dims, ncFile);
        setProjection(mesh, ncFile);

        // Parse Edges
        QVector<Edge> edges;
        edges = parseEdges(dims, ncFile);

        // Parse time array
        QDateTime refTime = parseTime(ncFile, dims, times);

        // Parse dataset info
        dataset_info_map dsinfo_map = parseDatasetInfo(dims, ncFile);

        // Create datasets
        addDatasets(mesh, dims, ncFile, fileName, times, dsinfo_map, refTime, edges);
    }
    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
