import queue
import numpy as np
import sounddevice as sd


def list_microphones():
    hostapi = sd.query_hostapis(sd.default.hostapi)["name"]
    result = {}
    for index, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] < 1:
            continue
        if sd.query_hostapis(dev["hostapi"])["name"] != hostapi:
            continue
        result[dev["name"]] = index
    return result


class MicMonitor:
    def __init__(self):
        self.stream = None
        self.levels = queue.Queue(maxsize=8)

    def start(self, device_index):
        self.stop()
        self.stream = sd.InputStream(
            device=device_index,
            channels=1,
            callback=self._callback,
            blocksize=1024,
        )
        self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def _callback(self, indata, frames, time, status):
        rms = float(np.sqrt(np.mean(indata ** 2)))
        try:
            self.levels.put_nowait(rms)
        except queue.Full:
            pass