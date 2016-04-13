# -*- coding: utf-8 -*-

# illuvis - Tools for the effective communication of flood risk
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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from StringIO import StringIO
import httplib, urllib
from postlib import *
from xml.etree import ElementTree
import platform
import os

class IlluvisClientError(Exception):
    def __init__(self, msg):
        self.msg = msg

class IlluvisRequestFailed(IlluvisClientError):
    def __init__(self, msg):
        IlluvisClientError.__init__(self, msg)

class IlluvisBadRequest(IlluvisClientError):
    def __init__(self, msg):
        IlluvisClientError.__init__(self, msg)

class IlluvisBadResponse(IlluvisClientError):
    def __init__(self, msg):
        IlluvisClientError.__init__(self, msg)

class StringIOWithCallBack(StringIO):
    
    def __init__(self, buf, callback, *args):
        StringIO.__init__(self, buf)
        self.seek(0, os.SEEK_END)
        self._total = self.tell()
        self.seek(0)
        self._callback = callback
        self._args = args
    
    def __len__(self):
        # Required for httplib?
        return self._total
    
    def read(self, size):
        data = StringIO.read(self, size)
        self._callback(self._total, len(data))
        return data

class HttpWorker(QObject):
    
    requestStartedSignal = pyqtSignal(str, name='requestStarted')
    requestFailedSignal = pyqtSignal(str, name='requestFailed')
    requestSucceededSignal = pyqtSignal(list, name='requestSucceeded')
    requestProgressChangedSignal = pyqtSignal(int, name='requestProgressChanged')
    
    def __init__(self, serverPath, host, port, path, userAgent, parent=None, method='POST'):
        QObject.__init__(self, parent)
        self.serverPath = serverPath
        self.host = host
        self.port = port
        self.path = path
        self.userAgent = userAgent
        self.dataSent = 0.0
        self.progress = 0
        self._requestInProgress = False
        
    def processBodyRead(self, totalLength, justRead):
        self.dataSent += justRead
        percentComplete = int( (self.dataSent / totalLength) * 100.0 )
        if percentComplete != self.progress:
            self.requestProgressChangedSignal.emit(percentComplete)
            self.progress = percentComplete
    
    @pyqtSlot(str, str, str)
    def makeRequest(self, requestType, contentType, body):
        
        requestDescription = 'Processing %s request...' % requestType
        self.requestStartedSignal.emit(requestDescription)
        self._requestInProgress = True
        self.dataSent = 0.0
        headers = { "Content-type": contentType,
                    "Accept": "text/plain",
                    "User-Agent": self.userAgent }
        
        body = StringIOWithCallBack(body, self.processBodyRead)
        
        try:
            conn = httplib.HTTPSConnection(self.host, self.port) # FIXME - validate server identity
            conn.request("POST", self.path, body, headers)
            response = conn.getresponse()
            httpStatus = response.status
            responseBody = response.read()
            conn.close()
        except:
            self.requestInProgress = False
            self.requestFailedSignal.emit('Failed to make request to server.')
            return
        self._requestInProgress = False
        self.requestSucceededSignal.emit([requestType, httpStatus, responseBody])
        
    def requestInProgress(self):
        return self._requestInProgress


