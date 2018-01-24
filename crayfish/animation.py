# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2016 Lutra Consulting

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
import subprocess
import tempfile

from PyQt4.QtCore import QSize, QRectF, Qt
from PyQt4.QtGui import QImage, QPainter
from PyQt4.QtXml import QDomDocument

from qgis.core import *

from .gui.utils import time_to_string


def animation(cfg, progress_fn=None):

  dpi = 96
  l = cfg['layer']
  w,h = cfg['img_size']
  imgfile = cfg['tmp_imgfile']
  layers = cfg['layers'] if 'layers' in cfg else [l.id()]
  extent = cfg['extent'] if 'extent' in cfg else l.extent()
  crs = cfg['crs'] if 'crs' in cfg else None
  dataset = l.currentDataSet()
  count = dataset.output_count()
  if 'time' in cfg:
    time_from, time_to = cfg['time']
  else:
    time_from, time_to = dataset.output(0).time(), dataset.output(dataset.output_count()-1).time()

  imgnum = 0
  for i,o in enumerate(dataset.outputs()):

    if progress_fn:
      progress_fn(i, count)

    if o.time() < time_from or o.time() > time_to:
      continue

    l.current_output_time = o.time()

    mr = QgsMapRenderer()
    # setup map parameters
    mr.setExtent(extent)  # only used when creating new composer map??
    mr.setLayerSet(layers)
    mr.setOutputSize(QSize(w,h), dpi) # only used when creating new composer map
    if crs is not None:
      mr.setDestinationCrs(crs)
      mr.setProjectionsEnabled(True)

    c = prep_comp(cfg, mr, o.time())

    # when using composition from template, match video's aspect ratio to paper size
    # by updating video's width (keeping the height)
    if cfg['layout']['type'] == 'file':
        aspect = c.paperWidth() / c.paperHeight()
        w = int(round(aspect * h))

    image = QImage(QSize(w, h), QImage.Format_RGB32)
    image.fill(0)
    imagePainter = QPainter(image)
    sourceArea = QRectF(0, 0, c.paperWidth(), c.paperHeight())
    targetArea = QRectF(0, 0, w, h)
    c.render(imagePainter, targetArea, sourceArea)
    imagePainter.end()

    imgnum += 1
    image.save(imgfile % imgnum)

  if progress_fn:
    progress_fn(count, count)


def prep_comp(cfg, mr, time):
    layoutcfg = cfg['layout']
    w,h = mr.outputSize().width(), mr.outputSize().height()
    dpi = mr.outputDpi()
    c = QgsComposition(mr)
    if layoutcfg['type'] == 'file':
        prepare_composition_from_template(c, cfg['layout']['file'], time)
    else:  # type == 'default'
        cm = prepare_composition(c, w, h, dpi, time, layoutcfg)
    return c


def composition_set_time(c, time, frmt=0):
    timeItem = c.getComposerItemById("time")
    if timeItem is not None:
        if frmt == 0: # hh:mm:ss
            txt = time_to_string(time)
        else:  # hh.hhh
            txt = "%06.3f" % time
        timeItem.setText(txt)


def prepare_composition_from_template(c, template_path, time):

    document = QDomDocument()
    document.setContent(open(template_path).read())
    c.loadFromTemplate(document)

    c.setPlotStyle(QgsComposition.Print)

    composition_set_time(c, time)


def set_composer_item_label(item, itemcfg):
    item.setBackgroundEnabled(itemcfg['bg'])
    item.setBackgroundColor(itemcfg['bg_color'])
    item.setFont(itemcfg['text_font'])
    item.setFontColor(itemcfg['text_color'])


def set_item_pos(item, posindex, c, is_legend=False):
    cw, ch = c.paperWidth(), c.paperHeight()
    r = item.rect()
    if is_legend:
        r = item.paintAndDetermineSize(None)

    if posindex == 0:  # top-left
        item.setItemPosition(0, 0)
    elif posindex == 1: # top-right
        item.setItemPosition(cw-r.width(),0)
    elif posindex == 2: # bottom-left
        item.setItemPosition(0, ch-r.height())
    else:  # bottom-right
        item.setItemPosition(cw-r.width(), ch-r.height())


def prepare_composition(c, w,h, dpi, time, layoutcfg):

    c.setPlotStyle(QgsComposition.Print)
    c.setPaperSize(w*25.4/dpi, h*25.4/dpi)
    c.setPrintResolution(dpi)

    composerMap = QgsComposerMap(c, 0, 0, c.paperWidth(), c.paperHeight())
    c.addItem(composerMap)

    if 'title' in layoutcfg:
        cTitle = QgsComposerLabel(c)
        cTitle.setId('title')
        c.addItem(cTitle)

        set_composer_item_label(cTitle, layoutcfg['title'])
        cTitle.setText(layoutcfg['title']['label'])
        cTitle.setHAlign(Qt.AlignCenter)
        cTitle.setVAlign(Qt.AlignCenter)
        cTitle.adjustSizeToText()
        cTitle.setItemPosition(0,0, c.paperWidth(), cTitle.rect().height())

    if 'time' in layoutcfg:
        cTime = QgsComposerLabel(c)
        cTime.setId('time')
        c.addItem(cTime)

        set_composer_item_label(cTime, layoutcfg['time'])
        composition_set_time(c, time, layoutcfg['time']['format'])
        cTime.adjustSizeToText()
        set_item_pos(cTime, layoutcfg['time']['position'], c)

    if 'legend' in layoutcfg:
        cLegend = QgsComposerLegend(c)
        cLegend.setId('legend')
        cLegend.setComposerMap(composerMap)
        c.addItem(cLegend)

        itemcfg = layoutcfg['legend']
        cLegend.setBackgroundEnabled(itemcfg['bg'])
        cLegend.setBackgroundColor(itemcfg['bg_color'])
        cLegend.setTitle('')
        for s in [QgsComposerLegendStyle.Title,
                  QgsComposerLegendStyle.Group,
                  QgsComposerLegendStyle.Subgroup,
                  QgsComposerLegendStyle.SymbolLabel]:
            cLegend.setStyleFont(s, itemcfg['text_font'])
        cLegend.setFontColor(itemcfg['text_color'])

        cLegend.adjustBoxSize()
        set_item_pos(cLegend, itemcfg['position'], c, True)

    return composerMap



def images_to_video(tmp_img_dir= "/tmp/vid/%03d.png", output_file="/tmp/vid/test.avi", fps=10, qual=1, ffmpeg_bin="ffmpeg"):
    if qual == 0: # lossless
        opts = ["-vcodec", "ffv1"]
    else:
        bitrate = 10000 if qual == 1 else 2000
        opts = ["-vcodec", "mpeg4", "-b", str(bitrate) + "K"]

    # if images do not start with 1: -start_number 14
    cmd = [ffmpeg_bin, "-f", "image2", "-framerate", str(fps), "-i", tmp_img_dir]
    cmd += opts
    cmd += ["-r", str(fps), "-f", "avi", "-y", output_file]

    f = tempfile.NamedTemporaryFile(prefix="crayfish",suffix=".txt")
    f.write(unicode(cmd).encode('utf8') + "\n\n")

    # stdin redirection is necessary in some cases on Windows
    res = subprocess.call(cmd, stdin=subprocess.PIPE, stdout=f, stderr=f)
    if res != 0:
        f.delete = False  # keep the file on error

    return res == 0, f.name
