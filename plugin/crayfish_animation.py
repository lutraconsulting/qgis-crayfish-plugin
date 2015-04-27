# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2014 Lutra Consulting

# info at lutraconsulting dot co dot uk
# Lutra Consulting
# 23 Chestnut Close
# Burgess Hill
# West Sussex
# RH15 8HN

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os

import crayfish

from PyQt4.QtCore import QSize, QRectF
from PyQt4.QtGui import QImage, QPainter
from PyQt4.QtXml import QDomDocument

from qgis.core import *

from crayfish_gui_utils import timeToString


def animation(l, time_from_to, w,h, imgfile, layers=None, extent=None, crs=None, template_path=None, progress_fn=None):

  dpi = 96
  dataset = l.currentDataSet()
  count = dataset.output_count()
  if time_from_to is not None:
    time_from, time_to = time_from_to
  else:
    time_from, time_to = dataset.output(0).time(), dataset.output(dataset.output_count()-1).time()

  for i,o in enumerate(dataset.outputs()):

    if progress_fn:
      progress_fn(i, count)

    if o.time() < time_from or o.time() > time_to:
      continue

    l.current_output_time = o.time()

    mr = QgsMapRenderer()
    # setup map parameters
    mr.setExtent(l.extent() if extent is None else extent)  # only used when creating new composer map??
    mr.setLayerSet([l.id()] if layers is None else layers)
    mr.setOutputSize(QSize(w,h), dpi) # only used when creating new composer map
    if crs is not None:
      mr.setDestinationCrs(crs)
      mr.setProjectionsEnabled(True)

    c = QgsComposition(mr)
    if template_path is None:
      cm = prepare_composition(c, w, h, dpi, o.time())
    else:
      prepare_composition_from_template(c, template_path, o.time())


    image = QImage(QSize(w, h), QImage.Format_RGB32)
    imagePainter = QPainter(image)
    sourceArea = QRectF(0, 0, c.paperWidth(), c.paperHeight())
    targetArea = QRectF(0, 0, w, h)
    c.render(imagePainter, targetArea, sourceArea)
    imagePainter.end()

    image.save(imgfile % (i+1))

  if progress_fn:
    progress_fn(count, count)


def prepare_composition_from_template(c, template_path, time):

    document = QDomDocument()
    document.setContent(open(template_path).read())
    c.loadFromTemplate(document)

    timeItem = c.getComposerItemById("time")
    if timeItem is not None:
      timeItem.setText(timeToString(time))


def prepare_composition(c, w,h, dpi, time):

    c.setPlotStyle(QgsComposition.Print)
    c.setPaperSize(w*25.4/dpi, h*25.4/dpi)
    c.setPrintResolution(dpi)

    composerMap = QgsComposerMap(c, 0, 0, c.paperWidth(), c.paperHeight())
    c.addItem(composerMap)

    composerLabel = QgsComposerLabel(c)
    composerLabel.setText(timeToString(time))
    composerLabel.adjustSizeToText()
    c.addItem(composerLabel)

    return composerMap

def images_to_video(tmp_img_dir="/tmp/vid/p*.png", output_file="/tmp/vid/test.avi", fps=10):
    cmd = 'mencoder "mf://%s" -mf fps=%d -o %s -ovc lavc' % (tmp_img_dir, fps, output_file)
    res = os.system(cmd)
    return res == 0
