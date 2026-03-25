import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PythonFileHandler(FileSystemEventHandler):
    def __init__(self, process):
        self.process = process
        self.last_modified = time.time()

    def on_modified(self, event):
        if event.src_path.endswith(".py") and time.time() - self.last_modified > 1:
            self.last_modified = time.time()
            print(f"\n📁 Detected change: {event.src_path}")
            self.process.terminate()
            self.process.wait()
            print("🚀 Restarting...\n")
            self.process = subprocess.Popen([sys.executable, "api.py"])


if __name__ == "__main__":
    process = subprocess.Popen([sys.executable, "api.py"])
    observer = Observer()
    observer.schedule(PythonFileHandler(process), ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        process.terminate()
