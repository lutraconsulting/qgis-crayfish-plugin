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

import datetime

from processing.tools import dataobjects
from processing.gui.wrappers import EnumWidgetWrapper, InvalidParameterValue
from qgis.core import (QgsProcessingParameterEnum,
                       QgsProcessingUtils,
                       QgsMeshDatasetIndex,
                       QgsMeshLayer,
                       QgsProviderRegistry,
                       QgsDataProvider,
                       QgsMapLayerType,
                       QgsProcessingException)


class DatasetWrapper(EnumWidgetWrapper):
    """Widget wrapper for selection of datasets groups of linked mesh layer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = dataobjects.createContext()

    def on_change(self, wrapper):
        # maps selected indexes to datasets groups indexes,
        # becasue filtering can change 1:1 relations
        self.index_map = {}

        mesh_layer = wrapper.widgetValue()
        all_options = []
        if mesh_layer:
            if type(mesh_layer) == str:
                mesh_layer = QgsProcessingUtils.mapLayerFromString(mesh_layer, self.context)

            if mesh_layer.type() != QgsMapLayerType.MeshLayer:
                return

            dp = mesh_layer.dataProvider()

            dataset_group_filter = self.parameterDefinition().datasetGroupFilter
            options = []
            for i in range(dp.datasetGroupCount()):
                meta = dp.datasetGroupMetadata(i)
                all_options.append(meta.name())
                if not dataset_group_filter or dataset_group_filter(meta):
                    self.index_map[len(options)] = i
                    options.append(meta.name())
        else:
            options = []
        # set all datasets groups names as parameter options,
        # but display only subset passed by filter
        self.parameterDefinition().setOptions(all_options)
        if self.parameterDefinition().allowMultiple():
            self.widget.updateForOptions(options)
        else:
            self.widget.clear()
            for i, opt in enumerate(options):
                self.widget.addItem(opt, i)

    def postInitialize(self, wrappers):
        super().postInitialize(wrappers)
        # find wrapper of mesh layer parameter and register listener for changing its value
        mesh_layer_param = self.parameterDefinition().layer
        wrapper = next((w for w in wrappers if w.parameterDefinition().name() == mesh_layer_param), None)

        # if not wrapper or wrapper.parameterDefinition().type() != 'mesh':
        if not wrapper:
            raise InvalidParameterValue('Dataset parameter must be linked to QgsProcessingParameterMeshLayer')
        wrapper.widgetValueHasChanged.connect(self.on_change)
        self.on_change(wrapper)

    def widgetValue(self):
        value = super().widgetValue()
        # transform indexes of selected items (possibly filtered) to mesh datasets groups indexes
        if type(value) == list:
            return list(map(lambda i: self.index_map[i], value))
        return self.index_map.get(value, None)


class DatasetParameter(QgsProcessingParameterEnum):
    def __init__(self, name, description='', layer=None, allowMultiple=True, datasetGroupFilter=None, optional=False):
        super().__init__(name, description, defaultValue=None, allowMultiple=allowMultiple, optional=optional)
        self.layer = layer
        self.datasetGroupFilter = datasetGroupFilter
        self.setMetadata({'widget_wrapper': DatasetWrapper})


class TimestepWidgetWrapper(EnumWidgetWrapper):
    """Widget wrapper for selection of timestep of linked mesh layer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context = dataobjects.createContext()

    def on_change(self, wrapper):
        mesh_layer = wrapper.widgetValue()
        self.widget.clear()
        if mesh_layer:
            if type(mesh_layer) == str:
                mesh_layer = QgsProcessingUtils.mapLayerFromString(mesh_layer, self.context)

            if mesh_layer.type() != QgsMapLayerType.MeshLayer:
                return
            dp = mesh_layer.dataProvider()

            datasetCount = 0
            groupWithMaximumDatasets = -1
            for i in range(dp.datasetGroupCount()):
                currentCount = dp.datasetCount(i)
                if currentCount > datasetCount:
                    datasetCount = currentCount
                    groupWithMaximumDatasets = i

            options = []
            if groupWithMaximumDatasets > -1:
                for i in range(datasetCount):
                    index = QgsMeshDatasetIndex(groupWithMaximumDatasets, i)
                    meta = dp.datasetMetadata(index)
                    time = meta.time()
                    options.append((mesh_layer.formatTime(time), i))
        else:
            options = []
        self.parameterDefinition().setOptions([t for t, v in options])
        for text, data in options:
            self.widget.addItem(text, data)

    def postInitialize(self, wrappers):
        super().postInitialize(wrappers)
        mesh_layer_param = self.parameterDefinition().layer
        wrapper = next((w for w in wrappers if w.parameterDefinition().name() == mesh_layer_param), None)

        # if not wrapper or wrapper.parameterDefinition().type() != 'mesh':
        if not wrapper:
            raise InvalidParameterValue('Timestep parameter must be linked to QgsProcessingParameterMeshLayer')

        wrapper.widgetValueHasChanged.connect(self.on_change)
        self.on_change(wrapper)


class TimestepParameter(QgsProcessingParameterEnum):
    def __init__(self, name, description='', layer=None, optional=False):
        super().__init__(name, description, allowMultiple=False, defaultValue=None, optional=optional)
        self.layer = layer
        self.setMetadata({'widget_wrapper': TimestepWidgetWrapper})
