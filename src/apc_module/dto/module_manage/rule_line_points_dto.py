from pydantic import BaseModel, ConfigDict


class RuleLinePointsDto(BaseModel):
    x: float
    y: float
    orderIndex: int
    model_config = ConfigDict(extra="ignore")