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

#include <QDateTime>

// keep in sync with DATETIME_FMT in core.py
#define DATETIME_FMT "yyyy-MM-dd'T'HH:mm:ss.z'Z'"

#include "crayfish.h"
#include "crayfish_mesh.h"
#include "crayfish_dataset.h"
#include "crayfish_output.h"
#include "crayfish_renderer.h"

#define CF_TYPES
typedef Mesh* MeshH;
typedef const Node* NodeH;
typedef const Element* ElementH;
typedef DataSet* DataSetH;
typedef const Output* OutputH;
typedef RendererConfig* RendererConfigH;
typedef Renderer* RendererH;
typedef QVariant* VariantH;
typedef QImage* ImageH;
typedef ColorMap* ColorMapH;

#include "crayfish_capi.h"

static LoadStatus sLastLoadStatus;


int CF_Version()
{
  return 0x020601; // 2.6.1
}


MeshH CF_LoadMesh(const char* meshFile)
{
  return (MeshH) Crayfish::loadMesh(QString::fromUtf8(meshFile), &sLastLoadStatus);
}


void CF_CloseMesh(MeshH mesh)
{
  delete mesh;
}


int CF_ExportGrid(OutputH output, double mupp, const char* outputFilename, const char* projWkt)
{
  return Crayfish::exportRawDataToTIF(output, mupp, QString::fromUtf8(outputFilename), QString::fromUtf8(projWkt));
}

int CF_ExportContours(OutputH output, double mupp, double interval, const char* outputFilename, const char* projWkt, bool useLines, ColorMapH cm)
{
  return Crayfish::exportContoursToSHP(output, mupp, interval, QString::fromUtf8(outputFilename), QString::fromUtf8(projWkt), useLines, (ColorMap*) cm);
}

int CF_Mesh_nodeCount(MeshH mesh)
{
  return mesh->nodes().count();
}


int CF_Mesh_elementCount(MeshH mesh)
{
  return mesh->elements().count();
}


NodeH CF_Mesh_nodeAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->nodes().count())
    return 0;

  const Node& n = mesh->nodes()[index];
  return &n;
}


ElementH CF_Mesh_elementAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->elements().count())
    return 0;

  const Element& e = mesh->elements()[index];
  return &e;
}


int CF_Mesh_dataSetCount(MeshH mesh)
{
  return mesh->dataSets().count();
}


DataSetH CF_Mesh_dataSetAt(MeshH mesh, int index)
{
  if (index < 0 || index >= mesh->dataSets().count())
    return 0;

  DataSet* ds = mesh->dataSets()[index];
  return ds;
}


int CF_DS_type(DataSetH ds)
{
  return ds->type();
}

int CF_E_nodeCount(ElementH elem) {
    return elem->nodeCount();
}

int CF_E_nodeIndexAt(ElementH elem, int index){
    if (index < 0 || index >= elem->nodeCount())
      return 0;

    return elem->p(index);
}

int CF_E_id(ElementH elem){
    return elem->id();
}

int CF_E_type(ElementH elem){
    return elem->eType();
}

int CF_N_id(NodeH node){
    return node->id();
}

double CF_N_x(NodeH node){
    return node->x;
}

double CF_N_y(NodeH node){
    return node->y;
}

// helper to return string data - without having to deal with memory too much.
// returned pointer is valid only next call. also not thread-safe.
const char* _return_str(const QString& str)
{
  static QByteArray lastStr;
  lastStr = str.toUtf8();
  return lastStr.constData();
}


const char* CF_DS_name(DataSetH ds)
{
  return _return_str(ds->name());
}


const char* CF_DS_fileName(DataSetH ds)
{
  return _return_str(ds->fileName());
}


int CF_DS_outputCount(DataSetH ds)
{
  return ds->outputCount();
}


OutputH CF_DS_outputAt(DataSetH ds, int index)
{
  if (index < 0 || index >= ds->outputCount())
    return 0;

  return ds->constOutput(index);
}


MeshH CF_DS_mesh(DataSetH ds)
{
  return (MeshH)ds->mesh();
}


int CF_O_type(OutputH o)
{
  return o->type();
}


float CF_O_time(OutputH o)
{
  return o->time;
}


float CF_O_valueAt(OutputH o, int index)
{
  if (o->type() == Output::TypeNode)
    return static_cast<const NodeOutput*>(o)->loadedValues()[index];
  else if (o->type() == Output::TypeElement)
    return static_cast<const ElementOutput*>(o)->loadedValues()[index];
  else
    return 0;
}

