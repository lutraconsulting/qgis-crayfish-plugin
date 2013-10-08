# -*- coding: utf-8 -*-

# Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
# Copyright (C) 2012 Peter Wells for Lutra Consulting

# peter dot wells at lutraconsulting dot co dot uk
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

from crayfish_viewer_vector_options_dialog_widget import Ui_Dialog

class CrayfishViewerVectorOptionsDialog(QDialog, Ui_Dialog):
    
    def __init__(self, iface, renderSettings, redrawFunction):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.iface = iface
        self.rs = renderSettings
        self.redraw = redrawFunction
        
        self.rs.save()
        
        # Populate the various widgets
        self.shaftLengthComboBox.setCurrentIndex( self.rs.shaftLength )
        self.stackedWidget.setCurrentIndex( self.rs.shaftLength )
        
        self.minimumShaftLineEdit.setText( str(self.rs.shaftLengthMin) )
        self.maximumShaftLineEdit.setText( str(self.rs.shaftLengthMax) )
        self.scaleByFactorOfLineEdit.setText( str(self.rs.shaftLengthScale) )
        self.lengthLineEdit.setText( str(self.rs.shaftLengthFixedLength) )
        self.lineWidthSpinBox.setValue( self.rs.lineWidth )
        
        self.displayVectorsOnGridGroupBox.setChecked( self.rs.displayVectorsOnGrid )
        self.xSpacingLineEdit.setText( str(self.rs.xSpacing) )
        self.ySpacingLineEdit.setText( str(self.rs.ySpacing) )
        
        self.headWidthLineEdit.setText( str(self.rs.headWidth) )
        self.headLengthLineEdit.setText( str(self.rs.headLength) )
        
        self.filterByMagGroupBox.setChecked( self.rs.filterByMag )
        self.minimumMagLineEdit.setText( str(self.rs.minMag) )
        self.maximumMagLineEdit.setText( str(self.rs.maxMag) )
        
        # Connect each of the widgets to the redraw function
        QObject.connect( self.shaftLengthComboBox, SIGNAL('currentIndexChanged(int)'), self.inputFocusChanged )
        QObject.connect( self.minimumShaftLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.maximumShaftLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.scaleByFactorOfLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.lengthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.lineWidthSpinBox, SIGNAL('valueChanged(int)'), self.inputFocusChanged )
        QObject.connect( self.xSpacingLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.ySpacingLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.headWidthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.connect( self.headLengthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )

    def __del__(self):
        QObject.disconnect( self.shaftLengthComboBox, SIGNAL('currentIndexChanged(int)'), self.inputFocusChanged )
        QObject.disconnect( self.minimumShaftLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.maximumShaftLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.scaleByFactorOfLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.lengthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.lineWidthSpinBox, SIGNAL('valueChanged(int)'), self.inputFocusChanged )
        QObject.disconnect( self.xSpacingLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.ySpacingLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.headWidthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
        QObject.disconnect( self.headLengthLineEdit, SIGNAL('editingFinished()'), self.inputFocusChanged )
    
    def inputFocusChanged(self, arg=None):
        self.saveRenderSettings()
        self.redraw()
    
    def saveRenderSettings(self):
        self.rs.shaftLength = self.shaftLengthComboBox.currentIndex()
        
        self.rs.shaftLengthMin = float( self.minimumShaftLineEdit.text() )
        self.rs.shaftLengthMax = float( self.maximumShaftLineEdit.text() )
        self.rs.shaftLengthScale = float( self.scaleByFactorOfLineEdit.text() )
        self.rs.shaftLengthFixedLength = float( self.lengthLineEdit.text() )
        self.rs.lineWidth = self.lineWidthSpinBox.value()
        
        self.rs.displayVectorsOnGrid = self.displayVectorsOnGridGroupBox.isChecked()
        self.rs.xSpacing = float( self.xSpacingLineEdit.text() )
        self.rs.ySpacing = float( self.ySpacingLineEdit.text() )
        
        self.rs.headWidth = float( self.headWidthLineEdit.text() )
        self.rs.headLength = float( self.headLengthLineEdit.text() )
        
        self.rs.filterByMag = self.filterByMagGroupBox.isChecked()
        self.rs.minMag = float( self.minimumMagLineEdit.text() )
        self.rs.maxMag = float( self.maximumMagLineEdit.text() )
    
    def shaftLengthMethodChanged(self, newIdx):
        """
            The method has been changed, show the appropriate UI
        """
        self.stackedWidget.setCurrentIndex( newIdx )
    
    def accept(self):
        #if not self.valuesOK():
        #    # Does this return cancel the commit or does it still effectively save the values?
        #    return
        self.saveRenderSettings()
        self.done(0)
        
    def apply(self):
        self.saveRenderSettings()
        self.redraw()
    
    def valuesOK(self):
        
        # minimumShaftLineEdit should be less and maximumShaftLineEdit and greater than 0
        
        shaftLengthMin = str( self.minimumShaftLineEdit.text() )
        if not shaftLengthMin.isdigit():
            return False
        shaftLengthMin = float(shaftLengthMin)
        
        shaftLengthMax = str( self.maximumShaftLineEdit.text() )
        if not shaftLengthMax.isdigit():
            return False
        shaftLengthMax = float(shaftLengthMax)
        
        if shaftLengthMin < 0:
            return False
        if shaftLengthMin >= shaftLengthMax:
            return False
            
        """
            FIXME - Finish this when you can be bothered
        """
        
        return True
    
    def reject(self):
        self.rs.restore()
        self.redraw()
        self.done(1)
