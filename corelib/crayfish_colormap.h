/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2014 Lutra Consulting

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

#ifndef CRAYFISH_COLORMAP_H
#define CRAYFISH_COLORMAP_H

#include <QColor>
#include <QVector>

class QPixmap;
class QSize;


/** keep information about how data should be rendered */
struct ColorMap
{
  struct Item
  {
    Item(double v = 0, QRgb c = 0): value(v), color(c) {}

    double value;
    QRgb color;
    QString label;
  };

  enum Method { Linear, Discrete } method;

  QVector<Item> items;
  int alpha;
  bool clipLow;  //!< values lower than first item's value will not be painted
  bool clipHigh; //!< values higher than last item's value will not be painted

  ColorMap() : method(Linear), alpha(255), clipLow(false), clipHigh(false) {}

  void clearItems() { items.clear(); }
  void addItem(const Item& item) { items.append(item); }
  void removeItem(int index) { items.remove(index); }
  void moveItem(int indexOld, int indexNew) { items.insert(indexNew, items.value(indexOld)); items.remove(indexNew > indexOld ? indexOld : indexOld+1); }
  Item& item(int index) { return items[index]; }

  void dump() const;

  QRgb value(double v) const;

  QPixmap previewPixmap(const QSize& size, double vMin, double vMax);

  /** default "cold-to-hot" color map */
  static ColorMap defaultColorMap(double vMin, double vMax);

protected:
  QRgb valueDiscrete(double v) const;
  QRgb valueLinear(double v) const;
};

#include <QMetaType>
Q_DECLARE_METATYPE(ColorMap)  // make available for QVariant

#endif // CRAYFISH_COLORMAP_H
