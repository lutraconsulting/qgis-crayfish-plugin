# -*- coding: utf-8 -*-
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
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QStyleOptionGraphicsItem
from PyQt5.QtXml import QDomDocument

from qgis.core import *
from qgis._3d import *
from .gui.utils import mesh_layer_active_dataset_group_with_maximum_timesteps


def _page_size(layout):
    """ returns QgsLayoutSize """
    main_page = layout.pageCollection().page(0)
    return main_page.pageSize()


def animation(cfg, progress_fn=None):
    dpi = 96
    cfg["dpi"] = dpi
    l = cfg['layer']
    w, h = cfg['img_size']
    imgfile = cfg['tmp_imgfile']
    layers = cfg['layers'] if 'layers' in cfg else [l.id()]
    extent = cfg['extent'] if 'extent' in cfg else l.extent()
    crs = cfg['crs'] if 'crs' in cfg else None
    dataset_group_index = mesh_layer_active_dataset_group_with_maximum_timesteps(l)
    assert (dataset_group_index is not None)
    count = l.dataProvider().datasetCount(dataset_group_index)
    assert (count > 2)

    if 'time' in cfg:
        time_from, time_to = cfg['time']
    else:
        time_from = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, 0)).time()
        time_to = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, count - 1)).time()


    # count actual timesteps to animate
    act_count = 0
    for i in range(count):
        time = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, i)).time()
        if time_from <= time <= time_to:
            act_count += 1

    # Reference time
    referenceTime=l.temporalProperties().referenceTime()

    # animate
    imgnum = 0
    for i in range(count):

        if progress_fn:
            progress_fn(imgnum, act_count)

        time = l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, i)).time()
        if time < time_from or time > time_to:
            continue

        currentTime=referenceTime.addMSecs(int(time)*3600*1000)
        formattedTime=currentTime.toString("yyyy-MM-dd HH:mm:ss")

        # Prepare layout
        layout = QgsPrintLayout(QgsProject.instance())
        layout.initializeDefaults()
        layout.setName('crayfish')

        layoutcfg = cfg['layout']
        if layoutcfg['type'] == 'file':
            prepare_composition_from_template(layout, cfg['layout']['file'], formattedTime)
            # when using composition from template, match video's aspect ratio to paper size
            # by updating video's width (keeping the height)
            aspect = _page_size(layout).width() / _page_size(layout).height()
            w = int(round(aspect * h))
        else:  # type == 'default'
            layout.renderContext().setDpi(dpi)
            layout.setUnits(QgsUnitTypes.LayoutMillimeters)
            main_page = layout.pageCollection().page(0)
            main_page.setPageSize(QgsLayoutSize(w * 25.4 / dpi, h * 25.4 / dpi, QgsUnitTypes.LayoutMillimeters))
            prepare_composition(layout, formattedTime, cfg, layoutcfg, extent, layers, crs)

        #Set timerange for map layouts
        timeRange = QgsDateTimeRange(currentTime, currentTime.addSecs(1))
        for layoutItem in layout.items():
            if isinstance(layoutItem, QgsLayoutItemMap): # or isinstance(layoutItem, QgsLayoutItem3DMap): (commented because not found in API)
                layoutItem.setTemporalRange(timeRange)

        imgnum += 1
        fname = imgfile % imgnum
        layout_exporter = QgsLayoutExporter(layout)
        image_export_settings = QgsLayoutExporter.ImageExportSettings()
        image_export_settings.dpi = dpi
        image_export_settings.imageSize = QSize(w, h)
        res = layout_exporter.exportToImage(os.path.abspath(fname), image_export_settings)
        if res != QgsLayoutExporter.Success:
            raise RuntimeError()

    if progress_fn:
        progress_fn(count, count)


def traceAnimation(cfg, progress_fn=None):
    dpi = 96
    cfg["dpi"] = dpi
    l = cfg['layer']
    m = cfg['map_settings']
    w, h = cfg['img_size']
    fps = cfg['fps']
    duration = cfg['duration']
    imgfile = cfg['tmp_imgfile']
    count = cfg['count']
    maxSpeed = cfg['max_speed']
    lifeTime = cfg['life_time']
    color = cfg['color']
    colorLayerSettings=cfg['colorLayerSettings']
    size = cfg['size']
    tailFactor=cfg['tail_factor']
    minTailLenght=cfg['min_tail_leght']
    persistence=cfg['persistence']

    #First, we need to obtain the image of the map without the particles and without the vector dataset rendered

    # store original settings
    original_rs = l.rendererSettings()

    tmpSettings=l.rendererSettings()
    tmpSettings.setActiveVectorDatasetGroup( -1 )
    l.setRendererSettings(tmpSettings)

    m.setOutputSize( QSize(w,h) )
    underLayerRenderer=QgsMapRendererParallelJob(m)

    underLayerRenderer.start()
    underLayerRenderer.waitForFinished()

    underLayerImage=underLayerRenderer.renderedImage()

    # restore original settings
    l.setRendererSettings(original_rs)

    # create an initialize the particles Renderer
    renderContext=QgsRenderContext.fromMapSettings(m)
    particlesRenderer=QgsMeshVectorTraceAnimationGenerator(l, renderContext)

    particlesRenderer.setFPS(fps)
    particlesRenderer.setMaxSpeedPixel(maxSpeed)
    particlesRenderer.setParticlesLifeTime(lifeTime)
    particlesRenderer.seedRandomParticles(count)
    if not colorLayerSettings:
        particlesRenderer.setParticlesColor(color)
    particlesRenderer.setParticlesSize(size)
    particlesRenderer.setTailFactor(tailFactor)
    particlesRenderer.setMinimumTailLength(minTailLenght)
    particlesRenderer.setTailPersitence(persistence)

    framesCount=duration*fps
    #start to increment and generate image
    for i in range(framesCount):

        if progress_fn:
            progress_fn(i, framesCount)

        particleImage = particlesRenderer.imageRendered()
        renderImage=underLayerImage.copy()
        painter=QPainter()
        painter.begin(renderImage)
        painter.drawImage(0,0,particleImage)
        painter.end()
        renderImage.save(imgfile% (i+1),"PNG")
    if progress_fn:
        progress_fn(framesCount, framesCount)

