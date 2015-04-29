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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import os
import shutil
import tempfile

from crayfish_animation import animation, images_to_video
from crayfish_gui_utils import timeToString

from crayfish_animation_dialog_widget import Ui_CrayfishAnimationDialog


class CrayfishAnimationDialog(QDialog, Ui_CrayfishAnimationDialog):

    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.l = iface.activeLayer()
        self.r = iface.mapCanvas().mapRenderer()

        self.populateTimes(self.cboStart)
        self.populateTimes(self.cboEnd)
        self.cboStart.setCurrentIndex(0)
        self.cboEnd.setCurrentIndex(self.cboEnd.count()-1)

        defprops = { 'text_color' : QColor(0,0,0), 'text_font' : QFont(), 'bg' : False, 'bg_color' : QColor(255,255,255) }
        titleprops = defprops.copy()
        titleprops['type'] = 'title'
        titleprops['label'] = self.l.name()
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

        self.buttonBox.accepted.connect(self.onOK)
        self.btnBrowseOutput.clicked.connect(self.browseOutput)


    def populateTimes(self, cbo):
        ds = self.l.currentDataSet()
        cbo.clear()
        if ds.time_varying():
            for output in ds.outputs():
                cbo.addItem(timeToString(output.time()), output.time())


    def browseOutput(self):
        settings = QSettings()
        lastUsedDir = settings.value("crayfishViewer/lastFolder")
        filename = QFileDialog.getSaveFileName(self, "Output file", lastUsedDir, "AVI files (*.avi)")
        if len(filename) == 0:
            return

        self.editOutput.setText(filename)
        settings.setValue("crayfishViewer/lastFolder", filename)


    def onOK(self):

        t_start = self.cboStart.itemData(self.cboStart.currentIndex())
        t_end = self.cboEnd.itemData(self.cboEnd.currentIndex())
        if t_start > t_end:
            QMessageBox.information(self, "Export", "Please set valid time interval")
            return

        output_file = self.editOutput.text()
        if len(output_file) == 0:
            QMessageBox.information(self, "Export", "Please set output animation file")
            return

        self.buttonBox.setEnabled(False)

        tmpdir = tempfile.mkdtemp(prefix='crayfish')

        w = self.spinWidth.value()
        h = self.spinHeight.value()
        fps = self.spinSpeed.value()
        img_output_tpl = os.path.join(tmpdir, "%03d.png")
        img_output_men = os.path.join(tmpdir, "*.png")
        tmpl = None # path to template file to be used

        prog = lambda i,cnt: self.updateProgress(i, cnt)

        QApplication.setOverrideCursor(Qt.WaitCursor)

        d = { 'layer'      : self.l,
              'time'       : (t_start, t_end),
              'img_size'   : (w, h),
              'tmp_imgfile': img_output_tpl,
              'layers'     : self.r.layerSet(),
              'extent'     : self.r.extent(),
              'crs'        : self.r.destinationCrs(),
              'layout'     : { 'type' : 'default' },
            }

        if self.groupTitle.isChecked():
            d['layout']['title'] = self.widgetTitleProps.props()
        if self.groupTime.isChecked():
            d['layout']['time'] = self.widgetTimeProps.props()
        if self.groupLegend.isChecked():
            d['layout']['legend'] = self.widgetLegendProps.props()

        if self.radQualBest.isChecked():
            qual = 0
        elif self.radQualLow.isChecked():
            qual = 2
        else:         # high
            qual = 1

        animation(d, prog)

        mencoder_res = images_to_video(img_output_men, output_file, fps, qual)

        if mencoder_res:
            shutil.rmtree(tmpdir)

        QApplication.restoreOverrideCursor()

        self.updateProgress(0,1)

        self.buttonBox.setEnabled(True)

        if mencoder_res:
            QMessageBox.information(self, "Export", "The export of animation was successful!")
        else:
            QMessageBox.warning(self, "Export", "An error occurred when converting images to video. The images are still available in " + tmpdir)

        self.accept()


    def updateProgress(self, i, cnt):
        """ callback from animation routine """
        self.progress.setMaximum(cnt)
        self.progress.setValue(i)
