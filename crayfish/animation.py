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

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtXml import QDomDocument

from qgis.core import *
from .gui.utils import time_to_string, mesh_layer_active_dataset_group_with_maximum_timesteps


def animation(cfg, progress_fn=None):
    dpi = 96
    l = cfg['layer']
    w, h = cfg['img_size']
    imgfile = cfg['tmp_imgfile']
    layers = cfg['layers'] if 'layers' in cfg else [l.id()]
    extent = cfg['extent'] if 'extent' in cfg else l.extent()
    crs = cfg['crs'] if 'crs' in cfg else None
    dataset_group_index = mesh_layer_active_dataset_group_with_maximum_timesteps(l)
    assert (dataset_group_index)
    count = l.dataProvider().datasetCount(dataset_group_index)
    assert (count > 2)

    if 'time' in cfg:
        time_from, time_to = cfg['time']
    else:
        time_from = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, 0)).time()
        time_to = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, count - 1)).time()

    # store default values
    default_rs = l.rendererSettings()

    # animate
    imgnum = 0
    for i in range(count):

        if progress_fn:
            progress_fn(i, count)

        time = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, i)).time()
        if time < time_from or time > time_to:
            continue

        # Set to render next timesteps
        rs = l.rendererSettings()
        asd = rs.activeScalarDataset()
        if asd.isValid():
            rs.setActiveScalarDataset(QgsMeshDatasetIndex(asd.group(), i))
        avd = rs.activeVectorDataset()
        if avd.isValid():
            rs.setActiveVectorDataset(QgsMeshDatasetIndex(avd.group(), i))
        l.setRendererSettings(rs)

        # Prepare layout
        layout = QgsPrintLayout(QgsProject.instance())
        layout.initializeDefaults()
        layout.setName('crayfish')

        layout_page = QgsLayoutItemPage(layout)
        layout_page.setPageSize(QgsLayoutSize(w, h, QgsUnitTypes.LayoutPixels))
        layout_page.decodePageOrientation('Portrait')

        paper = QSize(w, h)
        # paper = QSize(w*25.4/dpi, h*25.4/dpi) # mm

        layoutcfg = cfg['layout']
        if layoutcfg['type'] == 'file':
            prepare_composition_from_template(layout, cfg['layout']['file'], time)
            # when using composition from template, match video's aspect ratio to paper size
            # by updating video's width (keeping the height)
            aspect = paper.width() / paper.height()
            w = int(round(aspect * h))
        else:  # type == 'default'
            prepare_composition(layout, paper, time, layoutcfg, extent, layers, crs)

        imgnum += 1
        fname = imgfile % imgnum

        layout_exporter = QgsLayoutExporter(layout)
        image_export_settings = QgsLayoutExporter.ImageExportSettings()
        # image_export_settings.dpi = dpi
        image_export_settings.imageSize = QSize(w, h)

        res = layout_exporter.exportToImage(os.path.abspath(fname), image_export_settings)
        if res != QgsLayoutExporter.Success:
            raise RuntimeError()

    if progress_fn:
        progress_fn(count, count)

    # restore default
    l.setRendererSettings(default_rs)


def composition_set_time(c, time):
    for i in c.items():
        if isinstance(i, QgsLayoutItemLabel) and i.id() == "time":
            txt = time_to_string(time)
            i.setText(txt)


def prepare_composition_from_template(layout, template_path, time):
    document = QDomDocument()
    with open(template_path) as f:
        document.setContent(f.read())
    context = QgsReadWriteContext()
    context.setPathResolver(QgsProject.instance().pathResolver())
    context.setProjectTranslator(QgsProject.instance())
    layout.readLayoutXml(document.documentElement(), document, context)
    composition_set_time(layout, time)


def set_composer_item_label(item, itemcfg):
    item.setBackgroundEnabled(itemcfg['bg'])
    item.setBackgroundColor(itemcfg['bg_color'])
    item.setFont(itemcfg['text_font'])
    item.setFontColor(itemcfg['text_color'])


