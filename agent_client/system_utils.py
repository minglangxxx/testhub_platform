import psutil
import platform

def get_system_info():
    """Gathers basic system information."""
    return {
        "os_info": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
    }

def get_resource_usage():
    """Gathers current resource usage."""
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
    }

if __name__ == '__main__':
    print("System Info:", get_system_info())
    print("Resource Usage:", get_resource_usage())
