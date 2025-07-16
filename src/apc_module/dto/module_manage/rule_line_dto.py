from pydantic import BaseModel, ConfigDict
from typing import List
from .rule_line_points_dto import RuleLinePointsDto


class RuleLineDto(BaseModel):
    id: int
    ruleLine: List[RuleLinePointsDto]
    model_config = ConfigDict(extra="ignore")