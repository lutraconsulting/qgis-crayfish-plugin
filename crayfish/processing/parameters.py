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

from processing.gui.wrappers import EnumWidgetWrapper, InvalidParameterValue
from qgis.core import QgsProcessingParameterEnum, QgsMeshDatasetIndex


class DatasetGroupType():
    DataOnFaces = 0
    DataOnVertices = 1


class DatasetWrapper(EnumWidgetWrapper):

    def on_change(self, wrapper):
        # maps selected indexes to datasets groups indexes,
        # becasue filtering can change 1:1 relations
        self.index_map = {}
        mesh_layer = wrapper.widgetValue()
        all_options = []
        if mesh_layer:
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
        self.parameterDefinition().setOptions(all_options)
        if self.parameterDefinition().allowMultiple():
            self.widget.updateForOptions(options)
        else:
            self.widget.clear()
            for i, opt in enumerate(options):
                self.widget.addItem(opt, i)

    def postInitialize(self, wrappers):
        super(DatasetWrapper, self).postInitialize(wrappers)
        mesh_layer_param = self.parameterDefinition().layer
        wrapper = next((w for w in wrappers if w.parameterDefinition().name() == mesh_layer_param), None)

        if not wrapper or wrapper.parameterDefinition().type() != 'mesh':
            raise InvalidParameterValue('Dataset parameter must be linked to QgsProcessingParameterMeshLayer')
        wrapper.widgetValueHasChanged.connect(self.on_change)
        self.on_change(wrapper)

    def widgetValue(self):
        value = super().widgetValue()
        if type(value) == list:
            return list(map(lambda i: self.index_map[i], value))
        return self.index_map.get(value, None)


class DatasetParameter(QgsProcessingParameterEnum):
    def __init__(self, name, description='', layer=None, allowMultiple=True, datasetGroupFilter=None, optional=False):
        super(DatasetParameter, self).__init__(
                name, description, defaultValue=None, allowMultiple=allowMultiple, optional=optional)
        self.layer = layer
        self.datasetGroupFilter = datasetGroupFilter
        self.setMetadata({'widget_wrapper': DatasetWrapper})


class TimestepWidgetWrapper(EnumWidgetWrapper):

    def on_change(self, wrapper):
        mesh_layer = wrapper.widgetValue()
        if mesh_layer:
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
                    options.append((str(datetime.timedelta(hours=time)), time))
        else:
            options = []
        self.parameterDefinition().setOptions([t for t, v in options])
        self.widget.clear()
        for text, data in options:
            self.widget.addItem(text, data)

    def postInitialize(self, wrappers):
        super(TimestepWidgetWrapper, self).postInitialize(wrappers)
        mesh_layer_param = self.parameterDefinition().layer
        wrapper = next((w for w in wrappers if w.parameterDefinition().name() == mesh_layer_param), None)

        if not wrapper or wrapper.parameterDefinition().type() != 'mesh':
            raise InvalidParameterValue('Timestep parameter must be linked to QgsProcessingParameterMeshLayer')

        if wrapper.parameterDefinition().name() == self.param.layer:
            wrapper.widgetValueHasChanged.connect(self.on_change)
            self.on_change(wrapper)


class TimestepParameter(QgsProcessingParameterEnum):
    def __init__(self, name, description='', layer=None, optional=False):
        super(TimestepParameter, self).__init__(
                name, description, allowMultiple=False, defaultValue=None, optional=optional)
        self.layer = layer
        self.setMetadata({'widget_wrapper': TimestepWidgetWrapper})
