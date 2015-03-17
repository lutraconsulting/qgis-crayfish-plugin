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


#include "crayfish_colormap.h"

#include <QPainter>
#include <QPixmap>

void ColorMap::dump() const
{
  qDebug("COLOR RAMP: items %d", items.count());
  for (int i = 0; i < items.count(); ++i)
  {
    qDebug("%d:  %f  --  %08x", i, items[i].value, items[i].color);
  }
}


QRgb ColorMap::valueDiscrete(double v) const
{
  if (items.count() == 0)
    return qRgba(0,0,0,0);

  int currentIdx = items.count() / 2; // TODO: keep last used index

  while (currentIdx >= 0 && currentIdx < items.count())
  {
    // Start searching from the last index - assumtion is that neighboring pixels tend to be similar values
    const Item& currentItem = items.value(currentIdx);
    bool valueVeryClose = qAbs(v - currentItem.value) < 0.0000001;

    if (currentIdx != 0 && v <= items.at(currentIdx-1).value)
    {
      currentIdx--;
    }
    else if (v <= currentItem.value || valueVeryClose)
    {
      if (clipLow && currentIdx == 0 && v < currentItem.value)
        return qRgba(0,0,0,0); // clipped - transparent
      return qRgba( qRed(currentItem.color), qGreen(currentItem.color), qBlue(currentItem.color), alpha);
    }
    else
    {
      // Search deeper into the color ramp list
      currentIdx++;
    }
  }

  if (clipHigh)
    return qRgba(0,0,0,0); // clipped - transparent

  const Item& lastItem = items[items.count()-1];
  return qRgba( qRed(lastItem.color), qGreen(lastItem.color), qBlue(lastItem.color), alpha);
}


QRgb ColorMap::valueLinear(double v) const
{
  // interpolate
  int currentIdx = items.count() / 2; // TODO: keep last used index

  while (currentIdx >= 0 && currentIdx < items.count())
  {
    const Item& currentItem = items[currentIdx];
    bool valueVeryClose = qAbs(v - currentItem.value) < 0.0000001;

    if (currentIdx > 0 && v <= items[currentIdx-1].value)
    {
      currentIdx--;
    }
    else if (currentIdx > 0 && (v <= currentItem.value || valueVeryClose))
    {
      // we are at the right interval
      const Item& prevItem = items[currentIdx-1];
      double scale = (v - prevItem.value) / (currentItem.value - prevItem.value);
      int vR = (int)((double) qRed(prevItem.color)   + ((double)(qRed(currentItem.color)   - qRed(prevItem.color)  ) * scale) + 0.5);
      int vG = (int)((double) qGreen(prevItem.color) + ((double)(qGreen(currentItem.color) - qGreen(prevItem.color)) * scale) + 0.5);
      int vB = (int)((double) qBlue(prevItem.color)  + ((double)(qBlue(currentItem.color)  - qBlue(prevItem.color) ) * scale) + 0.5);
      return qRgba(vR, vG, vB, alpha);
    }
    else if ((currentIdx == 0               && ( ( !clipLow  && v <= currentItem.value ) || valueVeryClose ) )
          || (currentIdx == items.count()-1 && ( ( !clipHigh && v >= currentItem.value ) || valueVeryClose ) ) )
    {
      // outside of the range
      return qRgba( qRed(currentItem.color), qGreen(currentItem.color), qBlue(currentItem.color), alpha);
    }
    else if (v > currentItem.value)
    {
      currentIdx++;
    }
    else
    {
      return qRgba(0,0,0,0); // transparent pixel
    }
  }

  return qRgba(0,0,0,0); // transparent pixel
}

QRgb ColorMap::value(double v) const
{
  return method == Linear ? valueLinear(v) : valueDiscrete(v);
}


QPixmap ColorMap::previewPixmap(const QSize& size, double vMin, double vMax)
{
  QPixmap pix(size);
  pix.fill(Qt::white);
  QPainter p(&pix);

  if (items.count() == 0)
  {
    p.drawLine(0,0,size.width()-1,size.height()-1);
    p.drawLine(0,size.height()-1,size.width()-1,0);
  }
  else
  {
    for (int i = 0; i < size.width(); ++i)
    {
      double v = vMin + (vMax-vMin) *  i / (size.width()-1);
      p.setPen(QColor(value(v)));
      p.drawLine(i,0,i,size.height()-1);
    }
  }
  p.end();
  return pix;
}


ColorMap ColorMap::defaultColorMap(double vMin, double vMax)
{
  ColorMap map;
  map.items.append(Item(vMin, qRgb(0,0,255))); // blue
  map.items.append(Item(vMin*0.75+vMax*0.25, qRgb(0,255,255))); // cyan
  map.items.append(Item(vMin*0.50+vMax*0.50, qRgb(0,255,0))); // green
  map.items.append(Item(vMin*0.25+vMax*0.75, qRgb(255,255,0))); // yellow
  map.items.append(Item(vMax, qRgb(255,0,0))); // red
  return map;
}

