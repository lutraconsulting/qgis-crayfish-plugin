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

import platform
import os
import shutil
import tempfile

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qgis.core import *

from ..animation import animation, images_to_video
from .utils import load_ui, time_to_string, mesh_layer_active_dataset_group_with_maximum_timesteps
from .install_helper import downloadFfmpeg

uiDialog, qtBaseClass = load_ui('crayfish_animation_dialog_widget')


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


class CrayfishAnimationDialog(qtBaseClass, uiDialog):

    def __init__(self, iface, parent=None):

        qtBaseClass.__init__(self)
        uiDialog.__init__(self)
        self.setupUi(self)

        self.l = iface.activeLayer()
        self.r = iface.mapCanvas()

        dataset_group_index = mesh_layer_active_dataset_group_with_maximum_timesteps(self.l)
        self.populateTimes(self.cboStart, dataset_group_index)
        self.populateTimes(self.cboEnd, dataset_group_index)
        self.cboStart.setCurrentIndex(0)
        self.cboEnd.setCurrentIndex(self.cboEnd.count()-1)

        defprops = { 'text_color' : QColor(0,0,0), 'text_font' : QFont(), 'bg' : False, 'bg_color' : QColor(255,255,255) }
        titleprops = defprops.copy()
        titleprops['type'] = 'title'
        titleprops['label'] = ''
        timeprops = defprops.copy()
        timeprops['type'] = 'time'
        timeprops['format'] = 0
        timeprops['position'] = 3
        legendprops = defprops.copy()
        legendprops['type'] = 'legend'
        legendprops['position'] = 2
        self.widgetTitleProps.setProps(titleprops)
        self.widgetTimeProps.setProps(timeprops)
        self.widgetLegendProps.setProps(legendprops)

        self.restoreDefaults()

        self.buttonBox.accepted.connect(self.onOK)
        self.btnBrowseOutput.clicked.connect(self.browseOutput)
        self.btnBrowseTemplate.clicked.connect(self.browseTemplate)
        self.btnBrowseFfmpegPath.clicked.connect(self.browseFfmpegPath)

    def populateTimes(self, cbo, dataset_group_index):
        cbo.clear()
        if dataset_group_index:
            for i in range(self.l.dataProvider().datasetCount(dataset_group_index)):
                meta = self.l.dataProvider().datasetMetadata(QgsMeshDatasetIndex(dataset_group_index, i))
                cbo.addItem(time_to_string(meta.time()), meta.time())

    def browseOutput(self):
        settings = QSettings()
        lastUsedDir = settings.value("crayfishViewer/lastFolder")
        filename, _ = QFileDialog.getSaveFileName(self, "Output file", lastUsedDir, "AVI files (*.avi)")
        if len(filename) == 0:
            return

        self.editOutput.setText(filename)
        settings.setValue("crayfishViewer/lastFolder", filename)


    def browseTemplate(self):
        settings = QSettings()
        lastUsedDir = settings.value("crayfishViewer/lastFolder")
        filename, _ = QFileDialog.getOpenFileName(self, "Template file (.qpt)", lastUsedDir, "QGIS templates (*.qpt)")
        if len(filename) == 0:
            return

        self.editTemplate.setText(filename)
        settings.setValue("crayfishViewer/lastFolder", filename)

    def browseFfmpegPath(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Path to FFmpeg tool", '', "FFmpeg (ffmpeg ffmpeg.exe avconv avconv.exe)")
        if len(filename) == 0:
            return
        self.editFfmpegPath.setText(filename)


    def onOK(self):

        if self.radFfmpegSystem.isChecked():
            ffmpeg_bin = "ffmpeg"
            # debian systems use avconv (fork of ffmpeg)
            if which(ffmpeg_bin) is None:
                ffmpeg_bin = "avconv"
        else:
            ffmpeg_bin = self.editFfmpegPath.text()  # custom path

        if which(ffmpeg_bin) is None:
            QMessageBox.warning(self, "FFmpeg missing",
                "The tool for video creation (<a href=\"http://en.wikipedia.org/wiki/FFmpeg\">FFmpeg</a>) "
                "is missing. Please check your FFmpeg configuration in <i>Video</i> tab.<p>"
                "<b>Windows users:</b> Let Crayfish plugin download FFmpeg automatically or "
                "<a href=\"http://ffmpeg.zeranoe.com/builds/\">download</a> FFmpeg manually "
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

            reply = QMessageBox.question(self,
              'Download FFmpeg',
              "Would you like to download and auto-configure FFmpeg?\n\n"
              "The download may take some time (~13 MB).\n"
              "FFmpeg will be downloaded to Crayfish plugin's directory.",
              QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return

            ffmpeg_bin = downloadFfmpeg(self)
            if not ffmpeg_bin:
                return

            # configure the path automatically
            self.radFfmpegCustom.setChecked(True)
            self.editFfmpegPath.setText(ffmpeg_bin)
            s = QSettings()
            s.beginGroup("crayfishViewer/animation")
            s.setValue("ffmpeg", "custom")
            s.setValue("ffmpeg_path", ffmpeg_bin)


        t_start = self.cboStart.itemData(self.cboStart.currentIndex())
        t_end = self.cboEnd.itemData(self.cboEnd.currentIndex())
        if t_start > t_end:
            QMessageBox.information(self, "Export", "Please set valid time interval")
            return

        output_file = self.editOutput.text()
        if len(output_file) == 0:
            QMessageBox.information(self, "Export", "Please set output animation file")
            return

        if self.radLayoutCustom.isChecked():
            try:
                f = open(self.editTemplate.text())
                f.read()
                f.close()
            except IOError:
                QMessageBox.information(self, "Export", "The custom layout template file (.qpt) does not exist or it is not accessible")
                return

        self.buttonBox.setEnabled(False)

        tmpdir = tempfile.mkdtemp(prefix='crayfish')

        w = self.spinWidth.value()
        h = self.spinHeight.value()
        fps = self.spinSpeed.value()
        img_output_tpl = os.path.join(tmpdir, "%03d.png")
        tmpl = None # path to template file to be used

        prog = lambda i,cnt: self.updateProgress(i, cnt)

        QApplication.setOverrideCursor(Qt.WaitCursor)

        d = { 'layer'      : self.l,
              'time'       : (t_start, t_end),
              'img_size'   : (w, h),
              'tmp_imgfile': img_output_tpl,
              'layers'     : self.r.layers(),
              'extent'     : self.r.extent(),
              'crs'        : self.r.mapSettings().destinationCrs(),
              'layout'     : {},
            }

        if self.radLayoutDefault.isChecked():
            d['layout']['type'] = 'default'
            if self.groupTitle.isChecked():
                d['layout']['title'] = self.widgetTitleProps.props()
            if self.groupTime.isChecked():
                d['layout']['time'] = self.widgetTimeProps.props()
            if self.groupLegend.isChecked():
                d['layout']['legend'] = self.widgetLegendProps.props()
        else:
            d['layout']['type'] = 'file'
            d['layout']['file'] = self.editTemplate.text()

        animation(d, prog)

        ffmpeg_res, logfile = images_to_video(img_output_tpl, output_file, fps, self.quality(), ffmpeg_bin)

        if ffmpeg_res:
            shutil.rmtree(tmpdir)

        QApplication.restoreOverrideCursor()

        self.updateProgress(0,1)

        self.buttonBox.setEnabled(True)

        if ffmpeg_res:
            QMessageBox.information(self, "Export", "The export of animation was successful!")
        else:
            QMessageBox.warning(self, "Export",
                "An error occurred when converting images to video. "
                "The images are still available in " + tmpdir + "\n\n"
                "This should not happen. Please file a ticket in "
                "Crayfish issue tracker with the contents from the log file:\n" + logfile)

        self.storeDefaults()

        self.accept()


    def quality(self):
        if self.radQualBest.isChecked():
            return 0
        elif self.radQualLow.isChecked():
            return 2
        else:         # high
            return 1


    def setQuality(self, qual):
        if qual == 0:
            self.radQualBest.setChecked(True)
        elif qual == 2:
            self.radQualLow.setChecked(True)
        else:
            self.radQualHigh.setChecked(True)


    def updateProgress(self, i, cnt):
        """ callback from animation routine """
        self.progress.setMaximum(cnt)
        self.progress.setValue(i)
        qApp.processEvents()


    def storeDefaults(self):
        s = QSettings()
        s.beginGroup("crayfishViewer/animation")
        # general tab
        s.setValue("width", self.spinWidth.value())
        s.setValue("height", self.spinHeight.value())
        s.setValue("time_start", self.cboStart.itemData(self.cboStart.currentIndex()))
        s.setValue("time_end", self.cboEnd.itemData(self.cboEnd.currentIndex()))
        s.setValue("fps", self.spinSpeed.value())
        # layout tab
        s.setValue("layout_type", "default" if self.radLayoutDefault.isChecked() else "file")
        s.setValue("layout_default_title", self.groupTitle.isChecked())
        s.setValue("layout_default_time", self.groupTime.isChecked())
        s.setValue("layout_default_legend", self.groupLegend.isChecked())
        self.widgetTitleProps.storeDefaults(s)
        self.widgetTimeProps.storeDefaults(s)
        self.widgetLegendProps.storeDefaults(s)
        s.setValue("layout_file", self.editTemplate.text())
        # video tab
        s.setValue("quality", self.quality())
        s.setValue("ffmpeg", "system" if self.radFfmpegSystem.isChecked() else "custom")
        s.setValue("ffmpeg_path", self.editFfmpegPath.text())


    def restoreDefaults(self):
        s = QSettings()
        s.beginGroup("crayfishViewer/animation")
        for k in s.childKeys():
            if k == 'width':
                self.spinWidth.setValue(s.value(k,type=int))
            elif k == 'height':
                self.spinHeight.setValue(s.value(k,type=int))
            elif k == 'time_start':
                self.setTimeInCombo(self.cboStart, s.value(k,type=float))
            elif k == 'time_end':
                self.setTimeInCombo(self.cboEnd, s.value(k,type=float))
            elif k == 'fps':
                self.spinSpeed.setValue(s.value(k,type=int))
            elif k == 'layout_type':
                if s.value(k) == "file":
                    self.radLayoutCustom.setChecked(True)
                else:
                    self.radLayoutDefault.setChecked(True)
            elif k == 'layout_default_title':
                self.groupTitle.setChecked(s.value(k,type=bool))
            elif k == 'layout_default_time':
                self.groupTime.setChecked(s.value(k,type=bool))
            elif k == 'layout_default_legend':
                self.groupLegend.setChecked(s.value(k,type=bool))
            elif k == 'layout_file':
                self.editTemplate.setText(s.value(k))
            elif k == 'quality':
                self.setQuality(s.value(k,type=int))
            elif k == 'ffmpeg':
                if s.value(k) == 'custom':
                    self.radFfmpegCustom.setChecked(True)
                else:
                    self.radFfmpegSystem.setChecked(True)
            elif k == 'ffmpeg_path':
                self.editFfmpegPath.setText(s.value(k))

        self.widgetTitleProps.restoreDefaults(s)
        self.widgetTimeProps.restoreDefaults(s)
        self.widgetLegendProps.restoreDefaults(s)


    def setTimeInCombo(self, cbo, time):
        best_i = -1
        best_diff = 999999.
        for i in range(cbo.count()):
            diff = abs(time - cbo.itemData(i))
            if diff < best_diff:
                best_diff = diff
                best_i = i

        cbo.setCurrentIndex(best_i)
