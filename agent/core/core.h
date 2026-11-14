#ifndef CORE_H
#define CORE_H

#include <stdint.h>

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

struct core_info {
    int64_t pid;
    int32_t cpus;
    int32_t page_size;
    char host[256];
    int64_t uptime_s;
};

EXPORT int core_get_info(struct core_info *out);

#endif