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
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#ifndef CRAYFISH_HDF5_H
#define CRAYFISH_HDF5_H

/** A simple C++/Qt wrapper around HDF5 library API */

// for compatibility (older hdf5 version in Travis)
#define H5Gopen_vers 1

#include "hdf5.h"

#include <QSharedData>
#include <QStringList>
#include <QVector>

#define HDF_MAX_NAME 1024
struct HdfString {
  char data [HDF_MAX_NAME];
};

template <int TYPE> inline void hdfClose(hid_t id) {
  qDebug("Unknown type!");
}

template <> inline void hdfClose<H5I_FILE>(hid_t id) {
  H5Fclose(id);
}
template <> inline void hdfClose<H5I_GROUP>(hid_t id) {
  H5Gclose(id);
}
template <> inline void hdfClose<H5I_DATASET>(hid_t id) {
  H5Dclose(id);
}
template <> inline void hdfClose<H5I_ATTR>(hid_t id) {
  H5Dclose(id);
}

template <int TYPE>
class HdfH : public QSharedData {
public:
  HdfH(hid_t hid) : id(hid) {}
  HdfH(const HdfH& other) : QSharedData(other), id(other.id) { }
  ~HdfH() {
    if ( id >= 0 ) hdfClose<TYPE>(id);
  }

  hid_t id;
};

class HdfGroup;
class HdfDataset;
class HdfAttribute;

class HdfFile {
public:
  typedef HdfH<H5I_FILE> Handle;

  HdfFile(const QString& path) {
    d = new Handle( H5Fopen(path.toUtf8().data(), H5F_ACC_RDONLY, H5P_DEFAULT) );
  }

  bool isValid() const {
    return d->id >= 0;
  }
  hid_t id() const {
    return d->id;
  }

  inline QStringList groups() const;

  inline HdfGroup group(const QString& path) const;
  inline HdfDataset dataset(const QString& path) const;
  inline HdfAttribute attribute(const QString& attr_name) const;

protected:
  QSharedDataPointer<Handle> d;
};

class HdfGroup {
public:
  typedef HdfH<H5I_GROUP> Handle;

  HdfGroup(hid_t file, const QString& path) {
    d = new Handle( H5Gopen(file, path.toUtf8().data()) );
  }

  bool isValid() const {
    return d->id >= 0;
  }
  hid_t id() const {
    return d->id;
  }
  hid_t file_id() const {
    return H5Iget_file_id(d->id);
  }

  QString name() const {
    char name[HDF_MAX_NAME];
    H5Iget_name (d->id, name, HDF_MAX_NAME);
    return QString::fromUtf8(name);
  }

  QStringList groups() const {
    return objects(H5G_GROUP);
  }
  QStringList datasets() const {
    return objects(H5G_DATASET);
  }
  QStringList objects() const {
    return objects(H5G_UNKNOWN);
  }

  QString childPath(const QString& childName) const {
    return name() + "/" + childName;
  }

  inline HdfGroup group(const QString& groupName) const;
  inline HdfDataset dataset(const QString& dsName) const;
  inline HdfAttribute attribute(const QString& attr_name) const;

protected:
  QStringList objects(H5G_obj_t type) const {
    QStringList lst;

    hsize_t nobj;
    H5Gget_num_objs(d->id, &nobj);
    for (hsize_t i = 0; i < nobj; ++i) {
      if ( type == H5G_UNKNOWN || H5Gget_objtype_by_idx(d->id, i ) == type ) {
        char name[HDF_MAX_NAME];
        H5Gget_objname_by_idx(d->id, i, name, (size_t)HDF_MAX_NAME);
        lst << QString::fromUtf8(name);
      }
    }
    return lst;
  }

protected:
  QSharedDataPointer<Handle> d;
};


class HdfAttribute {
public:
  typedef HdfH<H5I_ATTR> Handle;

  HdfAttribute(hid_t obj_id, const QString& attr_name) {
    d = new Handle( H5Aopen(obj_id, attr_name.toUtf8().data(), H5P_DEFAULT) );
  }

  bool isValid() const {
    return d->id >= 0;
  }
  hid_t id() const {
    return d->id;
  }

  QString readString() const {
    char name[HDF_MAX_NAME];
    hid_t datatype = H5Tcopy(H5T_C_S1);
    H5Tset_size(datatype, HDF_MAX_NAME);
    herr_t status = H5Aread(d->id, datatype, name);
    if (status < 0) {
      qDebug("Failed to read data!");
      return QString();
    }
    H5Tclose(datatype);
    return QString::fromUtf8(name);
  }
protected:
  QSharedDataPointer<Handle> d;
};

