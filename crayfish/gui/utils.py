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
import platform

from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtCore import *
from qgis.core import *
from qgis.PyQt import uic
from qgis.utils import iface
qgis_message_bar = iface.messageBar()

from .install_helper import downloadFfmpeg

def float_safe(txt):
    """ convert to float, return 0 if conversion is not possible """
    try:
        return float(txt)
    except ValueError:
        return 0.


def time_to_string(layer, time):  # time is in hours
    if not layer or layer.type() != QgsMapLayer.LayerType.MeshLayer:
        raise Exception("unable to format time " + time)
    return layer.formatTime(time)

def mesh_layer_active_dataset_group_with_maximum_timesteps(layer):
    """ returns active dataset group with maximum datasets and the number of datasets """
    group_index = None
    timesteps = 0

    if layer and layer.dataProvider() and layer.type() == QgsMapLayer.LayerType.MeshLayer:
        rendererSettings = layer.rendererSettings()
        group_index = rendererSettings.activeScalarDatasetGroup()

        if group_index >= 0:
            timesteps = layer.dataProvider().datasetCount(group_index)

        vector_group_index = rendererSettings.activeVectorDatasetGroup()
        if vector_group_index>=0:
            avd_timesteps = layer.dataProvider().datasetCount(vector_group_index)
            if avd_timesteps > timesteps:
                group_index = vector_group_index

    return group_index

def load_ui(name):
    ui_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'ui',
                          name + '.ui')
    return uic.loadUiType(ui_file)

# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def handle_ffmpeg(dialog):
    if dialog.radFfmpegSystem.isChecked():
        ffmpeg_bin = "ffmpeg"
        # debian systems use avconv (fork of ffmpeg)
        if which(ffmpeg_bin) is None:
            ffmpeg_bin = "avconv"
    else:
        ffmpeg_bin = dialog.editFfmpegPath.text()  # custom path

    if which(ffmpeg_bin) is None:
        QMessageBox.warning(dialog, "FFmpeg missing",
                            "The tool for video creation (<a href=\"http://en.wikipedia.org/wiki/FFmpeg\">FFmpeg</a>) "
                            "is missing. Please check your FFmpeg configuration in <i>Video</i> tab.<p>"
                            "<b>Windows users:</b> Let Crayfish plugin download FFmpeg automatically or "
                            "<a href=\"https://download.osgeo.org/osgeo4w/x86_64/release/ffmpeg/\">download</a> FFmpeg manually "
                            "and configure path in <i>Video</i> tab to point to ffmpeg.exe.<p>"
                            "<b>Linux users:</b> Make sure FFmpeg is installed in your system - usually a package named "
                            "<tt>ffmpeg</tt>. On Debian/Ubuntu systems FFmpeg was replaced by Libav (fork of FFmpeg) "
                            "- use <tt>libav-tools</tt> package.<p>"
                            "<b>MacOS users:</b> Make sure FFmpeg is installed in your system <tt>brew install ffmpeg</tt>")

        if platform.system() != 'Windows':
            return

        # special treatment for Windows users!
        # offer automatic download and installation from Lutra web.
        # Official distribution is not used because:
        # 1. packages use 7zip compression (need extra software)
        # 2. packages contain extra binaries we do not need

        reply = QMessageBox.question(dialog,
                                     'Download FFmpeg',
                                     "Would you like to download and auto-configure FFmpeg?\n\n"
                                     "The download may take some time (~13 MB).\n"
                                     "FFmpeg will be downloaded to Crayfish plugin's directory.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if reply != QMessageBox.StandardButton.Yes:
            return

        ffmpeg_bin = downloadFfmpeg(dialog)
        if not ffmpeg_bin:
            return

        # configure the path automatically
        dialog.radFfmpegCustom.setChecked(True)
        dialog.editFfmpegPath.setText(ffmpeg_bin)
        s = QSettings()
        s.beginGroup("crayfishViewer/trace_animation")
        s.setValue("ffmpeg", "custom")
        s.setValue("ffmpeg_path", ffmpeg_bin)

    return ffmpeg_bin

def isLayer3d(layer):
    if layer is None:
        return False

    if layer.type()!=QgsMapLayerType.MeshLayer:
        return

    dataProvider=layer.dataProvider()
    if dataProvider is None:
        return False

    datasetGroupCount=dataProvider.datasetGroupCount()
    for i in range(datasetGroupCount):
        meta=dataProvider.datasetGroupMetadata(i)
        if meta.dataType()==QgsMeshDatasetGroupMetadata.DataType.DataOnVolumes:
            return True

    return False

def isLayer1d(layer):
    if layer is None:
        return False

    if layer.type()!=QgsMapLayerType.MeshLayer:
        return

    dataProvider=layer.dataProvider()
    if dataProvider.contains(QgsMesh.ElementType.Edge):
        return True
    else:
        return False

def isLayer2d(layer):
    if layer is None:
        return False

    if layer.type()!=QgsMapLayerType.MeshLayer:
        return
    
    dataProvider = layer.dataProvider()
    if dataProvider.contains(QgsMesh.ElementType.Face):
        return True
    else:
        return False