void CF_O_valueVectorAt(OutputH o, int index, float* x, float* y)
{
  if (o->type() == Output::TypeNode)
  {
    const NodeOutput* nodeO = static_cast<const NodeOutput*>(o);
    *x = nodeO->loadedValuesV()[index].x;
    *y = nodeO->loadedValuesV()[index].y;
  }
  else
  {
    const ElementOutput* elO = static_cast<const ElementOutput*>(o);
    *x = elO->loadedValuesV()[index].x;
    *y = elO->loadedValuesV()[index].y;
  }
}

void CF_O_range(OutputH o, float* zMin, float* zMax) {
    Q_ASSERT(zMin && zMax && o);
    o->getRange(*zMin, *zMax);
}

char CF_O_statusAt(OutputH o, int index)
{
  return static_cast<const NodeOutput*>(o)->isActive(index);
}

DataSetH CF_O_dataSet(OutputH o)
{
  return (DataSetH)o->dataSet;
}


bool CF_Mesh_loadDataSet(MeshH mesh, const char* path)
{
  Mesh::DataSets lst = Crayfish::loadDataSet(QString::fromUtf8(path), mesh, &sLastLoadStatus);
  if (!lst.count())
    return false;

  foreach (DataSet* ds, lst)
    mesh->addDataSet(ds);
  return true;
}


int CF_LastLoadError()
{
  return sLastLoadStatus.mLastError;
}


int CF_LastLoadWarning()
{
  return sLastLoadStatus.mLastWarning;
}


RendererH CF_R_create(RendererConfigH cfg, ImageH img)
{
  RendererH rend = new Renderer(*cfg, *img);
  return rend;
}


void CF_R_destroy(RendererH rend)
{
  delete rend;
}


void CF_R_draw(RendererH rend)
{
  rend->draw();
}


RendererConfigH CF_RC_create()
{
  RendererConfigH cfg = new RendererConfig();
  return cfg;
}


void CF_RC_destroy(RendererConfigH cfg)
{
  delete cfg;
}


void CF_RC_setView(RendererConfigH cfg, int width, int height, double llx, double lly, double pixelSize)
{
  cfg->outputSize = QSize(width, height);
  cfg->llX = llx;
  cfg->llY = lly;
  cfg->pixelSize = pixelSize;
}

void CF_RC_setOutputMesh(RendererConfigH cfg, MeshH mesh)
{
  cfg->outputMesh = mesh;
}

void CF_RC_setOutputContour(RendererConfigH cfg, OutputH output)
{
  cfg->outputContour = output;
}

void CF_RC_setOutputVector(RendererConfigH cfg, OutputH output)
{
  cfg->outputVector = output;
}


void CF_Mesh_extent(MeshH mesh, double* xmin, double* ymin, double* xmax, double* ymax)
{
  BBox b = mesh->extent();
  *xmin = b.minX;
  *ymin = b.minY;
  *xmax = b.maxX;
  *ymax = b.maxY;
}


double CF_Mesh_valueAt(MeshH mesh, OutputH output, double x, double y)
{
  return mesh->valueAt(output, x, y);
}

void CF_Mesh_setSourceCrs(MeshH mesh, const char* srcProj4)
{
  mesh->setSourceCrs(QString::fromAscii(srcProj4));
}

void CF_Mesh_setDestinationCrs(MeshH mesh, const char* destProj4)
{
  mesh->setDestinationCrs(QString::fromAscii(destProj4));
}

const char* CF_Mesh_sourceCrs(MeshH mesh)
{
  return _return_str(mesh->sourceCrs());
}

const char* CF_Mesh_destinationCrs(MeshH mesh)
{
  return _return_str(mesh->destinationCrs());
}


void CF_DS_valueRange(DataSetH ds, float* vMin, float* vMax)
{
  *vMin = ds->minZValue();
  *vMax = ds->maxZValue();
}

const char* CF_DS_refTime(DataSetH ds)
{
    QDateTime dt = ds->getRefTime();
    if (dt.isValid()) {
        return _return_str(dt.toString(DATETIME_FMT));
    } else {
        return "";
    }
}

