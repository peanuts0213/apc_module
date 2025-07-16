import asyncio
from threading import Event, Thread
import ray

from ..dto.kafka.producer.apc_event_dto import ApcEventDto
from ..dto.module_manage.request.request_put_rule_line_dto import (
  RequestPutRuleLineDto
)
from ..dto.module_manage.request_module_manage_dto import (
  RequestModuleManageDto
)
from .socket_client import SocketClient
from .tracking import Tracking

@ray.remote(num_cpus=0)
class ApcModule:
  def __init__(
    self,
    request_module_manage_dto: RequestModuleManageDto,
    bootstrap_servers: str,
    socketio_server_url: str,
    bottom_offset_ratio: int
  ):
    
    # Request Values
    self.cctv_id = request_module_manage_dto.cctvId
    self.area_id = request_module_manage_dto.areaId
    self.rule_line_list = request_module_manage_dto.ruleLineList
    
    self.bootstrap_servers = bootstrap_servers
    self.bottom_offset_ratio = bottom_offset_ratio
    #Thread
    self.run_thread: Thread | None = None
    
    # Flag for Process Control
    self.running = False
    self.stop_event: Event = Event()
    
    # Helpers
    self.socket_client = SocketClient(self.cctv_id, socketio_server_url)
    
    # Tracking 초기화
    self.tracking = Tracking(self.rule_line_list, self.bottom_offset_ratio)
  

  def start(self):
    if self.stop_event.is_set():
      self.stop_event.clear()

    if self.running:
      return
    
    self.running = True
    
    self.loop = asyncio.new_event_loop()
    self.run_thread = Thread(target=self._start_loop)
    self.run_thread.start()
    
  def _start_loop(self):
    asyncio.set_event_loop(self.loop)
    self.loop.run_until_complete(self.run())
####################################################
  def stop(self):
    print("stop")
    self.stop_event.set()
    if self.loop and self.loop.is_running():
      self.loop.call_soon_threadsafe(self.loop.stop)
    if self.run_thread and self.run_thread.is_alive():
        self.run_thread.join(timeout=2)
####################################################
  async def run(self):
    try:
      
      from ..service.kafka_service import KafkaService
      self.kafka_service = KafkaService(bootstrap_servers=self.bootstrap_servers)
      await self.kafka_service.start()
      
      while not self.stop_event.is_set():
        
          objects = self.socket_client.get_data()
          self.tracking.update_tracking(objects)
          
          for obj in objects:
            is_in = self.tracking.check_crossing(obj)
            if is_in is not None:
              event = ApcEventDto(
                cctvId=self.cctv_id, 
                areaId=self.area_id,
                isIn=is_in
              )
              await self.kafka_service.send("apc-event", event)
          
    except Exception as error:
      print(f"Error in run: {error}")
    finally:
      print("Run thread exiting")
      self.cleanup()
##################################################     
  def cleanup(self):
    """ 리소스 해제 Method """
    self.running = False
    if self.stop_event.is_set():
        self.stop_event.clear()

    try:
      if self.loop  and self.loop.is_running():
        self.socket_client.close()
        
        future = asyncio.run_coroutine_threadsafe(self.kafka_service.stop(), self.loop)
        future.result(timeout=3) 
    except Exception as e:
        print(f"[{self.cctv_id}] SocketClient close failed: {e}")

    self.tracking.clear()
    print(f"{self.cctv_id} CCTV ApcModule resources cleaned up")
    
    try:
      if self.loop and self.loop.is_running():
        self.loop.call_soon_threadsafe(self.loop.stop)
      if self.loop:
        self.loop.close()
        print(f"[{self.cctv_id}] Event loop closed")
    except Exception as e:
      print(f"[{self.cctv_id}] Failed to close loop: {e}")
############################################################################
  def update_rule_line(self, request_put_rule_line_dto: RequestPutRuleLineDto):
    self.tracking.rule_line_list = request_put_rule_line_dto.ruleLineList
    self.tracking.clear()