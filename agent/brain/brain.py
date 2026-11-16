import ctypes
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import errno

CORE = Path(__file__).resolve().parent.parent / "core"


class CoreInfo(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int64),
        ("cpus", ctypes.c_int32),
        ("page_size", ctypes.c_int32),
        ("host", ctypes.c_char * 256),
        ("uptime_s", ctypes.c_int64),
    ]


class CoreProc(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int64),
        ("ppid", ctypes.c_int64),
        ("name", ctypes.c_char * 64),
    ]


class CoreChild(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int64),
        ("handle", ctypes.c_int64),
    ]


class CoreCpu(ctypes.Structure):
    _fields_ = [
        ("user_us", ctypes.c_int64),
        ("kernel_us", ctypes.c_int64),
    ]


core = ctypes.CDLL(str(CORE / "sentry_core.dll"))

core.core_get_info.argtypes = [ctypes.POINTER(CoreInfo)]
core.core_get_info.restype = ctypes.c_int

core.core_list_procs.argtypes = [ctypes.POINTER(CoreProc), ctypes.c_int32, ctypes.POINTER(ctypes.c_int32)]
core.core_list_procs.restype = ctypes.c_int

core.core_spawn.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(CoreChild)]
core.core_spawn.restype = ctypes.c_int

core.core_wait.argtypes = [ctypes.POINTER(CoreChild), ctypes.c_int32, ctypes.POINTER(ctypes.c_int32)]
core.core_wait.restype = ctypes.c_int

core.core_proc_cpu.argtypes = [ctypes.c_int64, ctypes.POINTER(CoreCpu)]
core.core_proc_cpu.restype = ctypes.c_int

TOO_SMALL = 122 if sys.platform == "win32" else errno.ERANGE


def error_text(code):
    return os.strerror(code) if sys.platform != "win32" else ctypes.WinError(code)[1]


def get_info():
    info = CoreInfo()
    err = core.core_get_info(ctypes.byref(info))
    if err != 0:
        raise OSError(err, error_text(err))
    return {
        "pid": info.pid,
        "cpus": info.cpus,
        "page_size": info.page_size,
        "host": info.host.decode("utf-8", "replace"),
        "uptime_s": info.uptime_s,
    }


def list_procs(room=256):
    while True:
        buf = (CoreProc * room)()
        count = ctypes.c_int32()
        err = core.core_list_procs(buf, room, ctypes.byref(count))
        if err == 0:
            return [{"pid": p.pid, "ppid": p.ppid, "name": p.name.decode("utf-8", "replace")}
                    for p in buf[:count.value]]
        if err != TOO_SMALL:
            raise OSError(err, error_text(err))
        room = count.value + 64


def parents(procs, pid):
    by_pid = {p["pid"]: p for p in procs}
    chain = []
    while pid in by_pid and len(chain) < 64:
        p = by_pid[pid]
        chain.append(p)
        if p["ppid"] == pid:
            break
        pid = p["ppid"]
    return chain


def spawn(args):
    argv = (ctypes.c_char_p * (len(args) + 1))(*[a.encode("utf-8") for a in args], None)
    child = CoreChild()
    err = core.core_spawn(argv, ctypes.byref(child))
    if err != 0:
        raise OSError(err, error_text(err))
    return child


def wait(child, timeout_ms=-1):
    code = ctypes.c_int32()
    err = core.core_wait(ctypes.byref(child), timeout_ms, ctypes.byref(code))
    if err != 0:
        raise OSError(err, error_text(err))
    return code.value


def proc_cpu(pid):
    cpu = CoreCpu()
    if core.core_proc_cpu(pid, ctypes.byref(cpu)) != 0:
        return None
    return cpu.user_us + cpu.kernel_us


def cpu_load(interval=1.0):
    procs = list_procs()
    before = {p["pid"]: proc_cpu(p["pid"]) for p in procs}
    start = time.monotonic()
    time.sleep(interval)
    after = {p["pid"]: proc_cpu(p["pid"]) for p in procs}
    wall_us = (time.monotonic() - start) * 1_000_000
    load = []
    for p in procs:
        a, b = before[p["pid"]], after[p["pid"]]
        if a is not None and b is not None:
            load.append({"pid": p["pid"], "name": p["name"], "cpu": round((b - a) * 100 / wall_us)})
    return sorted(load, key=lambda x: x["cpu"], reverse=True)


def send(message, url):
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.URLError as e:
        return 0, str(e)


if __name__ == "__main__":
    child = spawn([sys.executable, "-c", "import time; time.sleep(1); raise SystemExit(3)"])
    procs = list_procs()
    chain = parents(procs, child.pid)
    code = wait(child, 5000)
    top = cpu_load()[:3]
    message = {"event": "agent_started", "os": sys.platform, **get_info(),
               "procs": len(procs), "child": child.pid, "child_code": code,
               "parents": [p["name"] for p in chain],
               "top": [{"pid": t["pid"], "name": t["name"], "cpu": t["cpu"]} for t in top]}
    print(json.dumps(message, ensure_ascii=False, indent=2))
    if len(sys.argv) > 1:
        status, body = send(message, sys.argv[1])
        print("n8n:", status, body)