from pydantic import BaseModel, ConfigDict
from typing import List
from ...module_manage.rule_line_dto import RuleLineDto


class ApcDataDto(BaseModel):
  id: int
  cctvId: int
  areaId: int
  ruleLineList: List[RuleLineDto]
  
  model_config = ConfigDict(extra="ignore")