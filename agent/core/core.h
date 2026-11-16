#ifndef CORE_H
#define CORE_H

#include <stdint.h>

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

#define CORE_HOST_MAX 256
#define CORE_NAME_MAX 64

struct core_info {
    int64_t pid;
    int32_t cpus;
    int32_t page_size;
    char host[CORE_HOST_MAX];
    int64_t uptime_s;
};

struct core_proc {
    int64_t pid;
    int64_t ppid;
    char name[CORE_NAME_MAX];
};

struct core_child {
    int64_t pid;
    int64_t handle;
};

struct core_cpu {
    int64_t user_us;
    int64_t kernel_us;
};

EXPORT int core_get_info(struct core_info *out);
EXPORT int core_list_procs(struct core_proc *out, int32_t max, int32_t *count);
EXPORT int core_spawn(char *const argv[], struct core_child *out);
EXPORT int core_wait(struct core_child *child, int32_t timeout_ms, int32_t *exit_code);
EXPORT int core_proc_cpu(int64_t pid, struct core_cpu *out);

#endif