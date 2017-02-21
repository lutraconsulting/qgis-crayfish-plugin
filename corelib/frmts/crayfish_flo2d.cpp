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

#include <QFile>
#include <QTextStream>
#include <QFileInfo>
#include <QStringList>
#include <QPair>
#include <QSet>
#include <QDir>

#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_mesh_2dm.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#include <iostream>

struct CellCenter
{
    int id;
    float x;
    float y;
    QVector<int> conn; // north, east, south, west cell center index
};

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}

static float getFloat(const QString& val) {
    float valF = val.toFloat();
    if (is_nodata(valF, 0.0f)) {
        return -9999.0;
    } else {
        return valF;
    }
}

static void addStaticDataset(QVector<float>& vals, const QString& name, const DataSet::Type type, const QString& datFileName, Mesh* mesh) {
    int nelem = mesh->elements().size();

    ElementOutput* o = new ElementOutput;

    o->init(nelem, false);
    o->time = 0.0;
    o->getValues() = vals;

    DataSet* ds = new DataSet(datFileName);
    ds->setType(type);
    ds->setName(name, false);
    ds->setIsTimeVarying(false);
    ds->addOutput(o);  // takes ownership of the Output
    ds->updateZRange();
    mesh->addDataSet(ds);
}


static void parseCADPTSFile(const QString& datFileName, QVector<CellCenter>& cells) {
    QFileInfo fi(datFileName);
    QString cadptsFileName(fi.dir().filePath("CADPTS.DAT"));
    QFile cadptsFile(cadptsFileName);
    if (!cadptsFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream cadptsStream(&cadptsFile);

    // CADPTS.DAT - COORDINATES OF CELL CENTERS (ELEM NUM, X, Y)
    while (!cadptsStream.atEnd())
    {
        QString line =  cadptsStream.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() != 3) {
            throw LoadStatus::Err_UnknownFormat;
        }
        CellCenter cc;
        cc.id = lineParts[1].toInt() -1; //numbered from 1
        cc.x = lineParts[1].toFloat();
        cc.y = lineParts[2].toFloat();
        cc.conn.resize(4);
        cells.append(cc);
    }
}

static QVector<float> parseFPLAINFile(const QString& datFileName, QVector<CellCenter>& cells) {
    // FPLAIN.DAT - CONNECTIVITY (ELEM NUM, ELEM N, ELEM E, ELEM S, ELEM W, MANNING-N, BED ELEVATION)
    QFileInfo fi(datFileName);
    QString fplainFileName(fi.dir().filePath("FPLAIN.DAT"));
    QFile fplainFile(fplainFileName);
    if (!fplainFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream fplainStream(&fplainFile);

    QVector<float> elevations;

    while (!fplainStream.atEnd())
    {
        QString line = fplainStream.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() != 7) {
            throw LoadStatus::Err_UnknownFormat;
        }
        int cc_i = lineParts[0].toInt() -1; //numbered from 1
        for (int j=0; j<4; ++j) {
            cells[cc_i].conn[j] = lineParts[j+1].toInt() -1; //numbered from 1, 0 boundary node
        }
        elevations.push_back(lineParts[6].toFloat());
    }

    return elevations;
}

