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

static void parseCADPTSFile(const QString& datFileName, Mesh::Nodes& nodes) {
    QFileInfo fi(datFileName);
    QString nodesFileName(fi.dir().filePath("CADPTS.DAT"));
    QFile nodesFile(nodesFileName);
    if (!nodesFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream nodesStream(&nodesFile);


    // CADPTS.DAT - COORDINATES (ELEM NUM, X, Y)
    while (!nodesStream.atEnd())
    {
        QString line = nodesStream.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() != 3) {
            throw LoadStatus::Err_UnknownFormat;
        }
        Node node;
        node.setId(lineParts[1].toInt() -1); //numbered from 1
        node.x = lineParts[1].toFloat();
        node.y = lineParts[2].toFloat();
        nodes.append(node);
    }
}

// recursive
// Go in clockwise direction to find faces
static void getNextIndex(int* myIndex, int* nextDirection, const QVector<QVector<int> >& orientedEdgeGroups) {
    QVector<int> myself = orientedEdgeGroups[*myIndex];
    *myIndex = myself[*nextDirection];
    *nextDirection = (*nextDirection + 1) % 4;
}

static bool createElement(int counter, int myIndex, int myDirection, Element& elem, QSet<QPair<int, int> >& visitedFaces, const QVector<QVector<int> >& orientedEdgeGroups) {
    if (myIndex < 0) return false; // we have come to dead end
    if (counter == 4) return true; // we have the face

    elem.setP(myDirection, myIndex);

    int nextIndex = myIndex;
    int nextDirection = myDirection;
    getNextIndex(&nextIndex, &nextDirection, orientedEdgeGroups);

    QPair<int, int> pair = qMakePair(myIndex, nextIndex);
    if (visitedFaces.contains(pair)) return false; // we already have this element created
    visitedFaces.insert(pair);

    counter++;
    return createElement(counter, nextIndex, nextDirection, elem,  visitedFaces, orientedEdgeGroups);
}

static void createElements(const QVector<QVector<int> >& orientedEdgeGroups, Mesh::Elements& elements) {
    // http://mathoverflow.net/a/23958
    // http://math.stackexchange.com/a/15069
    QSet<QPair<int, int> > visitedFaces;

    int elemId = 0;

    for (int i=0; i<orientedEdgeGroups.size(); ++i){
        Element elem;
        elem.setEType(Element::E4Q);
        elem.setId(elemId);
        bool success = createElement(0, i, 0, elem,  visitedFaces, orientedEdgeGroups);
        if (success) {
            elements.push_back(elem);
            ++elemId;
        }
    }

}

static QVector<float> parseFPLAINFile(const QString& datFileName, Mesh::Elements& elements) {
    // FPLAIN.DAT - CONNECTIVITY (NODE NUM, NODE N, NODE E, NODE S, NODE W, MANNING-N, BED ELEVATION)
    QFileInfo fi(datFileName);
    QString elemFileName(fi.dir().filePath("FPLAIN.DAT"));
    QFile elemFile(elemFileName);
    if (!elemFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream elemStream(&elemFile);

    QVector<float> elevations;
    QVector<QVector<int> > orientedEdgeGroups;

    while (!elemStream.atEnd())
    {
        QString line = elemStream.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() != 7) {
            throw LoadStatus::Err_UnknownFormat;
        }
        QVector<int> edgeGroup(4);
        edgeGroup[0] = lineParts[1].toInt() -1; //numbered from 1, 0 bondary node
        edgeGroup[1] = lineParts[2].toInt() -1; //numbered from 1, 0 bondary node
        edgeGroup[2] = lineParts[3].toInt() -1; //numbered from 1, 0 bondary node
        edgeGroup[3] = lineParts[4].toInt() -1; //numbered from 1, 0 bondary node
        orientedEdgeGroups.push_back(edgeGroup);

        elevations.push_back(lineParts[6].toFloat());
    }

    createElements(orientedEdgeGroups, elements);

    return elevations;
}

