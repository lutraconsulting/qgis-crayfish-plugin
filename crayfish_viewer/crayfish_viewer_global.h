/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2012 Peter Wells for Lutra Consulting

peter dot wells at lutraconsulting dot co dot uk
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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.from PyQt4.QtCore import *
*/

#ifndef CRAYFISHVIEWER_GLOBAL_H
#define CRAYFISHVIEWER_GLOBAL_H

#include <QtCore/qglobal.h>
#include <QString>
#include <vector>

#if defined(CRAYFISHVIEWER_LIBRARY)
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_EXPORT
#else
#  define CRAYFISHVIEWERSHARED_EXPORT Q_DECL_IMPORT
#endif

namespace ViewerError{
    enum Enum{
        None,
        FileNotFound
    };
};

namespace ViewerWarning{
    enum Enum{
        None,
        UnsupportedElement
    };
};

namespace DataSetType{
    enum Enum{
        Bed,
        Scalar,
        Vector
    };
};

struct Node{
    uint index;
    double x;
    double y;
    double z;
};

struct Element{
    uint index;
    bool isDummy;
    Node* p1;   // Top-Right node
    Node* p2;   // Top-Left node
    Node* p3;   // Bottom-Left node
    Node* p4;   // Bottom-Right node
    double maxSize; // Largest distance (real world) across the element
    double minX;
    double maxX;
    double minY;
    double maxY;
    bool hasRotation;
    double rotation;
    double sinAlpha;
    double cosAlpha;
    double sinNegAlpha;
    double cosNegAlpha;
};

struct Output{
    float time;
    char* statusFlags;
    float* values;
    float* values_x;
    float* values_y;
};

struct DataSet{
    DataSetType::Enum type;
    QString name;
    std::vector<Output*> outputs;
    float mZMin;
    float mZMax;
    bool timeVarying;
    int lastOutputRendered;
    bool contouredAutomatically;
    bool renderContours;
    bool renderVectors;
    float contourMin;
    float contourMax;
    bool isBed;
};

#endif // CRAYFISHVIEWER_GLOBAL_H
