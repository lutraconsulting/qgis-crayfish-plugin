/*
Crayfish - A collection of tools for TUFLOW and other hydraulic modelling packages
Copyright (C) 2016 Lutra Consulting

info at lutraconsulting dot co dot uk
Lutra Consulting
23 Chestnut Close
Burgess Hill
West Sussex
RH15 8HN

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
if the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#include "crayfish.h"
#include <vector>
#include <string>
#include <sstream>
#include <iostream>
#include <fstream>

#include "crayfish_dataset.h" 
#include "crayfish_output.h"
#include "crayfish_mesh.h"
 
#include "crayfish_hdf5.h"
#include "contrib/tinyxml2.h"

class snapshot;
class outputUpdaterXdmf;
static int readXdmfOutput(ElementOutput *o, int iT, int iF, outputUpdaterXdmf *updater);

class snapshot {
public:
	snapshot(){}
	double time;
	std::vector<std::string> names;
	std::vector<std::vector<std::vector<int> > > HyperSlabs;
	std::vector<std::string> paths;
};

class outputUpdaterXdmf : public outputUpdater {
public:
	outputUpdaterXdmf(){
		lastHdfFilename = "";
		lastDataSet = "";
		HdFile = NULL;
	};
	~outputUpdaterXdmf(){
		if (HdFile) delete HdFile;
	}
	std::vector<snapshot> snaps;
	std::string lastHdfFilename, lastDataSet; //Avoid reloading if file or dataset is the same
	HdfFile *HdFile;
	QVector<hsize_t> dataDim;
	QVector<double> data;
	int update(const Output *o, int iTime, int iField){
		int res =  readXdmfOutput(static_cast<ElementOutput*>(const_cast<Output*>(o)), iTime, iField, this);//non-const cast to fix...
		checkMem(o);
		(const_cast<DataSet*> (o->dataSet))->updateZRange(o->index);
		return res;
	}
};


tinyxml2::XMLElement *getCheckChild(tinyxml2::XMLElement *parent, std::string name){
	tinyxml2::XMLNode *child = parent->FirstChildElement(name.c_str());
	if (!child){
		qDebug("XML Element not found: %s", name.c_str());
		return NULL;
	}
	return child->ToElement();
}

tinyxml2::XMLElement *getCheckSibling(tinyxml2::XMLElement *from, std::string name){
	tinyxml2::XMLNode *child = from->NextSiblingElement(name.c_str());
	if (!child){
		qDebug("XML Element not found: %s", name.c_str());
		return NULL;
	}
	return child->ToElement();
}

std::vector<std::string> split(const std::string &s, char delim) {
	std::vector<std::string> elems;
	std::stringstream ss;
	ss.str(s);
	std::string item;
	while (std::getline(ss, item, delim)) {
		if ( item !="" )
			elems.push_back(item);
	}
	return elems;
}

static int parseXdmfXml(const QString& datFileName, std::vector<snapshot> &snaps, int nElems){
	std::string dfName = datFileName.toUtf8().constData();
	std::string dirName = dfName.substr(0, dfName.find_last_of("/\\") + 1);
	tinyxml2::XMLDocument xmfFile;
	if (xmfFile.LoadFile(dfName.c_str()) != tinyxml2::XML_SUCCESS){
		qDebug("Cannot open xmf file");
		return -1;
	}
	tinyxml2::XMLElement *elem = xmfFile.FirstChildElement("Xdmf");
	if (!elem){
		qDebug("XML Element not found: Xdmf");
		return -1;
	}
	if (strcmp(elem->Attribute("Version"), "2.0") != 0){
		qDebug("Only Xmdf version 2.0 is supported");
		return -1;
	}
	elem = getCheckChild(elem, "Domain");
	if (!elem) return -1;
	elem = getCheckChild(elem, "Grid");
	if (!elem) return -1;
	if (strcmp(elem->Attribute("GridType"), "Collection") != 0){
		qDebug("Expecting Collection Grid Type");
		return -1;
	}
	if (strcmp(elem->Attribute("CollectionType"), "Temporal") != 0){
		qDebug("Expecting Temporal Collection Type");
		return -1;
	}
	for (tinyxml2::XMLNode* gridNod = getCheckChild(elem, "Grid"); gridNod != NULL; gridNod = gridNod->NextSiblingElement("Grid")){
		snapshot snap;
		double t;
		tinyxml2::XMLElement *timeNod = getCheckChild(gridNod->ToElement(), "Time");
		if (!timeNod) return -1;
		timeNod->QueryDoubleAttribute("Value", &t);
		snap.time = t;
		for (tinyxml2::XMLNode* scalarNod = getCheckChild(gridNod->ToElement(), "Attribute"); scalarNod != NULL; scalarNod = scalarNod->NextSiblingElement("Attribute")){
			scalarNod = scalarNod->ToElement();
			if (strcmp(scalarNod->ToElement()->Attribute("Center"), "Cell") != 0){
				qDebug("Only cell centered data is currently supported");
				return -1;
			}
			if (strcmp(scalarNod->ToElement()->Attribute("AttributeType"), "Scalar") != 0 && strcmp(scalarNod->ToElement()->Attribute("AttributeType"), "Vector") != 0){
				qDebug("Only scalar and vector data are currently supported");
				return -1;
			}
			snap.names.push_back(scalarNod->ToElement()->Attribute("Name"));
			tinyxml2::XMLElement *itemNod = getCheckChild(scalarNod->ToElement(), "DataItem");
			if (!itemNod) return -1;
			if (strcmp(itemNod->Attribute("ItemType"), "HyperSlab") != 0 || strcmp(itemNod->Attribute("Type"), "HyperSlab") != 0){
				qDebug("Expecting HyperSlab ItemType and Type");
				return -1;
			}
			int dim;
			itemNod->QueryIntAttribute("Dimensions", &dim);
			if (dim != nElems){
				qDebug("Dataset dimensions should correspond to the number of mesh elements");
				return -1;
			}
			tinyxml2::XMLElement *slabNod = getCheckChild(itemNod, "DataItem");
			if (!slabNod) return -1;
			std::string slabDimS = slabNod->Attribute("Dimensions");
			std::stringstream slabDimSS(slabDimS);
			std::vector<int> slabDim;
			int number;
			while (slabDimSS >> number)
				slabDim.push_back(number);
			if (strcmp(slabNod->Attribute("Format"), "XML") != 0){
				qDebug("Only XML hyperSlab format supported");
				return -1;
			}
			if (slabDim.size() > 2){
				qDebug("Only two-dimensional slab array is supported");
				return -1;
			}

			std::string slabS = slabNod->GetText();
			std::stringstream slabSS(slabS);
			std::vector<std::vector <int> > slab(slabDim[0], std::vector<int>(slabDim[1]));
			int i = 0;
			while (slabSS >> number){
				slab[i / slabDim[0]][i%slabDim[0]] = number;
				i++;
			}
			if (i != slabDim[0] * slabDim[1]){
				qDebug("hyperSlab dimensions mismatch");
				return -1;
			}
			snap.HyperSlabs.push_back(slab);
			tinyxml2::XMLElement *snapshotNod = getCheckSibling(slabNod, "DataItem");
			if (!snapshotNod) return -1;
			std::string snapshotDimS = snapshotNod->Attribute("Dimensions");
			std::stringstream snapshotDimSS(snapshotDimS);
			std::vector<int> snapshotDim;
			while (snapshotDimSS >> number)
				snapshotDim.push_back(number);
			if (strcmp(snapshotNod->Attribute("Format"), "HDF") != 0){
				qDebug("Only HDF dataset format supported");
				return -1;
			}
			if (slabDim.size() > 2){
				qDebug("Only two-dimensional hdf array is supported");
				return -1;
			}
			std::string path = snapshotNod->GetText();
			path.erase(path.begin(), find_if_not(path.begin(), path.end(), [](int c){return isspace(c); }));
			path.erase(find_if_not(path.rbegin(), path.rend(), [](int c){return isspace(c); }).base(), path.end());
			snap.paths.push_back(dirName + path);
		}
		snaps.push_back(snap);
	}
	return 0;
}

Mesh::DataSets Crayfish::loadXdmfDataSet(const QString& datFileName, const Mesh* mesh, LoadStatus* status)
{
	outputUpdaterXdmf *updater = new outputUpdaterXdmf();
	const_cast<Mesh*>(mesh)->updater = updater;//Todo fix const cast
	int nElems = mesh->elements().count();
	if (parseXdmfXml(datFileName, updater->snaps, nElems) < 0){
		if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
		return Mesh::DataSets();
	}
	std::string path = updater->snaps[0].paths[0];
	updater->lastHdfFilename = path.substr(0, path.find_last_of(":"));
	if (updater->HdFile) delete updater->HdFile;
	updater->HdFile = new HdfFile(QString::fromStdString(updater->lastHdfFilename));
	if (!updater->HdFile->isValid())
	{
		qDebug("Cannot read h5 file %s", updater->lastHdfFilename.c_str());
		if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
		return Mesh::DataSets();
	}
	//We suppose all timesteps to have the same structure
	Mesh::DataSets datasets;
	for (int iF = 0; iF < updater->snaps[0].names.size(); iF++){
		DataSet* ds = new DataSet(datFileName);
		ds->index = iF;
		ds->setIsTimeVarying(true);
		ds->setName(QString::fromStdString(updater->snaps[0].names[iF]), false);
		if (updater->snaps[0].HyperSlabs[iF][2][1] == 1)
			ds->setType(DataSet::Scalar);
		else if (updater->snaps[0].HyperSlabs[iF][2][1] == 3)
			ds->setType(DataSet::Vector);
		else
		{
			qDebug("Wrong HyperSlab value: second column should terminate by 1 for scalars and 3 for vectors");
			if (status) status->mLastError = LoadStatus::Err_UnknownFormat;
			return Mesh::DataSets();
		}
		datasets.append(ds);
	}

	for (int iT = 0; iT < updater->snaps.size(); iT++){
		for (int iF = 0; iF < updater->snaps[iT].names.size(); iF++){
			ElementOutput* o = NULL;
			o = new ElementOutput;
			o->index = iT;
			o->time = updater->snaps[iT].time;
			datasets[iF]->addOutput(o);
		}
	}
	return datasets;
}



static int readXdmfOutput(ElementOutput *o, int iT, int iF, outputUpdaterXdmf *updater){
	snapshot &snap = updater->snaps[iT];
	std::string path = snap.paths[iF];
	std::string fname = path.substr(0, path.find_last_of(":"));
	if (strcmp(fname.c_str(), updater->lastHdfFilename.c_str()) != 0){
		if (updater->HdFile) delete updater->HdFile;
		updater->HdFile = new HdfFile(QString::fromStdString(fname));
		if (!updater->HdFile->isValid())
		{
			qDebug("Cannot read h5 file : %s", fname.c_str());
			return -1;
		}
		updater->lastHdfFilename = fname;
	}
	QStringList groupNames = updater->HdFile->groups();
	path = path.substr(path.find_last_of(":") + 1);
	std::vector<std::string> pathSplit = split(path, '/');
	if (!groupNames.contains(QString::fromStdString(pathSplit[0]))){
		qDebug("Datagroup not found : %s", pathSplit[0].c_str());
		return -1;
	}
	HdfGroup dataGroup = updater->HdFile->group(QString::fromStdString(pathSplit[0]));
	if (!dataGroup.isValid()){
		qDebug("Datagroup not valid");
		return -1;
	}
	for (int iP = 1; iP < pathSplit.size() - 1; iP++){
		if (!groupNames.contains(QString::fromStdString(pathSplit[iP]))){
			qDebug("Datagroup not found : %s", pathSplit[iP]);
			return -1;
		}
		dataGroup = dataGroup.group(QString::fromStdString(pathSplit[iP]));
		if (!dataGroup.isValid()){
			qDebug("Datagroup not valid");
			return -1;
		}
	}
	QStringList dataNames = dataGroup.datasets();
	if (!dataNames.contains(QString::fromStdString(pathSplit[pathSplit.size() - 1])))
	{
		qDebug("Dataset not having required arrays : %s", pathSplit[pathSplit.size() - 1].c_str());
	}
	if (strcmp(updater->lastDataSet.c_str(), pathSplit[pathSplit.size() - 1].c_str()) != 0){
		updater->lastDataSet = pathSplit[pathSplit.size() - 1];
		HdfDataset HDFdata = dataGroup.dataset(QString::fromStdString(pathSplit[pathSplit.size() - 1]));
		updater->data = HDFdata.readArrayDouble();  //Todo should be read only once for all fields, as for file opening
		updater->dataDim = HDFdata.dims();
	}
	if (snap.HyperSlabs[iF][2][1] == 1){ //Scalar
		o->init(snap.HyperSlabs[iF][2][0], false);
		int iElem = 0;
		for (int iSlab = 0; iSlab < snap.HyperSlabs[iF][2][0]; iSlab++){
			int idxI = snap.HyperSlabs[iF][0][0] + snap.HyperSlabs[iF][1][0] * iSlab;
			int idxJ = snap.HyperSlabs[iF][0][1];
			o->getValues().data()[iElem] = updater->data[updater->dataDim[1] * idxI + idxJ];
			iElem++;
		}
	}
	else { //Vector
		o->init(snap.HyperSlabs[iF][2][0], true);
		int iElem = 0;
		ElementOutput::float2D* data = o->getValuesV().data();
		for (int iSlab = 0; iSlab < snap.HyperSlabs[iF][2][0]; iSlab++){
			for (int jSlab = 0; jSlab < snap.HyperSlabs[iF][2][1]; jSlab++){
				int idxI = snap.HyperSlabs[iF][0][0] + snap.HyperSlabs[iF][1][0] * iSlab;
				int idxJx = snap.HyperSlabs[iF][0][1];
				int idxJy = snap.HyperSlabs[iF][0][1] + snap.HyperSlabs[iF][1][1];

				data[iElem].x = updater->data[updater->dataDim[1] * idxI + idxJx];
				data[iElem].y = updater->data[updater->dataDim[1] * idxI + idxJy];
				o->getValues().data()[iElem] = data[iElem].length();
			}
			iElem++;
		}

	}
	return 0;
}