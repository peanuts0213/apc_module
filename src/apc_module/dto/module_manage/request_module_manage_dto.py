from pydantic import BaseModel

from .rule_line_dto import RuleLineDto
from typing import List

class RequestModuleManageDto(BaseModel):
  cctvId: int
  areaId: int
  ruleLineList: List[RuleLineDto]