class IlluvisInterface(QObject):
    
    processedListProjectsResponseSignal = pyqtSignal(list, name='processedListProjectsResponse')
    processedListScenariosResponseSignal = pyqtSignal(list, name='processedListScenariosResponse')
    processedListOverlaysResponseSignal = pyqtSignal(list, name='processedListOverlaysResponse')
    processedListEventsResponseSignal = pyqtSignal(list, name='processedListEventsResponse')
    processedDiskUsageResponseSignal = pyqtSignal(int, int, name='processedDiskUsageResponse')
    processedUploadDataResponseSignal = pyqtSignal(name='processedUploadDataResponse')
    processedUploadOverlayResponseSignal = pyqtSignal(name='processedUploadOverlayResponse')
    requestProgressChangedSignal = pyqtSignal(int, name='requestProgressChanged')
    requestStartedSignal = pyqtSignal(str, name='requestStarted')
    requestFailedSignal = pyqtSignal(str, name='requestFailed')
    requestFinishedSignal = pyqtSignal(name='requestFinished')
    
    
    def __init__(self, parent=None):
        
        QObject.__init__(self, parent)
        
        self.username = None
        self.password = None
        self.serverHost = 'www.illuvis.com'
        self.serverPath = '/wsgi/upload.wsgi'
        self.serverPort = 443
        
        self.projectIdMapping = None
        self.scenarioIdMapping = None
        self.overlayIdMapping = None
        self.eventIdMapping = None
        
        self.versionString = '0.1.0'
        userAgent = 'illuvisPythonInterface/%s (%s)' % (self.versionString, platform.platform())
        self.httpWorker = HttpWorker(serverPath=self.serverPath, host=self.serverHost, port=self.serverPort, path=self.serverPath, userAgent=userAgent)
        self.httpWorker.requestStartedSignal.connect(self.handleRequestStarted)
        self.httpWorker.requestSucceededSignal.connect(self.handleResponse)
        self.httpWorker.requestFailedSignal.connect(self.handleFailure)
        self.httpWorker.requestProgressChangedSignal.connect(self.handleProgressChanged)
        self.httpWorkerThread = QThread()
        self.httpWorker.moveToThread(self.httpWorkerThread)
        self.httpWorkerThread.start()
    
    def __del__(self):
        self.httpWorker.requestProgressChangedSignal.disconnect(self.handleProgressChanged)
        self.httpWorker.requestFailedSignal.disconnect(self.handleFailure)
        self.httpWorker.requestSucceededSignal.disconnect(self.handleResponse)
        self.httpWorker.requestStartedSignal.disconnect(self.handleRequestStarted)
        
    def setCredentials(self, username, password):
        
        self.username = username
        self.password = password
        
    def parseData(self, data):
        f = StringIO(data)
        return ElementTree.parse(f)
        
    def extractProjects(self, data):
        """
            Extract projects from xml response
        """
        tree = self.parseData(data)
        projectElements = tree.findall('./Project')
        projects = []
        self.projectIdMapping = []
        for projectElement in projectElements:
            p = {}
            p['id'] = projectElement.get('id')
            p['name'] = projectElement.get('name')
            p['editable'] = projectElement.get('editable')
            if p['editable'].lower() == 'true':
                self.projectIdMapping.append(int(p['id']))
            projects.append(p)
        return projects
    
    def extractScenarios(self, data):
        """
            Extract scenarios from xml response
        """
        tree = self.parseData(data)
        scenarioElements = tree.findall('./Scenario')
        scenarios = []
        self.scenarioIdMapping = []
        for scenarioElement in scenarioElements:
            s = {}
            s['id'] = scenarioElement.get('id')
            self.scenarioIdMapping.append(int(s['id']))
            s['name'] = scenarioElement.get('name')
            descElems = scenarioElement.findall('./description')
            if len(descElems) > 0:
                s['description'] = descElems[0].text
            extentElems = scenarioElement.findall('./extent')
            if len(extentElems) > 0:
                s['extent'] = extentElems[0].text
            scenarios.append(s)
            
        return scenarios
        
    def extractOverlays(self, data):
        """
            Extract overlays from xml response
        """
        tree = self.parseData(data)
        overlayElements = tree.findall('./Overlay')
        overlays = []
        self.overlayIdMapping = []
        for overlayElement in overlayElements:
            o = {}
            o['id'] = overlayElement.get('id')
            self.overlayIdMapping.append(int(o['id']))
            o['name'] = overlayElement.get('name')
            o['geom_type'] = overlayElement.get('geom_type')
            # There may be other elements but we have not parsed them 
            # here
            overlays.append(o)
            
        return overlays
        
    def extractDiskUsage(self, data):
        tree = self.parseData(data)
        diskUsageElement = tree.findall('./DiskUsageReport')[0]
        usedMb = int(diskUsageElement.get('used'))
        totalMb = int(diskUsageElement.get('total'))
        return usedMb, totalMb
        
    def extractEvents(self, data):
        """
            Extract events from xml response
        """
        tree = self.parseData(data)
        eventElements = tree.findall('./Event')
        events = []
        self.eventIdMapping = []
        for eventElement in eventElements:
            e = {}
            e['id'] = eventElement.get('id')
            self.eventIdMapping.append(int(e['id']))
            e['name'] = eventElement.get('name')
            e['climate_change'] = eventElement.get('climate_change')
            
            returnPeriodElems = eventElement.findall('./ReturnPeriod')
            if len(returnPeriodElems) > 0:
                e['return_period'] = returnPeriodElems[0].text
            
            stormDurationElems = eventElement.findall('./StormDuration')
            if len(stormDurationElems) > 0:
                e['storm_duration'] = stormDurationElems[0].text
            
            modellerElems = eventElement.findall('./Modeller')
            if len(modellerElems) > 0:
                e['modeller'] = modellerElems[0].text
            
            modelNameElems = eventElement.findall('./ModelName')
            if len(modelNameElems) > 0:
                e['model_name'] = modelNameElems[0].text
            
            modelVersionElems = eventElement.findall('./ModelVersion')
            if len(modelVersionElems) > 0:
                e['model_version'] = modelVersionElems[0].text
            
            descriptionElems = eventElement.findall('./Description')
            if len(descriptionElems) > 0:
                e['description'] = descriptionElems[0].text
            
            extentElems = eventElement.findall('./Extent')
            if len(extentElems) > 0:
                e['extent'] = extentElems[0].text
            
            e['first_added'] = eventElement.findall('./FirstAdded')[0].text
            
            events.append(e)
            
        return events
    
    
    """
        Top-level functions
    """
    
    def listProjects(self):
        # The response of this request is handled by handleResponse()
        self.makeRequest(request='ListProjects')
        
    def listScenarios(self, projectId):
        mappedProjectId = self.projectIdMapping[projectId]
        params = [('project_id', str(mappedProjectId))]
        self.makeRequest(request='ListScenarios', params=params)
        
    def listOverlays(self, projectId):
        mappedProjectId = self.projectIdMapping[projectId]
        params = [('project_id', str(mappedProjectId))]
        self.makeRequest(request='ListOverlays', params=params)
    
    def listEvents(self, scenarioId):
        mappedScenarioId = self.scenarioIdMapping[scenarioId]
        params = [('scenario_id', str(mappedScenarioId))]
        self.makeRequest(request='ListEvents', params=params)
        
    def diskUsage(self):
        params = []
        self.makeRequest(request='DiskUsage', params=params)
    
    """ def register(self, registerParams, autoLogin=False):
        
            Make a registration and optionally login with those 
            credentials.
            Assumes registerParams is a list of tuples containing:
                email_address_1
                email_address_2
                password_1
                password_2
                first_name
                last_name
                organisation
        
        status, message, data = self.makeRequest(request='Register', params=registerParams)
        if status == 'Succeeded' and autoLogin:
            for key, val in registerParams:
                if key == 'email_address_1':
                    self.username = val
                elif key == 'password_1':
                    self.password = val """
                    
    def createProject(self, projectName):
        params = [('project_name',projectName)]
        self.makeRequest(request='CreateProject', params=params)
    
    def createScenario(self, projectId, scenarioName, scenarioDesc=None):
        mappedProjectId = self.projectIdMapping[projectId]
        params = [('project_id',str(mappedProjectId)),
                  ('scenario_name',scenarioName)]
        if scenarioDesc is not None:
            params.append( ('description',scenarioDesc) )
        self.makeRequest(request='CreateScenario', params=params)
        
    def createEvent(self, scenarioId, eventName, climateChange, **kwargs):
        mappedScenarioId = self.scenarioIdMapping[scenarioId]
        params = [('scenario_id',str(mappedScenarioId)),
                  ('event_name',eventName),
                  ('climate_change', str(climateChange))]
        if 'return_period' in kwargs.keys():
            params.append( ('return_period',kwargs['return_period']) )
        if 'storm_duration' in kwargs.keys():
            params.append( ('storm_duration',kwargs['storm_duration']) )
        if 'modeller' in kwargs.keys():
            params.append( ('modeller',kwargs['modeller']) )
        if 'model_name' in kwargs.keys():
            params.append( ('model_name',kwargs['model_name']) )
        if 'model_version' in kwargs.keys():
            params.append( ('model_version',kwargs['model_version']) )
        if 'description' in kwargs.keys():
            params.append( ('description',kwargs['description']) )
        self.makeRequest(request='CreateEvent', params=params)
        
    def uploadData(self, eventId, fileType, fileData, **kwargs):
        mappedEventId = self.eventIdMapping[eventId]
        params = [('event_id',str(mappedEventId)),
                  ('file_type', fileType)]
        files = [fileData] # fileData is a tuple of key, fileName and fileData
        self.makeRequest(request='UploadData', \
                         params=params, \
                         files=files)
    
    def uploadOverlay(self, projectId, labelColumnName, overlayName, fileData, **kwargs):
        mappedProjectId = self.projectIdMapping[projectId]
        params = [('project_id',str(mappedProjectId)),
                  ('overlay_name',str(overlayName))]
        
        if labelColumnName != None:
            params.append( ('label_column_name',str(labelColumnName)) )
                  
        files = [fileData] # fileData is a tuple of key, fileName and fileData
        self.makeRequest(request='UploadOverlay', \
                         params=params, \
                         files=files)
        
    def deleteProject(self, projectId):
        mappedProjectId = self.projectIdMapping[projectId]
        params = [('project_id',str(mappedProjectId))]
        self.makeRequest(request='DeleteProject', params=params)
        
    def deleteScenario(self, scenarioId):
        mappedScenarioId = self.scenarioIdMapping[scenarioId]
        params = [('scenario_id',str(mappedScenarioId))]
        self.makeRequest(request='DeleteScenario', params=params)
    
    def deleteEvent(self, eventId):
        mappedEventId = self.eventIdMapping[eventId]
        params = [('event_id',str(mappedEventId))]
        self.makeRequest(request='DeleteEvent', params=params)
        
    def deleteOverlay(self, overlayId):
        mappedOverlayId = self.overlayIdMapping[overlayId]
        params = [('overlay_id',str(mappedOverlayId))]
        self.makeRequest(request='DeleteOverlay', params=params)
        
    def testConnect(self):
        """
            Raises an exception if there is any problem.
        """
        self.listProjects()
        
    def makeRequest(self, request, **kwargs):
        
        """
            Returns <ResponseData/> element of illuvis response, or 
            None if the no <ResponseData/> tag was included in the 
            server response.  
            
            Possible excepetions:
                <IlluvisClientError>
                    <IlluvisRequestFailed>
                    <IlluvisBadRequest>
                    <IlluvisBadResponse>
        """
        
        # FIXME
        #if QMetaObject.invokeMethod(self.httpWorker, 'requestInProgress', Qt.QueuedConnection):
        #    raise IlluvisRequestFailed('There is already an ongoing request to the server.')
        
        fields = []
        files = []
        fields.append( ('request',request) )
        if self.username is not None:
            fields.append( ('username', self.username) )
        if self.password is not None:
            fields.append( ('password', self.password) )
        if 'params' in kwargs.keys():
            # Assuming kwargs['params'] is a list of tuples
            fields.extend(kwargs['params'])
        if 'files' in kwargs.keys():
            files.extend(kwargs['files'])
        contentType, body = encode_multipart_formdata(fields, files)
        
        QMetaObject.invokeMethod(self.httpWorker, 
                                'makeRequest', 
                                Qt.QueuedConnection, 
                                value0=Q_ARG(str, request), 
                                value1=Q_ARG(str, contentType), 
                                value2=Q_ARG(str, body))
        
        
        
    def handleResponse(self, responseData):
        
        requestType = responseData[0]
        httpStatus = responseData[1]
        responseText = responseData[2]
        
        if httpStatus == httplib.REQUEST_ENTITY_TOO_LARGE:
            # Request was too large for the server
            self.handleFailure('The uploaded file is too large.')
            return
        elif httpStatus != httplib.OK:
            # There was an unexpected problem
            self.handleFailure('The server says: %s' % httplib.responses[httpStatus])
            return
        try:
            responseTree = self.parseData(responseText)
            status = responseTree.findall('./Status')[0].text
            message = responseTree.findall('./Message')[0].text
        except:
            self.handleFailure('Failed to parse response from server.')
            return
        if status != 'Succeeded':
            self.handleFailure(message)
            return
        try:
            data = ElementTree.tostring( responseTree.findall('./ResponseData')[0] )
        except IndexError:
            data = None
        
        # Now handle request-specific stuff
        if requestType == 'ListProjects':
            projects = self.extractProjects(data)
            self.processedListProjectsResponseSignal.emit( projects )
        elif requestType == 'ListScenarios':
            scenarios = self.extractScenarios(data)
            self.processedListScenariosResponseSignal.emit( scenarios )
        elif requestType == 'ListOverlays':
            overlays = self.extractOverlays(data)
            self.processedListOverlaysResponseSignal.emit( overlays )
        elif requestType == 'ListEvents':
            events = self.extractEvents(data)
            self.processedListEventsResponseSignal.emit( events )
        elif requestType == 'DiskUsage':
            used, total = self.extractDiskUsage(data) # A tuple of usedMb, totalMb
            self.processedDiskUsageResponseSignal.emit( used, total )
        elif requestType == 'CreateEvent':
            pass
        elif requestType == 'CreateProject':
            pass
        elif requestType == 'CreateScenario':
            pass
        elif requestType == 'DeleteEvent':
            pass
        elif requestType == 'DeleteProject':
            pass
        elif requestType == 'DeleteScenario':
            pass
        elif requestType == 'DeleteOverlay':
            pass
        elif requestType == 'UploadData':
            self.processedUploadDataResponseSignal.emit()
        elif requestType == 'UploadOverlay':
            self.processedUploadOverlayResponseSignal.emit()
        else:
            self.handleFailure('Unsupported server response type: %s' % requestType)
            return
        self.requestFinishedSignal.emit()
            
    def handleRequestStarted(self, requestDescription):
        self.requestStartedSignal.emit(requestDescription)
    
    def handleFailure(self, msg):
        self.requestFailedSignal.emit(msg)
        self.requestFinishedSignal.emit()
    
    def handleProgressChanged(self, pctComplete):
        self.requestProgressChangedSignal.emit( pctComplete )
        

