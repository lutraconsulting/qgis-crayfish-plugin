#ifndef CRAYFISH_UTILS_H
#define CRAYFISH_UTILS_H

#include <QFileInfo>
#include <QString>

static inline bool equals(float val0, float val1, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val0 - val1) < eps;}

static inline bool fileExists(const QString& fileName) {
    QFileInfo check_file(fileName);
    return (check_file.exists() && check_file.isFile());
}

#endif // CRAYFISH_UTILS_H
