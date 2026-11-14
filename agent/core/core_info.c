#define _WIN32_WINNT 0x0600
#include "core.h"
#include <windows.h>

int core_get_info(struct core_info *out) {
    if (!out) return -1;

    out->pid = GetCurrentProcessId();

    SYSTEM_INFO si;
    GetSystemInfo(&si);
    out->cpus = si.dwNumberOfProcessors;
    out->page_size = si.dwPageSize;

    DWORD size = sizeof(out->host) - 1;
    if (GetComputerNameA(out->host, &size) == 0) {
        out->host[0] = '\0';
        return -2;
    }
    out->host[size] = '\0';

    DWORD64 ms = GetTickCount64();
    out->uptime_s = (int64_t)(ms / 1000);

    return 0;
}