def main():
    
    try:
        
        i = IlluvisInterface()
        
        # Register
        #registerParams = [  ('email_address_1','peter.wells@lutraconsulting.co.uk'),
        #                    ('email_address_2','peter.wells@lutraconsulting.co.uk'),
        #                    ('password_1','pass'),
        #                    ('password_2','pass'),
        #                    ('first_name','Peter'),
        #                    ('last_name','Wells'),
        #                    ('organisation','Lutra') ]
        #i.register(registerParams)
        
        # Test login
        i.setCredentials('peter.wells@lutraconsulting.co.uk', 'pass')
        i.testConnect()
        
        # Create new project
        i.createProject('My First Project')
        
        # List projects
        for proj in i.listProjects():
            print str(proj)
        
        # Create new scenaios
        i.createScenario(0, 'Baseline', 'The situation before the development.')
        i.createScenario(0, 'Proposed', 'The situation after we developed.')
        
        # List scenarios
        for scen in i.listScenarios(0):
            print str(scen)
        
        # Create events
        
        eventName = '100 Yr CCa'
        climateChange = True
        
        returnPeriod = '100 Yr'
        stormDuration = '29 Hr'
        modeller = 'PDW'
        modelName = 'London'
        modelVersion = '101'
        i.createEvent(0, eventName, climateChange, return_period=returnPeriod, \
                      storm_duration=stormDuration, modeller=modeller, \
                      model_name=modelName, model_version=modelVersion)
        
        eventName = '100 Yr CCb'
        climateChange = True
        
        returnPeriod = '100 Yr'
        stormDuration = '29 Hr'
        modeller = 'PDW'
        modelName = 'London'
        modelVersion = '101'
        i.createEvent(0, eventName, climateChange, return_period=returnPeriod, \
                      storm_duration=stormDuration, modeller=modeller, \
                      model_name=modelName, model_version=modelVersion)
        
        eventName = '100 Yr CCc'
        climateChange = True
        
        returnPeriod = '100 Yr'
        stormDuration = '29 Hr'
        modeller = 'PDW'
        modelName = 'London'
        modelVersion = '101'
        i.createEvent(1, eventName, climateChange, return_period=returnPeriod, \
                      storm_duration=stormDuration, modeller=modeller, \
                      model_name=modelName, model_version=modelVersion)
        
        eventName = '100 Yr CCd'
        climateChange = True
        
        returnPeriod = '100 Yr'
        stormDuration = '29 Hr'
        modeller = 'PDW'
        modelName = 'London'
        modelVersion = '101'
        i.createEvent(1, eventName, climateChange, return_period=returnPeriod, \
                      storm_duration=stormDuration, modeller=modeller, \
                      model_name=modelName, model_version=modelVersion)
        
        # List events
        for event in i.listEvents(0):
            print str(event)
    
    except IlluvisClientError as e:
        print 'Failed : %s' % e.msg
    
if __name__ == "__main__":
    main()
