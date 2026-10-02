
import platform
import shutil
import psutil


def get_system_info():
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(
        platform.system() == "Windows" and "C:\\" or "/"
    )

    return {
        "system": platform.system(),
        "release": platform.release(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "ram_total_gb": round(
            memory.total / (1024 ** 3), 2
        ),
        "ram_available_gb": round(
            memory.available / (1024 ** 3), 2
        ),
        "disk_total_gb": round(
            disk.total / (1024 ** 3), 2
        ),
        "disk_free_gb": round(
            disk.free / (1024 ** 3), 2
        ),
    }