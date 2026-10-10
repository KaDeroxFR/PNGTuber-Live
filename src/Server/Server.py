import asyncio
import io
import threading
from pathlib import Path
from aiohttp import web

OVERLAY = Path(__file__).parent / "overlay.html"


class OverlayServer:
    def __init__(self):
        self.loop = None
        self.thread = None
        self.runner = None
        self.clients = set()
        self.error = None
        self.running = False
        self.latest = None
        self.last_png = None
        self.new_frame = threading.Event()

    def submit(self, img):
        self.latest = img
        self.new_frame.set()

    def start(self, port):
        self.error = None
        ready = threading.Event()

        def run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            app = web.Application()
            app.add_routes([web.get("/", self.index), web.get("/ws", self.websocket)])
            self.runner = web.AppRunner(app)
            try:
                self.loop.run_until_complete(self.runner.setup())
                self.loop.run_until_complete(web.TCPSite(self.runner, "127.0.0.1", port).start())
            except OSError as e:
                self.error = e
                ready.set()
                return
            ready.set()
            self.loop.run_forever()
            self.loop.run_until_complete(self.runner.cleanup())
            self.loop.close()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        ready.wait()
        if not self.error:
            self.running = True
            threading.Thread(target=self._encode_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.new_frame.set()
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=3)
        self.loop = None

    def _encode_loop(self):
        while self.running:
            self.new_frame.wait(timeout=0.5)
            self.new_frame.clear()
            img = self.latest
            if img is None or not self.running:
                continue
            buf = io.BytesIO()
            img.save(buf, "PNG", compress_level=1)
            self.last_png = buf.getvalue()
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self._broadcast(self.last_png), self.loop)

    async def _broadcast(self, data):
        for ws in list(self.clients):
            try:
                await ws.send_bytes(data)
            except Exception:
                self.clients.discard(ws)

    async def index(self, request):
        return web.FileResponse(OVERLAY)

    async def websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)
        if self.last_png:
            await ws.send_bytes(self.last_png)
        try:
            async for _ in ws:
                pass
        finally:
            self.clients.discard(ws)
        return ws