void CF_RC_setParam(RendererConfigH cfg, const char* key, VariantH value)
{
  QString k = QString::fromAscii(key);
  if (k == "mesh")
    cfg->mesh.mRenderMesh = value->toBool();
  else if (k == "m_border_color")
    cfg->mesh.mMeshBorderColor = value->value<QColor>();
  else if (k == "m_fill_color")
    cfg->mesh.mMeshFillColor = value->value<QColor>();
  else if (k == "m_label_elem")
    cfg->mesh.mMeshElemLabel = value->toBool();
  else if (k == "m_border_width")
    cfg->mesh.mMeshBorderWidth = value->toInt();
  else if (k == "m_fill_enabled")
    cfg->mesh.mMeshFillEnabled = value->toBool();
  else if (k == "c_colormap")
    cfg->ds.mColorMap = value->value<ColorMap>();
  else if (k == "v_shaft_length_method")
    cfg->ds.mShaftLengthMethod = (ConfigDataSet::VectorLengthMethod) value->toInt();
  else if (k == "v_shaft_length_min")
    cfg->ds.mMinShaftLength = value->toFloat();
  else if (k == "v_shaft_length_max")
    cfg->ds.mMaxShaftLength = value->toFloat();
  else if (k == "v_shaft_length_scale")
    cfg->ds.mScaleFactor = value->toFloat();
  else if (k == "v_shaft_length_fixed")
    cfg->ds.mFixedShaftLength = value->toFloat();
  else if (k == "v_pen_width")
    cfg->ds.mLineWidth = value->toInt();
  else if (k == "v_head_width")
    cfg->ds.mVectorHeadWidthPerc = value->toFloat();
  else if (k == "v_head_length")
    cfg->ds.mVectorHeadLengthPerc = value->toFloat();
  else if (k == "v_grid")
    cfg->ds.mVectorUserGrid = value->toBool();
  else if (k == "v_grid_x")
    cfg->ds.mVectorUserGridCellSize.setWidth(value->toInt());
  else if (k == "v_grid_y")
    cfg->ds.mVectorUserGridCellSize.setHeight(value->toInt());
  else if (k == "v_filter_min")
    cfg->ds.mVectorFilterMin = value->toFloat();
  else if (k == "v_filter_max")
    cfg->ds.mVectorFilterMax = value->toFloat();
  else if (k == "v_color")
    cfg->ds.mVectorColor = value->value<QColor>();
  else if (k == "v_trace")
    cfg->ds.mVectorTrace = value->toBool();
  else if (k == "v_fps")
    cfg->ds.mVectorTraceFPS = value->toInt();
  else if (k == "v_calc_steps")
    cfg->ds.mVectorTraceCalculationSteps = value->toInt();
  else if (k == "v_anim_steps")
    cfg->ds.mVectorTraceAnimationSteps = value->toInt();
  else if (k == "v_show_particles")
    cfg->ds.mVectorTraceParticles = value->toBool();
  else if (k == "v_n_particles")
    cfg->ds.mVectorTraceParticlesCount = value->toInt();
  else
    qDebug("[setParam] unknown key: %s", key);
}



void CF_RC_getParam(RendererConfigH cfg, const char* key, VariantH value)
{
  QString k = QString::fromAscii(key);
  if (k == "mesh")
    *value = QVariant(cfg->mesh.mRenderMesh);
  else if (k == "m_border_color")
    *value = QVariant::fromValue(cfg->mesh.mMeshBorderColor);
  else if (k == "m_fill_color")
    *value = QVariant::fromValue(cfg->mesh.mMeshFillColor);
  else if (k == "m_label_elem")
    *value = QVariant::fromValue(cfg->mesh.mMeshElemLabel);
  else if (k == "m_border_width")
    *value = QVariant::fromValue(cfg->mesh.mMeshBorderWidth);
  else if (k == "m_fill_enabled")
    *value = QVariant::fromValue(cfg->mesh.mMeshFillEnabled);
  else if (k == "c_colormap")
    *value = QVariant::fromValue(cfg->ds.mColorMap);
  else if (k == "v_shaft_length_method")
    *value = QVariant(cfg->ds.mShaftLengthMethod);
  else if (k == "v_shaft_length_min")
    *value = QVariant(cfg->ds.mMinShaftLength);
  else if (k == "v_shaft_length_max")
    *value = QVariant(cfg->ds.mMaxShaftLength);
  else if (k == "v_shaft_length_scale")
    *value = QVariant(cfg->ds.mScaleFactor);
  else if (k == "v_shaft_length_fixed")
    *value = QVariant(cfg->ds.mFixedShaftLength);
  else if (k == "v_pen_width")
    *value = QVariant(cfg->ds.mLineWidth);
  else if (k == "v_head_width")
    *value = QVariant(cfg->ds.mVectorHeadWidthPerc);
  else if (k == "v_head_length")
    *value = QVariant(cfg->ds.mVectorHeadLengthPerc);
  else if (k == "v_grid")
    *value = QVariant(cfg->ds.mVectorUserGrid);
  else if (k == "v_grid_x")
    *value = QVariant(cfg->ds.mVectorUserGridCellSize.width());
  else if (k == "v_grid_y")
    *value = QVariant(cfg->ds.mVectorUserGridCellSize.height());
  else if (k == "v_filter_min")
    *value = QVariant(cfg->ds.mVectorFilterMin);
  else if (k == "v_filter_max")
    *value = QVariant(cfg->ds.mVectorFilterMax);
  else if (k == "v_color")
    *value = QVariant(cfg->ds.mVectorColor);
  else if (k == "v_trace")
    *value = QVariant(cfg->ds.mVectorTrace);
  else if (k == "v_fps")
    *value = QVariant(cfg->ds.mVectorTraceFPS);
  else if (k == "v_calc_steps")
    *value = QVariant(cfg->ds.mVectorTraceCalculationSteps);
  else if (k == "v_anim_steps")
    *value = QVariant(cfg->ds.mVectorTraceAnimationSteps);
  else if (k == "v_show_particles")
    *value = QVariant(cfg->ds.mVectorTraceParticles);
  else if (k == "v_n_particles")
    *value = QVariant(cfg->ds.mVectorTraceParticlesCount);
  else
    qDebug("[getParam] unknown key: %s", key);
}