class HdfDataset {
public:
  typedef HdfH<H5I_DATASET> Handle;

  HdfDataset(hid_t file, const QString& path) {
    d = new Handle( H5Dopen2(file, path.toUtf8().data(), H5P_DEFAULT) );
  }

  bool isValid() const {
    return d->id >= 0;
  }
  hid_t id() const {
    return d->id;
  }

  QVector<hsize_t> dims() const {
    hid_t sid = H5Dget_space(d->id);
    QVector<hsize_t> d(H5Sget_simple_extent_ndims(sid));
    H5Sget_simple_extent_dims(sid, d.data(), NULL);
    H5Sclose(sid);
    return d;
  }

  hsize_t elementCount() const {
    hsize_t count = 1;
    foreach (hsize_t dsize, dims())
    count *= dsize;
    return count;
  }

  H5T_class_t type() const {
    hid_t tid = H5Dget_type(d->id);
    H5T_class_t t_class = H5Tget_class(tid);
    H5Tclose(tid);
    return t_class;
  }

  QVector<uchar> readArrayUint8() const {
    return readArray<uchar>(H5T_NATIVE_UINT8);
  }

  QVector<float> readArray() const {
    return readArray<float>(H5T_NATIVE_FLOAT);
  }

  QVector<double> readArrayDouble() const {
    return readArray<double>(H5T_NATIVE_DOUBLE);
  }

  QVector<int> readArrayInt() const {
    return readArray<int>(H5T_NATIVE_INT);
  }

  QStringList readArrayString() const {
    QStringList ret;

    hid_t datatype = H5Tcopy(H5T_C_S1);
    H5Tset_size(datatype, HDF_MAX_NAME);

    QVector<HdfString> arr = readArray<HdfString>(datatype);

    H5Tclose(datatype);

    foreach (HdfString str, arr) {
      QString dat = QString::fromUtf8(str.data);
      ret.push_back(dat.trimmed());
    }

    return ret;
  }


  template <typename T> QVector<T> readArray(hid_t mem_type_id) const {
    hsize_t cnt = elementCount();
    QVector<T> data(cnt);
    herr_t status = H5Dread(d->id, mem_type_id, H5S_ALL, H5S_ALL, H5P_DEFAULT, data.data());
    if (status < 0) {
      qDebug("Failed to read data!");
      return QVector<T>();
    }
    return data;
  }

  float readFloat() {
    if (elementCount() != 1) {
      qDebug("Not scalar!");
      return 0;
    }

    float value;
    herr_t status = H5Dread(d->id, H5T_NATIVE_FLOAT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &value);
    if (status < 0) {
      qDebug("Failed to read data!");
      return 0;
    }
    return value;
  }

  QString readString() const {
    if (elementCount() != 1) {
      qDebug("Not scalar!");
      return QString();
    }

    char name[HDF_MAX_NAME];
    hid_t datatype = H5Tcopy(H5T_C_S1);
    H5Tset_size(datatype, HDF_MAX_NAME);
    herr_t status = H5Dread(d->id, datatype, H5S_ALL, H5S_ALL, H5P_DEFAULT, name);
    if (status < 0) {
      qDebug("Failed to read data!");
      return QString();
    }
    H5Tclose(datatype);
    return QString::fromUtf8(name);
  }

protected:
  QSharedDataPointer<Handle> d;
};

QStringList HdfFile::groups() const {
  return group("/").groups();
}

inline HdfGroup HdfFile::group(const QString& path) const {
  return HdfGroup(d->id, path);
}

inline HdfDataset HdfFile::dataset(const QString& path) const {
  return HdfDataset(d->id, path);
}

inline HdfGroup HdfGroup::group(const QString& groupName) const {
  return HdfGroup(file_id(), childPath(groupName));
}

inline HdfDataset HdfGroup::dataset(const QString& dsName) const {
  return HdfDataset(file_id(), childPath(dsName));
}

inline HdfAttribute HdfFile::attribute(const QString& attr_name) const {
  return HdfAttribute(d->id, attr_name);
}

inline HdfAttribute HdfGroup::attribute(const QString& attr_name) const {
  return HdfAttribute(d->id, attr_name);
}

#endif // CRAYFISH_HDF5_H
