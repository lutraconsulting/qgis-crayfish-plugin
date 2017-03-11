#ifndef CRAYFISH_NETCDF_H
#define CRAYFISH_NETCDF_H

#include <QString>

#include <netcdf.h>

#include "crayfish.h"

class NetCDFFile {
public:
    NetCDFFile():mNcid(0){}
    ~NetCDFFile() {
        if (mNcid != 0) nc_close(mNcid);
    }

    int handle() const {
        return mNcid;
    }

    int openFile(const QString& fileName) {
        int ncid = 0;
        int res = nc_open(fileName.toUtf8().constData(), NC_NOWRITE, &mNcid);
        if (res != NC_NOERR)
        {
            qDebug("error: %s", nc_strerror(res));
            throw LoadStatus::Err_UnknownFormat;
        }
        return ncid;
    }

    bool hasVariable(const QString& name) const {
        Q_ASSERT(mNcid != 0);
        int varid;
        return (nc_inq_varid(mNcid, name.toStdString().c_str(), &varid) == NC_NOERR);
    }

    QVector<int> readIntArr(const QString& name, size_t dim) const
    {
        Q_ASSERT(mNcid != 0);
        int arr_id;
        if (nc_inq_varid(mNcid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
        {
            throw LoadStatus::Err_UnknownFormat;
        }
        QVector<int> arr_val(dim);
        if (nc_get_var_int (mNcid, arr_id, arr_val.data()) != NC_NOERR)
        {
            throw LoadStatus::Err_UnknownFormat;
        }
        return arr_val;
    }


    QVector<double> readDoubleArr(const QString& name, size_t dim) const {
        Q_ASSERT(mNcid != 0);

        int arr_id;
        if (nc_inq_varid(mNcid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
        {
            throw LoadStatus::Err_UnknownFormat;
        }
        QVector<double> arr_val(dim);
        if (nc_get_var_double (mNcid, arr_id, arr_val.data()) != NC_NOERR)
        {
            throw LoadStatus::Err_UnknownFormat;
        }
        return arr_val;
    }


    int getAttrInt(const QString& name, const QString& attr_name) const {
        Q_ASSERT(mNcid != 0);

        int arr_id;
        if (nc_inq_varid(mNcid, name.toStdString().c_str(), &arr_id) != NC_NOERR)
        {
            throw LoadStatus::Err_UnknownFormat;
        }

        int val;
        if (nc_get_att_int(mNcid, arr_id, attr_name.toStdString().c_str(), &val))
        {
            throw LoadStatus::Err_UnknownFormat;
        }
        return val;
    }

    QString getAttrStr(const QString& name, const QString& attr_name) const {
        Q_ASSERT(mNcid != 0);

        int arr_id;
        if (nc_inq_varid(mNcid, name.toStdString().c_str(), &arr_id)) throw LoadStatus::Err_UnknownFormat;
        return getAttrStr(attr_name, arr_id);
    }

    QString getAttrStr(const QString& name, int varid) const {
        Q_ASSERT(mNcid != 0);

        size_t attlen = 0;

        if (nc_inq_attlen (mNcid, varid, name.toStdString().c_str(), &attlen)) {
            // attribute is missing
            return QString();
        }

        char *string_attr;
        string_attr = (char *) malloc(attlen + 1);

        if (nc_get_att_text(mNcid, varid, name.toStdString().c_str(), string_attr)) throw LoadStatus::Err_UnknownFormat;
        string_attr[attlen] = '\0';

        QString res(string_attr);
        free(string_attr);

        return res;
    }

    void getDimension(const QString& name, size_t* val, int* ncid_val) const {
        Q_ASSERT(mNcid != 0);

        if (nc_inq_dimid(mNcid, name.toStdString().c_str(), ncid_val) != NC_NOERR) throw LoadStatus::Err_UnknownFormat;
        if (nc_inq_dimlen(mNcid, *ncid_val, val) != NC_NOERR) throw LoadStatus::Err_UnknownFormat;
    }

    void getDimensionOptional(const QString& name, size_t* val, int* ncid_val) const {
        Q_ASSERT(mNcid != 0);

        try {
            getDimension(name, val, ncid_val);
        } catch (LoadStatus::Error) {
            *ncid_val = -1;
            *val = 0;
        }
    }
private:
    int mNcid;

};
#endif // CRAYFISH_NETCDF_H
