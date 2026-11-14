"""Мозг агента: загружает ядро на C и получает сведения о системе."""
import ctypes
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
LIB_NAME = {"win32": "sentry_core.dll", "darwin": "libsentry_core.dylib"}.get(sys.platform, "libsentry_core.so")


class CoreInfo(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_int64),
        ("cpus", ctypes.c_int32),
        ("page_size", ctypes.c_int32),
        ("host", ctypes.c_char * 256),
    ]


core = ctypes.CDLL(str(CORE_DIR / LIB_NAME))
core.core_get_info.argtypes = [ctypes.POINTER(CoreInfo)]
core.core_get_info.restype = ctypes.c_int


def error_text(code):
    if sys.platform == "win32":
        return ctypes.FormatError(code)
    return os.strerror(code)


def get_uptime_seconds():
    """Возвращает время работы системы в секундах (только Windows)."""
    if sys.platform == "win32":
        # GetTickCount64() возвращает миллисекунды с загрузки системы
        kernel32 = ctypes.windll.kernel32
        ms = kernel32.GetTickCount64()
        return ms // 1000
    else:
        # Для Linux/macOS читаем /proc/uptime
        try:
            with open("/proc/uptime", "r") as f:
                return int(float(f.read().split()[0]))
        except Exception:
            return 0


def get_info():
    info = CoreInfo()
    err = core.core_get_info(ctypes.byref(info))
    if err != 0:
        raise OSError(err, error_text(err))
    return {
        "pid": info.pid,
        "cpus": info.cpus,
        "page_size": info.page_size,
        "host": info.host.decode("utf-8"),
        "uptime_s": get_uptime_seconds(),
    }


if __name__ == "__main__":
    message = {"event": "agent_started", "os": sys.platform, **get_info()}
    print(json.dumps(message, ensure_ascii=False, indent=2))

    WEBHOOK_URL = "http://localhost:5678/webhook/d6645e2a-6544-4060-9ebd-92e5af94f832"
    data = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        print("n8n ответ:", resp.status, resp.read().decode())