# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2019 Lutra Consulting

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
from qgis.gui import *

from ..animation import traceAnimation, images_to_video
from .utils import load_ui, handle_ffmpeg


uiDialog, qtBaseClass = load_ui('crayfish_trace_animation_dialog_widget')


class CrayfishTraceAnimationDialog(qtBaseClass, uiDialog):

    def __init__(self, iface, parent=None):

        qtBaseClass.__init__(self)
        uiDialog.__init__(self)
        self.setupUi(self)

        self.l = iface.activeLayer()
        self.r = iface.mapCanvas()

        self.restoreDefaults()

        self.buttonBox.accepted.connect(self.onOK)
        self.btnBrowseOutput.clicked.connect(self.browseOutput)
        self.btnBrowseFfmpegPath.clicked.connect(self.browseFfmpegPath)
        self.btnBrowseImgTmpPath.clicked.connect(self.browseImgTmpPath)

    def browseOutput(self):
        settings = QSettings()
        lastUsedDir = settings.value("crayfishViewer/lastFolder")
        filename, _ = QFileDialog.getSaveFileName(self, "Output file", lastUsedDir, "AVI files (*.avi)")
        if len(filename) == 0:
            return

        self.editOutput.setText(filename)
        settings.setValue("crayfishViewer/lastFolder", filename)

    def browseFfmpegPath(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Path to FFmpeg tool", '', "FFmpeg (ffmpeg ffmpeg.exe avconv avconv.exe)")
        if len(filename) == 0:
            return
        self.editFfmpegPath.setText(filename)

    def browseImgTmpPath(self):
        dir = QFileDialog.getExistingDirectory(self, "Path to image folder")
        if len(dir) == 0:
            return
        self.editImgTmpPath.setText(dir)


    def onOK(self):

        ffmpeg_bin=handle_ffmpeg(self)
        if (ffmpeg_bin==""):
            return;

        output_file = self.editOutput.text()
        if len(output_file) == 0:
            QMessageBox.information(self, "Export", "Please set output animation file")
            return

        self.buttonBox.setEnabled(False)

        tmpdir = tempfile.mkdtemp(prefix='crayfish')
        deleteIntermediateImages = self.radDelTmpImg.isChecked()

        if not deleteIntermediateImages:
            tmpdir = self.editImgTmpPath.text()

        #General settings
        w = self.spinWidth.value()
        h = self.spinHeight.value()
        duration = self.spinDuration.value()
        fps = self.spinSpeed.value()
        img_output_tpl = os.path.join(tmpdir, "%05d.png")

        #Particles Settings
        color=self.particleColorButton.color()
        size=self.spinSize.value()
        count=self.spinCount.value()
        lifeTime=self.spinLifeTime.value()
        maxSpeed=self.spinMaxSpeed.value()
        tailFactor=self.spinTailFactor.value()
        minTailLenght=self.spinMinTailLenght.value()
        persistence=self.spinPersistence.value()


        tmpl = None # path to template file to be used

        prog = lambda i,cnt: self.updateProgress(i, cnt)

        QApplication.setOverrideCursor(Qt.WaitCursor)

        d = { 'layer'      : self.l,
              'img_size'   : (w, h),
              'tmp_imgfile': img_output_tpl,
              'fps'        : fps,
              'duration'   : duration,
              'map_settings': self.r.mapSettings(),
              'color'      : color,
              'size'       : size,
              'count'      : count,
              'life_time'  : lifeTime,
              'max_speed'  : maxSpeed,
              'tail_factor': tailFactor,
              'min_tail_leght':minTailLenght,
              'persistence':persistence,
              }

        traceAnimation(d, prog)

        ffmpeg_res, logfile = images_to_video(img_output_tpl, output_file, fps, self.quality(), ffmpeg_bin)

        if ffmpeg_res and deleteIntermediateImages:
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
        s.beginGroup("crayfishViewer/trace_animation")
        # general tab
        s.setValue("width", self.spinWidth.value())
        s.setValue("height", self.spinHeight.value())
        s.setValue("duration", self.spinDuration.value())
        s.setValue("fps", self.spinSpeed.value())
        # video tab
        s.setValue("quality", self.quality())
        s.setValue("ffmpeg", "system" if self.radFfmpegSystem.isChecked() else "custom")
        s.setValue("ffmpeg_path", self.editFfmpegPath.text())
        # particle tab
        color=self.particleColorButton.color()
        s.setValue("color", color)
        s.setValue("size", self.spinSize.value())
        s.setValue("count", self.spinCount.value())
        s.setValue("lifeTime", self.spinLifeTime.value())
        s.setValue("maxSpeed", self.spinMaxSpeed.value())
        s.setValue("tail_factor", self.spinTailFactor.value())
        s.setValue("min_tail_lenght", self.spinMinTailLenght.value())
        s.setValue("persistence", self.spinPersistence.value())


    def restoreDefaults(self):
        s = QSettings()
        s.beginGroup("crayfishViewer/trace_animation")
        for k in s.childKeys():
            if k == 'width':
                self.spinWidth.setValue(s.value(k,type=int))
            elif k == 'height':
                self.spinHeight.setValue(s.value(k,type=int))
            elif k == 'duration':
                self.spinDuration.setValue(s.value(k,type=float))
            elif k == 'fps':
                self.spinSpeed.setValue(s.value(k,type=int))
            elif k == 'quality':
                self.setQuality(s.value(k,type=int))
            elif k == 'ffmpeg':
                if s.value(k) == 'custom':
                    self.radFfmpegCustom.setChecked(True)
                else:
                    self.radFfmpegSystem.setChecked(True)
            elif k == 'ffmpeg_path':
                self.editFfmpegPath.setText(s.value(k))
            elif k == "color":
                color=QColor(s.value(k))
                self.particleColorButton.setColor(color)
            elif k == "size":
                self.spinSize.setValue(s.value(k, type=float))
            elif k == "count":
                self.spinCount.setValue(s.value(k, type=int))
            elif k == "lifeTime":
                self.spinLifeTime.setValue(s.value(k, type=float ))
            elif k == "maxSpeed":
                self.spinMaxSpeed.setValue(s.value(k,type=int))
            elif k == "tail_factor":
                self.spinTailFactor.setValue(s.value(k, type=float))
            elif k == "min_tail_lenght":
                self.spinMinTailLenght.setValue(s.value(k, type=int))
            elif k == "persistence":
                self.spinPersistence.setValue(s.value(k, type=float))



