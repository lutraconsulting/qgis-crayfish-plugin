# -*- coding: utf-8 -*-

# illuvis - Tools for the effective communication of flood risk
# Copyright (C) 2013 Lutra Consulting

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

import traceback
from illuvis_interface import *

from new_scenario_dialog_widget import Ui_Dialog

class NewScenarioDialog(QDialog, Ui_Dialog):
    
    def __init__(self, parent, projectId):
        
        QDialog.__init__(self)
        Ui_Dialog.__init__(self)
        
        self.setupUi(self)
        self.scenarioNameLineEdit.setFocus()
        self.parent = parent
        self.ilCon = parent.ilCon
        self.projectId = projectId
        
    
    def create(self):
        scenarioName = self.scenarioNameLineEdit.text()
        desc = self.descriptionTextEdit.toPlainText()
        scenarioDesc = None
        if len(desc) > 0:
            scenarioDesc = desc
        try:
            self.ilCon.createScenario(self.projectId, scenarioName, scenarioDesc)
            self.accept()
        except IlluvisClientError as e:
            QMessageBox.critical(self, 'Create Scenario', 'The following error occured when creating the scenario: %s' % e.msg)
        except:
            QMessageBox.critical(self, 'Create Scenario', 'The following unexpected error occured when creating the scenario: %s' % traceback.format_exc())
    
    
    def helpPressed(self):
        QDesktopServices.openUrl(QUrl('https://www.illuvis.com/docs/scenarios#qgis-create-scenario'))