static inline bool is_nodata(float val, float nodata = -9999.0, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val - nodata) < eps;}
static void activateElements(NodeOutput* tos, const Mesh* mesh){
   // Activate only elements that do all node's outputs with some data
   char* active = tos->active.data();

   for (int idx=0; idx<mesh->elements().size(); ++idx)
   {
       Element elem = mesh->elements().at(idx);

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

static float getFloat(const QString& val) {
    float valF = val.toFloat();
    if (is_nodata(valF, 0.0f)) {
        return -9999.0;
    } else {
        return valF;
    }
}

static void addOutput(DataSet* ds, NodeOutput* o, const Mesh* mesh) {
     activateElements(o, mesh);
     ds->addOutput(o);
}

static void parseTIMDEPFile(const QString& datFileName, Mesh* mesh, const QVector<float>& elevations) {\
    //TIMDEP.OUT
    // time (separate line)
    // For every node: node number (indexed from 1), depth, velocity, velocity x, velocity y

    QFileInfo fi(datFileName);
    QFile inFile(fi.dir().filePath("TIMDEP.OUT"));
    if (!inFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream in(&inFile);

    int nnodes = mesh->nodes().size();
    int nelems = mesh->elements().size();
    int ntimes = 0;

    float time = 0.0;
    int node_inx = 0;

    DataSet* depthDs = new DataSet(datFileName);
    depthDs->setType(DataSet::Scalar);
    depthDs->setName("Depth");

    DataSet* waterLevelDs = new DataSet(datFileName);
    waterLevelDs->setType(DataSet::Scalar);
    waterLevelDs->setName("Water Level");

    DataSet* flowDs = new DataSet(datFileName);
    flowDs->setType(DataSet::Vector);
    flowDs->setName("Velocity");

    NodeOutput* flowOutput = 0;
    NodeOutput* depthOutput = 0;
    NodeOutput* waterLevelOutput = 0;


    while (!in.atEnd())
    {
        QString line = in.readLine();
        QStringList lineParts = line.split(" ", QString::SkipEmptyParts);
        if (lineParts.size() == 1) {
            time = line.toFloat();
            ntimes++;

            if (depthOutput) addOutput(depthDs, depthOutput, mesh);
            if (flowOutput) addOutput(flowDs, flowOutput, mesh);
            if (waterLevelOutput) addOutput(waterLevelDs, waterLevelOutput, mesh);

            depthOutput = new NodeOutput;
            flowOutput = new NodeOutput;
            waterLevelOutput = new NodeOutput;

            depthOutput->init(nnodes, nelems, false); //scalar
            flowOutput->init(nnodes, nelems, true); //vector
            waterLevelOutput->init(nnodes, nelems, false); //scalar

            depthOutput->time = time;
            flowOutput->time = time;
            waterLevelOutput->time = time;

            node_inx = 0;

        } else if (lineParts.size() == 5) {
            // new node for time
            if (!depthOutput || !flowOutput || !waterLevelOutput) throw LoadStatus::Err_UnknownFormat;
            if (node_inx == nnodes) throw LoadStatus::Err_IncompatibleMesh;

            flowOutput->values[node_inx] = getFloat(lineParts[2]);
            flowOutput->valuesV[node_inx].x = getFloat(lineParts[3]);
            flowOutput->valuesV[node_inx].y = getFloat(lineParts[4]);

            float depth = getFloat(lineParts[1]);
            depthOutput->values[node_inx] = depth;

            if (!is_nodata(depth)) depth += elevations[node_inx];
            waterLevelOutput->values[node_inx] = depth;

            node_inx ++;

        } else {
            throw LoadStatus::Err_UnknownFormat;
        }
    }

    if (depthOutput) addOutput(depthDs, depthOutput, mesh);
    if (flowOutput) addOutput(flowDs, flowOutput, mesh);
    if (waterLevelOutput) addOutput(waterLevelDs, waterLevelOutput, mesh);

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

static void addStaticDataset(QVector<float>& vals, const QString& name, const DataSet::Type type, const QString& datFileName, Mesh* mesh) {
    int nelem = mesh->elements().size();
    int nnodes = mesh->nodes().size();

    NodeOutput* o = new NodeOutput;

    o->init(nnodes, nelem, false);
    o->time = 0.0;
    o->values = vals;

    if (type == DataSet::Bed) {
        memset(o->active.data(), 1, nelem); // All cells active
    } else {
        activateElements(o, mesh);
    }

    DataSet* ds = new DataSet(datFileName);
    ds->setType(type);
    ds->setName(name, false);
    ds->setIsTimeVarying(false);
    ds->addOutput(o);  // takes ownership of the Output
    ds->updateZRange();
    mesh->addDataSet(ds);
}

static void parseDEPTHFile(const QString&datFileName, Mesh* mesh, const QVector<float>& elevations) {
    QFileInfo fi(datFileName);
    QString nodesFileName(fi.dir().filePath("DEPTH.OUT"));
    QFile nodesFile(nodesFileName);
    if (!nodesFile.open(QIODevice::ReadOnly | QIODevice::Text)) throw LoadStatus::Err_FileNotFound;
    QTextStream nodesStream(&nodesFile);

    int nnodes = mesh->nodes().size();
    QVector<float> maxDepth(nnodes);
    QVector<float> maxWaterLevel(nnodes);

    int node_inx = 0;

    // DEPTH.OUT - COORDINATES (NODE NUM, X, Y, MAX DEPTH)
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
    addStaticDataset(maxDepth, "Water Level/Maximums", DataSet::Scalar, datFileName, mesh);
}

Mesh* Crayfish::loadFlo2D( const QString& datFileName, LoadStatus* status )
{
    if (status) status->clear();
    Mesh* mesh = 0;

    try
    {
        // Parse all nodes
        Mesh::Nodes nodes;
        parseCADPTSFile(datFileName, nodes);

        // Parse all elements
        Mesh::Elements elements;
        QVector<float> elevations = parseFPLAINFile(datFileName, elements);

        // Create mesh
        mesh = new Mesh(nodes, elements);

        // create output for bed elevation
        addStaticDataset(elevations, "Bed Elevation", DataSet::Bed, datFileName, mesh);

        // Create Depth and Velocity datasets Time varying datasets
        parseTIMDEPFile(datFileName, mesh, elevations);

        // Maximum Depth
        parseDEPTHFile(datFileName, mesh, elevations);

    }

    catch (LoadStatus::Error error)
    {
        if (status) status->mLastError = (error);
        if (mesh) delete mesh;
        mesh = 0;
    }

    return mesh;
}
