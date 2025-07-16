from pydantic import BaseModel, ConfigDict
from typing import List
from .apc_data_dto import ApcDataDto


class ChangeApcDataDto(BaseModel):
  apcDataList: List[ApcDataDto]
  model_config = ConfigDict(extra="ignore")