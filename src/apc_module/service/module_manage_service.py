import ray
import ray.actor

from apc_module.dto.kafka.consumer.change_apc_data_dto import ChangeApcDataDto

from ..dto.module_manage.request.request_put_rule_line_dto import (
  RequestPutRuleLineDto
)
from ..dto.module_manage.request_module_manage_dto import (
  RequestModuleManageDto
)
from ..dto.module_manage.response_module_mange_dto import (
  ResponseModuleManageDto
)
from ..module.apc_module import ApcModule

class ModuleManageService:
  def __init__(
    self,
    actors_dict: dict[int, ray.actor.ActorHandle],
    bootstrap_servers: str,
    socketio_server_url: str,
    bottom_offset_ratio: str
  ):
    self.actors_dict = actors_dict
    self.bootstrap_servers = bootstrap_servers
    self.socketio_server_url = socketio_server_url
    self.bottom_offset_ratio = int(bottom_offset_ratio)
    
  async def start_module(
    self, 
    req: RequestModuleManageDto
  ) -> ResponseModuleManageDto:
    cctv_id = req.cctvId
    
    if cctv_id in self.actors_dict:
      return ResponseModuleManageDto(
        isSuccess=False, 
        cctvIdListOfRunningActor=[
          key_list for 
          key_list in 
          self.actors_dict
        ]
      )
      
    actor: ray.actor.ActorHandle = ApcModule.remote(
      req,
      self.bootstrap_servers,
      self.socketio_server_url,
      self.bottom_offset_ratio
    ) #type: ignore
    actor.start.remote() #type: ignore
    self.actors_dict[cctv_id] = actor 
    
    return ResponseModuleManageDto(
      isSuccess=True, 
      cctvIdListOfRunningActor=[
        key_list for 
        key_list in 
        self.actors_dict
      ]
    )
    

  async def stop_module(
    self, 
    cctv_id: int
  ) -> ResponseModuleManageDto:
    
    if cctv_id in self.actors_dict:
      actor = self.actors_dict[cctv_id]
      actor.stop.remote() #type: ignore
      del self.actors_dict[cctv_id]
      return ResponseModuleManageDto(
        isSuccess=True, 
        cctvIdListOfRunningActor=[
          key_list for 
          key_list in 
          self.actors_dict
        ]
      )
      
    return ResponseModuleManageDto(
      isSuccess=False, 
      cctvIdListOfRunningActor=[
        key_list for 
        key_list in 
        self.actors_dict
      ]
    )
    
  def update_rule_line(
    self, 
    cctv_id: int,
    req: RequestPutRuleLineDto
  ) -> ResponseModuleManageDto:
    actor = self.actors_dict[cctv_id]
    actor.update_rule_line.remote(req) # type: ignore
    return ResponseModuleManageDto(
      isSuccess=True, 
      cctvIdListOfRunningActor=[
        key_list for 
        key_list in 
        self.actors_dict
      ]
    )
  
  async def apply_apc_data(self, data: ChangeApcDataDto):
    for config in data.apcDataList:
        cctv_id=config.cctvId
        area_id=config.areaId
        if cctv_id in self.actors_dict:
          self.update_rule_line(
            cctv_id,
            RequestPutRuleLineDto(
              ruleLineList=config.ruleLineList
            )
          )
          print(f"CCTV {cctv_id}is updated.", flush=True)
        else:
          await self.start_module(
            RequestModuleManageDto(
              cctvId=cctv_id,
              areaId=area_id,
              ruleLineList=config.ruleLineList
            )
          )
          print(f"CCTV {cctv_id}is start", flush=True)