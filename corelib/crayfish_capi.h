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

#ifndef CRAYFISH_CAPI_H
#define CRAYFISH_CAPI_H

#include <QtCore/qglobal.h>

#if defined(CRAYFISH_LIBRARY)
#  define CF_EXPORT Q_DECL_EXPORT
#else
#  define CF_EXPORT Q_DECL_IMPORT
#endif

extern "C"
{

#ifndef CF_TYPES
#define CF_TYPES
typedef void* MeshH;
typedef void* NodeH;
typedef void* ElementH;
typedef void* DataSetH;
typedef void* OutputH;
typedef void* RendererConfigH;
typedef void* RendererH;
typedef void* VariantH;
typedef void* ImageH;
typedef void* ColorMapH;
#endif

CF_EXPORT int CF_Version();

CF_EXPORT MeshH CF_LoadMesh(const char* meshFile);

CF_EXPORT void CF_CloseMesh(MeshH mesh);

CF_EXPORT int CF_LastLoadError();
CF_EXPORT int CF_LastLoadWarning();

CF_EXPORT int CF_ExportGrid(OutputH output, double mupp, const char* outputFilename, const char* projWkt);

CF_EXPORT int CF_ExportContours(OutputH output, double mupp, double interval, const char* outputFilename, const char* projWkt, bool useLines, ColorMapH cm);

// Mesh functions

CF_EXPORT int CF_Mesh_nodeCount(MeshH mesh);
CF_EXPORT NodeH CF_Mesh_nodeAt(MeshH mesh, int index);

CF_EXPORT int CF_Mesh_elementCount(MeshH mesh);
CF_EXPORT ElementH CF_Mesh_elementAt(MeshH mesh, int index);

CF_EXPORT int CF_Mesh_dataSetCount(MeshH mesh);
CF_EXPORT DataSetH CF_Mesh_dataSetAt(MeshH mesh, int index);


CF_EXPORT bool CF_Mesh_loadDataSet(MeshH mesh, const char* path);

CF_EXPORT void CF_Mesh_extent(MeshH mesh, double* xmin, double* ymin, double* xmax, double* ymax);

CF_EXPORT double CF_Mesh_valueAt(MeshH mesh, OutputH output, double x, double y);

CF_EXPORT void CF_Mesh_setSourceCrs(MeshH mesh, const char* srcProj4);
CF_EXPORT void CF_Mesh_setDestinationCrs(MeshH mesh, const char* destProj4);

CF_EXPORT const char* CF_Mesh_sourceCrs(MeshH mesh);
CF_EXPORT const char* CF_Mesh_destinationCrs(MeshH mesh);

// DataSet functions

CF_EXPORT int CF_DS_type(DataSetH ds);
CF_EXPORT const char* CF_DS_name(DataSetH ds);
CF_EXPORT const char* CF_DS_fileName(DataSetH ds);

CF_EXPORT int CF_DS_outputCount(DataSetH ds);
CF_EXPORT OutputH CF_DS_outputAt(DataSetH ds, int index);

CF_EXPORT MeshH CF_DS_mesh(DataSetH ds);
CF_EXPORT void CF_DS_valueRange(DataSetH ds, float* vMin, float* vMax);

// Output functions
CF_EXPORT int CF_O_type(OutputH o);
CF_EXPORT float CF_O_time(OutputH o);
CF_EXPORT float CF_O_valueAt(OutputH o, int index);
CF_EXPORT void CF_O_valueVectorAt(OutputH o, int index, float* x, float* y);
CF_EXPORT char CF_O_statusAt(OutputH o, int index);
CF_EXPORT DataSetH CF_O_dataSet(OutputH o);
CF_EXPORT void CF_O_Range(OutputH o, float* zMin, float* zMax);

// Renderer Config functions
CF_EXPORT RendererConfigH CF_RC_create();
CF_EXPORT void CF_RC_destroy(RendererConfigH cfg);
CF_EXPORT void CF_RC_setView(RendererConfigH cfg, int width, int height, double llx, double lly, double pixelSize);
CF_EXPORT void CF_RC_setOutputMesh(RendererConfigH cfg, MeshH mesh);
CF_EXPORT void CF_RC_setOutputContour(RendererConfigH cfg, OutputH output);
CF_EXPORT void CF_RC_setOutputVector(RendererConfigH cfg, OutputH output);
CF_EXPORT void CF_RC_setParam(RendererConfigH cfg, const char* key, VariantH value);
CF_EXPORT void CF_RC_getParam(RendererConfigH cfg, const char* key, VariantH value);

// Renderer functions
CF_EXPORT RendererH CF_R_create(RendererConfigH cfg, ImageH img);
CF_EXPORT void CF_R_destroy(RendererH rend);
CF_EXPORT void CF_R_draw(RendererH rend);

// Variant value
CF_EXPORT VariantH CF_V_create();
CF_EXPORT void CF_V_destroy(VariantH v);
CF_EXPORT int CF_V_type(VariantH v);
CF_EXPORT void CF_V_fromInt(VariantH v, int i);
CF_EXPORT int CF_V_toInt(VariantH v);
CF_EXPORT void CF_V_fromDouble(VariantH v, double d);
CF_EXPORT double CF_V_toDouble(VariantH v);
CF_EXPORT void CF_V_toColor(VariantH v, int* r, int* g, int* b, int* a);
CF_EXPORT void CF_V_fromColor(VariantH v, int r, int g, int b, int a);
CF_EXPORT void CF_V_toColorMap(VariantH v, ColorMapH cm);
CF_EXPORT void CF_V_fromColorMap(VariantH v, ColorMapH cm);

// Colormap
CF_EXPORT ColorMapH CF_CM_create();
CF_EXPORT void CF_CM_destroy(ColorMapH cm);
CF_EXPORT ColorMapH CF_CM_createDefault(double vmin, double vmax);
CF_EXPORT int CF_CM_value(ColorMapH cm, double v);
CF_EXPORT int CF_CM_itemCount(ColorMapH cm);
CF_EXPORT double CF_CM_itemValue(ColorMapH cm, int index);
CF_EXPORT int CF_CM_itemColor(ColorMapH cm, int index);
CF_EXPORT const char* CF_CM_itemLabel(ColorMapH cm, int index);
CF_EXPORT void CF_CM_setItemCount(ColorMapH cm, int count);
CF_EXPORT void CF_CM_setItemValue(ColorMapH cm, int index, double value);
CF_EXPORT void CF_CM_setItemColor(ColorMapH cm, int index, int color);
CF_EXPORT void CF_CM_setItemLabel(ColorMapH cm, int index, const char* label);
CF_EXPORT void CF_CM_clip(ColorMapH cm, int* clipLow, int* clipHigh);
CF_EXPORT void CF_CM_setClip(ColorMapH cm, int clipLow, int clipHigh);
CF_EXPORT int CF_CM_alpha(ColorMapH cm);
CF_EXPORT void CF_CM_setAlpha(ColorMapH cm, int alpha);
CF_EXPORT int CF_CM_method(ColorMapH cm);
CF_EXPORT void CF_CM_setMethod(ColorMapH cm, int method);

}

#endif // CRAYFISH_CAPI_H
