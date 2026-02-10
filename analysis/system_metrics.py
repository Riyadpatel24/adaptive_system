import psutil


class SystemMetrics:
    def collect(self):
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent
        }


def extract_metrics(telemetry):
    return {
        "avg_response_time": telemetry.get("avg_latency", 0),
        "failure_rate": telemetry.get("failure_rate", 0),
        "success_rate": telemetry.get("success_rate", 0)
    }