def composition_set_time(c, formattedTime):
    for i in c.items():
        if isinstance(i, QgsLayoutItemLabel) and i.id() == "time":
            i.setText(formattedTime)


def prepare_composition_from_template(layout, template_path, formattedTime):
    document = QDomDocument()
    with open(template_path) as f:
        document.setContent(f.read())
    context = QgsReadWriteContext()
    context.setPathResolver(QgsProject.instance().pathResolver())
    context.setProjectTranslator(QgsProject.instance())
    layout.readLayoutXml(document.documentElement(), document, context)
    composition_set_time(layout, formattedTime)


def set_composer_item_label(item, itemcfg):
    item.setBackgroundEnabled(itemcfg['bg'])
    item.setBackgroundColor(itemcfg['bg_color'])
    item.setFont(itemcfg['text_font'])
    item.setFontColor(itemcfg['text_color'])


class CFItemPosition:
    TOP_CENTER = -1
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3


def set_item_pos(item, posindex, layout):
    page_size = _page_size(layout)
    r = item.sizeWithUnits()
    assert (r.units() == QgsUnitTypes.LayoutMillimeters)
    assert (page_size.units() == QgsUnitTypes.LayoutMillimeters)

    if posindex == CFItemPosition.TOP_CENTER: # top-center
        item.attemptMove(QgsLayoutPoint((page_size.width() - r.width()) / 2, r.height(), QgsUnitTypes.LayoutMillimeters))
    elif posindex == CFItemPosition.TOP_LEFT:  # top-left
        item.attemptMove(QgsLayoutPoint(0, 0))
    elif posindex == CFItemPosition.TOP_RIGHT:  # top-right
        item.attemptMove(QgsLayoutPoint(page_size.width() - r.width(), 0, QgsUnitTypes.LayoutMillimeters))
    elif posindex == CFItemPosition.BOTTOM_LEFT:  # bottom-left
        item.attemptMove(QgsLayoutPoint(0, page_size.height() - r.height(), QgsUnitTypes.LayoutMillimeters))
    else: # bottom-right
        item.attemptMove(QgsLayoutPoint(page_size.width() - r.width(), page_size.height() - r.height(), QgsUnitTypes.LayoutMillimeters))


def fix_legend_box_size(cfg, legend):
    # adjustBoxSize() does not work without
    # call of the paint() function
    w, h = cfg['img_size']
    dpi = cfg['dpi']

    image = QImage(w, h, QImage.Format_ARGB32 )
    image.setDevicePixelRatio(dpi)
    p = QPainter(image)
    s = QStyleOptionGraphicsItem()
    legend.paint(p, s, None)
    p.end()

    # Now we can adjust box size
    legend.adjustBoxSize()


def prepare_composition(layout, time, cfg, layoutcfg, extent, layers, crs):
    layout_map = QgsLayoutItemMap(layout)
    layout_map.attemptResize(_page_size(layout))
    set_item_pos(layout_map, CFItemPosition.TOP_LEFT, layout)
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
        set_item_pos(cTitle, CFItemPosition.TOP_CENTER, layout)

    if 'time' in layoutcfg:
        cTime = QgsLayoutItemLabel(layout)
        cTime.setId('time')
        layout.addLayoutItem(cTime)

        set_composer_item_label(cTime, layoutcfg['time'])
        composition_set_time(layout, time)
        cTime.adjustSizeToText()
        set_item_pos(cTime, layoutcfg['time']['position'], layout)

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

        fix_legend_box_size(cfg, cLegend)
        set_item_pos(cLegend, itemcfg['position'], layout)


def images_to_video(tmp_img_dir="/tmp/vid/%05d.png", output_file="/tmp/vid/test.avi", fps=10, qual=1,
                    ffmpeg_bin="ffmpeg", keep_intermediate_images=False):
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
    if (res != 0) or keep_intermediate_images:
        f.delete = False  # keep the file on error or when defined to keep

    return res == 0, f.name
