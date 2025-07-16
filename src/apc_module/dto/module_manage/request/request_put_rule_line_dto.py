from pydantic import BaseModel
from typing import List
from ..rule_line_dto import RuleLineDto

class RequestPutRuleLineDto(BaseModel):
    ruleLineList: List[RuleLineDto]