static void parseTIMDEPFile(const QString& datFileName, Mesh* mesh, const QVector<float>& elevations) {\
    // TIMDEP.OUT
    // this file is optional, so if not present, reading is skipped
    // time (separate line)
    // For every node:
    // FLO2D: ELEM NUMber (indexed from 1), depth, velocity, velocity x, velocity y
    // FLO2DPro: ELEM NUMber (indexed from 1), depth, velocity, velocity x, velocity y, water surface elevation
    QFileInfo fi(datFileName);
    QFile inFile(fi.dir().filePath("TIMDEP.OUT"));
    if (!inFile.open(QIODevice::ReadOnly | QIODevice::Text)) return;
    QTextStream in(&inFile);

    int nnodes = mesh->nodes().size();
    int nelems = mesh->elements().size();
    int ntimes = 0;

    float time = 0.0;
    int elem_inx = 0;

    DataSet* depthDs = new DataSet(datFileName);
    depthDs->setType(DataSet::Scalar);
    depthDs->setName("Depth");

    DataSet* waterLevelDs = new DataSet(datFileName);
    waterLevelDs->setType(DataSet::Scalar);
    waterLevelDs->setName("Water Level");

    DataSet* flowDs = new DataSet(datFileName);
    flowDs->setType(DataSet::Vector);
    flowDs->setName("Velocity");

    ElementOutput* flowOutput = 0;
    ElementOutput* depthOutput = 0;
    ElementOutput* waterLevelOutput = 0;


    while (!in.atEnd())
    {
        QString line = in.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() == 1) {
            time = line.toFloat();
            ntimes++;

            if (depthOutput) depthDs->addOutput(depthOutput);
            if (flowOutput) flowDs->addOutput(flowOutput);
            if (waterLevelOutput) waterLevelDs->addOutput(waterLevelOutput);

            depthOutput = new ElementOutput;
            flowOutput = new ElementOutput;
            waterLevelOutput = new ElementOutput;

            depthOutput->init(nelems, false); //scalar
            flowOutput->init(nelems, true); //vector
            waterLevelOutput->init(nelems, false); //scalar

            depthOutput->time = time;
            flowOutput->time = time;
            waterLevelOutput->time = time;

            elem_inx = 0;

        } else if ((lineParts.size() == 5) || (lineParts.size() == 6)) {
            // new node for time
            if (!depthOutput || !flowOutput || !waterLevelOutput) throw LoadStatus::Err_UnknownFormat;
            if (elem_inx == nnodes) throw LoadStatus::Err_IncompatibleMesh;

            flowOutput->getValues()[elem_inx] = getFloat(lineParts[2]);
            flowOutput->getValuesV()[elem_inx].x = getFloat(lineParts[3]);
            flowOutput->getValuesV()[elem_inx].y = getFloat(lineParts[4]);

            float depth = getFloat(lineParts[1]);
            depthOutput->getValues()[elem_inx] = depth;

            if (!is_nodata(depth)) depth += elevations[elem_inx];
            waterLevelOutput->getValues()[elem_inx] = depth;

            elem_inx ++;

        } else {
            throw LoadStatus::Err_UnknownFormat;
        }
    }

    if (depthOutput) depthDs->addOutput(depthOutput);
    if (flowOutput) flowDs->addOutput(flowOutput);
    if (waterLevelOutput) waterLevelDs->addOutput(waterLevelOutput);

    depthDs->setIsTimeVarying(ntimes>1);
    flowDs->setIsTimeVarying(ntimes>1);
    waterLevelDs->setIsTimeVarying(ntimes>1);

    depthDs->updateZRange();
    flowDs->updateZRange();
    waterLevelDs->updateZRange();

    mesh->addDataSet(depthDs);
    mesh->addDataSet(flowDs);
    mesh->addDataSet(waterLevelDs);
}


static void parseDEPTHFile(const QString&datFileName, Mesh* mesh, const QVector<float>& elevations) {
    // this file is optional, so if not present, reading is skipped
    QFileInfo fi(datFileName);
    QString nodesFileName(fi.dir().filePath("DEPTH.OUT"));
    QFile nodesFile(nodesFileName);
    if (!nodesFile.open(QIODevice::ReadOnly | QIODevice::Text)) return;
    QTextStream nodesStream(&nodesFile);

    int nnodes = mesh->nodes().size();
    QVector<float> maxDepth(nnodes);
    QVector<float> maxWaterLevel(nnodes);

    int node_inx = 0;

    // DEPTH.OUT - COORDINATES (ELEM NUM, X, Y, MAX DEPTH)
    while (!nodesStream.atEnd())
    {
        if (node_inx == nnodes) throw LoadStatus::Err_IncompatibleMesh;

        QString line = nodesStream.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() != 4) {
            throw LoadStatus::Err_UnknownFormat;
        }

        float val = getFloat(lineParts[3]);
        maxDepth[node_inx] = val;

        //water level
        if (!is_nodata(val)) val += elevations[node_inx];
        maxWaterLevel[node_inx] = val;


        node_inx++;
    }

    addStaticDataset(maxDepth, "Depth/Maximums", DataSet::Scalar, datFileName, mesh);
    addStaticDataset(maxWaterLevel, "Water Level/Maximums", DataSet::Scalar, datFileName, mesh);
}


