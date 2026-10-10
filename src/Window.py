import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KaDerox.PNGTuberLive")

import os
import time
import customtkinter as ui
from Helpers.UIClasses import *
from Helpers.audio import list_microphones, MicMonitor
from Helpers.settings import load_settings, save_settings
from Server.Server import OverlayServer
import sys
from pathlib import Path

ui.set_appearance_mode("dark")
ui.set_default_color_theme("dark-blue")

DEFAULT_THRESHOLD = 15
DEFAULT_RELEASE = 250
DEFAULT_PORT = 8080

def resource_path(name):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / name)

class App(ui.CTk):
    def __init__(self):
        super().__init__()
        self.title("PNGTuber Live")
        self.geometry("1240x790")
        self.iconbitmap(resource_path("icon.ico"))
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.server = OverlayServer()

        self.current_level = 0.0
        self.gate_open = False
        self.last_loud = 0.0
        self.asset_map = {}

        avatar = Group(self, "Avatar", width=430, height=105)
        avatar.place(x=14, y=14)
        Label(avatar.body, "Idle image:").place(x=10, y=16)
        self.idle = ComboBox(avatar.body, values=["None"], width=300, command=self.refresh_preview)
        self.idle.place(x=115, y=12)
        Label(avatar.body, "Speaking:").place(x=10, y=54)
        self.speaking = ComboBox(avatar.body, values=["None"], width=300, command=self.refresh_preview)
        self.speaking.place(x=115, y=50)

        effects = Group(self, "Effects", width=430, height=350)
        effects.place(x=14, y=131)
        self.speaking_fx = EffectStack(effects.body, "Speaking effects", width=408, height=160)
        self.speaking_fx.place(x=10, y=6)
        self.idle_fx = EffectStack(effects.body, "Idle effects", width=408, height=160)
        self.idle_fx.place(x=10, y=174)

        audio = Group(self, "Audio", width=430, height=62)
        audio.place(x=14, y=493)
        self.mics = list_microphones()
        self.mic_names = list(self.mics) or ["None"]
        Label(audio.body, "Microphone:").place(x=10, y=14)
        self.microphone = ComboBox(audio.body, values=self.mic_names, width=300, command=self.on_mic_changed)
        self.microphone.place(x=115, y=10)

        gate = Group(self, "Noise gate", width=430, height=98)
        gate.place(x=14, y=567)
        Label(gate.body, "Input level:").place(x=10, y=8)
        self.meter = LevelMeter(gate.body, width=217, height=10, threshold=DEFAULT_THRESHOLD / 100)
        self.meter.place(x=150, y=12)
        self.gate_state = Label(gate.body, "Closed", width=48, anchor="e", text_color=MUTED)
        self.gate_state.place(x=367, y=6)
        Label(gate.body, "Threshold:").place(x=10, y=32)
        self.threshold = Slider(gate.body, value=DEFAULT_THRESHOLD, width=265, command=self.on_threshold_changed)
        self.threshold.place(x=150, y=32)
        Label(gate.body, "Release:").place(x=10, y=58)
        self.release = Slider(gate.body, value=DEFAULT_RELEASE, minimum=0, maximum=1000, suffix="ms", width=265)
        self.release.place(x=150, y=58)

        server = Group(self, "Server", width=430, height=62)
        server.place(x=14, y=674)
        Label(server.body, "Port:").place(x=10, y=14)
        self.port = SpinBox(server.body, value=DEFAULT_PORT, minimum=1024, maximum=65535, width=200)
        self.port.place(x=115, y=10)

        assets_group = Group(self, "Assets", width=430, height=722)
        assets_group.place(x=460, y=14)
        self.assets = AssetManager(assets_group.body, width=408, height=697, command=self.on_assets_changed)
        self.assets.place(x=10, y=8)

        preview_group = Group(self, "Preview", width=320, height=722)
        preview_group.place(x=906, y=14)
        self.preview = AvatarPreview(preview_group.body, width=296, height=623, on_frame=self.server.submit)
        self.preview.place(x=10, y=8)

        ToggleButton(self,text_off="Start server",text_on="Stop server",command_on=self.server_start,command_off=self.server_stop,width=130,height=28,font=normal_font(),).place(x=1100, y=750)
        AccentButton(self, text="Save", width=76, command=self.save).place(x=14, y=750)

        self.monitor = MicMonitor()
        self.load()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_level()
        self.animate()

    def on_assets_changed(self, paths):
        self.asset_map = {}
        for path in paths:
            name = os.path.basename(path)
            if name in self.asset_map:
                name = f"{name} ({os.path.basename(os.path.dirname(path))})"
            self.asset_map[name] = path
        names = list(self.asset_map)
        self.idle.set_values(names or ["None"])
        self.speaking.set_values(["None"] + names)
        self.refresh_preview()

    def refresh_preview(self, _=None):
        idle = self.asset_map.get(self.idle.get())
        speaking = self.asset_map.get(self.speaking.get())
        if self.gate_open:
            self.preview.show(speaking or idle, self.speaking_fx.get(), "speaking")
        else:
            self.preview.show(idle, self.idle_fx.get(), "idle")

    def on_threshold_changed(self, value):
        self.meter.set_threshold(value / 100)

    def reset(self):
        self.microphone.set(self.mic_names[0])
        self.on_mic_changed(self.mic_names[0])
        self.speaking_fx.clear()
        self.idle_fx.clear()
        self.threshold.set(DEFAULT_THRESHOLD)
        self.meter.set_threshold(DEFAULT_THRESHOLD / 100)
        self.release.set(DEFAULT_RELEASE)
        self.port.set(DEFAULT_PORT)
        self.assets.clear()

    def save(self):
        save_settings({
            "idle": self.asset_map.get(self.idle.get()),
            "speaking": self.asset_map.get(self.speaking.get()),
            "speaking_fx": self.speaking_fx.get(),
            "idle_fx": self.idle_fx.get(),
            "microphone": self.microphone.get(),
            "threshold": self.threshold.get(),
            "release": self.release.get(),
            "port": self.port.get(),
            "assets": self.assets.get(),
        })

    def load(self):
        data = load_settings()
        if not data:
            return

        for path in data.get("assets", []):
            self.assets.add(path, notify=False)
        self.on_assets_changed(self.assets.get())

        by_path = {path: name for name, path in self.asset_map.items()}
        if data.get("idle") in by_path:
            self.idle.set(by_path[data["idle"]])
        if data.get("speaking") in by_path:
            self.speaking.set(by_path[data["speaking"]])

        self.speaking_fx.set(data.get("speaking_fx", []))
        self.idle_fx.set(data.get("idle_fx", []))

        self.threshold.set(data.get("threshold", DEFAULT_THRESHOLD))
        self.meter.set_threshold(self.threshold.get() / 100)
        self.release.set(data.get("release", DEFAULT_RELEASE))
        self.port.set(data.get("port", DEFAULT_PORT))

        mic = data.get("microphone")
        if mic in self.mics:
            self.microphone.set(mic)
            self.on_mic_changed(mic)

        self.refresh_preview()

    def on_mic_changed(self, name):
        index = self.mics.get(name)
        if index is None:
            self.monitor.stop()
            self.current_level = 0.0
            return
        try:
            self.monitor.start(index)
        except Exception as e:
            print("Can't access microphone:", e)

    def update_level(self):
        peak = None
        while not self.monitor.levels.empty():
            value = self.monitor.levels.get_nowait()
            peak = value if peak is None else max(peak, value)
        if peak is not None:
            self.current_level = min(1.0, peak * 8)

        now = time.monotonic()
        if self.current_level >= self.threshold.get() / 100:
            self.gate_open = True
            self.last_loud = now
        elif self.gate_open and (now - self.last_loud) * 1000 > self.release.get():
            self.gate_open = False

        self.meter.set_level(self.current_level, self.gate_open)
        self.gate_state.configure(
            text="Open" if self.gate_open else "Closed",
            text_color=ACCENT if self.gate_open else MUTED,
        )
        self.after(30, self.update_level)

    def animate(self):
        start = time.perf_counter()
        self.refresh_preview()
        elapsed = (time.perf_counter() - start) * 1000
        self.after(max(1, int(16 - elapsed)), self.animate)

    def on_close(self):
        self.monitor.stop()
        self.destroy()

    def server_start(self):
        self.server.start(self.port.get())
        if self.server.error:
            print("Failed opening server:", self.server.error)
            self.server_toggle.set(False)
            return
        print("Overlay: http://localhost:%d" % self.port.get())

    def server_stop(self):
        self.server.stop()


if __name__ == "__main__":
    App().mainloop()