VariantH CF_V_create()
{
  return new QVariant();
}


void CF_V_destroy(VariantH v)
{
  delete v;
}


int CF_V_type(VariantH v)
{
 if (v->type() == QVariant::Invalid)
   return 0;
 if (v->type() == QVariant::Bool || v->type() == QVariant::Int)
   return 1;
 else if (v->type() == QVariant::Double || (int)v->type() == (int)QMetaType::Float)
   return 2;
 else if (v->type() == QVariant::Color)
   return 3;
 else if (v->canConvert<ColorMap>())
   return 4;
 else
 {
   qDebug("unknown type: %d",v->type());
   return -1;
 }
}


void CF_V_fromInt(VariantH v, int i)
{
  *v = QVariant(i);
}


int CF_V_toInt(VariantH v)
{
  return v->toInt();
}


void CF_V_fromDouble(VariantH v, double d)
{
  *v = QVariant(d);
}


double CF_V_toDouble(VariantH v)
{
  return v->toDouble();
}


void CF_V_fromColor(VariantH v, int r, int g, int b, int a)
{
  *v = QVariant::fromValue(QColor(r,g,b,a));
}

void CF_V_toColor(VariantH v, int* r, int* g, int* b, int* a)
{
  QColor c = v->value<QColor>();
  *r = c.red();
  *g = c.green();
  *b = c.blue();
  *a = c.alpha();
}

ColorMapH CF_CM_create()
{
  return new ColorMap();
}


void CF_CM_destroy(ColorMapH cm)
{
  delete cm;
}


int CF_CM_value(ColorMapH cm, double v)
{
  return cm->value(v);
}


void CF_V_toColorMap(VariantH v, ColorMapH cm)
{
  *cm = v->value<ColorMap>();
}


void CF_V_fromColorMap(VariantH v, ColorMapH cm)
{
  *v = QVariant::fromValue(*cm);
}


int CF_CM_itemCount(ColorMapH cm)
{
  return cm->items.count();
}


double CF_CM_itemValue(ColorMapH cm, int index)
{
  return cm->items[index].value;
}


int CF_CM_itemColor(ColorMapH cm, int index)
{
  return cm->items[index].color;
}


const char* CF_CM_itemLabel(ColorMapH cm, int index)
{
  return _return_str( cm->items[index].label );
}


void CF_CM_setItemCount(ColorMapH cm, int count)
{
  cm->items.resize(count);
}


void CF_CM_setItemValue(ColorMapH cm, int index, double value)
{
  cm->items[index].value = value;
}


void CF_CM_setItemColor(ColorMapH cm, int index, int color)
{
  cm->items[index].color = color;
}


void CF_CM_setItemLabel(ColorMapH cm, int index, const char* label)
{
  cm->items[index].label = QString::fromUtf8(label);
}


ColorMapH CF_CM_createDefault(double vmin, double vmax)
{
  return new ColorMap(ColorMap::defaultColorMap(vmin, vmax));
}

void CF_CM_clip(ColorMapH cm, int* clipLow, int* clipHigh)
{
  *clipLow = cm->clipLow;
  *clipHigh = cm->clipHigh;
}


void CF_CM_setClip(ColorMapH cm, int clipLow, int clipHigh)
{
  cm->clipLow = clipLow;
  cm->clipHigh = clipHigh;
}


int CF_CM_alpha(ColorMapH cm)
{
  return cm->alpha;
}


void CF_CM_setAlpha(ColorMapH cm, int alpha)
{
  cm->alpha = alpha;
}


int CF_CM_method(ColorMapH cm)
{
  return cm->method;
}


void CF_CM_setMethod(ColorMapH cm, int method)
{
  cm->method = (ColorMap::Method) method;
}