static void parseVELFPVELOCFile(const QString&datFileName, Mesh* mesh) {
    // these files are optional, so if not present, reading is skipped
    int nnodes = mesh->nodes().size();
    QFileInfo fi(datFileName);
    QVector<float> maxVel(nnodes);

    {
        QString nodesFileName(fi.dir().filePath("VELFP.OUT"));
        QFile nodesFile(nodesFileName);
        if (!nodesFile.open(QIODevice::ReadOnly | QIODevice::Text)) return;
        QTextStream nodesStream(&nodesFile);
        int node_inx = 0;

        // VELFP.OUT - COORDINATES (ELEM NUM, X, Y, MAX VEL) - Maximum floodplain flow velocity;
        while (!nodesStream.atEnd())
        {
            if (node_inx == nnodes) throw LoadStatus::Err_IncompatibleMesh;

            QString line = nodesStream.readLine();
            QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
            if (lineParts.size() != 4) {
                throw LoadStatus::Err_UnknownFormat;
            }

            float val = getFloat(lineParts[3]);
            maxVel[node_inx] = val;

            node_inx++;
        }
    }

    {
        QString nodesFileName(fi.dir().filePath("VELOC.OUT"));
        QFile nodesFile(nodesFileName);
        if (!nodesFile.open(QIODevice::ReadOnly | QIODevice::Text)) return;
        QTextStream nodesStream(&nodesFile);
        int node_inx = 0;

        // VELOC.OUT - COORDINATES (ELEM NUM, X, Y, MAX VEL)  - Maximum channel flow velocity
        while (!nodesStream.atEnd())
        {
            if (node_inx == nnodes) throw LoadStatus::Err_IncompatibleMesh;

            QString line = nodesStream.readLine();
            QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
            if (lineParts.size() != 4) {
                throw LoadStatus::Err_UnknownFormat;
            }

            float val = getFloat(lineParts[3]);
            if (!is_nodata(val)) { // overwrite value from VELFP if it is not 0
                maxVel[node_inx] = val;
            }

            node_inx++;
        }
    }

    addStaticDataset(maxVel, "Velocity/Maximums", DataSet::Scalar, datFileName, mesh);
}

static float calcCellSize(const QVector<CellCenter>& cells) {
    // find first cell that is not izolated from the others 
    // and return its distance to the neighbor's cell center
    for (int i=0; i<cells.size(); ++i) {
        for (int j=0; j<4; ++j) {
            int idx = cells[i].conn[0];
            if (idx > -1) {
                if ((j==0) || (j==2)) {
                    return fabs(cells[idx].y - cells[i].y);
                } else {
                    return fabs(cells[idx].x - cells[i].x);
                }
            }
        }
    }
    throw LoadStatus::Err_IncompatibleMesh;
}

static Node createNode(int& node_id, int position, float half_cell_size, const CellCenter& cell) {
    Node n;
    n.setId(node_id);
    n.x = cell.x;
    n.y = cell.y;

    switch (position) {
    case 0:
        n.x += half_cell_size;
        n.y -= half_cell_size;
        break;

    case 1:
        n.x += half_cell_size;
        n.y += half_cell_size;
        break;

    case 2:
        n.x -= half_cell_size;
        n.y += half_cell_size;
        break;

    case 3:
        n.x -= half_cell_size;
        n.y -= half_cell_size;
        break;
    }

    return n;
}

static Mesh* createMesh(const QVector<CellCenter>& cells, float half_cell_size) {
    // Create all elements from cell centers.
    // Nodes must be also created, they are not stored in FLO-2D files
    // try to reuse nodes already created for other elements by usage of unique_nodes set.   
    Mesh::Elements elements;
    Mesh::Nodes nodes;
    QSet<Node> unique_nodes;
    int node_id = 0;

    for (int i=0; i<cells.size(); ++i) {
        Element e;
        e.setEType(Element::E4Q);
        e.setId(i);

        for (int position=0; position<4; ++position) {
            Node n = createNode(node_id, position, half_cell_size, cells[i]);
            QSet<Node>::const_iterator iter = unique_nodes.constFind(n);
            if (iter == unique_nodes.constEnd()) {
                unique_nodes.insert(n);
                nodes.append(n);
                e.setP(position, node_id);
                ++node_id;
            } else {
                e.setP(position, iter->id());
            }
        }

        elements.append(e);
    }

    return new Mesh(nodes, elements);
}

Mesh* Crayfish::loadFlo2D( const QString& datFileName, LoadStatus* status )
{
    if (status) status->clear();
    Mesh* mesh = 0;

    QVector<CellCenter> cells;

    try
    {
        // Parse mesh info
        parseCADPTSFile(datFileName, cells);
        QVector<float> elevations = parseFPLAINFile(datFileName, cells);
        float cell_size = calcCellSize(cells);

        // Create mesh
        mesh = createMesh(cells, cell_size/2.0);

        // create output for bed elevation
        addStaticDataset(elevations, "Bed Elevation", DataSet::Bed, datFileName, mesh);

        // Create Depth and Velocity datasets Time varying datasets
        parseTIMDEPFile(datFileName, mesh, elevations);

        // Maximum Depth and Water Level
        parseDEPTHFile(datFileName, mesh, elevations);

        // Maximum Velocity
        parseVELFPVELOCFile(datFileName, mesh);

    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
