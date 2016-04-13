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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from qgis.core import *

from .install_helper import plugin_version_str
from .utils import load_ui

uiDialog, qtBaseClass = load_ui('crayfish_about_dialog_widget')

class CrayfishAboutDialog(qtBaseClass, uiDialog):

    def __init__(self, iface, activateNews=False):

        qtBaseClass.__init__(self)
        uiDialog.__init__(self)

        self.setupUi(self)
        self.iface = iface

        doc_dir = os.path.join(os.path.dirname(__file__), "..", "doc")
        self.about_page = os.path.join(doc_dir, "about.html")
        self.news_page = os.path.join(doc_dir, "news.html")

        self.aboutBrowser.setHtml(self.sourceAbout(), QUrl.fromLocalFile(self.about_page))
        self.aboutBrowser.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.aboutBrowser.linkClicked.connect(QDesktopServices.openUrl)

        self.newsBrowser.setHtml(self.sourceNews(), QUrl.fromLocalFile(self.news_page))
        self.newsBrowser.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.newsBrowser.linkClicked.connect(QDesktopServices.openUrl)

        if activateNews:
            self.tabWidget.setCurrentIndex(1)

    def sourceAbout(self):
        src = open(self.about_page).read()
        src = src.replace("%CRAYFISH_VERSION%", plugin_version_str())
        return src

    def sourceNews(self):
        return open(self.news_page).read()
