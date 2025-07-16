import asyncio
import json
import traceback
from typing import Any
import socketio # type: ignore
from queue import Queue
from threading import Thread

from ..dto.socket.result_dto import ResultDto

class SocketClient:
    def __init__(self, cctv_id: int, server_url:str):
        self.cctv_id = cctv_id
        self.sio = socketio.AsyncClient()
        self.queue: Queue[list[ResultDto]] = Queue(maxsize=1)
        self.server_url = server_url
        self.sio.on("connect", self.on_connect) # type: ignore
        self.sio.on("human_detect_event", self.on_event) # type: ignore

        self.loop = asyncio.new_event_loop()
        self._thread = Thread(target=self._start, daemon=True)
        self._thread.start()

    def _start(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect())

    async def _connect(self):
        while True:
            try:
                print(
                    f"client: {self.cctv_id} attempting connection to {self.server_url}", flush=True
                )
                await self.sio.connect(  # type: ignore
                    self.server_url, 
                    socketio_path="ws/socket.io/",
                    transports=["websocket"]
                )
                await self.sio.wait()
            except Exception as e:
                print(f"[client:{self.cctv_id}] Connection failed: {e}", flush=True)
                traceback.print_exc()
                await asyncio.sleep(5)

    async def on_connect(self):
        print(f"[client:{self.cctv_id}] Connected", flush=True)
        await self.sio.emit("register", {"cctv_id": self.cctv_id}) # type: ignore

    async def on_event(self, data: Any):
        try:
            parsed:list[ResultDto] = []
            for item in data:
                if isinstance(item, str):
                    try:
                        item: dict[str, Any] = json.loads(item)
                    except Exception as e:
                        print(f"[client:{self.cctv_id}] ❌ json.loads failed: {e}, \
                            value: {item}")
                        continue
                    
                parsed.append(ResultDto(**item))
                    
            print(
                f"[client:{self.cctv_id}] ✅ Parsed {len(parsed)} objects", flush=True
            )
            self.queue.put(parsed)
        except Exception as e:
            print(f"[client:{self.cctv_id}] Failed to parse data: {data}, error: {e}", flush=True)
            traceback.print_exc()

    def get_data(self):
        """ApcModule에서 데이터를 꺼낼 때 사용"""
        return self.queue.get()

    def close(self):
        try:
            future = asyncio.run_coroutine_threadsafe(self.sio.disconnect(), self.loop)
            future.result(timeout=3)  # optional: 결과 기다림 + timeout 설정 가능
        except Exception as error:
            print(f"[client: {self.cctv_id}] close failed: {error}", flush=True)
            traceback.print_exc()