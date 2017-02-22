#ifndef CRAYFISH_UTILS_H
#define CRAYFISH_UTILS_H

static inline bool equals(float val0, float val1, float eps=std::numeric_limits<float>::epsilon()) {return fabs(val0 - val1) < eps;}

#endif // CRAYFISH_UTILS_H
