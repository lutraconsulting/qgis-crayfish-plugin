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

#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_mesh_2dm.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"

#include <iostream>

Mesh* Crayfish::loadMesh2DM( const QString& twoDMFileName, LoadStatus* status ) {
  if (status) status->clear();
  //std::cerr << "CF: opening 2DM: " << twoDMFileName.toAscii().data() << std::endl;


  QFile file(twoDMFileName);
  if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
    if (status) status->mLastError = LoadStatus::Err_FileNotFound;
    return 0;
  }

  QTextStream in(&file);
  if (!in.readLine().startsWith("MESH2D")) {
    if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
    return 0;
  }

  int elemCount = 0;
  int nodeCount = 0;

  // Find out how many nodes and elements are contained in the .2dm mesh file
  while (!in.atEnd()) {
    QString line = in.readLine();
    if( line.startsWith("E4Q") ||
        line.startsWith("E3T")) {
      elemCount++;
    } else if( line.startsWith("ND") ) {
      nodeCount++;
    } else if( line.startsWith("E2L") ||
               line.startsWith("E3L") ||
               line.startsWith("E6T") ||
               line.startsWith("E8Q") ||
               line.startsWith("E9Q")) {
      if (status) status->mLastWarning = LoadStatus::Warn_UnsupportedElement;
      elemCount += 1; // We still count them as elements
    }
  }

  // Allocate memory
  Mesh::Nodes nodes(nodeCount);
  Mesh::Elements elements(elemCount);

  // create output for bed elevation
  NodeOutput* o = new NodeOutput;
  o->init(nodeCount, elemCount, false);
  o->time = 0.0;
  memset(o->getActive().data(), 1, elemCount); // All cells active

  in.seek(0);
  QStringList chunks = QStringList();

  int elemIndex = 0;
  int nodeIndex = 0;
  QMap<int, int> elemIDtoIndex;
  QMap<int, int> nodeIDtoIndex;
  //int maxElemID = 0;
  //int maxNodeID = 0;

  while (!in.atEnd()) {
    QString line = in.readLine();
    if( line.startsWith("E4Q") ) {
      chunks = line.split(" ", QString::SkipEmptyParts);
      Q_ASSERT(elemIndex < elemCount);

      int elemID = chunks[1].toInt();
      if (elemIDtoIndex.contains(elemID)) {
        if (status) status->mLastWarning = LoadStatus::Warn_ElementNotUnique;
        continue;
      }
      elemIDtoIndex[elemID] = elemIndex;
      //if (elemID > maxElemID)
      //  maxElemID = elemID;

      Element& elem = elements[elemIndex];
      elem.setId(elemID);
      elem.setEType(Element::E4Q);
      // Right now we just store node IDs here - we will convert them to node indices afterwards
      for (int i = 0; i < 4; ++i)
        elem.setP(i, chunks[i+2].toInt());

      elemIndex++;
    } else if( line.startsWith("E3T") ) {
      chunks = line.split(" ", QString::SkipEmptyParts);
      Q_ASSERT(elemIndex < elemCount);

      uint elemID = chunks[1].toInt();
      if (elemIDtoIndex.contains(elemID)) {
        if (status) status->mLastWarning = LoadStatus::Warn_ElementNotUnique;
        continue;
      }
      elemIDtoIndex[elemID] = elemIndex;
      //if (elemID > maxElemID)
      //  maxElemID = elemID;

      Element& elem = elements[elemIndex];
      elem.setId(elemID);
      elem.setEType(Element::E3T);
      // Right now we just store node IDs here - we will convert them to node indices afterwards
      for (int i = 0; i < 3; ++i)
        elem.setP(i, chunks[i+2].toInt());

      elemIndex++;
    } else if( line.startsWith("E2L") ||
               line.startsWith("E3L") ||
               line.startsWith("E6T") ||
               line.startsWith("E8Q") ||
               line.startsWith("E9Q")) {
      // We do not yet support these elements
      chunks = line.split(" ", QString::SkipEmptyParts);
      Q_ASSERT(elemIndex < elemCount);

      uint elemID = chunks[1].toInt();
      if (elemIDtoIndex.contains(elemID)) {
        if (status) status->mLastWarning = LoadStatus::Warn_ElementNotUnique;
        continue;
      }
      elemIDtoIndex[elemID] = elemIndex;
      //if (elemID > maxElemID)
      //  maxElemID = elemID;

      elements[elemIndex].setEType(Element::Undefined);

      elemIndex++;
    } else if( line.startsWith("ND") ) {
      chunks = line.split(" ", QString::SkipEmptyParts);
      int nodeID = chunks[1].toInt();

      if (nodeIDtoIndex.contains(nodeID)) {
        if (status) status->mLastWarning = LoadStatus::Warn_NodeNotUnique;
        continue;
      }
      nodeIDtoIndex[nodeID] = nodeIndex;
      //if (nodeID > maxNodeID)
      //  maxNodeID = nodeID;

      Q_ASSERT(nodeIndex < nodeCount);

      Node& n = nodes[nodeIndex];
      n.setId(nodeID);
      n.x = chunks[2].toDouble();
      n.y = chunks[3].toDouble();
      o->getValues()[nodeIndex] = chunks[4].toFloat();

      nodeIndex++;
    }
  }


  for (Mesh::Elements::iterator it = elements.begin(); it != elements.end(); ++it) {
    if( it->isDummy() )
      continue;

    Element& elem = *it;

    // Resolve node IDs in elements to node indices
    for (int nd = 0; nd < elem.nodeCount(); ++nd) {
      int nodeID = elem.p(nd);
      QMap<int, int>::const_iterator ni2i = nodeIDtoIndex.constFind(nodeID);
      if (ni2i != nodeIDtoIndex.end()) {
        elem.setP(nd, *ni2i); // convert from ID to index
      } else {
        elem.setEType(Element::Undefined); // mark element as unusable

        if (status) status->mLastWarning = LoadStatus::Warn_ElementWithInvalidNode;
      }
    }

    // check validity of the triangle
    // for now just checking if we have three distinct nodes
    if (elem.eType() == Element::E3T) {
      const Node& n1 = nodes[elem.p(0)];
      const Node& n2 = nodes[elem.p(1)];
      const Node& n3 = nodes[elem.p(2)];
      if (n1 == n2 || n1 == n3 || n2 == n3) {
        elem.setEType(Element::Undefined); // mark element as unusable

        if (status) status->mLastWarning = LoadStatus::Warn_InvalidElements;
      }
    }
  }

  Mesh* mesh = new Mesh(nodes, elements);

  // Create a dataset for the bed elevation
  DataSet* bedDs = new DataSet(twoDMFileName);
  bedDs->setType(DataSet::Bed);
  bedDs->setName("Bed Elevation");
  bedDs->setIsTimeVarying(false);
  bedDs->addOutput(o);  // takes ownership of the Output
  bedDs->updateZRange();
  mesh->addDataSet(bedDs);

  return mesh;
}
