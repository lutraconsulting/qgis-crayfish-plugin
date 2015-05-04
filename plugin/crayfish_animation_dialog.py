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
        self.btnBrowseMencoderPath.clicked.connect(self.browseMencoderPath)


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


    def browseTemplate(self):
        settings = QSettings()
        lastUsedDir = settings.value("crayfishViewer/lastFolder")
        filename = QFileDialog.getOpenFileName(self, "Template file (.qpt)", lastUsedDir, "QGIS templates (*.qpt)")
        if len(filename) == 0:
            return

        self.editTemplate.setText(filename)
        settings.setValue("crayfishViewer/lastFolder", filename)

    def browseMencoderPath(self):
        filename = QFileDialog.getOpenFileName(self, "Path to MEncoder tool", '', "MEncoder (mencoder mencoder.exe)")
        if len(filename) == 0:
            return
        self.editMencoderPath.setText(filename)


    def onOK(self):

        if self.radMencoderSystem.isChecked():
            mencoder_bin = "mencoder"
        else:
            mencoder_bin = self.editMencoderPath.text()  # custom path

        if which(mencoder_bin) is None:
            QMessageBox.warning(self, "MEncoder missing",
                "The tool for video creation (<a href=\"http://en.wikipedia.org/wiki/MEncoder\">MEncoder</a>) "
                "is missing. Please check your mencoder configuration in <i>Video</i> tab.<p>"
                "<b>Windows users:</b> <a href=\"http://sourceforge.net/projects/mplayerwin/\">Download</a> MEncoder "
                "and configure path to mencoder.exe from the downloaded package.<p>"
                "<b>Linux users:</b> Make sure Mencoder is installed in your system - on Debian/Ubuntu systems "
                "use <tt>sudo apt-get install mencoder</tt>")
            return

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

        mencoder_res = images_to_video(img_output_men, output_file, fps, self.quality(), mencoder_bin)

        if mencoder_res:
            shutil.rmtree(tmpdir)

        QApplication.restoreOverrideCursor()

        self.updateProgress(0,1)

        self.buttonBox.setEnabled(True)

        if mencoder_res:
            QMessageBox.information(self, "Export", "The export of animation was successful!")
        else:
            QMessageBox.warning(self, "Export", "An error occurred when converting images to video. The images are still available in " + tmpdir)

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
        s.setValue("mencoder", "system" if self.radMencoderSystem.isChecked() else "custom")
        s.setValue("mencoder_path", self.editMencoderPath.text())


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
            elif k == 'mencoder':
                if s.value(k) == 'custom':
                    self.radMencoderCustom.setChecked(True)
                else:
                    self.radMencoderSystem.setChecked(True)
            elif k == 'mencoder_path':
                self.editMencoderPath.setText(s.value(k))

        self.widgetTitleProps.restoreDefaults(s)
        self.widgetTimeProps.restoreDefaults(s)
        self.widgetLegendProps.restoreDefaults(s)


    def setTimeInCombo(self, cbo, time):
        best_i = -1
        best_diff = 999999.
        for i in xrange(cbo.count()):
            diff = abs(time - cbo.itemData(i))
            if diff < best_diff:
                best_diff = diff
                best_i = i

        cbo.setCurrentIndex(best_i)