def set_item_pos(item, posindex, paper, is_legend=False):
    cw, ch = paper.width(), paper.height()
    r = item.rect()
    # if is_legend:
    #    r = item.paintAndDetermineSize(None)

    if posindex == 0:  # top-left
        item.attemptMove(QgsLayoutPoint(0, 0))
    elif posindex == 1:  # top-right
        item.attemptMove(QgsLayoutPoint(cw - r.width(), 0, QgsUnitTypes.LayoutPixels))
    elif posindex == 2:  # bottom-left
        item.attemptMove(QgsLayoutPoint(0, ch - r.height(), QgsUnitTypes.LayoutPixels))
    else:  # bottom-right
        item.attemptMove(QgsLayoutPoint(cw - r.width(), ch - r.height(), QgsUnitTypes.LayoutPixels))


def prepare_composition(layout, paper, time, layoutcfg, extent, layers, crs):
    layout_map = QgsLayoutItemMap(layout)
    layout_map.attemptResize(QgsLayoutSize(paper.width(), paper.height(), QgsUnitTypes.LayoutPixels))
    layout_map.attemptMove(QgsLayoutPoint(0, 0))
    layout_map.setLayers(layers)
    if crs is not None:
        layout_map.setCrs(crs)
    layout_map.setExtent(extent)
    layout_map.refresh()
    layout.setReferenceMap(layout_map)
    layout.addLayoutItem(layout_map)

    if 'title' in layoutcfg:
        cTitle = QgsLayoutItemLabel(layout)
        cTitle.setId('title')
        layout.addLayoutItem(cTitle)

        set_composer_item_label(cTitle, layoutcfg['title'])
        cTitle.setText(layoutcfg['title']['label'])
        cTitle.setHAlign(Qt.AlignCenter)
        cTitle.setVAlign(Qt.AlignCenter)
        cTitle.adjustSizeToText()
        cTitle.attemptMove(QgsLayoutPoint((paper.width() - cTitle.rect().width()) / 2, cTitle.rect().height(),
                                          QgsUnitTypes.LayoutPixels))

    if 'time' in layoutcfg:
        cTime = QgsLayoutItemLabel(layout)
        cTime.setId('time')
        layout.addLayoutItem(cTime)

        set_composer_item_label(cTime, layoutcfg['time'])
        composition_set_time(layout, time)
        cTime.adjustSizeToText()
        set_item_pos(cTime, layoutcfg['time']['position'], paper)

    if 'legend' in layoutcfg:
        cLegend = QgsLayoutItemLegend(layout)
        cLegend.setId('legend')
        cLegend.setLinkedMap(layout_map)
        layout.addLayoutItem(cLegend)

        itemcfg = layoutcfg['legend']
        cLegend.setBackgroundEnabled(itemcfg['bg'])
        cLegend.setBackgroundColor(itemcfg['bg_color'])
        cLegend.setTitle('')
        for s in [QgsLegendStyle.Title,
                  QgsLegendStyle.Group,
                  QgsLegendStyle.Subgroup,
                  QgsLegendStyle.SymbolLabel]:
            cLegend.setStyleFont(s, itemcfg['text_font'])
        cLegend.setFontColor(itemcfg['text_color'])

        cLegend.adjustBoxSize()
        set_item_pos(cLegend, itemcfg['position'], paper, True)


def images_to_video(tmp_img_dir="/tmp/vid/%03d.png", output_file="/tmp/vid/test.avi", fps=10, qual=1,
                    ffmpeg_bin="ffmpeg"):
    if qual == 0:  # lossless
        opts = ["-vcodec", "ffv1"]
    else:
        bitrate = 10000 if qual == 1 else 2000
        opts = ["-vcodec", "mpeg4", "-b", str(bitrate) + "K"]

    # if images do not start with 1: -start_number 14
    cmd = [ffmpeg_bin, "-f", "image2", "-framerate", str(fps), "-i", tmp_img_dir]
    cmd += opts
    cmd += ["-r", str(fps), "-f", "avi", "-y", output_file]

    f = tempfile.NamedTemporaryFile(prefix="crayfish", suffix=".txt")
    f.write(str.encode(" ".join(cmd) + "\n\n"))

    # stdin redirection is necessary in some cases on Windows
    res = subprocess.call(cmd, stdin=subprocess.PIPE, stdout=f, stderr=f)
    if res != 0:
        f.delete = False  # keep the file on error

    return res == 0, f.name
