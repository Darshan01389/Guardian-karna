import psutil
import time
import json

class PerformanceMonitor:
    def __init__(self, interval=1):
        self.interval = interval

    def get_memory_usage(self):
        return psutil.virtual_memory()._asdict()

    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=self.interval)

    def get_disk_usage(self):
        return psutil.disk_usage('/')._asdict()

    def monitor(self, duration=10):
        results = []
        start_time = time.time()

        while (time.time() - start_time) < duration:
            performance_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()),
                'memory_usage': self.get_memory_usage(),
                'cpu_usage': self.get_cpu_usage(),
                'disk_usage': self.get_disk_usage(),
            }
            results.append(performance_data)
            time.sleep(self.interval)

        return json.dumps(results, indent=4)

if __name__ == '__main__':
    monitor = PerformanceMonitor(interval=1)
    print(monitor.monitor(duration=10))
