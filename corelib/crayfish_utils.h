#ifndef CRAYFISH_UTILS_H
#define CRAYFISH_UTILS_H

#include <QFileInfo>
#include <QString>

static inline bool equals(float val0, float val1, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val0 - val1) < eps;}

static inline bool fileExists(const QString& fileName) {
    QFileInfo check_file(fileName);
    return (check_file.exists() && check_file.isFile());
}

static QDateTime parseTimeUnits(const QString& units, float* timeDiv) {
    QDateTime refTime;

    QStringList formats_supported;
    formats_supported.append("yyyy-MM-dd HH:mm:ss");
    formats_supported.append("yyyy-MM-dd HH:mm:s.z");

    // We are trying to parse strings like
    // "seconds since 2001-05-05 00:00:00"
    // "hours since 1900-01-01 00:00:0.0"
    // "days since 1961-01-01 00:00:00"
    QStringList units_list = units.split(" since ");
    if (units_list.size() == 2) {
        // Give me hours
        if (units_list[0] == "seconds") {
            *timeDiv = 3600.0;
        } else if (units_list[0] == "minutes") {
            *timeDiv = 60.0;
        } else if (units_list[0] == "days") {
            *timeDiv = 1.0 / 24.0;
        } else {
            *timeDiv = 1.0; // hours
        }
        // now time
        foreach (QString fmt, formats_supported) {
            refTime =  QDateTime::fromString(units_list[1], fmt);
            if (refTime.isValid())
                break;

        }
    }

    return refTime;
}

#endif // CRAYFISH_UTILS_H
